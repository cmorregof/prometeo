# Auditoría de la ronda 20261008-2003 (rejuzgar, referencia R)

Fuente: `resultados/rejuicio/ronda2/rejuicio.jsonl` (749 intentos, 256 episodios). Episodio: la primera corrida en que terminó (regla de `ronda.py`). «En K»: antes del primer intento válido según R (o en cualquiera, si no hay válido) hubo uno «concordante_contaminado» o «indeterminado». Y: veredicto del juez; Y^a: el auditado (R).

Ejecución (Mac, sin API): `rejuzgar` juzgó 739 intentos el 14 oct de 01:37 a 07:09 con `--paralelo 2 --hilos 2`; el Mac se reinició a la fuerza a las 08:04 (`panic … btn_rst`); los 10 restantes (todos de E3) se juzgaron de 13:09 a 13:10 con `--paralelo 1`. `parametros.json` conserva solo la fecha de la reanudación (no guarda paralelo ni hilos). `cruzado`: 13:20–13:25. Lemas del cuaderno: ver la sección 5.

## 3. Por configuración

| config | intentos | FP | FN | sin juicio | contaminados | indeterminados | regla estricta | tiempo | episodios | en K | fuera de K | Y = 1 | Y^a = 1 | Y^a indet. |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B0 | 40 | 0 | 0 | 22 | 0 | 0 | 0 | 0 | 32 | 0 | 32 | 0 | 0 | 0 |
| B | 38 | 0 | 0 | 14 | 0 | 0 | 0 | 0 | 32 | 0 | 32 | 0 | 0 | 0 |
| C | 122 | 0 | 0 | 61 | 0 | 0 | 0 | 0 | 32 | 0 | 32 | 7 | 7 | 0 |
| E | 120 | 0 | 0 | 57 | 0 | 0 | 1 | 0 | 32 | 0 | 32 | 5 | 5 | 0 |
| F | 335 | 0 | 0 | 52 | 0 | 1 | 0 | 0 | 96 | 1 | 95 | 33 | 33 | 0 |
| C3 | 50 | 0 | 0 | 25 | 0 | 0 | 0 | 0 | 16 | 0 | 16 | 2 | 2 | 0 |
| E3 | 44 | 0 | 0 | 27 | 0 | 0 | 0 | 0 | 16 | 0 | 16 | 3 | 3 | 0 |

Contaminados, indeterminados y las demás categorías cuentan intentos; «en K» y las columnas Y cuentan episodios.

Intentos no concordantes (ni «sin juicio»):

| config | episodio | intento | juez | categoría | detalle | primer error del juez | primer error de R |
|---|---|---|---|---|---|---|---|
| F | pf_5c_a_priori_max#3 | 1 | LEMMA_FAILED | indeterminado | la biblioteca (o el preludio) no compila en este peldaño | *** Undefined fact: "cu_iterate_contraction_bound" (lema cu_iterate_first_step_bound del cuaderno, línea 16) | *** Undefined fact: "cu_iterate_contraction_bound" (line 89 of "~/isabelle/scratch/rejuicio/rj-dbu993zo/Rejuic |
| E | secante_1_inyectiva#E#2 | 2 | STATEMENT_DRIFT | regla_estricta | STATEMENT_DRIFT: STATEMENT_DRIFT: la PROOF no se admite: barra invertida fuera de un símbo |  |  |

### McNemar C frente a E, pareado por tarea y episodio, en los 8 peldaños de dificultad ≤ 3

Peldaños: rf_1_punto, rf_2_signo, rf_3_encaje, rf_4_raiz, rf_5_limites, secante_1_inyectiva, secante_2_cociente, secante_4_contraccion. b = gana E, b' = gana C; p exacto bilateral (`rejuzgar.p_mcnemar`).

