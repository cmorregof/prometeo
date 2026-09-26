# Informes de corrida: especificación (23 sep 2026)

Pedido literal de Carlos: «el PDF que quiero que generes es como este [plantilla_v0.1.tex] // No te pongas a
inventar un formato diferente y lo quiero para cada una de las corridas que estamos esperando».

## Formato (no negociable)

* Preámbulo: EXACTAMENTE las líneas de `plantilla_v0.1.tex` desde `\documentclass` hasta `\newtheorem{remark}`,
  byte a byte. Nada de paquetes nuevos (ni lmodern, ni babel, ni listings, ni microtype, ni xcolor). Si algo no
  se puede escribir con esos paquetes, se escribe de otra forma.
* Título: `Aprendizaje por refuerzo con verificación certificada\\como única recompensa:\\<asunto de la corrida>\\[0.4em]\large Informe de corrida del proyecto \texttt{rl\_metodos}`.
* Autor: `Carlos Manuel Orrego Franco\\Universidad Nacional de Colombia, Sede Manizales`.
* Fecha: `<Mes> de <año> --- informe de la corrida \texttt{<id>}` (mes y año del inicio de la corrida).
* Secciones, en este orden y con estos títulos: Propósito; El MDP común; La interfaz de verificador y sus tres
  instancias; Funciones de recompensa; Métricas; Jerarquía de confianza entre jueces; Entornos; Experimentos
  realizados y previstos (único título que cambia: la plantilla dice «previstos» y aquí ya hay resultados).
* Solo los entornos de la plantilla: `definition`, `remark`, `itemize`, `enumerate`, `tabular` con booktabs,
  `table` con `\caption` y `\label`, matemáticas de amsmath. Citas con `\citep`/`\citet` y
  `\bibliography{unirl_definicion}` (se copia `docs/nota/unirl_definicion.bib`).
* Todo en español. Nada de Unicode fuera de lo que `inputenc` utf8 + T1 aceptan (tildes, ñ, ¿, ¡ sí; τ, ≤, ‖, →,
  ⟹, símbolos de Isabelle NO: se escriben en matemáticas o se omiten). El texto que venga de datos (propuestas del
  modelo, errores de Isabelle) se sanea: `\texttt{}` con escapes, recortado, sin símbolos `\<...>` crudos.

## Contenido por sección

1. Propósito: primer párrafo de la plantilla literal. Segundo párrafo: qué es esta corrida (juez, objetivo,
   modelo y esfuerzo, presupuesto B, episodios, memoria sí/no y su redacción, lemas sí/no) y qué pregunta responde.
   Tercer párrafo: «Este informe sigue la estructura de la nota técnica: ... y reporta en §5 los valores medidos.»
2. El MDP común: la Definición de la plantilla literal. Si la corrida tiene memoria, el estado es
   $s_t = (T, \mathcal{C}_t, h_t, M_t)$ y se añade un ítem para $M_t$: biblioteca de lemas que el agente demostró y
   que Isabelle verificó (se añaden solos a cada intento) y resumen del mejor intento de cada episodio anterior;
   persiste entre episodios de la corrida; el modelo está congelado: la memoria es contexto, no entrenamiento.
   Observación «El objetivo es inmutable» literal, más el hash del objetivo de esta corrida.
3. La interfaz de verificador: Definición literal; las tres subsecciones con el texto de la plantilla CORREGIDO
   donde la implementación difiere (etiquetas reales de cada juez según `unirl/verifiers.py` y
   `unirl/gd_isabelle.py`; en $V_I$ la fase 2 son lemas auxiliares con demostración escritos por el agente y
   verificados en el kernel antes de usarse; en $V_P$ el modo `improve`, las fuentes de $\tau_{ref}$ y el aislamiento
   del programa). La subsección del juez de ESTA corrida lleva un párrafo «En esta corrida» con los parámetros.
   Para el juez de teorema (stepsize en Isabelle) se añade dentro de $V_I$ el párrafo «Variante de teorema» con el
   enunciado congelado (ver `docs/diseno_gd_isabelle.md`).
   La Observación «Existencia frente a descubrimiento» se reescribe con NUESTRAS mediciones, leídas de
   `runs/_baseline/bisection.json` (anotación del artículo: VCs cerradas de 15) y `runs/_baseline/upper_bound.json`
   (anotación del artículo + sus demostraciones manuales como lemas: ACCEPTED). No se repite ninguna cifra de la
   plantilla que no hayamos medido.
