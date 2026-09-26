"""Genera, desde los JSONL de `runs/`, los fragmentos LaTeX que usa la nota técnica:

* `resultados_auto.tex`: macros `\\R{clave}{campo}` con cada número citado en el texto, y las tablas
  de resumen, de etiquetas por juez y de intentos del juez Isabelle;
* `propuestas_isabelle.tex`: las anotaciones propuestas por el agente, literales.

Ningún número de las corridas de unirl se copia a mano (los recuentos del artículo y de 08 en la tabla de
reproducción sí, con su fuente citada).

    python -m unirl tables runs/ --out docs/nota/
"""

from __future__ import annotations

import json
import re
import statistics
import textwrap
from collections import Counter, defaultdict
from pathlib import Path

from .cli import load_attempts, summarize
from .verifiers import _PREPLAYED

ENV_KEY = {"bisection_graph": "BisG", "fixedpoint_graph": "PfG", "taylor_graph": "TayG", "newton_graph": "NewG",
           "secant_graph": "SecG", "bisection_isabelle": "BisI", "bisection_isabelle_lemas": "BisIL", "gd_pep_n4": "PepN"}
ENV_NAME = {"bisection_graph": "01 bisección", "fixedpoint_graph": "02 punto fijo", "taylor_graph": "03 Taylor",
            "newton_graph": "04 Newton", "secant_graph": "05 secante", "bisection_isabelle": "01 bisección",
            "bisection_isabelle_lemas": "01 bisección + lemas", "gd_pep_n4": "06 pasos GD"}
JUDGE_TEX = {"lemma_graph": "$V_G$", "pep": "$V_P$", "isabelle": "$V_I$"}
MODEL_KEY = {"gpt-5.4-mini": "Mini", "gpt-6-luna": "Luna"}
LABELS = {"lemma_graph": ["ACCEPTED", "INVALID_STEP", "DISTRACTOR", "UNKNOWN_LEMMA", "INCOMPLETE", "PROVIDER_ERROR"],
          "isabelle": ["ACCEPTED", "VC_OPEN", "VCG_FAILED", "LEMMA_FAILED", "ASSEMBLY_FAILED", "UNSOUND", "STATEMENT_DRIFT", "TIMEOUT", "INVALID_PROPOSAL", "PROVIDER_ERROR"]}
SC = {"ACCEPTED": "Accepted", "INVALID_STEP": "Invalid\\_Step", "DISTRACTOR": "Distractor", "UNKNOWN_LEMMA": "Unknown\\_Lemma",
      "INCOMPLETE": "Incomplete", "PROVIDER_ERROR": "Provider\\_Error", "VC_OPEN": "VC\\_Open", "VCG_FAILED": "VCG\\_Failed",
      "ASSEMBLY_FAILED": "Assembly\\_Failed", "LEMMA_FAILED": "Lemma\\_Failed", "UNSOUND": "Unsound", "STATEMENT_DRIFT": "Statement\\_Drift", "TIMEOUT": "Timeout",
      "INVALID_PROPOSAL": "Invalid\\_Proposal"}
ASCII = {"∧": "\\<and>", "∨": "\\<or>", "≤": "\\<le>", "≥": "\\<ge>", "¬": "\\<not>", "∃": "\\<exists>", "∀": "\\<forall>",
         "⌈": "\\<lceil>", "⌉": "\\<rceil>", "⟶": "\\<longrightarrow>", "→": "\\<longrightarrow>", "≠": "\\<noteq>", "|": "|"}


def tex(s: str) -> str:
    return (str(s).replace("\\", "\\textbackslash{}").replace("_", "\\_").replace("%", "\\%").replace("&", "\\&")
            .replace("#", "\\#").replace("{", "\\{").replace("}", "\\}").replace("\\textbackslash\\{\\}", "\\textbackslash{}"))


def key(env: str, model: str) -> str:
    return ENV_KEY.get(env, re.sub(r"[^A-Za-z]", "", env)) + MODEL_KEY.get(model, re.sub(r"[^A-Za-z]", "", model))


def proposer(model: str, effort: str) -> str:
    return f"\\texttt{{{tex(model)}}} ({effort})" if effort else f"\\texttt{{{tex(model)}}}"


