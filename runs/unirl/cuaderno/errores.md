# Errores frecuentes al escribir pruebas en Isabelle

Cada nombre marcado como inexistente se comprobó en Isabelle2025 (no existe) y cada alternativa también (sí existe).

## E001 · `nlinarith` no existe en Isabelle (método de Lean)

* En su lugar: método `linarith`, método `smt`, método `argo`.
* No existe en Isabelle. Da a linarith los productos como hechos explícitos (p. ej. mult_nonneg_nonneg, zero_le_power2) o usa smt.
* Visto en episodios de este cuaderno: 0.

## E002 · `ring` no existe en Isabelle (método de Lean)

* En su lugar: método `algebra`, hecho `algebra_simps`.
* No existe. Para identidades de anillos: `by algebra` o `by (simp add: algebra_simps)`.
* Visto en episodios de este cuaderno: 0.

## E003 · `ring_nf` no existe en Isabelle (método de Lean)

* En su lugar: hecho `algebra_simps`.
* No existe. Normaliza con `simp add: algebra_simps`.
* Visto en episodios de este cuaderno: 0.

## E004 · `field_simp` no existe en Isabelle (método de Lean)

* En su lugar: hecho `field_simps`.
* No existe como método; en Isabelle es una colección de reglas: `simp add: field_simps`.
* Visto en episodios de este cuaderno: 1.

## E005 · `omega` no existe en Isabelle (método de Lean)

* En su lugar: método `presburger`, método `arith`.
* No existe. Aritmética lineal entera o natural: presburger, arith, linarith.
* Visto en episodios de este cuaderno: 0.

## E006 · `positivity` no existe en Isabelle (método de Lean)

* En su lugar: método `simp`, hecho `mult_pos_pos`, hecho `zero_le_power2`.
* No existe. Prueba la positividad con simp y reglas como mult_pos_pos, add_pos_pos, zero_le_power2.
* Visto en episodios de este cuaderno: 0.

## E007 · `norm_num` no existe en Isabelle (método de Lean)

* En su lugar: método `simp`.
* No existe. Los cálculos con numerales los hace simp.
* Visto en episodios de este cuaderno: 0.

## E008 · `linear_combination` no existe en Isabelle (método de Lean)

* En su lugar: método `linarith`.
* No existe. Pasa a linarith los hechos que combinarías.
* Visto en episodios de este cuaderno: 0.

## E009 · `gcongr` no existe en Isabelle (método de Lean)

* En su lugar: hecho `mult_left_mono`, hecho `add_mono`, hecho `power_mono`.
* No existe. Usa reglas de monotonía explícitas.
* Visto en episodios de este cuaderno: 0.

## E010 · `aesop` no existe en Isabelle (método de Lean)

* En su lugar: método `auto`, método `blast`, método `force`, método `fastforce`.
* No existe. Búsqueda automática: auto, blast, force, fastforce.
* Visto en episodios de este cuaderno: 0.

## E011 · `sq_nonneg` no existe en Isabelle (hecho de Lean)

* En su lugar: hecho `zero_le_power2`.
* 0 ≤ x² se llama zero_le_power2.
* Visto en episodios de este cuaderno: 0.

## E012 · `inner_self_eq_norm_sq` no existe en Isabelle (hecho de Lean)

* En su lugar: hecho `power2_norm_eq_inner`, hecho `dot_square_norm`.
* ‖x‖² = ⟨x, x⟩ es power2_norm_eq_inner (y dot_square_norm en el otro sentido).
* Visto en episodios de este cuaderno: 0.

## E013 · `inner_self_eq_norm` no existe en Isabelle (hecho de Lean)

* En su lugar: hecho `power2_norm_eq_inner`.
* Nombre inventado; el hecho es power2_norm_eq_inner.
* Visto en episodios de este cuaderno: 0.

## E014 · `norm_sq_eq_inner` no existe en Isabelle (hecho de Lean)

* En su lugar: hecho `power2_norm_eq_inner`.
* Nombre inventado; el hecho es power2_norm_eq_inner.
* Visto en episodios de este cuaderno: 0.

## E015 · `abs_inner_le_norm` no existe en Isabelle (hecho de Lean)

* En su lugar: hecho `Cauchy_Schwarz_ineq2`, hecho `norm_cauchy_schwarz`.
* Cauchy–Schwarz: Cauchy_Schwarz_ineq2 (con valor absoluto) y norm_cauchy_schwarz.
* Visto en episodios de este cuaderno: 0.

## E016 · `inner_le_norm` no existe en Isabelle (hecho de Lean)

* En su lugar: hecho `norm_cauchy_schwarz`.
* Nombre inventado; ⟨x, y⟩ ≤ ‖x‖‖y‖ es norm_cauchy_schwarz.
* Visto en episodios de este cuaderno: 0.

