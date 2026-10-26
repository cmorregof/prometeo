# Prerregistro — Memoria certificada en tiempo de prueba: ¿mejora un modelo congelado con su propia biblioteca de lemas verificados por el kernel de Lean?

**VERSIÓN PARA CONGELAR — 26 oct 2026.** El §17 (precisiones operativas del arnés v6) prevalece donde es más específico que el resto del texto. Este texto incorpora dos revisiones independientes: la del 25 oct (`revision_independiente_prerregistro_2026-10-25.md`) y la del 26 oct (`revision_independiente_ronda2_v6_2026-10-26.md`). Claude propuso las decisiones marcadas como confirmadas, por delegación de Carlos («lo que tú me recomiendes», 25 oct 22:17), y Carlos las confirmó el 26 oct a las 12:36 («sí a todo»).

Al congelar se hacen cuatro cosas, **antes de la primera llamada a la API de la fase 1**: se fija la fecha, se calcula el SHA-256 de este archivo, se etiqueta el repositorio (tag git `prereg-v1`) y se registra en OSF Registries. Todo cambio posterior es una enmienda numerada y fechada en §15, con constancia de qué se había observado hasta ese momento. No hay ediciones silenciosas.

- **Autor:** Carlos Manuel Orrego-Franco (UNAL Manizales, corregof@unal.edu.co). Supervisores de la tesis: Juan Carlos Riaño Rojas y Fabián Fernando Serrano Suárez. Se nombran en la descripción y no figuran como coautores del registro salvo que lo acepten.
- **Tesis:** «Prometeo desencadenado: aprendizaje por refuerzo verbal con memoria verificada para la demostración formal de teoremas» (MSc en Matemáticas Aplicadas, UNAL Manizales).
- **Material ya observado antes de congelar.** Todo es exploratorio y queda fuera de los contrastes confirmatorios:
  - calibración con 100 tareas (24–25 oct);
  - tres corridas repetidas de Haiku SC sobre 60 tareas no-FC, para medir el ruido;
  - piloto de material con 121 tareas de 9 familias que **no** pertenecen a la población (10–19 tareas por familia);
  - censo de elegibilidad, sin API;
  - simulaciones de potencia.

  Ninguna tarea de la población se ha corrido con un cuaderno.
- **Compromiso de publicación:** sea cual sea el resultado, se publican todas las transcripciones (`intentos.jsonl`), los cuadernos congelados, el libro de gasto, el código y los análisis.

---

## 1. Preguntas e hipótesis confirmatorias

El objeto de estudio es el **sistema** formado por el modelo congelado y la biblioteca de lemas certificados, no el modelo solo. No se afirma que el modelo «acumule capacidad».

Las ramas que se comparan son:
- **SC:** el modelo sin biblioteca.
- **D100:** el modelo recibe, como contexto invocable, la biblioteca de lemas que él mismo certificó al resolver las tareas del otro pliegue de la misma familia.
- **P:** placebo de igual largo, hecho de lemas certificados de familias de otra fuente.
- **D100-texto:** el mismo contenido que D100, dado solo como pistas de texto.
- **R-texto:** las propuestas de lemas que el kernel rechazó, como texto.
- **SC_ig:** SC con intentos extra hasta igualar los tokens por intento de D100.

Las hipótesis:
- **H1 (memoria).** Con el mismo número de intentos y turnos, ¿resuelve D100 más tareas que SC?
- **H4 (filtro del kernel).** Con el mismo largo de contexto y el mismo origen, ¿valen más como pistas de texto los lemas que el kernel certificó (D100-texto) que las propuestas que rechazó (R-texto)?
- **H2 (no es solo contexto más largo).** ¿Supera D100 a P?
- **H3 (con cómputo igualado).** ¿Supera D100 a SC_ig?
- **H5 (invocabilidad).** Con el mismo contenido, ¿importa que los lemas sean invocables (D100) y no solo texto (D100-texto)?

Las cinco son bilaterales. Solo H3 respalda la frase «con cómputo igualado»; H1 compara a igual número de intentos.

**[decisión confirmada] D0 se fusiona con SC.** En el arnés, «CC con cuaderno vacío» produce byte a byte el mismo prompt y el mismo archivo Lean que SC, porque la sección del cuaderno se omite cuando está vacío (revisión independiente, §3). Mantenerla como rama aparte sería pagar dos veces por la misma condición. El control de H1 es SC.

## 2. Población, tareas y exclusiones

### 2.1 Corpus y entorno
- **Corpus:** corpus aprobado v1 de `prometeo_lean` (`aprobados/Corpus/corpus_v1.jsonl`, SHA-256 `a2f5e13c3e783888ffbbe21430c6dcc8692d135df313040c68c65c452c35b96d`). Los enunciados Lean se aprobaron y registraron con SHA antes de cualquier prueba.
- **Lean:** 4.34.1 (`leanprover/lean4:v4.34.1`).
- **Mathlib:** `d13f23b723b8a846827a245b89c10fc7d3f11612`.
- **Proyecto Lean del corpus:** `corpus_compilar/corpus_lean` (lake-manifest.json SHA-256 `65c8772460003dea93a0a4a7246295e13211a436ed73e2185a67cd09c54f707a`), con FormalConjecturesForMathlib y FormalConjecturesUtil copiados dentro. Huella del árbol: el SHA-256 de la lista ordenada de los SHA-256 de sus `.lean` es `08e2fe380063af9adecaae3f00fade453d5b860b71f6a5d1fc1ea677b60a767a`.

### 2.2 Criterios (aplicados sin API, ya ejecutados)
1. Enunciado verdadero (`verdad = verdadero`).
2. Fuera de formal-conjectures (FC).
3. No trivial: el martillo v2 sin LLM no la cierra, con evidencia positiva por `#print axioms`.
4. La referencia del kernel elabora sola con el arnés v5.
5. Sin casi-duplicados dentro de la familia. La clave es el tipo normalizado más el SHA del contexto sin comentarios.
6. Familia = par (fuente, familia), con al menos 20 tareas distintas. Las seis familias V1–V6 del ETP son familias separadas.
7. Tope de 40 tareas por familia. Las tareas se ordenan por SHA-256, se barajan con la semilla `20261026` y se toman las primeras 40. Esta permutación también fija el prefijo de 30 que usa el recorte de §11.

### 2.3 Resultado del censo (sin API, 25 oct)
Está en `corpus_compilar/censo_elegibilidad_v5/` (`elegibles.json` SHA-256 `fee6583cd5454b3e1e3c53f5cbf679e5c62cb17eb4ad4896980aadf53106a73f`): **F = 27 familias de 11 fuentes, 947 tareas distintas, 905 con tope 40.** El plan determinista (`runs/unirl/confirmatorio/v6/plan.json`, SHA-256 `3bb2525b5e80a45865964036516f0c1b10c06d36db09b7902159db34c8670366`) fija la submuestra, los pliegues y el prefijo de 30. La lista de familias y tareas se adjunta y forma parte del registro.

Las 27 familias son un censo del corpus aprobado, no una muestra. La inferencia por familia generaliza a familias de este tipo de corpus formal, con el mismo modelo y el mismo arnés.

