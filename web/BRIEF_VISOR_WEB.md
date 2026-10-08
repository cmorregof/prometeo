# Brief para Claude Code · visor web de `didactica.historia`

## Qué hay ya

- `didactica/historia/` entrena cuatro episodios históricos (euclides, cuadratura, quinto, beltrami)
  con el mismo motor: fase 1 (aprender a HACER) + fase 2 (aprender a DEMOSTRAR con un grafo de
  lemas, distractores y pasos **ámbar** = postulados/citas que se usan pero no se derivan).
- `python -m didactica.historia --all --record web/data --every 2` graba cada corrida a
  `web/data/<slug>.json` (1–5 MB). **El visor no entrena nada: reproduce estos JSON.** Así la
  demo en la charla es determinista, se puede pausar, adelantar y volver atrás.
- La interfaz de terminal (`tui.py`) queda como referencia de qué paneles hay y qué muestra cada uno.

## Qué construir

`web/`: sitio estático (Vite + React + TypeScript, o vanilla si prefieres; sin backend) desplegable en
Vercel con `vercel --prod` desde `web/`. Una sola página, tema oscuro, tipografía monoespaciada
para los lemas y una sans para el resto. Debe verse bien proyectado a 1920×1080.

### Esquema del JSON (`web/data/<slug>.json`)

```
episodio: { slug, titulo, subtitulo, fase1_titulo, fase2_titulo, lectura, has_phase1, action_names[] }
kb:       { theorem, steps[{key,title,text,deps[],distractor,qed,externo}], required[], min_len, depth{key:int} }
log[]:    líneas de la bitácora ("[  12.3s] F2 gen  206: ...")
milestones[]: { phase, episode, t, text }
curves:   { success1[], reward2[] }
frames[]: { kind: "iter"|"episode"|"iter2"|"final", phase: 1|2, gen, t, eps,
            stats{ok,fail,imposible,success100,qed,minimal,success2_100,best_reward,updates},
            log_len,                    # cuántas líneas de `log` ya existen en este cuadro
            board?,                     # snapshot del tablero de fase 1 (depende del episodio, abajo)
            action1?,                   # última acción de fase 1 (texto)
            policy1?,                   # [{estado, accion, ok, q[]}]  — sólo en algunos cuadros: conservar la última
            attempt?,                   # fase 2: [[key, ok], ...] intento en curso
            greedy? }                   # fase 2: [[key, ok], ...] demostración de la política voraz — conservar la última
```

`board` por episodio:

- **euclides**: `{a0, b0, history:[[a,b],...], last:"ok"|"falso"|"resta"|"", gcd, n}`
- **cuadratura**: `{task:"rect"|"circ", a, b, area, S:[longitudes trazadas], x, err, best_err, best_x, rect_ok, circle_tries, last, n}`
- **quinto**: `{world:"plano"|"disco", px, py, chords:[{ang, cut, p:[x,y], q:[x,y]}], parallels, last, n}` (coordenadas en el disco unidad)
- **beltrami**: no tiene fase 1.

### Layout (misma distribución que la terminal, pero con espacio)

