"""Etapa 3 de PLAN_rl_verbal.md: martillo (try0 + Sledgehammer) con caché, consulta de teoremas y glosario.

* `martillo_solo(juez)`: try0 (5 s) y, si no cierra, Sledgehammer (60 s) sobre la meta del peldaño en su contexto.
  Si encuentra una línea, el juez la verifica en el kernel; si es ACCEPTED, el peldaño está `resuelto_por_martillo`
  y no da crédito. Caché SQLite por (enunciado, cuaderno, límites, demostradores, versión de Isabelle).
* `martillo_en_pasos(juez, prueba)`: la prueba del agente marca pasos con `by martillo`; una pasada con un método
  auxiliar busca, para cada uno, una línea (caché, try0 o Sledgehammer) y la registra (esa pasada usa
  quick_and_dirty solo para seguir tras cada marca); después se sustituyen las líneas y el juez compila la prueba
  completa sin atajos. Nada entra como demostrado sin el kernel.
* `consultar(juez, consultas)`: búsqueda de teoremas (`find_theorems`) y existencia de hechos o métodos, en el mismo
  contexto que el juez. Las consultas se leen como DATOS desde un archivo, nunca como código.
* `verificar_glosario()`: comprueba mecánicamente el glosario Lean→Isabelle de cuaderno/glosario.json.
Todas las llamadas al martillo se hacen en serie: su límite es de tiempo real.
"""

from __future__ import annotations

import contextlib
import fcntl
import hashlib
import json
import re
import sqlite3
import threading
import time
from pathlib import Path

from .gd_isabelle import TheoremVerifier, check_lemma_block, check_proof, fill_lines, nombres_del_objetivo, translate_errors
from .verifiers import _PREPLAYED, _PROVER, merge_lemmas, tokenize_outer

BASE = Path(__file__).resolve().parent.parent
CACHE = BASE / "logs" / "martillo_cache.sqlite"
ISABELLE = "Isabelle2025"
CANDADO = BASE / "logs" / "martillo.lock"
SH_TIMEOUT, TRY0_TIMEOUT = 60, 5


@contextlib.contextmanager
def candado_martillo():
    """El martillo corre en serie aunque haya episodios en paralelo (su límite es de tiempo real): candado de archivo
    compartido por todos los procesos. Devuelve los segundos esperados."""
    CANDADO.parent.mkdir(parents=True, exist_ok=True)
    with open(CANDADO, "w") as fh:
        t = time.monotonic()
        fcntl.flock(fh, fcntl.LOCK_EX)
        try:
            yield time.monotonic() - t
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)
# Si el Mac se suspende, el reloj de pared (el que usan los límites de Sledgehammer) avanza y el monótono no: un
# «timeout» así no es de Sledgehammer. Más de SUSPENSION_S de diferencia invalida el resultado (no se guarda).
SUSPENSION_S = 5.0


class Reloj:
    """Mide a la vez el tiempo monótono (sin suspensión en macOS) y el de pared; la diferencia es tiempo suspendido."""

    def __init__(self):
        self.m0, self.p0 = time.monotonic(), time.time()

    def ms(self) -> int:
        return round((time.monotonic() - self.m0) * 1000)

    def suspension_s(self) -> float:
        return round(max(0.0, (time.time() - self.p0) - (time.monotonic() - self.m0)), 1)
MAX_CONSULTAS_POR_LOTE = 4
MAX_RESULTADOS = 20

# ----------------------------------------------------------------------------------------------- ML común

