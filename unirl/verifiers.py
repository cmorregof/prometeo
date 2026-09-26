"""Tres jueces con la misma interfaz `verify(target, proposal) -> Outcome`.

* `LemmaGraphVerifier` (V_G): envuelve los grafos de lemas escritos a mano de 01–05. Su confianza descansa
  íntegramente en el grafo humano: acepta exactamente las cadenas que el autor del grafo consideró válidas.
* `PEPVerifier` (V_P): envoltorio fino de `steprl.env.score` (06). No toca el 06.
* `IsabelleVerifier` (V_I): envoltorio fino de `isarl.driver` (08). No toca el 08.

Cada juez sabe además cómo presentar su target al proponente (`describe`, `feedback`) y cómo
interpretar su respuesta (`parse`), porque el formato de la propuesta es propio de cada juez.
El agente nunca se puntúa a sí mismo: la recompensa sale solo de `verify`.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import math
import os
import random
import re
import signal
import subprocess
import sys
import tempfile
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

ROOT = Path(__file__).resolve().parent.parent.parent  # rl_metodos/
TARGETS = ROOT / "09_unified" / "targets"


@dataclass
class Outcome:
    accepted: bool
    outcome_label: str
    partial_credit: float  # en [0, 1]; solo se usa con recompensa moldeada
    cost_s: float
    raw: dict[str, Any] = field(default_factory=dict)


class Verifier(Protocol):
    name: str
    LABELS: tuple[str, ...]

    def target(self) -> dict: ...
    def verify(self, target: dict, proposal: Any) -> Outcome: ...
    def describe(self, target: dict) -> str: ...
    def parse(self, text: str) -> Any: ...
    def feedback(self, proposal: Any, outcome: Outcome) -> str: ...


def _import_from(project_dir: str, module: str):
    """Importa `module` desde `rl_metodos/<project_dir>` sin instalar nada ni tocar el proyecto."""
    p = str(ROOT / project_dir)
    if p not in sys.path:
        sys.path.insert(0, p)
    return importlib.import_module(module)


# ----------------------------------------------------------------------------- V_G: grafo de lemas


class LemmaGraphVerifier:
    """Proposal = lista ordenada de identificadores de lema (anonimizados: L01…); la justificación libre se ignora.

    Aceptada ⇔ cada paso tiene sus dependencias ya establecidas, no se repite, no es distractor,
    y la cadena llega al teorema (QED); lo que venga después de QED se ignora. Los ids se anonimizan y
    barajan con semilla fija y no se muestran los títulos, porque en 01–05 el título delata al distractor.
    Progreso parcial: fracción del cierre de dependencias de QED ya establecida.
    """

    name = "lemma_graph"
    LABELS = ("ACCEPTED", "INVALID_STEP", "DISTRACTOR", "UNKNOWN_LEMMA", "INCOMPLETE")

    def __init__(self, project: str, seed: int = 0):
        self.project = project
        pkg = [d.name for d in (ROOT / project).iterdir() if d.is_dir() and (d / "proof_kb.py").exists()][0]
        self.kb = _import_from(project, f"{pkg}.proof_kb")
        self.steps = list(self.kb.STEPS)
        self.qed = [s for s in self.steps if s.is_qed][0]
        self.required = frozenset(self.kb.REQUIRED_KEYS)
        order = list(range(len(self.steps)))
        random.Random(seed).shuffle(order)
        self.alias = {self.steps[k].key: f"L{i + 1:02d}" for i, k in enumerate(order)}
        self.key_of = {v: k for k, v in self.alias.items()}
        self.by_key = {s.key: s for s in self.steps}

    # En 7 de los 36 distractores de 01–05 el texto trae al final la refutación del profesor entre paréntesis,
    # p. ej. «(¡falso: el orden es φ < 2!)». Se quita al mostrarlo; 01–05 no se tocan.
    _REFUTATION = re.compile(r"\s*\((?:¡[^()]*!|[^()]*(?:falso|eso es)[^()]*)\)\s*$", re.I)

    def shown_text(self, s) -> str:
        return self._REFUTATION.sub("", s.text) if s.distractor else s.text

    def target(self) -> dict:
        lemmas = sorted(({"id": self.alias[s.key], "text": self.shown_text(s)} for s in self.steps), key=lambda d: d["id"])
        return {
            "id": f"{self.project}:{self.qed.key}",
            "statement": self.qed.text,
            "goal_id": self.alias[self.qed.key],
            "lemmas": lemmas,
            "n_lemmas": len(self.steps),
            "n_distractors": sum(s.distractor for s in self.steps),
            "min_length": int(self.kb.MIN_PROOF_LENGTH),
            "hash": hashlib.sha256(json.dumps(lemmas, ensure_ascii=False).encode()).hexdigest()[:16],
        }

    def _partial(self, established: set[str]) -> float:
        return len(established & self.required) / len(self.required)

    def verify(self, target: dict, proposal: list[str]) -> Outcome:
        t0 = time.perf_counter()
        established: set[str] = set()
        for i, lid in enumerate(proposal):
            key = self.key_of.get(lid)
            if key is None:
                return Outcome(False, "UNKNOWN_LEMMA", self._partial(established), time.perf_counter() - t0,
                               {"failed_at": i, "id": lid, "reason": "identificador desconocido"})
            s = self.by_key[key]
            if s.distractor:
                label, reason = "DISTRACTOR", "el enunciado es falso o no aplica aquí"
            elif key in established:
                label, reason = "INVALID_STEP", "paso repetido"
            elif any(d not in established for d in s.deps):
                label, reason = "INVALID_STEP", "usa hipótesis que aún no están establecidas"
            else:
                label, reason = "", ""
            if label:
                return Outcome(False, label, self._partial(established), time.perf_counter() - t0,
                               {"failed_at": i, "id": lid, "key": key, "reason": reason})
            established.add(key)
            if s.is_qed:
                return Outcome(True, "ACCEPTED", 1.0, time.perf_counter() - t0,
                               {"length": i + 1, "keys": [self.key_of[x] for x in proposal[: i + 1]], "ignored_after_qed": len(proposal) - i - 1})
        return Outcome(False, "INCOMPLETE", self._partial(established), time.perf_counter() - t0,
                       {"established": len(established), "reason": "la cadena no llega a la conclusión"})

    def describe(self, target: dict) -> str:
        lines = [f"TEOREMA A DEMOSTRAR ({target['goal_id']}): {target['statement']}", "",
                 "LEMAS DISPONIBLES (algunos son falsos o no aplican; no se dice cuáles):"]
        for l in target["lemmas"]:
            lines.append(f"  {l['id']}: {l['text']}")
        lines += ["", "Reglas: cada paso solo puede usar lo establecido por los pasos anteriores; no repitas pasos;",
                  f"la cadena debe terminar en {target['goal_id']}. Longitud mínima posible: {target['min_length']} pasos.",
                  'Responde SOLO con un JSON: {"steps": ["L03", "L11", ...]}. Puedes añadir una justificación breve después, se ignora.']
        return "\n".join(lines)

    def parse(self, text: str) -> list[str]:
        m = re.search(r"\{.*?\"steps\".*?\}", text, re.S)
        if m:
            try:
                return [str(x) for x in json.loads(m.group(0))["steps"]]
            except Exception:
                pass
        return re.findall(r"\bL\d{2}\b", text)

    def feedback(self, proposal: list[str], outcome: Outcome) -> str:
        r = outcome.raw
        if outcome.outcome_label in ("INVALID_STEP", "DISTRACTOR", "UNKNOWN_LEMMA"):
            return f"{outcome.outcome_label} en el paso {r['failed_at'] + 1} ({r['id']}): {r['reason']}. Los {r['failed_at']} pasos anteriores eran válidos."
        if outcome.outcome_label == "INCOMPLETE":
            return f"INCOMPLETE: {r['established']} pasos válidos pero {r['reason']}."
        return outcome.outcome_label


# ----------------------------------------------------------------------------- V_P: PEP (06)

# El programa propuesto se ejecuta en un intérprete aparte (06 lo ejecuta en su propio proceso con los builtins
# restringidos, y por introspección podía alcanzar los módulos del juez y sustituir la puntuación). El hijo solo
# devuelve la sucesión h; el padre puntúa la sucesión literal con 06, en un proceso que la propuesta no tocó.
_PEP_RUNNER = r'''
import contextlib, io, json, sys
sys.path.insert(0, sys.argv[1])
from steprl.env import run_program
code = sys.stdin.read()
buf = io.StringIO()
try:
    with contextlib.redirect_stdout(buf):
        h = [float(x) for x in run_program(code, int(sys.argv[2]), timeout_s=float(sys.argv[3]))]
    res = {"h": h}
except BaseException as e:
    # solo el tipo: el texto de la excepción lo controla el programa y podría llevar contenido de archivos
    res = {"error": type(e).__name__}
sys.__stdout__.write("\n" + json.dumps(res) + "\n")
sys.__stdout__.flush()
'''


class PEPVerifier:
    """Proposal = código Python con `schedule(n)`; target = instancia (n, μ, criterio, ¿negativos?).

    mode = "improve" (por defecto, el de la nota técnica): aceptada ⇔ el peor caso mejora estrictamente
    la mejor referencia conocida τ_ref **y** la mejora pasa la certificación racional exacta de 06
    (CERTIFIED). mode = "match": además acepta τ ≤ τ_ref·(1+TOL) según el valor numérico del SDP (MATCHED);
    sirve para ensayos, no es un certificado exacto.
    """

    name = "pep"
    LABELS = ("CERTIFIED", "MATCHED", "INVALID_SCHEDULE", "NOT_IMPROVED", "CERTIFICATION_FAILED")
    TOL = 1e-4

    def __init__(self, n: int = 4, mu: float = 0.0, objective: str = "fval", negative: bool = False, mode: str = "improve",
                 program_timeout_s: float = 2.0, process_timeout_s: float = 60.0):
        if mode not in ("improve", "match"):
            raise ValueError("mode ∈ {improve, match}")
        self.mode = mode
        self.program_timeout_s, self.process_timeout_s = program_timeout_s, process_timeout_s
        self.env06 = _import_from("06_stepsizes", "steprl.env")
        self.refs06 = _import_from("06_stepsizes", "steprl.refs")
        self.evolve06 = _import_from("06_stepsizes", "steprl.evolve")
        self.inst = self.refs06.Instance(n=n, mu=mu, objective=objective, allow_negative=negative)
        # Las referencias se leen una vez: 06 las relee de refs.json en cada score(), y un programa con acceso al
        # disco podría subir τ_ref y convertir un paso cualquiera en «mejora certificada».
        self.refs = self.refs06.load_refs()
        self.tau_ref, self.ref_source = self.refs06.reference(self.inst, self.refs)
        self.sandboxed = Path("/usr/bin/sandbox-exec").exists()

    def target(self) -> dict:
        tau_ref, src = self.tau_ref, self.ref_source
        return {"id": f"pep:{self.inst.label()}", "n": self.inst.n, "mu": self.inst.mu, "objective": self.inst.objective,
                "negative": self.inst.allow_negative, "tau_ref": tau_ref, "ref_source": src, "mode": self.mode,
                "hash": hashlib.sha256(self.inst.label().encode()).hexdigest()[:16]}

    def run_isolated(self, code: str) -> tuple[list[float] | None, str]:
        """Ejecuta `schedule(n)` en un intérprete aparte y devuelve (h, error)."""
        cmd = [sys.executable, "-I", "-B", "-c", _PEP_RUNNER, str(ROOT / "06_stepsizes"), str(self.inst.n), str(self.program_timeout_s)]
        if self.sandboxed:  # macOS: sin red y sin escritura en disco para el programa propuesto
            cmd = ["/usr/bin/sandbox-exec", "-p", '(version 1)(allow default)(deny network*)(deny file-write* (require-not (literal "/dev/null")))'] + cmd
        try:
            p = subprocess.run(cmd, input=code, capture_output=True, text=True, timeout=self.process_timeout_s, cwd=tempfile.gettempdir())
        except subprocess.TimeoutExpired:
            return None, f"ProgramTimeout: el proceso del programa superó {self.process_timeout_s:.0f} s"
        lines = [l for l in p.stdout.splitlines() if l.strip()]
        try:
            res = json.loads(lines[-1])
        except Exception:
            return None, f"salida ilegible del programa (código {p.returncode}): {(p.stderr or p.stdout)[-200:]}"
        if "error" in res:
            return None, res["error"]
        h = res.get("h")
        if not isinstance(h, list) or len(h) != self.inst.n or not all(isinstance(x, (int, float)) and math.isfinite(x) for x in h):
            return None, "el programa no devolvió n números finitos"
        return [float(x) for x in h], ""

    def verify(self, target: dict, proposal: str) -> Outcome:
        t0 = time.perf_counter()
        h, err = self.run_isolated(proposal)
        if h is None:
            return Outcome(False, "INVALID_SCHEDULE", 0.0, time.perf_counter() - t0, {"error": err, "reward06": self.env06.INVALID_REWARD})
        canonical = "def schedule(n):\n    return " + repr(h)
        sc = self.env06.score(canonical, self.inst, refs=self.refs)  # la sucesión literal; valida de nuevo y puntúa en el padre
        if sc.ok and sc.tau_ref != target["tau_ref"]:
            raise RuntimeError(f"τ_ref cambió durante la verificación ({sc.tau_ref} ≠ {target['tau_ref']})")
        cost = time.perf_counter() - t0
        if not sc.ok:
            return Outcome(False, "INVALID_SCHEDULE", 0.0, cost, {"error": sc.error, "reward06": self.env06.INVALID_REWARD})
        raw = {"tau": sc.tau, "tau_ref": sc.tau_ref, "reward06": sc.reward, "h": sc.h, "improved": sc.improved,
               "certified": sc.certified, "tau_cert": sc.tau_cert if sc.certified else None,
               "proposal_sha": hashlib.sha256(proposal.encode()).hexdigest()[:16], "sandbox": self.sandboxed}
        credit = max(0.0, min(1.0, 1.0 + sc.reward))  # 1 = iguala; < 1 = peor
        if sc.improved and sc.certified and sc.tau_cert < sc.tau_ref:
            return Outcome(True, "CERTIFIED", 1.0, cost, raw)
        if self.mode == "match" and sc.tau <= sc.tau_ref * (1 + self.TOL):
            return Outcome(True, "MATCHED", 1.0, cost, raw)
        if sc.improved and sc.certified is False:
            return Outcome(False, "CERTIFICATION_FAILED", credit, cost, raw)
        return Outcome(False, "NOT_IMPROVED", credit, cost, raw)

    def describe(self, target: dict) -> str:
        goal = "Se acepta solo una MEJORA estricta con certificado exacto." if self.mode == "improve" else "Se acepta igualarlo (tolerancia relativa 1e-4) o mejorarlo."
        return (f"Instancia: n = {target['n']} pasos, μ = {target['mu']} (L = 1), criterio {target['objective']}, "
                f"pasos negativos {'permitidos' if target['negative'] else 'prohibidos'}.\n"
                f"Mejor peor caso conocido: τ_ref = {target['tau_ref']:.7f} ({target['ref_source']}). {goal}\n"
                "Devuelve UN bloque ```python``` con `schedule(n: int) -> list[float]` (solo math y numpy).")

    def parse(self, text: str) -> str:
        return self.evolve06.extract_code(text)

    def feedback(self, proposal: str, outcome: Outcome) -> str:
        r = outcome.raw
        if outcome.outcome_label == "INVALID_SCHEDULE":
            return f"INVALID_SCHEDULE: {r['error']}"
        return f"{outcome.outcome_label}: τ = {r['tau']:.7f} vs τ_ref = {r['tau_ref']:.7f}; h = {[round(x, 4) for x in r['h']]}"


# ----------------------------------------------------------------------------- V_I: Isabelle (08)

# Una sugerencia de Sledgehammer cuenta solo si su preplay terminó: "Try this: <método> (12 ms)".
# El driver de 08 acepta también sugerencias sin preplay (">", "timed out", "failed"); aquí no.
_PREPLAYED = re.compile(r"Try this: ((?:using .+? )?by .+?) \((\d+(?:\.\d+)?) (ms|s)\)\s*$", re.S)
_PROVER = re.compile(r"^(\w+)(?: found a proof|: Try this)", re.M)

# Lista blanca de la anotación. Isabelle decodifica escapes y tokeniza distinto que una expresión regular, así
# que se admite solo lo necesario para escribir un término: letras, dígitos, espacios, esta puntuación y los
# símbolos \<nombre> de la lista. La garantía de fondo es la etapa 0 (igualdad de programas en el kernel).
_ALLOWED_SYMBOLS = frozenset("""and or not le ge noteq lceil rceil lfloor rfloor bar exists forall in notin
    longrightarrow longleftrightarrow times cdot bullet lambda alpha beta gamma delta epsilon mu theta tau sigma rho
    infinity subseteq subset union inter inverse le ge lessapprox approx sqrt ^sup ^sub""".split())
_ALLOWED_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 \t\n()+-*/^<>=.,:{}[]|~'_!?")
_SYMBOL = re.compile(r"\\<(\^?[A-Za-z]+)>")
# Salir del hueco: comillas, cartuchos, comentarios, marcadores de plantilla, sintaxis de programa.
_STRUCTURAL = re.compile(r'"|\\<open>|\\<close>|‹|›|\(\*|\*\)|\\<comment>|__|;|:=|`'
                         r"|(?<![A-Za-z0-9_'])(?:do|od|fi|while|invariant|variant|skip|program|procedure)(?![A-Za-z0-9_'])")
_UNSOUND_TOKENS = re.compile(r"(?<![A-Za-z0-9_'])(?:sorry|oops|axiomatization|oracle|skip_proof)(?![A-Za-z0-9_'])")


def check_annotation(text: str) -> tuple[str, str] | None:
    """None si la anotación pasa la lista blanca; si no, (etiqueta, motivo)."""
    if _STRUCTURAL.search(text):
        return "STATEMENT_DRIFT", f"la anotación sale de su hueco: {_STRUCTURAL.search(text).group(0)!r}"
    if _UNSOUND_TOKENS.search(text):
        return "UNSOUND", "sorry/oops/axiomatization/oracle en la anotación"
    for m in _SYMBOL.finditer(text):
        if m.group(1) not in _ALLOWED_SYMBOLS:
            return "INVALID_PROPOSAL", f"símbolo no admitido: \\<{m.group(1)}>"
    rest = _SYMBOL.sub(" ", text)
    bad = sorted({c for c in rest if c not in _ALLOWED_CHARS})
    if bad:
        return "INVALID_PROPOSAL", f"caracteres no admitidos: {''.join(bad)!r}"
    return None


# Lemas auxiliares del agente (fase 2). Son texto de teoría, así que el filtro tokeniza como el analizador
# léxico externo de Isabelle (comentarios anidados, cadenas con escapes, símbolos \<…>) y solo admite, como
# comandos, los de enunciar y demostrar lemas. La lista de comandos existentes sale del propio Isabelle
# (targets/isabelle_commands.txt). Además, en el kernel: el enunciado congelado se lee antes y después del texto
# del agente y debe coincidir término a término, y no puede aparecer ningún axioma nuevo.
ISABELLE_COMMANDS = frozenset((TARGETS / "isabelle_commands.txt").read_text(encoding="utf-8").split())
ALLOWED_COMMANDS = frozenset({"lemma", "theorem", "corollary", "proposition", "proof", "qed", "by", ".", "..", "apply",
                              "done", "using", "unfolding", "have", "show", "hence", "thus", "obtain", "fix", "assume",
                              "presume", "define", "let", "note", "from", "with", "then", "also", "finally", "moreover",
                              "ultimately", "next", "case", "subgoal", "supply", "{", "}", "defer", "prefer", "consider"})
_LEMMA_HEADS = {"lemma", "theorem", "corollary", "proposition"}
# comandos que pueden cambiar cómo se lee o qué significa el enunciado congelado (deriva); el resto de comandos no
# admitidos (p. ej. una definition auxiliar) es una propuesta inválida
_MEANING_COMMANDS = {"end", "context", "notation", "no_notation", "type_notation", "no_type_notation", "syntax", "no_syntax",
                     "translations", "parse_translation", "print_translation", "parse_ast_translation", "print_ast_translation",
                     "typed_print_translation", "declare", "setup", "local_setup", "attribute_setup", "method_setup",
                     "simproc_setup", "ML", "ML_file", "ML_val", "ML_command", "ML_prf", "ML_export", "hide_const", "hide_fact",
                     "hide_type", "hide_class", "unbundle", "bundle", "include", "including", "program", "procedure", "zstore",
                     "overloading", "instantiation", "instance", "consts", "defs", "abbreviation", "adhoc_overloading",
                     "no_adhoc_overloading", "method", "alias", "type_alias", "lifting_update", "setup_lifting"}
# métodos que ejecutan ML o evalúan código: no son comandos, se prohíben por nombre
_BANNED_WORDS = {"tactic", "raw_tactic", "eval", "normalization", "code_simp", "sorry", "oops", "begin", "end"}
_FORMAL_COMMENT = ("\\<comment>", "\\<^cancel>", "\\<^marker>", "\\<open>", "\\<close>")
LEMMAS_MAX_CHARS = 20000


def tokenize_outer(text: str) -> list[tuple[str, str]]:
    """Tokens (clase, texto) según el léxico externo de Isabelle, lo justo para este filtro. Lanza ValueError
    ante cualquier construcción que no se admite (cartuchos, texto literal, comillas invertidas, comentarios
    formales, cadenas o comentarios sin cerrar, barras invertidas fuera de un símbolo o de una cadena)."""
    toks, i, n = [], 0, len(text)
    while i < n:
        c = text[i]
        if c.isspace():
            i += 1
        elif text.startswith("(*", i):  # comentario, anidado como en Isabelle; las comillas dentro no cuentan
            depth, i = 1, i + 2
            while i < n and depth:
                if text.startswith("(*", i):
                    depth, i = depth + 1, i + 2
                elif text.startswith("*)", i):
                    depth, i = depth - 1, i + 2
                else:
                    i += 1
            if depth:
                raise ValueError("comentario sin cerrar")
        elif c == '"':  # cadena: \" \\ \ddd y símbolos \<…>
            j = i + 1
            while True:
                if j >= n:
                    raise ValueError("cadena sin cerrar")
                if text[j] == '"':
                    break
                if text[j] == "\\":
                    m = re.match(r"\\<\^?[A-Za-z][A-Za-z0-9_']*>|\\[\"\\]|\\[0-9]{3}", text[j:])
                    if not m:
                        raise ValueError("escape no admitido dentro de una cadena")
                    j += len(m.group(0))
                else:
                    j += 1
            toks.append(("string", text[i:j + 1]))
            i = j + 1
        elif c in "`‹›" or text.startswith("{*", i) or text.startswith("*}", i):
            raise ValueError(f"construcción no admitida: {c!r}")
        elif c == "\\":
            m = re.match(r"\\<\^?[A-Za-z][A-Za-z0-9_']*>", text[i:])
            if not m or m.group(0) in _FORMAL_COMMENT:
                raise ValueError("barra invertida fuera de un símbolo, o comentario formal")
            toks.append(("sym", m.group(0)))
            i += len(m.group(0))
        else:
            # identificadores como en Isabelle (lexicon.ML): empiezan por letra; un identificador largo encadena
            # segmentos «.segmento» que también empiezan por letra. Así «ML.5» son tres tokens, como en Isabelle.
            m = re.match(r"[A-Za-z][A-Za-z0-9_']*(?:\.[A-Za-z][A-Za-z0-9_']*)*|\d+|\.\.|[^\sA-Za-z0-9\"\\`]", text[i:])
            toks.append(("word" if m.group(0)[0].isalpha() else "punct", m.group(0)))
            i += len(m.group(0))
    return toks


_LEMMA_HEAD_LINE = re.compile(r"^\s*(lemma|theorem|corollary|proposition)\s+([A-Za-z][A-Za-z0-9_']*)")


def split_lemmas(text: str) -> list[dict]:
    """Parte un bloque en lemas: [{name, text, first, last}] con líneas 0-based relativas al bloque. Un lema empieza
    en una línea que abre con lemma/theorem/corollary/proposition y termina antes del siguiente."""
    lines = text.split("\n")
    heads = [(k, m.group(2)) for k, l in enumerate(lines) if (m := _LEMMA_HEAD_LINE.match(l))]
    out = []
    for n, (k, name) in enumerate(heads):
        end = heads[n + 1][0] - 1 if n + 1 < len(heads) else len(lines) - 1
        out.append({"name": name, "text": "\n".join(lines[k:end + 1]).strip(), "first": k, "last": end})
    return out


def merge_lemmas(library: str, agent: str) -> str:
    """Lemas de la biblioteca (demostrados por el agente y verificados por Isabelle) seguidos de los del agente; si el agente redefine un nombre de la
    biblioteca, gana su versión."""
    mine = {b["name"] for b in split_lemmas(agent)}
    lib = [b["text"] for b in split_lemmas(library) if b["name"] not in mine]
    return "\n\n".join(lib + ([agent] if agent.strip() else [])).strip()


def check_lemmas(text: str) -> tuple[str, str] | None:
    """None si el bloque de lemas pasa el filtro; si no, (etiqueta, motivo)."""
    if len(text) > LEMMAS_MAX_CHARS:
        return "INVALID_PROPOSAL", f"el bloque de lemas supera {LEMMAS_MAX_CHARS} caracteres"
    if "__" in text or "[[" in text:
        return "STATEMENT_DRIFT", "el bloque de lemas contiene '__' o '[['"
    try:
        toks = tokenize_outer(text)
    except ValueError as e:
        return "STATEMENT_DRIFT", f"el bloque de lemas no se admite: {e}"
    words = [t for k, t in toks if k in ("word", "punct")]
    # además, cada segmento de un identificador largo se revisa por separado (defensa en profundidad)
    for w in [seg for t in words for seg in t.split(".") if seg] + words:
        if w in ("sorry", "oops", "axiomatization", "axioms", "oracle"):
            return "UNSOUND", f"el bloque de lemas usa {w}"
        if w in _BANNED_WORDS:
            return "STATEMENT_DRIFT", f"el bloque de lemas usa {w!r}"
        if w in ISABELLE_COMMANDS and w not in ALLOWED_COMMANDS:
            label = "STATEMENT_DRIFT" if w in _MEANING_COMMANDS else "INVALID_PROPOSAL"
            return label, f"comando no admitido en el bloque de lemas: {w!r} (solo lemas con su prueba)"
    if not words or words[0] not in _LEMMA_HEADS:
        return "INVALID_PROPOSAL", "el bloque de lemas debe empezar con `lemma`"
    return None


LEMMAS_THEORY = r'''theory Lemmas
  imports __IMPORTS__
begin

__AUX__

__STORE__

__REFPROGRAM__

context
  fixes __FIXES__
  assumes __ASSUMES__
begin

__PRELUDE__

ML \<open>
  val isarl_axioms0 = length (Theory.all_axioms_of (Proof_Context.theory_of @{context}))
  val isarl_concl0 = @{prop \<open>__CONCLREF__\<close>}
\<close>

__AGENTLEMMAS__

ML \<open>
  val _ = if @{prop \<open>__CONCLREF__\<close>} aconv isarl_concl0 then () else error "isarl: el enunciado congelado se lee distinto"
  val _ = if length (Theory.all_axioms_of (Proof_Context.theory_of @{context})) = isarl_axioms0 then ()
          else error "isarl: los lemas añadieron axiomas"
  val _ = File.write (Path.explode "__DIR__/lemmas.ok") ""
\<close>

end

end
'''


def _descendants(pid: int) -> list[int]:
    out = subprocess.run(["ps", "-A", "-o", "pid=,ppid="], capture_output=True, text=True).stdout
    kids: dict[int, list[int]] = {}
    for line in out.splitlines():
        a, b = line.split()
        kids.setdefault(int(b), []).append(int(a))
    res, stack = [], [pid]
    while stack:
        for c in kids.get(stack.pop(), []):
            res.append(c)
            stack.append(c)
    return res


def kill_tree(pids: list[int]) -> None:
    """Mata procesos y todos sus descendientes (Java, Poly/ML y demostradores de Sledgehammer)."""
    victims = []
    for p in pids:
        victims += [p] + _descendants(p)
    for sig in (signal.SIGTERM, signal.SIGKILL):
        for v in victims:
            try:
                os.kill(v, sig)
            except ProcessLookupError:
                pass
        time.sleep(1)


def kill_build_of(work: Path) -> None:
    """Tras un TIMEOUT del driver de 08 (que solo mata al envoltorio `isabelle`), limpia los procesos huérfanos
    de esa compilación: el proceso Java lleva `-d <work>` en su línea de órdenes."""
    out = subprocess.run(["pgrep", "-f", str(work)], capture_output=True, text=True).stdout
    kill_tree([int(x) for x in out.split()])


FINAL_THEORY = r'''theory Final
  imports __IMPORTS__
begin

__AUX__

__STORE__

__PROGRAM__

__REFPROGRAM__

context
  fixes __FIXES__
  assumes __ASSUMES__
begin

ML \<open>
  val isarl_axioms0 = length (Theory.all_axioms_of (Proof_Context.theory_of @{context}))
  val isarl_expected = @{prop \<open>__CONCLREF__\<close>}
\<close>

__PRELUDE__

lemma isarl_target: "__CONCL__"
  apply vcg
__SUBGOALS__
  done

lemma isarl_same_program: "__NAME__ x = __NAME___ref x"
  by (simp only: __NAME___def __NAME___ref_def while_inv_var_def)

lemma isarl_final: "__CONCLREF__"
  using isarl_target by (simp only: isarl_same_program)

ML \<open>
  val th = @{thm isarl_final}
  val oracles = Thm_Deps.all_oracles [th]
  val skip = Thm_Deps.has_skip_proof [th]
  val _ = File.write (Path.explode "__OUT__")
    ("{\"oracles\": [" ^ String.concatWith "," (map (fn ((n, _), _) => "\"" ^ n ^ "\"") oracles) ^ "], \"skip_proof\": "
      ^ (if skip then "true" else "false")
      ^ ", \"prop_ok\": " ^ (if Thm.prop_of th aconv isarl_expected then "true" else "false")
      ^ ", \"axioms_ok\": " ^ (if length (Theory.all_axioms_of (Proof_Context.theory_of @{context})) = isarl_axioms0 then "true" else "false")
      ^ ", \"prop\": \"" ^ String.translate (fn #"\"" => "'" | #"\\" => "/" | #"\n" => " " | c => String.str c)
          (XML.content_of (YXML.parse_body (Syntax.string_of_term @{context} (Thm.prop_of th)))) ^ "\"}")
\<close>

end

end
'''

SAME_THEORY = r'''theory Same
  imports __IMPORTS__
begin

__STORE__

__PROGRAM__

ML \<open>File.write (Path.explode "__DIR__/parsed.ok") ""\<close>

__REFPROGRAM__

lemma isarl_same_program: "__NAME__ x = __NAME___ref x"
  by (simp only: __NAME___def __NAME___ref_def while_inv_var_def)

ML \<open>File.write (Path.explode "__DIR__/same.ok") ""\<close>

end
'''


def _fill(template: str, table: dict[str, str]) -> str:
    """Sustitución en una sola pasada: el texto insertado nunca se vuelve a examinar."""
    return re.sub(r"__([A-Z]+)__", lambda m: table[m.group(1)], template)


class IsabelleVerifier:
    """Proposal = {"invariant": str, "variant": str}; target = plantilla congelada (programa, tripleta, lemas prestados).

    Etapas: (0) lista blanca de la anotación y demostración en el kernel de que el programa anotado es igual al
    congelado con anotaciones fijas (`while_inv_var B I V P = iterate B P`, así que la igualdad vale exactamente
    cuando solo cambian las anotaciones); (1)–(2) driver de 08: `vcg` + try0 + Sledgehammer con límite fijo sobre
    cada VC; (3) si todas las VCs tienen prueba de una línea con preplay, se ensambla el teorema completo, se pasa
    al programa congelado con la igualdad de (0) y se compila; (4) el teorema no puede depender de oráculos ni de
    `skip_proof`. ACCEPTED solo si todo pasa.
    """

    name = "isabelle"
    allow_lemmas = False
    LABELS = ("ACCEPTED", "VC_OPEN", "VCG_FAILED", "LEMMA_FAILED", "ASSEMBLY_FAILED", "UNSOUND", "STATEMENT_DRIFT", "TIMEOUT", "INVALID_PROPOSAL")

    def __init__(self, target_name: str = "bisection", sh_timeout: int = 60, try0_timeout: int = 5, build_timeout_s: float = 1800,
                 expected_hash: str | None = None, allow_lemmas: bool = False, lemas_parciales: bool = False):
        self.allow_lemmas = allow_lemmas
        # lemas_parciales (24 sep 2026, pedido de Carlos): si algún lema falla, se descartan SOLO los que fallan (se
        # verifican uno a uno) y las VCs se evalúan con los que sí compilan; el intento recibe crédito parcial
        # (fracción de VCs cerradas) en vez de perderse entero. Por defecto apagado: las corridas anteriores no cambian.
        self.lemas_parciales = lemas_parciales
        self.driver = _import_from("08_isabelle", "isarl.driver")
        self.config08 = _import_from("08_isabelle", "isarl.config")
        self.sh_timeout, self.try0_timeout, self.build_timeout_s = sh_timeout, try0_timeout, build_timeout_s
        self.target_name = target_name
        self.spec = self._load_spec()
        self.frozen_hash = self._hash(self.spec)
        pinned = expected_hash or self.spec.get("frozen_hash")
        if pinned and pinned != self.frozen_hash:
            raise ValueError(f"el objetivo {target_name} no coincide con su hash fijado ({self.frozen_hash} ≠ {pinned})")
        self.pinned_hash = pinned
        tmpl = self.spec["program_template"]
        k = tmpl.index("\nprogram ")
        self.store, self.program_cmd = tmpl[:k].strip(), tmpl[k + 1:].strip()
        self.prog_name = re.match(r"program\s+(\w+)", self.program_cmd).group(1)
        self.ref_program = re.sub(rf"^program\s+{self.prog_name}\b", f"program {self.prog_name}_ref", self.program_cmd, count=1)
        self.ref_program = self.ref_program.replace("__INVARIANT__", "True").replace("__VARIANT__", "(0::nat)")
        self.concl_ref = re.sub(rf"\b{self.prog_name}\b", f"{self.prog_name}_ref", self.spec["concl"])

    def _load_spec(self) -> dict:
        spec = json.loads((TARGETS / f"{self.target_name}.json").read_text(encoding="utf-8"))
        spec["aux"] = (TARGETS / spec["aux_file"]).read_text(encoding="utf-8") if spec.get("aux_file") else ""
        return spec

    @staticmethod
    def _hash(spec: dict) -> str:
        frozen = {k: spec.get(k, "") for k in ("imports", "aux", "program_template", "fixes", "assumes", "concl", "prelude")}
        return hashlib.sha256(json.dumps(frozen, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16]

    def target(self) -> dict:
        return {"id": f"isabelle:{self.spec['name']}", "statement_es": self.spec["statement_es"], "program_template": self.spec["program_template"],
                "fixes": self.spec["fixes"], "assumes": self.spec["assumes"], "concl": self.spec["concl"],
                "borrowed_lemmas": self.spec.get("borrowed_lemmas", []), "hash": self.frozen_hash}

    # -- utilidades
    @staticmethod
    def one_liner(v) -> tuple[str, str, str, int] | None:
        """(método de una línea, fuente, prover, ms) si la VC la cierra try0 o Sledgehammer con preplay terminado."""
        if v.try0:
            return v.try0, "try0", v.try0.split()[1].strip("()") if len(v.try0.split()) > 1 else "try0", int(v.try0_ms)
        if v.sh_found:
            m = _PREPLAYED.search(v.sh_message or "")
            if m:
                prover = _PROVER.search("\n".join(v.sh_messages or []))
                return m.group(1).strip(), "sledgehammer", prover.group(1) if prover else "?", int(v.sh_ms)
        return None

    def annotated_program(self, inv: str, var: str) -> str:
        # la anotación se inserta en una sola pasada y al final: nada la vuelve a examinar
        return _fill(self.program_cmd, {"INVARIANT": inv, "VARIANT": var})

    def build(self, work: Path, theory: str, name: str, timeout_s: float) -> tuple[int, str]:
        """Compila una teoría en una sesión con nombre único (no choca con IsaRL_Scratch de 08) y mata el árbol
        de procesos si se agota el tiempo."""
        session = f"IsaRL_U_{uuid.uuid4().hex[:10]}"
        (work / f"{name}.thy").write_text(theory, encoding="utf-8")
        # parallel_proofs = 0: sin él, Isabelle comprueba las pruebas `by` en paralelo y sigue ejecutando los comandos
        # siguientes, así que un marcador escrito después de un lema se escribiría aunque la prueba del lema fallara.
        (work / "ROOT").write_text(f"session {session} = {self.config08.PAPER_SESSION} +\n  options [document = false, timeout = 0, parallel_proofs = 0]\n"
                                   f"  theories\n    {name}\n", encoding="utf-8")
        cmd = [str(self.config08.ISABELLE_BIN), "build", "-o", "document=false"]
        for d in self.config08.session_dirs() + [str(work)]:
            cmd += ["-d", d]
        cmd.append(session)
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        try:
            out, _ = p.communicate(timeout=timeout_s)
            return p.returncode, out
        except subprocess.TimeoutExpired:
            kill_tree([p.pid])
            out, _ = p.communicate()
            return -9, (out or "") + f"\n[unirl] TIMEOUT tras {timeout_s:.0f} s"

    def same_program(self, inv: str, var: str) -> tuple[str, list[str]]:
        """Etapa 0: 'ok', 'parse' (la anotación no se analiza o no tipa), 'drift' (el programa cambió) o 'timeout'."""
        work = Path(tempfile.mkdtemp(prefix="same-", dir=str(self.config08.SCRATCH)))
        thy = _fill(SAME_THEORY, {"IMPORTS": self.spec["imports"], "STORE": self.store, "REFPROGRAM": self.ref_program,
                                  "NAME": self.prog_name, "DIR": str(work), "PROGRAM": "__AGENTPROGRAM__"})
        thy = thy.replace("__AGENTPROGRAM__", self.annotated_program(inv, var))  # el texto del agente entra el último
        rc, log = self.build(work, thy, "Same", min(self.build_timeout_s, 600))
        errors = [l for l in log.splitlines() if l.startswith("***")][:10]
        if rc == -9:
            return "timeout", errors
        if not (work / "parsed.ok").exists():
            return "parse", errors
        if rc != 0 or not (work / "same.ok").exists():  # la compilación entera debe pasar, no solo el marcador
            return "drift", errors
        return "ok", errors

    def _lemmas_build(self, lemmas: str) -> tuple[int, str, int, Path]:
        work = Path(tempfile.mkdtemp(prefix="lemmas-", dir=str(self.config08.SCRATCH)))
        thy = _fill(LEMMAS_THEORY, {"IMPORTS": self.spec["imports"], "AUX": self.spec["aux"], "STORE": self.store,
                                    "REFPROGRAM": self.ref_program, "FIXES": self.spec["fixes"], "ASSUMES": self.spec["assumes"],
                                    "PRELUDE": self.spec.get("prelude", ""), "CONCLREF": self.concl_ref, "DIR": str(work),
                                    "AGENTLEMMAS": "__AGENTLEMMASX__"})
        offset = thy[:thy.index("__AGENTLEMMASX__")].count("\n") + 1  # línea 1-based donde empieza el texto del agente
        thy = thy.replace("__AGENTLEMMASX__", lemmas)
        rc, log = self.build(work, thy, "Lemmas", self.build_timeout_s)
        return rc, log, offset, work

    def check_lemmas_in_kernel(self, lemmas: str) -> tuple[str, list[str], list[dict]]:
        """Etapa 0b: los lemas del agente se demuestran en el contexto de las hipótesis, con pruebas secuenciales.
        Devuelve ('ok' | 'failed' | 'timeout', errores, lemas verificados). Si el bloque falla, los lemas sin
        errores en su tramo se vuelven a compilar solos; los que pasan esa segunda compilación cuentan como
        verificados (sirven para la memoria entre episodios)."""
        rc, log, offset, work = self._lemmas_build(lemmas)
        errors = [l for l in log.splitlines() if l.startswith("***")][:15]
        blocks = split_lemmas(lemmas)
        if rc == -9:
            return "timeout", errors, []
        if rc == 0 and (work / "lemmas.ok").exists():
            return "ok", errors, [{"name": b["name"], "text": b["text"]} for b in blocks]
        bad_lines = {int(m) - offset for m in re.findall(r'\(line (\d+) of "[^"]*Lemmas\.thy"\)', log)}
        clean = [b for b in blocks if not any(b["first"] <= L <= b["last"] for L in bad_lines)]
        verified = []
        if clean and len(clean) < len(blocks):
            sub = "\n\n".join(b["text"] for b in clean)
            rc2, log2, _, work2 = self._lemmas_build(sub)
            if rc2 == 0 and (work2 / "lemmas.ok").exists():
                verified = [{"name": b["name"], "text": b["text"]} for b in clean]
        return "failed", errors, verified

    def lemas_uno_a_uno(self, lemmas: str, max_rondas: int = 12) -> tuple[list[dict], list[dict], list[str]]:
        """Separa los lemas que compilan de los que no: compila el bloque; si falla, quita el lema donde está el primer
        error (y con él los que ya no compilen sin él, en rondas siguientes) y repite. Con parallel_proofs = 0
        Isabelle se detiene en el primer error, así que cada ronda descubre a lo sumo un lema fallido.
        Devuelve (verificados, fallidos [{name, errors}], errores de la primera ronda)."""
        blocks = split_lemmas(lemmas)
        vivos, fallidos, primeros = list(blocks), [], []
        for ronda in range(max_rondas):
            if not vivos:
                break
            texto = "\n\n".join(b["text"] for b in vivos)
            rc, log, offset, work = self._lemmas_build(texto)
            errs = [l for l in log.splitlines() if l.startswith("***")][:15]
            if ronda == 0:
                primeros = errs
            if rc == 0 and (work / "lemmas.ok").exists():
                return [{"name": b["name"], "text": b["text"]} for b in vivos], fallidos, primeros
            if rc == -9:
                break
            lineas = [int(m) - offset for m in re.findall(r'\(line (\d+) of "[^"]*Lemmas\.thy"\)', log)]
            rel = split_lemmas(texto)
            culpable = next((i for i, b in enumerate(rel) if any(b["first"] <= L <= b["last"] for L in lineas)), None)
            if culpable is None:  # error fuera de los lemas (p. ej. el ML de comprobación): no se puede atribuir
                fallidos += [{"name": b["name"], "errors": errs[:6]} for b in vivos]
                vivos = []
                break
            fallidos.append({"name": vivos[culpable]["name"], "errors": errs[:6]})
            vivos = vivos[:culpable] + vivos[culpable + 1:]
        fallidos += [{"name": b["name"], "errors": ["sin verificar: se agotaron las rondas o el tiempo"]} for b in vivos]
        return [], fallidos, primeros

    def prelude_with(self, lemmas: str) -> str:
        return (self.spec.get("prelude", "") + "\n\n" + lemmas).strip()

    def assemble(self, inv: str, var: str, methods: list[str], work: Path, lemmas: str = "") -> dict:
        """Compila el teorema completo con las pruebas de una línea, lo pasa al programa congelado y devuelve
        {rc, oracles, skip_proof, prop, errors}."""
        work.mkdir(parents=True, exist_ok=True)
        out = work / "final.json"
        subgoals = "\n".join(f"  subgoal {m}" for m in methods)
        table = {"IMPORTS": self.spec["imports"], "AUX": self.spec["aux"], "STORE": self.store, "REFPROGRAM": self.ref_program,
                 "FIXES": self.spec["fixes"], "ASSUMES": self.spec["assumes"], "PRELUDE": "__AGENTPRELUDE__",
                 "CONCL": self.spec["concl"], "CONCLREF": self.concl_ref, "SUBGOALS": subgoals, "NAME": self.prog_name,
                 "OUT": str(out), "PROGRAM": "__AGENTPROGRAM__"}
        thy = (_fill(FINAL_THEORY, table).replace("__AGENTPROGRAM__", self.annotated_program(inv, var))
               .replace("__AGENTPRELUDE__", self.prelude_with(lemmas)))
        rc, log = self.build(work, thy, "Final", self.build_timeout_s)
        res = {"rc": rc, "errors": [l for l in log.splitlines() if l.startswith("***")][:10]}
        if out.exists():
            res.update(json.loads(out.read_text(encoding="utf-8")))
        return res

    def verify(self, target: dict, proposal: dict) -> Outcome:
        t0 = time.perf_counter()
        inv, var = (proposal or {}).get("invariant", "").strip(), (proposal or {}).get("variant", "").strip()
        lemmas = (merge_lemmas((proposal or {}).get("lemmas_library", ""), (proposal or {}).get("lemmas", "")).strip()
                  if self.allow_lemmas else "")
        if lemmas:
            bad = check_lemmas(lemmas)
            if bad and bad[0] in ("STATEMENT_DRIFT", "UNSOUND"):
                return Outcome(False, bad[0], 0.0, time.perf_counter() - t0, {"reason": bad[1], "stage": "lemmas"})
        # 1) salir del hueco se detecta antes que cualquier otra cosa, para que la razón de deriva cuente todos los intentos
        for text in (inv, var):
            bad = check_annotation(text)
            if bad and bad[0] == "STATEMENT_DRIFT":
                return Outcome(False, "STATEMENT_DRIFT", 0.0, time.perf_counter() - t0, {"reason": bad[1]})
        if self._hash(self._load_spec()) != self.frozen_hash or target.get("hash") != self.frozen_hash:
            return Outcome(False, "STATEMENT_DRIFT", 0.0, time.perf_counter() - t0, {"reason": "el objetivo congelado cambió en disco"})
        if not inv or not var:
            return Outcome(False, "INVALID_PROPOSAL", 0.0, 0.0, {"reason": "falta invariante o variante"})
        for text in (inv, var):
            bad = check_annotation(text)
            if bad:
                return Outcome(False, bad[0], 0.0, time.perf_counter() - t0, {"reason": bad[1]})
        if lemmas:
            bad = check_lemmas(lemmas)
            if bad:
                return Outcome(False, bad[0], 0.0, time.perf_counter() - t0, {"reason": bad[1], "stage": "lemmas"})
        # 2) etapa 0: el programa anotado es el congelado (en el kernel)
        same, errs = self.same_program(inv, var)
        if same == "timeout":
            return Outcome(False, "TIMEOUT", 0.0, time.perf_counter() - t0, {"stage": 0, "errors": errs})
        if same == "parse":
            return Outcome(False, "VCG_FAILED", 0.0, time.perf_counter() - t0, {"stage": 0, "errors": errs, "error": "la anotación no se analiza o no tipa"})
        if same == "drift":
            return Outcome(False, "STATEMENT_DRIFT", 0.0, time.perf_counter() - t0, {"stage": 0, "errors": errs, "reason": "el kernel no prueba que el programa anotado sea el congelado"})
        # 2b) etapa 0b: la demostración de cada lema del agente se verifica en el kernel antes de usarlo
        n_lemmas = len(re.findall(r"(?m)^\s*(?:lemma|corollary|theorem|proposition)\b", lemmas))
        verified_lemmas: list[dict] = []
        lemas_fallidos: list[dict] = []
        if lemmas and self.lemas_parciales:
            verified_lemmas, lemas_fallidos, _ = self.lemas_uno_a_uno(lemmas)
            lemmas = "\n\n".join(v["text"] for v in verified_lemmas)  # las VCs se evalúan solo con los que compilan
        elif lemmas:
            st, lerrs, verified_lemmas = self.check_lemmas_in_kernel(lemmas)
            if st == "timeout":
                return Outcome(False, "TIMEOUT", 0.0, time.perf_counter() - t0, {"stage": "0b", "errors": lerrs, "n_lemmas": n_lemmas})
            if st == "failed":
                return Outcome(False, "LEMMA_FAILED", 0.0, time.perf_counter() - t0,
                               {"stage": "0b", "errors": lerrs, "n_lemmas": n_lemmas, "verified_lemmas": verified_lemmas})
        # 3) VCs con el driver de 08
        work = Path(tempfile.mkdtemp(prefix="driver-", dir=str(self.config08.SCRATCH)))
        program = self.spec["aux"] + "\n" + self.store + "\n\n" + self.annotated_program(inv, var)
        r = self.driver.run_driver(imports=self.spec["imports"], program=program, fixes=self.spec["fixes"],
                                   assumes=self.spec["assumes"], concl=self.spec["concl"], prelude=self.prelude_with(lemmas),
                                   sh_timeout=self.sh_timeout, try0_timeout=self.try0_timeout, build_timeout_s=self.build_timeout_s, work=work)
        errors = [l for l in r.raw_log.splitlines() if l.startswith("***")]
        if r.build_rc == -9:
            kill_build_of(work)
            return Outcome(False, "TIMEOUT", 0.0, time.perf_counter() - t0, {"stage": 1, "errors": errors[:10]})
        if r.error:
            return Outcome(False, "VCG_FAILED", 0.0, time.perf_counter() - t0, {"stage": 1, "errors": errors[:10], "error": r.error})
        vcs, methods = [], []
        for v in r.vcs:
            ol = self.one_liner(v)
            vcs.append({"index": v.index, "goal": v.goal, "closed_by": ol[0] if ol else None, "source": ol[1] if ol else None,
                        "prover": ol[2] if ol else None, "ms": ol[3] if ol else int(v.sh_ms), "sh_outcome": v.sh_outcome,
                        "sh_message": (v.sh_message or "")[:500]})
            if ol:
                methods.append(ol[0])
        n_closed = len(methods)
        frac = n_closed / r.n_vcs if r.n_vcs else 1.0
        raw = {"n_vcs": r.n_vcs, "n_closed_auto": n_closed, "vcs": vcs, "vcg_ms": r.vcg_ms, "driver_s": round(r.elapsed_s, 1),
               "provers": r.provers, "errors": errors[:10], "same_program": "ok", "n_lemmas": n_lemmas, "verified_lemmas": verified_lemmas,
               "lemas_fallidos": lemas_fallidos, "lemas_parciales": self.lemas_parciales,
               "lemmas_used": sorted({m for v in vcs if v["closed_by"] for m in re.findall(r"[A-Za-z_][A-Za-z0-9_']*", v["closed_by"])}
                                     & set(re.findall(r"(?m)^\s*(?:lemma|corollary|theorem|proposition)\s+([A-Za-z_][A-Za-z0-9_']*)", lemmas)))}
        if n_closed < r.n_vcs:
            return Outcome(False, "VC_OPEN", frac, time.perf_counter() - t0, raw)
        # 4) ensamblado, paso al programa congelado y oráculos
        fin = self.assemble(inv, var, methods, Path(tempfile.mkdtemp(prefix="final-", dir=str(self.config08.SCRATCH))), lemmas)
        raw["final"] = fin
        if fin["rc"] == -9:
            return Outcome(False, "TIMEOUT", 0.0, time.perf_counter() - t0, raw)
        if fin["rc"] != 0 or "oracles" not in fin:
            return Outcome(False, "ASSEMBLY_FAILED", frac, time.perf_counter() - t0, raw)
        if fin["oracles"] or fin["skip_proof"] or not fin.get("axioms_ok", False):
            return Outcome(False, "UNSOUND", 0.0, time.perf_counter() - t0, raw)
        if not fin.get("prop_ok", False):  # el teorema aceptado debe ser, término a término, el enunciado congelado
            return Outcome(False, "STATEMENT_DRIFT", 0.0, time.perf_counter() - t0, raw)
        return Outcome(True, "ACCEPTED", 1.0, time.perf_counter() - t0, raw)

    def describe(self, target: dict) -> str:
        return (f"TEOREMA ({target['id']}): {target['statement_es']}\n\n"
                f"Variables fijas: {target['fixes']}\nHipótesis:\n{target['assumes']}\n\nTripleta de Hoare (total): {target['concl']}\n\n"
                f"Programa (Isabelle/ITrees; los huecos __INVARIANT__ y __VARIANT__ son lo único que puedes escribir):\n{target['program_template']}\n\n"
                f"Lemas prestados disponibles: {', '.join(target['borrowed_lemmas']) or 'ninguno'}.\n"
                "Escribe el invariante del bucle y el variante (expresión natural que decrece estrictamente), en sintaxis de Isabelle/HOL\n"
                "con símbolos ASCII (\\<and>, \\<le>, \\<lceil>, \\<rceil>, \\<bar>). Responde exactamente así:\n"
                "INVARIANT: <<< ... >>>\nVARIANT: <<< ... >>>" + (LEMMAS_HELP if self.allow_lemmas else ""))

    def parse(self, text: str) -> dict:
        # \b: "INVARIANT" contiene "VARIANT". (?!>): el cierre es el ÚLTIMO de una racha de '>', porque la
        # anotación puede terminar en un símbolo como \<rceil> pegado al cierre: "\<rceil>>>>".
        inv = re.search(r"\bINVARIANT:\s*<<<(.*?)>>>(?!>)", text, re.S)
        var = re.search(r"\bVARIANT:\s*<<<(.*?)>>>(?!>)", text, re.S)
        out = {"invariant": self._close_symbol((inv.group(1) if inv else "").strip()),
               "variant": self._close_symbol((var.group(1) if var else "").strip())}
        if self.allow_lemmas:
            lem = re.search(r"\bLEMMAS:\s*<<<(.*?)>>>(?!>)", text, re.S)
            out["lemmas"] = (lem.group(1) if lem else "").strip()
        return out

    @staticmethod
    def _nota_lemas(r: dict) -> str:
        """Con lemas parciales: qué lemas se verificaron y cuáles se descartaron, con sus errores literales."""
        if not r.get("lemas_parciales"):
            return ""
        ok = [v["name"] for v in r.get("verified_lemmas") or []]
        s = f"Lemas verificados y usados en las VCs: {', '.join(ok) if ok else 'ninguno'}.\n"
        for f in r.get("lemas_fallidos") or []:
            s += f"Lema DESCARTADO {f['name']}: " + " | ".join(e[:200] for e in f.get("errors", [])[:4]) + "\n"
        return s

    @staticmethod
    def _close_symbol(s: str) -> str:
        """Reparación de la colisión entre el delimitador «>>>» y un símbolo final de Isabelle: en «\\<rceil>>>»
        es ambiguo si el cierre se comió el «>» del símbolo. Un símbolo sin cerrar al final nunca es válido,
        así que se cierra. No cambia ninguna propuesta que ya fuera sintácticamente completa."""
        return re.sub(r"(\\<[A-Za-z_^][A-Za-z0-9_']*)$", r"\1>", s)

    def feedback(self, proposal: dict, outcome: Outcome) -> str:
        r = outcome.raw
        if outcome.outcome_label == "VC_OPEN":
            open_vcs = [v for v in r["vcs"] if not v["closed_by"]]
            lines = [f"VC_OPEN: {r['n_closed_auto']}/{r['n_vcs']} VCs cerradas automáticamente. Abiertas (texto literal del objetivo):"]
            lines += [f"  VC {v['index']}: {v['goal']}" for v in open_vcs]
            return self._nota_lemas(r) + "\n".join(lines)
        if outcome.outcome_label == "LEMMA_FAILED":
            return "LEMMA_FAILED: Isabelle rechazó los lemas (errores literales):\n" + "\n".join(r.get("errors", [])[:12])
        if outcome.outcome_label in ("VCG_FAILED", "TIMEOUT", "ASSEMBLY_FAILED"):
            errs = r.get("errors") or (r.get("final") or {}).get("errors", [])
            return self._nota_lemas(r) + f"{outcome.outcome_label}: " + " | ".join(errs[:5])
        return f"{outcome.outcome_label}: {r.get('reason', '')}"


LEMMAS_HELP = """

