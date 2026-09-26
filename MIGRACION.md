# MIGRACION.md · reorganización del 26 de septiembre de 2026 (rama `reorganizar`)

Estructura de destino: `ESTRUCTURA_OBJETIVO.md` (documento de Carlos, ahora en el repo con sus ajustes del 26–27 sep). Antes de tocar el repo se sacaron de él, fuera
de todo repositorio: el libro del director (`Conjeturas/` → `~/Personal/_director/Conjeturas/`), su paquete
(`paquete_completo.zip` → `~/Personal/_director/`) y la convocatoria (→ `~/Personal/_convocatorias/`), con SHA-256
iguales antes y después (`~/Personal/_revision_general/limpieza/sha_paso5_*.txt`). Nada científico se borró; lo
regenerable se borró; los dos `.Rhistory` se archivaron en `~/Personal/_archivo_limpieza_20260926/` (manifiesto A2).

## 1. Ruta vieja → ruta nueva

Código y documentos con `git mv` (git registra 577 renombrados); registros con `mv` y manifiesto SHA-256
(`_revision_general/limpieza/manifiesto_intocables_{antes,despues}.txt`: las 361 huellas de `runs/`, `logs/`, `corpus/`,
`cuaderno/`, `certificados/`, `*.jsonl`, `gasto.json` y las pruebas privadas son idénticas; solo se añade el tar de la
instantánea).

