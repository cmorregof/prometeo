1. **Hipótesis 1** (H1). g es continua en [a, b] y g([a, b]) ⊆ [a, b].
2. **Hipótesis 2** (H2). g es contracción: existe k ∈ [0, 1) con |g(x) − g(y)| ≤ k·|x − y| para todo x, y ∈ [a, b].
3. **Definición** (DEF). Sea x₀ ∈ [a, b] y xₙ₊₁ = g(xₙ). Por H1 e inducción, xₙ ∈ [a, b] para todo n.
4. **Función auxiliar** (AUX). h(x) = g(x) − x es continua, h(a) = g(a) − a ≥ 0 y h(b) = g(b) − b ≤ 0.
5. **Existencia** (EXIST). Por Bolzano aplicado a h existe p ∈ [a, b] con h(p) = 0, es decir g(p) = p.
6. **Pasos consecutivos** (STEP). |xₙ₊₁ − xₙ| = |g(xₙ) − g(xₙ₋₁)| ≤ k·|xₙ − xₙ₋₁| ≤ kⁿ·|x₁ − x₀|.
7. **Contracción del error** (ERR). |xₙ₊₁ − p| = |g(xₙ) − g(p)| ≤ k·|xₙ − p|.
8. **Decaimiento geométrico** (GEO). Por inducción sobre n: |xₙ − p| ≤ kⁿ·|x₀ − p|.
9. **Unicidad** (UNIQ). Si p y q son puntos fijos, |p − q| = |g(p) − g(q)| ≤ k·|p − q| con k < 1, luego p = q.
10. **Cota a priori** (PRIORI). p ∈ [a, b] ⇒ |x₀ − p| ≤ max(x₀ − a, b − x₀), luego |xₙ − p| ≤ kⁿ·max(x₀ − a, b − x₀).
11. **Convergencia** (LIM). Como 0 ≤ k < 1, kⁿ → 0, así que xₙ → p.
12. **Cota a posteriori** (POST). |xₙ − p| ≤ Σᵢ₌ₙ^∞ |xᵢ₊₁ − xᵢ| ≤ kⁿ·|x₁ − x₀|·Σⱼ kʲ = kⁿ/(1 − k)·|x₁ − x₀| (serie geométrica y xₙ → p).
13. **Conclusión** (QED). Existe un único punto fijo p, xₙ → p para todo x₀ ∈ [a, b] y valen las cotas a priori y a posteriori. ∎