ML_COMUN = r'''
  fun esc s =
    String.translate (fn #"\"" => "\\\"" | #"\\" => "\\\\" | #"\n" => "\\n" | #"\t" => "\\t"
                        | c => if Char.ord c < 32 then " " else String.str c) s
  fun jstr s = "\"" ^ esc s ^ "\""
  fun jlist xs = "[" ^ String.concatWith "," xs ^ "]"
  fun jobj kvs = "{" ^ String.concatWith "," (map (fn (k, v) => jstr k ^ ":" ^ v) kvs) ^ "}"
  fun jbool b = if b then "true" else "false"
  fun ms t = Int.toString (Time.toMilliseconds t)
  fun plain s = XML.content_of (YXML.parse_body s)
  val isarl_etiquetas = [__ETIQUETAS__] : string list

  fun apply_method_text txt st =
    let val (text, _) = Method.read_closure_input (Proof.context_of st) (Input.string txt)
    in case Seq.pull (Proof.apply (text, Position.no_range) st) of
         SOME (Seq.Result st', _) => SOME st'
       | _ => NONE
    end
  fun cierra txt st =
    (case Exn.result (fn () => apply_method_text txt st) () of
       Exn.Res (SOME st') => Thm.no_prems (#goal (Proof.goal st'))
     | _ => false)

  fun run_try0 st =
    case Exn.result (fn () =>
      let
        val t = SOME (seconds (Real.fromInt __TRYCERO__))
        val res = Try0.try0 t [] st
        val res2 = if null res then Try0.try0 t (map (fn l => ((Facts.named l, []), [Try0.Use])) isarl_etiquetas) st else []
      in res @ res2 end) () of
      Exn.Res [] => NONE
    | Exn.Res ({command, time, ...} :: _) => SOME (command, time)
    | Exn.Exn _ => NONE

  fun run_sh st =
    let
      val thy = Proof.theory_of st
      val msgs = Unsynchronized.ref ([] : string list)
      val params = Sledgehammer_Commands.default_params thy
        [("timeout", Int.toString __SH__), ("verbose", "false"), ("isar_proofs", "false")]
      val timer = Timing.start ()
      val r = Exn.result (fn () =>
        Sledgehammer.run_sledgehammer params Sledgehammer_Prover.Normal
          (SOME (fn s => msgs := s :: !msgs)) 1 Sledgehammer_Fact.no_fact_override st) ()
      val elapsed = #elapsed (Timing.result timer)
    in
      case r of
        Exn.Res (found, (outcome, msg)) =>
          (found, Sledgehammer.short_string_of_sledgehammer_outcome outcome, plain msg, map plain (rev (!msgs)), elapsed)
      | Exn.Exn exn => (false, "exception", plain (Runtime.exn_message exn), [], elapsed)
    end

  (* try0 y, si no cierra, Sledgehammer: el JSON de un intento del martillo sobre un estado de prueba *)
  fun martillar st =
    case run_try0 st of
      SOME (cmd, t) => jobj [("fuente", jstr "try0"), ("linea", jstr cmd), ("ms", Int.toString t)]
    | NONE =>
        let val (found, outcome, msg, msgs, t) = run_sh st
        in jobj [("fuente", jstr "sledgehammer"), ("encontrado", jbool found), ("resultado", jstr outcome),
                 ("mensaje", jstr msg), ("mensajes", jlist (map jstr msgs)), ("ms", ms t)] end
'''

TEORIA_SOLO = r'''theory Martillo
  imports __IMPORTS__
begin

__PRELUDE__

context
  fixes __FIXES__
  assumes __ASSUMES__
begin

__AGENTLEMMAS__

ML \<open>
local
''' + ML_COMUN + r'''
  val ctxt = @{context}
  val concl = @{prop \<open>__CONCL__\<close>}
  val st0 = Proof.theorem NONE (K I) [[(concl, [])]] ctxt
  val res = martillar st0
  val provers = plain (Sledgehammer_Commands.default_params (Proof_Context.theory_of ctxt) [] |> #provers |> String.concatWith " ")
in
  val _ = File.write (Path.explode "__OUT__") (jobj [("resultado", res), ("provers", jstr provers)])
end
\<close>

end

end
'''

