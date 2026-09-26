# InterpRL · informe de aprendizaje

Generado: 2026-09-25 14:49 · semilla 0 · tolerancia 1e-05 · tiempo total **7.9 s**
(fase 1: 7.7 s, fase 2: 0.1 s).

## Síntesis: cómo aprendió

**Fase 1 (interpolación).** El agente elige una familia de nodos (γ = 0 equiespaciados … γ = 1 Chebyshev) y luego decide, nodo a nodo, si sigue o entrega, viendo solo la diferencia entre los dos últimos interpolantes. En sus primeras 100 generaciones acertó el 6 % de las veces. En la generación 55 fijó el criterio de parada: entregar cuando |pₙ − pₙ₋₁| es mucho menor que la tolerancia y va bajando, que es el estimador de error de cualquiera que no conoce f. En la 543 pasó a preferir de forma estable γ = 1, los nodos de Chebyshev: con equiespaciados las funciones tipo Runge empeoran al añadir nodos y el episodio se agota. Valores finales del bandido: Q(γ=0.00) = -19.4 (88 usos), Q(γ=0.25) = -7.9 (111 usos), Q(γ=0.50) = -10.4 (62 usos), Q(γ=0.75) = -10.6 (133 usos), Q(γ=1.00) = -1.5 (2606 usos). Desde la 431 su regla de parada coincide con la teoría en todos los estados bien visitados. Total: 2221 aproximaciones correctas, 758 entregas prematuras y 21 agotadas en 3000 generaciones (7.7 s); media final de 17.6 nodos.

**Fase 2 (demostración).** Los pasos se asentaron en la política en este orden: H2 (gen 1), DEFW (gen 2), FIX (gen 2), H1 (gen 2), EXIST (gen 5), CHEB (gen 21), AUX (gen 100), DERIV (gen 100), ZEROS (gen 125), ROLLE (gen 150), BOUND (gen 175), FORMULA (gen 175), QED (gen 225). El último fue QED (gen 225); la conclusión tiene profundidad 8 (la cadena larga es función auxiliar → ceros → Rolle iterado → fórmula → cota). Primera demostración completa en la generación 207, primera sin saltos lógicos en la 284, primera mínima (13 pasos) en la 284. La política voraz produce la demostración mínima desde la generación 225. Cometió 8458 saltos lógicos, 3433 con distractores: «más nodos ⇒ menos error» fue intentado 412 veces, «f continua ⇒ pₙ → f» 446, el non sequitur de Weierstrass 438 y la confusión con el resto de Taylor 454; todos quedaron descartados. Total: 2764 demostraciones completas y 1701 mínimas en 3000 generaciones (0.1 s).

**Lectura.** En la práctica, el agente descubrió que dónde se ponen los nodos importa más que cuántos: con nodos equiespaciados hay funciones para las que añadir nodos empeora (Runge), y con los de Chebyshev el error baja geométricamente. En la teoría, aprendió que el error es f⁽ⁿ⁺¹⁾(ξ)·w(x)/(n+1)! y que el único factor que los nodos controlan es máx|w|, que Chebyshev minimiza. Lo que la teoría clásica no da es el conjunto de nodos que minimiza la constante de Lebesgue: eso es la fase 3 (`python -m interprl search`), donde no hay grafo sino un verificador. Tiempo total: 7.9 s.

## Demostración final (política voraz, sin exploración)

**Teorema (error de interpolación).** Sea f ∈ Cⁿ⁺¹[a, b] y pₙ el interpolante en n + 1 nodos distintos. Para cada x existe ξ con
f(x) − pₙ(x) = f⁽ⁿ⁺¹⁾(ξ)·w(x)/(n+1)!, w(t) = ∏(t − xᵢ). Con nodos de Chebyshev en [−1, 1], máx|w| = 2⁻ⁿ es mínimo.

