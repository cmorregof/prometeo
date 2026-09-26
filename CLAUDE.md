# rl_metodos · contexto para Claude

Serie de agentes de Reinforcement Learning (RL) tabular que aprenden métodos numéricos y "demuestran" su teorema de
convergencia en la terminal; un entorno unificado (`unirl`) con jueces intercambiables (grafo de lemas, PEP, Isabelle/HOL);
y un experimento de RL verbal con memoria certificada por el kernel. Autor: Carlos Orrego (cmorregofranco@gmail.com).
Idioma del repo y de toda la comunicación: **español**.

El repo tiene tres usos que conviven:

1. **Investigación**: `unirl`, `steprl`, `isarl`, `corpus/`, `runs/`, `resultados/`, `docs/formulacion/`.
2. **Docencia**: `didactica/` y `docs/curso/` (métodos numéricos, matemáticas, semestres 2–4). Empezar por `docs/curso/contexto.md`.
3. **Divulgación**: los README de cada subpaquete didáctico.

## Estructura (desde la reorganización del 26 sep 2026; destino en `ESTRUCTURA_OBJETIVO.md`, tabla completa en `MIGRACION.md`)

```
pyproject.toml   ÚNICO: paquetes unirl, steprl, isarl, didactica.*; extra [dev]; un solo .venv en la raíz
didactica/       los seis agentes tabulares, como subpaquetes: biseccion, punto_fijo, taylor, newton, secante, interpolacion
  qagent.py      el QAgent compartido (Q-learning tabular, ε-greedy, tasa 1/N opcional, bono UCB); una sola copia
unirl/           un MDP con jueces intercambiables; RL verbal con cuaderno verificado; configs/ y tools/ dentro; isabelle_commands.txt
steprl/          juez PEP: verificador SDP, certificados racionales exactos, referencias, evolución con LLM
isarl/           juez Isabelle: driver vcg + try0 + Sledgehammer, reproducción de la Tabla 1 del artículo
corpus/curado/   raices/ (48 peldaños aprobados), programas/ (objetivos del juez de programa: bisection, countdown, lemas prestados),
                 stepsize/ (objetivos del juez de teorema gd_* y sus certificados gd_cert/); corpus/existencia/ reservado (vacío)
certificados/    certificados PEP versionados (n = 6 sigue marcado como no resuelto frente a la tabla publicada)
runs/            registros de corridas; INTOCABLES en contenido
  didactica/<metodo>/<fecha>/   pep/<fecha>/   isabelle/   unirl/<entorno>/<fecha-modelo>/   unirl/cuaderno/ (estado vivo)   corridas_locales/
logs/            libro de gastos (gasto.json), caché del martillo, guiones y .log de cada corrida
resultados/      inventario, métricas consolidadas, estadística, auditoría de cifras, informe de estado
docs/formulacion/  formulación del RL verbal, nota técnica de unirl, plan, relanzamiento, diseño del juez de stepsize
docs/informes/   un informe por corrida (plantilla_v0.1.tex, ESPEC.md); reproducción de la Tabla 1
docs/curso/      material docente: contexto, guía de terminal, laboratorios (Markdown es la fuente; tex/ derivado)
docs/ejecuciones_pep/   notas de las ejecuciones de evolve
tests/           didactica/ steprl/ unirl/ (+ fixtures/pruebas_privadas, no versionadas) y conftest.py
```

Cada subpaquete de `didactica/` tiene la misma anatomía (`interpolacion` añade `interp.py`, el verificador numérico,
y `search.py`, la fase 3):

| módulo | qué es |
|---|---|
| `env_<metodo>.py` | entorno de la fase 1: problemas aleatorios, estado observable, acciones, recompensa con *shaping* por potencial |
| `proof_kb.py` | grafo de lemas del teorema: `Step(key, title, text, deps, distractor, is_qed)`; `REQUIRED_KEYS`, `MIN_PROOF_LENGTH` |
| `env_proof.py` | entorno de la fase 2: estado = máscara de pasos establecidos; válido ⇔ deps cumplidas, no repetido, no distractor |
| `trainer.py` | bucle de ambas fases, hitos (`mark`), política voraz, curvas; importa `QAgent` de `didactica.qagent` |
| `tui.py` | interfaz `rich` (necesita terminal ≥ 120×40) |
| `report.py` | `informe.md`, `demostracion.md`, `historia.json` en `<out>/<fecha>/` |
| `cli.py` | flags: `--episodes1 --episodes2 --seed --tol --speed --fast --no-tui --out` |

