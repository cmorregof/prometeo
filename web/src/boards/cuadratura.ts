// Izquierda: la figura dada (rectángulo a×b o círculo de radio a). Derecha: el cuadrado de lado x,
// a la misma escala. Debajo, las longitudes trazadas S como segmentos rotulados. En modo círculo,
// una barra logarítmica con el mejor error, que baja y nunca llega al fondo.

import type { Board, BoardCuadratura, Frame } from '../types'
import type { BoardView } from './index'
import { clear, fmt, svgEl } from './svg'

const W = 800
const H = 420
const K = 30 // px por unidad de longitud
const MAX_SIDE = 8
const CX_FIG = 190
const CX_SQ = 560
const CY = 175
const LOG_MAX = 8 // la barra abarca de 10^0 a 10^-8

export class CuadraturaBoard implements BoardView {
  private svg: SVGSVGElement
  private figura: SVGGElement
  private cuadrado: SVGRectElement
  private cuadradoLabel: SVGTextElement
  private cuadradoLabel2: SVGTextElement
  private figuraLabel: SVGTextElement
  private trazadas: SVGGElement
  private progreso: SVGGElement
  private nivel: SVGRectElement
  private nivelLabel: SVGTextElement
  private contador: SVGTextElement

  constructor(host: HTMLElement) {
    this.svg = svgEl('svg', { viewBox: `0 0 ${W} ${H}`, preserveAspectRatio: 'xMidYMid meet' })
    this.figuraLabel = svgEl('text', { x: 20, y: 22, class: 'dim', 'font-size': 13 })
    this.cuadradoLabel = svgEl('text', { x: 420, y: 22, class: 'dim', 'font-size': 13 })
    this.cuadradoLabel2 = svgEl('text', { x: 420, y: 38, class: 'dim', 'font-size': 13 })
    this.figura = svgEl('g')
    this.cuadrado = svgEl('rect', { class: 'cuadrado', x: CX_SQ, y: CY, width: 0, height: 0 })
    this.trazadas = svgEl('g')
    this.progreso = svgEl('g')
    this.contador = svgEl('text', { x: 20, y: H - 6, 'font-size': 13 })
    // barra logarítmica (sólo círculo)
    this.progreso.appendChild(svgEl('rect', { class: 'progreso-fondo', x: 738, y: 40, width: 30, height: 270, rx: 4 }))
    this.nivel = svgEl('rect', { class: 'progreso-nivel', x: 738, y: 40, width: 30, height: 0, rx: 4 })
    this.progreso.appendChild(this.nivel)
    this.progreso.appendChild(svgEl('text', { x: 753, y: 32, 'text-anchor': 'middle', class: 'dim', 'font-size': 11 }, 'mejor error'))
    for (let e = 0; e <= LOG_MAX; e += 2) {
      const y = 40 + (e / LOG_MAX) * 270
      this.progreso.appendChild(svgEl('line', { x1: 730, x2: 738, y1: y, y2: y, stroke: '#8b93a7' }))
      this.progreso.appendChild(svgEl('text', { x: 726, y: y + 4, 'text-anchor': 'end', class: 'dim', 'font-size': 10 }, e === 0 ? '1' : `1e-${e}`))
    }
    this.progreso.appendChild(svgEl('text', { x: 753, y: 330, 'text-anchor': 'middle', class: 'ambar', 'font-size': 12, 'font-weight': 700 }, 'nunca 0'))
    this.nivelLabel = svgEl('text', { x: 720, y: 60, 'text-anchor': 'end', class: 'ambar', 'font-size': 11 })
    this.progreso.appendChild(this.nivelLabel)
    for (const el of [this.figuraLabel, this.cuadradoLabel, this.cuadradoLabel2, this.figura, this.cuadrado, this.trazadas, this.progreso, this.contador])
      this.svg.appendChild(el)
    host.appendChild(this.svg)
  }

