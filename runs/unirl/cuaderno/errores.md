# Errores frecuentes al escribir pruebas en Isabelle

Cada nombre marcado como inexistente se comprobó en Isabelle2025 (no existe) y cada alternativa también (sí existe).

## E001 · `nlinarith` no existe en Isabelle (método de Lean)

* En su lugar: método `linarith`, método `smt`, método `argo`.
* No existe en Isabelle. Da a linarith los productos como hechos explícitos (p. ej. mult_nonneg_nonneg, zero_le_power2) o usa smt.
* Visto en episodios de este cuaderno: 0.

## E002 · `ring` no existe en Isabelle (método de Lean)

* En su lugar: método `algebra`, hecho `algebra_simps`.
* No existe. Para identidades de anillos: `by algebra` o `by (simp add: algebra_simps)`.
* Visto en episodios de este cuaderno: 1.

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
* Visto en episodios de este cuaderno: 1.

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
* Visto en episodios de este cuaderno: 1.

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
* Visto en episodios de este cuaderno: 4.

## A042 · aprendido en los episodios de train

* Al volver a fijar `f` en un lema cuando el contexto ya la fija, Isabelle produce `Duplicate fixed variable(s): "f"`.
* Visto en episodios de este cuaderno: 0.

## A043 · aprendido en los episodios de train

* Si las premisas disponibles no bastan para aplicar el método inicial al subobjetivo, Isabelle produce `Failed to apply initial proof method`.
* Visto en episodios de este cuaderno: 0.

## A044 · aprendido en los episodios de train

* Si la prueba deja una submeta aritmética sin resolver, como `(l + u) / 2 ≤ u`, Isabelle produce `Failed to finish proof`.
* Visto en episodios de este cuaderno: 0.

## A045 · aprendido en los episodios de train

* Usar un hecho no declarado produce `Undefined fact: "cu_bisection_invariant".`
* Comprobado en Isabelle2025: hecho `cu_bisection_invariant` no existe.
* Visto en episodios de este cuaderno: 0.

## A046 · aprendido en los episodios de train

* La simplificación amplia de la definición recursiva agotó repetidamente el tiempo de compilación.
* Visto en episodios de este cuaderno: 0.

## A047 · aprendido en los episodios de train

* Se intentó concluir \(0 \le k\) a partir de \(0 \le k^n k\), algo que no se deduce sin una hipótesis de signo sobre \(k\).
* Visto en episodios de este cuaderno: 0.

## A048 · aprendido en los episodios de train

* Las cotas de orden no cierran por sí solas la meta de valor absoluto si la cota inferior no se expresa en la orientación requerida por la caracterización de \(|\cdot|\).
* Visto en episodios de este cuaderno: 0.

## A049 · aprendido en los episodios de train

* Isabelle da `Undefined fact` cuando se usa un lema auxiliar que no está disponible en el contexto activo; citarlo no incorpora su declaración.
* Visto en episodios de este cuaderno: 0.

## A050 · aprendido en los episodios de train

* En una cota de productos, Isabelle no cierra la monotonía si no se proporciona la no negatividad del factor y se multiplica por el lado correcto.
* Visto en episodios de este cuaderno: 0.

## A051 · aprendido en los episodios de train

* La normalización automática de potencias puede dejar sin probar una igualdad cuando los exponentes aparecen en órdenes distintos.
* Visto en episodios de este cuaderno: 0.

## A052 · aprendido en los episodios de train

* El tipo del índice auxiliar de Taylor puede quedar indeterminado; hay que fijarlo explícitamente como `nat`.
* Visto en episodios de este cuaderno: 0.

## A053 · aprendido en los episodios de train

* Las reglas del valor medio no emparejan una derivabilidad expresada como cuantificación lógica con una premisa que esperan como regla de Isar.
* Visto en episodios de este cuaderno: 0.

## A054 · aprendido en los episodios de train

* Una referencia a un lema auxiliar no compilado o fuera del contexto produce `Undefined fact`.
* Visto en episodios de este cuaderno: 0.

