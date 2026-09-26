"""Etapa 4 de PLAN_rl_verbal.md: la recompensa r_V (solo métrica) y la medida de legibilidad de una prueba.

Los pesos del proponente no cambian: r_V no entrena nada ni decide qué entra al cuaderno (eso lo deciden las reglas de
`cuaderno.py`). Sirve para comparar configuraciones. Para un intento sobre el peldaño T:

    r_V = 0                                   si el martillo solo resuelve T (línea base A, para este cuaderno);
    r_V = 0                                   si la prueba del agente es un solo `by martillo` sobre la meta;
    r_V = 0                                   si la prueba aceptada es UNA SOLA LÍNEA OPACA (PLAN §12, punto aprobado
                                              por Carlos el 24 sep 2026: eso es «el martillo lo hizo»);
    r_V = 0                                   si la etiqueta es de deriva, UNSOUND, sintaxis o propuesta inválida;
    r_V = ρ + BONO · [aceptada]               en otro caso,

con ρ = 1 si la prueba se aceptó y, si no, la fracción de pasos `by martillo` que el martillo cerró (0 sin marcas).
La verdad la decide solo el kernel: nada de esto cambia la etiqueta ACCEPTED.

Una línea es OPACA si su método es `smt` o `metis` con más de UMBRAL_HECHOS hechos (los del método más los de su
`using`). Una prueba es de UNA SOLA LÍNEA OPACA si, quitando los cierres triviales (`.`, `..` y `by` con un solo
método de TRIVIALES sin argumentos), le queda una única invocación (`by …` o `apply …`) y es opaca. Así no se esquiva
envolviéndola en `proof - show ?thesis … qed` ni añadiendo un `have … by simp`.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from .verifiers import ALLOWED_COMMANDS, ISABELLE_COMMANDS, tokenize_outer

BASE = Path(__file__).resolve().parent.parent
RESULTADOS = BASE / "resultados"
BONO = 1.0
UMBRAL_HECHOS = 4
OPACOS = frozenset({"smt", "metis"})
ENUNCIADOS = frozenset({"have", "show", "hence", "thus", "obtain", "consider"})
SIN_CREDITO = frozenset({"STATEMENT_DRIFT", "UNSOUND", "SYNTAX_ERROR", "INVALID_PROPOSAL"})
TRIVIALES = frozenset({"simp", "auto", "assumption", "fact", "blast", "rule"})
_CIERRES = frozenset({";", ",", "|"})


class LineaBaseDesactualizada(RuntimeError):
    pass


# ----------------------------------------------------------------------------- lectura de la prueba


def _cerrar(toks: list[tuple[str, str]], i: int, abre: str, cierra: str) -> int:
    """Índice justo después del grupo que abre en toks[i] (== abre)."""
    d = 0
    while i < len(toks):
        if toks[i][1] == abre:
            d += 1
        elif toks[i][1] == cierra:
            d -= 1
            if d == 0:
                return i + 1
        i += 1
    return i


def _metodo(toks, i) -> tuple[list[tuple[str, str]], int]:
    """Expresión de método en toks[i]: un grupo entre paréntesis (sin los paréntesis de fuera) o un nombre, con su
    `+`/`?` opcional."""
    if i >= len(toks):
        return [], i
    if toks[i][1] == "(":
        j = _cerrar(toks, i, "(", ")")
        return toks[i + 1:j - 1], j
    if toks[i][0] == "word":
        j = i + 1
        while j < len(toks) and toks[j][1] in ("+", "?"):
            j += 1
        return toks[i:j], j
    return [], i


def _es_inicio_de_metodo(tok: tuple[str, str]) -> bool:
    return tok[1] == "(" or (tok[0] == "word" and tok[1] not in ISABELLE_COMMANDS and tok[1] not in ALLOWED_COMMANDS)


def _hechos(toks, i, fin: int | None = None) -> tuple[int, int]:
    """Cuenta hechos (nombres) desde toks[i] hasta un comando o un separador; salta atributos [..] y selecciones (..)."""
    n, fin = 0, len(toks) if fin is None else fin
    while i < fin:
        k, t = toks[i]
        if t == "[":
            i = _cerrar(toks, i, "[", "]")
            continue
        if t == "(":
            i = _cerrar(toks, i, "(", ")")
            continue
        if t in _CIERRES or t == ")" or (k == "word" and (t in ALLOWED_COMMANDS or t in ISABELLE_COMMANDS)):
            break
        if k == "word":
            n += 1
        i += 1
    return n, i


def opacidad(expr: list[tuple[str, str]], hechos_using: int = 0) -> tuple[bool, int]:
    """(opaca, hechos) de una expresión de método: busca smt/metis a cualquier profundidad y cuenta sus hechos."""
    peor = 0
    for k, (clase, t) in enumerate(expr):
        if clase == "word" and t in OPACOS:
            j = k + 1
            if j < len(expr) and expr[j][1] == "(":  # opciones: (verit, del_insts), (no_types, lifting)
                j = _cerrar(expr, j, "(", ")")
            n, _ = _hechos(expr, j)
            peor = max(peor, n + hechos_using)
    hay = any(c == "word" and t in OPACOS for c, t in expr)
    return hay and peor > UMBRAL_HECHOS, peor


def invocaciones(prueba: str) -> list[dict]:
    """Invocaciones terminales de una prueba Isar: [{tipo: by|apply|.|.., metodos: [texto], opaca, hechos}]."""
    toks = tokenize_outer(prueba)
    out, i, using = [], 0, 0
    while i < len(toks):
        k, t = toks[i]
        if t == "using" or t == "unfolding":
            n, j = _hechos(toks, i + 1)
            using = using + n if t == "using" else using
            i = j
            continue
        if t in ENUNCIADOS or t in ("next", "qed", "case", "also", "finally", "moreover", "ultimately"):
            using = 0
        if t == "by":
            metodos, j = [], i + 1
            e1, j = _metodo(toks, j)
            metodos.append(e1)
            if j < len(toks) and _es_inicio_de_metodo(toks[j]):
                e2, j = _metodo(toks, j)
                metodos.append(e2)
            ops = [opacidad(e, using) for e in metodos if e]
            out.append({"tipo": "by", "metodos": [" ".join(x for _, x in e) for e in metodos if e],
                        "opaca": any(o for o, _ in ops), "hechos": max([h for _, h in ops] or [0])})
            using, i = 0, j
            continue
        if t == "apply":  # cada paso de un guion apply es su propia invocación
            e, j = _metodo(toks, i + 1)
            o, h = opacidad(e, using)
            out.append({"tipo": "apply", "metodos": [" ".join(x for _, x in e)], "opaca": o, "hechos": h})
            using, i = 0, j
            continue
        if t in (".", ".."):
            out.append({"tipo": t, "metodos": [], "opaca": False, "hechos": 0})
        i += 1
    return out


def trivial(x: dict) -> bool:
    """Cierre trivial: `.`, `..`, o `by M` con un solo método de TRIVIALES sin argumentos."""
    return x["tipo"] in (".", "..") or (x["tipo"] == "by" and len(x["metodos"]) == 1 and x["metodos"][0] in TRIVIALES)


def legibilidad(prueba: str, marcas: int | None = None, cerradas_por_martillo: int = 0) -> dict:
    """Medida mecánica de legibilidad (PLAN §12, punto 2). `prueba` es la prueba FINAL (con las líneas del martillo
    ya pegadas); `marcas` y `cerradas_por_martillo`, las del martillo por pasos si lo hubo."""
    toks = tokenize_outer(prueba)
    inv = invocaciones(prueba)
    pasos = sum(1 for k, t in toks if k == "word" and t in ENUNCIADOS)
    opacas = sum(1 for x in inv if x["opaca"])
    una_linea = len(inv) == 1
    efectivas = [x for x in inv if not trivial(x)]
    return {
        "pasos_explicitos": pasos,
        "invocaciones": len(inv),
        "opacas": opacas,
        "fraccion_opacas": round(opacas / len(inv), 3) if inv else 0.0,
        "pasos_del_martillo": cerradas_por_martillo,
        "fraccion_martillo": round(cerradas_por_martillo / len(inv), 3) if inv else 0.0,
        "comentarios": len(re.findall(r"\(\*", prueba)),
        "lineas": sum(1 for l in prueba.splitlines() if l.strip()),
        "caracteres": len(prueba),
        "una_linea": una_linea,
        "una_linea_opaca": len(efectivas) == 1 and efectivas[0]["opaca"],
        "invocaciones_no_triviales": len(efectivas),
        "max_hechos": max([x["hechos"] for x in inv] or [0]),
    }


def martillo_en_la_meta(prueba_agente: str) -> bool:
    """La prueba del agente es solo `by martillo` (o `by (martillo …)`) sobre la meta entera: es el martillo solo."""
    inv = invocaciones(prueba_agente)
    return len(inv) == 1 and inv[0]["tipo"] == "by" and bool(inv[0]["metodos"]) and \
        re.fullmatch(r"martillo(\s+\d+)?", inv[0]["metodos"][0]) is not None


# ----------------------------------------------------------------------------- línea base


def ruta_linea_base(cuaderno_hash: str = "") -> Path:
    return RESULTADOS / (f"martillo_linea_base_{cuaderno_hash}.json" if cuaderno_hash else "martillo_linea_base.json")


def resueltos_por_martillo(cuaderno_hash: str = "", ids: list[str] | None = None) -> set[str]:
    """Peldaños que el martillo resuelve solo con ESTE cuaderno. Sin la línea base de este cuaderno (o incompleta para
    los peldaños pedidos) no hay recompensa: hay que recalcularla (tools/linea_base_martillo.py)."""
    ruta = ruta_linea_base(cuaderno_hash)
    if not ruta.exists():
        raise LineaBaseDesactualizada(f"no hay línea base del martillo para el cuaderno {cuaderno_hash or 'vacío'} ({ruta.name})")
    d = json.loads(ruta.read_text(encoding="utf-8"))
    if d.get("cuaderno") != (cuaderno_hash or "sin-cuaderno"):
        raise LineaBaseDesactualizada(f"{ruta.name} es de otro cuaderno ({d.get('cuaderno')})")
    medidos = {f["id"] for f in d["filas"]}
    faltan = sorted(set(ids or []) - medidos)
    if faltan:
        raise LineaBaseDesactualizada(f"la línea base no tiene {faltan[:5]}")
    return {f["id"] for f in d["filas"] if f["resuelto_por_martillo"]}


# ----------------------------------------------------------------------------- recompensa


def recompensa(peldano: str, etiqueta: str, prueba_agente: str, prueba_final: str | None = None, marcas: int = 0,
               cerradas: int = 0, resueltos: set[str] | None = None, cuaderno_hash: str = "") -> dict:
    """r_V de un intento, con el motivo y la legibilidad. `prueba_final` es la del agente con las líneas del martillo
    pegadas (si no hubo marcas, la misma). `resueltos`: la línea base (si no se da, se lee para `cuaderno_hash`)."""
    resueltos = resueltos_por_martillo(cuaderno_hash, [peldano]) if resueltos is None else resueltos
    final = prueba_final if prueba_final is not None else prueba_agente
    aceptada = etiqueta == "ACCEPTED"
    try:
        leg = legibilidad(final, marcas, cerradas if aceptada else 0)
    except ValueError:  # texto que el filtro léxico no lee: no hay prueba que medir
        leg = None
    rho = 1.0 if aceptada else (cerradas / marcas if marcas else 0.0)

    def res(r: float, motivo: str) -> dict:
        return {"r": round(r, 4), "motivo": motivo, "rho": round(rho, 4), "bono": BONO if aceptada and r > 0 else 0.0,
                "aceptada": aceptada, "etiqueta": etiqueta, "legibilidad": leg, "bono_valor": BONO,
                "umbral_hechos": UMBRAL_HECHOS}
    if peldano in resueltos:
        return res(0.0, "resuelto_por_martillo")
    if leg is not None and martillo_en_la_meta(prueba_agente):
        return res(0.0, "martillo_en_la_meta")
    if etiqueta in SIN_CREDITO:
        return res(0.0, "sin_credito_" + etiqueta.lower())
    if aceptada and leg and leg["una_linea_opaca"]:
        return res(0.0, "una_linea_opaca")
    if aceptada:
        return res(rho + BONO, "aceptada")
    return res(rho, "parcial" if rho > 0 else "nada")
