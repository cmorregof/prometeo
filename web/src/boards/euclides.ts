// Antifairesis: por cada paso de `history`, dos barras (a naranja, b azul) a escala de a0,
// con marcas cada b unidades sobre la de a. Las filas viejas suben y se desvanecen; la
// actual brilla. Cuando llega una fila nueva, sus barras se acortan desde las de la anterior.

import type { Board, BoardEuclides, Frame } from '../types'
import type { BoardView } from './index'
import { clear, svgEl } from './svg'

const W = 800
const H = 420
const X0 = 64
const BARS_W = 720
const ROW_H = 30
const BAR_H = 12
const Y_LAST = 388

interface Row {
  g: SVGGElement
  ra: SVGRectElement
  rb: SVGRectElement
}

function isPrefix(p: [number, number][], h: [number, number][]): boolean {
  if (p.length > h.length) return false
  for (let i = 0; i < p.length; i++) if (p[i][0] !== h[i][0] || p[i][1] !== h[i][1]) return false
  return true
}

export class EuclidesBoard implements BoardView {
  private svg: SVGSVGElement
  private layer: SVGGElement
  private status: SVGTextElement
  private pair: SVGTextElement
  private rows = new Map<number, Row>()
  private prev: BoardEuclides | null = null
  private base = 0

  constructor(host: HTMLElement) {
    this.svg = svgEl('svg', { viewBox: `0 0 ${W} ${H}`, preserveAspectRatio: 'xMidYMid meet' })
    const leg = svgEl('text', { x: X0, y: 16, class: 'dim', 'font-size': 12 })
    leg.innerHTML =
      '<tspan fill="#e0873a">■</tspan> a   <tspan fill="#5b9dd9">■</tspan> b   <tspan fill="#fff">┃</tspan> cada b unidades sobre a: cuántas veces cabe'
    this.svg.appendChild(leg)
    this.pair = svgEl('text', { x: W - 8, y: 20, 'text-anchor': 'end', class: 'grande' })
    this.svg.appendChild(this.pair)
    this.status = svgEl('text', { x: W - 8, y: 48, 'text-anchor': 'end', class: 'grande' })
    this.svg.appendChild(this.status)
    this.layer = svgEl('g')
    this.svg.appendChild(this.layer)
    host.appendChild(this.svg)
  }

  headline(board: Board): string {
    const b = board as BoardEuclides
    const [a, bb] = b.history[b.history.length - 1]
    const st =
      b.last === 'ok'
        ? `<span class="ok">✔ medida común = ${b.gcd}</span>`
        : b.last === 'falso'
          ? `<span class="bad">✘ declaró en falso</span>`
          : b.last === 'resta'
            ? `<span class="go">… midiendo</span>`
            : ''
    return `<b>a = ${b.a0}, b = ${b.b0}</b> · mcd real = ${b.gcd} · paso ${b.n} · ahora (${a}, ${bb}) ${st}`
  }

  update(board: Board, _f: Frame, animate: boolean): void {
    const b = board as BoardEuclides
    const h = b.history
    const scale = BARS_W / b.a0
    let appendFrom = 0
    let rebuild = true
    if (animate && this.prev && this.prev.a0 === b.a0 && this.prev.b0 === b.b0) {
      const p = this.prev.history
      for (let k = 0; k <= p.length; k++) {
        if (isPrefix(p.slice(k), h)) {
          this.base += k
          appendFrom = p.length - k
          rebuild = false
          break
        }
      }
    }
    if (rebuild) {
      clear(this.layer)
      this.rows.clear()
      this.base = 0
      appendFrom = 0
    }
    // filas que salieron por arriba
    for (const [idx, row] of this.rows) {
      if (idx < this.base) {
        row.g.remove()
        this.rows.delete(idx)
      }
    }
    const last = h.length - 1
    for (let i = 0; i < h.length; i++) {
      const idx = this.base + i
      const [a, bb] = h[i]
      const y = Y_LAST - (last - i) * ROW_H
      const wa = Math.max(2, a * scale)
      const wb = Math.max(2, bb * scale)
      let row = this.rows.get(idx)
      if (!row) {
        row = this.makeRow(a, bb, scale)
        this.rows.set(idx, row)
        this.layer.appendChild(row.g)
        const isNew = i >= appendFrom && !rebuild
        if (isNew && i > 0) {
          // arranca con las longitudes de la fila anterior: se ve cortar
          const [pa, pb] = h[i - 1]
          row.ra.style.width = `${Math.max(2, pa * scale)}px`
          row.rb.style.width = `${Math.max(2, pb * scale)}px`
          row.g.style.opacity = '0'
          row.g.style.transform = `translate(0px, ${y + ROW_H}px)`
          void row.g.getBoundingClientRect()
        } else {
          row.g.style.transform = `translate(0px, ${y}px)`
        }
      }
      row.ra.style.width = `${wa}px`
      row.rb.style.width = `${wb}px`
      row.g.style.transform = `translate(0px, ${y}px)`
      row.g.style.opacity = i === last ? '1' : String(Math.max(0.15, 0.7 - (last - i) * 0.06))
      row.g.classList.toggle('actual', i === last)
    }
    const [a, bb] = h[last]
    this.pair.textContent = `(${a}, ${bb})`
    if (b.last === 'ok') {
      this.status.textContent = `✔ medida común = ${b.gcd}`
      this.status.setAttribute('class', 'grande verde')
    } else if (b.last === 'falso') {
      this.status.textContent = `✘ declaró en falso: ${bb} no mide a ${a}`
      this.status.setAttribute('class', 'grande rojo')
    } else {
      this.status.textContent = ''
    }
    this.prev = b
  }

  private makeRow(a: number, b: number, scale: number): Row {
    const g = svgEl('g', { class: 'fila' })
    g.appendChild(svgEl('text', { x: X0 - 8, y: BAR_H, 'text-anchor': 'end', class: 'dim', 'font-size': 12 }, String(a)))
    g.appendChild(svgEl('text', { x: X0 - 8, y: 2 * BAR_H + 2, 'text-anchor': 'end', class: 'dim', 'font-size': 12 }, String(b)))
    const ra = svgEl('rect', { class: 'bar-a', x: X0, y: 1, height: BAR_H, rx: 2, width: Math.max(2, a * scale) })
    const rb = svgEl('rect', { class: 'bar-b', x: X0, y: BAR_H + 3, height: BAR_H, rx: 2, width: Math.max(2, b * scale) })
    g.appendChild(ra)
    g.appendChild(rb)
    if (b > 0) {
      for (let k = 1; k * b < a; k++) {
        const x = X0 + k * b * scale
        g.appendChild(svgEl('line', { class: 'marca', x1: x, x2: x, y1: -1, y2: BAR_H + 2 }))
      }
    }
    return { g, ra, rb }
  }
}
