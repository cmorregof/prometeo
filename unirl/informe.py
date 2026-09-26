"""Informes de corrida en PDF con el formato de la plantilla del autor (`docs/informes/ESPEC.md`).

    python -m unirl informe --runs runs/<env>/<id> [más carpetas] --out docs/informes/<slug>
    python -m unirl informe --ultima env1,env2 --model gpt-6-luna --slug <slug>

Detecta el tipo de cada corrida (programa de Isabelle, PEP, teorema de Isabelle, grafo), agrupa varias carpetas
del mismo modelo en un informe, calcula las métricas y escribe `informe.tex`. El preámbulo se copia byte a byte de
`plantilla_v0.1.tex`, y los párrafos que la especificación pide literales se leen del mismo archivo, no se copian a
mano. Todo número sale de los datos (attempts.jsonl, meta.json, memoria.json, runs/_baseline); todo texto que
viene de los datos (propuestas del modelo, errores de Isabelle, LEEME.md) se sanea antes de entrar al .tex.
Compila con `taskpolicy -b latexmk -pdf` (prioridad mínima de macOS). No ejecuta Isabelle ni ningún juez: solo lee.
"""

from __future__ import annotations

import ast
import json
import os
import re
import shutil
import statistics
import subprocess
import time
import tomllib
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from .cli import summarize
from .report import PAPER, vc_kind
from .verifiers import IsabelleVerifier, LemmaGraphVerifier, PEPVerifier, split_lemmas

BASE = Path(__file__).resolve().parent.parent  # rl_metodos/
PKG = Path(__file__).resolve().parent  # unirl/: configs y targets viven dentro del paquete
PLANTILLA = BASE / "docs" / "informes" / "plantilla_v0.1.tex"
BIB = BASE / "docs" / "formulacion" / "unirl_definicion.bib"
RUNS = BASE / "runs" / "unirl"
INFORMES = BASE / "docs" / "informes"
TEXBIN = Path("/Library/TeX/texbin")
PROPONENTES = ("gpt-6-luna", "gpt-6-astra")
SECCIONES = ("Propósito", "El MDP común", "La interfaz de verificador y sus tres instancias", "Funciones de recompensa",
             "Métricas", "Jerarquía de confianza entre jueces", "Entornos", "Experimentos realizados y previstos")
MESES = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre")

# Referencias que no están en la .bib de la nota; se añaden solo a la copia local del informe.
BIB_EXTRA = {
    "Nesterov2018": """
% [NV] Añadida por unirl/informe.py (juez de teorema: interp <=> convexa y L-suave); sin verificar contra la fuente.
@book{Nesterov2018,
  author    = {Nesterov, Yurii},
  title     = {Lectures on Convex Optimization},
  publisher = {Springer},
  year      = {2018}
}
""",
}

# ----------------------------------------------------------------------------- saneo del texto que viene de datos

# Símbolos de Isabelle en su forma ASCII (la sintaxis ASCII de Isabelle/HOL, legible y sin Unicode).
_ISA = {"and": "&", "or": "|", "not": "~", "le": "<=", "ge": ">=", "noteq": "~=", "lceil": "ceiling(", "rceil": ")",
        "lfloor": "floor(", "rfloor": ")", "bar": "|", "exists": "EX ", "forall": "ALL ", "in": ":", "notin": "~:",
        "longrightarrow": "-->", "Longrightarrow": "==>", "longleftrightarrow": "<->", "And": "!!", "lbrakk": "[|",
        "rbrakk": "|]", "Rightarrow": "=>", "rightarrow": "->", "times": "*", "cdot": "*", "bullet": "*", "lambda": "%",
        "equiv": "==", "open": "'", "close": "'", "^sup": "^", "^sub": "_", "inter": "Int", "union": "Un",
        "subseteq": "<=", "subset": "<", "infinity": "inf", "sqrt": "sqrt", "Colon": "::", "circ": "o", "langle": "<",
        "rangle": ">", "turnstile": "|-", "comment": "--"}
# Unicode que aparece en errores de Isabelle y en textos de los modelos, a ASCII.
_UNI = {"∧": "&", "∨": "|", "¬": "~", "≤": "<=", "≥": ">=", "≠": "~=", "⌈": "ceiling(", "⌉": ")", "⌊": "floor(",
        "⌋": ")", "∃": "EX ", "∀": "ALL ", "∈": ":", "∉": "~:", "⟶": "-->", "→": "->", "⟹": "==>", "⋀": "!!",
        "⟦": "[|", "⟧": "|]", "⇒": "=>", "⟷": "<->", "×": "*", "·": "*", "λ": "%", "‹": "'", "›": "'", "—": "-",
        "–": "-", "−": "-", "“": '"', "”": '"', "‘": "'", "’": "'", "…": "...", "τ": "tau", "μ": "mu", "α": "alpha",
        "β": "beta", "γ": "gamma", "δ": "delta", "ε": "eps", "φ": "phi", "π": "pi", "σ": "sigma", "ρ": "rho",
        "θ": "theta", "ξ": "xi", "√": "sqrt", "∞": "inf", "²": "^2", "³": "^3", "₀": "0", "₁": "1", "₂": "2",
        "ₙ": "n", "ₖ": "k", "‖": "||", "∇": "grad ", "≈": "~", "∎": "", "\u00a0": " "}
# Fuera del ASCII imprimible, solo lo que inputenc utf8 + T1 aceptan sin paquetes nuevos.
_LATIN = frozenset("áéíóúÁÉÍÓÚñÑüÜ¿¡")
_LATIN_TEXTO = _LATIN | frozenset("«»")
_ESC = {"\\": r"\textbackslash{}", "{": r"\{", "}": r"\}", "$": r"\$", "&": r"\&", "#": r"\#",
        "^": r"\textasciicircum{}", "_": r"\_", "%": r"\%", "~": r"\textasciitilde{}"}
_LIG = frozenset("<>-,'`!?")  # pares que T1 convierte en ligaduras (« » ¡ ¿ – „ ”): se separan con {}
_CORTE = frozenset("/(,=+*_|:;&-")  # tras estos caracteres se permite partir un \texttt largo


def a_ascii(s, extra: frozenset = _LATIN) -> str:
    """Traduce símbolos de Isabelle (\\<and>) y Unicode conocido a ASCII y quita el resto del Unicode no admitido."""
    s = unicodedata.normalize("NFC", str(s))
    s = re.sub(r"\\<(\^?[A-Za-z][A-Za-z0-9_']*)>", lambda m: _ISA.get(m.group(1), " " + m.group(1).lstrip("^") + " "), s)
    s = s.replace("\\<", "<")  # un símbolo sin cerrar no pasa crudo
    s = "".join(_UNI.get(c, c) for c in s)
    out = []
    for c in s:
        if c in "\t\n\r":
            out.append(" ")
        elif 32 <= ord(c) < 127 or c in extra:
            out.append(c)
    return re.sub(r" {2,}", " ", "".join(out)).strip()


def escapar(s: str, cortes: bool = False) -> str:
    """Escapa los caracteres especiales de LaTeX (s ya debe ser ASCII saneado)."""
    out, prev = [], ""
    for c in s:
        if prev in _LIG and c in _LIG:
            out.append("{}")
        out.append(_ESC.get(c, c))
        if cortes and c in _CORTE:
            out.append(r"\allowbreak{}")
        prev = c
    return "".join(out)


def _recortar(s: str, n: int | None) -> str:
    return s if n is None or len(s) <= n else s[: max(0, n - 3)].rstrip() + "..."


def saneo(s, n: int | None = 300) -> str:
    """Texto de datos para texto normal: sin Unicode no admitido, recortado a n caracteres y escapado."""
    return escapar(_recortar(a_ascii(s, _LATIN_TEXTO), n))


def tt(s, n: int | None = 300) -> str:
    """Texto de datos en \\texttt{}: ASCII, recortado, escapado y con puntos de corte."""
    return r"\texttt{" + escapar(_recortar(a_ascii(s), n), cortes=True) + "}"


def lab(l: str) -> str:
    """Etiqueta del juez en versalitas, como en la plantilla (VC_OPEN → \\textsc{VC\\_Open})."""
    if not re.fullmatch(r"[A-Z0-9_]+", str(l)):
        return tt(l, 40)
    return r"\textsc{" + r"\_".join(p if p in ("VC", "VCG", "PEP") else p.capitalize() for p in l.split("_")) + "}"


def n_es(x, nd: int = 1) -> str:
    """Número con coma decimal (vale en texto y en matemáticas)."""
    if x is None:
        return "---"
    if isinstance(x, int) or (isinstance(x, float) and nd == 0):
        return f"{x:.0f}" if isinstance(x, float) else str(x)
    return f"{x:.{nd}f}".replace(".", "{,}")


def g_es(x) -> str:
    """Número con el formato más corto (%g) y coma decimal."""
    return "---" if x is None else f"{x:g}".replace(".", "{,}")


def dur(seg: float | None) -> str:
    if seg is None:
        return "---"
    seg = int(round(seg))
    h, m = seg // 3600, (seg % 3600) // 60
    return f"{h}\\,h~{m}\\,min" if h else f"{m}\\,min~{seg % 60}\\,s"


# ----------------------------------------------------------------------------- plantilla


def plantilla() -> str:
    return PLANTILLA.read_text(encoding="utf-8")


def preambulo() -> bytes:
    """Las líneas de la plantilla desde \\documentclass hasta \\newtheorem{remark}, byte a byte."""
    b = PLANTILLA.read_bytes()
    i = b.index(b"\\documentclass")
    j = b.index(b"\\newtheorem{remark}", i)
    return b[i: b.index(b"\n", j) + 1]


def _entre(texto: str, ini: str, fin: str, incluir: bool = True) -> str:
    i = texto.index(ini)
    j = texto.index(fin, i + len(ini))
    return texto[i: j + len(fin)] if incluir else texto[i + len(ini): j]


def literales() -> dict[str, str]:
    """Fragmentos que la especificación pide literales, leídos de la plantilla."""
    t = plantilla()
    met = _entre(t, "\\section{Métricas}", "\\section{Jerarquía", incluir=False)
    items = _entre(met, "\\begin{enumerate}\n", "\\end{enumerate}", incluir=False)
    return {
        "proposito1": _entre(t, "\\section{Propósito}\n\n", "\n\n", incluir=False).strip(),
        "def_mdp": _entre(t, "\\begin{definition}[Entorno", "\\end{definition}"),
        "obs_inmutable": _entre(t, "\\begin{remark}[El objetivo es inmutable]", "\\end{remark}"),
        "def_verificador": _entre(t, "\\begin{definition}[Verificador]", "\\end{definition}"),
        "recompensa": _entre(t, "\\section{Funciones de recompensa}\n", "\\section{Métricas}", incluir=False).strip(),
        "metricas_intro": met[: met.index("\\begin{enumerate}")].strip(),
        "metricas_items": [x.strip() for x in re.split(r"\n\s*\\item ", "\n" + items) if x.strip()],
        "jerarquia": _entre(t, "\\section{Jerarquía de confianza entre jueces}\n", "\\section{Entornos}", incluir=False).strip(),
    }


# ----------------------------------------------------------------------------- lectura de corridas


def leer_jsonl(path: Path) -> list[dict]:
    """Tolerante a una última línea a medio escribir (la corrida en curso escribe mientras se lee)."""
    out = []
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def episodios(intentos: list[dict], B: int) -> list[dict]:
    """Por episodio: t* = primer paso aceptado, o B si se agotó el presupuesto; None si está sin terminar
    (el mismo criterio de censura que `cli.summarize`)."""
    por = defaultdict(list)
    for r in intentos:
        por[r["episode"]].append(r)
    out = []
    for ep in sorted(por):
        rs = sorted(por[ep], key=lambda r: r["step"])
        Bep = int(rs[0].get("budget", B))
        acc = [r["step"] for r in rs if r.get("accepted")]
        evaluados = [r for r in rs if r["outcome_label"] != "PROVIDER_ERROR"]
        # sin aceptar y con parte del presupuesto gastado en fallos del proveedor: no mide t* (criterio de cli.summarize)
        sin_modelo = not acc and len(rs) >= Bep and len(evaluados) < Bep
        completo = bool(acc) or (len(rs) >= Bep and not sin_modelo)
        out.append({"ep": ep, "intentos": rs, "aceptado": bool(acc), "completo": completo, "sin_modelo": sin_modelo,
                    "t": (acc[0] if acc else Bep) if completo else None, "B": Bep})
    return out