## E017 · `inner_neg_right` no existe en Isabelle (hecho de Lean)

* En su lugar: hecho `inner_minus_right`.
* En Isabelle es inner_minus_right.
* Visto en episodios de este cuaderno: 0.

## E018 · `div_le_iff` no existe en Isabelle (hecho de Lean)

* En su lugar: hecho `divide_le_eq`, hecho `pos_divide_le_eq`.
* División y desigualdad: divide_le_eq, pos_divide_le_eq.
* Visto en episodios de este cuaderno: 0.

## E019 · `divide_less_iff` no existe en Isabelle (hecho de Lean)

* En su lugar: hecho `divide_less_eq`.
* Nombre inventado; usa divide_less_eq.
* Visto en episodios de este cuaderno: 0.

## E020 · `mul_pos` no existe en Isabelle (hecho de Lean)

* En su lugar: hecho `mult_pos_pos`.
* Producto de positivos: mult_pos_pos.
* Visto en episodios de este cuaderno: 0.

## E021 · `mul_le_mul_of_nonneg_left` no existe en Isabelle (hecho de Lean)

* En su lugar: hecho `mult_left_mono`.
* Monotonía del producto: mult_left_mono.
* Visto en episodios de este cuaderno: 0.

## E022 · `log_div` no existe en Isabelle (hecho de Lean)

* En su lugar: hecho `log_divide`.
* El logaritmo de un cociente es log_divide.
* Visto en episodios de este cuaderno: 0.

## E023 · `abs_sub_comm` no existe en Isabelle (hecho de Lean)

* En su lugar: hecho `abs_minus_commute`.
* |a − b| = |b − a| es abs_minus_commute.
* Visto en episodios de este cuaderno: 0.

## E024 · `pow_le_pow_left` no existe en Isabelle (hecho de Lean)

* En su lugar: hecho `power_mono`.
* Monotonía de la potencia: power_mono.
* Visto en episodios de este cuaderno: 0.

## E025 · `add_pow_two` no existe en Isabelle (hecho de Lean)

* En su lugar: hecho `power2_sum`.
* (a + b)² es power2_sum.
* Visto en episodios de este cuaderno: 0.

## A026 · aprendido en los episodios de train

* El método inicial falló repetidamente al disponer solo de `l ≤ u` frente a una meta de cotas para el punto medio.
* Visto en episodios de este cuaderno: 0.

## A027 · aprendido en los episodios de train

* Un `by` puede fallar con `Failed to apply initial proof method` cuando las premisas introducidas no bastan para cerrar el objetivo.
* Visto en episodios de este cuaderno: 0.

## A028 · aprendido en los episodios de train

* La prueba puede acabar con `Failed to finish proof` y dejar una meta algebraica pendiente; conviene obtener antes las igualdades o cotas auxiliares necesarias.
* Visto en episodios de este cuaderno: 0.

## A029 · aprendido en los episodios de train

* Declarar de nuevo una variable ya fijada provoca `Duplicate fixed variable(s)`, como ocurrió con `x` en `sign_step`.
* Visto en episodios de este cuaderno: 0.

## A030 · aprendido en los episodios de train

* `calc` no se acepta como comando de Isar; para encadenar igualdades o desigualdades se puede usar `also` y `finally`.
* Comprobado en Isabelle2025: método `calc` no existe.
* Visto en episodios de este cuaderno: 0.

## A031 · aprendido en los episodios de train

* Isabelle informó que `power_nonneg` no está disponible como hecho con ese nombre.
* Comprobado en Isabelle2025: hecho `power_nonneg` no existe.
* Visto en episodios de este cuaderno: 0.

## A032 · aprendido en los episodios de train

* Isabelle informó que `tendsto_pow_zero` no está disponible como hecho con ese nombre.
* Comprobado en Isabelle2025: hecho `tendsto_pow_zero` no existe.
* Visto en episodios de este cuaderno: 0.

## A033 · aprendido en los episodios de train

* Isabelle informó que `tendsto_iff_dist` no está disponible como hecho con ese nombre.
* Comprobado en Isabelle2025: hecho `tendsto_iff_dist` no existe.
* Visto en episodios de este cuaderno: 0.

## A034 · aprendido en los episodios de train

* Declarar un lema global con la variable fija `x` del contexto produjo `Duplicate fixed variable(s): "x"`; el error se repitió en varios episodios.
* Visto en episodios de este cuaderno: 0.

## A035 · aprendido en los episodios de train

* La simplificación dejó abierta una identidad de potencias y productos; añadir `mult.commute` tampoco cerró la meta.
* Visto en episodios de este cuaderno: 0.

## A036 · aprendido en los episodios de train

* Isabelle rechaza fijar dos veces la misma variable (`Duplicate fixed variable(s): "x"`); evita repetirla en `fixes`.
* Visto en episodios de este cuaderno: 0.

