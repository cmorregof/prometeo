"""Beltrami (1868), Klein (1871): la geometría hiperbólica es tan consistente
como la euclidiana. Sólo fase 2: la demostración por modelo.

La idea que cierra el arco de las geometrías: no se demuestra que la
geometría hiperbólica sea "verdadera", se construye un modelo de ella DENTRO
de la euclidiana. Si la hiperbólica tuviera una contradicción, la traducción
de esa contradicción sería una contradicción euclidiana. Consistencia
relativa: exactamente la estrategia que Hilbert querrá para la aritmética y
que Gödel mostrará que no cierra sobre sí misma.
"""

from __future__ import annotations

from ..core import Episodio, ProofKB, Step

THEOREM = ("Si la geometría euclidiana es consistente, la geometría hiperbólica (I–IV más la negación del V) "
           "también lo es.")

STEPS = [
    Step("HE", "Hipótesis", "Supongamos consistente la geometría euclidiana del plano."),
    Step("MOD", "El modelo", "Dentro del plano euclidiano fijamos un círculo Γ. Llamamos 'punto' a cada punto interior de Γ y 'recta' a cada cuerda abierta de Γ.", ("HE",)),
    Step("V1", "Se cumple I", "Por dos puntos interiores pasa exactamente una cuerda: la recta euclidiana que los une, cortada por Γ.", ("MOD",)),
    Step("V2", "Se cumple II", "Una cuerda abierta no tiene extremos dentro del modelo: con la métrica de Cayley–Klein, d(P,Q) = ½|ln(P,Q;A,B)|, la longitud hacia el borde es infinita.", ("MOD",)),
    Step("V3", "Se cumplen III y IV", "Círculos y ángulos rectos se definen con esa métrica; los axiomas de congruencia se verifican en el modelo.", ("V2",)),
    Step("NEG5", "Se viola el V", "Dada una cuerda L y un punto P fuera de ella, hay infinitas cuerdas por P que no cortan a L dentro de Γ.", ("MOD",)),
    Step("TRAD", "Traducción", "Cada enunciado hiperbólico se traduce en un enunciado euclidiano sobre puntos y cuerdas de Γ, y cada demostración hiperbólica en una euclidiana.", ("V1", "V3", "NEG5")),
    Step("CONTRA", "Contrapositiva", "Si de I–IV y ¬V se dedujera una contradicción, su traducción sería una contradicción deducible en la geometría euclidiana.", ("TRAD",)),
    Step("QED", "Conclusión", "Eso contradice HE. Luego la geometría hiperbólica es consistente si la euclidiana lo es. ∎", ("CONTRA", "HE"), is_qed=True),
    # distractores
    Step("D_REP", "Saccheri", "La hipótesis del ángulo agudo es repugnante, luego el modelo no vale.", distractor=True),
    Step("D_VERDAD", "Distractor", "El modelo demuestra que el espacio físico es hiperbólico.", distractor=True),
    Step("D_ABS", "Distractor", "Esto demuestra la consistencia ABSOLUTA de la geometría hiperbólica.", distractor=True),
    Step("D_SUMA", "Distractor", "La suma de los ángulos de un triángulo es 180°, luego hay contradicción en el modelo.", distractor=True),
    Step("D_FIN", "Distractor", "Las cuerdas son finitas, luego se viola el postulado II.", distractor=True),
    Step("D_GAUSS", "Distractor", "Gauss no lo publicó por miedo a los beocios, luego no cuenta.", distractor=True),
]

EPISODIO = Episodio(
    slug="beltrami",
    titulo="Beltrami y Klein · la geometría hiperbólica es tan consistente como la euclidiana",
    subtitulo="no se demuestra que sea verdadera: se construye un modelo dentro de la de Euclides",
    fase1_titulo="",
    fase2_titulo="Fase 2 · demostrando la consistencia relativa por modelo",
    kb=ProofKB(THEOREM, STEPS),
    make_phase1=None,
    episodes2=3000,
    lectura=("Fíjense en el distractor D_ABS: el modelo NO da consistencia absoluta, la traslada a la geometría "
             "euclidiana, que a su vez se traslada (Descartes, Hilbert) a los números reales, que se trasladan a "
             "los naturales. Toda la cadena cuelga de la consistencia de la aritmética. Ese es el hilo que "
             "recogen Frege y Russell, y el que Gödel corta en 1931."),
)
