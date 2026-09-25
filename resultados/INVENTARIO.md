# Inventario de resultados · rl_metodos (Etapa 0)

Hecho el 25 sep 2026, entre las 12:00 y las 13:00 (hora de Colombia, UTC−5), por Claude, **solo leyendo**. No se
modificó ningún archivo del repo fuera de `resultados/`, no se interrumpió ni se lanzó ninguna corrida y no se llamó a
ninguna API. Commit de referencia (HEAD): `dcb8f7bc343870eadb7482527fbc7614c3e7f251`.

---

## 0. Lo que cambia la premisa del pedido

1. **No hay nada corriendo.** `ps` (12:09) no muestra ningún proceso de Python, Isabelle ni `caffeinate`. La única
   pestaña de la terminal no está ejecutando nada. El Mac arrancó hoy a las 07:09.
2. **Las cinco corridas de la Etapa 7 del RL verbal (25 sep, 07:32–09:27) se detuvieron por dos errores de código.
   Ninguna terminó.** La huella actual de `unirl` (`5ef59e25793670fb`, SHA-256 de `unirl/*.py`) coincide con la que
   registran esas corridas, así que los dos errores siguen sin corregir.
   * **Evaluación (B0/B/C de Luna, C3 de Luna y C3 de Sol).** El caché SQLite del martillo se crea en el hilo principal.
     Cuando un episodio corre en un hilo trabajador y el modelo entrega una prueba con marcas `by martillo` que pasan los
     filtros, `Cache.lineas_de` lanza `sqlite3.ProgrammingError` (`unirl/martillo.py:295`) y el episodio muere sin
     quedar registrado. El bucle de `evaluar` solo captura `ProviderFatal` (`unirl/experimentos.py:315–322`), pero
     `ThreadPoolExecutor.__exit__` espera a los trabajos pendientes. Por eso cada corrida **recorrió toda su lista de
     trabajos** y solo al final imprimió el error y salió, sin escribir `episodios.csv` ni `resumen.md`. Se perdieron
     **63 de 128 episodios** (47 + 9 + 7). **La pérdida no es aleatoria**: son justamente los episodios en que el modelo
     quiso usar el martillo por pasos. Los conteos parciales no estiman ninguna tasa.
   * **Cuaderno (Luna, config. F, train).** En la primera destilación, tras 6 de 32 episodios, Luna devolvió 5 errores
     aprendidos sin el campo `en_su_lugar`. `Cuaderno.guardar()` escribió `errores.json`, `lemas.json` y
     `estrategias.json`, y después cayó al generar `errores.md` (`KeyError`, `unirl/cuaderno.py:77`). El cuaderno en
     disco quedó a medio escribir (§4).
3. **Consecuencia:** no hay cuaderno congelado, así que E, E3 y la línea base del martillo con cuaderno no se pueden
   correr. **La primera ronda no tiene ninguna corrida terminada.** Las pruebas de la Etapa 2 (Clopper–Pearson,
   McNemar, acuerdo entre episodios) no tienen hoy datos para las hipótesis de la primera ronda.
4. **`formulacion_rl_verbal.tex` no está en el disco.** H1–H4 no aparecen definidas en ningún archivo del repo. Hasta
   recibirla no puedo enlazar resultados con hipótesis ni saber qué pruebas admite la formulación.

## 1. Convenciones de este inventario

* **Estados** (decisión de Carlos del 25 sep: cuatro, nunca mezclados). *Terminado*: corrida completa. *En curso*:
  ejecutándose ahora, con resultado parcial, fecha y porcentaje de avance. *Interrumpida por error*: se detuvo por un
  error del código o de la infraestructura; sus datos son parciales y no estiman nada. *Planeado*: diseñado, sin datos.
* **Procedencia.** 01–07 están versionados, y el paquete de cada uno no cambia desde su último commit: 01 y 02
  `ee8277d`, 03 y 04 `51ded6b`, 05 `70aedc6`, 06 `4e447f1` y 07 `0c992c8`. Pero sus `runs/` están ignorados por git
  y no anotan el commit, así que el commit de una corrida se infiere por su fecha. **`08_isabelle/` y `09_unified/` no
  están versionados** (`??` en `git status`): el `git_commit: dcb8f7b` que anotan las corridas de 09 no identifica su
  código. Lo identifica la huella `unirl_sha256` de cada `meta.json`. Propongo fijar además cada archivo fuente por su
  SHA-256 (apéndice A).
* **Horas.** Locales (UTC−5), salvo las del CI de GitHub (UTC).

---

## 2. Inventario por subproyecto

### 01 · bisección (`bisectrl`)

