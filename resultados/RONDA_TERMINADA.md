# Ronda 20261008-2003: TERMINADA

Inicio 2026-10-08T20:05:58; informe 2026-10-14T00:38:34. Libro de la ronda: `logs/gasto_ronda_20261008-2003.json` (total $4.3269 de $15.00).

## Cuaderno

Corrida `20261008-200559-gpt-6-luna`: 96 episodios de train registrados, 33 aceptados; congelado con hash `835d3070e3b0c3b1` (lemas `2ceab27c97e13a3f`).

## H1: margen del martillo con el cuaderno congelado

Línea base A con el cuaderno (`martillo_linea_base_2ceab27c97e13a3f.json`): el martillo deja sin cerrar **16 de 16** peldaños de test. Criterio prerregistrado |T*_test| ≥ 12, contando solo mediciones válidas: **se cumple**.

## Episodios válidos por fase y configuración

| fase | modelo | config | episodios | aceptados | tasa | sobre T* | sobre T*, dif. ≤ 3 | corridas |
|---|---|---|---|---|---|---|---|---|
| cuaderno | gpt-6-luna | F | 96 | 33 | 0.34 | 0/0 | 0/0 | 1 |
| evaluacion | gpt-6-luna | B0 | 32 | 0 | 0.00 | 0/32 | 0/16 | 3 |
| evaluacion | gpt-6-luna | B | 32 | 0 | 0.00 | 0/32 | 0/16 | 3 |
| evaluacion | gpt-6-luna | C | 32 | 7 | 0.22 | 7/32 | 7/16 | 4 |
| pareada_luna | gpt-6-luna | C3 | 16 | 2 | 0.12 | 2/16 | 2/8 | 2 |
| pareada_sol | gpt-6-sol | C3 | 0 | — | — | — | — | 0 |
| evaluacion_E | gpt-6-luna | E | 32 | 5 | 0.16 | 5/32 | 5/16 | 1 |
| pareada_luna | gpt-6-luna | E3 | 16 | 3 | 0.19 | 3/16 | 3/8 | 1 |
| pareada_sol | gpt-6-sol | E3 | 0 | — | — | — | — | 0 |

Un episodio es válido si alguno de sus intentos no fue PROVIDER_ERROR; si un episodio se repitió al reanudar, cuenta el primero válido.

## McNemar (pareado por peldaño y episodio; H2)

| comparación | conjunto | pares | b (E gana) | b' (C gana) | p exacto bilateral |
|---|---|---|---|---|---|
| Luna: C frente a E (2 episodios) | primario: dificultad ≤ 3 | 16 | 2 | 4 | 0.6875 |
| Luna: C frente a E (2 episodios) | secundario: todo T* | 32 | 2 | 4 | 0.6875 |
| Luna: C frente a E (2 episodios) | secundario: dificultad 4–5 | 16 | 0 | 0 | — |
| Luna: C3 frente a E3 | primario: dificultad ≤ 3 | 8 | 2 | 1 | 1.0 |
| Luna: C3 frente a E3 | secundario: todo T* | 16 | 2 | 1 | 1.0 |
| Luna: C3 frente a E3 | secundario: dificultad 4–5 | 8 | 0 | 0 | — |
| Sol: C3 frente a E3 | primario: dificultad ≤ 3 | 0 | 0 | 0 | — |
| Sol: C3 frente a E3 | secundario: todo T* | 0 | 0 | 0 | — |
| Sol: C3 frente a E3 | secundario: dificultad 4–5 | 0 | 0 | 0 | — |

Sobre T*_test (peldaños que el martillo con cuaderno no cierra) cuando hay línea base; si no, sobre todos. Análisis primario de H2 desde la ronda 2 (prerregistrado el 27 sep 2026): dificultad ≤ 3; secundarios: todo T*_test y dificultad 4–5. En la ronda 1 el primario fue todo T*_test (su RONDA_TERMINADA.md se generó con la versión anterior de este informe).

## Por peldaño (1 = aceptado, 0 = no, · = sin episodio; dos episodios se muestran como «xy»)

| peldaño | dif. | en T* | B0 (eval) | B (eval) | C (eval) | E (E) | C3 (luna) | E3 (luna) | C3 (sol) | E3 (sol) |
|---|---|---|---|---|---|---|---|---|---|---|
| rf_1_punto | 2 | sí | 00 | 00 | 11 | 11 | 1 | 1 | · | · |
| rf_2_signo | 2 | sí | 00 | 00 | 11 | 01 | 0 | 1 | · | · |
| rf_3_encaje | 3 | sí | 00 | 00 | 10 | 00 | 1 | 0 | · | · |
| rf_4_raiz | 3 | sí | 00 | 00 | 00 | 00 | 0 | 0 | · | · |
| rf_5_limites | 3 | sí | 00 | 00 | 00 | 00 | 0 | 0 | · | · |
| rf_6_convergencia | 5 | sí | 00 | 00 | 00 | 00 | 0 | 0 | · | · |
| rf_6c_puntos_convergen | 5 | sí | 00 | 00 | 00 | 00 | 0 | 0 | · | · |
| secante_1_inyectiva | 2 | sí | 00 | 00 | 11 | 00 | 0 | 1 | · | · |
| secante_2_cociente | 2 | sí | 00 | 00 | 00 | 11 | 0 | 0 | · | · |
| secante_3_producto | 5 | sí | 00 | 00 | 00 | 00 | 0 | 0 | · | · |
| secante_4_contraccion | 2 | sí | 00 | 00 | 00 | 00 | 0 | 0 | · | · |
| secante_4c_contraccion_local | 4 | sí | 00 | 00 | 00 | 00 | 0 | 0 | · | · |
| secante_5_convergencia | 4 | sí | 00 | 00 | 00 | 00 | 0 | 0 | · | · |
| secante_5c_convergencia_local | 5 | sí | 00 | 00 | 00 | 00 | 0 | 0 | · | · |
| secante_6_fibonacci | 4 | sí | 00 | 00 | 00 | 00 | 0 | 0 | · | · |
| secante_6c_orden_phi | 5 | sí | 00 | 00 | 00 | 00 | 0 | 0 | · | · |

## Gasto de la ronda por fase

| fase | llamadas | $ |
|---|---|---|
| cuaderno | 447 | 2.1868 |
| evaluacion | 309 | 1.0629 |
| evaluacion_E | 166 | 0.6012 |
| pareada_luna | 120 | 0.4759 |
| preflight | 5 | 0.0000 |
| **total** | 1047 | **4.3269** |
