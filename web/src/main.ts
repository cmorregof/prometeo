import './style.css'
import type { Recording } from './types'
import { Session } from './state'
import { Player, type FrameEvent } from './player'
import { Panels } from './ui/panels'
import { Controls } from './ui/controls'
import { renderGraph } from './ui/graph'
import { renderFinal } from './ui/final'
import { makeBoard, type BoardView } from './boards/index'

const ORDEN = ['euclides', 'cuadratura', 'quinto', 'beltrami'] as const
const NOMBRES: Record<string, string> = {
  euclides: '1 · Euclides: medir',
  cuadratura: '2 · Cuadratura',
  quinto: '3 · Quinto postulado',
  beltrami: '4 · Beltrami',
}

class App {
  private sess: Session | null = null
  private player: Player
  private panels = new Panels()
  private controls: Controls
  private board: BoardView | null = null
  private tablero = document.getElementById('tablero')!
  private select = document.getElementById('ep') as HTMLSelectElement
  private hideWorld = true
  private finalShown = false
  private lastUrl = 0

  constructor() {
    this.player = new Player([], (ev) => this.onFrame(ev), () => this.onState())
    this.controls = new Controls(this.player, {
      onGraph: () => this.showGraph(),
      onLectura: () => this.sess && renderFinal(this.sess),
      onEpisode: (k) => this.open(ORDEN[k]),
      onHideWorld: (v) => {
        this.hideWorld = v
        this.board?.setHideWorld?.(v)
        this.player.seek(this.player.cursor)
      },
    })
    for (const slug of ORDEN) {
      const o = document.createElement('option')
      o.value = slug
      o.textContent = NOMBRES[slug]
      this.select.appendChild(o)
    }
    this.select.onchange = () => this.open(this.select.value)
    document.querySelectorAll<HTMLElement>('[data-cierra]').forEach((b) => {
      b.onclick = () => document.getElementById(b.dataset.cierra!)!.classList.add('oculto')
    })
    document.querySelectorAll<HTMLElement>('.overlay').forEach((o) => {
      o.addEventListener('click', (ev) => {
        if (ev.target === o) o.classList.add('oculto')
      })
    })
    document.getElementById('btn-otra-vez')!.onclick = () => {
      document.getElementById('overlay-final')!.classList.add('oculto')
      this.player.seek(0)
      this.player.play()
    }
    window.addEventListener('popstate', () => this.fromUrl())
  }

  async start(): Promise<void> {
    await this.fromUrl()
  }

  private async fromUrl(): Promise<void> {
    const params = new URLSearchParams(location.search)
    const ep = params.get('ep') ?? 'quinto'
    const frame = params.get('frame')
    const slug = (ORDEN as readonly string[]).includes(ep) ? ep : 'quinto'
    await this.open(slug, frame !== null ? Number(frame) : undefined, false)
  }

  async open(slug: string, frame?: number, pushUrl = true): Promise<void> {
    if (this.sess && this.sess.rec.episodio.slug === slug && frame === undefined) return
    const cargando = document.getElementById('cargando')!
    cargando.classList.remove('oculto')
    this.player.pause()
    let rec: Recording
    try {
      const r = await fetch(`${import.meta.env.BASE_URL}data/${slug}.json`)
      if (!r.ok) throw new Error(`${r.status} ${r.statusText}`)
      rec = (await r.json()) as Recording
    } catch (e) {
      cargando.textContent = `no se pudo cargar data/${slug}.json: ${String(e)}`
      return
    }
    cargando.classList.add('oculto')
    cargando.textContent = 'cargando…'
    document.querySelectorAll('.overlay').forEach((o) => o.classList.add('oculto'))
    const sess = new Session(rec)
    this.sess = sess
    this.select.value = slug
    document.title = `${rec.episodio.titulo} · historia`
    this.panels.layout(rec.episodio.has_phase1)
    this.panels.reset(sess)
    this.controls.reset(sess)
    this.board = null
    this.tablero.innerHTML = ''
    const first = sess.frames[0]
    if (rec.episodio.has_phase1 && first.board) {
      this.board = makeBoard(first.board, this.tablero)
      this.board.setHideWorld?.(this.hideWorld)
    }
    this.player.setFrames(sess.frames)
    this.finalShown = false
    if (pushUrl) history.replaceState(null, '', `?ep=${slug}`)
    const f0 = frame !== undefined && Number.isFinite(frame) ? Math.max(0, Math.min(sess.n - 1, frame)) : 0
    this.player.seek(f0)
    if (frame === undefined) this.player.play()
  }

  private onFrame(ev: FrameEvent): void {
    const sess = this.sess
    if (!sess) return
    const i = ev.cursor
    const f = sess.frames[i]
    const prev = i > 0 && !ev.jumped ? sess.frames[i - 1] : null
    this.panels.header(sess, f, i)
    if (this.board && f.board) {
      this.board.update(f.board, f, !ev.jumped)
      this.panels.board(this.board.headline(f.board), f.action1)
    }
    this.panels.policy(sess, i)
    this.panels.proof(sess, f, prev)
    this.panels.belief(sess, i)
    this.panels.stats(sess, f)
    this.panels.log(sess, f, ev.newLog)
    this.controls.update(i, f.gen, f.phase)
    if (ev.reachedEnd && f.kind === 'final') {
      if (!this.finalShown) renderFinal(sess)
      this.finalShown = true
    } else this.finalShown = false
    const now = performance.now()
    if (ev.jumped || !this.player.playing || now - this.lastUrl > 1000) {
      this.lastUrl = now
      this.syncUrl()
    }
  }

  private onState(): void {
    this.controls.state()
    this.syncUrl()
  }

  private syncUrl(): void {
    if (!this.sess) return
    history.replaceState(null, '', `?ep=${this.sess.rec.episodio.slug}&frame=${this.player.cursor}`)
  }

  private showGraph(): void {
    const sess = this.sess
    if (!sess) return
    const f = sess.frames[this.player.cursor]
    const established = new Set<string>()
    if (f.phase === 2 && f.attempt) for (const [k, ok] of f.attempt) if (ok) established.add(k)
    renderGraph(sess, established, document.getElementById('grafo')!)
    document.getElementById('grafo-sub')!.textContent =
      f.phase === 2 ? `estado del intento en curso · generación ${f.gen} · mínimo ${sess.kb.min_len} pasos` : `todavía en la fase 1 · mínimo ${sess.kb.min_len} pasos`
    document.getElementById('overlay-grafo')!.classList.remove('oculto')
  }
}

new App().start()
