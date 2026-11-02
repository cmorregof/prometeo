# Errata: etiqueta de las 200 tareas falsas del ETP (2 nov 2026)

**El corpus congelado no se tocó.** Esta errata va aparte, en `tantalus/refutaciones_etp/`. Ni
`corpus_compilar/FINAL/corpus_compilado.jsonl` ni ningún juez cambiaron. SHA-256 del corpus, igual antes y después de
este trabajo: `14418bfc765a8e4ba7942787e66bc398e583f44d12bd7f8f8f944998ffa53129`.

## Qué estaba guardado

Las 200 tareas con `fuente = "etp"` y `verdad = "falso"` guardan este enunciado, que cambia solo en el nombre:

```lean
theorem etp_<A>_<B> : ¬ ∀ (G : Type) [Magma G], LeyA G → LeyB G := by sorry
```

## Qué es lo correcto

La proposición guardada es **verdadera**: dice que la implicación falla. Lo falso es la implicación positiva:

```lean
∀ (G : Type) [Magma G], LeyA G → LeyB G
```

El par correcto es uno de estos dos: enunciado positivo con `verdad = "falso"`, o enunciado negado con
`verdad = "verdadero"`. El corpus guardó el enunciado negado con la etiqueta del positivo.

## Por qué

El campo `verdad` describe el enunciado guardado en `enunciado_lean`. Las tareas de refutación de π-Base sí lo hacen
bien: guardan la negación con `verdad = "verdadero"`, y sus notas lo explican. El ETP quedó con la etiqueta de la
implicación que refuta el repositorio, no con la de la proposición guardada.

Las pruebas lo confirman. En las 200, `¬ ∀ G, LeyA G → LeyB G` quedó demostrado en Lean y el kernel lo aceptó: 170 con
contramodelo finito y `decide`, y 30 con un modelo infinito del ETP. Ver `resumen.csv`.

## Qué no se debe confundir

- **Cada tarea se distingue por sus definiciones.** El texto `∀ G, LeyA G → LeyB G` es idéntico en las 200; lo que
  cambia son `LeyA` y `LeyB`, que están en `contexto_lean`. Por eso el SHA-256 del enunciado falso se toma sobre
  contexto más enunciado (`enunciados/`). El hash del texto solo daría el mismo valor 200 veces.
- **No todas tienen contramodelo pequeño.** La comprobación previa de 12 tareas (todas de tamaño ≤ 3) no representa a
  las 200, que están repartidas por familia:

  | Familia | Tareas | Contramodelo |
  |---|---:|---|
  | F1 | 35 | tamaño 2 |
  | F2 | 35 | tamaño 3 |
  | F3 | 35 | tamaño 4 |
  | F4 | 35 | tablas de tamaño 5 a 9 |
  | F6 | 30 | tamaño 2 |
  | F5 | 30 | **ninguno finito** |

- **Las 30 F5 son pares de Austin.** Las 30 están en `testigos_etp/Austin_implications.txt` (commit `1aec8a7` del
  ETP): LeyA implica LeyB en todo magma finito, de modo que solo un magma infinito puede refutarlas. Sus refutaciones
  se portaron del ETP a Lean 4.34.1; los detalles están en `infinitos/LEEME_PORT.md`.

## Lo que esta errata no cubre

No se evaluó el efecto de la etiqueta sobre el estudio prerregistrado en OSF ni sobre sus jueces. Corregirla allí sería
un cambio de protocolo y le corresponde decidirlo a Carlos.