# Pasada 1 de martillo_en_pasos: el método `martillo k` busca una línea para su meta y la registra; sigue con
# cheat_tac (la sesión de esta pasada usa quick_and_dirty; la pasada 2 compila sin atajos con el juez).
TEORIA_PASOS = r'''theory MartilloPasos
  imports __IMPORTS__
begin

__PRELUDE__

ML \<open>
''' + ML_COMUN + r'''
  (* caché de pasos: archivo de datos (meta US método US línea RS ...), leído en ejecución, nunca pegado como código ML *)
  val isarl_cache =
    map (fn r => case String.fields (fn c => Char.ord c = 31) r of [m, met, l] => (m, (met, l)) | _ => ("", ("", "")))
      (String.tokens (fn c => Char.ord c = 30) (File.read (Path.explode "__CACHEIN__")))
  val isarl_pasos = Unsynchronized.ref ([] : string list)
  (* Isabelle evalúa el método primero sobre un estado ficticio `TERM _` (cierre del contexto), sin subobjetivos:
     ahí hay que fallar en silencio, sin martillar ni registrar nada *)
  fun isarl_martillo k ctxt i st = if Thm.nprems_of st < i then Seq.empty else
    let
      val goal = Logic.get_goal (Thm.prop_of st) i
      val texto = plain (Syntax.string_of_term ctxt goal)
      val pst = Proof.theorem NONE (K I) [[(goal, [])]] ctxt
      val res =
        case AList.lookup (op =) isarl_cache texto of
          SOME (met, l) => if cierra met pst then jobj [("fuente", jstr "cache"), ("linea", jstr l), ("ms", "0")] else martillar pst
        | NONE => martillar pst
      val _ = isarl_pasos := jobj [("k", Int.toString k), ("meta", jstr texto), ("resultado", res)] :: !isarl_pasos
    in Skip_Proof.cheat_tac ctxt i st end
\<close>

method_setup martillo = \<open>Scan.lift Parse.nat >> (fn k => fn ctxt => SIMPLE_METHOD' (fn i => fn st => isarl_martillo k ctxt i st))\<close>

context
  fixes __FIXES__
  assumes __ASSUMES__
begin

__AGENTLEMMAS__

theorem isarl_target: "__CONCL__"
__AGENTPROOF__

end

ML \<open>File.write (Path.explode "__OUT__") (jlist (rev (!isarl_pasos)))\<close>

end
'''

TEORIA_CONSULTA = r'''theory Consulta
  imports __IMPORTS__
begin

__PRELUDE__

context
  fixes __FIXES__
  assumes __ASSUMES__
begin

__AGENTLEMMAS__

ML \<open>
local
''' + ML_COMUN + r'''
  val ctxt = @{context}
  (* cada línea del archivo: tipo TAB texto; el texto es un DATO, no código *)
  val lineas = filter (fn l => l <> "") (split_lines (File.read (Path.explode "__IN__")))
  fun una l =
    let val (tipo, texto) = case String.fields (fn c => c = #"\t") l of [a, b] => (a, b) | _ => ("?", l)
    in
      if tipo = "buscar" then
        (case Exn.result (fn () =>
            let val crit = Find_Theorems.read_query Position.none texto
                val (total, ths) = Find_Theorems.find_theorems_cmd ctxt NONE (SOME __LIMITE__) true crit
            in jobj [("tipo", jstr tipo), ("consulta", jstr texto),
                     ("total", case total of SOME n => Int.toString n | NONE => "null"),
                     ("resultados", jlist (map (fn (nm, th) => jobj [("nombre", jstr (Thm_Name.print nm)),
                        ("enunciado", jstr (plain (Syntax.string_of_term ctxt (Thm.prop_of th))))]) ths))] end) () of
           Exn.Res j => j
         | Exn.Exn e => jobj [("tipo", jstr tipo), ("consulta", jstr texto), ("error", jstr (plain (Runtime.exn_message e)))])
      else if tipo = "hecho" then
        (case Exn.result (fn () => Proof_Context.get_fact ctxt (Facts.named texto)) () of
           Exn.Res ths => jobj [("tipo", jstr tipo), ("consulta", jstr texto), ("existe", "true"),
                                ("enunciado", jlist (map (fn th => jstr (plain (Syntax.string_of_term ctxt (Thm.prop_of th)))) (take 3 ths)))]
         | Exn.Exn _ => jobj [("tipo", jstr tipo), ("consulta", jstr texto), ("existe", "false")])
      else if tipo = "metodo" then
        (case Exn.result (fn () => Method.check_name ctxt (texto, Position.none)) () of
           Exn.Res _ => jobj [("tipo", jstr tipo), ("consulta", jstr texto), ("existe", "true")]
         | Exn.Exn _ => jobj [("tipo", jstr tipo), ("consulta", jstr texto), ("existe", "false")])
      else jobj [("tipo", jstr tipo), ("consulta", jstr texto), ("error", jstr "tipo de consulta desconocido")]
    end
in
  val _ = File.write (Path.explode "__OUT__") (jlist (map una lineas))
end
\<close>

end

end
'''

# ----------------------------------------------------------------------------------------------- caché


def _ml_str(s: str) -> str:
    """Literal de cadena ML para identificadores (etiquetas de hipótesis); los símbolos \\<...> de Isabelle van tal cual."""
    return '"' + re.sub(r"\\(?!<)", r"\\\\", s).replace('"', '\\"').replace("\n", "\\n") + '"'