`steprl` rompe el patrón: no hay grafo de lemas; un SDP (`pep.py`) certifica cada propuesta, `certify.py` produce
certificados racionales exactos y `evolve.py` hace que un LLM proponga programas. Las claves se leen del `.env` de la
raíz (ignorado por git; nunca se imprime ni se copia).

## Cómo ejecutar

Un solo entorno virtual en la raíz (Python 3.13 en esta máquina; el CI usa 3.12):

```bash
cd ~/Personal/rl_metodos && source .venv/bin/activate      # o: python -m venv .venv && pip install -e ".[dev]"
python -m didactica.biseccion                              # con animación, ~1–2 min
python -m didactica.biseccion --no-tui --seed 1 --out /tmp/runs   # sin interfaz: < 1 s (no escribir en runs/)
python -m steprl verify                                    # ~2 s
python -m unirl target --config unirl/configs/bisection_graph.toml
pytest -q                                                  # todo; las de Isabelle se omiten si no está instalada
pytest -q -m "not isabelle"                                # lo que corre el CI
```

Tiempos medidos (25 sep 2026, `resultados/corridas_locales/tiempos.md`): `--no-tui` con 3000 + 3000 generaciones tarda
0,35–0,41 s en bisección, punto fijo, Taylor, Newton y secante, y 7,9–8,0 s en interpolación; `steprl verify`, 2,3 s.

Calibración de bisección con semilla 1 (reproducida exacta el 25 sep 2026 y tras la reorganización): λ = ½ estable en la
generación 345, invariante de Bolzano en la 358, primera demostración completa en la 256 de la fase 2, primera mínima
en la 459. Con 100 generaciones no aprende nada; con 300 aprende a medias. Útil para laboratorios.

El RL verbal (`unirl.experimentos`) llama a la API de OpenAI y gasta dinero: **solo lo lanza Carlos**, con los comandos de
`docs/formulacion/RELANZAMIENTO.md`. Claude no lanza corridas ni llama a la API.

## Convenciones

* Commits en español, imperativo o descriptivo corto, con prefijo del paquete (`unirl: ...`, `didactica: ...`, `steprl: ...`).
* Un solo `.gitignore` en la raíz. `runs/didactica/` y `runs/pep/` no se versionan (registros deterministas o pesados);
  `runs/unirl/`, `runs/isabelle/` y `runs/corridas_locales/` sí, salvo `llamadas.jsonl` (texto íntegro de cada llamada,
  citado por SHA-256). `logs/*.sqlite`, candados y `tests/unirl/fixtures/pruebas_privadas/` tampoco se versionan.
* `runs/` (incluido `runs/unirl/cuaderno/`), `logs/`, `corpus/`, `certificados/`, `gasto.json` y todo `*.jsonl` son **intocables**: no se
  reescriben ni se borran; si hay que moverlos, con SHA-256 antes y después.
* Los README de cada subpaquete son la documentación de referencia; el README raíz resume la serie con cifras
  auditadas (`resultados/auditoria_cifras.md`). Toda cifra lleva su archivo de origen; sin archivo, «no medido».
* CI (`.github/workflows/tests.yml`): `pip install -e ".[dev]"`, `pytest -m "not isabelle"` y dos humos, en Python 3.12.
* Para fines docentes no se cambian los paquetes: los experimentos de laboratorio se hacen con los scripts de
  `docs/curso/labNN/` (cambian constantes en memoria) y se revierten con `git checkout`.
* Corridas nuevas: `runs/<juez>/<dominio>/<fecha>/`. Nada nuevo se crea fuera de la estructura de `MIGRACION.md`.

## Honestidad sobre lo que hace la "fase 2"

La fase 2 **no demuestra teoremas**: el grafo de lemas está escrito a mano y el agente aprende un orden topológico
válido y a descartar distractores. Lo matemáticamente sustancioso es escribir el grafo (qué depende de qué, qué errores
son tentadores). Esto hay que decirlo así a los estudiantes. El salto a "el agente encuentra la demostración" solo
ocurre con un verificador independiente: el SDP de `steprl` y el kernel de Isabelle en `unirl` («Luna demuestra,
Isabelle verifica»; nunca «Isabelle demostró»).