  headline(board: Board): string {
    const b = board as BoardCuadratura
    const fig = b.task === 'rect' ? `rectángulo ${b.a}×${b.b}` : `círculo de radio ${b.a}`
    const st =
      b.last === 'ok'
        ? '<span class="ok">✔ cuadrado</span>'
        : b.last === 'falso'
          ? '<span class="bad">✘ declaró en falso</span>'
          : b.last === 'traza'
            ? '<span class="go">… trazando</span>'
            : ''
    return `<b>${fig}</b> · área = ${b.area.toFixed(4)} · lado buscado = ${Math.sqrt(b.area).toFixed(6)} · paso ${b.n} ${st}`
  }

  update(board: Board, _f: Frame, _animate: boolean): void {
    const b = board as BoardCuadratura
    clear(this.figura)
    if (b.task === 'rect') {
      const w = b.a * K
      const h = b.b * K
      this.figura.appendChild(svgEl('rect', { class: 'figura-rect', x: CX_FIG - w / 2, y: CY - h / 2, width: w, height: h }))
      this.figuraLabel.textContent = `rectángulo ${b.a} × ${b.b}   área ${fmt(b.area)}`
    } else {
      this.figura.appendChild(svgEl('circle', { class: 'figura-circ', cx: CX_FIG, cy: CY, r: b.a * K }))
      this.figuraLabel.textContent = `círculo de radio ${b.a}   área πr² = ${b.area.toFixed(3)}`
    }
    const side = Math.min(MAX_SIDE, b.x)
    const s = side * K
    const ok = b.err < 1e-9
    this.cuadrado.setAttribute('class', 'cuadrado' + (ok ? ' ok' : '') + (b.x > MAX_SIDE ? ' recortado' : ''))
    this.cuadrado.style.x = `${CX_SQ - s / 2}px`
    this.cuadrado.style.y = `${CY - s / 2}px`
    this.cuadrado.style.width = `${s}px`
    this.cuadrado.style.height = `${s}px`
    this.cuadradoLabel.textContent = `cuadrado de lado x = ${b.x.toFixed(5)}` + (b.x > MAX_SIDE ? '  (fuera de escala)' : '')
    this.cuadradoLabel2.textContent = `x² = ${(b.x * b.x).toFixed(3)}   err ${b.err.toExponential(1)}`
    this.cuadradoLabel2.setAttribute('class', ok ? 'verde' : 'dim')
    // longitudes trazadas
    clear(this.trazadas)
    this.trazadas.appendChild(svgEl('text', { x: 20, y: 352, class: 'dim', 'font-size': 12 }, 'longitudes trazadas (regla y compás):'))
    const S = b.S.slice(-9)
    S.forEach((v, i) => {
      const x = 20 + i * 78
      const len = Math.max(3, Math.min(70, v * 10))
      const isLast = i === S.length - 1
      this.trazadas.appendChild(svgEl('line', { class: 'seg' + (isLast ? ' ultimo' : ''), x1: x, x2: x + len, y1: 372, y2: 372 }))
      this.trazadas.appendChild(svgEl('text', { x, y: 392, 'font-size': 11, class: isLast ? '' : 'dim' }, fmt(v, 4)))
    })
    // círculo: barra logarítmica del mejor error
    if (b.task === 'circ') {
      this.progreso.style.display = ''
      const e = Math.max(b.best_err, 1e-12)
      const frac = Math.min(1, -Math.log10(e) / LOG_MAX)
      this.nivel.style.height = `${270 * frac}px`
      this.nivelLabel.textContent = b.best_err.toExponential(1)
      this.nivelLabel.setAttribute('y', String(40 + 270 * frac + 4))
      this.contador.textContent = `círculos intentados: ${b.circle_tries} · cuadrados: 0 · mejor aproximación hasta hoy: x = ${b.best_x.toFixed(6)}, err ${b.best_err.toExponential(1)}`
      this.contador.setAttribute('class', 'ambar')
    } else {
      this.progreso.style.display = 'none'
      this.contador.textContent = `rectángulos cuadrados hasta ahora: ${b.rect_ok}`
      this.contador.setAttribute('class', 'verde')
    }
  }
}
