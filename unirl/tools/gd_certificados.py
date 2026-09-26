"""Certificados racionales EXACTOS del PEP para los objetivos gd del juez de Isabelle (docs/diseno_gd_isabelle.md).

Para gd_n1 (h = [3/2], τ = 1/8), gd_const_n2 (h = [1, 1], τ = 1/10) y el control gd_const_n3 (h = [1, 1, 1],
τ = 1/14), con L = 1, μ = 0 y criterio f(xₙ) − f*, se buscan

* multiplicadores λᵢⱼ ≥ 0 racionales con conservación de flujo, y
* una descomposición M(λ, τ) = Σₖ dₖ wₖ wₖᵀ con dₖ ≥ 0 racionales y wₖ vectores de enteros en la base del Gram,

con τ EXACTAMENTE el del objetivo (sin redondear hacia arriba: la cota es la óptima, M es singular y un redondeo
ingenuo no cierra). Todo se comprueba en `fractions.Fraction`.

Convención (la de `steprl.certify._vectors_exact` del 06, con x* = 0 trasladado a xs):

* puntos 0…n = x₀…xₙ (los iterados; x₀ = x0) y punto n+1 = xs (x*, con g(xs) = 0 por `opt`);
* base del Gram: e₀ = x0 − xs, e₁₊ₖ = gₖ = g(xₖ), k = 0…n;
* λᵢⱼ multiplica holguraᵢⱼ = f(xᵢ) − f(xⱼ) − ⟨gⱼ, xᵢ − xⱼ⟩ − ½‖gᵢ − gⱼ‖² ≥ 0, que es interp[of xᵢ xⱼ]
  (en `interp`, x = xᵢ e y = xⱼ);
* flujo: para k = 0…n, Σⱼ λₖⱼ − Σᵢ λᵢₖ = −[k = n];
* identidad (la que usa Isabelle): τ‖x0 − xs‖² − (f(xₙ) − f(xs)) = Σ λᵢⱼ·holguraᵢⱼ + Σₖ dₖ‖wₖ‖².

Búsqueda: para pasos constantes h = 1, la forma cerrada de Drori y Teboulle (2014): λ_{k,k+1} = (k+1)/(2n−k) en la
cadena y λ_{*,k} = λ_{k,k+1} − λ_{k−1,k} desde x*. Si no, el dual numérico con τ fijo (mínima Σλ, que cae en un
vértice de la cara óptima) redondeado con `limit_denominator`. La descomposición es LDLᵀ exacta; se prueba cada
orden de pivotes y se queda la de coeficientes más cortos, con wₖ escalado a enteros primos entre sí.

Uso: .venv/bin/python tools/gd_certificados.py  (escribe corpus/curado/stepsize/gd_cert/<objetivo>.json y comprueba todo).
"""

from __future__ import annotations

import itertools
import json
import math
import random
import sys
import warnings
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parents[2]  # rl_metodos/
OUT = HERE / "corpus" / "curado" / "stepsize" / "gd_cert"

from steprl.certify import assemble, exact_matrices, flow_residuals, is_psd_exact  # noqa: E402

L, MU, CRITERIO = Fraction(1), Fraction(0), "fval"

OBJETIVOS = {
    "gd_n1": {"h": ["3/2"], "tau": "1/8",
              "concl": "f (gd g [3/2] x0) - f xs \\<le> 1/8 * (norm (x0 - xs))\\<^sup>2"},
    "gd_const_n2": {"h": ["1", "1"], "tau": "1/10",
                    "concl": "f (gd g [1, 1] x0) - f xs \\<le> 1/10 * (norm (x0 - xs))\\<^sup>2"},
    # control: solo JSON (no es objetivo del juez)
    "gd_const_n3": {"h": ["1", "1", "1"], "tau": "1/14", "concl": None},
}

