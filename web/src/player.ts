// Cursor sobre frames[] con reloj propio: cada clase de cuadro tiene su duración
// base, un multiplicador de velocidad y una pausa de 2,5 s cuando aparece un hito.

import type { Frame, Kind } from './types'

export const DWELL_MS: Record<Kind, number> = { iter: 60, iter2: 250, episode: 8, final: 0 }
export const SPEEDS = [0.25, 0.5, 1, 2, 4, 8]
export const MILESTONE_PAUSE_MS = 2500

export interface FrameEvent {
  cursor: number
  newLog: boolean // este cuadro trae líneas nuevas en la bitácora
  jumped: boolean // salto (línea de tiempo, URL, tecla): sin animaciones
  reachedEnd: boolean
}

export class Player {
  cursor = 0
  playing = false
  speedIdx = 2
  pauseOnMilestone = true
  private pauseUntil = 0
  private acc = 0
  private lastTs = 0
  private raf = 0

  constructor(
    private frames: Frame[],
    private onFrame: (ev: FrameEvent) => void,
    private onState: () => void,
  ) {}

  get speed(): number {
    return SPEEDS[this.speedIdx]
  }

  get n(): number {
    return this.frames.length
  }

  setFrames(frames: Frame[]): void {
    this.pause()
    this.frames = frames
    this.cursor = 0
    this.acc = 0
    this.pauseUntil = 0
  }

  play(): void {
    if (this.playing) return
    if (this.cursor >= this.n - 1) this.cursor = 0
    this.playing = true
    this.lastTs = performance.now()
    this.acc = 0
    this.raf = requestAnimationFrame((ts) => this.loop(ts))
    this.onState()
  }

  pause(): void {
    if (!this.playing) return
    this.playing = false
    cancelAnimationFrame(this.raf)
    this.onState()
  }

  toggle(): void {
    if (this.playing) this.pause()
    else this.play()
  }

  seek(i: number): void {
    this.cursor = Math.max(0, Math.min(this.n - 1, Math.round(i)))
    this.acc = 0
    this.pauseUntil = 0
    this.onFrame({ cursor: this.cursor, newLog: false, jumped: true, reachedEnd: this.cursor === this.n - 1 })
    this.onState()
  }

  step(delta: number): void {
    this.pause()
    const prev = this.frames[this.cursor]
    this.cursor = Math.max(0, Math.min(this.n - 1, this.cursor + delta))
    const newLog = delta > 0 && this.frames[this.cursor].log_len > prev.log_len
    this.onFrame({ cursor: this.cursor, newLog, jumped: Math.abs(delta) !== 1, reachedEnd: this.cursor === this.n - 1 })
    this.onState()
  }

  faster(): void {
    this.speedIdx = Math.min(SPEEDS.length - 1, this.speedIdx + 1)
    this.onState()
  }

  slower(): void {
    this.speedIdx = Math.max(0, this.speedIdx - 1)
    this.onState()
  }

  private loop(ts: number): void {
    if (!this.playing) return
    if (ts < this.pauseUntil) {
      this.lastTs = ts
      this.raf = requestAnimationFrame((t) => this.loop(t))
      return
    }
    this.acc += ts - this.lastTs
    this.lastTs = ts
    let advanced = false
    let newLog = false
    let guard = 0
    while (this.acc >= DWELL_MS[this.frames[this.cursor].kind] / this.speed && guard++ < 400) {
      if (this.cursor >= this.n - 1) break
      this.acc -= DWELL_MS[this.frames[this.cursor].kind] / this.speed
      const prevLog = this.frames[this.cursor].log_len
      this.cursor++
      advanced = true
      if (this.frames[this.cursor].log_len > prevLog) {
        newLog = true
        if (this.pauseOnMilestone) {
          this.pauseUntil = ts + MILESTONE_PAUSE_MS
          this.acc = 0
        }
        break
      }
    }
    const end = this.cursor >= this.n - 1
    if (advanced) this.onFrame({ cursor: this.cursor, newLog, jumped: false, reachedEnd: end })
    if (end) {
      this.playing = false
      this.onState()
      return
    }
    this.raf = requestAnimationFrame((t) => this.loop(t))
  }
}
