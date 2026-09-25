# Plan: aprendizaje por refuerzo verbal para demostrar teoremas de búsqueda de raíces

Etapa 0 (inventario y plan), 24 sep 2026. Autor del pedido: Carlos Manuel Orrego Franco. Redactado por Claude.
Estado: plan **aprobado** el 24 sep 2026 con los ajustes de §8. Etapas 0 a 6 hechas (§10, §11, §13, §14); pruebas
inteligibles aprobadas (§12). Etapa 7 en marcha (25 sep): Carlos pidió «adelantar todo lo que más se pueda».

## 1. Qué se acordó

Objetivo: que Luna y Astra, con los pesos congelados, mejoren demostrando teoremas de búsqueda de raíces gracias a
un cuaderno persistente verificado (estilo Reflexion). Se actualiza el cuaderno, no los pesos: es aprendizaje en
contexto con memoria curada, y así se describirá en cualquier informe.

Principios (de la propuesta): el kernel de Isabelle es la única fuente de verdad; el juez decide qué entra al
cuaderno; todo enunciado redactado por un LLM pasa por revisión de Carlos; nada de crédito por lo que el martillo
hace solo; el código del modelo se ejecuta aislado.

Cambios aceptados sobre la propuesta original:

1. Glosario Lean→Isabelle y herramienta de consulta de teoremas en el **entorno base** de todas las
   configuraciones, con tope de consultas por episodio. Configuración **B0** sin ellos, para medir su aporte.
2. **Teoremas puros primero** (juez de teorema, ~5 s por verificación). La verificación de programas (tripletas de
   Hoare, 8–23 min por intento) queda como pista posterior. El código de lemas parciales se queda en esa pista:
   **no se prueba ni se enciende ahora**.
3. **Escaleras de teoremas** por método (peldaños pequeños) en lugar de un teorema por método.
4. La recompensa por fracción de pasos cerrados es **solo métrica**; lo que entra al cuaderno se decide con
   reglas que no dependen de ella (§3.6).
5. Reflexión y prueba en **una sola llamada** al modelo.
6. El cuaderno se construye con **Luna**; Astra se usa en evaluación y transferencia.
7. Episodios de evaluación **independientes**: sin memoria de episodios, solo el cuaderno congelado. Ninguna
   demostración de referencia (las del artículo, nuestras cotas superiores, certificados del PEP) entra al cuaderno
   ni a los prompts.
8. Resultados **por teorema y por método**; el plan propone cómo separar el test (§3.2).

## 2. Inventario

### 2.1 Isabelle y dependencias

| componente | versión | dónde |
|---|---|---|
| Isabelle | Isabelle2025 (`isabelle version`) | `~/isabelle/Isabelle2025.app` |
| AFP | mirror-afp-2025 (64e064e, 3 abr 2025), 900 entradas | `~/isabelle/CyPhyAssure/mirror-afp-2025` |
| Artículo (Bryant, Huerta y Munive, Foster 2026) | Verified_Numerical_Methods 0e7830d | `~/isabelle/Verified_Numerical_Methods` (fuera del repo) |
| Isabelle/UTP (ITrees, VCG) | commits ≤ 16 ene 2026 | `~/isabelle/PINS.md` |
| Heaps compilados | HOL, HOL-Analysis, ITree_Numeric_VCG, Numerical_Methods_Paper | `~/.isabelle/Isabelle2025/heaps/` |

### 2.2 Cómo se invoca hoy el juez y cuánto tarda

`python -m unirl run --config <toml>` → `make_verifier` → juez → `isabelle build` de una sesión temporal con nombre
único (`parallel_proofs = 0`), cuyas comprobaciones escriben JSON desde ML (oráculos, `skip_proof`, conteo de
axiomas, igualdad del enunciado término a término con `aconv`).

| juez | archivo | qué acepta | tiempo medido |
|---|---|---|---|
| teorema (stepsize) | `unirl/gd_isabelle.py` | teorema puro sobre HOL-Analysis; el agente escribe PROOF y LEMMAS | mediana 5,1 s por intento; máx. 309 s (3 TIMEOUT a 300 s) |
| programa (bisección) | `unirl/verifiers.py` `IsabelleVerifier` | invariante, variante y lemas; VCs por try0 + Sledgehammer 60 s | lemas: ~28 s; con VCs: 8–23 min |
| consulta de teoremas (prueba de hoy) | — | `find_theorems` en una compilación por lotes | ~8 s + 10 s de cortesía; en modo por lotes Isabelle **no imprime** los resultados: hay que escribirlos a un archivo desde ML |

Proponentes (corridas del 23–24 sep): Luna ~1,5–4 min por respuesta (mediana 194 s en stepsize); Astra mediana
25 min (rango 5 min–2,5 h) en bisección.

### 2.3 Código de lemas parciales

`unirl/verifiers.py`: opción `lemas_parciales` (por defecto apagada) y método `IsabelleVerifier.lemas_uno_a_uno`.
Qué hace: compila el bloque de lemas; si falla, quita el lema donde está el primer error y repite (hasta 12
rondas), y evalúa las VCs solo con los lemas que compilan; el feedback lista los lemas descartados con sus errores.
Qué le falta: pruebas rápidas y en Isabelle, mostrar la recompensa en el prompt, soporte en los informes, y una
decisión sobre dependencias entre lemas (hoy, un lema que usa a otro descartado cae en la ronda siguiente). El
juez de teorema tiene su propio rescate, de todo o nada (`check_lemmas_in_kernel`). Según lo acordado, queda para
la pista de programas y no se toca ahora.

### 2.4 Búsqueda de raíces ya formalizada

