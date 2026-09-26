# Revisión de enunciados: corpus de búsqueda de raíces

Redactados por Claude el 24 sep 2026. Carlos revisó y aprobó el 24 sep 2026 («todos correctos matemáticamente; apruebo con estos cambios») y, en una segunda revisión, aprobó `pf_6p_a_posteriori` (con dependencia `pf_2_dentro`) y `newton_6c_q_orden2`, y confirmó las hipótesis sobrantes. Todos aprobados. Solo los aprobados pueden usarse en una corrida. Análogos directos entre métodos: `secante_6c_orden_phi` (test) y `newton_6c_q_orden2` (train).

Qué se comprobó, sin demostrar ninguna conclusión (eso es trabajo del proponente):

* **Isabelle**: el preludio compila; las hipótesis y la conclusión se leen y tipan en su contexto; y una `interpretation` con valores concretos demuestra que las hipótesis se pueden cumplir (el peldaño no es vacuo). Detalle en `validacion_isabelle.json`.
* **Numérica**: casos aleatorios que cumplen las hipótesis; la conclusión se cumplió en todos (`tools/corpus_raices.py`). Detecta errores de formalización (constantes, exponentes); no es una demostración.

Convenciones de HOL que conviene tener presentes: x/0 = 0; `real n` es n como real; `(g ^^ n) x0` es g aplicada n veces; `X ⇢ L` (`\<longlonglongrightarrow>`) es convergencia de sucesiones. Imports de todos: `HOL-Analysis.Analysis` (nunca las teorías del artículo).

Split: **train** = bisección, punto fijo, Newton, órdenes (32 peldaños); **test** = secante y regula falsi completos, con sus peldaños bajos (16 peldaños); total 48. El test tiene solo dos métodos: los resultados se reportarán por teorema y por nivel de dificultad.

Peldaños por nivel de dificultad:

| dificultad | train | test |
|---|---|---|
| 1 | 3 | 0 |
| 2 | 12 | 5 |
| 3 | 10 | 3 |
| 4 | 6 | 3 |
| 5 | 1 | 5 |

Versión: **clásica** es la forma de libro del resultado; **debilitada** tiene una conclusión más débil o hipótesis más fuertes en algo que importa (δ fijo, cotas dadas, peor constante), y se dice en qué y por qué. Cada debilitada con forma clásica más fuerte va seguida de esa versión clásica (sufijo `c`), también pendiente de revisión. Un peldaño clásico que arrastra hipótesis del contexto común que no usa se marca clásico con esa nota.

| id | método | split | versión | dificultad | estado | Isabelle | numérica |
|---|---|---|---|---|---|---|---|
| `bis_1_ancho` | Bisección | train | clasica | 1 | aprobado | ✓ | 400/400 |
| `bis_2_encaje` | Bisección | train | clasica | 2 | aprobado | ✓ | 400/400 |
| `bis_3_signo` | Bisección | train | clasica | 2 | aprobado | ✓ | 400/400 |
| `bis_4_raiz` | Bisección | train | clasica | 3 | aprobado | ✓ | 400/400 |
| `bis_5_cota` | Bisección | train | debilitada | 3 | aprobado | ✓ | 400/400 |
| `bis_5c_cota_uniforme` | Bisección | train | clasica | 3 | aprobado | ✓ | 400/400 |
| `bis_6_iteraciones` | Bisección | train | clasica | 2 | aprobado | ✓ | 400/400 |
| `bis_7_convergencia` | Bisección | train | clasica | 4 | aprobado | ✓ | 400/400 |
| `pf_1_derivada` | Punto fijo | train | clasica | 2 | aprobado | ✓ | 400/400 |
| `pf_2_dentro` | Punto fijo | train | clasica | 1 | aprobado | ✓ | 400/400 |
| `pf_3_unicidad` | Punto fijo | train | clasica | 2 | aprobado | ✓ | 400/400 |
| `pf_4_decaimiento` | Punto fijo | train | clasica | 2 | aprobado | ✓ | 400/400 |
| `pf_5_a_priori` | Punto fijo | train | debilitada | 2 | aprobado | ✓ | 400/400 |
| `pf_5c_a_priori_max` | Punto fijo | train | clasica | 2 | aprobado | ✓ | 400/400 |
| `pf_6_a_priori_x1` | Punto fijo | train | clasica | 3 | aprobado | ✓ | 400/400 |
| `pf_6p_a_posteriori` | Punto fijo | train | clasica | 3 | aprobado | ✓ | 400/400 |
| `pf_7_existencia` | Punto fijo | train | clasica | 3 | aprobado | ✓ | 400/400 |
| `pf_8_convergencia` | Punto fijo | train | clasica | 4 | aprobado | ✓ | 400/400 |
| `pf_9_cuadratico` | Punto fijo | train | debilitada | 3 | aprobado | ✓ | 400/400 |
| `pf_9c_cuadratico_medio` | Punto fijo | train | clasica | 3 | aprobado | ✓ | 400/400 |
| `newton_1_paso` | Newton | train | clasica | 4 | aprobado | ✓ | 400/400 |
| `newton_2_contraccion` | Newton | train | debilitada | 2 | aprobado | ✓ | 400/400 |
| `newton_2c_contraccion_local` | Newton | train | clasica | 4 | aprobado | ✓ | 400/400 |
| `newton_3_decaimiento` | Newton | train | debilitada | 2 | aprobado | ✓ | 400/400 |
| `newton_4_convergencia` | Newton | train | debilitada | 3 | aprobado | ✓ | 400/400 |
| `newton_4c_convergencia_local` | Newton | train | clasica | 4 | aprobado | ✓ | 400/400 |
| `newton_5_orden2` | Newton | train | debilitada | 3 | aprobado | ✓ | 400/400 |
| `newton_5c_orden2_local` | Newton | train | clasica | 4 | aprobado | ✓ | 400/400 |
| `orden_1_lineal` | Órdenes de convergencia | train | clasica | 1 | aprobado | ✓ | 400/400 |
| `orden_2_cuadratico_lineal` | Órdenes de convergencia | train | clasica | 2 | aprobado | ✓ | 400/400 |
| `orden_3_cuadratico` | Órdenes de convergencia | train | clasica | 2 | aprobado | ✓ | 400/400 |
| `secante_1_inyectiva` | Secante | test | clasica | 2 | aprobado | ✓ | 400/400 |
| `secante_2_cociente` | Secante | test | clasica | 2 | aprobado | ✓ | 400/400 |
| `secante_3_producto` | Secante | test | clasica | 5 | aprobado | ✓ | 400/400 |
| `secante_4_contraccion` | Secante | test | debilitada | 2 | aprobado | ✓ | 400/400 |
| `secante_4c_contraccion_local` | Secante | test | clasica | 4 | aprobado | ✓ | 400/400 |
| `secante_5_convergencia` | Secante | test | debilitada | 4 | aprobado | ✓ | 400/400 |
| `secante_5c_convergencia_local` | Secante | test | clasica | 5 | aprobado | ✓ | 400/400 |
| `secante_6_fibonacci` | Secante | test | debilitada | 4 | aprobado | ✓ | 400/400 |
| `secante_6c_orden_phi` | Secante | test | clasica | 5 | aprobado | ✓ | 17/17 |
| `rf_1_punto` | Regula falsi | test | clasica | 2 | aprobado | ✓ | 148/148 |
| `rf_2_signo` | Regula falsi | test | clasica | 2 | aprobado | ✓ | 400/400 |
| `rf_3_encaje` | Regula falsi | test | clasica | 3 | aprobado | ✓ | 400/400 |
| `rf_4_raiz` | Regula falsi | test | clasica | 3 | aprobado | ✓ | 400/400 |
| `rf_5_limites` | Regula falsi | test | clasica | 3 | aprobado | ✓ | 400/400 |
| `rf_6_convergencia` | Regula falsi | test | debilitada | 5 | aprobado | ✓ | 400/400 |
| `rf_6c_puntos_convergen` | Regula falsi | test | clasica | 5 | aprobado | ✓ | 392/392 |
| `newton_6c_q_orden2` | Newton | train | clasica | 5 | aprobado | ✓ | 20/20 |

## Bisección

Preludio (definiciones congeladas):

```isabelle
primrec biseccion :: "(real \<Rightarrow> real) \<Rightarrow> real \<Rightarrow> real \<Rightarrow> nat \<Rightarrow> real \<times> real" where
  "biseccion f a b 0 = (a, b)"
| "biseccion f a b (Suc n) = (case biseccion f a b n of (l, u) \<Rightarrow>
     (if f l * f ((l + u) / 2) \<le> 0 then (l, (l + u) / 2) else ((l + u) / 2, u)))"

definition punto_medio :: "(real \<Rightarrow> real) \<Rightarrow> real \<Rightarrow> real \<Rightarrow> nat \<Rightarrow> real" where
  "punto_medio f a b n = (fst (biseccion f a b n) + snd (biseccion f a b n)) / 2"
```

Lectura: biseccion f a b n es el par (aₙ, bₙ) tras n pasos: se parte en el punto medio m y se conserva [aₙ, m] si f(aₙ)·f(m) ≤ 0 (incluye f(m) = 0) y [m, bₙ] si no. punto_medio f a b n = (aₙ + bₙ)/2.

Hipótesis típicas: f : ℝ → ℝ, a, b reales (cada peldaño añade lo que necesita: a ≤ b, continuidad en [a, b], f(a)·f(b) ≤ 0).

### `bis_1_ancho` (train, dificultad 1)

**Versión clásica** (arrastra hipótesis que no usa: a ≤ b).

**Enunciado:** Tras n pasos, el intervalo mide (b − a)/2ⁿ.

```isabelle
fixes f :: "real \<Rightarrow> real" and a b :: real and n :: nat
assumes ab: "a \<le> b"
shows "snd (biseccion f a b n) - fst (biseccion f a b n) = (b - a) / 2 ^ n"
```

* Fuente: 01_biseccion (grafo), paso de longitudes.
* Referencia privada (nunca se muestra al proponente): ninguna.
* Supuestos dudosos: ninguno señalado.
* Comprobaciones: Isabelle ✓ (ejemplo de no vacuidad, en el orden de los fixes: (\<lambda>x::real. x), -1, 1, 0); numérica 400/400.
* Hash del enunciado: `72f3ced7066207f3`.

Estado: **aprobado** por Carlos (24 sep 2026).

### `bis_2_encaje` (train, dificultad 2)

**Versión clásica**.

**Enunciado:** Los intervalos están contenidos en [a, b], son no vacíos y encajados: aₙ ≤ aₙ₊₁ y bₙ₊₁ ≤ bₙ.

```isabelle
fixes f :: "real \<Rightarrow> real" and a b :: real and n :: nat
assumes ab: "a \<le> b"
shows "a \<le> fst (biseccion f a b n) \<and> fst (biseccion f a b n) \<le> snd (biseccion f a b n) \<and> snd (biseccion f a b n) \<le> b \<and> fst (biseccion f a b n) \<le> fst (biseccion f a b (Suc n)) \<and> snd (biseccion f a b (Suc n)) \<le> snd (biseccion f a b n)"
```

* Fuente: 01_biseccion (grafo). Depende de: `bis_1_ancho`.
* Referencia privada (nunca se muestra al proponente): ninguna.
* Supuestos dudosos: ninguno señalado.
* Comprobaciones: Isabelle ✓ (ejemplo de no vacuidad, en el orden de los fixes: (\<lambda>x::real. x), -1, 1, 0); numérica 400/400.
* Hash del enunciado: `200d5924aa258282`.

