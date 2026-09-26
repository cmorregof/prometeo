# FixpointRL · informe de aprendizaje

Generado: 2026-09-25 14:49 · semilla 0 · tolerancia 1e-06 · tiempo total **0.3 s**
(fase 1: 0.1 s, fase 2: 0.1 s).

## Síntesis: cómo aprendió

**Fase 1 (punto fijo).** El agente empieza con un α arbitrario y solo observa la razón de residuos ρ = |f(xₙ₊₁)|/|f(xₙ)| y si la iteración oscila. En sus primeras 100 generaciones convergió el 25 % de las veces (un α fijo converge ~35 %). En la generación 2 aprendió que una divergencia monótona (ρ > 1 sin oscilar) significa que α tiene el signo equivocado y hay que invertirlo. En la 26 aprendió que oscilar es señal de que α es demasiado grande (|1 − αf'| > 1 con signo negativo) y hay que reducirlo. En la 1612 su ley de control coincidía con la teoría de Banach en los 12 estados observables y se mantuvo estable: ρ <0.25     monót. → mantener α; ρ <0.25     oscila → mantener α; ρ 0.5–0.8   monót. → doblar α; ρ 0.5–0.8   oscila → reducir α a la mitad; ρ 1–1.5     monót. → invertir signo de α. Es decir, el agente aprendió a mantener |g'| < 1 y a empujar ρ hacia 0, que es acercar α a 1/f'(r): el paso de Newton. Desde la generación 661 converge en ≥ 95 % de los casos. Total: 2667 convergencias, 218 divergencias y 115 episodios agotados en 3000 generaciones (0.1 s); media final de 11.7 iteraciones por convergencia.

**Fase 2 (demostración).** Los pasos se asentaron en la política en el orden en que sus dependencias quedaban disponibles: H1 (gen 1), H2 (gen 1), AUX (gen 8), DEF (gen 8), EXIST (gen 8), STEP (gen 10), UNIQ (gen 10), ERR (gen 100), GEO (gen 125), LIM (gen 150), PRIORI (gen 175), POST (gen 200), QED (gen 200). El último fue QED (gen 200); la conclusión tiene profundidad 7 en el grafo, así que su valor solo se propaga hacia atrás una vez recorrida la cadena completa. Primera demostración completa en la generación 193, primera sin saltos lógicos en la 440, primera mínima (13 pasos) en la 440. La política voraz produce la demostración mínima desde la generación 200. Cometió 8040 saltos lógicos, 3040 con distractores: el error clásico «|g'(p)| < 1 basta para cualquier x₀» fue intentado 422 veces y el non sequitur «existe punto fijo, luego la iteración converge» 452 veces; ambos quedaron descartados. Total: 2788 demostraciones completas y 1715 mínimas en 3000 generaciones (0.1 s).

**Lectura.** Las dos fases cuentan la misma historia desde lados distintos. En la práctica, el agente descubre que lo único que decide la convergencia es la constante de contracción empírica ρ ≈ |g'(r)| y aprende a fabricar un mapa contractivo ajustando α. En la teoría, aprende que la hipótesis de contracción (k < 1) es la que produce existencia y unicidad del punto fijo, la convergencia geométrica y las cotas de error, y que ni Bolzano, ni la acotación, ni |g'(p)| < 1 a solas la sustituyen. Tiempo total: 0.3 s.

## Demostración final (política voraz, sin exploración)

**Teorema (punto fijo de Banach en [a, b]).** Sea g continua en [a, b] con g([a, b]) ⊆ [a, b] y
|g(x) − g(y)| ≤ k·|x − y| con 0 ≤ k < 1. Entonces g tiene un único punto fijo p, la iteración xₙ₊₁ = g(xₙ)
converge a p para todo x₀ ∈ [a, b], |xₙ − p| ≤ kⁿ·max(x₀ − a, b − x₀) y |xₙ − p| ≤ kⁿ/(1 − k)·|x₁ − x₀|.

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

## Fase 1 · ley de control aprendida (12/12 estados coinciden con la teoría)

Acciones: `=` mantener α, `×2` doblar, `÷2` reducir a la mitad, `±` invertir el signo.

| ρ = |f(xₙ₊₁)|/|f(xₙ)| | forma | acción aprendida | teoría | |
|---|---|---|---|---|
| ρ <0.25 | monótona | = | = | ✔ |
| ρ <0.25 | oscila | = | = | ✔ |
| ρ 0.25–0.5 | monótona | = | =/×2 | ✔ |
| ρ 0.25–0.5 | oscila | ÷2 | =/÷2 | ✔ |
| ρ 0.5–0.8 | monótona | ×2 | ×2 | ✔ |
| ρ 0.5–0.8 | oscila | ÷2 | ÷2 | ✔ |
| ρ 0.8–1 | monótona | ×2 | ×2 | ✔ |
| ρ 0.8–1 | oscila | ÷2 | ÷2 | ✔ |
| ρ 1–1.5 | monótona | ± | ± | ✔ |
| ρ 1–1.5 | oscila | ÷2 | ÷2 | ✔ |
| ρ ≥1.5 | monótona | ± | ±/÷2 | ✔ |
| ρ ≥1.5 | oscila | ÷2 | ÷2 | ✔ |

Convergencias: 2667 · divergencias: 218 · agotadas: 115
· éxito final (100 últimas): 93 % · iteraciones medias: 11.7

## Fase 2 · orden en que se asentó cada paso

| paso | título | profundidad | 1ª vez válido (gen) | entra en política voraz (gen) | usos |
|---|---|---|---|---|---|
| H1 | Hipótesis 1 | 0 | 1 | 1 | 2788 |
| H2 | Hipótesis 2 | 0 | 2 | 1 | 2788 |
| AUX | Función auxiliar | 1 | 2 | 8 | 2788 |
| DEF | Definición | 1 | 2 | 8 | 2788 |
| EXIST | Existencia | 2 | 2 | 8 | 2788 |
| STEP | Pasos consecutivos | 2 | 16 | 10 | 2788 |
| UNIQ | Unicidad | 3 | 12 | 10 | 2788 |
| ERR | Contracción del error | 3 | 45 | 100 | 2788 |
| GEO | Decaimiento geométrico | 4 | 45 | 125 | 2788 |
| LIM | Convergencia | 5 | 45 | 150 | 2788 |
| PRIORI | Cota a priori | 5 | 45 | 175 | 2788 |
| POST | Cota a posteriori | 6 | 128 | 200 | 2788 |
| QED | Conclusión | 7 | — | 200 | 2788 |

Saltos lógicos más frecuentes:

| paso | tipo | intentos inválidos |
|---|---|---|
| D_BOLZ | Non sequitur | 452 |
| D_NEWTON | Otro método | 448 |
| QED | Conclusión | 443 |
| D_BOUND | Falso | 441 |
| D_K1 | Falso | 435 |
| D_MONO | Insuficiente | 434 |
| D_LOCAL | Error clásico | 422 |
| LIM | Convergencia | 421 |

Demostraciones completas: 2788 · mínimas: 1715 · mejor retorno: +13.50 (gen 440).

## Bitácora de hitos

| fase | generación | tiempo | hito |
|---|---|---|---|
| 1 | 2 | 0.0 s | aprendió que si diverge monótonamente el signo de α está mal: invertirlo |
| 1 | 26 | 0.0 s | aprendió que si oscila α es demasiado grande: reducirlo (|g'| < 1 es lo que importa) |
| 1 | 27 | 0.0 s | primera convergencia (28 iteraciones, f = -3.44(x−0.58) + 0.3(x−0.58)³) |
| 1 | 661 | 0.0 s | ≥95 % de convergencia en las últimas 100 generaciones |
| 1 | 1612 | 0.1 s | su ley de control coincide con la teoría de Banach en los 12 estados (estable 100 gen.) |
| 1 | 3000 | 0.1 s | fase 1 terminada: 2667 convergencias, 218 divergencias, 115 agotadas |
| 2 | 1 | 0.1 s | primer paso válido: Hipótesis 1 (H1) |
| 2 | 193 | 0.2 s | ¡primera demostración completa! 13 pasos, 16 saltos lógicos |
| 2 | 200 | 0.2 s | la política voraz (sin exploración) ya produce la demostración mínima |
| 2 | 440 | 0.2 s | primera demostración sin ningún salto lógico |
| 2 | 440 | 0.2 s | primera demostración mínima (13 pasos, sin desvíos) |
| 2 | 3000 | 0.3 s | fase 2 terminada: 2788 demostraciones completas, 1715 mínimas |