### 2.4 Exclusión previa simétrica
Se aplica después de la fase 1 y antes de cualquier celda de test. Una tarea de test T se excluye de **todas** las ramas si se cumple esto: para algún lema L de **cualquiera de las dos** construcciones del otro pliegue, `example : T := by first | exact L | exact L .. | simpa using L` cierra en 10 s o menos, sin otras premisas.

Una familia sigue en el estudio si le quedan al menos 10 tareas después de la exclusión. Se reporta el conteo de excluidas por familia.

## 3. Diseño

### 3.1 Partición
Cada familia se parte en dos pliegues. Los grupos de casi-duplicados y de variantes de una misma implicación van enteros a un mismo pliegue. El algoritmo:
1. Se barajan los grupos con la semilla `20261027`.
2. Cada grupo va al pliegue que tenga menos tareas.
3. Si los dos pliegues tienen las mismas tareas, el grupo va al pliegue 1.

Cada tarea es de test una sola vez, con los cuadernos construidos sobre el otro pliegue de su familia.

### 3.2 Construcción de cuadernos (fase 1)
- **Modelo y configuración:** Haiku 5.5 (identificador de la API `claude-haiku-5-5`), configuración CC en línea, en serie dentro de cada pliegue. En cada llamada se registra el campo `model` que devuelve la API.
- **Dos construcciones independientes por pliegue,** c = 1 y c = 2, cada una con un orden aleatorio de tareas: semillas `20261031` + c.
- **Qué se guarda:** los lemas certificados y las propuestas rechazadas, con su origen (tarea, episodio, intento).
- **Qué cuenta como rechazado para R-texto:** un bloque `cu_…` cuyo enunciado elabora y cuya prueba el kernel rechaza. Quedan fuera:
  - los errores de sintaxis;
  - los rechazos por palabra prohibida;
  - los enunciados α-equivalentes entre sí (se deja uno);
  - todo enunciado α-equivalente a un certificado de la misma construcción.
- **Filtro de compilación, sin API.** Para cada tarea de test y cada bloque de cuaderno que esa tarea pueda recibir (D100, P, D50), se compila «contexto de la tarea + bloque» con el timeout de §4. Del bloque de esa tarea se quitan los lemas que no compilan y los que cambian el enunciado aprobado (por ejemplo, una `instance`). Para detectarlos se comprueba que el tipo del enunciado, elaborado después del bloque, coincide con la referencia del kernel elaborada antes. Los enunciados de D100-texto y de R-texto deben elaborar en el contexto de la tarea de test; el filtro es el mismo para las dos ramas, y también la regla para los enunciados que dependen de `def`s del mismo bloque. Las tareas con el mismo SHA de contexto comparten el resultado. Se reporta cuántos lemas caen por rama y por familia.
- **Congelado:** los cuadernos, los fondos y los bloques filtrados se congelan con su SHA-256. Se registran como **anexo fechado antes de la fase 2**. Ese anexo es mecánico: no deja ninguna decisión abierta.
- **Curva en línea:** el pase de construcción sirve también como curva en línea, que es un análisis secundario (§9).

### 3.3 Ramas de test (fase 2)

| Rama | Contexto que recibe el modelo | k | Papel |
|---|---|---|---|
| **SC** | Sin cuaderno | 3 | Control de H1 y H3 |
| **D100** | Cuaderno completo de la construcción asignada, del otro pliegue, invocable (los lemas van declarados en el archivo) | 3 | Tratamiento |
| **P** | Placebo: lemas certificados de familias de **otra fuente**, invocables, igualados en tokens a D100 de esa construcción | 2 | Control de H2 |
| **D100-texto** | El mismo contenido que D100, como pistas de texto no declaradas, con la instrucción literal del Anexo B | 3 | Tratamiento de H4; control de H5 |
| **R-texto** | Rechazados del **otro pliegue** y de la **misma construcción**, como texto, igualados en tokens a D100-texto, con la misma instrucción | 3 | Control de H4 |
| **SC_ig** | SC con K_ig intentos (§3.4) | 2 | Control de H3 |
| **D50** | Submuestra **aleatoria** del 50 % de los lemas de D100 (redondeo hacia arriba), con la semilla `20261032` | 1 | Secundaria: dosis exógena |

**[Decisión confirmada por Carlos, 26 oct, 12:36]** Quedan fuera del registro:
- la rama X (transferencia entre familias);
- R-no-refutado (necesita una tubería de refutación aparte);
- la subida de k;
- Sonnet. Con 27 USD en caja no se puede financiar. Si se corre algún día, será exploratorio y no registrado.

**Asignación de construcción (contrabalanceo).**
- Para cada tarea, la semilla 1 usa la construcción c sorteada con `20261030`, y la semilla 2 usa la otra. La semilla 3 se sortea.
- En una misma (tarea, semilla), D100, P, D100-texto, R-texto y D50 usan la misma construcción.
- P y R-texto se igualan al largo de **esa** construcción.

**Estrato = fuente del corpus.** El fondo de P para una familia es la unión de los certificados de las dos construcciones de todas las familias de otra fuente, después del filtro de compilación para la tarea. Los lemas se eligen con la semilla `20261029`.

**H4 primario restringido.**
- Entran al análisis primario de H4 solo las familias cuyo fondo propio de rechazados (otro pliegue, misma construcción) alcanza al menos el 80 % del objetivo de tokens en las dos construcciones.
- La lista se calcula **después de la exclusión previa**, sobre las familias que siguen en el estudio, y la comprobación de F_H4 ≥ 12 se hace sobre esa lista. Se fija al cerrar la fase 1 y va en el anexo.
- En las demás familias R-texto **no** se rellena con material ajeno: no se corre, y esas familias quedan fuera de H4.
- Si menos de 12 familias cumplen, H4 es no evaluable (§10).

**Igualación de largo.**
- **Qué se mide:** el largo de un bloque es su número de tokens **tal como lo ve el modelo** en el prompt: enunciados y nombres, sin pruebas ni origen. Se cuenta con el contador de tokens de la API (`count_tokens`, sin costo) para `claude-haiku-5-5`.
- **El campo «origen»** (hoy muestra ids de tarea y episodio) se quita en todas las ramas.
- **Cómo se arma el bloque:** se añaden lemas o propuestas enteros, en orden aleatorio (semilla `20261029`), mientras el total no pase del objetivo + 5 %.
- **Si no alcanza:** cuando no se llega al objetivo − 5 %, se usa lo que haya y se declara.
- **Reporte:** se reporta también el número de enunciados de cada bloque.
- **Orden en el contexto:** D100 y D100-texto llevan los lemas en el orden en que el kernel los certificó. P y R-texto, en el orden aleatorio de la selección.

### 3.4 SC_ig
SC_ig es el mismo episodio que SC, pero con K_ig intentos de prueba y los mismos 3 turnos de exploración.

K_ig = mín(12, máx(4, redondeo(4 · r))).

- **Qué es r:** el cociente entre los tokens medios **por intento** en D100 y en SC. Cuentan la entrada, la salida con el pensamiento y las lecturas de caché.
- **Dónde se mide r:** en las celdas de D100 y SC del primer 10 % del orden de la fase 2. Medir por intento quita casi toda la dependencia del resultado.
- **Orden de las celdas:** las celdas de SC_ig se barajan con la semilla `20261028` entre el 90 % restante.
- **Registro:** K_ig se registra como enmienda mecánica antes de la primera celda de SC_ig.
- **Reporte:** se reportan los tokens realizados por rama. La igualación es ex ante.