| experimento | configuración | registros | estado | métricas disponibles |
|---|---|---|---|---|
| Q-agent, fases 1 y 2 | 3000 + 3000 generaciones, semilla 0, tol 10⁻³ | 8 corridas (15, 16, 18 y 24 sep) en `01_biseccion/runs/2026091{5,6,8}-*/` y `20260924-161133/`: `historia.json`, `informe.md`, `demostracion.md` | terminado | Hitos idénticos en las 8 (el entrenamiento es determinista). Fase 1: Bolzano en la gen. 305, λ = ½ estable en la 343, ≥ 95 % de convergencia desde la 475; 2818 convergencias y 182 raíces perdidas. Fase 2: primera demostración completa en la gen. 303, política voraz mínima desde la 375, primera mínima en la 435; 2672 completas y 1686 mínimas; 9682 saltos lógicos (3593 con distractores). Curvas por generación. |
| Q-agent corto | 200 + 100, semilla 42 | 2 corridas (21 sep): `runs/20260921-09{3835,4003}/` | terminado | 52 convergencias de 200; 0 demostraciones |
| calibración citada en `CLAUDE.md` | semilla 1 | **ninguno** | — | **No medido.** Las cifras λ = ½ ~345, Bolzano ~358, demostración ~256 y mínima ~459 no tienen archivo de origen. |
| CI (humo) | 800 + 800, semilla 0, Ubuntu, Python 3.12.14 | GitHub Actions, run 35779899804 (commit `dcb8f7b`, 22 sep 20:22 UTC) | terminado | pytest pasa; el informe impreso está en el log |

### 02 · punto fijo (`fixpointrl`)

| experimento | configuración | registros | estado | métricas disponibles |
|---|---|---|---|---|
| Q-agent, fases 1 y 2 | 3000 + 3000, semilla 0, tol 10⁻⁶ | `02_punto_fijo/runs/20260908-231722/` | terminado | Fase 1: ley de control igual a la de Banach en los 12 estados (gen. 1612), ≥ 95 % desde la 661; 2667 convergencias, 218 divergencias y 115 agotadas. Fase 2: completa en la gen. 193, mínima en la 440; 2788 completas y 1715 mínimas. |
| CI (humo) | 800 + 800, semilla 0 | run 35779899804 | terminado | pytest pasa |

### 03 · Taylor (`taylorrl`)

| experimento | configuración | registros | estado | métricas disponibles |
|---|---|---|---|---|
| Q-agent, fases 1 y 2 | 3000 + 3000, semilla 0, tol 10⁻⁶ | `03_taylor/runs/20260908-234647/` y `20260915-073657/` (idénticas) | terminado | Fase 1: ley igual a la teoría en 11 estados (gen. 898), ≥ 95 % desde la 1390; 1352 aproximaciones correctas, 1104 divergencias detectadas y 544 veredictos erróneos. Fase 2: completa en la gen. 194, mínima en la 322; 2783 completas y 1664 mínimas. |
| CI (humo) | 800 + 800, semilla 0 | run 35779899804 | terminado | pytest pasa |

### 04 · Newton (`newtonrl`) y 05 · secante (`secantrl`)

| experimento | configuración | registros | estado | métricas disponibles |
|---|---|---|---|---|
| Q-agent con la configuración por defecto | 3000 + 3000 | **ninguna corrida guardada** (no hay `runs/`) | — | **No medido** en local. Las cifras del README no tienen registro. |
| CI (humo) | 800 + 800, semilla 0 | run 35779899804, jobs 106922444949 (04) y 106922444907 (05) | terminado | pytest 6/6 (04) y 8/8 (05). El informe impreso está en el log; por ejemplo, 04: orden observado ≈ 2,13 y ley igual a Armijo en 6 de 7 estados. |

### 06 · stepsizes (PEP, `steprl`)

| experimento | configuración | modelo | registros | estado | métricas disponibles |
|---|---|---|---|---|---|
| `evolve` 01 | objetivo anytime; métrica de la época: garantía anclada en ½; salida de 16k | gpt-6-astra | `06_stepsizes/runs/20260909-214116/evolucion.json`; nota `docs/ejecucion-01-gpt-6-astra.md` | terminado | 17 generaciones más 2 líneas base; **6 válidas**, 11 cortadas por longitud; la gen. 17 sobreajusta el horizonte (`_HORIZON = 31`). El exponente por duplicación de la nota (1,047 en la gen. 2) se recalculó a posteriori y **no está en el JSON** (§4). |
| `evolve` 02 | exponente por duplicación, horizontes 31 y 63 | gpt-6-astra | `runs/20260910-075701/` | terminado | 4 generaciones, 4 válidas |
| `evolve` 03 | puntuación C(1,12) | gpt-6-astra | `runs/20260910-090345/`, `runs/evolve-03.log` | terminado | 20 generaciones; **1 válida**, 19 con error de conexión |
| `evolve` 04 | puntuación C(1,12) | gpt-6-astra | `runs/20260910-102749/`, `runs/evolve-04.log` | terminado | 20 generaciones; 9 válidas, 8 SolverError de Clarabel y 3 errores de conexión. Mejor C(1,12) = 0,167 (gen. 15), frente a 0,408 del paso constante y 4,161 del silver (menor es mejor). |
| referencias por entropía cruzada | 60 instancias (n ≤ 12; μ ∈ {0; 0,01; 0,1}; f(xₙ) − f* y ‖∇f(xₙ)‖²) | — | `steprl/refs.json`, `runs/refs-20260916.log` | terminado | τ_ref por instancia: 54 de la búsqueda propia y 6 de la tabla publicada |
| certificados racionales exactos | f(xₙ) − f*, μ = 0, L = 1 | — | `certificados/fval_mu0_n{3,6,12}.json` (commit `4e447f1`), `runs/cert-*.json` | terminado | τ certificado: n = 2: 0,065951634994; n = 3: 0,042893459677; n = 6: 0,019665446255; n = 12: 0,008972494158. En n = 6 hay dos certificados distintos (§4). |
| pruebas | pytest | — | CI, run 35779899804, job 106922444942 | terminado, **falla** | 2 de 36 fallan (`tests/test_env.py:32` y `:62`): comparan con la referencia vieja de la tabla (0,042895), que cambió en `refs.json` con el commit `4e447f1`. **CI en rojo desde el 17 sep.** |
| PEP como juez en 09 (V_P) | 5 variantes abiertas × 3 episodios, B = 4, memoria entre episodios | gpt-6-astra y gpt-6-luna | `09_unified/runs/pep_*/` (24 sep, 06:01–08:00) | terminado | Astra: 15 de 15 episodios CERTIFIED (16 intentos, 1 INVALID_SCHEDULE por un NameError), que son **5 descubrimientos y 10 repeticiones** (ver abajo). Luna: 0 de 15 (60 intentos: 59 NOT_IMPROVED y 1 INVALID_SCHEDULE). |
| lo mismo, descartado | 10 corridas lanzadas sin créditos | ambos | `09_unified/runs/_descartado_sin_creditos/` | terminado, **sin datos** | 120 PROVIDER_ERROR; no miden nada |