| ruta vieja | ruta nueva | cómo | nota |
|---|---|---|---|
| `01_biseccion/bisectrl/` | `didactica/biseccion/` | git mv | importación `didactica.biseccion` |
| `02_punto_fijo/fixpointrl/` | `didactica/punto_fijo/` | git mv | `didactica.punto_fijo` |
| `03_taylor/taylorrl/` | `didactica/taylor/` | git mv | |
| `04_newton/newtonrl/` | `didactica/newton/` | git mv | |
| `05_secante/secantrl/` | `didactica/secante/` | git mv | |
| `07_interpolacion/interprl/` | `didactica/interpolacion/` | git mv | |
| `01_biseccion/bisectrl/agent.py` | `didactica/qagent.py` | git mv | los otros cinco `agent.py`, idénticos (SHA `3174d553…`), se eliminaron; `trainer.py` importa `from ..qagent import QAgent` |
| `0X_*/<pkg>/__main__.py` (×6) | se conservan en cada subpaquete | — | hacen falta para `python -m didactica.<metodo>`; `didactica/__main__.py` nuevo es un despachador (`python -m didactica biseccion …`) |
| `0X_*/README.md` (×6), `06_stepsizes/README.md` | `didactica/<metodo>/README.md`, `steprl/README.md` | git mv | **encaje provisional**: la estructura no los menciona |
| `0X_*/docs/captura.svg` (01–05) | `didactica/<metodo>/docs/captura.svg` | git mv | **provisional** |
| `06_stepsizes/steprl/` | `steprl/` | git mv | `steprl/providers.py` lee ahora `.env` de la raíz |
| `06_stepsizes/.env` | `.env` | mv | ignorado; no se imprime ni se copia |
| `06_stepsizes/certificados/` | `certificados/` | git mv | |
| `06_stepsizes/runs/2026*/` y sueltos (`cert-*.json`, `evolve-0*.log`, `refs-*.log`) | `runs/pep/` | mv (no versionados) | los sueltos quedan directamente en `runs/pep/` (**provisional**) |
| `06_stepsizes/docs/ejecucion-01-gpt-6-astra.md` | `docs/ejecuciones_pep/` | git mv | |
| `06_stepsizes/tests/*.py` | `tests/steprl/` | git mv | |
| `08_isabelle/isarl/` | `isarl/` | git mv | el preámbulo de la estructura dice `isabelle/`; el árbol dice `isarl/`: **se siguió el árbol** |
| `08_isabelle/runs/` | `runs/isabelle/` | git mv | |
| `08_isabelle/runs_repro.log` | `logs/runs_repro.log` | git mv | **provisional**, con los otros sueltos; explicado en `logs/LEEME.md` |
| `08_isabelle/docs/reproduccion-bisection.md` | `docs/informes/reproduccion-bisection.md` | git mv | **provisional** |
| `08_isabelle/tests/`, `08_isabelle/isabelle/Targets/` (vacías) | eliminadas | rmdir | |
| `09_unified/unirl/` | `unirl/` | git mv | sin `sys.path`; ver §2 |
| `09_unified/configs/`, `tools/` | `unirl/configs/`, `unirl/tools/` | git mv | código y configuración: dentro del paquete (aceptado el 26 sep) |
| `09_unified/targets/{bisection,countdown}.json`, `_bisection_aux.thy.part` | `corpus/curado/programas/` | git mv | son enunciados (tripletas de Hoare congeladas y sus lemas prestados): decisión por contenido del 26 sep |
| `09_unified/targets/gd_*.json`, `targets/gd_cert/` | `corpus/curado/stepsize/`, `corpus/curado/stepsize/gd_cert/` | git mv | enunciados del juez de teorema y sus certificados y pruebas de referencia |
| `09_unified/targets/isabelle_commands.txt` | `unirl/isabelle_commands.txt` | git mv | dato del filtro léxico: código |
| `09_unified/corpus/raices/` | `corpus/curado/raices/` | git mv | `corpus/existencia/LEEME.md` nuevo |
| `09_unified/cuaderno/` | `runs/unirl/cuaderno/` | git mv (SHA-256 de los 4 archivos igual; hash del cuaderno `0b6385c1aed55323`, el sembrado) | estado de las corridas del RL verbal (decisión del 26 sep) |
| `09_unified/runs/` | `runs/unirl/` | git mv (+ `llamadas.jsonl` no versionados, con la carpeta) | |
| `.snap_astra_bis/unirl/` | `runs/unirl/bisection_isabelle_lemas_mem/20260923-224900-gpt-6-astra-high/codigo_unirl_61c5c2b8.tar.gz` | tar + rm | huella de los `.py` del tar: `61c5c2b8649611f6`, igual a `code.unirl_sha256` de esa corrida |
| `09_unified/logs/` | `logs/` | git mv (+ `.sqlite`, `.lock`, `.pid` con la carpeta) | |
| `09_unified/runs_bisection_graph.log`, `…_graph_luna.log`, `…_isabelle.log`, `runs_isabelle_paper_inv.json` | `logs/` | git mv | `logs/LEEME.md` |
| `09_unified/resultados/*` (6 archivos) | `resultados/` | git mv | **provisional**: fusionados con `resultados/`; `unirl.recompensa` escribe ahí |
| `09_unified/docs/nota/` | `docs/formulacion/` | git mv | sin `unirl_definicion_v0.2_preliminar.pdf` (B5, `git rm`) |
| `09_unified/docs/informes/` | `docs/informes/` | git mv | sin `_descartado_sin_creditos/` (B6, `git rm`) |
| `09_unified/docs/diseno_gd_isabelle.md`, `PLAN_rl_verbal.md`, `RELANZAMIENTO.md`, `README.md` | `docs/formulacion/` (el README como `unirl_README.md`) | git mv | **provisional**; los comandos de `RELANZAMIENTO.md` se actualizaron a la raíz |
| `09_unified/tests/*.py`, `tests/fixtures/` | `tests/unirl/` | git mv / mv | `pruebas_privadas/` sigue sin versionar |
| `0X_*/tests/test_envs.py` (×6) | `tests/didactica/test_<metodo>.py` | git mv | renombrados para no chocar |
| `resultados/corridas_locales/` | `runs/corridas_locales/` | git mv | sus subcarpetas conservan los nombres viejos (`01_biseccion_100gen`, …) |
| `0X_*/pyproject.toml` (×7) y `09_unified/pyproject.toml` | `pyproject.toml` único | git rm + nuevo | paquetes `unirl`, `steprl`, `isarl`, `didactica.*`; extra `dev` = `pytest`, `pepit` |
| `0X_*/LICENSE` (×7, idénticos) | `LICENSE` | git mv (01) + git rm (6) | |
| `.gitignore` de 01–05, 06, 07, 08, 09, `resultados/`, `docs/curso/tex/` (×11) | `.gitignore` único | git rm + nuevo | §4 de la estructura, más `!logs/**/*.log`, `.env.*`, `*.pyc`, `build/`, `dist/` |
| `.github/workflows/tests.yml` (7 trabajos) | un solo flujo | reescrito | `pytest tests/didactica tests/steprl tests/unirl -m "not isabelle"` + dos humos |
| `01_biseccion/.Rhistory`, `06_stepsizes/.Rhistory` | `~/Personal/_archivo_limpieza_20260926/rl_metodos/…` | mover.py (A2) | el de 06 estaba versionado; git lo registra como borrado |
| ocho `.venv/`, `__pycache__/`, `.pytest_cache/`, `*.egg-info/`, `.DS_Store`, auxiliares de LaTeX, `docs/curso/tex/*.pdf`, `resultados/_compilacion.txt` | borrados | rm | regenerables (§3 de la estructura); el `.venv` único se creó antes de borrar los viejos |
| `06_stepsizes/06_stepsizes/`, `07_interpolacion/docs/` (vacías) | eliminadas | rmdir | |