### 3.5 Fases y orden

**Fase 1 (tope 24 USD).** Comprende:
- la construcción de cuadernos;
- el filtro de compilación;
- el martillo con cuadernos;
- la exclusión previa;
- la lista de familias de H4;
- la evaluación de §10.

Las familias se construyen en orden aleatorio (semilla `20261033`), y cada construcción se completa entera. Si se alcanza el tope, las familias sin construir quedan fuera antes de cualquier test, sin haber visto resultados.

**Fase 2 (tope 260 USD).**
- Todas las celdas tarea × rama × semilla en orden aleatorio (semilla `20261028`), en una sola ventana.
- El mismo número de procesos de Lean en paralelo durante toda la ventana.
- Puede empezar días o semanas después de la fase 1, según los fondos. Esa pausa está prevista y no es una desviación.

**Si cambia la versión del modelo.**
- Si el `model` devuelto al empezar la fase 2 difiere del de la fase 1, se repite la fase 1 con la versión nueva antes del test.
- Si cambia durante la fase 2, se detiene la corrida y las celdas posteriores se analizan aparte.

## 4. Episodio y cómputo (igual en todas las ramas)

**Episodio.**
- K = 4 intentos de prueba (K_ig en SC_ig), 3 turnos de exploración (EVAL con tope) y reflexión entre intentos.
- En test el cuaderno está **congelado**: no se le añade nada.
- Los lemas `cu_` que el modelo certifica dentro de un episodio solo valen en ese episodio.

**Prompt.**
- El SISTEMA y las cabeceras de cada rama son los textos literales del Anexo B.
- Se neutraliza la frase del SISTEMA que dice que los lemas sirven «también en tareas futuras», porque en test es falsa.

**Parámetros de la API.**
- Haiku sin parámetro de esfuerzo.
- `max_tokens` = 32 000 por llamada, con el pensamiento incluido.
- Pensamiento adaptativo por omisión: no se envía `thinking`.
- Temperatura: la que pone la API por omisión.
- Sin task budgets; `--recorte ninguno`.
- Reintentos ante errores del proveedor: los de `complete_with_retries` del arnés, con las mismas esperas en todas las ramas.
- Las flags literales de la corrida van en el Anexo B.

**Fallos y cortes.**
- Una llamada cortada por max_tokens cuenta como un turno perdido, sin reintento, y se registra su `stop_reason`.
- Una negativa del modelo (refusal) o un error de programa cuentan como no resuelta.
- Un episodio interrumpido se vuelve a correr desde cero, una sola vez. Vale la segunda corrida, y se reporta el conteo por rama.

**Tiempo de Lean.**
- `UNIRL_TIMEOUT_LEAN` = 300 s en el juicio y en EVAL.
- Una tarea con `SIN_SALIDA_LEAN` se rejuzga una vez con 900 s, solo el juez y sin API. Si persiste, cuenta como no resuelta.
- Los timeouts se reportan por rama.

## 5. Medida y juez

**Respuesta.** Tarea resuelta (1/0) por (tarea, rama, semilla). Por tarea y rama se usa la tasa media sobre las semillas.

**Cuándo una tarea cuenta como resuelta.** El juez debe dar `ACCEPTED`, lo que exige todo esto:
- El archivo compila sin errores.
- El teorema aprobado y `unirl_chk` usan solo `propext`, `Classical.choice` y `Quot.sound`.
- El tipo del teorema demostrado coincide con la referencia del kernel, que se elabora **antes** de cualquier texto del modelo:
  ```
  private theorem unirl_ref_<nonce> … := unirl_sorry_<nonce>
  theorem unirl_chk_<nonce> : type_of% @unirl_ref_<nonce> := @_root_.<nombre>
  ```
- Una recompilación con un nonce nuevo da el mismo resultado.
- El tipo impreso coincide en texto con el de la referencia.
- `STATEMENT_DRIFT` cuenta siempre como no resuelta.
- Sin `native_decide`.

**Arnés.** `rl_metodos/unirl/corpus_confirmatorio.py`. La v5 (SHA-256 `c974c63f…`) implementa el juez y la configuración CC de la fase 1. Lean corre con el entorno sin secretos (`LakeSinSecretos`).

**Arnés v6** (módulos `plan_v6`, `prompts_v6`, `tokens_api`, `fase1`, `fase2`, `confirmatorio_v6` y `analisis_v6`; ver §17.17). Implementa:
- todas las ramas de §3.3;
- el contrabalanceo;
- las réplicas por semilla;
- el orden por celda;
- el filtro de compilación;
- los fondos;
- la igualación;
- ITT;
- el recorte automático;
- las guardias;
- el análisis de §7–§8.

Instalado el 26 oct de 2026 a las 12:23 con `correr_35_instalar_v6_r2.sh`: pasan 480 pruebas (1 saltada), el humo por rama con Lean real y sin API da OK, y HUMO_V6_OK queda escrito. La entrega tiene SHA256SUMS_v6 = `1b69e8ed…` (§17.17).

**Intención de tratar.**
- Toda celda programada cuenta.
- Una celda sin ninguna llamada facturada se reprograma una vez, al final de la ventana. Si vuelve a fallar, cuenta como no resuelta.
- Se reporta la tasa de celdas sin llamada por rama.

**Auditoría a mano.**
- Es descriptiva y ciega a la rama: 20 pruebas aceptadas por rama, más todas las `STATEMENT_DRIFT`.
- No cambia ningún resultado.
- Si encuentra un fallo del juez, se corrige el juez y se vuelve a juzgar **todo**, sin API y en todas las ramas, como enmienda.

## 6. Estimando y efecto mínimo de interés
- **Estimando:** la diferencia media de la tasa de resolución entre ramas, ponderada por tarea, en la población de §2.
- **EMI:** 5 pp sobre el total. Se justifica por el equilibrio de costo (CC es ≈ 10 % más caro) y porque es un tercio del salto de Haiku a Sonnet.
- **Cómo se traduce con el techo:** si el cuaderno no mueve las tareas que SC ya resuelve siempre (≈ 38 % se resolvió en 3 de 3 corridas de SC), 5 pp sobre el total equivalen a ≈ 8 pp en las tareas con margen.
- **Qué efecto usa la simulación:** Δ = 7,5 pp en las tareas con margen (p_SC < 0,85). Eso da ≈ 4,7–5 pp sobre el total, algo por debajo del EMI, así que la potencia simulada es conservadora para el EMI.

## 7. Análisis

**Estadístico.**
- Por tarea: la diferencia entre ramas, promediada sobre las semillas.
- Por familia f: S_f = suma de las diferencias de sus m_f tareas.
- Total de tareas: n = Σ m_f.
- Estimador (media ponderada por tarea): θ̂ = Σ S_f / n.
- t = θ̂ / SE_CR1, con SE_CR1 = √( F/(F−1) · Σ_f (S_f − m_f θ̂)² ) / n.

