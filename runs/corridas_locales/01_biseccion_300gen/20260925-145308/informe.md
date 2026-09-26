# BisectRL · informe de aprendizaje

Generado: 2026-09-25 14:53 · semilla 1 · tolerancia 0.001 · tiempo total **0.0 s**
(fase 1: 0.0 s, fase 2: 0.0 s).

## Síntesis: cómo aprendió

**Fase 1 (bisección).** En las primeras 100 generaciones el agente convergió solo 15 veces: cortaba en fracciones arbitrarias y con frecuencia conservaba el subintervalo equivocado, perdiendo la raíz. No llegó a fijar por completo la regla de conservación. El corte λ = 1/2 no se estabilizó como el mejor. Total: 130 convergencias y 170 raíces perdidas en 300 generaciones (0.0 s).

**Fase 2 (demostración).** Los primeros pasos válidos fueron las hipótesis, que no dependen de nada; después el agente fue asentando lemas en el orden en que sus dependencias quedaban disponibles: H1 (gen 2), H2 (gen 2), CONV_A (gen 16), CONV_B (gen 16), DEF (gen 16), INV (gen 16), MONO_A (gen 16), MONO_B (gen 16), WIDTH (gen 18), CONT (gen 175), MID (gen 175), SAME (gen 175), QED (gen 300), ROOT (gen 300). El último paso en entrar en la política fue ROOT (gen 300); el paso más profundo del grafo de dependencias es QED (profundidad 7), lo que explica por qué la conclusión se aprende al final: su valor solo se propaga hacia atrás una vez que la cadena completa ha sido recorrida. La primera demostración completa apareció en la generación 256, La política voraz produce la demostración mínima desde la generación 300. En total cometió 6652 saltos lógicos, 2548 de ellos con lemas distractores; el non sequitur «por Bolzano existe raíz, luego el método converge» fue intentado 355 veces y quedó descartado por su recompensa negativa. Total: 9 demostraciones completas y 0 mínimas en 300 generaciones (0.0 s).

**Lectura.** Nada del método ni de la demostración estaba programado como regla: solo la recompensa (progreso por evaluación, penalización por perder el cambio de signo, coste por línea y bono por ∎) y un verificador de dependencias. Con eso, una tabla Q descubrió el punto medio, el invariante de Bolzano y el orden lógico monotonía → convergencia → mismo límite → continuidad → raíz → cota → ∎. Tiempo total: 0.0 s.

## Demostración final (política voraz, sin exploración)

**Teorema.** Sea f continua en [a, b] con f(a)·f(b) < 0. Las sucesiones de la bisección satisfacen
mₙ → c con f(c) = 0 y |mₙ − c| ≤ (b − a)/2ⁿ⁺¹.

1. **Hipótesis 2** (H2). f(a) · f(b) < 0 (cambio de signo).
2. **Definición** (DEF). Sea a₀ = a, b₀ = b, mₙ = (aₙ + bₙ)/2. Si f(aₙ)·f(mₙ) ≤ 0 tomar [aₙ₊₁, bₙ₊₁] = [aₙ, mₙ]; si no, [mₙ, bₙ].
3. **Monotonía de aₙ** (MONO_A). (aₙ) es no decreciente y acotada superiormente por b.
4. **Convergencia de aₙ** (CONV_A). Toda sucesión monótona y acotada converge: aₙ → α.
5. **Monotonía de bₙ** (MONO_B). (bₙ) es no creciente y acotada inferiormente por a.
6. **Invariante** (INV). Por inducción sobre n: f(aₙ) · f(bₙ) ≤ 0 para todo n (el cambio de signo nunca se pierde).
7. **Hipótesis 1** (H1). f es continua en [a, b].
8. **Convergencia de bₙ** (CONV_B). Análogamente bₙ → β.
9. **Longitud** (WIDTH). Cada paso divide la longitud a la mitad: bₙ − aₙ = (b − a) / 2ⁿ.
10. **Mismo límite** (SAME). β − α = lim (bₙ − aₙ) = lim (b − a)/2ⁿ = 0, luego α = β =: c.
11. **Continuidad** (CONT). Por continuidad de f: f(aₙ) · f(bₙ) → f(c) · f(c) = f(c)².
12. **Raíz** (ROOT). El límite de una sucesión ≤ 0 es ≤ 0: f(c)² ≤ 0, así que f(c) = 0.
13. **Cota de error** (MID). c ∈ [aₙ, bₙ] para todo n, luego |mₙ − c| ≤ (bₙ − aₙ)/2 = (b − a)/2ⁿ⁺¹.
14. **Conclusión** (QED). Por tanto mₙ → c, f(c) = 0 y el error decrece geométricamente. ∎

