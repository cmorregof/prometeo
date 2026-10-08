#!/usr/bin/env python3
"""Re-adjudicación de los veredictos del juez de teorema con un verificador de referencia independiente (8 oct 2026).

Por qué existe. Por solidez (supuestos C1 y C2a de la propuesta), el juez no acepta nada que la especificación V
rechace: sus errores solo pueden ser falsos negativos, y entonces E[p̂_X] = Se_X · p_X. La comparación entre
configuraciones solo es justa si la sensibilidad Se es la misma en todas; en la ronda 1 no lo fue (los lemas del cuaderno
iban dentro del contexto y todo intento de E y E3 en secante_1 a secante_4 fallaba con «Duplicate fixed variable»;
`resultados/mcnemar_ronda_20260926.md`, sección 3). Ningún teorema descarta los falsos negativos: dependen del arnés
(extracción, ensamblado de la teoría, ubicación de la biblioteca, límites de tiempo). Este guion los mide. Las
proposiciones y sus pruebas están en «Insesgamiento del juez» (seccion_insesgamiento.tex, junto a la propuesta de tesis).

Subcomandos:
  rejuzgar --desde ISO [--hasta ISO]   vuelve a juzgar con la referencia los intentos de las corridas de la ventana
                                       (por defecto, las fases de una ronda) y escribe el informe
  resumen  --etiqueta NOMBRE           rehace el informe desde rejuicio.jsonl, sin compilar nada
  cruzado  --desde ISO [--hasta ISO]   formato cruzado: cada prueba aceptada sin cuaderno se vuelve a juzgar con el juez
                                       ACTUAL, sin biblioteca y con la biblioteca del cuaderno de ese peldaño; el
                                       veredicto no debería cambiar (lo habría detectado el defecto de la ronda 1)

La referencia no importa unirl.gd_isabelle ni unirl.verifiers (solo `cruzado` usa el juez, porque lo que prueba es el
juez). Para cada intento:
  1. filtro mínimo F_min sobre el texto sin comentarios ni cadenas: sorry, oops, axiomatization, axioms, oracle,
     quick_and_dirty, skip_proof, ML y su familia (setup, method_setup, …), tactic, eval. Si lo toca: V = 0 sin compilar;
  2. una sola teoría: preludio · biblioteca a nivel de teoría (como en su admisión) · contexto congelado del peldaño ·
     lemas del agente · `theorem <nonce>_objetivo` · PROOF. Los nombres llevan un nonce aleatorio que el texto del agente
     no puede conocer, y si el agente redefine un lema del cuaderno vale su versión;
  3. `isabelle build` con parallel_proofs = 0, un límite generoso (--limite, 600 s: el doble del juez) y sandbox-exec
     si existe;
  4. acepta solo si rc = 0, el enunciado demostrado es término a término el congelado (aconv), no hay oráculos ni
     skip_proof y ningún axioma nuevo (por nombre) aparece después de la biblioteca.
No aplica las reglas estrictas del juez (notación, cartuchos, solo comandos de prueba en PROOF, nombres reservados,
formato de la respuesta): un rechazo que solo se debe a ellas sale como `regla_estricta`, no como falso negativo.

Categorías por intento (juez frente a referencia):
  concordante              mismo veredicto
  concordante_contaminado  los dos rechazan, pero el juez culpó a un lema del cuaderno: la retroalimentación al agente
                           no habló de su prueba (la trayectoria posterior ya no es la que habría tenido con un juez correcto)
  FN                       el juez rechazó y la referencia acepta (subcausa: biblioteca, tiempo, otro)
  FP                       el juez aceptó y la referencia rechaza
  regla_estricta           la referencia acepta, pero el juez rechazó por una regla declarada más estricta que V
  tiempo                   la referencia acepta, pero tardó más que el límite del juez
  indeterminado            no se puede juzgar: biblioteca que no compila o no se reconstruye, objetivo cambiado, o marcas
                           del martillo abiertas por una biblioteca rota
  sin_juicio               marcas `by martillo` sin cerrar: el juez nunca vio una prueba completa (V = 0 por definición)

Convenciones del repo: no llama a la API; solo lee runs/, logs/ y corpus/; escribe en resultados/rejuicio/<etiqueta>/;
espera su turno si hay compilaciones de Isabelle ajenas (para no frenar una ronda en curso); --ensayo prepara todo sin
compilar. Ejemplo (ronda 1):

  python unirl/tools/rejuzgar.py rejuzgar --desde 2026-09-26T20:17:27 --hasta 2026-09-27T14:03:07 --etiqueta ronda1 --ensayo
  python unirl/tools/rejuzgar.py rejuzgar --desde 2026-09-26T20:17:27 --hasta 2026-09-27T14:03:07 --etiqueta ronda1
  python unirl/tools/rejuzgar.py cruzado  --desde 2026-09-26T20:17:27 --hasta 2026-09-27T14:03:07 --etiqueta ronda1

Tiempo: en la ronda 1 son 601 intentos, de los que unos 300 piden compilar (los demás tienen marcas sin cerrar o no traen
prueba). El juez tardó 10,6 s de mediana por intento con dos compilaciones; la referencia hace una, así que la ronda
entera debería tomar entre una y dos horas, más lo que tarden los pocos intentos que agotan el límite. Se puede cortar y
reanudar: lo ya juzgado queda en rejuicio.jsonl y no se repite.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import os
import random
import re
import shutil
import signal
import string
import subprocess
import sys
import tempfile
import threading
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from math import comb
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
RUNS = Path(os.environ.get("REJUICIO_RUNS") or RAIZ / "runs" / "unirl" / "rl_verbal")
CORPUS = Path(os.environ.get("REJUICIO_CORPUS") or RAIZ / "corpus" / "curado")
CUADERNO = Path(os.environ.get("REJUICIO_CUADERNO") or RAIZ / "runs" / "unirl" / "cuaderno")
RESULTADOS = Path(os.environ.get("REJUICIO_RESULTADOS") or RAIZ / "resultados" / "rejuicio")
VERSION_REFERENCIA = "referencia-2026-10-08"
FASES_RONDA = ("cuaderno", "evaluacion", "evaluacion_E", "pareada_luna", "pareada_sol")
HASH_CAMPOS = ("imports", "prelude", "fixes", "assumes", "concl")  # los de TheoremVerifier._hash
ETIQUETAS_FILTRO = ("UNSOUND", "STATEMENT_DRIFT", "INVALID_PROPOSAL", "SYNTAX_ERROR")
LIMITE_JUEZ_POR_DEFECTO = 300.0


def isabelle_por_defecto() -> Path:
    """La misma ruta que isarl.config, sin importarlo: ISARL_ISABELLE o ~/isabelle/Isabelle2025.app/bin/isabelle."""
    if os.environ.get("ISARL_ISABELLE"):
        return Path(os.environ["ISARL_ISABELLE"])
    raiz = Path(os.environ.get("ISARL_ISABELLE_ROOT", Path.home() / "isabelle"))
    return raiz / "Isabelle2025.app" / "bin" / "isabelle"


def scratch_por_defecto() -> Path:
    return Path(os.environ.get("ISARL_SCRATCH", Path.home() / "isabelle" / "scratch")) / "rejuicio"


# ----------------------------------------------------------------------------- utilidades


def hash_texto(texto: str) -> str:
    """Igual que unirl.cuaderno.hash_texto: con él se registró `biblioteca_hash`."""
    return hashlib.sha256(texto.encode()).hexdigest()[:16] if texto.strip() else ""


def hash_objetivo(spec: dict) -> str:
    """Igual que TheoremVerifier._hash: con él se registró `veredicto_meta.objetivo_hash`."""
    congelado = {k: spec.get(k, "") for k in HASH_CAMPOS}
    return hashlib.sha256(json.dumps(congelado, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16]


def leer_jsonl(ruta: Path) -> list[dict]:
    if not ruta.exists():
        return []
    filas = []
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        if linea.strip():
            try:
                filas.append(json.loads(linea))
            except json.JSONDecodeError:
                pass
    return filas


def leer_meta(d: Path) -> dict | None:
    try:
        return json.loads((d / "meta.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def p_mcnemar(b: int, bp: int) -> float | None:
    """p exacto bilateral bajo Bin(b + b', 1/2) (la misma fórmula que unirl/tools/ronda.py sin scipy)."""
    n = b + bp
    if n == 0:
        return None
    k = min(b, bp)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n)


