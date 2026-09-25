1. **Hipótesis 2** (H2). f(a) · f(b) < 0 (cambio de signo).
2. **Definición** (DEF). Sea a₀ = a, b₀ = b, mₙ = (aₙ + bₙ)/2. Si f(aₙ)·f(mₙ) ≤ 0 tomar [aₙ₊₁, bₙ₊₁] = [aₙ, mₙ]; si no, [mₙ, bₙ].
3. **Monotonía de bₙ** (MONO_B). (bₙ) es no creciente y acotada inferiormente por a.
4. **Hipótesis 1** (H1). f es continua en [a, b].
5. **Longitud** (WIDTH). Cada paso divide la longitud a la mitad: bₙ − aₙ = (b − a) / 2ⁿ.
6. **Monotonía de aₙ** (MONO_A). (aₙ) es no decreciente y acotada superiormente por b.
7. **Invariante** (INV). Por inducción sobre n: f(aₙ) · f(bₙ) ≤ 0 para todo n (el cambio de signo nunca se pierde).
8. **Convergencia de aₙ** (CONV_A). Toda sucesión monótona y acotada converge: aₙ → α.
9. **Convergencia de bₙ** (CONV_B). Análogamente bₙ → β.
10. **Mismo límite** (SAME). β − α = lim (bₙ − aₙ) = lim (b − a)/2ⁿ = 0, luego α = β =: c.
11. **Continuidad** (CONT). Por continuidad de f: f(aₙ) · f(bₙ) → f(c) · f(c) = f(c)².
12. **Raíz** (ROOT). El límite de una sucesión ≤ 0 es ≤ 0: f(c)² ≤ 0, así que f(c) = 0.
13. **Cota de error** (MID). c ∈ [aₙ, bₙ] para todo n, luego |mₙ − c| ≤ (bₙ − aₙ)/2 = (b − a)/2ⁿ⁺¹.
14. **Conclusión** (QED). Por tanto mₙ → c, f(c) = 0 y el error decrece geométricamente. ∎