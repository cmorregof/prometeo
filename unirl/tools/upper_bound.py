"""Cota superior con la acción de lemas: la anotación del artículo más sus propias pruebas manuales escritas
como lemas del agente (los tres hechos previos, la línea smt del variante y bisect_root_extract, copiados de
Bisection.thy@0e7830d). Si el juez no acepta esto, la acción de lemas no basta.  → runs/_baseline/upper_bound.json"""
import json, sys, time
from dataclasses import asdict
from pathlib import Path
HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
from unirl.verifiers import IsabelleVerifier  # noqa: E402
v = IsabelleVerifier("bisection", allow_lemmas=True)
lemmas = (HERE / "tools" / "upper_bound_lemmas.thy.part").read_text(encoding="utf-8")
t0 = time.time()
o = v.verify(v.target(), {"invariant": v.spec["paper_invariant"], "variant": v.spec["paper_variant"], "lemmas": lemmas})
out = HERE / "runs" / "_baseline" / "upper_bound.json"
out.write_text(json.dumps({"seconds": round(time.time() - t0, 1), "outcome": asdict(o)}, ensure_ascii=False, indent=1), encoding="utf-8")
print(o.outcome_label, o.raw.get("n_closed_auto"), "/", o.raw.get("n_vcs"), "lemas usados:", o.raw.get("lemmas_used"), "final:", {k: (o.raw.get("final") or {}).get(k) for k in ("rc", "oracles", "skip_proof")})
for vc in o.raw.get("vcs", []):
    print(f"  VC {vc['index']:2d} {vc['source'] or 'ABIERTA':>12} {(vc['closed_by'] or '')[:90]}")
print(o.raw.get("errors"))