**La «fuga de memoria» del PEP.** No es una fuga de memoria RAM: es la solución colándose por la memoria entre
episodios, y ocurrió en las corridas de 09 que usan el juez PEP de 06. En los episodios 2 y 3 de cada variante, Astra
recibió en el resumen de episodios anteriores el programa ya certificado del episodio 1, y lo volvió a enviar.
Comprobado con las sucesiones de pasos `h` de `attempts.jsonl`:

| variante | τ_ref (entropía cruzada) | τ de Astra, ep. 1 | mejora | episodios 2 y 3 frente al 1 |
|---|---|---|---|---|
| ‖∇f‖², n = 4, μ = 0 | 0,016985992 | 0,016909103 | 0,453 % | programa idéntico (mismo SHA) |
| ‖∇f‖², n = 4, μ = 0, pasos negativos permitidos | 0,016985992 | 0,016909103 | 0,453 % | programa idéntico; mismos 4 pasos positivos que sin permitir negativos, en otro orden |
| ‖∇f‖², n = 6, μ = 0 | 0,007222300 | 0,007153534 | 0,952 % | otro código, pasos idénticos |
| f − f*, n = 4, μ = 0,01 | 0,029543102 | 0,029324729 | 0,739 % | pasos casi iguales (diferencia máxima 4,5·10⁻⁵) |
| f − f*, n = 5, μ = 0,1 | 0,007605479 | 0,007528933 | 1,006 % | pasos casi iguales (diferencia máxima 4,2·10⁻⁵) |

Corrección aplicada: (a) en el recuento, 5 descubrimientos independientes y no 15
(`09_unified/docs/informes/pep_variantes-gpt-6-astra/comentario.tex`); (b) en el diseño del RL verbal, los episodios de
evaluación son independientes, sin memoria de episodios (PLAN §1, punto 7). La referencia es la búsqueda propia, no un
óptimo publicado: CERTIFIED dice «mejor que nuestra búsqueda», no «mejor que la literatura».

### 07 · interpolación (`interprl`)

| experimento | configuración | registros | estado | métricas disponibles |
|---|---|---|---|---|
| fases 1 y 2 | 3000 + 3000, semilla 1 (según el README) | **ninguna corrida guardada** | — | **No medido.** Las cifras del README no tienen registro. |
| fase 3 (constante de Lebesgue Λ) | n = 4, 8, 12 | tabla del README, sin registro | — | **No medido.** |
| CI (humo) | 800 + 800 y `search --n 4 --iters 5` | run 35779899804, job 106922444925 | terminado | pytest 9/9. Informe impreso: 343 aproximaciones correctas, 452 entregas prematuras y 5 agotadas en 800; γ = 1 (Chebyshev) estable desde la gen. 543. |

### 08 · Isabelle: reproducción de la Tabla 1 del artículo

Artículo: Bryant, Huerta y Munive y Foster (2026), arXiv:2511.20550v3 (`09_unified/docs/nota/unirl_definicion.bib`).
Código del artículo fijado en `Verified_Numerical_Methods@0e7830d`, fuera del repo (`~/isabelle/PINS.md`).