def _split_goal(goal: str) -> tuple[str, str]:
    """(premisas, conclusión) del texto de una VC «⋀x. ⟦p1; …⟧ ⟹ c»."""
    parts = goal.split("\\<Longrightarrow>")
    return ("\\<Longrightarrow>".join(parts[:-1]), parts[-1]) if len(parts) > 1 else ("", goal)


_NEW_GUARD = ("tol < u - (l + u) / 2", "tol < (l + u) / 2 - l", "tol < (b - a) / (2 ^ iter * 2)", "tol < (b - a) / (2 * 2 ^ iter)")


def vc_kind(goal: str, variant: str = "") -> str:
    """Clasificación heurística de una VC de la bisección por su conclusión y sus premisas:
    postcondición (la guarda negada «¬ tol < …» está entre las premisas: es la salida del bucle),
    inicialización (VC sin parámetros ⋀), invariante (preservación: la guarda del nuevo estado está entre las
    premisas, o nada de lo anterior) y variante (decrecimiento estricto: «Suc iter <», una comparación estricta
    entre techos, o «int iter < ⌈…⌉» cuando el variante propuesto es ⌈…⌉ − int iter)."""
    prem, concl = _split_goal(goal)
    if "\\<not> tol <" in prem:
        return "postcondición"
    if "\\<And>" not in goal:
        return "inicialización"
    if any(g in prem for g in _NEW_GUARD):
        return "invariante"
    c = concl.strip()
    if ("Suc iter <" in c or re.search(r"\\<rceil>\)?\s*<\s*(?:nat\s*)?\(?\s*\\<lceil>", c)
            or ("- int iter" in variant and re.match(r"int iter < \\<lceil>", c))):
        return "variante"
    if "int iter = \\<lceil>" in c or ("\\<exists>c" in c and "\\<le> tol" in c):
        return "postcondición"
    return "invariante"


PAPER = json.loads((Path(__file__).resolve().parents[1] / "corpus" / "curado" / "programas" / "bisection.json").read_text(encoding="utf-8"))


def _norm(t: str) -> str:
    return re.sub(r"[\s()]", "", t)


def num(x: float, nd: int = 1) -> str:
    """Número con coma decimal para la nota en español."""
    return f"{x:.{nd}f}".replace(".", "{,}")


def macro(k: str, field: str, value) -> str:
    return f"\\expandafter\\def\\csname R@{k}@{field}\\endcsname{{{value}}}"


def ascii_isabelle(s: str) -> str:
    for u, a in ASCII.items():
        s = s.replace(u, a)
    return "".join(c if ord(c) < 128 else "?" for c in s)


