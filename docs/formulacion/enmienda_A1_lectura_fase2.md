# Enmienda A1 del prerregistro: lectura de resultados en la fase 2

**Registro:** <https://osf.io/w4eru> (SHA-256 del prerregistro `e6a2b5750b1ee1acf6c25bd094ec7c8e206ab02e465e4dd5d6cbd745b8e221fd`).
**Fecha:** 2 de noviembre de 2026.
**Decisión:** Carlos Manuel Orrego-Franco.
**Tipo:** corrección de un defecto del arnés, antes de la fase 2. Va según §15 del prerregistro, que no se edita.

## El defecto

En `unirl/fase2.py`, después de terminar cada celda y hasta completar el primer 10 % de la cola, `_n10_completo` lee
`resultados.jsonl` entero. Esa lectura no tomaba el cerrojo `_LOCK_REG`, que sí usan las escrituras. Con `--paralelo 4`,
otro hilo puede estar escribiendo en ese momento:

1. La lectura encuentra una línea a medio escribir y lanza `JSONDecodeError`.
2. `trabajador` lo captura como un error de la celda y añade una fila `error de programa` con `resuelto: False` e
   `intentos: 0`, aunque la celda ya tenía su resultado real.
3. `analisis_v6.cargar` no elimina duplicados y `tasas` promedia todas las filas: una celda resuelta contaría como 0,5.

## Cómo se encontró

La prueba `test_r2_retencion_de_sc_ig_no_interrumpe_celdas_en_curso` falló una vez en el CI de Linux, con el proveedor seco
(sin API), y pasó al repetirla. Pasó 290 de 290 veces en macOS.

- **Lo deducido:** la prueba no imprime `errores.jsonl`, así que el error no se vio directamente en ese CI. Las 162 celdas
  impresas estaban bien, de modo que la fila mala era de una celda ya impresa, y lo único que corre después de imprimir es
  esta lectura.
- **Lo reproducido:** al simular una escritura en dos partes, salieron de 9 a 17 filas falsas en 3 de 3 corridas, todas
  por `JSONDecodeError`.

## El cambio

Una sola cosa en `unirl/fase2.py`: las dos lecturas de `_n10_completo` se hacen dentro de `with K._LOCK_REG:`.

**No cambian** el juez (`unirl/corpus_confirmatorio.py`, `c974c63f…`), `frontera.py`, los prompts, el plan, el anexo, las
hipótesis, el análisis ni `test_v6.py`. `fase2.py` no entra en `_huella_codigo`, así que la huella del código tampoco cambia.

**Regla añadida:** al terminar la fase 2, y antes de analizar, se comprueba que `errores.jsonl` no exista. Si existe, se
reporta su contenido junto con los resultados.

## Hashes

`docs/formulacion/SHA256SUMS_v6` no se toca: sigue siendo el registrado (`1b69e8ed…`). Los bytes registrados de `fase2.py`
siguen en el commit `22fad88`, con hash `7e201c9f…`. El hash nuevo está en `docs/formulacion/SHA256SUMS_v6_A1`.

## Verificación

- `tests/unirl/test_enmienda_a1.py` falla con el `fase2.py` registrado y pasa con el cambio.
- La suite completa sin Isabelle pasa con el cambio.

## Constancia de lo observado

Al escribir esta enmienda ya se conocían los datos de la fase 1 (1.808 episodios), en la que no hay `errores.jsonl` ni filas
`error de programa`. En `runs/unirl/confirmatorio/v6/` no hay carpeta de la fase 2, es decir, no consta ninguna corrida de
esa fase ni se observó ningún resultado de test. El defecto se encontró con un proveedor simulado, sin mirar resultados.
