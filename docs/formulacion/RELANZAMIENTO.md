# Relanzamiento de la primera ronda del RL verbal

Preparado el 25 sep 2026 por Claude. **No se lanzó nada**: Carlos corre estos comandos en su terminal.

* Código corregido en el commit `b008480` (rama `versionar-y-corregir`); huella de `unirl`: `0e36aba0a1d3ca02`. Las corridas
  del 25 sep por la mañana (huella `5ef59e25793670fb`) quedan como **interrumpidas por error**: ver el
  `INTERRUMPIDA.md` de cada una en `runs/unirl/rl_verbal/`.
* El cuaderno se resembró a su estado inicial, hash `0b6385c1aed55323`, el mismo con que empezó la corrida
  interrumpida. El estado en que quedó al fallar está archivado en
  `runs/unirl/rl_verbal/cuaderno/20260925-073216-gpt-6-luna/cuaderno_al_interrumpirse/`.
* El umbral de H1 quedó prerregistrado en `docs/nota/formulacion_rl_verbal.tex` (commit `b9d850f`, 25 sep 14:30),
  antes de construir el cuaderno.

## Ronda 3 (preparada el 17 oct 2026; **no lanzada**)

Exploratoria y de mecanismo; **no es una prueba de H2**. Prerregistro: párrafo «Ronda 3» de
`docs/formulacion/formulacion_rl_verbal.tex`. Pregunta si un proponente más capaz cita y usa los 26 lemas del cuaderno
congelado `835d3070e3b0c3b1` que el martillo no demuestra solo; Luna no citó ninguno en la ronda 2 (0 de 120 intentos
de E). Se reporta junto con las rondas 1 y 2, y la auditoría va antes de cualquier análisis.

| | |
|---|---|
| Proponentes | `claude-sonnet-5-5` y después `claude-opus-5-5` (API de Anthropic, sin fallback; un rechazo es `REFUSAL`, intento fallido) |
| Esfuerzo y temperatura | `high`; la temperatura por omisión de la API (no se envía); los dos se registran en cada llamada |
| Tareas | los 16 teoremas de test, dos episodios por teorema, C y E (E con el cuaderno `835d3070e3b0c3b1`) |
| Juez y código | `teorema-2026-09-30`; commit `f413acb`, huella de `unirl` `24bdd337e927ff1d` |
| Presupuesto | tope duro de USD 75: 37,5 para C (fase `evaluacion`) y 37,5 para E (fase `evaluacion_E`); libro `logs/gasto_ronda_r3_<id>.json` |
| Estimación | ≈ USD 24 con Sonnet 5.5 y ≈ 47 con Opus 5.5, si gastan los tokens de Luna en la ronda 2 por episodio |

```bash
cd ~/Personal/rl_metodos && unirl/tools/lanzar_ronda3.sh --dry-run   # ensayo en seco: sin API, dos peldaños
cd ~/Personal/rl_metodos && unirl/tools/lanzar_ronda3.sh             # lanza (o reanuda) con nohup y caffeinate
unirl/tools/lanzar_ronda3.sh --detener                               # parar al terminar los episodios en curso
```

La clave es la `ANTHROPIC_API_KEY` del `.env` de la raíz. Los créditos vencen el 19 oct 2026 (UTC). Al terminar,
antes de mirar resultados, la auditoría (sin API), con la ventana que diga `logs/ronda_r3_<id>/meta.json`:

```bash
.venv/bin/python unirl/tools/rejuzgar.py rejuzgar --desde <inicio> --fases evaluacion,evaluacion_E --etiqueta ronda3 --paralelo 1
.venv/bin/python unirl/tools/rejuzgar.py cruzado  --desde <inicio> --fases evaluacion,evaluacion_E --etiqueta ronda3
```

## Ronda 2 (preparada el 27 sep 2026; **no lanzada**)

La ronda 1 (`20260926-2016`, 26–27 sep; informe en `resultados/RONDA_TERMINADA.md`, commit `ec6d9eb`) cumplió H1
(|T*_test| = 16 de 16) y no sostuvo H2: E 4/32 frente a C 6/32; McNemar Luna C/E b = 0, b' = 2, p = 0,5. Diagnóstico
sobre los registros (`llamadas.jsonl`, locales): el cuaderno admitió **un solo lema** (`sign_step`) porque los lemas
solo se cosechaban de los `LEMMAS` que Luna escribía por su cuenta (2 de 10 pruebas aceptadas; la otra candidata se
rechazó por nombre reservado); ese lema se mostró en los 16 peldaños de test sin compartir ningún identificador con
ellos, y las 35 respuestas de E/E3 que lo citaron fallaron todas. Ningún modelo aceptó nada de dificultad 4 o 5 en
ninguna configuración. Sol costó $8,11 de $10,78 y no superó a Luna (C3 4/16 en ambos; E3 4/16 frente a 2/16).

