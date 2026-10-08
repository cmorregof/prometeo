// Botones, velocidad, línea de tiempo con hitos y atajos de teclado.

import { esc, type Session } from '../state'
import type { Player } from '../player'

const $ = (id: string): HTMLElement => {
  const el = document.getElementById(id)
  if (!el) throw new Error(`falta #${id}`)
  return el
}

export class Controls {
  private btnPlay = $('btn-play')
  private velocidad = $('velocidad')
  private timeline = $('timeline')
  private relleno = $('tl-relleno')
  private marcas = $('tl-marcas')
  private cursor = $('tl-cursor')
  private posicion = $('posicion')
  private chkPausa = $('chk-pausa') as HTMLInputElement
  private n = 1

  constructor(
    private player: Player,
    private hooks: { onGraph: () => void; onLectura: () => void; onEpisode: (k: number) => void; onHideWorld: (v: boolean) => void },
  ) {
    $('btn-inicio').onclick = () => player.seek(0)
    $('btn-atras').onclick = () => player.step(-1)
    $('btn-adelante').onclick = () => player.step(1)
    this.btnPlay.onclick = () => player.toggle()
    $('btn-menos').onclick = () => player.slower()
    $('btn-mas').onclick = () => player.faster()
    $('btn-grafo').onclick = () => hooks.onGraph()
    $('btn-lectura').onclick = () => hooks.onLectura()
    this.chkPausa.onchange = () => (player.pauseOnMilestone = this.chkPausa.checked)
    const chkOcultar = $('chk-ocultar') as HTMLInputElement
    chkOcultar.onchange = () => hooks.onHideWorld(chkOcultar.checked)
    this.timeline.onclick = (ev) => {
      const r = this.timeline.getBoundingClientRect()
      const frac = Math.max(0, Math.min(1, (ev.clientX - r.left) / r.width))
      player.seek(frac * (this.n - 1))
    }
    document.addEventListener('keydown', (ev) => this.onKey(ev))
  }

  private onKey(ev: KeyboardEvent): void {
    const t = ev.target as HTMLElement | null
    if (t && (t.tagName === 'INPUT' || t.tagName === 'SELECT' || t.tagName === 'TEXTAREA')) return
    const overlays = document.querySelectorAll('.overlay:not(.oculto)')
    if (ev.key === 'Escape') {
      overlays.forEach((o) => o.classList.add('oculto'))
      return
    }
    switch (ev.key) {
      case ' ':
        ev.preventDefault()
        this.player.toggle()
        break
      case 'ArrowLeft':
        ev.preventDefault()
        this.player.step(ev.shiftKey ? -25 : -1)
        break
      case 'ArrowRight':
        ev.preventDefault()
        this.player.step(ev.shiftKey ? 25 : 1)
        break
      case 'ArrowUp':
        ev.preventDefault()
        this.player.faster()
        break
      case 'ArrowDown':
        ev.preventDefault()
        this.player.slower()
        break
      case 'Home':
        this.player.seek(0)
        break
      case 'End':
        this.player.seek(this.player.n - 1)
        break
      case 'g':
        this.hooks.onGraph()
        break
      case 'l':
        this.hooks.onLectura()
        break
      case '1':
      case '2':
      case '3':
      case '4':
        this.hooks.onEpisode(Number(ev.key) - 1)
        break
    }
  }

  /** Marcas de hitos y divisor de fase para una grabación nueva. */
  reset(sess: Session): void {
    this.n = sess.n
    const parts: string[] = []
    if (sess.phase2Start < sess.n && sess.phase2Start > 0)
      parts.push(`<div class="tl-fase" style="left:${(100 * sess.phase2Start) / (sess.n - 1)}%"></div>`)
    sess.rec.log.forEach((line, k) => {
      const i = sess.milestoneFrame[k]
      const cls = /postulado|NUNCA|nunca/.test(line) ? 'ambar' : /∎|mínima|ESTO|redescubrió|distingue|reconoce|regla completa/.test(line) ? 'verde' : ''
      parts.push(`<div class="tl-marca ${cls}" style="left:${(100 * i) / (sess.n - 1)}%" title="${esc(line)}" data-frame="${i}"></div>`)
    })
    this.marcas.innerHTML = parts.join('')
    this.marcas.querySelectorAll<HTMLElement>('.tl-marca').forEach((m) => {
      m.onclick = (ev) => {
        ev.stopPropagation()
        this.player.seek(Number(m.dataset.frame))
      }
    })
    document.getElementById('lbl-ocultar')!.classList.toggle('oculto', sess.rec.episodio.slug !== 'quinto')
  }

  update(cursor: number, gen: number, phase: number): void {
    const frac = this.n > 1 ? cursor / (this.n - 1) : 0
    this.relleno.style.width = `${100 * frac}%`
    this.cursor.style.left = `${100 * frac}%`
    this.posicion.textContent = `cuadro ${cursor} / ${this.n - 1} · F${phase} gen ${gen}`
  }

  state(): void {
    this.btnPlay.textContent = this.player.playing ? '⏸' : '▶'
    this.velocidad.textContent = `${this.player.speed}×`
    this.chkPausa.checked = this.player.pauseOnMilestone
  }
}