| experimento | configuración | registros | estado | métricas disponibles |
|---|---|---|---|---|
| compilación de la sesión del artículo | Isabelle2025, heaps propios | solo la nota `08_isabelle/docs/reproduccion-bisection.md` (no hay log crudo en el repo) | terminado | HOL-Analysis 5 min 09 s, ITree_Numeric_VCG 1 min 50 s, Numerical_Methods_Paper 36 s. Dos desviaciones documentadas: `root.tex` mínimos y submódulos de Isabelle/UTP fijados al 16 ene 2026. |
| fila «Bisection: 15 VCs, 13 auto» | `vcg`; por VC, `try0` 5 s y Sledgehammer 60 s; 7 demostradores | `08_isabelle/runs/repro_bisection.json` (23 sep 15:00; 424 s) | terminado | 15 VCs. **La automatización sola cierra 9**: VC 1, 2, 3, 5, 6, 7, 11, 12 y 13. **2 más** (VC 14 y 15) solo con el lema importado `bisect_root_extract`, que empaqueta la prueba manual del artículo. **4 abiertas** (VC 4, 8, 9 y 10, el variante). |
| VC 4 con más tiempo | Sledgehammer 240 s | `08_isabelle/runs/repro_vc4_240s.json` | terminado | timeout a los 243,6 s |
| línea `smt` del artículo | aplicada a las VC 4, 8, 9 y 10 | `09_unified/runs/_baseline/given_smt_08.json` (23 sep 19:37) | terminado | Las 4 cierran en 183–210 ms con 18 hechos. **13 de 15 tienen una prueba de una línea verificada**, como dice el artículo. |
| VC adelgazada a una premisa | Sledgehammer 60 s, con y sin el preludio del artículo | `09_unified/runs/_baseline/sh_goals.json` | terminado | timeout en las 4 combinaciones |
| cota superior del juez V_I | anotación del artículo más lemas auxiliares | `09_unified/runs/_baseline/upper_bound.json` | terminado | ACCEPTED, 15 de 15 VCs, 214,5 s: el juez sí puede aceptar |
| primer intento del driver | — | `08_isabelle/runs_repro.log` (23 sep 14:52) | terminado, fallido | error léxico de SML; sustituido por la corrida de las 15:00 |

**Intentos de Luna y Astra bajo el juez de Isabelle.** Los registros están en `09_unified/runs/`, no en 08.

| corrida | modelo | configuración | intentos | aceptados | etiquetas |
|---|---|---|---|---|---|
| `bisection_isabelle/20260923-155924` | Luna | invariante y variante, 3 episodios, B = 4 | 12 | 0 | 12 VC_OPEN |
| `bisection_isabelle_lemas/20260923-211101` | Luna | + lemas, sin memoria; detenida en el ep. 2 a pedido del autor (vale el ep. 1) | 4 | 0 | 2 VC_OPEN, 2 LEMMA_FAILED |
| `bisection_isabelle_lemas_mem/20260923-215521` | Luna | + lemas + memoria (v1), 3 episodios | 12 | 0 | 2 VC_OPEN, 10 LEMMA_FAILED |
| `…lemas_mem/20260923-224900` + `20260924-060102` | Astra | lo mismo; el ep. 3 se perdió sin créditos y se repitió | 12 válidos (+4 PROVIDER_ERROR) | 0 | 12 LEMMA_FAILED; mediana por respuesta de 1149 s en la primera carpeta (incluye los intentos con error del proveedor) y 617 s en la continuación |
| `gd_n1`, `gd_const_n2`, `gd_const_textbook`, `gd_const_dt` (24 sep) | Luna | teorema de stepsize, 3 episodios × 4 intentos cada uno | 48 | 0 | gd_n1 con el analizador viejo (4 INVALID_PROPOSAL espurios) |
| stepsize en Isabelle con Astra | Astra | aprobado el 23 sep | — | — | **planeado, no corrido** |

**Tácticas de Lean.** Contadas una vez por intento y método en los registros crudos de esas corridas, coinciden
exactamente con PLAN §2.6: `nlinarith` 6, `ring` 3, `field_simp` 3, `omega` 1 y `positivity` 1. De esas 14
apariciones, 13 son de Luna y 1 de Astra (`field_simp`). Hay además 10 nombres de hecho inexistentes distintos (p. ej. `sq_nonneg`, `abs_inner_le_norm`).

### 09 · unified (`unirl`)

**09.a · Jueces del 23–24 sep (antes del RL verbal).** Todas con Luna (esfuerzo alto) y B = 4.

| juez y entorno | registros | estado | métricas |
|---|---|---|---|
| grafo de lemas (V_G), 5 métodos × 20 episodios | `runs/{bisection,fixedpoint,newton,secant,taylor}_graph/20260923-*` | terminado | 20 de 20 aceptados en los cinco. Aceptación en el 1.er intento en todos los episodios, salvo 3 de secante y 4 de Taylor (2.º intento). |
| V_I, V_P y stepsize | ver 06 y 08 | terminado | ver arriba |
| archivadas | `runs/_*` (cada una con su `LEEME.md`) | terminado, **excluido** | Excluidas por decisión (gpt-5.4-mini: solo Luna) o descartadas por defecto del protocolo (refutaciones visibles, colisión del delimitador `>>>`, mismo segundo, pilotos) |

La nota técnica v0.2 (`docs/nota/unirl_definicion.pdf`, 23 sep 20:49) y los informes por corrida (`docs/informes/*`)
son documentos derivados; su fuente son los `attempts.jsonl`.

**09.b · Etapas del plan (`PLAN_rl_verbal.md`).**

| etapa | contenido | estado | evidencia |
|---|---|---|---|
| 0 | plan | terminado: aprobado el 24 sep con los ajustes de §8 | PLAN §1–9 |
| 1 | corpus de búsqueda de raíces | terminado: 48 peldaños aprobados | `corpus/raices/` (ver 09.c) |
| 2 | juez robusto, aislamiento y libro de gastos | terminado | PLAN §10; `corpus/raices/validacion_exportacion.json` |
| 3 | martillo, consulta y errores sembrados | terminado. **Línea base A: 1 de 48** (train 1/32, test 0/16): `pf_3_unicidad`, con una `smt` opaca de 7 hechos. Media de 76,0 s por peldaño (65,9–99,0 s). | PLAN §11; `resultados/martillo_linea_base.{json,csv,md}` (24 sep 16:54) |
| 4 | recompensa r_V y admisión al cuaderno | terminado | PLAN §13 |
| 5–6 | episodio con reflexión y cuaderno | código terminado. Humo: `orden_1_lineal`, ACCEPTED en el intento 4, $0,0038. | PLAN §14; `runs/rl_verbal/humo/20260925-072357-gpt-6-luna/` |
| 7 | experimentos | **interrumpida por error** (las 4 corridas largas); relanzamiento preparado | ver 09.f |