| resultado | dónde | forma |
|---|---|---|
| Teorema de Bolzano, `sign_prop`, `bisect_root_extract` | artículo, `Bisection.thy` | lemas puros |
| `bisection_error_bound` | artículo, `Bisection.thy` | tripleta de Hoare (programa ITrees) |
| `bisection_correct` (refinamiento), versiones en punto flotante | artículo, `Bisection_Extra.thy` | refinamiento + IEEE 754 |
| \|g'\| ≤ c < 1 ⇒ contracción (`contractive_deriv_bound`), decaimiento del error `fpm_err_decay`, `fpm_step_decay`, cotas de iteraciones, convergencia cuadrática `fpm_iter_quadratic_convergence` | artículo, `Fixed_Point_Method.thy` | lemas puros + programa `fpm` |
| Taylor (varias formas), derivadas de orden superior | artículo, `Higher_Diffs/` | lemas puros |
| IVT, IVT2, MVT, Taylor, punto fijo de Banach (`banach_fix`) | biblioteca de Isabelle | lemas puros |
| Newton general, secante, regula falsi, Dekker, Brent, ITP | — | **no encontrados** (el AFP local solo tiene Newton para raíces cuadradas: `Sqrt_Babylonian`) |

Los resultados del artículo son **demostraciones de referencia**: su código es público desde julio de 2026 y puede
estar en los datos de entrenamiento de los modelos (riesgo de contaminación, §6). Nunca se importan en el contexto
del juez de un peldaño derivado de ellos ni entran al cuaderno.

### 2.5 Enunciados de 01, 02, 04 y 05 sin versión en Isabelle

| proyecto | teorema (del grafo `proof_kb.py`) | pasos / distractores | en Isabelle |
|---|---|---|---|
| 01 bisección | f continua en [a,b], f(a)f(b) < 0 ⇒ mₙ → c, f(c) = 0, \|mₙ − c\| ≤ (b − a)/2ⁿ⁺¹ | 21 / 7 | parcial: el artículo tiene la versión de programa y Bolzano |
| 02 punto fijo | g contractiva en [a,b] con g([a,b]) ⊆ [a,b] ⇒ punto fijo único, convergencia, cota a priori y a posteriori | 20 / 7 | parcial: Banach (biblioteca) y cotas del artículo (en entorno local) |
| 04 Newton | f ∈ C², f(r) = 0, f'(r) ≠ 0 ⇒ ∃δ, convergencia con \|eₙ₊₁\| ≤ (M/2m)\|eₙ\|² | 18 / 7 | no |
| 05 secante | mismas hipótesis ⇒ \|eₙ₊₁\| ≤ (M/2m)\|eₙ\|\|eₙ₋₁\|, orden φ | 21 / 8 | no |

### 2.6 Lecciones de las corridas del 23–24 sep que el plan incorpora

* Los dos modelos escriben Isabelle como si fuera Lean (métodos inexistentes en Isabelle: `nlinarith` 6 veces,
  `ring` 3, `field_simp` 3, `omega` 1, `positivity` 1) y citan nombres de Mathlib. Es el cuello de botella; de ahí
  el glosario y la consulta (§3.4).
* Un error de formato (`LEMMAS: <<<>>`) costó 4 intentos; el analizador ya separa bloques. Se reportará aparte.
* La memoria de episodios filtró la solución en el PEP (15/15 de Astra = 5 descubrimientos + 10 repeticiones).
* Sin créditos de OpenAI la cola siguió; el bucle ya aborta ante `insufficient_quota`. Se añade tope de llamadas.
* Un texto que el filtro no puede leer (una comilla sin cerrar) se etiqueta STATEMENT_DRIFT; en este cambio se
  separará como SYNTAX_ERROR para no inflar la razón de deriva.

## 3. Diseño por etapa

### 3.1 Etapa 1: corpus `corpus/raices/`

Una entrada JSON por peldaño: `id`, `metodo`, `peldano`, enunciado Isabelle (imports, preludio, fixes, assumes,
concl — el formato de `targets/gd_*.json`, con hash), enunciado en español, `fuente` (artículo, subproyecto, libro),
`dependencias` (ids), `estado` (`aprobado` | `pendiente_revision` | `conjetura`), `dificultad` (1–5, estimada),
`split` (`train` | `test`), `referencia_privada` (ruta a una prueba conocida, si existe; nunca se muestra).

Currículo propuesto (se ajusta con Carlos al revisar los enunciados):

| método | peldaños propuestos |
|---|---|
| bisección | ancho (b − a)/2ⁿ; invariante de signo; raíz en [aₙ, bₙ] (vía IVT); cota del punto medio; iteraciones ⌈log₂((b − a)/tol)⌉; convergencia |
| punto fijo | \|g'\| ≤ c < 1 ⇒ contracción; unicidad; decaimiento cⁿ; cota a posteriori cⁿ/(1 − c)\|x₁ − x₀\|; convergencia; cuadrática si g'(p) = 0 |
| Newton | error de un paso (Taylor + MVT); permanencia en [r − δ, r + δ]; convergencia local; orden 2 |
| secante | error de un paso con diferencias divididas; cota producto; convergencia local; orden φ |
| regula falsi | invariante de horquilla; convergencia; orden lineal |
| híbridos | Dekker, Brent, ITP: fuera de la primera ronda |
| órdenes de convergencia | definiciones y lemas generales (orden p > 1 ⇒ superlineal, etc.) |

Cada método necesita un preludio con la definición de su iteración como función pura (como `gd` en stepsize). Los
preludios y enunciados que redacte un LLM entran como `pendiente_revision` y se listan en
`corpus/raices/revision_enunciados.md` (Isabelle, lectura en español, supuestos dudosos, y si es satisfacible:
cada enunciado lleva una prueba de no vacuidad de sus hipótesis, como en stepsize).

### 3.2 Cómo separar el test: por peldaño o por método completo

| | por método completo (p. ej. test = secante y regula falsi) | por peldaño (algunos peldaños de cada método) |
|---|---|---|
| qué mide | transferencia a métodos no vistos: lo que importa para buscar resultados nuevos | generalización dentro de un método ya visto |
| fuga | baja: ningún lema del cuaderno se escribió para ese método | alta: los peldaños hermanos están correlacionados; un lema de train puede implicar un peldaño de test casi directamente |
| poder estadístico | bajo: 2 métodos de test; la varianza la domina qué métodos se eligen | mayor: más ítems, misma distribución |
| comparabilidad train/test | peor: el test puede ser más difícil por naturaleza | buena |

