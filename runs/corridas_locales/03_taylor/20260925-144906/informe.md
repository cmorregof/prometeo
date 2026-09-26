# TaylorRL · informe de aprendizaje

Generado: 2026-09-25 14:49 · semilla 0 · tolerancia 1e-06 · tiempo total **0.2 s**
(fase 1: 0.1 s, fase 2: 0.1 s).

## Síntesis: cómo aprendió

**Fase 1 (serie de Taylor).** El agente suma términos de la serie en 0 para calcular f(x*) sin conocer f ni su radio de convergencia; solo ve el tamaño del último término frente a la tolerancia y el cociente entre términos consecutivos. En sus primeras 100 generaciones acertó el 21 % de las veces: paraba demasiado pronto o seguía sumando series que no convergen. En la generación 226 descubrió el criterio del cociente: si |tₙ/tₙ₋₁| ≥ 1 de forma sostenida (no solo al principio, donde eˣ con x = 2.5 también crece), la serie no converge y hay que abandonar. En la 213 fijó el criterio del último término: parar cuando |tₙ| ≪ tol y los términos decrecen, que es la cota de la cola geométrica |tₙ|·q/(1 − q). Desde la 898 su ley coincide con la teoría en todos los estados bien visitados. Desde la generación 1390 acierta en ≥ 95 % de los casos. Total: 1352 aproximaciones correctas, 1104 divergencias detectadas, 544 veredictos erróneos en 3000 generaciones (0.1 s); media final de 9.7 términos por aproximación.

**Fase 2 (demostración).** Los pasos se asentaron en la política en este orden: FACT (gen 1), H1 (gen 1), DEF (gen 2), AUX (gen 20), DERIV (gen 20), AUXZ (gen 21), MATCH (gen 21), ROLLE1 (gen 100), ROLLEN (gen 100), BOUND (gen 125), LAGR (gen 125), CONV (gen 250), QED (gen 250). El último fue QED (gen 250); la conclusión tiene profundidad 9 en el grafo (Rolle iterado es la cadena larga), así que su valor solo se propaga hacia atrás una vez recorrida entera. Primera demostración completa en la generación 194, primera sin saltos lógicos en la 322, primera mínima (13 pasos) en la 322. La política voraz produce la demostración mínima desde la generación 250. Cometió 8262 saltos lógicos, 3048 con distractores: «f ∈ C^∞ luego su serie converge a f» fue intentado 443 veces, «los términos tienden a 0 luego la serie converge» 447 veces y el non sequitur del teorema del valor medio 450 veces; todos quedaron descartados. Total: 2783 demostraciones completas y 1664 mínimas en 3000 generaciones (0.1 s).

