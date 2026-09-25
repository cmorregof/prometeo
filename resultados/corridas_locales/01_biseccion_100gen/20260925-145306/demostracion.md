1. **Hipótesis 2** (H2). f(a) · f(b) < 0 (cambio de signo).
2. **Definición** (DEF). Sea a₀ = a, b₀ = b, mₙ = (aₙ + bₙ)/2. Si f(aₙ)·f(mₙ) ≤ 0 tomar [aₙ₊₁, bₙ₊₁] = [aₙ, mₙ]; si no, [mₙ, bₙ].
3. **Monotonía de bₙ** (MONO_B). (bₙ) es no creciente y acotada inferiormente por a.
4. **Longitud** (WIDTH). Cada paso divide la longitud a la mitad: bₙ − aₙ = (b − a) / 2ⁿ.
   - ✗ *salto lógico:* Por Bolzano existe c con f(c) = 0; luego mₙ → c.  (¡existencia no implica convergencia!)
   - ✗ *salto lógico:* Por continuidad de f: f(aₙ) · f(bₙ) → f(c) · f(c) = f(c)².
   - ✗ *salto lógico:* (bₙ) es no creciente y acotada inferiormente por a.
   - ✗ *salto lógico:* Por Bolzano existe c con f(c) = 0; luego mₙ → c.  (¡existencia no implica convergencia!)
   - ✗ *salto lógico:* Cada paso divide la longitud a la mitad: bₙ − aₙ = (b − a) / 2ⁿ.
   - ✗ *salto lógico:* Por continuidad de f: f(aₙ) · f(bₙ) → f(c) · f(c) = f(c)².
   - ✗ *salto lógico:* Por continuidad de f: f(aₙ) · f(bₙ) → f(c) · f(c) = f(c)².
   - ✗ *salto lógico:* β − α = lim (bₙ − aₙ) = lim (b − a)/2ⁿ = 0, luego α = β =: c.
   - ✗ *salto lógico:* (bₙ) es no creciente y acotada inferiormente por a.
   - ✗ *salto lógico:* Por continuidad de f: f(aₙ) · f(bₙ) → f(c) · f(c) = f(c)².
   - ✗ *salto lógico:* Por Bolzano existe c con f(c) = 0; luego mₙ → c.  (¡existencia no implica convergencia!)
5. **Monotonía de aₙ** (MONO_A). (aₙ) es no decreciente y acotada superiormente por b.
   - ✗ *salto lógico:* El límite de una sucesión ≤ 0 es ≤ 0: f(c)² ≤ 0, así que f(c) = 0.
   - ✗ *salto lógico:* β − α = lim (bₙ − aₙ) = lim (b − a)/2ⁿ = 0, luego α = β =: c.
6. **Convergencia de aₙ** (CONV_A). Toda sucesión monótona y acotada converge: aₙ → α.
   - ✗ *salto lógico:* La sucesión (aₙ) diverge a +∞.
7. **Convergencia de bₙ** (CONV_B). Análogamente bₙ → β.
8. **Hipótesis 1** (H1). f es continua en [a, b].
   - ✗ *salto lógico:* Por Bolzano existe c con f(c) = 0; luego mₙ → c.  (¡existencia no implica convergencia!)
9. **Mismo límite** (SAME). β − α = lim (bₙ − aₙ) = lim (b − a)/2ⁿ = 0, luego α = β =: c.
10. **Invariante** (INV). Por inducción sobre n: f(aₙ) · f(bₙ) ≤ 0 para todo n (el cambio de signo nunca se pierde).
11. **Continuidad** (CONT). Por continuidad de f: f(aₙ) · f(bₙ) → f(c) · f(c) = f(c)².
   - ✗ *salto lógico:* La sucesión (aₙ) diverge a +∞.
   - ✗ *salto lógico:* Cada paso divide la longitud a la mitad: bₙ − aₙ = (b − a) / 2ⁿ.
   - ✗ *salto lógico:* f(a) · f(b) < 0 (cambio de signo).
   - ✗ *salto lógico:* (bₙ) es no creciente y acotada inferiormente por a.