// Índices derivados de una grabación: última política/voraz vista, hitos → cuadro,
// análisis de un intento (motivo de cada paso inválido) y veredicto de la voraz.

import type { Attempt, Frame, KB, PolicyRow, Recording, Step } from './types'

export interface Line {
  key: string
  ok: boolean
  step: Step
  n: number // número de orden entre los válidos (0 si inválido)
  reason?: string // 'distractor' | 'repetido' | 'faltan: X, Y'
}

export interface Verdict {
  html: string
  finished: boolean
  clean: boolean
  minimal: boolean
  ambar: string[] // claves ámbar usadas (válidas)
}

export class Session {
  readonly frames: Frame[]
  readonly kb: KB
  readonly stepByKey = new Map<string, Step>()
  readonly lastPolicy: Int32Array
  readonly lastGreedy: Int32Array
  readonly milestoneFrame: number[] // línea k de la bitácora → primer cuadro en que existe
  readonly phase2Start: number
  readonly qedKey: string | null
  readonly coreSteps: Step[] // no distractores, en orden

  constructor(readonly rec: Recording) {
    this.frames = rec.frames
    this.kb = rec.kb
    for (const s of rec.kb.steps) this.stepByKey.set(s.key, s)
    this.coreSteps = rec.kb.steps.filter((s) => !s.distractor)
    this.qedKey = rec.kb.steps.find((s) => s.qed)?.key ?? null
    const n = this.frames.length
    this.lastPolicy = new Int32Array(n)
    this.lastGreedy = new Int32Array(n)
    let lp = -1
    let lg = -1
    let p2 = -1
    for (let i = 0; i < n; i++) {
      const f = this.frames[i]
      if (f.policy1) lp = i
      if (f.greedy) lg = i
      this.lastPolicy[i] = lp
      this.lastGreedy[i] = lg
      if (p2 < 0 && f.phase === 2) p2 = i
    }
    this.phase2Start = p2 < 0 ? n : p2
    this.milestoneFrame = []
    let k = 0
    for (let i = 0; i < n; i++) {
      while (k < this.frames[i].log_len) {
        this.milestoneFrame[k] = i
        k++
      }
    }
    while (k < rec.log.length) this.milestoneFrame[k++] = n - 1
  }

  get n(): number {
    return this.frames.length
  }

  step(key: string): Step {
    const s = this.stepByKey.get(key)
    if (!s) throw new Error(`paso desconocido: ${key}`)
    return s
  }

  policyAt(i: number): PolicyRow[] | null {
    const j = this.lastPolicy[i]
    return j >= 0 ? (this.frames[j].policy1 ?? null) : null
  }

  greedyAt(i: number): Attempt | null {
    const j = this.lastGreedy[i]
    return j >= 0 ? (this.frames[j].greedy ?? null) : null
  }

  /** Recalcula el motivo de cada paso inválido a partir del propio intento. */
  analyze(attempt: Attempt): Line[] {
    const established = new Set<string>()
    const out: Line[] = []
    let n = 0
    for (const [key, ok] of attempt) {
      const step = this.step(key)
      if (ok) {
        n++
        established.add(key)
        out.push({ key, ok, step, n })
        continue
      }
      let reason: string
      if (step.distractor) reason = 'distractor'
      else if (established.has(key)) reason = 'repetido'
      else {
        const missing = step.deps.filter((d) => !established.has(d))
        reason = missing.length ? `faltan: ${missing.join(', ')}` : 'inválido'
      }
      out.push({ key, ok, step, n: 0, reason })
    }
    return out
  }

  verdict(attempt: Attempt): Verdict {
    const valid = attempt.filter(([, ok]) => ok).map(([k]) => k)
    const clean = attempt.every(([, ok]) => ok)
    const finished = this.qedKey !== null && valid.includes(this.qedKey)
    const minimal = finished && clean && valid.length === this.kb.min_len
    const ambar = valid.filter((k) => this.step(k).externo)
    let html: string
    if (minimal) html = '<span class="v-ok">demostración mínima y correcta ✔</span>'
    else if (finished)
      html = '<span class="v-full">completa</span>' + (clean ? '' : ' <span class="v-bad">con saltos lógicos</span>')
    else html = '<span class="v-part">incompleta: no llega a ∎</span>'
    return { html, finished, clean, minimal, ambar }
  }

  /** Profundidad de todo paso no distractor (kb.depth sólo trae los requeridos). */
  depths(): Map<string, number> {
    const memo = new Map<string, number>()
    const d = (k: string): number => {
      const m = memo.get(k)
      if (m !== undefined) return m
      const s = this.step(k)
      const v = s.deps.length ? 1 + Math.max(...s.deps.map(d)) : 0
      memo.set(k, v)
      return v
    }
    for (const s of this.coreSteps) d(s.key)
    return memo
  }
}

export function fmtTime(t: number): string {
  if (t < 60) return `${t.toFixed(3)} s`
  const m = Math.floor(t / 60)
  return `${m} min ${(t - 60 * m).toFixed(1)} s`
}

export function esc(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
}