class Cache:
    """Caché SQLite del martillo. `evaluar` lo crea en el hilo principal y lo usan los episodios desde hilos
    trabajadores (25 sep: con la conexión por defecto, atada a su hilo, cada episodio con `by martillo` moría con
    sqlite3.ProgrammingError). La conexión se comparte entre hilos bajo un candado, y SQLite coordina los procesos
    que comparten el archivo."""

    def __init__(self, ruta: Path = CACHE):
        ruta.parent.mkdir(parents=True, exist_ok=True)
        self._candado = threading.Lock()
        self.db = sqlite3.connect(str(ruta), check_same_thread=False, timeout=60)
        with self._candado:
            self.db.execute("create table if not exists martillo (clave text primary key, tipo text, resultado text, fecha text)")

    @staticmethod
    def clave(*partes: str) -> str:
        return hashlib.sha256("\x1f".join(partes).encode()).hexdigest()

    def leer(self, clave: str) -> dict | None:
        with self._candado:
            r = self.db.execute("select resultado from martillo where clave = ?", (clave,)).fetchone()
        return json.loads(r[0]) if r else None

    def guardar(self, clave: str, tipo: str, resultado: dict) -> None:
        with self._candado:
            self.db.execute("insert or replace into martillo values (?, ?, ?, ?)",
                            (clave, tipo, json.dumps(resultado, ensure_ascii=False), time.strftime("%Y-%m-%dT%H:%M:%S")))
            self.db.commit()

    def lineas_de(self, prefijo: str) -> list[tuple[str, str]]:
        """(meta, línea) guardadas para un contexto (enunciado + cuaderno), para ofrecerlas al método `martillo`."""
        with self._candado:
            filas = self.db.execute("select resultado from martillo where tipo = 'paso'").fetchall()
        out = []
        for (res,) in filas:
            d = json.loads(res)
            if d.get("contexto") == prefijo and d.get("linea"):
                out.append((d["meta"], d["linea"]))
        return out


def linea_de(resultado: dict) -> str | None:
    """Línea de una prueba de una línea: la de try0, o la sugerida por Sledgehammer con preplay terminado."""
    if resultado.get("fuente") in ("try0", "cache"):
        return resultado.get("linea")
    if resultado.get("encontrado"):
        m = _PREPLAYED.search(resultado.get("mensaje") or "")
        if m:
            return m.group(1).strip()
    return None


_LINEA = re.compile(r"^\s*(?:using\s+(?P<hechos>.+?)\s+)?by\s+(?P<metodo>.+?)\s*$", re.S)


def metodo_de_linea(linea: str) -> str | None:
    """`by M` → `M`; `using F by M` → `(use F in M)`: el texto de método que aplica la línea a un estado ya abierto."""
    m = _LINEA.match(linea or "")
    if not m:
        return None
    return f"(use {m['hechos']} in {m['metodo']})" if m["hechos"] else m["metodo"]


def _tabla(juez: TheoremVerifier, lemas: str = "") -> dict:
    s = juez.spec
    return {"IMPORTS": s["imports"], "PRELUDE": s["prelude"], "FIXES": s["fixes"], "ASSUMES": s["assumes"], "CONCL": s["concl"],
            "AGENTLEMMAS": lemas,
            "ETIQUETAS": ", ".join(_ml_str(e) for e in sorted(nombres_del_objetivo({"assumes": s["assumes"]}))),
            "SH": str(SH_TIMEOUT), "TRYCERO": str(TRY0_TIMEOUT), "LIMITE": str(MAX_RESULTADOS)}


def _contexto(juez: TheoremVerifier, cuaderno_hash: str) -> str:
    return "|".join([juez.frozen_hash, cuaderno_hash or "sin-cuaderno", str(SH_TIMEOUT), str(TRY0_TIMEOUT), ISABELLE])


# ----------------------------------------------------------------------------------------------- martillo solo


