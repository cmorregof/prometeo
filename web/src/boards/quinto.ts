// ¿Plano de Euclides o disco de Klein? El mundo se oculta hasta que el agente declara: sólo se ven
// la recta L, el punto P y las rectas trazadas por P (verde: no corta a L; roja punteada: corta).
// Al declarar, se revela: en el disco aparece el borde (las rectas son cuerdas); en el plano las
// rectas se prolongan por todo el panel.

import type { Board, BoardQuinto, Chord, Frame } from '../types'
import type { BoardView } from './index'
import { clear, svgEl } from './svg'

const W = 800
const H = 420
const CX = 400
const CY = 215
const R = 190
const BOX = { xmin: -CX / R, xmax: (W - CX) / R, ymin: -(H - CY) / R, ymax: CY / R }

type Mode = 'oculto' | 'disco' | 'plano'

function sx(x: number): number {
  return CX + x * R
}
function sy(y: number): number {
  return CY - y * R
}

/** Prolonga la recta pq hasta el borde del panel (Liang–Barsky). */
function extend(p: [number, number], q: [number, number]): [[number, number], [number, number]] {
  const dx = q[0] - p[0]
  const dy = q[1] - p[1]
  let t0 = -1e9
  let t1 = 1e9
  const clip = (den: number, num: number): void => {
    if (Math.abs(den) < 1e-12) return
    const t = num / den
    if (den < 0) t0 = Math.max(t0, t)
    else t1 = Math.min(t1, t)
  }
  clip(-dx, p[0] - BOX.xmin)
  clip(dx, BOX.xmax - p[0])
  clip(-dy, p[1] - BOX.ymin)
  clip(dy, BOX.ymax - p[1])
  return [
    [p[0] + t0 * dx, p[1] + t0 * dy],
    [p[0] + t1 * dx, p[1] + t1 * dy],
  ]
}

export class QuintoBoard implements BoardView {
  private svg: SVGSVGElement
  private disco: SVGCircleElement
  private Lext: SVGLineElement
  private L: SVGLineElement
  private cuerdas: SVGGElement
  private halo: SVGCircleElement
  private P: SVGCircleElement
  private mundo: SVGTextElement
  private contador: SVGTextElement
  private declaracion: SVGTextElement
  private leyenda: SVGTextElement
  private hideWorld = true
  private prev: BoardQuinto | null = null
  private mode: Mode = 'oculto'
  private drawn: SVGLineElement[] = []
  private lastFrame: Frame | null = null

  constructor(host: HTMLElement) {
    this.svg = svgEl('svg', { viewBox: `0 0 ${W} ${H}`, preserveAspectRatio: 'xMidYMid meet' })
    this.disco = svgEl('circle', { class: 'disco', cx: CX, cy: CY, r: R })
    this.Lext = svgEl('line', { class: 'recta-L ext', x1: 0, x2: W, y1: sy(0), y2: sy(0) })
    this.L = svgEl('line', { class: 'recta-L', x1: sx(-1), x2: sx(1), y1: sy(0), y2: sy(0) })
    this.cuerdas = svgEl('g')
    this.halo = svgEl('circle', { class: 'halo-P', r: 14 })
    this.P = svgEl('circle', { class: 'punto-P', r: 6 })
    this.mundo = svgEl('text', { x: 14, y: 26, class: 'mundo-oculto' })
    this.contador = svgEl('text', { x: W - 14, y: 34, 'text-anchor': 'end', class: 'enorme' })
    this.declaracion = svgEl('text', { x: CX, y: H - 14, 'text-anchor': 'middle', class: 'grande' })
    this.leyenda = svgEl('text', { x: 14, y: 48, class: 'dim', 'font-size': 12 })
    this.leyenda.innerHTML = '<tspan fill="#7fbf5a">━━</tspan> no corta a L   <tspan fill="#d9534f">╌╌</tspan> corta a L   <tspan fill="#c678dd">●</tspan> P   <tspan fill="#fff">━━</tspan> L'
    const Ltxt = svgEl('text', { x: sx(1) + 8, y: sy(0) + 5, 'font-size': 16, 'font-weight': 700 }, 'L')
    const Ptxt = svgEl('text', { class: 'ptxt', 'font-size': 16, 'font-weight': 700, fill: '#c678dd' }, 'P')
    for (const el of [this.disco, this.Lext, this.L, Ltxt, this.cuerdas, this.halo, this.P, Ptxt, this.mundo, this.contador, this.declaracion, this.leyenda])
      this.svg.appendChild(el)
    host.appendChild(this.svg)
  }

  setHideWorld(v: boolean): void {
    this.hideWorld = v
    if (this.prev) this.update(this.prev, this.lastFrame, false)
  }

