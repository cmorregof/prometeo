# Re-adjudicación del juez: `ronda2`

Generado el 2026-10-14 13:10 con `unirl/tools/rejuzgar.py` (referencia-2026-10-08), sin llamar a la API. Corridas: `cuaderno/20261008-200559-gpt-6-luna`, `evaluacion/20261008-200559-gpt-6-luna`, `pareada_luna/20261008-200559-gpt-6-luna`, `evaluacion/20261008-204019-gpt-6-luna`, `pareada_luna/20261008-204019-gpt-6-luna`, `evaluacion/20261009-080009-gpt-6-luna`, `evaluacion/20261009-100605-gpt-6-luna`, `evaluacion_E/20261013-221752-gpt-6-luna`, `pareada_luna/20261013-221752-gpt-6-luna`. Referencia: límite 600.0 s, sandbox sí. Cada intento se compara con lo que dice la especificación V aplicada por una implementación aparte (cabecera del guion).

## 1. Veredictos por configuración (intentos)

| fase | modelo | config | intentos | concordante | concordante_contaminado | FN | FP | regla_estricta | tiempo | indeterminado | sin_juicio |
|---|---|---|---|---|---|---|---|---|---|---|---|
| cuaderno | gpt-6-luna | F | 335 | 282 | 0 | 0 | 0 | 0 | 0 | 1 | 52 |
| evaluacion | gpt-6-luna | B | 38 | 24 | 0 | 0 | 0 | 0 | 0 | 0 | 14 |
| evaluacion | gpt-6-luna | B0 | 40 | 18 | 0 | 0 | 0 | 0 | 0 | 0 | 22 |
| evaluacion | gpt-6-luna | C | 122 | 61 | 0 | 0 | 0 | 0 | 0 | 0 | 61 |
| evaluacion_E | gpt-6-luna | E | 120 | 62 | 0 | 0 | 0 | 1 | 0 | 0 | 57 |
| pareada_luna | gpt-6-luna | C3 | 50 | 25 | 0 | 0 | 0 | 0 | 0 | 0 | 25 |
| pareada_luna | gpt-6-luna | E3 | 44 | 17 | 0 | 0 | 0 | 0 | 0 | 0 | 27 |

## 2. Sensibilidad y falsos positivos por configuración

Se = intentos que el juez aceptó entre los que V acepta (con sus reglas y su límite); la cota es la de la regla de tres (95 %) cuando no hubo falsos negativos entre los rechazos re-juzgados.

| modelo | config | V acepta | el juez acepta | FN | Se | FP | rechazos re-juzgados | cota FN si FN = 0 |
|---|---|---|---|---|---|---|---|---|
| gpt-6-luna | B | 1 | 1 | 0 | 1,00 | 0 | 23 | 0,122 |
| gpt-6-luna | B0 | 0 | 0 | 0 | — | 0 | 18 | 0,153 |
| gpt-6-luna | C | 8 | 8 | 0 | 1,00 | 0 | 53 | 0,055 |
| gpt-6-luna | C3 | 2 | 2 | 0 | 1,00 | 0 | 23 | 0,122 |
| gpt-6-luna | E | 5 | 5 | 0 | 1,00 | 0 | 58 | 0,050 |
| gpt-6-luna | E3 | 3 | 3 | 0 | 1,00 | 0 | 14 | 0,193 |
| gpt-6-luna | F | 33 | 33 | 0 | 1,00 | 0 | 249 | 0,012 |

## 3. Casos que no son concordantes

| config | episodio | intento | juez | categoría | detalle | primer error del juez | primer error de la referencia | archivo |
|---|---|---|---|---|---|---|---|---|
| F | pf_5c_a_priori_max#3 | 1 | LEMMA_FAILED | indeterminado | la biblioteca (o el preludio) no compila en este peldaño | *** Undefined fact: "cu_iterate_contraction_bound" (lema cu_iterate_first_step_bound del cuaderno, línea 16) | *** Undefined fact: "cu_iterate_contraction_bound" (line 89 of "~/isabelle/scratch/rejuicio/rj-dbu993zo/Rejuicio.thy") | `cuaderno/20261008-200559-gpt-6-luna/llamadas.jsonl:352` |
| E | secante_1_inyectiva#E#2 | 2 | STATEMENT_DRIFT | regla_estricta | STATEMENT_DRIFT: STATEMENT_DRIFT: la PROOF no se admite: barra invertida fuera de un símbolo, o comentario formal |  |  | `evaluacion_E/20261013-221752-gpt-6-luna/llamadas.jsonl:75` |

## 4. Episodios: juez frente a referencia

Un episodio auditado vale 1 si alguno de sus intentos es válido según V; queda indeterminado si ninguno lo es y alguno no se pudo juzgar. «Contaminado»: antes del primer intento válido hubo uno cuya retroalimentación culpó al cuaderno o que no se pudo juzgar; ese episodio habría seguido otra trayectoria con un juez correcto y hay que volver a correrlo para conocer su resultado contrafactual.

| modelo | config | episodios | aceptados (juez) | válidos (auditados) | indeterminados | contaminados |
|---|---|---|---|---|---|---|
| gpt-6-luna | B | 32 | 0 | 0 | 0 | 0 |
| gpt-6-luna | B0 | 32 | 0 | 0 | 0 | 0 |
| gpt-6-luna | C | 32 | 7 | 7 | 0 | 0 |
| gpt-6-luna | C3 | 16 | 2 | 2 | 0 | 0 |
| gpt-6-luna | E | 32 | 5 | 5 | 0 | 0 |
| gpt-6-luna | E3 | 16 | 3 | 3 | 0 | 0 |
| gpt-6-luna | F | 96 | 33 | 33 | 0 | 1 |