def cota_regla_de_tres(n: int, alfa: float = 0.05) -> float | None:
    """Cota superior (1 − α) de una tasa de error con 0 errores en n casos: 1 − α^(1/n) ≈ 3/n."""
    return None if n <= 0 else 1 - alfa ** (1 / n)


# ----------------------------------------------------------------------------- texto de Isabelle


def _saltar_cartucho(t: str, i: int) -> int:
    """Índice justo después del cartucho que abre en i (anidado; \\<open>…\\<close> o ‹…›)."""
    prof, n = 0, len(t)
    while i < n:
        if t.startswith("\\<open>", i):
            prof, i = prof + 1, i + 7
        elif t.startswith("\\<close>", i):
            prof, i = prof - 1, i + 8
        elif t[i] == "‹":
            prof, i = prof + 1, i + 1
        elif t[i] == "›":
            prof, i = prof - 1, i + 1
        else:
            i += 1
        if prof == 0:
            return i
    return n


def sin_comentarios_ni_cadenas(t: str) -> str:
    """El texto sin comentarios (* … *) (anidados) ni cadenas "…"; los cartuchos se conservan, porque en uno de texto
    puede ir una antiquotation que ejecuta ML."""
    out, i, n = [], 0, len(t)
    while i < n:
        if t.startswith("(*", i):
            prof, i = 1, i + 2
            while i < n and prof:
                if t.startswith("(*", i):
                    prof, i = prof + 1, i + 2
                elif t.startswith("*)", i):
                    prof, i = prof - 1, i + 2
                else:
                    i += 1
            out.append(" ")
        elif t[i] == '"':
            j = i + 1
            while j < n and t[j] != '"':
                j += 2 if t[j] == "\\" else 1
            out.append(" ")
            i = j + 1
        elif t.startswith("\\<open>", i) or t[i] == "‹":
            j = _saltar_cartucho(t, i)
            out.append(t[i:j])
            i = j
        else:
            out.append(t[i])
            i += 1
    return "".join(out)


_PROHIBIDAS = re.compile(
    r"(?<![A-Za-z0-9_'])(sorry|oops|axiomatization|axioms|oracle|quick_and_dirty|skip_proof|S?ML(?:_[A-Za-z_]+)?|setup|"
    r"local_setup|declaration|syntax_declaration|method_setup|attribute_setup|simproc_setup|tactic|raw_tactic|eval)"
    r"(?![A-Za-z0-9_'])")


def prohibida(texto: str) -> str | None:
    """La primera palabra de F_min en el texto (fuera de comentarios y cadenas), o None."""
    m = _PROHIBIDAS.search(sin_comentarios_ni_cadenas(texto or ""))
    return m.group(1) if m else None


_CABEZA = re.compile(r"(?m)^[ \t]*(?:lemma|theorem|corollary|proposition)[ \t]+([A-Za-z][A-Za-z0-9_']*)")


def nombres_de_lemas(texto: str) -> list[str]:
    return _CABEZA.findall(sin_comentarios_ni_cadenas(texto or ""))


def bloques_de_lemas(texto: str) -> list[tuple[str, str]]:
    """(nombre, texto) de cada lema de un bloque, cortando en cada cabeza al inicio de línea."""
    if not (texto or "").strip():
        return []
    cortes = [m.start() for m in _CABEZA.finditer(texto)]
    if not cortes:
        return [("", texto.strip())]
    trozos = [texto[a:b].strip() for a, b in zip(cortes, cortes[1:] + [len(texto)])]
    if texto[:cortes[0]].strip():
        trozos[0] = texto[:cortes[0]].strip() + "\n" + trozos[0]
    return [((_CABEZA.match(t) or [None, ""])[1], t) for t in trozos]


def biblioteca_sin_redefinidos(biblioteca: str, lemas_agente: str) -> str:
    """Si el agente redefine un lema del cuaderno con el mismo nombre, vale su versión (dos hechos con un nombre chocan)."""
    propios = set(nombres_de_lemas(lemas_agente))
    return "\n\n".join(t for n, t in bloques_de_lemas(biblioteca) if n not in propios).strip()


_MARCA = re.compile(r"\bby\s+(?:\(\s*)?martillo\b")


def marcas_abiertas(intento: "Intento") -> bool:
    """¿Quedó alguna marca `by martillo` sin cerrar? Entonces el juez nunca vio una prueba completa."""
    if intento.marcas is not None and intento.cerradas is not None and intento.marcas > intento.cerradas:
        return True
    return bool(_MARCA.search(intento.prueba or ""))


# ----------------------------------------------------------------------------- registros


@dataclass
class Intento:
    fase: str
    corrida: str
    modelo: str
    config: str
    episodio_id: str
    peldano: str
    split: str
    dificultad: int | None
    intento: int
    llamada: int | None
    linea: int  # línea (1-based) en llamadas.jsonl
    etiqueta: str
    prueba: str
    lemas: str
    respuesta: str
    feedback: str
    errores: list[str]
    biblioteca_hash: str
    nombres_biblioteca: list[str]
    marcas: int | None
    cerradas: int | None
    objetivo_hash: str
    limite_juez: float | None
    version_juez: str
    cuaderno_hash: str
    registrado: bool = True  # el episodio de este intento tiene fila en episodios.jsonl de su corrida (terminó)
    aceptado_registro: bool | None = None  # lo que dice esa fila

    @property
    def k(self) -> int | None:
        cola = self.episodio_id.rsplit("#", 1)[-1]
        return int(cola) if cola.isdigit() else None

    @property
    def aceptado(self) -> bool:
        return self.etiqueta == "ACCEPTED"

    @property
    def archivo(self) -> str:
        return f"{self.fase}/{self.corrida}/llamadas.jsonl:{self.linea}"


def corridas(desde: str, hasta: str | None, fases: tuple[str, ...] | list[str]) -> list[Path]:
    """Carpetas de las fases con `inicio` en [desde, hasta), en orden cronológico."""
    out = []
    for fase in fases:
        base = RUNS / fase
        if not base.is_dir():
            continue
        for d in sorted(base.iterdir()):
            m = leer_meta(d) if d.is_dir() else None
            if not m:
                continue
            ini = m.get("inicio", "")
            if ini < desde or (hasta and ini >= hasta):
                continue
            out.append(d)
    return sorted(out, key=lambda d: ((leer_meta(d) or {}).get("inicio", ""), d.parent.name))