Estado: **aprobado** por Carlos (24 sep 2026).

### `bis_3_signo` (train, dificultad 2)

**Versión clásica**.

**Enunciado:** Invariante de signo: si f(a)·f(b) ≤ 0, entonces f(aₙ)·f(bₙ) ≤ 0 para todo n.

```isabelle
fixes f :: "real \<Rightarrow> real" and a b :: real and n :: nat
assumes signo: "f a * f b \<le> 0"
shows "f (fst (biseccion f a b n)) * f (snd (biseccion f a b n)) \<le> 0"
```

* Fuente: 01_biseccion (grafo).
* Referencia privada (nunca se muestra al proponente): ninguna.
* Supuestos dudosos: ninguno señalado.
* Comprobaciones: Isabelle ✓ (ejemplo de no vacuidad, en el orden de los fixes: (\<lambda>x::real. x), -1, 1, 0); numérica 400/400.
* Hash del enunciado: `d28609a35522482a`.

Estado: **aprobado** por Carlos (24 sep 2026).

### `bis_4_raiz` (train, dificultad 3)

**Versión clásica**.

**Enunciado:** Con f continua y f(a)·f(b) ≤ 0, cada intervalo [aₙ, bₙ] contiene una raíz (Bolzano).

```isabelle
fixes f :: "real \<Rightarrow> real" and a b :: real and n :: nat
assumes ab: "a \<le> b"
    and cont: "continuous_on {a..b} f"
    and signo: "f a * f b \<le> 0"
shows "\<exists>c. fst (biseccion f a b n) \<le> c \<and> c \<le> snd (biseccion f a b n) \<and> f c = 0"
```

* Fuente: 01_biseccion (grafo); artículo: Bolzanos_theorem. Depende de: `bis_2_encaje`, `bis_3_signo`.
* Referencia privada (nunca se muestra al proponente): Verified_Numerical_Methods/Numerical_Methods/Bisection.thy: Bolzanos_theorem.
* Supuestos dudosos: ninguno señalado.
* Comprobaciones: Isabelle ✓ (ejemplo de no vacuidad, en el orden de los fixes: (\<lambda>x::real. x), -1, 1, 0); numérica 400/400.
* Hash del enunciado: `dbcbd93d1d29a9b8`.

Estado: **aprobado** por Carlos (24 sep 2026).

### `bis_5_cota` (train, dificultad 3)

**Versión debilitada**: la raíz c puede depender de n; en la forma clásica es la misma c (el límite) para todo n. Versión clásica más fuerte: `bis_5c_cota_uniforme`.

**Enunciado:** Existe una raíz c en [a, b] con |mₙ − c| ≤ (b − a)/2ⁿ⁺¹ (la cota del teorema de 01).

```isabelle
fixes f :: "real \<Rightarrow> real" and a b :: real and n :: nat
assumes ab: "a \<le> b"
    and cont: "continuous_on {a..b} f"
    and signo: "f a * f b \<le> 0"
shows "\<exists>c. a \<le> c \<and> c \<le> b \<and> f c = 0 \<and> \<bar>punto_medio f a b n - c\<bar> \<le> (b - a) / 2 ^ Suc n"
```

* Fuente: 01_biseccion (teorema del grafo). Depende de: `bis_1_ancho`, `bis_4_raiz`.
* Referencia privada (nunca se muestra al proponente): Verified_Numerical_Methods/Numerical_Methods/Bisection.thy: bisect_root_extract (forma parecida).
* Supuestos dudosos: ninguno señalado.
* Comprobaciones: Isabelle ✓ (ejemplo de no vacuidad, en el orden de los fixes: (\<lambda>x::real. x), -1, 1, 0); numérica 400/400.
* Hash del enunciado: `667b74708f44cc0f`.

Estado: **aprobado** por Carlos (24 sep 2026).

### `bis_5c_cota_uniforme` (train, dificultad 3)

**Versión clásica** (más fuerte que `bis_5_cota`).

**Enunciado:** Existe una raíz c en [a, b] tal que, para todo n, |mₙ − c| ≤ (b − a)/2ⁿ⁺¹ (la misma c para todo n).

```isabelle
fixes f :: "real \<Rightarrow> real" and a b :: real
assumes ab: "a \<le> b"
    and cont: "continuous_on {a..b} f"
    and signo: "f a * f b \<le> 0"
shows "\<exists>c. a \<le> c \<and> c \<le> b \<and> f c = 0 \<and> (\<forall>n. \<bar>punto_medio f a b n - c\<bar> \<le> (b - a) / 2 ^ Suc n)"
```

* Fuente: 01_biseccion (teorema del grafo, forma clásica). Depende de: `bis_5_cota`, `bis_7_convergencia`.
* Referencia privada (nunca se muestra al proponente): ninguna.
* Supuestos dudosos: ninguno señalado.
* Comprobaciones: Isabelle ✓ (ejemplo de no vacuidad, en el orden de los fixes: (\<lambda>x::real. x), -1, 1); numérica 400/400.
* Hash del enunciado: `d9c2492ebc4cc93e`.

Estado: **aprobado** por Carlos (24 sep 2026).

### `bis_6_iteraciones` (train, dificultad 2)

**Versión clásica** (es la forma de libro: basta n ≥ log₂((b − a)/tol) (equivale a n ≥ ⌈log₂((b − a)/tol)⌉ porque n es natural)).

**Enunciado:** Si n ≥ log₂((b − a)/tol), el intervalo mide a lo sumo tol.

```isabelle
fixes f :: "real \<Rightarrow> real" and a b :: real and tol :: real and n :: nat
assumes ab: "a < b"
    and tol: "0 < tol"
shows "log 2 ((b - a) / tol) \<le> real n \<Longrightarrow> snd (biseccion f a b n) - fst (biseccion f a b n) \<le> tol"
```

* Fuente: 01_biseccion; artículo (iter = ⌈log₂((b − a)/tol)⌉). Depende de: `bis_1_ancho`.
* Referencia privada (nunca se muestra al proponente): ninguna.
* Supuestos dudosos: Es la condición suficiente con n real ≥ log₂(…); el artículo usa el techo exacto.
* Comprobaciones: Isabelle ✓ (ejemplo de no vacuidad, en el orden de los fixes: (\<lambda>x::real. x), -1, 1, 1, 0); numérica 400/400.
* Hash del enunciado: `2a4aaf1f50726074`.

Estado: **aprobado** por Carlos (24 sep 2026).

### `bis_7_convergencia` (train, dificultad 4)

**Versión clásica**.

**Enunciado:** Los puntos medios convergen a una raíz c de f en [a, b].

```isabelle
fixes f :: "real \<Rightarrow> real" and a b :: real
assumes ab: "a \<le> b"
    and cont: "continuous_on {a..b} f"
    and signo: "f a * f b \<le> 0"
shows "\<exists>c. a \<le> c \<and> c \<le> b \<and> f c = 0 \<and> (\<lambda>k. punto_medio f a b k) \<longlonglongrightarrow> c"
```

* Fuente: 01_biseccion (teorema del grafo). Depende de: `bis_1_ancho`, `bis_2_encaje`, `bis_3_signo`.
* Referencia privada (nunca se muestra al proponente): ninguna.
* Supuestos dudosos: ninguno señalado.
* Comprobaciones: Isabelle ✓ (ejemplo de no vacuidad, en el orden de los fixes: (\<lambda>x::real. x), -1, 1); numérica 400/400.
* Hash del enunciado: `6dc8d99eb7f0ac82`.

Estado: **aprobado** por Carlos (24 sep 2026).


## Punto fijo

Lectura: Sin definiciones nuevas: la iteración es (g ^^ n) x0, la n-ésima composición de g aplicada a x0.

Hipótesis típicas: g : [a, b] → [a, b] (dentro), k-contractiva en [a, b] con 0 ≤ k < 1 (contr), x0 ∈ [a, b].

### `pf_1_derivada` (train, dificultad 2)

**Versión clásica**.

**Enunciado:** Si |g'| ≤ k en [a, b], g es k-Lipschitz en [a, b] (valor medio).

```isabelle
fixes g g' :: "real \<Rightarrow> real" and a b k x y :: real
assumes ab: "a \<le> b"
    and deriv: "\<And>t. t \<in> {a..b} \<Longrightarrow> (g has_real_derivative g' t) (at t)"
    and cota: "\<And>t. t \<in> {a..b} \<Longrightarrow> \<bar>g' t\<bar> \<le> k"
    and hx: "x \<in> {a..b}"
    and hy: "y \<in> {a..b}"
shows "\<bar>g x - g y\<bar> \<le> k * \<bar>x - y\<bar>"
```

* Fuente: 02_punto_fijo; artículo: contractive_deriv_bound_closed.
* Referencia privada (nunca se muestra al proponente): Verified_Numerical_Methods/Numerical_Methods/Fixed_Point_Method.thy: contractive_deriv_bound_closed.
* Supuestos dudosos: ninguno señalado.
* Comprobaciones: Isabelle ✓ (ejemplo de no vacuidad, en el orden de los fixes: (\<lambda>x::real. x / 2), (\<lambda>x::real. 1 / 2), 0, 1, 1 / 2, 0, 1); numérica 400/400 (débil: solo compara los extremos del intervalo, no pares arbitrarios).
* Hash del enunciado: `9fc014edd38f84ee`.

Estado: **aprobado** por Carlos (24 sep 2026).

### `pf_2_dentro` (train, dificultad 1)

**Versión clásica** (arrastra hipótesis que no usa: la contracción (contr) y 0 ≤ k < 1).

**Enunciado:** Los iterados se quedan en [a, b].

```isabelle
fixes g :: "real \<Rightarrow> real" and a b k x0 :: real and n :: nat
assumes ab: "a \<le> b"
    and dentro: "\<And>x. x \<in> {a..b} \<Longrightarrow> g x \<in> {a..b}"
    and contr: "\<And>x y. x \<in> {a..b} \<Longrightarrow> y \<in> {a..b} \<Longrightarrow> \<bar>g x - g y\<bar> \<le> k * \<bar>x - y\<bar>"
    and k0: "0 \<le> k" and k1: "k < 1" and x0: "x0 \<in> {a..b}"
shows "(g ^^ n) x0 \<in> {a..b}"
```

* Fuente: 02_punto_fijo (grafo).
* Referencia privada (nunca se muestra al proponente): Fixed_Point_Method.thy: fpm_iters_in_cball (versión en bola).
* Supuestos dudosos: ninguno señalado.
* Comprobaciones: Isabelle ✓ (ejemplo de no vacuidad, en el orden de los fixes: (\<lambda>x::real. x / 2), 0, 1, 1 / 2, 1, 0); numérica 400/400.
* Hash del enunciado: `33fc1ed389b5a3fb`.

Estado: **aprobado** por Carlos (24 sep 2026).

### `pf_3_unicidad` (train, dificultad 2)

**Versión clásica** (arrastra hipótesis que no usa: x0 y la invariancia de [a, b] (dentro)).

**Enunciado:** Hay a lo sumo un punto fijo en [a, b].

```isabelle
fixes g :: "real \<Rightarrow> real" and a b k x0 :: real and p q :: real
assumes ab: "a \<le> b"
    and dentro: "\<And>x. x \<in> {a..b} \<Longrightarrow> g x \<in> {a..b}"
    and contr: "\<And>x y. x \<in> {a..b} \<Longrightarrow> y \<in> {a..b} \<Longrightarrow> \<bar>g x - g y\<bar> \<le> k * \<bar>x - y\<bar>"
    and k0: "0 \<le> k" and k1: "k < 1" and x0: "x0 \<in> {a..b}"
    and hp: "p \<in> {a..b}"
    and fp: "g p = p"
    and hq: "q \<in> {a..b}"
    and fq: "g q = q"
shows "p = q"
```