```
┌ cabecera: título del episodio · subtítulo · reloj · Fase N · generación ─────────────────┐
│ ┌ Fase 1: tablero (SVG grande) ─────────┐ ┌ Fase 2: intento en curso ──────────────────┐ │
│ │                                        │ │ cajitas de lemas (verde/ámbar/gris)         │ │
│ │                                        │ │ líneas: verde · ámbar ⚠ · rojo tachado      │ │
│ ├ Lo que aprendió a hacer (tabla) ───────┤ ├ Lo que el agente cree ahora ───────────────┤ │
│ │ estado → acción  ✔/✘  Q                │ │ veredicto + teorema + demostración voraz    │ │
│ └────────────────────────────────────────┘ └────────────────────────────────────────────┘ │
│ ┌ Marcador ────────────┐ ┌ Bitácora de hitos ───────────────────────────────────────────┐ │
│ └──────────────────────┘ └──────────────────────────────────────────────────────────────┘ │
│ ┌ controles: ▶/⏸ · velocidad (0.25×–8×) · paso a paso (←/→) · línea de tiempo con hitos ─┐ │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

Si el episodio no tiene fase 1 (beltrami), la columna izquierda la ocupa "Lo que el agente cree ahora"
a página completa.

### Reproducción

- Un cursor sobre `frames[]`. Velocidad base: cuadros `iter` 60 ms, `iter2` 250 ms (hay que poder leer
  cada línea de la demostración), `episode` 8 ms. Multiplicador de 0.25× a 8×.
- **Al llegar a un cuadro cuyo `log_len` aumenta, pausar 2.5 s** y resaltar la nueva línea de la bitácora
  (esto es lo que se lee en voz alta). Opción para desactivar la pausa.
- Línea de tiempo: marcas en los hitos; clic salta al cuadro. Teclas: espacio = pausa, ←/→ = un cuadro,
  ↑/↓ = velocidad, `1..4` = cambiar de episodio.
- Selector de episodio en la cabecera (carga otro JSON). URL `?ep=quinto&frame=1234` para poder abrir
  la charla exactamente en un momento.
- Al final (`kind:"final"`): mostrar `episodio.lectura` en un panel de cierre, con la demostración final.

### Tableros SVG (lo importante: que se ENTIENDA a primera vista)

**euclides.** Dos barras horizontales apiladas por cada paso de `history` (a arriba en naranja, b abajo en
azul), a escala de `a0`; sobre la barra de a, marcas verticales cada `b` unidades para que se vea "cuántas
veces cabe". Los pasos viejos se van desvaneciendo hacia arriba; el actual, brillante. Rótulo con
`(a, b)` y, al final, "medida común = d" en verde o "✘ declaró en falso" en rojo. Transición animada
(200 ms) cuando la barra se acorta: se ve *cortar*.

**cuadratura.** Izquierda: la figura dada (rectángulo a×b naranja, o círculo de radio a). Derecha: el
cuadrado de lado `x` (azul; verde cuando `err < 1e-9`). Ambos a la misma escala de área. Debajo, la
lista de longitudes trazadas `S` como segmentos cortos rotulados. En modo círculo, una barra de progreso
logarítmica con `best_err` ("mejor aproximación hasta hoy") que baja y **nunca llega al fondo**; rótulo
fijo "nunca 0".

**quinto.** ESTE es el que en terminal no se entendía. En SVG:
- `world = "disco"`: círculo grande (el borde del disco de Klein) con relleno muy tenue. La recta L es una
  cuerda gruesa blanca. P es un punto magenta con halo. Cada cuerda por P: verde si `cut=false`, roja
  punteada si `cut=true`, y la última trazada más gruesa con una animación de trazo (stroke-dashoffset).
  Rótulo: "disco de Klein: las rectas son cuerdas". Contador grande: "no cortan a L: n".
- `world = "plano"`: sin círculo; L es una recta que atraviesa todo el panel; las rectas por P también
  atraviesan todo el panel (usar `p`,`q` y prolongar). Rótulo: "plano de Euclides".
- El mundo real se muestra **tachado/oculto hasta que el agente declara** (`last` ∈ {ok, falso}), y
  entonces se revela con la declaración en verde o rojo. Así la audiencia juega a adivinar con el agente.

### Panel de demostración (fase 2)

- Fila de cajitas con `kb.steps` no-distractores en orden: gris apagado (no establecido), verde
  (establecido), **ámbar** (establecido y `externo`). Tooltip con el texto del lema.
- `attempt`: lista numerada. Válido → verde con `key` en negrita y el texto; `externo` → ámbar con el
  icono ⚠ y la etiqueta "postulado / cita: no se deriva"; inválido → rojo, tachado, precedido de ✗ y
  con un sub-rótulo del motivo: "distractor" si `step.distractor`, "repetido" si ya estaba, si no
  "faltan: X, Y" (las deps no establecidas; se calculan del propio `attempt`).
- Al llegar a QED: ∎ grande con un destello breve.
- `greedy` ("Lo que el agente cree ahora"): mismo formato, más un veredicto: *mínima y correcta ✔* si
  todas válidas y `len == kb.min_len`; *completa* / *incompleta: no llega a ∎*; y siempre, si hay pasos
  ámbar, **"⚠ apoyada en k postulado(s)/cita(s): P1, PUENTE"** en ámbar y grande. En `quinto` ese rótulo
  es el mensaje de la charla: nunca desaparece.
- Un botón "ver grafo" que despliega el DAG de `kb` (deps como flechas, profundidad como capas) con los
  nodos coloreados por estado; layout simple por capas de `kb.depth`.

### Marcador y bitácora

- Marcador: reloj, generación, ε con barra, F1 logros/fracasos (+ "imposibles" en ámbar si > 0),
  éxito/100, F2 completas, mínimas, mejor retorno, y dos sparklines (`curves.success1` hasta la
  generación actual; `curves.reward2` ídem).
- Bitácora: `log[0:log_len]`, la última línea resaltada; líneas con "postulado"/"NUNCA" en ámbar,
  con "∎"/"mínima"/"ESTO"/"redescubrió"/"distingue"/"reconoce" en verde.

### Estilo

Fondo #0f1115, paneles #161a22 con borde 1px #2a3040, texto #d6dae3, atenuado #8b93a7,
verde #7fbf5a, ámbar #e0a63a, rojo #d9534f, azul #5b9dd9, magenta #c678dd, naranja #e0873a.
Nada de librerías de gráficos pesadas: SVG a mano y CSS transitions. Sin frameworks de UI.

### Entregable

- `web/` con `package.json`, `src/`, `public/data/*.json` (copiar de `web/data`), `README.md` con
  `npm run dev`, `npm run build`, `vercel --prod`.
- Un script `make data` (o npm script) que ejecute `python -m didactica.historia --all --record web/public/data --every 2`.
- Que `npm run dev` abra directo en `?ep=quinto`.
