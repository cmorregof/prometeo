# NewtonRL · informe de aprendizaje

Generado: 2026-09-25 14:49 · semilla 0 · tolerancia 1e-09 · tiempo total **0.2 s**
(fase 1: 0.1 s, fase 2: 0.1 s).

## Síntesis: cómo aprendió

**Fase 1 (Newton con salvaguardas).** El agente conoce el paso de Newton pero no cuándo es seguro darlo entero. Solo observa la reducción del residuo ρ = |f(xₙ)|/|f(xₙ₋₁)| y si el paso propuesto crece o decrece, y elige entre paso completo, amortiguado (½, ¼) o retroceder con búsqueda lineal. En las primeras 100 generaciones convergió el 93 % de las veces (Newton puro converge ~73 % en este banco: arctan diverge desde |x₀| > 1.39, ∛x diverge desde cualquier x₀, ln x salta fuera del dominio, x·e^(−x²) cicla). En la generación 33 fijó que, cuando el residuo cae rápido, el paso completo es el mejor: es la cuenca de convergencia cuadrática. En la 29 aprendió a rechazar los pasos que empeoran |f| y retroceder con búsqueda lineal: Newton amortiguado. Desde la 106 el orden de convergencia observado en sus últimas iteraciones es ≈ 2.25: los dígitos correctos se duplican en cada paso, tal como predice el teorema. Su ley final coincide con Armijo en 5/7 estados bien visitados (ρ<0.05    paso decrece → paso completo λ=1; 0.05–0.5  paso decrece → paso completo λ=1; 0.05–0.5  paso crece → paso completo λ=1; 0.5–1     paso decrece → paso λ=1/4; 0.5–1     paso crece → paso completo λ=1; ρ≥1       paso decrece → paso completo λ=1; ρ≥1       paso crece → retroceder y dar medio paso). Y descubrió un matiz que la regla no contempla (gen 1236): si el paso de Newton propuesto ya decrece, dar el paso completo es más barato que la búsqueda lineal, que cuesta varias evaluaciones. Desde la generación 111 converge en ≥ 95 % de los casos. Total: 2859 convergencias, 15 divergencias y 126 episodios agotados en 3000 generaciones (0.1 s); media final de 9.2 evaluaciones por convergencia.

**Fase 2 (demostración).** Los pasos se asentaron en la política en este orden: H1 (gen 6), TAYLOR (gen 7), DEF (gen 15), ERRID (gen 15), NBHD (gen 15), QUAD (gen 15), CONV (gen 28), DELTA (gen 28), INV (gen 28), ORDER (gen 28), QED (gen 125). El último fue QED (gen 125); la conclusión tiene profundidad 9. Primera demostración completa en la generación 102, primera sin saltos lógicos en la 353, primera mínima (11 pasos) en la 353. La política voraz produce la demostración mínima desde la generación 125. Cometió 8291 saltos lógicos, 3402 con distractores: «Newton converge desde cualquier x₀» fue intentado 485 veces, «con raíz múltiple sigue siendo cuadrático» 506 veces y el non sequitur de Bolzano 490 veces; todos quedaron descartados. Total: 2779 demostraciones completas y 1752 mínimas en 3000 generaciones (0.1 s).

**Lectura.** Las dos fases se explican mutuamente. El teorema dice que Newton es cuadrático *cerca* de una raíz simple: la identidad del error sale del resto de Lagrange (proyecto 03) y el entorno seguro exige f' ≠ 0. La fase 1 muestra exactamente los dos lados: dentro de la cuenca el agente da pasos completos y ve duplicarse los dígitos; fuera de ella (arctan lejos, ∛x con f' infinita en la raíz, ln x fuera del dominio) el paso completo destruye la convergencia y hace falta amortiguar. Tiempo total: 0.2 s.

## Demostración final (política voraz, sin exploración)

**Teorema (convergencia cuadrática local de Newton).** Sea f ∈ C² en un entorno de r con f(r) = 0 y f'(r) ≠ 0. Existe δ > 0 tal
que para todo x₀ con |x₀ − r| ≤ δ la sucesión xₙ₊₁ = xₙ − f(xₙ)/f'(xₙ) converge a r y |xₙ₊₁ − r| ≤ (M/2m)·|xₙ − r|².

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

## Fase 1 · ley de control aprendida (5/7 estados coinciden con Armijo; orden observado 2.25)

Acciones: `λ1` paso completo, `λ½` y `λ¼` amortiguados, `↩` retroceder con búsqueda lineal.

