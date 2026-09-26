# Tiempos de pared de las corridas locales sin API (25 sep 2026, 14:49–14:53)

Medidos por Claude con `time.time()` antes y después de cada orden, en el MacBook Air (M-series) de Carlos, con nada
más corriendo. Incluyen el arranque de Python. Commit del repo: `e419660` (rama `versionar-y-corregir`).

| orden | tiempo |
|---|---|
| `python -m bisectrl --no-tui --seed 0` (3000 + 3000; la primera se repitió a las 14:51 porque la de semilla 1 cayó en la misma carpeta y la pisó) | 0,41 s |
| `python -m bisectrl --no-tui --seed 1` | 0,38 s |
| `python -m fixpointrl --no-tui --seed 0` | 0,39 s |
| `python -m taylorrl --no-tui --seed 0` | 0,35 s |
| `python -m newtonrl --no-tui --seed 0` | 0,36 s |
| `python -m secantrl --no-tui --seed 0` | 0,40 s |
| `python -m interprl --no-tui --seed 1` | 7,92 s |
| `python -m interprl --no-tui --seed 0` | 8,02 s |
| `python -m interprl search --n 4` | 0,84 s |
| `python -m interprl search --n 8` | 2,45 s |
| `python -m interprl search --n 12` | 6,44 s |
| `python -m steprl verify` | 2,34 s |
| `lineas_base_puras.py` (5 estrategias × 3000 problemas) | 0,51 s |

Las pruebas (`pytest -q`) guardan su propio tiempo en `pytest/*.xml`.