  headline(board: Board): string {
    const b = board as BoardQuinto
    const declared = b.last === 'ok' || b.last === 'falso' || b.last === 'adivinó'
    const mundo = declared || !this.hideWorld ? `<b>${b.world}</b>` : '<b>¿?</b>'
    const st =
      b.last === 'ok'
        ? '<span class="ok">✔ declaró bien</span>'
        : b.last === 'falso'
          ? '<span class="bad">✘ declaró mal</span>'
          : b.last === 'adivinó'
            ? '<span class="bad">✘ declaró sin evidencia</span>'
            : b.last === 'traza'
              ? '<span class="go">… trazando</span>'
              : ''
    return `mundo oculto: ${mundo} · trazos ${b.chords.length} · no cortan a L: <b>${b.parallels}</b> ${st}`
  }

  update(board: Board, f: Frame | null, animate: boolean): void {
    const b = board as BoardQuinto
    if (f) this.lastFrame = f
    const declared = b.last === 'ok' || b.last === 'falso' || b.last === 'adivinó'
    const mode: Mode = declared || !this.hideWorld ? b.world : 'oculto'
    const sameEp =
      this.prev !== null && this.prev.world === b.world && this.prev.px === b.px && this.prev.py === b.py && this.mode === mode
    const prefix = sameEp && this.prev!.chords.length <= b.chords.length && this.prev!.chords.every((c, i) => c.ang === b.chords[i].ang)
    if (!(animate && prefix)) {
      clear(this.cuerdas)
      this.drawn = []
    }
    for (let i = this.drawn.length; i < b.chords.length; i++) {
      const el = this.chord(b.chords[i], mode)
      if (animate && prefix) el.classList.add('nueva')
      this.cuerdas.appendChild(el)
      this.drawn.push(el)
    }
    this.drawn.forEach((el, i) => el.classList.toggle('ultima', i === b.chords.length - 1))
    // mundo
    this.disco.style.opacity = mode === 'disco' ? '1' : '0'
    this.Lext.style.opacity = mode === 'plano' ? '1' : '0'
    if (mode === 'disco') {
      this.mundo.textContent = 'disco de Klein: las rectas son cuerdas'
      this.mundo.setAttribute('class', 'mundo-oculto revelado')
      this.mundo.setAttribute('fill', '#5b9dd9')
    } else if (mode === 'plano') {
      this.mundo.textContent = 'plano de Euclides'
      this.mundo.setAttribute('class', 'mundo-oculto revelado')
      this.mundo.setAttribute('fill', '#d6dae3')
    } else {
      this.mundo.textContent = 'mundo: ¿plano o disco?   (se revela cuando el agente declare)'
      this.mundo.setAttribute('class', 'mundo-oculto tachado')
      this.mundo.removeAttribute('fill')
    }
    // P
    const px = sx(b.px)
    const py = sy(b.py)
    this.P.setAttribute('cx', String(px))
    this.P.setAttribute('cy', String(py))
    this.halo.setAttribute('cx', String(px))
    this.halo.setAttribute('cy', String(py))
    const ptxt = this.svg.querySelector('.ptxt') as SVGTextElement
    ptxt.setAttribute('x', String(px + 12))
    ptxt.setAttribute('y', String(py - 10))
    // contador y declaración
    this.contador.textContent = `no cortan a L: ${b.parallels}`
    this.contador.setAttribute('class', 'enorme ' + (b.parallels >= 2 ? 'verde' : b.parallels === 1 ? '' : 'dim'))
    const accion = f?.action1 ?? ''
    if (b.last === 'ok') {
      this.declaracion.textContent = `✔ ${accion} — y era el ${b.world}`
      this.declaracion.setAttribute('class', 'grande verde')
    } else if (b.last === 'falso') {
      this.declaracion.textContent = `✘ ${accion} — pero era el ${b.world}`
      this.declaracion.setAttribute('class', 'grande rojo')
    } else if (b.last === 'adivinó') {
      this.declaracion.textContent = `✘ ${accion} — sin evidencia (menos de 2 trazos); era el ${b.world}`
      this.declaracion.setAttribute('class', 'grande rojo')
    } else {
      this.declaracion.textContent = ''
    }
    this.prev = b
    this.mode = mode
  }

  private chord(c: Chord, mode: Mode): SVGLineElement {
    let p = c.p
    let q = c.q
    if (mode === 'plano') [p, q] = extend(c.p, c.q)
    return svgEl('line', {
      class: 'cuerda ' + (c.cut ? 'corta' : 'paralela'),
      x1: sx(p[0]),
      y1: sy(p[1]),
      x2: sx(q[0]),
      y2: sy(q[1]),
    })
  }
}