**Prueba.**
- Permutación de signo por familia, bilateral y **exhaustiva**: se usan los 2^F vectores de signos, incluida la identidad.
- Para cada vector se recalcula t, y p = #{|t*| ≥ |t|} / 2^F.
- Con F = 27 son 1,3 × 10⁸ vectores, que se calculan por bloques.
- La decisión la da la permutación. El IC del 95 % (Wald agrupado, t_{F−1}) es descriptivo.
- No hay covariables.
- En H5 y en las ramas con k distinto, la simetría bajo H0 es aproximada. Con la studentización y familias de ≈ 30 tareas, la aproximación basta, y se declara así.

**Sensibilidades.**
- Media ponderada por familia.
- Sin las familias con tasa de éxito ≥ 0,85 en el pase de entrenamiento. No usa datos de test.
- Las seis familias del ETP como un solo cluster (F = 22).
- Sin el estrato «cerrable por martillo + cuaderno».

## 8. Multiplicidad y regla de decisión

### 8.1 Grafo de α (Bretz et al.)
**[Decisión confirmada: opción A, Holm en el par H1–H4]**

Pesos iniciales: H1 = H4 = 0,025. Cuando se rechaza una hipótesis, su α pasa así:

| Se rechaza | Su α pasa a |
|---|---|
| H1 | ½ a H4, ½ a H2 |
| H4 | todo a H1; si H1 ya se rechazó, a H2 |
| H2 | ½ a H3, ½ a H5 |
| H3 | ½ a H5, ½ a H4 |
| H5 | ½ a H3, ½ a H4 |

Consecuencias:
- Si H1 rechaza, H4 pasa a 0,0375 y H2 a 0,0125.
- Si además rechaza H4, H2 llega a 0,05.
- Si H4 rechaza primero, H1 pasa a 0,05.

**Dirección.** Un rechazo propaga α solo si la estimación va en la dirección prevista: D100 mejor o, en H4, certificado mejor. Un rechazo en la dirección contraria se reporta, pero no propaga.

**H4 no evaluable** (§3.3, §10). Su peso pasa a H1, que queda a 0,05.

**Orden de procesamiento**, para que el resultado no dependa del orden de rechazo, que importa por la regla de dirección:
1. En cada paso, entre las hipótesis con p_j ≤ w_j · α, se procesa la de menor p_j / w_j.
2. Un rechazo en dirección contraria se registra, y su peso se pierde: no se transfiere.

Todo lo que no está en el grafo es secundario y se reporta sin α.

### 8.2 Equivalencia
- El TOST se aplica solo a las hipótesis contrastadas y no rechazadas, con margen ±5 pp e IC del **95 %** (α = 0,025 por lado).
- Las hipótesis que la cadena no alcanzó se reportan como secundarias, sin conclusión de equivalencia.
- Las conclusiones de equivalencia no están cubiertas por el control del grafo, y así se declara.

### 8.3 Interpretación conjunta de H1 y H4 (redacción que se usará)

| | **H4 sí** (certificado > rechazado) | **H4 nulo** (TOST ±5) | **H4 no concluyente** |
|---|---|---|---|
| **H1 sí** | «Con el mismo número de intentos, la memoria certificada propia mejora al sistema en X pp, y el filtro del kernel aporta: rechazados del mismo origen no sirven igual.» La expresión «cómputo igualado» se usa solo si H3 rechaza. Si H5 > 0: «y también importa que el lema sea invocable». | «El contenido ayuda, pero el filtro no: rechazados del mismo origen sirven igual como texto.» Si H5 > 0, el kernel importa por la invocabilidad, no por la selección. | Se reporta H1 y el IC de H4, sin conclusión sobre el filtro. |
| **H1 nulo** | «La memoria certificada no añade capacidad frente a no tener memoria, pero el filtro sí separa memoria útil de inútil.» Se distingue de forma descriptiva si certificado-texto > SC o si rechazado-texto < SC (en ese caso el kernel *protege*). | «Con el mismo número de intentos, un modelo congelado no gana con sus propios lemas certificados dentro de la familia.» **No** se escribe «el kernel no importa»: no había efecto de contenido que filtrar. | Como en la columna de la izquierda, sin conclusión sobre el filtro. |
| **H1 en contra** (D100 < SC) | «El contexto de la biblioteca daña a este modelo.» Para separar el largo del contenido se usa P frente a SC (secundaria). | Igual. | Igual. |
| **H1 no concluyente** | Se reportan los intervalos y se dice así. | Igual. | Igual. |

Casos transversales:
- Si el efecto se concentra en el estrato cerrable por martillo + cuaderno: «recuperación, no capacidad».
- Si martillo + cuaderno iguala a D100: la ganancia es de la biblioteca, no del modelo.

## 9. Análisis secundarios (sin α, declarados)

**Contrastes y descripciones.**
- Tendencia SC < D50 < D100.
- P frente a SC: si el placebo daña, cambia la lectura de H2.
- Pendiente de la curva en línea del pase de construcción frente a la posición.
- Efecto en las tareas «moneda» (0 < tasa de SC < 1 en sus 3 réplicas). Es descriptivo.
- Uso de constantes del cuaderno en el término de la prueba. Es un mecanismo descriptivo, nunca un estrato.
- Estratificación por similitud con el lema más cercano.
- Heterogeneidad según la línea de base de la familia (SC).
- Tokens y USD por tarea resuelta.
- Tasa de llamadas cortadas y de timeouts, por rama.
- Tasa de certificación c del pase.
- Potencia y resultado de H2, H3 y H5 con el α que les llegó.

**Línea base sin LLM (obligatoria, descriptiva).** El martillo con los lemas de D100 como premisas, sobre las mismas tareas de test. Además define el estrato pretratamiento «cerrable por martillo + cuaderno».

## 10. Planes alternativos
Se evalúan al cerrar la fase 1, antes de cualquier celda de test.
- **Cuadernos raquíticos.** Se cuenta la mediana de lemas certificados sobre las 108 construcciones (27 familias × 2 pliegues × 2 construcciones). Si es < 3, se pasa al **plan B**: SC contra CC con el cuaderno de entrenamiento congelado, sobre las mismas tareas y con los mismos controles de cómputo, EMI 3 pp y TOST ±3. Es otro estimando, y se dice así.
- **F < 12** tras la exclusión previa: plan B.
- **H4 no evaluable** si menos de 12 familias cumplen el 80 % de §3.3. En ese caso R-texto no se corre, y el α de H4 pasa a H1.

## 11. Presupuesto y regla de recorte

**Estimación.** Haiku cuesta ≈ 0,011–0,012 USD por episodio, según la calibración y el piloto.

| Fase | Cálculo | Episodios | USD |
|---|---|---:|---:|
| Fase 1 | Dos construcciones sobre 905 tareas | ≈ 1 800 | ≈ 21 |
| Fase 2 | 905 tareas × 18 episodios (SC 3 + D100 3 + P 2 + D100-texto 3 + R-texto 3 + SC_ig ≈ 2 × 1,5 + D50 1) | ≈ 16 300 | ≈ 195; ≈ 235 con 20 % de holgura por contexto más largo |
| **Total** | | | **≈ 255** |

**Topes fijos.** Fase 1: **24 USD**. Fase 2: **260 USD**. Manda el tope numérico, no lo que haya en la cuenta. **Fondos de la fase 2.** Salen de los créditos solicitados al programa AI for Science de Anthropic o, si no llegan, del aporte propio de Carlos, que es de unos 200 USD al mes. La fase 2 no empieza hasta que el tope de 260 USD esté cubierto y autorizado en FECHA.

