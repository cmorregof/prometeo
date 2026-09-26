"""Comprobación a posteriori: las corridas de V_I se hicieron antes de añadir la etapa 0 (lista blanca y
igualdad de programas en el kernel). Aquí se pasa esa etapa sobre cada propuesta registrada y se comprueba que
la etiqueta publicada no cambiaría: VCG_FAILED ⇔ la anotación no se analiza; el resto ⇔ el programa es el congelado.

    python tools/posthoc_stage0.py      → runs/_baseline/posthoc_stage0.json
"""
import glob
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parents[2]  # rl_metodos/
sys.path.insert(0, str(HERE))
from unirl.cli import load_attempts  # noqa: E402
from unirl.verifiers import IsabelleVerifier, check_annotation  # noqa: E402

v = IsabelleVerifier("bisection")
rows = []
for r in load_attempts(HERE / "runs" / "unirl"):
    if r["judge"] != "isabelle":
        continue
    p = r.get("proposal") or {}
    inv, var = p.get("invariant", ""), p.get("variant", "")
    allow = check_annotation(inv) or check_annotation(var)
    t = time.time()
    same, errs = ("skip", []) if allow else v.same_program(inv, var)
    expected = "parse" if r["outcome_label"] == "VCG_FAILED" else "ok"
    rows.append({"run": r["run"], "model": r["model"], "episode": r["episode"], "step": r["step"], "label": r["outcome_label"],
                 "allowlist": allow, "stage0": same, "consistent": (allow is None and same == expected), "seconds": round(time.time() - t, 1),
                 "errors": errs[:3]})
    print(rows[-1]["model"], r["episode"], r["step"], r["outcome_label"], "→", same, "OK" if rows[-1]["consistent"] else "¡DISTINTO!")
out = HERE / "runs" / "unirl" / "_baseline" / "posthoc_stage0.json"
out.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"{sum(x['consistent'] for x in rows)}/{len(rows)} coherentes → {out}")
