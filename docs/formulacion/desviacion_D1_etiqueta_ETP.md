# Desviación D1 del prerregistro: etiqueta invertida en 200 tareas del ETP

**Registro:** <https://osf.io/w4eru> (SHA-256 del prerregistro `e6a2b5750b1ee1acf6c25bd094ec7c8e206ab02e465e4dd5d6cbd745b8e221fd`).
**Fecha de la desviación:** 2 de noviembre de 2026.
**Decisión:** Carlos Manuel Orrego-Franco.

El prerregistro congelado no se edita. Su §14 dice «Ninguna» porque el defecto no se conocía al congelar.

## Qué pasó

Las 200 tareas del corpus con `fuente = etp` y `verdad = falso` guardan el enunciado
`¬ ∀ (G : Type) [Magma G], LeyA G → LeyB G`. Esa proposición es **verdadera**; lo falso es la implicación sin la negación.
La etiqueta correcta para el enunciado guardado era `verdad = verdadero`. El defecto ya estaba al congelar y se detectó el
2 de noviembre de 2026, después de terminar la fase 1.

Ahora hay prueba de que la etiqueta está mal: el kernel de Lean aceptó el enunciado guardado en las 200. Ver `resumen.csv`
y `ERRATA_etiqueta_ETP.md`.

## Efecto sobre el estudio

**El criterio 1 de §2.2 (`verdad = verdadero`) excluyó las 200 del censo.** Se comprobó sobre los archivos de
`runs/unirl/confirmatorio/v6/`:

| Archivo | Ids de estas 200 que aparecen |
|---|---:|
| `plan.json` | 0 |
| `fase1/intentos.jsonl` | 0 |
| `fase1/construcciones.jsonl` | 0 |
| `fase1/llamadas.jsonl` | 0 |

- **Datos ya recogidos:** ningún episodio de la fase 1 usó estas tareas, así que ningún dato ni veredicto cambia.
- **Familias del ETP en el plan:** solo V1–V6, que no tienen este defecto.
- **Calibración:** `muestra_calibracion` aplica el mismo filtro, así que estas tareas tampoco entraron ahí.
- **Lo que sí cambia es el alcance:** con la etiqueta correcta, las 200 habrían pasado el criterio 1 y el 2. Sus seis
  familias (F1–F6, de 30 a 35 tareas cada una) cumplen el mínimo de 20 del criterio 6. Los criterios 3 a 5 nunca se les
  aplicaron, así que no se sabe cuántas habrían quedado. El censo pudo tener hasta 6 familias y 200 tareas más que las 27
  familias y 905 tareas registradas.

## Qué se hace

1. **Se mantienen sin cambios** el corpus, el censo, `plan.json` (27 familias, 905 tareas) y todos los jueces. Las 200 no
   se añaden al estudio.
2. **Se reporta como límite de alcance:** §2.3 llama a las 27 familias «un censo del corpus aprobado». Al publicar se dirá
   que ese censo dejó fuera estas 200 tareas por el defecto, y que el estudio no tiene ninguna familia de refutaciones del
   ETP.
3. **La corrección de la etiqueta queda fuera del corpus congelado:** va en `ERRATA_etiqueta_ETP.md`. Quien reutilice el
   corpus debe leer la errata.

Corregir la etiqueta y volver a correr el censo habría cambiado el plan después de ver la fase 1. Por eso se declara como
desviación y no se corrige.

## Constancia de lo observado

Al decidir esto ya se conocían los datos de la fase 1 (1.808 episodios y 7.772 llamadas, terminada el 27 de octubre de
2026). En `runs/unirl/confirmatorio/v6/` no hay carpeta de la fase 2, es decir, no consta ninguna corrida de esa fase.
Encontrar el defecto y decidir esto no requirió mirar ningún resultado por condición.