**09.c · Corpus de búsqueda de raíces** (`corpus/raices/*.json`, 48 archivos). Todos en estado `aprobado`, redactados
por Claude el 24 sep y aprobados por Carlos Manuel Orrego Franco el 24 sep (campo `aprobacion` de cada JSON y
`revision_enunciados.md`). 37 clásicos y 11 debilitados.

| método | split | dif. 1 | dif. 2 | dif. 3 | dif. 4 | dif. 5 | total |
|---|---|---|---|---|---|---|---|
| bisección | train | 1 | 3 | 3 | 1 | 0 | 8 |
| punto fijo | train | 1 | 5 | 5 | 1 | 0 | 12 |
| órdenes | train | 1 | 2 | 0 | 0 | 0 | 3 |
| Newton | train | 0 | 2 | 2 | 4 | 1 | 9 |
| **train** | | 3 | 12 | 10 | 6 | 1 | **32** |
| regula falsi | test | 0 | 2 | 3 | 0 | 2 | 7 |
| secante | test | 0 | 3 | 0 | 3 | 3 | 9 |
| **test** | | 0 | 5 | 3 | 3 | 5 | **16** |

Comprobaciones por peldaño, todas sin demostrar la conclusión:

1. **Isabelle**: el preludio compila, el enunciado tipa y una `interpretation` con valores concretos demuestra que las
   hipótesis se pueden cumplir. Pasa en 6 de 6 teorías de método, que cubren los 48 peldaños
   (`validacion_isabelle.json`).
2. **Numérica**: la conclusión se cumple en todos los casos aleatorios en 48 de 48. Hay 400 casos por peldaño salvo en
   `rf_6c` (392), `rf_1` (148), `newton_6c` (20) y `secante_6c` (17). En 3 peldaños (`pf_1`, `pf_3` y `pf_8`) la nota de
   revisión marca la comprobación como débil.
3. **Exportación**: el teorema se exporta al contexto global y un `sorry` se detecta como `skip_proof` en 48 de 48
   (`validacion_exportacion.json`).
4. **Aprobación humana**: 48 de 48.

Seis peldaños de train tienen una prueba de referencia privada, que nunca se muestra al proponente: `bis_4`, `bis_5`,
`pf_1`, `pf_2`, `pf_4` y `pf_9`.

**09.d · Pruebas automáticas.**

| conjunto | registros | estado | resultado |
|---|---|---|---|
| rápidas (sin Isabelle) | `09_unified/resultados/pruebas_rapidas.xml` (24 sep 16:54) | terminado | 148 pruebas, 0 fallos, 3,7 s |
| con Isabelle | `09_unified/resultados/pruebas_isabelle.xml` (24 sep 16:54) | terminado | 17 pruebas, 0 fallos, 440 s |
| Etapas 5–6 («160 rápidas», PLAN §14) | **ninguno** | — | **No medido**: no hay salida guardada (§4) |
| CI | — | — | 08 y 09 no están en el CI (no están versionados) |

**09.e · Libro de gastos** (`09_unified/logs/gasto.json`; tope $25, ampliable a $28 si Sol lo requiere, PLAN §9.5).
Empieza el 25 sep a las 07:24. Las corridas anteriores (06 y 09 del 23–24 sep, con Luna y Astra) **no registraron
tokens**: su costo no está medido.

| corrida (25 sep) | modelo | llamadas | $ | de ellos, en episodios que no llegaron a cerrarse |
|---|---|---|---|---|
| humo | Luna | 4 | 0,003848 | 0 |
| cuaderno | Luna | 28 | 0,088981 | 0,002782 (la destilación, guardada a medias) |
| evaluación B0/B/C | Luna | 230 | 0,740976 | 0,335765 |
| pareada C3 | Luna | 44 | 0,163994 | 0,063871 |
| medición de Sol | Sol | 3 | 0,208352 | 0 (medición prevista) |
| pareada C3 | Sol | 45 | 2,952131 | 1,273691 |
| **total** | | **354** | **4,158282** | **1,676109** |

Queda $20,841718 del tope de $25. Costo medio por llamada según el libro: Luna $0,00326 (306 llamadas), Sol $0,06584
(48 llamadas). Las 3 llamadas de medición de Sol costaron en promedio $0,0695, menos que los $0,12 que según PLAN §9.4
habrían obligado a recortar la evaluación de Luna.

**09.f · Corridas de la Etapa 7** (`09_unified/runs/rl_verbal/`, logs en `09_unified/logs/`). Código `unirl`
`5ef59e25793670fb` en todas, salvo el humo (`32799044dbcbbb01`).

