# Auditoría de las cifras de los README (25 sep 2026)

Decisión de Carlos: «Donde un README tenga cifras sin registro, reprodúcelas o márcalas para quitarlas». Para cada
cifra: dónde está, qué registro la respalda ahora y qué se midió. Las corridas nuevas están en
`resultados/corridas_locales/` (commit `e419660`, sin API) y sus tiempos, en `corridas_locales/tiempos.md`.

Veredictos: **✓** se reproduce; **≈** se reproduce con matiz; **✗** no se reproduce (proponer el valor medido);
**pendiente**: sin registro, y reproducirla carga la máquina, así que va después de las corridas del RL verbal.
No se editó ningún README: las correcciones esperan tu visto bueno.

| # | dónde | cifra escrita | registro | medido | veredicto |
|---|---|---|---|---|---|
| 1 | `CLAUDE.md:57` | `--no-tui` con 3000 + 3000 tarda 0,35 s en 01–05 | `tiempos.md` | 0,35–0,41 s | ✓ |
| 2 | `CLAUDE.md:57` | ~15 s en 07 | `tiempos.md` | 7,9–8,0 s | ✗: poner ~8 s |
| 3 | `CLAUDE.md:57` | 06 `verify` tarda ~3 s | `tiempos.md` | 2,3 s | ✓ |
| 4 | `CLAUDE.md:59` | semilla 1: λ = ½ en la gen. ~345, Bolzano ~358, demostración ~256, mínima ~459 | `corridas_locales/01_biseccion/20260925-144905/historia.json` | 345, 358, 256 y 459 | ✓ exacto |
| 5 | `CLAUDE.md:61` | con 100 generaciones no aprende nada; con 300, a medias | `corridas_locales/01_biseccion_{100,300}gen/` | 100: 15/100 convergencias, 0 demostraciones; 300: 130/300, 9 completas, 0 mínimas | ✓ |
| 6 | `01_biseccion/README.md:28` | Q(0,5) = 0, Q(0,4) = Q(0,6) ≈ −0,03, Q(0,1) ≈ −0,55 | `corridas_locales/01_biseccion/20260925-145147/informe.md` (y las 8 corridas guardadas con semilla 0) | 0; −0,055 y −0,043; −0,550 | ✗ en 0,4 y 0,6: poner ≈ −0,05 |
| 7 | `02_punto_fijo/README.md:34` | un α fijo converge ~35 % | `corridas_locales/lineas_base_puras.json` | 33,1 % (993/3000) | ≈ |
| 8 | `02_punto_fijo/README.md:34` | el agente, ~90–96 % y ~11 iteraciones | `corridas_locales/02_punto_fijo/20260925-144906/informe.md` | 93 % (100 últimas) y 11,7 | ✓ |
| 9 | `03_taylor/README.md:35` | sumar sin criterio nunca acierta | — | no medido | pendiente (cualitativa; medible con una estrategia «no parar nunca») |
| 10 | `03_taylor/README.md:35` | el agente, ~90–95 % y ~9 términos | `corridas_locales/03_taylor/20260925-144906/informe.md` | 90 % y 9,7 | ≈ |
| 11 | `04_newton/README.md:28` | Newton puro converge ~73 % | `lineas_base_puras.json` | 74,4 % (2231/3000) | ✓ |
| 12 | `04_newton/README.md:36` | el agente, ~93–96 % y ~9 evaluaciones | `corridas_locales/04_newton/20260925-144906/informe.md` | 96 % y 9,2 | ✓ |
| 13 | `04_newton/README.md:32` | orden observado ≈ 2 | ídem | 2,25 | ✓ |
| 14 | `05_secante/README.md:29` | secante pura ~69 %, regula falsi ~63 %, bisección siempre con ~32 evaluaciones | `lineas_base_puras.json` | 67,6 %; 62,9 %; 100 % con 31,7 | ✓ |
| 15 | `05_secante/README.md:33` | orden observado (mediana) ≈ 1,62 | `corridas_locales/05_secante/20260925-144907/informe.md` | 1,60 | ✓ |
| 16 | `05_secante/README.md:37` | el agente, ~100 % y ~10 evaluaciones | ídem | 100 % y 10,2 | ✓ |
| 17 | `06_stepsizes/README.md:18–24` | validación: paso constante exacto; garantía del silver k = 1…4; óptimo n = 1 | `corridas_locales/_log_06_verify.txt`; `steprl/refs.json` | exacto; se cumple k = 1…4; h = 1,5, τ = 0,1250 | ✓ |
| 18 | `06_stepsizes/README.md:22` | coincide con PEPit hasta 10⁻⁶ | `corridas_locales/pytest/06_stepsizes.xml` (`test_matches_pepit_on_random_schedules`) | la prueba pasa | ✓ |
| 19 | `06_stepsizes/README.md:33–40` | tabla de la búsqueda n = 1…8 (τ encontrado) | ninguno: `refs.json` es otra búsqueda, con otros parámetros | no medido | pendiente (CPU de minutos a horas) |
| 20 | `06_stepsizes/README.md:38` | n = 6: τ = 0,020049, «0,25 % bajo la tabla» | `certificados/fval_mu0_n6.json` (commit `4e447f1`) | certificado 0,019665446 (2,2 % bajo 0,0201) | ✗: celda desactualizada, «por corregir» según el propio commit |
| 21 | `06_stepsizes/README.md:90` | SDP n = 8 ≈ 80 ms, n = 12 ≈ 200 ms, n = 24 ≈ 1 s; certificado n = 12 ≈ 1 s | ninguno | no medido | pendiente (`steprl bench`) |
| 22 | `07_interpolacion/README.md:23` | criterio de parada en la gen. ~80; coincide con la teoría en 8 estados | `corridas_locales/07_interpolacion/20260925-144926/historia.json` (semilla 1) | gen. 80; 8 estados (gen. 526) | ✓ |
| 23 | `07_interpolacion/README.md:24` | γ = 1 estable en la gen. 500–800 según semilla; Q(γ=1) ≈ −3 y Q(γ=0) ≈ −12 | ídem y CI (semilla 0) | gen. 726 (semilla 1) y 543 (semilla 0); −2,84 y −13,43 | ≈ (Q(γ=0) final −13,4) |
| 24 | `07_interpolacion/README.md:25` | éxito 80–90 %, con ~19 nodos de media | ídem | 89 % y 17,4 nodos | ≈ en el éxito; ✗ en los nodos: poner ~17 |
| 25 | `07_interpolacion/README.md:27` | Λ equiespaciados n = 16: 934; Chebyshev: 2,7 | ídem (`informe.md`) | 934,534 y 2,725 | ✓ |
| 26 | `07_interpolacion/README.md:38` | semilla 1: demostración completa ~190, mínima ~460 | ídem | 186 y 463 | ✓ |
| 27 | `07_interpolacion/README.md:52–54` | n = 8: Λ = 2,27473107 / 1,94157316 / 1,93872335 | `corridas_locales/07_interpolacion/20260925-144935/busqueda_n8.json`, recalculado con otra malla | 2,27473077 / 1,94157277 / 1,93866819 | ✗ desde la 7.ª cifra (el verificador actual reproduce sus valores a 12 cifras con otra malla) |
| 28 | `07_interpolacion/README.md:61–62` | tabla n = 4 y 8 a 4 cifras | ídem | coinciden | ✓ |
| 29 | `07_interpolacion/README.md:63` | n = 12: Λ encontrado 2,1574 | `…/20260925-144938/busqueda_n12.json` | 2,16267 con la configuración por defecto (semilla 0, 40 iteraciones) | ✗: no se reproduce |
| 30 | `07_interpolacion/README.md:61–63` | tiempos 0,6 / 1,8 / 5,4 s | `tiempos.md` | 0,84 / 2,45 / 6,44 s | ≈ (dependen de la máquina) |
| 31 | `08_isabelle/docs/reproduccion-bisection.md:10–12` | HOL-Analysis 5 min 09 s; ITree_Numeric_VCG 1 min 50 s; Numerical_Methods_Paper 36 s | base de compilación de Isabelle (`~/.isabelle/Isabelle2025/heaps/*/log/*.db`, `session_timing`) | 281,4 s; 98,2 s; 30,0 s | ✗: probablemente miden cosas distintas (tiempo de sesión frente al mensaje «Finished»); citar la base |
| 32 | `08_isabelle/docs/reproduccion-bisection.md:29` | 424 s para las 15 VCs; `vcg` 2,2 s | `08_isabelle/runs/repro_bisection.json` | 423,6 s; 2,151 s | ✓ |
| 33 | `08_isabelle/docs/reproduccion-bisection.md:35` | la `smt` del artículo usa 19 lemas | `09_unified/runs/_baseline/given_smt_08.json` | 18 hechos | ✗: poner 18 |
| 34 | `09_unified/PLAN_rl_verbal.md:565` | 160 pruebas rápidas | `corridas_locales/pytest/09_unified_rapidas.xml` (después de las correcciones) | 168 | ✗: el 160 no tiene registro; hoy son 168 |

Hallazgo de paso: las salidas de 01–05 y 07 se nombran por segundo (`runs/AAAAMMDD-HHMMSS/`), y dos corridas lanzadas en
el mismo segundo escriben en la misma carpeta. Pasó aquí con 01 (la corrida con semilla 1 pisó la de semilla 0, que se
repitió). No se tocó el paquete.
