"""Paso (c): reproducir la fila «Bisection 15 VCs, 13 auto» de la Tabla 1 con los invariantes
originales del paper. Importa la teoría `Bisection` de la sesión del paper (con su `program`,
su invariante y su variante) y relanza vcg + try0 + Sledgehammer sobre la misma tripleta.

    python -m isarl.repro_bisection [--sh-timeout 60] [--no-prelude]
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from . import config
from .driver import isabelle_env, run_driver

# Tripleta EXACTA de bisection_error_bound (Bisection.thy, commit 0e7830d, líneas 167-173).
FIXES = 'f :: "real \\<Rightarrow> real" and a b tol :: real'
ASSUMES = '''postive_tolerance: "0 < tol"
    and sufficiently_small_tol: "tol < b-a"
    and continuous_f: "continuous_on {a..b} f"
    and opposite_signs: "f(a)*f(b)<0"'''
CONCL = ('H[True] bisection(f,a,b,tol) '
         '[\\<exists> c::real. f(c) = 0 \\<and> c \\<in> {a<..<b} \\<and> u-l \\<le> tol \\<and> \\<bar>c-xmid\\<bar> \\<le> (b-a)/2^iter '
         '\\<and> \\<bar>c-xmid\\<bar> \\<le> tol \\<and> iter = \\<lceil>log 2 ((b-a) / tol)\\<rceil>]')
# Los tres hechos que el paper establece antes de `proof (vcg)` (parte de su demostración manual).
PRELUDE = '''lemma a_less_than_b: "a < b" using postive_tolerance sufficiently_small_tol by auto
lemma ln2_g_0 [simp]: "\\<lceil>log 2 ((b - a) / tol)\\<rceil> > 0" using sufficiently_small_tol postive_tolerance by force
lemma log_pos [simp]: "0 < log 2 ((b - a) / tol)" using ln2_g_0 zero_less_ceiling by simp'''


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sh-timeout", type=int, default=60)
    ap.add_argument("--try0-timeout", type=int, default=5)
    ap.add_argument("--no-prelude", action="store_true", help="sin los tres hechos previos del paper")
    ap.add_argument("--only", type=str, default="", help="índices de VC separados por coma (p. ej. 4,8)")
    ap.add_argument("--out", type=Path, default=Path("runs") / "repro_bisection.json")
    args = ap.parse_args(argv)
    env = isabelle_env()
    print("provers externos:", {k: bool(v) for k, v in env.items()})
    t = time.time()
    r = run_driver(imports='"Numerical_Methods_Paper.Bisection"', program="", fixes=FIXES, assumes=ASSUMES,
                   concl=CONCL, prelude="" if args.no_prelude else PRELUDE,
                   sh_timeout=args.sh_timeout, try0_timeout=args.try0_timeout,
                   only=tuple(int(x) for x in args.only.split(',') if x.strip()))
    print(f"build rc={r.build_rc}  {r.elapsed_s:.0f} s  vcg {r.vcg_ms} ms  provers: {r.provers}")
    if r.error:
        print("ERROR:", r.error)
        print(r.raw_log[-3000:])
        return 1
    for v in r.vcs:
        print(f"VC {v.index:2d} [{v.method:>14}] {v.one_liner or 'ABIERTA':<60} :: {v.goal[:90]}")
    print(f"\nVCs: {r.n_vcs}   cerradas por automatización: {r.n_closed_auto}   (paper: 15 / 13)")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({"env": env, "result": r.to_dict(), "seconds": time.time() - t}, indent=1, ensure_ascii=False))
    print("guardado en", args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
