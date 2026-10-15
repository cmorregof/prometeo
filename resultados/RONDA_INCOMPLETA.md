# Ronda 20261008-2003: INCOMPLETA

Inicio 2026-10-08T20:05:58; informe 2026-10-13T12:50:20. Libro de la ronda: `logs/gasto_ronda_20261008-2003.json` (total $2.5124 de $15.00).

## Dónde quedó y por qué

detenida por señal (Ctrl-C o kill) Tue Oct 13 12:50:19 -05 2026

Para continuar: volver a lanzar `unirl/tools/lanzar_ronda.sh`; salta las fases hechas y relanza los peldaños que faltan.

## Cuaderno

Corrida `20261008-200559-gpt-6-luna`: 57 episodios de train registrados, 21 aceptados; **no congelado**.

## H1: margen del martillo con el cuaderno congelado

No evaluable: no hay cuaderno congelado.

## Episodios válidos por fase y configuración

| fase | modelo | config | episodios | aceptados | tasa | sobre T* | sobre T*, dif. ≤ 3 | corridas |
|---|---|---|---|---|---|---|---|---|
| cuaderno | gpt-6-luna | F | 57 | 21 | 0.37 | — | — | 1 |
| evaluacion | gpt-6-luna | B0 | 32 | 0 | 0.00 | — | — | 3 |
| evaluacion | gpt-6-luna | B | 32 | 0 | 0.00 | — | — | 3 |
| evaluacion | gpt-6-luna | C | 32 | 7 | 0.22 | — | — | 4 |
| pareada_luna | gpt-6-luna | C3 | 16 | 2 | 0.12 | — | — | 2 |
| pareada_sol | gpt-6-sol | C3 | 0 | — | — | — | — | 0 |
| evaluacion_E | gpt-6-luna | E | 0 | — | — | — | — | 0 |
| pareada_luna | gpt-6-luna | E3 | 0 | — | — | — | — | 0 |
| pareada_sol | gpt-6-sol | E3 | 0 | — | — | — | — | 0 |

Un episodio es válido si alguno de sus intentos no fue PROVIDER_ERROR; si un episodio se repitió al reanudar, cuenta el primero válido.

## McNemar (pareado por peldaño y episodio; H2)

| comparación | conjunto | pares | b (E gana) | b' (C gana) | p exacto bilateral |
|---|---|---|---|---|---|
| Luna: C frente a E (2 episodios) | primario: dificultad ≤ 3 | 0 | 0 | 0 | — |
| Luna: C frente a E (2 episodios) | secundario: todo T* | 0 | 0 | 0 | — |
| Luna: C frente a E (2 episodios) | secundario: dificultad 4–5 | 0 | 0 | 0 | — |
| Luna: C3 frente a E3 | primario: dificultad ≤ 3 | 0 | 0 | 0 | — |
| Luna: C3 frente a E3 | secundario: todo T* | 0 | 0 | 0 | — |
| Luna: C3 frente a E3 | secundario: dificultad 4–5 | 0 | 0 | 0 | — |
| Sol: C3 frente a E3 | primario: dificultad ≤ 3 | 0 | 0 | 0 | — |
| Sol: C3 frente a E3 | secundario: todo T* | 0 | 0 | 0 | — |
| Sol: C3 frente a E3 | secundario: dificultad 4–5 | 0 | 0 | 0 | — |

Sobre T*_test (peldaños que el martillo con cuaderno no cierra) cuando hay línea base; si no, sobre todos. Análisis primario de H2 desde la ronda 2 (prerregistrado el 27 sep 2026): dificultad ≤ 3; secundarios: todo T*_test y dificultad 4–5. En la ronda 1 el primario fue todo T*_test (su RONDA_TERMINADA.md se generó con la versión anterior de este informe).

## Por peldaño (1 = aceptado, 0 = no, · = sin episodio; dos episodios se muestran como «xy»)

| peldaño | dif. | en T* | B0 (eval) | B (eval) | C (eval) | E (E) | C3 (luna) | E3 (luna) | C3 (sol) | E3 (sol) |
|---|---|---|---|---|---|---|---|---|---|---|
| rf_1_punto | 2 | — | 00 | 00 | 11 | ·· | 1 | · | · | · |
| rf_2_signo | 2 | — | 00 | 00 | 11 | ·· | 0 | · | · | · |
| rf_3_encaje | 3 | — | 00 | 00 | 10 | ·· | 1 | · | · | · |
| rf_4_raiz | 3 | — | 00 | 00 | 00 | ·· | 0 | · | · | · |
| rf_5_limites | 3 | — | 00 | 00 | 00 | ·· | 0 | · | · | · |
| rf_6_convergencia | 5 | — | 00 | 00 | 00 | ·· | 0 | · | · | · |
| rf_6c_puntos_convergen | 5 | — | 00 | 00 | 00 | ·· | 0 | · | · | · |
| secante_1_inyectiva | 2 | — | 00 | 00 | 11 | ·· | 0 | · | · | · |
| secante_2_cociente | 2 | — | 00 | 00 | 00 | ·· | 0 | · | · | · |
| secante_3_producto | 5 | — | 00 | 00 | 00 | ·· | 0 | · | · | · |
| secante_4_contraccion | 2 | — | 00 | 00 | 00 | ·· | 0 | · | · | · |
| secante_4c_contraccion_local | 4 | — | 00 | 00 | 00 | ·· | 0 | · | · | · |
| secante_5_convergencia | 4 | — | 00 | 00 | 00 | ·· | 0 | · | · | · |
| secante_5c_convergencia_local | 5 | — | 00 | 00 | 00 | ·· | 0 | · | · | · |
| secante_6_fibonacci | 4 | — | 00 | 00 | 00 | ·· | 0 | · | · | · |
| secante_6c_orden_phi | 5 | — | 00 | 00 | 00 | ·· | 0 | · | · | · |

## Gasto de la ronda por fase

| fase | llamadas | $ |
|---|---|---|
| cuaderno | 260 | 1.1882 |
| evaluacion | 309 | 1.0629 |
| pareada_luna | 64 | 0.2612 |
| preflight | 3 | 0.0000 |
| **total** | 636 | **2.5124** |