Además puedes escribir LEMAS AUXILIARES (opcional). Se demuestran en el contexto de las hipótesis de arriba (puedes
usar sus nombres, los lemas prestados y todo HOL-Analysis) y quedan disponibles para cerrar las VCs: Sledgehammer
los considera, y entran en el teorema final. Solo se admiten comandos `lemma nombre: "enunciado"` (o con
`assumes ... shows ...`) seguidos de una prueba completa (`by ...`, `using ... by ...`, `apply ... done` o
`proof ... qed`). No se admiten sorry, definiciones, notación, declare, ML ni tactic. Isabelle comprueba cada
prueba antes de usar los lemas: si alguna falla, el intento es LEMMA_FAILED y verás los errores literales.
Declara con `fixes` las variables nuevas de tus lemas (p. ej. `fixes k :: nat`): algunos nombres, como iter, son
constantes del marco ITrees y fuera de las VCs no se leen como variables.
Añade al final de tu respuesta:
LEMMAS: <<< lemma ... >>>"""


def make_verifier(cfg: dict) -> Verifier:
    j = cfg["judge"]
    if j == "lemma_graph":
        return LemmaGraphVerifier(cfg["project"], seed=int(cfg.get("seed", 0)))
    if j == "pep":
        return PEPVerifier(n=int(cfg.get("n", 4)), mu=float(cfg.get("mu", 0.0)), objective=cfg.get("objective", "fval"),
                           negative=bool(cfg.get("negative", False)), mode=cfg.get("mode", "improve"))
    if j == "isabelle":
        return IsabelleVerifier(cfg.get("target", "bisection"), sh_timeout=int(cfg.get("sh_timeout", 60)),
                                try0_timeout=int(cfg.get("try0_timeout", 5)), build_timeout_s=float(cfg.get("build_timeout_s", 1800)),
                                expected_hash=cfg.get("target_hash"), allow_lemmas=bool(cfg.get("allow_lemmas", False)),
                                lemas_parciales=bool(cfg.get("lemas_parciales", False)))
    if j == "isabelle_theorem":
        from .gd_isabelle import TheoremVerifier
        kw = {"build_timeout_s": float(cfg.get("build_timeout_s", 300)), "cortesia": bool(cfg.get("cortesia", True)),
              "aislado": bool(cfg.get("aislado", True))}
        if cfg.get("peldano"):  # peldaño del corpus: exige la aprobación de Carlos (corpus.NoAprobado si no la hay)
            return TheoremVerifier.desde_corpus(cfg["peldano"], cfg.get("corpus", "raices"), **kw)
        return TheoremVerifier(cfg.get("target"), expected_hash=cfg.get("target_hash"), **kw)
    raise ValueError(f"juez desconocido: {j}")
