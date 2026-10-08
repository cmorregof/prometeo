"""Cuaderno del minero (PLAN_rl_verbal.md, §3.4 y Etapa 6). Por ahora, solo los errores.

`cuaderno/errores.json` es la fuente; `cuaderno/errores.md` se genera desde ella y es lo que ve el proponente.
Semilla (Etapa 3): el glosario Lean→Isabelle, y solo si su comprobación contra Isabelle está al día (mismo hash del
glosario) y todas sus filas pasaron: cada nombre de Lean que desaconseja no existe y cada alternativa sí existe.
Cada error lleva contadores; la Etapa 6 los incrementa con los episodios de train (nunca con los de evaluación).
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DIR = BASE / "runs" / "unirl" / "cuaderno"  # estado vivo del cuaderno del RL verbal (reorganización del 26 sep 2026)
GLOSARIO = DIR / "glosario.json"
VERIFICACION = DIR / "glosario_verificacion.json"
ERRORES_JSON = DIR / "errores.json"
ERRORES_MD = DIR / "errores.md"
TIPO = {"metodo": "método", "hecho": "hecho"}


class GlosarioSinVerificar(RuntimeError):
    pass


def _hash(ruta: Path) -> str:
    return hashlib.sha256(ruta.read_bytes()).hexdigest()[:16]


def sembrar_errores(glosario: Path = GLOSARIO, verificacion: Path = VERIFICACION) -> dict:
    """Errores iniciales desde el glosario comprobado. Falla si la comprobación no existe, es de otra versión del
    glosario o tiene alguna fila que no pasó."""
    if not verificacion.exists():
        raise GlosarioSinVerificar("falta la comprobación del glosario (martillo.verificar_glosario)")
    v = json.loads(verificacion.read_text(encoding="utf-8"))
    if v.get("glosario_hash") != _hash(glosario):
        raise GlosarioSinVerificar("la comprobación es de otra versión del glosario: hay que repetirla")
    malas = [f["lean"] for f in v["filas"] if not f["ok"]]
    if not v.get("ok") or malas:
        raise GlosarioSinVerificar(f"filas del glosario que no pasaron: {malas}")
    g = json.loads(glosario.read_text(encoding="utf-8"))
    filas = {f["lean"]: f for f in v["filas"]}
    errores = []
    for i, e in enumerate(g["entradas"], 1):
        f = filas.get(e["lean"])
        if f is None:
            raise GlosarioSinVerificar(f"{e['lean']}: sin fila en la comprobación")
        errores.append({
            "id": f"E{i:03d}", "clase": "glosario", "lean": e["lean"], "tipo": e["tipo"],
            "en_su_lugar": [{"tipo": a["tipo"], "nombre": a["nombre"]} for a in e["isabelle"]],
            "nota": e["nota"], "origen": f"glosario ({e.get('visto_en', 'sin registro')})",
            "comprobado": {"isabelle": v.get("isabelle"), "fecha": v["fecha"], "glosario_hash": v["glosario_hash"],
                           "lean_existe": f["lean_existe_en_isabelle"], "alternativas": f["alternativas"]},
            "contadores": {"apariciones": 0, "ultimo_episodio": None},
        })
    return {"version": 1, "sembrado": time.strftime("%Y-%m-%dT%H:%M:%S"), "errores": errores}


def registrar_aparicion(doc: dict, id_: str, episodio: str, split: str) -> None:
    """Suma una aparición del error `id_`. Solo los episodios de train escriben en el cuaderno."""
    if split != "train":
        raise ValueError("solo los episodios de train escriben en el cuaderno")
    e = next(x for x in doc["errores"] if x["id"] == id_)
    e["contadores"]["apariciones"] += 1
    e["contadores"]["ultimo_episodio"] = episodio


def render_errores(doc: dict) -> str:
    """errores.md: lo que ve el proponente (sin fechas ni hashes, que no le sirven)."""
    out = ["# Errores frecuentes al escribir pruebas en Isabelle", "",
           "Cada nombre marcado como inexistente se comprobó en Isabelle2025 (no existe) y cada alternativa también "
           "(sí existe).", ""]
    for e in doc["errores"]:
        if e.get("clase") == "aprendido":
            # de la destilación (Etapa 6): texto libre, sin `en_su_lugar`; sus afirmaciones de existencia se
            # comprobaron en Isabelle al admitirlo (25 sep: un KeyError aquí detuvo la construcción del cuaderno)
            out += [f"## {e['id']} · aprendido en los episodios de train", "", f"* {e['texto']}"]
            out += [f"* Comprobado en Isabelle2025: {TIPO[a['tipo']]} `{a['nombre']}` "
                    f"{'existe' if a['existe'] else 'no existe'}." for a in e.get("afirma", [])]
            out += [f"* Visto en episodios de este cuaderno: {e['contadores']['apariciones']}.", ""]
            continue
        alts = ", ".join(f"{TIPO[a['tipo']]} `{a['nombre']}`" for a in e["en_su_lugar"])
        out += [f"## {e['id']} · `{e['lean']}` no existe en Isabelle ({TIPO[e['tipo']]} de Lean)", "",
                f"* En su lugar: {alts}.", f"* {e['nota']}",
                f"* Visto en episodios de este cuaderno: {e['contadores']['apariciones']}.", ""]
    return "\n".join(out)


def escribir_errores(doc: dict, ruta_json: Path = ERRORES_JSON, ruta_md: Path = ERRORES_MD) -> None:
    ruta_json.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    ruta_md.write_text(render_errores(doc), encoding="utf-8")


# ============================================================================= admisión (Etapa 4, PLAN §3.6)
#
# Qué entra al cuaderno se decide con estas reglas, que NO dependen de r_V:
#   lemas: solo si el kernel los verifica como enunciados independientes (a nivel de teoría, fuera del contexto con
#          las hipótesis del peldaño, con el cuaderno previo como único contexto extra);
#   errores: de cualquier episodio de train; si afirman que un nombre o método existe o no, se comprueba en Isabelle;
#   estrategias: solo de episodios de train aceptados o que aportaron lemas verificados; con contadores de intentos y
#          éxitos, y descarte por umbral tras un mínimo de intentos.

import re as _re  # noqa: E402

MIN_INTENTOS_ESTRATEGIA = 5
UMBRAL_EXITO_ESTRATEGIA = 0.2
MAX_TEXTO_ERROR = 400
_NOMBRE = _re.compile(r"[A-Za-z][A-Za-z0-9_']*$")

LEMA_ADMISION = r'''theory Admision
  imports "HOL-Analysis.Analysis"
begin

__PRELUDE__

ML \<open>
  val isarl_axioms0 = length (Theory.all_axioms_of @{theory})
\<close>

__CUADERNO__

ML \<open>
  val _ = if can (Proof_Context.get_fact @{context}) (Facts.named "__NOMBRE__")
          then error "isarl: el nombre ya existe (sombrearía un hecho de Isabelle o del cuaderno)" else ()
\<close>

__LEMA__

ML \<open>
  val ths = Proof_Context.get_fact @{context} (Facts.named "__NOMBRE__")
  val _ = File.write (Path.explode "__OUT__")
    ("{\"oracles\": [" ^ String.concatWith "," (map (fn ((n, _), _) => "\"" ^ n ^ "\"") (Thm_Deps.all_oracles ths))
      ^ "], \"skip_proof\": " ^ (if Thm_Deps.has_skip_proof ths then "true" else "false")
      ^ ", \"axioms_ok\": " ^ (if length (Theory.all_axioms_of @{theory}) = isarl_axioms0 then "true" else "false") ^ "}")
\<close>

end
'''


def preludios() -> dict[str, str]:
    """Preludio de cada método, leído de los peldaños aprobados (todos los de un método comparten preludio)."""
    from . import corpus
    out: dict[str, str] = {}
    for p in corpus.usables():
        if p["metodo"] in out and out[p["metodo"]] != p["prelude"]:
            raise ValueError(f"el método {p['metodo']} tiene dos preludios distintos")
        out[p["metodo"]] = p["prelude"]
    return out


def reservados() -> set[str]:
    """Nombres que un lema del cuaderno no puede declarar: etiquetas de hipótesis y constantes de los preludios de
    todos los peldaños (en un peldaño, la etiqueta local taparía al lema del cuaderno)."""
    from . import corpus
    from .gd_isabelle import nombres_del_objetivo
    return set().union(*(nombres_del_objetivo(p) for p in corpus.usables()))


def constantes_por_metodo() -> dict[str, set[str]]:
    return {m: set(_re.findall(r"^\s*(?:primrec|fun|function|definition|abbreviation)\s+([A-Za-z_][A-Za-z0-9_']*)",
                               pre, _re.M)) for m, pre in preludios().items()}


def alcance(lema: str, metodo: str | None) -> tuple[str | None, str]:
    """('general' | método, '') si el lema puede entrar, o (None, motivo). Un lema que usa constantes del preludio de
    un método es de ese método (y solo se admite desde un episodio de ese método); si no usa ninguna, es general."""
    # las constantes aparecen dentro de las cadenas del enunciado: se buscan como palabras sueltas en todo el texto
    usadas = {m for m, cs in constantes_por_metodo().items()
              if any(_re.search(rf"(?<![A-Za-z0-9_']){_re.escape(c)}(?![A-Za-z0-9_'])", lema) for c in cs)}
    if not usadas:
        return "general", ""
    if len(usadas) > 1:
        return None, f"usa constantes de varios métodos: {sorted(usadas)}"
    (m,) = usadas
    if metodo != m:
        return None, f"usa constantes de {m} y el episodio es de {metodo}"
    return m, ""


def admitir_lema(lema: str, metodo: str | None, cuaderno_general: str = "", cuaderno_metodo: str = "",
                 juez=None, split: str = "train") -> dict:
    """Decide si un lema entra al cuaderno. Filtro léxico, un solo lema, nombre libre, alcance; y el kernel: el lema se
    compila a nivel de teoría (sin las hipótesis del peldaño), sin oráculos, sin skip_proof y sin axiomas nuevos."""
    from .gd_isabelle import TheoremVerifier, check_lemma_block, fill_lines
    from .verifiers import split_lemmas

    def no(motivo: str, **kw) -> dict:
        return {"admitido": False, "motivo": motivo, **kw}
    if split != "train":
        return no("solo los episodios de train escriben en el cuaderno")
    bloques = split_lemmas(lema)
    if len(bloques) != 1:
        return no(f"se admite un lema a la vez (hay {len(bloques)})")
    nombre = bloques[0]["name"]
    if not _NOMBRE.match(nombre) or nombre.startswith("isarl"):
        return no(f"nombre no admitido: {nombre!r}")
    mal = check_lemma_block(lema, reservados())
    if mal:
        return no(f"{mal[0]}: {mal[1]}", nombre=nombre)
    previos = {b["name"] for b in split_lemmas(cuaderno_general) + split_lemmas(cuaderno_metodo)}
    if nombre in previos:
        return no(f"el cuaderno ya tiene un lema llamado {nombre}", nombre=nombre)
    esc, motivo = alcance(lema, metodo)
    if esc is None:
        return no(motivo, nombre=nombre)
    juez = juez or TheoremVerifier.desde_corpus("orden_1_lineal")
    w = juez._workdir("gd-admision-")
    out = w / "admision.json"
    contexto = cuaderno_general + ("\n\n" + cuaderno_metodo if esc != "general" else "")
    thy, _ = fill_lines(LEMA_ADMISION, {"PRELUDE": preludios()[esc] if esc != "general" else "",
                                        "CUADERNO": contexto.strip(), "NOMBRE": nombre, "LEMA": lema.strip(),
                                        "OUT": str(out)})
    rc, log = juez.build(w, thy, "Admision", 300)
    errores = [l for l in log.splitlines() if l.startswith("***")][:8]
    if rc != 0 or not out.exists():
        if any("isarl: el nombre ya existe" in e for e in errores):
            return no(f"el nombre {nombre} ya existe en Isabelle o en el cuaderno: lo taparía", nombre=nombre, alcance=esc)
        return no("el kernel no verifica el lema como enunciado independiente", nombre=nombre, alcance=esc, errores=errores)
    d = json.loads(out.read_text())
    if d["oracles"] or d["skip_proof"] or not d["axioms_ok"]:
        return no("el lema depende de oráculos, skip_proof o axiomas nuevos", nombre=nombre, alcance=esc)
    return {"admitido": True, "motivo": "", "nombre": nombre, "alcance": esc, "texto": lema.strip()}


def admitir_error(error: dict, split: str, comprobar=None) -> dict:
    """error = {texto, afirma: [{tipo: metodo|hecho, nombre, existe: bool}]}. Entra desde cualquier episodio de train;
    cada afirmación de existencia se comprueba (por defecto en Isabelle con martillo.consultar) y basta una falsa para
    rechazarlo. `comprobar(afirmaciones) -> {(tipo, nombre): bool | None}`."""
    if split != "train":
        return {"admitido": False, "motivo": "solo los episodios de train escriben en el cuaderno"}
    texto = (error.get("texto") or "").strip()
    if not texto or len(texto) > MAX_TEXTO_ERROR:
        return {"admitido": False, "motivo": f"texto vacío o de más de {MAX_TEXTO_ERROR} caracteres"}
    afirma = error.get("afirma") or []
    for a in afirma:
        if a.get("tipo") not in ("metodo", "hecho") or not _NOMBRE.match(str(a.get("nombre", ""))) or \
                not isinstance(a.get("existe"), bool):
            return {"admitido": False, "motivo": f"afirmación mal formada: {a}"}
    if afirma:
        if comprobar is None:
            from . import martillo
            from .gd_isabelle import TheoremVerifier

            def comprobar(xs):
                r = martillo.consultar(TheoremVerifier.desde_corpus("orden_1_lineal"),
                                       [{"tipo": x["tipo"], "texto": x["nombre"]} for x in xs], tope=len(xs))
                return {(y["tipo"], y["consulta"]): y.get("existe") for y in r}
        vistos = comprobar(afirma)
        for a in afirma:
            real = vistos.get((a["tipo"], a["nombre"]))
            if real is None:
                return {"admitido": False, "motivo": f"no se pudo comprobar {a['nombre']}"}
            if real != a["existe"]:
                return {"admitido": False, "motivo": f"afirmación falsa: {a['nombre']} {'sí' if real else 'no'} existe"}
    return {"admitido": True, "motivo": "", "texto": texto, "afirma": afirma,
            "contadores": {"apariciones": 0, "ultimo_episodio": None}}


def admitir_estrategia(estrategia: str, episodio: dict) -> dict:
    """Solo de episodios de train aceptados o que aportaron lemas verificados. Empieza con contadores en cero."""
    if episodio.get("split") != "train":
        return {"admitido": False, "motivo": "solo los episodios de train escriben en el cuaderno"}
    if not (episodio.get("aceptado") or episodio.get("lemas_verificados", 0) > 0):
        return {"admitido": False, "motivo": "el episodio no se aceptó ni aportó lemas verificados"}
    texto = (estrategia or "").strip()
    if not texto or len(texto) > MAX_TEXTO_ERROR:
        return {"admitido": False, "motivo": f"texto vacío o de más de {MAX_TEXTO_ERROR} caracteres"}
    return {"admitido": True, "motivo": "", "texto": texto, "origen": episodio.get("id"),
            "contadores": {"intentos": 0, "exitos": 0}}


def registrar_uso_estrategia(e: dict, exito: bool, split: str) -> None:
    if split != "train":
        raise ValueError("solo los episodios de train escriben en el cuaderno")
    e["contadores"]["intentos"] += 1
    e["contadores"]["exitos"] += int(bool(exito))


def descartar_estrategias(estrategias: list[dict], min_intentos: int = MIN_INTENTOS_ESTRATEGIA,
                          umbral: float = UMBRAL_EXITO_ESTRATEGIA) -> tuple[list[dict], list[dict]]:
    """(vigentes, descartadas): se descarta una estrategia con al menos `min_intentos` usos y tasa de éxito < umbral."""
    vig, desc = [], []
    for e in estrategias:
        c = e["contadores"]
        (desc if c["intentos"] >= min_intentos and c["exitos"] / c["intentos"] < umbral else vig).append(e)
    return vig, desc


# ============================================================================= el cuaderno (Etapa 6, PLAN §3.8)
#
# cuaderno/ (o una copia congelada en cuaderno/congelados/<hash>/):
#   errores.json      glosario sembrado (clase «glosario») + errores aprendidos (clase «aprendido»), con contadores;
#   lemas.json        lemas admitidos por el kernel, con alcance (general | método) y procedencia;
#   estrategias.json  estrategias admitidas, con contadores de intentos y éxitos;
#   episodios.jsonl   resumen de cada episodio de train (el proponente no lo lee).
# Solo los episodios de train escriben; la evaluación usa una copia congelada con su hash.

import shutil  # noqa: E402

CONGELADOS = DIR / "congelados"
PRESUPUESTO = {"errores": 1500, "lemas": 3500, "estrategias": 1500}  # caracteres en el prompt (el glosario va completo)  # caracteres en el prompt
K_RECUPERAR = {"errores": 6, "lemas": 8, "estrategias": 5}
# Ronda 2 (27 sep 2026, prerregistrado antes de lanzarla): un lema se muestra solo si su enunciado comparte al menos
# MINIMO_IDS_LEMA identificadores con el enunciado o el preludio del teorema; los símbolos (\<le>, \<Longrightarrow>…)
# no cuentan. En la ronda 1 el único lema, sign_step, se mostró en los 16 teoremas de test sin compartir ningún
# identificador con ellos, y las 35 respuestas que lo citaron fallaron (resultados/RONDA_TERMINADA.md). 0 = regla de
# la ronda 1 (solo orden por coincidencia, sin umbral).
MINIMO_IDS_LEMA = 1
_PALABRAS_VACIAS = frozenset("""and assumes fixes shows lemma theorem by proof qed using unfolding apply done have show
hence thus obtain real nat bool where if then else let in fst snd of the de la el en y que con por para los las un una es
se si no a o del al lo su sus""".split())


def hash_texto(texto: str) -> str:
    return hashlib.sha256(texto.encode()).hexdigest()[:16] if texto.strip() else ""


def claves(texto: str) -> set[str]:
    """Identificadores y símbolos de un texto (Isabelle o español), para recuperar por coincidencia."""
    ids = {w.lower() for w in _re.findall(r"[A-Za-z][A-Za-z0-9_']+", texto)} - _PALABRAS_VACIAS
    syms = set(_re.findall(r"\\<\^?[A-Za-z]+>", texto))
    return {w for w in ids if len(w) > 2} | syms


def identificadores(texto: str) -> set[str]:
    """Las claves que no son símbolos \\<…> (las palabras que derivan de un símbolo, como `bar` de \\<bar>, sí cuentan)."""
    return {w for w in claves(texto) if not w.startswith("\\<")}


def cierre_de_dependencias(elegidos: list[dict], disponibles: list[dict]) -> list[dict]:
    """Los lemas `elegidos` más los del cuaderno que sus pruebas citan por nombre, transitivamente, en el orden del
    cuaderno. Ese orden es el de admisión: cada lema se admitió con los anteriores ya en la teoría, así que sus
    dependencias quedan antes. 30 sep 2026: en la ronda 2, cu_iterate_contraction_bound se mostraba sin
    cu_funpow_invariant, que su prueba usa, y la biblioteca no compilaba («Undefined fact»)."""
    por_nombre = {l["nombre"]: l for l in disponibles}
    orden = {l["nombre"]: i for i, l in enumerate(disponibles)}
    pendientes, cerrados = [l["nombre"] for l in elegidos], set()
    while pendientes:
        n = pendientes.pop()
        if n in cerrados or n not in por_nombre:
            continue
        cerrados.add(n)
        texto = por_nombre[n]["texto"]
        pendientes += [m for m in por_nombre if m not in cerrados
                       and _re.search(rf"(?<![A-Za-z0-9_']){_re.escape(m)}(?![A-Za-z0-9_'])", texto)]
    return sorted((por_nombre[n] for n in cerrados), key=lambda l: orden[l["nombre"]])


def enunciado_de_lema(texto: str) -> str:
    """La cabeza del lema (nombre y enunciado), sin su prueba: todo hasta el primer comando de prueba fuera de comillas."""
    dentro, i = False, 0
    while i < len(texto):
        c = texto[i]
        if c == '"':
            dentro = not dentro
        elif not dentro:
            m = _re.match(r"(?:(?<=\s)|^)(by|proof|apply|using|unfolding)\b", texto[i:]) if (i == 0 or texto[i - 1].isspace()) else None
            if m:
                return texto[:i].strip()
        i += 1
    return texto.strip()


class Cuaderno:
    def __init__(self, dir: Path | None = None, solo_lectura: bool = False):
        # el directorio por defecto se lee al construir, no al definir la clase (25 sep: con `dir: Path = DIR`, una
        # prueba que parchaba DIR escribió en el cuaderno real)
        self.dir, self.solo_lectura = Path(dir) if dir is not None else DIR, solo_lectura
        self.errores = self._leer("errores.json", {"errores": []})
        self.lemas: list[dict] = self._leer("lemas.json", {"lemas": []})["lemas"]
        self.estrategias: list[dict] = self._leer("estrategias.json", {"estrategias": []})["estrategias"]

    def _leer(self, nombre: str, defecto: dict) -> dict:
        f = self.dir / nombre
        return json.loads(f.read_text(encoding="utf-8")) if f.exists() else json.loads(json.dumps(defecto))

    # -- identidad
    def contenido(self) -> dict:
        return {"errores": self.errores.get("errores", []), "lemas": self.lemas, "estrategias": self.estrategias}

    def hash(self) -> str:
        return hashlib.sha256(json.dumps(self.contenido(), ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16]

    def hash_lemas(self) -> str:
        """Identifica los lemas (lo único que cambia lo que el martillo puede cerrar): clave de la línea base."""
        return hash_texto("\n\n".join(sorted(l["texto"] for l in self.lemas)))

    def guardar(self) -> None:
        if self.solo_lectura:
            raise PermissionError("cuaderno congelado: la evaluación no escribe")
        self.dir.mkdir(parents=True, exist_ok=True)
        for nombre, datos in (("errores.json", self.errores), ("lemas.json", {"lemas": self.lemas}),
                              ("estrategias.json", {"estrategias": self.estrategias})):
            tmp = self.dir / f".{nombre}.tmp"
            tmp.write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")
            tmp.replace(self.dir / nombre)
        if self.dir == DIR:
            (DIR / "errores.md").write_text(render_errores(self.errores), encoding="utf-8")

    def congelar(self) -> "Cuaderno":
        """Copia de solo lectura en cuaderno/congelados/<hash>/ (con su hash en el nombre y en congelado.json)."""
        h = self.hash()
        destino = CONGELADOS / h
        if not destino.exists():
            destino.mkdir(parents=True)
            for nombre in ("errores.json", "lemas.json", "estrategias.json"):
                if (self.dir / nombre).exists():
                    shutil.copy2(self.dir / nombre, destino / nombre)
            (destino / "congelado.json").write_text(json.dumps({"hash": h, "hash_lemas": self.hash_lemas(),
                                                                "fecha": time.strftime("%Y-%m-%dT%H:%M:%S"),
                                                                "origen": str(self.dir)}, indent=1), encoding="utf-8")
        c = Cuaderno(destino, solo_lectura=True)
        if c.hash() != h:
            raise ValueError("la copia congelada no coincide con el cuaderno")
        return c

    # -- recuperación
    def _rankear(self, items: list[dict], texto_de, spec: dict, k: int, presupuesto: int, extra=lambda x: 0.0,
                 minimo_ids: int = 0, cabeza=lambda t: t) -> list[dict]:
        """`minimo_ids` (ronda 2): se descarta lo que no comparte al menos tantos identificadores (sin símbolos) con el
        teorema, medidos sobre `cabeza(texto)` (para un lema, su enunciado sin la prueba)."""
        objetivo = claves(" ".join(spec.get(c, "") for c in ("prelude", "fixes", "assumes", "concl", "statement_es")))
        puntuados = []
        for n, it in enumerate(items):
            if minimo_ids and len(identificadores(cabeza(texto_de(it))) & objetivo) < minimo_ids:
                continue
            s = len(claves(texto_de(it)) & objetivo) + extra(it)
            puntuados.append((s, -n, it))
        puntuados.sort(key=lambda x: (x[0], x[1]), reverse=True)
        out, usado = [], 0
        for s, _, it in puntuados:
            if len(out) >= k:
                break
            t = len(texto_de(it))
            if usado + t > presupuesto:
                continue
            out.append(it)
            usado += t
        return out

    def lemas_aplicables(self, metodo: str) -> list[dict]:
        return [l for l in self.lemas if l["alcance"] in ("general", metodo)]

    def recuperar(self, spec: dict, partes: tuple[str, ...]) -> dict:
        """Lo que ve el proponente en un peldaño: k elementos por parte, por coincidencia de identificadores y símbolos
        con el enunciado y el preludio, dentro de un presupuesto fijo de caracteres."""
        sel = {"errores": [], "lemas": [], "estrategias": []}
        if "errores" in partes:
            aprendidos = [e for e in self.errores.get("errores", []) if e.get("clase") == "aprendido"]
            sel["errores"] = self._rankear(aprendidos, lambda e: e["texto"], spec, K_RECUPERAR["errores"],
                                           PRESUPUESTO["errores"], lambda e: 0.5 * e["contadores"]["apariciones"])
        if "lemas" in partes:
            aplicables = self.lemas_aplicables(spec["metodo"])
            sel["lemas"] = self._rankear(aplicables, lambda l: l["texto"], spec,
                                         K_RECUPERAR["lemas"], PRESUPUESTO["lemas"],
                                         lambda l: 2.0 if l["alcance"] == spec["metodo"] else 0.0,
                                         minimo_ids=MINIMO_IDS_LEMA, cabeza=enunciado_de_lema)
            # lo que se compila: los mostrados y sus dependencias, en el orden del cuaderno (lo que se muestra no cambia)
            sel["biblioteca"] = cierre_de_dependencias(sel["lemas"], aplicables)
        if "estrategias" in partes:
            sel["estrategias"] = self._rankear(
                self.estrategias, lambda e: e["texto"] + " " + e.get("topico", ""), spec, K_RECUPERAR["estrategias"],
                PRESUPUESTO["estrategias"],
                lambda e: (e["contadores"]["exitos"] + 1) / (e["contadores"]["intentos"] + 2))
        return sel

    @staticmethod
    def biblioteca(sel: dict) -> str:
        """Texto de los lemas que se compilan con cada intento, a nivel de teoría y antes de los del agente: los
        mostrados y sus dependencias en el orden del cuaderno (`sel["biblioteca"]`); sin esa clave, los mostrados."""
        return "\n\n".join(l["texto"] for l in sel.get("biblioteca", sel.get("lemas", [])))

    def glosario_compacto(self) -> str:
        filas = []
        for e in self.errores.get("errores", []):
            if e.get("clase") != "glosario":
                continue
            alts = ", ".join(a["nombre"] for a in e["en_su_lugar"])
            nota = _re.sub(r"^No existe( en Isabelle)?\.\s*", "", e["nota"])
            filas.append(f"- `{e['lean']}` ({TIPO[e['tipo']]} de Lean) no existe en Isabelle → {alts}. {nota}".rstrip())
        return "\n".join(filas)  # completo: es el entorno base comprobado (~3 400 caracteres)

    @staticmethod
    def render(sel: dict) -> str:
        partes = []
        if sel.get("errores"):
            partes.append("Errores que ya se cometieron en otros teoremas (comprobados en Isabelle):\n"
                          + "\n".join(f"- {e['texto']}" for e in sel["errores"]))
        if sel.get("lemas"):
            partes.append("Lemas del cuaderno: el kernel ya los verificó y se añaden solos a tu intento; úsalos por su "
                          "nombre y no los repitas en LEMMAS:\n"
                          + "\n".join(f"- {enunciado_de_lema(l['texto'])}" for l in sel["lemas"]))
        if sel.get("estrategias"):
            partes.append("Estrategias que funcionaron en otros teoremas (con cuántas veces se usaron y se aceptó):\n"
                          + "\n".join(f"- {e['texto']} (usada {e['contadores']['intentos']} veces, aceptada "
                                      f"{e['contadores']['exitos']})" for e in sel["estrategias"]))
        return "\n\n".join(partes)

    # -- escritura desde episodios de train
    def registrar_errores_de_intentos(self, errores_kernel: list[str], episodio: str, split: str) -> list[str]:
        """Cuenta las apariciones de los errores conocidos: `Undefined method: "X"` / `Undefined fact: "X"` con X uno de
        los nombres de Lean del glosario (o de un error aprendido que afirme que X no existe)."""
        if split != "train":
            return []
        vistos = []
        texto = "\n".join(errores_kernel)
        for e in self.errores.get("errores", []):
            nombres = [e["lean"]] if e.get("clase") == "glosario" else [a["nombre"] for a in e.get("afirma", []) if not a["existe"]]
            if any(_re.search(rf'Undefined (?:method|fact|constant)[^"\n]*"{_re.escape(n)}"', texto) for n in nombres):
                e["contadores"]["apariciones"] += 1
                e["contadores"]["ultimo_episodio"] = episodio
                vistos.append(e.get("id", e.get("texto", "")[:40]))
        return vistos

    def agregar_lema(self, admitido: dict, procedencia: dict) -> None:
        self.lemas.append({"nombre": admitido["nombre"], "texto": admitido["texto"], "alcance": admitido["alcance"],
                           "procedencia": procedencia})

    def cuaderno_de(self, alcance_: str) -> tuple[str, str]:
        """(lemas generales, lemas del método): el contexto con que se admite un lema nuevo."""
        gen = "\n\n".join(l["texto"] for l in self.lemas if l["alcance"] == "general")
        met = "\n\n".join(l["texto"] for l in self.lemas if l["alcance"] == alcance_) if alcance_ != "general" else ""
        return gen, met

    def agregar_error(self, admitido: dict, procedencia: dict) -> None:
        n = len(self.errores.setdefault("errores", [])) + 1
        self.errores["errores"].append({"id": f"A{n:03d}", "clase": "aprendido", "texto": admitido["texto"],
                                        "afirma": admitido["afirma"], "contadores": admitido["contadores"],
                                        "procedencia": procedencia})

    def agregar_estrategia(self, admitida: dict, topico: str, procedencia: dict) -> None:
        self.estrategias.append({"texto": admitida["texto"], "topico": topico, "origen": admitida.get("origen"),
                                 "contadores": admitida["contadores"], "procedencia": procedencia})


def render_errores_aprendidos(doc: dict) -> str:
    return "\n".join(f"- {e['texto']}" for e in doc.get("errores", []) if e.get("clase") == "aprendido")
