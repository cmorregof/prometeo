# Línea base: martillo solo (configuración A)

Fecha: 2026-09-24 16:54. Cuaderno: sin cuaderno. try0 5 s, Sledgehammer 60 s, en serie. Una línea cuenta solo si el juez la acepta en el kernel.

**Resueltos por el martillo: 1 de 48.** Estos peldaños no dan crédito en la Etapa 4.

43 filas salen de la caché de la primera corrida (24 sep 2026, 14:03–15:13), anterior al registro automático de suspensiones. Una auditoría posterior comparó, peldaño a peldaño, el tiempo de pared de Sledgehammer (su JSON) con el tiempo monótono medido en Python: solo secante_4c, secante_5, secante_5c y secante_6 tuvieron la máquina suspendida durante la búsqueda, y se rehicieron (más secante_6c, con una suspensión fuera de Sledgehammer).

* train: 1 de 32
* test: 0 de 16

| peldaño | método | split | dif. | versión | resuelto | fuente | Sledgehammer | juez | s | carga |
|---|---|---|---|---|---|---|---|---|---|---|
| bis_1_ancho | biseccion | train | 1 | clasica | no | sledgehammer | timeout |  | 69.5 | 6.22 |
| bis_2_encaje | biseccion | train | 2 | clasica | no | sledgehammer | timeout |  | 70.1 | 7.75 |
| bis_3_signo | biseccion | train | 2 | clasica | no | sledgehammer | timeout |  | 65.9 | 8.58 |
| bis_4_raiz | biseccion | train | 3 | clasica | no | sledgehammer | timeout |  | 81.2 | 10.44 |
| bis_5_cota | biseccion | train | 3 | debilitada | no | sledgehammer | timeout |  | 79.4 | 8.6 |
| bis_5c_cota_uniforme | biseccion | train | 3 | clasica | no | sledgehammer | timeout |  | 79.9 | 8.04 |
| bis_6_iteraciones | biseccion | train | 2 | clasica | no | sledgehammer | timeout |  | 70.1 | 8.25 |
| bis_7_convergencia | biseccion | train | 4 | clasica | no | sledgehammer | timeout |  | 76.5 | 8.26 |
| newton_1_paso | newton | train | 4 | clasica | no | sledgehammer | timeout |  | 75.0 | 7.92 |
| newton_2_contraccion | newton | train | 2 | debilitada | no | sledgehammer | timeout |  | 74.9 | 7.42 |
| newton_2c_contraccion_local | newton | train | 4 | clasica | no | sledgehammer | timeout |  | 80.2 | 7.29 |
| newton_3_decaimiento | newton | train | 2 | debilitada | no | sledgehammer | timeout |  | 75.1 | 7.25 |
| newton_4_convergencia | newton | train | 3 | debilitada | no | sledgehammer | timeout |  | 80.6 | 7.04 |
| newton_4c_convergencia_local | newton | train | 4 | clasica | no | sledgehammer | timeout |  | 80.2 | 7.22 |
| newton_5_orden2 | newton | train | 3 | debilitada | no | sledgehammer | timeout |  | 75.0 | 7.26 |
| newton_5c_orden2_local | newton | train | 4 | clasica | no | sledgehammer | timeout |  | 79.7 | 7.8 |
| newton_6c_q_orden2 | newton | train | 5 | clasica | no | sledgehammer | timeout |  | 80.2 | 7.71 |
| orden_1_lineal | ordenes | train | 1 | clasica | no | sledgehammer | timeout |  | 69.7 | 7.66 |
| orden_2_cuadratico_lineal | ordenes | train | 2 | clasica | no | sledgehammer | timeout |  | 69.9 | 7.48 |
| orden_3_cuadratico | ordenes | train | 2 | clasica | no | sledgehammer | timeout |  | 69.4 | 8.19 |
| pf_1_derivada | punto_fijo | train | 2 | clasica | no | sledgehammer | timeout |  | 75.5 | 7.79 |
| pf_2_dentro | punto_fijo | train | 1 | clasica | no | sledgehammer | timeout |  | 75.2 | 7.23 |
| pf_3_unicidad | punto_fijo | train | 2 | clasica | **sí** | sledgehammer | some | ACCEPTED | 99.0 | 3.97 |
| pf_4_decaimiento | punto_fijo | train | 2 | clasica | no | sledgehammer | timeout |  | 74.8 | 7.36 |
| pf_5_a_priori | punto_fijo | train | 2 | debilitada | no | sledgehammer | timeout |  | 74.8 | 7.4 |
| pf_5c_a_priori_max | punto_fijo | train | 2 | clasica | no | sledgehammer | timeout |  | 74.9 | 7.26 |
| pf_6_a_priori_x1 | punto_fijo | train | 3 | clasica | no | sledgehammer | timeout |  | 74.9 | 7.36 |
| pf_6p_a_posteriori | punto_fijo | train | 3 | clasica | no | sledgehammer | timeout |  | 74.6 | 7.53 |
| pf_7_existencia | punto_fijo | train | 3 | clasica | no | sledgehammer | timeout |  | 80.4 | 8.53 |
| pf_8_convergencia | punto_fijo | train | 4 | clasica | no | sledgehammer | timeout |  | 80.6 | 7.9 |
| pf_9_cuadratico | punto_fijo | train | 3 | debilitada | no | sledgehammer | timeout |  | 74.5 | 7.9 |
| pf_9c_cuadratico_medio | punto_fijo | train | 3 | clasica | no | sledgehammer | timeout |  | 75.1 | 7.91 |
| rf_1_punto | regula_falsi | test | 2 | clasica | no | sledgehammer | timeout |  | 70.3 | 7.53 |
| rf_2_signo | regula_falsi | test | 2 | clasica | no | sledgehammer | timeout |  | 66.2 | 8.54 |
| rf_3_encaje | regula_falsi | test | 3 | clasica | no | sledgehammer | timeout |  | 70.2 | 7.88 |
| rf_4_raiz | regula_falsi | test | 3 | clasica | no | sledgehammer | timeout |  | 76.4 | 7.64 |
| rf_5_limites | regula_falsi | test | 3 | clasica | no | sledgehammer | timeout |  | 75.8 | 8.12 |
| rf_6_convergencia | regula_falsi | test | 5 | debilitada | no | sledgehammer | timeout |  | 81.5 | 8.3 |
| rf_6c_puntos_convergen | regula_falsi | test | 5 | clasica | no | sledgehammer | timeout |  | 81.0 | 7.52 |
| secante_1_inyectiva | secante | test | 2 | clasica | no | sledgehammer | timeout |  | 72.9 | 7.54 |
| secante_2_cociente | secante | test | 2 | clasica | no | sledgehammer | timeout |  | 75.5 | 8.96 |
| secante_3_producto | secante | test | 5 | clasica | no | sledgehammer | timeout |  | 75.6 | 10.77 |
| secante_4_contraccion | secante | test | 2 | debilitada | no | sledgehammer | timeout |  | 75.9 | 13.68 |
| secante_4c_contraccion_local | secante | test | 4 | clasica | no | sledgehammer | timeout |  | 79.6 | 7.3 |
| secante_5_convergencia | secante | test | 4 | debilitada | no | sledgehammer | timeout |  | 75.4 | 7.58 |
| secante_5c_convergencia_local | secante | test | 5 | clasica | no | sledgehammer | timeout |  | 80.1 | 7.58 |
| secante_6_fibonacci | secante | test | 4 | debilitada | no | sledgehammer | timeout |  | 74.7 | 8.29 |
| secante_6c_orden_phi | secante | test | 5 | clasica | no | sledgehammer | timeout |  | 80.3 | 7.94 |

## Líneas aceptadas

* `pf_3_unicidad`: `by (smt (verit, del_insts) contr fp fq hp hq k1 mult_le_cancel_right1)`