## A037 · aprendido en los episodios de train

* Si el lema auxiliar no se declaró en el contexto, Isabelle informa `Undefined fact` al usarlo como `newton_local_bound`.
* Comprobado en Isabelle2025: hecho `newton_local_bound` no existe.
* Visto en episodios de este cuaderno: 0.

## A038 · aprendido en los episodios de train

* Isabelle informa `Undefined fact` cuando se invoca `abs_eq_zero` como hecho; comprueba el nombre disponible antes de usarlo.
* Comprobado en Isabelle2025: hecho `abs_eq_zero` no existe.
* Visto en episodios de este cuaderno: 0.

## A039 · aprendido en los episodios de train

* En una aplicación de Taylor, un índice sin tipo fijado puede causar `Type unification failed` cuando el operador espera `nat` y el argumento queda con tipo indeterminado.
* Visto en episodios de este cuaderno: 0.

## A040 · aprendido en los episodios de train

* Isabelle rechazó `newton_local_constants` y `newton_local_data` como hechos indefinidos en el contexto.
* Comprobado en Isabelle2025: hecho `newton_local_constants` no existe.
* Comprobado en Isabelle2025: hecho `newton_local_data` no existe.
* Visto en episodios de este cuaderno: 0.

## A041 · aprendido en los episodios de train

* Isabelle rechazó `martillo` como método indefinido.
* Comprobado en Isabelle2025: método `martillo` no existe.
* Visto en episodios de este cuaderno: 1.

## A042 · aprendido en los episodios de train

* Pasar una condición booleana a un lema que Isabelle espera que reciba un valor real causa el error de que `real` no es un subtipo de `bool`.
* Visto en episodios de este cuaderno: 0.

## A043 · aprendido en los episodios de train

* Declarar en `fixes` una variable que ya está fijada en el contexto produce `Duplicate fixed variable(s)`; en este episodio el nombre repetido era `f`.
* Visto en episodios de este cuaderno: 0.

## A044 · aprendido en los episodios de train

* `linarith` puede dejar sin probar una cota del punto medio que contiene división si antes no se introduce la identidad que elimina esa división.
* Visto en episodios de este cuaderno: 0.

## A045 · aprendido en los episodios de train

* Usar un nombre de hecho no disponible en la teoría produce `Undefined fact`; ocurrió con `le_of_lt`, `cu_midpoint_order` y `cu_bisection_invariant`.
* Comprobado en Isabelle2025: hecho `le_of_lt` no existe.
* Comprobado en Isabelle2025: hecho `cu_midpoint_order` no existe.
* Comprobado en Isabelle2025: hecho `cu_bisection_invariant` no existe.
* Visto en episodios de este cuaderno: 1.

## A046 · aprendido en los episodios de train

* Usar un método no definido produce `Undefined method`; ocurrió con `exact` y `martillo`.
* Comprobado en Isabelle2025: método `exact` no existe.
* Comprobado en Isabelle2025: método `martillo` no existe.
* Visto en episodios de este cuaderno: 0.

## A047 · aprendido en los episodios de train

* Ante una meta universal con índice aún no fijado, un método inicial de prueba puede fallar; abrir con `proof -` y fijar explícitamente el índice evita ese fallo.
* Visto en episodios de este cuaderno: 0.

## A048 · aprendido en los episodios de train

* La inducción puede fallar con `Unable to figure out induct rule` si la variable sobre la que se induce no está declarada como variable local del lema.
* Visto en episodios de este cuaderno: 0.

## A049 · aprendido en los episodios de train

* Una búsqueda automática como `smt` puede no cerrar una transferencia de signos entre productos; conviene explicitar los casos de signo y las desigualdades necesarias.
* Visto en episodios de este cuaderno: 0.

## A050 · aprendido en los episodios de train

* Aplicar un lema de monotonía para productos con hipótesis de signo de orientación incompatible deja la meta sin resolver o produce `no unifiers`.
* Visto en episodios de este cuaderno: 0.

## A051 · aprendido en los episodios de train

* Una prueba de que el punto medio queda por debajo del extremo superior puede seguir incompleta si solo se estableció la cota hacia el extremo inferior.
* Visto en episodios de este cuaderno: 0.

## A052 · aprendido en los episodios de train

* Isabelle rechaza volver a fijar una variable que ya está fijada en el contexto, así que conviene usar otro nombre en los lemas auxiliares.
* Visto en episodios de este cuaderno: 0.

## A053 · aprendido en los episodios de train

* Isabelle informa que `le_of_lt` es un hecho indefinido; para pasar de una desigualdad estricta a una no estricta, se puede usar `linarith` en estos ejemplos.
* Comprobado en Isabelle2025: hecho `le_of_lt` no existe.
* Visto en episodios de este cuaderno: 0.
