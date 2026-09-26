1. **Hipótesis** (H1). f es de clase Cⁿ⁺¹ en un intervalo I que contiene a a y a x (x ≠ a).
2. **Polinomio y resto** (DEF). Pₙ(t) = Σₖ₌₀ⁿ f⁽ᵏ⁾(a)(t − a)ᵏ/k!  y  Rₙ(t) = f(t) − Pₙ(t).
3. **Derivadas coinciden en a** (MATCH). Pₙ⁽ᵏ⁾(a) = f⁽ᵏ⁾(a) para k = 0, …, n, luego Rₙ⁽ᵏ⁾(a) = 0 para k = 0, …, n.
4. **Lema del factorial** (FACT). Para todo r > 0: rⁿ⁺¹/(n+1)! → 0 cuando n → ∞ (el cociente entre términos consecutivos r/(n+2) → 0).
5. **Función auxiliar** (AUX). Sea K la constante con Rₙ(x) = K(x − a)ⁿ⁺¹/(n+1)! y g(t) = Rₙ(t) − K(t − a)ⁿ⁺¹/(n+1)!.
6. **Derivada (n+1)-ésima** (DERIV). Pₙ⁽ⁿ⁺¹⁾ ≡ 0 (grado n), luego g⁽ⁿ⁺¹⁾(t) = f⁽ⁿ⁺¹⁾(t) − K.
7. **Ceros de g** (AUXZ). g(x) = 0 por la elección de K, y g⁽ᵏ⁾(a) = 0 para k = 0, …, n.
8. **Rolle** (ROLLE1). g(a) = g(x) = 0 y g ∈ C¹ ⇒ por Rolle existe ξ₁ entre a y x con g'(ξ₁) = 0.
9. **Rolle iterado** (ROLLEN). g'(a) = g'(ξ₁) = 0 ⇒ existe ξ₂ con g''(ξ₂) = 0; repitiendo n+1 veces existe ξ con g⁽ⁿ⁺¹⁾(ξ) = 0.
10. **Resto de Lagrange** (LAGR). 0 = g⁽ⁿ⁺¹⁾(ξ) = f⁽ⁿ⁺¹⁾(ξ) − K ⇒ K = f⁽ⁿ⁺¹⁾(ξ), es decir Rₙ(x) = f⁽ⁿ⁺¹⁾(ξ)(x − a)ⁿ⁺¹/(n+1)!.
11. **Cota del resto** (BOUND). Si |f⁽ⁿ⁺¹⁾| ≤ M en I: |Rₙ(x)| ≤ M|x − a|ⁿ⁺¹/(n+1)!.
12. **Convergencia de la serie** (CONV). Si |f⁽ᵏ⁾| ≤ M en I para todo k, entonces |Rₙ(x)| ≤ M|x − a|ⁿ⁺¹/(n+1)! → 0 y Σ f⁽ᵏ⁾(a)(x − a)ᵏ/k! = f(x).
13. **Conclusión** (QED). f(x) = Pₙ(x) + f⁽ⁿ⁺¹⁾(ξ)(x − a)ⁿ⁺¹/(n+1)!, y con derivadas uniformemente acotadas la serie de Taylor converge a f. ∎