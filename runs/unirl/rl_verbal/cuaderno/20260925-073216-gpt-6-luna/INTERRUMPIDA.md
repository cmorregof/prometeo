# Interrumpida por error (25 sep 2026)

Estado: **interrumpida por error**. No terminó ni está en curso: sus datos son parciales.

* **Qué pasó.** En la primera destilación (tras 6 de 32 episodios) Luna devolvió 5 errores aprendidos, que no tienen el campo `en_su_lugar`. `Cuaderno.guardar()` escribió `errores.json`, `lemas.json` y `estrategias.json` y cayó al generar `errores.md` (`KeyError`, `unirl/cuaderno.py`; traza en `logs/cuaderno_luna.log`).
* **Qué quedó.** 6 episodios en `episodios.jsonl` (1 aceptado, `bis_2_encaje`). El cuaderno quedó a medio escribir: su estado en ese momento está en `cuaderno_al_interrumpirse/` (hash 1bef1be0853836cc: 30 errores, 2 estrategias, 0 lemas; `errores.md` sin los 5 aprendidos). Después el cuaderno se resembró a su estado inicial, el mismo con que empezó esta corrida (hash 0b6385c1aed55323).
* **Costo.** $0,088981 en 28 llamadas (`logs/gasto.json`); la de destilación no está en `llamadas.jsonl`.
* **Código.** `unirl` 5ef59e25793670fb, versionado en el commit 9b5e3fe. Corregido en el commit b008480, con pruebas de regresión en `tests/test_regresiones_25sep.py`.
* **Qué se hace.** Se repite completa con el código corregido; los episodios perdidos no se rellenan.