**Regla de recorte por costo, fijada de antemano.**
- **Quién decide:** el arnés, de forma automática. Usa el libro de gasto y la lista de celdas planificadas, nunca los resultados.
- **Cuándo:** una sola vez, justo al completarse el primer 10 % de las celdas de test (n10). Se aplica si el gasto proyectado supera el tope de la fase 2.
- **Orden del recorte:**
  1. Quitar D50.
  2. Bajar P de k = 2 a k = 1.
  3. Bajar el tope por familia de 40 a 30 (el prefijo de la permutación de §2.2). Las celdas ya corridas en tareas fuera del prefijo se conservan y se reportan, pero no entran al análisis primario. Los cuadernos no cambian.
  4. Si la proyección sigue por encima de 260 USD: quitar las celdas de la semilla 3, la sorteada, en SC, D100, D100-texto y R-texto.
- **Qué no se recorta nunca:** ninguna rama de la cadena de α se elimina. Los pasos 1–4 solo quitan réplicas, tareas del final de la permutación o la rama secundaria.
- **Tope duro:**
  - Si aun así se alcanza el tope duro de 260 USD, la corrida se detiene y las celdas no corridas quedan sin correr.
  - El análisis primario de cada contraste usa las tareas con al menos una semilla completada en sus dos ramas, promediando sobre las semillas completadas.
  - Como el orden de las celdas es aleatorio, la falta de datos es aleatoria por diseño.
  - Se reporta el número de celdas perdidas por rama.
- **Registro:** cada paso se registra como enmienda antes de seguir.

La regla viene de Patodiya (2026), enmienda A9: su costo real fue 2,5 veces el calculado.

## 12. Potencia (simulación adjunta)

**Hecho.** Carlos corrió la simulación final el 26 oct, con R = 5 000 y φ = 0,5 / 0,67 / 0,8. Los resultados están en `potencia/simulacion_prereg_resultados_phi*.md`. En la nula global, el error de tipo I fue 0,025 para H1 y 0,026 para H4, y el FWER fue 0,051, con un error estándar de Monte Carlo de 0,003 (la cota de 0,05 es justa en la nula global). La simulación usa:
- la t studentizada, sin covariable;
- el grafo de la opción A, con la regla de dirección;
- el TOST con IC del 95 %;
- SC fusionado con D0 y los k de §3.3;
- φ como fracción de familias que entran a H4;
- los tamaños reales de las 27 familias del censo;
- R = 5 000.

Se reporta la potencia de H1, H4, H2, H3 y H5 con el α que de verdad les llega, y el error de tipo I de H1 y H4. **Regla:** la nula se simula con R = 20 000 y dos semillas. Si en las dos el error de tipo I de H1 o de H4 pasa de 0,025 por más de 2 errores estándar de Monte Carlo (≈ 0,0022), no se congela, y la prueba se cambia antes de congelar. En la validación preliminar, con R = 20 000 y dos semillas, salió H1 0,025 / 0,026 y H4 0,024 / 0,023.

**Validación preliminar con el análisis exacto** (`potencia/simulacion_prereg.py`, R = 2 000–10 000 en la nube; la corrida final con R = 5 000 la hace Carlos):
- **Error de tipo I** en la nula global (R = 10 000): H1 0,025, H4 0,026. FWER 0,050. En las nulas parciales, FWER ≤ 0,041. Con la ETP como un solo cluster (F = 22): H1 0,025, H4 0,024. Ninguno pasa de 0,030.
- **Escenario EMI** (cada contraste con 7,5 pp en las tareas con margen; para H4 eso supone que D100-texto rinde como D100; φ = 0,67), dentro del grafo: H1 0,97, H4 0,90, «H1 y H4» 0,89, H2 0,90. Con φ = 0,5 / 0,8, H4 da 0,77 / 0,95.
- **H3 y H5:** les llega un α medio de ≈ 0,011 y ≈ 0,021, con potencias de ≈ 0,70 y ≈ 0,34 en el escenario por omisión. **Se declara que H3 y H5 tienen potencia baja:** un no rechazo en ellas no es evidencia de ausencia.
- **Escenario de mitad** (D100-texto a medio camino entre SC y D100, es decir, Δ4 ≈ la mitad del EMI): H4 y «H1 y H4» caen a ≈ 0,40. **El diseño tiene potencia para un efecto del filtro del tamaño del EMI, no para uno de la mitad.** Por eso un H4 no concluyente no se interpreta como ausencia de efecto.

**Supuestos de ruido.**
- Mezcla de tres corridas de Haiku SC sobre 60 tareas: 12 resueltas 0 de 3 veces, 11 una vez, 14 dos veces y 23 las tres.
- Discordancia test-retest ≈ 0,28.
- Efecto aleatorio de familia.
- Techo en p_SC ≥ 0,85.
- Dos cuadernos por pliegue.

## 13. Integridad de la corrida
- Ningún enunciado se cambia después de congelar. El juez compara contra la referencia del kernel.
- Las celdas las ejecuta el arnés v6 con el SHA de §5 y §17.17, y el análisis lo hace `analisis_v6.py`, congelado con él. El libro de gasto y `intentos.jsonl` se conservan íntegros.
- El modelo confirmatorio (Haiku 5.5) se fija aquí, antes de ver resultados, siguiendo el protocolo de Thomas et al. (2026) contra el p-hacking con LLM.
- **Contaminación por preentrenamiento.** π-Base, ETP y PutnamBench son públicos. Eso sube los niveles en todas las ramas por igual: afecta al techo, no al contraste dentro del modelo. Se declara como límite de la validez externa.
- **Un solo modelo y un solo corpus.** Es una limitación declarada.

## 14. Desviaciones conocidas al congelar
- Ninguna. Los dos arreglos del arnés del 26 oct (§17.17) se hicieron antes de congelar y no se ha corrido nada con la API.

## 15. Enmiendas
Van numeradas (A1, A2, …) y fechadas, con el motivo y con la constancia de si se observó algún resultado de test.

Hay dos enmiendas mecánicas previstas, que no cuentan como desviaciones:
- el anexo de cuadernos de la fase 1;
- K_ig.

## 16. Trabajo relacionado
Buscamos estudios prerregistrados con LLM y verificador formal el 25 y el 26 oct 2026. Las fuentes fueron DataCite/OSF, Zenodo, OpenAlex, arXiv y OSF Registries, este último buscado directamente vía SHARE con 18 consultas. **Entre los que encontramos**, ninguno contrasta una biblioteca de lemas acumulada entre problemas, ni separa el filtro del kernel (certificados frente a rechazados del mismo origen). Los dos más cercanos:
- **Patodiya, «Budgeted Vericoding»** (Zenodo 10.5281/zenodo.21897886; congelado el 7 ago 2026). Políticas de presupuesto en Dafny, Verus y Lean 4.
- **Li y Li, «Repair, Retry, and the Cost of Hindsight»** (arXiv 2610.22698). Cinco documentos de registro internos; historial dentro del problema, en Lean.

Las bibliotecas de lemas sin prerregistro son el antecedente técnico: LEGO-Prover, LeanAgent, y las bibliotecas de habilidades al estilo de Voyager o DreamCoder. Este registro no reclama novedad frente a ellas, sino un contraste controlado y prerregistrado.