**Lectura.** En la práctica, el agente descubrió que lo que decide si una serie sirve es el cociente entre términos (d'Alembert) y que el último término, junto con ese cociente, acota la cola. En la teoría, aprendió que el resto de Lagrange sale de aplicar Rolle n+1 veces a una función auxiliar, y que la serie converge a f solo cuando ese resto tiende a 0, cosa que ni la suavidad C^∞ ni el hecho de que los términos se hagan pequeños garantizan. Este resto es justo lo que necesitará Newton en el proyecto 04. Tiempo total: 0.2 s.

## Demostración final (política voraz, sin exploración)

**Teorema (Taylor con resto de Lagrange).** Sea f ∈ Cⁿ⁺¹ en un intervalo que contiene a a y a x. Existe ξ entre a y x con
f(x) = Σₖ₌₀ⁿ f⁽ᵏ⁾(a)(x − a)ᵏ/k! + f⁽ⁿ⁺¹⁾(ξ)(x − a)ⁿ⁺¹/(n+1)!. Si |f⁽ᵏ⁾| ≤ M para todo k, la serie de Taylor converge a f(x).

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

## Fase 1 · ley aprendida (13/13 estados bien visitados coinciden con la teoría)

Acciones: `+` sumar el siguiente término, `■` parar y entregar, `✗` abandonar (la serie no converge).

| último término | cociente q | n | acción aprendida | teoría | |
|---|---|---|---|---|---|
| |t|<tol/100 | q<0.5 | n ≤ 4 | + | ■ | ✘ |
| |t|<tol/100 | 0.5≤q<1 | n ≤ 4 | ? | ■ | — |
| |t|<tol/100 | q≥1 | n ≤ 4 | ? | + | — |
| tol/100–tol | q<0.5 | n ≤ 4 | ■ | ■ | ✔ |
| tol/100–tol | 0.5≤q<1 | n ≤ 4 | ? | ■/+ | — |
| tol/100–tol | q≥1 | n ≤ 4 | ? | + | — |
| tol–100tol | q<0.5 | n ≤ 4 | + | + | ✔ |
| tol–100tol | 0.5≤q<1 | n ≤ 4 | ? | + | — |
| tol–100tol | q≥1 | n ≤ 4 | ? | + | — |
| |t|≥100tol | q<0.5 | n ≤ 4 | + | + | ✔ |
| |t|≥100tol | 0.5≤q<1 | n ≤ 4 | + | + | ✔ |
| |t|≥100tol | q≥1 | n ≤ 4 | + | + | ✔ |
| |t|<tol/100 | q<0.5 | n > 4 | ■ | ■ | ✔ |
| |t|<tol/100 | 0.5≤q<1 | n > 4 | ? | ■ | — |
| |t|<tol/100 | q≥1 | n > 4 | ? | ✗ | — |
| tol/100–tol | q<0.5 | n > 4 | ■ | ■ | ✔ |
| tol/100–tol | 0.5≤q<1 | n > 4 | ■ | ■/+ | ✔ |
| tol/100–tol | q≥1 | n > 4 | ? | ✗ | — |
| tol–100tol | q<0.5 | n > 4 | + | + | ✔ |
| tol–100tol | 0.5≤q<1 | n > 4 | + | + | ✔ |
| tol–100tol | q≥1 | n > 4 | ? | ✗ | — |
| |t|≥100tol | q<0.5 | n > 4 | + | + | ✔ |
| |t|≥100tol | 0.5≤q<1 | n > 4 | + | + | ✔ |
| |t|≥100tol | q≥1 | n > 4 | ✗ | ✗ | ✔ |

Aproximaciones correctas: 1352 · divergencias detectadas: 1104 · veredictos erróneos: 544
· agotadas: 0 · éxito final (100 últimas): 90 % · términos medios: 9.7

## Fase 2 · orden en que se asentó cada paso

| paso | título | profundidad | 1ª vez válido (gen) | entra en política voraz (gen) | usos |
|---|---|---|---|---|---|
| FACT | Lema del factorial | 0 | 1 | 1 | 2783 |
| H1 | Hipótesis | 0 | 1 | 1 | 2783 |
| DEF | Polinomio y resto | 1 | 2 | 2 | 2783 |
| AUX | Función auxiliar | 2 | 2 | 20 | 2783 |
| DERIV | Derivada (n+1)-ésima | 3 | 4 | 20 | 2783 |
| MATCH | Derivadas coinciden en a | 2 | 2 | 21 | 2783 |
| AUXZ | Ceros de g | 3 | 14 | 21 | 2783 |
| ROLLE1 | Rolle | 4 | 14 | 100 | 2783 |
| ROLLEN | Rolle iterado | 5 | 76 | 100 | 2783 |
| LAGR | Resto de Lagrange | 6 | 76 | 125 | 2783 |
| BOUND | Cota del resto | 7 | 145 | 125 | 2783 |
| CONV | Convergencia de la serie | 8 | 145 | 250 | 2783 |
| QED | Conclusión | 9 | — | 250 | 2783 |

Saltos lógicos más frecuentes:

| paso | tipo | intentos inválidos |
|---|---|---|
| QED | Conclusión | 453 |
| D_TVM | Non sequitur | 450 |
| LAGR | Resto de Lagrange | 450 |
| D_TERM | Falso | 447 |
| D_NEWTON | Otro método | 446 |
| D_BOLZ | Irrelevante | 443 |
| D_CINF | Error clásico | 443 |
| ROLLEN | Rolle iterado | 440 |

Demostraciones completas: 2783 · mínimas: 1664 · mejor retorno: +13.50 (gen 322).

## Bitácora de hitos

| fase | generación | tiempo | hito |
|---|---|---|---|
| 1 | 132 | 0.0 s | primera aproximación correcta: sin x en x* = 1.00 con 6 términos (óptimo 5) |
| 1 | 213 | 0.0 s | descubrió el criterio del último término: parar cuando |tₙ| ≪ tol y los términos decrecen |
| 1 | 226 | 0.0 s | descubrió el criterio del cociente: si |tₙ/tₙ₋₁| ≥ 1 de forma sostenida, la serie no converge |
| 1 | 898 | 0.0 s | su ley coincide con la teoría en los 11 estados visitados (estable 100 gen.) |
| 1 | 1390 | 0.0 s | ≥95 % de aciertos en las últimas 100 generaciones |
| 1 | 3000 | 0.1 s | fase 1 terminada: 1352 aproximaciones correctas, 1104 divergencias detectadas, 544 veredictos erróneos, 0 agotadas |
| 2 | 1 | 0.1 s | primer paso válido: Hipótesis (H1) |
| 2 | 194 | 0.1 s | ¡primera demostración completa! 13 pasos, 13 saltos lógicos |
| 2 | 250 | 0.1 s | la política voraz (sin exploración) ya produce la demostración mínima |
| 2 | 322 | 0.1 s | primera demostración sin ningún salto lógico |
| 2 | 322 | 0.1 s | primera demostración mínima (13 pasos, sin desvíos) |
| 2 | 3000 | 0.2 s | fase 2 terminada: 2783 demostraciones completas, 1664 mínimas |
