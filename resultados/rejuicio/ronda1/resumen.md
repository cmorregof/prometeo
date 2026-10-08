# Re-adjudicación del juez: `ronda1`

Generado el 2026-10-08 15:13 con `unirl/tools/rejuzgar.py` (referencia-2026-10-08), sin llamar a la API. Corridas: `cuaderno/20260926-201727-gpt-6-luna`, `evaluacion/20260926-201727-gpt-6-luna`, `pareada_luna/20260926-201727-gpt-6-luna`, `pareada_sol/20260926-201727-gpt-6-sol`, `evaluacion/20260926-233322-gpt-6-luna`, `pareada_luna/20260926-233322-gpt-6-luna`, `pareada_sol/20260926-233322-gpt-6-sol`, `evaluacion_E/20260927-084149-gpt-6-luna`, `pareada_luna/20260927-084149-gpt-6-luna`, `pareada_sol/20260927-084149-gpt-6-sol`, `evaluacion_E/20260927-090507-gpt-6-luna`, `pareada_luna/20260927-090507-gpt-6-luna`, `pareada_sol/20260927-090507-gpt-6-sol`. Referencia: límite 600.0 s, sandbox sí. Cada intento se compara con lo que dice la especificación V aplicada por una implementación aparte (cabecera del guion).

## 1. Veredictos por configuración (intentos)

| fase | modelo | config | intentos | concordante | concordante_contaminado | FN | FP | regla_estricta | tiempo | indeterminado | sin_juicio |
|---|---|---|---|---|---|---|---|---|---|---|---|
| cuaderno | gpt-6-luna | F | 109 | 53 | 10 | 0 | 0 | 0 | 0 | 6 | 40 |
| evaluacion | gpt-6-luna | B | 34 | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 18 |
| evaluacion | gpt-6-luna | B0 | 34 | 14 | 0 | 0 | 0 | 0 | 0 | 0 | 20 |
| evaluacion | gpt-6-luna | C | 116 | 55 | 0 | 0 | 0 | 0 | 0 | 0 | 61 |
| evaluacion_E | gpt-6-luna | E | 122 | 50 | 13 | 0 | 0 | 0 | 0 | 14 | 45 |
| pareada_luna | gpt-6-luna | C3 | 48 | 29 | 0 | 0 | 0 | 0 | 0 | 0 | 19 |
| pareada_luna | gpt-6-luna | E3 | 46 | 24 | 4 | 0 | 0 | 0 | 0 | 7 | 11 |
| pareada_sol | gpt-6-sol | C3 | 45 | 38 | 0 | 0 | 0 | 0 | 0 | 0 | 7 |
| pareada_sol | gpt-6-sol | E3 | 47 | 22 | 6 | 0 | 0 | 0 | 0 | 7 | 12 |

## 2. Sensibilidad y falsos positivos por configuración

Se = intentos que el juez aceptó entre los que V acepta (con sus reglas y su límite); la cota es la de la regla de tres (95 %) cuando no hubo falsos negativos entre los rechazos re-juzgados.

| modelo | config | V acepta | el juez acepta | FN | Se | FP | rechazos re-juzgados | cota FN si FN = 0 |
|---|---|---|---|---|---|---|---|---|
| gpt-6-luna | B | 5 | 5 | 0 | 1,00 | 0 | 11 | 0,238 |
| gpt-6-luna | B0 | 0 | 0 | 0 | — | 0 | 14 | 0,193 |
| gpt-6-luna | C | 7 | 7 | 0 | 1,00 | 0 | 48 | 0,061 |
| gpt-6-luna | C3 | 4 | 4 | 0 | 1,00 | 0 | 25 | 0,113 |
| gpt-6-luna | E | 4 | 4 | 0 | 1,00 | 0 | 59 | 0,050 |
| gpt-6-luna | E3 | 2 | 2 | 0 | 1,00 | 0 | 26 | 0,109 |
| gpt-6-luna | F | 10 | 10 | 0 | 1,00 | 0 | 53 | 0,055 |
| gpt-6-sol | C3 | 4 | 4 | 0 | 1,00 | 0 | 34 | 0,084 |
| gpt-6-sol | E3 | 4 | 4 | 0 | 1,00 | 0 | 24 | 0,117 |

## 3. Casos que no son concordantes

