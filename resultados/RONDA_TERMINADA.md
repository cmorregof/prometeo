# Ronda 20260926-2016: TERMINADA

Inicio 2026-09-26T20:17:27; informe 2026-09-27T11:38:45. Libro de la ronda: `logs/gasto_ronda_20260926-2016.json` (total $10.7793 de $15.00).

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
| evaluacion_E | gpt-6-luna | E | 32 | 4 | 0.12 | 4/32 | 2 |
| pareada_luna | gpt-6-luna | E3 | 16 | 2 | 0.12 | 2/16 | 2 |
| pareada_sol | gpt-6-sol | E3 | 16 | 4 | 0.25 | 4/16 | 2 |

Un episodio es válido si alguno de sus intentos no fue PROVIDER_ERROR; si un episodio se repitió al reanudar, cuenta el primero válido.

## McNemar (pareado por peldaño y episodio; H2)

| comparación | pares | b (E gana) | b' (C gana) | p exacto bilateral |
|---|---|---|---|---|
| Luna: C frente a E (2 episodios) | 32 | 0 | 2 | 0.5 |
| Luna: C3 frente a E3 | 16 | 0 | 2 | 0.5 |
| Sol: C3 frente a E3 | 16 | 1 | 1 | 1.0 |

Sobre T*_test (peldaños que el martillo con cuaderno no cierra) cuando hay línea base; si no, sobre todos.

### Añadido el 30 sep 2026: C frente a B0 y frente a B (exploratorio, no es H2)

Recalculado el 30 sep 2026 desde los `episodios.jsonl` de las corridas de esta ronda (inicio entre 2026-09-26T20:17:27 y 2026-09-27T14:03:07), sin correr nada y con la misma regla: cuenta el primer episodio válido. H2 prerregistrada es E frente a C (`docs/formulacion/formulacion_rl_verbal.tex`, líneas 205 y 222); estas comparaciones son exploratorias. C difiere de B en la reflexión y además en los intentos (4 frente a 1); de B0, también en el glosario y las consultas (`unirl/reflexion.py` en `a5f6c14`, líneas 52–54).

| comparación | unidad | pares | gana C | gana el otro | p exacto bilateral |
|---|---|---|---|---|---|
| Luna: C frente a B0 | peldaño y episodio (2 por peldaño) | 32 | 6 | 0 | 0.0312 |
| Luna: C frente a B0 | peldaño (cerrado si algún episodio lo cerró) | 16 | 3 | 0 | 0.25 |
| Luna: C frente a B | peldaño y episodio (2 por peldaño) | 32 | 3 | 1 | 0.625 |
| Luna: C frente a B | peldaño (cerrado si algún episodio lo cerró) | 16 | 1 | 1 | 1.0 |

## Por peldaño (1 = aceptado, 0 = no, · = sin episodio; dos episodios se muestran como «xy»)

| peldaño | dif. | en T* | B0 (eval) | B (eval) | C (eval) | E (E) | C3 (luna) | E3 (luna) | C3 (sol) | E3 (sol) |
|---|---|---|---|---|---|---|---|---|---|---|
| rf_1_punto | 2 | sí | 00 | 11 | 11 | 11 | 1 | 1 | 1 | 1 |
| rf_2_signo | 2 | sí | 00 | 00 | 11 | 11 | 1 | 1 | 1 | 1 |
| rf_3_encaje | 3 | sí | 00 | 00 | 00 | 00 | 0 | 0 | 0 | 1 |
| rf_4_raiz | 3 | sí | 00 | 01 | 00 | 00 | 0 | 0 | 1 | 1 |
| rf_5_limites | 3 | sí | 00 | 00 | 00 | 00 | 0 | 0 | 0 | 0 |
| rf_6_convergencia | 5 | sí | 00 | 00 | 00 | 00 | 0 | 0 | 0 | 0 |
| rf_6c_puntos_convergen | 5 | sí | 00 | 00 | 00 | 00 | 0 | 0 | 0 | 0 |
| secante_1_inyectiva | 2 | sí | 00 | 00 | 00 | 00 | 1 | 0 | 1 | 0 |
| secante_2_cociente | 2 | sí | 00 | 01 | 11 | 00 | 1 | 0 | 0 | 0 |
| secante_3_producto | 5 | sí | 00 | 00 | 00 | 00 | 0 | 0 | 0 | 0 |
| secante_4_contraccion | 2 | sí | 00 | 00 | 00 | 00 | 0 | 0 | 0 | 0 |
| secante_4c_contraccion_local | 4 | sí | 00 | 00 | 00 | 00 | 0 | 0 | 0 | 0 |
| secante_5_convergencia | 4 | sí | 00 | 00 | 00 | 00 | 0 | 0 | 0 | 0 |
| secante_5c_convergencia_local | 5 | sí | 00 | 00 | 00 | 00 | 0 | 0 | 0 | 0 |
| secante_6_fibonacci | 4 | sí | 00 | 00 | 00 | 00 | 0 | 0 | 0 | 0 |
| secante_6c_orden_phi | 5 | sí | 00 | 00 | 00 | 00 | 0 | 0 | 0 | 0 |

## Gasto de la ronda por fase

| fase | llamadas | $ |
|---|---|---|
| cuaderno | 150 | 0.5485 |
| evaluacion | 280 | 0.9999 |
| evaluacion_E | 180 | 0.6106 |
| pareada_luna | 126 | 0.5065 |
| pareada_sol | 121 | 8.1138 |
| preflight | 2 | 0.0000 |
| **total** | 859 | **10.7793** |
