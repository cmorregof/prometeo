1. **Hipótesis 2** (H2). x₀ < x₁ < … < xₙ son n + 1 nodos distintos en [a, b].
2. **Hipótesis 1** (H1). f ∈ Cⁿ⁺¹[a, b].
3. **Polinomio nodal** (DEFW). w(t) = ∏ᵢ₌₀ⁿ (t − xᵢ) tiene grado n + 1, coeficiente principal 1 y w⁽ⁿ⁺¹⁾ ≡ (n + 1)!.
4. **Existencia y unicidad** (EXIST). Existe un único pₙ de grado ≤ n con pₙ(xᵢ) = f(xᵢ): la base de Lagrange ℓᵢ lo construye y dos soluciones difieren en un polinomio de grado ≤ n con n + 1 ceros, luego nulo.
5. **Fijar x** (FIX). Sea x ∈ [a, b] distinto de todos los nodos (si x = xᵢ ambos lados de la fórmula son 0). Entonces w(x) ≠ 0.
6. **Minimalidad de Chebyshev** (CHEB). En [−1, 1], entre todos los polinomios mónicos de grado n + 1, Tₙ₊₁/2ⁿ tiene la menor norma uniforme, 2⁻ⁿ; sus ceros son los nodos de Chebyshev y con ellos máx|w| = 2⁻ⁿ.
7. **Función auxiliar** (AUX). Sea g(t) = f(t) − pₙ(t) − [f(x) − pₙ(x)]·w(t)/w(x). Por H1, g ∈ Cⁿ⁺¹[a, b].
8. **n + 2 ceros** (ZEROS). g se anula en los n + 1 nodos (allí f = pₙ y w = 0) y en x (por construcción): n + 2 ceros distintos.
9. **Derivada n + 1** (DERIV). pₙ⁽ⁿ⁺¹⁾ ≡ 0 (grado ≤ n) y w⁽ⁿ⁺¹⁾ ≡ (n + 1)!, luego g⁽ⁿ⁺¹⁾(t) = f⁽ⁿ⁺¹⁾(t) − [f(x) − pₙ(x)]·(n + 1)!/w(x).
10. **Rolle iterado** (ROLLE). Entre dos ceros consecutivos de g hay un cero de g′ (Rolle): g′ tiene ≥ n + 1 ceros, g″ ≥ n, …, g⁽ⁿ⁺¹⁾ tiene al menos un cero ξ ∈ (a, b).
11. **Fórmula del error** (FORMULA). Evaluando en ξ: 0 = f⁽ⁿ⁺¹⁾(ξ) − [f(x) − pₙ(x)]·(n + 1)!/w(x), es decir f(x) − pₙ(x) = f⁽ⁿ⁺¹⁾(ξ)·w(x)/(n + 1)!.
12. **Cota uniforme** (BOUND). Con M = máx|f⁽ⁿ⁺¹⁾|: máx_{[a,b]} |f − pₙ| ≤ M · máx|w| / (n + 1)!. El único factor que depende de los nodos es máx|w|.
13. **Conclusión** (QED). Con nodos de Chebyshev, máx|f − pₙ| ≤ M / (2ⁿ (n + 1)!), y ninguna otra elección de nodos mejora el factor máx|w|. ∎