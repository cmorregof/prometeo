# Resumen de 20260926-233322-gpt-6-luna

Episodios: 90; llamadas: 265; costo: $0.9650.

| config | episodios | aceptados | éxito en el intento (mediana) | r_V medio | llamadas | $ |
|---|---|---|---|---|---|---|
| B | 30 | 3 | 1 | 0.21 | 79 | 0.1929 |
| B0 | 30 | 0 | — | 0.02 | 30 | 0.1440 |
| C | 30 | 4 | 1.0 | 0.31 | 156 | 0.6282 |

Etiquetas de los intentos: PROOF_FAILED 109, LEMMA_FAILED 31, INVALID_PROPOSAL 17, ACCEPTED 7, STATEMENT_DRIFT 4, TIMEOUT 1

| peldaño | dif. | config | aceptado | intento | r_V | motivo |
|---|---|---|---|---|---|---|
| rf_2_signo | 2 | B | no | — | 0.0 | nada |
| rf_2_signo | 2 | B | sí | 1 | 2.0 | aceptada |
| rf_2_signo | 2 | B0 | no | — | 0.0 | nada |
| rf_2_signo | 2 | B0 | no | — | 0.0 | sin_credito_invalid_proposal |
| rf_2_signo | 2 | C | sí | 1 | 2.0 | aceptada |
| rf_2_signo | 2 | C | sí | 2 | 2.0 | aceptada |
| rf_3_encaje | 3 | B | no | — | 0.0 | nada |
| rf_3_encaje | 3 | B | no | — | 0.0 | sin_credito_statement_drift |
| rf_3_encaje | 3 | B0 | no | — | 0.0 | nada |
| rf_3_encaje | 3 | B0 | no | — | 0.0 | nada |
| rf_3_encaje | 3 | C | no | — | 0.0 | nada |
| rf_3_encaje | 3 | C | no | — | 0.0 | nada |
| rf_4_raiz | 3 | B | no | — | 0.0 | nada |
| rf_4_raiz | 3 | B | sí | 1 | 2.0 | aceptada |
| rf_4_raiz | 3 | B0 | no | — | 0.0 | nada |
| rf_4_raiz | 3 | B0 | no | — | 0.0 | nada |
| rf_4_raiz | 3 | C | no | — | 0.0 | nada |
| rf_4_raiz | 3 | C | no | — | 0.0 | nada |
| rf_5_limites | 3 | B | no | — | 0.0 | nada |
| rf_5_limites | 3 | B | no | — | 0.0 | nada |
| rf_5_limites | 3 | B0 | no | — | 0.0 | nada |
| rf_5_limites | 3 | B0 | no | — | 0.0 | nada |
| rf_5_limites | 3 | C | no | — | 0.0 | nada |
| rf_5_limites | 3 | C | no | — | 0.0 | nada |
| rf_6_convergencia | 5 | B | no | — | 0.0 | nada |
| rf_6_convergencia | 5 | B | no | — | 0.0 | nada |
| rf_6_convergencia | 5 | B0 | no | — | 0.0 | nada |
| rf_6_convergencia | 5 | B0 | no | — | 0.0 | nada |
| rf_6_convergencia | 5 | C | no | — | 0.0 | nada |
| rf_6_convergencia | 5 | C | no | — | 0.2 | nada |
| rf_6c_puntos_convergen | 5 | B | no | — | 0.0 | nada |
| rf_6c_puntos_convergen | 5 | B | no | — | 0.0 | nada |
| rf_6c_puntos_convergen | 5 | B0 | no | — | 0.0 | nada |
| rf_6c_puntos_convergen | 5 | B0 | no | — | 0.5 | parcial |
| rf_6c_puntos_convergen | 5 | C | no | — | 0.0 | nada |
| rf_6c_puntos_convergen | 5 | C | no | — | 0.0 | nada |
| secante_1_inyectiva | 2 | B | no | — | 0.0 | nada |
| secante_1_inyectiva | 2 | B | no | — | 0.0 | nada |
| secante_1_inyectiva | 2 | B0 | no | — | 0.0 | nada |
| secante_1_inyectiva | 2 | B0 | no | — | 0.0 | nada |
| secante_1_inyectiva | 2 | C | no | — | 0.6667 | nada |
| secante_1_inyectiva | 2 | C | no | — | 0.0 | nada |
| secante_2_cociente | 2 | B | no | — | 0.0 | nada |
| secante_2_cociente | 2 | B | sí | 1 | 2.0 | aceptada |
| secante_2_cociente | 2 | B0 | no | — | 0.0 | nada |
| secante_2_cociente | 2 | B0 | no | — | 0.0 | nada |
| secante_2_cociente | 2 | C | sí | 1 | 2.0 | aceptada |
| secante_2_cociente | 2 | C | sí | 1 | 2.0 | aceptada |
| secante_3_producto | 5 | B | no | — | 0.0 | nada |
| secante_3_producto | 5 | B | no | — | 0.0 | nada |
| secante_3_producto | 5 | B0 | no | — | 0.0 | nada |
| secante_3_producto | 5 | B0 | no | — | 0.0 | nada |
| secante_3_producto | 5 | C | no | — | 0.0 | nada |
| secante_3_producto | 5 | C | no | — | 0.0 | sin_credito_invalid_proposal |
| secante_4_contraccion | 2 | B | no | — | 0.0 | nada |
| secante_4_contraccion | 2 | B | no | — | 0.0 | nada |
| secante_4_contraccion | 2 | B0 | no | — | 0.0 | nada |
| secante_4_contraccion | 2 | B0 | no | — | 0.0 | nada |
| secante_4_contraccion | 2 | C | no | — | 0.4 | nada |
| secante_4_contraccion | 2 | C | no | — | 0.0 | nada |
| secante_4c_contraccion_local | 4 | B | no | — | 0.0 | nada |
| secante_4c_contraccion_local | 4 | B | no | — | 0.0 | nada |
| secante_4c_contraccion_local | 4 | B0 | no | — | 0.0 |  |
| secante_4c_contraccion_local | 4 | B0 | no | — | 0.0 | nada |
| secante_4c_contraccion_local | 4 | C | no | — | 0.0 | nada |
| secante_4c_contraccion_local | 4 | C | no | — | 0.0 | nada |
| secante_5_convergencia | 4 | B | no | — | 0.2 | parcial |
| secante_5_convergencia | 4 | B | no | — | 0.0 | nada |
| secante_5_convergencia | 4 | B0 | no | — | 0.0 | nada |
| secante_5_convergencia | 4 | B0 | no | — | 0.0 | martillo_en_la_meta |
| secante_5_convergencia | 4 | C | no | — | 0.0 | nada |
| secante_5_convergencia | 4 | C | no | — | 0.0 | nada |
| secante_5c_convergencia_local | 5 | B | no | — | 0.0 | nada |
| secante_5c_convergencia_local | 5 | B | no | — | 0.0 | nada |
| secante_5c_convergencia_local | 5 | B0 | no | — | 0.0 |  |
| secante_5c_convergencia_local | 5 | B0 | no | — | 0.0 | nada |
| secante_5c_convergencia_local | 5 | C | no | — | 0.0 | nada |
| secante_5c_convergencia_local | 5 | C | no | — | 0.0 | nada |
| secante_6_fibonacci | 4 | B | no | — | 0.0 | nada |
| secante_6_fibonacci | 4 | B | no | — | 0.0 | nada |
| secante_6_fibonacci | 4 | B0 | no | — | 0.0 | nada |
| secante_6_fibonacci | 4 | B0 | no | — | 0.0 | nada |
| secante_6_fibonacci | 4 | C | no | — | 0.0 | sin_credito_statement_drift |
| secante_6_fibonacci | 4 | C | no | — | 0.0 | nada |
| secante_6c_orden_phi | 5 | B | no | — | 0.0 | martillo_en_la_meta |
| secante_6c_orden_phi | 5 | B | no | — | 0.0 |  |
| secante_6c_orden_phi | 5 | B0 | no | — | 0.0 |  |
| secante_6c_orden_phi | 5 | B0 | no | — | 0.0 |  |
| secante_6c_orden_phi | 5 | C | no | — | 0.0 | nada |
| secante_6c_orden_phi | 5 | C | no | — | 0.0 | nada |
