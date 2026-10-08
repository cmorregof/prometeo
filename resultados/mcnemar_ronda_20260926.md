# McNemar ampliado de la ronda 1 (`20260926-2016`)

Generado el 30 sep 2026 por Claude Code, **sin volver a correr nada**: solo lectura de los `episodios.jsonl` de las corridas
de la ronda 1 (las de `runs/unirl/rl_verbal/{evaluacion,evaluacion_E,pareada_luna,pareada_sol}/` con `inicio` entre
2026-09-26T20:17:27 y 2026-09-27T14:03:07, el inicio de la ronda 2). Regla de fusión, la misma del informe
(`unirl/tools/ronda.py`, `episodios_validos`): un episodio es válido si algún intento no fue `PROVIDER_ERROR`; si un
episodio aparece dos veces, cuenta el primero válido. T*_test = los 16 peldaños (`resultados/martillo_linea_base_2b6d69992bce9f0d.json`),
con la salvedad de la sección 3.

No se añadió al informe `resultados/RONDA_TERMINADA.md` porque la ronda 2, al terminar, escribirá su propio informe en esa
misma ruta (`unirl/tools/ronda.py`, función `informe`, `nombre = "RONDA_TERMINADA.md"`). El de la ronda 1 está versionado
en el commit `ec6d9eb`.

## 1. Tabla (todas las comparaciones, tres unidades de pareo)

La unidad prerregistrada es la tarea τ (`docs/formulacion/formulacion_rl_verbal.tex:205-210`: b y b' cuentan tareas; la
potencia de la línea 212 se calcula con 16 pares). El informe de la ronda pareó por peldaño y episodio (32 pares con dos
episodios); esa elección no estaba prerregistrada. «Colapsado por peldaño»: un peldaño cuenta como cerrado si algún
episodio lo cerró. «Solo episodio 1»: el primer episodio de cada peldaño.

| comparación (primera frente a segunda) | unidad | pares | gana la primera | gana la segunda | p exacto bilateral |
|---|---|---|---|---|---|
| Luna: C frente a B0 | peldaño y episodio | 32 | 6 | 0 | 0,031 |
| Luna: C frente a B0 | colapsado por peldaño | 16 | 3 | 0 | 0,250 |
| Luna: C frente a B0 | solo episodio 1 | 16 | 3 | 0 | 0,250 |
| Luna: C frente a B | peldaño y episodio | 32 | 3 | 1 | 0,625 |
| Luna: C frente a B | colapsado por peldaño | 16 | 1 | 1 | 1,000 |
| Luna: C frente a B | solo episodio 1 | 16 | 2 | 0 | 0,500 |
| Luna: C frente a E (H2) | peldaño y episodio | 32 | 2 | 0 | 0,500 |
| Luna: C frente a E (H2) | colapsado por peldaño | 16 | 1 | 0 | 1,000 |
| Luna: C frente a E (H2) | solo episodio 1 | 16 | 1 | 0 | 1,000 |
| Luna: C3 frente a E3 | peldaño y episodio | 16 | 2 | 0 | 0,500 |
| Luna: C3 frente a E3 | colapsado por peldaño | 16 | 2 | 0 | 0,500 |
| Luna: C3 frente a E3 | solo episodio 1 | 16 | 2 | 0 | 0,500 |
| Sol: C3 frente a E3 | peldaño y episodio | 16 | 1 | 1 | 1,000 |
| Sol: C3 frente a E3 | colapsado por peldaño | 16 | 1 | 1 | 1,000 |
| Sol: C3 frente a E3 | solo episodio 1 | 16 | 1 | 1 | 1,000 |

## 2. Pares discordantes, con archivo y línea (pareo por peldaño y episodio)