## A055 · aprendido en los episodios de train

* Declarar un lema con una variable ya fijada en el contexto produce `Duplicate fixed variable(s)`; usa nombres auxiliares distintos.
* Visto en episodios de este cuaderno: 0.

## A056 · aprendido en los episodios de train

* Invocar un hecho `cu_...` que no se declaró ni se incluyó produce `Undefined fact`.
* Comprobado en Isabelle2025: hecho `cu_newton_step_quadratic` no existe.
* Comprobado en Isabelle2025: hecho `cu_medio_en_intervalo` no existe.
* Visto en episodios de este cuaderno: 0.

## A057 · aprendido en los episodios de train

* `Failed to apply initial proof method` se repitió cuando el método inicial no cerró la meta; comprobar que las hipótesis bastan o descomponer explícitamente los casos de signo.
* Visto en episodios de este cuaderno: 0.

## A058 · aprendido en los episodios de train

* `Failed to finish proof` se repitió con subobjetivos abiertos; exponer las ecuaciones de cada rama y cerrar por separado las metas residuales.
* Visto en episodios de este cuaderno: 0.

## A059 · aprendido en los episodios de train

* Referenciar lemas auxiliares aún no definidos o registrados produjo `Undefined fact`.
* Comprobado en Isabelle2025: hecho `cu_iterate_contraction_diameter` no existe.
* Comprobado en Isabelle2025: hecho `cu_fixed_point_posteriori_step` no existe.
* Comprobado en Isabelle2025: hecho `cu_funpow_Suc_apply` no existe.
* Comprobado en Isabelle2025: hecho `cu_power_tends_zero` no existe.
* Visto en episodios de este cuaderno: 0.

## A060 · aprendido en los episodios de train

* Declarar de nuevo `n` como variable fija en un contexto donde ya estaba fijada produjo `Duplicate fixed variable(s)`.
* Visto en episodios de este cuaderno: 0.

## A061 · aprendido en los episodios de train

* Volver a fijar el parámetro `p` cuando ya está fijado en el contexto causa `Duplicate fixed variable(s)`.
* Visto en episodios de este cuaderno: 0.

## A062 · aprendido en los episodios de train

* Usar `mem_Icc` como hecho produjo `Undefined fact` en ese contexto.
* Comprobado en Isabelle2025: hecho `mem_Icc` no existe.
* Visto en episodios de este cuaderno: 0.

## A063 · aprendido en los episodios de train

* Usar `omega` produjo `Undefined method` en ese contexto.
* Comprobado en Isabelle2025: método `omega` no existe.
* Visto en episodios de este cuaderno: 0.

## A064 · aprendido en los episodios de train

* Una proposición mal parentizada sobre `has_real_derivative` produjo un error de sintaxis al analizar la prueba.
* Visto en episodios de este cuaderno: 0.

## A065 · aprendido en los episodios de train

* Introducir `calc` en una posición donde Isabelle esperaba un comando exterior produjo un error de sintaxis; `calc` debe aparecer dentro de la estructura Isar apropiada.
* Visto en episodios de este cuaderno: 0.

## A066 · aprendido en los episodios de train

* Dejar sin fijar como natural el índice de una sucesión de derivadas causó un fallo de unificación de tipos al compararlo con `0` y `1`.
* Visto en episodios de este cuaderno: 0.

## A067 · aprendido en los episodios de train

* Una táctica de cierre no resolvió las obligaciones de derivabilidad de una función auxiliar y dejó esas premisas como subobjetivos.
* Visto en episodios de este cuaderno: 0.

## A068 · aprendido en los episodios de train

* `MacLaurin.Taylor` entrega un punto interior `t`, por lo que no cierra directamente un objetivo que exige un testigo expresado como `aa + v * (bb - aa)`.
* Visto en episodios de este cuaderno: 0.

## A069 · aprendido en los episodios de train