Enmiendas prerregistradas el 27 sep 2026, antes de lanzar (párrafo «Ronda 2» de
`docs/formulacion/formulacion_rl_verbal.tex`); **ninguna corrida de la ronda 2 existe**:

| # | enmienda | dónde |
|---|---|---|
| 1 | F pide de 1 a 3 lemas reutilizables por intento (prefijo `cu_`); la destilación también propone lemas (`LEMAS: <<< … >>>`), solo generales; el kernel decide, como antes | `unirl/reflexion.py` (`Config.pedir_lemas`), `unirl/experimentos.py` (`PROMPT_DESTILAR`, `destilar`) |
| 2 | tres pasadas sobre los 32 peldaños de train (96 episodios; episodio `<peldaño>#<pasada>`), partiendo del estado final de la ronda 1 (`fbd88bf0474ad117`); tope de llamadas de `cuaderno` 236 → 720 | `experimentos.py` (`--pasadas`), `lanzar_ronda.sh` (`PASADAS_CUADERNO=3`, `HASH_CUADERNO_INICIO`), `preflight.sh --cuaderno=` |
| 3 | un lema se muestra solo si su enunciado comparte ≥ 1 identificador con el teorema (símbolos aparte); con esta regla `sign_step` no se habría mostrado en ningún peldaño de test | `unirl/cuaderno.py` (`MINIMO_IDS_LEMA`) |
| 4 | análisis primario de H2: McNemar sobre T*_test con dificultad ≤ 3 (8 peldaños, 16 pares); secundarios: todo T* y dificultad 4–5 | `unirl/tools/ronda.py` (`CONJUNTOS_MCNEMAR`) |
| 5 | sin Sol (H4 pospuesta); `CON_SOL=1` la devuelve con su tope de $10 | `lanzar_ronda.sh` (`CON_SOL=0`) |
| 6 | sin cambios en B0, B, C, E, E3, martillo, línea base A ni umbral de H1 (se recalcula con el cuaderno congelado nuevo) | — |

Lo que **no** cambia, dicho bien: B, C y E ya veían el glosario Lean→Isabelle (25 entradas sembradas) como bloque
fijo; los 16 errores «aprendidos» de la ronda 1 son otra cosa (`calc`, `Duplicate fixed variable`, hechos inexistentes)
y solo los ve F. C supera a B porque tiene reflexión y 4 intentos frente a 1, no por el cuaderno.

Gasto estimado de la ronda 2 sin Sol (con las cifras de la ronda 1): cuaderno 3 × $0,55 ≈ $1,65; B0/B/C $1,00;
E $0,61; pareadas Luna $0,51; total ≈ $3,8. Topes por fase: cuaderno $3, evaluación $3, E $2, pareadas Luna $2,
Sol $0; total $15.

```bash
cd ~/Personal/rl_metodos && unirl/tools/lanzar_ronda.sh --dry-run   # ensayo en seco: 3 pasadas sobre 1 peldaño de train, sin API
cd ~/Personal/rl_metodos && unirl/tools/lanzar_ronda.sh             # ronda 2: el preflight exige el cuaderno vivo en fbd88bf0474ad117
```

El informe (`RONDA_TERMINADA.md`) trae ahora la columna «sobre T*, dif. ≤ 3» y el McNemar por conjunto; el de la
ronda 1 se generó con la versión anterior y no se regenera.

## Ejecución automática (26 sep 2026): `unirl/tools/lanzar_ronda.sh`

Los pasos de abajo se pueden correr a mano, pestaña por pestaña, o con el guion, que hace todo solo y sobrevive a cortes
de red y a cerrar la terminal:

```bash
cd ~/Personal/rl_metodos && unirl/tools/lanzar_ronda.sh --dry-run   # ensayo en seco: sin API, dos peldaños, ~2 min
cd ~/Personal/rl_metodos && unirl/tools/lanzar_ronda.sh             # preflight y lanzamiento con nohup + caffeinate
```

