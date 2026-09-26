# rl_metodos

**Agentes de Reinforcement Learning que aprenden métodos numéricos y «demuestran» su convergencia en la terminal; un
entorno con jueces intercambiables (grafo de lemas, PEP, Isabelle/HOL); y un experimento de RL verbal con memoria
certificada por el kernel de Isabelle.** Toda cifra de este README tiene registro (`resultados/auditoria_cifras.md`,
25 sep 2026); lo que no se ha medido se dice.

## Un solo paquete

```bash
python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"
python -m didactica.biseccion                    # o punto_fijo, taylor, newton, secante, interpolacion; --no-tui < 1 s
python -m steprl verify                          # el verificador PEP contra sus referencias (~2 s)
python -m unirl target --config unirl/configs/bisection_graph.toml
pytest -q                                        # 77 pruebas didácticas y de steprl + 170 de unirl; Isabelle si está
```

| carpeta | qué es |
|---|---|
| `didactica/` | seis agentes tabulares, uno por método, con un único `QAgent` (`qagent.py`) |
| `unirl/` | un MDP, jueces intercambiables; el RL verbal con cuaderno; `configs/`, `tools/` |
| `steprl/` | juez PEP: verificador SDP, certificados racionales exactos, evolución con LLM |
| `isarl/` | juez Isabelle: `vcg` + `try0` + Sledgehammer; reproducción de la Tabla 1 de Bryant, Huerta y Munive, Foster (2026) |
| `corpus/curado/` | `raices/`: 48 peldaños de búsqueda de raíces en Isabelle, aprobados uno a uno; `programas/` y `stepsize/`: los objetivos congelados del juez Isabelle y sus certificados |
| `runs/`, `logs/`, `certificados/` | registros de corridas y estado (el cuaderno vivo del RL verbal está en `runs/unirl/cuaderno/`); intocables |
| `resultados/` | inventario, métricas consolidadas, estadística, auditoría de cifras, informe de estado (PDF) |
| `docs/formulacion/` | la formulación del RL verbal (H1–H4, McNemar, potencia), la nota técnica de `unirl`, el plan y el relanzamiento |
| `docs/curso/` | material docente: contexto, laboratorios 1 y 2 |

`ESTRUCTURA_OBJETIVO.md` es la estructura de destino y `MIGRACION.md` la tabla ruta vieja → ruta nueva (los proyectos 01–09 de antes del 26 sep 2026).

## La serie didáctica (`didactica/`)

Cada método es un proyecto con el mismo formato, al estilo de los vídeos de *AI Warehouse*:

1. **Fase 1 · el método.** Un agente tabular (Q-learning) que no conoce el algoritmo aprende, a base de recompensas, a
   ejecutarlo. Lo que emerge es el método del libro de texto.
2. **Fase 2 · la demostración.** El teorema de convergencia se modela como un grafo de lemas con dependencias, mezclado
   con distractores (errores reales de estudiante). El agente aprende a ordenar los pasos válidos y a rechazar los
   distractores. **No demuestra nada nuevo**: el grafo está escrito a mano.
3. **Interfaz en vivo** con `rich` e **informe** en Markdown con la historia en JSON.