| corrida | modelo | config. | plan | registrados | estado | inicio → último registro |
|---|---|---|---|---|---|---|
| humo `20260925-072357` | Luna | C | 1 episodio | 1 | terminado | 07:23 → 07:25 |
| medición `20260925-073231` | Sol | — | 3 llamadas | 3 | terminado | 07:32 → 07:39 |
| cuaderno `20260925-073216` | Luna | F (train) | 32 episodios | 6 (19 %) | **interrumpida por error** (`KeyError`) | 07:32 → 08:34 |
| evaluación `20260925-073228` | Luna | B0, B, C (test, 2 ep.) | 96 | 49 (51 %): B0 14, B 21, C 14 | **interrumpida por error** (SQLite) | 07:32 → 09:27 |
| pareada `20260925-073939` | Luna | C3 (test, 1 ep.) | 16 | 7 (44 %) | **interrumpida por error** (SQLite) | 07:39 → 08:31 |
| pareada `20260925-073936` | Sol | C3 (test, 1 ep.) | 16 | 9 (56 %) | **interrumpida por error** (SQLite) | 07:39 → 08:50 |
| A con cuaderno (martillo solo) | — | A | 16 | — | planeado (necesita el cuaderno congelado) | — |
| evaluación E | Luna | E (2 ep.) | 32 | — | planeado (necesita el cuaderno) | — |
| pareadas E3 | Luna y Sol | E3 | 16 + 16 | — | planeado (necesita el cuaderno) | — |
| D y F en evaluación, transferencia con Astra | — | — | — | — | planeado, fuera de la primera ronda (Astra aplazada) | — |

Aceptados entre los episodios **registrados**: B0 0 de 14, B 3 de 21, C 8 de 14, C3 de Luna 2 de 7, C3 de Sol 4 de 9 y
cuaderno 1 de 6. Por la pérdida no aleatoria, **no son tasas y no deben citarse como tales**. Métricas registradas por
llamada: tokens (entrada, caché, salida y razonamiento), dólares, segundos de modelo, juez y martillo, espera del
candado, carga, suspensión, etiqueta, r_V, legibilidad (pasos, invocaciones, opacas y comentarios) e intento del éxito.

---

## 3. Problemas encontrados (material para la sección 7 del informe)

| problema | evidencia | estado |
|---|---|---|
| El caché SQLite del martillo se usa desde hilos trabajadores y los errores quedan ocultos | trazas al final de `logs/eval_luna_B0_B_C.log`, `pareada_luna_C3.log` y `pareada_sol_C3.log`; 63 episodios perdidos | **sin corregir** |
| La destilación produce errores sin `en_su_lugar` y `errores.md` no se regenera | traza en `logs/cuaderno_luna.log` | **sin corregir**; el cuaderno quedó a medio escribir |
| La solución se cuela por la memoria entre episodios en el PEP (el 15/15 son 5 descubrimientos) | `runs/pep_*astra*/attempts.jsonl` (sucesiones `h`) | corregido en el recuento y en el diseño |
| Los modelos escriben tácticas de Lean en Isabelle (14 intentos) | `runs/bisection_isabelle_lemas_mem/*`, `runs/gd_*` | mitigado: glosario Lean→Isabelle de 25 entradas comprobado en Isabelle. Su efecto (B0 frente a B) **no está medido**: solo hay datos parciales. |
| Recompensa por fracción de pasos | PLAN §1 punto 4, §12–13 | Decisión de diseño: es solo métrica y r_V = 0 en 4 casos. **No hay ningún caso de trampa observado registrado**, y ninguna corrida usó crédito parcial (57 `meta.json` con `shaped = false`). |
| La cola siguió lanzando corridas sin créditos (24 sep 04:44) | `logs/cola_noche.log`; `runs/_descartado_sin_creditos/LEEME.md` | corregido: aborto ante `insufficient_quota`, libro de gastos y tope en dólares |
| El Mac se suspendió y Sledgehammer dio timeouts falsos en 4 peldaños | PLAN §11 | corregido: `Reloj` compara pared y monótono, y las corridas van con `caffeinate -i` |
| El analizador trató `LEMMAS: <<<>>` como lemas (gd_n1, 4 intentos) | `runs/gd_n1/*/LEEME.md` | corregido el 24 sep 06:50 |
| El delimitador `>>>` colisiona con símbolos de Isabelle; hubo refutaciones visibles en 7 distractores | `runs/_descartado_*/LEEME.md` | corregido y repetido |
| El programa de V_P podía falsear CERTIFIED por introspección | README de 09, nota técnica | corregido: intérprete aparte y sandbox |
| 06: generaciones cortadas por longitud (11 de 17) y sobreajuste al horizonte | `docs/ejecucion-01-gpt-6-astra.md` | corregido: 64k y dos horizontes |
| CI en rojo desde el 17 sep | run 35779899804, job 06 | **sin corregir** (pruebas del 06 con la referencia vieja) |

## 4. Inconsistencias entre registros (no elegí ninguna en silencio)