| comparación | peldaño | episodio | primera | segunda | episodio de la primera | episodio de la segunda |
|---|---|---|---|---|---|---|
| Luna: C frente a B0 | rf_1_punto | 1 | 1 | 0 | `evaluacion/20260926-201727-gpt-6-luna/episodios.jsonl:6` | `evaluacion/20260926-201727-gpt-6-luna/episodios.jsonl:1` |
| Luna: C frente a B0 | rf_1_punto | 2 | 1 | 0 | `evaluacion/20260926-201727-gpt-6-luna/episodios.jsonl:5` | `evaluacion/20260926-201727-gpt-6-luna/episodios.jsonl:3` |
| Luna: C frente a B0 | rf_2_signo | 1 | 1 | 0 | `evaluacion/20260926-233322-gpt-6-luna/episodios.jsonl:4` | `evaluacion/20260926-201727-gpt-6-luna/episodios.jsonl:8` |
| Luna: C frente a B0 | rf_2_signo | 2 | 1 | 0 | `evaluacion/20260926-201727-gpt-6-luna/episodios.jsonl:11` | `evaluacion/20260926-201727-gpt-6-luna/episodios.jsonl:7` |
| Luna: C frente a B0 | secante_2_cociente | 1 | 1 | 0 | `evaluacion/20260926-233322-gpt-6-luna/episodios.jsonl:47` | `evaluacion/20260926-233322-gpt-6-luna/episodios.jsonl:41` |
| Luna: C frente a B0 | secante_2_cociente | 2 | 1 | 0 | `evaluacion/20260926-233322-gpt-6-luna/episodios.jsonl:48` | `evaluacion/20260926-233322-gpt-6-luna/episodios.jsonl:46` |
| Luna: C frente a B | rf_2_signo | 1 | 1 | 0 | `evaluacion/20260926-233322-gpt-6-luna/episodios.jsonl:4` | `evaluacion/20260926-201727-gpt-6-luna/episodios.jsonl:9` |
| Luna: C frente a B | rf_2_signo | 2 | 1 | 0 | `evaluacion/20260926-201727-gpt-6-luna/episodios.jsonl:11` | `evaluacion/20260926-201727-gpt-6-luna/episodios.jsonl:10` |
| Luna: C frente a B | rf_4_raiz | 2 | 0 | 1 | `evaluacion/20260926-233322-gpt-6-luna/episodios.jsonl:20` | `evaluacion/20260926-233322-gpt-6-luna/episodios.jsonl:16` |
| Luna: C frente a B | secante_2_cociente | 1 | 1 | 0 | `evaluacion/20260926-233322-gpt-6-luna/episodios.jsonl:47` | `evaluacion/20260926-233322-gpt-6-luna/episodios.jsonl:43` |
| Luna: C frente a E (H2) | secante_2_cociente | 1 | 1 | 0 | `evaluacion/20260926-233322-gpt-6-luna/episodios.jsonl:47` | `evaluacion_E/20260927-090507-gpt-6-luna/episodios.jsonl:6` |
| Luna: C frente a E (H2) | secante_2_cociente | 2 | 1 | 0 | `evaluacion/20260926-233322-gpt-6-luna/episodios.jsonl:48` | `evaluacion_E/20260927-090507-gpt-6-luna/episodios.jsonl:7` |
| Luna: C3 frente a E3 | secante_1_inyectiva | 1 | 1 | 0 | `pareada_luna/20260926-233322-gpt-6-luna/episodios.jsonl:5` | `pareada_luna/20260927-084149-gpt-6-luna/episodios.jsonl:8` |
| Luna: C3 frente a E3 | secante_2_cociente | 1 | 1 | 0 | `pareada_luna/20260926-233322-gpt-6-luna/episodios.jsonl:7` | `pareada_luna/20260927-090507-gpt-6-luna/episodios.jsonl:1` |
| Sol: C3 frente a E3 | rf_3_encaje | 1 | 0 | 1 | `pareada_sol/20260926-201727-gpt-6-sol/episodios.jsonl:3` | `pareada_sol/20260927-084149-gpt-6-sol/episodios.jsonl:3` |
| Sol: C3 frente a E3 | secante_1_inyectiva | 1 | 1 | 0 | `pareada_sol/20260926-233322-gpt-6-sol/episodios.jsonl:3` | `pareada_sol/20260927-084149-gpt-6-sol/episodios.jsonl:7` |

Rutas relativas a `runs/unirl/rl_verbal/`.

## 3. Salvedad que cambia la lectura de E: secante_1 a secante_4