CONVENCION = (
    "Puntos 0..n = x_0..x_n (iterados de gd, x_0 = x0) y punto n+1 = xs (x*, g(xs) = 0 por opt). "
    "Base del Gram: e_0 = x0 - xs, e_{k+1} = g_k = g(x_k) para k = 0..n (la de steprl.certify._vectors_exact "
    "con x* = 0); x_{k+1} = x_k - h_k g_k. lambda_ij multiplica holgura_ij = f(x_i) - f(x_j) - <g_j, x_i - x_j> "
    "- (1/2)||g_i - g_j||^2 >= 0, que es interp[of x_i x_j] (en interp, x = x_i, y = x_j). Flujo: para k = 0..n, "
    "sum_j lambda_kj - sum_i lambda_ik = -[k = n]. M = sum lambda_ij A_ij + tau e_0 e_0^T (steprl.certify.assemble) "
    "= sum_k d_k w_k w_k^T, con w_k = sum_b w_k[b] e_b. Identidad exacta: tau ||x0 - xs||^2 - (f(x_n) - f(xs)) = "
    "sum lambda_ij holgura_ij + sum_k d_k ||w_k||^2."
)


# ----------------------------------------------------------------------------- utilidades

def pq(x: Fraction) -> str:
    """Racional como «p/q» (siempre con denominador, también los enteros)."""
    x = Fraction(x)
    return f"{x.numerator}/{x.denominator}"


def nombres_puntos(n: int) -> list[str]:
    return [f"x{k}" for k in range(n + 1)] + ["xs"]


def nombres_base(n: int) -> list[str]:
    return ["x0 - xs"] + [f"g{k}" for k in range(n + 1)]


# ----------------------------------------------------------------------------- multiplicadores

def lambda_drori_teboulle(n: int) -> dict[tuple[int, int], Fraction]:
    """Paso constante h = 1 (L = 1): λ_{k,k+1} = (k+1)/(2n−k), k = 0…n−1 (en Drori–Teboulle 2014, λᵢ = i/(2N+1−i));
    desde x* (índice n+1): λ_{*,k} = λ_{k,k+1} − λ_{k−1,k}, con λ_{−1,0} = 0 y λ_{n,n+1} = 1 (cierra el flujo)."""
    star = n + 1
    cadena = [Fraction(k + 1, 2 * n - k) for k in range(n)]
    lam = {(k, k + 1): cadena[k] for k in range(n)}
    for k in range(n + 1):
        sale = cadena[k] if k < n else Fraction(1)
        entra = cadena[k - 1] if k > 0 else Fraction(0)
        lam[(star, k)] = sale - entra
    return {p: v for p, v in lam.items() if v != 0}


def lambda_numerico(h: list[Fraction], tau: Fraction) -> dict[tuple[int, int], float]:
    """Dual del PEP con τ fijo: mínima Σλ con λ ≥ 0, flujo cerrado y M(λ, τ) ⪰ 0 (cae en un vértice de la cara)."""
    import cvxpy as cp
    import numpy as np
    from steprl.pep import interpolation_matrices

    n = len(h)
    dim = n + 2
    pairs, mats = interpolation_matrices([float(x) for x in h], float(L), float(MU))
    lam = cp.Variable(len(pairs), nonneg=True)
    e0 = np.zeros(dim)
    e0[0] = 1.0
    M = sum(lam[p] * mats[p] for p in range(len(pairs))) + float(tau) * np.outer(e0, e0)
    cons = [M >> 0]
    for k in range(n + 1):
        sale = sum(lam[q] for q, (i, _) in enumerate(pairs) if i == k)
        entra = sum(lam[q] for q, (_, j) in enumerate(pairs) if j == k)
        cons.append(sale - entra + (1.0 if k == n else 0.0) == 0)
    prob = cp.Problem(cp.Minimize(cp.sum(lam)), cons)
    with warnings.catch_warnings():  # «optimal_inaccurate» es normal con M singular; decide la comprobación exacta
        warnings.simplefilter("ignore")
        prob.solve(solver="CLARABEL", tol_gap_abs=1e-11, tol_gap_rel=1e-11, tol_feas=1e-11, max_iter=500)
    if lam.value is None:
        return {}
    return {p: float(lam.value[q]) for q, p in enumerate(pairs)}


def racionalizar(lam_f: dict[tuple[int, int], float], max_den: int) -> dict[tuple[int, int], Fraction]:
    out = {}
    for p, v in lam_f.items():
        r = Fraction(v).limit_denominator(max_den)
        if r > 0 and abs(v - float(r)) < 1e-5:
            out[p] = r
    return out