def build(runs_dir: Path, repro_json: Path | None = None) -> tuple[str, str]:
    order = list(ENV_NAME)
    rows = sorted(summarize(runs_dir), key=lambda r: (r["judge"] == "isabelle", order.index(r["env"]) if r["env"] in order else 99,
                                                      r["model"] != "gpt-5.4-mini"))
    recs = load_attempts(runs_dir)
    out = ["% Generado por `python -m unirl tables`. No editar a mano.",
           "\\providecommand{\\R}[2]{\\csname R@#1@#2\\endcsname}"]
    for r in rows:
        k = key(r["env"], r["model"])
        vals = {"ep": r["episodes"], "acc": r["accepted_eps"], "att": r["attempts"], "B": "/".join(map(str, r["budget"])),
                "tstar": f"{r['tstar_median']:g}".replace(".", "{,}"), "judges": num(r['judge_s_mean'], 0), "llms": num(r['llm_s_mean'], 0),
                "model": tex(r["model"]), "effort": r["effort"]}
        for lab in LABELS.get(r["judge"], []):
            vals[lab] = r["outcomes"].get(lab, 0)
        if r["drift_num_den"]:
            vals["driftnum"], vals["driftden"] = r["drift_num_den"]
        out += [macro(k, f, v) for f, v in vals.items()]

    # --- tabla de resumen
    out += ["", "\\newcommand{\\TablaResumen}{%", "\\begin{tabular}{@{}lllrrrlrr@{}}", "\\toprule",
            "método & juez & proponente & ep. & acept. & $t^*$ med. & distribución de $t^*$ & s juez & s LLM \\\\",
            "\\midrule"]
    for r in rows:
        dist = ", ".join(f"{t}:{n}" for t, n in r["tstar_dist"].items())
        out.append(f"{ENV_NAME.get(r['env'], tex(r['env']))} & {JUDGE_TEX[r['judge']]} & {proposer(r['model'], r['effort'])} & "
                   f"{r['episodes']} & {r['accepted_eps']} & {num(r['tstar_median'], 1).replace('{,}0', '')} & {dist} & {num(r['judge_s_mean'])} & {num(r['llm_s_mean'])} \\\\")
    out += ["\\bottomrule", "\\end{tabular}}", ""]

    # --- etiquetas por juez
    for judge, name in (("lemma_graph", "TablaEtiquetasG"), ("isabelle", "TablaEtiquetasI")):
        jr = [r for r in rows if r["judge"] == judge]
        if not jr:
            out.append(f"\\newcommand{{\\{name}}}{{(sin corridas)}}")
            continue
        labs = [l for l in LABELS[judge] if any(r["outcomes"].get(l) for r in jr)]
        out += [f"\\newcommand{{\\{name}}}{{%", "\\begin{tabular}{@{}ll" + "r" * (len(labs) + 2) + "@{}}", "\\toprule",
                "método & proponente & intentos & " + " & ".join(f"\\textsc{{{SC[l]}}}" for l in labs) + " & razón de deriva \\\\", "\\midrule"]
        for r in jr:
            dn, dd = r["drift_num_den"]
            ratio = (f"{dn}/{dd} = {num(dn / dd, 2)}" if dd else ("---" if not dn else f"{dn}/0"))
            out.append(f"{ENV_NAME.get(r['env'], tex(r['env']))} & {proposer(r['model'], r['effort'])} & {r['attempts']} & "
                       + " & ".join(str(r["outcomes"].get(l, 0)) for l in labs) + f" & {ratio} \\\\")
        out += ["\\bottomrule", "\\end{tabular}}", ""]

    # --- intentos del juez Isabelle
    iso = sorted((r for r in recs if r["judge"] == "isabelle"), key=lambda r: (r["model"], r["run"], r["episode"], r["step"]))
    open_kinds_total: dict[str, Counter] = defaultdict(Counter)
    best: dict[str, float] = defaultdict(float)
    out += ["\\newcommand{\\TablaIntentosI}{%", "\\begin{longtable}{@{}lrrlrlr@{}}",
            "\\caption{Intentos de $V_I$ en orden. ``Cerradas'' cuenta las VCs con prueba de una línea; el tipo de cada VC abierta se asigna por su conclusión y sus premisas (heurística). Las anotaciones están en el Apéndice~\\ref{app:propuestas}.}\\label{tab:intentosI}\\\\", "\\toprule",
            "proponente & ep. & paso & resultado & cerradas & VCs abiertas (tipo) & s juez \\\\", "\\midrule", "\\endhead"]
    for r in iso:
        raw = r.get("raw") or {}
        n, c = raw.get("n_vcs"), raw.get("n_closed_auto")
        var_r = (r.get("proposal") or {}).get("variant", "")
        kinds = Counter(vc_kind(v["goal"], var_r) for v in raw.get("vcs", []) if not v.get("closed_by"))
        open_kinds_total[r["model"]].update(kinds)
        if n:
            best[r["model"]] = max(best[r["model"]], c / n)
        closed = f"{c}/{n}" if n else "---"
        kinds_s = ", ".join(f"{k} {v}" for k, v in sorted(kinds.items())) or "---"
        out.append(f"{proposer(r['model'], r['effort'])} & {r['episode']} & {r['step']} & \\textsc{{{SC.get(r['outcome_label'], tex(r['outcome_label']))}}} & "
                   f"{closed} & {kinds_s} & {r['cost_s']:.0f} \\\\")
    out += ["\\bottomrule", "\\end{longtable}}", ""]
    for model, cnt in open_kinds_total.items():
        k = key("bisection_isabelle", model)
        for kind, v in cnt.items():
            out.append(macro(k, "open" + {"variante": "var", "postcondición": "post", "invariante": "inv", "inicialización": "ini"}[kind], v))
        out.append(macro(k, "bestfrac", num(best[model], 2)))
    # rasgos de las propuestas, por modelo
    for model in {r["model"] for r in iso}:
        rs = [r for r in iso if r["model"] == model]
        k = key("bisection_isabelle", model)
        props_m = [(r.get("proposal") or {}) for r in rs]
        withvcs = [r for r in rs if (r.get("raw") or {}).get("n_vcs")]
        fr = [r["raw"]["n_closed_auto"] / r["raw"]["n_vcs"] for r in withvcs]
        out += [macro(k, "nprops", len(rs)),
                macro(k, "nexists", sum("\\<exists>c" in p.get("invariant", "") for p in props_m)),
                macro(k, "nulvar", sum(bool(re.search(r"\(\s*u\s*-\s*l\s*\)", p.get("variant", ""))) for p in props_m)),
                macro(k, "nitervar", sum("iter" in p.get("variant", "") for p in props_m)),
                macro(k, "meanfrac", num(statistics.fmean(fr), 2) if fr else "---"),
                macro(k, "npostopen", sum(any(vc_kind(v["goal"], r["proposal"].get("variant", "")) == "postcondición" and not v["closed_by"] for v in r["raw"].get("vcs", [])) for r in withvcs)),
                macro(k, "nvcgfail", sum(r["outcome_label"] == "VCG_FAILED" for r in rs)),
                macro(k, "nsameinv", sum(_norm(p.get("invariant", "")) == _norm(PAPER["paper_invariant"]) for p in props_m)),
                macro(k, "nsamevar", sum(_norm(p.get("variant", "")) == _norm(PAPER["paper_variant"]) for p in props_m)),
                macro(k, "nexistsopen", sum(1 for r in withvcs if "\\<exists>c" in (r.get("proposal") or {}).get("invariant", "")
                                            and any(not v["closed_by"] and vc_kind(v["goal"], r["proposal"].get("variant", "")) == "invariante"
                                                    and "\\<exists>c" in v["goal"].split("\\<Longrightarrow>")[-1] for v in r["raw"]["vcs"]))),
                macro(k, "nvaropen", sum(1 for r in withvcs for v in r["raw"]["vcs"] if not v["closed_by"] and vc_kind(v["goal"], r["proposal"].get("variant", "")) == "variante")),
                macro(k, "nvaropenlog", sum(1 for r in withvcs for v in r["raw"]["vcs"] if not v["closed_by"] and vc_kind(v["goal"], r["proposal"].get("variant", "")) == "variante"
                                            and "log 2" in v["goal"].split("\\<Longrightarrow>")[-1])),
                macro(k, "vcsmin", min((r["raw"]["n_vcs"] for r in withvcs), default="---")),
                macro(k, "vcsmax", max((r["raw"]["n_vcs"] for r in withvcs), default="---"))]
    closed_counts = [(r["model"], (r.get("raw") or {}).get("n_closed_auto"), (r.get("raw") or {}).get("n_vcs")) for r in iso]
    for model in {m for m, _, _ in closed_counts}:
        cs = [(c, n) for m, c, n in closed_counts if m == model and n]
        if cs:
            k = key("bisection_isabelle", model)
            bc, bn = max(cs, key=lambda x: x[0] / x[1])
            out.append(macro(k, "bestcn", f"{bc}/{bn}"))
            out.append(macro(k, "nwithvcs", len(cs)))

    # --- reproducción de la Tabla 1 (08)
    if repro_json and Path(repro_json).exists():
        d = json.loads(Path(repro_json).read_text(encoding="utf-8"))
        res = d["result"]
        out.append(macro("Repro", "nvcs", res["n_vcs"]))
        out.append(macro("Repro", "closed", res["n_closed_auto"]))
        out.append(macro("Repro", "seconds", f"{d['seconds']:.0f}"))

    # --- línea base: invariante del paper bajo V_I (tools/baseline_paper.py) y prueba de adelgazamiento (tools/sh_goal.py)
    base = Path(runs_dir) / "_baseline" / "bisection.json"
    if base.exists():
        b = json.loads(base.read_text(encoding="utf-8"))
        o = b["outcome"]
        raw = o.get("raw", {})
        out += [macro("BaseI", "label", SC.get(o["outcome_label"], tex(o["outcome_label"]))), macro("BaseI", "nvcs", raw.get("n_vcs", "---")),
                macro("BaseI", "closed", raw.get("n_closed_auto", "---")), macro("BaseI", "seconds", f"{b['seconds']:.0f}")]
        kinds = Counter(vc_kind(v["goal"], b.get("variant", PAPER["paper_variant"])) for v in raw.get("vcs", []) if not v.get("closed_by"))
        for kind, abbr in (("variante", "var"), ("postcondición", "post"), ("invariante", "inv"), ("inicialización", "ini")):
            out.append(macro("BaseI", "open" + abbr, kinds.get(kind, 0)))
    else:
        out += [macro("BaseI", f, "\\textbf{??}") for f in ("label", "nvcs", "closed", "seconds", "openvar", "openpost", "openinv", "openini")]
    shg = Path(runs_dir) / "_baseline" / "sh_goals.json"
    if shg.exists():
        d = json.loads(shg.read_text(encoding="utf-8"))
        out.append(macro("SH", "timeout", d["timeout"]))
        for pre, res in d["results"].items():
            for g in res:
                if "name" in g:
                    ok = bool(_PREPLAYED.search(g.get("message", ""))) if g.get("found") else False
                    out.append(macro("SH", f"{pre}{g['name']}", "sí" if ok else "no"))
                    out.append(macro("SH", f"{pre}{g['name']}ms", f"{g['ms'] / 1000:.0f}"))
                    m = _PREPLAYED.search(g.get("message", ""))
                    out.append(macro("SH", f"{pre}{g['name']}proof", tex(m.group(1)) if m else "---"))

    ph = Path(runs_dir) / "_baseline" / "posthoc_stage0.json"
    if ph.exists():
        rows_ph = json.loads(ph.read_text(encoding="utf-8"))
        out += [macro("PostH", "n", len(rows_ph)), macro("PostH", "consistent", sum(r["consistent"] for r in rows_ph)),
                macro("PostH", "allowfail", sum(bool(r["allowlist"]) for r in rows_ph)),
                macro("PostH", "drift", sum(r["stage0"] == "drift" for r in rows_ph))]
    else:
        out += [macro("PostH", f, "\\textbf{??}") for f in ("n", "consistent", "allowfail", "drift")]

    # --- propuestas literales
    props = ["% Generado por `python -m unirl tables`. No editar a mano."]
    for r in iso:
        p = r.get("proposal") or {}
        inv = ascii_isabelle(p.get("invariant", ""))
        var = ascii_isabelle(p.get("variant", ""))
        body = "\n".join(textwrap.wrap("INVARIANT: " + inv, 92, subsequent_indent="    ", break_on_hyphens=False) or ["INVARIANT:"]) + "\n" + \
               "\n".join(textwrap.wrap("VARIANT:   " + var, 92, subsequent_indent="    ", break_on_hyphens=False) or ["VARIANT:"])
        raw = r.get("raw") or {}
        res = r["outcome_label"] + (f", {raw['n_closed_auto']}/{raw['n_vcs']} VCs" if raw.get("n_vcs") else "")
        props += [f"\\par\\medskip\\noindent\\textbf{{{proposer(r['model'], r['effort'])}, episodio {r['episode']}, paso {r['step']}:}} \\textsc{{{SC.get(r['outcome_label'], tex(r['outcome_label']))}}}\\par\\nopagebreak",
                  "\\begin{lstlisting}", body, "\\end{lstlisting}", f"% {res}"]
    return "\n".join(out) + "\n", "\n".join(props) + "\n"


def cmd_tables(args) -> int:
    outdir = Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)
    a, b = build(Path(args.runs), Path(args.repro) if args.repro else None)
    (outdir / "resultados_auto.tex").write_text(a, encoding="utf-8")
    (outdir / "propuestas_isabelle.tex").write_text(b, encoding="utf-8")
    print(f"escrito {outdir / 'resultados_auto.tex'} y {outdir / 'propuestas_isabelle.tex'}")
    return 0
