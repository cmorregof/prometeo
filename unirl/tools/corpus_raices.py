"""Corpus de búsqueda de raíces (Etapa 1 de PLAN_rl_verbal.md): fuente única de los peldaños.

Cada peldaño es un teorema puro de Isabelle/HOL en el formato del juez de teorema (`unirl/gd_isabelle.py`):
imports, preludio (definiciones de la iteración), fixes, assumes, concl. Este archivo genera
`corpus/raices/<id>.json` y `corpus/raices/revision_enunciados.md`, y hace la comprobación numérica de cada
peldaño (casos aleatorios que cumplen las hipótesis; la conclusión debe cumplirse).

Todos los enunciados los redactó Claude: entran como `pendiente_revision` hasta que Carlos los apruebe.

Uso:
  .venv/bin/python tools/corpus_raices.py            # comprobación numérica + escribe JSON y revisión
  .venv/bin/python tools/corpus_raices.py --solo-num # solo la comprobación numérica
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[2]  # rl_metodos/
OUT = HERE / "corpus" / "curado" / "raices"
IMPORTS = '"HOL-Analysis.Analysis"'
HASH_FIELDS = ("imports", "prelude", "fixes", "assumes", "concl")  # los mismos que TheoremVerifier._hash

# ----------------------------------------------------------------------------------------------- preludios

PRELUDIO = {
    "biseccion": r'''primrec biseccion :: "(real \<Rightarrow> real) \<Rightarrow> real \<Rightarrow> real \<Rightarrow> nat \<Rightarrow> real \<times> real" where
  "biseccion f a b 0 = (a, b)"
| "biseccion f a b (Suc n) = (case biseccion f a b n of (l, u) \<Rightarrow>
     (if f l * f ((l + u) / 2) \<le> 0 then (l, (l + u) / 2) else ((l + u) / 2, u)))"

definition punto_medio :: "(real \<Rightarrow> real) \<Rightarrow> real \<Rightarrow> real \<Rightarrow> nat \<Rightarrow> real" where
  "punto_medio f a b n = (fst (biseccion f a b n) + snd (biseccion f a b n)) / 2"''',
    "punto_fijo": "",
    "newton": r'''definition paso_newton :: "(real \<Rightarrow> real) \<Rightarrow> (real \<Rightarrow> real) \<Rightarrow> real \<Rightarrow> real" where
  "paso_newton f f' x = x - f x / f' x"''',
    "ordenes": "",
    "secante": r'''definition paso_secante :: "(real \<Rightarrow> real) \<Rightarrow> real \<Rightarrow> real \<Rightarrow> real" where
  "paso_secante f x y = y - f y * (y - x) / (f y - f x)"

fun secante :: "(real \<Rightarrow> real) \<Rightarrow> real \<Rightarrow> real \<Rightarrow> nat \<Rightarrow> real" where
  "secante f x0 x1 0 = x0"
| "secante f x0 x1 (Suc 0) = x1"
| "secante f x0 x1 (Suc (Suc n)) = paso_secante f (secante f x0 x1 n) (secante f x0 x1 (Suc n))"

fun fibo :: "nat \<Rightarrow> nat" where
  "fibo 0 = 0"
| "fibo (Suc 0) = 1"
| "fibo (Suc (Suc n)) = fibo (Suc n) + fibo n"''',
    "regula_falsi": r'''definition punto_rf :: "(real \<Rightarrow> real) \<Rightarrow> real \<Rightarrow> real \<Rightarrow> real" where
  "punto_rf f l u = (l * f u - u * f l) / (f u - f l)"

primrec regula_falsi :: "(real \<Rightarrow> real) \<Rightarrow> real \<Rightarrow> real \<Rightarrow> nat \<Rightarrow> real \<times> real" where
  "regula_falsi f a b 0 = (a, b)"
| "regula_falsi f a b (Suc n) = (case regula_falsi f a b n of (l, u) \<Rightarrow>
     (if f l * f (punto_rf f l u) \<le> 0 then (l, punto_rf f l u) else (punto_rf f l u, u)))"''',
}

LECTURA_PRELUDIO = {
    "biseccion": "biseccion f a b n es el par (aₙ, bₙ) tras n pasos: se parte en el punto medio m y se conserva [aₙ, m] si "
                 "f(aₙ)·f(m) ≤ 0 (incluye f(m) = 0) y [m, bₙ] si no. punto_medio f a b n = (aₙ + bₙ)/2.",
    "punto_fijo": "Sin definiciones nuevas: la iteración es (g ^^ n) x0, la n-ésima composición de g aplicada a x0.",
    "newton": "paso_newton f f' x = x − f(x)/f'(x). La iteración es (paso_newton f f' ^^ n) x0. En HOL, x/0 = 0; las "
              "hipótesis garantizan que f' no se anula cerca de la raíz.",
    "ordenes": "Sin definiciones: e :: nat ⇒ real es una sucesión de errores cualquiera.",
    "secante": "paso_secante f x y = y − f(y)(y − x)/(f(y) − f(x)) (x es el iterado anterior, y el actual). secante f x0 x1 n "
               "es xₙ. fibo es la sucesión de Fibonacci (fibo 0 = 0, fibo 1 = 1). En HOL, x/0 = 0.",
    "regula_falsi": "punto_rf f l u = (l·f(u) − u·f(l))/(f(u) − f(l)), el cero de la secante entre (l, f(l)) y (u, f(u)). "
                    "regula_falsi f a b n es el par (lₙ, uₙ); se conserva [lₙ, c] si f(lₙ)·f(c) ≤ 0 y [c, uₙ] si no.",
}

# ----------------------------------------------------------------------------------------------- hipótesis comunes

BIS_FIX = 'f :: "real \\<Rightarrow> real" and a b :: real'
PF_FIX = 'g :: "real \\<Rightarrow> real" and a b k x0 :: real'
PF_ASM = ('ab: "a \\<le> b"\n    and dentro: "\\<And>x. x \\<in> {a..b} \\<Longrightarrow> g x \\<in> {a..b}"\n'
          '    and contr: "\\<And>x y. x \\<in> {a..b} \\<Longrightarrow> y \\<in> {a..b} \\<Longrightarrow> \\<bar>g x - g y\\<bar> \\<le> k * \\<bar>x - y\\<bar>"\n'
          '    and k0: "0 \\<le> k" and k1: "k < 1" and x0: "x0 \\<in> {a..b}"')
N_FIX = "f f' f'' :: \"real \\<Rightarrow> real\" and r \\<delta> m M :: real"
N_ASM = ('d1: "\\<And>t. \\<bar>t - r\\<bar> \\<le> \\<delta> \\<Longrightarrow> (f has_real_derivative f\' t) (at t)"\n'
         '    and d2: "\\<And>t. \\<bar>t - r\\<bar> \\<le> \\<delta> \\<Longrightarrow> (f\' has_real_derivative f\'\' t) (at t)"\n'
         '    and raiz: "f r = 0" and m_pos: "0 < m"\n'
         '    and cota1: "\\<And>t. \\<bar>t - r\\<bar> \\<le> \\<delta> \\<Longrightarrow> m \\<le> \\<bar>f\' t\\<bar>"\n'
         '    and cota2: "\\<And>t. \\<bar>t - r\\<bar> \\<le> \\<delta> \\<Longrightarrow> \\<bar>f\'\' t\\<bar> \\<le> M"\n'
         '    and delta_pos: "0 < \\<delta>" and delta_chico: "M * \\<delta> \\<le> m"')
RF_FIX = 'f :: "real \\<Rightarrow> real" and a b :: real'
RF_ASM = 'ab: "a < b" and fa: "f a < 0" and fb: "0 < f b" and cont: "continuous_on {a..b} f"'

LECTURA_HIP = {
    "biseccion": "f : ℝ → ℝ, a, b reales (cada peldaño añade lo que necesita: a ≤ b, continuidad en [a, b], f(a)·f(b) ≤ 0).",
    "punto_fijo": "g : [a, b] → [a, b] (dentro), k-contractiva en [a, b] con 0 ≤ k < 1 (contr), x0 ∈ [a, b].",
    "newton": "En I = [r − δ, r + δ]: f derivable con derivada f', f' derivable con derivada f'' (dos veces derivable, no se pide "
              "f'' continua); f(r) = 0; m ≤ |f'| con m > 0; |f''| ≤ M; δ > 0 y M·δ ≤ m (δ pequeño: da el factor 1/2 de "
              "contracción).",
    "ordenes": "e es una sucesión real cualquiera con una recurrencia de cota (lineal o cuadrática).",
    "secante": "Las mismas de Newton: en I = [r − δ, r + δ], f dos veces derivable, f(r) = 0, m ≤ |f'|, |f''| ≤ M, M·δ ≤ m.",
    "regula_falsi": "a < b, f(a) < 0 < f(b) (orientación fija, sin pérdida de generalidad), f continua en [a, b].",
}


def _h(*partes: str) -> str:
    return "\n    and ".join(p for p in partes if p)


# ----------------------------------------------------------------------------------------------- peldaños

P: list[dict] = []


def peldano(id_, metodo, n, split, dif, fixes, assumes, concl, es, fuente, deps=(), dudas="", ref=None, num=None):
    P.append({"id": id_, "metodo": metodo, "peldano": n, "split": split, "dificultad": dif, "fixes": fixes,
              "assumes": assumes, "concl": concl, "statement_es": es, "fuente": fuente, "dependencias": list(deps),
              "supuestos_dudosos": dudas, "referencia_privada": ref, "_num": num})


# --- bisección (train)
peldano("bis_1_ancho", "biseccion", 1, "train", 1, BIS_FIX + " and n :: nat", 'ab: "a \\<le> b"',
        "snd (biseccion f a b n) - fst (biseccion f a b n) = (b - a) / 2 ^ n",
        "Tras n pasos, el intervalo mide (b − a)/2ⁿ.", "01_biseccion (grafo), paso de longitudes")
peldano("bis_2_encaje", "biseccion", 2, "train", 2, BIS_FIX + " and n :: nat", 'ab: "a \\<le> b"',
        "a \\<le> fst (biseccion f a b n) \\<and> fst (biseccion f a b n) \\<le> snd (biseccion f a b n) \\<and> "
        "snd (biseccion f a b n) \\<le> b \\<and> fst (biseccion f a b n) \\<le> fst (biseccion f a b (Suc n)) \\<and> "
        "snd (biseccion f a b (Suc n)) \\<le> snd (biseccion f a b n)",
        "Los intervalos están contenidos en [a, b], son no vacíos y encajados: aₙ ≤ aₙ₊₁ y bₙ₊₁ ≤ bₙ.",
        "01_biseccion (grafo)", ["bis_1_ancho"])
peldano("bis_3_signo", "biseccion", 3, "train", 2, BIS_FIX + " and n :: nat", 'signo: "f a * f b \\<le> 0"',
        "f (fst (biseccion f a b n)) * f (snd (biseccion f a b n)) \\<le> 0",
        "Invariante de signo: si f(a)·f(b) ≤ 0, entonces f(aₙ)·f(bₙ) ≤ 0 para todo n.", "01_biseccion (grafo)")
peldano("bis_4_raiz", "biseccion", 4, "train", 3, BIS_FIX + " and n :: nat",
        _h('ab: "a \\<le> b"', 'cont: "continuous_on {a..b} f"', 'signo: "f a * f b \\<le> 0"'),
        "\\<exists>c. fst (biseccion f a b n) \\<le> c \\<and> c \\<le> snd (biseccion f a b n) \\<and> f c = 0",
        "Con f continua y f(a)·f(b) ≤ 0, cada intervalo [aₙ, bₙ] contiene una raíz (Bolzano).",
        "01_biseccion (grafo); artículo: Bolzanos_theorem", ["bis_2_encaje", "bis_3_signo"],
        ref="Verified_Numerical_Methods/Numerical_Methods/Bisection.thy: Bolzanos_theorem")
peldano("bis_5_cota", "biseccion", 5, "train", 3, BIS_FIX + " and n :: nat",
        _h('ab: "a \\<le> b"', 'cont: "continuous_on {a..b} f"', 'signo: "f a * f b \\<le> 0"'),
        "\\<exists>c. a \\<le> c \\<and> c \\<le> b \\<and> f c = 0 \\<and> \\<bar>punto_medio f a b n - c\\<bar> \\<le> (b - a) / 2 ^ Suc n",
        "Existe una raíz c en [a, b] con |mₙ − c| ≤ (b − a)/2ⁿ⁺¹ (la cota del teorema de 01).",
        "01_biseccion (teorema del grafo)", ["bis_1_ancho", "bis_4_raiz"],
        ref="Verified_Numerical_Methods/Numerical_Methods/Bisection.thy: bisect_root_extract (forma parecida)")
peldano("bis_6_iteraciones", "biseccion", 6, "train", 2, BIS_FIX + " and tol :: real and n :: nat",
        _h('ab: "a < b"', 'tol: "0 < tol"'),
        "log 2 ((b - a) / tol) \\<le> real n \\<Longrightarrow> snd (biseccion f a b n) - fst (biseccion f a b n) \\<le> tol",
        "Si n ≥ log₂((b − a)/tol), el intervalo mide a lo sumo tol.", "01_biseccion; artículo (iter = ⌈log₂((b − a)/tol)⌉)",
        ["bis_1_ancho"], dudas="Es la condición suficiente con n real ≥ log₂(…); el artículo usa el techo exacto.")
peldano("bis_7_convergencia", "biseccion", 7, "train", 4, BIS_FIX,
        _h('ab: "a \\<le> b"', 'cont: "continuous_on {a..b} f"', 'signo: "f a * f b \\<le> 0"'),
        "\\<exists>c. a \\<le> c \\<and> c \\<le> b \\<and> f c = 0 \\<and> (\\<lambda>k. punto_medio f a b k) \\<longlonglongrightarrow> c",
        "Los puntos medios convergen a una raíz c de f en [a, b].", "01_biseccion (teorema del grafo)",
        ["bis_1_ancho", "bis_2_encaje", "bis_3_signo"])

# --- punto fijo (train)
peldano("pf_1_derivada", "punto_fijo", 1, "train", 2,
        "g g' :: \"real \\<Rightarrow> real\" and a b k x y :: real",
        _h('ab: "a \\<le> b"', 'deriv: "\\<And>t. t \\<in> {a..b} \\<Longrightarrow> (g has_real_derivative g\' t) (at t)"',
           'cota: "\\<And>t. t \\<in> {a..b} \\<Longrightarrow> \\<bar>g\' t\\<bar> \\<le> k"', 'hx: "x \\<in> {a..b}"', 'hy: "y \\<in> {a..b}"'),
        "\\<bar>g x - g y\\<bar> \\<le> k * \\<bar>x - y\\<bar>",
        "Si |g'| ≤ k en [a, b], g es k-Lipschitz en [a, b] (valor medio).", "02_punto_fijo; artículo: contractive_deriv_bound_closed",
        ref="Verified_Numerical_Methods/Numerical_Methods/Fixed_Point_Method.thy: contractive_deriv_bound_closed")
peldano("pf_2_dentro", "punto_fijo", 2, "train", 1, PF_FIX + " and n :: nat", PF_ASM,
        "(g ^^ n) x0 \\<in> {a..b}", "Los iterados se quedan en [a, b].", "02_punto_fijo (grafo)",
        ref="Fixed_Point_Method.thy: fpm_iters_in_cball (versión en bola)")
peldano("pf_3_unicidad", "punto_fijo", 3, "train", 2, PF_FIX + " and p q :: real",
        _h(PF_ASM, 'hp: "p \\<in> {a..b}"', 'fp: "g p = p"', 'hq: "q \\<in> {a..b}"', 'fq: "g q = q"'),
        "p = q", "Hay a lo sumo un punto fijo en [a, b].", "02_punto_fijo (grafo)")
peldano("pf_4_decaimiento", "punto_fijo", 4, "train", 2, PF_FIX + " and p :: real and n :: nat",
        _h(PF_ASM, 'hp: "p \\<in> {a..b}"', 'fp: "g p = p"'),
        "\\<bar>(g ^^ n) x0 - p\\<bar> \\<le> k ^ n * \\<bar>x0 - p\\<bar>", "|xₙ − p| ≤ kⁿ|x0 − p|.",
        "02_punto_fijo; artículo: fpm_err_decay", ["pf_2_dentro"], ref="Fixed_Point_Method.thy: fpm_err_decay")
peldano("pf_5_a_priori", "punto_fijo", 5, "train", 2, PF_FIX + " and p :: real and n :: nat",
        _h(PF_ASM, 'hp: "p \\<in> {a..b}"', 'fp: "g p = p"'),
        "\\<bar>(g ^^ n) x0 - p\\<bar> \\<le> k ^ n * (b - a)", "Cota a priori: |xₙ − p| ≤ kⁿ(b − a).",
        "02_punto_fijo (cota a priori, con b − a en lugar de max(x0 − a, b − x0))", ["pf_4_decaimiento"],
        dudas="02 usa max(x0 − a, b − x0), que es más fina; aquí b − a.")
peldano("pf_6_a_priori_x1", "punto_fijo", 6, "train", 3, PF_FIX + " and p :: real and n :: nat",
        _h(PF_ASM, 'hp: "p \\<in> {a..b}"', 'fp: "g p = p"'),
        "\\<bar>(g ^^ n) x0 - p\\<bar> \\<le> k ^ n / (1 - k) * \\<bar>g x0 - x0\\<bar>",
        "Cota a priori en función del primer paso: |xₙ − p| ≤ kⁿ/(1 − k)·|x1 − x0|.",
        "02_punto_fijo (el grafo la llama «a posteriori»; en la terminología usual es a priori: solo usa x0 y x1)",
        ["pf_4_decaimiento"])
peldano("pf_6p_a_posteriori", "punto_fijo", "6p", "train", 3, PF_FIX + " and p :: real and n :: nat",
        _h(PF_ASM, 'hp: "p \\<in> {a..b}"', 'fp: "g p = p"'),
        "\\<bar>(g ^^ Suc n) x0 - p\\<bar> \\<le> k / (1 - k) * \\<bar>(g ^^ Suc n) x0 - (g ^^ n) x0\\<bar>",
        "Cota a posteriori (terminología usual): |xₙ − p| ≤ k/(1 − k)·|xₙ − xₙ₋₁| para n ≥ 1.",
        "terminología usual de la iteración de punto fijo; 02 no la incluye", ["pf_2_dentro"],
        dudas="Se escribe con Suc n para que valga desde n = 1 (xₙ₋₁ debe existir).")
peldano("pf_7_existencia", "punto_fijo", 7, "train", 3, PF_FIX, PF_ASM,
        "\\<exists>p \\<in> {a..b}. g p = p", "g tiene un punto fijo en [a, b].", "02_punto_fijo; biblioteca: banach_fix",
        dudas="La biblioteca tiene banach_fix (espacios métricos completos); puede que el martillo lo cierre.")
peldano("pf_8_convergencia", "punto_fijo", 8, "train", 4, PF_FIX, PF_ASM,
        "\\<exists>p \\<in> {a..b}. g p = p \\<and> (\\<lambda>n. (g ^^ n) x0) \\<longlonglongrightarrow> p",
        "La iteración converge al punto fijo.", "02_punto_fijo (teorema del grafo)", ["pf_7_existencia", "pf_4_decaimiento"])
peldano("pf_9_cuadratico", "punto_fijo", 9, "train", 3, "g g' :: \"real \\<Rightarrow> real\" and a b p L x :: real",
        _h('ab: "a \\<le> b"', 'hp: "p \\<in> {a..b}"', 'fp: "g p = p"',
           'deriv: "\\<And>t. t \\<in> {a..b} \\<Longrightarrow> (g has_real_derivative g\' t) (at t)"',
           'cota: "\\<And>t. t \\<in> {a..b} \\<Longrightarrow> \\<bar>g\' t\\<bar> \\<le> L * \\<bar>t - p\\<bar>"', 'hx: "x \\<in> {a..b}"'),
        "\\<bar>g x - p\\<bar> \\<le> L * (x - p)\\<^sup>2",
        "Si |g'(t)| ≤ L|t − p| (en particular g'(p) = 0), un paso es cuadrático: |g(x) − p| ≤ L(x − p)².",
        "02_punto_fijo; artículo: fpm_iter_quadratic_convergence (otra forma)",
        dudas="Constante L y no L/2: la versión con L/2 necesita integrar; con el valor medio sale L.",
        ref="Fixed_Point_Method.thy: fpm_iter_quadratic_convergence (forma distinta)")

# --- Newton (train)
N_HX = 'hx: "\\<bar>x - r\\<bar> \\<le> \\<delta>"'
N_HX0 = 'hx0: "\\<bar>x0 - r\\<bar> \\<le> \\<delta>"'
peldano("newton_1_paso", "newton", 1, "train", 4, N_FIX + " and x :: real", _h(N_ASM, N_HX),
        "\\<bar>paso_newton f f' x - r\\<bar> \\<le> M / (2 * m) * (x - r)\\<^sup>2",
        "Error de un paso: |N(x) − r| ≤ M/(2m)·(x − r)² (Taylor con resto de Lagrange).", "04_newton (grafo)",
        dudas="Se pide f dos veces derivable en I, no f ∈ C²: el enunciado es un poco más fuerte que el de 04.")
peldano("newton_2_contraccion", "newton", 2, "train", 2, N_FIX + " and x :: real", _h(N_ASM, N_HX),
        "\\<bar>paso_newton f f' x - r\\<bar> \\<le> \\<bar>x - r\\<bar> / 2",
        "Con M·δ ≤ m, un paso reduce el error al menos a la mitad (y el iterado se queda en I).", "04_newton", ["newton_1_paso"])
peldano("newton_3_decaimiento", "newton", 3, "train", 2, N_FIX + " and x0 :: real and n :: nat", _h(N_ASM, N_HX0),
        "\\<bar>(paso_newton f f' ^^ n) x0 - r\\<bar> \\<le> \\<delta> / 2 ^ n", "|xₙ − r| ≤ δ/2ⁿ.", "04_newton",
        ["newton_2_contraccion"])
peldano("newton_4_convergencia", "newton", 4, "train", 3, N_FIX + " and x0 :: real", _h(N_ASM, N_HX0),
        "(\\<lambda>n. (paso_newton f f' ^^ n) x0) \\<longlonglongrightarrow> r", "Newton converge a r desde todo x0 ∈ I.",
        "04_newton (teorema del grafo)", ["newton_3_decaimiento"])
peldano("newton_5_orden2", "newton", 5, "train", 3, N_FIX + " and x0 :: real and n :: nat", _h(N_ASM, N_HX0),
        "M / (2 * m) * \\<bar>(paso_newton f f' ^^ n) x0 - r\\<bar> \\<le> (M / (2 * m) * \\<bar>x0 - r\\<bar>) ^ (2 ^ n)",
        "Orden 2: con εₙ = M/(2m)|xₙ − r|, εₙ ≤ ε₀^(2ⁿ).", "04_newton (orden cuadrático)", ["newton_1_paso", "newton_3_decaimiento"])

# --- órdenes de convergencia (train)
peldano("orden_1_lineal", "ordenes", 1, "train", 1, 'e :: "nat \\<Rightarrow> real" and c :: real and n :: nat',
        _h('c0: "0 \\<le> c"', 'paso: "\\<And>j. \\<bar>e (Suc j)\\<bar> \\<le> c * \\<bar>e j\\<bar>"'),
        "\\<bar>e n\\<bar> \\<le> c ^ n * \\<bar>e 0\\<bar>", "Recurrencia lineal: |eₙ| ≤ cⁿ|e₀|.", "estándar")
peldano("orden_2_cuadratico_lineal", "ordenes", 2, "train", 2, 'e :: "nat \\<Rightarrow> real" and C :: real and n :: nat',
        _h('C0: "0 \\<le> C"', 'paso: "\\<And>j. \\<bar>e (Suc j)\\<bar> \\<le> C * (e j)\\<^sup>2"', 'inicio: "C * \\<bar>e 0\\<bar> \\<le> 1 / 2"'),
        "\\<bar>e n\\<bar> \\<le> \\<bar>e 0\\<bar> / 2 ^ n", "Si |eₙ₊₁| ≤ C eₙ² y C|e₀| ≤ 1/2, entonces |eₙ| ≤ |e₀|/2ⁿ.",
        "estándar", ["orden_1_lineal"])
peldano("orden_3_cuadratico", "ordenes", 3, "train", 2, 'e :: "nat \\<Rightarrow> real" and C :: real and n :: nat',
        _h('C0: "0 \\<le> C"', 'paso: "\\<And>j. \\<bar>e (Suc j)\\<bar> \\<le> C * (e j)\\<^sup>2"'),
        "C * \\<bar>e n\\<bar> \\<le> (C * \\<bar>e 0\\<bar>) ^ (2 ^ n)", "Si |eₙ₊₁| ≤ C eₙ², entonces C|eₙ| ≤ (C|e₀|)^(2ⁿ).", "estándar")

# --- secante (test)
S_XY = _h(N_ASM, N_HX, 'hy: "\\<bar>y - r\\<bar> \\<le> \\<delta>"', 'dist: "x \\<noteq> y"')
S_01 = _h(N_ASM, N_HX0, 'hx1: "\\<bar>x1 - r\\<bar> \\<le> \\<delta>"', 'dist: "x0 \\<noteq> x1"')
peldano("secante_1_inyectiva", "secante", 1, "test", 2, N_FIX + " and x y :: real", S_XY, "f x \\<noteq> f y",
        "En I, f es inyectiva (|f'| ≥ m > 0): el paso de la secante está bien definido.", "05_secante (grafo)")
peldano("secante_2_cociente", "secante", 2, "test", 2, N_FIX + " and x y :: real", S_XY,
        "m \\<le> \\<bar>(f y - f x) / (y - x)\\<bar>", "El cociente de diferencias en I está acotado por abajo por m.",
        "05_secante (grafo)", ["secante_1_inyectiva"])
peldano("secante_3_producto", "secante", 3, "test", 5, N_FIX + " and x y :: real", S_XY,
        "\\<bar>paso_secante f x y - r\\<bar> \\<le> M / (2 * m) * \\<bar>x - r\\<bar> * \\<bar>y - r\\<bar>",
        "Cota producto: |S(x, y) − r| ≤ M/(2m)·|x − r|·|y − r| (diferencias divididas).", "05_secante (teorema del grafo)",
        ["secante_2_cociente"])
peldano("secante_4_contraccion", "secante", 4, "test", 2, N_FIX + " and x y :: real", S_XY,
        "\\<bar>paso_secante f x y - r\\<bar> \\<le> \\<bar>y - r\\<bar> / 2",
        "Con M·δ ≤ m, un paso de la secante reduce el error del iterado actual al menos a la mitad.", "05_secante",
        ["secante_3_producto"])
peldano("secante_5_convergencia", "secante", 5, "test", 4, N_FIX + " and x0 x1 :: real", S_01,
        "(\\<lambda>n. secante f x0 x1 n) \\<longlonglongrightarrow> r", "La secante converge a r desde x0 ≠ x1 en I.",
        "05_secante (teorema del grafo)", ["secante_4_contraccion"],
        dudas="Si un iterado cae en r, los siguientes quedan en r (en HOL, 0/0 = 0); el enunciado lo cubre.")
peldano("secante_6_fibonacci", "secante", 6, "test", 4, N_FIX + " and x0 x1 :: real and n :: nat", S_01,
        "M / (2 * m) * \\<bar>secante f x0 x1 n - r\\<bar> \\<le> (1 / 2) ^ fibo (Suc n)",
        "Orden φ en forma explícita: M/(2m)|xₙ − r| ≤ (1/2)^F(n+1), con F de Fibonacci (F(n) ~ φⁿ/√5).",
        "05_secante (orden φ)", ["secante_3_producto"],
        dudas="Codifica el orden φ con exponentes de Fibonacci en lugar de un límite de cocientes. Fibonacci del preludio: "
              "fibo 0 = 0, fibo 1 = 1, fibo (n + 2) = fibo (n + 1) + fibo n; la cota de xₙ usa fibo (n + 1): 1, 1, 2, 3, 5, 8, … "
              "para n = 0, 1, 2, 3, 4, 5, …")

# --- regula falsi (test)
RF_N = RF_FIX + " and n :: nat"
peldano("rf_1_punto", "regula_falsi", 1, "test", 2, 'f :: "real \\<Rightarrow> real" and l u :: real',
        _h('lu: "l < u"', 'fl: "f l < 0"', 'fu: "0 \\<le> f u"'),
        "l < punto_rf f l u \\<and> punto_rf f l u \\<le> u",
        "Si l < u y f(l) < 0 ≤ f(u), el punto de falsa posición cae en (l, u].", "estándar (regula falsi)")
peldano("rf_2_signo", "regula_falsi", 2, "test", 2, RF_N, _h('fa: "f a < 0"', 'fb: "0 < f b"'),
        "f (fst (regula_falsi f a b n)) < 0 \\<and> 0 \\<le> f (snd (regula_falsi f a b n))",
        "Invariante de signo: f(lₙ) < 0 ≤ f(uₙ).", "estándar (regula falsi)")
peldano("rf_3_encaje", "regula_falsi", 3, "test", 3, RF_N, _h('ab: "a < b"', 'fa: "f a < 0"', 'fb: "0 < f b"'),
        "a \\<le> fst (regula_falsi f a b n) \\<and> fst (regula_falsi f a b n) < snd (regula_falsi f a b n) \\<and> "
        "snd (regula_falsi f a b n) \\<le> b \\<and> fst (regula_falsi f a b n) \\<le> fst (regula_falsi f a b (Suc n)) \\<and> "
        "snd (regula_falsi f a b (Suc n)) \\<le> snd (regula_falsi f a b n)",
        "Horquillas encajadas no degeneradas: a ≤ lₙ < uₙ ≤ b, lₙ ≤ lₙ₊₁, uₙ₊₁ ≤ uₙ.", "estándar (regula falsi)",
        ["rf_1_punto", "rf_2_signo"])
peldano("rf_4_raiz", "regula_falsi", 4, "test", 3, RF_N, RF_ASM,
        "\\<exists>c. fst (regula_falsi f a b n) \\<le> c \\<and> c \\<le> snd (regula_falsi f a b n) \\<and> f c = 0",
        "Cada horquilla [lₙ, uₙ] contiene una raíz.", "estándar (regula falsi)", ["rf_2_signo", "rf_3_encaje"])
peldano("rf_5_limites", "regula_falsi", 5, "test", 3, RF_FIX, RF_ASM,
        "convergent (\\<lambda>n. fst (regula_falsi f a b n)) \\<and> convergent (\\<lambda>n. snd (regula_falsi f a b n))",
        "Los dos extremos convergen (sucesiones monótonas acotadas).", "estándar (regula falsi)", ["rf_3_encaje"])
peldano("rf_6_convergencia", "regula_falsi", 6, "test", 5, RF_FIX, RF_ASM,
        "\\<exists>c. a \\<le> c \\<and> c \\<le> b \\<and> f c = 0 \\<and> ((\\<lambda>n. fst (regula_falsi f a b n)) \\<longlonglongrightarrow> c \\<or> "
        "(\\<lambda>n. snd (regula_falsi f a b n)) \\<longlonglongrightarrow> c)",
        "Al menos un extremo converge a una raíz (el otro puede quedarse fijo).", "estándar (regula falsi)",
        ["rf_2_signo", "rf_3_encaje", "rf_5_limites"],
        dudas="No se afirma que los dos extremos converjan a la raíz: en general uno se queda quieto.")

# --- versiones clásicas más fuertes de los peldaños debilitados (pedido de Carlos, 24 sep 2026)
NC_FIX = "f f' f'' :: \"real \\<Rightarrow> real\" and r \\<epsilon> :: real"
NC_ASM = ('eps: "0 < \\<epsilon>"\n'
          '    and d1: "\\<And>t. \\<bar>t - r\\<bar> < \\<epsilon> \\<Longrightarrow> (f has_real_derivative f\' t) (at t)"\n'
          '    and d2: "\\<And>t. \\<bar>t - r\\<bar> < \\<epsilon> \\<Longrightarrow> (f\' has_real_derivative f\'\' t) (at t)"\n'
          '    and c2: "continuous_on {r - \\<epsilon><..<r + \\<epsilon>} f\'\'"\n'
          '    and raiz: "f r = 0" and simple: "f\' r \\<noteq> 0"')
LECTURA_NC = ("Hipótesis clásicas locales: f de clase C² cerca de r (f' y f'' existen en (r − ε, r + ε) y f'' es continua), "
              "f(r) = 0 y f'(r) ≠ 0 (raíz simple). No se dan δ, m ni M: el peldaño debe encontrarlos.")
peldano("bis_5c_cota_uniforme", "biseccion", "5c", "train", 3, BIS_FIX,
        _h('ab: "a \\<le> b"', 'cont: "continuous_on {a..b} f"', 'signo: "f a * f b \\<le> 0"'),
        "\\<exists>c. a \\<le> c \\<and> c \\<le> b \\<and> f c = 0 \\<and> (\\<forall>n. \\<bar>punto_medio f a b n - c\\<bar> \\<le> (b - a) / 2 ^ Suc n)",
        "Existe una raíz c en [a, b] tal que, para todo n, |mₙ − c| ≤ (b − a)/2ⁿ⁺¹ (la misma c para todo n).",
        "01_biseccion (teorema del grafo, forma clásica)", ["bis_5_cota", "bis_7_convergencia"])
peldano("pf_5c_a_priori_max", "punto_fijo", "5c", "train", 2, PF_FIX + " and p :: real and n :: nat",
        _h(PF_ASM, 'hp: "p \\<in> {a..b}"', 'fp: "g p = p"'),
        "\\<bar>(g ^^ n) x0 - p\\<bar> \\<le> k ^ n * max (x0 - a) (b - x0)",
        "Cota a priori clásica: |xₙ − p| ≤ kⁿ·max(x0 − a, b − x0).", "02_punto_fijo (cota a priori del grafo)", ["pf_4_decaimiento"])
peldano("pf_9c_cuadratico_medio", "punto_fijo", "9c", "train", 3, "g g' :: \"real \\<Rightarrow> real\" and a b p L x :: real",
        _h('ab: "a \\<le> b"', 'hp: "p \\<in> {a..b}"', 'fp: "g p = p"',
           'deriv: "\\<And>t. t \\<in> {a..b} \\<Longrightarrow> (g has_real_derivative g\' t) (at t)"',
           'cota: "\\<And>t. t \\<in> {a..b} \\<Longrightarrow> \\<bar>g\' t\\<bar> \\<le> L * \\<bar>t - p\\<bar>"', 'hx: "x \\<in> {a..b}"'),
        "\\<bar>g x - p\\<bar> \\<le> L / 2 * (x - p)\\<^sup>2",
        "Con la constante clásica: |g(x) − p| ≤ (L/2)(x − p)².", "02_punto_fijo; análogo de Taylor con |g''| ≤ L",
        ["pf_9_cuadratico"], dudas="Sale por monotonía de g(t) − p ∓ (L/2)(t − p)² (o integrando); el valor medio solo da L.")
peldano("newton_2c_contraccion_local", "newton", "2c", "train", 4, NC_FIX, NC_ASM,
        "\\<exists>\\<delta>>0. \\<forall>x. \\<bar>x - r\\<bar> \\<le> \\<delta> \\<longrightarrow> \\<bar>paso_newton f f' x - r\\<bar> \\<le> \\<bar>x - r\\<bar> / 2",
        "Forma clásica local: existe δ > 0 tal que un paso de Newton reduce el error al menos a la mitad en [r − δ, r + δ].",
        "04_newton (forma clásica)", ["newton_2_contraccion"])
peldano("newton_4c_convergencia_local", "newton", "4c", "train", 4, NC_FIX, NC_ASM,
        "\\<exists>\\<delta>>0. \\<forall>x0. \\<bar>x0 - r\\<bar> \\<le> \\<delta> \\<longrightarrow> (\\<lambda>n. (paso_newton f f' ^^ n) x0) \\<longlonglongrightarrow> r",
        "Teorema clásico de convergencia local de Newton: existe δ > 0 tal que Newton converge a r desde todo x0 ∈ [r − δ, r + δ].",
        "04_newton (teorema del grafo, forma clásica)", ["newton_4_convergencia", "newton_2c_contraccion_local"])
peldano("newton_5c_orden2_local", "newton", "5c", "train", 4, NC_FIX, NC_ASM,
        "\\<exists>\\<delta>>0. \\<exists>C. \\<forall>x0 n. \\<bar>x0 - r\\<bar> \\<le> \\<delta> \\<longrightarrow> "
        "\\<bar>(paso_newton f f' ^^ Suc n) x0 - r\\<bar> \\<le> C * ((paso_newton f f' ^^ n) x0 - r)\\<^sup>2",
        "Orden 2 clásico: existen δ > 0 y C con |xₙ₊₁ − r| ≤ C(xₙ − r)² para todo x0 ∈ [r − δ, r + δ] y todo n.",
        "04_newton (orden cuadrático, forma clásica)", ["newton_5_orden2", "newton_4c_convergencia_local"])
peldano("newton_6c_q_orden2", "newton", "6c", "train", 5, NC_FIX, NC_ASM,
        "\\<exists>\\<delta>>0. \\<forall>x0. \\<bar>x0 - r\\<bar> \\<le> \\<delta> \\<longrightarrow> (\\<forall>n. (paso_newton f f' ^^ n) x0 \\<noteq> r) \\<longrightarrow> "
        "(\\<lambda>n. \\<bar>(paso_newton f f' ^^ Suc n) x0 - r\\<bar> / ((paso_newton f f' ^^ n) x0 - r)\\<^sup>2) \\<longlonglongrightarrow> \\<bar>f'' r / (2 * f' r)\\<bar>",
        "Q-orden 2 clásico: si ningún iterado cae en r, |eₙ₊₁|/eₙ² → |f''(r)/(2f'(r))| (análogo de secante_6c; si f''(r) = 0 el límite es 0).",
        "04_newton (orden cuadrático, forma clásica del límite)", ["newton_5c_orden2_local", "newton_4c_convergencia_local"],
        dudas="Peldaño de dificultad 5 para train, propuesto a pedido de Carlos; sin f''(r) ≠ 0 el enunciado sigue siendo cierto con límite 0.")
peldano("secante_4c_contraccion_local", "secante", "4c", "test", 4, NC_FIX, NC_ASM,
        "\\<exists>\\<delta>>0. \\<forall>x y. \\<bar>x - r\\<bar> \\<le> \\<delta> \\<longrightarrow> \\<bar>y - r\\<bar> \\<le> \\<delta> \\<longrightarrow> x \\<noteq> y \\<longrightarrow> "
        "\\<bar>paso_secante f x y - r\\<bar> \\<le> \\<bar>y - r\\<bar> / 2",
        "Forma clásica local: existe δ > 0 tal que un paso de la secante con x ≠ y en [r − δ, r + δ] reduce a la mitad el error del iterado actual.",
        "05_secante (forma clásica)", ["secante_4_contraccion"])
peldano("secante_5c_convergencia_local", "secante", "5c", "test", 5, NC_FIX, NC_ASM,
        "\\<exists>\\<delta>>0. \\<forall>x0 x1. \\<bar>x0 - r\\<bar> \\<le> \\<delta> \\<longrightarrow> \\<bar>x1 - r\\<bar> \\<le> \\<delta> \\<longrightarrow> x0 \\<noteq> x1 \\<longrightarrow> "
        "(\\<lambda>n. secante f x0 x1 n) \\<longlonglongrightarrow> r",
        "Teorema clásico de convergencia local de la secante: existe δ > 0 tal que converge desde todo x0 ≠ x1 en [r − δ, r + δ].",
        "05_secante (teorema del grafo, forma clásica)", ["secante_5_convergencia", "secante_4c_contraccion_local"])
peldano("secante_6c_orden_phi", "secante", "6c", "test", 5, NC_FIX, _h(NC_ASM, 'curva: "f\'\' r \\<noteq> 0"'),
        "\\<exists>\\<delta>>0. \\<forall>x0 x1. \\<bar>x0 - r\\<bar> \\<le> \\<delta> \\<longrightarrow> \\<bar>x1 - r\\<bar> \\<le> \\<delta> \\<longrightarrow> x0 \\<noteq> x1 \\<longrightarrow> "
        "(\\<forall>n. secante f x0 x1 n \\<noteq> r) \\<longrightarrow> (\\<lambda>n. \\<bar>secante f x0 x1 (Suc n) - r\\<bar> / "
        "\\<bar>secante f x0 x1 n - r\\<bar> powr ((1 + sqrt 5) / 2)) \\<longlonglongrightarrow> \\<bar>f'' r / (2 * f' r)\\<bar> powr ((1 + sqrt 5) / 2 - 1)",
        "Orden φ clásico (Q-orden): si f''(r) ≠ 0 y ningún iterado cae en r, |eₙ₊₁|/|eₙ|^φ → |f''(r)/(2f'(r))|^(φ−1), con φ = (1 + √5)/2.",
        "05_secante (orden φ, forma clásica)", ["secante_6_fibonacci", "secante_5c_convergencia_local"],
        dudas="Es el resultado clásico sobre el límite del cociente; exige f''(r) ≠ 0 (si no, el orden es mayor) y que ningún iterado sea exactamente r.")
peldano("rf_6c_puntos_convergen", "regula_falsi", "6c", "test", 5, RF_FIX,
        _h(RF_ASM, 'unica: "\\<And>c d. c \\<in> {a..b} \\<Longrightarrow> d \\<in> {a..b} \\<Longrightarrow> f c = 0 \\<Longrightarrow> f d = 0 \\<Longrightarrow> c = d"'),
        "\\<exists>c. a \\<le> c \\<and> c \\<le> b \\<and> f c = 0 \\<and> (\\<lambda>n. case regula_falsi f a b n of (l, u) \\<Rightarrow> punto_rf f l u) \\<longlonglongrightarrow> c",
        "Forma clásica: si la raíz en [a, b] es única, los puntos de falsa posición cₙ convergen a ella.",
        "estándar (regula falsi, forma clásica)", ["rf_6_convergencia"])

# qué es clásico y qué está debilitado (y por qué)
CLASIFICACION = {
    "bis_5_cota": ("debilitada", "la raíz c puede depender de n; en la forma clásica es la misma c (el límite) para todo n", "bis_5c_cota_uniforme"),
    "pf_5_a_priori": ("debilitada", "usa b − a en lugar de max(x0 − a, b − x0), que es más fina", "pf_5c_a_priori_max"),
    "pf_9_cuadratico": ("debilitada", "constante L en lugar de L/2: con el valor medio sale L; L/2 necesita un argumento de monotonía o integrar", "pf_9c_cuadratico_medio"),
    "newton_2_contraccion": ("debilitada", "δ fijo por M·δ ≤ m y cotas m, M dadas como hipótesis, en lugar de ∃δ a partir de f ∈ C² y f'(r) ≠ 0", "newton_2c_contraccion_local"),
    "newton_3_decaimiento": ("debilitada", "δ fijo (M·δ ≤ m); no tiene un enunciado clásico propio: su contenido clásico está en la convergencia local", "newton_4c_convergencia_local"),
    "newton_4_convergencia": ("debilitada", "δ fijo por M·δ ≤ m y cotas dadas, en lugar de ∃δ a partir de f ∈ C² y f'(r) ≠ 0", "newton_4c_convergencia_local"),
    "newton_5_orden2": ("debilitada", "δ fijo; forma explícita εₙ ≤ ε₀^(2ⁿ) en lugar de ∃δ ∃C con |eₙ₊₁| ≤ C eₙ²", "newton_5c_orden2_local"),
    "secante_4_contraccion": ("debilitada", "δ fijo (M·δ ≤ m) y cotas dadas, en lugar de ∃δ", "secante_4c_contraccion_local"),
    "secante_5_convergencia": ("debilitada", "δ fijo (M·δ ≤ m) y cotas dadas, en lugar de ∃δ", "secante_5c_convergencia_local"),
    "secante_6_fibonacci": ("debilitada", "δ fijo, y el orden φ como cota con exponentes de Fibonacci (R-orden) en lugar del límite del cociente |eₙ₊₁|/|eₙ|^φ (Q-orden)", "secante_6c_orden_phi"),
    "rf_6_convergencia": ("debilitada", "solo afirma que un extremo converge a una raíz; la forma clásica, con raíz única, afirma que los puntos cₙ convergen a ella", "rf_6c_puntos_convergen"),
}
NOTA_CLASICA = {
    "bis_1_ancho": "arrastra hipótesis que no usa: a ≤ b",
    "bis_6_iteraciones": "es la forma de libro: basta n ≥ log₂((b − a)/tol) (equivale a n ≥ ⌈log₂((b − a)/tol)⌉ porque n es natural)",
    "pf_2_dentro": "arrastra hipótesis que no usa: la contracción (contr) y 0 ≤ k < 1",
    "pf_3_unicidad": "arrastra hipótesis que no usa: x0 y la invariancia de [a, b] (dentro)",
    "pf_7_existencia": "arrastra hipótesis que no usa: x0",
    "newton_1_paso": "arrastra hipótesis que no usa: M·δ ≤ m",
    "secante_1_inyectiva": "arrastra hipótesis que no usa: f'' y su cota, M·δ ≤ m",
    "secante_2_cociente": "arrastra hipótesis que no usa: f'' y su cota, M·δ ≤ m",
    "secante_3_producto": "arrastra hipótesis que no usa: M·δ ≤ m",
    "rf_5_limites": "arrastra hipótesis que no usa: la continuidad de f",
}
FUERTES = {v[2] for v in CLASIFICACION.values()}
for _p in P:
    if _p["id"] in CLASIFICACION:
        _p["version"], _p["debilitacion"], _p["version_clasica"] = CLASIFICACION[_p["id"]]
    else:
        _p["version"], _p["debilitacion"], _p["version_clasica"] = "clasica", NOTA_CLASICA.get(_p["id"], ""), None
    _p["debil_de"] = sorted(k for k, v in CLASIFICACION.items() if v[2] == _p["id"]) if _p["id"] in FUERTES else []
# orden final: cada versión clásica nueva justo después del (último) peldaño débil del que es versión clásica
_nuevas = {q["id"]: q for q in P if q["id"] in FUERTES}
_orden = []
for _p in [q for q in P if q["id"] not in FUERTES]:
    _orden.append(_p)
    for fid, f in _nuevas.items():
        if f not in _orden and _p["id"] == max(f["debil_de"], key=lambda d: [q["id"] for q in P].index(d)):
            _orden.append(f)
assert len(_orden) == len(P), "orden incompleto"
P[:] = _orden

# ----------------------------------------------------------------------------------------------- comprobación numérica

R = random.Random(20260924)


def bis_py(f, a, b, n):
    l, u = a, b
    for _ in range(n):
        m = (l + u) / 2
        if f(l) * f(m) <= 0:
            u = m
        else:
            l = m
    return l, u


def rf_py(f, a, b, n):
    l, u = a, b
    for _ in range(n):
        c = (l * f(u) - u * f(l)) / (f(u) - f(l)) if f(u) != f(l) else 0.0
        if f(l) * f(c) <= 0:
            u = c
        else:
            l = c
    return l, u


def raiz_biseccion(f, l, u, it=200):
    for _ in range(it):
        m = (l + u) / 2
        if f(l) * f(m) <= 0:
            u = m
        else:
            l = m
    return (l + u) / 2


def f_cambio_signo():
    """Polinomio cúbico aleatorio y un intervalo con cambio de signo."""
    while True:
        c = [R.uniform(-3, 3) for _ in range(4)]
        f = lambda x, c=c: c[0] + c[1] * x + c[2] * x * x + c[3] * x ** 3
        a = R.uniform(-3, 1); b = a + R.uniform(0.2, 4)
        if f(a) * f(b) < 0:
            return f, a, b


def f_newton():
    """f(x) = β(x − r) + γ(x − r)² + ε(x − r)³ con derivadas exactas, y δ que cumple las hipótesis."""
    r = R.uniform(-2, 2); beta = R.choice([-1, 1]) * R.uniform(0.5, 3); gam = R.uniform(-2, 2); eps = R.uniform(-1, 1)
    f = lambda x: beta * (x - r) + gam * (x - r) ** 2 + eps * (x - r) ** 3
    d1 = lambda x: beta + 2 * gam * (x - r) + 3 * eps * (x - r) ** 2
    d2 = lambda x: 2 * gam + 6 * eps * (x - r)
    delta = R.uniform(0.05, 0.6)
    for _ in range(60):
        xs = [r - delta + 2 * delta * i / 400 for i in range(401)]
        m = min(abs(d1(x)) for x in xs); M = max(abs(d2(x)) for x in xs)
        if m > 0 and M * delta <= m:
            return f, d1, d2, r, delta, m * (1 - 1e-12), M * (1 + 1e-12)
        delta /= 1.5
    return None


def num_checks(casos: int = 400) -> dict:
    res, tol = {}, 1e-9

    def ok(pid, cond):
        res.setdefault(pid, [0, 0])
        res[pid][0] += 1
        res[pid][1] += int(bool(cond))

    for _ in range(casos):
        f, a, b = f_cambio_signo(); n = R.randint(0, 25)
        l, u = bis_py(f, a, b, n); l1, u1 = bis_py(f, a, b, n + 1)
        ok("bis_1_ancho", abs((u - l) - (b - a) / 2 ** n) <= tol * (1 + b - a))
        ok("bis_2_encaje", a <= l <= u <= b and l <= l1 and u1 <= u)
        ok("bis_3_signo", f(l) * f(u) <= tol)
        c = raiz_biseccion(f, l, u); ok("bis_4_raiz", l - tol <= c <= u + tol and abs(f(c)) < 1e-6)
        ok("bis_5_cota", abs((l + u) / 2 - c) <= (b - a) / 2 ** (n + 1) + tol)
        t = R.uniform(1e-6, 1); nn = math.ceil(math.log2((b - a) / t)) if (b - a) / t > 1 else 0
        lt, ut = bis_py(f, a, b, max(nn, 0)); ok("bis_6_iteraciones", (ut - lt) <= t + tol)
        mids = [sum(bis_py(f, a, b, k)) / 2 for k in (40, 60)]; ok("bis_7_convergencia", abs(mids[0] - mids[1]) < 1e-9 and abs(f(mids[1])) < 1e-6)
        # punto fijo: g(x) = α + k sin(w x)/w, contractiva con constante k, en [α − R, α + R] con k/w ≤ R
        k = R.uniform(0, 0.95); w = R.uniform(0.3, 3); al = R.uniform(-2, 2); Rr = k / w + R.uniform(0, 1)
        g = lambda x: al + k * math.sin(w * x) / w
        A, B = al - Rr, al + Rr; x0 = R.uniform(A, B); p = x0
        for _i in range(3000):
            p = g(p)
        n = R.randint(0, 30); xn = x0
        for _i in range(n):
            xn = g(xn)
        ok("pf_1_derivada", abs(g(A) - g(B)) <= k * abs(A - B) + tol)
        ok("pf_2_dentro", A - tol <= xn <= B + tol)
        ok("pf_3_unicidad", abs(g(p) - p) < 1e-9)
        ok("pf_4_decaimiento", abs(xn - p) <= k ** n * abs(x0 - p) + 1e-9)
        ok("pf_5_a_priori", abs(xn - p) <= k ** n * (B - A) + 1e-9)
        ok("pf_6_a_priori_x1", abs(xn - p) <= k ** n / (1 - k) * abs(g(x0) - x0) + 1e-9)
        xn1 = g(xn)
        ok("pf_6p_a_posteriori", abs(xn1 - p) <= k / (1 - k) * abs(xn1 - xn) + 1e-9)
        ok("pf_7_existencia", A <= p <= B and abs(g(p) - p) < 1e-9)
        ok("pf_8_convergencia", abs(xn - p) <= k ** n * (B - A) + 1e-9)
        # cuadrático: g(x) = p + c(x − p)² + d(x − p)³; |g'(t)| ≤ L|t − p| con L = 2|c| + 3|d|·rad
        pp = R.uniform(-1, 1); cc = R.uniform(-2, 2); dd = R.uniform(-2, 2); rad = R.uniform(0.1, 1)
        gq = lambda x: pp + cc * (x - pp) ** 2 + dd * (x - pp) ** 3
        L = 2 * abs(cc) + 3 * abs(dd) * rad; xq = R.uniform(pp - rad, pp + rad)
        ok("pf_9_cuadratico", abs(gq(xq) - pp) <= L * (xq - pp) ** 2 + 1e-12)
        # Newton y secante
        z = f_newton()
        if z:
            f, d1, d2, r, dl, m, M = z
            N = lambda x: x - f(x) / d1(x)
            x = R.uniform(r - dl, r + dl)
            ok("newton_1_paso", abs(N(x) - r) <= M / (2 * m) * (x - r) ** 2 + 1e-12)
            ok("newton_2_contraccion", abs(N(x) - r) <= abs(x - r) / 2 + 1e-12)
            n = R.randint(0, 6); xn = x
            for _i in range(n):
                xn = N(xn)
            ok("newton_3_decaimiento", abs(xn - r) <= dl / 2 ** n + 1e-12)
            xl = x
            for _i in range(8):
                xl = N(xl)
            ok("newton_4_convergencia", abs(xl - r) < 1e-9)
            ok("newton_5_orden2", M / (2 * m) * abs(xn - r) <= (M / (2 * m) * abs(x - r)) ** (2 ** n) + 1e-12)
            S = lambda x, y: y - f(y) * (y - x) / (f(y) - f(x)) if f(y) != f(x) else y
            y = R.uniform(r - dl, r + dl)
            if x != y:
                ok("secante_1_inyectiva", f(x) != f(y))
                ok("secante_2_cociente", m <= abs((f(y) - f(x)) / (y - x)) + 1e-12)
                ok("secante_3_producto", abs(S(x, y) - r) <= M / (2 * m) * abs(x - r) * abs(y - r) + 1e-12)
                ok("secante_4_contraccion", abs(S(x, y) - r) <= abs(y - r) / 2 + 1e-12)
                seq = [x, y]
                for _i in range(12):
                    seq.append(S(seq[-2], seq[-1]) if seq[-1] != seq[-2] else seq[-1])
                ok("secante_5_convergencia", abs(seq[-1] - r) < 1e-9)
                fib = [0, 1]
                for _i in range(20):
                    fib.append(fib[-1] + fib[-2])
                ok("secante_6_fibonacci", all(M / (2 * m) * abs(seq[i] - r) <= 0.5 ** fib[i + 1] + 1e-12 for i in range(len(seq))))
        # órdenes
        c = R.uniform(0, 1.5); e = [R.uniform(-2, 2)]
        for _i in range(20):
            e.append(R.uniform(-1, 1) * c * abs(e[-1]))
        n = R.randint(0, 20); ok("orden_1_lineal", abs(e[n]) <= c ** n * abs(e[0]) + 1e-12)
        C = R.uniform(0, 3); e = [R.uniform(-1, 1) / (2 * C) if C > 0 else R.uniform(-1, 1)]
        for _i in range(12):
            e.append(R.uniform(-1, 1) * C * e[-1] ** 2)
        n = R.randint(0, 12)
        ok("orden_2_cuadratico_lineal", abs(e[n]) <= abs(e[0]) / 2 ** n + 1e-12)
        ok("orden_3_cuadratico", C * abs(e[n]) <= (C * abs(e[0])) ** (2 ** n) + 1e-12)
        # regula falsi (orientación f(a) < 0 < f(b))
        f, a, b = f_cambio_signo()
        if f(a) > 0:
            f = (lambda h: (lambda x: -h(x)))(f)
        n = R.randint(0, 30); l, u = rf_py(f, a, b, n); l1, u1 = rf_py(f, a, b, n + 1)
        lo, hi = sorted([R.uniform(-3, 3), R.uniform(-3, 3)])
        if lo < hi and f(lo) < 0 <= f(hi):
            cp = (lo * f(hi) - hi * f(lo)) / (f(hi) - f(lo)); ok("rf_1_punto", lo < cp <= hi + tol)
        ok("rf_2_signo", f(l) < 0 <= f(u) + tol)
        ok("rf_3_encaje", a <= l < u <= b and l <= l1 and u1 <= u)
        c = raiz_biseccion(f, l, u); ok("rf_4_raiz", l - tol <= c <= u + tol and abs(f(c)) < 1e-6)
        L2, U2 = rf_py(f, a, b, 10000), rf_py(f, a, b, 20000)  # convergencia lenta con un extremo fijo
        ok("rf_5_limites", abs(L2[0] - U2[0]) < 1e-7 and abs(L2[1] - U2[1]) < 1e-7)
        ok("rf_6_convergencia", abs(f(U2[0])) < 1e-6 or abs(f(U2[1])) < 1e-6)
    num_checks_clasicas(ok, casos)
    return res


def num_checks_clasicas(ok, casos: int) -> None:
    """Comprobaciones de las versiones clásicas añadidas el 24 sep 2026."""
    from decimal import Decimal, getcontext
    from fractions import Fraction
    import numpy as np
    tol = 1e-9
    for _ in range(casos):
        f, a, b = f_cambio_signo()
        c = sum(bis_py(f, a, b, 200)) / 2
        ok("bis_5c_cota_uniforme", abs(f(c)) < 1e-6 and all(abs(sum(bis_py(f, a, b, n)) / 2 - c) <= (b - a) / 2 ** (n + 1) + tol for n in range(40)))
        k = R.uniform(0, 0.95); w = R.uniform(0.3, 3); al = R.uniform(-2, 2); Rr = k / w + R.uniform(0, 1)
        g = lambda x: al + k * math.sin(w * x) / w
        A, B = al - Rr, al + Rr; x0 = R.uniform(A, B); pp = x0
        for _i in range(3000):
            pp = g(pp)
        n = R.randint(0, 30); xn = x0
        for _i in range(n):
            xn = g(xn)
        ok("pf_5c_a_priori_max", abs(xn - pp) <= k ** n * max(x0 - A, B - x0) + 1e-9)
        q = R.uniform(-1, 1); cc = R.uniform(-2, 2); dd = R.uniform(-2, 2); rad = R.uniform(0.1, 1)
        gq = lambda x: q + cc * (x - q) ** 2 + dd * (x - q) ** 3
        L = 2 * abs(cc) + 3 * abs(dd) * rad; xq = R.uniform(q - rad, q + rad)
        ok("pf_9c_cuadratico_medio", abs(gq(xq) - q) <= L / 2 * (xq - q) ** 2 + 1e-12)
        z = f_newton()
        if z:  # las clásicas son ∃δ: el δ de f_newton sirve de testigo (f cúbica es C² y f'(r) = β ≠ 0)
            f, d1, d2, r, dl, m, M = z
            N = lambda x: x - f(x) / d1(x)
            x = R.uniform(r - dl, r + dl)
            ok("newton_2c_contraccion_local", abs(N(x) - r) <= abs(x - r) / 2 + 1e-12)
            xs = [x]
            for _i in range(8):
                xs.append(N(xs[-1]))
            ok("newton_4c_convergencia_local", abs(xs[-1] - r) < 1e-9)
            ok("newton_5c_orden2_local", all(abs(xs[i + 1] - r) <= M / (2 * m) * (xs[i] - r) ** 2 + 1e-12 for i in range(6)))
            S = lambda x, y: y - f(y) * (y - x) / (f(y) - f(x)) if f(y) != f(x) else y
            y = R.uniform(r - dl, r + dl)
            if x != y:
                ok("secante_4c_contraccion_local", abs(S(x, y) - r) <= abs(y - r) / 2 + 1e-12)
                seq = [x, y]
                for _i in range(12):
                    seq.append(S(seq[-2], seq[-1]) if seq[-1] != seq[-2] else seq[-1])
                ok("secante_5c_convergencia_local", abs(seq[-1] - r) < 1e-9)
        # regula falsi con raíz única: los puntos c_n convergen a ella
        f, a, b = f_cambio_signo()
        if f(a) > 0:
            f = (lambda h: (lambda x: -h(x)))(f)
        coef = np.polyfit(np.linspace(a, b, 9), [f(t) for t in np.linspace(a, b, 9)], 3)
        reales = [z.real for z in np.roots(coef) if abs(z.imag) < 1e-9 and a <= z.real <= b]
        if len(reales) == 1:
            def c_n(n):
                l, u = rf_py(f, a, b, n)
                return (l * f(u) - u * f(l)) / (f(u) - f(l)) if f(u) != f(l) else 0.0
            ok("rf_6c_puntos_convergen", abs(c_n(20000) - reales[0]) < 1e-6 and abs(c_n(20000) - c_n(10000)) < 1e-7)
    # orden φ clásico, en aritmética decimal de 1200 dígitos (los errores llegan a ~10^-500; el cociente converge
    # despacio: su error logarítmico se multiplica por −1/φ en cada paso)
    getcontext().prec = 1200
    phi = (1 + Decimal(5).sqrt()) / 2
    D = lambda q: Decimal(q.numerator) / Decimal(q.denominator)
    for _ in range(max(20, casos // 20)):
        r = D(Fraction(R.randint(-20, 20), 10)); beta = D(Fraction(R.choice([-1, 1]) * R.randint(5, 30), 10))
        gam = D(Fraction(R.choice([-1, 1]) * R.randint(1, 20), 10)); eps = D(Fraction(R.randint(-10, 10), 10))
        f = lambda x: beta * (x - r) + gam * (x - r) ** 2 + eps * (x - r) ** 3
        dl = abs(beta) / (4 * (abs(gam) + abs(eps) + 1))  # contracción ≈ 1/4: el error llega a ~10^-370, representable
        x0 = r + dl * R.randint(-9, 9) / 10; x1 = r + dl * R.randint(-9, 9) / 10
        if x0 == x1 or x0 == r or x1 == r:
            continue
        seq = [x0, x1]
        for _i in range(13):
            u, v = seq[-2], seq[-1]
            if f(v) == f(u):
                break
            seq.append(v - f(v) * (v - u) / (f(v) - f(u)))
        e = [abs(t - r) for t in seq]
        if len(seq) < 15 or any(t == 0 for t in e):
            continue
        limite = abs(gam / beta) ** (phi - 1)
        desvios = [abs(e[i + 1] / e[i] ** phi / limite - 1) for i in range(10, 14)]
        ok("secante_6c_orden_phi", desvios[-1] < Decimal("0.03") and desvios[-1] <= desvios[0])
    # Q-orden 2 de Newton: |e_{n+1}|/e_n^2 → |f''(r)/(2f'(r))| = |γ/β| (converge rápido; decimal de 400 dígitos)
    getcontext().prec = 400
    for _ in range(max(20, casos // 20)):
        r = D(Fraction(R.randint(-20, 20), 10)); beta = D(Fraction(R.choice([-1, 1]) * R.randint(5, 30), 10))
        gam = D(Fraction(R.randint(-20, 20), 10)); eps = D(Fraction(R.randint(-10, 10), 10))
        f = lambda x: beta * (x - r) + gam * (x - r) ** 2 + eps * (x - r) ** 3
        d1 = lambda x: beta + 2 * gam * (x - r) + 3 * eps * (x - r) ** 2
        dl = abs(beta) / (4 * (abs(gam) + abs(eps) + 1))
        x = r + dl * R.randint(1, 9) / 10 * R.choice([-1, 1])
        e = []
        for _i in range(7):
            e.append(abs(x - r)); x = x - f(x) / d1(x)
        if any(t == 0 for t in e):
            continue
        limite = abs(gam / beta)
        ok("newton_6c_q_orden2", abs(e[-1] / e[-2] ** 2 - limite) <= Decimal("0.01") * (limite + 1))


# ----------------------------------------------------------------------------------------------- salida


# Aprobación de Carlos (chat del 24 sep 2026): «Revisión de enunciados: todos correctos matemáticamente; apruebo con
# estos cambios». Quedan pendientes los peldaños añadidos en esa misma revisión.
APROBACION = {"por": "Carlos Manuel Orrego Franco", "fecha": "2026-09-24",
              "nota": "revisión de enunciados: todos correctos matemáticamente; aprobado con los cambios pedidos"}
PENDIENTES: set[str] = set()  # pf_6p_a_posteriori y newton_6c_q_orden2 los aprobó Carlos el 24 sep 2026 (segunda revisión)
# análogos directos entre métodos: se citan al interpretar resultados (pedido de Carlos)
ANALOGOS = {"secante_6c_orden_phi": "newton_6c_q_orden2", "newton_6c_q_orden2": "secante_6c_orden_phi"}


def entrada_json(p: dict) -> dict:
    e = {"id": p["id"], "name": p["id"], "kind": "theorem", "metodo": p["metodo"], "peldano": p["peldano"], "split": p["split"],
         "estado": "pendiente_revision" if p["id"] in PENDIENTES else "aprobado", "dificultad": p["dificultad"], "fuente": p["fuente"], "dependencias": p["dependencias"],
         "imports": IMPORTS, "session_parent": "HOL-Analysis", "prelude": PRELUDIO[p["metodo"]], "fixes": p["fixes"],
         "assumes": p["assumes"], "concl": p["concl"], "statement_es": p["statement_es"],
         "supuestos_dudosos": p["supuestos_dudosos"], "referencia_privada": p["referencia_privada"], "borrowed_lemmas": [],
         "version": p["version"], "debilitacion": p["debilitacion"], "version_clasica": p["version_clasica"], "debil_de": p["debil_de"],
         "analogo": ANALOGOS.get(p["id"]),
         "redactado_por": "Claude (Opus 5.5), 24 sep 2026"}
    frozen = {k: e.get(k, "") for k in HASH_FIELDS}
    if e["estado"] == "aprobado":
        e["aprobacion"] = APROBACION
    e["frozen_hash"] = hashlib.sha256(json.dumps(frozen, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16]
    return e


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--solo-num", action="store_true")
    ap.add_argument("--casos", type=int, default=400)
    a = ap.parse_args()
    num = num_checks(a.casos)
    malos = {k: v for k, v in num.items() if v[1] != v[0]}
    faltan = [p["id"] for p in P if p["id"] not in num]
    for p in P:
        t, s = num.get(p["id"], [0, 0])
        print(f"{p['id']:28s} {s}/{t} casos {'OK' if t and s == t else 'REVISAR'}")
    if a.solo_num:
        return 0 if not malos and not faltan else 2
    OUT.mkdir(parents=True, exist_ok=True)
    for p in P:
        e = entrada_json(p)
        e["comprobacion_numerica"] = {"casos": num.get(p["id"], [0, 0])[0], "cumplen": num.get(p["id"], [0, 0])[1]}
        (OUT / f"{p['id']}.json").write_text(json.dumps(e, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(P)} peldaños escritos en {OUT.relative_to(HERE)}; con problemas numéricos: {sorted(malos) or 'ninguno'}; sin comprobar: {faltan or 'ninguno'}")
    print("revisión:", escribir_revision().relative_to(HERE))
    return 0 if not malos and not faltan else 2



# ----------------------------------------------------------------------------------------------- archivo de revisión

# comprobaciones numéricas débiles: se declaran en la revisión para no presentarlas como más de lo que son
NUM_DEBIL = {
    "pf_1_derivada": "solo compara los extremos del intervalo, no pares arbitrarios",
    "pf_3_unicidad": "solo comprueba que el punto hallado por iteración es fijo, no la unicidad",
    "pf_8_convergencia": "repite la cota a priori; la convergencia se sigue de ella",
}


def escribir_revision() -> Path:
    """corpus/raices/revision_enunciados.md: todo lo que Carlos necesita para aprobar, corregir o descartar cada peldaño."""
    import corpus_isabelle as ci  # import tardío: corpus_isabelle importa este módulo
    val = json.loads((OUT / "validacion_isabelle.json").read_text(encoding="utf-8")) if (OUT / "validacion_isabelle.json").exists() else {}
    ents = {p["id"]: json.loads((OUT / f"{p['id']}.json").read_text(encoding="utf-8")) for p in P}
    nombres = {"biseccion": "Bisección", "punto_fijo": "Punto fijo", "newton": "Newton", "ordenes": "Órdenes de convergencia",
               "secante": "Secante", "regula_falsi": "Regula falsi"}
    L = ["# Revisión de enunciados: corpus de búsqueda de raíces", "",
         "Redactados por Claude el 24 sep 2026. Carlos revisó y aprobó el 24 sep 2026 («todos correctos matemáticamente; "
         "apruebo con estos cambios») y, en una segunda revisión, aprobó `pf_6p_a_posteriori` (con dependencia `pf_2_dentro`) "
         "y `newton_6c_q_orden2`, y confirmó las hipótesis sobrantes. "
         + (("Pendientes de revisión: " + ", ".join(f"`{i}`" for i in sorted(PENDIENTES)) + ". ") if PENDIENTES else "Todos aprobados. ")
         + "Solo los aprobados pueden usarse en una corrida. Análogos directos entre métodos: `secante_6c_orden_phi` (test) "
         "y `newton_6c_q_orden2` (train).", "",
         "Qué se comprobó, sin demostrar ninguna conclusión (eso es trabajo del proponente):", "",
         "* **Isabelle**: el preludio compila; las hipótesis y la conclusión se leen y tipan en su contexto; y una "
         "`interpretation` con valores concretos demuestra que las hipótesis se pueden cumplir (el peldaño no es vacuo). "
         "Detalle en `validacion_isabelle.json`.",
         "* **Numérica**: casos aleatorios que cumplen las hipótesis; la conclusión se cumplió en todos (`tools/corpus_raices.py`). "
         "Detecta errores de formalización (constantes, exponentes); no es una demostración.", "",
         "Convenciones de HOL que conviene tener presentes: x/0 = 0; `real n` es n como real; `(g ^^ n) x0` es g aplicada n veces; "
         "`X ⇢ L` (`\\<longlonglongrightarrow>`) es convergencia de sucesiones. Imports de todos: `HOL-Analysis.Analysis` "
         "(nunca las teorías del artículo).", "",
         f"Split: **train** = bisección, punto fijo, Newton, órdenes ({sum(q['split'] == 'train' for q in P)} peldaños); "
         f"**test** = secante y regula falsi completos, con sus peldaños bajos ({sum(q['split'] == 'test' for q in P)} peldaños); "
         f"total {len(P)}. El test tiene solo dos métodos: los resultados se reportarán por teorema y por nivel de dificultad.", "",
         "Peldaños por nivel de dificultad:", "", "| dificultad | train | test |", "|---|---|---|",
         *[f"| {d} | {sum(q['split'] == 'train' and q['dificultad'] == d for q in P)} | {sum(q['split'] == 'test' and q['dificultad'] == d for q in P)} |"
           for d in range(1, 6)], "",
         "Versión: **clásica** es la forma de libro del resultado; **debilitada** tiene una conclusión más débil o hipótesis "
         "más fuertes en algo que importa (δ fijo, cotas dadas, peor constante), y se dice en qué y por qué. Cada debilitada "
         "con forma clásica más fuerte va seguida de esa versión clásica (sufijo `c`), también pendiente de revisión. Un "
         "peldaño clásico que arrastra hipótesis del contexto común que no usa se marca clásico con esa nota.", "",
         "| id | método | split | versión | dificultad | estado | Isabelle | numérica |", "|---|---|---|---|---|---|---|---|"]
    for p in P:
        e = ents[p["id"]]
        vi = "✓" if val.get(p["metodo"], {}).get("ok") else "✗"
        cn = e.get("comprobacion_numerica", {})
        L.append(f"| `{p['id']}` | {nombres[p['metodo']]} | {p['split']} | {p['version']} | {p['dificultad']} | {e['estado']} | {vi} | {cn.get('cumplen')}/{cn.get('casos')} |")
    for m in PRELUDIO:
        L += ["", f"## {nombres[m]}", ""]
        if PRELUDIO[m]:
            L += ["Preludio (definiciones congeladas):", "", "```isabelle", PRELUDIO[m], "```", ""]
        L += [f"Lectura: {LECTURA_PRELUDIO[m]}", "", f"Hipótesis típicas: {LECTURA_HIP[m]}", ""]
        for p in [q for q in P if q["metodo"] == m]:
            e = ents[p["id"]]
            cn = e.get("comprobacion_numerica", {})
            testigo = ", ".join(ci.TESTIGOS[p["id"]])
            if p["version"] == "debilitada":
                vers = (f"**Versión debilitada**: {p['debilitacion']}. Versión clásica más fuerte: `{p['version_clasica']}`.")
            elif p["debil_de"]:
                vers = f"**Versión clásica** (más fuerte que {', '.join(f'`{d}`' for d in p['debil_de'])})."
            else:
                vers = "**Versión clásica**" + (f" ({p['debilitacion']})." if p["debilitacion"] else ".")
            L += [f"### `{p['id']}` ({p['split']}, dificultad {p['dificultad']})", "", vers, "",
                  f"**Enunciado:** {p['statement_es']}", "", "```isabelle", f"fixes {p['fixes']}", f"assumes {p['assumes']}",
                  f"shows \"{p['concl']}\"", "```", "",
                  f"* Fuente: {p['fuente']}." + (f" Depende de: {', '.join(f'`{d}`' for d in p['dependencias'])}." if p["dependencias"] else ""),
                  f"* Referencia privada (nunca se muestra al proponente): {p['referencia_privada'] or 'ninguna'}.",
                  f"* Supuestos dudosos: {p['supuestos_dudosos'].rstrip('.') or 'ninguno señalado'}.",
                  f"* Comprobaciones: Isabelle {'✓' if val.get(m, {}).get('ok') else '✗'} (ejemplo de no vacuidad, en el orden de "
                  f"los fixes: {testigo}); numérica {cn.get('cumplen')}/{cn.get('casos')}"
                  + (f" (débil: {NUM_DEBIL[p['id']]})" if p["id"] in NUM_DEBIL else "") + ".", f"* Hash del enunciado: `{e['frozen_hash']}`.", "",
                  ("- [ ] aprobar   - [ ] corregir: ______________________   - [ ] descartar" if p["id"] in PENDIENTES
                   else "Estado: **aprobado** por Carlos (24 sep 2026)."), ""]
    ruta = OUT / "revision_enunciados.md"
    ruta.write_text("\n".join(L) + "\n", encoding="utf-8")
    return ruta


if __name__ == "__main__":
    raise SystemExit(main())