| # | qué | un registro dice | otro dice | lectura |
|---|---|---|---|---|
| 1 | llamadas de la Etapa 7 | `logs/gasto.json`: 230 / 44 / 45 llamadas | `llamadas.jsonl`: 183 / 35 / 38 | Explicado: falta exactamente la llamada que mató a cada episodio (47, 9 y 7 episodios caídos). Emparejando por tokens y dólares no sobra ninguna fila. **El libro es la fuente completa del costo.** |
| 2 | estado del cuaderno | `cuaderno/errores.json` (08:34:07): 30 errores | `cuaderno/errores.md` (08:33:02): 25 | El `.md` no incluye los 5 aprendidos (A026–A030) porque su generación falló. |
| 3 | pruebas de las Etapas 5–6 | PLAN §14: «160 rápidas» | único XML guardado (24 sep 16:54): 148 rápidas y 17 con Isabelle | Del «160» no hay salida registrada. |
| 4 | hechos de la `smt` del variante (08) | `08_isabelle/docs/reproduccion-bisection.md`: «19 lemas» | `given_smt_08.json` y la línea misma: 18 hechos | Error de la nota: son 18. |
| 5 | τ certificado con n = 6 (06) | README: τ = 0,020049 (búsqueda; «0,25 % bajo la tabla») | `certificados/fval_mu0_n6.json` (commit `4e447f1`): 0,019665446; `runs/cert-fval_mu0_n6.json`: 0,019885665 | Son sucesiones de pasos distintas y el último certificado es el vigente (2,2 % bajo el 0,0201 tabulado). **El README está desactualizado** («celda por corregir», según el commit). La discrepancia con la tabla publicada no está resuelta. |
| 6 | calibración de 01 | `CLAUDE.md`: semilla 1, λ = ½ ~345, etc. | `runs/` de 01: solo semillas 0 y 42 | Sin archivo de origen. |
| 7 | cifras de 07 (y de 04/05) | README: semilla 1, tabla de Λ | no hay `runs/` | Sin archivo de origen. |
| 8 | exponente por duplicación de `evolve` 01 (06) | la nota: 1,047 (gen. 2), etc. | `evolucion.json` de esa corrida: solo la métrica vieja | Recalculado a posteriori; solo existe en la nota. |
| 9 | commit de las corridas de 09 | `meta.json`: `git_commit dcb8f7b` | `09_unified/` no está versionado | El commit no fija el código; lo fija la huella `unirl_sha256`. |
| 10 | gasto en `logs/cuaderno_luna.log` | «gasto $0.972» en el ep. 2 | la corrida gastó $0,089 en total | El log muestra el total global del libro, que suma todas las corridas paralelas; no es el gasto del cuaderno. |

## 5. Pendientes y costo estimado (nada se ha lanzado)

Las estimaciones son cotas superiores: llamadas máximas multiplicadas por el costo medio medido por llamada (Luna
$0,00326 y Sol $0,06584, según el libro). No son resultados.

| # | pendiente | API | cota de costo | tiempo (medido en las parciales) |
|---|---|---|---|---|
| 0 | corregir los 2 errores (caché por hilo o conexión con candado; capturar toda excepción por episodio; `render_errores` tolerante y regenerar `errores.md`), con una prueba que ejercite el martillo desde hilos | no | $0 | — |
| 1 | reconstruir el cuaderno (Luna, F, 32 peldaños de train; tope de 236 llamadas) | sí | ≤ $0,77 | ≈ 10 min por episodio, unas 5–6 h en serie |
| 2 | congelar el cuaderno y calcular la línea base A con él (martillo, 16 peldaños de test) | no | $0 | ≈ 20 min en serie |
| 3 | evaluación B0/B/C de Luna, 2 episodios: completa (≤ 320 llamadas), o solo los 47 perdidos (≤ 159) | sí | completa ≤ $1,04; solo perdidos ≤ $0,52 | la parcial duró 1 h 55 min con 3 en paralelo |
| 4 | evaluación E de Luna, 2 episodios (≤ 192 llamadas) | sí | ≤ $0,63 | ≈ 1 h |
| 5 | pareadas de Luna: C3 completa (≤ 64 llamadas) o solo 9 perdidos (≤ 36), más E3 (≤ 64) | sí | ≤ $0,42 (o ≤ $0,33) | ≈ 50 min por configuración (la C3 parcial duró 52 min) |
| 6 | pareadas de Sol: C3 completa (≤ 64) o solo 7 perdidos (≤ 28), más E3 (≤ 64) | sí | ≤ $8,43 (o ≤ $6,06) | ≈ 70 min por configuración (la C3 parcial duró 71 min) |
| | **total de la primera ronda** | | **≤ $11,29 repitiendo todo**; ≤ $8,30 solo con los perdidos | |

Mi recomendación: repetir completas las tres corridas de evaluación después de corregir, en lugar de rellenar solo los
episodios perdidos. Así cada tabla sale de una sola versión del código y de una sola sesión, y la diferencia es de unos
$3, dentro de los $20,84 que quedan. Con el máximo observado por llamada de Sol ($0,1783), el peor caso de la fila 6
pasaría de $22. El tope global del libro lo impide, pero conviene saberlo.

**Sin costo de API**, útiles para llenar celdas «no medido» si lo autorizas en la Etapa 1:

* 04, 05 y 07 con `--no-tui --seed 0` y la configuración por defecto (≈ 0,35 s, 0,35 s y 15 s), y `interprl search`
  con n = 4, 8 y 12 (≈ 8 s);
* 01 con `--seed 1`, para respaldar o corregir la calibración de `CLAUDE.md` (≈ 0,35 s);
* pytest de 01–07 en local, y las pruebas rápidas de 09 **en una copia** de `09_unified/`, para no tocar el cuaderno
  real;