Control: 0 episodios en que la agregación de los intentos difiere de `episodios.jsonl` (debería ser 0) y 0 episodios sin fila en `episodios.jsonl` (interrumpidos y nunca repetidos).

## 5. McNemar recalculado (peldaños de test)

b = gana la segunda configuración, b' = gana la primera; p exacto bilateral. «excluir», «0» y «1»: qué se hace con los episodios indeterminados en la versión auditada.

| comparación | unidad | veredictos | indeterminados | pares | b | b' | p |
|---|---|---|---|---|---|---|---|
| gpt-6-luna: C frente a E | peldaño y episodio | juez | — | 32 | 2 | 4 | 0,688 |
| gpt-6-luna: C frente a E | peldaño y episodio | auditados | excluir | 32 | 2 | 4 | 0,688 |
| gpt-6-luna: C frente a E | peldaño y episodio | auditados | 0 | 32 | 2 | 4 | 0,688 |
| gpt-6-luna: C frente a E | peldaño y episodio | auditados | 1 | 32 | 2 | 4 | 0,688 |
| gpt-6-luna: C frente a E | colapsado por peldaño | juez | — | 16 | 1 | 2 | 1,000 |
| gpt-6-luna: C frente a E | colapsado por peldaño | auditados | excluir | 16 | 1 | 2 | 1,000 |
| gpt-6-luna: C frente a E | colapsado por peldaño | auditados | 0 | 16 | 1 | 2 | 1,000 |
| gpt-6-luna: C frente a E | colapsado por peldaño | auditados | 1 | 16 | 1 | 2 | 1,000 |
| gpt-6-luna: C3 frente a E3 | peldaño y episodio | juez | — | 16 | 2 | 1 | 1,000 |
| gpt-6-luna: C3 frente a E3 | peldaño y episodio | auditados | excluir | 16 | 2 | 1 | 1,000 |
| gpt-6-luna: C3 frente a E3 | peldaño y episodio | auditados | 0 | 16 | 2 | 1 | 1,000 |
| gpt-6-luna: C3 frente a E3 | peldaño y episodio | auditados | 1 | 16 | 2 | 1 | 1,000 |
| gpt-6-luna: C3 frente a E3 | colapsado por peldaño | juez | — | 16 | 2 | 1 | 1,000 |
| gpt-6-luna: C3 frente a E3 | colapsado por peldaño | auditados | excluir | 16 | 2 | 1 | 1,000 |
| gpt-6-luna: C3 frente a E3 | colapsado por peldaño | auditados | 0 | 16 | 2 | 1 | 1,000 |
| gpt-6-luna: C3 frente a E3 | colapsado por peldaño | auditados | 1 | 16 | 2 | 1 | 1,000 |
| gpt-6-luna: C frente a B0 | peldaño y episodio | juez | — | 32 | 0 | 7 | 0,016 |
| gpt-6-luna: C frente a B0 | peldaño y episodio | auditados | excluir | 32 | 0 | 7 | 0,016 |
| gpt-6-luna: C frente a B0 | peldaño y episodio | auditados | 0 | 32 | 0 | 7 | 0,016 |
| gpt-6-luna: C frente a B0 | peldaño y episodio | auditados | 1 | 32 | 0 | 7 | 0,016 |
| gpt-6-luna: C frente a B0 | colapsado por peldaño | juez | — | 16 | 0 | 4 | 0,125 |
| gpt-6-luna: C frente a B0 | colapsado por peldaño | auditados | excluir | 16 | 0 | 4 | 0,125 |
| gpt-6-luna: C frente a B0 | colapsado por peldaño | auditados | 0 | 16 | 0 | 4 | 0,125 |
| gpt-6-luna: C frente a B0 | colapsado por peldaño | auditados | 1 | 16 | 0 | 4 | 0,125 |
| gpt-6-luna: C frente a B | peldaño y episodio | juez | — | 32 | 0 | 7 | 0,016 |
| gpt-6-luna: C frente a B | peldaño y episodio | auditados | excluir | 32 | 0 | 7 | 0,016 |
| gpt-6-luna: C frente a B | peldaño y episodio | auditados | 0 | 32 | 0 | 7 | 0,016 |
| gpt-6-luna: C frente a B | peldaño y episodio | auditados | 1 | 32 | 0 | 7 | 0,016 |
| gpt-6-luna: C frente a B | colapsado por peldaño | juez | — | 16 | 0 | 4 | 0,125 |
| gpt-6-luna: C frente a B | colapsado por peldaño | auditados | excluir | 16 | 0 | 4 | 0,125 |
| gpt-6-luna: C frente a B | colapsado por peldaño | auditados | 0 | 16 | 0 | 4 | 0,125 |
| gpt-6-luna: C frente a B | colapsado por peldaño | auditados | 1 | 16 | 0 | 4 | 0,125 |

## 6. Cómo leerlo

* Por solidez, el juez solo puede fallar por falsos negativos; un FP aquí es una alarma: revisa el caso a mano.
* Si Se cambia entre configuraciones, la comparación está sesgada hacia la de mayor Se, aunque cada veredicto por separado parezca razonable. Si Se es igual en todas, la prueba conserva su nivel y solo pierde potencia.
* `regla_estricta` no es un error del juez: son pruebas válidas para el kernel que violan una regla declarada. Si su frecuencia cambia entre configuraciones, conviene saberlo.
* Los episodios contaminados no se corrigen con la auditoría: hay que volver a correrlos con el juez corregido.
