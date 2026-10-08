# Visor web de `didactica.historia`

Reproduce en el navegador las grabaciones de los cuatro episodios históricos (Euclides, cuadratura,
quinto postulado, Beltrami). **No entrena nada**: lee `public/data/<slug>.json`, grabado con
`python -m didactica.historia --record`, y lo reproduce cuadro a cuadro. Así la demostración en una
charla es determinista: se puede pausar, adelantar, volver atrás y abrir exactamente en un momento.

Sitio estático (Vite + TypeScript vanilla, SVG a mano, sin librerías de interfaz ni de gráficos).
Pensado para proyectarse a 1920 × 1080 en tema oscuro.

## Uso

```bash
cd web
npm install
npm run dev        # abre http://localhost:5173/?ep=quinto
npm run build      # produce dist/ (tipos comprobados con tsc)
npm run preview    # sirve dist/ para probar la compilación
vercel --prod      # despliega dist/ (o: npm run deploy)
```

## Regenerar las grabaciones

Los JSON de `public/data/` salen del entrenador de `didactica/historia/` (una de cada dos generaciones
tras las primeras 60, semilla 0). Para regenerarlos, desde `web/`:

```bash
make data          # = cd .. && .venv/bin/python -m didactica.historia --all --record web/public/data --every 2
```

o `npm run data`. Tarda unos segundos por episodio; cada archivo pesa entre 1 y 5 MB.

## Qué se ve

Misma distribución que la interfaz de terminal (`didactica/historia/tui.py`), con espacio:

| zona | contenido |
|---|---|
| cabecera | título · subtítulo · ⏱ tiempo real de entrenamiento hasta ese cuadro · fase · generación · selector de episodio |
| fase 1 (izquierda, arriba) | el tablero SVG del episodio: barras de Euclides, figura y cuadrado de la cuadratura, disco de Klein / plano |
| lo que aprendió a hacer | estado → acción con mayor Q, ✔/✘ y los valores Q |
| fase 2 (derecha, arriba) | el intento en curso: cajitas de lemas (gris · verde · ámbar), lista numerada; inválidos en rojo tachado con el motivo (`distractor`, `repetido`, `faltan: X, Y`); ∎ con destello |
| lo que el agente cree ahora | la demostración de la política voraz, con veredicto (mínima y correcta / completa / incompleta) y, si se apoya en postulados o citas, el aviso ámbar «⚠ apoyada en k postulado(s)/cita(s)» |
| marcador | reloj, generación, ε, F1 logros/fracasos (+ imposibles), éxito/100, F2 completas, mínimas, mejor retorno y dos *sparklines* |
| bitácora | los hitos hasta ese cuadro; el último resaltado; ámbar si habla de postulados o de «nunca», verde si es ∎, mínima, «ESTO», redescubrió, distingue, reconoce |
| controles | ▶/⏸ · velocidad 0,25×–8× · paso a paso · línea de tiempo con marcas en los hitos · pausa en hitos · «ver grafo» · «lectura» |

Si el episodio no tiene fase 1 (Beltrami), «Lo que el agente cree ahora» ocupa toda la columna izquierda.

### El quinto postulado

El mundo (plano de Euclides o disco de Klein) queda **oculto hasta que el agente declara**: sólo se ven L, P
y las rectas trazadas por P (verde: no corta a L; roja punteada: corta). Al declarar se revela: en el disco
aparece el borde («las rectas son cuerdas»), en el plano las rectas se prolongan por todo el panel, y la
declaración sale en verde o en rojo. La casilla «ocultar el mundo hasta declarar» lo desactiva.
En la fase 2, el aviso ámbar «apoyada en … PUENTE» es el mensaje de la charla y no desaparece nunca.

## Reproducción

* Un cursor sobre `frames[]`. Duración base: cuadros `iter` 60 ms, `iter2` 250 ms (se puede leer cada línea
  de la demostración), `episode` 8 ms. Multiplicador de 0,25× a 8×.
* Cuando un cuadro trae una línea nueva en la bitácora, pausa 2,5 s y la resalta (es lo que se lee en voz
  alta). Se desactiva con la casilla «pausa en hitos».
* Al final (`kind: "final"`) se abre el panel de cierre con la lectura del episodio y la demostración final.

### Teclas

| tecla | acción |
|---|---|
| espacio | reproducir / pausar |
| ← / → | un cuadro atrás / adelante (con Mayús, 25) |
| ↑ / ↓ | más rápido / más lento |
| Inicio / Fin | primer / último cuadro |
| 1 2 3 4 | cambiar de episodio |
| g | grafo de lemas (DAG por capas de profundidad, nodos coloreados por el intento en curso) |
| l | lectura del episodio |
| Esc | cerrar capas |

### URL

`?ep=quinto&frame=1234` abre el episodio en ese cuadro, en pausa. El visor mantiene la URL al día al pausar,
saltar o avanzar paso a paso (y una vez por segundo durante la reproducción): basta copiarla.

## Esquema del JSON

Ver `didactica/historia/record.py` y `src/types.ts`. Resumen:

```
episodio: { slug, titulo, subtitulo, fase1_titulo, fase2_titulo, lectura, has_phase1, action_names[] }
kb:       { theorem, steps[{key,title,text,deps[],distractor,qed,externo}], required[], min_len, depth{key:int} }
log[]:    líneas de la bitácora
milestones[]: { phase, episode, t, text }
curves:   { success1[], reward2[] }        # success1 tiene una entrada por generación no imposible
frames[]: { kind, phase, gen, t, eps, stats{…}, log_len, board?, action1?, policy1?, attempt?, greedy? }
```

`policy1` y `greedy` sólo vienen en algunos cuadros: el visor conserva el último visto (índices precalculados
en `src/state.ts`, de modo que saltar a cualquier cuadro es O(1)).

## Estructura

```
web/
  index.html            esqueleto de la página
  vite.config.ts        npm run dev abre en ?ep=quinto
  src/main.ts           carga del JSON, URL, teclado, orquestación
  src/types.ts          esquema del JSON
  src/state.ts          índices derivados, análisis del intento (motivos), veredicto
  src/player.ts         cursor, duraciones, velocidad, pausa en hitos
  src/ui/panels.ts      cabecera, intento, creencia, política, marcador, bitácora
  src/ui/controls.ts    botones, línea de tiempo, teclas
  src/ui/graph.ts       DAG del grafo de lemas
  src/ui/final.ts       panel de cierre
  src/boards/           euclides.ts · cuadratura.ts · quinto.ts (SVG a mano)
  src/style.css         paleta y distribución
  public/data/*.json    las grabaciones
  Makefile              make data
```