* guardar como fuente los logs del CI del run 35779899804 (humo de 01–07).

Todo con `--out resultados/corridas_locales/`, sin escribir en los `runs/` de los paquetes.

## 6. Lo que necesito de ti para seguir

1. **`formulacion_rl_verbal.tex`.** Necesito el enunciado de H1–H4 (en particular, qué es exactamente H1, «margen»),
   qué pruebas admite la formulación, y su estilo: ¿XeLaTeX con Avenir Next, como `docs/curso/tex`, o pdfLaTeX, como
   `plantilla_v0.1.tex`? ¿Qué colores?
2. **Etiqueta de las corridas detenidas.** Propongo «parcial (detenida por error)» dentro de tu estado «en curso»,
   diciendo explícitamente que nada se está ejecutando. ¿O prefieres un cuarto estado, «interrumpida»?
3. **Datos parciales de la Etapa 7 en el informe.** Recomiendo mostrarlos solo en la sección de problemas, como conteos
   y sin intervalos ni pruebas, porque la pérdida no es aleatoria. ¿De acuerdo?
4. **Corridas sin costo de API** (lista del §5): ¿las corro en la Etapa 1 para llenar las celdas «no medido», o las dejo
   así?
5. **Fuera del informe:** ¿preparo la corrección de los dos errores y los comandos de relanzamiento (sin lanzar nada;
   tú los corres en tu terminal), o esperamos a terminar el informe?

Fuera de alcance: `Conjeturas/` y `Convocatoria-XVIII-PREMIO-GUILR-2026_signed-1.pdf`, en la raíz y sin versionar, no
son experimentos de `rl_metodos`.

---

## Apéndice A · Huellas SHA-256 de las fuentes (primeros 16 dígitos, 25 sep 2026)

| huella | archivo |
|---|---|
| `936d47504c65b94d` | `09_unified/logs/gasto.json` |
| `c272c3c00656fad5` | `09_unified/runs/rl_verbal/evaluacion/20260925-073228-gpt-6-luna/episodios.jsonl` |
| `ee19fa93f3af662a` | `…/evaluacion/20260925-073228-gpt-6-luna/llamadas.jsonl` |
| `b55d6176cde3ff7e` | `…/pareada_luna/20260925-073939-gpt-6-luna/episodios.jsonl` |
| `41e2c709d520f62d` | `…/pareada_luna/20260925-073939-gpt-6-luna/llamadas.jsonl` |
| `08d67fc16cb59d04` | `…/pareada_sol/20260925-073936-gpt-6-sol/episodios.jsonl` |
| `4947274b1471e82d` | `…/pareada_sol/20260925-073936-gpt-6-sol/llamadas.jsonl` |
| `69dcefc6ba59d7be` | `…/cuaderno/20260925-073216-gpt-6-luna/episodios.jsonl` (igual a `09_unified/cuaderno/episodios.jsonl`) |
| `460f0c565ac65045` | `…/cuaderno/20260925-073216-gpt-6-luna/llamadas.jsonl` |
| `11627f013e2edd8c` | `…/humo/20260925-072357-gpt-6-luna/episodios.jsonl` |
| `14b17471d9c9593e` | `…/medicion_sol/20260925-073231-gpt-6-sol/llamadas.jsonl` |
| `beec50e600bc6344` | `09_unified/cuaderno/errores.json` |
| `fcb6f02b94e9048a` | `09_unified/cuaderno/errores.md` |
| `eab5db5af508f6eb` | `09_unified/cuaderno/estrategias.json` |
| `ae09166cf0c64662` | `09_unified/cuaderno/lemas.json` |
| `404f799d93412d5f` | `09_unified/resultados/martillo_linea_base.json` |
| `3248517588c65b6d` | `09_unified/resultados/pruebas_rapidas.xml` |
| `33a8103e90568603` | `09_unified/resultados/pruebas_isabelle.xml` |
| `6d6acaa6dcbdef36` | `09_unified/corpus/raices/validacion_isabelle.json` |
| `5f282e47aad7f548` | `09_unified/corpus/raices/validacion_exportacion.json` |
| `ccccd389060011f7` | `09_unified/corpus/raices/revision_enunciados.md` |
| `c4be51692f85e60c` | `09_unified/PLAN_rl_verbal.md` |
| `1d6a82dda914114a` | `09_unified/runs/_baseline/given_smt_08.json` |
| `ea9f97306cc71ec7` | `09_unified/runs/_baseline/sh_goals.json` |
| `cb56cc9e2e7018a7` | `09_unified/runs/_baseline/upper_bound.json` |
| `efbdd2e623e4feab` | `08_isabelle/runs/repro_bisection.json` |
| `eb1d9fa582235636` | `08_isabelle/runs/repro_vc4_240s.json` |
| `26138f90573a989f` | `06_stepsizes/certificados/fval_mu0_n6.json` |
| `03ed991dc37fb2c8` | `06_stepsizes/runs/cert-fval_mu0_n6.json` |
| `405da8162e7ef5d4` | `06_stepsizes/steprl/refs.json` |

En la Etapa 1 se amplía a todos los archivos que usen las tablas, incluidos los `historia.json` de 01–03 y los
`attempts.jsonl` de 09.
