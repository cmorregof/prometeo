"""Línea base: el juez Isabelle de 09 (código definitivo) sobre el target congelado, con el invariante y el
variante que escribieron los autores del paper. Escribe runs/_baseline/<target>.json.

    python tools/baseline_paper.py [--target bisection]
"""
import argparse
import json
import sys
import time
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from unirl.verifiers import IsabelleVerifier  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--target", default="bisection")
ap.add_argument("--sh-timeout", type=int, default=60)
a = ap.parse_args()
v = IsabelleVerifier(a.target, sh_timeout=a.sh_timeout)
t0 = time.time()
o = v.verify(v.target(), {"invariant": v.spec["paper_invariant"], "variant": v.spec["paper_variant"]})
out = Path(__file__).resolve().parent.parent / "runs" / "_baseline" / f"{a.target}.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({"target": a.target, "hash": v.frozen_hash, "sh_timeout": a.sh_timeout, "seconds": round(time.time() - t0, 1),
                           "outcome": asdict(o)}, ensure_ascii=False, indent=1), encoding="utf-8")
print(o.outcome_label, o.raw.get("n_closed_auto"), "/", o.raw.get("n_vcs"), "→", out)
for vc in o.raw.get("vcs", []):
    print(f"  VC {vc['index']:2d} {vc['source'] or 'ABIERTA':>12} {vc['prover'] or '':>10} {(vc['closed_by'] or '')[:70]}")