def intentos_de(d: Path) -> list[Intento]:
    """Los intentos juzgados de una corrida (tipo «intento», sin PROVIDER_ERROR)."""
    meta = leer_meta(d) or {}
    cfgs = meta.get("configs") or ([meta["config"]] if meta.get("config") else [])
    out = []
    ruta = d / "llamadas.jsonl"
    if not ruta.exists():
        return out
    # un episodio interrumpido (corte de red) no tiene fila en episodios.jsonl y la ronda no lo cuenta: se repitió
    registro = {}
    for e in leer_jsonl(d / "episodios.jsonl"):
        registro.setdefault(e.get("episodio_id"), bool(e.get("aceptado")))
    for i, linea in enumerate(ruta.read_text(encoding="utf-8").splitlines(), 1):
        try:
            r = json.loads(linea)
        except json.JSONDecodeError:
            continue
        if r.get("tipo") != "intento" or r.get("etiqueta") in (None, "PROVIDER_ERROR"):
            continue
        vm = r.get("veredicto_meta") or {}
        prueba = r.get("prueba_final") if r.get("prueba_final") is not None else r.get("proof")
        out.append(Intento(
            fase=d.parent.name, corrida=d.name, modelo=r.get("modelo") or meta.get("modelo", ""),
            config=r.get("config") or (cfgs[0] if len(cfgs) == 1 else ""), episodio_id=r.get("episodio_id", ""),
            peldano=r.get("peldano", ""), split=r.get("split", ""), dificultad=r.get("dificultad"),
            intento=int(r.get("intento") or 0), llamada=r.get("llamada"), linea=i, etiqueta=r["etiqueta"],
            prueba=str(prueba or ""), lemas=str(r.get("lemmas") or ""), respuesta=str(r.get("respuesta") or ""),
            feedback=str(r.get("feedback") or ""), errores=[str(e) for e in (r.get("errores") or [])],
            biblioteca_hash=r.get("biblioteca_hash") or "",
            nombres_biblioteca=list(r.get("lemas_biblioteca") or r.get("lemas_mostrados") or []),
            marcas=r.get("marcas"), cerradas=r.get("cerradas"), objetivo_hash=vm.get("objetivo_hash") or "",
            limite_juez=vm.get("limite_compilacion_s"), version_juez=vm.get("juez") or "",
            cuaderno_hash=r.get("cuaderno_hash") or "", registrado=r.get("episodio_id") in registro,
            aceptado_registro=registro.get(r.get("episodio_id"))))
    return out