4. Funciones de recompensa: texto de la plantilla literal + «En esta corrida: ...» (recompensa activa, shaped, β,
   penalización de deriva) desde meta.json. Para $V_P$ se reportan en §5 los valores de $r_P$ (`raw.reward06`).
5. Métricas: la lista de 6 de la plantilla, cada ítem con su valor medido (o «no aplica / no se midió» y por qué).
   (1) $t^*$ mediana y por episodio, censurada en $B$. (2) tabla de etiquetas. (3) razón de deriva según el juez
   (para $V_P$: conteo de INVALID_SCHEDULE). (4) transferencia: la memoria dentro de una corrida NO es
   transferencia entre objetivos; se dice así. (5) comparación: tabla con las otras corridas del mismo método
   (otros jueces y otros modelos) leídas de `runs/` (se ignoran carpetas `_*`). (6) costo: segundos de juez y de LLM
   por intento (media, mediana, máximo) y duración total.
   Tablas adicionales por tipo: programa ($V_I$ bisección): intento a intento (episodio, paso, etiqueta, VCs
   cerradas/total, lemas propuestos, lemas verificados, segundos de juez) y la biblioteca final de la memoria
   (nombres). PEP: por instancia ($n$, $\mu$, criterio, pasos negativos, $\tau_{ref}$ y fuente, mejor $\tau$,
   mejor $r_P$, ¿CERTIFIED?) y los mejores pasos $h$. Teorema: por objetivo (aceptado, $t^*$, etiquetas, lemas
   verificados).
6. Jerarquía de confianza: tabla y párrafo de la plantilla literales + «Residuo en esta corrida» específico
   (bisección: lemas prestados Bolzano y sign_prop, adecuación de la tripleta; PEP: $\tau_{ref}$ de nuestra
   búsqueda en las variantes abiertas, así que CERTIFIED significa mejorar nuestra referencia, no la literatura;
   teorema: la equivalencia interp ⇔ convexa y 1-suave no está formalizada).
7. Entornos: la tabla de la plantilla con los números RECALCULADOS de los grafos de 01–05 (lemas, distractores,
   cadena mínima) y filas reales: 06 ($V_P$), bisección $V_I$ (08), y los objetivos de stepsize en Isabelle (09).
   El pie se corrige con los hechos actuales (proponentes gpt-6-luna y gpt-6-astra con esfuerzo high; objetivos
   de $V_I$ disponibles). Se marca qué filas corresponden a esta corrida.
8. Experimentos realizados y previstos: `enumerate` con esta corrida y su resultado en una frase con números, las
   corridas relacionadas y lo siguiente. Si existe `comentario.tex` en la carpeta del informe, se incluye como
   `\begin{remark}[Interpretación]...\end{remark}` al final de la sección (lo escribe Claude a mano).

Todo número sale de los datos (attempts.jsonl, meta.json, memoria.json, runs/_baseline); nada se escribe a mano.
Una corrida sin terminar se marca «en curso» con los episodios completos hasta el momento.

## Uso

```
python -m unirl informe --runs runs/<env>/<id> [más carpetas] --out docs/informes/<slug>
python -m unirl informe --ultima <env1,env2,...> --model gpt-6-luna --slug <slug>   # última corrida de cada env con ese modelo
```
Salida: `docs/informes/<slug>/informe.tex`, `informe.pdf` (latexmk + bibtex), `unirl_definicion.bib`.