---

## Anexo A. Semillas
| Semilla | Uso |
|---|---|
| 20261026 | Submuestra por familia |
| 20261027 | Pliegues |
| 20261028 | Orden de las celdas de test y de SC_ig |
| 20261029 | Fondo de P e igualación de largo |
| 20261030 | Construcción asignada por (tarea, semilla) |
| 20261031 + c | Orden de la construcción c |
| 20261032 | D50 |
| 20261033 | Orden de las familias en la fase 1 |
| 20261034 | Muestra de la auditoría a mano |

## Anexo B. Prompts y flags literales
Abajo va copiado íntegro el archivo `ANEXO_B_prompts_v6_mac.md`, generado en el Mac con el v6 instalado. Su SHA-256 es `ce1e99c2d2d9523e7d9989e39ced87061b5de288729ff6c8462b0751a2a92f3a`, idéntico al que generó el instalador.

## Anexo B — Prompts y flags literales del arnés v6

Generado por `python -m unirl.confirmatorio_v6 prompts`. Los textos de abajo son los que el arnés envía, byte a byte, sobre una tarea de ejemplo (`ejemplo:doble_par`) con dos lemas de ejemplo. En las celdas reales cambian solo la tarea, los lemas/pistas, los lemas locales, la historia y el presupuesto.

### B.1 SISTEMA de test (fase 2, todas las ramas)

```
Eres un matemático que demuestra teoremas en Lean 4 con Mathlib. El kernel de Lean decide qué es verdad; tú nunca afirmas que algo está demostrado. Explora con EVAL cuando no sepas qué dice una definición, y parte la prueba en lemas pequeños que el kernel certifique.

Cada respuesta tuya es UNA de dos cosas.

(1) Exploración (no gasta intento; hay un tope de turnos):
EVAL: <<< código Lean: def/abbrev/instance/example, #eval, #check, #reduce >>>
(hasta dos bloques EVAL). El sistema lo compila en el contexto del problema y del cuaderno y te devuelve la salida.

(2) Un intento, con cualquiera de estas partes:
REFLEXION: <<< qué aprendiste del intento anterior y qué cambias (máx. 150 palabras) >>>
LEMA: <<< theorem cu_nombre … := by … >>>  (uno o varios bloques; antes del theorem puedes poner def/instance cu_…)
AUX: <<< definiciones auxiliares para la prueba principal (nombres aux_… o cu_…) >>>
PRUEBA: <<< las tácticas de la prueba del teorema pedido, sin `by` >>>

Un LEMA que el kernel acepta queda disponible por su nombre en todo lo que sigue de este episodio. Las reflexiones son texto: orientan, no valen como verdad.

Reglas del juez: todo nombre que declares empieza por cu_ (lemas) o aux_ (AUX); las instancias llevan nombre. Prohibido: sorry, admit, axiom, native_decide, implemented_by, unsafe, opaque, open, notation, attribute, namespace, section, end, import, include, set_option (salvo maxHeartbeats y maxRecDepth), metaprogramación. Solo se admiten los axiomas propext, Classical.choice y Quot.sound. El enunciado no se puede cambiar: se compara con el aprobado, y una instancia tuya que cambie el significado de un nombre del enunciado lo invalida.
```

### B.2 SISTEMA de la fase 1 (construcción CC en línea; la v5 literal: ahí la frase sobre tareas futuras es verdadera)

```
Eres un matemático que demuestra teoremas en Lean 4 con Mathlib. El kernel de Lean decide qué es verdad; tú nunca afirmas que algo está demostrado. Explora con EVAL cuando no sepas qué dice una definición, y parte la prueba en lemas pequeños que el kernel certifique.

Cada respuesta tuya es UNA de dos cosas.

(1) Exploración (no gasta intento; hay un tope de turnos):
EVAL: <<< código Lean: def/abbrev/instance/example, #eval, #check, #reduce >>>
(hasta dos bloques EVAL). El sistema lo compila en el contexto del problema y del cuaderno y te devuelve la salida.

(2) Un intento, con cualquiera de estas partes:
REFLEXION: <<< qué aprendiste del intento anterior y qué cambias (máx. 150 palabras) >>>
LEMA: <<< theorem cu_nombre … := by … >>>  (uno o varios bloques; antes del theorem puedes poner def/instance cu_…)
AUX: <<< definiciones auxiliares para la prueba principal (nombres aux_… o cu_…) >>>
PRUEBA: <<< las tácticas de la prueba del teorema pedido, sin `by` >>>

Un LEMA que el kernel acepta entra al cuaderno y queda disponible por su nombre en todo lo que sigue (en la condición con cuaderno, también en tareas futuras). Las reflexiones son texto: orientan, no valen como verdad.

Reglas del juez: todo nombre que declares empieza por cu_ (lemas) o aux_ (AUX); las instancias llevan nombre. Prohibido: sorry, admit, axiom, native_decide, implemented_by, unsafe, opaque, open, notation, attribute, namespace, section, end, import, include, set_option (salvo maxHeartbeats y maxRecDepth), metaprogramación. Solo se admiten los axiomas propext, Classical.choice y Quot.sound. El enunciado no se puede cambiar: se compara con el aprobado, y una instancia tuya que cambie el significado de un nombre del enunciado lo invalida.
```

Diferencia exacta: «Un LEMA que el kernel acepta entra al cuaderno y queda disponible por su nombre en todo lo que sigue (en la condición con cuaderno, también en tareas futuras).» → «Un LEMA que el kernel acepta queda disponible por su nombre en todo lo que sigue de este episodio.».

### B.3 Prompt de usuario, rama SC (primera llamada: sin lemas locales ni historia)

````
## La tarea: ejemplo:doble_par

El contexto aprobado (no se puede cambiar):
```lean
import Mathlib
set_option relaxedAutoImplicit false
set_option maxSynthPendingDepth 3

namespace Ejemplo

def doble (n : Nat) : Nat := 2 * n

```

Demuestra este teorema (escribe solo las tácticas en PRUEBA):
```lean
theorem doble_par (n : Nat) : doble n % 2 = 0 := by
```

## Presupuesto
Te quedan 4 intentos y 3 turnos de exploración.

````

### B.3 Prompt de usuario, rama D100 (primera llamada: sin lemas locales ni historia)

````
## La tarea: ejemplo:doble_par

El contexto aprobado (no se puede cambiar):
```lean
import Mathlib
set_option relaxedAutoImplicit false
set_option maxSynthPendingDepth 3

namespace Ejemplo

def doble (n : Nat) : Nat := 2 * n

```

Demuestra este teorema (escribe solo las tácticas en PRUEBA):
```lean
theorem doble_par (n : Nat) : doble n % 2 = 0 := by
```

## El cuaderno

Lemas certificados por el kernel de Lean, ya declarados en el archivo (úsalos por su nombre):
- `cu_doble_eq` : (n : Nat) : doble n = 2 * n
- `cu_dos_mul_mod` : (n : Nat) : 2 * n % 2 = 0

## Presupuesto
Te quedan 4 intentos y 3 turnos de exploración.

````

### B.3 Prompt de usuario, rama P (primera llamada: sin lemas locales ni historia)

````
## La tarea: ejemplo:doble_par