| config | episodio | intento | juez | categoría | detalle | primer error del juez | primer error de la referencia | archivo |
|---|---|---|---|---|---|---|---|---|
| E | secante_1_inyectiva#E#1 | 4 | LEMMA_FAILED | concordante_contaminado | el juez culpó a un lema del cuaderno; la referencia, a la prueba | *** Duplicate fixed variable(s): "x" | *** Failed to finish proof (line 140 of "~/isabelle/scratch/rejuicio/rj-u1b9xhm5/Rejuicio.thy"): | `evaluacion_E/20260927-090507-gpt-6-luna/llamadas.jsonl:26` |
| E | secante_1_inyectiva#E#2 | 1 | LEMMA_FAILED | concordante_contaminado | el juez culpó a un lema del cuaderno; la referencia, a la prueba | *** Duplicate fixed variable(s): "x" | *** Failed to apply initial proof method (line 173 of "~/isabelle/scratch/rejuicio/rj-f9v0kcr_/Rejuicio.thy"): | `evaluacion_E/20260927-090507-gpt-6-luna/llamadas.jsonl:30` |
| E | secante_1_inyectiva#E#2 | 2 | LEMMA_FAILED | concordante_contaminado | el juez culpó a un lema del cuaderno; la referencia, a la prueba | *** Duplicate fixed variable(s): "x" | *** Failed to apply initial proof method (line 175 of "~/isabelle/scratch/rejuicio/rj-zgsrcxte/Rejuicio.thy"): | `evaluacion_E/20260927-090507-gpt-6-luna/llamadas.jsonl:31` |
| E | secante_1_inyectiva#E#2 | 3 | LEMMA_FAILED | concordante_contaminado | el juez culpó a un lema del cuaderno; la referencia, a la prueba | *** Duplicate fixed variable(s): "x" | *** Failed to apply initial proof method (line 174 of "~/isabelle/scratch/rejuicio/rj-0ljveiqi/Rejuicio.thy"): | `evaluacion_E/20260927-090507-gpt-6-luna/llamadas.jsonl:32` |
| E | secante_1_inyectiva#E#2 | 4 | LEMMA_FAILED | concordante_contaminado | el juez culpó a un lema del cuaderno; la referencia, a la prueba | *** Duplicate fixed variable(s): "x" | *** Failed to apply initial proof method (line 174 of "~/isabelle/scratch/rejuicio/rj-0j_wmz_b/Rejuicio.thy"): | `evaluacion_E/20260927-090507-gpt-6-luna/llamadas.jsonl:33` |
| E | secante_2_cociente#E#1 | 2 | LEMMA_FAILED | concordante_contaminado | el juez culpó a un lema del cuaderno; la referencia, a la prueba | *** Duplicate fixed variable(s): "x" | *** Failed to finish proof (line 166 of "~/isabelle/scratch/rejuicio/rj-degfsfqz/Rejuicio.thy"): | `evaluacion_E/20260927-090507-gpt-6-luna/llamadas.jsonl:42` |
| E | secante_2_cociente#E#1 | 3 | LEMMA_FAILED | concordante_contaminado | el juez culpó a un lema del cuaderno; la referencia, a la prueba | *** Duplicate fixed variable(s): "x" | *** Failed to finish proof (line 169 of "~/isabelle/scratch/rejuicio/rj-hiox1xm0/Rejuicio.thy"): | `evaluacion_E/20260927-090507-gpt-6-luna/llamadas.jsonl:44` |
| E | secante_2_cociente#E#1 | 4 | LEMMA_FAILED | concordante_contaminado | el juez culpó a un lema del cuaderno; la referencia, a la prueba | *** Duplicate fixed variable(s): "x" | *** Failed to finish proof (line 169 of "~/isabelle/scratch/rejuicio/rj-f8b2yuds/Rejuicio.thy"): | `evaluacion_E/20260927-090507-gpt-6-luna/llamadas.jsonl:46` |
| E | secante_2_cociente#E#2 | 1 | LEMMA_FAILED | concordante_contaminado | el juez culpó a un lema del cuaderno; la referencia, a la prueba | *** Duplicate fixed variable(s): "x" | *** Undefined fact: "has_real_derivative_imp_continuous" (line 184 of "~/isabelle/scratch/rejuicio/rj-5zkmr3ax/Rejuicio.thy") | `evaluacion_E/20260927-090507-gpt-6-luna/llamadas.jsonl:41` |
| E | secante_2_cociente#E#2 | 2 | LEMMA_FAILED | concordante_contaminado | el juez culpó a un lema del cuaderno; la referencia, a la prueba | *** Duplicate fixed variable(s): "x" | *** Undefined fact: "has_real_derivative_imp_continuous" (line 196 of "~/isabelle/scratch/rejuicio/rj-1epwcsw1/Rejuicio.thy") | `evaluacion_E/20260927-090507-gpt-6-luna/llamadas.jsonl:43` |
| E | secante_2_cociente#E#2 | 3 | LEMMA_FAILED | concordante_contaminado | el juez culpó a un lema del cuaderno; la referencia, a la prueba | *** Duplicate fixed variable(s): "x" | *** Undefined fact: "has_real_derivative_imp_continuous" (line 193 of "~/isabelle/scratch/rejuicio/rj-w_6pezej/Rejuicio.thy") | `evaluacion_E/20260927-090507-gpt-6-luna/llamadas.jsonl:45` |
| E | secante_2_cociente#E#2 | 4 | LEMMA_FAILED | concordante_contaminado | el juez culpó a un lema del cuaderno; la referencia, a la prueba | *** Duplicate fixed variable(s): "x" | *** Undefined fact: "has_real_derivative_imp_continuous" (line 204 of "~/isabelle/scratch/rejuicio/rj-v_kfos_6/Rejuicio.thy") | `evaluacion_E/20260927-090507-gpt-6-luna/llamadas.jsonl:47` |
| E | secante_4_contraccion#E#2 | 2 | LEMMA_FAILED | concordante_contaminado | el juez culpó a un lema del cuaderno; la referencia, a la prueba | *** Duplicate fixed variable(s): "x" | *** Failed to apply initial proof method: | `evaluacion_E/20260927-090507-gpt-6-luna/llamadas.jsonl:74` |
| E3 | secante_1_inyectiva#E3#1 | 2 | LEMMA_FAILED | concordante_contaminado | el juez culpó a un lema del cuaderno; la referencia, a la prueba | *** Duplicate fixed variable(s): "x" | *** Failed to finish proof (line 149 of "~/isabelle/scratch/rejuicio/rj-rwl3oslp/Rejuicio.thy"): | `pareada_luna/20260927-084149-gpt-6-luna/llamadas.jsonl:27` |
| E3 | secante_1_inyectiva#E3#1 | 3 | LEMMA_FAILED | concordante_contaminado | el juez culpó a un lema del cuaderno; la referencia, a la prueba | *** Duplicate fixed variable(s): "x" | *** Failed to finish proof (line 149 of "~/isabelle/scratch/rejuicio/rj-4oxkgd5y/Rejuicio.thy"): | `pareada_luna/20260927-084149-gpt-6-luna/llamadas.jsonl:29` |
| E3 | secante_1_inyectiva#E3#1 | 3 | LEMMA_FAILED | concordante_contaminado | el juez culpó a un lema del cuaderno; la referencia, a la prueba | *** Duplicate fixed variable(s): "x" | *** Failed to refine any pending goal | `pareada_sol/20260927-084149-gpt-6-sol/llamadas.jsonl:26` |
| E3 | secante_2_cociente#E3#1 | 1 | LEMMA_FAILED | concordante_contaminado | el juez culpó a un lema del cuaderno; la referencia, a la prueba | *** Duplicate fixed variable(s): "x" | *** Undefined fact: "abs_le" (line 140 of "~/isabelle/scratch/rejuicio/rj-gg2b5ezr/Rejuicio.thy") | `pareada_luna/20260927-090507-gpt-6-luna/llamadas.jsonl:4` |
| E3 | secante_2_cociente#E3#1 | 2 | LEMMA_FAILED | concordante_contaminado | el juez culpó a un lema del cuaderno; la referencia, a la prueba | *** Duplicate fixed variable(s): "x" | *** Failed to finish proof (line 146 of "~/isabelle/scratch/rejuicio/rj-0xoz2i5u/Rejuicio.thy"): | `pareada_sol/20260927-090507-gpt-6-sol/llamadas.jsonl:4` |
| E3 | secante_2_cociente#E3#1 | 3 | LEMMA_FAILED | concordante_contaminado | el juez culpó a un lema del cuaderno; la referencia, a la prueba | *** Duplicate fixed variable(s): "x" | *** Failed to finish proof (line 152 of "~/isabelle/scratch/rejuicio/rj-i03dqszq/Rejuicio.thy"): | `pareada_luna/20260927-090507-gpt-6-luna/llamadas.jsonl:7` |
| E3 | secante_2_cociente#E3#1 | 3 | LEMMA_FAILED | concordante_contaminado | el juez culpó a un lema del cuaderno; la referencia, a la prueba | *** Duplicate fixed variable(s): "x" | *** Failed to finish proof (line 146 of "~/isabelle/scratch/rejuicio/rj-labg6pyd/Rejuicio.thy"): | `pareada_sol/20260927-090507-gpt-6-sol/llamadas.jsonl:6` |
| E3 | secante_3_producto#E3#1 | 1 | LEMMA_FAILED | concordante_contaminado | el juez culpó a un lema del cuaderno; la referencia, a la prueba | *** Duplicate fixed variable(s): "x" | *** Undefined method: "martillo" (line 141 of "~/isabelle/scratch/rejuicio/rj-ecfyj_el/Rejuicio.thy") | `pareada_sol/20260927-090507-gpt-6-sol/llamadas.jsonl:8` |
| E3 | secante_3_producto#E3#1 | 3 | LEMMA_FAILED | concordante_contaminado | el juez culpó a un lema del cuaderno; la referencia, a la prueba | *** Duplicate fixed variable(s): "x" | *** Failed to apply initial proof method (line 155 of "~/isabelle/scratch/rejuicio/rj-x74xgow5/Rejuicio.thy"): | `pareada_sol/20260927-090507-gpt-6-sol/llamadas.jsonl:12` |
| E3 | secante_4_contraccion#E3#1 | 3 | LEMMA_FAILED | concordante_contaminado | el juez culpó a un lema del cuaderno; la referencia, a la prueba | *** Duplicate fixed variable(s): "x" | *** Failed to finish proof (line 143 of "~/isabelle/scratch/rejuicio/rj-d433dpcs/Rejuicio.thy"): | `pareada_sol/20260927-090507-gpt-6-sol/llamadas.jsonl:21` |
| F | newton_1_paso#1 | 3 | LEMMA_FAILED | concordante_contaminado | el juez culpó a un lema del cuaderno; la referencia, a la prueba | *** Duplicate fixed variable(s): "x" |  | `cuaderno/20260926-201727-gpt-6-luna/llamadas.jsonl:99` |
| F | newton_1_paso#1 | 4 | LEMMA_FAILED | concordante_contaminado | el juez culpó a un lema del cuaderno; la referencia, a la prueba | *** Duplicate fixed variable(s): "x" |  | `cuaderno/20260926-201727-gpt-6-luna/llamadas.jsonl:100` |
| F | pf_1_derivada#1 | 2 | LEMMA_FAILED | concordante_contaminado | el juez culpó a un lema del cuaderno; la referencia, a la prueba | *** Duplicate fixed variable(s): "x" | *** Undefined fact: "has_real_derivative_imp_continuous" (line 128 of "~/isabelle/scratch/rejuicio/rj-80yxhlaw/Rejuicio.thy") | `cuaderno/20260926-201727-gpt-6-luna/llamadas.jsonl:43` |
| F | pf_1_derivada#1 | 3 | LEMMA_FAILED | concordante_contaminado | el juez culpó a un lema del cuaderno; la referencia, a la prueba | *** Duplicate fixed variable(s): "x" | *** Undefined fact: "has_real_derivative_imp_continuous" (line 128 of "~/isabelle/scratch/rejuicio/rj-xn3iess1/Rejuicio.thy") | `cuaderno/20260926-201727-gpt-6-luna/llamadas.jsonl:44` |
| F | pf_1_derivada#1 | 4 | LEMMA_FAILED | concordante_contaminado | el juez culpó a un lema del cuaderno; la referencia, a la prueba | *** Duplicate fixed variable(s): "x" | *** Undefined fact: "has_real_derivative_imp_continuous" (line 128 of "~/isabelle/scratch/rejuicio/rj-eclcj_u2/Rejuicio.thy") | `cuaderno/20260926-201727-gpt-6-luna/llamadas.jsonl:45` |
| F | pf_9_cuadratico#1 | 4 | LEMMA_FAILED | concordante_contaminado | el juez culpó a un lema del cuaderno; la referencia, a la prueba | *** Duplicate fixed variable(s): "x" | *** Undefined fact: "has_real_derivative_imp_continuous" (line 165 of "~/isabelle/scratch/rejuicio/rj-60s3lm6w/Rejuicio.thy") | `cuaderno/20260926-201727-gpt-6-luna/llamadas.jsonl:79` |
| F | pf_9c_cuadratico_medio#1 | 1 | LEMMA_FAILED | concordante_contaminado | el juez culpó a un lema del cuaderno; la referencia, a la prueba | *** Duplicate fixed variable(s): "x" | *** Undefined fact: "has_real_derivative_def" (line 134 of "~/isabelle/scratch/rejuicio/rj-ean29n_q/Rejuicio.thy") | `cuaderno/20260926-201727-gpt-6-luna/llamadas.jsonl:82` |
| F | pf_9c_cuadratico_medio#1 | 2 | LEMMA_FAILED | concordante_contaminado | el juez culpó a un lema del cuaderno; la referencia, a la prueba | *** Duplicate fixed variable(s): "x" | *** Undefined fact: "has_real_derivative_def" (line 145 of "~/isabelle/scratch/rejuicio/rj-j5vi4hdi/Rejuicio.thy") | `cuaderno/20260926-201727-gpt-6-luna/llamadas.jsonl:83` |
| F | pf_9c_cuadratico_medio#1 | 3 | LEMMA_FAILED | concordante_contaminado | el juez culpó a un lema del cuaderno; la referencia, a la prueba | *** Duplicate fixed variable(s): "x" | *** Undefined fact: "has_real_derivative_def" (line 144 of "~/isabelle/scratch/rejuicio/rj-n33riqz9/Rejuicio.thy") | `cuaderno/20260926-201727-gpt-6-luna/llamadas.jsonl:84` |
| F | pf_9c_cuadratico_medio#1 | 4 | LEMMA_FAILED | concordante_contaminado | el juez culpó a un lema del cuaderno; la referencia, a la prueba | *** Duplicate fixed variable(s): "x" | *** Undefined fact: "has_real_derivative_def" (line 145 of "~/isabelle/scratch/rejuicio/rj-txiuphq6/Rejuicio.thy") | `cuaderno/20260926-201727-gpt-6-luna/llamadas.jsonl:85` |
| E | secante_2_cociente#E#1 | 1 | PROOF_FAILED | indeterminado | marcas abiertas: el martillo corrió con una biblioteca que no compilaba | *** Duplicate fixed variable(s): "x" |  | `evaluacion_E/20260927-090507-gpt-6-luna/llamadas.jsonl:40` |
| E | secante_3_producto#E#1 | 1 | PROOF_FAILED | indeterminado | marcas abiertas: el martillo corrió con una biblioteca que no compilaba | *** Duplicate fixed variable(s): "x" |  | `evaluacion_E/20260927-090507-gpt-6-luna/llamadas.jsonl:55` |
| E | secante_3_producto#E#1 | 2 | PROOF_FAILED | indeterminado | marcas abiertas: el martillo corrió con una biblioteca que no compilaba | *** Duplicate fixed variable(s): "x" |  | `evaluacion_E/20260927-090507-gpt-6-luna/llamadas.jsonl:58` |
| E | secante_3_producto#E#1 | 3 | PROOF_FAILED | indeterminado | marcas abiertas: el martillo corrió con una biblioteca que no compilaba | *** Duplicate fixed variable(s): "x" |  | `evaluacion_E/20260927-090507-gpt-6-luna/llamadas.jsonl:61` |
| E | secante_3_producto#E#1 | 4 | PROOF_FAILED | indeterminado | marcas abiertas: el martillo corrió con una biblioteca que no compilaba | *** Duplicate fixed variable(s): "x" |  | `evaluacion_E/20260927-090507-gpt-6-luna/llamadas.jsonl:64` |
| E | secante_3_producto#E#2 | 1 | PROOF_FAILED | indeterminado | marcas abiertas: el martillo corrió con una biblioteca que no compilaba | *** Duplicate fixed variable(s): "x" |  | `evaluacion_E/20260927-090507-gpt-6-luna/llamadas.jsonl:56` |
| E | secante_3_producto#E#2 | 2 | PROOF_FAILED | indeterminado | marcas abiertas: el martillo corrió con una biblioteca que no compilaba | *** Duplicate fixed variable(s): "x" |  | `evaluacion_E/20260927-090507-gpt-6-luna/llamadas.jsonl:59` |
| E | secante_3_producto#E#2 | 3 | PROOF_FAILED | indeterminado | marcas abiertas: el martillo corrió con una biblioteca que no compilaba | *** Duplicate fixed variable(s): "x" |  | `evaluacion_E/20260927-090507-gpt-6-luna/llamadas.jsonl:62` |
| E | secante_3_producto#E#2 | 4 | PROOF_FAILED | indeterminado | marcas abiertas: el martillo corrió con una biblioteca que no compilaba | *** Duplicate fixed variable(s): "x" |  | `evaluacion_E/20260927-090507-gpt-6-luna/llamadas.jsonl:66` |
| E | secante_4_contraccion#E#1 | 1 | PROOF_FAILED | indeterminado | marcas abiertas: el martillo corrió con una biblioteca que no compilaba | *** Duplicate fixed variable(s): "x" |  | `evaluacion_E/20260927-090507-gpt-6-luna/llamadas.jsonl:57` |
| E | secante_4_contraccion#E#1 | 2 | PROOF_FAILED | indeterminado | marcas abiertas: el martillo corrió con una biblioteca que no compilaba | *** Duplicate fixed variable(s): "x" |  | `evaluacion_E/20260927-090507-gpt-6-luna/llamadas.jsonl:60` |
| E | secante_4_contraccion#E#1 | 3 | PROOF_FAILED | indeterminado | marcas abiertas: el martillo corrió con una biblioteca que no compilaba | *** Duplicate fixed variable(s): "x" |  | `evaluacion_E/20260927-090507-gpt-6-luna/llamadas.jsonl:63` |
| E | secante_4_contraccion#E#1 | 4 | PROOF_FAILED | indeterminado | marcas abiertas: el martillo corrió con una biblioteca que no compilaba | *** Duplicate fixed variable(s): "x" |  | `evaluacion_E/20260927-090507-gpt-6-luna/llamadas.jsonl:69` |
| E | secante_4_contraccion#E#2 | 1 | PROOF_FAILED | indeterminado | marcas abiertas: el martillo corrió con una biblioteca que no compilaba | *** Duplicate fixed variable(s): "x" |  | `evaluacion_E/20260927-090507-gpt-6-luna/llamadas.jsonl:73` |
| E3 | secante_1_inyectiva#E3#1 | 1 | PROOF_FAILED | indeterminado | marcas abiertas: el martillo corrió con una biblioteca que no compilaba | *** Duplicate fixed variable(s): "x" |  | `pareada_luna/20260927-084149-gpt-6-luna/llamadas.jsonl:24` |
| E3 | secante_1_inyectiva#E3#1 | 1 | PROOF_FAILED | indeterminado | marcas abiertas: el martillo corrió con una biblioteca que no compilaba | *** Duplicate fixed variable(s): "x" |  | `pareada_sol/20260927-084149-gpt-6-sol/llamadas.jsonl:23` |
| E3 | secante_1_inyectiva#E3#1 | 2 | PROOF_FAILED | indeterminado | marcas abiertas: el martillo corrió con una biblioteca que no compilaba | *** Duplicate fixed variable(s): "x" |  | `pareada_sol/20260927-084149-gpt-6-sol/llamadas.jsonl:24` |
| E3 | secante_2_cociente#E3#1 | 1 | PROOF_FAILED | indeterminado | marcas abiertas: el martillo corrió con una biblioteca que no compilaba | *** Duplicate fixed variable(s): "x" |  | `pareada_sol/20260927-090507-gpt-6-sol/llamadas.jsonl:3` |
| E3 | secante_2_cociente#E3#1 | 2 | PROOF_FAILED | indeterminado | marcas abiertas: el martillo corrió con una biblioteca que no compilaba | *** Duplicate fixed variable(s): "x" |  | `pareada_luna/20260927-090507-gpt-6-luna/llamadas.jsonl:6` |
| E3 | secante_3_producto#E3#1 | 1 | PROOF_FAILED | indeterminado | marcas abiertas: el martillo corrió con una biblioteca que no compilaba | *** Duplicate fixed variable(s): "x" |  | `pareada_luna/20260927-090507-gpt-6-luna/llamadas.jsonl:3` |
| E3 | secante_3_producto#E3#1 | 2 | PROOF_FAILED | indeterminado | marcas abiertas: el martillo corrió con una biblioteca que no compilaba | *** Duplicate fixed variable(s): "x" |  | `pareada_luna/20260927-090507-gpt-6-luna/llamadas.jsonl:5` |
| E3 | secante_3_producto#E3#1 | 2 | PROOF_FAILED | indeterminado | marcas abiertas: el martillo corrió con una biblioteca que no compilaba | *** Duplicate fixed variable(s): "x" |  | `pareada_sol/20260927-090507-gpt-6-sol/llamadas.jsonl:10` |
| E3 | secante_3_producto#E3#1 | 3 | PROOF_FAILED | indeterminado | marcas abiertas: el martillo corrió con una biblioteca que no compilaba | *** Duplicate fixed variable(s): "x" |  | `pareada_luna/20260927-090507-gpt-6-luna/llamadas.jsonl:9` |
| E3 | secante_4_contraccion#E3#1 | 1 | PROOF_FAILED | indeterminado | marcas abiertas: el martillo corrió con una biblioteca que no compilaba | *** Duplicate fixed variable(s): "x" |  | `pareada_luna/20260927-090507-gpt-6-luna/llamadas.jsonl:11` |
| E3 | secante_4_contraccion#E3#1 | 1 | PROOF_FAILED | indeterminado | marcas abiertas: el martillo corrió con una biblioteca que no compilaba | *** Duplicate fixed variable(s): "x" |  | `pareada_sol/20260927-090507-gpt-6-sol/llamadas.jsonl:16` |
| E3 | secante_4_contraccion#E3#1 | 2 | PROOF_FAILED | indeterminado | marcas abiertas: el martillo corrió con una biblioteca que no compilaba | *** Duplicate fixed variable(s): "x" |  | `pareada_luna/20260927-090507-gpt-6-luna/llamadas.jsonl:20` |
| E3 | secante_4_contraccion#E3#1 | 2 | PROOF_FAILED | indeterminado | marcas abiertas: el martillo corrió con una biblioteca que no compilaba | *** Duplicate fixed variable(s): "x" |  | `pareada_sol/20260927-090507-gpt-6-sol/llamadas.jsonl:19` |
| E3 | secante_5_convergencia#E3#1 | 2 | PROOF_FAILED | indeterminado | la compilación falló fuera del texto del agente | *** Bad context for command "ML" (line 149 of "~/isabelle/scratch/gd-final-tnit0dtm/Final.thy") | *** Bad context for command "ML" (line 153 of "~/isabelle/scratch/rejuicio/rj-vfc2v3s6/Rejuicio.thy") | `pareada_sol/20260927-090507-gpt-6-sol/llamadas.jsonl:24` |
| F | newton_1_paso#1 | 1 | PROOF_FAILED | indeterminado | marcas abiertas: el martillo corrió con una biblioteca que no compilaba | *** Duplicate fixed variable(s): "x" |  | `cuaderno/20260926-201727-gpt-6-luna/llamadas.jsonl:97` |
| F | newton_1_paso#1 | 2 | PROOF_FAILED | indeterminado | marcas abiertas: el martillo corrió con una biblioteca que no compilaba | *** Duplicate fixed variable(s): "x" |  | `cuaderno/20260926-201727-gpt-6-luna/llamadas.jsonl:98` |
| F | newton_2_contraccion#1 | 3 | PROOF_FAILED | indeterminado | marcas abiertas: el martillo corrió con una biblioteca que no compilaba | *** Duplicate fixed variable(s): "x" |  | `cuaderno/20260926-201727-gpt-6-luna/llamadas.jsonl:105` |
| F | newton_2_contraccion#1 | 4 | PROOF_FAILED | indeterminado | marcas abiertas: el martillo corrió con una biblioteca que no compilaba | *** Duplicate fixed variable(s): "x" |  | `cuaderno/20260926-201727-gpt-6-luna/llamadas.jsonl:106` |
| F | pf_1_derivada#1 | 1 | PROOF_FAILED | indeterminado | marcas abiertas: el martillo corrió con una biblioteca que no compilaba | *** Duplicate fixed variable(s): "x" |  | `cuaderno/20260926-201727-gpt-6-luna/llamadas.jsonl:42` |
| F | pf_9_cuadratico#1 | 3 | PROOF_FAILED | indeterminado | marcas abiertas: el martillo corrió con una biblioteca que no compilaba | *** Duplicate fixed variable(s): "x" |  | `cuaderno/20260926-201727-gpt-6-luna/llamadas.jsonl:78` |

