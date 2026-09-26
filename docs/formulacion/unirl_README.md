# 09 · UniRL — un MDP, jueces intercambiables

**Un solo entorno para toda la serie: un proponente (LLM) propone un objeto de demostración y un verificador
independiente lo puntúa. El agente nunca se puntúa a sí mismo.** Los proyectos 01–08 no se tocan: `unirl`
los importa desde sus carpetas (`sys.path`) y los envuelve.

La definición formal, los resultados y las amenazas a la validez están en la nota técnica
[`docs/nota/unirl_definicion.pdf`](docs/nota/unirl_definicion.pdf) (fuente `.tex` en la misma carpeta).

```
unirl/verifiers.py   Outcome{accepted, outcome_label, partial_credit, cost_s, raw}; tres jueces con la misma interfaz
unirl/env.py         ProofEnv: estado = (enunciado, lemas/VCs disponibles, historial); acción = propuesta; episodio ≤ B
unirl/loop.py        bucle proponente–verificador (estructura de steprl.evolve del 06), JSONL de cada intento
unirl/cli.py         run / summary / tables / target
unirl/report.py      tablas y macros LaTeX para la nota, generadas desde los JSONL
configs/*.toml       un archivo por entorno: método, juez, proveedor, modelo, presupuesto
targets/             objetivos congelados del juez Isabelle (programa + tripleta + lemas prestados), con su hash fijado
tools/               línea base con la anotación del artículo; Sledgehammer sobre VCs sueltas
tests/               jueces, bucle y resumen sin LLM; los marcados `isabelle` necesitan Isabelle2025
```

## Los tres jueces

| juez | propuesta | acepta si | etiquetas | en qué reposa su confianza |
|---|---|---|---|---|
| `lemma_graph` (01–05) | lista ordenada de ids de paso (`L01`…) | la cadena respeta dependencias, no repite, no usa distractores y llega a QED | ACCEPTED, INVALID_STEP, DISTRACTOR, UNKNOWN_LEMMA, INCOMPLETE | **el grafo escrito a mano**: acepta exactamente lo que su autor consideró válido. No demuestra nada por sí mismo |
| `pep` (06) | código Python `schedule(n)` | modo `improve` (defecto): el peor caso mejora estrictamente τ_ref y la mejora pasa el certificado racional exacto de 06. Modo `match`: además igualar numéricamente | CERTIFIED, MATCHED, NOT_IMPROVED, CERTIFICATION_FAILED, INVALID_SCHEDULE | el SDP de 06 y su certificador exacto |
| `isabelle` (08) | invariante y variante del bucle | el teorema completo se compila en el kernel sin oráculos (ver abajo) | ACCEPTED, VC_OPEN, VCG_FAILED, ASSEMBLY_FAILED, UNSOUND, STATEMENT_DRIFT, TIMEOUT, INVALID_PROPOSAL | el kernel de Isabelle/HOL; la adecuación de la tripleta; la elección de los lemas prestados |

**Qué ve el proponente en `lemma_graph`.** Ids anonimizados y barajados (semilla fija), el texto de cada paso y la
longitud mínima. No ve los títulos (en 01–05 delatan al distractor) ni la refutación que el profesor puso entre
paréntesis al final de 7 de los 36 distractores («(¡falso: …!)»).

**`pep`.** El programa propuesto se ejecuta en un intérprete aparte (`python -I`) y el juez puntúa la sucesión
literal que devuelve. Una revisión adversarial mostró que, ejecutado en el proceso del juez (como hace 06), el
programa podía alcanzar por introspección `steprl.env` y sustituir la puntuación y el certificado.

**`isabelle`, por etapas.**
0. Lista blanca de la anotación (letras, dígitos, puntuación de términos y una lista de símbolos `\<…>`); lo que
   intenta salir del hueco (comillas, cartuchos, comentarios, `;`, `:=`, `do`/`od`/`fi`, marcadores `__X__`) es
   STATEMENT_DRIFT. Después, el kernel demuestra que el programa anotado es igual al congelado con anotaciones fijas
   (`while_inv_var B I V P = iterate B P`, así que solo pueden diferir las anotaciones); si no, STATEMENT_DRIFT.
1. `vcg` sobre la tripleta (driver de 08).
2. Cada VC: `try0` 5 s y, si falla, Sledgehammer 60 s. Solo cuentan sugerencias con *preplay* terminado.
3. Si todas cierran: se ensambla el teorema (`apply vcg`, un `subgoal` por VC, `done`), se pasa al programa congelado
   con la igualdad de la etapa 0 y se compila en una sesión con nombre único.
4. El teorema no puede depender de oráculos ni de `skip_proof` (`Thm_Deps.all_oracles`).

El hash de la parte congelada del objetivo está fijado en su JSON (`frozen_hash`) y se recalcula desde disco en cada
verificación. Un objetivo de control (`targets/countdown.json`) comprueba ACCEPTED, VC_OPEN y la detección de oráculos.

Recompensa: 1 en ACCEPTED, 0 en el resto. Con `--shaped --beta β` (β ∈ [0, 0,5]) se suma β·(crédito parcial) en los
pasos no aceptados. `drift_penalty = δ` en la configuración da −δ a STATEMENT_DRIFT (experimentos de control).

## Uso

```bash
cd 09_unified && python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"
python -m unirl target  --config configs/bisection_graph.toml        # lo que ve el proponente
python -m unirl run     --config configs/bisection_graph.toml --episodes 20
python -m unirl run     --config configs/bisection_isabelle.toml --episodes 3 --model gpt-6-luna --effort high
python -m unirl summary runs/                                        # una tabla por (entorno, juez, modelo, esfuerzo)
python -m unirl tables  runs/ --out docs/nota && (cd docs/nota && latexmk -pdf unirl_definicion.tex)
pytest -q -m "not isabelle"      # rápidos
pytest -q -m isabelle            # extremo a extremo con Isabelle (~2 min; no correr durante un experimento)
```

Las claves se leen de `06_stepsizes/.env` (vía `steprl.providers`). Proponente de todas las configuraciones:
`gpt-6-luna` con esfuerzo `high` (decisión del autor para v0.2); se cambia en el `.toml` o con `--model/--effort`.
Las corridas con `gpt-5.4-mini` quedan archivadas en `runs/_excluido_solo_luna`.
Con `memory = "run"` el proponente recuerda entre episodios: la biblioteca de lemas que demostró y que Isabelle
verificó (se añaden solos a cada intento) y el mejor intento de cada episodio. `memory_prompt` fija la redacción de
ese encabezado: `v1` es la de la primera corrida de Luna y se mantiene en `bisection_isabelle_lemas_mem.toml` para
comparar modelos con el mismo mensaje; `v2` (por defecto) atribuye bien: el agente demuestra, Isabelle verifica.
Las corridas de Isabelle no deben solaparse: Sledgehammer tiene límite de tiempo real.

Las carpetas `runs/_*` son pilotos, corridas descartadas (cada una con un `LEEME.md` que explica por qué) y líneas
base; `summary` y `tables` las ignoran.