El contexto aprobado (no se puede cambiar):
```lean
import Mathlib
set_option relaxedAutoImplicit false
set_option maxSynthPendingDepth 3

namespace Ejemplo

def doble (n : Nat) : Nat := 2 * n

```

Demuestra este teorema (escribe solo las tácticas en PRUEBA):
```lean
theorem doble_par (n : Nat) : doble n % 2 = 0 := by
```

## El cuaderno

Lemas certificados por el kernel de Lean, ya declarados en el archivo (úsalos por su nombre):
- `cu_doble_eq` : (n : Nat) : doble n = 2 * n
- `cu_dos_mul_mod` : (n : Nat) : 2 * n % 2 = 0

## Presupuesto
Te quedan 4 intentos y 3 turnos de exploración.

````

### B.3 Prompt de usuario, rama D100-texto (primera llamada: sin lemas locales ni historia)

````
## La tarea: ejemplo:doble_par

El contexto aprobado (no se puede cambiar):
```lean
import Mathlib
set_option relaxedAutoImplicit false
set_option maxSynthPendingDepth 3

namespace Ejemplo

def doble (n : Nat) : Nat := 2 * n

```

Demuestra este teorema (escribe solo las tácticas en PRUEBA):
```lean
theorem doble_par (n : Nat) : doble n % 2 = 0 := by
```

## Pistas

Enunciados en texto, NO declarados en el archivo: no existen en Lean y no se pueden invocar por su nombre (hacerlo da `unknown identifier`). Si alguno te sirve, tienes que volver a demostrarlo tú como LEMA, con un nombre cu_ nuevo, antes de usarlo. Son solo pistas: no se garantiza que sean ciertos ni demostrables.
- `cu_doble_eq` : (n : Nat) : doble n = 2 * n
- `cu_dos_mul_mod` : (n : Nat) : 2 * n % 2 = 0

## Presupuesto
Te quedan 4 intentos y 3 turnos de exploración.

````

### B.3 Prompt de usuario, rama R-texto (primera llamada: sin lemas locales ni historia)

````
## La tarea: ejemplo:doble_par

El contexto aprobado (no se puede cambiar):
```lean
import Mathlib
set_option relaxedAutoImplicit false
set_option maxSynthPendingDepth 3

namespace Ejemplo

def doble (n : Nat) : Nat := 2 * n

```

Demuestra este teorema (escribe solo las tácticas en PRUEBA):
```lean
theorem doble_par (n : Nat) : doble n % 2 = 0 := by
```

## Pistas

Enunciados en texto, NO declarados en el archivo: no existen en Lean y no se pueden invocar por su nombre (hacerlo da `unknown identifier`). Si alguno te sirve, tienes que volver a demostrarlo tú como LEMA, con un nombre cu_ nuevo, antes de usarlo. Son solo pistas: no se garantiza que sean ciertos ni demostrables.
- `cu_doble_eq` : (n : Nat) : doble n = 2 * n
- `cu_dos_mul_mod` : (n : Nat) : 2 * n % 2 = 0

## Presupuesto
Te quedan 4 intentos y 3 turnos de exploración.

````

### B.3 Prompt de usuario, rama SC_ig (primera llamada: sin lemas locales ni historia)

````
## La tarea: ejemplo:doble_par

El contexto aprobado (no se puede cambiar):
```lean
import Mathlib
set_option relaxedAutoImplicit false
set_option maxSynthPendingDepth 3

namespace Ejemplo

def doble (n : Nat) : Nat := 2 * n

```

Demuestra este teorema (escribe solo las tácticas en PRUEBA):
```lean
theorem doble_par (n : Nat) : doble n % 2 = 0 := by
```

## Presupuesto
Te quedan 4 intentos y 3 turnos de exploración.

````

### B.3 Prompt de usuario, rama D50 (primera llamada: sin lemas locales ni historia)

````
## La tarea: ejemplo:doble_par

El contexto aprobado (no se puede cambiar):
```lean
import Mathlib
set_option relaxedAutoImplicit false
set_option maxSynthPendingDepth 3

namespace Ejemplo

def doble (n : Nat) : Nat := 2 * n

```

Demuestra este teorema (escribe solo las tácticas en PRUEBA):
```lean
theorem doble_par (n : Nat) : doble n % 2 = 0 := by
```

## El cuaderno

Lemas certificados por el kernel de Lean, ya declarados en el archivo (úsalos por su nombre):
- `cu_doble_eq` : (n : Nat) : doble n = 2 * n
- `cu_dos_mul_mod` : (n : Nat) : 2 * n % 2 = 0

## Presupuesto
Te quedan 4 intentos y 3 turnos de exploración.

````

### B.4 Cabeceras literales

Cuaderno invocable (D100, P, D50; también la construcción CC de la fase 1):
```
## El cuaderno

Lemas certificados por el kernel de Lean, ya declarados en el archivo (úsalos por su nombre):
- `cu_doble_eq` : (n : Nat) : doble n = 2 * n
- `cu_dos_mul_mod` : (n : Nat) : 2 * n % 2 = 0
```

Pistas de texto (D100-texto y R-texto, idéntica en las dos):
```
## Pistas

Enunciados en texto, NO declarados en el archivo: no existen en Lean y no se pueden invocar por su nombre (hacerlo da `unknown identifier`). Si alguno te sirve, tienes que volver a demostrarlo tú como LEMA, con un nombre cu_ nuevo, antes de usarlo. Son solo pistas: no se garantiza que sean ciertos ni demostrables.
- `cu_doble_eq` : (n : Nat) : doble n = 2 * n
- `cu_dos_mul_mod` : (n : Nat) : 2 * n % 2 = 0
```

Comprobación mecánica: `cabecera('D100-texto', x) == cabecera('R-texto', x)` para todo x → True.
La línea de cada lema/pista es `prompts_v6.linea_lema(nombre, enunciado)` = «- `nombre` : enunciado». El largo de un bloque es el conteo (`count_tokens`) de sus líneas unidas por saltos de línea como UN solo mensaje, menos el armazón del mensaje medido una vez (C3).

### B.5 Flags y parámetros literales de la corrida

```
{
 "modelo": "claude-haiku-5-5",
 "max_tokens": 32000,
 "thinking": "no se envía (adaptativo por omisión)",
 "output_config.effort": "no se envía (Haiku sin esfuerzo)",
 "temperature": "no se envía (la de la API por omisión)",
 "--recorte": "ninguno",
 "--task-budget": 0,
 "UNIRL_TIMEOUT_LEAN": 300,
 "rejuicio_SIN_SALIDA": 900,
 "reintentos": "loop.complete_with_retries, ESPERAS_REINTENTO = (2, 5, 11, 26, 60) s, iguales en todas las ramas",
 "K": 4,
 "turnos_exploracion": 3,
 "max_evals_por_turno": 2,
 "max_lemas_por_intento": 4,
 "tope_fase1_usd": 24.0,
 "tope_fase2_usd": 260.0,
 "libro": "/Users/cmorregof/Personal/rl_metodos/logs/gasto_confirmatorio.json",
 "UNIRL_TOPE_CONFIRMATORIO_USD": "gastado previo + 24 (fase 1); gastado previo + 260 (fase 2) (§17.15)",
 "--paralelo": 4,
 "recorte_automatico": "una sola vez al completarse n10, dentro de fase2 (§11, C6); pasos D50 → P k=1 → tope 30 → sin semilla 3",
 "tolerancia_igualacion": "máx(5 %, mediana de tokens por lema del bloque objetivo) (§17.7)",
 "conteo_tokens": "bloque entero como un solo mensaje, menos el armazón medido una vez (C3)"
}
```