| método | qué aprende el agente | medido (semilla 0 salvo indicación; `resultados/corridas_locales/`) |
|---|---|---|
| bisección | cortar en λ = ½ y conservar el subintervalo con cambio de signo | con semilla 1: λ = ½ estable en la generación 345, invariante de Bolzano en la 358; demostración completa en la 256, mínima en la 459 |
| punto fijo | ajustar α en x ← x − α·f(x) hasta que el mapa sea contractivo | un α fijo converge el 33,1 % de las veces; el agente, el 93 % con 11,7 iteraciones de media |
| Taylor | cuántos términos sumar, cuándo parar y cuándo la serie no converge | 90 % de aproximaciones correctas con 9,7 términos de media |
| Newton | cuándo dar el paso completo y cuándo amortiguar (Armijo emerge) | Newton puro converge el 74,4 %; el agente, el 96 % con 9,2 evaluaciones; orden observado 2,25 |
| secante | cuándo fiarse de la secante y cuándo refugiarse en el corchete (Dekker emerge) | secante pura 67,6 %, regula falsi 62,9 %, bisección 100 % con 31,7 evaluaciones; el agente 100 % con 10,2; orden observado 1,60 |
| interpolación | dónde poner los nodos (Chebyshev emerge frente a equiespaciados) y cuántos; fase 3: nodos con constante de Lebesgue menor que Chebyshev, con verificador | γ = 1 (Chebyshev) estable en la generación 726 (semilla 1) y 543 (semilla 0); Λ con n = 16: 934,5 equiespaciados frente a 2,725 Chebyshev; búsqueda n = 8: Λ = 1,93867 (Chebyshev extendido 1,94157) |

Los proyectos se encadenan: el punto fijo óptimo (α = 1/f′) es el paso de Newton; el resto de Lagrange de Taylor es
la herramienta con la que Newton demuestra la convergencia cuadrática; Bolzano reaparece en el punto fijo; la secante
es Newton con la derivada sustituida por un cociente incremental y usa el corchete de la bisección como salvaguarda.

## Los jueces (`unirl`, `steprl`, `isarl`)

Un proponente (un modelo de lenguaje) propone un objeto de prueba y un juez independiente decide. La recompensa solo
viene del juez; el proponente nunca se puntúa a sí mismo. Lo que cambia es el juez, y con él lo que la aceptación deja
sin certificar (`docs/formulacion/unirl_definicion.pdf`):

| juez | acepta | en qué reposa la confianza | medido |
|---|---|---|---|
| grafo de lemas (V_G) | una cadena válida en el grafo escrito a mano | el autor del grafo | gpt-6-luna: 20 de 20 episodios en los cinco métodos |
| PEP (V_P, `steprl`) | una cota de peor caso mejor que la referencia, con certificado racional exacto | la formulación del PEP y el certificador | 5 mejoras certificadas de gpt-6-astra sobre nuestra referencia (0,45–1,0 %); certificados exactos para n = 2, 3, 6, 12 (`certificados/`); en n = 6 el certificado da 0,019665 frente a 0,0201 tabulado: **no resuelto** |
| Isabelle/HOL (V_I, `isarl`) | el teorema compilado en el kernel, sin oráculos | el kernel; la adecuación del enunciado; la matemática importada | 0 aceptados en 40 intentos válidos de dos modelos; la reproducción de la Tabla 1 del artículo: 15 VCs, la automatización sola cierra 9 en 60 s, 13 tienen prueba de una línea verificada |

**RL verbal con memoria certificada** (`docs/formulacion/formulacion_rl_verbal.tex`): una política fija (pesos
congelados) acumula un cuaderno de lemas verificados por el kernel, errores y estrategias; H1–H4 prerregistradas, con
McNemar pareado y potencia declarada. Línea base del martillo solo: **1 de 48** peldaños (test 0 de 16). La primera ronda
está preparada (`docs/formulacion/RELANZAMIENTO.md`) y **no ha terminado**: sus corridas del 25 sep 2026 se interrumpieron
por dos errores ya corregidos; no hay aún ninguna medida de H2.

## Ideas de diseño que se repiten

* **Shaping basado en potencial** (Ng, Harada y Russell, 1999): recompensa densa sin cambiar la política óptima.
* **Estados observables, no privilegiados**: nada que el método real no pueda medir.
* **Distractores que son errores reales de estudiante**: «Bolzano garantiza raíz, luego el método converge».
* **Hitos comparados con la teoría**: el informe marca cuándo la política coincide con la regla del libro y señala los matices.
* **El potencial del shaping no depende de lo que el agente controla**.
* **Cuatro estados de corrida que no se mezclan**: terminado, en curso, interrumpida por error, planeado. Toda cifra con archivo.

## Licencia

MIT.