| veredicto | indeterminados de Y^a | pares | b (E gana) | b' (C gana) | p |
|---|---|---|---|---|---|
| Y (juez) | — | 16 | 2 | 4 | 0,6875 |
| Y^a (auditado) | excluir | 16 | 2 | 4 | 0,6875 |
| Y^a (auditado) | 0 | 16 | 2 | 4 | 0,6875 |
| Y^a (auditado) | 1 | 16 | 2 | 4 | 0,6875 |
| Y^R (kernel, sin reglas declaradas; no prerregistrado) | excluir | 16 | 2 | 3 | 1,0000 |
| Y^R (kernel, sin reglas declaradas; no prerregistrado) | 0 | 16 | 2 | 3 | 1,0000 |
| Y^R (kernel, sin reglas declaradas; no prerregistrado) | 1 | 16 | 2 | 3 | 1,0000 |

Pares discordantes (peldaño, episodio → C, E) con Y y con Y^R:

- Y: rf_2_signo#1 → 1, 0; rf_3_encaje#1 → 1, 0; secante_1_inyectiva#1 → 1, 0; secante_1_inyectiva#2 → 1, 0; secante_2_cociente#1 → 0, 1; secante_2_cociente#2 → 0, 1
- Y^R: rf_2_signo#1 → 1, 0; rf_3_encaje#1 → 1, 0; secante_1_inyectiva#1 → 1, 0; secante_2_cociente#1 → 0, 1; secante_2_cociente#2 → 0, 1

## 4. Intentos de E y E3 que citan un lema del cuaderno

