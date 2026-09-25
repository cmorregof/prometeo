"""Nota técnica del aprendizaje verbal (PLAN_rl_verbal.md) en PDF, con el formato de la plantilla del autor.

Mismo preámbulo (byte a byte), mismo título, autor y secciones que la plantilla (docs/informes/ESPEC.md); los
párrafos literales se leen de la plantilla. Todo número sale de los datos: corpus/raices/*.json, sus validaciones,
cuaderno/glosario_verificacion.json, resultados/martillo_linea_base.json, resultados/martillo_pasos_demo.json,
resultados/pruebas_*.xml y logs/gasto.json. Un apéndice trae la escalera completa (los 48 enunciados congelados).
No ejecuta Isabelle ni modelos: solo lee y compila con latexmk.

Uso: .venv/bin/python tools/nota_rl_verbal.py [--sin-pdf]
Salida: docs/informes/rl_verbal/nota.tex, nota.pdf, unirl_definicion.bib
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "tools"))
from unirl import corpus, cuaderno as C, recompensa as R  # noqa: E402
from unirl.gd_isabelle import TheoremVerifier  # noqa: E402
from unirl.informe import BIB, compilar, escapar, lab, lista_etiquetas, literales, n_es, preambulo, tt  # noqa: E402
import corpus_raices as cr  # noqa: E402

OUT = HERE / "docs" / "informes" / "rl_verbal"
RAICES = HERE / "corpus" / "raices"
RES = HERE / "resultados"
METODOS = [("biseccion", "bisección"), ("punto_fijo", "punto fijo"), ("newton", "Newton"),
           ("ordenes", "órdenes de convergencia"), ("secante", "secante"), ("regula_falsi", "regula falsi")]
NOMBRE = dict(METODOS)
MESES = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
         "noviembre", "diciembre")

BIB_EXTRA = """
% [NV] Añadidas por tools/nota_rl_verbal.py solo a la copia de esta nota; sin verificar contra la fuente.
@inproceedings{Shinn2023,
  author    = {Shinn, Noah and Cassano, Federico and Berman, Edward and Gopinath, Ashwin and Narasimhan, Karthik and Yao, Shunyu},
  title     = {Reflexion: Language Agents with Verbal Reinforcement Learning},
  booktitle = {Advances in Neural Information Processing Systems 36 (NeurIPS 2023)},
  year      = {2023}
}

@inproceedings{PaulsonBlanchette2010,
  author    = {Paulson, Lawrence C. and Blanchette, Jasmin Christian},
  title     = {Three Years of Experience with {S}ledgehammer, a Practical Link between Automatic and Interactive Theorem Provers},
  booktitle = {Proceedings of the 8th International Workshop on the Implementation of Logics (IWIL 2010)},
  year      = {2010}
}