def martillo_solo(juez: TheoremVerifier, cuaderno_hash: str = "", cache: Cache | None = None, usar_cache: bool = True,
                  biblioteca: str = "") -> dict:
    """{resuelto_por_martillo, linea, fuente, veredicto_juez, ms, desde_cache, provers}. En serie; con caché.
    `biblioteca`: los lemas del cuaderno para este peldaño (su hash va en `cuaderno_hash`, que entra en la clave)."""
    cache = cache or Cache()
    clave = Cache.clave("solo", _contexto(juez, cuaderno_hash))
    if usar_cache and (c := cache.leer(clave)) is not None:
        return {**c, "desde_cache": True}
    w = juez._workdir("gd-martillo-")
    out = w / "martillo.json"
    thy, _ = fill_lines(TEORIA_SOLO, {**_tabla(juez, biblioteca), "OUT": str(out)})
    with candado_martillo() as espera:
        reloj = Reloj()
        rc, log = juez.build(w, thy, "Martillo", SH_TIMEOUT * 4 + 120)
        suspension = reloj.suspension_s()
    d = json.loads(out.read_text()) if out.exists() else {"resultado": {"fuente": "error", "mensaje": "\n".join(
        l for l in log.splitlines() if l.startswith("***"))[:1000]}, "provers": ""}
    res = d["resultado"]
    linea = linea_de(res)
    veredicto = None
    if linea:  # nada cuenta sin el kernel: la línea se compila con el juez (aislado, con todos sus filtros)
        veredicto = juez.verify(juez.target(), {"proof": linea, "lemmas_library": biblioteca}).outcome_label
    r = {"resuelto_por_martillo": veredicto == "ACCEPTED", "linea": linea, "fuente": res.get("fuente"),
         "resultado_sh": res.get("resultado"), "veredicto_juez": veredicto, "ms": reloj.ms(),
         "sh_ms_pared": int(res["ms"]) if str(res.get("ms", "")).isdigit() else None, "suspension_s": suspension,
         "espera_candado_s": round(espera, 1),
         "provers": d.get("provers"), "rc": rc, "cuaderno": cuaderno_hash or "sin-cuaderno", "fecha": time.strftime("%Y-%m-%dT%H:%M:%S"),
         "veredicto_meta": juez.metadatos()}
    # no se guardan (y se reintentan) los fallos de infraestructura: sin JSON, o con la máquina suspendida durante la
    # búsqueda sin haber encontrado nada (una línea encontrada sí vale: el juez la verificó)
    invalido = res.get("fuente") == "error" or (suspension > SUSPENSION_S and not r["resuelto_por_martillo"])
    r["invalido"] = invalido
    if not invalido:
        cache.guardar(clave, "solo", r)
    return {**r, "desde_cache": False}


# ----------------------------------------------------------------------------------------------- martillo en pasos

_MARCA = re.compile(r"\bby\s+martillo\b")


def marcar_pasos(prueba: str) -> tuple[str, int]:
    """Numera las marcas `by martillo` → `by (martillo k)`. Devuelve (texto, número de marcas)."""
    k = 0

    def rep(_m):
        nonlocal k
        k += 1
        return f"by (martillo {k})"
    return _MARCA.sub(rep, prueba), k


