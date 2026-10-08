// DAG del grafo de lemas: capas por profundidad (hipótesis arriba, ∎ abajo), distractores en una
// fila aparte; nodos coloreados por el estado del intento en curso.

import { esc, type Session } from '../state'

export function renderGraph(sess: Session, established: Set<string>, host: HTMLElement): void {
  const W = 1000
  const H = 620
  const depths = sess.depths()
  const maxD = Math.max(0, ...depths.values())
  const layers = new Map<number, string[]>()
  for (const s of sess.coreSteps) {
    const d = depths.get(s.key) ?? 0
    if (!layers.has(d)) layers.set(d, [])
    layers.get(d)!.push(s.key)
  }
  const pos = new Map<string, [number, number]>()
  const NW = 118
  const NH = 40
  const top = 40
  const bottom = H - 110
  for (const [d, keys] of layers) {
    const y = maxD === 0 ? top : top + ((bottom - top) * d) / maxD
    keys.forEach((k, i) => pos.set(k, [((i + 1) * W) / (keys.length + 1), y]))
  }
  const dis = sess.kb.steps.filter((s) => s.distractor)
  dis.forEach((s, i) => pos.set(s.key, [((i + 1) * W) / (dis.length + 1), H - 40]))

  const parts: string[] = []
  parts.push(
    `<defs><marker id="flecha" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="#8b93a7"/></marker></defs>`,
  )
  for (const s of sess.coreSteps) {
    const [x1, y1] = pos.get(s.key)!
    for (const d of s.deps) {
      const [x0, y0] = pos.get(d)!
      const cls = established.has(d) ? (sess.step(d).externo ? 'ext' : 'est') : ''
      const ya = y0 + NH / 2
      const yb = y1 - NH / 2
      const c = (yb - ya) / 2
      parts.push(`<path class="arista ${cls}" d="M${x0} ${ya} C${x0} ${ya + c}, ${x1} ${yb - c}, ${x1} ${yb}" marker-end="url(#flecha)"/>`)
    }
  }
  parts.push(`<text x="${W - 8}" y="${H - 62}" text-anchor="end" fill="#d9534f" font-size="11">distractores (nunca válidos)</text>`)
  for (const s of sess.kb.steps) {
    const [x, y] = pos.get(s.key)!
    const cls = s.distractor ? 'dis' : established.has(s.key) ? (s.externo ? 'ext' : 'est') : 'no'
    const title = s.title.length > 20 ? s.title.slice(0, 19) + '…' : s.title
    parts.push(
      `<g class="nodo ${cls}"><title>${esc(s.key)} · ${esc(s.title)}\n${esc(s.text)}</title>` +
        `<rect x="${x - NW / 2}" y="${y - NH / 2}" width="${NW}" height="${NH}"/>` +
        `<text x="${x}" y="${y - 1}">${esc(s.key)}${s.qed ? ' ∎' : ''}</text>` +
        `<text class="titulo" x="${x}" y="${y + NH / 2 + 12}">${esc(title)}</text></g>`,
    )
  }
  host.innerHTML = `<svg viewBox="0 0 ${W} ${H}">${parts.join('')}</svg>`
}