Propuesta: **test principal por método completo** (secante y regula falsi: cada uno tiene un "hermano" en train,
Newton y bisección), y un **diagnóstico secundario por peldaño** dentro de los métodos de train, reportado aparte y
nunca mezclado con el principal. Si el costo lo permite más adelante, dejar-un-método-fuera rotando.
Reporte: tasa por teorema y por método (fracción de peldaños resueltos por método), con intervalos por bootstrap
por conglomerados (remuestreando métodos, no teoremas), porque los peldaños de una escalera están correlacionados.

### 3.3 Etapa 2: juez robusto

Ya existe: filtros léxicos con lista blanca de comandos (rechaza sorry, oops, axiomatization, oracle, ML*, setup*,
declare, notation, `[[...]]`, cartuchos, marcadores), igualdad del enunciado término a término en el kernel (más
fuerte que una comparación normalizada de texto), oráculos y `skip_proof` (`Thm_Deps`), conteo de axiomas,
exportación al contexto global, límites de tiempo con muerte del árbol de procesos, hash del objetivo releído de
disco. Falta:
* **Aislamiento real**: perfil de `sandbox-exec` para `isabelle build` sin red y con escritura solo en el
  directorio de trabajo, `~/.isabelle` y temporales (probarlo: Java y Poly/ML pueden necesitar otras rutas).
* **Metadatos en cada veredicto**: versión de Isabelle, límites de tiempo, huella del código y del cuaderno.
* Etiqueta **SYNTAX_ERROR** separada de STATEMENT_DRIFT (§2.6).
* Generalizar `TheoremVerifier` a las entradas del corpus (hoy lee `targets/<nombre>.json`).

### 3.4 Entorno base: glosario y consulta (presentes en todas las configuraciones salvo B0)

* **Glosario Lean→Isabelle** sembrado en `cuaderno/errores.md` desde el día uno y **comprobado mecánicamente**: cada
  nombre de Isabelle que recomienda existe, y cada método de Lean que desaconseja no existe. Entradas iniciales,
  a comprobar: `nlinarith`/`positivity` (no existen; usar `linarith` con productos explícitos, `sos`, `smt`),
  `ring` (→ `algebra` o `simp add: algebra_simps`), `field_simp` (→ `simp add: field_simps`), `omega`
  (→ `presburger`, `arith`), `norm_num` (→ `simp`, `eval`), `sq_nonneg` (→ `zero_le_power2`),
  `inner_self_eq_norm_sq` (→ `power2_norm_eq_inner`), `abs_inner_le_norm` (→ `norm_cauchy_schwarz`),
  `div_le_iff` (→ `divide_le_eq`), `mul_pos` (→ `mult_pos_pos`).
* **Consulta** como acción gratuita (no cuenta como intento), con tope por episodio (propuesta: 8) y resultados
  truncados (20 teoremas, presupuesto fijo de tokens). Tipos: buscar teoremas por patrón o subcadena de nombre;
  comprobar si un hecho o un método existe. Implementación: el agente da solo el patrón (saneado con el mismo
  tokenizador; sin ML ni cartuchos); el juez lo inserta en una teoría fija cuyo ML llama a `Find_Theorems` y
  escribe JSON. Coste medido: ~8 s por consulta por lotes; si es un cuello de botella, `isabelle server` con una
  sesión persistente (más complejo). La consulta usa el mismo contexto que el juez (imports del peldaño +
  `Cuaderno.thy`) y **nunca** las teorías del artículo, para que no encuentre la respuesta de un peldaño derivado de
  ellas.

### 3.5 Etapa 3: martillo

`martillo_solo(peldaño)`: Sledgehammer sobre la meta con límite fijo (60 s, como en 08); si cierra, se registra la
línea, el peldaño se marca `resuelto_por_martillo` y no da crédito. `martillo_en_pasos(esqueleto)`: Sledgehammer
sobre cada `have` sin justificar del esqueleto del agente; se pega la línea y el kernel compila el documento.
Implementación reutilizando el patrón del driver de 08 (Sledgehammer desde ML dentro de la compilación). Caché
SQLite con clave hash(meta normalizada, versión de `Cuaderno.thy`, demostrador, límite, versión de Isabelle).
Las llamadas al martillo se hacen **en serie**: su límite es de tiempo real y la concurrencia lo distorsiona.
Línea base de `martillo_solo` recalculada cada vez que cambia `Cuaderno.thy`.

### 3.6 Etapa 4: recompensa (métrica) y qué entra al cuaderno

r = 0 si `martillo_solo` resolvió el peldaño; si no, r = fracción de pasos cerrados + bono si la prueba completa
pasa el kernel. Solo métrica: no actualiza pesos ni decide escrituras. Qué entra al cuaderno:
* **lemas**: solo si el kernel los verifica como enunciados independientes (en el contexto del cuaderno);
* **errores**: de cualquier episodio de train; los que afirman que un nombre o método existe o no, comprobados
  mecánicamente;
* **estrategias**: solo de episodios aceptados, o que aportaron lemas verificados; con contadores de intentos y
  éxitos; descarte por umbral tras un mínimo de intentos.

### 3.7 Etapa 5: reflexión

Hasta K intentos por episodio (propuesta: K = 4). Tras un fallo, el modelo recibe los errores del kernel
truncados y la lista de pasos no cerrados, y responde en **una sola llamada** con `REFLEXION: <<< ... >>>`
(límite de palabras) y la nueva prueba. La reflexión se guarda en el registro del episodio.

### 3.8 Etapa 6: cuaderno del minero

Como en la propuesta: `Cuaderno.thy` (lemas con procedencia: peldaño, episodio, modelo, fecha), `errores.md`,
`estrategias.md`, `episodios.jsonl` (el proponente no lo lee). Solo train escribe. Recuperación: k elementos por
coincidencia de constantes, símbolos y etiqueta de tópico, con presupuesto fijo de tokens. Cada M episodios, Luna
destila errores y estrategias nuevas (con contadores en cero). La evaluación usa una copia congelada con su hash.
Cada entrada registra qué modelo la originó (transferencia).