def martillo_en_pasos(juez: TheoremVerifier, prueba: str, cuaderno_hash: str = "", cache: Cache | None = None,
                      lemas: str = "", biblioteca: str = "") -> dict:
    """{marcas, cerradas, fraccion, pasos, prueba_final, outcome, veredicto_juez, errores, ...}.

    Sin marcas `by martillo`, el juez compila la prueba tal cual. Con marcas: los filtros del juez se aplican ANTES de la
    pasada 1 (que corre con quick_and_dirty: sin ellos entraría un sorry o ML del agente); la pasada 1 busca una línea
    para cada marca (caché, try0 o Sledgehammer), en serie con el candado; si todas cierran, la pasada 2 es el juez con
    las líneas pegadas. Si alguna no cierra, no hay pasada 2: el intento es PROOF_FAILED con los errores de la pasada 1
    traducidos a líneas de la PROOF del agente. `lemas`: los del agente; `biblioteca`: los del cuaderno."""
    cache = cache or Cache()
    propuesta = {"lemmas": lemas, "lemmas_library": biblioteca}
    marcada, n = marcar_pasos(prueba)
    base = {"marcas": n, "cerradas": 0, "fraccion": None, "pasos": [], "prueba_final": prueba, "suspension_s": 0.0,
            "espera_candado_s": 0.0, "martillo_s": 0.0, "errores": []}
    todos = merge_lemmas(biblioteca, lemas).strip()
    filtros = check_proof(marcada) or (check_lemma_block(todos, juez.reservados) if todos else None)
    if n == 0 or filtros:
        o = juez.verify(juez.target(), {"proof": prueba, **propuesta})
        return {**base, "outcome": o, "veredicto_juez": o.outcome_label}
    ctx = _contexto(juez, cuaderno_hash)
    conocidas = cache.lineas_de(ctx)
    w = juez._workdir("gd-pasos-")
    out = w / "pasos.json"
    filas = [(m, metodo_de_linea(l), l) for m, l in conocidas]
    (w / "cache_pasos.txt").write_text("\x1e".join("\x1f".join(f) for f in filas
                                                    if f[1] and not re.search("[\x1e\x1f]", "".join(f))), encoding="utf-8")
    tabla = {**_tabla(juez, todos), "OUT": str(out), "AGENTPROOF": marcada, "CACHEIN": str(w / "cache_pasos.txt")}
    thy, starts = fill_lines(TEORIA_PASOS, tabla)
    with candado_martillo() as espera:
        reloj = Reloj()
        rc, log = _build_quick(juez, w, thy, "MartilloPasos", (SH_TIMEOUT + TRY0_TIMEOUT) * n + 180)
        suspension, martillo_s = reloj.suspension_s(), reloj.ms() / 1000
    pasos = json.loads(out.read_text()) if out.exists() else []
    lineas = {}
    for p in pasos:
        lin = linea_de(p["resultado"])
        p["linea"] = lin
        if lin:
            lineas[int(p["k"])] = lin
            cache.guardar(Cache.clave("paso", ctx, p["meta"]), "paso", {"contexto": ctx, "meta": p["meta"], "linea": lin})
    final = re.sub(r"by \(martillo (\d+)\)", lambda m: lineas.get(int(m.group(1)), m.group(0)), marcada)
    errores = translate_errors(log, "MartilloPasos", starts["AGENTPROOF"], marcada, starts["AGENTLEMMAS"], todos)
    res = {**base, "cerradas": len(lineas), "fraccion": len(lineas) / n, "pasos": pasos, "prueba_final": final,
           "rc_pasada1": rc, "suspension_s": suspension, "espera_candado_s": round(espera, 1),
           "martillo_s": round(martillo_s, 1), "errores": errores, "errores_pasada1": errores[:8]}
    if len(lineas) == n and rc == 0:
        o = juez.verify(juez.target(), {"proof": final, **propuesta})
        return {**res, "outcome": o, "veredicto_juez": o.outcome_label}
    abiertas = sorted(set(range(1, n + 1)) - set(lineas))
    return {**res, "outcome": None, "veredicto_juez": "PROOF_FAILED", "marcas_abiertas": abiertas}


def _build_quick(juez: TheoremVerifier, work: Path, thy: str, nombre: str, timeout_s: float) -> tuple[int, str]:
    """Como juez.build pero con quick_and_dirty (solo para la pasada 1 de martillo_en_pasos)."""
    import subprocess
    import uuid
    from .gd_isabelle import kill_build_of, kill_tree, perfil_sandbox
    juez.espera_s += juez.esperar_turno()
    sesion = f"IsaRL_GD_{uuid.uuid4().hex[:10]}"
    (work / f"{nombre}.thy").write_text(thy, encoding="utf-8")
    (work / "ROOT").write_text(f'session {sesion} = "{juez.SESSION_PARENT}" +\n'
                               "  options [document = false, timeout = 0, parallel_proofs = 0, quick_and_dirty = true]\n"
                               f"  theories\n    {nombre}\n", encoding="utf-8")
    cmd = [str(juez.config08.ISABELLE_BIN), "build", "-o", "document=false", "-d", str(work), sesion]
    if juez.aislado:
        cmd = ["/usr/bin/sandbox-exec", "-p", perfil_sandbox(work)] + cmd
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
    try:
        out, _ = p.communicate(timeout=timeout_s)
        return p.returncode, out
    except subprocess.TimeoutExpired:
        kill_tree([p.pid]); kill_build_of(work)
        return -9, "[unirl] TIMEOUT"


# ----------------------------------------------------------------------------------------------- consulta

_CONSULTA_OK = re.compile(r"^[A-Za-z0-9_'.:\"()\[\]\-+*/^<>=,?!| ]+$")


