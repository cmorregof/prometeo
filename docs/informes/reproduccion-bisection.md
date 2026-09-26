# Pasos (b) y (c): sesión del paper y fila de bisección de la Tabla 1 (23 sep 2026)

## (b) Compilación de `Numerical_Methods_Paper` (commit 0e7830d)

MacBook Air M-series, 25 GB, Isabelle2025 (`~/isabelle/Isabelle2025.app`), sin parche CyPhyAssure.
`isabelle build -b -o document=false -d ~/isabelle/CyPhyAssure -d ~/isabelle/Verified_Numerical_Methods Numerical_Methods_Paper`

| sesión (heap) | tiempo real | CPU | qué carga |
|---|---|---|---|
| HOL-Analysis | 5 min 09 s | 29 min 49 s | — |
| ITree_Numeric_VCG | 1 min 50 s | 9 min 45 s | Optics, Shallow_Expressions, Z/Circus_Toolkit, Interaction_Trees, ITree_UTP, ITree_VCG, ODE, Hybrid-Library (teorías cargadas dentro de la sesión) |
| Numerical_Methods_Paper | 36 s | 2 min 20 s | Smooth_Manifolds, Higher_Diffs, Bisection, Fixed_Point_Method, Perceptron, Gradient_Descent |

Total ≈ 7,5 min (los heaps de HOL vienen precompilados en el bundle). Sin warnings, sin errores, sin `sorry`/`oops`
(`isabelle build_log -H Warning -H Error Numerical_Methods_Paper` vacío). Los cuatro teoremas quedan en el heap.

Desviaciones respecto al commit, documentadas en `~/isabelle/PINS.md`:
1. El repo declara `document_files "root.tex"` pero no los versiona: se crearon dos `root.tex` mínimos.
2. Los submódulos de CyPhyAssure (a41662b) no compilan la sesión: `interaction-trees` 5528a8b es anterior a la
   sintaxis `H[P] C [Q]` del paper y referencia `seq_itree`, inexistente. Se fijaron los repos de Isabelle/UTP al
   último commit ≤ 16 ene 2026 (`interaction-trees` d3bc22c, que ya tiene `H[…]` y `old[…]`). Los commits del
   23 jul 2026 (fecha del paper) fallan por el cambio de sintaxis IsaCircus entre `interaction-trees` y `Circus_Toolkit`.

## (c) Driver y fila «Bisection: 15 VCs, 13 auto, 195 LOC»

Driver: `isarl/driver.py` (teoría de trabajo + ML: `vcg`, `try0` 5 s, Sledgehammer 60 s, todo dentro de
`isabelle build` de la sesión `IsaRL_Scratch` sobre el heap del paper). Reproducción: `python -m isarl.repro_bisection`.
Provers externos detectados: E, Vampire, Z3, cvc5, SPASS, Zipperposition, veriT (todos los del bundle).
Tiempo: 424 s (7 min) para las 15 VCs; `vcg` tarda 2,2 s.

| VC | qué es | cerrada por | paper |
|---|---|---|---|
| 1, 5 | signo tras la rama `then`/`else` | Sledgehammer → `smt (verit) zero_compare_simps` | `meson sign_prop` |
| 2, 3, 6, 7 | aritmética de la mitad del intervalo | `try0` → `argo` | `simp`, `smt` |
| 4, 8, 9, 10 | **variante decrece** | ABIERTA: Sledgehammer agota 60 s y 240 s. La línea `smt` del paper (19 lemas) la cierra en 0,2 s (comprobado con `given`) | `smt` (1) + `thus` (3) |
| 11, 12, 13 | precondición → invariante | Sledgehammer, 1 línea | `simp`, `auto`, `linarith` |
| 14, 15 | invariante ∧ ¬guarda → postcondición | Sledgehammer, **usando `bisect_root_extract`**, el lema auxiliar de 40 líneas que el paper escribió para esta VC | manual (Isar) |

Recuento honesto:

| criterio | VCs | auto | 
|---|---|---|
| paper (Tabla 1) | 15 | 13 (87 %) |
| driver, tal cual | 15 | 11 (73 %): 9 genuinas + 2 que solo salen porque el lema `bisect_root_extract` está importado |
| driver, sin contar el lema que empaqueta la prueba manual | 15 | 9 (60 %) |
| driver + líneas verificadas (las 4 `smt` del paper) | 15 | 13 (87 %): coincide con el paper |

Conclusión: el conjunto de VCs es idéntico (15) y para 13 de ellas existe una prueba de una línea verificada, como
dice el paper. Lo que **no** se reproduce en esta máquina es que Sledgehammer *encuentre* la `smt` del variante:
en el paper la VC se enuncia con una sola premisa (`tol < (b-a)/2^iter ⟹ …`), es decir, el humano la adelgazó antes
de lanzar Sledgehammer; con las 7 premisas que produce `vcg` los provers no la encuentran en 4 minutos.
Ese adelgazamiento es una acción manual que conviene registrar (o dar al agente como acción de fase 2).

Cuidado para (d): `bisect_root_extract` no es «matemática auxiliar», es la prueba de la postcondición empaquetada.
Si el target importa la teoría del paper completa, el agente recibe esas 2 VCs gratis. Propuesta: importar solo
`Bolzanos_theorem` y `sign_prop` (matemática) y excluir `bisect_root_extract`.