El único lema del cuaderno congelado, `sign_step`, declara `fixes x y z :: real`
(`runs/unirl/cuaderno/congelados/fbd88bf0474ad117/lemas.json`). Los lemas del cuaderno se compilan dentro del contexto
del peldaño, y secante_1 a secante_4 fijan `x y :: real` en ese contexto (`corpus/curado/raices/`). Resultado: en E y E3
todo intento que llega a compilar falla en el lema de la biblioteca con «Duplicate fixed variable(s): "x"», antes de
mirar la prueba del modelo. Ejemplo: `runs/unirl/rl_verbal/evaluacion_E/20260927-090507-gpt-6-luna/llamadas.jsonl:26`,
error «At command "lemma" (lema sign_step, línea 1)».

| fase | config | intentos en secante_1–4 | con «Duplicate fixed variable» | aceptados |
|---|---|---|---|---|
| evaluacion (C) | C | 26 | 0 | 2 |
| evaluacion_E | E | 32 | 27 | 0 |
| pareada_luna | C3 | 10 | 0 | 2 |
| pareada_luna | E3 | 12 | 11 | 0 |
| pareada_sol | C3 | 11 | 0 | 1 |
| pareada_sol | E3 | 12 | 12 | 0 |

Los intentos de E sin ese error en esos peldaños no llegaron a compilar (4 `STATEMENT_DRIFT` y 1 más, rechazados por el filtro).
Todos los pares en que C (o C3) gana a E (o E3) están en secante_1 o secante_2. La misma colisión explica que la línea
base con cuaderno no dejara resultado válido en esos cuatro peldaños: tres intentos cada uno
(`resultados/martillo_linea_base_2b6d69992bce9f0d.json`, campo `intentos`) y ninguna entrada en la caché del martillo
entre las 08:25 y las 08:42 del 27 sep (`logs/martillo_cache.sqlite`, 12 entradas para 16 peldaños). H1 sigue
cumpliéndose con los 12 peldaños medidos válidamente (12 ≥ 12), pero en el límite.

### Sensibilidad: sin secante_1 a secante_4 (12 peldaños)

| comparación (primera frente a segunda) | unidad | pares | gana la primera | gana la segunda | p exacto bilateral |
|---|---|---|---|---|---|
| Luna: C frente a B0 | peldaño y episodio | 24 | 4 | 0 | 0,125 |
| Luna: C frente a B0 | colapsado por peldaño | 12 | 2 | 0 | 0,500 |
| Luna: C frente a B0 | solo episodio 1 | 12 | 2 | 0 | 0,500 |
| Luna: C frente a B | peldaño y episodio | 24 | 2 | 1 | 1,000 |
| Luna: C frente a B | colapsado por peldaño | 12 | 1 | 1 | 1,000 |
| Luna: C frente a B | solo episodio 1 | 12 | 1 | 0 | 1,000 |
| Luna: C frente a E (H2) | peldaño y episodio | 24 | 0 | 0 | — |
| Luna: C frente a E (H2) | colapsado por peldaño | 12 | 0 | 0 | — |
| Luna: C frente a E (H2) | solo episodio 1 | 12 | 0 | 0 | — |
| Luna: C3 frente a E3 | peldaño y episodio | 12 | 0 | 0 | — |
| Luna: C3 frente a E3 | colapsado por peldaño | 12 | 0 | 0 | — |
| Luna: C3 frente a E3 | solo episodio 1 | 12 | 0 | 0 | — |
| Sol: C3 frente a E3 | peldaño y episodio | 12 | 0 | 1 | 1,000 |
| Sol: C3 frente a E3 | colapsado por peldaño | 12 | 0 | 1 | 1,000 |
| Sol: C3 frente a E3 | solo episodio 1 | 12 | 0 | 1 | 1,000 |

## 4. Sensibilidad a la regla de fusión: rf_2_signo, B, episodio 2

El episodio `rf_2_signo#B#2` se corrió dos veces por la reanudación tras el corte de red del 26 sep: la primera vez no se
aceptó (`runs/unirl/rl_verbal/evaluacion/20260926-201727-gpt-6-luna/episodios.jsonl:10`) y la segunda sí
(`runs/unirl/rl_verbal/evaluacion/20260926-233322-gpt-6-luna/episodios.jsonl:5`). Con la regla fijada antes de la ronda
cuenta la primera. Si contara la segunda, C frente a B por peldaño y episodio quedaría 2 a 1 (p = 1,0) y colapsado 0 a 1.
Los otros cuatro episodios repetidos de rf_2_signo tienen el mismo resultado las dos veces.