Preflight (`unirl/tools/preflight.sh`): Isabelle responde, el `.venv` importa `unirl`, `steprl` e `isarl`, la clave está
en el `.env` y una llamada mínima a Luna funciona, disco ≥ 5 GB, cuaderno en el hash sembrado, rama `reorganizar` limpia,
`pytest` rápido en verde. Luego pasos 1–4 en paralelo, 5, y 6–7 en paralelo; cada fase deja un marcador en
`logs/ronda_<id>/`; al relanzar se saltan las hechas y se repiten solo los peldaños sin episodios válidos. Libro propio
de la ronda en `logs/gasto_ronda_<id>.json` (topes duros: total $15; por fase, en la cabecera del guion). Al final:
`resultados/consolidar.py` y `resultados/RONDA_TERMINADA.md` (o `RONDA_INCOMPLETA.md` con la fase y el motivo).
Con el libro nuevo, los topes de llamadas por fase (decisión (a)) vuelven a contar desde cero y ya alcanzan.

## Antes de empezar

1. Estar en la rama con las correcciones (o en `main`, si ya la fusionaste):
   `git -C ~/Personal/rl_metodos branch --show-current` (desde el 26 sep todo vive en la raíz: un solo `.venv`, `runs/unirl/`, `logs/`).
2. Saldo de OpenAI: el libro de gastos deja $20,84 bajo el tope de $25, y la cota de toda la ronda es ≤ $11,16 (llamadas máximas por el costo medio medido por llamada).
   Comprueba en la página de facturación de OpenAI que la cuenta tenga saldo (el 24 sep se agotó). Si se agota, cada
   corrida se detiene sola con `ABORTADA.txt`.
3. No correr las pruebas con Isabelle (`pytest -m isabelle`) mientras corren los experimentos: el martillo tiene
   límites de tiempo real.

## Pasos 1 a 4: en paralelo, cada uno en su pestaña (como el 25 sep)

Ninguno necesita el cuaderno, así que pueden correr a la vez. El martillo sigue en serie entre todos los procesos (un
candado de archivo), y cada veredicto registra la carga de la máquina.

| paso | qué | cota de llamadas | cota de costo | duración esperada |
|---|---|---|---|---|
| 1 | construir el cuaderno: Luna, config. F, 32 peldaños de train, en serie (32 × 6 llamadas + 6 destilaciones) | 198 (quedan 208 en la fase `cuaderno`) | ≤ $0,65 | ≈ 5–6 h |
| 2 | evaluación B0, B, C: Luna, test, 2 episodios, 3 en paralelo | 320 (quedan 384 en `evaluacion`) | ≤ $1,04 | ≈ 2 h |
| 3 | pareada C3: Luna, test, 1 episodio, 2 en paralelo | 64 (quedan 110 en `pareada_luna`) | ≤ $0,21 | ≈ 1 h |
| 4 | pareada C3: Sol, test, 1 episodio, 2 en paralelo | 64 (quedan 109 en `pareada_sol`) | ≤ $4,21 | ≈ 1,2 h |

Los comandos están en §6.

## Paso 5: A con el cuaderno congelado (H1), cuando terminen los pasos 1 a 4

La línea base A corre **sola y en serie** (PLAN §8, punto 4): el martillo solo, con los lemas que el cuaderno congelado
le mostraría a E, sobre los 16 peldaños de test. No llama a la API. Dura ≈ 20 min.

Criterio prerregistrado: **H1 se cumple si quedan sin cerrar al menos 12 de los 16** (|T*_test| ≥ 12). El resultado
queda en `resultados/martillo_linea_base_<hash de los lemas>.json`.

## Pasos 6 y 7: E (Luna) y E3 (Luna y Sol). Antes hay que decidir dos cosas

**(a) Topes de llamadas por fase.** El libro de gastos cuenta las llamadas de cada fase sumando **todas** las corridas,
y las interrumpidas ya consumieron 28, 230, 44 y 45. Con los topes aprobados no alcanza:

| fase | tope | ya usadas | quedan tras los pasos 1–4 (peor caso) | E / E3 necesita como máximo |
|---|---|---|---|---|
| `evaluacion` | 614 | 230 | 384 − 320 = 64 | 192 (E, 2 episodios) |
| `pareada_luna` | 154 | 44 | 110 − 64 = 46 | 64 (E3) |
| `pareada_sol` | 154 | 45 | 109 − 64 = 45 | 64 (E3) |