@book{NipkowPaulsonWenzel2002,
  author    = {Nipkow, Tobias and Paulson, Lawrence C. and Wenzel, Markus},
  title     = {{I}sabelle/{HOL}: A Proof Assistant for Higher-Order Logic},
  series    = {Lecture Notes in Computer Science},
  volume    = {2283},
  publisher = {Springer},
  year      = {2002}
}
"""

# ----------------------------------------------------------------------------- texto con matemáticas

_SUB = {"₀": "0", "₁": "1", "₂": "2", "ₙ": "n", "₊": "+", "₋": "-"}
_SUP = {"ⁿ": "n", "⁺": "+", "¹": "1", "²": "2"}
_MAT = {"≤": r"\le", "≥": r"\ge", "≠": r"\neq", "−": "-", "·": r"\cdot", "δ": r"\delta", "ε": r"\varepsilon",
        "φ": r"\varphi", "→": r"\to", "∃": r"\exists", "∈": r"\in", "⌈": r"\lceil", "⌉": r"\rceil"}
_LATIN = set("áéíóúÁÉÍÓÚñÑüÜ¿¡")


def _grupo(s: str, i: int) -> tuple[str, int]:
    """Tras un '^': un grupo entre paréntesis equilibrados, o una corrida de letras, cifras y paréntesis pegados."""
    if i < len(s) and s[i] == "(":
        d, j = 0, i
        while j < len(s):
            d += {"(": 1, ")": -1}.get(s[j], 0)
            j += 1
            if d == 0:
                break
        return s[i:j], j
    j = i
    while j < len(s) and (s[j].isalnum() or s[j] in "φ" or s[j] in _SUP):
        j += 1
        if j < len(s) and s[j] == "(":
            g, j = _grupo(s, j)
    return s[i:j], j


def en_mate(s: str) -> str:
    """Texto corto de los enunciados en modo matemático (sin delimitadores)."""
    out, i = [], 0
    while i < len(s):
        c = s[i]
        if c in _SUB or c in _SUP:
            tabla, marca = (_SUB, "_") if c in _SUB else (_SUP, "^")
            j = i
            while j < len(s) and s[j] in tabla:
                j += 1
            out.append(marca + "{" + "".join(tabla[x] for x in s[i:j]) + "}")
            i = j
        elif c == "^":
            g, i = _grupo(s, i + 1)
            out.append("^{" + en_mate(g) + "}")
        elif c == "√":
            j = i + 1
            while j < len(s) and s[j].isdigit():
                j += 1
            out.append(r"\sqrt{" + s[i + 1:j] + "}")
            i = j
        elif c in _MAT:
            out.append(_MAT[c] + (" " if _MAT[c].startswith("\\") else ""))
            i += 1
        elif c == "|":
            out.append("|")
            i += 1
        elif c in "{}":
            out.append("\\" + c)
            i += 1
        else:
            out.append(c)
            i += 1
    return "".join(out)


def es_tex(s: str) -> str:
    """Enunciado en español con Unicode matemático → LaTeX: lo que no es ASCII ni latino va en modo matemático."""
    out, i = [], 0
    while i < len(s):
        c = s[i]
        if c in _SUB or c in _SUP or c in _MAT or c in "√^":
            j = i
            while j < len(s) and (s[j] in _SUB or s[j] in _SUP):
                j += 1
            if c == "^":
                g, j = _grupo(s, i + 1)
                out.append("$^{" + en_mate(g) + "}$")
            elif c == "√":
                j = i + 1
                while j < len(s) and s[j].isdigit():
                    j += 1
                out.append("$" + en_mate(s[i:j]) + "$")
            else:
                j = max(j, i + 1)
                out.append("$" + en_mate(s[i:j]) + "$")
            i = j
        elif c == "|":
            out.append("$|$")
            i += 1
        elif ord(c) < 128:  # la corrida ASCII entera, para que escapar() separe las ligaduras ('' → ”)
            j = i
            while j < len(s) and ord(s[j]) < 128 and s[j] not in "|^":
                j += 1
            out.append(escapar(s[i:j]))
            i = j
        elif c in _LATIN:
            out.append(c)
            i += 1
        else:
            i += 1  # nada de Unicode fuera de lo admitido: se omite
    return "".join(out).replace("$$", "")


def isa(s: str, n: int | None = None) -> str:
    """Texto de Isabelle en su sintaxis ASCII, en \\texttt, con cortes. `\\<longlonglongrightarrow>` (límite de
    una sucesión) se escribe con su abreviatura ASCII de Isabelle, `---->`; delta y epsilon quedan como nombres."""
    s = s.replace("\\<longlonglongrightarrow>", "---->").replace("\\<delta>", "delta").replace("\\<epsilon>", "epsilon")
    return tt(s, n)


# ----------------------------------------------------------------------------- datos


def leer(ruta: Path, defecto=None):
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except Exception:
        return defecto


def pruebas() -> dict:
    """Conteos de resultados/pruebas_*.xml (pytest --junitxml)."""
    out = {}
    for f in sorted(RES.glob("pruebas_*.xml")):
        try:
            r = ET.parse(f).getroot()
            s = r if r.tag == "testsuite" else r.find("testsuite")
            out[f.stem.removeprefix("pruebas_")] = {k: int(s.get(k, 0)) for k in ("tests", "failures", "errors", "skipped")}
        except Exception:
            pass
    return out


def fecha_es(t: float | None = None) -> str:
    lt = time.localtime(t)
    return f"{lt.tm_mday} de {MESES[lt.tm_mon - 1]} de {lt.tm_year}"


# ----------------------------------------------------------------------------- secciones


def s_proposito(L: dict, ps: list[dict]) -> str:
    tr = [p for p in ps if p["split"] == "train"]
    te = [p for p in ps if p["split"] == "test"]
    return "\n".join([
        "\\section{Propósito}", "", L["proposito1"], "",
        "Esta nota plantea la pista de \\emph{aprendizaje verbal} del subproyecto 09. Un proponente de pesos congelados "
        "(\\texttt{gpt-\\allowbreak{}6-\\allowbreak{}luna}; como segundo modelo, \\texttt{gpt-\\allowbreak{}6-\\allowbreak{}sol}) intenta "
        f"demostrar en Isabelle/HOL \\citep{{NipkowPaulsonWenzel2002}} una escalera de {len(ps)} teoremas sobre cinco métodos de búsqueda "
        "de raíces y un grupo de lemas de órdenes de convergencia. Tras cada intento fallido reflexiona sobre los errores del kernel, al "
        "estilo de Reflexion \\citep{Shinn2023}. Entre episodios consulta un \\emph{cuaderno} persistente al que sólo entra lo que el juez "
        "verificó. Se actualiza el cuaderno, no los pesos: es aprendizaje en contexto con memoria curada, y así se reporta. Pregunta que "
        f"responde: con un cuaderno escrito en {len(tr)} peldaños de bisección, punto fijo, Newton y órdenes, ¿demuestra el proponente "
        f"más teoremas de dos métodos que nunca vio (secante y regula falsi, {len(te)} peldaños) que sin el cuaderno?", "",
        "Cinco principios, acordados antes de escribir código: (i) el kernel de Isabelle es la única fuente de verdad; (ii) el juez, y no el "
        "modelo, decide qué entra al cuaderno; (iii) todo enunciado redactado por un modelo pasa por revisión humana antes de usarse; "
        "(iv) lo que la automatización resuelve sola no da crédito; (v) todo lo que escribe el modelo se compila aislado, sin red y sin "
        "escritura fuera de su directorio.", "",
        "Esta nota sigue la estructura de la nota técnica: el MDP común (§2), la interfaz de verificador y sus tres instancias (§3), las "
        "funciones de recompensa (§4), las métricas (§5), la jerarquía de confianza entre jueces (§6) y los entornos (§7, "
        "Tabla~\\ref{tab:envs}). Cierra con lo hecho y lo previsto (§8). El Apéndice~\\ref{ap:escalera} trae los enunciados congelados "
        "completos.", ""])


def s_mdp(L: dict) -> str:
    d = L["def_mdp"].replace("$s_t = (T, \\mathcal{C}_t, h_t)$", "$s_t = (T, \\mathcal{C}_t, h_t, M)$")
    extra = ("  \\item \\textbf{Cuaderno} $M$: los lemas que el kernel verificó como enunciados independientes, con su procedencia "
             "(\\texttt{Cuaderno.thy}); los errores frecuentes, cada uno comprobado mecánicamente (\\texttt{errores.md}); y las "
             "estrategias que llevaron a demostraciones aceptadas, con contadores de intentos y éxitos (\\texttt{estrategias.md}). "
             "Sólo los episodios de entrenamiento escriben en él; la evaluación usa una copia congelada con su hash. El modelo está "
             "congelado: el cuaderno es contexto, no entrenamiento.\n")
    d = d.replace("  \\item \\textbf{Acción}", extra + "  \\item \\textbf{Acción}")
    return "\n".join([
        "\\section{El MDP común}", "", d, "",
        "En la pista verbal la acción y el presupuesto se concretan así:",
        "\\begin{itemize}",
        "  \\item Una acción es una sola llamada al modelo, que devuelve una reflexión breve sobre el intento anterior y una demostración "
        "Isar completa. La demostración puede traer lemas auxiliares con su demostración y marcar pasos con \\texttt{by martillo}, que "
        "el juez intenta cerrar con automatización (§3).",
        "  \\item Además hay \\emph{consultas}, gratuitas porque no cuentan como intento: buscar teoremas por patrón o por nombre, o "
        "comprobar si un hecho o un método existe. Se hacen hasta 4 por turno y 8 por episodio.",
        "  \\item El presupuesto es de $B = K = 4$ intentos por episodio. En la comparación entre modelos es $K = 3$, con un turno de "
        "consulta. Se registra en qué intento ocurre cada éxito.",
        "\\end{itemize}", "", L["obs_inmutable"], "",
        "\\begin{remark}[Escalera congelada]\nCada peldaño de la escalera lleva su hash congelado, su estado \\texttt{aprobado} y el "
        "registro de la aprobación humana (quién y cuándo). El cargador rechaza cualquier peldaño que no esté aprobado: sin aprobación "
        "no hay juez.\n\\end{remark}", ""])


def s_verificador(L: dict, base: dict, demo: dict | None, glos: dict | None) -> str:
    labels = lista_etiquetas("isabelle_teorema", TheoremVerifier.LABELS).replace(
        lab("SYNTAX_ERROR"), lab("SYNTAX_ERROR") + " (cadena o comentario sin cerrar)")
    out = ["\\section{La interfaz de verificador y sus tres instancias}", "", L["def_verificador"], "",
           "\\subsection{Juez de grafo de lemas ($V_G$)}", "",
           "Proviene de los subproyectos 01--05: el objetivo es un grafo de lemas escrito a mano, con distractores tomados de errores "
           "reales de estudiantes, y la propuesta es una cadena de lemas. En esta pista no se usa como juez. Sirve de fuente: la "
           "escalera de la bisección, el punto fijo, Newton y la secante sale de esos grafos, con los mismos pasos y los mismos "
           "errores tentadores, ahora como teoremas que hay que demostrar en lugar de nodos que hay que ordenar.", "",
           "\\subsection{Juez PEP ($V_P$)}", "",
           "Proviene del subproyecto 06: certifica cotas de peor caso de programas de tamaños de paso resolviendo un programa "
           "semidefinido, con certificado racional exacto \\citep{DroriTeboulle2014,TaylorHendrickxGlineur2017}. En esta pista no "
           "interviene; se menciona porque es el único juez de la serie independiente del grafo humano además de $V_I$.", "",
           "\\subsection{Juez Isabelle ($V_I$)}", "",
           "Proviene del subproyecto 08 y del marco de \\citet{BryantHuertaFoster2026}. En esta pista se usa su \\textbf{variante de "
           "teorema}: el objetivo es un teorema puro de Isabelle/HOL (preludio con las definiciones del método, variables fijadas, "
           "hipótesis con nombre y conclusión), congelado y aprobado. La propuesta es el texto Isar de la demostración y, "
           "opcionalmente, un bloque de lemas auxiliares con su demostración. El juez procede así.",
           "\\begin{enumerate}",
           "  \\item Filtro léxico: sólo texto de demostración. Nada de ML, \\texttt{sorry}, \\texttt{oops}, axiomas, definiciones ni "
           "nombres reservados, que son las etiquetas de las hipótesis, las constantes del preludio y \\texttt{isarl*}.",
           "  \\item Compila el peldaño con el texto del agente dentro de un contexto con las hipótesis. Comprueba que el enunciado leído "
           "antes y después del texto del agente coincide término a término.",
           "  \\item Exporta el teorema al contexto global instanciando por nombre cada variable, con "
           + tt("isarl_target[where v = v, OF assms]") + ", para que sólo dependa de las hipótesis congeladas.",
           "  \\item Comprueba en el kernel que no dependa de oráculos ni de \\texttt{skip\\_proof} y que no haya axiomas nuevos.",
           "\\end{enumerate}",
           "Cada compilación corre bajo \\texttt{sandbox-exec}, sin red externa ni escritura fuera de su directorio, y cada veredicto "
           "guarda la versión de Isabelle, la del juez, el límite de tiempo, la carga de la máquina y el hash del objetivo. "
           f"Etiquetas: {labels}.", "",
           "\\textbf{Martillo y consulta.} El martillo es \\texttt{try0} (5\\,s) y, si no cierra, Sledgehammer (60\\,s) "
           "\\citep{PaulsonBlanchette2010}. Se usa de dos maneras.",
           "\\begin{itemize}",
           "  \\item Solo, sobre la meta del peldaño: es la configuración A, la línea base.",
           "  \\item Sobre cada paso que el agente marca con \\texttt{by martillo}. Una primera pasada busca una línea para cada marca "
           "(caché, \\texttt{try0} o Sledgehammer) y sigue adelante. Luego se pegan las líneas y el juez compila la demostración completa "
           "sin atajos.",
           "\\end{itemize}",
           "Ninguna línea cuenta sin el kernel. Las llamadas al martillo van en serie, porque su límite es de tiempo real, y se "
           "guardan en una caché cuya clave es el enunciado, el cuaderno, los límites y la versión de Isabelle. La consulta lee el patrón "
           "del agente como dato, nunca como código, y lo pasa a \\texttt{find\\_theorems} en el mismo contexto que el juez; devuelve a lo "
           "sumo 20 teoremas.", ""]
    if glos:
        filas = glos.get("filas", [])
        out += [f"\\textbf{{Glosario.}} Los modelos escriben Lean con frecuencia. El glosario tiene {len(filas)} entradas de Lean a "
                "Isabelle, sacadas de los errores de las corridas anteriores. Se comprobó en Isabelle2025 "
                f"({'todas pasan' if glos.get('ok') else 'no todas pasan'}): cada nombre de Lean que desaconseja no existe y cada "
                "alternativa que recomienda sí existe. Así se siembra \\texttt{errores.md}.", ""]
    out.append(obs_existencia(base, demo))
    return "\n".join(out)


def obs_existencia(base: dict | None, demo: dict | None) -> str:
    frases = []
    if base and base.get("filas"):
        fs = base["filas"]
        res = [f for f in fs if f["resuelto_por_martillo"]]
        estado = "completa" if len(fs) == base.get("total", len(fs)) else f"en curso: {len(fs)} de {base.get('total')} peldaños"
        frases.append(f"En la línea base ({estado}), el martillo solo resuelve {len(res)} de {len(fs)} peldaños, con la línea "
                      "aceptada por el juez" + (": " + ", ".join(tt(f["id"], 40) for f in res) if res else "") + ".")
        agotados = sum(1 for f in fs if f.get("resultado_sh") == "timeout")
        frases.append((f"En los {agotados} que no cierra" if agotados == len(fs) - len(res) else
                       f"En {agotados} de los {len(fs) - len(res)} que no cierra") + ", Sledgehammer agota sus 60\\,s sin encontrar nada. "
                      "Los peldaños con definiciones recursivas (la bisección, las iteraciones) piden inducción, y Sledgehammer "
                      "no hace inducción.")
    if demo:
        frases.append(
            f"En cambio, en {tt(demo['peldano'], 30)}, con el esqueleto de la inducción escrito y el paso inductivo marcado "
            f"\\texttt{{by martillo}}, Sledgehammer encuentra la línea {tt(demo['linea'], 120)} y el juez acepta la "
            f"demostración completa: {n_es(demo['s_primera'], 0)}\\,s en total, búsqueda y verificación incluidas, y "
            f"{n_es(demo['s_cache'], 0)}\\,s la segunda vez, con la caché.")
    frases.append("Por eso la recompensa (§4) no premia lo que el martillo hace solo: el mérito está en el esqueleto.")
    return "\\begin{remark}[Existencia frente a descubrimiento]\\label{obs:existencia}\n" + " ".join(frases) + "\n\\end{remark}\n"


def s_recompensa(L: dict) -> str:
    return "\n".join([
        "\\section{Funciones de recompensa}", "", L["recompensa"], "",
        "\\subsection{En la pista verbal}",
        "Los pesos no se actualizan, así que la recompensa no entrena nada: es una \\emph{métrica}. Para un peldaño $T$ y un intento "
        "con resultado $o$,",
        "\\[",
        "  r_V(o) = \\rho(o) + b\\cdot\\mathbb{1}[o.\\texttt{accepted} = 1],",
        "\\]",
        "salvo en cuatro casos, en los que $r_V(o) = 0$:",
        "\\begin{itemize}",
        "  \\item el martillo solo resuelve el peldaño ($T \\in \\mathcal{M}$);",
        "  \\item la prueba del agente es sólo \\texttt{by martillo} sobre la meta;",
        "  \\item la prueba aceptada es una sola línea opaca;",
        "  \\item la etiqueta es \\textsc{Statement\\_Drift}, \\textsc{Unsound}, \\textsc{Syntax\\_Error} o \\textsc{Invalid\\_Proposal}.",
        "\\end{itemize}",
        f"Aquí $b = {n_es(R.BONO, 0)}$. $\\mathcal{{M}}$ son los peldaños que el martillo resuelve solo con el mismo cuaderno: sin esa "
        "línea base no se calcula $r_V$. $\\rho(o) = 1$ si la prueba se aceptó y, si no, la fracción de pasos \\texttt{by martillo} "
        "que el martillo cerró (0 sin marcas). Una línea es \\emph{opaca} si usa \\texttt{smt} o \\texttt{metis} con más de "
        f"{R.UMBRAL_HECHOS} hechos, contando los de su \\texttt{{using}}. Una prueba es \\emph{{una sola línea opaca}} si, quitando los "
        "cierres triviales (\\texttt{.}, \\texttt{..}, \\texttt{by simp}, \\texttt{by auto} y similares, sin argumentos), le queda "
        "una única invocación y es opaca. La regla, aprobada por el autor el 24 de septiembre, no cambia lo que acepta el kernel: sólo "
        "niega el crédito, porque eso es «el martillo lo hizo». Lo que entra al cuaderno se decide con reglas que no dependen de "
        "$r_V$:",
        "\\begin{itemize}",
        "  \\item \\textbf{Lemas}: sólo si el kernel los verifica como enunciados independientes. Se compilan a nivel de teoría, fuera "
        "del contexto con las hipótesis del peldaño, con el cuaderno previo como único contexto extra. Un lema que usa constantes del "
        "preludio de un método es de ese método; si no usa ninguna, es general. No puede tapar un hecho que ya exista.",
        "  \\item \\textbf{Errores}: de cualquier episodio de entrenamiento. Si afirman que un nombre o método existe o no, se "
        "comprueban mecánicamente.",
        "  \\item \\textbf{Estrategias}: sólo de episodios aceptados o que aportaron lemas verificados. Llevan contadores de intentos y "
        f"éxitos, y se descartan si tras {C.MIN_INTENTOS_ESTRATEGIA} usos su tasa de éxito es menor que "
        f"{n_es(C.UMBRAL_EXITO_ESTRATEGIA, 1)}.",
        "\\end{itemize}",
        "La recompensa por lemas parciales (crédito a lemas que el kernel acepta aunque la demostración falle) queda apagada: pertenece "
        "a la pista de programas y no se prueba ni se enciende en esta.", ""])


def s_metricas(L: dict, gasto: float, n_llamadas: int) -> str:
    # medida de la prueba privada de referencia (solo sus números: la prueba no sale de tests/fixtures)
    LEG = R.legibilidad((HERE / "tests" / "fixtures" / "pruebas_privadas" / "orden_1_lineal.txt").read_text(encoding="utf-8"))
    items = [
        "\\textbf{Intentos hasta aceptación}: $t^* \\le K$ por episodio, censurado en $K$, y en qué intento ocurre cada éxito.",
        "\\textbf{Distribución de etiquetas}: conteo de cada etiqueta de $V_I$ sobre todos los intentos. \\textsc{Syntax\\_Error} se "
        "cuenta aparte desde la Etapa 2; antes se confundía con la deriva.",
        "\\textbf{Razón de deriva}: \\textsc{Statement\\_Drift} frente a \\textsc{Proof\\_Failed}.",
        "\\textbf{Transferencia}: es la medida central de esta pista. Se mide la tasa de éxito en los peldaños de test (métodos que "
        "no aparecen en entrenamiento) con el cuaderno congelado (configuración E) frente a sin él (C). La comparación es pareada por "
        "peldaño, con conteo de pares discordantes y prueba exacta de McNemar. Se reporta por teorema y por nivel de dificultad; con "
        "sólo dos métodos en test no se remuestrea por método. \\texttt{secante\\_6c\\_orden\\_phi} se interpreta junto a "
        "\\texttt{newton\\_6c\\_q\\_orden2}, su análogo directo en entrenamiento.",
        "\\textbf{Comparación}: en lugar de comparar jueces, se comparan configuraciones (A, B0, B, C, D, E, F; §8) y modelos (Luna "
        "frente a Sol, pareados por peldaño y configuración, con el mismo presupuesto).",
        "\\textbf{Costo}: dólares reales de cada llamada según sus tokens (libro de gastos), segundos de modelo, de juez y de martillo, "
        "y consultas usadas.",
    ]
    return "\n".join(["\\section{Métricas}", "", L["metricas_intro"], "", "\\begin{enumerate}",
                      *[f"  \\item {x}" for x in items], "\\end{enumerate}", "",
                      "Además, cada prueba aceptada lleva una medida mecánica de \\emph{legibilidad}, que se reporta junto a la "
                      "tasa de éxito:",
                      "\\begin{itemize}",
                      "  \\item pasos explícitos (\\texttt{have}, \\texttt{show}, \\texttt{obtain});",
                      "  \\item invocaciones de métodos;",
                      "  \\item líneas opacas;",
                      "  \\item pasos cerrados por el martillo;",
                      "  \\item comentarios, líneas y caracteres.",
                      "\\end{itemize}",
                      "Es la respuesta al pedido del autor de que las demostraciones sean inteligibles. La prueba de referencia "
                      f"de \\texttt{{orden\\_1\\_lineal}}, por ejemplo, tiene {LEG['pasos_explicitos']} pasos explícitos, "
                      f"{LEG['invocaciones_no_triviales']} invocaciones no triviales y "
                      + ("ninguna línea opaca." if not LEG["opacas"] else f"{LEG['opacas']} líneas opacas."), "",
                      f"Aún no hay corridas con modelo en esta pista: el libro de gastos registra {n_llamadas} llamadas y "
                      f"\\${n_es(gasto, 2)}. Los únicos valores medidos son los del juez y el martillo (§3 y §8).", ""])


def s_jerarquia(L: dict, ps: list[dict], vexp: dict, viso: dict) -> str:
    deb = [p for p in ps if p.get("version") == "debilitada"]
    arr = [p for p in ps if (p.get("debilitacion") or "").startswith("arrastra")]
    num = [p for p in ps if p.get("comprobacion_numerica")]
    num_ok = [p for p in num if p["comprobacion_numerica"].get("cumplen") == p["comprobacion_numerica"].get("casos")]
    exp_ok = sum(1 for v in vexp.values() if v.get("exporta") and v.get("skip_proof_detectado"))
    met_ok = sum(1 for v in viso.values() if v.get("ok"))
    r = ("la adecuación de cada enunciado congelado al teorema que se quería. Los redactó Claude a partir de los grafos de 01--05 y de "
         "la literatura clásica, y el autor los revisó y aprobó uno por uno: esa revisión es la frontera semántica. Para acotarla, "
         f"{len(deb)} peldaños quedaron marcados como versiones debilitadas y cada uno tiene su versión clásica en la escalera. "
         f"{len(arr)} peldaños quedaron marcados porque arrastran hipótesis que no usan. Además hubo tres comprobaciones mecánicas. "
         f"Isabelle leyó y tipó las hipótesis y la conclusión de cada método ({met_ok} de {len(viso)} métodos). Una interpretación "
         "con valores concretos mostró que las hipótesis no son contradictorias. Una comprobación numérica ejecutó el método con "
         "problemas aleatorios y confirmó la conclusión en todos los casos "
         f"({len(num_ok)} de {len(num)} peldaños con comprobación). La teoría final de cada peldaño exporta el teorema y detecta un "
         f"\\texttt{{sorry}} de prueba como \\texttt{{skip\\_proof}} en {exp_ok} de {len(vexp)} peldaños. Se importa HOL-Analysis "
         "como matemática de confianza.")
    viejo = ("La Observación 2 muestra que incluso lo que el artículo de referencia reporta como ``automático'' contiene "
             "decisiones humanas en esa frontera.")
    assert viejo in L["jerarquia"], "cambió el párrafo de la plantilla"
    # en esta nota la Observación 2 es otra: la frase remite a la medición del subproyecto 08, que es de donde viene
    jer = L["jerarquia"].replace(viejo, "Al reproducir la bisección de \\citet{BryantHuertaFoster2026} en el subproyecto 08 se "
                                        "vio que incluso lo que el artículo reporta como ``automático'' contiene decisiones "
                                        "humanas en esa frontera.")
    return "\\section{Jerarquía de confianza entre jueces}\n\n" + jer + "\n\n\\textbf{Residuo en esta pista:} " + r + "\n"


def s_entornos(ps: list[dict], base: dict | None) -> str:
    resueltos = {f["id"]: f["resuelto_por_martillo"] for f in (base or {}).get("filas", [])}
    filas = []
    for m, nombre in METODOS:
        g = [p for p in ps if p["metodo"] == m]
        if not g:
            continue
        cl = sum(p.get("version") == "clasica" for p in g)
        dif = sorted(p["dificultad"] for p in g)
        hechos = [p for p in g if p["id"] in resueltos]
        mart = f"{sum(resueltos[p['id']] for p in hechos)} de {len(hechos)}" if hechos else "---"
        filas.append(f"{nombre} & {g[0]['split']} & {len(g)} & {cl} & {len(g) - cl} & {dif[0]}--{dif[-1]} & {mart} \\\\")
    tot = []
    for split in ("train", "test"):
        g = [p for p in ps if p["split"] == split]
        hechos = [p for p in g if p["id"] in resueltos]
        mart = f"{sum(resueltos[p['id']] for p in hechos)} de {len(hechos)}" if hechos else "---"
        cl = sum(p.get("version") == "clasica" for p in g)
        tot.append(f"\\textbf{{total {split}}} & & {len(g)} & {cl} & {len(g) - cl} & & {mart} \\\\")
    cuenta = Counter((p["split"], p["dificultad"]) for p in ps)
    dfil = [f"{s} & " + " & ".join(str(cuenta.get((s, d), 0)) for d in range(1, 6)) + f" & {sum(cuenta.get((s, d), 0) for d in range(1, 6))} \\\\"
            for s in ("train", "test")]
    return "\n".join([
        "\\section{Entornos}", "",
        "El entorno de esta pista es la escalera \\texttt{corpus/raices}: peldaños pequeños por método, del paso elemental al teorema "
        "de convergencia con su orden. La separación entre entrenamiento y test es por método completo, peldaños bajos incluidos. Así "
        "el test mide transferencia a métodos no vistos y no a variantes de un mismo método.", "",
        "\\begin{table}[h]", "\\centering", "\\footnotesize",
        "\\begin{tabular}{@{}llrrrcr@{}}", "\\toprule",
        "método & split & peldaños & clásicos & debilitados & dificultad & resueltos por el martillo \\\\", "\\midrule",
        *filas, "\\midrule", *tot, "\\bottomrule", "\\end{tabular}",
        "\\caption{Escalera de búsqueda de raíces. Un peldaño debilitado añade hipótesis o fija constantes respecto del enunciado "
        "clásico; cada uno tiene su versión clásica en la escalera. La dificultad va de 1 (un paso) a 5 (orden de convergencia clásico). "
        "La última columna es la línea base de la configuración A (§3); sin línea base, un guion. El proponente es "
        "\\texttt{gpt-6-luna} con esfuerzo alto; \\texttt{gpt-6-sol}, sólo en la comparación pareada sobre test.}",
        "\\label{tab:envs}", "\\end{table}", "",
        "\\begin{center}", "\\footnotesize", "\\begin{tabular}{@{}lrrrrrr@{}}", "\\toprule",
        "split & dif.~1 & dif.~2 & dif.~3 & dif.~4 & dif.~5 & total \\\\", "\\midrule", *dfil, "\\bottomrule",
        "\\end{tabular}", "\\end{center}", ""])


def s_experimentos(ps: list[dict], base: dict | None, demo: dict | None, glos: dict | None, prs: dict, viso: dict,
                   vexp: dict, comentario: str | None) -> str:
    tr = sum(p["split"] == "train" for p in ps)
    te = len(ps) - tr
    rap, isa_ = prs.get("rapidas"), prs.get("isabelle")

    def cuenta(x):
        if not x:
            return "---"
        mal = x["failures"] + x["errors"]
        return f"{x['tests'] - mal - x['skipped']} de {x['tests']} pasan" + (f" ({mal} fallan)" if mal else "")
    items = [
        "\\textbf{Etapa 0, plan.} Inventario del código, del juez y de los costos medidos, y plan por etapas. El autor lo aprobó con "
        "ajustes: glosario y consulta en el entorno base, teoremas puros primero, test por método y presupuesto con tope en dólares.",
        f"\\textbf{{Etapa 1, escalera.}} {len(ps)} peldaños ({tr} de entrenamiento y {te} de test), todos aprobados por el autor. "
        f"Validación en Isabelle de {sum(v.get('ok', False) for v in viso.values())} de {len(viso)} métodos; exportación y detección "
        f"de \\texttt{{sorry}} en {sum(1 for v in vexp.values() if v.get('exporta') and v.get('skip_proof_detectado'))} de "
        f"{len(vexp)} peldaños.",
        "\\textbf{Etapa 2, juez robusto.} Juez por peldaño, etiqueta \\textsc{Syntax\\_Error}, exportación con instanciación por "
        "nombre, aislamiento con \\texttt{sandbox-exec} (escribir fuera y la red externa quedan bloqueados), metadatos en cada "
        "veredicto y libro de gastos con tope en dólares.",
        ("\\textbf{Etapa 3, martillo.} " if base and len(base.get("filas", [])) == base.get("total") else
         "\\textbf{Etapa 3, martillo (en curso).} ")
        + (f"Línea base de la configuración A: {len(base['filas'])} de {base.get('total')} peldaños medidos, "
           f"{(lambda k: f'{k} resuelto' if k == 1 else f'{k} resueltos')(sum(f['resuelto_por_martillo'] for f in base['filas']))} por el martillo solo, "
           f"{n_es(sum(f['s'] for f in base['filas']) / max(1, len(base['filas'])), 0)}\\,s de media por peldaño. "
           + ("Cuatro peldaños se repitieron porque el Mac se suspendió durante la búsqueda: el límite de Sledgehammer "
              "corre en tiempo de pared y la suspensión lo consumía. Ahora el martillo compara el reloj de pared con el "
              "monótono, descarta y repite toda búsqueda con suspensión, y las corridas van bajo \\texttt{caffeinate}. "
              if any(f.get("suspension_s") is not None for f in base["filas"]) else "")
           if base and base.get("filas") else "")
        + (f"Martillo por pasos comprobado en {tt(demo['peldano'], 30)} (Observación~\\ref{{obs:existencia}}). " if demo else "")
        + (f"Glosario comprobado ({len(glos.get('filas', []))} entradas) y errores del cuaderno sembrados desde él. " if glos else "")
        + "Consulta de teoremas con saneado y tope.",
        "\\textbf{Etapa 4, recompensa y admisión.} Se implementaron $r_V$ con la regla de la línea opaca, la legibilidad y "
        "las reglas de admisión al cuaderno. Se comprobaron en Isabelle: entran un lema general y uno de bisección con su "
        "preludio. Se rechazan tres: uno falso, uno que usaba la hipótesis \\texttt{ab} del peldaño y uno que se llamaba "
        "\\texttt{mult\\_left\\_mono} (taparía el de Isabelle).",
    ]
    if rap or isa_:
        items.append(f"\\textbf{{Pruebas automáticas.}} Rápidas: {cuenta(rap)}. Con Isabelle: {cuenta(isa_)}.")
    prev = [
        "\\textbf{Etapa 5}: el bucle de reflexión con $K$ intentos, consultas en lotes y topes de llamadas por fase. La "
        "instrucción al proponente pide demostraciones inteligibles: Isar estructurado, un paso por idea, hipótesis citadas "
        "por su nombre y un comentario breve en español en cada paso no trivial. Cada prueba aceptada irá completa en el "
        "informe final.",
        "\\textbf{Etapa 6}: el cuaderno (\\texttt{Cuaderno.thy}, \\texttt{errores.md}, \\texttt{estrategias.md}), con admisión por "
        "el juez; sólo lo escribe el entrenamiento.",
        "\\textbf{Etapa 7}: los experimentos. Configuraciones: A (martillo solo); B0 (proponente y martillo, sin glosario, consulta "
        "ni reintentos); B (B0 con glosario y consulta); C (B con reintentos y reflexión); D (C con el cuaderno de errores); E (D con "
        "los lemas); F (E con las estrategias). Primera ronda: A, B0, B, C y E; luego Sol en C y E sobre test.",
    ]
    presupuesto = [
        "\\begin{center}", "\\footnotesize", "\\begin{tabular}{@{}lrrr@{}}", "\\toprule",
        "fase & llamadas & con 20\\,\\% & costo \\\\", "\\midrule",
        "cuaderno (Luna, train) & 197 & 236 & \\$1{,}54 \\\\",
        "evaluación completa (Luna, test, 2 episodios) & 512 & 614 & \\$3{,}99 \\\\",
        "comparación pareada (Luna, C y E, $K = 3$) & 128 & 154 & \\$1{,}00 \\\\",
        "comparación pareada (Sol, C y E, $K = 3$) & 128 & 154 & \\$19{,}97 \\\\",
        "\\midrule", "total & & & \\$26{,}50 \\\\", "\\bottomrule", "\\end{tabular}", "\\end{center}",
        "Costos estimados con 5\\,000 tokens de entrada y 12\\,000 de salida por llamada, a precios de lista. El tope del libro de "
        "gastos es \\$25; sube a \\$28 sólo si el costo medido de Sol lo exige, y antes de usar Sol se miden 3 llamadas. La "
        "evaluación de Luna conserva sus 2 episodios por peldaño, que miden la variabilidad dentro de un mismo modelo.",
    ]
    out = ["\\section{Experimentos realizados y previstos}", "", "Hecho hasta el " + fecha_es() + ":", "\\begin{enumerate}",
           *[f"  \\item {x}" for x in items], "\\end{enumerate}", "", "Previsto:", "\\begin{enumerate}",
           *[f"  \\item {x}" for x in prev], "\\end{enumerate}", "", *presupuesto, ""]
    if comentario:
        out += ["\\begin{remark}[Interpretación]", comentario.strip(), "\\end{remark}", ""]
    return "\n".join(out)


def apendice(ps: list[dict]) -> str:
    out = ["\\appendix", "\\section{La escalera completa}\\label{ap:escalera}", "",
           "\\raggedright  % texto de Isabelle en \\texttt: sin justificar, para que las líneas no se salgan del margen", "",
           "Enunciados congelados y aprobados, en la sintaxis ASCII de Isabelle (\\texttt{<=} es $\\le$, \\texttt{|x|} es el valor "
           "absoluto, \\texttt{!!} y \\texttt{ALL} son cuantificadores universales, \\texttt{\\%x.} es $\\lambda x.$). Cada peldaño da "
           "su identificador, su split, su dificultad, su versión y el enunciado en español con el que se aprobó.", ""]
    for m, nombre in METODOS:
        g = sorted([p for p in ps if p["metodo"] == m], key=lambda p: cr_orden(p))
        if not g:
            continue
        out += [f"\\subsection{{{nombre[0].upper() + nombre[1:]} ({g[0]['split']})}}", ""]
        pre = (cr.PRELUDIO.get(m) or "").strip()
        if pre:
            out += ["{\\footnotesize Preludio: " + isa(" ".join(pre.split()), None) + "\\par}", ""]
        out.append("\\begin{itemize}")
        for p in g:
            extra = []
            if p.get("version") == "debilitada" and p.get("version_clasica"):
                extra.append(f"clásica: {tt(p['version_clasica'], 40)}")
            if (p.get("debilitacion") or "").startswith("arrastra"):
                extra.append(es_tex(p["debilitacion"]))
            if p.get("analogo"):
                extra.append(f"análogo: {tt(p['analogo'], 40)}")
            version = {"clasica": "clásica", "debilitada": "debilitada"}.get(p.get("version"), p.get("version"))
            cab = (f"{tt(p['id'], 60)} ({p['split']}, dificultad {p['dificultad']}, {version}"
                   + ("; " + "; ".join(extra) if extra else "") + ")")
            enun = (f"\\textbf{{fixes}} {isa(' '.join(p['fixes'].split()), None)}"
                    + (f" \\textbf{{assumes}} {isa(' '.join(p['assumes'].split()), None)}" if p['assumes'].strip() else "")
                    + f" \\textbf{{shows}} {isa(' '.join(p['concl'].split()), None)}")
            out.append(f"  \\item {cab}. {es_tex(p['statement_es'])}\\\\\n  {{\\footnotesize {enun}\\par}}")
        out += ["\\end{itemize}", ""]
    return "\n".join(out)


def cr_orden(p: dict):
    """Por número de peldaño; la versión clásica (p. ej. 5c) justo después de la débil (5)."""
    m = re.match(r"(\d+)(.*)", str(p["peldano"]))
    return (int(m.group(1)), m.group(2), p["id"]) if m else (99, str(p["peldano"]), p["id"])


# ----------------------------------------------------------------------------- documento


def documento() -> str:
    L = literales()
    ps = corpus.usables()
    viso = leer(RAICES / "validacion_isabelle.json", {})
    vexp = leer(RAICES / "validacion_exportacion.json", {})
    glos = leer(HERE / "cuaderno" / "glosario_verificacion.json")
    base = leer(RES / "martillo_linea_base.json")
    if base is not None:
        base["total"] = len(ps)
    demo = leer(RES / "martillo_pasos_demo.json")
    libro = leer(HERE / "logs" / "gasto.json", {}) or {}
    entradas = libro.get("llamadas", []) if isinstance(libro, dict) else []
    gasto = sum(e.get("usd", 0) for e in entradas)
    comentario = (OUT / "comentario.tex").read_text(encoding="utf-8") if (OUT / "comentario.tex").exists() else None
    titulo = ("\\title{Aprendizaje por refuerzo con verificación certificada\\\\como única recompensa:\\\\aprendizaje verbal con un "
              "cuaderno verificado\\\\en teoremas de búsqueda de raíces\\\\[0.4em]\\large Nota técnica del proyecto "
              "\\texttt{rl\\_metodos}}")
    partes = [preambulo().decode("utf-8"), "", titulo,
              "\\author{Carlos Manuel Orrego Franco\\\\Universidad Nacional de Colombia, Sede Manizales}",
              f"\\date{{Septiembre de 2026 --- borrador v0.1, estado al {fecha_es()}}}", "",
              "\\begin{document}", "\\maketitle", "",
              s_proposito(L, ps), s_mdp(L), s_verificador(L, base, demo, glos), s_recompensa(L),
              s_metricas(L, gasto, len(entradas)), s_jerarquia(L, ps, vexp, viso), s_entornos(ps, base),
              s_experimentos(ps, base, demo, glos, pruebas(), viso, vexp, comentario),
              "\\bibliography{unirl_definicion}", "", apendice(ps), "", "\\end{document}", ""]
    return "\n".join(partes)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sin-pdf", action="store_true")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    tex = OUT / "nota.tex"
    tex.write_text(documento(), encoding="utf-8")
    bib = BIB.read_text(encoding="utf-8")
    (OUT / "unirl_definicion.bib").write_text(bib.rstrip("\n") + "\n" + BIB_EXTRA, encoding="utf-8")
    print(f"escrito {tex}")
    if a.sin_pdf:
        return 0
    r = compilar(tex)
    print(json.dumps({k: v for k, v in r.items() if k != "salida"}, ensure_ascii=False))
    return 0 if r.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
