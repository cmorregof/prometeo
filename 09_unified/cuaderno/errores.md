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
* Visto en episodios de este cuaderno: 0.

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