## 4. Episodios: juez frente a referencia

Un episodio auditado vale 1 si alguno de sus intentos es válido según V; queda indeterminado si ninguno lo es y alguno no se pudo juzgar. «Contaminado»: antes del primer intento válido hubo uno cuya retroalimentación culpó al cuaderno o que no se pudo juzgar; ese episodio habría seguido otra trayectoria con un juez correcto y hay que volver a correrlo para conocer su resultado contrafactual.

| modelo | config | episodios | aceptados (juez) | válidos (auditados) | indeterminados | contaminados |
|---|---|---|---|---|---|---|
| gpt-6-luna | B | 32 | 4 | 4 | 0 | 0 |
| gpt-6-luna | B0 | 32 | 0 | 0 | 0 | 0 |
| gpt-6-luna | C | 32 | 6 | 6 | 0 | 0 |
| gpt-6-luna | C3 | 16 | 4 | 4 | 0 | 0 |
| gpt-6-luna | E | 32 | 4 | 4 | 5 | 8 |
| gpt-6-luna | E3 | 16 | 2 | 2 | 4 | 4 |
| gpt-6-luna | F | 32 | 10 | 10 | 4 | 5 |
| gpt-6-sol | C3 | 16 | 4 | 4 | 0 | 0 |
| gpt-6-sol | E3 | 16 | 4 | 4 | 5 | 5 |

