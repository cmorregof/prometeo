1. **Hipótesis** (H1). f ∈ C² en un entorno de r, f(r) = 0 y f'(r) ≠ 0 (raíz simple).
2. **Entorno seguro** (NBHD). Por continuidad de f' y f'' existe δ₀ > 0 con |f'(x)| ≥ m > 0 y |f''(x)| ≤ M en I = [r − δ₀, r + δ₀].
3. **Taylor (n = 1)** (TAYLOR). Por el teorema de Taylor con resto de Lagrange en xₙ: 0 = f(r) = f(xₙ) + f'(xₙ)(r − xₙ) + ½f''(ξₙ)(r − xₙ)², con ξₙ entre xₙ y r.
4. **Definición** (DEF). Para xₙ ∈ I el paso xₙ₊₁ = xₙ − f(xₙ)/f'(xₙ) está bien definido porque f'(xₙ) ≠ 0.
5. **Identidad del error** (ERRID). Dividiendo por f'(xₙ) y usando la definición: r − xₙ₊₁ = −f''(ξₙ)/(2f'(xₙ)) · (r − xₙ)².
6. **Cota cuadrática** (QUAD). Con eₙ = xₙ − r: |eₙ₊₁| ≤ (M / 2m)·|eₙ|² =: C·|eₙ|² mientras xₙ ∈ I.
7. **Elección de δ** (DELTA). Tómese δ ≤ δ₀ con C·δ < 1. Si |e₀| ≤ δ entonces |e₁| ≤ C·δ·|e₀| < |e₀| ≤ δ.
8. **Invariante** (INV). Por inducción xₙ ∈ [r − δ, r + δ] para todo n y |eₙ₊₁| ≤ (C·δ)·|eₙ|.
9. **Convergencia** (CONV). |eₙ| ≤ (C·δ)ⁿ·|e₀| → 0 porque C·δ < 1, luego xₙ → r.
10. **Orden 2** (ORDER). De la cota cuadrática, |eₙ₊₁|/|eₙ|² ≤ C: la convergencia es de orden al menos 2 (los dígitos correctos se duplican).
11. **Conclusión** (QED). Newton converge a r desde todo x₀ con |x₀ − r| ≤ δ, con orden cuadrático. ∎