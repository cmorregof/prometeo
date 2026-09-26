# Interrumpida por error (25 sep 2026)

Estado: **interrumpida por error**. No terminó ni está en curso: sus datos son parciales.

* **Qué pasó.** El caché SQLite del martillo se creaba en el hilo principal y se usaba desde los hilos trabajadores: `Cache.lineas_de` lanzaba `sqlite3.ProgrammingError` (`unirl/martillo.py`). Cada episodio en que el modelo entregó una prueba con marcas `by martillo` murió en ese intento sin quedar registrado. Como `evaluar` solo capturaba `ProviderFatal`, la corrida siguió hasta agotar su lista y solo al final imprimió el error (`logs/pareada_sol_C3.log`), sin escribir `episodios.csv` ni `resumen.md`.
* **Qué quedó.** 9 de 16 episodios en `episodios.jsonl`; 7 perdidos. **La pérdida no es aleatoria**: son los episodios en que el modelo quiso usar el martillo por pasos. Los conteos parciales no estiman ninguna tasa.
* **Costo.** $2,952131 en 45 llamadas (`logs/gasto.json`). A `llamadas.jsonl` le falta exactamente la llamada que mató a cada episodio (7).
* **Código.** `unirl` 5ef59e25793670fb, versionado en el commit 9b5e3fe. Corregido en el commit b008480, con pruebas de regresión en `tests/test_regresiones_25sep.py`.
* **Qué se hace.** Se repite completa con el código corregido; los episodios perdidos no se rellenan.