1. **Hipótesis 2** (H2). x₀ < x₁ < … < xₙ son n + 1 nodos distintos en [a, b].
2. **Existencia y unicidad** (EXIST). Existe un único pₙ de grado ≤ n con pₙ(xᵢ) = f(xᵢ): la base de Lagrange ℓᵢ lo construye y dos soluciones difieren en un polinomio de grado ≤ n con n + 1 ceros, luego nulo.
3. **Hipótesis 1** (H1). f ∈ Cⁿ⁺¹[a, b].
4. **Polinomio nodal** (DEFW). w(t) = ∏ᵢ₌₀ⁿ (t − xᵢ) tiene grado n + 1, coeficiente principal 1 y w⁽ⁿ⁺¹⁾ ≡ (n + 1)!.
5. **Fijar x** (FIX). Sea x ∈ [a, b] distinto de todos los nodos (si x = xᵢ ambos lados de la fórmula son 0). Entonces w(x) ≠ 0.
6. **Minimalidad de Chebyshev** (CHEB). En [−1, 1], entre todos los polinomios mónicos de grado n + 1, Tₙ₊₁/2ⁿ tiene la menor norma uniforme, 2⁻ⁿ; sus ceros son los nodos de Chebyshev y con ellos máx|w| = 2⁻ⁿ.
7. **Función auxiliar** (AUX). Sea g(t) = f(t) − pₙ(t) − [f(x) − pₙ(x)]·w(t)/w(x). Por H1, g ∈ Cⁿ⁺¹[a, b].
8. **n + 2 ceros** (ZEROS). g se anula en los n + 1 nodos (allí f = pₙ y w = 0) y en x (por construcción): n + 2 ceros distintos.
9. **Rolle iterado** (ROLLE). Entre dos ceros consecutivos de g hay un cero de g′ (Rolle): g′ tiene ≥ n + 1 ceros, g″ ≥ n, …, g⁽ⁿ⁺¹⁾ tiene al menos un cero ξ ∈ (a, b).
10. **Derivada n + 1** (DERIV). pₙ⁽ⁿ⁺¹⁾ ≡ 0 (grado ≤ n) y w⁽ⁿ⁺¹⁾ ≡ (n + 1)!, luego g⁽ⁿ⁺¹⁾(t) = f⁽ⁿ⁺¹⁾(t) − [f(x) − pₙ(x)]·(n + 1)!/w(x).
11. **Fórmula del error** (FORMULA). Evaluando en ξ: 0 = f⁽ⁿ⁺¹⁾(ξ) − [f(x) − pₙ(x)]·(n + 1)!/w(x), es decir f(x) − pₙ(x) = f⁽ⁿ⁺¹⁾(ξ)·w(x)/(n + 1)!.
12. **Cota uniforme** (BOUND). Con M = máx|f⁽ⁿ⁺¹⁾|: máx_{[a,b]} |f − pₙ| ≤ M · máx|w| / (n + 1)!. El único factor que depende de los nodos es máx|w|.
13. **Conclusión** (QED). Con nodos de Chebyshev, máx|f − pₙ| ≤ M / (2ⁿ (n + 1)!), y ninguna otra elección de nodos mejora el factor máx|w|. ∎

## Fase 1 · familia de nodos aprendida

| γ | Q(γ) = retorno medio del episodio | usos | mejor |
|---|---|---|---|
| 0.00 | -19.35 | 88 |  |
| 0.25 | -7.94 | 111 |  |
| 0.50 | -10.42 | 62 |  |
| 0.75 | -10.58 | 133 |  |
| 1.00 | -1.50 | 2606 | ★ |

γ = 0 son nodos equiespaciados; γ = 1, Chebyshev–Lobatto. Por qué gana Chebyshev, en números (independientes del agente):

| n | Λ equiespaciados | Λ Chebyshev | máx\|w\| equiespaciados | máx\|w\| Chebyshev |
|---|---|---|---|---|
| 4 | 2.208 | 1.799 | 1.13e-01 | 1.16e-01 |
| 8 | 10.946 | 2.275 | 1.88e-02 | 7.66e-03 |
| 12 | 89.325 | 2.539 | 4.01e-03 | 4.84e-04 |
| 16 | 934.534 | 2.725 | 9.43e-04 | 3.04e-05 |
| 24 | 137851.979 | 2.984 | 5.98e-05 | 1.19e-07 |

## Fase 1 · regla de parada aprendida (9/9 estados bien visitados coinciden con la teoría)

Acciones: `+` añadir un nodo, `■` parar y entregar. Estimador: est = máx|pₙ − pₙ₋₁| / escala.

| estimador | tendencia | n | acción aprendida | teoría | |
|---|---|---|---|---|---|
| est<tol/100 | baja | n ≤ 6 | ? | ■ | — |
| est<tol/100 | sube | n ≤ 6 | ? | ■/+ | — |
| tol/100–tol | baja | n ≤ 6 | ■ | ■/+ | ✔ |
| tol/100–tol | sube | n ≤ 6 | ? | + | — |
| tol–100tol | baja | n ≤ 6 | + | + | ✔ |
| tol–100tol | sube | n ≤ 6 | ? | + | — |
| est≥100tol | baja | n ≤ 6 | + | + | ✔ |
| est≥100tol | sube | n ≤ 6 | + | + | ✔ |
| est<tol/100 | baja | n > 6 | ■ | ■ | ✔ |
| est<tol/100 | sube | n > 6 | ? | ■/+ | — |
| tol/100–tol | baja | n > 6 | ■ | ■/+ | ✔ |
| tol/100–tol | sube | n > 6 | + | + | ✔ |
| tol–100tol | baja | n > 6 | + | + | ✔ |
| tol–100tol | sube | n > 6 | + | + | ✔ |
| est≥100tol | baja | n > 6 | + | + | ✔ |
| est≥100tol | sube | n > 6 | + | + | ✔ |