| config | episodio | intento | lemas citados | juez | R | categoría | primer error del juez | primer error de R | ¿prueba o arnés? |
|---|---|---|---|---|---|---|---|---|---|
| E | rf_4_raiz#E#1 | 1 | cu_bolzano_product | PROOF_FAILED | rechaza | concordante | *** Failed to finish proof (línea 82 de tu PROOF): | *** Failed to finish proof (line 204 of "~/isabelle/scratch/rejuicio/rj-q909phv8/Rejuicio.thy"): | prueba |
| E | rf_4_raiz#E#1 | 2 | cu_bolzano_product | PROOF_FAILED | rechaza | concordante | *** exception THM 0 raised (line 307 of "drule.ML"): | *** exception THM 0 raised (line 307 of "drule.ML"): | prueba |
| E | rf_4_raiz#E#1 | 3 | cu_bolzano_product | PROOF_FAILED | rechaza | concordante | *** Bad arguments for method "HOL.simp" (línea 80 de tu PROOF): | *** Bad arguments for method "HOL.simp" (line 202 of "~/isabelle/scratch/rejuicio/rj-219qnv4y/Rejuicio.thy"): | prueba |
| E | rf_4_raiz#E#1 | 4 | cu_bolzano_product | PROOF_FAILED | rechaza | concordante | *** Failed to finish proof (línea 81 de tu PROOF): | *** Failed to finish proof (line 203 of "~/isabelle/scratch/rejuicio/rj-4hlyku23/Rejuicio.thy"): | prueba |
| E | rf_4_raiz#E#2 | 1 | cu_bolzano_product | LEMMA_FAILED | rechaza | concordante | *** Failed to apply initial proof method (lema rf_interval_invariant, línea 43): | *** Failed to apply initial proof method (line 162 of "~/isabelle/scratch/rejuicio/rj-_8r6w7dh/Rejuicio.thy"): | prueba |
| E | rf_4_raiz#E#2 | 2 | cu_bolzano_product | LEMMA_FAILED | rechaza | concordante | *** Bad arguments for method "HOL.simp" (lema rf_interval_invariant, línea 82): | *** Bad arguments for method "HOL.simp" (line 201 of "~/isabelle/scratch/rejuicio/rj-h60qqr6f/Rejuicio.thy"): | prueba |
| E | rf_4_raiz#E#2 | 3 | cu_bolzano_product | LEMMA_FAILED | rechaza | concordante | *** Failed to apply initial proof method (lema rf_interval_invariant, línea 68): | *** Failed to apply initial proof method (line 187 of "~/isabelle/scratch/rejuicio/rj-tl3ic0qo/Rejuicio.thy"): | prueba |
| E | rf_4_raiz#E#2 | 4 | cu_bolzano_product | LEMMA_FAILED | rechaza | concordante | *** Failed to finish proof (lema rf_interval_invariant, línea 99): | *** Failed to finish proof (line 218 of "~/isabelle/scratch/rejuicio/rj-4y87dp33/Rejuicio.thy"): | prueba |
| E | rf_6_convergencia#E#2 | 1 | cu_bolzano_product | PROOF_FAILED | rechaza | sin_juicio |  | marcas `by martillo` sin cerrar | prueba (marcas sin cerrar) |
| E | rf_6_convergencia#E#2 | 2 | cu_bolzano_product | PROOF_FAILED | rechaza | sin_juicio | *** Bad arguments for method "martillo" (línea 39 de tu PROOF) | marcas `by martillo` sin cerrar | prueba (marcas sin cerrar) |
| E | secante_4c_contraccion_local#E#1 | 1 | cu_compact_real_abs_bound | PROOF_FAILED | rechaza | sin_juicio | *** Bad arguments for method "martillo" (lema local_fprime_lipschitz, línea 22) | marcas `by martillo` sin cerrar | prueba (marcas sin cerrar) |
| E | secante_4c_contraccion_local#E#1 | 2 | cu_compact_real_abs_bound | LEMMA_FAILED | rechaza | concordante | *** Duplicate fixed variable(s): "r" | *** Duplicate fixed variable(s): "r" | arnés por diseño (su lema, dentro del contexto, choca con el `fixes` del peldaño) |
| E | secante_4c_contraccion_local#E#1 | 3 | cu_compact_real_abs_bound | LEMMA_FAILED | rechaza | concordante | *** Failed to apply initial proof method (lema local_fprime_lipschitz, línea 57): | *** Failed to apply initial proof method (line 240 of "~/isabelle/scratch/rejuicio/rj-oqa7o7mr/Rejuicio.thy"): | prueba |
| E | secante_4c_contraccion_local#E#1 | 4 | cu_compact_real_abs_bound | LEMMA_FAILED | rechaza | concordante | *** Undefined fact: "local_between_bound" (lema local_fprime_lipschitz, línea 24) | *** Undefined fact: "local_between_bound" (line 151 of "~/isabelle/scratch/rejuicio/rj-3joa2yxe/Rejuicio.thy") | prueba |
| E | secante_5c_convergencia_local#E#2 | 3 | cu_power_tends_zero | PROOF_FAILED | rechaza | sin_juicio | *** Failed to refine any pending goal | marcas `by martillo` sin cerrar | prueba (marcas sin cerrar) |
| E | secante_5c_convergencia_local#E#2 | 4 | cu_power_tends_zero | PROOF_FAILED | rechaza | sin_juicio | *** Failed to finish proof (línea 31 de tu PROOF): | marcas `by martillo` sin cerrar | prueba (marcas sin cerrar) |
| E3 | rf_4_raiz#E3#1 | 1 | cu_bolzano_product | INVALID_PROPOSAL | rechaza | concordante |  | *** Duplicate fixed variable(s): "f" | arnés por diseño (su lema, dentro del contexto, choca con el `fixes` del peldaño) |
| E3 | rf_4_raiz#E3#1 | 2 | cu_bolzano_product | LEMMA_FAILED | rechaza | concordante | *** Bad arguments for method "HOL.simp" (lema rf_step_property, línea 81): | *** Bad arguments for method "HOL.simp" (line 200 of "~/isabelle/scratch/rejuicio/rj-67xehdxl/Rejuicio.thy"): | prueba |
| E3 | rf_4_raiz#E3#1 | 3 | cu_bolzano_product | LEMMA_FAILED | rechaza | concordante | *** Failed to apply initial proof method (lema rf_step_property, línea 36): | *** Failed to apply initial proof method (line 155 of "~/isabelle/scratch/rejuicio/rj-eaphuc_k/Rejuicio.thy"): | prueba |
| E3 | rf_6_convergencia#E3#1 | 1 | cu_bolzano_product | PROOF_FAILED | rechaza | sin_juicio | *** Failed to apply initial proof method (línea 10 de tu PROOF): | marcas `by martillo` sin cerrar | prueba (marcas sin cerrar) |
| E3 | secante_5c_convergencia_local#E3#1 | 3 | cu_compact_real_abs_bound | PROOF_FAILED | rechaza | sin_juicio |  | marcas `by martillo` sin cerrar | prueba (marcas sin cerrar) |