def tipo_de(meta: dict, intentos: list[dict]) -> str:
    j = meta.get("judge", "")
    if j == "lemma_graph":
        return "grafo"
    if j == "pep":
        return "pep"
    if j == "isabelle_teorema" or any((r.get("raw") or {}).get("kind") == "theorem" for r in intentos):
        return "teorema"
    if j == "isabelle":
        return "programa"
    raise ValueError(f"juez desconocido en meta.json: {j!r}")


def procesos_unirl() -> list[dict]:
    """Corridas `python -m unirl run` vivas (solo se leen con ps; no se tocan)."""
    try:
        out = subprocess.run(["ps", "-Ao", "command="], capture_output=True, text=True, timeout=10).stdout
    except Exception:
        return []
    res = []
    for line in out.splitlines():
        toks = line.split()
        if "unirl" not in toks or "run" not in toks or "--config" not in toks:
            continue

        def arg(name, default=None):
            i = toks.index(name) if name in toks else -1
            return toks[i + 1] if 0 <= i < len(toks) - 1 else default

        cfg = None
        for cand in (Path(arg("--config")), BASE / arg("--config")):
            try:
                if cand.exists():
                    cfg = tomllib.loads(cand.read_text(encoding="utf-8"))
                    break
            except Exception:
                pass
        if not cfg:
            continue
        try:
            eps = int(arg("--episodes", 20))
        except ValueError:
            eps = None
        res.append({"env": cfg.get("name"), "model": arg("--model", cfg.get("model", "")),
                    "effort": arg("--effort", cfg.get("effort", "")), "episodes": eps})
    return res


@dataclass
class Corrida:
    carpeta: Path
    meta: dict
    intentos: list[dict]
    memoria: dict | None = None
    leeme: str | None = None
    estado: str = "terminada"  # terminada | en curso | detenida | interrumpida
    previstos: int | None = None
    tipo: str = ""
    eps: list[dict] = field(default_factory=list)
    reemplazados: list[dict] = field(default_factory=list)  # intentos sin evaluar sustituidos por una continuación
    continuaciones: list[str] = field(default_factory=list)  # ids de las corridas que repitieron episodios de esta

    @property
    def env(self) -> str:
        return self.meta.get("env", self.carpeta.parent.name)

    @property
    def id(self) -> str:
        return self.carpeta.name

    @property
    def model(self) -> str:
        return self.meta.get("model", "")

    @property
    def effort(self) -> str:
        return self.meta.get("effort", "")

    @property
    def cfg(self) -> dict:
        return self.meta.get("config", {}) or {}

    @property
    def target(self) -> dict:
        return self.meta.get("target", {}) or {}

    @property
    def B(self) -> int:
        return int(self.meta.get("budget", self.cfg.get("budget", 0)) or 0)

    @property
    def completos(self) -> list[dict]:
        return [e for e in self.eps if e["completo"]]

    @property
    def tstar(self) -> list[int]:
        return [e["t"] for e in self.completos]

    @property
    def memoria_activa(self) -> bool:
        return self.meta.get("memory", self.cfg.get("memory", "none")) not in ("none", None, "")

    @property
    def redaccion_memoria(self) -> str:
        # la primera corrida con memoria es anterior a `memory_prompt`; entonces solo existía la redacción v1
        return self.meta.get("memory_prompt") or self.cfg.get("memory_prompt") or "v1"

    @property
    def lemas_activos(self) -> bool:
        return bool(self.cfg.get("allow_lemmas", False)) or self.tipo == "teorema"

    @property
    def objetivo(self) -> str:
        return self.cfg.get("target") or self.target.get("name") or self.env


def _ultima_de(dir_env: Path, model: str) -> Path | None:
    cands = []
    if dir_env.is_dir():
        for c in dir_env.iterdir():
            if c.name.startswith("_") or not (c / "meta.json").exists():
                continue
            try:
                meta = json.loads((c / "meta.json").read_text(encoding="utf-8"))
            except Exception:
                continue
            if meta.get("model") == model:
                cands.append((meta.get("started", ""), c.name, c))
    return max(cands)[2] if cands else None


def cargar(carpeta: Path, procesos: list[dict] | None = None) -> Corrida:
    carpeta = Path(carpeta).resolve()
    meta = json.loads((carpeta / "meta.json").read_text(encoding="utf-8"))
    intentos = leer_jsonl(carpeta / "attempts.jsonl")
    c = Corrida(carpeta, meta, intentos)
    if (carpeta / "memoria.json").exists():
        try:
            c.memoria = json.loads((carpeta / "memoria.json").read_text(encoding="utf-8"))
        except Exception:
            c.memoria = None
    if (carpeta / "LEEME.md").exists():
        c.leeme = (carpeta / "LEEME.md").read_text(encoding="utf-8")
    c.tipo = tipo_de(meta, intentos)
    c.eps = episodios(intentos, c.B)
    procesos = procesos_unirl() if procesos is None else procesos
    if c.leeme is not None and re.search(r"detenid|interrump|abortad|descartad", c.leeme, re.I):
        c.estado = "detenida"
    else:
        vivo = [p for p in procesos if p["env"] == c.env and p["model"] == c.model and (not p["effort"] or p["effort"] == c.effort)]
        if vivo and _ultima_de(carpeta.parent, c.model) == carpeta:
            c.estado, c.previstos = "en curso", vivo[0]["episodes"]
        elif c.eps and not c.eps[-1]["completo"]:
            c.estado = "interrumpida"
    return c


def continuacion_de(carpeta: Path) -> dict | None:
    """continuacion.json: {"de": <id de la corrida original>, "episodio": k}. La carpeta repite, desde la memoria
    que la original tenía al final del episodio k − 1, el episodio k que en la original no se evaluó (p. ej. porque
    la API se quedó sin créditos)."""
    f = Path(carpeta) / "continuacion.json"
    if not f.exists():
        return None
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
        return d if d.get("de") and int(d.get("episodio", 0)) >= 1 else None
    except Exception:
        return None


def fusionar_continuaciones(corridas: list[Corrida], procesos: list[dict] | None = None) -> list[Corrida]:
    """Integra cada continuación en su corrida original (cargándola de la carpeta hermana si no está en la lista):
    sus intentos pasan a la original con el episodio renumerado (el episodio 1 de la continuación es el episodio k
    de la original) y los intentos de la original desde el episodio k se apartan en `reemplazados`."""
    por_id = {c.id: c for c in corridas}
    out = [c for c in corridas if continuacion_de(c.carpeta) is None]
    for c in corridas:
        d = continuacion_de(c.carpeta)
        if d is None:
            continue
        madre = por_id.get(d["de"])
        if madre is None:
            hermana = c.carpeta.parent / d["de"]
            if not (hermana / "meta.json").exists():
                out.append(c)  # sin la original no hay nada que fusionar
                continue
            madre = cargar(hermana, procesos)
            por_id[madre.id] = madre
            out.append(madre)
        k = int(d["episodio"])
        madre.reemplazados += [r for r in madre.intentos if r["episode"] >= k]
        madre.intentos = ([r for r in madre.intentos if r["episode"] < k]
                          + [dict(r, episode=r["episode"] + k - 1, continuacion=c.id) for r in c.intentos])
        madre.eps = episodios(madre.intentos, madre.B)
        madre.continuaciones.append(c.id)
        mf = (c.cfg or {}).get("memory_file")
        if mf and Path(mf).exists():
            try:
                madre.memoria = json.loads(Path(mf).read_text(encoding="utf-8"))
            except Exception:
                pass
        if c.estado == "en curso":
            madre.estado, madre.previstos = "en curso", (k - 1) + (c.previstos or 1)
        elif madre.estado != "detenida":
            madre.estado = "terminada" if all(e["completo"] or e.get("sin_modelo") for e in madre.eps) else madre.estado
    return out


def ultima_corrida(runs_root: Path, env: str, model: str) -> Path | None:
    """La corrida más reciente de runs/<env>/ con ese modelo (se ignoran carpetas que empiezan por «_»)."""
    return _ultima_de(Path(runs_root) / env, model)


def todas_las_corridas(runs_root: Path) -> list[Path]:
    out = []
    root = Path(runs_root)
    if not root.is_dir():
        return out
    for f in sorted(root.rglob("meta.json")):
        if any(p.startswith("_") for p in f.relative_to(root).parts):
            continue
        out.append(f.parent)
    return out


# ----------------------------------------------------------------------------- métricas


def _mediana(xs):
    return statistics.median(xs) if xs else None


def resumen_oficial(c: Corrida) -> dict | None:
    """La fila de `cli.summarize` para esta carpeta (misma censura de t*); None si no hay episodios completos."""
    for _ in range(3):
        try:
            rows = summarize(c.carpeta)
            return rows[0] if rows else None
        except json.JSONDecodeError:  # línea a medio escribir de una corrida en curso
            time.sleep(1)
    return None


def etiquetas(c: Corrida) -> Counter:
    return Counter(r["outcome_label"] for r in c.intentos)


def estadisticos(xs: list[float]) -> tuple:
    return (statistics.fmean(xs), statistics.median(xs), max(xs)) if xs else (None, None, None)


def duracion(c: Corrida) -> float | None:
    try:
        t0 = datetime.fromisoformat(c.meta["started"])
        t1 = max(datetime.fromisoformat(r["time"]) for r in c.intentos if r.get("time"))
        return (t1 - t0).total_seconds()
    except Exception:
        return None


def metodo(env: str) -> str:
    if env.startswith("bisection"):
        return "bisección"
    if env.startswith("fixedpoint"):
        return "punto fijo"
    if env.startswith("taylor"):
        return "Taylor"
    if env.startswith("newton"):
        return "Newton"
    if env.startswith("secant"):
        return "secante"
    if env.startswith("pep_") or env.startswith("gd_"):
        return "pasos de GD"
    return env


JUEZ_TEX = {"lemma_graph": "$V_G$", "pep": "$V_P$", "isabelle": "$V_I$", "isabelle_teorema": "$V_I$ (teorema)"}
TIPO_JUEZ = {"grafo": "$V_G$", "pep": "$V_P$", "programa": "$V_I$", "teorema": "$V_I$"}


def proponente(model: str, effort: str) -> str:
    return tt(model, 40) + (f" ({saneo(effort, 20)})" if effort else "")


def lemas_propuestos(r: dict) -> int | None:
    p = r.get("proposal")
    if not isinstance(p, dict) or "lemmas" not in p:
        return None
    return len(split_lemmas(p.get("lemmas") or ""))


def lemas_verificados(r: dict) -> int | None:
    raw = r.get("raw") or {}
    if "verified_lemmas" in raw:
        return len(raw["verified_lemmas"] or [])
    if raw.get("n_lemmas") == 0:
        return 0
    if raw.get("n_lemmas") and r["outcome_label"] in ("VC_OPEN", "ACCEPTED", "ASSEMBLY_FAILED"):
        return raw["n_lemmas"]  # pasaron la etapa 0b completos
    return None


def primer_error(r: dict, n: int = 150) -> str:
    """Primer error de Isabelle del intento, sin rutas y saneado (hasta la línea «At command»)."""
    raw = r.get("raw") or {}
    errs = raw.get("errors") or (raw.get("final") or {}).get("errors") or []
    lineas = []
    for e in errs:
        e = re.sub(r"^\*\*\*\s?", "", str(e))
        if e.startswith("At command") and lineas:
            break
        lineas.append(e.strip())
        if len(lineas) >= 4:
            break
    txt = " ".join(lineas) or raw.get("reason") or raw.get("error") or ""
    txt = re.sub(r'\(line (\d+) of "[^"]*"\)', r"(línea \1)", txt)
    txt = re.sub(r'"[^"]*/(?:isabelle|scratch)[^"]*"', '"..."', txt)
    return saneo(txt, n)


# ----------------------------------------------------------------------------- textos por juez