# ----------------------------------------------------------------------------- descomposición en cuadrados

def _ldl(M: list[list[Fraction]], orden: tuple[int, ...]) -> list[tuple[Fraction, list[Fraction]]] | None:
    """LDLᵀ exacta con los pivotes en `orden`. None si algún pivote es negativo o un pivote nulo tiene fila no nula."""
    dim = len(M)
    A = [row[:] for row in M]
    cuadrados = []
    usados: list[int] = []
    for k in orden:
        d = A[k][k]
        resto = [i for i in orden if i not in usados and i != k]
        if d < 0:
            return None
        if d == 0:
            if any(A[i][k] != 0 for i in resto):
                return None
            usados.append(k)
            continue
        w = [Fraction(0)] * dim
        w[k] = Fraction(1)
        for i in resto:
            w[i] = A[i][k] / d
        for i in resto + [k]:
            for j in resto + [k]:
                A[i][j] -= d * w[i] * w[j]
        cuadrados.append((d, w))
        usados.append(k)
    return cuadrados


def _entero(d: Fraction, w: list[Fraction]) -> tuple[Fraction, list[Fraction]]:
    """Reescala d·wwᵀ = (d/c²)(cw)(cw)ᵀ con cw de enteros primos entre sí y primer coeficiente no nulo positivo."""
    c = math.lcm(*[x.denominator for x in w])
    v = [x * c for x in w]
    gcd = math.gcd(*[int(x) for x in v])
    v = [x / gcd for x in v]
    c = Fraction(c, gcd)
    if next(x for x in v if x != 0) < 0:
        v = [-x for x in v]
    return d / (c * c), v


def _tamano(cuadrados) -> int:
    return sum(len(pq(d)) + sum(len(str(x)) for x in w) for d, w in cuadrados)


def descomponer(M: list[list[Fraction]]) -> list[tuple[Fraction, list[Fraction]]]:
    """M = Σ dₖ wₖ wₖᵀ exacta; entre todos los órdenes de pivotes, la de texto más corto (menos cuadrados primero)."""
    mejor = None
    for orden in itertools.permutations(range(len(M))):
        c = _ldl(M, orden)
        if c is None:
            continue
        c = [_entero(d, w) for d, w in c]
        clave = (len(c), _tamano(c))
        if mejor is None or clave < mejor[0]:
            mejor = (clave, c)
    if mejor is None:
        raise ValueError("M no es semidefinida positiva")
    return mejor[1]


# ----------------------------------------------------------------------------- verificación exacta

def _cuadrados_matriz(cuadrados, dim: int) -> list[list[Fraction]]:
    S = [[Fraction(0)] * dim for _ in range(dim)]
    for d, w in cuadrados:
        for i in range(dim):
            for j in range(dim):
                S[i][j] += d * w[i] * w[j]
    return S


def verificar(cert: dict) -> tuple[bool, str]:
    """Comprobación exacta del certificado guardado: λ ≥ 0, flujo, d ≥ 0 y M(λ, τ) = Σ dₖwₖwₖᵀ entrada a entrada
    (M la arma `steprl.certify.assemble`, la misma construcción del verificador del 06)."""
    h = [Fraction(x) for x in cert["h"]]
    tau = Fraction(cert["tau"])
    n = len(h)
    lam = {(p["i"], p["j"]): Fraction(p["lambda"]) for p in cert["lambda"]}
    if any(v < 0 for v in lam.values()):
        return False, "algún λ es negativo"
    if any(not (0 <= i <= n + 1 and 0 <= j <= n + 1 and i != j) for i, j in lam):
        return False, "par (i, j) fuera de rango"
    res = flow_residuals(n, CRITERIO, lam)
    if any(r != 0 for r in res):
        return False, f"el flujo no cierra: {[str(r) for r in res]}"
    cuadrados = [(Fraction(c["d"]), [Fraction(x) for x in c["w"]]) for c in cert["cuadrados"]]
    if any(d < 0 for d, _ in cuadrados):
        return False, "algún d es negativo"
    if any(len(w) != n + 2 for _, w in cuadrados):
        return False, "algún w no tiene la dimensión de la base"
    M = assemble(h, L, MU, CRITERIO, lam, tau)
    if M != _cuadrados_matriz(cuadrados, n + 2):
        return False, "M(λ, τ) ≠ Σ d w wᵀ"
    if [[str(x) for x in row] for row in M] != cert.get("M", [[str(x) for x in row] for row in M]):
        return False, "la M guardada no coincide con la reconstruida"
    if not is_psd_exact(M):  # redundante con lo anterior; defensa en profundidad
        return False, "M(λ, τ) no es semidefinida positiva"
    return True, "certificado válido"