### 3.9 Etapa 7: experimentos

A (martillo solo), **B0** (proponente + martillo, sin glosario ni consulta, sin reintentos), B (B0 + glosario +
consulta), C (B + reintentos con reflexión), D (C + errores), E (D + lemas), F (E + estrategias). Primera ronda:
A, B0, B, C, E. El cuaderno se construye una vez en train con la configuración más rica; D, E y F lo evalúan con
partes apagadas. Transferencia: cuaderno de Luna evaluado con Astra. Métricas por teorema y por método: tasa de
éxito en test, fracción media de pasos cerrados, llamadas a la API, tiempo de martillo y de juez, y consultas
usadas. Salida: CSV + informe corto en markdown (y, si Carlos lo pide, PDF con el formato de su plantilla).

## 4. Archivos

Nuevos (todos en `09_unified/`): `corpus/raices/*.json`, `corpus/raices/revision_enunciados.md`,
`unirl/corpus.py` (carga, validación, split), `unirl/aislamiento.py` (sandbox), `unirl/consulta.py`,
`unirl/martillo.py` (+ caché SQLite), `unirl/cuaderno.py` (admisión, recuperación, destilación),
`unirl/reflexion.py` (episodio con K intentos, consultas y reflexión), `unirl/experimentos.py` (configuraciones
A–F, CSV e informe), `cuaderno/` (Cuaderno.thy, errores.md, estrategias.md, episodios.jsonl),
`configs/rl_verbal/*.toml`, `tests/test_rl_verbal.py`, proponente simulado para pruebas sin costo.
Modificados: `unirl/gd_isabelle.py` (generalizar a corpus, SYNTAX_ERROR, metadatos, aislamiento),
`unirl/cli.py` (subcomandos), `unirl/loop.py` (acción de consulta; tope de llamadas).
No se tocan 01–08 ni la pista de programas (lemas parciales).

Pruebas automáticas mínimas (de la propuesta): acepta una prueba válida; rechaza sorry; rechaza ML; rechaza un
enunciado modificado; el caché devuelve la línea guardada; los lemas parciales cuentan bien (esta queda para la
pista de programas, por el punto 2); el cuaderno rechaza un lema no verificado. Añadidas: la consulta rechaza
patrones con ML o cartuchos y respeta el tope; el glosario se comprueba contra Isabelle.

## 5. Presupuesto y tiempos (estimados con lo medido)

Por intento de Luna: ~3,5 min (modelo) + ~5 s (juez) + consultas (~8–18 s cada una). Con ~20 peldaños de train,
K = 4 y un episodio por peldaño, construir el cuaderno lleva ~5 h. Evaluar la primera ronda (4 configuraciones con
modelo × ~10 peldaños de test × 2 episodios × K = 4) son ~320 intentos, ~19 h en serie; con 4 episodios en paralelo
(el cuello de botella es la API, no el juez), ~5 h. Astra cuesta ~7 veces más por intento: solo un subconjunto del
test y la transferencia. Tope configurable de llamadas por corrida y modo simulado para validar sin costo.

## 6. Riesgos

1. **Tiempo de revisión de Carlos**: cada enunciado y preludio nuevo necesita su aprobación; por eso escaleras de
   peldaños pequeños y un archivo de revisión legible.
2. **Contaminación**: el código del artículo es público; los modelos pueden haberlo visto. Se marcarán los peldaños
   con formalización pública y se reportarán aparte.
3. **Poder estadístico**: pocos métodos en test; intervalos por conglomerados; no sobreinterpretar diferencias.
4. **Martillo no determinista** (tiempo real, carga de la máquina): en serie, con caché, y con la línea base
   recalculada.
5. **La consulta como fuga**: si el contexto contiene la respuesta, la consulta la encuentra; por eso el contexto
   del juez nunca incluye las teorías del artículo, y los lemas del cuaderno que implican un peldaño de test se
   reportan como transferencia, medida con el cuaderno congelado.
6. **Aislamiento en macOS**: `sandbox-exec` está en desuso pero funciona; hay que probar qué rutas necesita
   Isabelle.
7. **Costo de Astra** y límites de la API: tope de llamadas y aborto ante errores de crédito (ya implementado).
8. **Límites de sesión de Claude**: se trabaja etapa por etapa, sin flotas de agentes.

## 7. Decisiones que necesito de Carlos

1. Aprobar el plan, o ajustarlo.
2. Test: ¿por método completo (propuesta: secante y regula falsi) con diagnóstico por peldaño aparte?
3. K = 4 intentos y 8 consultas por episodio, ¿o otros valores?
4. Tope de llamadas a la API por corrida (propuesta: 150 para Luna, 40 para Astra).
5. ¿El informe final de experimentos también con el formato de su plantilla, en PDF?

## 8. Ajustes aprobados por Carlos (24 sep 2026)

1. Test por método: secante y regula falsi completos, **con sus peldaños bajos**. Con solo dos métodos no se
   remuestrea por método: se reporta por teorema y se dice explícitamente que el test tiene dos métodos.
2. K = 4 intentos y 8 consultas por episodio. Se registra **en qué intento** ocurre cada éxito.
3. Topes fijados solo después de mostrar la cuenta (§9).
4. La configuración A (martillo solo) corre **siempre en serie**. En corridas paralelas, cada veredicto registra la
   carga de la máquina, y el informe dice si hubo fallos por límite de tiempo.
5. Informe final en PDF con la plantilla de Carlos; durante las corridas, markdown y CSV.

## 9. Presupuesto: la cuenta para fijar los topes

Medido el 24 sep 2026: una llamada representativa a Luna (esfuerzo high; un peldaño de Newton con un intento fallido
en el historial) usó 1 208 tokens de entrada y 8 389 de salida, de ellos 8 191 de razonamiento, en 88 s. Para
estimar se toma entrada 5 000 (el prompt crece con el cuaderno y el historial) y salida 12 000. Astra no se ha medido:
sus llamadas de la bisección tardaron de 5 min a 2,5 h, así que se dan tres escenarios de salida.
Precios estándar de OpenAI por millón de tokens (página de precios, consultada el 24 sep 2026): Luna $0,10 entrada y
$0,50 salida; Astra $10 entrada y $50 salida (100 veces Luna).