* La simplificación por sí sola no cerró varias igualdades de potencias anidadas; fue necesario separar y normalizar las identidades de exponentes.
* Visto en episodios de este cuaderno: 0.

## A070 · aprendido en los episodios de train

* Aplicar MVT directamente no unifica cuando las hipótesis dan derivadas reales, pero el teorema requiere continuidad y diferenciabilidad en el interior; hay que establecer primero las condiciones requeridas.
* Visto en episodios de este cuaderno: 0.

## A071 · aprendido en los episodios de train

* Usar mult_mono para acotar cuadrados falla si faltan las no negatividades o se suministran en el orden incorrecto.
* Visto en episodios de este cuaderno: 0.

## A072 · aprendido en los episodios de train

* Reutilizar una variable fija del contexto, como f o r, en una declaración nueva produce Duplicate fixed variable(s).
* Visto en episodios de este cuaderno: 0.

## A073 · aprendido en los episodios de train

* Se informó como indefinido el hecho has_real_derivative_imp_differentiable.
* Comprobado en Isabelle2025: hecho `has_real_derivative_imp_differentiable` no existe.
* Visto en episodios de este cuaderno: 0.

## A074 · aprendido en los episodios de train

* Se informó como indefinido el hecho cu_newton_local_half.
* Comprobado en Isabelle2025: hecho `cu_newton_local_half` no existe.
* Visto en episodios de este cuaderno: 0.

## A075 · aprendido en los episodios de train

* Se informó como indefinido el hecho tendsto_powr_zero.
* Comprobado en Isabelle2025: hecho `tendsto_powr_zero` no existe.
* Visto en episodios de este cuaderno: 0.

## A076 · aprendido en los episodios de train

* Se informó como indefinido el hecho divide_nonneg_iff.
* Comprobado en Isabelle2025: hecho `divide_nonneg_iff` no existe.
* Visto en episodios de este cuaderno: 0.

## A077 · aprendido en los episodios de train

* martillo no se reconoce como método de Isabelle.
* Comprobado en Isabelle2025: método `martillo` no existe.
* Visto en episodios de este cuaderno: 2.

## A078 · aprendido en los episodios de train

* La aplicación de `tendsto` falló por incompatibilidad de tipos al pasar `at r` donde se esperaba una función.
* Visto en episodios de este cuaderno: 0.

## A079 · aprendido en los episodios de train

* La cota de `((1/2::'a)^n)` quedó con el tipo demasiado general para demostrar que es menor o igual que 1.
* Visto en episodios de este cuaderno: 0.

## A080 · aprendido en los episodios de train

* `HOL.simp` rechazó constantes y hechos escritos como argumentos entre corchetes; las reglas adicionales se indican con `simp add:`.
* Visto en episodios de este cuaderno: 0.

## A081 · aprendido en los episodios de train

* La aplicación de `mult_nonneg_nonpos` no unificó porque sus premisas exigen un factor no negativo y otro no positivo.
* Visto en episodios de este cuaderno: 0.

## A082 · aprendido en los episodios de train

* Separar la proposición de la declaración `lemma` hizo que el analizador esperara una proposición y encontrara el fin de entrada.
* Visto en episodios de este cuaderno: 0.

## A083 · aprendido en los episodios de train

* Usar `calc` como comando Isar independiente hizo que el analizador esperara un comando y encontrara ese identificador.
* Visto en episodios de este cuaderno: 0.

## A084 · aprendido en los episodios de train

* La prueba de no negatividad de una potencia dejó pendiente una desigualdad porque el producto tenía los factores en un orden distinto al de la hipótesis inductiva.
* Visto en episodios de este cuaderno: 0.

## A085 · aprendido en los episodios de train

* Se intentó usar un hecho auxiliar que no estaba disponible en el contexto.
* Comprobado en Isabelle2025: hecho `cu_iterate_contraction_bound` no existe.
* Visto en episodios de este cuaderno: 0.

## A086 · aprendido en los episodios de train

