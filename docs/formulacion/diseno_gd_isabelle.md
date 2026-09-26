# Juez de teorema en Isabelle para pasos de descenso de gradiente (diseño, 23 sep 2026)

Pedido de Carlos: «Luna demuestra, Isabelle verifica» en el problema de stepsizes del 06. A diferencia de la
bisección (programa ITrees + tripleta de Hoare + anotaciones), aquí el objetivo es un TEOREMA puro de Isabelle/HOL
sobre espacios con producto interno, y la acción del agente es la DEMOSTRACIÓN (texto Isar) más lemas auxiliares
opcionales. El juez solo compila; no agrega automatización (no hay Sledgehammer).

## Enunciado congelado (texto exacto; ASCII de Isabelle)

Importa `"HOL-Analysis.Inner_Product"` (sesión padre `HOL-Analysis`, heap ya compilado en ~/.isabelle).

PRELUDIO (antes del contexto; definicional, sin axiomas):

```
primrec gd :: "('a::real_inner \<Rightarrow> 'a) \<Rightarrow> real list \<Rightarrow> 'a \<Rightarrow> 'a" where
  "gd g [] x = x"
| "gd g (h # hs) x = gd g hs (x - h *\<^sub>R g x)"
```

FIXES (objetivos con n fijo):
```
f :: "'a::real_inner \<Rightarrow> real" and g :: "'a \<Rightarrow> 'a" and x0 xs :: 'a
```
FIXES (objetivos para todo n): lo mismo más ` and n :: nat` (n fijo en el contexto, para que el enunciado
leído antes y después del texto del agente tenga las mismas variables libres).

ASSUMES (todos los objetivos):
```
interp: "\<And>x y. f y + inner (g y) (x - y) + (1/2) * (norm (g x - g y))\<^sup>2 \<le> f x"
    and opt: "g xs = 0"
```

CONCL:

| objetivo | CONCL | tipo |
|---|---|---|
| gd_n1 | `f (gd g [3/2] x0) - f xs \<le> 1/8 * (norm (x0 - xs))\<^sup>2` | n fijo, cota exacta (óptimo de un paso) |
| gd_const_n2 | `f (gd g [1, 1] x0) - f xs \<le> 1/10 * (norm (x0 - xs))\<^sup>2` | n fijo, cota exacta de Drori–Teboulle para N = 2 |
| gd_const_textbook | `0 < n \<Longrightarrow> f (gd g (replicate n 1) x0) - f xs \<le> (norm (x0 - xs))\<^sup>2 / (2 * real n)` | todo n, cota clásica L·R²/(2n) |
| gd_const_dt | `f (gd g (replicate n 1) x0) - f xs \<le> (norm (x0 - xs))\<^sup>2 / (4 * real n + 2)` | todo n, cota exacta de Drori–Teboulle (2014) |

Lectura matemática (L = 1): `interp` para TODO par x, y caracteriza exactamente a las funciones convexas y 1-suaves
con gradiente g (Nesterov, Thm. 2.1.5, y su recíproco); `opt` dice que xs es estacionario, luego minimizador.
`gd g hs x0` aplica x_{k+1} = x_k − h_k·g(x_k). Las hipótesis son satisfacibles: f(x) = ½‖x‖², g = id, xs = 0
(igualdad en interp); la validación lo comprueba en el kernel para que el teorema no sea vacuo.

Residuo de confianza (va en los informes): que interp ⇔ «convexa y L-suave con gradiente g» NO se demuestra en
Isabelle; es matemática de libro aceptada, como los lemas prestados de la bisección.

## Teoría que compila el juez (una sola pasada de sustitución; el texto del agente entra el último)

```
theory Final
  imports __IMPORTS__
begin

__PRELUDE__

context
  fixes __FIXES__
  assumes __ASSUMES__
begin

ML \<open>
  val isarl_axioms0 = length (Theory.all_axioms_of (Proof_Context.theory_of @{context}))
  val isarl_expected = @{prop \<open>__CONCL__\<close>}
\<close>

__AGENTLEMMAS__

theorem isarl_target: "__CONCL__"
__AGENTPROOF__

ML \<open>
  val isarl_prop_ok = Thm.prop_of @{thm isarl_target} aconv isarl_expected
\<close>

end

theorem isarl_export:
  fixes __FIXES__
  assumes __ASSUMES__
  shows "__CONCL__"
  by (rule isarl_target[OF interp opt])

ML \<open>
  (* escribe __OUT__ con: oracles (Thm_Deps.all_oracles [@{thm isarl_export}]), skip_proof (Thm_Deps.has_skip_proof),
     prop_ok (isarl_prop_ok), axioms_ok (número de axiomas = isarl_axioms0), export_ok = true *)
\<close>

end
```

`isarl_export` lo escribe el juez: su enunciado es el teorema global congelado y su prueba solo usa
`isarl_target`. Si `isarl_target` dependiera de algo más que interp y opt, la exportación no cerraría.

