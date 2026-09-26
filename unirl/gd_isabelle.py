"""Juez de TEOREMA en Isabelle para pasos de descenso de gradiente (diseño: docs/diseno_gd_isabelle.md).

A diferencia de `IsabelleVerifier` (programa ITrees + tripleta de Hoare + anotaciones, con Sledgehammer), aquí el
objetivo es un teorema puro de Isabelle/HOL sobre espacios con producto interno y la acción del agente es la
DEMOSTRACIÓN (texto Isar) más lemas auxiliares opcionales. El juez solo compila: no agrega automatización.

Garantías, en orden:
  1. filtro léxico del texto del agente (`tokenize_outer`): solo comandos de prueba en PROOF, solo lemas con su
     prueba en LEMMAS; nada de sorry, ML, notación, declare, `[[ ]]`, cartuchos ni marcadores `__`;
  2. el objetivo congelado se relee de disco y su hash debe coincidir;
  3. los lemas se demuestran en el kernel antes de usarlos (etapa Lemmas, con el marcador lemmas.ok);
  4. teoría Final: el enunciado se lee antes y después del texto del agente y debe coincidir término a término
     (prop_ok), no aparece ningún axioma nuevo (axioms_ok), y el teorema global `isarl_export` —que escribe el juez
     con el enunciado congelado— se deduce de `isarl_target` usando solo interp y opt, sin oráculos ni skip_proof.

Residuo de confianza (va en los informes): que interp ⇔ «f convexa y 1-suave con gradiente g» no se demuestra en
Isabelle; es matemática de libro (Nesterov, Thm. 2.1.5, y su recíproco).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
import time
import uuid
from pathlib import Path

from .verifiers import (ALLOWED_COMMANDS, ISABELLE_COMMANDS, TARGETS, _BANNED_WORDS, _LEMMA_HEADS, _MEANING_COMMANDS,
                        IsabelleVerifier, Outcome, _import_from, check_lemmas, kill_build_of, kill_tree, merge_lemmas,
                        split_lemmas, tokenize_outer)

# ----------------------------------------------------------------------------- filtros

PROOF_MAX_CHARS = 20000
# comandos de prueba: los de ALLOWED_COMMANDS salvo los que abren un enunciado nuevo
PROOF_COMMANDS = frozenset(ALLOWED_COMMANDS - _LEMMA_HEADS)
_UNSOUND_WORDS = frozenset({"sorry", "oops", "axiomatization", "axioms", "oracle"})
# palabras que, justo después de `theorem isarl_target: "..."`, alargarían el enunciado (p. ej. `if "False"` añade
# una hipótesis); el kernel lo detecta igual (prop_ok), pero así se etiqueta sin compilar
_STATEMENT_WORDS = frozenset({"if", "for", "when", "and", "shows", "assumes", "fixes", "obtains", "defines", "includes",
                              "notes", "constrains", "where"})
# nombres que usa el juez; los lemas del agente no pueden declararlos
_RESERVED = re.compile(r"(?:isarl[A-Za-z0-9_']*|interp|opt|gd)$")  # los del objetivo gd original (compatibilidad)


def nombres_del_objetivo(spec: dict) -> set[str]:
    """Nombres que los lemas del agente no pueden declarar: etiquetas de las hipótesis (`ab:`, `interp:`, …) y
    constantes que define el preludio (`primrec`, `fun`, `definition`, …)."""
    etiquetas = set(re.findall(r"(?:^|\band\b)\s*([A-Za-z_][A-Za-z0-9_']*)\s*:", spec.get("assumes", ""), re.M))
    constantes = set(re.findall(r"^\s*(?:primrec|fun|function|definition|abbreviation)\s+([A-Za-z_][A-Za-z0-9_']*)",
                                spec.get("prelude", ""), re.M))
    return etiquetas | constantes


def check_proof(text: str) -> tuple[str, str] | None:
    """None si el texto de PROOF pasa el filtro; si no, (etiqueta, motivo). Con varias infracciones gana la deriva,
    luego UNSOUND y luego INVALID_PROPOSAL."""
    if not text.strip():
        return "INVALID_PROPOSAL", "PROOF vacío: falta la demostración (PROOF: <<< ... >>>)"
    if len(text) > PROOF_MAX_CHARS:
        return "INVALID_PROPOSAL", f"la PROOF supera {PROOF_MAX_CHARS} caracteres"
    if "__" in text or "[[" in text:
        return "STATEMENT_DRIFT", "la PROOF contiene '__' o '[['"
    try:
        toks = tokenize_outer(text)
    except ValueError as e:
        return _sintaxis(("STATEMENT_DRIFT", f"la PROOF no se admite: {e}"))
    words = [t for k, t in toks if k in ("word", "punct")]
    # cada segmento de un identificador largo se revisa además por separado (defensa en profundidad, como check_lemmas)
    segs = [seg for t in words for seg in t.split(".") if seg] + words
    for w in segs:
        if (w in _BANNED_WORDS and w not in _UNSOUND_WORDS) or w in _MEANING_COMMANDS:
            return "STATEMENT_DRIFT", f"la PROOF usa {w!r}"
    for w in segs:
        if w in _UNSOUND_WORDS:
            return "UNSOUND", f"la PROOF usa {w}"
    for w in words:
        if w in ISABELLE_COMMANDS and w not in PROOF_COMMANDS:
            return "INVALID_PROPOSAL", (f"comando no admitido en PROOF: {w!r} (solo comandos de prueba; los lemas "
                                        "auxiliares van en LEMMAS)")
    if not toks:
        return "INVALID_PROPOSAL", "la PROOF no contiene ninguna demostración"
    i = 0
    if toks[0][1] == "(" and len(toks) > 1 and toks[1][1] == "is":  # patrón «(is "...")» del enunciado: inofensivo
        while i < len(toks) and toks[i][1] != ")":
            i += 1
        i += 1
    if i >= len(toks):
        return "INVALID_PROPOSAL", "la PROOF no contiene ninguna demostración"
    kind, first = toks[i]
    if kind == "string" or first in _STATEMENT_WORDS:
        return "STATEMENT_DRIFT", f"la PROOF empieza con {first[:40]!r}: eso alargaría el enunciado de isarl_target"
    if first not in PROOF_COMMANDS:
        return "INVALID_PROPOSAL", f"la PROOF debe empezar con un comando de prueba (by, proof, using, unfolding, apply, ...), no con {first[:40]!r}"
    return None


def reserved_names(text: str, extra: set[str] | frozenset = frozenset()) -> list[str]:
    """Nombres reservados que el bloque de lemas DECLARA (tras lemma/theorem/…, o seguidos de «:», con atributos
    opcionales entre corchetes). Usarlos (p. ej. `using interp`) está permitido. `extra`: nombres del objetivo."""
    try:
        toks = tokenize_outer(text)
    except ValueError:
        return []
    found = []
    for i, (kind, t) in enumerate(toks):
        if kind != "word" or not (_RESERVED.match(t) or t in extra):
            continue
        j = i + 1
        if j < len(toks) and toks[j][1] == "[":  # nombre[simp]:
            depth = 0
            while j < len(toks):
                if toks[j][1] == "[":
                    depth += 1
                elif toks[j][1] == "]":
                    depth -= 1
                    if depth == 0:
                        j += 1
                        break
                j += 1
        prev = toks[i - 1][1] if i else ""
        nxt = toks[j][1] if j < len(toks) else ""
        if prev in _LEMMA_HEADS or nxt == ":":
            found.append(t)
    return found


def _sintaxis(res: tuple[str, str] | None) -> tuple[str, str] | None:
    """Un texto que no se puede leer por una cadena o un comentario sin cerrar es un error de sintaxis, no un intento
    de salir del hueco: SYNTAX_ERROR (para no inflar la razón de deriva; 24 sep 2026)."""
    if res and res[0] == "STATEMENT_DRIFT" and "sin cerrar" in res[1]:
        return "SYNTAX_ERROR", res[1]
    return res


def check_lemma_block(text: str, extra: set[str] | frozenset = frozenset()) -> tuple[str, str] | None:
    """`check_lemmas` de verifiers.py más los nombres reservados del juez de teorema y del objetivo."""
    if "PROOF:" in text or text.lstrip().startswith(">"):
        return "INVALID_PROPOSAL", ("el bloque LEMMAS no se cerró bien: escribe LEMMAS: <<< lemma ... >>> (tres '>' al final) "
                                    "u omítelo si no tienes lemas")
    bad = _sintaxis(check_lemmas(text))
    if bad:
        return bad
    names = reserved_names(text, extra)
    if names:
        return "INVALID_PROPOSAL", f"nombre reservado en LEMMAS: {names[0]!r} (isarl*, las etiquetas de las hipótesis y las constantes del preludio son del juez)"
    return None


# ----------------------------------------------------------------------------- teorías

def fill_lines(template: str, table: dict[str, str]) -> tuple[str, dict[str, int]]:
    """Sustitución en UNA sola pasada (como `_fill`): el texto insertado nunca se vuelve a examinar, así que un
    `__CONCL__` escrito por el agente queda literal. Devuelve además la línea (1-based) donde empieza cada hueco."""
    out, pos, starts, line = [], 0, {}, 1
    for m in re.finditer(r"__([A-Z]+)__", template):
        chunk = template[pos:m.start()]
        out.append(chunk)
        line += chunk.count("\n")
        starts.setdefault(m.group(1), line)
        value = table[m.group(1)]
        out.append(value)
        line += value.count("\n")
        pos = m.end()
    out.append(template[pos:])
    return "".join(out), starts


LEMMAS_THEOREM = r'''theory Lemmas
  imports __IMPORTS__
begin

__PRELUDE__

context
  fixes __FIXES__
  assumes __ASSUMES__
begin

ML \<open>
  val isarl_axioms0 = length (Theory.all_axioms_of (Proof_Context.theory_of @{context}))
  val isarl_concl0 = @{prop \<open>__CONCL__\<close>}
\<close>

__AGENTLEMMAS__

ML \<open>
  val _ = if @{prop \<open>__CONCL__\<close>} aconv isarl_concl0 then () else error "isarl: el enunciado congelado se lee distinto"
  val _ = if length (Theory.all_axioms_of (Proof_Context.theory_of @{context})) = isarl_axioms0 then ()
          else error "isarl: los lemas añadieron axiomas"
  val _ = File.write (Path.explode "__DIR__/lemmas.ok") ""
\<close>

end

end
'''

# La del diseño, más una escritura de target.json justo después de isarl_target (prop_ok, oráculos y skip_proof de
# isarl_target): si el agente prueba OTRO enunciado, isarl_export no compila (rc ≠ 0) y sin este archivo el intento
# se confundiría con PROOF_FAILED. El ML de después de `end` no usa nada definido dentro del contexto (isarl_axioms0
# se cuenta a nivel de teoría, antes del contexto; prop_ok sale de target.json), para no depender de si los valores
# de ML de un contexto local sobreviven a su `end`.
FINAL_THEOREM = r'''theory Final
  imports __IMPORTS__
begin

__PRELUDE__

ML \<open>
  val isarl_axioms0 = length (Theory.all_axioms_of @{theory})
\<close>

context
  fixes __FIXES__
  assumes __ASSUMES__
begin

ML \<open>
  val isarl_expected = @{prop \<open>__CONCL__\<close>}
\<close>

__AGENTLEMMAS__

theorem isarl_target: "__CONCL__"
__AGENTPROOF__

ML \<open>
  val isarl_prop_ok = Thm.prop_of @{thm isarl_target} aconv isarl_expected
  val _ = File.write (Path.explode "__TARGETOUT__")
    ("{\"prop_ok\": " ^ (if isarl_prop_ok then "true" else "false")
      ^ ", \"oracles\": [" ^ String.concatWith "," (map (fn ((n, _), _) => "\"" ^ n ^ "\"") (Thm_Deps.all_oracles [@{thm isarl_target}]))
      ^ "], \"skip_proof\": " ^ (if Thm_Deps.has_skip_proof [@{thm isarl_target}] then "true" else "false") ^ "}")
\<close>

end

theorem isarl_export:
  fixes __FIXES__
  assumes __ASSUMES__
  shows "__CONCL__"
  by (rule isarl_target[where __INST__, OF assms])

ML \<open>
  val th = @{thm isarl_export}
  val oracles = Thm_Deps.all_oracles [th]
  val skip = Thm_Deps.has_skip_proof [th]
  val _ = File.write (Path.explode "__OUT__")
    ("{\"oracles\": [" ^ String.concatWith "," (map (fn ((n, _), _) => "\"" ^ n ^ "\"") oracles) ^ "], \"skip_proof\": "
      ^ (if skip then "true" else "false")
      ^ ", \"axioms_ok\": " ^ (if length (Theory.all_axioms_of @{theory}) = isarl_axioms0 then "true" else "false")
      ^ ", \"export_ok\": true"
      ^ ", \"prop\": \"" ^ String.translate (fn #"\"" => "'" | #"\\" => "/" | #"\n" => " " | c => String.str c)
          (XML.content_of (YXML.parse_body (Syntax.string_of_term @{context} (Thm.prop_of th)))) ^ "\"}")
\<close>

end
'''

_LINE_REF = re.compile(r'\(line (\d+) of "([^"]*)"\)')


def translate_errors(log: str, thy_name: str, proof_first: int | None = None, proof: str = "",
                     lemmas_first: int | None = None, lemmas: str = "", limit: int = 40) -> list[str]:
    """Líneas «***» del registro de Isabelle, con la posición traducida cuando cae en el texto del agente:
    «(línea k de tu PROOF)» o «(lema nombre, línea k)». El resto del mensaje queda literal."""
    blocks = split_lemmas(lemmas) if lemmas else []
    n_proof = proof.count("\n") + 1 if proof else 0

    def where(L: int) -> str | None:
        if proof_first is not None and n_proof and proof_first <= L < proof_first + n_proof:
            return f"línea {L - proof_first + 1} de tu PROOF"
        if lemmas_first is not None:
            rel = L - lemmas_first
            for b in blocks:
                if b["first"] <= rel <= b["last"]:
                    return f"lema {b['name']}, línea {rel - b['first'] + 1}"
        return None

    def rep(m: re.Match) -> str:
        if not re.search(rf"(^|/){re.escape(thy_name)}\.thy$", m.group(2)):
            return m.group(0)
        w = where(int(m.group(1)))
        return f"({w})" if w else m.group(0)

    out = []
    for line in log.splitlines():
        if line.startswith("***") and line[3:].strip():
            out.append(_LINE_REF.sub(rep, line))
            if len(out) >= limit:
                break
    return out


def nombres_fijos(fixes: str) -> list[str]:
    """Variables de `fixes`, en orden: los identificadores antes de cada '::' en cada grupo separado por 'and'."""
    out = []
    for grupo in re.split(r"\band\b", fixes):
        out += grupo.split("::")[0].split()
    return out


def instanciacion(spec: dict) -> str:
    """`v = v and …` para exportar isarl_target: instanciar por nombre evita la unificación de orden superior, que
    falla con hipótesis como ⋀j. |e (Suc j)| ≤ c·|e j| («OF: multiple unifiers»). Solo las variables que aparecen
    en las hipótesis o la conclusión (las demás no quedan en el teorema exportado)."""
    texto = spec.get("assumes", "") + " " + spec.get("concl", "")
    usadas = [v for v in nombres_fijos(spec.get("fixes", "")) if re.search(rf"(?<![A-Za-z0-9_'.]){re.escape(v)}(?![A-Za-z0-9_'])", texto)]
    # un nombre que termina en dígito (x0) se lee como variable con índice (x, 0): se escribe ?x0.0
    return " and ".join(f"?{v}.0 = {v}" if v[-1].isdigit() else f"{v} = {v}" for v in usadas)


def perfil_sandbox(work: Path) -> str:
    """Perfil de sandbox-exec para una compilación: sin red externa (Isabelle usa sockets locales entre Scala y
    Poly/ML) y sin escritura fuera del directorio de trabajo, ~/.isabelle (heaps y registros) y los temporales."""
    home = str(Path.home())
    return ('(version 1)(allow default)'
            '(deny network-outbound (remote ip))(allow network-outbound (remote ip "localhost:*"))'
            '(deny file-write* (require-all'
            f' (require-not (subpath "{Path(work).resolve()}"))'
            f' (require-not (subpath "{home}/.isabelle"))'
            ' (require-not (subpath "/private/tmp")) (require-not (subpath "/private/var/folders"))'
            ' (require-not (subpath "/dev"))))')


# ----------------------------------------------------------------------------- juez

class TheoremVerifier:
    """Proposal = {"proof": str, "lemmas": str (opcional), "lemmas_library": str (opcional; la memoria)};
    target = teorema congelado (targets/<nombre>.json: preludio, fixes, assumes, concl).

    Etapas: (a) filtros de PROOF y LEMMAS; (b) hash del objetivo releído de disco; (c) si hay lemas, se demuestran
    en el kernel (teoría Lemmas) y, si fallan, se recuperan los limpios para la memoria; (d) teoría Final con el
    texto del agente insertado en una sola pasada; (e) final.json. ACCEPTED solo si todo pasa.
    """

    name = "isabelle_teorema"
    LABELS = ("ACCEPTED", "PROOF_FAILED", "LEMMA_FAILED", "UNSOUND", "STATEMENT_DRIFT", "SYNTAX_ERROR", "TIMEOUT", "INVALID_PROPOSAL")
    VERSION_JUEZ = "teorema-2026-09-24"  # cambia cuando cambia algo que afecte veredictos
    SESSION_PARENT = "HOL-Analysis"
    HASH_FIELDS = ("imports", "prelude", "fixes", "assumes", "concl")

    def __init__(self, target_name: str, build_timeout_s: float = 300, expected_hash: str | None = None, cortesia: bool = True,
                 spec_path: Path | None = None, aislado: bool = True):
        """`target_name`: objetivo de targets/<nombre>.json, o, con `spec_path`, la entrada del corpus (usar
        `desde_corpus`, que exige la aprobación de Carlos). `aislado`: compilar bajo sandbox-exec (sin red, sin
        escritura fuera del directorio de trabajo, ~/.isabelle y los temporales)."""
        self.cortesia, self.espera_s = cortesia, 0.0
        self.spec_path = Path(spec_path) if spec_path else None
        self.aislado = bool(aislado) and Path("/usr/bin/sandbox-exec").exists()
        if not target_name:
            raise ValueError("falta el objetivo (target) del juez de teorema")
        self.config08 = _import_from("08_isabelle", "isarl.config")
        self.scratch = Path(self.config08.SCRATCH)
        self.build_timeout_s = float(build_timeout_s)
        self.target_name = target_name
        self.spec = self._load_spec()
        if self.spec.get("kind", "theorem") != "theorem":
            raise ValueError(f"el objetivo {target_name} no es de tipo theorem")
        if self.spec.get("session_parent", self.SESSION_PARENT) != self.SESSION_PARENT:
            raise ValueError(f"el objetivo {target_name} pide la sesión padre {self.spec['session_parent']!r}; el juez usa {self.SESSION_PARENT!r}")
        self.frozen_hash = self._hash(self.spec)
        for pinned, source in ((self.spec.get("frozen_hash"), "frozen_hash del objetivo"), (expected_hash, "target_hash de la configuración")):
            if pinned and pinned != self.frozen_hash:
                raise ValueError(f"el objetivo {target_name} no coincide con su hash fijado ({self.frozen_hash} ≠ {pinned}, {source})")
        self.pinned_hash = expected_hash or self.spec.get("frozen_hash")
        self.reservados = frozenset(nombres_del_objetivo(self.spec))

    @classmethod
    def desde_corpus(cls, id_: str, tema: str = "raices", base: Path | None = None, **kw) -> "TheoremVerifier":
        """Juez para un peldaño del corpus. Lanza corpus.NoAprobado si Carlos no lo aprobó."""
        from .corpus import CORPUS, exigir_usable
        e = exigir_usable(id_, tema, base)
        return cls(e["id"], spec_path=(base or CORPUS) / tema / f"{e['id']}.json", expected_hash=e["frozen_hash"], **kw)

    def _load_spec(self) -> dict:
        ruta = self.spec_path or (TARGETS / f"{self.target_name}.json")
        return json.loads(ruta.read_text(encoding="utf-8"))

    def metadatos(self) -> dict:
        """Lo que cada veredicto registra para ser reproducible: versión de Isabelle, límites, aislamiento y carga."""
        try:
            carga = [round(x, 2) for x in os.getloadavg()]
        except OSError:
            carga = None
        return {"isabelle": "Isabelle2025", "juez": self.VERSION_JUEZ, "limite_compilacion_s": self.build_timeout_s,
                "aislado": self.aislado, "carga_1_5_15": carga, "objetivo_hash": self.frozen_hash,
                "fecha": time.strftime("%Y-%m-%dT%H:%M:%S")}

    @classmethod
    def _hash(cls, spec: dict) -> str:
        frozen = {k: spec.get(k, "") for k in cls.HASH_FIELDS}
        return hashlib.sha256(json.dumps(frozen, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16]

    def target(self) -> dict:
        s = self.spec
        return {"id": f"isabelle_teorema:{s['name']}", "kind": "theorem", "statement_es": s["statement_es"],
                "imports": s["imports"], "prelude": s["prelude"], "fixes": s["fixes"], "assumes": s["assumes"],
                "concl": s["concl"], "borrowed_lemmas": s.get("borrowed_lemmas", []), "hash": self.frozen_hash}

    # -- compilación
    @staticmethod
    def compilaciones_ajenas() -> bool:
        """¿Hay alguna compilación de Isabelle que no sea de este juez? (p. ej. la bisección, cuyo Sledgehammer tiene
        límite de tiempo real y no debe competir por CPU)."""
        out = subprocess.run(["ps", "-ax", "-o", "command="], capture_output=True, text=True).stdout
        return any("Isabelle_Tool build" in l and "/gd-" not in l and "IsaRL_GD_" not in l for l in out.splitlines())

    def esperar_turno(self, quieto_s: float = 2.0, paso_s: float = 1.0) -> float:
        """Cortesía: antes de compilar, espera a que pasen `quieto_s` segundos seguidos sin compilaciones ajenas.
        Devuelve los segundos esperados (no cuentan en el costo del juez ni en su límite de tiempo)."""
        if not self.cortesia:
            return 0.0
        t0, libre = time.perf_counter(), 0.0
        while libre < quieto_s:
            if self.compilaciones_ajenas():
                libre = 0.0
            else:
                libre += paso_s
            time.sleep(paso_s)
        return time.perf_counter() - t0

    def build(self, work: Path, theory: str, name: str, timeout_s: float) -> tuple[int, str]:
        """Compila una teoría en una sesión con nombre único sobre HOL-Analysis y mata el árbol de procesos si se
        agota el tiempo (rc = -9). Antes espera su turno (cortesía con otras compilaciones de Isabelle)."""
        self.espera_s += self.esperar_turno()
        session = f"IsaRL_GD_{uuid.uuid4().hex[:10]}"
        (work / f"{name}.thy").write_text(theory, encoding="utf-8")
        # parallel_proofs = 0: las pruebas se comprueban en orden y el primer error detiene la teoría, así que ningún
        # marcador (lemmas.ok, target.json, final.json) se escribe tras una prueba fallida
        (work / "ROOT").write_text(f'session {session} = "{self.SESSION_PARENT}" +\n'
                                   "  options [document = false, timeout = 0, parallel_proofs = 0]\n"
                                   f"  theories\n    {name}\n", encoding="utf-8")
        cmd = [str(self.config08.ISABELLE_BIN), "build", "-o", "document=false", "-d", str(work), session]
        if self.aislado:
            cmd = ["/usr/bin/sandbox-exec", "-p", perfil_sandbox(work)] + cmd
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
        try:
            out, _ = p.communicate(timeout=timeout_s)
            return p.returncode, out
        except subprocess.TimeoutExpired:
            kill_tree([p.pid])
            kill_build_of(work)
            try:
                out, _ = p.communicate(timeout=60)
            except subprocess.TimeoutExpired:
                out = ""
            return -9, (out or "") + f"\n[unirl] TIMEOUT tras {timeout_s:.0f} s"

    def _workdir(self, prefix: str) -> Path:
        self.scratch.mkdir(parents=True, exist_ok=True)
        return Path(tempfile.mkdtemp(prefix=prefix, dir=str(self.scratch)))

    def lemmas_theory(self, lemmas: str, work: Path) -> tuple[str, int]:
        """Teoría Lemmas y línea (1-based) donde empieza el bloque de lemas."""
        s = self.spec
        thy, starts = fill_lines(LEMMAS_THEOREM, {"IMPORTS": s["imports"], "PRELUDE": s["prelude"], "FIXES": s["fixes"],
                                                  "ASSUMES": s["assumes"], "CONCL": s["concl"], "DIR": str(work),
                                                  "AGENTLEMMAS": lemmas})
        return thy, starts["AGENTLEMMAS"]

    def _lemmas_build(self, lemmas: str) -> tuple[int, str, int, Path]:
        work = self._workdir("gd-lemmas-")
        thy, first = self.lemmas_theory(lemmas, work)
        rc, log = self.build(work, thy, "Lemmas", self.build_timeout_s)
        return rc, log, first, work

    def check_lemmas_in_kernel(self, lemmas: str) -> tuple[str, list[str], list[dict]]:
        """Como `IsabelleVerifier.check_lemmas_in_kernel`: ('ok' | 'failed' | 'timeout', errores, lemas verificados).
        Si el bloque falla, los lemas sin errores en su tramo se compilan solos; si pasan, cuentan como verificados."""
        rc, log, first, work = self._lemmas_build(lemmas)
        errors = translate_errors(log, "Lemmas", lemmas_first=first, lemmas=lemmas)
        blocks = split_lemmas(lemmas)
        if rc == -9:
            return "timeout", errors, []
        if rc == 0 and (work / "lemmas.ok").exists():
            return "ok", errors, [{"name": b["name"], "text": b["text"]} for b in blocks]
        bad_lines = {int(m) - first for m in re.findall(r'\(line (\d+) of "[^"]*Lemmas\.thy"\)', log)}
        clean = [b for b in blocks if not any(b["first"] <= L <= b["last"] for L in bad_lines)]
        verified = []
        if clean and len(clean) < len(blocks):
            rc2, _, _, work2 = self._lemmas_build("\n\n".join(b["text"] for b in clean))
            if rc2 == 0 and (work2 / "lemmas.ok").exists():
                verified = [{"name": b["name"], "text": b["text"]} for b in clean]
        return "failed", errors, verified

    def final_theory(self, proof: str, lemmas: str, out: Path, target_out: Path) -> tuple[str, dict[str, int]]:
        """Ensamblado de la teoría Final en una sola pasada; el texto del agente no se vuelve a examinar."""
        s = self.spec
        return fill_lines(FINAL_THEOREM, {"IMPORTS": s["imports"], "PRELUDE": s["prelude"], "FIXES": s["fixes"],
                                          "ASSUMES": s["assumes"], "CONCL": s["concl"], "OUT": str(out), "INST": instanciacion(s),
                                          "TARGETOUT": str(target_out), "AGENTLEMMAS": lemmas, "AGENTPROOF": proof})

    def compile_final(self, proof: str, lemmas: str = "", work: Path | None = None) -> dict:
        """Compila la teoría Final SIN pasar por los filtros (lo usa `verify` tras filtrarlos, y los controles de la
        validación para comprobar el kernel). Devuelve {rc, errors, cheating, final_json, target, …final.json}."""
        work = Path(work) if work else self._workdir("gd-final-")
        work.mkdir(parents=True, exist_ok=True)
        out, tout = work / "final.json", work / "target.json"
        thy, starts = self.final_theory(proof, lemmas, out, tout)
        t = time.perf_counter()
        rc, log = self.build(work, thy, "Final", self.build_timeout_s)
        fin = {"rc": rc, "build_s": round(time.perf_counter() - t, 1),
               "errors": translate_errors(log, "Final", starts["AGENTPROOF"], proof, starts["AGENTLEMMAS"], lemmas),
               # sorry en una compilación por lotes: Isabelle lo rechaza sin quick_and_dirty (Method.cheating)
               "cheating": "Cheating requires quick_and_dirty mode" in log, "final_json": False, "work": str(work)}
        if out.exists():
            try:
                fin.update(json.loads(out.read_text(encoding="utf-8")))
                fin["final_json"] = True
            except ValueError as e:
                fin["final_json_error"] = str(e)[:200]
        if tout.exists():
            try:
                fin["target"] = json.loads(tout.read_text(encoding="utf-8"))
            except ValueError as e:
                fin["target"] = {"error": str(e)[:200]}
        return fin

    @staticmethod
    def classify(fin: dict) -> tuple[str, str]:
        """(etiqueta, motivo) a partir de lo que dejó la compilación de la teoría Final."""
        if fin["rc"] == -9:
            return "TIMEOUT", "la compilación de la teoría final superó el límite de tiempo"
        tgt = fin.get("target") or {}
        if fin["rc"] != 0:
            if fin.get("cheating"):
                return "UNSOUND", "la demostración usa sorry (Isabelle lo rechaza fuera de quick_and_dirty)"
            if tgt.get("oracles") or tgt.get("skip_proof"):
                return "UNSOUND", f"isarl_target depende de oráculos: {tgt.get('oracles')}"
            if tgt and not tgt.get("prop_ok", False):
                return "STATEMENT_DRIFT", "el teorema demostrado no es, término a término, el enunciado congelado"
            return "PROOF_FAILED", "Isabelle rechazó la demostración"
        if not fin.get("final_json"):
            return "STATEMENT_DRIFT", "la compilación terminó sin escribir final.json: la exportación no llegó al final"
        fin["prop_ok"] = bool(tgt.get("prop_ok", False))  # se lee dentro del contexto (target.json)
        if fin.get("oracles") or fin.get("skip_proof") or not fin.get("axioms_ok", False):
            return "UNSOUND", (f"oráculos {fin.get('oracles')}, skip_proof = {fin.get('skip_proof')}, "
                               f"axiomas sin cambios = {fin.get('axioms_ok')}")
        if not fin.get("prop_ok", False) or not fin.get("export_ok", False):
            return "STATEMENT_DRIFT", "el teorema demostrado no es, término a término, el enunciado congelado"
        return "ACCEPTED", "el kernel aceptó el enunciado congelado sin oráculos ni axiomas nuevos"

    # -- interfaz Verifier
    def verify(self, target: dict, proposal: dict) -> Outcome:
        t0 = time.perf_counter()
        self.espera_s = 0.0
        p = proposal if isinstance(proposal, dict) else {}
        proof = str(p.get("proof") or "").strip()
        lemmas = merge_lemmas(str(p.get("lemmas_library") or ""), str(p.get("lemmas") or "")).strip()
        n_lemmas = len(re.findall(r"(?m)^\s*(?:lemma|corollary|theorem|proposition)\b", lemmas))
        base = {"kind": "theorem", "stage": "filtro", "errors": [], "n_lemmas": n_lemmas, "verified_lemmas": [],
                "final": None, "build_s": 0.0, "proof_chars": len(proof)}

        def done(label: str, **kw) -> Outcome:
            ok = label == "ACCEPTED"
            espera = round(self.espera_s, 1)  # turno esperado por cortesía: no es costo del juez
            return Outcome(ok, label, 1.0 if ok else 0.0, time.perf_counter() - t0 - espera,
                           {**base, **kw, "espera_s": espera, "veredicto": self.metadatos()})

        # (a) filtros; (b) hash. La deriva se detecta antes que cualquier otra cosa, para que cuente en todos los intentos.
        checks = [("PROOF", check_proof(proof))] + ([("LEMMAS", check_lemma_block(lemmas, self.reservados))] if lemmas else [])
        for block, bad in checks:
            if bad and bad[0] == "STATEMENT_DRIFT":
                return done("STATEMENT_DRIFT", reason=bad[1], block=block)
        try:
            disk_hash = self._hash(self._load_spec())
        except (OSError, ValueError):
            disk_hash = None
        if disk_hash != self.frozen_hash or (target or {}).get("hash") != self.frozen_hash:
            return done("STATEMENT_DRIFT", stage="hash", reason="el objetivo congelado cambió en disco")
        for wanted in ("UNSOUND", "SYNTAX_ERROR", "INVALID_PROPOSAL"):
            for block, bad in checks:
                if bad and bad[0] == wanted:
                    return done(wanted, reason=bad[1], block=block)
        # (c) lemas en el kernel
        build_s, verified = 0.0, []
        if lemmas:
            tb = time.perf_counter()
            st, lerrs, verified = self.check_lemmas_in_kernel(lemmas)
            build_s += time.perf_counter() - tb
            if st == "timeout":
                return done("TIMEOUT", stage="lemas", errors=lerrs, build_s=round(build_s, 1),
                            reason=f"la compilación de los lemas superó {self.build_timeout_s:.0f} s")
            if st == "failed":
                return done("LEMMA_FAILED", stage="lemas", errors=lerrs, verified_lemmas=verified, build_s=round(build_s, 1),
                            reason="Isabelle rechazó los lemas")
        # (d) teoría Final; (e) final.json
        fin = self.compile_final(proof, lemmas)
        build_s += fin["build_s"]
        label, reason = self.classify(fin)
        return done(label, stage="final", errors=fin["errors"], final=fin, build_s=round(build_s, 1), reason=reason,
                    verified_lemmas=verified if label in ("ACCEPTED", "PROOF_FAILED") else [])

    def describe(self, target: dict) -> str:
        todo_n = bool(re.search(r"\bn\s*::\s*nat\b", target["fixes"]))
        lines = [
            f"TEOREMA ({target['id']}): {target['statement_es']}",
            "",
            "Teoría: imports \"HOL-Analysis.Inner_Product\" (sobre Complex_Main: números reales, espacios reales con",
            "producto interno, inner, norm, listas). Puedes usar cualquier resultado de esa biblioteca.",
            "",
            "Preludio congelado (antes del contexto; define la iteración del descenso de gradiente):",
            target["prelude"],
            "",
            "Contexto congelado:",
            f"  fixes {target['fixes']}",
            f"  assumes {target['assumes']}",
            "",
            "Qué dicen las hipótesis (L = 1):",
            "  - interp: la desigualdad para TODO par x, y caracteriza exactamente a las funciones f convexas y 1-suaves",
            "    (gradiente 1-Lipschitz) cuyo gradiente es g.",
            "  - opt: g xs = 0, es decir, xs es estacionario; por convexidad, xs minimiza f.",
            "  - gd g hs x aplica x_{k+1} = x_k - h_k * g(x_k) con los pasos de la lista hs, en orden.",
        ]
        if todo_n:
            lines.append("  - n :: nat está fija en el contexto (el enunciado vale para cada n).")
        lines += [
            "",
            "Enunciado a demostrar, dentro de ese contexto:",
            f"  theorem isarl_target: \"{target['concl']}\"",
            "",
            "PROOF (obligatorio) es el texto que va justo después de esa línea: `by ...`, `using ... by ...`,",
            "`unfolding ... by ...`, `apply ... done` o `proof - ... qed`. Puedes citar las hipótesis por su nombre (interp, opt).",
            "LEMMAS (opcional): lemas auxiliares `lemma nombre: \"...\"` (o con fixes/assumes/shows) seguidos de su prueba",
            "completa. Se demuestran en el mismo contexto, antes del teorema (pueden usar interp y opt; f, g, x0, xs"
            + (" y n" if todo_n else "") + " son las",
            "fijas; otras variables libres quedan cuantificadas). Isabelle comprueba cada prueba antes que el teorema: si",
            "alguna falla, el intento es LEMMA_FAILED y verás los errores; los lemas verificados se conservan en la memoria.",
            "",
            "Reglas (un filtro las comprueba antes de compilar):",
            "  - sin sorry ni oops; sin definiciones, notación, declare, ML, métodos que ejecutan ML (tactic, eval) ni [[ ]];",
            "  - sin cartuchos (\\<open>...\\<close>, ‹...›) ni comillas invertidas: nombra los hechos (have h1: \"...\") y",
            "    cítalos por su nombre;",
            "  - PROOF solo contiene comandos de prueba (nada de lemma/theorem: los auxiliares van en LEMMAS);",
            "  - nombres reservados, que tus lemas no pueden declarar: isarl*, interp, opt, gd;",
            f"  - como mucho {PROOF_MAX_CHARS} caracteres por bloque; símbolos en ASCII de Isabelle (\\<le>, \\<Rightarrow>,",
            "    \\<^sup>2, *\\<^sub>R, \\<And>, \\<Longrightarrow>).",
            f"El juez solo compila (no hay Sledgehammer); cada compilación tiene un límite de {self.build_timeout_s:.0f} s.",
            "",
            "Responde exactamente así (LEMMAS es opcional):",
            "LEMMAS: <<< lemma ... >>>",
            "PROOF: <<< ... >>>",
        ]
        return "\n".join(lines)

    def parse(self, text: str) -> dict:
        # \b: no confundir con otra palabra que termine igual. (?!>): el cierre es el ÚLTIMO de una racha de '>',
        # porque el texto puede terminar en un símbolo como \<rceil> pegado al cierre: "\<rceil>>>>".
        text = text or ""
        proof = re.search(r"\bPROOF:\s*<<<(.*?)>>>(?!>)", text, re.S)
        # Los bloques no se solapan: LEMMAS se busca en el texto SIN el bloque PROOF. Así un LEMMAS mal cerrado
        # («LEMMAS: <<<>>») no se come la demostración (24 sep 2026, 06:50: le pasó a Luna en gd_n1, ep. 1, paso 1).
        resto = text[:proof.start()] + text[proof.end():] if proof else text
        lem = re.search(r"\bLEMMAS:\s*<<<(.*?)>>>(?!>)", resto, re.S)
        return {"proof": IsabelleVerifier._close_symbol((proof.group(1) if proof else "").strip()),
                "lemmas": IsabelleVerifier._close_symbol((lem.group(1) if lem else "").strip())}

    def feedback(self, proposal: dict, outcome: Outcome) -> str:
        r = outcome.raw or {}
        label = outcome.outcome_label
        errs = r.get("errors") or []
        if label == "PROOF_FAILED":
            return ("PROOF_FAILED: Isabelle rechazó la demostración (errores literales):\n"
                    + ("\n".join(errs[:12]) if errs else "(Isabelle no dio mensajes de error)"))
        if label == "LEMMA_FAILED":
            s = ("LEMMA_FAILED: Isabelle rechazó los lemas (errores literales):\n"
                 + ("\n".join(errs[:12]) if errs else "(Isabelle no dio mensajes de error)"))
            if r.get("verified_lemmas"):
                s += "\nLemas sin errores que Isabelle sí verificó: " + ", ".join(v["name"] for v in r["verified_lemmas"])
            return s
        if label == "TIMEOUT":
            return f"TIMEOUT: {r.get('reason', '')}" + (" | " + " | ".join(errs[:5]) if errs else "")
        return f"{label}: {r.get('reason', '')}"