Propuesta: subir cada tope en lo que consumieron las corridas interrumpidas (`cuaderno` 264, `evaluacion` 844,
`pareada_luna` 198, `pareada_sol` 199), sin tocar el tope global de $25, que sigue siendo el que protege el gasto. Es una
línea en `unirl/experimentos.py` (`TOPES`). **No está aplicada**: espera tu aprobación.

**(b) Qué es E.** **Decidido el 26 sep 2026, antes de lanzar la ronda:** E es C más **solo los lemas certificados** del
cuaderno congelado (la parte $L$; sin notas de error ni estrategias), y E3 es E con K = 3. Así queda en `unirl/reflexion.py`
(`CONFIGS`) y en la formulación (tabla de configuraciones y sección de prerregistro). Ninguna corrida de E anterior existe.

## Qué mirar mientras corren

* El avance, en los logs de cada pestaña (`logs/*_relanzamiento.log`).
* Una corrida que se detiene escribe `ABORTADA.txt` en su carpeta, con el motivo y la traza, y termina con código 1.
  Tras un fallo del código ya no se lanza ningún episodio más: los que están en curso terminan.
* El gasto acumulado:
  `.venv/bin/python -c "import json; print(round(json.load(open('logs/gasto.json'))['total_usd'], 4))"`.

## 6. Comandos

Todos desde `~/Personal/rl_metodos` (raíz del repo, con el `.venv` único).

Pestaña 1, paso 1 (cuaderno):

```bash
cd ~/Personal/rl_metodos && caffeinate -i .venv/bin/python -m unirl.experimentos cuaderno --modelo gpt-6-luna 2>&1 | tee logs/cuaderno_luna_relanzamiento.log
```

Pestaña 2, paso 2 (B0, B, C con Luna):

```bash
cd ~/Personal/rl_metodos && caffeinate -i .venv/bin/python -m unirl.experimentos evaluar --modelo gpt-6-luna --configs B0,B,C --episodios 2 --paralelo 3 2>&1 | tee logs/eval_luna_B0_B_C_relanzamiento.log
```

Pestaña 3, paso 3 (C3 con Luna):

```bash
cd ~/Personal/rl_metodos && caffeinate -i .venv/bin/python -m unirl.experimentos evaluar --modelo gpt-6-luna --configs C3 --episodios 1 --paralelo 2 --fase pareada_luna 2>&1 | tee logs/pareada_luna_C3_relanzamiento.log
```

Pestaña 4, paso 4 (C3 con Sol):

```bash
cd ~/Personal/rl_metodos && caffeinate -i .venv/bin/python -m unirl.experimentos evaluar --modelo gpt-6-sol --configs C3 --episodios 1 --paralelo 2 --fase pareada_sol 2>&1 | tee logs/pareada_sol_C3_relanzamiento.log
```

Paso 5, cuando hayan terminado los pasos 1 a 4. Lee el hash del cuaderno congelado y corre A con él:

```bash
cd ~/Personal/rl_metodos && H=$(.venv/bin/python -c "import json,glob; print(json.load(open(sorted(glob.glob('runs/unirl/rl_verbal/cuaderno/*/FIN.json'))[-1]))['cuaderno'])") && echo "cuaderno congelado: $H" && caffeinate -i .venv/bin/python -m unirl.experimentos linea-base --cuaderno $H 2>&1 | tee logs/linea_base_cuaderno_relanzamiento.log
```

Paso 6, después de decidir (a) y (b). E con Luna (en la misma pestaña del paso 5, que ya tiene `$H`):

```bash
caffeinate -i .venv/bin/python -m unirl.experimentos evaluar --modelo gpt-6-luna --configs E --episodios 2 --paralelo 3 --cuaderno $H 2>&1 | tee logs/eval_luna_E_relanzamiento.log
```

Paso 7, E3 con Luna y con Sol (pueden ir a la vez, en dos pestañas; en una pestaña nueva hay que volver a leer `$H`
con la primera parte del comando del paso 5):

```bash
caffeinate -i .venv/bin/python -m unirl.experimentos evaluar --modelo gpt-6-luna --configs E3 --episodios 1 --paralelo 2 --cuaderno $H --fase pareada_luna 2>&1 | tee logs/pareada_luna_E3_relanzamiento.log
```

```bash
caffeinate -i .venv/bin/python -m unirl.experimentos evaluar --modelo gpt-6-sol --configs E3 --episodios 1 --paralelo 2 --cuaderno $H --fase pareada_sol 2>&1 | tee logs/pareada_sol_E3_relanzamiento.log
```