## 2. Cambios de código (todos en el commit «reorganizar (4)»)

* `unirl/verifiers.py`: `ROOT` es la raíz del repo; `objetivo(nombre)` busca `<nombre>.json` en `corpus/curado/*/` (`TARGETS` = `corpus/curado/stepsize`, `TARGETS_PROGRAMAS` = `corpus/curado/programas`); `ISABELLE_COMMANDS` se lee de `unirl/isabelle_commands.txt`; `_import_from` ya no toca `sys.path`
  (importa `steprl`, `isarl` con `importlib`); el juez de grafo importa `didactica.<metodo>.proof_kb` y acepta los
  nombres viejos de las configs (`01_biseccion` → `biseccion`, tabla `PROYECTOS`); el intérprete aislado del PEP recibe
  la raíz del repo.
* `unirl/cli.py`: sin `sys.path`; por defecto `runs/unirl`, `docs/formulacion` y `runs/isabelle/repro_bisection.json`;
  la huella «sucia» mira `unirl/`.
* `unirl/informe.py`, `report.py`, `corpus.py`, `experimentos.py`: `docs/formulacion`, `runs/unirl`, `unirl/configs`,
  `unirl/targets`, `corpus/curado`.
* `unirl/gd_isabelle.py`: `importlib.import_module("isarl.config")`; el objetivo se localiza con `objetivo(nombre)`.
* `unirl/cuaderno.py`, `unirl/martillo.py` y dos herramientas: el cuaderno vivo está en `runs/unirl/cuaderno/`.
* `unirl/tools/*.py`: `HERE = parents[2]` (raíz), `unirl/tools`, `unirl/targets`, `runs/unirl`, `corpus/curado/raices`;
  sin `sys.path` hacia 06 y 08.
* `unirl/configs/*_graph.toml`: `project = "biseccion"` (etc.).
* `steprl/cli.py`, `steprl/providers.py`: mensajes sobre el `.env` de la raíz (la ruta ya era `parent.parent/.env`).
* `tests/unirl/*`: rutas a `corpus/curado/raices`, `runs/unirl`, `unirl/tools`; `tests/didactica/*`: `didactica.<metodo>`;
  `tests/conftest.py` nuevo (omite las pruebas `isabelle` si no está instalada); `tests/unirl/test_isarl.py` nuevo.
* `docs/curso/lab01/experimentos.py`, `lab02/experimentos.py`: `didactica.biseccion`, `didactica.punto_fijo`; se ejecutan
  desde la raíz con el `.venv` único.
* `resultados/consolidar.py`, `estadistica.py`, `tablas_informe.py`: rutas nuevas (`runs/didactica`, `runs/pep`,
  `runs/isabelle`, `runs/unirl`, `runs/corridas_locales`, `corpus/curado`, `certificados`, `steprl/refs.json`,
  `docs/formulacion`); las rutas históricas se conservan solo para `git log`. `tablas_informe.py` **no se volvió a
  correr**: `resultados/tablas/` y el informe de estado quedan como estaban (fechados al 25 sep, commit `22d4ba7`).
* `CLAUDE.md` y `README.md` reescritos (rutas nuevas; cifras de `resultados/auditoria_cifras.md`).

