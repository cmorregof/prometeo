// Paneles HTML: cabecera, intento en curso, creencia (voraz), política aprendida, marcador, bitácora.

import { esc, fmtTime, type Line, type Session } from '../state'
import type { Attempt, Frame, PolicyRow } from '../types'

const $ = <T extends HTMLElement = HTMLElement>(id: string): T => {
  const el = document.getElementById(id)
  if (!el) throw new Error(`falta #${id}`)
  return el as T
}

export function proofHTML(lines: Line[]): string {
  return lines
    .map((l) => {
      const t = esc(l.step.text)
      if (l.ok) {
        const cls = 'ok' + (l.step.externo ? ' externo' : '') + (l.step.qed ? ' qed' : '')
        const warn = l.step.externo ? '<span class="aviso">⚠ postulado / cita: no se deriva</span>' : ''
        return `<li class="${cls}" title="${esc(l.step.title)}"><span class="n">${l.n}.</span><b class="key">${esc(l.key)}</b><span class="txt">${warn}${t}</span></li>`
      }
      return `<li class="bad" title="${esc(l.step.title)}"><span class="n">✗</span><s class="key">${esc(l.key)}</s><span class="txt"><s>${t}</s><span class="motivo">${esc(l.reason ?? '')}</span></span></li>`
    })
    .join('')
}

export function chipsHTML(sess: Session, established: Set<string>): string {
  return sess.coreSteps
    .map((s) => {
      const cls = established.has(s.key) ? (s.externo ? 'ext' : 'est') : 'no'
      return `<span class="chip ${cls}" title="${esc(s.key)} · ${esc(s.title)}: ${esc(s.text)}">${esc(s.key)}</span>`
    })
    .join('')
}

export function ambarHTML(ambar: string[]): string {
  if (!ambar.length) return ''
  const n = ambar.length
  return `⚠ apoyada en ${n} postulado${n === 1 ? '' : 's'}/cita${n === 1 ? '' : 's'}: ${ambar.map(esc).join(', ')}`
}

function logClass(line: string): string {
  if (/postulado|NUNCA|nunca/.test(line)) return 'ambar'
  if (/∎|mínima|ESTO|redescubrió|distingue|reconoce|regla completa/.test(line)) return 'verde'
  return ''
}

export function sparkline(values: number[], lo: number, hi: number, color: string): string {
  const W = 200
  const H = 40
  if (!values.length) return ''
  const N = Math.min(values.length, 160)
  const pts: [number, number][] = []
  for (let k = 0; k < N; k++) {
    const i0 = Math.floor((k * values.length) / N)
    const i1 = Math.max(i0 + 1, Math.floor(((k + 1) * values.length) / N))
    let s = 0
    for (let i = i0; i < i1; i++) s += values[i]
    const v = s / (i1 - i0)
    const x = (k / Math.max(1, N - 1)) * W
    const y = hi === lo ? H / 2 : H - 2 - ((v - lo) / (hi - lo)) * (H - 4)
    pts.push([x, y])
  }
  const d = pts.map(([x, y], i) => `${i ? 'L' : 'M'}${x.toFixed(1)} ${y.toFixed(1)}`).join(' ')
  const area = `${d} L${W} ${H} L0 ${H} Z`
  return `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none"><path class="area" d="${area}" fill="${color}"/><path d="${d}" stroke="${color}"/></svg>`
}

export class Panels {
  private titulo = $('titulo')
  private subtitulo = $('subtitulo')
  private reloj = $('reloj')
  private fase = $('fase')
  private gen = $('gen')
  private pTablero = $('p-tablero')
  private tableroTitulo = $('tablero-titulo')
  private tableroCabecera = $('tablero-cabecera')
  private tableroAccion = $('tablero-accion')
  private pPolitica = $('p-politica')
  private politica = $('politica')
  private pIntento = $('p-intento')
  private intentoTitulo = $('intento-titulo')
  private intentoCabecera = $('intento-cabecera')
  private chips = $('chips')
  private intento = $<HTMLOListElement>('intento')
  private qed = $('qed')
  private pCreencia = $('p-creencia')
  private veredicto = $('veredicto')
  private ambarAviso = $('ambar-aviso')
  private teorema = $('teorema')
  private voraz = $<HTMLOListElement>('voraz')
  private marcador = $('marcador')
  private bitacora = $<HTMLOListElement>('bitacora')

  private renderedLog = -1
  private renderedGreedy = -2
  private renderedPolicy = -2
  private qedShown = false

  reset(sess: Session): void {
    const e = sess.rec.episodio
    this.titulo.textContent = e.titulo
    this.subtitulo.textContent = e.subtitulo
    this.tableroTitulo.textContent = e.fase1_titulo || 'Fase 1'
    this.intentoTitulo.textContent = e.fase2_titulo
    this.teorema.textContent = `Teorema. ${sess.kb.theorem}`
    this.renderedLog = -1
    this.renderedGreedy = -2
    this.renderedPolicy = -2
    this.qedShown = false
    this.qed.classList.remove('visible', 'destello')
    this.bitacora.innerHTML = ''
    this.intento.innerHTML = ''
    this.voraz.innerHTML = ''
    this.politica.innerHTML = ''
    this.chips.innerHTML = chipsHTML(sess, new Set())
  }

