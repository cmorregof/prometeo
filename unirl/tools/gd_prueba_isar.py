"""Demostraciones Isar de referencia (cota superior) para los objetivos gd con n fijo, generadas desde los
certificados racionales exactos de corpus/curado/stepsize/gd_cert/<objetivo>.json (tools/gd_certificados.py).

La demostración es el dual del PEP escrito en Isabelle: una instancia de `interp` por cada multiplicador λᵢⱼ > 0,
un hecho 0 ≤ ‖wₖ‖² por cada cuadrado de la descomposición M = Σ dₖ wₖ wₖᵀ, y el cierre por aritmética lineal
después de expandir los productos internos (los átomos son f(·) y ⟨u, v⟩ entre x0, xs y los g(xₖ)). Como la
aritmética lineal encuentra sola los coeficientes, los λ y d solo deciden QUÉ hechos se citan.

Variantes (la validación prueba en orden y se queda con la primera que Isabelle acepta):
  A: expansión con `simp only` y cierre con linarith;
  B: expansión con el simpset completo más algebra_simps, que cierra solo (validación del 24 sep: el linarith
     posterior sobraba);
  C: expansión con `simp only` y cierre con argo (decisión de aritmética lineal con reconstrucción de prueba).
Validación del 24 sep 2026: C es ACCEPTED en gd_n1 y gd_const_n2 (≈ 5 s); A falla (linarith no cierra).

Uso: .venv/bin/python tools/gd_prueba_isar.py   (escribe corpus/curado/stepsize/gd_cert/<objetivo>.proof_{A,B,C}.txt)
"""

from __future__ import annotations

import json
import re
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parents[2]  # rl_metodos/
CERT = HERE / "corpus" / "curado" / "stepsize" / "gd_cert"
OBJETIVOS = ("gd_n1", "gd_const_n2")

EXPANSION = ("power2_norm_eq_inner inner_diff_left inner_diff_right inner_add_left inner_add_right inner_minus_left "
             "inner_minus_right inner_scaleR_left inner_scaleR_right inner_zero_left inner_zero_right opt inner_commute")


def num(q: Fraction) -> str:
    """Numeral de Isabelle para un racional: 2, (3/2), (- 3/2)."""
    if q.denominator == 1:
        return str(q.numerator) if q >= 0 else f"(- {-q.numerator})"
    return f"({q.numerator}/{q.denominator})" if q >= 0 else f"(- {-q.numerator}/{q.denominator})"


def combinacion(coefs: list[Fraction], base: list[str]) -> str:
    """Σ c·v como término de Isabelle, con *\\<^sub>R para los escalares y signos limpios."""
    partes = []
    for c, v in zip(coefs, base):
        if c == 0:
            continue
        mag = abs(c)
        t = v if mag == 1 else f"{num(mag)} *\\<^sub>R {v}"
        if not partes:
            partes.append(t if c > 0 else f"- {t}")
        else:
            partes.append(f"+ {t}" if c > 0 else f"- {t}")
    return " ".join(partes) if partes else "0"


def generar(obj: str, variante: str) -> str:
    c = json.loads((CERT / f"{obj}.json").read_text(encoding="utf-8"))
    h = [Fraction(x) for x in c["h"]]
    n = len(h)
    pts = [f"x{k}" for k in range(n + 1)] + ["xs"]
    base = ["(x0 - xs)"] + [f"g x{k}" for k in range(n + 1)]
    lista = re.search(r"gd g (\[[^\]]*\]) x0", c["concl"]).group(1)
    L = ["proof -"]
    L.append(f"  (* certificado exacto del PEP para h = {[str(x) for x in h]}, tau = {c['tau']} (corpus/curado/stepsize/gd_cert/{obj}.json) *)")
    for k in range(1, n + 1):
        L.append(f'  define x{k} where "x{k} = x{k-1} - {num(h[k-1])} *\\<^sub>R g x{k-1}"')
    defs = " ".join(f"x{k}_def" for k in range(n, 0, -1))
    L.append(f'  have run: "gd g {lista} x0 = x{n}"')
    L.append(f"    by (simp add: {defs})")
    hechos = []
    for e in c["lambda"]:
        i, j = e["i"], e["j"]
        xi, yj = pts[i], pts[j]
        nombre = f"i_{i}_{j}"
        L.append(f"  (* lambda = {e['lambda']}: interp con x = {xi}, y = {yj} *)")
        L.append(f'  have {nombre}: "f {yj} + inner (g {yj}) ({xi} - {yj}) + (1/2) * (norm (g {xi} - g {yj}))\\<^sup>2 \\<le> f {xi}"')
        L.append("    by (rule interp)")
        hechos.append(nombre)
    for k, sq in enumerate(c["cuadrados"]):
        w = [Fraction(x) for x in sq["w"]]
        nombre = f"s_{k}"
        L.append(f"  (* d = {sq['d']}: cuadrado de la descomposición exacta de M *)")
        L.append(f'  have {nombre}: "0 \\<le> (norm ({combinacion(w, base)}))\\<^sup>2"')
        L.append("    by simp")
        hechos.append(nombre)
    L.append("  show ?thesis")
    L.append("    unfolding run")
    L.append(f"    using {' '.join(hechos)} opt")
    L.append(f"    unfolding {defs}")
    if variante == "A":
        L.append(f"    by (simp (no_asm_use) only: {EXPANSION}) linarith")
    elif variante == "B":
        L.append(f"    by (simp (no_asm_use) add: {EXPANSION} algebra_simps)")
    elif variante == "C":
        L.append(f"    by (simp (no_asm_use) only: {EXPANSION}) argo")
    else:
        raise ValueError(variante)
    L.append("qed")
    return "\n".join(L) + "\n"


def main() -> None:
    for obj in OBJETIVOS:
        for v in "ABC":
            p = CERT / f"{obj}.proof_{v}.txt"
            p.write_text(generar(obj, v), encoding="utf-8")
            print("escrito", p.relative_to(HERE))


if __name__ == "__main__":
    main()
