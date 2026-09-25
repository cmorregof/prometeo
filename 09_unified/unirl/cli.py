"""CLI de unirl.

    python -m unirl run --config configs/bisection_graph.toml --episodes 20 [--model X] [--budget N] [--shaped --beta 0.5]
    python -m unirl summary runs/ [--json out.json]   # una tabla: entorno, juez, modelo, episodios, t* (mediana), resultados
    python -m unirl target --config ...                # imprime lo que ve el proponente

En `summary`, t* es el número de intentos hasta ACCEPTED, con t* = B si el episodio no se aceptó (definición
de la nota técnica); se informa además cuántos episodios se aceptaron. Las carpetas que empiezan por «_»
(pilotos, corridas descartadas) se excluyen.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import subprocess
import sys
import tomllib
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from .env import ProofEnv
from .loop import run_episodes
from .verifiers import ROOT, make_verifier

PKG = Path(__file__).resolve().parent


def load_config(path: Path) -> dict:
    return tomllib.loads(Path(path).read_text(encoding="utf-8"))


def make_provider(cfg: dict):
    sys.path.insert(0, str(ROOT / "06_stepsizes"))
    from steprl.providers import make_provider as mk  # reutiliza providers.py del 06 tal cual (lee 06/.env)

    kw = {}
    if cfg.get("provider") == "openai" and cfg.get("effort"):
        kw["reasoning_effort"] = cfg["effort"]
    if cfg.get("provider") == "anthropic" and cfg.get("effort"):
        kw["effort"] = cfg["effort"]
    interno = mk(cfg.get("provider", "openai"), cfg.get("model"), **kw)
    if cfg.get("provider", "openai") == "openai" and cfg.get("contabilidad", True):
        # toda llamada a OpenAI pasa por el libro de gastos (tope en dólares del proyecto y tope de llamadas de la fase)
        from .gasto import Libro, ProveedorContable, TOPE_USD
        libro = Libro(tope_usd=float(cfg.get("tope_usd", TOPE_USD)))
        return ProveedorContable(interno, libro, fase=cfg.get("fase", "otras"), corrida=cfg.get("name", "?"),
                                 tope_llamadas=cfg.get("tope_llamadas"))
    return interno


def code_fingerprint() -> dict:
    h = hashlib.sha256()
    for f in sorted(PKG.glob("*.py")):
        h.update(f.read_bytes())
    try:
        commit = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
        dirty = bool(subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain", "09_unified/unirl"], capture_output=True, text=True).stdout.strip())
    except Exception:
        commit, dirty = "", None
    return {"unirl_sha256": h.hexdigest()[:16], "git_commit": commit, "unirl_dirty": dirty}


def cmd_run(args) -> int:
    cfg = load_config(args.config)
    if args.model:
        cfg["model"] = args.model
    if args.budget:
        cfg["budget"] = args.budget
    if args.effort:
        cfg["effort"] = args.effort
    verifier = make_verifier(cfg)
    shaped = bool(args.shaped or cfg.get("shaped", False))
    beta = float(args.beta if args.beta is not None else cfg.get("beta", 0.5))
    env = ProofEnv(verifier, budget=int(cfg.get("budget", 5)), shaped=shaped, beta=beta, drift_penalty=float(cfg.get("drift_penalty", 0.0)))
    provider = make_provider(cfg)
    tag = f"{cfg.get('model', '')}-{cfg.get('effort', '')}".strip("-").replace("/", "_")
    out = Path(args.out) / cfg["name"] / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{tag}"
    if out.exists():
        raise SystemExit(f"ya existe {out}: dos corridas no pueden compartir carpeta")
    meta = {"env": cfg["name"], "judge": verifier.name, "provider": cfg.get("provider", "openai"), "model": cfg.get("model", ""),
            "effort": cfg.get("effort", ""), "budget": env.budget, "shaped": env.shaped, "beta": env.beta if shaped else 0.0,
            "run": out.name}
    extra = {"config": cfg, "code": code_fingerprint()}
    print(f"entorno {cfg['name']} · juez {verifier.name} · modelo {meta['model']} · presupuesto {env.budget} pasos · {args.episodes} episodios → {out}")
    memory = None
    if cfg.get("memory", "none") != "none":
        from .loop import Memory
        mpath = Path(cfg["memory_file"]) if cfg.get("memory_file") else out / "memoria.json"
        memory = Memory(mpath, wording=cfg.get("memory_prompt", "v2"))
        meta["memory"] = cfg["memory"]
        meta["memory_prompt"] = memory.wording
    from .loop import ProviderFatal
    try:
        eps = run_episodes(env, provider, args.episodes, out, meta, extra=extra, memory=memory)
    except ProviderFatal as e:
        print(f"\nCORRIDA ABORTADA: error del proveedor que no se arregla reintentando: {e}")
        (out / "ABORTADA.txt").write_text(f"error del proveedor: {e}\n", encoding="utf-8")
        return 3
    acc = [e["steps"] for e in eps if e["accepted"]]
    tstar = [e["steps"] if e["accepted"] else env.budget for e in eps]
    print(f"\naceptados {len(acc)}/{len(eps)}; t* (mediana, censurada en B = {env.budget}): {statistics.median(tstar):g}")
    return 0


def load_attempts(runs_dir: Path) -> list[dict]:
    recs = []
    for f in sorted(Path(runs_dir).rglob("attempts.jsonl")):
        if any(part.startswith("_") for part in f.relative_to(runs_dir).parts):
            continue
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                r.setdefault("run", f.parent.name)
                recs.append(r)
    return recs


def summarize(runs_dir: Path) -> list[dict]:
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for r in load_attempts(runs_dir):
        groups[(r["env"], r["judge"], r["model"], r.get("effort", ""))].append(r)
    rows = []
    for (env, judge, model, effort), recs in sorted(groups.items()):
        per_ep: dict[tuple, list[dict]] = defaultdict(list)
        for r in recs:
            per_ep[(r["run"], r["episode"])].append(r)
        tstar, accepted_eps, budgets, unfinished, no_model = [], 0, set(), 0, 0
        for ep_recs in list(per_ep.values()):
            ep_recs.sort(key=lambda r: r["step"])
            B = int(ep_recs[0].get("budget", len(ep_recs)))
            if not any(r["accepted"] for r in ep_recs) and len(ep_recs) < B:
                unfinished += 1  # episodio en curso: ni aceptado ni agotado; no entra en t*
                continue
            # un episodio sin aceptar cuyo presupuesto se gastó en fallos del proveedor (PROVIDER_ERROR: el modelo no
            # respondió y el juez no evaluó nada) no mide t*: no entra, se cuenta aparte
            evaluated = [r for r in ep_recs if r["outcome_label"] != "PROVIDER_ERROR"]
            if not any(r["accepted"] for r in ep_recs) and len(evaluated) < B:
                no_model += 1
                continue
            budgets.add(B)
            acc = [r["step"] for r in ep_recs if r["accepted"]]
            if acc:
                accepted_eps += 1
                tstar.append(acc[0])
            else:
                tstar.append(B)
        counts = Counter(r["outcome_label"] for r in recs)
        judged = [r for r in recs if r["outcome_label"] != "PROVIDER_ERROR"] or recs
        drift = None
        if judge == "isabelle":
            drift = (counts.get("STATEMENT_DRIFT", 0), counts.get("VC_OPEN", 0))
        elif judge == "lemma_graph":
            drift = (counts.get("DISTRACTOR", 0), counts.get("INVALID_STEP", 0))
        if not tstar:
            continue
        rows.append({"env": env, "judge": judge, "model": model, "effort": effort, "episodes": len(tstar), "unfinished": unfinished, "no_model_eps": no_model, "accepted_eps": accepted_eps,
                     "attempts": len(recs), "budget": sorted(budgets), "tstar_median": statistics.median(tstar),
                     "tstar_dist": dict(sorted(Counter(tstar).items())), "outcomes": dict(sorted(counts.items())),  # etiquetas: todos los intentos
                     "drift_num_den": drift,
                     "judge_s_mean": round(statistics.fmean(r["cost_s"] for r in judged), 2),  # sin PROVIDER_ERROR
                     "llm_s_mean": round(statistics.fmean(r["llm_s"] for r in judged), 1),
                     "runs": sorted({r["run"] for r in recs})})
    return rows


def cmd_summary(args) -> int:
    rows = summarize(Path(args.runs))
    if not rows:
        print("sin corridas en", args.runs)
        return 1
    hdr = f"{'entorno':<18} {'juez':<12} {'modelo (esfuerzo)':<20} {'ep.':>4} {'acept.':>6} {'B':>3} {'t* med.':>7}  resultados"
    print(hdr)
    print("-" * len(hdr))
    for r in rows:
        outs = ", ".join(f"{k} {v}" for k, v in r["outcomes"].items())
        B = "/".join(map(str, r["budget"]))
        mdl = f"{r['model']} ({r['effort']})" if r['effort'] else r['model']
        print(f"{r['env']:<18} {r['judge']:<12} {mdl:<20} {r['episodes']:>4} {r['accepted_eps']:>6} {B:>3} {r['tstar_median']:>7g}  {outs}"
              f"  (juez {r['judge_s_mean']} s/intento, llm {r['llm_s_mean']} s)")
    if args.json:
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json).write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


def cmd_target(args) -> int:
    cfg = load_config(args.config)
    v = make_verifier(cfg)
    print(v.describe(v.target()))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="unirl")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--config", required=True, type=Path)
    r.add_argument("--episodes", type=int, default=20)
    r.add_argument("--model", default=None)
    r.add_argument("--effort", default=None)
    r.add_argument("--budget", type=int, default=None)
    r.add_argument("--shaped", action="store_true")
    r.add_argument("--beta", type=float, default=None)
    r.add_argument("--out", type=Path, default=Path("runs"))
    r.set_defaults(fn=cmd_run)
    s = sub.add_parser("summary")
    s.add_argument("runs", nargs="?", default="runs")
    s.add_argument("--json", default=None)
    s.set_defaults(fn=cmd_summary)
    tb = sub.add_parser("tables", help="fragmentos LaTeX para la nota técnica")
    tb.add_argument("runs", nargs="?", default="runs")
    tb.add_argument("--out", default="docs/nota")
    tb.add_argument("--repro", default=str(ROOT / "08_isabelle" / "runs" / "repro_bisection.json"))
    tb.set_defaults(fn=lambda a: __import__("unirl.report", fromlist=["cmd_tables"]).cmd_tables(a))
    t = sub.add_parser("target")
    t.add_argument("--config", required=True, type=Path)
    t.set_defaults(fn=cmd_target)
    ip = sub.add_parser("informe", help="informe PDF de una o varias corridas del mismo modelo (docs/informes/ESPEC.md)")
    ip.add_argument("--runs", nargs="+", default=None, help="carpetas runs/<env>/<id>")
    ip.add_argument("--ultima", default=None, help="env1,env2,...: la corrida más reciente de runs/<env>/ con --model")
    ip.add_argument("--model", default=None)
    ip.add_argument("--slug", default=None, help="escribe en docs/informes/<slug>")
    ip.add_argument("--out", default=None, help="carpeta de salida (en lugar de --slug)")
    ip.add_argument("--runs-root", default=None, help="raíz de las corridas (por defecto 09_unified/runs)")
    ip.add_argument("--no-pdf", action="store_true", help="solo escribe informe.tex, sin compilar")
    ip.set_defaults(fn=lambda a: __import__("unirl.informe", fromlist=["cmd_informe"]).cmd_informe(a))
    args = ap.parse_args(argv)
    return args.fn(args)
