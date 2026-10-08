// Esquema de web/public/data/<slug>.json, tal como lo escribe didactica/historia/record.py.

export type Kind = 'iter' | 'episode' | 'iter2' | 'final'

export interface Step {
  key: string
  title: string
  text: string
  deps: string[]
  distractor: boolean
  qed: boolean
  externo: boolean // postulado / cita: válido pero no derivado (ámbar)
}

export interface KB {
  theorem: string
  steps: Step[]
  required: string[]
  min_len: number
  depth: Record<string, number>
}

export interface EpisodioMeta {
  slug: string
  titulo: string
  subtitulo: string
  fase1_titulo: string
  fase2_titulo: string
  lectura: string
  has_phase1: boolean
  action_names: string[]
}

export interface Stats {
  ok: number
  fail: number
  imposible: number
  success100: number | null
  qed: number
  minimal: number
  success2_100: number | null
  best_reward: number | null
  updates: number
}

/** [clave del paso, ¿fue válido?] */
export type Attempt = [string, boolean][]

export interface PolicyRow {
  estado: string
  accion: string
  ok: boolean
  q: number[]
}

export interface BoardEuclides {
  a0: number
  b0: number
  history: [number, number][]
  last: '' | 'ok' | 'falso' | 'resta'
  gcd: number
  n: number
}

export interface BoardCuadratura {
  task: 'rect' | 'circ'
  a: number
  b: number
  area: number
  S: number[]
  x: number
  err: number
  best_err: number
  best_x: number
  rect_ok: number
  circle_tries: number
  last: '' | 'ok' | 'falso' | 'traza'
  n: number
}

export interface Chord {
  ang: number
  cut: boolean
  p: [number, number]
  q: [number, number]
}

export interface BoardQuinto {
  world: 'plano' | 'disco'
  px: number
  py: number
  chords: Chord[]
  parallels: number
  last: '' | 'ok' | 'falso' | 'adivinó' | 'traza'
  n: number
}

export type Board = BoardEuclides | BoardCuadratura | BoardQuinto

export interface Frame {
  kind: Kind
  phase: 1 | 2
  gen: number
  t: number
  eps: number
  stats: Stats
  log_len: number
  board?: Board
  action1?: string | null
  policy1?: PolicyRow[] // disperso: conservar el último
  attempt?: Attempt
  greedy?: Attempt // disperso: conservar el último
}

export interface Milestone {
  phase: number
  episode: number
  t: number
  text: string
}

export interface Recording {
  episodio: EpisodioMeta
  kb: KB
  log: string[]
  milestones: Milestone[]
  curves: { success1: number[]; reward2: number[] }
  frames: Frame[]
}