## Fase 1 · política de corte aprendida

| λ | Q(λ) = progreso medio − 1 | mejor |
|---|---|---|
| 0.1 | -0.534 |  |
| 0.2 | -0.253 |  |
| 0.3 | -0.122 |  |
| 0.4 | -0.017 |  |
| 0.5 | -0.000 | ★ |
| 0.6 | -0.087 |  |
| 0.7 | -0.107 |  |
| 0.8 | -0.284 |  |
| 0.9 | -0.487 |  |

Regla de conservación (signos de f(a), f(x), f(b) → lado conservado):

| signos | lado | ¿preserva el cambio de signo? |
|---|---|---|
| (−, −, +) | der | ✔ |
| (−, +, +) | izq | ✔ |
| (+, −, −) | izq | ✔ |
| (+, +, −) | der | ✔ |

Convergencias: 130 · raíces perdidas: 170 · éxito final (100 últimas): 74 %
· iteraciones / óptimo (100 últimas): 1.10

## Fase 2 · orden en que se asentó cada paso

| paso | título | profundidad | 1ª vez válido (gen) | entra en política voraz (gen) | usos en demostraciones |
|---|---|---|---|---|---|
| H1 | Hipótesis 1 | 0 | 1 | 2 | 9 |
| H2 | Hipótesis 2 | 0 | 1 | 2 | 9 |
| DEF | Definición | 1 | 2 | 16 | 9 |
| MONO_A | Monotonía de aₙ | 2 | 2 | 16 | 9 |
| MONO_B | Monotonía de bₙ | 2 | 3 | 16 | 9 |
| INV | Invariante | 2 | 2 | 16 | 9 |
| CONV_B | Convergencia de bₙ | 3 | 36 | 16 | 9 |
| CONV_A | Convergencia de aₙ | 3 | 2 | 16 | 9 |
| WIDTH | Longitud | 2 | 2 | 18 | 9 |
| SAME | Mismo límite | 4 | 83 | 175 | 9 |
| MID | Cota de error | 5 | 174 | 175 | 9 |
| CONT | Continuidad | 5 | 174 | 175 | 9 |
| ROOT | Raíz | 6 | 198 | 300 | 9 |
| QED | Conclusión | 7 | — | 300 | 9 |

Saltos lógicos más frecuentes:

| paso | tipo | intentos inválidos |
|---|---|---|
| D_DERIV | Distractor | 385 |
| D_NEWTON | Distractor | 377 |
| D_UNIQ | Distractor | 371 |
| QED | Conclusión | 361 |
| D_DIV | Distractor | 359 |
| SAME | Mismo límite | 357 |
| D_BOLZ | Non sequitur | 355 |
| D_LIP | Distractor | 354 |

Demostraciones completas: 9 · mínimas: 0 · mejor retorno: +5.00 (gen 268).

## Bitácora de hitos

| fase | generación | tiempo | hito |
|---|---|---|---|
| 1 | 7 | 0.0 s | primera convergencia (15 iteraciones, f = sin(1.38x) − 0.72) |
| 1 | 300 | 0.0 s | fase 1 terminada: 130 convergencias, 170 raíces perdidas |
| 2 | 1 | 0.0 s | primer paso válido: Hipótesis 2 (H2) |
| 2 | 256 | 0.0 s | ¡primera demostración completa! 14 pasos, 13 saltos lógicos |
| 2 | 300 | 0.0 s | la política voraz (sin exploración) ya produce la demostración mínima |
| 2 | 300 | 0.0 s | fase 2 terminada: 9 demostraciones completas, 0 mínimas |
