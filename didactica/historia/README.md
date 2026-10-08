# didactica.historia

**Un agente de RL rehace, en vivo en la terminal, episodios de la historia de la matemática:
primero aprende a HACER (medir, cuadrar, trazar paralelas), luego aprende a DEMOSTRAR.**

Mismo estilo que BisectRL (`didactica.biseccion`): tabla Q, recompensas, verificador de
dependencias con distractores, bitácora de hitos, informe final. Novedad: los pasos
**ámbar** (`externo=True`), postulados o citas que el verificador acepta pero no deriva.
Cuando una demostración llega a ∎ apoyada en ámbar, la interfaz lo dice.

```
python -m didactica.historia --list
python -m didactica.historia euclides     --speed 3
python -m didactica.historia cuadratura   --speed 3
python -m didactica.historia quinto       --speed 3
python -m didactica.historia beltrami     --speed 3
python -m didactica.historia --all --fast --no-tui      # sólo informes
pytest -q tests/didactica/test_historia.py
```

| episodio | fase 1 (hacer) | fase 2 (demostrar) | lo que se ve |
|---|---|---|---|
| `euclides` | antifairesis: dos segmentos, quitar b de a hasta que uno mida al otro | *Elementos* VII.1–2: el proceso termina y da la mayor medida común | el residuo emerge de la economía de pasos |
| `cuadratura` | regla y compás: cuadrar un rectángulo (II.14) y un círculo | imposibilidad moderna, con **LIND** (Lindemann) en ámbar | el "mejor error" del círculo baja y nunca llega a 0 |
| `quinto` | ¿plano o disco de Klein? trazar por P y contar paralelas | intentar deducir el V de I–IV: toda ∎ pasa por **PUENTE** (ámbar) | Beltrami en colores: no hay demostración limpia |
| `beltrami` | — | consistencia relativa de la hiperbólica por modelo | la consistencia se traslada, no se gana |

## Estructura

```
didactica/historia/
  core.py          Step (con `externo`), ProofKB, ProofEnv, protocolo Phase1, Trainer genérico, Raster
  tui.py           interfaz en vivo (rich): tablero de fase 1, política aprendida, demostración, creencia, marcador, bitácora
  report.py        informe.md, demostracion.md, historia.json
  cli.py           línea de comandos
  episodios/       un archivo por parada: entorno de fase 1 + grafo de lemas + distractores + lectura
```

## Añadir un episodio

1. Un entorno de fase 1 que cumpla `core.Phase1` (`reset`, `step`, `render`, `policy_summary`,
   `milestones`, `headline`, `optimal_steps`), o `make_phase1=None` si sólo hay demostración.
2. Una lista de `Step` con `deps`; distractores con `distractor=True`; postulados/citas con `externo=True`.
3. Un `Episodio(...)` llamado `EPISODIO`, y registrarlo en `episodios/__init__.py`.

El `QAgent` se importa de `didactica/qagent.py` (el compartido del repo); si no está, `core.py`
trae uno equivalente de respaldo.

Requiere Python ≥ 3.10, `rich`, y una terminal de al menos 140 × 45.