  header(sess: Session, f: Frame, i: number): void {
    this.reloj.textContent = `⏱ ${fmtTime(f.t)}`
    const done = i === sess.n - 1
    this.fase.textContent = done ? 'ENTRENAMIENTO TERMINADO' : `Fase ${f.phase}`
    this.fase.classList.toggle('terminado', done)
    this.gen.textContent = `generación ${f.gen}`
    const p1 = sess.rec.episodio.has_phase1
    if (p1) {
      this.pTablero.className = 'panel ' + (f.phase === 1 ? 'activa' : 'completada')
      this.pPolitica.className = 'panel ' + (f.phase === 1 ? 'activa' : 'completada')
    }
    this.pIntento.className = 'panel ' + (f.phase === 2 ? (done ? 'completada' : 'activa2') : '')
    this.pCreencia.className = 'panel ' + (f.phase === 2 ? 'activa2' : '')
  }

  board(headline: string, action: string | null | undefined): void {
    this.tableroCabecera.innerHTML = headline
    this.tableroAccion.textContent = `acción: ${action ?? '—'}`
  }

  policy(sess: Session, i: number): void {
    const j = sess.lastPolicy[i]
    if (j === this.renderedPolicy) return
    this.renderedPolicy = j
    const rows = sess.policyAt(i)
    if (!rows) {
      this.politica.innerHTML = '<div class="espera">todavía no ha aprendido nada</div>'
      return
    }
    this.politica.innerHTML = policyHTML(rows, sess.rec.episodio.action_names, sess.rec.episodio.slug)
  }

  proof(sess: Session, f: Frame, prev: Frame | null): void {
    if (f.phase !== 2 || !f.attempt) {
      this.intentoCabecera.innerHTML = '<span class="espera">en espera de la fase 1…</span>'
      this.intento.innerHTML = ''
      this.chips.innerHTML = chipsHTML(sess, new Set())
      return
    }
    const lines = sess.analyze(f.attempt)
    const valid = lines.filter((l) => l.ok)
    const nExt = valid.filter((l) => l.step.externo).length
    const nBad = lines.length - valid.length
    const finished = sess.qedKey !== null && valid.some((l) => l.key === sess.qedKey)
    this.intentoCabecera.innerHTML =
      `intento actual · <span class="ok">${valid.length}</span> pasos válidos · <span style="color:var(--amber)">${nExt}</span> postulados · ` +
      `<span class="bad">${nBad}</span> saltos lógicos` +
      (finished ? '  <span class="ok">∎ QED</span>' : '')
    this.chips.innerHTML = chipsHTML(sess, new Set(valid.map((l) => l.key)))
    this.intento.innerHTML = proofHTML(lines)
    this.intento.scrollTop = this.intento.scrollHeight
    // ∎ con destello al llegar
    const prevFinished = !!prev?.attempt && prev.phase === 2 && sess.qedKey !== null && prev.attempt.some(([k, ok]) => ok && k === sess.qedKey)
    if (finished && !this.qedShown) {
      this.qed.classList.add('visible')
      if (prev !== null && !prevFinished) {
        this.qed.classList.remove('destello')
        void this.qed.offsetWidth
        this.qed.classList.add('destello')
      }
    } else if (!finished && this.qedShown) {
      this.qed.classList.remove('visible', 'destello')
    }
    this.qedShown = finished
  }

  belief(sess: Session, i: number): void {
    const j = sess.lastGreedy[i]
    if (j === this.renderedGreedy) return
    this.renderedGreedy = j
    const g = sess.greedyAt(i)
    if (!g) {
      this.veredicto.innerHTML = '<span class="espera">en espera de la fase 2…</span>'
      this.ambarAviso.classList.add('oculto')
      this.voraz.innerHTML = ''
      return
    }
    const v = sess.verdict(g)
    this.veredicto.innerHTML = `política voraz (sin explorar): ${v.html}`
    if (v.ambar.length) {
      this.ambarAviso.textContent = ambarHTML(v.ambar)
      this.ambarAviso.classList.remove('oculto')
    } else this.ambarAviso.classList.add('oculto')
    this.voraz.innerHTML = proofHTML(sess.analyze(g))
  }