Resumen: {'prueba': 12, 'prueba (marcas sin cerrar)': 7, 'arnés por diseño (su lema, dentro del contexto, choca con el `fixes` del peldaño)': 2}. «Prueba»: el juez y R rechazan por un error del texto del agente; «marcas sin cerrar»: el martillo no cerró algún `by martillo` y nadie vio una prueba completa; «arnés»: FN, regla estricta, tiempo, indeterminado, contaminado o falla de biblioteca.

## 5. Los lemas del cuaderno 835d3070e3b0c3b1

Fuente: `resultados/rejuicio/ronda2/lemas_martillo.jsonl` (80 lemas). Martillo de la ronda: try0 5 s y Sledgehammer 60 s sobre el enunciado a nivel de teoría, sin el resto del cuaderno; «sí» si la línea encontrada compila sin atajos en la plantilla de admisión del cuaderno. «Mostrado»: el lema apareció en `lemas_mostrados` de algún intento de E o E3.

- Alcance: {'general': 79, 'biseccion': 1}; método de origen: {'biseccion': 20, 'punto_fijo': 42, 'ordenes': 10, 'newton': 8}.
- Mostrados en algún peldaño de prueba: 18; nunca: 62.
- El martillo solo los demuestra: 54 de 80 (try0: 22, Sledgehammer: 32); entre los mostrados: 8 de 18.
- Repetidos (`lemas_martillo_repeticion.jsonl`, 15 oct): 20: los «no» de la primera corrida con más de 5 s de suspensión (el Mac se durmió con la tapa cerrada a las 13:39 del 14 oct; un «no» bajo suspensión puede ser un tiempo agotado) y `cu_abs_distance_between` (dos conclusiones: la primera corrida solo cerraba una). Un «sí» con suspensión vale: la línea se comprobó sin atajos.
- «No» que siguen dudosos (suspensión > 5 s también al repetir): 0; línea encontrada que no compila en la pasada 2: 0.

