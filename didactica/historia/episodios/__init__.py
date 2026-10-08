"""Registro de episodios, en orden histórico."""

from . import beltrami, cuadratura, euclides_mcd, quinto_postulado

EPISODIOS = {
    e.EPISODIO.slug: e.EPISODIO
    for e in (euclides_mcd, cuadratura, quinto_postulado, beltrami)
}
ORDEN = list(EPISODIOS)