Aproximaciones correctas: 2221 · entregas prematuras: 758 · agotadas: 21
· éxito final (100 últimas): 88 % · nodos medios: 17.6

## Fase 2 · orden en que se asentó cada paso

| paso | título | profundidad | 1ª vez válido (gen) | entra en política voraz (gen) | usos |
|---|---|---|---|---|---|
| H2 | Hipótesis 2 | 0 | 2 | 1 | 2764 |
| H1 | Hipótesis 1 | 0 | 1 | 2 | 2764 |
| DEFW | Polinomio nodal | 1 | 2 | 2 | 2764 |
| FIX | Fijar x | 2 | 10 | 2 | 2764 |
| EXIST | Existencia y unicidad | 1 | 2 | 5 | 2764 |
| CHEB | Minimalidad de Chebyshev | 2 | 10 | 21 | 2764 |
| AUX | Función auxiliar | 3 | 47 | 100 | 2764 |
| DERIV | Derivada n + 1 | 4 | 47 | 100 | 2764 |
| ZEROS | n + 2 ceros | 4 | 65 | 125 | 2764 |
| ROLLE | Rolle iterado | 5 | 65 | 150 | 2764 |
| FORMULA | Fórmula del error | 6 | 142 | 175 | 2764 |
| BOUND | Cota uniforme | 7 | 179 | 175 | 2764 |
| QED | Conclusión | 8 | — | 225 | 2764 |

Saltos lógicos más frecuentes:

| paso | tipo | intentos inválidos |
|---|---|---|
| D_TAYLOR | Distractor | 454 |
| D_CONT | Distractor | 446 |
| QED | Conclusión | 439 |
| D_WEIER | Non sequitur | 438 |
| D_NEWTON | Distractor | 431 |
| FORMULA | Fórmula del error | 431 |
| ZEROS | n + 2 ceros | 430 |
| D_EQUI | Distractor | 427 |

Demostraciones completas: 2764 · mínimas: 1701 · mejor retorno: +13.50 (gen 284).

## Fase 3 · lo que la teoría no da

El teorema dice que Chebyshev minimiza máx|w|, pero no qué nodos minimizan la constante de Lebesgue Λ (la amplificación
del error en los datos). Eso solo se conoce numéricamente. `python -m interprl search --n 8` busca nodos con Λ menor que
la de Chebyshev extendido usando el verificador `lebesgue_constant`, y `verify` recalcula el resultado con otra malla.

## Bitácora de hitos

| fase | generación | tiempo | hito |
|---|---|---|---|
| 1 | 1 | 0.0 s | primera aproximación correcta: e^(0.6x) con n = 8 (γ = 0.75); óptimo con Chebyshev n = 5 |
| 1 | 55 | 0.0 s | descubrió el criterio de parada: entregar cuando |pₙ − pₙ₋₁| ≪ tol y va bajando |
| 1 | 431 | 0.4 s | su regla coincide con la teoría en los 8 estados visitados (estable 100 gen.) |
| 1 | 543 | 0.6 s | prefiere γ = 1 de forma estable: nodos de Chebyshev (Q = -5.1 frente a -12.3 con equiespaciados) |
| 1 | 3000 | 7.7 s | fase 1 terminada: 2221 aproximaciones correctas, 758 entregas prematuras, 21 agotadas |
| 2 | 1 | 7.7 s | primer paso válido: Hipótesis 1 (H1) |
| 2 | 207 | 7.7 s | ¡primera demostración completa! 13 pasos, 14 saltos lógicos |
| 2 | 225 | 7.7 s | la política voraz (sin exploración) ya produce la demostración mínima |
| 2 | 284 | 7.8 s | primera demostración sin ningún salto lógico |
| 2 | 284 | 7.8 s | primera demostración mínima (13 pasos, sin desvíos) |
| 2 | 3000 | 7.9 s | fase 2 terminada: 2764 demostraciones completas, 1701 mínimas |