# ----------------------------------------------------------------------------- identidad con vectores aleatorios

def _v_add(u, v):
    return tuple(a + b for a, b in zip(u, v))


def _v_sub(u, v):
    return tuple(a - b for a, b in zip(u, v))


def _v_scale(c, v):
    return tuple(c * a for a in v)


def _inner(u, v) -> Fraction:
    return sum((a * b for a, b in zip(u, v)), Fraction(0))


def holgura_interp(fx, fy, gx, gy, x, y) -> Fraction:
    """interp[of x y] dice  f y + inner (g y) (x - y) + (1/2) * (norm (g x - g y))² ≤ f x;  holgura = der. − izq."""
    return fx - (fy + _inner(gy, _v_sub(x, y)) + Fraction(1, 2) * _inner(_v_sub(gx, gy), _v_sub(gx, gy)))


def _q(rng: random.Random) -> Fraction:
    return Fraction(rng.randint(-9, 9), rng.randint(1, 6))


def identidad_aleatoria(cert: dict, semilla: int = 0, dim: int = 5, pruebas: int = 20) -> tuple[bool, str]:
    """En Q^dim con x0, xs, g(x_k) y f arbitrarios (x_{k+1} = x_k − h_k g(x_k), g(xs) = 0): comprueba en Fraction
    τ‖x0 − xs‖² − (f_n − f*) = Σ λᵢⱼ·holguraᵢⱼ + Σ dₖ‖wₖ‖², con holguraᵢⱼ tomada literalmente de interp[of xᵢ xⱼ].
    No usa nada del 06: es independiente de la construcción matricial."""
    rng = random.Random(semilla)
    h = [Fraction(x) for x in cert["h"]]
    tau = Fraction(cert["tau"])
    n = len(h)
    star = n + 1
    lam = {(p["i"], p["j"]): Fraction(p["lambda"]) for p in cert["lambda"]}
    cuadrados = [(Fraction(c["d"]), [Fraction(x) for x in c["w"]]) for c in cert["cuadrados"]]
    for t in range(pruebas):
        x0 = tuple(_q(rng) for _ in range(dim))
        xs = tuple(_q(rng) for _ in range(dim))
        xk, gk = [x0], []
        for k in range(n + 1):
            gk.append(tuple(_q(rng) for _ in range(dim)))
            if k < n:
                xk.append(_v_sub(xk[k], _v_scale(h[k], gk[k])))
        fk = [_q(rng) for _ in range(n + 1)]
        fstar = _q(rng)
        X, G, Fv = xk + [xs], gk + [tuple(Fraction(0) for _ in range(dim))], fk + [fstar]  # g(xs) = 0
        izquierda = tau * _inner(_v_sub(x0, xs), _v_sub(x0, xs)) - (fk[n] - fstar)
        derecha = sum((v * holgura_interp(Fv[i], Fv[j], G[i], G[j], X[i], X[j]) for (i, j), v in lam.items()), Fraction(0))
        base = [_v_sub(x0, xs)] + gk
        for d, w in cuadrados:
            vec = tuple(Fraction(0) for _ in range(dim))
            for c, e in zip(w, base):
                vec = _v_add(vec, _v_scale(c, e))
            derecha += d * _inner(vec, vec)
        if izquierda != derecha:
            return False, f"prueba {t}: {izquierda} ≠ {derecha}"
        assert star == len(X) - 1
    return True, f"identidad exacta en {pruebas} pruebas aleatorias (Q^{dim})"


# ----------------------------------------------------------------------------- construcción