* Fuente: 02_punto_fijo (grafo).
* Referencia privada (nunca se muestra al proponente): ninguna.
* Supuestos dudosos: ninguno señalado.
* Comprobaciones: Isabelle ✓ (ejemplo de no vacuidad, en el orden de los fixes: (\<lambda>x::real. x / 2), 0, 1, 1 / 2, 1, 0, 0); numérica 400/400 (débil: solo comprueba que el punto hallado por iteración es fijo, no la unicidad).
* Hash del enunciado: `47498b0f668de5de`.

Estado: **aprobado** por Carlos (24 sep 2026).

### `pf_4_decaimiento` (train, dificultad 2)

**Versión clásica**.

**Enunciado:** |xₙ − p| ≤ kⁿ|x0 − p|.

```isabelle
fixes g :: "real \<Rightarrow> real" and a b k x0 :: real and p :: real and n :: nat
assumes ab: "a \<le> b"
    and dentro: "\<And>x. x \<in> {a..b} \<Longrightarrow> g x \<in> {a..b}"
    and contr: "\<And>x y. x \<in> {a..b} \<Longrightarrow> y \<in> {a..b} \<Longrightarrow> \<bar>g x - g y\<bar> \<le> k * \<bar>x - y\<bar>"
    and k0: "0 \<le> k" and k1: "k < 1" and x0: "x0 \<in> {a..b}"
    and hp: "p \<in> {a..b}"
    and fp: "g p = p"
shows "\<bar>(g ^^ n) x0 - p\<bar> \<le> k ^ n * \<bar>x0 - p\<bar>"
```

* Fuente: 02_punto_fijo; artículo: fpm_err_decay. Depende de: `pf_2_dentro`.
* Referencia privada (nunca se muestra al proponente): Fixed_Point_Method.thy: fpm_err_decay.
* Supuestos dudosos: ninguno señalado.
* Comprobaciones: Isabelle ✓ (ejemplo de no vacuidad, en el orden de los fixes: (\<lambda>x::real. x / 2), 0, 1, 1 / 2, 1, 0, 0); numérica 400/400.
* Hash del enunciado: `c4527a0b170707da`.

Estado: **aprobado** por Carlos (24 sep 2026).

### `pf_5_a_priori` (train, dificultad 2)

**Versión debilitada**: usa b − a en lugar de max(x0 − a, b − x0), que es más fina. Versión clásica más fuerte: `pf_5c_a_priori_max`.

**Enunciado:** Cota a priori: |xₙ − p| ≤ kⁿ(b − a).

```isabelle
fixes g :: "real \<Rightarrow> real" and a b k x0 :: real and p :: real and n :: nat
assumes ab: "a \<le> b"
    and dentro: "\<And>x. x \<in> {a..b} \<Longrightarrow> g x \<in> {a..b}"
    and contr: "\<And>x y. x \<in> {a..b} \<Longrightarrow> y \<in> {a..b} \<Longrightarrow> \<bar>g x - g y\<bar> \<le> k * \<bar>x - y\<bar>"
    and k0: "0 \<le> k" and k1: "k < 1" and x0: "x0 \<in> {a..b}"
    and hp: "p \<in> {a..b}"
    and fp: "g p = p"
shows "\<bar>(g ^^ n) x0 - p\<bar> \<le> k ^ n * (b - a)"
```

* Fuente: 02_punto_fijo (cota a priori, con b − a en lugar de max(x0 − a, b − x0)). Depende de: `pf_4_decaimiento`.
* Referencia privada (nunca se muestra al proponente): ninguna.
* Supuestos dudosos: 02 usa max(x0 − a, b − x0), que es más fina; aquí b − a.
* Comprobaciones: Isabelle ✓ (ejemplo de no vacuidad, en el orden de los fixes: (\<lambda>x::real. x / 2), 0, 1, 1 / 2, 1, 0, 0); numérica 400/400.
* Hash del enunciado: `565b7cd5ec98d5d4`.

Estado: **aprobado** por Carlos (24 sep 2026).

### `pf_5c_a_priori_max` (train, dificultad 2)

**Versión clásica** (más fuerte que `pf_5_a_priori`).

**Enunciado:** Cota a priori clásica: |xₙ − p| ≤ kⁿ·max(x0 − a, b − x0).

```isabelle
fixes g :: "real \<Rightarrow> real" and a b k x0 :: real and p :: real and n :: nat
assumes ab: "a \<le> b"
    and dentro: "\<And>x. x \<in> {a..b} \<Longrightarrow> g x \<in> {a..b}"
    and contr: "\<And>x y. x \<in> {a..b} \<Longrightarrow> y \<in> {a..b} \<Longrightarrow> \<bar>g x - g y\<bar> \<le> k * \<bar>x - y\<bar>"
    and k0: "0 \<le> k" and k1: "k < 1" and x0: "x0 \<in> {a..b}"
    and hp: "p \<in> {a..b}"
    and fp: "g p = p"
shows "\<bar>(g ^^ n) x0 - p\<bar> \<le> k ^ n * max (x0 - a) (b - x0)"
```

* Fuente: 02_punto_fijo (cota a priori del grafo). Depende de: `pf_4_decaimiento`.
* Referencia privada (nunca se muestra al proponente): ninguna.
* Supuestos dudosos: ninguno señalado.
* Comprobaciones: Isabelle ✓ (ejemplo de no vacuidad, en el orden de los fixes: (\<lambda>x::real. x / 2), 0, 1, 1 / 2, 1, 0, 0); numérica 400/400.
* Hash del enunciado: `f8156b4e0634d33e`.

Estado: **aprobado** por Carlos (24 sep 2026).

### `pf_6_a_priori_x1` (train, dificultad 3)

**Versión clásica**.

**Enunciado:** Cota a priori en función del primer paso: |xₙ − p| ≤ kⁿ/(1 − k)·|x1 − x0|.

```isabelle
fixes g :: "real \<Rightarrow> real" and a b k x0 :: real and p :: real and n :: nat
assumes ab: "a \<le> b"
    and dentro: "\<And>x. x \<in> {a..b} \<Longrightarrow> g x \<in> {a..b}"
    and contr: "\<And>x y. x \<in> {a..b} \<Longrightarrow> y \<in> {a..b} \<Longrightarrow> \<bar>g x - g y\<bar> \<le> k * \<bar>x - y\<bar>"
    and k0: "0 \<le> k" and k1: "k < 1" and x0: "x0 \<in> {a..b}"
    and hp: "p \<in> {a..b}"
    and fp: "g p = p"
shows "\<bar>(g ^^ n) x0 - p\<bar> \<le> k ^ n / (1 - k) * \<bar>g x0 - x0\<bar>"
```

* Fuente: 02_punto_fijo (el grafo la llama «a posteriori»; en la terminología usual es a priori: solo usa x0 y x1). Depende de: `pf_4_decaimiento`.
* Referencia privada (nunca se muestra al proponente): ninguna.
* Supuestos dudosos: ninguno señalado.
* Comprobaciones: Isabelle ✓ (ejemplo de no vacuidad, en el orden de los fixes: (\<lambda>x::real. x / 2), 0, 1, 1 / 2, 1, 0, 0); numérica 400/400.
* Hash del enunciado: `0184ccb814746f49`.

Estado: **aprobado** por Carlos (24 sep 2026).

### `pf_6p_a_posteriori` (train, dificultad 3)

**Versión clásica**.

**Enunciado:** Cota a posteriori (terminología usual): |xₙ − p| ≤ k/(1 − k)·|xₙ − xₙ₋₁| para n ≥ 1.

```isabelle
fixes g :: "real \<Rightarrow> real" and a b k x0 :: real and p :: real and n :: nat
assumes ab: "a \<le> b"
    and dentro: "\<And>x. x \<in> {a..b} \<Longrightarrow> g x \<in> {a..b}"
    and contr: "\<And>x y. x \<in> {a..b} \<Longrightarrow> y \<in> {a..b} \<Longrightarrow> \<bar>g x - g y\<bar> \<le> k * \<bar>x - y\<bar>"
    and k0: "0 \<le> k" and k1: "k < 1" and x0: "x0 \<in> {a..b}"
    and hp: "p \<in> {a..b}"
    and fp: "g p = p"
shows "\<bar>(g ^^ Suc n) x0 - p\<bar> \<le> k / (1 - k) * \<bar>(g ^^ Suc n) x0 - (g ^^ n) x0\<bar>"
```

* Fuente: terminología usual de la iteración de punto fijo; 02 no la incluye. Depende de: `pf_2_dentro`.
* Referencia privada (nunca se muestra al proponente): ninguna.
* Supuestos dudosos: Se escribe con Suc n para que valga desde n = 1 (xₙ₋₁ debe existir).
* Comprobaciones: Isabelle ✓ (ejemplo de no vacuidad, en el orden de los fixes: (\<lambda>x::real. x / 2), 0, 1, 1 / 2, 1, 0, 0); numérica 400/400.
* Hash del enunciado: `6feb8e8f5110ca65`.

Estado: **aprobado** por Carlos (24 sep 2026).

### `pf_7_existencia` (train, dificultad 3)

**Versión clásica** (arrastra hipótesis que no usa: x0).

**Enunciado:** g tiene un punto fijo en [a, b].

```isabelle
fixes g :: "real \<Rightarrow> real" and a b k x0 :: real
assumes ab: "a \<le> b"
    and dentro: "\<And>x. x \<in> {a..b} \<Longrightarrow> g x \<in> {a..b}"
    and contr: "\<And>x y. x \<in> {a..b} \<Longrightarrow> y \<in> {a..b} \<Longrightarrow> \<bar>g x - g y\<bar> \<le> k * \<bar>x - y\<bar>"
    and k0: "0 \<le> k" and k1: "k < 1" and x0: "x0 \<in> {a..b}"
shows "\<exists>p \<in> {a..b}. g p = p"
```

* Fuente: 02_punto_fijo; biblioteca: banach_fix.
* Referencia privada (nunca se muestra al proponente): ninguna.
* Supuestos dudosos: La biblioteca tiene banach_fix (espacios métricos completos); puede que el martillo lo cierre.
* Comprobaciones: Isabelle ✓ (ejemplo de no vacuidad, en el orden de los fixes: (\<lambda>x::real. x / 2), 0, 1, 1 / 2, 1); numérica 400/400.
* Hash del enunciado: `b920faa6953648bf`.

Estado: **aprobado** por Carlos (24 sep 2026).

### `pf_8_convergencia` (train, dificultad 4)

**Versión clásica**.

**Enunciado:** La iteración converge al punto fijo.

```isabelle
fixes g :: "real \<Rightarrow> real" and a b k x0 :: real
assumes ab: "a \<le> b"
    and dentro: "\<And>x. x \<in> {a..b} \<Longrightarrow> g x \<in> {a..b}"
    and contr: "\<And>x y. x \<in> {a..b} \<Longrightarrow> y \<in> {a..b} \<Longrightarrow> \<bar>g x - g y\<bar> \<le> k * \<bar>x - y\<bar>"
    and k0: "0 \<le> k" and k1: "k < 1" and x0: "x0 \<in> {a..b}"
shows "\<exists>p \<in> {a..b}. g p = p \<and> (\<lambda>n. (g ^^ n) x0) \<longlonglongrightarrow> p"
```