| ρ = |f(xₙ)|/|f(xₙ₋₁)| | paso propuesto | acción aprendida | Armijo (c = ½) | | visitas |
|---|---|---|---|---|---|
| ρ<0.05 | decrece | λ1 | λ1 | ✔ | 4561 |
| ρ<0.05 | crece | ? | λ1 | — | 0 |
| 0.05–0.5 | decrece | λ1 | λ1 | ✔ | 8407 |
| 0.05–0.5 | crece | λ1 | λ1 | ✔ | 168 |
| 0.5–1 | decrece | λ¼ | ↩/λ½/λ¼ | ✔ | 3826 |
| 0.5–1 | crece | λ1 | ↩/λ½/λ¼ | ✘ (matiz) | 8601 |
| ρ≥1 | decrece | λ1 | ↩/λ½/λ¼ | ✘ (matiz) | 362 |
| ρ≥1 | crece | ↩ | ↩/λ½/λ¼ | ✔ | 4199 |

Convergencias: 2859 · divergencias: 15 · agotadas: 126
· éxito final (100 últimas): 96 % · evaluaciones medias: 9.2

## Fase 2 · orden en que se asentó cada paso

| paso | título | profundidad | 1ª vez válido (gen) | entra en política voraz (gen) | usos |
|---|---|---|---|---|---|
| H1 | Hipótesis | 0 | 1 | 6 | 2779 |
| TAYLOR | Taylor (n = 1) | 1 | 1 | 7 | 2779 |
| NBHD | Entorno seguro | 1 | 1 | 15 | 2779 |
| DEF | Definición | 2 | 2 | 15 | 2779 |
| ERRID | Identidad del error | 3 | 32 | 15 | 2779 |
| QUAD | Cota cuadrática | 4 | 38 | 15 | 2779 |
| DELTA | Elección de δ | 5 | 53 | 28 | 2779 |
| INV | Invariante | 6 | 65 | 28 | 2779 |
| CONV | Convergencia | 7 | 68 | 28 | 2779 |
| ORDER | Orden 2 | 8 | 92 | 28 | 2779 |
| QED | Conclusión | 9 | — | 125 | 2779 |

Saltos lógicos más frecuentes:

| paso | tipo | intentos inválidos |
|---|---|---|
| D_MULT | Falso | 506 |
| D_LINEAR | Insuficiente | 502 |
| DELTA | Elección de δ | 490 |
| D_BOLZ | Non sequitur | 490 |
| D_GLOBAL | Error clásico | 485 |
| D_MONO | Insuficiente | 476 |
| QED | Conclusión | 476 |
| D_FP0 | Absurdo | 475 |

Demostraciones completas: 2779 · mínimas: 1752 · mejor retorno: +14.50 (gen 353).

## Bitácora de hitos

| fase | generación | tiempo | hito |
|---|---|---|---|
| 1 | 1 | 0.0 s | primera convergencia: x·e^{−x²} desde x₀ = 0.41 con 11 evaluaciones |
| 1 | 29 | 0.0 s | aprendió a rechazar los pasos que empeoran |f| y retroceder con búsqueda lineal (Newton amortiguado) |
| 1 | 33 | 0.0 s | aprendió que cuando el residuo cae rápido el paso completo de Newton es el mejor (cuenca cuadrática) |
| 1 | 106 | 0.0 s | orden de convergencia observado ≈ 1.70: los dígitos correctos se duplican (convergencia cuadrática) |
| 1 | 111 | 0.0 s | ≥95 % de convergencia en las últimas 100 generaciones (Newton puro: ~73 %) |
| 1 | 1236 | 0.1 s | matiz que Armijo no contempla: si el paso de Newton propuesto ya decrece, el paso completo es más barato que la búsqueda lineal |
| 1 | 3000 | 0.1 s | fase 1 terminada: 2859 convergencias, 15 divergencias, 126 agotadas |
| 2 | 1 | 0.1 s | primer paso válido: Hipótesis (H1) |
| 2 | 102 | 0.1 s | ¡primera demostración completa! 11 pasos, 13 saltos lógicos |
| 2 | 125 | 0.1 s | la política voraz (sin exploración) ya produce la demostración mínima |
| 2 | 353 | 0.2 s | primera demostración sin ningún salto lógico |
| 2 | 353 | 0.2 s | primera demostración mínima (11 pasos, sin desvíos) |
| 2 | 3000 | 0.2 s | fase 2 terminada: 2779 demostraciones completas, 1752 mínimas |
