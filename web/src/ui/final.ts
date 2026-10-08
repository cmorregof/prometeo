// Panel de cierre: la lectura del episodio y la demostración final de la política voraz.

import { type Session } from '../state'
import { ambarHTML, proofHTML } from './panels'

export function renderFinal(sess: Session): void {
  const e = sess.rec.episodio
  const overlay = document.getElementById('overlay-final')!
  document.getElementById('final-titulo')!.firstChild!.textContent = `Lectura · ${e.titulo} `
  document.getElementById('final-lectura')!.textContent = e.lectura
  document.getElementById('final-teorema')!.textContent = `Teorema. ${sess.kb.theorem}`
  const g = sess.greedyAt(sess.n - 1)
  const ver = document.getElementById('final-veredicto')!
  const amb = document.getElementById('final-ambar')!
  const ol = document.getElementById('final-prueba')!
  if (g) {
    const v = sess.verdict(g)
    ver.innerHTML = `política voraz (sin explorar): ${v.html}`
    if (v.ambar.length) {
      amb.textContent = ambarHTML(v.ambar)
      amb.classList.remove('oculto')
    } else amb.classList.add('oculto')
    ol.innerHTML = proofHTML(sess.analyze(g))
  } else {
    ver.textContent = ''
    ol.innerHTML = ''
    amb.classList.add('oculto')
  }
  overlay.classList.remove('oculto')
}