* Fuente: 02_punto_fijo (teorema del grafo). Depende de: `pf_7_existencia`, `pf_4_decaimiento`.
* Referencia privada (nunca se muestra al proponente): ninguna.
* Supuestos dudosos: ninguno señalado.
* Comprobaciones: Isabelle ✓ (ejemplo de no vacuidad, en el orden de los fixes: (\<lambda>x::real. x / 2), 0, 1, 1 / 2, 1); numérica 400/400 (débil: repite la cota a priori; la convergencia se sigue de ella).
* Hash del enunciado: `63018e59d510d346`.

Estado: **aprobado** por Carlos (24 sep 2026).

### `pf_9_cuadratico` (train, dificultad 3)

**Versión debilitada**: constante L en lugar de L/2: con el valor medio sale L; L/2 necesita un argumento de monotonía o integrar. Versión clásica más fuerte: `pf_9c_cuadratico_medio`.

**Enunciado:** Si |g'(t)| ≤ L|t − p| (en particular g'(p) = 0), un paso es cuadrático: |g(x) − p| ≤ L(x − p)².

```isabelle
fixes g g' :: "real \<Rightarrow> real" and a b p L x :: real
assumes ab: "a \<le> b"
    and hp: "p \<in> {a..b}"
    and fp: "g p = p"
    and deriv: "\<And>t. t \<in> {a..b} \<Longrightarrow> (g has_real_derivative g' t) (at t)"
    and cota: "\<And>t. t \<in> {a..b} \<Longrightarrow> \<bar>g' t\<bar> \<le> L * \<bar>t - p\<bar>"
    and hx: "x \<in> {a..b}"
shows "\<bar>g x - p\<bar> \<le> L * (x - p)\<^sup>2"
```

* Fuente: 02_punto_fijo; artículo: fpm_iter_quadratic_convergence (otra forma).
* Referencia privada (nunca se muestra al proponente): Fixed_Point_Method.thy: fpm_iter_quadratic_convergence (forma distinta).
* Supuestos dudosos: Constante L y no L/2: la versión con L/2 necesita integrar; con el valor medio sale L.
* Comprobaciones: Isabelle ✓ (ejemplo de no vacuidad, en el orden de los fixes: (\<lambda>x::real. 0), (\<lambda>x::real. 0), 0, 1, 0, 0, 0); numérica 400/400.
* Hash del enunciado: `7af30f59331129c7`.

Estado: **aprobado** por Carlos (24 sep 2026).

### `pf_9c_cuadratico_medio` (train, dificultad 3)

**Versión clásica** (más fuerte que `pf_9_cuadratico`).

**Enunciado:** Con la constante clásica: |g(x) − p| ≤ (L/2)(x − p)².

```isabelle
fixes g g' :: "real \<Rightarrow> real" and a b p L x :: real
assumes ab: "a \<le> b"
    and hp: "p \<in> {a..b}"
    and fp: "g p = p"
    and deriv: "\<And>t. t \<in> {a..b} \<Longrightarrow> (g has_real_derivative g' t) (at t)"
    and cota: "\<And>t. t \<in> {a..b} \<Longrightarrow> \<bar>g' t\<bar> \<le> L * \<bar>t - p\<bar>"
    and hx: "x \<in> {a..b}"
shows "\<bar>g x - p\<bar> \<le> L / 2 * (x - p)\<^sup>2"
```

* Fuente: 02_punto_fijo; análogo de Taylor con |g''| ≤ L. Depende de: `pf_9_cuadratico`.
* Referencia privada (nunca se muestra al proponente): ninguna.
* Supuestos dudosos: Sale por monotonía de g(t) − p ∓ (L/2)(t − p)² (o integrando); el valor medio solo da L.
* Comprobaciones: Isabelle ✓ (ejemplo de no vacuidad, en el orden de los fixes: (\<lambda>x::real. 0), (\<lambda>x::real. 0), 0, 1, 0, 0, 0); numérica 400/400.
* Hash del enunciado: `062c07466125b4cb`.

Estado: **aprobado** por Carlos (24 sep 2026).


## Newton

Preludio (definiciones congeladas):

```isabelle
definition paso_newton :: "(real \<Rightarrow> real) \<Rightarrow> (real \<Rightarrow> real) \<Rightarrow> real \<Rightarrow> real" where
  "paso_newton f f' x = x - f x / f' x"
```