## 3. Verificación (criterios de terminación, §5 de la estructura)

| criterio | resultado |
|---|---|
| `pytest` completo en el `.venv` nuevo | rápidas: **247 pasan** (77 de didáctica y steprl + 170 de unirl, incluida la nueva de `isarl`), 19 con Isabelle deseleccionadas; con Isabelle: **19 pasan** en 8 min 33 s (`~/isabelle/Isabelle2025.app` presente; sin corridas en marcha) |
| calibración de `didactica.biseccion`, semilla 1 | **idéntica**: los 11 hitos coinciden con `runs/corridas_locales/01_biseccion/20260925-144905/historia.json` (λ = ½ en 345, Bolzano en 358, demostración en 256, mínima en 459) |
| `resultados/consolidar.py` | `metricas.csv` (776 líneas) y `resumen.json` (3395) **idénticos** a los versionados tras sustituir las rutas viejas por las nuevas en la columna `fuente` y en `corrida`, y salvo `generado`, `commit` (HEAD) y el `codigo` «HEAD» de las corridas locales. Se versionan regenerados, con las rutas nuevas |
| manifiesto SHA-256 de lo intocable | 361 huellas idénticas (los dos `.DS_Store` que había dentro de `runs/` se borraron por ser regenerables); solo se añade `codigo_unirl_61c5c2b8.tar.gz` |
| `git status` limpio; un commit por paso; sin push; sin API | commits: `e469100` (pendientes de la revisión), `392e88f` (paso 1), `9e02a99` (pasos 2 y 3), `d9cadb6` (paso 4), `86ec868` (paso 5) y el commit de este archivo con `README.md` y `CLAUDE.md` (paso 6). Sin `push`. Ninguna llamada a la API |
| `MIGRACION.md` y `CLAUDE.md` | este archivo; `CLAUDE.md` con las rutas nuevas |

## 4. Decisiones de Carlos del 26 sep (segunda ronda) sobre los encajes provisionales

Todos aceptados, con dos ajustes ya aplicados: el cuaderno va a `runs/unirl/cuaderno/` y los objetivos congelados del juez
Isabelle, por ser enunciados, a `corpus/curado/{programas,stepsize}/`. `isarl/` se mantiene (el preámbulo de la estructura
estaba equivocado y se corrigió). Los `__main__.py` por subpaquete se conservan. De los documentos con rutas viejas se
actualizaron solo los que se ejecutan o se leen como estado actual (`RELANZAMIENTO.md`, los README de cada método y de
`steprl`, `CLAUDE.md`) y se añadió una nota al inicio de `resultados/INVENTARIO.md`, `auditoria_cifras.md` e
`informe_estado.tex` (comentario; el PDF no cambia). Las guías y notas del curso no se tocan (texto histórico ya usado en
clase). `resultados/tablas/` y el informe de estado quedan al 25 sep hasta que termine la ronda. Lo que sigue era la lista
original de encajes provisionales, conservada como registro:

1. Los marcados **provisional** en §1: READMEs y capturas junto a su paquete; `unirl/{configs,targets,tools}` dentro del
   paquete; `cuaderno/` en la raíz; los seis archivos de `09_unified/resultados/` fusionados en `resultados/`; el plan, el
   relanzamiento, el diseño del juez de stepsize y el README de 09 en `docs/formulacion/`; la reproducción de la Tabla 1
   en `docs/informes/`; `runs_repro.log` en `logs/`; los sueltos de 06 en `runs/pep/`.
2. `isarl/` frente a `isabelle/` (preámbulo y árbol de la estructura discrepan).
3. Los `__main__.py` de cada subpaquete didáctico se conservan (necesarios para `python -m didactica.<metodo>`).
4. **Documentos con rutas viejas**: la guía del curso, el contexto, las notas del docente, el plan, el inventario y los
   informes citan `01_biseccion/`, `bisectrl`, `09_unified/` … Son textos fechados o material docente; no los reescribí
   (solo los comandos de `RELANZAMIENTO.md`, que vas a ejecutar). Lista en el mensaje de entrega.
5. `resultados/tablas/` y el informe de estado no se regeneraron: sus rutas de procedencia son las del 25 sep.