Llamadas por episodio: hasta K = 4 pruebas más hasta 2 turnos de consulta (las 8 consultas se piden en lotes de a 4
por turno; cada turno es una llamada).

| fase | cuenta | llamadas | +20 % | costo |
|---|---|---|---|---|
| construir el cuaderno (Luna) | 24 peldaños de train × (4 + 2) + 4 destilaciones (una cada 6 episodios) | 148 | 178 | $0,83–1,15 |
| evaluar, primera ronda (Luna) | test 12 × 2 episodios: B0 × 1, B × (1 + 2), C × 6, E × 6 | 384 | 461 | $2,17–3,00 |
| transferencia (Astra, config. E, 1 episodio por peldaño) | 12 × 6 | 72 | 86 | $48 / $134 / $264 con salida de 10k / 30k / 60k tokens |

Topes propuestos: Luna 180 llamadas para el cuaderno y 470 para la evaluación; Astra 86 llamadas y **$150**.
Propongo, además, un tope en dólares calculado con los tokens reales de cada respuesta (hoy no se registran;
se añadirá en la Etapa 5), y medir primero 3 llamadas de Astra para elegir el escenario. Construir un cuaderno con
Astra (transferencia en el otro sentido) costaría ~$230–270 más y queda fuera de la primera ronda.

### 9.1 Recuento tras añadir las versiones clásicas (24 sep 2026)

El corpus pasó de 36 a 46 peldaños (train 24 → 30, test 12 → 16) al añadir las 10 versiones clásicas. Los topes
aprobados se calcularon con 24/12; la cuenta nueva, con los mismos supuestos:

| fase | cuenta | llamadas | +20 % | costo |
|---|---|---|---|---|
| cuaderno (Luna) | 30 × (4 + 2) + 5 destilaciones | 185 | 222 | $1,05–1,45 |
| evaluación (Luna) | 16 × 2 × (1 + 3 + 6 + 6) | 512 | 614 | $2,90–4,00 |
| transferencia (Astra, E) | 16 × 6 | 96 | 115 | $63 / $179 / $351 (salida 10k / 30k / 60k) |

Pendiente de decisión de Carlos: subir los topes a 222 / 614 llamadas para Luna, y para Astra, o mantener 86
llamadas y $150 (alcanza para ~12 peldaños de test si la salida es de ~30k tokens), o decidir tras medir 3 llamadas.

### 9.2 Decisión de Carlos (24 sep 2026): topes y presupuesto total

* Luna: 222 llamadas para el cuaderno y 614 para la evaluación (≈ $5,5 en el peor caso, con margen).
* Astra: se aplaza; primero se miden 3 llamadas y se decide con esos números.
* **Presupuesto total: $25**, y lo que se use de Astra solo para algo interesante. Tras Luna quedan ≈ $19,5; con
  la medición previa, ≈ $15–18 para Astra: unas 10 llamadas si su salida ronda los 30k tokens, unas 30 si ronda los
  10k.
* Requisito nuevo antes de cualquier corrida con modelo: **libro de gastos** persistente (`logs/gasto.json`) que suma
  el costo real de cada llamada (tokens de la respuesta × precio) y un **tope global en dólares** (25) que aborta la
  corrida antes de pasarse, además del tope de llamadas por fase.

### 9.3 Segundo modelo: Sol en lugar de Astra (24 sep 2026)

Carlos elige `gpt-6-sol` ($2 entrada, $10 salida por millón de tokens) como segundo modelo; Astra queda para un
proyecto más ambicioso con presupuesto propio. Luna, Sol y Astra son la misma familia GPT-6 en tres escalones de
precio, así que Luna frente a Sol mide el efecto de un modelo intermedio sin cambiar de generación.

Diseño propuesto para Sol (pendiente de confirmar tras medir 3 llamadas, < $1): configuraciones C (sin cuaderno) y E
(cuaderno congelado de Luna) sobre los 16 peldaños de test, un episodio por peldaño, K = 3 intentos y 1 turno de
consulta por episodio: 2 × 16 × 4 = 128 llamadas, ≈ $17 si su salida se parece a la de Luna. Con Luna (≈ $5,5) el
total queda en ≈ $22,5, bajo el tope de $25. Si Sol razona mucho más que Luna, se reduce el test a los peldaños más
informativos antes que pasarse del tope. Sin las dos configuraciones no se puede separar el efecto del modelo del
efecto del cuaderno.

### 9.4 Revisión de enunciados y comparación entre modelos (24 sep 2026)