Etapa de lemas (si hay lemas del agente o de la biblioteca de la memoria): una teoría `Lemmas` con el mismo
preludio y contexto, el ML con `isarl_axioms0` e `isarl_concl0` antes del texto del agente y, después, el ML que
comprueba que el enunciado congelado se lee igual y que no hay axiomas nuevos y escribe `lemmas.ok`
(mismo patrón que `LEMMAS_THEORY` de `unirl/verifiers.py`).

Sesión: `session IsaRL_GD_<uuid> = "HOL-Analysis" + options [document = false, timeout = 0, parallel_proofs = 0]`.
El prefijo `IsaRL_GD_` distingue estas compilaciones de las de la bisección (`IsaRL_U_`).

## Propuesta del agente y filtros

Formato de respuesta: `PROOF: <<< ... >>>` (obligatorio: el texto que va justo después de
`theorem isarl_target: "..."`, p. ej. `proof - ... qed`, `by ...`, `using ... by ...`, `apply ... done`) y
`LEMMAS: <<< lemma ... >>>` (opcional; mismo filtro que `check_lemmas`). Cierre con `(?!>)` y `_close_symbol`.

Filtro de PROOF: `tokenize_outer`; solo comandos de prueba (ALLOWED_COMMANDS sin lemma/theorem/corollary/
proposition); prohibidos sorry, oops, axiomatization, oracle (UNSOUND), `_BANNED_WORDS`, `__`, `[[` y los
comandos de `_MEANING_COMMANDS` (STATEMENT_DRIFT); cualquier otro comando de teoría es INVALID_PROPOSAL.
Nombres reservados para lemas del agente: `isarl*`, `interp`, `opt`, `gd` (INVALID_PROPOSAL).
Longitud máxima de PROOF: 20000 caracteres.

## Etiquetas y crédito

ACCEPTED (compila, rc = 0, final.json con oracles = [], skip_proof = false, prop_ok, axioms_ok, export_ok),
PROOF_FAILED (errores en la prueba del teorema), LEMMA_FAILED (errores en los lemas; se recuperan los lemas
limpios para la memoria como en `check_lemmas_in_kernel`), UNSOUND (oráculos, skip_proof, axiomas nuevos, o
sorry/oops en el texto), STATEMENT_DRIFT (prop_ok falso, objetivo cambiado en disco, o comandos que cambian el
significado), TIMEOUT, INVALID_PROPOSAL. Recompensa base binaria; crédito parcial 0 salvo ACCEPTED.
`raw["kind"] = "theorem"`; la memoria ordena los intentos por lemas verificados.

## Cota superior (existencia)

Para gd_n1 y gd_const_n2 se genera una demostración a partir de un certificado racional EXACTO del PEP (dual:
multiplicadores λᵢⱼ ≥ 0 y una suma de cuadrados), como la cota superior de la bisección. Para los objetivos
«todo n» no hay cota superior en este juez: los teoremas son ciertos (libro de texto; Drori–Teboulle 2014), pero
nadie los ha formalizado aquí.

## Restricción de ejecución

Mientras corre la bisección (Luna y luego Astra) no se compila nada en Isabelle: Sledgehammer tiene límite de
tiempo real. La validación (`tools/gd_validar.py`) corre en la cola antes de las corridas gd.

## Estado al 24 sep 2026, 06:30 (validado en Isabelle)

* `tools/gd_validar.py`: no vacuidad OK; controles OK (sorry por filtro y por kernel → UNSOUND; `by simp` →
  PROOF_FAILED); cota superior: la variante C (expansión con `simp only` + `argo`) generada desde el certificado
  exacto es ACCEPTED en gd_n1 y en gd_const_n2, ≈ 5 s por compilación. La variante A (linarith) no cierra.
* Prueba de punta a punta con el bucle y un proponente simulado: lema bueno + prueba mala → PROOF_FAILED con el lema
  verificado en la memoria; demostración de referencia → ACCEPTED; el siguiente prompt trae la memoria y el error.
* Cambio respecto del diseño: el conteo de axiomas se hace a nivel de teoría antes del contexto y prop_ok se lee de
  target.json (dentro del contexto), para no depender de valores de ML de un contexto local después de su `end`.
* Cortesía: cada compilación gd espera 10 s seguidos sin compilaciones ajenas de Isabelle (la bisección); la espera
  queda en `raw.espera_s` y no cuenta en el costo del juez. Así las corridas gd pueden convivir con una bisección.
* 24 sep, ~06:50: `parse` busca LEMMAS en el texto sin el bloque PROOF (los bloques no se solapan). Antes, un
  `LEMMAS: <<<>>` mal cerrado se comía la demostración y el intento salía INVALID_PROPOSAL con un motivo confuso: le
  pasó a Luna en gd_n1, ep. 1, paso 1 (único intento con el analizador anterior). Astra corre gd con el nuevo.
