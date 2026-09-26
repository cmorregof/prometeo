1. **Hipótesis** (H1). f ∈ C² en un entorno de r, f(r) = 0 y f'(r) ≠ 0 (raíz simple).
2. **Forma de Newton** (INTERP). Con diferencias divididas, para todo x: f(x) = f(xₙ) + f[xₙ₋₁, xₙ](x − xₙ) + f[xₙ₋₁, xₙ, x](x − xₙ)(x − xₙ₋₁). En x = r el lado izquierdo es 0.
3. **Entorno seguro** (NBHD). Por continuidad de f' y f'' existe δ₀ > 0 con |f'(x)| ≥ m > 0 y |f''(x)| ≤ M en I = [r − δ₀, r + δ₀].
4. **Definición** (DEF). Para xₙ ≠ xₙ₋₁ en I, f(xₙ) ≠ f(xₙ₋₁) (f es inyectiva en I porque f' ≠ 0), luego el paso de la secante xₙ₊₁ = xₙ − f(xₙ)(xₙ − xₙ₋₁)/(f(xₙ) − f(xₙ₋₁)) está bien definido.
5. **Identidad del error** (ERRID). Dividiendo por f[xₙ₋₁, xₙ] y usando la definición: r − xₙ₊₁ = −(f[xₙ₋₁, xₙ, r] / f[xₙ₋₁, xₙ]) · (r − xₙ)(r − xₙ₋₁).
6. **Valor medio** (MVT). Si xₙ₋₁, xₙ ∈ I: f[xₙ₋₁, xₙ] = f'(ξₙ) con |f'(ξₙ)| ≥ m, y f[xₙ₋₁, xₙ, r] = ½f''(ηₙ) con |f''(ηₙ)| ≤ M (Rolle iterado, como en el resto de Lagrange).
7. **Cota producto** (PROD). Con eₙ = xₙ − r: |eₙ₊₁| ≤ (M / 2m)·|eₙ|·|eₙ₋₁| =: C·|eₙ|·|eₙ₋₁| mientras xₙ₋₁, xₙ ∈ I.
8. **Elección de δ** (DELTA). Tómese δ ≤ δ₀ con C·δ < 1. Si |e₀|, |e₁| ≤ δ entonces |e₂| ≤ C·|e₁|·|e₀| ≤ (C·δ)·|e₁| < δ.
9. **Invariante** (INV). Por inducción xₙ ∈ [r − δ, r + δ] para todo n y |eₙ₊₁| ≤ (C·δ)·|eₙ|.
10. **Convergencia** (CONV). |eₙ| ≤ (C·δ)ⁿ⁻¹·|e₁| → 0 porque C·δ < 1, luego xₙ → r.
11. **Fibonacci** (FIB). Sea dₙ = C·|eₙ| ≤ d := C·δ < 1. De la cota producto, dₙ₊₁ ≤ dₙ·dₙ₋₁, luego dₙ ≤ d^{Fₙ} con Fₙ los números de Fibonacci (F₀ = F₁ = 1).
12. **Orden φ** (ORDER). Si |eₙ₊₁| ~ K·|eₙ|ᵖ, la cota producto da p = 1 + 1/p, es decir p² = p + 1: p = φ = (1 + √5)/2 ≈ 1.618 (= lím Fₙ₊₁/Fₙ). Superlineal, pero no cuadrático.
13. **Conclusión** (QED). La secante converge a r desde todo par x₀, x₁ con |xᵢ − r| ≤ δ, con orden φ ≈ 1.618. ∎