ETIQ_DESC = {
    "lemma_graph": {"ACCEPTED": "la cadena llega a \\textsc{Qed}", "INVALID_STEP": "dependencia no establecida o paso repetido",
                    "DISTRACTOR": "el paso es un distractor", "UNKNOWN_LEMMA": "identificador ajeno al grafo",
                    "INCOMPLETE": "todos los pasos son válidos pero la cadena no llega a \\textsc{Qed}; es un resultado por intento, no por presupuesto"},
    "pep": {"CERTIFIED": "mejora estricta de $\\tau_{\\mathrm{ref}}$ con certificado racional exacto; es la aceptación",
            "MATCHED": "sólo en modo \\texttt{match}: iguala $\\tau_{\\mathrm{ref}}$ con tolerancia relativa $10^{-4}$, sin certificado exacto",
            "INVALID_SCHEDULE": "el programa falla, se agota su tiempo o no devuelve $n$ números finitos válidos",
            "NOT_IMPROVED": "programa válido que no mejora $\\tau_{\\mathrm{ref}}$",
            "CERTIFICATION_FAILED": "mejora numérica cuyo certificado exacto falla"},
    "isabelle": {"ACCEPTED": "todas las etapas pasan: el teorema está en el kernel", "VC_OPEN": "alguna obligación sin prueba de una línea",
                 "VCG_FAILED": "la anotación no se analiza o no tipa, o \\texttt{vcg} falla",
                 "LEMMA_FAILED": "el kernel rechaza la demostración de algún lema del agente",
                 "ASSEMBLY_FAILED": "las obligaciones se cierran por separado pero el teorema ensamblado no compila",
                 "UNSOUND": "\\texttt{sorry}, \\texttt{oops}, oráculos, \\texttt{skip\\_proof} o axiomas nuevos",
                 "STATEMENT_DRIFT": "la propuesta sale de su hueco o el kernel no prueba que el programa anotado sea el congelado",
                 "TIMEOUT": "se agota el tiempo de compilación", "INVALID_PROPOSAL": "falta el invariante o el variante, o hay símbolos o comandos no admitidos"},
    "isabelle_teorema": {"ACCEPTED": "compila sin oráculos, sin \\texttt{skip\\_proof} ni axiomas nuevos y el teorema es el enunciado congelado",
                         "PROOF_FAILED": "errores en la demostración del teorema", "LEMMA_FAILED": "errores en los lemas del agente",
                         "UNSOUND": "oráculos, \\texttt{skip\\_proof}, axiomas nuevos, o \\texttt{sorry}/\\texttt{oops} en el texto",
                         "STATEMENT_DRIFT": "el teorema probado no es el congelado, el objetivo cambió en disco o hay comandos que cambian el significado",
                         "TIMEOUT": "se agota el tiempo de compilación", "INVALID_PROPOSAL": "comandos o nombres no admitidos"},
}