Control: 0 episodios en que la agregación de los intentos difiere de `episodios.jsonl` (debería ser 0) y 0 episodios sin fila en `episodios.jsonl` (interrumpidos y nunca repetidos).

## 5. McNemar recalculado (peldaños de test)

b = gana la segunda configuración, b' = gana la primera; p exacto bilateral. «excluir», «0» y «1»: qué se hace con los episodios indeterminados en la versión auditada.

| comparación | unidad | veredictos | indeterminados | pares | b | b' | p |
|---|---|---|---|---|---|---|---|
| gpt-6-luna: C frente a E | peldaño y episodio | juez | — | 32 | 0 | 2 | 0,500 |
| gpt-6-luna: C frente a E | peldaño y episodio | auditados | excluir | 27 | 0 | 1 | 1,000 |
| gpt-6-luna: C frente a E | peldaño y episodio | auditados | 0 | 32 | 0 | 2 | 0,500 |
| gpt-6-luna: C frente a E | peldaño y episodio | auditados | 1 | 32 | 4 | 1 | 0,375 |
| gpt-6-luna: C frente a E | colapsado por peldaño | juez | — | 16 | 0 | 1 | 1,000 |
| gpt-6-luna: C frente a E | colapsado por peldaño | auditados | excluir | 13 | 0 | 0 | — |
| gpt-6-luna: C frente a E | colapsado por peldaño | auditados | 0 | 16 | 0 | 1 | 1,000 |
| gpt-6-luna: C frente a E | colapsado por peldaño | auditados | 1 | 16 | 2 | 0 | 0,500 |
| gpt-6-luna: C3 frente a E3 | peldaño y episodio | juez | — | 16 | 0 | 2 | 0,500 |
| gpt-6-luna: C3 frente a E3 | peldaño y episodio | auditados | excluir | 12 | 0 | 0 | — |
| gpt-6-luna: C3 frente a E3 | peldaño y episodio | auditados | 0 | 16 | 0 | 2 | 0,500 |
| gpt-6-luna: C3 frente a E3 | peldaño y episodio | auditados | 1 | 16 | 2 | 0 | 0,500 |
| gpt-6-luna: C3 frente a E3 | colapsado por peldaño | juez | — | 16 | 0 | 2 | 0,500 |
| gpt-6-luna: C3 frente a E3 | colapsado por peldaño | auditados | excluir | 12 | 0 | 0 | — |
| gpt-6-luna: C3 frente a E3 | colapsado por peldaño | auditados | 0 | 16 | 0 | 2 | 0,500 |
| gpt-6-luna: C3 frente a E3 | colapsado por peldaño | auditados | 1 | 16 | 2 | 0 | 0,500 |
| gpt-6-luna: C frente a B0 | peldaño y episodio | juez | — | 32 | 0 | 6 | 0,031 |
| gpt-6-luna: C frente a B0 | peldaño y episodio | auditados | excluir | 32 | 0 | 6 | 0,031 |
| gpt-6-luna: C frente a B0 | peldaño y episodio | auditados | 0 | 32 | 0 | 6 | 0,031 |
| gpt-6-luna: C frente a B0 | peldaño y episodio | auditados | 1 | 32 | 0 | 6 | 0,031 |
| gpt-6-luna: C frente a B0 | colapsado por peldaño | juez | — | 16 | 0 | 3 | 0,250 |
| gpt-6-luna: C frente a B0 | colapsado por peldaño | auditados | excluir | 16 | 0 | 3 | 0,250 |
| gpt-6-luna: C frente a B0 | colapsado por peldaño | auditados | 0 | 16 | 0 | 3 | 0,250 |
| gpt-6-luna: C frente a B0 | colapsado por peldaño | auditados | 1 | 16 | 0 | 3 | 0,250 |
| gpt-6-luna: C frente a B | peldaño y episodio | juez | — | 32 | 1 | 3 | 0,625 |
| gpt-6-luna: C frente a B | peldaño y episodio | auditados | excluir | 32 | 1 | 3 | 0,625 |
| gpt-6-luna: C frente a B | peldaño y episodio | auditados | 0 | 32 | 1 | 3 | 0,625 |
| gpt-6-luna: C frente a B | peldaño y episodio | auditados | 1 | 32 | 1 | 3 | 0,625 |
| gpt-6-luna: C frente a B | colapsado por peldaño | juez | — | 16 | 1 | 1 | 1,000 |
| gpt-6-luna: C frente a B | colapsado por peldaño | auditados | excluir | 16 | 1 | 1 | 1,000 |
| gpt-6-luna: C frente a B | colapsado por peldaño | auditados | 0 | 16 | 1 | 1 | 1,000 |
| gpt-6-luna: C frente a B | colapsado por peldaño | auditados | 1 | 16 | 1 | 1 | 1,000 |
| gpt-6-sol: C3 frente a E3 | peldaño y episodio | juez | — | 16 | 1 | 1 | 1,000 |
| gpt-6-sol: C3 frente a E3 | peldaño y episodio | auditados | excluir | 11 | 1 | 0 | 1,000 |
| gpt-6-sol: C3 frente a E3 | peldaño y episodio | auditados | 0 | 16 | 1 | 1 | 1,000 |
| gpt-6-sol: C3 frente a E3 | peldaño y episodio | auditados | 1 | 16 | 5 | 0 | 0,062 |
| gpt-6-sol: C3 frente a E3 | colapsado por peldaño | juez | — | 16 | 1 | 1 | 1,000 |
| gpt-6-sol: C3 frente a E3 | colapsado por peldaño | auditados | excluir | 11 | 1 | 0 | 1,000 |
| gpt-6-sol: C3 frente a E3 | colapsado por peldaño | auditados | 0 | 16 | 1 | 1 | 1,000 |
| gpt-6-sol: C3 frente a E3 | colapsado por peldaño | auditados | 1 | 16 | 5 | 0 | 0,062 |

## 6. Cómo leerlo

* Por solidez, el juez solo puede fallar por falsos negativos; un FP aquí es una alarma: revisa el caso a mano.
* Si Se cambia entre configuraciones, la comparación está sesgada hacia la de mayor Se, aunque cada veredicto por separado parezca razonable. Si Se es igual en todas, la prueba conserva su nivel y solo pierde potencia.
* `regla_estricta` no es un error del juez: son pruebas válidas para el kernel que violan una regla declarada. Si su frecuencia cambia entre configuraciones, conviene saberlo.
* Los episodios contaminados no se corrigen con la auditoría: hay que volver a correrlos con el juez corregido.
