# Refutaciones en Lean de las falsas del ETP

**Resultado: 200 de 200 refutadas en Lean 4.34.1 + Mathlib v4.34.1.**

- **170 con contramodelo finito y `decide`:** ninguna depende de axiomas.
- **30 con modelo infinito (familia F5):** son pares de Austin, que no tienen contramodelo finito. Sus pruebas se portaron
  del ETP y usan solo axiomas estándar. Ver [infinitos/LEEME_PORT.md](infinitos/LEEME_PORT.md).

| Archivo | Qué es |
|---|---|
| `tareas_etp.jsonl` | las 200 tareas: leyes, enunciado guardado y enunciado falso correcto |
| `contramodelos.jsonl` | tabla, tamaño y origen del contramodelo de cada tarea |
| `lean/ETP_<id>.lean` | un archivo por cada una de las 170 refutadas |
| `enunciados/ETP_<id>.falso.txt` | definiciones más enunciado falso de las 200 (lo que cubre su hash) |
| `resumen.csv` | id, n, compiló, axiomas, táctica, segundos y hashes |
| `SHA256SUMS` | hashes de los `.lean` y de los enunciados, comprobables con `shasum -c` |
| `ERRATA_etiqueta_ETP.md` | la errata de la etiqueta |
| `DESVIACION_D1_etiqueta_ETP.md` | la desviación del prerregistro por esa etiqueta |
| `sorteo_400_falsas.py`, `banco_400_falsas.jsonl` | las 400 falsas del banco: las 200 del ETP y 200 computacionales sorteadas |
| `testigos_etp/` | archivos del ETP (commit `1aec8a7`, Apache-2.0): tablas F4, pares de Austin y fuentes de las F5 en `fuentes_f5/` |
| `infinitos/lean_f5/ETP_<id>.lean` | un archivo por cada una de las 30 F5 |
| `infinitos/PortF5/` | la biblioteca portada del ETP de la que dependen esas 30 |

Los 13 archivos de las tablas F4 solo se leen como datos; no se compila ni se ejecuta nada de `testigos_etp/`. Cada tabla
se acepta solo si la evaluación exhaustiva en Python confirma que cumple LeyA y no cumple LeyB, y
luego la vuelve a comprobar el kernel.

## Reproducir

Los scripts esperan esta carpeta en `Proyecto Godel/tantalus/refutaciones_etp/`, con el corpus en
`Proyecto Godel/corpus_compilar/`. En una copia del repositorio público, los `.lean` de `lean/` compilan en cualquier
proyecto con Lean 4.34.1 y Mathlib v4.34.1, y `tareas_etp.jsonl` trae el contexto de cada tarea. Para las F5, hay que ajustar
la ruta del proyecto de Lean en `infinitos/construir.sh` y en `generar_y_compilar.py`.

Desde esta carpeta, comprueba los hashes:

```bash
shasum -a 256 -c SHA256SUMS --quiet
```

Regenera los `.lean` a partir de las tablas (deben dar los mismos hashes):

```bash
python3 generar_y_compilar.py generar
```

Borra los resultados guardados para que nada se salte:

```bash
rm -f resultados_compilacion.jsonl
```

Compila las 170 finitas (unos 4 minutos con 4 procesos):

```bash
python3 generar_y_compilar.py compilar -j 4
```

Las 30 F5 se compilan aparte, desde `infinitos/` (la biblioteca tarda alrededor de un minuto y las tareas unos 2 en serie):

```bash
cd infinitos && ./construir.sh && python3 generar_f5.py compilar -j 1 && cd ..
```

Luego se actualizan `resumen.csv` y `SHA256SUMS`, y debe decir `refutadas: 200 de 200`:

```bash
python3 generar_y_compilar.py registrar
```

Para rehacer también la búsqueda de contramodelos (unos 6 minutos, casi todos en las F5 que agotan tiempo):

```bash
rm -f contramodelos.jsonl
```

```bash
python3 buscar_contramodelos.py --testigos testigos_etp --limite 20
```

Para compilar un archivo suelto a mano, desde `corpus_compilar/corpus_lean`:

```bash
lake env lean "../../tantalus/refutaciones_etp/lean/ETP_29_2279.lean"
```

Debe imprimir `'refuta_29_2279' does not depend on any axioms`.

## Controles hechos

- Una tabla alterada que no cumple LeyA hace fallar la compilación.
- Una prueba con `sorry` se detecta: `#print axioms` muestra `sorryAx`.
- El enunciado tal como está guardado en el corpus se prueba con `refuta_<id>`.
- Se comprobó que `native_decide`, `sorry`, `admit`, `axiom`, `implemented_by`, `ofReduceBool` y `unsafe` no aparecen en
  los `.lean`, salvo la línea `#print axioms`.
- En las F5, usar el testigo de otra tarea hace fallar la compilación.
- En las F5, un `sorry` puesto dentro de la biblioteca aparece como `sorryAx` en `#print axioms` de la tarea final.
- En las F5, alterar la operación del modelo de `Eq1437` hace fallar la prueba de su ley.