Lectura: paso_newton f f' x = x − f(x)/f'(x). La iteración es (paso_newton f f' ^^ n) x0. En HOL, x/0 = 0; las hipótesis garantizan que f' no se anula cerca de la raíz.

Hipótesis típicas: En I = [r − δ, r + δ]: f derivable con derivada f', f' derivable con derivada f'' (dos veces derivable, no se pide f'' continua); f(r) = 0; m ≤ |f'| con m > 0; |f''| ≤ M; δ > 0 y M·δ ≤ m (δ pequeño: da el factor 1/2 de contracción).

### `newton_1_paso` (train, dificultad 4)

**Versión clásica** (arrastra hipótesis que no usa: M·δ ≤ m).

**Enunciado:** Error de un paso: |N(x) − r| ≤ M/(2m)·(x − r)² (Taylor con resto de Lagrange).

```isabelle
fixes f f' f'' :: "real \<Rightarrow> real" and r \<delta> m M :: real and x :: real
assumes d1: "\<And>t. \<bar>t - r\<bar> \<le> \<delta> \<Longrightarrow> (f has_real_derivative f' t) (at t)"
    and d2: "\<And>t. \<bar>t - r\<bar> \<le> \<delta> \<Longrightarrow> (f' has_real_derivative f'' t) (at t)"
    and raiz: "f r = 0" and m_pos: "0 < m"
    and cota1: "\<And>t. \<bar>t - r\<bar> \<le> \<delta> \<Longrightarrow> m \<le> \<bar>f' t\<bar>"
    and cota2: "\<And>t. \<bar>t - r\<bar> \<le> \<delta> \<Longrightarrow> \<bar>f'' t\<bar> \<le> M"
    and delta_pos: "0 < \<delta>" and delta_chico: "M * \<delta> \<le> m"
    and hx: "\<bar>x - r\<bar> \<le> \<delta>"
shows "\<bar>paso_newton f f' x - r\<bar> \<le> M / (2 * m) * (x - r)\<^sup>2"
```

* Fuente: 04_newton (grafo).
* Referencia privada (nunca se muestra al proponente): ninguna.
* Supuestos dudosos: Se pide f dos veces derivable en I, no f ∈ C²: el enunciado es un poco más fuerte que el de 04.
* Comprobaciones: Isabelle ✓ (ejemplo de no vacuidad, en el orden de los fixes: (\<lambda>x::real. x), (\<lambda>x::real. 1), (\<lambda>x::real. 0), 0, 1, 1, 0, 0); numérica 400/400.
* Hash del enunciado: `7ab6a41a7aba8fa7`.

Estado: **aprobado** por Carlos (24 sep 2026).

### `newton_2_contraccion` (train, dificultad 2)

**Versión debilitada**: δ fijo por M·δ ≤ m y cotas m, M dadas como hipótesis, en lugar de ∃δ a partir de f ∈ C² y f'(r) ≠ 0. Versión clásica más fuerte: `newton_2c_contraccion_local`.

**Enunciado:** Con M·δ ≤ m, un paso reduce el error al menos a la mitad (y el iterado se queda en I).

```isabelle
fixes f f' f'' :: "real \<Rightarrow> real" and r \<delta> m M :: real and x :: real
assumes d1: "\<And>t. \<bar>t - r\<bar> \<le> \<delta> \<Longrightarrow> (f has_real_derivative f' t) (at t)"
    and d2: "\<And>t. \<bar>t - r\<bar> \<le> \<delta> \<Longrightarrow> (f' has_real_derivative f'' t) (at t)"
    and raiz: "f r = 0" and m_pos: "0 < m"
    and cota1: "\<And>t. \<bar>t - r\<bar> \<le> \<delta> \<Longrightarrow> m \<le> \<bar>f' t\<bar>"
    and cota2: "\<And>t. \<bar>t - r\<bar> \<le> \<delta> \<Longrightarrow> \<bar>f'' t\<bar> \<le> M"
    and delta_pos: "0 < \<delta>" and delta_chico: "M * \<delta> \<le> m"
    and hx: "\<bar>x - r\<bar> \<le> \<delta>"
shows "\<bar>paso_newton f f' x - r\<bar> \<le> \<bar>x - r\<bar> / 2"
```

* Fuente: 04_newton. Depende de: `newton_1_paso`.
* Referencia privada (nunca se muestra al proponente): ninguna.
* Supuestos dudosos: ninguno señalado.
* Comprobaciones: Isabelle ✓ (ejemplo de no vacuidad, en el orden de los fixes: (\<lambda>x::real. x), (\<lambda>x::real. 1), (\<lambda>x::real. 0), 0, 1, 1, 0, 0); numérica 400/400.
* Hash del enunciado: `da20b8a35d3ee5f1`.

Estado: **aprobado** por Carlos (24 sep 2026).

### `newton_2c_contraccion_local` (train, dificultad 4)

**Versión clásica** (más fuerte que `newton_2_contraccion`).

**Enunciado:** Forma clásica local: existe δ > 0 tal que un paso de Newton reduce el error al menos a la mitad en [r − δ, r + δ].

```isabelle
fixes f f' f'' :: "real \<Rightarrow> real" and r \<epsilon> :: real
assumes eps: "0 < \<epsilon>"
    and d1: "\<And>t. \<bar>t - r\<bar> < \<epsilon> \<Longrightarrow> (f has_real_derivative f' t) (at t)"
    and d2: "\<And>t. \<bar>t - r\<bar> < \<epsilon> \<Longrightarrow> (f' has_real_derivative f'' t) (at t)"
    and c2: "continuous_on {r - \<epsilon><..<r + \<epsilon>} f''"
    and raiz: "f r = 0" and simple: "f' r \<noteq> 0"
shows "\<exists>\<delta>>0. \<forall>x. \<bar>x - r\<bar> \<le> \<delta> \<longrightarrow> \<bar>paso_newton f f' x - r\<bar> \<le> \<bar>x - r\<bar> / 2"
```

* Fuente: 04_newton (forma clásica). Depende de: `newton_2_contraccion`.
* Referencia privada (nunca se muestra al proponente): ninguna.
* Supuestos dudosos: ninguno señalado.
* Comprobaciones: Isabelle ✓ (ejemplo de no vacuidad, en el orden de los fixes: (\<lambda>x::real. x), (\<lambda>x::real. 1), (\<lambda>x::real. 0), 0, 1); numérica 400/400.
* Hash del enunciado: `ba97c50bb24868c3`.

Estado: **aprobado** por Carlos (24 sep 2026).

### `newton_3_decaimiento` (train, dificultad 2)

**Versión debilitada**: δ fijo (M·δ ≤ m); no tiene un enunciado clásico propio: su contenido clásico está en la convergencia local. Versión clásica más fuerte: `newton_4c_convergencia_local`.

**Enunciado:** |xₙ − r| ≤ δ/2ⁿ.

```isabelle
fixes f f' f'' :: "real \<Rightarrow> real" and r \<delta> m M :: real and x0 :: real and n :: nat
assumes d1: "\<And>t. \<bar>t - r\<bar> \<le> \<delta> \<Longrightarrow> (f has_real_derivative f' t) (at t)"
    and d2: "\<And>t. \<bar>t - r\<bar> \<le> \<delta> \<Longrightarrow> (f' has_real_derivative f'' t) (at t)"
    and raiz: "f r = 0" and m_pos: "0 < m"
    and cota1: "\<And>t. \<bar>t - r\<bar> \<le> \<delta> \<Longrightarrow> m \<le> \<bar>f' t\<bar>"
    and cota2: "\<And>t. \<bar>t - r\<bar> \<le> \<delta> \<Longrightarrow> \<bar>f'' t\<bar> \<le> M"
    and delta_pos: "0 < \<delta>" and delta_chico: "M * \<delta> \<le> m"
    and hx0: "\<bar>x0 - r\<bar> \<le> \<delta>"
shows "\<bar>(paso_newton f f' ^^ n) x0 - r\<bar> \<le> \<delta> / 2 ^ n"
```

* Fuente: 04_newton. Depende de: `newton_2_contraccion`.
* Referencia privada (nunca se muestra al proponente): ninguna.
* Supuestos dudosos: ninguno señalado.
* Comprobaciones: Isabelle ✓ (ejemplo de no vacuidad, en el orden de los fixes: (\<lambda>x::real. x), (\<lambda>x::real. 1), (\<lambda>x::real. 0), 0, 1, 1, 0, 0, 0); numérica 400/400.
* Hash del enunciado: `128ec3384c1032cc`.

Estado: **aprobado** por Carlos (24 sep 2026).

### `newton_4_convergencia` (train, dificultad 3)

**Versión debilitada**: δ fijo por M·δ ≤ m y cotas dadas, en lugar de ∃δ a partir de f ∈ C² y f'(r) ≠ 0. Versión clásica más fuerte: `newton_4c_convergencia_local`.

**Enunciado:** Newton converge a r desde todo x0 ∈ I.

```isabelle
fixes f f' f'' :: "real \<Rightarrow> real" and r \<delta> m M :: real and x0 :: real
assumes d1: "\<And>t. \<bar>t - r\<bar> \<le> \<delta> \<Longrightarrow> (f has_real_derivative f' t) (at t)"
    and d2: "\<And>t. \<bar>t - r\<bar> \<le> \<delta> \<Longrightarrow> (f' has_real_derivative f'' t) (at t)"
    and raiz: "f r = 0" and m_pos: "0 < m"
    and cota1: "\<And>t. \<bar>t - r\<bar> \<le> \<delta> \<Longrightarrow> m \<le> \<bar>f' t\<bar>"
    and cota2: "\<And>t. \<bar>t - r\<bar> \<le> \<delta> \<Longrightarrow> \<bar>f'' t\<bar> \<le> M"
    and delta_pos: "0 < \<delta>" and delta_chico: "M * \<delta> \<le> m"
    and hx0: "\<bar>x0 - r\<bar> \<le> \<delta>"
shows "(\<lambda>n. (paso_newton f f' ^^ n) x0) \<longlonglongrightarrow> r"
```

* Fuente: 04_newton (teorema del grafo). Depende de: `newton_3_decaimiento`.
* Referencia privada (nunca se muestra al proponente): ninguna.
* Supuestos dudosos: ninguno señalado.
* Comprobaciones: Isabelle ✓ (ejemplo de no vacuidad, en el orden de los fixes: (\<lambda>x::real. x), (\<lambda>x::real. 1), (\<lambda>x::real. 0), 0, 1, 1, 0, 0); numérica 400/400.
* Hash del enunciado: `f52d6b6a4b96dc23`.

Estado: **aprobado** por Carlos (24 sep 2026).

### `newton_4c_convergencia_local` (train, dificultad 4)

**Versión clásica** (más fuerte que `newton_3_decaimiento`, `newton_4_convergencia`).

**Enunciado:** Teorema clásico de convergencia local de Newton: existe δ > 0 tal que Newton converge a r desde todo x0 ∈ [r − δ, r + δ].

```isabelle
fixes f f' f'' :: "real \<Rightarrow> real" and r \<epsilon> :: real
assumes eps: "0 < \<epsilon>"
    and d1: "\<And>t. \<bar>t - r\<bar> < \<epsilon> \<Longrightarrow> (f has_real_derivative f' t) (at t)"
    and d2: "\<And>t. \<bar>t - r\<bar> < \<epsilon> \<Longrightarrow> (f' has_real_derivative f'' t) (at t)"
    and c2: "continuous_on {r - \<epsilon><..<r + \<epsilon>} f''"
    and raiz: "f r = 0" and simple: "f' r \<noteq> 0"
shows "\<exists>\<delta>>0. \<forall>x0. \<bar>x0 - r\<bar> \<le> \<delta> \<longrightarrow> (\<lambda>n. (paso_newton f f' ^^ n) x0) \<longlonglongrightarrow> r"
```

* Fuente: 04_newton (teorema del grafo, forma clásica). Depende de: `newton_4_convergencia`, `newton_2c_contraccion_local`.
* Referencia privada (nunca se muestra al proponente): ninguna.
* Supuestos dudosos: ninguno señalado.
* Comprobaciones: Isabelle ✓ (ejemplo de no vacuidad, en el orden de los fixes: (\<lambda>x::real. x), (\<lambda>x::real. 1), (\<lambda>x::real. 0), 0, 1); numérica 400/400.
* Hash del enunciado: `39a338884385067e`.

Estado: **aprobado** por Carlos (24 sep 2026).

### `newton_5_orden2` (train, dificultad 3)

**Versión debilitada**: δ fijo; forma explícita εₙ ≤ ε₀^(2ⁿ) en lugar de ∃δ ∃C con |eₙ₊₁| ≤ C eₙ². Versión clásica más fuerte: `newton_5c_orden2_local`.

**Enunciado:** Orden 2: con εₙ = M/(2m)|xₙ − r|, εₙ ≤ ε₀^(2ⁿ).

```isabelle
fixes f f' f'' :: "real \<Rightarrow> real" and r \<delta> m M :: real and x0 :: real and n :: nat
assumes d1: "\<And>t. \<bar>t - r\<bar> \<le> \<delta> \<Longrightarrow> (f has_real_derivative f' t) (at t)"
    and d2: "\<And>t. \<bar>t - r\<bar> \<le> \<delta> \<Longrightarrow> (f' has_real_derivative f'' t) (at t)"
    and raiz: "f r = 0" and m_pos: "0 < m"
    and cota1: "\<And>t. \<bar>t - r\<bar> \<le> \<delta> \<Longrightarrow> m \<le> \<bar>f' t\<bar>"
    and cota2: "\<And>t. \<bar>t - r\<bar> \<le> \<delta> \<Longrightarrow> \<bar>f'' t\<bar> \<le> M"
    and delta_pos: "0 < \<delta>" and delta_chico: "M * \<delta> \<le> m"
    and hx0: "\<bar>x0 - r\<bar> \<le> \<delta>"
shows "M / (2 * m) * \<bar>(paso_newton f f' ^^ n) x0 - r\<bar> \<le> (M / (2 * m) * \<bar>x0 - r\<bar>) ^ (2 ^ n)"
```

* Fuente: 04_newton (orden cuadrático). Depende de: `newton_1_paso`, `newton_3_decaimiento`.
* Referencia privada (nunca se muestra al proponente): ninguna.
* Supuestos dudosos: ninguno señalado.
* Comprobaciones: Isabelle ✓ (ejemplo de no vacuidad, en el orden de los fixes: (\<lambda>x::real. x), (\<lambda>x::real. 1), (\<lambda>x::real. 0), 0, 1, 1, 0, 0, 0); numérica 400/400.
* Hash del enunciado: `95bfa59d75f3a404`.

Estado: **aprobado** por Carlos (24 sep 2026).

### `newton_5c_orden2_local` (train, dificultad 4)

**Versión clásica** (más fuerte que `newton_5_orden2`).

**Enunciado:** Orden 2 clásico: existen δ > 0 y C con |xₙ₊₁ − r| ≤ C(xₙ − r)² para todo x0 ∈ [r − δ, r + δ] y todo n.

```isabelle
fixes f f' f'' :: "real \<Rightarrow> real" and r \<epsilon> :: real
assumes eps: "0 < \<epsilon>"
    and d1: "\<And>t. \<bar>t - r\<bar> < \<epsilon> \<Longrightarrow> (f has_real_derivative f' t) (at t)"
    and d2: "\<And>t. \<bar>t - r\<bar> < \<epsilon> \<Longrightarrow> (f' has_real_derivative f'' t) (at t)"
    and c2: "continuous_on {r - \<epsilon><..<r + \<epsilon>} f''"
    and raiz: "f r = 0" and simple: "f' r \<noteq> 0"
shows "\<exists>\<delta>>0. \<exists>C. \<forall>x0 n. \<bar>x0 - r\<bar> \<le> \<delta> \<longrightarrow> \<bar>(paso_newton f f' ^^ Suc n) x0 - r\<bar> \<le> C * ((paso_newton f f' ^^ n) x0 - r)\<^sup>2"
```

* Fuente: 04_newton (orden cuadrático, forma clásica). Depende de: `newton_5_orden2`, `newton_4c_convergencia_local`.
* Referencia privada (nunca se muestra al proponente): ninguna.
* Supuestos dudosos: ninguno señalado.
* Comprobaciones: Isabelle ✓ (ejemplo de no vacuidad, en el orden de los fixes: (\<lambda>x::real. x), (\<lambda>x::real. 1), (\<lambda>x::real. 0), 0, 1); numérica 400/400.
* Hash del enunciado: `8bc627f5b70c69f8`.

Estado: **aprobado** por Carlos (24 sep 2026).

### `newton_6c_q_orden2` (train, dificultad 5)

**Versión clásica**.

**Enunciado:** Q-orden 2 clásico: si ningún iterado cae en r, |eₙ₊₁|/eₙ² → |f''(r)/(2f'(r))| (análogo de secante_6c; si f''(r) = 0 el límite es 0).

```isabelle
fixes f f' f'' :: "real \<Rightarrow> real" and r \<epsilon> :: real
assumes eps: "0 < \<epsilon>"
    and d1: "\<And>t. \<bar>t - r\<bar> < \<epsilon> \<Longrightarrow> (f has_real_derivative f' t) (at t)"
    and d2: "\<And>t. \<bar>t - r\<bar> < \<epsilon> \<Longrightarrow> (f' has_real_derivative f'' t) (at t)"
    and c2: "continuous_on {r - \<epsilon><..<r + \<epsilon>} f''"
    and raiz: "f r = 0" and simple: "f' r \<noteq> 0"
shows "\<exists>\<delta>>0. \<forall>x0. \<bar>x0 - r\<bar> \<le> \<delta> \<longrightarrow> (\<forall>n. (paso_newton f f' ^^ n) x0 \<noteq> r) \<longrightarrow> (\<lambda>n. \<bar>(paso_newton f f' ^^ Suc n) x0 - r\<bar> / ((paso_newton f f' ^^ n) x0 - r)\<^sup>2) \<longlonglongrightarrow> \<bar>f'' r / (2 * f' r)\<bar>"
```

* Fuente: 04_newton (orden cuadrático, forma clásica del límite). Depende de: `newton_5c_orden2_local`, `newton_4c_convergencia_local`.
* Referencia privada (nunca se muestra al proponente): ninguna.
* Supuestos dudosos: Peldaño de dificultad 5 para train, propuesto a pedido de Carlos; sin f''(r) ≠ 0 el enunciado sigue siendo cierto con límite 0.
* Comprobaciones: Isabelle ✓ (ejemplo de no vacuidad, en el orden de los fixes: (\<lambda>x::real. x), (\<lambda>x::real. 1), (\<lambda>x::real. 0), 0, 1); numérica 20/20.
* Hash del enunciado: `7982410512a6e2da`.

Estado: **aprobado** por Carlos (24 sep 2026).


## Órdenes de convergencia

Lectura: Sin definiciones: e :: nat ⇒ real es una sucesión de errores cualquiera.

Hipótesis típicas: e es una sucesión real cualquiera con una recurrencia de cota (lineal o cuadrática).

### `orden_1_lineal` (train, dificultad 1)

**Versión clásica**.

**Enunciado:** Recurrencia lineal: |eₙ| ≤ cⁿ|e₀|.

```isabelle
fixes e :: "nat \<Rightarrow> real" and c :: real and n :: nat
assumes c0: "0 \<le> c"
    and paso: "\<And>j. \<bar>e (Suc j)\<bar> \<le> c * \<bar>e j\<bar>"
shows "\<bar>e n\<bar> \<le> c ^ n * \<bar>e 0\<bar>"
```

* Fuente: estándar.
* Referencia privada (nunca se muestra al proponente): ninguna.
* Supuestos dudosos: ninguno señalado.
* Comprobaciones: Isabelle ✓ (ejemplo de no vacuidad, en el orden de los fixes: (\<lambda>j::nat. 0::real), 0, 0); numérica 400/400.
* Hash del enunciado: `70d4ebc924a91b2c`.

Estado: **aprobado** por Carlos (24 sep 2026).

### `orden_2_cuadratico_lineal` (train, dificultad 2)

**Versión clásica**.

**Enunciado:** Si |eₙ₊₁| ≤ C eₙ² y C|e₀| ≤ 1/2, entonces |eₙ| ≤ |e₀|/2ⁿ.

```isabelle
fixes e :: "nat \<Rightarrow> real" and C :: real and n :: nat
assumes C0: "0 \<le> C"
    and paso: "\<And>j. \<bar>e (Suc j)\<bar> \<le> C * (e j)\<^sup>2"
    and inicio: "C * \<bar>e 0\<bar> \<le> 1 / 2"
shows "\<bar>e n\<bar> \<le> \<bar>e 0\<bar> / 2 ^ n"
```

* Fuente: estándar. Depende de: `orden_1_lineal`.
* Referencia privada (nunca se muestra al proponente): ninguna.
* Supuestos dudosos: ninguno señalado.
* Comprobaciones: Isabelle ✓ (ejemplo de no vacuidad, en el orden de los fixes: (\<lambda>j::nat. 0::real), 0, 0); numérica 400/400.
* Hash del enunciado: `16338255825007e9`.

Estado: **aprobado** por Carlos (24 sep 2026).

### `orden_3_cuadratico` (train, dificultad 2)

**Versión clásica**.

**Enunciado:** Si |eₙ₊₁| ≤ C eₙ², entonces C|eₙ| ≤ (C|e₀|)^(2ⁿ).

```isabelle
fixes e :: "nat \<Rightarrow> real" and C :: real and n :: nat
assumes C0: "0 \<le> C"
    and paso: "\<And>j. \<bar>e (Suc j)\<bar> \<le> C * (e j)\<^sup>2"
shows "C * \<bar>e n\<bar> \<le> (C * \<bar>e 0\<bar>) ^ (2 ^ n)"
```

* Fuente: estándar.
* Referencia privada (nunca se muestra al proponente): ninguna.
* Supuestos dudosos: ninguno señalado.
* Comprobaciones: Isabelle ✓ (ejemplo de no vacuidad, en el orden de los fixes: (\<lambda>j::nat. 0::real), 0, 0); numérica 400/400.
* Hash del enunciado: `ac75fa4b77147121`.

Estado: **aprobado** por Carlos (24 sep 2026).


## Secante

Preludio (definiciones congeladas):

```isabelle
definition paso_secante :: "(real \<Rightarrow> real) \<Rightarrow> real \<Rightarrow> real \<Rightarrow> real" where
  "paso_secante f x y = y - f y * (y - x) / (f y - f x)"

fun secante :: "(real \<Rightarrow> real) \<Rightarrow> real \<Rightarrow> real \<Rightarrow> nat \<Rightarrow> real" where
  "secante f x0 x1 0 = x0"
| "secante f x0 x1 (Suc 0) = x1"
| "secante f x0 x1 (Suc (Suc n)) = paso_secante f (secante f x0 x1 n) (secante f x0 x1 (Suc n))"

fun fibo :: "nat \<Rightarrow> nat" where
  "fibo 0 = 0"
| "fibo (Suc 0) = 1"
| "fibo (Suc (Suc n)) = fibo (Suc n) + fibo n"
```

Lectura: paso_secante f x y = y − f(y)(y − x)/(f(y) − f(x)) (x es el iterado anterior, y el actual). secante f x0 x1 n es xₙ. fibo es la sucesión de Fibonacci (fibo 0 = 0, fibo 1 = 1). En HOL, x/0 = 0.

Hipótesis típicas: Las mismas de Newton: en I = [r − δ, r + δ], f dos veces derivable, f(r) = 0, m ≤ |f'|, |f''| ≤ M, M·δ ≤ m.

### `secante_1_inyectiva` (test, dificultad 2)

**Versión clásica** (arrastra hipótesis que no usa: f'' y su cota, M·δ ≤ m).

**Enunciado:** En I, f es inyectiva (|f'| ≥ m > 0): el paso de la secante está bien definido.

```isabelle
fixes f f' f'' :: "real \<Rightarrow> real" and r \<delta> m M :: real and x y :: real
assumes d1: "\<And>t. \<bar>t - r\<bar> \<le> \<delta> \<Longrightarrow> (f has_real_derivative f' t) (at t)"
    and d2: "\<And>t. \<bar>t - r\<bar> \<le> \<delta> \<Longrightarrow> (f' has_real_derivative f'' t) (at t)"
    and raiz: "f r = 0" and m_pos: "0 < m"
    and cota1: "\<And>t. \<bar>t - r\<bar> \<le> \<delta> \<Longrightarrow> m \<le> \<bar>f' t\<bar>"
    and cota2: "\<And>t. \<bar>t - r\<bar> \<le> \<delta> \<Longrightarrow> \<bar>f'' t\<bar> \<le> M"
    and delta_pos: "0 < \<delta>" and delta_chico: "M * \<delta> \<le> m"
    and hx: "\<bar>x - r\<bar> \<le> \<delta>"
    and hy: "\<bar>y - r\<bar> \<le> \<delta>"
    and dist: "x \<noteq> y"
shows "f x \<noteq> f y"
```

* Fuente: 05_secante (grafo).
* Referencia privada (nunca se muestra al proponente): ninguna.
* Supuestos dudosos: ninguno señalado.
* Comprobaciones: Isabelle ✓ (ejemplo de no vacuidad, en el orden de los fixes: (\<lambda>x::real. x), (\<lambda>x::real. 1), (\<lambda>x::real. 0), 0, 1, 1, 0, 0, 1 / 2); numérica 400/400.
* Hash del enunciado: `e299c647a2092728`.

Estado: **aprobado** por Carlos (24 sep 2026).

### `secante_2_cociente` (test, dificultad 2)

**Versión clásica** (arrastra hipótesis que no usa: f'' y su cota, M·δ ≤ m).

**Enunciado:** El cociente de diferencias en I está acotado por abajo por m.

```isabelle
fixes f f' f'' :: "real \<Rightarrow> real" and r \<delta> m M :: real and x y :: real
assumes d1: "\<And>t. \<bar>t - r\<bar> \<le> \<delta> \<Longrightarrow> (f has_real_derivative f' t) (at t)"
    and d2: "\<And>t. \<bar>t - r\<bar> \<le> \<delta> \<Longrightarrow> (f' has_real_derivative f'' t) (at t)"
    and raiz: "f r = 0" and m_pos: "0 < m"
    and cota1: "\<And>t. \<bar>t - r\<bar> \<le> \<delta> \<Longrightarrow> m \<le> \<bar>f' t\<bar>"
    and cota2: "\<And>t. \<bar>t - r\<bar> \<le> \<delta> \<Longrightarrow> \<bar>f'' t\<bar> \<le> M"
    and delta_pos: "0 < \<delta>" and delta_chico: "M * \<delta> \<le> m"
    and hx: "\<bar>x - r\<bar> \<le> \<delta>"
    and hy: "\<bar>y - r\<bar> \<le> \<delta>"
    and dist: "x \<noteq> y"
shows "m \<le> \<bar>(f y - f x) / (y - x)\<bar>"
```

* Fuente: 05_secante (grafo). Depende de: `secante_1_inyectiva`.
* Referencia privada (nunca se muestra al proponente): ninguna.
* Supuestos dudosos: ninguno señalado.
* Comprobaciones: Isabelle ✓ (ejemplo de no vacuidad, en el orden de los fixes: (\<lambda>x::real. x), (\<lambda>x::real. 1), (\<lambda>x::real. 0), 0, 1, 1, 0, 0, 1 / 2); numérica 400/400.
* Hash del enunciado: `74c64b83dea2bcae`.

Estado: **aprobado** por Carlos (24 sep 2026).

### `secante_3_producto` (test, dificultad 5)

**Versión clásica** (arrastra hipótesis que no usa: M·δ ≤ m).

**Enunciado:** Cota producto: |S(x, y) − r| ≤ M/(2m)·|x − r|·|y − r| (diferencias divididas).

```isabelle
fixes f f' f'' :: "real \<Rightarrow> real" and r \<delta> m M :: real and x y :: real
assumes d1: "\<And>t. \<bar>t - r\<bar> \<le> \<delta> \<Longrightarrow> (f has_real_derivative f' t) (at t)"
    and d2: "\<And>t. \<bar>t - r\<bar> \<le> \<delta> \<Longrightarrow> (f' has_real_derivative f'' t) (at t)"
    and raiz: "f r = 0" and m_pos: "0 < m"
    and cota1: "\<And>t. \<bar>t - r\<bar> \<le> \<delta> \<Longrightarrow> m \<le> \<bar>f' t\<bar>"
    and cota2: "\<And>t. \<bar>t - r\<bar> \<le> \<delta> \<Longrightarrow> \<bar>f'' t\<bar> \<le> M"
    and delta_pos: "0 < \<delta>" and delta_chico: "M * \<delta> \<le> m"
    and hx: "\<bar>x - r\<bar> \<le> \<delta>"
    and hy: "\<bar>y - r\<bar> \<le> \<delta>"
    and dist: "x \<noteq> y"
shows "\<bar>paso_secante f x y - r\<bar> \<le> M / (2 * m) * \<bar>x - r\<bar> * \<bar>y - r\<bar>"
```

* Fuente: 05_secante (teorema del grafo). Depende de: `secante_2_cociente`.
* Referencia privada (nunca se muestra al proponente): ninguna.
* Supuestos dudosos: ninguno señalado.
* Comprobaciones: Isabelle ✓ (ejemplo de no vacuidad, en el orden de los fixes: (\<lambda>x::real. x), (\<lambda>x::real. 1), (\<lambda>x::real. 0), 0, 1, 1, 0, 0, 1 / 2); numérica 400/400.
* Hash del enunciado: `ed42cd1f08abc301`.

Estado: **aprobado** por Carlos (24 sep 2026).

### `secante_4_contraccion` (test, dificultad 2)

**Versión debilitada**: δ fijo (M·δ ≤ m) y cotas dadas, en lugar de ∃δ. Versión clásica más fuerte: `secante_4c_contraccion_local`.

**Enunciado:** Con M·δ ≤ m, un paso de la secante reduce el error del iterado actual al menos a la mitad.

```isabelle
fixes f f' f'' :: "real \<Rightarrow> real" and r \<delta> m M :: real and x y :: real
assumes d1: "\<And>t. \<bar>t - r\<bar> \<le> \<delta> \<Longrightarrow> (f has_real_derivative f' t) (at t)"
    and d2: "\<And>t. \<bar>t - r\<bar> \<le> \<delta> \<Longrightarrow> (f' has_real_derivative f'' t) (at t)"
    and raiz: "f r = 0" and m_pos: "0 < m"
    and cota1: "\<And>t. \<bar>t - r\<bar> \<le> \<delta> \<Longrightarrow> m \<le> \<bar>f' t\<bar>"
    and cota2: "\<And>t. \<bar>t - r\<bar> \<le> \<delta> \<Longrightarrow> \<bar>f'' t\<bar> \<le> M"
    and delta_pos: "0 < \<delta>" and delta_chico: "M * \<delta> \<le> m"
    and hx: "\<bar>x - r\<bar> \<le> \<delta>"
    and hy: "\<bar>y - r\<bar> \<le> \<delta>"
    and dist: "x \<noteq> y"
shows "\<bar>paso_secante f x y - r\<bar> \<le> \<bar>y - r\<bar> / 2"
```

* Fuente: 05_secante. Depende de: `secante_3_producto`.
* Referencia privada (nunca se muestra al proponente): ninguna.
* Supuestos dudosos: ninguno señalado.
* Comprobaciones: Isabelle ✓ (ejemplo de no vacuidad, en el orden de los fixes: (\<lambda>x::real. x), (\<lambda>x::real. 1), (\<lambda>x::real. 0), 0, 1, 1, 0, 0, 1 / 2); numérica 400/400.
* Hash del enunciado: `a587e99ea12f6920`.

Estado: **aprobado** por Carlos (24 sep 2026).

### `secante_4c_contraccion_local` (test, dificultad 4)

**Versión clásica** (más fuerte que `secante_4_contraccion`).

**Enunciado:** Forma clásica local: existe δ > 0 tal que un paso de la secante con x ≠ y en [r − δ, r + δ] reduce a la mitad el error del iterado actual.

```isabelle
fixes f f' f'' :: "real \<Rightarrow> real" and r \<epsilon> :: real
assumes eps: "0 < \<epsilon>"
    and d1: "\<And>t. \<bar>t - r\<bar> < \<epsilon> \<Longrightarrow> (f has_real_derivative f' t) (at t)"
    and d2: "\<And>t. \<bar>t - r\<bar> < \<epsilon> \<Longrightarrow> (f' has_real_derivative f'' t) (at t)"
    and c2: "continuous_on {r - \<epsilon><..<r + \<epsilon>} f''"
    and raiz: "f r = 0" and simple: "f' r \<noteq> 0"
shows "\<exists>\<delta>>0. \<forall>x y. \<bar>x - r\<bar> \<le> \<delta> \<longrightarrow> \<bar>y - r\<bar> \<le> \<delta> \<longrightarrow> x \<noteq> y \<longrightarrow> \<bar>paso_secante f x y - r\<bar> \<le> \<bar>y - r\<bar> / 2"
```

* Fuente: 05_secante (forma clásica). Depende de: `secante_4_contraccion`.
* Referencia privada (nunca se muestra al proponente): ninguna.
* Supuestos dudosos: ninguno señalado.
* Comprobaciones: Isabelle ✓ (ejemplo de no vacuidad, en el orden de los fixes: (\<lambda>x::real. x), (\<lambda>x::real. 1), (\<lambda>x::real. 0), 0, 1); numérica 400/400.
* Hash del enunciado: `baba05a3a8a62465`.

Estado: **aprobado** por Carlos (24 sep 2026).

### `secante_5_convergencia` (test, dificultad 4)

**Versión debilitada**: δ fijo (M·δ ≤ m) y cotas dadas, en lugar de ∃δ. Versión clásica más fuerte: `secante_5c_convergencia_local`.

**Enunciado:** La secante converge a r desde x0 ≠ x1 en I.

```isabelle
fixes f f' f'' :: "real \<Rightarrow> real" and r \<delta> m M :: real and x0 x1 :: real
assumes d1: "\<And>t. \<bar>t - r\<bar> \<le> \<delta> \<Longrightarrow> (f has_real_derivative f' t) (at t)"
    and d2: "\<And>t. \<bar>t - r\<bar> \<le> \<delta> \<Longrightarrow> (f' has_real_derivative f'' t) (at t)"
    and raiz: "f r = 0" and m_pos: "0 < m"
    and cota1: "\<And>t. \<bar>t - r\<bar> \<le> \<delta> \<Longrightarrow> m \<le> \<bar>f' t\<bar>"
    and cota2: "\<And>t. \<bar>t - r\<bar> \<le> \<delta> \<Longrightarrow> \<bar>f'' t\<bar> \<le> M"
    and delta_pos: "0 < \<delta>" and delta_chico: "M * \<delta> \<le> m"
    and hx0: "\<bar>x0 - r\<bar> \<le> \<delta>"
    and hx1: "\<bar>x1 - r\<bar> \<le> \<delta>"
    and dist: "x0 \<noteq> x1"
shows "(\<lambda>n. secante f x0 x1 n) \<longlonglongrightarrow> r"
```

* Fuente: 05_secante (teorema del grafo). Depende de: `secante_4_contraccion`.
* Referencia privada (nunca se muestra al proponente): ninguna.
* Supuestos dudosos: Si un iterado cae en r, los siguientes quedan en r (en HOL, 0/0 = 0); el enunciado lo cubre.
* Comprobaciones: Isabelle ✓ (ejemplo de no vacuidad, en el orden de los fixes: (\<lambda>x::real. x), (\<lambda>x::real. 1), (\<lambda>x::real. 0), 0, 1, 1, 0, 0, 1 / 2); numérica 400/400.
* Hash del enunciado: `02eff1afa4180646`.

Estado: **aprobado** por Carlos (24 sep 2026).

### `secante_5c_convergencia_local` (test, dificultad 5)

**Versión clásica** (más fuerte que `secante_5_convergencia`).

**Enunciado:** Teorema clásico de convergencia local de la secante: existe δ > 0 tal que converge desde todo x0 ≠ x1 en [r − δ, r + δ].

```isabelle
fixes f f' f'' :: "real \<Rightarrow> real" and r \<epsilon> :: real
assumes eps: "0 < \<epsilon>"
    and d1: "\<And>t. \<bar>t - r\<bar> < \<epsilon> \<Longrightarrow> (f has_real_derivative f' t) (at t)"
    and d2: "\<And>t. \<bar>t - r\<bar> < \<epsilon> \<Longrightarrow> (f' has_real_derivative f'' t) (at t)"
    and c2: "continuous_on {r - \<epsilon><..<r + \<epsilon>} f''"
    and raiz: "f r = 0" and simple: "f' r \<noteq> 0"
shows "\<exists>\<delta>>0. \<forall>x0 x1. \<bar>x0 - r\<bar> \<le> \<delta> \<longrightarrow> \<bar>x1 - r\<bar> \<le> \<delta> \<longrightarrow> x0 \<noteq> x1 \<longrightarrow> (\<lambda>n. secante f x0 x1 n) \<longlonglongrightarrow> r"
```

* Fuente: 05_secante (teorema del grafo, forma clásica). Depende de: `secante_5_convergencia`, `secante_4c_contraccion_local`.
* Referencia privada (nunca se muestra al proponente): ninguna.
* Supuestos dudosos: ninguno señalado.
* Comprobaciones: Isabelle ✓ (ejemplo de no vacuidad, en el orden de los fixes: (\<lambda>x::real. x), (\<lambda>x::real. 1), (\<lambda>x::real. 0), 0, 1); numérica 400/400.
* Hash del enunciado: `9fe9e716a4249f7f`.

Estado: **aprobado** por Carlos (24 sep 2026).

### `secante_6_fibonacci` (test, dificultad 4)

**Versión debilitada**: δ fijo, y el orden φ como cota con exponentes de Fibonacci (R-orden) en lugar del límite del cociente |eₙ₊₁|/|eₙ|^φ (Q-orden). Versión clásica más fuerte: `secante_6c_orden_phi`.

**Enunciado:** Orden φ en forma explícita: M/(2m)|xₙ − r| ≤ (1/2)^F(n+1), con F de Fibonacci (F(n) ~ φⁿ/√5).

```isabelle
fixes f f' f'' :: "real \<Rightarrow> real" and r \<delta> m M :: real and x0 x1 :: real and n :: nat
assumes d1: "\<And>t. \<bar>t - r\<bar> \<le> \<delta> \<Longrightarrow> (f has_real_derivative f' t) (at t)"
    and d2: "\<And>t. \<bar>t - r\<bar> \<le> \<delta> \<Longrightarrow> (f' has_real_derivative f'' t) (at t)"
    and raiz: "f r = 0" and m_pos: "0 < m"
    and cota1: "\<And>t. \<bar>t - r\<bar> \<le> \<delta> \<Longrightarrow> m \<le> \<bar>f' t\<bar>"
    and cota2: "\<And>t. \<bar>t - r\<bar> \<le> \<delta> \<Longrightarrow> \<bar>f'' t\<bar> \<le> M"
    and delta_pos: "0 < \<delta>" and delta_chico: "M * \<delta> \<le> m"
    and hx0: "\<bar>x0 - r\<bar> \<le> \<delta>"
    and hx1: "\<bar>x1 - r\<bar> \<le> \<delta>"
    and dist: "x0 \<noteq> x1"
shows "M / (2 * m) * \<bar>secante f x0 x1 n - r\<bar> \<le> (1 / 2) ^ fibo (Suc n)"
```

* Fuente: 05_secante (orden φ). Depende de: `secante_3_producto`.
* Referencia privada (nunca se muestra al proponente): ninguna.
* Supuestos dudosos: Codifica el orden φ con exponentes de Fibonacci en lugar de un límite de cocientes. Fibonacci del preludio: fibo 0 = 0, fibo 1 = 1, fibo (n + 2) = fibo (n + 1) + fibo n; la cota de xₙ usa fibo (n + 1): 1, 1, 2, 3, 5, 8, … para n = 0, 1, 2, 3, 4, 5, ….
* Comprobaciones: Isabelle ✓ (ejemplo de no vacuidad, en el orden de los fixes: (\<lambda>x::real. x), (\<lambda>x::real. 1), (\<lambda>x::real. 0), 0, 1, 1, 0, 0, 1 / 2, 0); numérica 400/400.
* Hash del enunciado: `6c5dbec184863675`.

Estado: **aprobado** por Carlos (24 sep 2026).

### `secante_6c_orden_phi` (test, dificultad 5)

**Versión clásica** (más fuerte que `secante_6_fibonacci`).

**Enunciado:** Orden φ clásico (Q-orden): si f''(r) ≠ 0 y ningún iterado cae en r, |eₙ₊₁|/|eₙ|^φ → |f''(r)/(2f'(r))|^(φ−1), con φ = (1 + √5)/2.

```isabelle
fixes f f' f'' :: "real \<Rightarrow> real" and r \<epsilon> :: real
assumes eps: "0 < \<epsilon>"
    and d1: "\<And>t. \<bar>t - r\<bar> < \<epsilon> \<Longrightarrow> (f has_real_derivative f' t) (at t)"
    and d2: "\<And>t. \<bar>t - r\<bar> < \<epsilon> \<Longrightarrow> (f' has_real_derivative f'' t) (at t)"
    and c2: "continuous_on {r - \<epsilon><..<r + \<epsilon>} f''"
    and raiz: "f r = 0" and simple: "f' r \<noteq> 0"
    and curva: "f'' r \<noteq> 0"
shows "\<exists>\<delta>>0. \<forall>x0 x1. \<bar>x0 - r\<bar> \<le> \<delta> \<longrightarrow> \<bar>x1 - r\<bar> \<le> \<delta> \<longrightarrow> x0 \<noteq> x1 \<longrightarrow> (\<forall>n. secante f x0 x1 n \<noteq> r) \<longrightarrow> (\<lambda>n. \<bar>secante f x0 x1 (Suc n) - r\<bar> / \<bar>secante f x0 x1 n - r\<bar> powr ((1 + sqrt 5) / 2)) \<longlonglongrightarrow> \<bar>f'' r / (2 * f' r)\<bar> powr ((1 + sqrt 5) / 2 - 1)"
```

* Fuente: 05_secante (orden φ, forma clásica). Depende de: `secante_6_fibonacci`, `secante_5c_convergencia_local`.
* Referencia privada (nunca se muestra al proponente): ninguna.
* Supuestos dudosos: Es el resultado clásico sobre el límite del cociente; exige f''(r) ≠ 0 (si no, el orden es mayor) y que ningún iterado sea exactamente r.
* Comprobaciones: Isabelle ✓ (ejemplo de no vacuidad, en el orden de los fixes: (\<lambda>x::real. x + x * x), (\<lambda>x::real. 1 + 2 * x), (\<lambda>x::real. 2), 0, 1 / 4); numérica 17/17.
* Hash del enunciado: `507e735cea27d7e4`.

Estado: **aprobado** por Carlos (24 sep 2026).


## Regula falsi

Preludio (definiciones congeladas):

```isabelle
definition punto_rf :: "(real \<Rightarrow> real) \<Rightarrow> real \<Rightarrow> real \<Rightarrow> real" where
  "punto_rf f l u = (l * f u - u * f l) / (f u - f l)"

primrec regula_falsi :: "(real \<Rightarrow> real) \<Rightarrow> real \<Rightarrow> real \<Rightarrow> nat \<Rightarrow> real \<times> real" where
  "regula_falsi f a b 0 = (a, b)"
| "regula_falsi f a b (Suc n) = (case regula_falsi f a b n of (l, u) \<Rightarrow>
     (if f l * f (punto_rf f l u) \<le> 0 then (l, punto_rf f l u) else (punto_rf f l u, u)))"
```

Lectura: punto_rf f l u = (l·f(u) − u·f(l))/(f(u) − f(l)), el cero de la secante entre (l, f(l)) y (u, f(u)). regula_falsi f a b n es el par (lₙ, uₙ); se conserva [lₙ, c] si f(lₙ)·f(c) ≤ 0 y [c, uₙ] si no.

Hipótesis típicas: a < b, f(a) < 0 < f(b) (orientación fija, sin pérdida de generalidad), f continua en [a, b].

### `rf_1_punto` (test, dificultad 2)

**Versión clásica**.

**Enunciado:** Si l < u y f(l) < 0 ≤ f(u), el punto de falsa posición cae en (l, u].

```isabelle
fixes f :: "real \<Rightarrow> real" and l u :: real
assumes lu: "l < u"
    and fl: "f l < 0"
    and fu: "0 \<le> f u"
shows "l < punto_rf f l u \<and> punto_rf f l u \<le> u"
```

* Fuente: estándar (regula falsi).
* Referencia privada (nunca se muestra al proponente): ninguna.
* Supuestos dudosos: ninguno señalado.
* Comprobaciones: Isabelle ✓ (ejemplo de no vacuidad, en el orden de los fixes: (\<lambda>x::real. x), -1, 1); numérica 148/148.
* Hash del enunciado: `4c9e7c3f1e897b52`.

Estado: **aprobado** por Carlos (24 sep 2026).

### `rf_2_signo` (test, dificultad 2)

**Versión clásica**.

**Enunciado:** Invariante de signo: f(lₙ) < 0 ≤ f(uₙ).

```isabelle
fixes f :: "real \<Rightarrow> real" and a b :: real and n :: nat
assumes fa: "f a < 0"
    and fb: "0 < f b"
shows "f (fst (regula_falsi f a b n)) < 0 \<and> 0 \<le> f (snd (regula_falsi f a b n))"
```

* Fuente: estándar (regula falsi).
* Referencia privada (nunca se muestra al proponente): ninguna.
* Supuestos dudosos: ninguno señalado.
* Comprobaciones: Isabelle ✓ (ejemplo de no vacuidad, en el orden de los fixes: (\<lambda>x::real. x), -1, 1, 0); numérica 400/400.
* Hash del enunciado: `0388da3956126023`.

Estado: **aprobado** por Carlos (24 sep 2026).

### `rf_3_encaje` (test, dificultad 3)

**Versión clásica**.

**Enunciado:** Horquillas encajadas no degeneradas: a ≤ lₙ < uₙ ≤ b, lₙ ≤ lₙ₊₁, uₙ₊₁ ≤ uₙ.

```isabelle
fixes f :: "real \<Rightarrow> real" and a b :: real and n :: nat
assumes ab: "a < b"
    and fa: "f a < 0"
    and fb: "0 < f b"
shows "a \<le> fst (regula_falsi f a b n) \<and> fst (regula_falsi f a b n) < snd (regula_falsi f a b n) \<and> snd (regula_falsi f a b n) \<le> b \<and> fst (regula_falsi f a b n) \<le> fst (regula_falsi f a b (Suc n)) \<and> snd (regula_falsi f a b (Suc n)) \<le> snd (regula_falsi f a b n)"
```

* Fuente: estándar (regula falsi). Depende de: `rf_1_punto`, `rf_2_signo`.
* Referencia privada (nunca se muestra al proponente): ninguna.
* Supuestos dudosos: ninguno señalado.
* Comprobaciones: Isabelle ✓ (ejemplo de no vacuidad, en el orden de los fixes: (\<lambda>x::real. x), -1, 1, 0); numérica 400/400.
* Hash del enunciado: `98f605c6c2f5bc4d`.

Estado: **aprobado** por Carlos (24 sep 2026).

### `rf_4_raiz` (test, dificultad 3)

**Versión clásica**.

**Enunciado:** Cada horquilla [lₙ, uₙ] contiene una raíz.

```isabelle
fixes f :: "real \<Rightarrow> real" and a b :: real and n :: nat
assumes ab: "a < b" and fa: "f a < 0" and fb: "0 < f b" and cont: "continuous_on {a..b} f"
shows "\<exists>c. fst (regula_falsi f a b n) \<le> c \<and> c \<le> snd (regula_falsi f a b n) \<and> f c = 0"
```

* Fuente: estándar (regula falsi). Depende de: `rf_2_signo`, `rf_3_encaje`.
* Referencia privada (nunca se muestra al proponente): ninguna.
* Supuestos dudosos: ninguno señalado.
* Comprobaciones: Isabelle ✓ (ejemplo de no vacuidad, en el orden de los fixes: (\<lambda>x::real. x), -1, 1, 0); numérica 400/400.
* Hash del enunciado: `834ccf56047c171e`.

Estado: **aprobado** por Carlos (24 sep 2026).

### `rf_5_limites` (test, dificultad 3)

**Versión clásica** (arrastra hipótesis que no usa: la continuidad de f).

**Enunciado:** Los dos extremos convergen (sucesiones monótonas acotadas).

```isabelle
fixes f :: "real \<Rightarrow> real" and a b :: real
assumes ab: "a < b" and fa: "f a < 0" and fb: "0 < f b" and cont: "continuous_on {a..b} f"
shows "convergent (\<lambda>n. fst (regula_falsi f a b n)) \<and> convergent (\<lambda>n. snd (regula_falsi f a b n))"
```

* Fuente: estándar (regula falsi). Depende de: `rf_3_encaje`.
* Referencia privada (nunca se muestra al proponente): ninguna.
* Supuestos dudosos: ninguno señalado.
* Comprobaciones: Isabelle ✓ (ejemplo de no vacuidad, en el orden de los fixes: (\<lambda>x::real. x), -1, 1); numérica 400/400.
* Hash del enunciado: `34431834873ae0ba`.

Estado: **aprobado** por Carlos (24 sep 2026).

### `rf_6_convergencia` (test, dificultad 5)

**Versión debilitada**: solo afirma que un extremo converge a una raíz; la forma clásica, con raíz única, afirma que los puntos cₙ convergen a ella. Versión clásica más fuerte: `rf_6c_puntos_convergen`.

**Enunciado:** Al menos un extremo converge a una raíz (el otro puede quedarse fijo).

```isabelle
fixes f :: "real \<Rightarrow> real" and a b :: real
assumes ab: "a < b" and fa: "f a < 0" and fb: "0 < f b" and cont: "continuous_on {a..b} f"
shows "\<exists>c. a \<le> c \<and> c \<le> b \<and> f c = 0 \<and> ((\<lambda>n. fst (regula_falsi f a b n)) \<longlonglongrightarrow> c \<or> (\<lambda>n. snd (regula_falsi f a b n)) \<longlonglongrightarrow> c)"
```

* Fuente: estándar (regula falsi). Depende de: `rf_2_signo`, `rf_3_encaje`, `rf_5_limites`.
* Referencia privada (nunca se muestra al proponente): ninguna.
* Supuestos dudosos: No se afirma que los dos extremos converjan a la raíz: en general uno se queda quieto.
* Comprobaciones: Isabelle ✓ (ejemplo de no vacuidad, en el orden de los fixes: (\<lambda>x::real. x), -1, 1); numérica 400/400.
* Hash del enunciado: `47d4ce911880dafd`.

Estado: **aprobado** por Carlos (24 sep 2026).

### `rf_6c_puntos_convergen` (test, dificultad 5)

**Versión clásica** (más fuerte que `rf_6_convergencia`).

**Enunciado:** Forma clásica: si la raíz en [a, b] es única, los puntos de falsa posición cₙ convergen a ella.

```isabelle
fixes f :: "real \<Rightarrow> real" and a b :: real
assumes ab: "a < b" and fa: "f a < 0" and fb: "0 < f b" and cont: "continuous_on {a..b} f"
    and unica: "\<And>c d. c \<in> {a..b} \<Longrightarrow> d \<in> {a..b} \<Longrightarrow> f c = 0 \<Longrightarrow> f d = 0 \<Longrightarrow> c = d"
shows "\<exists>c. a \<le> c \<and> c \<le> b \<and> f c = 0 \<and> (\<lambda>n. case regula_falsi f a b n of (l, u) \<Rightarrow> punto_rf f l u) \<longlonglongrightarrow> c"
```

* Fuente: estándar (regula falsi, forma clásica). Depende de: `rf_6_convergencia`.
* Referencia privada (nunca se muestra al proponente): ninguna.
* Supuestos dudosos: ninguno señalado.
* Comprobaciones: Isabelle ✓ (ejemplo de no vacuidad, en el orden de los fixes: (\<lambda>x::real. x), -1, 1); numérica 392/392.
* Hash del enunciado: `5a973432f8e0abe7`.

Estado: **aprobado** por Carlos (24 sep 2026).