Carlos aprobó los 46 enunciados revisados («todos correctos matemáticamente»), con cambios: pf_6 pasa a llamarse
`pf_6_a_priori_x1` (02 la llama «a posteriori», pero en la terminología usual es a priori: solo usa x0 y x1); se
agrega la a posteriori verdadera `pf_6p_a_posteriori` (|xₙ − p| ≤ k/(1 − k)·|xₙ − xₙ₋₁|) y, como peldaño de
dificultad 5 para train, `newton_6c_q_orden2` (|eₙ₊₁|/eₙ² → |f''(r)/(2f'(r))|). Esos dos quedan pendientes de
revisión. Corpus: 48 peldaños, train 32 (30 aprobados) y test 16; el test tiene 5 peldaños de dificultad 5 y train 1.

Reporte: test por teorema y por nivel de dificultad (no se remuestrea por método: solo hay dos).

Comparación entre modelos con el mismo presupuesto: además de su evaluación completa, Luna corre en test con la
misma configuración que Sol (C y E, K = 3, 1 turno de consulta, 1 episodio por peldaño). Análisis de C contra E
**pareado sobre los mismos peldaños**, para cada modelo (tabla por peldaño y conteo de pares discordantes, prueba
exacta de McNemar), y de Luna contra Sol pareado por peldaño y configuración. Se registra en qué intento ocurre
cada éxito.

Recuento con train = 32 (si se aprueban los dos peldaños nuevos):

| fase | llamadas | +20 % | costo (5k entrada / 12k salida) |
|---|---|---|---|
| cuaderno (Luna) | 32 × 6 + 5 = 197 | 236 | $1,54 |
| evaluación completa (Luna) | 16 × 2 × 16 = 512 | 614 | $3,99 |
| comparación pareada (Luna, C y E) | 2 × 16 × 4 = 128 | 154 | $1,00 |
| comparación pareada (Sol, C y E) | 128 | 154 | $19,97 (sin margen $16,64) |
| **total** | | | **$26,50 con margen; $22,08 sin margen** |

Con el margen del 20 % el peor caso pasa de $25 por $1,50. El tope en dólares del libro de gastos impide pasarse;
para no depender de él, se decide tras medir 3 llamadas de Sol: si su costo por llamada resulta ≥ $0,12, la
evaluación completa de Luna usa 1 episodio por peldaño en lugar de 2 (ahorra ≈ $2). Tope de cuaderno propuesto: 236
llamadas (el aprobado era 222, calculado con 30 peldaños de train).

### 9.5 Decisiones del 24 sep 2026 (segunda revisión)

* Aprobados `pf_6p_a_posteriori` (dependencia corregida a `pf_2_dentro`) y `newton_6c_q_orden2`: 48 peldaños
  aprobados (train 32, test 16). Confirmadas las hipótesis sobrantes de `pf_3` (dentro), `pf_7` (x0) y `bis_1` (a ≤ b).
* Al interpretar `secante_6c_orden_phi` se reporta que `newton_6c_q_orden2` es su análogo directo en train.
* Tope del cuaderno: 236 llamadas.
* No se recorta la evaluación de Luna: los 2 episodios estiman la variabilidad dentro de un mismo modelo. Si el costo
  medido de Sol lo requiere, el tope en dólares sube de $25 a **$28**.

## 10. Etapa 2 hecha: juez robusto y libro de gastos (24 sep 2026)

* `TheoremVerifier.desde_corpus(id)` (y `make_verifier` con `peldano = "<id>"`): juez para peldaños aprobados; un
  peldaño no aprobado no tiene juez (`corpus.NoAprobado`).
* Exportación genérica al contexto global con **instanciación por nombre** (`isarl_target[where v = v …, OF assms]`;
  `?x0.0` para nombres terminados en dígito). La forma anterior (`OF interp opt`) fallaba con hipótesis como
  ⋀j. |e (Suc j)| ≤ c·|e j| («OF: multiple unifiers») y hacía pasar una prueba correcta por PROOF_FAILED.
  Comprobado en los 48 peldaños: la teoría final exporta en 48/48, y el `sorry` de prueba se detecta como
  `skip_proof` en 48/48 (`tools/corpus_exportacion.py`).
* Nombres reservados por objetivo: etiquetas de las hipótesis y constantes del preludio, más `isarl*`.
* Etiqueta **SYNTAX_ERROR** (cadena o comentario sin cerrar), separada de STATEMENT_DRIFT.
* **Aislamiento** con `sandbox-exec`: sin red externa (Isabelle conserva sus sockets locales), sin escritura fuera del
  directorio de trabajo, `~/.isabelle` y temporales. Comprobado: escribir fuera da «Operation not permitted»; la red
  externa no conecta (sin el aislamiento, la misma consulta responde 200); las compilaciones funcionan.
* **Metadatos en cada veredicto**: Isabelle2025, versión del juez, límite de compilación, aislamiento, carga de la
  máquina (1, 5 y 15 min) y hash del objetivo.
* **Libro de gastos** (`unirl/gasto.py`, `logs/gasto.json`): toda llamada a OpenAI pasa por `ProveedorContable`,
  que registra los tokens reales y su costo, y antes de cada llamada exige que el peor caso quepa en el tope en
  dólares (25; 28 si lo requiere Sol) y en el tope de llamadas de la fase; si no, aborta la corrida.
* Pruebas: 88 rápidas y 6 con Isabelle, todas pasan. Demostraciones de referencia privadas en
  `tests/fixtures/pruebas_privadas/` (nunca se muestran al proponente).

## 11. Etapa 3 hecha: martillo, consulta y errores sembrados (24 sep 2026)

* `unirl/martillo.py`:
  * `martillo_solo`: try0 5 s y Sledgehammer 60 s. Una línea cuenta solo si el juez la acepta en el kernel.
  * `martillo_en_pasos`: el agente marca pasos con `by martillo`. La pasada 1 busca una línea por marca (caché, try0 o
    Sledgehammer); luego el juez compila la prueba completa con las líneas pegadas.
  * Caché SQLite por enunciado, cuaderno, límites y versión de Isabelle; `consultar` (saneo y tope explícito);
    `verificar_glosario`.
* Lecciones de Isabelle:
  * Un `method_setup` se evalúa primero sobre un estado ficticio `TERM _`, sin subobjetivos, y ahí debe fallar en silencio.
  * Los datos van a ML por archivo, nunca pegados como literales: los símbolos `\<...>` rompen el escape.
  * En el ML de Isabelle, `ord` es de cadenas: hay que usar `Char.ord`.
* **Línea base A**: la resuelve el martillo solo en **1 de 48** (train 1 de 32, test 0 de 16): `pf_3_unicidad`, con
  `by (smt (verit, del_insts) contr fp fq hp hq k1 mult_le_cancel_right1)`. En los otros 47, Sledgehammer agota sus 60 s
  sin encontrar nada. Media: 76 s por peldaño. Detalle en `resultados/martillo_linea_base.{md,csv,json}`.
* **Martillo por pasos** (`resultados/martillo_pasos_demo.json`): en `orden_1_lineal`, con el esqueleto de la inducción
  y el paso inductivo marcado, Sledgehammer encuentra `using ordered_comm_semiring_class.comm_mult_left_mono by blast`
  y el juez acepta la prueba completa. Tarda 21 s; la segunda vez sale de la caché en 15 s.
* **Suspensión de la máquina** (lección):
  * El Mac se suspendió durante 4 peldaños de secante. El límite de Sledgehammer corre en tiempo de pared, así que su
    «timeout» llegó con 18–48 s de búsqueda real.
  * Se detectó comparando el tiempo de pared de Sledgehammer con el monótono de Python.
  * Ahora `Reloj` mide los dos, y una búsqueda con más de 5 s de suspensión y sin resultado no se guarda y se repite.
  * Los 4 peldaños (más `secante_6c`) se rehicieron bajo `caffeinate -i`, con Sledgehammer de 62,0 a 62,9 s y
    suspensión 0. El resultado no cambió.
  * **En la Etapa 7 todas las corridas van bajo `caffeinate -i`**, y cada veredicto registra la suspensión.
* **Errores sembrados**:
  * El glosario se volvió a comprobar en Isabelle: 25 de 25, con su hash en `glosario_verificacion.json`.
  * `unirl/cuaderno.py` siembra `cuaderno/errores.json` y `errores.md`: 25 errores con contadores en 0.
  * Solo train los incrementa, y se niega a sembrar si la comprobación no es del mismo glosario.
* Herramientas: `tools/linea_base_martillo.py` (con `--rehacer`), `tools/martillo_pasos_demo.py`,
  `tools/sembrar_errores.py` y `tools/nota_rl_verbal.py`. Esta última genera la nota del problema en PDF con la
  plantilla de Carlos, en `docs/informes/rl_verbal/nota.pdf`, con la escalera completa en el apéndice.
* Pruebas: 114 rápidas y 12 con Isabelle, todas pasan (`resultados/pruebas_*.xml`). Nuevas: la caché devuelve la línea
  guardada; no se guardan los fallos de infraestructura ni las búsquedas con suspensión; la consulta rechaza ML,
  cartuchos y comentarios y respeta el tope sin descartar en silencio; los errores se siembran solo de un glosario
  comprobado; el martillo por pasos cierra `orden_1_lineal` y la segunda vez usa la caché.

## 12. Pruebas inteligibles (pedido de Carlos, 24 sep 2026): propuesta

Hoy el proponente devuelve la demostración Isar completa y queda en el registro de cada intento. Pero el kernel acepta
igual una línea opaca (`by (smt ... siete hechos)`) que una demostración estructurada. Propuesta:

1. **La verdad la sigue decidiendo solo el kernel**: la inteligibilidad no cambia la etiqueta ACCEPTED. Entra por
   cuatro lados:
2. **Instrucción al proponente** (Etapa 5):
   * Isar estructurado: `proof … qed`, `have`/`show`, `also`/`finally`, `obtain`.
   * Un paso por idea matemática, con las hipótesis citadas por su etiqueta.
   * Un comentario breve en español `(* … *)` en cada paso no trivial.
   * No cerrar el teorema entero con una sola llamada de automatización, salvo en peldaños triviales.
3. **Medida mecánica de legibilidad** por prueba aceptada:
   * número de pasos explícitos (`have`/`show`/`obtain`);
   * fracción de pasos cerrados por el martillo;
   * líneas opacas: `smt` o `metis` con más de 4 hechos;
   * longitud, y si la prueba es de una sola línea.
   Se reporta junto a la tasa de éxito, por teorema y por configuración.
4. **Crédito** (`r_V`, Etapa 4): una prueba aceptada cuyo nivel superior es una sola línea opaca recibe el mismo trato
   que `martillo_solo`, es decir, sin crédito. Eso es precisamente «el martillo lo hizo». Una línea legible como
   `by (induction n) simp_all` sí da crédito.
5. **Informe**:
   * Cada prueba aceptada va completa en el apéndice del PDF final, con el intento en que se logró y su reflexión.
   * Los pasos que cerró el martillo van marcados con `(* martillo *)`.
   * Opcional: una lectura en español redactada por el modelo, marcada como **no verificada** (el kernel no revisa prosa).

**Decisión de Carlos (24 sep 2026): se aplica el punto 4** («Aplica el punto 3», en la numeración del mensaje).

## 13. Etapa 4 hecha: recompensa, legibilidad y admisión al cuaderno (24 sep 2026)

* `unirl/recompensa.py` calcula la métrica, que no entrena ni decide escrituras: `r_V = ρ + b·[aceptada]`, con
  **b = 1**. ρ = 1 si la prueba se aceptó; si no, es la fracción de marcas `by martillo` cerradas (0 sin marcas).
  r_V = 0 en cuatro casos:
  * el martillo solo resuelve el peldaño (según la línea base de ese mismo cuaderno);
  * la prueba del agente es solo `by martillo` sobre la meta;
  * la prueba aceptada es una sola línea opaca (§12);
  * la etiqueta es de deriva, UNSOUND, SYNTAX_ERROR o INVALID_PROPOSAL.
* Sin la línea base del cuaderno en uso no hay recompensa (`LineaBaseDesactualizada`). La herramienta de línea base
  escribe un archivo por cuaderno: `martillo_linea_base[_<hash>].json`.
* **Opaca**: `smt` o `metis` con más de 4 hechos, contando los de su `using`.
* **Una sola línea opaca**: quitando los cierres triviales, queda una única invocación, y es opaca. Son cierres
  triviales `.`, `..` y `by simp`, `by auto`, `by blast`, `by assumption`, `by fact` y `by rule`, todos sin argumentos.
  Así no se esquiva la regla envolviendo la línea en `proof - show ?thesis … qed` ni añadiendo un `have … by simp`.
  Cada `apply` de un guion cuenta como invocación, así que un guion con inducción no es «una línea».
* **Legibilidad** de cada prueba: pasos explícitos, invocaciones (totales y no triviales), opacas, pasos del martillo,
  comentarios, líneas y caracteres. La prueba de referencia de `orden_1_lineal` da 4 pasos, 3 invocaciones no triviales
  y 0 opacas; la línea `smt` de `pf_3` es una sola línea opaca, con 7 hechos.
* **Admisión** (`unirl/cuaderno.py`):
  * **Lemas**:
    * El kernel los compila a nivel de teoría, fuera del contexto con las hipótesis del peldaño, con el cuaderno previo
      como único contexto; sin oráculos, sin skip_proof y sin axiomas nuevos.
    * Se admite un lema a la vez, con nombre libre. No puede tapar un hecho existente ni usar etiquetas o constantes
      reservadas del corpus.
    * **Alcance**: si usa constantes del preludio de un método, es de ese método y solo entra desde un episodio suyo;
      si no, es general. Los lemas de punto fijo y de órdenes son generales, porque su preludio no define constantes.
  * **Errores**: desde cualquier episodio de train; cada afirmación de existencia se comprueba en Isabelle, y una sola
    falsa basta para rechazarlo.
  * **Estrategias**: solo de episodios de train aceptados o que aportaron lemas verificados. Tienen contadores y se
    descartan con al menos 5 usos y una tasa de éxito menor que 0,2 (umbrales propuestos, se pueden cambiar).
  * Comprobado en Isabelle:
    * entran un lema general y `bis_cero` (de bisección, con su preludio);
    * se rechazan uno falso (la prueba no cierra), uno que usaba `ab` (fuera del peldaño no existe) y uno llamado
      `mult_left_mono` (taparía el de Isabelle).
* La recompensa por lemas parciales sigue apagada (pista de programas).
* Pruebas: `tests/test_recompensa.py`, con 34 rápidas y 5 con Isabelle.

## 14. Etapas 5 y 6 hechas: episodio con reflexión y cuaderno (25 sep 2026)

* **Episodio** (`unirl/reflexion.py`):
  * Cada llamada al modelo es una de dos cosas:
    * un turno de consulta: `CONSULTAS` sin `PROOF`. Se ejecutan hasta 4 consultas en el contexto del peldaño, con los
      lemas del cuaderno; no gasta intento y tiene tope de turnos;
    * un intento: `REFLEXION` (desde el 2.º, máximo 150 palabras), `LEMMAS` opcional y `PROOF`.
  * Evaluación de cada intento: martillo por pasos (en serie, con candado entre procesos), luego el juez, luego r_V.
    Si una marca no cierra, el intento es PROOF_FAILED, y el modelo ve la meta abierta y los errores traducidos a
    líneas de su PROOF.
  * Registro por llamada: tokens y dólares, segundos de modelo, juez y martillo, carga, suspensión, legibilidad y r_V.
  * Un error del proveedor gasta un intento. La falta de créditos o el tope de gasto abortan la corrida.
* **Seguridad** (hallazgo de esta etapa): la pasada 1 del martillo corre con quick_and_dirty. Ahora el texto del
  agente pasa los filtros del juez antes de esa pasada; sin ellos, un `sorry` o ML del agente habría entrado ahí.
* **Configuraciones** (`CONFIGS`):

  | config | intentos | turnos de consulta | glosario | reflexión | cuaderno |
  |---|---|---|---|---|---|
  | B0 | 1 | 0 | no | no | nada |
  | B | 1 | 2 | sí | no | nada |
  | C | 4 | 2 | sí | sí | nada |
  | D | 4 | 2 | sí | sí | errores |
  | E | 4 | 2 | sí | sí | errores y lemas |
  | F | 4 | 2 | sí | sí | errores, lemas y estrategias |
  | C3 | 3 | 1 | sí | sí | nada |
  | E3 | 3 | 1 | sí | sí | errores y lemas |

  C3 y E3 son las de la comparación entre modelos.
* **Instrucción al modelo**:
  * No es Lean.
  * Isar estructurado, un paso por idea, hipótesis citadas por su nombre y un comentario en español `(* … *)` en cada
    paso no trivial.
  * Se le dice que una prueba que sea solo `by martillo`, o una línea opaca, no cuenta como inteligible.
* **Cuaderno** (`unirl/cuaderno.py`, clase `Cuaderno`):
  * Archivos: `errores.json` (glosario más errores aprendidos), `lemas.json`, `estrategias.json` y `episodios.jsonl`.
  * **Recuperación**: k elementos por parte (errores 6, lemas 8, estrategias 5), por coincidencia de identificadores y
    símbolos con el enunciado y el preludio, con presupuesto de caracteres (1 500, 3 500 y 1 500). El glosario va
    completo (unos 3 300 caracteres).
  * Los lemas mostrados son los que el juez añade al intento. Un lema de un método solo se muestra en ese método.
  * **Congelado**: copia en `cuaderno/congelados/<hash>/`, de solo lectura, que se comprueba contra su hash.
* **Construcción del cuaderno** (`python -m unirl.experimentos cuaderno`):
  * Train con la configuración F, en serie. Orden: bisección, punto fijo, órdenes y Newton, por peldaño.
  * Tras cada episodio:
    * se cuentan los errores del kernel (`Undefined method/fact "X"`);
    * se actualizan los contadores de las estrategias mostradas;
    * pasan por la admisión del kernel hasta 4 lemas que el juez verificó en el episodio.
  * Cada 6 episodios, Luna destila errores (sus afirmaciones de existencia se comprueban en Isabelle) y estrategias
    (solo de episodios aceptados o con lemas).
  * Se reanuda con `--reanudar`. Al final, el cuaderno se congela.
  * En train, r_V usa la línea base sin cuaderno.
* **Evaluación** (`python -m unirl.experimentos evaluar`):
  * Test, episodios en paralelo (el martillo sigue en serie por el candado).
  * La línea base del martillo con los lemas del cuaderno congelado se calcula con `linea-base --cuaderno <hash>`,
    y la recompensa la exige.
* `medir-sol`: 3 llamadas de Sol para medir el costo antes de la comparación.
* `resumen`: `episodios.csv` y `resumen.md` por corrida.
* **Pruebas**: 160 rápidas (entre ellas el episodio con proponente simulado, los turnos de consulta, el error del
  proveedor, la recuperación, el congelado, los contadores y la destilación). El episodio simulado con Isabelle real
  (consulta, fallo, reflexión, aceptación con el martillo) pasa en 36 s.
* Hallazgo corregido: en B0 (sin consultas), el prompt terminaba invitando a «hacer primero CONSULTAS».

