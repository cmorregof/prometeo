# Port de los modelos infinitos del ETP (familia F5)

Las 30 tareas F5 son pares de Austin: no tienen contramodelo finito. Sus refutaciones usan modelos infinitos del
repositorio `teorth/equational_theories`, commit `1aec8a7` (Apache-2.0), portados de Lean 4.29.1 a Lean 4.34.1 con el
Mathlib v4.34.1 de `corpus_compilar/corpus_lean`. Las fuentes originales están en `../testigos_etp/fuentes_f5/`.

## Estructura

- `PortF5/`: la biblioteca portada. Todo vive en `namespace ETP`, con `ETP.Magma` y notación `scoped`, para no chocar con
  el `Magma` que define el corpus.
- `PortF5/Tareas.lean`: un teorema `ETP.t_<id>` por tarea, en forma plana: `∃ G o, LeyA con o ∧ ¬ LeyB con o`.
- `lean_f5/ETP_<id>.lean`: el contexto del corpus, sin cambiar un carácter, y `refuta_<id>` con su `Magma` y sus `LeyA`
  y `LeyB`. El kernel exige que el testigo sea el de esas leyes.
- `generar_f5.py`: genera `Tareas.lean` y `lean_f5/`. Calcula por unificación los argumentos de cada instancia.
- `construir.sh`: compila `PortF5` en orden hacia `build/`.
- `portar_una_vez.py`: el paso inicial. Ya no se puede volver a correr, porque borraría los arreglos de abajo.

## Las 12 construcciones

| Construcción | Origen en el ETP | Tareas |
|---|---|---:|
| reescritura `rw481` | `Confluence3.lean` | 4 |
| reescritura `rw1276` | `Confluence2.lean` | 1 |
| reescritura `rw1523` | `Confluence2.lean` | 3 |
| reescritura `rw3588` | `Confluence2.lean` | 4 |
| reescritura `rw1443` | `Confluence4.lean` | 2 |
| reescritura `rw1633` | `Confluence4.lean` | 2 |
| voraz `Eq883` | `Generated/Greedy/Eq883.lean` | 3 |
| sobre ℕ, `Equation3994` | `InfModel.lean` | 1 |
| sobre ℕ × Fin 3, `Eq1437` | `ManuallyProved/Equation1437.lean` | 1 |
| sobre ℕ, `op_1659_4315` | `ManuallyProved/Equation1659.lean` | 4 |
| sobre ℕ, `op_1661_1657` | `ManuallyProved/Equation1661.lean` | 4 |
| sobre ℕ, `op_1701_8` | `ManuallyProved/Equation1701.lean` | 1 |

En 15 de las 30 se usa el magma opuesto (`x ◇' y := y ◇ x`).

## Qué cambió frente al original

**Recortes, sin efecto matemático:**

- Se quitaron `@[equational_result]`, los `private` y los teoremas que ninguna tarea usa.
- Las listas de `Facts` quedaron solo con las leyes necesarias.
- `Ecuaciones.lean` define como `abbrev` solo las ecuaciones usadas, con el texto de `Equations/*.lean`.

**Arreglos por el cambio de versión:**

- `rw481` y `rw1523`: en `IsProjOrNF`, el caso de la hoja pasó de un `simp` a `rfl`.
- La táctica `refute`: ya no sintetizaba `Decidable (a ≠ b)` en esos sistemas, así que ahora compara los términos con
  `Subtype.val` y usa `decide +kernel`.
- `Eq883`: se añadió un `show` antes del `simpa` de `toMagma_equation883`.

**Otra forma de cerrar la prueba:**

- En los modelos sobre ℕ, LeyB se refuta con valores explícitos y `decide`, sin pasar por las implicaciones del ETP.
  Los valores salieron de evaluar cada modelo en Python.
- `Eq1437` conserva la operación del original, pero ahora prueba la ley en forma plana (`satisface1437`), y el ¬LeyB se
  demuestra en cada tarea.

## Axiomas

`#print axioms` da `propext`, `Classical.choice` y `Quot.sound` en 25 tareas, y `propext` y `Quot.sound` en 5. No aparecen
`sorry`, `native_decide`, `admit`, `axiom`, `implemented_by`, `ofReduceBool`, `unsafe` ni `skipKernelTC` en `PortF5/` ni
en `lean_f5/`.

## Reproducir

Desde esta carpeta, compila la biblioteca (alrededor de un minuto):

```bash
./construir.sh
```

Compila las 30 (unos 2 minutos en serie):

```bash
python3 generar_f5.py compilar -j 1
```