* `calc` produjo un error de sintaxis porque no es una orden Isar válida en esos bloques; la cadena de cotas se puede expresar con `also` y `finally`.
* Visto en episodios de este cuaderno: 0.

## A087 · aprendido en los episodios de train

* Declarar `p` como variable fija en un lema cuando ya está fijada en el contexto produce `Duplicate fixed variable(s)`.
* Visto en episodios de este cuaderno: 0.

## A088 · aprendido en los episodios de train

* `simp` no demuestra por sí solo igualdades entre valores absolutos de diferencias si no se establecen antes los signos.
* Visto en episodios de este cuaderno: 0.

## A089 · aprendido en los episodios de train

* El método `martillo` no está definido en el entorno Isabelle usado.
* Comprobado en Isabelle2025: método `martillo` no existe.
* Visto en episodios de este cuaderno: 1.

## A090 · aprendido en los episodios de train

* El hecho `lipschitz_continuous_on` no está definido en el entorno Isabelle usado.
* Comprobado en Isabelle2025: hecho `lipschitz_continuous_on` no existe.
* Visto en episodios de este cuaderno: 0.

## A091 · aprendido en los episodios de train

* Isabelle rechaza un lema que vuelve a fijar una variable ya fijada por el contexto; ocurrió con `n` y con `f`.
* Visto en episodios de este cuaderno: 0.

## A092 · aprendido en los episodios de train

* Al aplicar Taylor, no basta con obtener un punto de resto en un intervalo cerrado: hay que conservar la condición estricta de que esté entre los extremos.
* Visto en episodios de este cuaderno: 0.

## A093 · aprendido en los episodios de train

* Un comando de nivel de teoría como `theorem` no puede aparecer dentro de `PROOF`; la prueba debe empezar directamente con `proof`.
* Visto en episodios de este cuaderno: 0.

## A094 · aprendido en los episodios de train

* Un lema auxiliar no puede volver a fijar una variable que ya está fijada en el contexto, como `f` o `r`.
* Visto en episodios de este cuaderno: 0.

## A095 · aprendido en los episodios de train

* Isabelle no encuentra el hecho `le_of_lt`.
* Comprobado en Isabelle2025: hecho `le_of_lt` no existe.
* Visto en episodios de este cuaderno: 0.

## A096 · aprendido en los episodios de train

* Isabelle no encuentra el hecho `cu_newton_quadratic_step` si el lema auxiliar no se declaró en el contexto.
* Comprobado en Isabelle2025: hecho `cu_newton_quadratic_step` no existe.
* Visto en episodios de este cuaderno: 0.

## A097 · aprendido en los episodios de train

* Isabelle no reconoce `martillo` como método de prueba.
* Comprobado en Isabelle2025: método `martillo` no existe.
* Visto en episodios de este cuaderno: 0.

## A098 · aprendido en los episodios de train

* La aplicación de `D` falla si se pasa un índice de tipo incompatible; hay que separar el tipo del índice del tipo de los argumentos reales.
* Visto en episodios de este cuaderno: 0.

## A099 · aprendido en los episodios de train

* La inducción no se cierra si el punto inicial no se generaliza para mantener una hipótesis inductiva aplicable al sucesor.
* Visto en episodios de este cuaderno: 0.

## A100 · aprendido en los episodios de train

* Una aplicación inicial de método puede fallar cuando el objetivo usa cotas con `min` y `max` y las hipótesis solo dan cotas en un intervalo ordenado; hay que transportar las cotas o separar los casos de orden.
* Visto en episodios de este cuaderno: 0.

## A101 · aprendido en los episodios de train

* Un límite de una composición no se obtiene automáticamente si la composición o los filtros no están instanciados de forma compatible.
* Visto en episodios de este cuaderno: 0.

## A102 · aprendido en los episodios de train

* `qed` falla si aún queda un subobjetivo pendiente, aunque la estructura general de la prueba parezca completa.
* Visto en episodios de este cuaderno: 0.