  stats(sess: Session, f: Frame): void {
    const s = f.stats
    const p1 = sess.rec.episodio.has_phase1
    const pct = (v: number | null): string => (v === null ? '—' : `${Math.round(100 * v)} %`)
    const rows: string[] = []
    const row = (k1: string, v1: string, k2: string, v2: string, c1 = '', c2 = ''): void => {
      rows.push(`<span class="k">${k1}</span><span class="v ${c1}">${v1}</span><span class="k">${k2}</span><span class="v ${c2}">${v2}</span>`)
    }
    row('⏱ entrenamiento', fmtTime(f.t), 'generación', String(f.gen))
    row('fase', `${f.phase}/2`, 'ε exploración', `${f.eps.toFixed(3)}<span class="eps"><i style="width:${(100 * f.eps).toFixed(1)}%"></i></span>`)
    if (p1) {
      const fails = `${s.fail}` + (s.imposible ? ` <span class="ambar">+${s.imposible} imposibles</span>` : '')
      row('F1 logros', String(s.ok), 'F1 fracasos', fails, 'verde', 'rojo')
      row('F1 éxito/100', pct(s.success100), 'Q updates', s.updates.toLocaleString('es'))
    } else row('Q updates', s.updates.toLocaleString('es'), '', '')
    row('F2 completas', String(s.qed), 'F2 mínimas', String(s.minimal), 'verde', 'verde')
    row('F2 éxito/100', pct(s.success2_100), 'F2 mejor retorno', s.best_reward === null ? '—' : (s.best_reward > 0 ? '+' : '') + s.best_reward.toFixed(1))
    if (p1) {
      const c1 = sess.rec.curves.success1.slice(0, s.ok + s.fail)
      rows.push(`<div class="spark"><span class="k">F1 éxito/100</span>${sparkline(c1, 0, 1, '#7fbf5a')}</div>`)
    }
    const c2 = f.phase === 2 ? sess.rec.curves.reward2.slice(0, f.gen) : []
    if (c2.length) {
      const lo = Math.min(...c2)
      const hi = Math.max(...c2)
      rows.push(`<div class="spark"><span class="k">F2 retorno</span>${sparkline(c2, lo, hi, '#c678dd')}</div>`)
    } else rows.push(`<div class="spark"><span class="k">F2 retorno</span><span class="dim">—</span></div>`)
    this.marcador.innerHTML = rows.join('')
  }

  log(sess: Session, f: Frame, highlightNew: boolean): void {
    const n = f.log_len
    if (n === this.renderedLog) return
    const lines = sess.rec.log.slice(0, n)
    const from = this.renderedLog
    this.bitacora.innerHTML = lines
      .map((l, k) => {
        const cls = [logClass(l), k === n - 1 ? 'actual' : '', highlightNew && k >= from && from >= 0 ? 'nueva' : ''].filter(Boolean).join(' ')
        return `<li class="${cls}" title="${esc(l)}">${esc(l)}</li>`
      })
      .join('')
    this.renderedLog = n
    this.bitacora.scrollTop = this.bitacora.scrollHeight
  }

  layout(hasPhase1: boolean): void {
    const app = document.getElementById('app')!
    app.classList.toggle('sin-fase1', !hasPhase1)
    const izq = document.getElementById('col-izq')!
    const der = document.getElementById('col-der')!
    if (hasPhase1) {
      this.pTablero.classList.remove('oculto')
      this.pPolitica.classList.remove('oculto')
      if (this.pCreencia.parentElement !== der) der.appendChild(this.pCreencia)
    } else {
      this.pTablero.classList.add('oculto')
      this.pPolitica.classList.add('oculto')
      if (this.pCreencia.parentElement !== izq) izq.appendChild(this.pCreencia)
    }
  }
}

function policyHTML(rows: PolicyRow[], actions: string[], slug: string): string {
  const tr = rows
    .map((r) => {
      const max = Math.max(...r.q)
      const q = r.q
        .map((v, i) => {
          const s = (v >= 0 ? '+' : '') + v.toFixed(1)
          const name = r.q.length === actions.length ? esc(actions[i]) : ''
          return v === max && r.q.length > 1 ? `<b title="${name}">${s}</b>` : `<span title="${name}">${s}</span>`
        })
        .join(' ')
      return `<tr><td class="estado">${esc(r.estado)}</td><td>→</td><td class="accion ${r.ok ? 'ok' : 'bad'}">${esc(r.accion)}</td><td class="${r.ok ? 'ok' : 'bad'}">${r.ok ? '✔' : '✘'}</td><td class="q">Q = ${q}</td></tr>`
    })
    .join('')
  const nota =
    slug === 'cuadratura'
      ? '<div class="nota">√(x·y) es la media geométrica (VI.13). Con x = a, y = b, el cuadrado de lado √(ab) tiene el área del rectángulo: eso es II.14. Para el círculo no hay secuencia que llegue.</div>'
      : slug === 'quinto'
        ? '<div class="nota">tras 2+ trazos: (trazos, cuántos no cortan) → acción con mayor Q</div>'
        : '<div class="nota">regla aprendida: estado → acción con mayor Q</div>'
  return `<table>${tr}</table>${nota}`
}

export function greedyOf(sess: Session, i: number): Attempt | null {
  return sess.greedyAt(i)
}