class Lemas:
    """Textos de los lemas del cuaderno por nombre (cuadernos congelados y cuaderno vivo), para reconstruir la
    biblioteca de cada intento y comprobarla contra su `biblioteca_hash`."""

    def __init__(self, base: Path | None = None):
        base = Path(base) if base is not None else CUADERNO  # se lee al construir, no al importar el módulo
        self.textos: dict[str, list[str]] = defaultdict(list)
        fuentes = sorted((base / "congelados").glob("*/lemas.json")) + [base / "lemas.json"]
        for f in fuentes:
            try:
                datos = json.loads(f.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            for l in datos.get("lemas", []):
                if l.get("texto") and l["texto"] not in self.textos[l.get("nombre", "")]:
                    self.textos[l.get("nombre", "")].append(l["texto"])

    def biblioteca(self, nombres: list[str], hash_esperado: str, tope: int = 256) -> str | None:
        """El texto `"\\n\\n".join(...)` de esos lemas cuyo hash es el registrado (si un nombre tuvo varios textos, se
        prueban las combinaciones, hasta `tope`); None si ninguna coincide."""
        if not hash_esperado:
            return ""
        opciones = [self.textos.get(n, []) for n in nombres]
        if not nombres or any(not o for o in opciones):
            return None
        for combinacion in itertools.islice(itertools.product(*opciones), tope):
            texto = "\n\n".join(combinacion)
            if hash_texto(texto) == hash_esperado:
                return texto
        return None


def leer_objetivo(peldano: str) -> dict | None:
    for f in sorted(CORPUS.glob(f"*/{peldano}.json")):
        try:
            return json.loads(f.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
    return None


# ----------------------------------------------------------------------------- la referencia

PLANTILLA = r'''theory Rejuicio
  imports __IMPORTS__
begin

__PRELUDE__

ML \<open>
  val __N___ax0 = map #1 (Theory.all_axioms_of @{theory})
\<close>

__LIBRARY__

ML \<open>
  val __N___ax1 = map #1 (Theory.all_axioms_of @{theory})
\<close>

context
  fixes __FIXES__
  assumes __ASSUMES__
begin

ML \<open>
  val __N___esperado = @{prop \<open>__CONCL__\<close>}
\<close>

__AGENTLEMMAS__

theorem __N___objetivo: "__CONCL__"
__AGENTPROOF__

ML \<open>
  val __N___th = @{thm __N___objetivo}
  val _ = File.write (Path.explode "__OUTDIR__/objetivo.txt")
    ("prop_ok=" ^ (if Thm.prop_of __N___th aconv __N___esperado then "1" else "0") ^ "\n"
      ^ "oraculos=" ^ String.concatWith "," (map (fn ((n, _), _) => n) (Thm_Deps.all_oracles [__N___th])) ^ "\n"
      ^ "skip_proof=" ^ (if Thm_Deps.has_skip_proof [__N___th] then "1" else "0") ^ "\n")
\<close>

end

ML \<open>
  fun __N___nuevos antes despues = List.filter (fn a => not (List.exists (fn b => b = a) antes)) despues
  val _ = File.write (Path.explode "__OUTDIR__/axiomas.txt")
    ("biblioteca=" ^ String.concatWith "," (__N___nuevos __N___ax0 __N___ax1) ^ "\n"
      ^ "agente=" ^ String.concatWith "," (__N___nuevos __N___ax1 (map #1 (Theory.all_axioms_of @{theory}))) ^ "\n")
\<close>

end
'''

# bloque de la plantilla al que pertenece cada hueco (para atribuir los errores)
_BLOQUE_DE = {"PRELUDE": "preludio", "LIBRARY": "biblioteca", "AGENTLEMMAS": "lemas", "AGENTPROOF": "prueba"}


def nonce() -> str:
    return "rj" + "".join(random.SystemRandom().choice(string.ascii_lowercase) for _ in range(10))


def ensamblar(spec: dict, biblioteca: str, lemas: str, prueba: str, outdir: Path, n: str) -> tuple[str, dict]:
    """La teoría en UNA pasada (el texto insertado no se vuelve a examinar) y los tramos de líneas (1-based, inclusivos)
    de cada bloque: preludio, biblioteca, lemas, enunciado y prueba."""
    tabla = {"IMPORTS": spec["imports"], "PRELUDE": spec.get("prelude", ""), "LIBRARY": biblioteca, "FIXES": spec["fixes"],
             "ASSUMES": spec["assumes"], "CONCL": spec["concl"], "AGENTLEMMAS": lemas, "AGENTPROOF": prueba,
             "OUTDIR": str(outdir), "N": n}
    partes, pos, linea, tramos = [], 0, 1, {}
    for m in re.finditer(r"__([A-Z]+)__", PLANTILLA):
        trozo = PLANTILLA[pos:m.start()]
        partes.append(trozo)
        linea += trozo.count("\n")
        valor = tabla[m.group(1)]
        if m.group(1) in _BLOQUE_DE:
            tramos[_BLOQUE_DE[m.group(1)]] = (linea, linea + valor.count("\n"))
        partes.append(valor)
        linea += valor.count("\n")
        pos = m.end()
    partes.append(PLANTILLA[pos:])
    thy = "".join(partes)
    lineas = thy.splitlines()
    tramos["enunciado"] = next(((i, i) for i, l in enumerate(lineas, 1) if l.startswith(f"theorem {n}_objetivo:")), (0, 0))
    return thy, tramos


_REF_LINEA = re.compile(r'\(line (\d+) of "([^"]*)"\)')


def errores_de_log(log: str, tramos: dict, tope: int = 12) -> tuple[list[str], list[str]]:
    """Las líneas «***» y el bloque al que apunta cada una (preludio, biblioteca, lemas, enunciado, prueba o plantilla)."""
    errores, bloques = [], []
    for l in log.splitlines():
        if not (l.startswith("***") and l[3:].strip()):
            continue
        if len(errores) < tope:
            errores.append(l)
        for m in _REF_LINEA.finditer(l):
            if not m.group(2).endswith("Rejuicio.thy"):
                continue
            L = int(m.group(1))
            bloque = next((b for b, (a, z) in tramos.items() if a <= L <= z), "plantilla")
            bloques.append(bloque)
    return errores, bloques


def leer_pares(ruta: Path) -> dict[str, str] | None:
    if not ruta.exists():
        return None
    out = {}
    for l in ruta.read_text(encoding="utf-8", errors="replace").splitlines():
        if "=" in l:
            k, v = l.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def perfil_sandbox(work: Path) -> str:
    """macOS: sin red externa (Isabelle usa sockets locales) y sin escritura fuera del directorio de trabajo,
    ~/.isabelle y los temporales. La misma política que el juez, escrita aparte."""
    home = str(Path.home())
    return ('(version 1)(allow default)'
            '(deny network-outbound (remote ip))(allow network-outbound (remote ip "localhost:*"))'
            '(deny file-write* (require-all'
            f' (require-not (subpath "{Path(work).resolve()}"))'
            f' (require-not (subpath "{home}/.isabelle"))'
            ' (require-not (subpath "/private/tmp")) (require-not (subpath "/private/var/folders"))'
            ' (require-not (subpath "/dev"))))')


def compilaciones_ajenas() -> bool:
    """¿Hay una compilación de Isabelle que no sea de este guion (p. ej., el juez de una ronda en curso)?"""
    try:
        out = subprocess.run(["ps", "-ax", "-o", "command="], capture_output=True, text=True, timeout=20).stdout
    except (OSError, subprocess.SubprocessError):
        return False
    return any("Isabelle_Tool build" in l and "Rejuicio_" not in l for l in out.splitlines())


@dataclass
class Referencia:
    isabelle: Path = field(default_factory=isabelle_por_defecto)
    scratch: Path = field(default_factory=scratch_por_defecto)
    limite_s: float = 900.0
    hilos: int | None = None
    sandbox: bool = True
    cortesia: bool = True
    conservar: bool = False

    def __post_init__(self):
        self.sandbox = self.sandbox and Path("/usr/bin/sandbox-exec").exists()

    def esperar_turno(self, quieto_s: float = 4.0, paso_s: float = 2.0) -> float:
        if not self.cortesia:
            return 0.0
        t0, libre = time.monotonic(), 0.0
        while libre < quieto_s:
            libre = 0.0 if compilaciones_ajenas() else libre + paso_s
            time.sleep(paso_s)
        return time.monotonic() - t0

    def compilar(self, work: Path, thy: str, padre: str = "HOL-Analysis") -> tuple[int, str, float]:
        session = f"Rejuicio_{os.urandom(5).hex()}"
        (work / "Rejuicio.thy").write_text(thy, encoding="utf-8")
        (work / "ROOT").write_text(f'session {session} = "{padre}" +\n'
                                   "  options [document = false, timeout = 0, parallel_proofs = 0]\n"
                                   "  theories\n    Rejuicio\n", encoding="utf-8")
        cmd = [str(self.isabelle), "build", "-o", "document=false", "-d", str(work)]
        if self.hilos:
            cmd += ["-o", f"threads={self.hilos}"]
        cmd.append(session)
        if self.sandbox:
            cmd = ["/usr/bin/sandbox-exec", "-p", perfil_sandbox(work)] + cmd
        t0 = time.monotonic()
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                             errors="replace", start_new_session=True)
        try:
            out, _ = p.communicate(timeout=self.limite_s)
            return p.returncode, out, time.monotonic() - t0
        except subprocess.TimeoutExpired:
            for matar in (lambda: os.killpg(p.pid, signal.SIGKILL),
                          lambda: subprocess.run(["pkill", "-9", "-f", session], timeout=20),
                          lambda: subprocess.run(["pkill", "-9", "-f", str(work)], timeout=20)):
                try:
                    matar()
                except (OSError, subprocess.SubprocessError):
                    pass
            try:
                out, _ = p.communicate(timeout=60)
            except subprocess.TimeoutExpired:
                out = ""
            return -9, (out or "") + f"\n[rejuicio] TIEMPO tras {self.limite_s:.0f} s", time.monotonic() - t0

    def juzgar(self, spec: dict, biblioteca: str, lemas: str, prueba: str, ensayo: bool = False) -> dict:
        """Veredicto de la referencia: {'veredicto': 'acepta' | 'rechaza' | 'indeterminado', 'motivo', …}."""
        res = {"veredicto": None, "motivo": "", "rc": None, "build_s": None, "prop_ok": None, "oraculos": [],
               "skip_proof": None, "axiomas_biblioteca": [], "axiomas_agente": [], "errores": [], "bloques_error": [],
               "espera_s": 0.0, "work": None}
        w = prohibida(lemas) or prohibida(prueba)
        if w:
            return {**res, "veredicto": "rechaza", "motivo": f"F_min: el texto usa «{w}»"}
        if not prueba.strip():
            return {**res, "veredicto": "rechaza", "motivo": "sin prueba"}
        biblioteca = biblioteca_sin_redefinidos(biblioteca, lemas)
        if prohibida(biblioteca):
            return {**res, "veredicto": "indeterminado", "motivo": f"la biblioteca usa «{prohibida(biblioteca)}»"}
        self.scratch.mkdir(parents=True, exist_ok=True)
        work = Path(tempfile.mkdtemp(prefix="rj-", dir=str(self.scratch)))
        thy, tramos = ensamblar(spec, biblioteca, lemas, prueba, work, nonce())
        if ensayo:
            (work / "Rejuicio.thy").write_text(thy, encoding="utf-8")
            return {**res, "veredicto": "ensayo", "motivo": "no se compiló (--ensayo)", "work": str(work)}
        res["espera_s"] = round(self.esperar_turno(), 1)
        rc, log, dt = self.compilar(work, thy, spec.get("session_parent", "HOL-Analysis"))
        (work / "build.log").write_text(log, encoding="utf-8")
        errores, bloques = errores_de_log(log, tramos)
        res.update(rc=rc, build_s=round(dt, 1), errores=errores, bloques_error=sorted(set(bloques)), work=str(work))
        if rc == -9:
            res.update(veredicto="rechaza", motivo=f"tiempo: no terminó en {self.limite_s:.0f} s")
        elif rc == 0:
            obj, ax = leer_pares(work / "objetivo.txt"), leer_pares(work / "axiomas.txt")
            if obj is None or ax is None:
                res.update(veredicto="indeterminado", motivo="rc = 0 sin los archivos de salida")
            else:
                res.update(prop_ok=obj.get("prop_ok") == "1", skip_proof=obj.get("skip_proof") == "1",
                           oraculos=[o for o in obj.get("oraculos", "").split(",") if o],
                           axiomas_biblioteca=[a for a in ax.get("biblioteca", "").split(",") if a],
                           axiomas_agente=[a for a in ax.get("agente", "").split(",") if a])
                if res["axiomas_biblioteca"]:
                    res.update(veredicto="indeterminado", motivo=f"la biblioteca añade axiomas: {res['axiomas_biblioteca'][:3]}")
                elif res["oraculos"] or res["skip_proof"]:
                    res.update(veredicto="rechaza", motivo=f"oráculos {res['oraculos']}, skip_proof = {res['skip_proof']}")
                elif res["axiomas_agente"]:
                    res.update(veredicto="rechaza", motivo=f"axiomas nuevos: {res['axiomas_agente'][:3]}")
                elif not res["prop_ok"]:
                    res.update(veredicto="rechaza", motivo="el teorema demostrado no es, término a término, el congelado")
                else:
                    res.update(veredicto="acepta", motivo="el kernel aceptó el enunciado congelado sin oráculos ni axiomas nuevos")
        elif set(bloques) & {"biblioteca", "preludio"}:
            res.update(veredicto="indeterminado", motivo="la biblioteca (o el preludio) no compila en este peldaño")
        elif set(bloques) & {"lemas", "enunciado", "prueba"}:
            res.update(veredicto="rechaza", motivo="Isabelle rechazó la prueba o los lemas del agente")
        else:
            res.update(veredicto="indeterminado", motivo="la compilación falló fuera del texto del agente")
        return res


# ----------------------------------------------------------------------------- comparación juez / referencia


def culpa_de_la_biblioteca(intento: Intento) -> bool:
    """¿El juez atribuyó el rechazo a un lema del cuaderno? Desde el 30 sep los errores lo dicen («del cuaderno,
    línea»); antes, el lema del cuaderno aparecía como «(lema <nombre>, línea k)» con un nombre que el agente no definió."""
    textos = intento.errores + [intento.feedback]
    if any("del cuaderno, línea" in e for e in textos):
        return True
    propios = set(nombres_de_lemas(intento.lemas))
    return any(f"(lema {n}, línea" in e for n in intento.nombres_biblioteca if n not in propios for e in textos)


def rechazo_por_filtro(intento: Intento) -> bool:
    """Rechazo del filtro léxico del juez (antes de compilar): etiqueta de filtro y ningún error de Isabelle."""
    return intento.etiqueta in ETIQUETAS_FILTRO and not intento.errores


def categorizar(intento: Intento, ref: dict) -> tuple[str, str]:
    """(categoría, detalle) para un intento ya juzgado por la referencia (ver la cabecera)."""
    v = ref.get("veredicto")
    if v in (None, "ensayo"):
        return "pendiente", ref.get("motivo", "")
    if v == "indeterminado":
        return "indeterminado", ref.get("motivo", "")
    if intento.aceptado:
        return ("concordante", "los dos aceptan") if v == "acepta" else ("FP", ref.get("motivo", ""))
    if v == "rechaza":
        if culpa_de_la_biblioteca(intento):
            return "concordante_contaminado", "el juez culpó a un lema del cuaderno; la referencia, a la prueba"
        return "concordante", "los dos rechazan"
    # el juez rechazó y la referencia acepta
    if rechazo_por_filtro(intento):
        return "regla_estricta", f"{intento.etiqueta}: {intento.feedback[:160]}"
    if intento.etiqueta == "TIMEOUT":
        limite = intento.limite_juez or LIMITE_JUEZ_POR_DEFECTO
        if (ref.get("build_s") or 0) > limite:
            return "tiempo", f"la referencia tardó {ref.get('build_s')} s; el límite del juez era {limite:.0f} s"
        return "FN", "tiempo: el juez se quedó sin tiempo y la referencia terminó dentro de su límite"
    if culpa_de_la_biblioteca(intento):
        return "FN", "biblioteca: el juez culpó a un lema del cuaderno"
    return "FN", f"otro: {intento.etiqueta}"


def y_referencia(cat: str, intento: Intento) -> int | None:
    """Veredicto de V (con las reglas declaradas y el límite del juez) que el intento recibe tras la auditoría."""
    if cat in ("indeterminado", "pendiente"):
        return None
    if cat == "FN" or (cat == "concordante" and intento.aceptado):
        return 1
    return 0


# ----------------------------------------------------------------------------- orquestación


def seleccionar(desde: str, hasta: str | None, fases, configs=None, peldanos=None) -> list[Intento]:
    todos = []
    for d in corridas(desde, hasta, fases):
        todos += intentos_de(d)
    if configs:
        todos = [i for i in todos if i.config in configs]
    if peldanos:
        todos = [i for i in todos if i.peldano in peldanos]
    return todos


def preparar(intento: Intento, lemas_cuaderno: Lemas) -> tuple[dict | None, str | None, str | None]:
    """(objetivo, biblioteca, motivo de indeterminación). Comprueba el hash del objetivo y el de la biblioteca."""
    spec = leer_objetivo(intento.peldano)
    if spec is None:
        return None, None, f"no está el objetivo {intento.peldano} en {CORPUS}"
    if intento.objetivo_hash and hash_objetivo(spec) != intento.objetivo_hash:
        return None, None, f"el objetivo cambió en disco ({hash_objetivo(spec)} ≠ {intento.objetivo_hash})"
    bib = lemas_cuaderno.biblioteca(intento.nombres_biblioteca, intento.biblioteca_hash)
    if bib is None:
        return spec, None, f"no se pudo reconstruir la biblioteca {intento.biblioteca_hash} ({intento.nombres_biblioteca})"
    return spec, bib, None


def clave_de(intento: Intento, spec: dict | None, bib: str | None, limite: float) -> str:
    datos = {"v": VERSION_REFERENCIA, "obj": hash_objetivo(spec) if spec else intento.peldano, "bib": bib or "",
             "lemas": intento.lemas, "prueba": intento.prueba, "limite": limite}
    return hashlib.sha256(json.dumps(datos, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:24]


def fila(intento: Intento, ref: dict, cat: str, detalle: str, clave: str) -> dict:
    return {"clave": clave, "fase": intento.fase, "corrida": intento.corrida, "modelo": intento.modelo,
            "config": intento.config, "episodio_id": intento.episodio_id, "peldano": intento.peldano, "split": intento.split,
            "dificultad": intento.dificultad, "k": intento.k, "intento": intento.intento, "archivo": intento.archivo,
            "etiqueta_juez": intento.etiqueta, "y_juez": int(intento.aceptado), "version_juez": intento.version_juez,
            "limite_juez": intento.limite_juez, "biblioteca_hash": intento.biblioteca_hash,
            "registrado": intento.registrado, "aceptado_registro": intento.aceptado_registro,
            "culpa_biblioteca_juez": culpa_de_la_biblioteca(intento), "primer_error_juez": (intento.errores or [""])[0][:300],
            "categoria": cat, "detalle": detalle, "y_ref": y_referencia(cat, intento),
            "ref": ref, "primer_error_ref": (ref.get("errores") or [""])[0][:300],
            "referencia": VERSION_REFERENCIA, "fecha": time.strftime("%Y-%m-%dT%H:%M:%S")}


def rejuzgar(args) -> int:
    fases = tuple(args.fases.split(",")) if args.fases else FASES_RONDA
    intentos = seleccionar(args.desde, args.hasta, fases, set(args.configs.split(",")) if args.configs else None,
                           set(args.peldanos.split(",")) if args.peldanos else None)
    if args.solo == "rechazos":
        intentos = [i for i in intentos if not i.aceptado]
    elif args.solo == "aceptados":
        intentos = [i for i in intentos if i.aceptado]
    salida = RESULTADOS / args.etiqueta
    registro = salida / "rejuicio.jsonl"
    previas = leer_jsonl(registro) if not args.ensayo else []
    hechas = {f["clave"]: f for f in previas}  # una teoría ya compilada se reusa para intentos idénticos
    hechos_ids = {(f["corrida"], f["archivo"]) for f in previas}
    lemas_cuaderno = Lemas()
    ref = Referencia(isabelle=Path(args.isabelle) if args.isabelle else isabelle_por_defecto(),
                     scratch=Path(args.scratch) if args.scratch else scratch_por_defecto(), limite_s=args.limite,
                     hilos=args.hilos, sandbox=not args.sin_sandbox, cortesia=not args.sin_cortesia,
                     conservar=args.conservar)
    if not args.ensayo and not ref.isabelle.exists():
        print(f"[rejuicio] no está Isabelle en {ref.isabelle} (ISARL_ISABELLE o --isabelle)", file=sys.stderr)
        return 2
    if not args.ensayo:
        salida.mkdir(parents=True, exist_ok=True)
        (salida / "parametros.json").write_text(json.dumps({
            "desde": args.desde, "hasta": args.hasta, "fases": list(fases), "configs": args.configs,
            "peldanos": args.peldanos, "solo": args.solo, "limite_s": args.limite, "isabelle": str(ref.isabelle),
            "sandbox": ref.sandbox, "cortesia": ref.cortesia, "referencia": VERSION_REFERENCIA,
            "fecha": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "corridas": [f"{d.parent.name}/{d.name}" for d in corridas(args.desde, args.hasta, fases)]},
            ensure_ascii=False, indent=1), encoding="utf-8")

    cerrojo = threading.Lock()
    trabajos, directas = {}, []
    for it in intentos:
        if (it.corrida, it.archivo) in hechos_ids:
            continue
        if marcas_abiertas(it):
            if culpa_de_la_biblioteca(it):
                directas.append((it, {"veredicto": "indeterminado", "motivo": "marcas abiertas: el martillo corrió con "
                                      "una biblioteca que no compilaba"}, "indeterminado"))
            else:
                directas.append((it, {"veredicto": "rechaza", "motivo": "marcas `by martillo` sin cerrar"}, "sin_juicio"))
            continue
        spec, bib, motivo = preparar(it, lemas_cuaderno)
        if motivo:
            directas.append((it, {"veredicto": "indeterminado", "motivo": motivo}, "indeterminado"))
            continue
        clave = clave_de(it, spec, bib, args.limite)
        trabajos.setdefault(clave, (spec, bib, []))[2].append(it)
    pendientes = {c: t for c, t in trabajos.items() if c not in hechas}
    print(f"[rejuicio] {len(intentos)} intentos en {len(corridas(args.desde, args.hasta, fases))} corridas; "
          f"{len(directas)} sin compilar (marcas abiertas o indeterminados); {len(trabajos)} teorías distintas, "
          f"{len(pendientes)} por compilar", flush=True)
    if args.max is not None:
        pendientes = dict(list(pendientes.items())[:args.max])

    def escribir(filas: list[dict]) -> None:
        if args.ensayo:
            return
        with cerrojo, registro.open("a", encoding="utf-8") as fh:
            for f in filas:
                fh.write(json.dumps(f, ensure_ascii=False) + "\n")

    escribir([fila(it, r, cat, r["motivo"], clave_de(it, None, None, args.limite) + f"-{it.corrida}-{it.linea}")
              for it, r, cat in directas])
    for clave, (spec, bib, its) in trabajos.items():  # ya compiladas antes: se reusan para intentos nuevos idénticos
        if clave in hechas and clave not in pendientes:
            escribir([fila(it, hechas[clave]["ref"], *categorizar(it, hechas[clave]["ref"]), clave) for it in its
                      if (it.corrida, it.archivo) not in hechos_ids])

    def uno(clave: str):
        spec, bib, its = pendientes[clave]
        r = ref.juzgar(spec, bib, its[0].lemas, its[0].prueba, ensayo=args.ensayo)
        filas = [fila(it, r, *categorizar(it, r), clave) for it in its]
        if r.get("work") and not args.ensayo and not args.conservar and all(f["categoria"] == "concordante" for f in filas):
            shutil.rmtree(r["work"], ignore_errors=True)  # las teorías de los casos raros se conservan para revisarlas
        escribir(filas)
        return clave, r, filas

    hechos, t0 = 0, time.monotonic()
    with ThreadPoolExecutor(max_workers=max(1, args.paralelo)) as ex:
        futuros = [ex.submit(uno, c) for c in pendientes]
        for f in as_completed(futuros):
            clave, r, filas = f.result()
            hechos += 1
            cats = Counter(x["categoria"] for x in filas)
            print(f"[rejuicio] {hechos}/{len(pendientes)} {filas[0]['episodio_id']} #{filas[0]['intento']}: "
                  f"juez {filas[0]['etiqueta_juez']}, referencia {r['veredicto']} ({r.get('build_s')} s) → "
                  f"{', '.join(f'{k} {v}' for k, v in cats.items())}", flush=True)
    if args.ensayo:
        print(f"[rejuicio] ensayo: {len(pendientes)} teorías escritas sin compilar en {ref.scratch} "
              f"({time.monotonic() - t0:.1f} s)")
        return 0
    informe(args.etiqueta, getattr(args, "comparar", None))
    return 0


# ----------------------------------------------------------------------------- informe


COMPARACIONES_POR_DEFECTO = [("C", "E"), ("C3", "E3"), ("C", "B0"), ("C", "B")]
CATEGORIAS = ("concordante", "concordante_contaminado", "FN", "FP", "regla_estricta", "tiempo", "indeterminado", "sin_juicio")


def _fmt_p(p):
    return "—" if p is None else f"{p:.3f}".replace(".", ",")


def _fmt_x(x, dec=2):
    return "—" if x is None else f"{x:.{dec}f}".replace(".", ",")


def episodios(filas: list[dict]) -> dict[tuple, dict]:
    """(modelo, config, episodio_id) → episodio auditado, con la regla de la ronda (unirl/tools/ronda.py,
    `episodios_validos`): cuenta la primera corrida, en orden cronológico, en que el episodio terminó (tiene fila en
    episodios.jsonl) con algún intento juzgado. Si ninguna ocurrencia terminó, la primera con intentos juzgados."""
    por_ocurrencia = defaultdict(list)
    for f in filas:
        por_ocurrencia[(f["modelo"], f["config"], f["episodio_id"], f["corrida"])].append(f)
    orden = sorted(por_ocurrencia.items(), key=lambda kv: (not all(f.get("registrado", True) for f in kv[1]), kv[0][3]))
    elegidos = {}
    for (modelo, config, eid, corrida), fs in orden:
        clave = (modelo, config, eid)
        if clave in elegidos:
            continue
        fs = sorted(fs, key=lambda f: f["intento"])
        y_juez = int(any(f["y_juez"] for f in fs))
        ys = [f["y_ref"] for f in fs]
        y_ref = 1 if 1 in ys else (None if None in ys else 0)
        primero_valido = next((f["intento"] for f in fs if f["y_ref"] == 1), None)
        antes = [f for f in fs if primero_valido is None or f["intento"] < primero_valido]
        contaminado = any(f["categoria"] in ("concordante_contaminado", "indeterminado") for f in antes)
        elegidos[clave] = {"modelo": modelo, "config": config, "episodio_id": eid, "corrida": corrida,
                           "fase": fs[0]["fase"], "peldano": fs[0]["peldano"], "split": fs[0]["split"], "k": fs[0]["k"],
                           "dificultad": fs[0]["dificultad"], "y_juez": y_juez, "y_ref": y_ref, "contaminado": contaminado,
                           "intentos": len(fs), "registrado": all(f.get("registrado", True) for f in fs),
                           "aceptado_registro": fs[0].get("aceptado_registro")}
    return elegidos


def pares(eps: dict, modelo: str, a: str, b: str, unidad: str, indet: str) -> list[tuple[int, int]] | None:
    """Pares (y_a, y_b) sobre peldaños de test; unidad «episodio» (peldaño y episodio) o «peldaño» (colapsado).
    indet: 'excluir', '0' o '1' para los episodios indeterminados (y_ref = None). Con y_juez no hay indeterminados."""
    def y(e, campo):
        v = e[campo]
        if v is None:
            return None if indet == "excluir" else int(indet)
        return v

    A = {(e["peldano"], e["k"]): e for e in eps.values() if e["modelo"] == modelo and e["config"] == a and e["split"] == "test"}
    B = {(e["peldano"], e["k"]): e for e in eps.values() if e["modelo"] == modelo and e["config"] == b and e["split"] == "test"}
    comunes = sorted(set(A) & set(B))
    if not comunes:
        return None
    out = {"juez": [], "ref": []}
    for campo, nombre in (("y_juez", "juez"), ("y_ref", "ref")):
        if unidad == "episodio":
            for c in comunes:
                ya, yb = y(A[c], campo), y(B[c], campo)
                if ya is not None and yb is not None:
                    out[nombre].append((ya, yb))
        else:
            for p in sorted({c[0] for c in comunes}):
                va = [y(A[c], campo) for c in comunes if c[0] == p]
                vb = [y(B[c], campo) for c in comunes if c[0] == p]
                ya = 1 if 1 in va else (None if None in va else 0)
                yb = 1 if 1 in vb else (None if None in vb else 0)
                if ya is not None and yb is not None:
                    out[nombre].append((ya, yb))
    return out


def informe(etiqueta: str, comparar: list[str] | None = None) -> Path:
    salida = RESULTADOS / etiqueta
    filas = leer_jsonl(salida / "rejuicio.jsonl")
    # la última fila de cada intento manda (un intento re-juzgado aparece al final)
    ultimas = {}
    for f in filas:
        ultimas[(f["corrida"], f["archivo"])] = f
    filas = list(ultimas.values())
    params = json.loads((salida / "parametros.json").read_text(encoding="utf-8")) if (salida / "parametros.json").exists() else {}
    grupos = defaultdict(list)
    for f in filas:
        grupos[(f["fase"], f["modelo"], f["config"])].append(f)
    L = [f"# Re-adjudicación del juez: `{etiqueta}`", "",
         f"Generado el {time.strftime('%Y-%m-%d %H:%M')} con `unirl/tools/rejuzgar.py` ({VERSION_REFERENCIA}), sin llamar a "
         "la API. Corridas: " + (", ".join(f"`{c}`" for c in params.get("corridas", [])) or "—") + ". Referencia: "
         f"límite {params.get('limite_s', '—')} s, sandbox {'sí' if params.get('sandbox') else 'no'}. Cada intento se "
         "compara con lo que dice la especificación V aplicada por una implementación aparte (cabecera del guion).", "",
         "## 1. Veredictos por configuración (intentos)", "",
         "| fase | modelo | config | intentos | " + " | ".join(CATEGORIAS) + " |",
         "|---|---|---|---|" + "---|" * len(CATEGORIAS)]
    for (fase, modelo, config), fs in sorted(grupos.items()):
        c = Counter(f["categoria"] for f in fs)
        L.append(f"| {fase} | {modelo} | {config} | {len(fs)} | " + " | ".join(str(c.get(k, 0)) for k in CATEGORIAS) + " |")
    L += ["", "## 2. Sensibilidad y falsos positivos por configuración", "",
          "Se = intentos que el juez aceptó entre los que V acepta (con sus reglas y su límite); la cota es la de la regla "
          "de tres (95 %) cuando no hubo falsos negativos entre los rechazos re-juzgados.", "",
          "| modelo | config | V acepta | el juez acepta | FN | Se | FP | rechazos re-juzgados | cota FN si FN = 0 |",
          "|---|---|---|---|---|---|---|---|---|"]
    por_cfg = defaultdict(list)
    for f in filas:
        por_cfg[(f["modelo"], f["config"])].append(f)
    for (modelo, config), fs in sorted(por_cfg.items()):
        validos = [f for f in fs if f["y_ref"] == 1]
        fn = sum(1 for f in fs if f["categoria"] == "FN")
        fp = sum(1 for f in fs if f["categoria"] == "FP")
        acept = sum(1 for f in fs if f["y_juez"] == 1)
        rej = [f for f in fs if f["y_juez"] == 0 and f["categoria"] not in ("sin_juicio", "indeterminado", "pendiente")]
        se = (len(validos) - fn) / len(validos) if validos else None
        cota = cota_regla_de_tres(len(rej)) if fn == 0 else None
        L.append(f"| {modelo} | {config} | {len(validos)} | {acept} | {fn} | {_fmt_x(se)} | {fp} | {len(rej)} | "
                 f"{'—' if cota is None else _fmt_x(cota, 3)} |")
    L += ["", "## 3. Casos que no son concordantes", "",
          "| config | episodio | intento | juez | categoría | detalle | primer error del juez | primer error de la referencia | archivo |",
          "|---|---|---|---|---|---|---|---|---|"]
    raros = [f for f in filas if f["categoria"] not in ("concordante", "sin_juicio")]
    for f in sorted(raros, key=lambda f: (f["categoria"], f["config"], f["episodio_id"], f["intento"])):
        limpio = lambda s: (s or "").replace("|", "/").replace("\n", " ")[:140]
        L.append(f"| {f['config']} | {f['episodio_id']} | {f['intento']} | {f['etiqueta_juez']} | {f['categoria']} | "
                 f"{limpio(f['detalle'])} | {limpio(f['primer_error_juez'])} | {limpio(f['primer_error_ref'])} | `{f['archivo']}` |")
    if not raros:
        L.append("| — | — | — | — | — | — | — | — | — |")
    eps = episodios(filas)
    L += ["", "## 4. Episodios: juez frente a referencia", "",
          "Un episodio auditado vale 1 si alguno de sus intentos es válido según V; queda indeterminado si ninguno lo es y "
          "alguno no se pudo juzgar. «Contaminado»: antes del primer intento válido hubo uno cuya retroalimentación culpó "
          "al cuaderno o que no se pudo juzgar; ese episodio habría seguido otra trayectoria con un juez correcto y hay que "
          "volver a correrlo para conocer su resultado contrafactual.", "",
          "| modelo | config | episodios | aceptados (juez) | válidos (auditados) | indeterminados | contaminados |",
          "|---|---|---|---|---|---|---|"]
    por_cfg_ep = defaultdict(list)
    for e in eps.values():
        por_cfg_ep[(e["modelo"], e["config"])].append(e)
    for (modelo, config), es in sorted(por_cfg_ep.items()):
        L.append(f"| {modelo} | {config} | {len(es)} | {sum(e['y_juez'] for e in es)} | "
                 f"{sum(1 for e in es if e['y_ref'] == 1)} | {sum(1 for e in es if e['y_ref'] is None)} | "
                 f"{sum(1 for e in es if e['contaminado'])} |")
    distintos = [e for e in eps.values() if e.get("aceptado_registro") is not None and bool(e["aceptado_registro"]) != bool(e["y_juez"])]
    sin_registro = [e for e in eps.values() if not e.get("registrado", True)]
    L += ["", f"Control: {len(distintos)} episodios en que la agregación de los intentos difiere de `episodios.jsonl` "
          f"(debería ser 0) y {len(sin_registro)} episodios sin fila en `episodios.jsonl` (interrumpidos y nunca repetidos)."]
    comps = []
    for c in (comparar or []):
        partes = c.split(":")
        comps.append(tuple(partes) if len(partes) == 3 else (None, *partes))
    if not comps:
        modelos = sorted({e["modelo"] for e in eps.values()})
        comps = [(m, a, b) for m in modelos for a, b in COMPARACIONES_POR_DEFECTO]
    L += ["", "## 5. McNemar recalculado (peldaños de test)", "",
          "b = gana la segunda configuración, b' = gana la primera; p exacto bilateral. «excluir», «0» y «1»: qué se hace "
          "con los episodios indeterminados en la versión auditada.", "",
          "| comparación | unidad | veredictos | indeterminados | pares | b | b' | p |", "|---|---|---|---|---|---|---|---|"]
    resumen_mc = []
    for modelo, a, b in comps:
        modelos = [modelo] if modelo else sorted({e["modelo"] for e in eps.values()})
        for m in modelos:
            for unidad in ("episodio", "peldaño"):
                for indet in ("excluir", "0", "1"):
                    ps = pares(eps, m, a, b, unidad, indet)
                    if ps is None:
                        continue
                    for nombre, lista in (("juez", ps["juez"]), ("auditados", ps["ref"])):
                        if nombre == "juez" and indet != "excluir":
                            continue
                        bb = sum(1 for x, y in lista if y == 1 and x == 0)
                        bp = sum(1 for x, y in lista if x == 1 and y == 0)
                        p = p_mcnemar(bb, bp)
                        resumen_mc.append({"modelo": m, "a": a, "b": b, "unidad": unidad, "veredictos": nombre,
                                           "indeterminados": indet if nombre == "auditados" else "—", "pares": len(lista),
                                           "b_gana_segunda": bb, "b_prima_gana_primera": bp, "p": p})
                        L.append(f"| {m}: {a} frente a {b} | {'peldaño y episodio' if unidad == 'episodio' else 'colapsado por peldaño'} | "
                                 f"{nombre} | {indet if nombre == 'auditados' else '—'} | {len(lista)} | {bb} | {bp} | {_fmt_p(p)} |")
    L += ["", "## 6. Cómo leerlo", "",
          "* Por solidez, el juez solo puede fallar por falsos negativos; un FP aquí es una alarma: revisa el caso a mano.",
          "* Si Se cambia entre configuraciones, la comparación está sesgada hacia la de mayor Se, aunque cada veredicto "
          "por separado parezca razonable. Si Se es igual en todas, la prueba conserva su nivel y solo pierde potencia.",
          "* `regla_estricta` no es un error del juez: son pruebas válidas para el kernel que violan una regla declarada. "
          "Si su frecuencia cambia entre configuraciones, conviene saberlo.",
          "* Los episodios contaminados no se corrigen con la auditoría: hay que volver a correrlos con el juez corregido.", ""]
    ruta = salida / "resumen.md"
    ruta.write_text("\n".join(L), encoding="utf-8")
    (salida / "resumen.json").write_text(json.dumps({"parametros": params, "categorias_por_config": {
        f"{k[0]}|{k[1]}|{k[2]}": dict(Counter(f["categoria"] for f in fs)) for k, fs in grupos.items()},
        "mcnemar": resumen_mc}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[rejuicio] informe en {ruta}")
    return ruta


# ----------------------------------------------------------------------------- formato cruzado (usa el juez actual)


def candidatos_cruzado(intentos: list[Intento], lemas_cuaderno: Lemas) -> tuple[list[Intento], dict[str, str]]:
    """Las pruebas aceptadas sin biblioteca (sin repetir) en peldaños donde algún intento de la ventana tuvo biblioteca, y
    la biblioteca de cada peldaño (la primera que se reconstruye contra su hash)."""
    bibs: dict[str, str] = {}
    for it in intentos:
        if it.biblioteca_hash and it.peldano not in bibs:
            b = lemas_cuaderno.biblioteca(it.nombres_biblioteca, it.biblioteca_hash)
            if b:
                bibs[it.peldano] = b
    vistos, unicos = set(), []
    for it in intentos:
        if it.aceptado and not it.biblioteca_hash and it.peldano in bibs and not marcas_abiertas(it):
            k = (it.peldano, it.prueba, it.lemas)
            if k not in vistos:
                vistos.add(k)
                unicos.append(it)
    return unicos, bibs


def cruzado(args) -> int:
    """Cada prueba aceptada sin biblioteca se vuelve a juzgar con el juez ACTUAL dos veces: tal cual (reproducibilidad) y
    con la biblioteca que el cuaderno mostraba en ese peldaño (invariancia). Si el veredicto cambia con la biblioteca,
    el juez depende del formato del intento: justo el error diferencial de la ronda 1."""
    sys.path.insert(0, str(RAIZ))
    from unirl.gd_isabelle import TheoremVerifier  # el juez: aquí lo que se prueba es él

    fases = tuple(args.fases.split(",")) if args.fases else FASES_RONDA
    unicos, bibs = candidatos_cruzado(seleccionar(args.desde, args.hasta, fases), Lemas())
    salida = RESULTADOS / args.etiqueta
    salida.mkdir(parents=True, exist_ok=True)
    print(f"[cruzado] {len(unicos)} pruebas aceptadas sin cuaderno en peldaños donde el cuaderno mostraba lemas")
    filas = []
    for it in unicos[: args.max if args.max is not None else None]:
        juez = TheoremVerifier.desde_corpus(it.peldano)
        sola = juez.verify(juez.target(), {"proof": it.prueba, "lemmas": it.lemas})
        con = juez.verify(juez.target(), {"proof": it.prueba, "lemmas": it.lemas, "lemmas_library": bibs[it.peldano]})
        f = {"episodio_id": it.episodio_id, "intento": it.intento, "archivo": it.archivo, "peldano": it.peldano,
             "config": it.config, "juez": juez.VERSION_JUEZ, "original": it.etiqueta, "sin_biblioteca": sola.outcome_label,
             "con_biblioteca": con.outcome_label, "errores_con_biblioteca": (con.raw.get("errors") or [])[:4],
             "biblioteca_hash": hash_texto(bibs[it.peldano]), "fecha": time.strftime("%Y-%m-%dT%H:%M:%S")}
        filas.append(f)
        print(f"[cruzado] {it.episodio_id} #{it.intento}: sin biblioteca {f['sin_biblioteca']}, con biblioteca "
              f"{f['con_biblioteca']}", flush=True)
        with (salida / "cruzado.jsonl").open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(f, ensure_ascii=False) + "\n")
    L = [f"# Formato cruzado: `{args.etiqueta}`", "",
         f"Juez actual ({filas[0]['juez'] if filas else '—'}). Cada prueba aceptada sin cuaderno se juzgó de nuevo tal cual y "
         "con la biblioteca que el cuaderno mostraba en su peldaño. Lo esperado: ACCEPTED en las dos columnas. Si cambia "
         "solo con la biblioteca, el veredicto depende del formato del intento (salvo que la biblioteca traiga reglas "
         "[simp] que cambian la automatización: mira los errores).", "",
         "| episodio | intento | peldaño | original | sin biblioteca | con biblioteca | errores con biblioteca |",
         "|---|---|---|---|---|---|---|"]
    for f in filas:
        L.append(f"| {f['episodio_id']} | {f['intento']} | {f['peldano']} | {f['original']} | {f['sin_biblioteca']} | "
                 f"{f['con_biblioteca']} | {' · '.join(e.replace('|', '/')[:90] for e in f['errores_con_biblioteca'][:2])} |")
    cambios = sum(1 for f in filas if f["sin_biblioteca"] != f["con_biblioteca"])
    no_reproducidos = sum(1 for f in filas if f["sin_biblioteca"] != "ACCEPTED")
    L += ["", f"Cambios con la biblioteca: {cambios} de {len(filas)}. No reproducidos sin biblioteca: {no_reproducidos}.", ""]
    (salida / "cruzado.md").write_text("\n".join(L), encoding="utf-8")
    print(f"[cruzado] informe en {salida / 'cruzado.md'}")
    return 0


# ----------------------------------------------------------------------------- CLI


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="orden", required=True)

    def ventana(p):
        p.add_argument("--desde", required=True, help="inicio ISO de la ventana (inclusive), p. ej. 2026-09-26T20:17:27")
        p.add_argument("--hasta", help="fin ISO de la ventana (exclusivo)")
        p.add_argument("--fases", help=f"fases separadas por comas (por defecto: {','.join(FASES_RONDA)})")
        p.add_argument("--etiqueta", default=None, help="nombre de la carpeta en resultados/rejuicio/")
        p.add_argument("--max", type=int, default=None, help="como mucho N teorías (para probar)")

    p = sub.add_parser("rejuzgar", help="re-juzga con la referencia y escribe el informe")
    ventana(p)
    p.add_argument("--configs", help="solo estas configuraciones (B0,B,C,E,F,C3,E3)")
    p.add_argument("--peldanos", help="solo estos peldaños")
    p.add_argument("--solo", choices=("todos", "rechazos", "aceptados"), default="todos")
    p.add_argument("--limite", type=float, default=600.0, help="límite por compilación de la referencia (s)")
    p.add_argument("--paralelo", type=int, default=1, help="compilaciones simultáneas (cada una usa varios GB)")
    p.add_argument("--hilos", type=int, default=None, help="threads de Isabelle por compilación")
    p.add_argument("--isabelle", help="ruta al binario isabelle (por defecto, la de isarl.config)")
    p.add_argument("--scratch", help="carpeta de trabajo (por defecto ~/isabelle/scratch/rejuicio)")
    p.add_argument("--sin-sandbox", action="store_true")
    p.add_argument("--sin-cortesia", action="store_true", help="no esperar a que terminen otras compilaciones")
    p.add_argument("--conservar", action="store_true", help="conservar las teorías de los casos concordantes")
    p.add_argument("--ensayo", action="store_true", help="prepara y escribe las teorías, sin compilar ni registrar")
    p.add_argument("--comparar", action="append", help="MODELO:A:B o A:B (repetible); por defecto C:E, C3:E3, C:B0, C:B")

    p = sub.add_parser("resumen", help="rehace el informe desde rejuicio.jsonl")
    p.add_argument("--etiqueta", required=True)
    p.add_argument("--comparar", action="append")

    p = sub.add_parser("cruzado", help="formato cruzado con el juez actual")
    ventana(p)

    args = ap.parse_args(argv)
    if getattr(args, "etiqueta", None) is None and args.orden in ("rejuzgar", "cruzado"):
        args.etiqueta = "ventana-" + args.desde.replace(":", "").replace("-", "")[:13]
    if args.orden == "rejuzgar":
        return rejuzgar(args)
    if args.orden == "resumen":
        informe(args.etiqueta, args.comparar)
        return 0
    return cruzado(args)


if __name__ == "__main__":
    sys.exit(main())
