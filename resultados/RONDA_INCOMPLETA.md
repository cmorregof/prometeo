# Ronda 20260926-2016: INCOMPLETA

Inicio 2026-09-26T20:17:27; informe 2026-09-27T09:03:30. Libro de la ronda: `logs/gasto_ronda_20260926-2016.json` (total $7.5432 de $15.00).

## Dónde quedó y por qué

2026-09-27 09:03:07  fase 08_pareada_sol_E3: 2026-09-27T09:02:25: tope de la fase 'pareada_sol' ($6.00): gastado $5.3595, la llamada siguiente puede costar hasta $0.6546

Para continuar: volver a lanzar `unirl/tools/lanzar_ronda.sh`; salta las fases hechas y relanza los peldaños que faltan.

## Cuaderno

Corrida `20260926-201727-gpt-6-luna`: 32 episodios de train registrados, 10 aceptados; congelado con hash `fbd88bf0474ad117` (lemas `2b6d69992bce9f0d`).

## H1: margen del martillo con el cuaderno congelado

Línea base A con el cuaderno (`martillo_linea_base_2b6d69992bce9f0d.json`): el martillo deja sin cerrar **16 de 16** peldaños de test. Criterio prerregistrado |T*_test| ≥ 12: **se cumple**.

## Episodios válidos por fase y configuración

| fase | modelo | config | episodios | aceptados | tasa | sobre T* | corridas |
|---|---|---|---|---|---|---|---|
| cuaderno | gpt-6-luna | F | 32 | 10 | 0.31 | 0/0 | 1 |
| evaluacion | gpt-6-luna | B0 | 32 | 0 | 0.00 | 0/32 | 2 |
| evaluacion | gpt-6-luna | B | 32 | 4 | 0.12 | 4/32 | 2 |
| evaluacion | gpt-6-luna | C | 32 | 6 | 0.19 | 6/32 | 2 |
| pareada_luna | gpt-6-luna | C3 | 16 | 4 | 0.25 | 4/16 | 2 |
| pareada_sol | gpt-6-sol | C3 | 16 | 4 | 0.25 | 4/16 | 2 |
| evaluacion_E | gpt-6-luna | E | 10 | 4 | 0.40 | 4/10 | 1 |
| pareada_luna | gpt-6-luna | E3 | 8 | 2 | 0.25 | 2/8 | 1 |
| pareada_sol | gpt-6-sol | E3 | 7 | 4 | 0.57 | 4/7 | 1 |

Un episodio es válido si alguno de sus intentos no fue PROVIDER_ERROR; si un episodio se repitió al reanudar, cuenta el primero válido.

## McNemar (pareado por peldaño y episodio; H2)

| comparación | pares | b (E gana) | b' (C gana) | p exacto bilateral |
|---|---|---|---|---|
| Luna: C frente a E (2 episodios) | 10 | 0 | 0 | — |
| Luna: C3 frente a E3 | 8 | 0 | 1 | 1.0 |
| Sol: C3 frente a E3 | 7 | 1 | 1 | 1.0 |

Sobre T*_test (peldaños que el martillo con cuaderno no cierra) cuando hay línea base; si no, sobre todos.

## Por peldaño (1 = aceptado, 0 = no, · = sin episodio; dos episodios se muestran como «xy»)

| peldaño | dif. | en T* | B0 (eval) | B (eval) | C (eval) | E (E) | C3 (luna) | E3 (luna) | C3 (sol) | E3 (sol) |
|---|---|---|---|---|---|---|---|---|---|---|
| rf_1_punto | 2 | sí | 00 | 11 | 11 | 11 | 1 | 1 | 1 | 1 |
| rf_2_signo | 2 | sí | 00 | 00 | 11 | 11 | 1 | 1 | 1 | 1 |
| rf_3_encaje | 3 | sí | 00 | 00 | 00 | 00 | 0 | 0 | 0 | 1 |
| rf_4_raiz | 3 | sí | 00 | 01 | 00 | 00 | 0 | 0 | 1 | 1 |
| rf_5_limites | 3 | sí | 00 | 00 | 00 | 00 | 0 | 0 | 0 | 0 |
| rf_6_convergencia | 5 | sí | 00 | 00 | 00 | ·· | 0 | 0 | 0 | 0 |
| rf_6c_puntos_convergen | 5 | sí | 00 | 00 | 00 | ·· | 0 | 0 | 0 | · |
| secante_1_inyectiva | 2 | sí | 00 | 00 | 00 | ·· | 1 | 0 | 1 | 0 |
| secante_2_cociente | 2 | sí | 00 | 01 | 11 | ·· | 1 | · | 0 | · |
| secante_3_producto | 5 | sí | 00 | 00 | 00 | ·· | 0 | · | 0 | · |
| secante_4_contraccion | 2 | sí | 00 | 00 | 00 | ·· | 0 | · | 0 | · |
| secante_4c_contraccion_local | 4 | sí | 00 | 00 | 00 | ·· | 0 | · | 0 | · |
| secante_5_convergencia | 4 | sí | 00 | 00 | 00 | ·· | 0 | · | 0 | · |
| secante_5c_convergencia_local | 5 | sí | 00 | 00 | 00 | ·· | 0 | · | 0 | · |
| secante_6_fibonacci | 4 | sí | 00 | 00 | 00 | ·· | 0 | · | 0 | · |
| secante_6c_orden_phi | 5 | sí | 00 | 00 | 00 | ·· | 0 | · | 0 | · |

## Gasto de la ronda por fase

| fase | llamadas | $ |
|---|---|---|
| cuaderno | 150 | 0.5485 |
| evaluacion | 280 | 0.9999 |
| evaluacion_E | 49 | 0.1930 |
| pareada_luna | 94 | 0.3862 |
| pareada_sol | 85 | 5.4156 |
| preflight | 1 | 0.0000 |
| **total** | 659 | **7.5432** |