def sanear_consulta(tipo: str, texto: str) -> str | None:
    """None si la consulta se admite; si no, el motivo. Nada de cartuchos, comentarios, saltos ni código."""
    if tipo not in ("buscar", "hecho", "metodo"):
        return "tipo de consulta desconocido (usa buscar, hecho o metodo)"
    t = texto.strip()
    if not t or len(t) > 200 or "\t" in t or "\n" in t:
        return "consulta vacía, demasiado larga o con saltos de línea"
    sin_simbolos = re.sub(r"\\<\^?[A-Za-z]+>", "x", t)
    if not _CONSULTA_OK.match(sin_simbolos) or "(*" in t or "*)" in t:
        return "caracteres no admitidos en la consulta"
    if tipo in ("hecho", "metodo") and not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_'.]*", t):
        return "un nombre de hecho o de método es un identificador"
    try:
        tokenize_outer(t)
    except ValueError as e:
        return f"la consulta no se lee: {e}"
    return None


def consultar(juez: TheoremVerifier, consultas: list[dict], tope: int = MAX_CONSULTAS_POR_LOTE, biblioteca: str = "") -> list[dict]:
    """[{tipo, texto}] → resultados en el contexto del peldaño, en una compilación. Las que pasan del tope no se
    ejecutan y vuelven con un error (no se descartan en silencio)."""
    admitidas, res = [], []
    for i, c in enumerate(consultas):
        motivo = (f"excede el tope de {tope} consultas por turno" if i >= tope
                  else sanear_consulta(c.get("tipo", ""), c.get("texto", "")))
        if motivo:
            res.append({"tipo": c.get("tipo"), "consulta": c.get("texto"), "error": motivo})
        else:
            admitidas.append(c)
    if admitidas:
        w = juez._workdir("gd-consulta-")
        (w / "consultas.txt").write_text("".join(f"{c['tipo']}\t{c['texto'].strip()}\n" for c in admitidas), encoding="utf-8")
        out = w / "consulta.json"
        thy, _ = fill_lines(TEORIA_CONSULTA, {**_tabla(juez, biblioteca), "IN": str(w / "consultas.txt"), "OUT": str(out)})
        rc, log = juez.build(w, thy, "Consulta", 180)
        if out.exists():
            res += json.loads(out.read_text())
        else:
            res += [{"tipo": c["tipo"], "consulta": c["texto"], "error": "la consulta no se pudo ejecutar"} for c in admitidas]
    for r in res:  # presupuesto fijo: a lo sumo MAX_RESULTADOS teoremas y enunciados recortados
        if "resultados" in r:
            r["resultados"] = [{"nombre": x["nombre"], "enunciado": x["enunciado"][:300]} for x in r["resultados"][:MAX_RESULTADOS]]
    return res


# ----------------------------------------------------------------------------------------------- glosario

GLOSARIO = BASE / "cuaderno" / "glosario.json"


def verificar_glosario(juez: TheoremVerifier | None = None, salida: Path | None = None) -> dict:
    """Comprueba en Isabelle que cada método o hecho de Lean del glosario NO existe y que cada alternativa de
    Isabelle SÍ existe. Escribe el resultado en cuaderno/glosario_verificacion.json."""
    juez = juez or TheoremVerifier.desde_corpus("orden_1_lineal")
    g = json.loads(GLOSARIO.read_text(encoding="utf-8"))
    consultas = []
    for e in g["entradas"]:
        consultas.append({"tipo": e["tipo"], "texto": e["lean"]})
        for alt in e["isabelle"]:
            consultas.append({"tipo": alt["tipo"], "texto": alt["nombre"]})
    resultados = {}
    for i in range(0, len(consultas), 40):  # la verificación del glosario es nuestra: lotes grandes
        for r in consultar(juez, consultas[i:i + 40], tope=40):
            resultados[(r["tipo"], r["consulta"])] = r.get("existe")
    ok, filas = True, []
    for e in g["entradas"]:
        lean_existe = resultados.get((e["tipo"], e["lean"]))
        alts = [(a["nombre"], resultados.get((a["tipo"], a["nombre"]))) for a in e["isabelle"]]
        bien = lean_existe is False and all(x is True for _, x in alts)
        ok &= bien
        filas.append({"lean": e["lean"], "lean_existe_en_isabelle": lean_existe, "alternativas": dict(alts), "ok": bien})
    res = {"ok": ok, "fecha": time.strftime("%Y-%m-%dT%H:%M:%S"), "isabelle": ISABELLE,
              "glosario_hash": hashlib.sha256(GLOSARIO.read_bytes()).hexdigest()[:16], "filas": filas}
    (salida or GLOSARIO.parent / "glosario_verificacion.json").write_text(json.dumps(res, ensure_ascii=False, indent=1),
                                                                        encoding="utf-8")
    return res