| # | lema | alcance | origen | peldaños de prueba donde se mostró | ¿el martillo solo? | línea |
|---|---|---|---|---|---|---|
| 1 | sign_step | general | bis_3_signo (biseccion) | 0 | sí | by (smt (verit, ccfv_threshold) mult_eq_0_iff xy_bad xz zero_le_mult_i |
| 2 | cu_midpoint_halves | general | bis_1_ancho (biseccion) | 0 | sí | by (smt (verit, best) diff_divide_distrib real_average_minus_second sp |
| 3 | cu_power_halving | general | bis_1_ancho (biseccion) | 0 | sí | by simp |
| 4 | cu_product_sign_transfer | general | bis_3_signo (biseccion) | 0 | sí | by (smt (verit, ccfv_threshold) mult_eq_0_iff xy xz zero_le_mult_iff) |
| 5 | cu_bisection_step_sign | general | bis_3_signo (biseccion) | 0 | sí | by (smt (verit, best) mult_le_0_iff xy) |
| 6 | cu_bolzano_product | general | bis_4_raiz (biseccion) | 3: rf_3_encaje, rf_4_raiz, rf_6_convergencia | sí | by (metis IVT' IVT2' contxy mult_le_0_iff signxy xy) |
| 7 | cu_deriv_bound_lipschitz | general | pf_1_derivada (punto_fijo) | 1: secante_3_producto | no |  |
| 8 | cu_funpow_closed | general | pf_2_dentro (punto_fijo) | 2: rf_1_punto, rf_3_encaje | no |  |
| 9 | cu_contraction_fixed_unique | general | pf_3_unicidad (punto_fijo) | 0 | sí | using c_less_one contraction fixed_x fixed_y mult_less_cancel_right2 b |
| 10 | cu_iterate_contraction_bound | general | pf_4_decaimiento (punto_fijo) | 5: rf_1_punto, rf_2_signo, rf_6c_puntos_convergen, secante_1_inyectiva, secante_6_fibonacci | no |  |
| 11 | cu_iterated_contraction_bound | general | pf_5_a_priori (punto_fijo) | 0 | no |  |
| 12 | cu_interval_distance_bound_v3 | general | pf_5_a_priori (punto_fijo) | 0 | sí | using assms by fastforce |
| 13 | cu_interval_distance_bound_final | general | pf_5_a_priori (punto_fijo) | 0 | sí | using assms by fastforce |
| 14 | cu_iterated_contraction_bound_final | general | pf_5_a_priori (punto_fijo) | 0 | no |  |
| 15 | cu_interval_endpoint_bound | general | pf_5c_a_priori_max (punto_fijo) | 0 | sí | using assms by force |
| 16 | cu_fixedpoint_first_step_bound | general | pf_6_a_priori_x1 (punto_fijo) | 0 | no |  |
| 17 | cu_iterate_first_step_bound | general | pf_6_a_priori_x1 (punto_fijo) | 1: secante_4_contraccion | no |  |
| 18 | cu_abs_posteriori | general | pf_6p_a_posteriori (punto_fijo) | 0 | no |  |
| 19 | cu_real_lipschitz_continuous | general | pf_7_existencia (punto_fijo) | 0 | no |  |
| 20 | cu_interval_endpoint_bounds | general | pf_7_existencia (punto_fijo) | 3: rf_5_limites, secante_4_contraccion, secante_4c_contraccion_local | sí | using assms by presburger |
| 21 | cu_geometric_power_tends_zero | general | pf_8_convergencia (punto_fijo) | 0 | sí | by (simp add: LIMSEQ_realpow_zero less nonneg) |
| 22 | cu_real_geometric_sequence_tends_zero | general | pf_8_convergencia (punto_fijo) | 0 | sí | using LIMSEQ_realpow_zero less nonneg by blast |
| 23 | cu_abs_square | general | pf_9_cuadratico (punto_fijo) | 0 | sí | by (simp add: power2_eq_square) |
| 24 | cu_quadratic_derivative_step | general | pf_9_cuadratico (punto_fijo) | 0 | no |  |
| 25 | cu_deriv_nonnegative_nondecreasing | general | pf_9c_cuadratico_medio (punto_fijo) | 2: rf_4_raiz, rf_6_convergencia | sí | by (metis DERIV_nonneg_imp_nondecreasing atLeastAtMost_iff ddata nonne |
| 26 | cu_abs_recurrence_bound | general | orden_1_lineal (ordenes) | 1: rf_2_signo | no |  |
| 27 | cu_abs_recurrence_bound_v2 | general | orden_1_lineal (ordenes) | 0 | no |  |
| 28 | cu_abs_square_scale | general | orden_3_cuadratico (ordenes) | 0 | sí | by (metis (no_types, lifting) ab_semigroup_mult_class.mult_ac(1) bound |
| 29 | cu_square_recurrence_bound | general | orden_3_cuadratico (ordenes) | 1: rf_5_limites | no |  |
| 30 | cu_newton_algebra | general | newton_2_contraccion (newton) | 0 | no |  |
| 31 | cu_medio_en_intervalo | general | bis_1_ancho (biseccion) | 0 | sí | using assms by simp |
| 32 | cu_mitad_longitud | general | bis_1_ancho (biseccion) | 0 | sí | by argo |
| 33 | cu_divide_power_two_half | general | bis_1_ancho (biseccion) | 0 | sí | by simp |
| 34 | cu_midpoint_bounds | general | bis_2_encaje (biseccion) | 0 | sí | using assms by simp |
| 35 | cu_split_interval | general | bis_2_encaje (biseccion) | 0 | sí | using assms by force |
| 36 | cu_product_sign_switch | general | bis_3_signo (biseccion) | 0 | sí | by (smt (verit) xy xz zero_less_mult_iff) |
| 37 | cu_product_sign_step | general | bis_5_cota (biseccion) | 0 | sí | by (smt (verit, del_insts) mult_eq_0_iff not_pr pq zero_le_mult_iff) |
| 38 | cu_log2_to_power_bound | general | bis_6_iteraciones (biseccion) | 0 | sí | by (smt (verit, ccfv_SIG) less_log_of_power logarithm_bound) |
| 39 | cu_log2_power_bound | general | bis_6_iteraciones (biseccion) | 0 | sí | by (smt (verit, ccfv_threshold) less_log_of_power log_bound) |
| 40 | cu_bisection_width | biseccion | bis_6_iteraciones (biseccion) | 0 | no |  |
| 41 | cu_deriv_bound_lipschitz_between_points | general | pf_1_derivada (punto_fijo) | 0 | no |  |
| 42 | cu_contraction_fixed_point_unique | general | pf_3_unicidad (punto_fijo) | 6: secante_1_inyectiva, secante_2_cociente, secante_3_producto, secante_4_contraccion, secante_5_convergencia, secante_6_fibonacci | sí | by (smt (verit, del_insts) fx fy less lip mult_less_cancel_right2 x_me |
| 43 | cu_iterates_preserve_set | general | pf_4_decaimiento (punto_fijo) | 1: secante_3_producto | no |  |
| 44 | cu_iterate_power_error | general | pf_5_a_priori (punto_fijo) | 0 | no |  |
| 45 | cu_funpow_preserves_set | general | pf_5c_a_priori_max (punto_fijo) | 1: rf_1_punto | no |  |
| 46 | cu_iterate_fixedpoint_contraction | general | pf_5c_a_priori_max (punto_fijo) | 1: rf_5_limites | no |  |
| 47 | cu_interval_distance_max | general | pf_5c_a_priori_max (punto_fijo) | 0 | sí | using assms by auto |
| 48 | cu_funpow_suc_apply | general | pf_6p_a_posteriori (punto_fijo) | 0 | sí | by simp |
| 49 | cu_power_tends_zero | general | pf_8_convergencia (punto_fijo) | 2: secante_5c_convergencia_local, secante_6c_orden_phi | sí | using LIMSEQ_realpow_zero c_less_one c_nonneg by blast |
| 50 | cu_squeeze_nonnegative | general | pf_8_convergencia (punto_fijo) | 0 | sí | by (smt (verit) LIMSEQ_iff_nz bound nonneg norm_conv_dist order.trans  |
| 51 | cu_abs_product_real | general | orden_1_lineal (ordenes) | 2: secante_2_cociente, secante_5_convergencia | sí | using abs_mult by blast |
| 52 | cu_scale_le_real | general | orden_1_lineal (ordenes) | 0 | sí | by (simp add: landau_omega.R_mult_left_mono r_nonneg xy) |
| 53 | cu_between_abs_bound | general | newton_1_paso (newton) | 0 | sí | using assms by auto |
| 54 | cu_abs_division_bound | general | newton_2_contraccion (newton) | 0 | sí | by (simp add: A_nonneg abs_bound frac_le q_le_abs_v q_pos) |
| 55 | cu_abs_segment_bound | general | newton_5_orden2 (newton) | 0 | sí | using assms by argo |
| 56 | cu_square_iterate_bound | general | newton_5_orden2 (newton) | 0 | no |  |
| 57 | cu_compact_real_abs_bound | general | newton_5c_orden2_local (newton) | 4: rf_6c_puntos_convergen, secante_4c_contraccion_local, secante_5c_convergencia_local, secante_6c_orden_phi | sí | by (metis compact_A cont_A continuous_on_compact_bound real_norm_def) |
| 58 | cu_real_power_suc | general | bis_1_ancho (biseccion) | 2: rf_3_encaje, rf_6c_puntos_convergen | sí | by simp |
| 59 | cu_sign_product | general | bis_3_signo (biseccion) | 0 | sí | by (smt (verit, del_insts) xy xz zero_less_mult_iff) |
| 60 | cu_log2_nat_bound | general | bis_6_iteraciones (biseccion) | 0 | sí | by (smt (verit, ccfv_threshold) less_log_of_power log_bound) |
| 61 | cu_log2_power_nat_bound | general | bis_6_iteraciones (biseccion) | 0 | sí | by (smt (verit, del_insts) less_log_of_power log_bound) |
| 62 | cu_real_interval_between | general | pf_1_derivada (punto_fijo) | 0 | sí | using assms by simp |
| 63 | cu_abs_difference_symmetric | general | pf_4_decaimiento (punto_fijo) | 0 | sí | by fastforce |
| 64 | cu_iterated_lipschitz_bound | general | pf_5_a_priori (punto_fijo) | 0 | no |  |
| 65 | cu_interval_abs_distance_bound | general | pf_5_a_priori (punto_fijo) | 0 | sí | using assms by force |
| 66 | cu_real_power_nonneg | general | pf_5_a_priori (punto_fijo) | 0 | sí | using assms by presburger |
| 67 | cu_interval_abs_le_max | general | pf_5c_a_priori_max (punto_fijo) | 0 | sí | using assms by fastforce |
| 68 | cu_interval_distance_to_margin | general | pf_5c_a_priori_max (punto_fijo) | 0 | sí | using assms by auto |
| 69 | cu_iterate_fixed_point_lipschitz_bound | general | pf_5c_a_priori_max (punto_fijo) | 0 | no |  |
| 70 | cu_iterate_preserves_set | general | pf_6_a_priori_x1 (punto_fijo) | 0 | no |  |
| 71 | cu_posteriori_scalar | general | pf_6p_a_posteriori (punto_fijo) | 0 | no |  |
| 72 | cu_lipschitz_continuous | general | pf_7_existencia (punto_fijo) | 5: secante_2_cociente, secante_4c_contraccion_local, secante_5_convergencia, secante_5c_convergencia_local, secante_6c_orden_phi | no |  |
| 73 | cu_abs_distance_between | general | pf_9_cuadratico (punto_fijo) | 0 | sí | apply (use assms in fastforce)   apply (use assms in simp)   done |
| 74 | cu_abs_product_square | general | pf_9_cuadratico (punto_fijo) | 0 | sí | by (simp add: power2_eq_square) |
| 75 | cu_real_scale_mono_nonneg | general | orden_1_lineal (ordenes) | 0 | sí | by (simp add: assms(1,2) landau_omega.R_mult_left_mono) |
| 76 | cu_scale_le_nonneg | general | orden_1_lineal (ordenes) | 0 | sí | by (simp add: assms(1,2) landau_omega.R_mult_left_mono) |
| 77 | cu_real_nonneg_scale_order | general | orden_1_lineal (ordenes) | 0 | sí | by (simp add: landau_omega.R_mult_left_mono r_nonneg xy) |
| 78 | cu_scale_abs_quadratic | general | orden_3_cuadratico (ordenes) | 0 | sí | by (metis (no_types, lifting) ab_semigroup_mult_class.mult_ac(1) bound |
| 79 | cu_abs_divide_bound | general | newton_2_contraccion (newton) | 0 | sí | by (metis a_bound abs_div_pos b_pos mult.commute pos_divide_le_eq) |
| 80 | cu_abs_quotient_bound | general | newton_2_contraccion (newton) | 0 | sí | by (metis a_bound abs_div_pos b_pos mult.commute pos_divide_le_eq) |