def labels_teorema() -> tuple[str, ...]:
    """Etiquetas del juez de teorema, leídas del código de `unirl/gd_isabelle.py` sin importarlo (sin efectos)."""
    f = BASE / "unirl" / "gd_isabelle.py"
    if f.exists():
        try:
            tree = ast.parse(f.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    vals = {}
                    for st in node.body:
                        if isinstance(st, ast.Assign) and len(st.targets) == 1 and isinstance(st.targets[0], ast.Name):
                            try:
                                vals[st.targets[0].id] = ast.literal_eval(st.value)
                            except Exception:
                                pass
                    if vals.get("name") == "isabelle_teorema" and isinstance(vals.get("LABELS"), (tuple, list)):
                        return tuple(vals["LABELS"])
        except Exception:
            pass
    return ("ACCEPTED", "PROOF_FAILED", "LEMMA_FAILED", "UNSOUND", "STATEMENT_DRIFT", "TIMEOUT", "INVALID_PROPOSAL")


def lista_etiquetas(juez: str, labels) -> str:
    desc = ETIQ_DESC.get(juez, {})
    partes = [lab(l) + (f" ({desc[l]})" if l in desc else "") for l in labels]
    return ", ".join(partes[:-1]) + " y " + partes[-1] if len(partes) > 1 else "".join(partes)


# Enunciados congelados del juez de teorema (docs/diseno_gd_isabelle.md), en matemáticas.
GD_ENUNCIADOS = {
    "gd_n1": (r"f(\mathrm{gd}\ g\ [3/2]\ x_0) - f(x_s) \le \tfrac{1}{8}\,\|x_0 - x_s\|^2", "$n = 1$ fijo; cota exacta del paso óptimo"),
    "gd_const_n2": (r"f(\mathrm{gd}\ g\ [1, 1]\ x_0) - f(x_s) \le \tfrac{1}{10}\,\|x_0 - x_s\|^2", "$n = 2$ fijo; cota exacta de Drori--Teboulle"),
    "gd_const_textbook": (r"0 < n \Longrightarrow f(\mathrm{gd}\ g\ (1,\dots,1)_n\ x_0) - f(x_s) \le \frac{\|x_0 - x_s\|^2}{2n}", "todo $n$; cota clásica"),
    "gd_const_dt": (r"f(\mathrm{gd}\ g\ (1,\dots,1)_n\ x_0) - f(x_s) \le \frac{\|x_0 - x_s\|^2}{4n + 2}", "todo $n$; cota exacta de Drori--Teboulle"),
}
CRITERIO = {"fval": r"$f(x_n) - f^*$", "gradnorm": r"$\|\nabla f(x_n)\|^2$"}
FUENTE_REF = {"ce": "búsqueda propia de 06 (entropía cruzada)", "tabla": "tabla publicada \\citep{DasGuptaVanParysRyu2024}",
              "constante": "paso constante"}


def objetivo_tex(c: Corrida) -> str:
    return tt(c.target.get("id") or c.objetivo, 60)


# ----------------------------------------------------------------------------- el informe


@dataclass
class Informe:
    corridas: list[Corrida]
    runs_root: Path
    comentario: str | None = None

    @property
    def tipo(self) -> str:
        return self.corridas[0].tipo

    @property
    def c0(self) -> Corrida:
        return self.corridas[0]

    @property
    def grupo(self) -> bool:
        return len(self.corridas) > 1

    @property
    def model(self) -> str:
        return self.c0.model

    @property
    def effort(self) -> str:
        return self.c0.effort

    @property
    def juez(self) -> str:
        return self.c0.meta.get("judge", "")

    @property
    def intentos(self) -> list[dict]:
        return [r for c in self.corridas for r in c.intentos]

    @property
    def tstar(self) -> list[int]:
        return [t for c in self.corridas for t in c.tstar]


def _nombre_corta(c: Corrida) -> str:
    return tt(c.env, 40)


def asunto(inf: Informe) -> str:
    c = inf.c0
    if inf.tipo == "programa":
        s = "bisección bajo $V_I$" if c.objetivo == "bisection" else f"{tt(c.objetivo, 30)} bajo $V_I$"
        extras = [x for x, on in (("lemas", c.lemas_activos), ("memoria", c.memoria_activa)) if on]
        s += (" con " + " y ".join(extras)) if extras else ": anotación de bucle"
    elif inf.tipo == "pep":
        s = "variantes del PEP bajo $V_P$" if inf.grupo else f"PEP {CRITERIO.get(c.target.get('objective'), '')} con $n = {c.target.get('n', '?')}$ bajo $V_P$"
    elif inf.tipo == "teorema":
        s = "cotas de GD en Isabelle ($V_I$, teorema)" if inf.grupo else f"cota de GD {tt(c.objetivo, 30)} bajo $V_I$"
    else:
        s = f"{metodo(c.env)} bajo $V_G$"
    return s


def fecha_mes(c: Corrida) -> str:
    try:
        dt = datetime.fromisoformat(c.meta["started"])
    except Exception:
        dt = datetime.fromisoformat(min(r["time"] for r in c.intentos)) if c.intentos else datetime.now()
    return f"{MESES[dt.month - 1].capitalize()} de {dt.year}"


def cabecera(inf: Informe) -> str:
    primero = min(inf.corridas, key=lambda c: c.meta.get("started", ""))
    if inf.grupo:
        ids = sorted(c.id for c in inf.corridas)
        quien = f"informe de las corridas {tt(ids[0], 60)} a {tt(ids[-1], 60)}"
    else:
        quien = f"informe de la corrida {tt(inf.c0.id, 60)}"
    return "\n".join([
        r"\title{Aprendizaje por refuerzo con verificación certificada\\como única recompensa:\\" + asunto(inf)
        + r"\\[0.4em]\large Informe de corrida del proyecto \texttt{rl\_metodos}}",
        r"\author{Carlos Manuel Orrego Franco\\Universidad Nacional de Colombia, Sede Manizales}",
        r"\date{" + fecha_mes(primero) + " --- " + quien + "}",
    ])


def _n_eps(n: int) -> str:
    return "1 episodio completo" if n == 1 else f"{n} episodios completos"


def nota_continuacion(c: Corrida) -> str:
    if not c.continuaciones:
        return ""
    k = min(r["episode"] for r in c.intentos if r.get("continuacion")) if any(r.get("continuacion") for r in c.intentos) else None
    return (f"; el episodio {k} se repitió en la corrida {', '.join(tt(x, 50) for x in c.continuaciones)}, que parte de la "
            f"memoria del final del episodio {k - 1 if k else '?'} (la corrida original lo perdió: {len(c.reemplazados)} "
            "intentos \\textsc{Provider\\_Error}, sin respuesta del modelo, que se apartan)") if k else ""


def estado_tex(c: Corrida) -> str:
    return _estado_tex(c) + nota_continuacion(c)


def _estado_tex(c: Corrida) -> str:
    n = len(c.completos)
    if c.estado == "en curso":
        prev = f" de {c.previstos} previstos" if c.previstos else ""
        return f"\\textbf{{en curso}}: {_n_eps(n)}{prev} al generar este informe"
    if c.estado == "detenida":
        return f"\\textbf{{detenida}} antes de terminar; {_n_eps(n)}"
    if c.estado == "interrumpida":
        return f"\\textbf{{interrumpida}} (el último episodio quedó sin terminar y no hay proceso vivo); {_n_eps(n)}"
    return f"terminada; {_n_eps(n)}"


def pregunta(inf: Informe) -> str:
    c = inf.c0
    m = tt(inf.model, 40)
    if inf.tipo == "programa":
        if c.lemas_activos:
            q = (f"¿basta que {m} escriba lemas auxiliares propios, cuya demostración verifica el kernel antes de usarlos, "
                 "para cerrar las obligaciones que la automatización de una línea deja abiertas?")
            if c.memoria_activa:
                q += " ¿Y ayuda recordar entre episodios los lemas ya verificados y el mejor intento?"
        else:
            q = f"¿encuentra {m}, escribiendo sólo el invariante y el variante del bucle, una anotación con la que la automatización de una línea cierre todas las obligaciones y el kernel acepte el teorema?"
    elif inf.tipo == "pep":
        q = f"¿mejora {m}, con certificado racional exacto, la mejor referencia conocida $\\tau_{{\\mathrm{{ref}}}}$ en {'cada instancia' if inf.grupo else 'esta instancia'}?"
    elif inf.tipo == "teorema":
        q = f"¿escribe {m} una demostración Isar de {'cada cota' if inf.grupo else 'la cota'} que el kernel acepte? El proponente demuestra; Isabelle verifica."
    else:
        q = f"¿ordena {m} los pasos del grafo en una cadena válida hasta \\textsc{{Qed}} sin caer en distractores?"
    return "Pregunta que responde: " + q


def s_proposito(inf: Informe, L: dict) -> str:
    c = inf.c0
    partes = []
    mem = ""
    if c.memoria_activa:
        mem = (f"Memoria entre episodios: sí (\\texttt{{{saneo(c.meta.get('memory', c.cfg.get('memory', '')), 20)}}}"
               + (f"; encabezado de la biblioteca en su redacción {saneo(c.redaccion_memoria, 10)}" if inf.tipo != "pep" else "")
               + (", que atribuye los lemas a Isabelle; la redacción v2 atribuye bien: el agente demuestra, Isabelle verifica. Se conserva v1 para comparar modelos con el mismo mensaje)"
                  if inf.tipo != "pep" and c.redaccion_memoria == "v1" else ")") + ".")
    else:
        mem = "Memoria entre episodios: no; cada episodio empieza sin historial."
    lem = ""
    if inf.tipo == "programa":
        lem = " Lemas auxiliares del agente: " + ("sí." if c.lemas_activos else "no; la única acción es la anotación del bucle.")
    B = sorted({x.B for x in inf.corridas})
    Btex = "/".join(str(b) for b in B)
    if inf.grupo:
        lista = "; ".join(f"({i}) {tt(x.env, 40)}, {tt(x.id, 40)}, {estado_tex(x)}" for i, x in enumerate(inf.corridas, 1))
        partes.append(
            f"Este informe agrupa {len(inf.corridas)} corridas del proponente {proponente(inf.model, inf.effort)} bajo {TIPO_JUEZ[inf.tipo]}"
            + (" (variante de teorema)" if inf.tipo == "teorema" else "")
            + f", una por objetivo: {lista}. Presupuesto $B = {Btex}$ intentos por episodio. {mem}{lem} {pregunta(inf)}")
    else:
        jz = {"programa": "$V_I$ en su variante de programa (anotación de un bucle en Isabelle/ITrees)", "pep": "$V_P$ (PEP)",
              "teorema": "$V_I$ en su variante de teorema", "grafo": "$V_G$ (grafo de lemas)"}[inf.tipo]
        partes.append(
            f"Esta corrida ({tt(c.id, 60)}, en \\texttt{{runs/}} bajo {tt(c.env, 60)}) usa el juez {jz} sobre el objetivo "
            f"{objetivo_tex(c)} (hash {tt(c.target.get('hash', '---'), 20)}), con el proponente {tt(c.model, 40)} y esfuerzo de razonamiento "
            f"{tt(c.effort or '---', 20)}. Presupuesto $B = {c.B}$ intentos por episodio; estado: {estado_tex(c)}. {mem}{lem} {pregunta(inf)}")
    for x in inf.corridas:
        if x.leeme:
            partes.append(f"Nota de la carpeta {tt(x.id, 60)} (\\texttt{{LEEME.md}}): «{saneo(x.leeme, 700)}»")
    p3 = ("Este informe sigue la estructura de la nota técnica: el MDP común (§2), la interfaz de verificador y sus tres "
          "instancias (§3), las funciones de recompensa (§4), las métricas (§5), la jerarquía de confianza entre jueces (§6) y "
          "los entornos (§7, Tabla~\\ref{tab:envs}); cierra con los experimentos realizados y previstos (§8), y reporta en §5 "
          "los valores medidos.")
    # \sloppy en los párrafos con identificadores mecanográficos largos: permite espacios más anchos en vez de salirse del margen
    return ("\\section{Propósito}\n\n" + L["proposito1"] + "\n\n" + "\n\n".join("{\\sloppy " + x + "\\par}" for x in partes)
            + "\n\n" + p3 + "\n")


def s_mdp(inf: Informe, L: dict) -> str:
    d = L["def_mdp"]
    c = inf.c0
    if c.memoria_activa:
        d = d.replace(r"$s_t = (T, \mathcal{C}_t, h_t)$", r"$s_t = (T, \mathcal{C}_t, h_t, M_t)$", 1)
        if inf.tipo == "pep":
            item = (r"  \item \textbf{Memoria} $M_t$: resumen del mejor intento de cada episodio anterior (su $\tau$ frente a "
                    r"$\tau_{\mathrm{ref}}$ y sus pasos). Persiste entre episodios de la corrida. El modelo está congelado: la memoria es contexto, no entrenamiento.")
        else:
            item = (r"  \item \textbf{Memoria} $M_t$: biblioteca de lemas que el agente demostró y que Isabelle verificó (se añaden "
                    r"solos a cada intento) y resumen del mejor intento de cada episodio anterior. Persiste entre episodios de la "
                    r"corrida. El modelo está congelado: la memoria es contexto, no entrenamiento.")
        lines = d.split("\n")
        k = next(i for i, l in enumerate(lines) if "\\textbf{Estado}" in l)
        lines.insert(k + 1, item)
        d = "\n".join(lines)
    o = L["obs_inmutable"]
    if inf.grupo:
        h = "; ".join(f"{tt(x.env, 40)}: {tt(x.target.get('hash', '---'), 20)}" for x in inf.corridas)
        extra = f"\\sloppy En este informe, los hashes de los objetivos son: {h}."
    else:
        extra = f"En esta corrida, el hash del objetivo es {tt(c.target.get('hash', '---'), 20)}."
    if inf.tipo == "pep":
        extra += (" En $V_P$ no existe la etiqueta \\textsc{Statement\\_Drift}: la instancia $(n, \\mu, \\text{criterio})$ la fija el "
                  "entorno y la propuesta sólo produce la sucesión de pasos; el hash es el de la etiqueta de la instancia.")
    elif inf.tipo == "grafo":
        extra += (" En $V_G$ no existe la etiqueta \\textsc{Statement\\_Drift}: el proponente sólo puede nombrar pasos del grafo, y un "
                  "identificador ajeno es \\textsc{Unknown\\_Lemma}.")
    elif inf.tipo == "programa":
        extra += (" En $V_I$ el hash cubre las importaciones, la matemática auxiliar, la plantilla del programa, las hipótesis y la "
                  "conclusión; se recalcula desde disco en cada verificación.")
    o = o.replace("\\end{remark}", extra + "\n\\end{remark}")
    return "\\section{El MDP común}\n\n" + d + "\n\n" + o + "\n"


def _baseline(runs_root: Path, nombre: str) -> dict | None:
    f = Path(runs_root) / "_baseline" / nombre
    try:
        return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None
    except Exception:
        return None


def obs_existencia_teorema() -> str:
    """Observación de existencia para el juez de teorema (stepsize): lee logs/gd_validacion.json."""
    try:
        v = json.loads((BASE / "logs" / "gd_validacion.json").read_text(encoding="utf-8"))
    except Exception:
        return ("\\begin{remark}[Existencia frente a descubrimiento]\nNo hay registro de la validación del juez de teorema "
                "(\\texttt{logs/gd\\_validacion.json}).\n\\end{remark}\n")
    ok = [(o, next(i for i in c["intentos"] if i["etiqueta"] == "ACCEPTED")) for o, c in v.get("cota_superior", {}).items() if c.get("aceptada")]
    acept = "; ".join(f"{tt(o, 30)}: variante {tt(i['variante'].split('.')[-2].replace('proof_', ''), 5)}, \\textsc{{Accepted}} en "
                      f"{n_es(i['s'], 1)}\\,s" for o, i in ok)
    ctrl = [v.get(k, {}).get("ok") for k in ("no_vacuo", "control_filtro_sorry", "control_kernel_sorry", "control_by_simp")]
    return ("\\begin{remark}[Existencia frente a descubrimiento]\n"
            "Para los objetivos con $n$ fijo existe una demostración que $V_I$ acepta: la que se genera desde un certificado "
            "racional exacto del PEP (multiplicadores $\\lambda_{ij} \\ge 0$ de las desigualdades de interpolación y una suma de "
            "cuadrados, comprobados en aritmética racional; \\texttt{targets/gd\\_cert/}), escrita en Isar como instancias de "
            "\\texttt{interp}, cuadrados no negativos y aritmética lineal. Con el juez real, con todos sus filtros: " + acept +
            f" (validación del {tt(v.get('fin', '---')[:16], 20)}, \\texttt{{logs/gd\\_validacion.json}}). La misma validación comprobó "
            "que las hipótesis son satisfacibles ($f(x) = x^2/2$, $g = \\mathrm{id}$, $x_s = 0$ en $\\mathbb{R}$), que "
            "\\texttt{sorry} lo detienen el filtro y el kernel, y que \\texttt{by simp} no demuestra el objetivo de un paso"
            + ("" if all(ctrl) else " (\\textbf{algún control falló}: ver el registro)") + ". "
            "Para los objetivos ``para todo $n$'' no hay cota superior en este juez: los teoremas son ciertos (la cota de libro de "
            "texto y la de \\citet{DroriTeboulle2014}), pero no tenemos su demostración formal. Lo que el proponente no ve es el "
            "certificado: descubrir qué desigualdades combinar, y con qué pesos, es justamente la parte difícil.\n\\end{remark}\n")


def obs_existencia(inf: Informe) -> str:
    if inf.tipo == "teorema":
        return obs_existencia_teorema()
    b = _baseline(inf.runs_root, "bisection.json")
    ub = _baseline(inf.runs_root, "upper_bound.json")
    sh = _baseline(inf.runs_root, "sh_goals.json")
    frases = []
    if b:
        raw = b["outcome"].get("raw", {})
        kinds = Counter(vc_kind(v["goal"], b.get("variant", PAPER["paper_variant"])) for v in raw.get("vcs", []) if not v.get("closed_by"))
        abiertas = ", ".join(f"{k} de {tipo}" for tipo, k in sorted(kinds.items(), key=lambda kv: -kv[1]))
        frases.append(
            f"Con la anotación del propio artículo (su invariante y su variante), $V_I$ genera {raw.get('n_vcs', '---')} obligaciones y la "
            f"automatización de una línea cierra {raw.get('n_closed_auto', '---')} en esta máquina, con Sledgehammer limitado a "
            f"{b.get('sh_timeout', '---')}\\,s por obligación: {lab(b['outcome']['outcome_label'])}, {n_es(b.get('seconds'), 0)}\\,s de juez "
            f"(\\texttt{{runs/\\_baseline/bisection.json}}). Quedan abiertas {abiertas or 'ninguna'} (clasificación heurística por la conclusión y las premisas de cada obligación).")
    if sh:
        ensayos = [g for res in sh.get("results", {}).values() for g in res if "name" in g]
        hallados = sum(bool(g.get("found")) for g in ensayos)
        frases.append(
            f"Adelgazar las premisas no basta: sobre una obligación del variante, con todas sus premisas o con una sola, y con o sin los "
            f"hechos previos de la demostración del artículo, Sledgehammer encuentra prueba en {hallados} de {len(ensayos)} ensayos de "
            f"{sh.get('timeout', '---')}\\,s (\\texttt{{sh\\_goals.json}}).")
    if ub:
        raw = ub["outcome"].get("raw", {})
        usados = ", ".join(tt(x, 40) for x in raw.get("lemmas_used", [])) or "ninguno"
        frases.append(
            f"Con la misma anotación y, como lemas del agente, las demostraciones manuales de los autores (los hechos previos, la línea "
            f"\\texttt{{smt}} del variante y \\texttt{{bisect\\_root\\_extract}}), el juez da {lab(ub['outcome']['outcome_label'])}: "
            f"{raw.get('n_closed_auto', '---')} de {raw.get('n_vcs', '---')} obligaciones cerradas, {raw.get('n_lemmas', '---')} lemas "
            f"verificados en el kernel, de los que las pruebas de una línea usan {usados}; {n_es(ub.get('seconds'), 0)}\\,s de juez "
            f"(\\texttt{{upper\\_bound.json}}). Existe, pues, una demostración que $V_I$ acepta; lo que la automatización no descubre es "
            f"justamente la parte que los autores escribieron a mano.")
    if not frases:
        frases.append("No se encontraron las mediciones de línea base (\\texttt{runs/\\_baseline}); no se reporta ninguna cifra.")
    frases.append("Por eso $V_I$ distingue tres líneas base: automatización sobre todas las premisas de \\texttt{vcg}, automatización "
                  "con un filtro de relevancia estándar, y selección de premisas como acción explícita del agente. Nunca se mezclan. "
                  "Hoy están implementadas la primera y la acción de lemas auxiliares del agente; el filtro de relevancia y la "
                  "selección de premisas son trabajo futuro.")
    return "\\begin{remark}[Existencia frente a descubrimiento]\n" + " ".join(frases) + "\n\\end{remark}\n"


def s_verificador(inf: Informe, L: dict) -> str:
    c = inf.c0
    out = ["\\section{La interfaz de verificador y sus tres instancias}", "", L["def_verificador"], ""]
    # V_G
    out += ["\\subsection{Juez de grafo de lemas ($V_G$)}", "",
            "Proviene de los subproyectos 01--05. Un objetivo $T$ es un grafo dirigido acíclico $G = (\\Lambda, D)$ de pasos "
            "$\\lambda \\in \\Lambda$, cada uno con dependencias $D(\\lambda) \\subseteq \\Lambda$, un subconjunto $\\Delta \\subset \\Lambda$ "
            "de \\emph{distractores} (pasos falsos o inaplicables, tomados de errores reales de estudiantes) y un paso distinguido "
            "\\textsc{Qed}. Una propuesta es una secuencia $a = (\\lambda_1, \\dots, \\lambda_k)$ de identificadores anónimos "
            "(\\texttt{L01}, \\texttt{L02}, \\dots, barajados con semilla fija); no se muestran los títulos de los pasos ni las "
            "refutaciones del profesor, que delatan al distractor. El juez acepta si existe $j \\le k$ con $\\lambda_j = \\textsc{Qed}$ "
            "tal que, para todo $i \\le j$,",
            "\\[",
            "  \\lambda_i \\notin \\Delta,\\quad \\lambda_i \\notin \\{\\lambda_1,\\dots,\\lambda_{i-1}\\},\\quad D(\\lambda_i) \\subseteq \\{\\lambda_1,\\dots,\\lambda_{i-1}\\};",
            "\\]",
            "lo que venga después de \\textsc{Qed} se ignora. Etiquetas, asignadas en el primer paso que falla: "
            + lista_etiquetas("lemma_graph", LemmaGraphVerifier.LABELS)
            + ". Progreso parcial: fracción del cierre de dependencias de \\textsc{Qed} establecida antes del primer fallo.", ""]
    if inf.tipo == "grafo":
        t = c.target
        out += [f"\\textbf{{En esta corrida.}} Grafo del subproyecto {tt(c.cfg.get('project', '---'), 30)}: {t.get('n_lemmas', '---')} pasos, "
                f"{t.get('n_distractors', '---')} distractores, cadena mínima de {t.get('min_length', '---')} pasos; semilla de anonimización "
                f"{c.cfg.get('seed', 0)}.", ""]
    # V_P
    out += ["\\subsection{Juez PEP ($V_P$)}", "",
            "Proviene del subproyecto 06, que se usa sin modificaciones. El objetivo es una instancia: la clase de funciones $L$-suaves "
            "($\\mu$-fuertemente) convexas con $L = 1$, un horizonte $n$, un criterio ($f(x_n) - f^*$ o $\\|\\nabla f(x_n)\\|^2$, con "
            "$\\|x_0 - x^*\\| \\le 1$) y si se admiten pasos negativos; una propuesta es un programa \\texttt{schedule(n)} que genera pasos "
            "$(h_0,\\dots,h_{n-1})$. El programa se ejecuta en un intérprete aparte (en macOS, bajo un \\emph{sandbox} sin red ni escritura "
            "en disco) y el juez puntúa, en un proceso que el programa no tocó, la sucesión literal que devuelve; las referencias se leen "
            "una sola vez al empezar. El juez resuelve el problema de estimación de desempeño (PEP) como un programa semidefinido y obtiene "
            "el peor caso $\\tau(h)$; el certificado dual es la demostración de la cota \\citep{DroriTeboulle2014,TaylorHendrickxGlineur2017}. "
            "En el modo por defecto, \\texttt{improve}, toda mejora afirmada se recalcula con tolerancias finas y se certifica en aritmética "
            "racional exacta; se acepta sólo si la cota certificada es estrictamente menor que $\\tau_{\\mathrm{ref}}$. La referencia "
            "$\\tau_{\\mathrm{ref}}$ es el mínimo entre la tabla publicada de óptimos numéricos, que sólo cubre $f(x_n) - f^*$ con $\\mu = 0$ "
            "\\citep{DasGuptaVanParysRyu2024,GrimmerShuWang2024}, y la búsqueda propia de 06 por entropía cruzada; en las variantes "
            "abiertas (norma del gradiente, fuertemente convexo, pasos negativos) sólo hay búsqueda propia. Etiquetas: "
            + lista_etiquetas("pep", PEPVerifier.LABELS) + ".", ""]
    if inf.tipo == "pep":
        filas = []
        for x in inf.corridas:
            t = x.target
            sand = {r.get("raw", {}).get("sandbox") for r in x.intentos if "sandbox" in (r.get("raw") or {})}
            filas.append(f"{tt(t.get('id', x.env), 50)} (modo {tt(t.get('mode', '---'), 12)}, $\\tau_{{\\mathrm{{ref}}}} = {n_es(t.get('tau_ref'), 7)}$, "
                         f"fuente: {FUENTE_REF.get(t.get('ref_source'), saneo(t.get('ref_source', '---'), 40))}"
                         + (f"; \\emph{{sandbox}}: {'sí' if sand == {True} else ('no' if sand == {False} else 'mixto')}" if sand else "") + ")")
        out += ["\\textbf{En esta corrida.} " + ("Instancias: " if inf.grupo else "Instancia ") + "; ".join(filas) + ".", ""]
    # V_I
    out += ["\\subsection{Juez Isabelle ($V_I$)}", "",
            "Proviene del subproyecto 08 y del marco Isabelle/ITrees \\citep{BryantHuertaFoster2026}. Un objetivo es un programa imperativo "
            "junto con un triple de Hoare de corrección total $H[P]\\,C\\,[Q]$, ambos congelados; una propuesta es una anotación "
            "$a = (\\mathit{inv}, \\mathit{var})$ de invariante y variante de bucle y, en fase 2, además lemas auxiliares con su "
            "demostración, escritos por el agente y verificados en el kernel antes de usarse. El juez procede por etapas: (0) la anotación "
            "pasa una lista blanca de símbolos y el kernel demuestra que el programa anotado es igual al congelado con anotaciones fijas; "
            "(0b) si hay lemas, pasan un filtro léxico (sólo enunciados con su demostración: nada de \\texttt{sorry}, definiciones, notación "
            "ni ML) y se compilan en el contexto de las hipótesis, comprobando que el enunciado congelado se lee igual y que no aparecen "
            "axiomas nuevos; (1) inserta la anotación y ejecuta el generador de condiciones de verificación \\texttt{vcg}; (2) intenta "
            "cerrar cada obligación con automatización de una línea (\\texttt{try0} y, si falla, Sledgehammer con tiempo límite fijo), y "
            "sólo cuenta una sugerencia de Sledgehammer si su reconstrucción (\\emph{preplay}) terminó; (3) si todas cierran, ensambla el "
            "teorema completo, lo compila y lo traslada al programa congelado; (4) comprueba que no dependa de oráculos, de "
            "\\texttt{skip\\_proof} ni de axiomas nuevos. Etiquetas: " + lista_etiquetas("isabelle", IsabelleVerifier.LABELS)
            + ". Progreso parcial: fracción de obligaciones cerradas en \\textsc{VC\\_Open} y \\textsc{Assembly\\_Failed}, y $0$ en las demás.", ""]
    if inf.tipo == "programa":
        cfg = c.cfg
        prest = ", ".join(tt(re.split(r"\s*\(", s)[0], 40) for s in c.target.get("borrowed_lemmas", [])) or "ninguno"
        code = c.meta.get("code", {})
        out += [f"\\textbf{{En esta corrida.}} Objetivo {objetivo_tex(c)} (hash {tt(c.target.get('hash', '---'), 20)}); lemas prestados: {prest}. "
                f"\\texttt{{try0}}: {cfg.get('try0_timeout', 5)}\\,s; Sledgehammer: {cfg.get('sh_timeout', 60)}\\,s por obligación; límite de "
                f"compilación: {g_es(cfg.get('build_timeout_s', 1800))}\\,s. Lemas del agente: {'sí' if c.lemas_activos else 'no'}; memoria: "
                f"{'sí' if c.memoria_activa else 'no'}. Código de \\texttt{{unirl}}: huella {tt(code.get('unirl_sha256', '---'), 20)}, commit "
                f"{tt(code.get('git_commit', '---'), 12)}{' con cambios sin versionar' if code.get('unirl_dirty') else ''}.", ""]
    if inf.tipo == "teorema":
        labs_t = labels_teorema()
        items = []
        for x in inf.corridas:
            e = GD_ENUNCIADOS.get(x.objetivo)
            if e:
                items.append(f"  \\item {tt(x.objetivo, 30)} ({e[1]}; hash {tt(x.target.get('hash', '---'), 20)}):\n  \\[ {e[0]} \\]")
            else:
                items.append(f"  \\item {tt(x.objetivo, 30)} (hash {tt(x.target.get('hash', '---'), 20)}): {tt(x.target.get('concl', '---'), 300)}.")
        out += ["\\textbf{Variante de teorema.} El objetivo es un teorema puro de Isabelle/HOL sobre un espacio con producto interno; la "
                "acción del agente es la demostración (texto Isar) más lemas auxiliares opcionales, y el juez sólo compila: no añade "
                "automatización. Hipótesis congeladas, con $L = 1$: $f(y) + \\langle g(y), x - y\\rangle + \\tfrac12\\|g(x) - g(y)\\|^2 \\le f(x)$ "
                "para todo $x, y$ (\\texttt{interp}) y $g(x_s) = 0$ (\\texttt{opt}); $\\mathrm{gd}\\ g\\ hs\\ x_0$ aplica "
                "$x_{k+1} = x_k - h_k\\, g(x_k)$ con los pasos de la lista $hs$. El enunciado leído antes y después del texto del agente debe "
                "coincidir término a término, y el teorema se exporta al contexto global usando sólo \\texttt{interp} y \\texttt{opt}. "
                "Etiquetas: " + lista_etiquetas("isabelle_teorema", labs_t) + ". Enunciados de este informe:",
                "\\begin{itemize}", *items, "\\end{itemize}", ""]
    out.append(obs_existencia(inf))
    return "\n".join(out)


def s_recompensa(inf: Informe, L: dict) -> str:
    c = inf.c0
    shaped = {bool(x.meta.get("shaped")) for x in inf.corridas}
    betas = {float(x.meta.get("beta", 0.0) or 0.0) for x in inf.corridas}
    deltas = {float(x.cfg.get("drift_penalty", 0.0) or 0.0) for x in inf.corridas}
    if shaped == {False}:
        r = "recompensa base binaria $r(o)$; la moldeada está desactivada ($\\beta = 0$)"
    else:
        r = "recompensa moldeada $r_\\beta$ con $\\beta \\in \\{" + ", ".join(g_es(b) for b in sorted(betas)) + "\\}$"
    d = ("penalización de deriva $\\delta = " + "/".join(g_es(x) for x in sorted(deltas)) + "$"
         + (" (\\textsc{Statement\\_Drift} recibe $0$)" if deltas == {0.0} else ""))
    extra = ""
    if inf.tipo == "pep":
        extra = (" La recompensa continua $r_P$ de 06 se registra en cada intento (\\texttt{raw.reward06}) y sus valores se reportan en §5; "
                 "no entra en la recompensa del MDP. En el modo \\texttt{improve} la aceptación es la binarización de $r_P$ con certificado "
                 "exacto: mejora estricta de $\\tau_{\\mathrm{ref}}$ certificada.")
    if inf.tipo in ("programa", "teorema", "grafo"):
        extra = " En esta corrida el proponente no aprende de la recompensa: el modelo está congelado y la recompensa se registra."
    return ("\\section{Funciones de recompensa}\n\n" + L["recompensa"] + "\n\n\\medskip\\noindent\\textbf{En esta corrida:} "
            + r + "; " + d + "." + extra + "\n")


def _tabla(spec: str, cabeza: str, filas: list[str], caption: str, label: str, tam: str = "\\footnotesize") -> str:
    # \tabcolsep algo menor que el de LaTeX (6 pt): las tablas anchas caben sin paquetes fuera de la plantilla
    return "\n".join(["\\begin{table}[!ht]", "\\centering", tam, "\\setlength{\\tabcolsep}{4pt}", "\\begin{tabular}{" + spec + "}", "\\toprule", cabeza + " \\\\",
                      "\\midrule", *[f + " \\\\" for f in filas], "\\bottomrule", "\\end{tabular}",
                      "\\caption{" + caption + "}", "\\label{" + label + "}", "\\end{table}"])


def tabla_etiquetas(inf: Informe) -> str:
    cnts = [etiquetas(x) for x in inf.corridas]
    todas = sorted({l for c in cnts for l in c}, key=lambda l: (l != "ACCEPTED" and l != "CERTIFIED", l))
    if inf.grupo:
        cab = "etiqueta & " + " & ".join(f"({i})" for i in range(1, len(inf.corridas) + 1)) + " & total"
        filas = [lab(l) + " & " + " & ".join(str(c.get(l, 0)) for c in cnts) + f" & {sum(c.get(l, 0) for c in cnts)}" for l in todas]
        filas.append("intentos & " + " & ".join(str(len(x.intentos)) for x in inf.corridas) + f" & {len(inf.intentos)}")
        spec = "@{}l" + "r" * (len(inf.corridas) + 1) + "@{}"
        cap = "Etiquetas del juez sobre todos los intentos; las columnas siguen la numeración de las corridas en §1."
    else:
        cab = "etiqueta & intentos"
        filas = [lab(l) + f" & {cnts[0].get(l, 0)}" for l in todas] + [f"total & {len(inf.intentos)}"]
        spec = "@{}lr@{}"
        cap = "Etiquetas del juez sobre todos los intentos de la corrida."
    return _tabla(spec, cab, filas, cap, "tab:etiquetas")


def _abiertas(r: dict) -> str:
    raw = r.get("raw") or {}
    var = (r.get("proposal") or {}).get("variant", "") if isinstance(r.get("proposal"), dict) else ""
    k = Counter(vc_kind(v["goal"], var) for v in raw.get("vcs", []) if not v.get("closed_by"))
    abbr = {"invariante": "inv.", "variante": "var.", "postcondición": "post.", "inicialización": "ini."}
    return ", ".join(f"{abbr.get(t, t)} {n}" for t, n in sorted(k.items())) or ("---" if not raw.get("n_vcs") else "ninguna")


def tablas_programa(inf: Informe) -> str:
    out = []
    for x in inf.corridas:
        lem = x.lemas_activos
        cab = "ep. & paso & etiqueta & VCs cerradas & abiertas (tipo)" + (" & lemas prop. & lemas verif." if lem else "") + " & s juez & s LLM"
        filas = []
        for r in sorted(x.intentos, key=lambda r: (r["episode"], r["step"])):
            raw = r.get("raw") or {}
            vcs = f"{raw['n_closed_auto']}/{raw['n_vcs']}" if raw.get("n_vcs") else "---"
            f = f"{r['episode']} & {r['step']} & {lab(r['outcome_label'])} & {vcs} & {_abiertas(r)}"
            if lem:
                lp, lv = lemas_propuestos(r), lemas_verificados(r)
                f += f" & {'---' if lp is None else lp} & {'---' if lv is None else lv}"
            f += f" & {n_es(float(r.get('cost_s', 0.0)), 0)} & {n_es(float(r.get('llm_s', 0.0)), 0)}"
            filas.append(f)
        spec = "@{}rrlrl" + ("rr" if lem else "") + "rr@{}"
        cap = ("Intentos en orden. ``VCs cerradas'' cuenta las obligaciones con prueba de una línea; el tipo de cada VC abierta "
               "(invariante, variante, postcondición, inicialización) se asigna por su conclusión y sus premisas (heurística de \\texttt{unirl/report.py}).")
        if lem:
            cap += (" ``Lemas prop.'' son los que el agente escribió en ese intento; ``lemas verif.'', los que el kernel verificó en ese "
                    "intento, incluidos los de la biblioteca de la memoria; --- indica que el registro de la corrida no lo guarda.")
        for k in range(0, len(filas), 36):
            out.append(_tabla(spec, cab, filas[k:k + 36], cap + (f" (parte {k // 36 + 1})" if len(filas) > 36 else ""),
                              f"tab:intentos-{x.env}-{k // 36}"))
        # biblioteca final y mejor intento
        det = []
        if x.memoria_activa:
            lib = list((x.memoria or {}).get("library", {}))
            det.append(f"Biblioteca de la memoria al generar el informe ({len(lib)} lemas, que {tt(x.model, 40)} demostró y cuya demostración "
                       f"Isabelle verificó): " + (", ".join(tt(n, 50) for n in lib) if lib else "vacía") + ".")
        con = [r for r in x.intentos if (r.get("raw") or {}).get("n_vcs")]
        if con:
            best = max(con, key=lambda r: (r.get("accepted"), r["raw"]["n_closed_auto"] / r["raw"]["n_vcs"]))
            p = best.get("proposal") or {}
            # texto mecanográfico largo: alineado a la izquierda para que no se salga del margen
            det.append(f"{{\\raggedright Mejor intento por fracción de obligaciones cerradas: episodio {best['episode']}, paso {best['step']}, "
                       f"{best['raw']['n_closed_auto']} de {best['raw']['n_vcs']} ({lab(best['outcome_label'])}). Invariante: "
                       f"{tt(p.get('invariant', ''), 420)}. Variante: {tt(p.get('variant', ''), 160)}.\\par}}")
        fallos = [r for r in x.intentos if r["outcome_label"] in ("LEMMA_FAILED", "VCG_FAILED", "ASSEMBLY_FAILED", "TIMEOUT", "INVALID_PROPOSAL", "STATEMENT_DRIFT", "UNSOUND")]
        if fallos:
            det.append("Primer error de Isabelle (o motivo del juez) en los intentos que no llegaron a las obligaciones, saneado y recortado:")
            det.append("\\begin{itemize}\n" + "\n".join(f"  \\item ep.~{r['episode']}, paso {r['step']}, {lab(r['outcome_label'])}: {primer_error(r)}"
                                                           for r in fallos) + "\n\\end{itemize}")
        if det:
            out.append("\n\n".join(det))
    return "\n\n".join(out)


def _mejor_pep(x: Corrida) -> dict:
    val = [r for r in x.intentos if (r.get("raw") or {}).get("tau") is not None]
    rp = [float((r.get("raw") or {}).get("reward06")) for r in x.intentos if (r.get("raw") or {}).get("reward06") is not None]
    res = {"validos": len(val), "rp_max": max(rp) if rp else None, "certificado": any(r["outcome_label"] == "CERTIFIED" for r in x.intentos),
           "tau": None, "h": None}
    if val:
        def tau_de(r):
            raw = r["raw"]
            return raw["tau_cert"] if raw.get("certified") and raw.get("tau_cert") is not None else raw["tau"]
        b = min(val, key=tau_de)
        res["tau"], res["h"] = tau_de(b), b["raw"].get("h")
    return res


def tablas_pep(inf: Informe) -> str:
    filas, filas_h = [], []
    for i, x in enumerate(inf.corridas, 1):
        t = x.target
        m = _mejor_pep(x)
        ac = sum(e["aceptado"] for e in x.completos)
        filas.append(f"({i}) & {t.get('n', '---')} & {g_es(t.get('mu'))} & {CRITERIO.get(t.get('objective'), tt(t.get('objective', '---'), 12))} & "
                     f"{'sí' if t.get('negative') else 'no'} & {n_es(t.get('tau_ref'), 7)} ({saneo(t.get('ref_source', '---'), 12)}) & "
                     f"{n_es(m['tau'], 7)} & {n_es(m['rp_max'], 4)} & {'sí' if m['certificado'] else 'no'} & {ac}/{len(x.completos)} & "
                     f"{g_es(_mediana(x.tstar))}")
        h = m["h"]
        filas_h.append(f"({i}) & " + (", ".join(n_es(float(v), 4) for v in h) if h else "---"))
    cab = ("& $n$ & $\\mu$ & criterio & neg. & $\\tau_{\\mathrm{ref}}$ (fuente) & mejor $\\tau$ & mejor $r_P$ & \\textsc{Certified} & acept. & $t^*$ med.")
    cap = ("Por instancia: $\\tau_{\\mathrm{ref}}$ y su fuente (\\texttt{ce}: búsqueda propia de 06 por entropía cruzada; \\texttt{tabla}: "
           "óptimos publicados), el mejor peor caso $\\tau$ entre los programas válidos (el certificado si lo hay), el mayor $r_P$ registrado "
           "(\\texttt{raw.reward06}), si hubo \\textsc{Certified}, episodios aceptados sobre completos y $t^*$ mediano (censurado en $B$).")
    out = [_tabla("@{}lrrlcrrrcrr@{}", cab, filas, cap, "tab:instancias", "\\scriptsize")]
    out.append(_tabla("@{}ll@{}", "& mejores pasos $h$ (en unidades de $1/L$)", filas_h,
                      "Pasos del programa con el mejor $\\tau$ de cada instancia, redondeados a cuatro decimales.", "tab:pasos"))
    return "\n\n".join(out)


def tablas_teorema(inf: Informe) -> str:
    filas = []
    for x in inf.corridas:
        et = etiquetas(x)
        lv = [v for v in (lemas_verificados(r) for r in x.intentos) if v is not None]
        filas.append(f"{tt(x.objetivo, 30)} & {'sí' if any(e['aceptado'] for e in x.completos) else 'no'} & "
                     f"{sum(e['aceptado'] for e in x.completos)}/{len(x.completos)} & {g_es(_mediana(x.tstar))} & "
                     + ", ".join(f"{lab(l)} {n}" for l, n in sorted(et.items())) + f" & {max(lv) if lv else '---'}")
    out = [_tabla("@{}lcrrp{4.6cm}r@{}", "objetivo & aceptado & ep. acept. & $t^*$ med. & etiquetas & lemas verif. (máx.)", filas,
                  "Por objetivo: episodios aceptados sobre completos, $t^*$ mediano (censurado en $B$), etiquetas de todos los intentos y "
                  "el mayor número de lemas verificados en un intento.", "tab:objetivos")]
    filas2 = []
    for x in inf.corridas:
        for r in sorted(x.intentos, key=lambda r: (r["episode"], r["step"])):
            lp, lv = lemas_propuestos(r), lemas_verificados(r)
            filas2.append(f"{tt(x.objetivo, 30)} & {r['episode']} & {r['step']} & {lab(r['outcome_label'])} & {'---' if lp is None else lp} & "
                          f"{'---' if lv is None else lv} & {n_es(float(r.get('cost_s', 0.0)), 0)} & {n_es(float(r.get('llm_s', 0.0)), 0)}")
    for k in range(0, len(filas2), 36):
        out.append(_tabla("@{}lrrlrrrr@{}", "objetivo & ep. & paso & etiqueta & lemas prop. & lemas verif. & s juez & s LLM", filas2[k:k + 36],
                          "Intentos en orden." + (f" Parte {k // 36 + 1}." if len(filas2) > 36 else ""), f"tab:intentos-{k // 36}"))
    fallos = [(x, r) for x in inf.corridas for r in x.intentos if not r.get("accepted") and r["outcome_label"] != "PROVIDER_ERROR"]
    if fallos:
        out.append("{\\raggedright\\sloppy Primer error de Isabelle (o motivo del juez) en los intentos no aceptados, saneado y recortado:\n\\begin{itemize}\n"
                   + "\n".join(f"  \\item {tt(x.objetivo, 30)}, ep.~{r['episode']}, paso {r['step']}, {lab(r['outcome_label'])}: {primer_error(r, 120)}"
                               for x, r in fallos[:40]) + "\n\\end{itemize}\n\\par}")
    return "\n\n".join(out)


def tablas_grafo(inf: Informe) -> str:
    filas = []
    for x in inf.corridas:
        for e in x.eps:
            seq = ", ".join(lab(r["outcome_label"]) for r in e["intentos"])
            filas.append(f"{tt(x.env, 30)} & {e['ep']} & {len(e['intentos'])} & {'---' if e['t'] is None else e['t']} & {seq}")
    out = []
    for k in range(0, len(filas), 40):
        out.append(_tabla("@{}lrrrl@{}", "entorno & ep. & intentos & $t^*$ & etiquetas en orden", filas[k:k + 40],
                          "Episodios en orden." + (f" Parte {k // 40 + 1}." if len(filas) > 40 else ""), f"tab:episodios-{k // 40}"))
    return "\n\n".join(out)


def tabla_comparacion(inf: Informe) -> tuple[str, list[dict]]:
    met = metodo(inf.c0.env)
    rows = []
    for _ in range(3):
        try:
            rows = summarize(inf.runs_root)
            break
        except json.JSONDecodeError:
            time.sleep(1)
    rows = [r for r in rows if metodo(r["env"]) == met]
    mios = {(x.env, x.model, x.effort) for x in inf.corridas}
    filas = []
    for r in sorted(rows, key=lambda r: (r["judge"], r["env"], r["model"])):
        marca = "$^\\ast$" if (r["env"], r["model"], r["effort"]) in mios else ""
        filas.append(f"{tt(r['env'], 40)}{marca} & {JUEZ_TEX.get(r['judge'], tt(r['judge'], 20))} & {proponente(r['model'], r['effort'])} & "
                     f"{r['episodes']} & {r['accepted_eps']} & {'/'.join(map(str, r['budget']))} & {g_es(r['tstar_median'])} & {r['attempts'] - r['outcomes'].get('PROVIDER_ERROR', 0)} & "
                     f"{n_es(r['judge_s_mean'], 1)} & {n_es(r['llm_s_mean'], 1)}")
    if not filas:
        return "", rows
    t = _tabla("@{}llllrrrrrr@{}", "entorno & juez & proponente & ep. & acept. & $B$ & $t^*$ med. & intentos & s juez & s LLM", filas,
               f"Corridas del mismo método ({met}) en \\texttt{{runs/}} (se ignoran las carpetas que empiezan por ``\\_''), agrupadas por "
               "entorno, juez y proponente como en \\texttt{python -m unirl summary}. ``ep.'' cuenta episodios completos; los segundos son "
               "medias por intento evaluado; ``intentos'' no cuenta los \\textsc{Provider\\_Error} (sin respuesta del modelo). $^\\ast$: entornos y proponente de este informe.", "tab:comparacion", "\\scriptsize")
    return t, rows


def s_metricas(inf: Informe, L: dict) -> str:
    items = list(L["metricas_items"])
    c = inf.c0
    med = []
    # (1) t*
    partes = []
    for i, x in enumerate(inf.corridas, 1):
        of = resumen_oficial(x)
        m = of["tstar_median"] if of else None
        pre = f"({i}) " if inf.grupo else ""
        por_ep = ", ".join(f"ep.~{e['ep']}: {e['t']}{'' if e['aceptado'] else ' (sin aceptar)'}" for e in x.completos) or "ninguno completo"
        s = (f"{pre}$t^*$ mediana ${g_es(m)}$ sobre {_n_eps(len(x.completos))}, censurada en $B = {x.B}$; por episodio: {por_ep}; "
             f"aceptados {sum(e['aceptado'] for e in x.completos)} de {len(x.completos)}.")
        sin = [e for e in x.eps if not e["completo"]]
        if sin:
            s += " " + "; ".join(f"El episodio {e['ep']} tiene {len(e['intentos'])} intentos y está sin terminar ({x.estado}): no entra en $t^*$" for e in sin) + "."
        partes.append(s)
    if inf.grupo and inf.tstar:
        partes.append(f"En conjunto, $t^*$ mediana ${g_es(statistics.median(inf.tstar))}$ sobre {_n_eps(len(inf.tstar))}.")
    med.append(" ".join(partes))
    # (2) etiquetas
    med.append(f"Tabla~\\ref{{tab:etiquetas}}: {len(inf.intentos)} intentos en total.")
    # (3) deriva
    et = Counter(r["outcome_label"] for r in inf.intentos)
    if inf.tipo == "programa":
        a, b = et.get("STATEMENT_DRIFT", 0), et.get("VC_OPEN", 0)
        med.append(f"\\textsc{{Statement\\_Drift}}/\\textsc{{VC\\_Open}} $= {a}/{b}$" + (f" $= {n_es(a / b, 2)}$" if b else "") + ".")
    elif inf.tipo == "teorema":
        a, b = et.get("STATEMENT_DRIFT", 0), et.get("PROOF_FAILED", 0)
        med.append(f"En la variante de teorema el análogo de \\textsc{{VC\\_Open}} es \\textsc{{Proof\\_Failed}}: \\textsc{{Statement\\_Drift}}/\\textsc{{Proof\\_Failed}} $= {a}/{b}$"
                   + (f" $= {n_es(a / b, 2)}$" if b else "") + ".")
    elif inf.tipo == "grafo":
        a, b = et.get("DISTRACTOR", 0), et.get("INVALID_STEP", 0)
        med.append(f"\\textsc{{Distractor}}/\\textsc{{Invalid\\_Step}} $= {a}/{b}$" + (f" $= {n_es(a / b, 2)}$" if b else "") + ".")
    else:
        med.append(f"$V_P$ no tiene etiqueta de deriva (la instancia la fija el entorno); se reporta el conteo de \\textsc{{Invalid\\_Schedule}}: "
                   f"{et.get('INVALID_SCHEDULE', 0)} de {len(inf.intentos)} intentos.")
    # (4) transferencia
    if any(x.memoria_activa for x in inf.corridas):
        med.append("No aplica: la memoria de esta corrida recuerda entre episodios del \\emph{mismo} objetivo; no es transferencia "
                   "entre objetivos, y no se midió ninguna.")
    else:
        med.append("No se midió: la transferencia entre objetivos está prevista y no implementada; los episodios de esta corrida "
                   "empiezan sin historial.")
    # (5) comparación
    tcomp, rows = tabla_comparacion(inf)
    med.append(("Tabla~\\ref{tab:comparacion}." if tcomp else "No hay otras corridas del mismo método con episodios completos.")
               + " Los enunciados de $V_G$ y $V_I$ no coinciden, así que la comparación es indirecta.")
    # (6) costo
    evaluados = [r for r in inf.intentos if r["outcome_label"] != "PROVIDER_ERROR"]
    n_prov = len(inf.intentos) - len(evaluados)
    cj = [float(r.get("cost_s", 0.0)) for r in evaluados]
    cl = [float(r.get("llm_s", 0.0)) for r in evaluados]
    mj, ej, xj = estadisticos(cj)
    ml, el, xl = estadisticos(cl)
    durs = [duracion(x) for x in inf.corridas]
    dtxt = "; ".join((f"({i}) " if inf.grupo else "") + dur(d) for i, d in enumerate(durs, 1))
    if any(x.continuaciones for x in inf.corridas):
        dtxt += (" (desde el inicio de la corrida original hasta el último intento de la continuación; incluye la pausa "
                 "entre ambas carpetas)")
    med.append(f"Segundos de juez por intento: media {n_es(mj, 1)}, mediana {n_es(ej, 1)}, máximo {n_es(xj, 1)}; segundos de modelo: media "
               f"{n_es(ml, 1)}, mediana {n_es(el, 1)}, máximo {n_es(xl, 1)}. Suma: {n_es(sum(cj), 0)}\\,s de juez y {n_es(sum(cl), 0)}\\,s de modelo. "
               f"Duración desde el inicio hasta el último intento registrado: {dtxt}."
               + (f" Se excluyen {n_prov} intentos \\textsc{{Provider\\_Error}}: el modelo no respondió (tiempo agotado o "
                  "cuenta de OpenAI sin créditos) y el juez no evaluó nada; tampoco cuentan en $t^*$ los episodios cuyo "
                  "presupuesto se gastó en esos fallos." if n_prov else ""))
    body = ["\\section{Métricas}", "", L["metricas_intro"], "\\begin{enumerate}"]
    for it, m in zip(items, med):
        body.append("  \\item " + it + "\n\n  \\emph{En esta corrida:} " + m)
    body.append("\\end{enumerate}")
    body.append(tabla_etiquetas(inf))
    if tcomp:
        body.append(tcomp)
    body.append({"programa": tablas_programa, "pep": tablas_pep, "teorema": tablas_teorema, "grafo": tablas_grafo}[inf.tipo](inf))
    return "\n\n".join(body) + "\n"


def s_jerarquia(inf: Informe, L: dict) -> str:
    c = inf.c0
    if inf.tipo == "programa":
        prest = ", ".join(tt(re.split(r"\s*\(", s)[0], 40) for s in c.target.get("borrowed_lemmas", [])) or "ninguno"
        r = (f"los lemas prestados ({prest}), copiados con sus demostraciones: el kernel comprueba esas demostraciones, pero su elección es "
             "humana; la adecuación de la tripleta congelada al enunciado informal de la bisección; y el modelo del programa en números "
             "reales, no en punto flotante.")
        if c.lemas_activos:
            r += (" Los lemas del agente no añaden residuo de corrección, porque el kernel verifica sus demostraciones antes de usarlos; "
                  "sí lo añaden a la interpretación: el juez no decide si un lema ``auxiliar'' ya contiene la prueba pedida, como muestra "
                  "la cota superior de la Observación~2.")
    elif inf.tipo == "pep":
        fuentes = {x.target.get("ref_source") for x in inf.corridas}
        r = "la formulación del PEP de 06 y la implementación de su certificador exacto."
        if "ce" in fuentes:
            abiertas = [x for x in inf.corridas if x.target.get("ref_source") == "ce"]
            r += (f" En {len(abiertas)} de {len(inf.corridas)} instancias $\\tau_{{\\mathrm{{ref}}}}$ viene de nuestra búsqueda (entropía cruzada), "
                  "no de la literatura: \\textsc{Certified} significa mejorar nuestra referencia con certificado exacto, no mejorar lo publicado.")
        r += " El \\emph{sandbox} protege el estado del juez, no aísla por completo la máquina: el programa aún puede leer archivos."
    elif inf.tipo == "teorema":
        r = ("la equivalencia entre la hipótesis \\texttt{interp} y ``$f$ convexa y $1$-suave con gradiente $g$'' no está formalizada en "
             "Isabelle: es matemática de libro aceptada \\citep{Nesterov2018}, como los lemas prestados de la bisección. También la "
             "adecuación del enunciado congelado a la cota que se pretende (la de Drori--Teboulle en los objetivos exactos) "
             "\\citep{DroriTeboulle2014}.")
    else:
        r = "el grafo, escrito por el profesor: la aceptación dice que la cadena respeta las dependencias que él declaró, no que el agente sepa demostrar."
    return "\\section{Jerarquía de confianza entre jueces}\n\n" + L["jerarquia"] + "\n\n\\textbf{Residuo en esta corrida:} " + r + "\n"


def objetivos_vi_teorema() -> list[str]:
    """Objetivos del juez de teorema que existen en el repositorio (configs o targets)."""
    nombres = set()
    for f in (PKG / "configs").glob("*.toml"):
        try:
            cfg = tomllib.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        if cfg.get("judge") in ("isabelle_teorema", "gd_isabelle", "isabelle_theorem"):
            nombres.add(cfg.get("target") or cfg.get("name"))
    for f in (PKG / "targets").glob("gd_*.json"):
        nombres.add(f.stem)
    return sorted(n for n in nombres if n)


def s_entornos(inf: Informe) -> str:
    textos = {"01_biseccion": ("bisección", r"$m_n \to c$, $f(c)=0$, error $\le (b-a)/2^{n+1}$", "$V_G$, $V_I$"),
              "02_punto_fijo": ("punto fijo", "Banach en $[a,b]$: unicidad, convergencia, cotas", "$V_G$"),
              "03_taylor": ("Taylor", "resto de Lagrange; convergencia con derivadas acotadas", "$V_G$"),
              "04_newton": ("Newton", "convergencia local cuadrática", "$V_G$"),
              "05_secante": ("secante", r"convergencia local de orden $\varphi$", "$V_G$")}
    mios_env = {x.env for x in inf.corridas}
    proyectos_mios = {x.cfg.get("project") for x in inf.corridas if x.tipo == "grafo"}
    filas = []
    for p, (met, obj, jz) in textos.items():
        try:
            t = LemmaGraphVerifier(p).target()
            nums = f"{t['n_lemmas']} & {t['n_distractors']} & {t['min_length']}"
        except Exception:
            nums = "--- & --- & ---"
        marca = "$^\\ast$" if p in proyectos_mios else ""
        filas.append(f"{p[:2]}{marca} & {met} & {obj} & {jz} & {nums}")
    pep_mio = "$^\\ast$" if inf.tipo == "pep" else ""
    filas.append(f"06{pep_mio} & pasos de GD & cota de peor caso $f(x_n)-f^*$ o $\\|\\nabla f(x_n)\\|^2$ (PEP) & $V_P$ & --- & --- & ---")
    bis_mio = "$^\\ast$" if inf.tipo == "programa" else ""
    filas.append(f"08{bis_mio} & bisección & triple de Hoare de corrección total del programa \\texttt{{bisection}} & $V_I$ (programa) & --- & --- & ---")
    gd = objetivos_vi_teorema()
    gd_mio = "$^\\ast$" if inf.tipo == "teorema" else ""
    if gd:
        filas.append(f"09{gd_mio} & pasos de GD & {len(gd)} teoremas de cota: " + ", ".join(tt(n, 30) for n in gd) + " & $V_I$ (teorema) & --- & --- & ---")
    else:
        filas.append(f"09{gd_mio} & pasos de GD & cotas de GD de paso fijo en Isabelle (previstas) & $V_I$ (teorema) & --- & --- & ---")
    # proponentes con corridas en runs/
    cuenta = Counter()
    for d in todas_las_corridas(inf.runs_root):
        try:
            m = json.loads((d / "meta.json").read_text(encoding="utf-8")).get("model", "")
        except Exception:
            continue
        cuenta[m] += 1
    prop = ", ".join(f"{tt(m, 30)}: {cuenta.get(m, 0)}" for m in PROPONENTES)
    vi = ["\\texttt{bisection} (variante de programa)"] + ([f"{len(gd)} cotas de GD (variante de teorema)"] if gd else [])
    cap = ("Entornos de \\texttt{unirl}. En 01--05 los números se recalculan de los grafos (\\texttt{proof\\_kb}): ``lemas'' cuenta todos los "
           "pasos, incluidos distractores y \\textsc{Qed}; ``cad.\\ mín.'' es el cierre de dependencias de \\textsc{Qed}. Objetivos de $V_I$ "
           "disponibles: " + " y ".join(vi) + ". El punto fijo aún no tiene objetivo formal; Taylor, Newton y secante sólo disponen de juez de "
           "grafo. Proponentes: \\texttt{gpt-6-luna} y \\texttt{gpt-6-astra}, ambos con esfuerzo \\texttt{high}, para todos los jueces (corridas en "
           "\\texttt{runs/}: " + prop + "). $^\\ast$: filas de este informe.")
    tabla = "\n".join(["\\begin{table}[!ht]", "\\centering", "\\footnotesize", "\\begin{tabular}{@{}llp{5.0cm}lrrr@{}}", "\\toprule",
                       "sub. & método & objetivo de fase 2 & juez & lemas & distr. & cad.\\ mín. \\\\", "\\midrule",
                       *[f + " \\\\" for f in filas], "\\bottomrule", "\\end{tabular}", "\\caption{" + cap + "}", "\\label{tab:envs}", "\\end{table}"])
    return "\\section{Entornos}\n\n" + tabla + "\n"


def frase_resultado(x: Corrida) -> str:
    et = etiquetas(x)
    acc = sum(e["aceptado"] for e in x.completos)
    s = (f"{acc} aceptados de {_n_eps(len(x.completos))}, $t^*$ mediana ${g_es(_mediana(x.tstar))}$ ($B = {x.B}$); etiquetas: "
         + ", ".join(f"{lab(l)} {n}" for l, n in sorted(et.items(), key=lambda kv: -kv[1])))
    if x.tipo == "programa":
        con = [r for r in x.intentos if (r.get("raw") or {}).get("n_vcs")]
        if con:
            b = max(con, key=lambda r: r["raw"]["n_closed_auto"] / r["raw"]["n_vcs"])
            s += f"; mejor intento {b['raw']['n_closed_auto']}/{b['raw']['n_vcs']} obligaciones cerradas"
        if x.memoria_activa:
            s += f"; biblioteca final de {len((x.memoria or {}).get('library', {}))} lemas verificados"
    elif x.tipo == "pep":
        m = _mejor_pep(x)
        s += f"; mejor $\\tau = {n_es(m['tau'], 7)}$ frente a $\\tau_{{\\mathrm{{ref}}}} = {n_es(x.target.get('tau_ref'), 7)}$"
    if acc and x.tipo in ("programa", "teorema"):
        s += f". {tt(x.model, 30)} demuestra, Isabelle verifica"
    return s


def s_experimentos(inf: Informe) -> str:
    items = []
    for x in inf.corridas:
        items.append(f"\\emph{{Este informe}}: {tt(x.env, 40)} con {proponente(x.model, x.effort)} ({tt(x.id, 50)}; {estado_tex(x)}). {frase_resultado(x)}.")
    mias = {x.carpeta for x in inf.corridas}
    ids_mios = {x.id for x in inf.corridas} | {c for x in inf.corridas for c in x.continuaciones}
    met = metodo(inf.c0.env)
    rel = []
    for d in todas_las_corridas(inf.runs_root):
        cont = continuacion_de(d)
        if d.resolve() in mias or d.name in ids_mios or (cont and cont["de"] in ids_mios):
            continue
        try:
            y = cargar(d, procesos=_PROCESOS)
        except Exception:
            continue
        if metodo(y.env) != met:
            continue
        rel.append(y)
    rel = fusionar_continuaciones(rel, _PROCESOS)
    for y in sorted(rel, key=lambda y: (y.env, y.meta.get("started", ""))):
        est = "" if y.estado == "terminada" else f"; {estado_tex(y)}"
        items.append(f"Relacionada: {tt(y.env, 40)} bajo {JUEZ_TEX.get(y.meta.get('judge'), '?')} con {proponente(y.model, y.effort)} "
                     f"({tt(y.id, 50)}{est}). {frase_resultado(y)}.")
    # lo siguiente: el otro proponente en los mismos entornos, si aún no tiene corrida
    for x in inf.corridas:
        for m in PROPONENTES:
            if ultima_corrida(inf.runs_root, x.env, m) is None:
                items.append(f"Prevista: {tt(x.env, 40)} con {tt(m, 30)} (\\texttt{{high}}), misma configuración; aún sin corrida en \\texttt{{runs/}}.")
    items.append("Prevista: transferencia entre objetivos (métrica 4), no implementada.")
    out = ("\\section{Experimentos realizados y previstos}\n\n{\\raggedright\n\\begin{enumerate}\n" + "\n".join("  \\item " + i for i in items)
           + "\n\\end{enumerate}\n\\par}\n")
    if inf.comentario:
        out += "\n\\begin{remark}[Interpretación]\n" + inf.comentario.strip() + "\n\\end{remark}\n"
    return out


_PROCESOS: list[dict] = []


def generar_tex(inf: Informe) -> str:
    L = literales()
    partes = [cabecera(inf), "", "\\begin{document}", "\\maketitle", "",
              s_proposito(inf, L), s_mdp(inf, L), s_verificador(inf, L), s_recompensa(inf, L), s_metricas(inf, L),
              s_jerarquia(inf, L), s_entornos(inf), s_experimentos(inf),
              "\\bibliography{unirl_definicion}", "", "\\end{document}", ""]
    return "\n".join(partes)


# ----------------------------------------------------------------------------- escritura y compilación


def copiar_bib(out: Path, tipo: str) -> None:
    texto = BIB.read_text(encoding="utf-8")
    if tipo == "teorema":
        for k, v in BIB_EXTRA.items():
            if k not in texto:
                texto = texto.rstrip("\n") + "\n" + v
    (out / "unirl_definicion.bib").write_text(texto, encoding="utf-8")


def compilar(tex: Path) -> dict:
    """latexmk -pdf con prioridad mínima; devuelve {ok, rc, overfull (pt), indefinidas, citas}."""
    latexmk = shutil.which("latexmk") or str(TEXBIN / "latexmk")
    if not Path(latexmk).exists():
        return {"ok": False, "motivo": "no hay latexmk"}
    env = os.environ.copy()
    env["PATH"] = f"{TEXBIN}:{env.get('PATH', '')}"
    cmd = [latexmk, "-pdf", "-interaction=nonstopmode", tex.name]
    if shutil.which("taskpolicy"):
        cmd = ["taskpolicy", "-b"] + cmd
    # la salida de latexmk puede traer bytes latin-1 (eco de líneas del .tex): se decodifica con reemplazo
    p = subprocess.run(cmd, cwd=tex.parent, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=900)
    log = tex.with_suffix(".log")
    txt = log.read_text(encoding="utf-8", errors="replace") if log.exists() else ""
    over = [float(x) for x in re.findall(r"Overfull \\hbox \((\d+(?:\.\d+)?)pt too wide\)", txt)]
    return {"ok": p.returncode == 0 and tex.with_suffix(".pdf").exists(), "rc": p.returncode, "overfull": over,
            "indefinidas": "There were undefined references" in txt or "Reference `" in txt,
            "citas": sorted(set(re.findall(r"Citation `([^']+)'[^\n]*undefined", txt))),
            "errores": re.findall(r"^! .*$", txt, re.M)[:5], "salida": (p.stdout or "")[-1500:]}


def generar_informe(carpetas: list[Path], out: Path, runs_root: Path = RUNS, compilar_pdf: bool = True) -> dict:
    global _PROCESOS
    _PROCESOS = procesos_unirl()
    corridas = fusionar_continuaciones([cargar(Path(c), _PROCESOS) for c in carpetas], _PROCESOS)
    if not corridas:
        raise SystemExit("sin corridas")
    tipos = {c.tipo for c in corridas}
    if len(tipos) > 1:
        raise SystemExit(f"no se mezclan tipos de corrida en un informe: {sorted(tipos)}")
    modelos = {c.model for c in corridas}
    if len(modelos) > 1:
        raise SystemExit(f"un informe agrupa corridas de un solo modelo; hay {sorted(modelos)}")
    corridas.sort(key=lambda c: (c.meta.get("started", ""), c.env))
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    com = out / "comentario.tex"
    inf = Informe(corridas, Path(runs_root), com.read_text(encoding="utf-8") if com.exists() else None)
    tex = out / "informe.tex"
    tex.write_bytes(preambulo() + b"\n" + generar_tex(inf).encode("utf-8"))
    copiar_bib(out, inf.tipo)
    res = {"tex": str(tex), "tipo": inf.tipo, "corridas": [str(c.carpeta) for c in corridas], "estados": [c.estado for c in corridas]}
    if compilar_pdf:
        res["compilacion"] = compilar(tex)
        res["pdf"] = str(tex.with_suffix(".pdf"))
    return res


def cmd_informe(args) -> int:
    runs_root = Path(args.runs_root) if getattr(args, "runs_root", None) else RUNS
    carpetas: list[Path] = [Path(p) for p in (args.runs or [])]
    if args.ultima:
        if not args.model:
            raise SystemExit("--ultima necesita --model")
        for env in [e.strip() for e in args.ultima.split(",") if e.strip()]:
            d = ultima_corrida(runs_root, env, args.model)
            if d is None:
                print(f"[informe] aviso: no hay corrida de {env} con {args.model} en {runs_root}")
                continue
            carpetas.append(d)
    if not carpetas:
        print("[informe] sin corridas que informar")
        return 1
    if args.out and args.slug:
        raise SystemExit("usa --slug o --out, no ambos")
    if args.out:
        out = Path(args.out)
    else:
        slug = args.slug or (Path(carpetas[0]).parent.name + "-" + (args.model or json.loads((Path(carpetas[0]) / "meta.json").read_text(encoding="utf-8")).get("model", "")))
        out = INFORMES / slug
    res = generar_informe(carpetas, out, runs_root, compilar_pdf=not args.no_pdf)
    print(f"[informe] {res['tipo']}: {len(res['corridas'])} corrida(s) ({', '.join(res['estados'])}) → {res['tex']}")
    comp = res.get("compilacion")
    if comp:
        if comp.get("ok"):
            graves = [x for x in comp["overfull"] if x > 10]
            print(f"[informe] PDF: {res['pdf']} (cajas desbordadas: {len(comp['overfull'])}, > 10 pt: {len(graves)}; "
                  f"referencias indefinidas: {'sí' if comp['indefinidas'] else 'no'}; citas indefinidas: {comp['citas'] or 'ninguna'})")
        else:
            print(f"[informe] la compilación falló: {comp.get('motivo') or comp.get('errores')}")
            return 2
    return 0