### B.6 Ramas (§3.3)

| rama | k | K | invocable | texto | fuente del bloque |
|---|---:|---:|---|---|---|
| SC | 3 | 4 | False | False | ninguna |
| D100 | 3 | 4 | True | False | propio |
| P | 2 | 4 | True | False | placebo |
| D100-texto | 3 | 4 | False | True | propio |
| R-texto | 3 | 4 | False | True | rechazados |
| SC_ig | 2 | K_ig | False | False | ninguna |
| D50 | 1 | 4 | True | False | d50 |

SHA-256 del SISTEMA de test: `8ffdcfd8c777983a636b170aa7f0044ec9b80b10ee16782d7015191dd834fbb0`; de la fase 1: `ddbfa46488783d9d4664db2acf11dfc9ab4c10236e430beef3ca2904f5b61cf2`.

---

### Al congelar
Se calcula el SHA-256 de este archivo, se pone el tag `prereg-v1`, se registra en OSF y se escribe `PRERREGISTRO_REGISTRADO`.

## 17. Precisiones operativas (implementación del arnés v6, `REVISION_V6.md` §4)
1. **Variantes de una misma implicación** (§3.1): dos tareas de la misma familia cuyos ids contienen el mismo `imp:P…-P…`.
2. **Representante de un grupo de casi-duplicados:** el de menor id (orden lexicográfico).
3. **Orden «por SHA-256»** (§2.2 p. 7): por el `sha256_tarea` del corpus (contexto + enunciado).
4. **Semillas por tarea:** para cada (tarea, construcción c), la semilla efectiva es la cadena `<semilla>:<id>:<c>` (y `…:R` para R-texto). Un cambio en la lista de tareas no mueve las selecciones de las demás.
5. **SC_ig** (§3.4):
   - n10 = ⌈0,10 · N_total⌉ celdas, contando las de SC_ig, tomadas del orden sin SC_ig.
   - El 90 % restante se baraja junto con las de SC_ig con `20261028`.
   - r = (Σ tokens / Σ intentos en D100) ÷ (lo mismo en SC).
   - «Tokens» = entrada total (incluidas lecturas y escrituras de caché) + salida (incluido el pensamiento).
   - Redondeo: medio al par.
6. **Regla del 80 % de H4:** la familia entra si, para cada uno de sus 4 pares (pliegue, c), tokens(rechazados) ≥ 0,8 · tokens(cuaderno sin filtrar).
7. **Tolerancia de la igualación:** la tolerancia es el mayor de dos valores: 5 % o la mediana de tokens por lema del bloque objetivo. Se añaden elementos enteros en orden aleatorio, saltando los que no caben, y nunca se pasa del límite superior. Si no se llega al límite inferior, el bloque se declara «corto» y se reporta la diferencia.
8. **P y el filtro de compilación:** se selecciona del fondo, se filtra lo seleccionado en el contexto de la tarea y, si algo cayó, se completa del fondo. Son como máximo 3 vueltas. Se reportan las caídas.
9. **Exclusión previa** (§2.4):
   - Se compila un archivo por (tarea, construcción) con una copia del enunciado aprobado por lema: `theorem unirl_excl_k <cabecera> := by first | exact L | exact L .. | simpa using L`.
   - `maxHeartbeats` por omisión; tope del archivo = 10 s por lema + 60 s de importación.
   - Si el archivo no termina, la tarea queda «sin dato», no se excluye y se reporta.
   - Se declara que `simpa using L` cierra lo que `simp` cierra solo; la población ya pasó por el martillo v2, que incluye `simp`.
10. **Error de sintaxis** (§3.2): algún mensaje de Lean del bloque viene del parser (`unexpected token`, `expected …`, `unterminated`).
    - De un bloque con varios teoremas, entra como rechazado solo el primero que el kernel rechazó.
    - Un enunciado que depende de `def`s del mismo bloque y no elabora solo se descarta.
11. **Tope de la fase 1:** antes de empezar una familia, debe cumplirse gastado + episodios restantes × costo medio realizado ≤ 24 USD. Si no se cumple, esa familia y las siguientes quedan fuera. Si el tope duro corta una construcción a la mitad, esa familia también queda fuera.
12. **Refusal y corte por max_tokens:** consumen un intento y se registran; el episodio sigue con los intentos que le queden.
13. **SISTEMA:**
    - en la fase 1, el de la v5 literal (la frase de «tareas futuras» es verdadera en CC en línea);
    - en la fase 2, el neutralizado.
    - La cabecera del cuaderno, sin origen, es la misma en las dos fases.
    - En el archivo Lean, los lemas del cuaderno se declaran sin el comentario de origen.
14. **Muestra de calibración:** las 100 tareas de la calibración del 24–25 oct **siguen** en la población si cumplen §2.2. La calibración fue exploratoria, con SC y CC sobre muestras sin cuadernos de familia. Se reporta una sensibilidad que las excluye. **[Decisión confirmada por Carlos, 26 oct, 12:36]**
15. **Topes del libro:**
    - tope global = gastado previo + 24 USD en la fase 1, y + 260 USD en la fase 2;
    - la proyección de §11 lee el libro de gasto y la lista de celdas planificadas (`cola.json`), que no contiene resultados.
16. **Paralelismo:** `--paralelo 4` en las dos fases, igual durante toda la ventana.
17. **Arnés v6:**
    - módulos `plan_v6`, `prompts_v6`, `tokens_api`, `fase1`, `fase2`, `confirmatorio_v6` y `analisis_v6`, con el juez sin cambios (`corpus_confirmatorio.py` c974c63f…);
    - entrega identificada por `SHA256SUMS_v6` (SHA-256 `1b69e8ed41bda156793019fde6547cf733777eb35666a3db4b3e4a3c8ebfc98c`. Es la ronda 2, con `analisis_v6`, más dos arreglos del 26 oct que detectó el humo con Lean real. (1) En la exclusión previa se añadió `exact L ..`: el enunciado aprobado introduce sus binders, y `exact L` solo no cerraba ni con un lema idéntico. (2) El filtro de texto ahora usa las líneas de error y descarta los tipos con `sorry`: Lean recupera los errores de elaboración con `sorry`, y `#check` imprimía un tipo aunque el enunciado no elaborara.);
    - prompts literales en `ANEXO_B_prompts_v6.md`.
    - Humo con Lean real: OK (HUMO_V6_OK, 26 oct, 12:23).
    - `plan.json`, generado sobre el censo v5: SHA-256 `3bb2525b5e80a45865964036516f0c1b10c06d36db09b7902159db34c8670366`. Tiene F = 27 y 905 tareas; los pliegues miden lo que aparece en la salida del plan.
    - Anexo B: SHA-256 `ce1e99c2…` (ver Anexo B).
    - **Guardias:** la fase 1 no arranca sin `PRERREGISTRO_REGISTRADO` (URL de OSF + SHA-256 de este archivo congelado). La fase 2 no arranca sin el anexo íntegro y registrado, sin los conteos de tokens o si se activó el plan B.