def _candidatos(h: list[Fraction], tau: Fraction):
    n = len(h)
    if all(x == 1 for x in h):
        yield "forma cerrada de Drori y Teboulle (2014) para paso constante h = 1", lambda_drori_teboulle(n)
    lam_f = lambda_numerico(h, tau)
    for max_den in (12, 60, 360, 2520, 10**4, 10**6):
        yield f"dual numérico con tau fijo (mínima suma de lambda) y limit_denominator({max_den})", racionalizar(lam_f, max_den)


def _tau_sdp(h: list[Fraction]) -> float:
    """Valor numérico del PEP (primal, informativo): debe coincidir con τ hasta la tolerancia del solver."""
    from steprl.pep import gd_worst_case

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return round(gd_worst_case([float(x) for x in h]).value, 10)


def construir(objetivo: str) -> dict:
    spec = OBJETIVOS[objetivo]
    h = [Fraction(x) for x in spec["h"]]
    tau = Fraction(spec["tau"])
    n = len(h)
    for metodo, lam in _candidatos(h, tau):
        if not lam or any(r != 0 for r in flow_residuals(n, CRITERIO, lam)):
            continue
        M = assemble(h, L, MU, CRITERIO, lam, tau)
        if not is_psd_exact(M):
            continue
        cuadrados = descomponer(M)
        puntos = nombres_puntos(n)
        cert = {
            "objetivo": objetivo,
            "concl": spec["concl"],
            "h": [pq(x) for x in h],
            "tau": pq(tau),
            "L": pq(L), "mu": pq(MU), "criterio": "f(x_n) - f*",
            "convencion": CONVENCION,
            "puntos": puntos,
            "base": nombres_base(n),
            "lambda": [{"i": i, "j": j, "lambda": pq(v), "isabelle": f"interp[of {puntos[i]} {puntos[j]}]"}
                       for (i, j), v in sorted(lam.items())],
            "cuadrados": [{"d": pq(d), "w": [str(x) for x in w]} for d, w in cuadrados],
            "M": [[str(x) for x in row] for row in M],
            "metodo": metodo,
            "tau_sdp": _tau_sdp(h),
        }
        ok, msg = verificar(cert)
        if not ok:
            raise AssertionError(f"{objetivo}: {msg}")
        ok, msg2 = identidad_aleatoria(cert)
        if not ok:
            raise AssertionError(f"{objetivo}: {msg2}")
        cert["verificacion"] = {"matrices": msg, "identidad": msg2}
        return cert
    raise RuntimeError(f"{objetivo}: no se encontró un certificado exacto con tau = {tau}")


def a_json(cert: dict) -> str:
    """JSON legible: una clave por línea; listas de escalares y cada λ o cuadrado en una sola línea."""
    lineas = ["{"]
    items = list(cert.items())
    for k, (clave, v) in enumerate(items):
        coma = "," if k < len(items) - 1 else ""
        if isinstance(v, list) and v and isinstance(v[0], (dict, list)):
            lineas.append(f" {json.dumps(clave)}: [")
            lineas += [f"  {json.dumps(x, ensure_ascii=False)}{',' if t < len(v) - 1 else ''}" for t, x in enumerate(v)]
            lineas.append(f" ]{coma}")
        else:
            lineas.append(f" {json.dumps(clave)}: {json.dumps(v, ensure_ascii=False)}{coma}")
    return "\n".join(lineas + ["}"]) + "\n"


def cargar(objetivo: str) -> dict:
    return json.loads((OUT / f"{objetivo}.json").read_text(encoding="utf-8"))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for objetivo in OBJETIVOS:
        cert = construir(objetivo)
        (OUT / f"{objetivo}.json").write_text(a_json(cert), encoding="utf-8")
        lam = ", ".join(f"({p['i']},{p['j']})={p['lambda']}" for p in cert["lambda"])
        sq = "; ".join(f"{c['d']}·[{', '.join(c['w'])}]" for c in cert["cuadrados"])
        print(f"{objetivo}: tau = {cert['tau']}  [{cert['metodo']}]\n  lambda: {lam}\n  cuadrados: {sq}\n"
              f"  {cert['verificacion']['matrices']}; {cert['verificacion']['identidad']}")


if __name__ == "__main__":
    main()
