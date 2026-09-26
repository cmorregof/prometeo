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

**(b) Qué es E.** La formulación define E como «C más el cuaderno congelado», y el cuaderno es c = (L, E, S): lemas,
errores **y estrategias**. En el código y en PLAN §3.9, E es «errores y lemas»; las estrategias entran en F. Si E debe
incluir las estrategias, el paso 6 se corre con `--configs F` y el 7 necesitaría una configuración E3 con estrategias
(`F3`, que hoy no existe). Mientras no digas otra cosa, los comandos usan E y E3 tal como están en el código.

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
