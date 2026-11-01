"""Análisis confirmatorio de los datos reales de la fase 2 (prerregistro v3, §7, §8, §11 «tope duro», §17.14).

Entrada: la carpeta de la fase 2 (`resultados_finales.jsonl` si existe —tras el rejuicio—, si no `resultados.jsonl`;
`cola.json`; `enmiendas/recorte.json`), el anexo de la fase 1 (plan, exclusión, H4, martillo con cuaderno) y, para una
sensibilidad, la carpeta de la fase 1 (`construcciones.jsonl`).

Qué celdas entran (ronda 2, C5):
  * las que tienen `resuelto` (0/1): resueltas, no resueltas, «interrumpida dos veces» (= 0), sin llamada en la
    reprogramación (= 0), con rejuicio de 900 s (ya fundido en `resultados_finales.jsonl`);
  * fuera: las celdas recortadas (nunca se corrieron) y, si el recorte 3 (`tope_familia_30`) o el 4 (`quitar_s3`) se
    activó, las celdas ya corridas de tareas fuera del prefijo o de la semilla 3: se reportan y no entran al primario;
  * tareas excluidas por §2.4: no están en la cola; R-texto solo existe en las familias de H4;
  * tope duro (§11): por contraste entran las tareas con al menos una semilla completada en sus DOS ramas, promediando
    sobre las semillas completadas; se reporta el número de celdas perdidas por rama.

Estadístico (§7): por tarea, diferencia de tasas (media sobre semillas); S_f por familia; θ̂ = Σ S_f / n;
t = θ̂ / SE_CR1; p por permutación de signo exhaustiva (2^F vectores; `p_exhaustiva` de simulacion_prereg.py, copiada);
IC 95 % Wald con t_{F−1} (descriptivo). Grafo de §8.1 (opción A) con la regla de dirección y el orden «menor p/(w·α)
primero; un rechazo en contra se registra y su peso se pierde» (B-c). TOST ±5 pp con IC 95 % solo en las contrastadas
y no rechazadas (§8.2). Sensibilidades de §7: media ponderada por familia; sin familias con éxito ≥ 0,85 en el pase de
entrenamiento; ETP como un solo cluster; sin el estrato «cerrable por martillo + cuaderno»; y sin las tareas de la
calibración (§17.14). Secundarios sin α (§9): SC < D50 < D100, P frente a SC.

    python -m unirl.analisis_v6 --fase2 runs/unirl/confirmatorio/v6/fase2 --anexo runs/unirl/confirmatorio/v6/anexo_fase1 \\
        [--fase1 runs/unirl/confirmatorio/v6/fase1] [--calibracion muestra.json] --salida analisis.json
"""

from __future__ import annotations

import argparse
import json
import math
import random
from collections import defaultdict
from pathlib import Path

import numpy as np

from . import plan_v6 as P

HIP = ("H1", "H2", "H3", "H4", "H5")
CONTRASTE = {"H1": ("D100", "SC"), "H2": ("D100", "P"), "H3": ("D100", "SC_ig"), "H4": ("D100-texto", "R-texto"), "H5": ("D100", "D100-texto")}
SECUNDARIOS = {"D50-SC": ("D50", "SC"), "D100-D50": ("D100", "D50"), "P-SC": ("P", "SC"), "D100texto-SC": ("D100-texto", "SC"), "Rtexto-SC": ("R-texto", "SC")}
PESOS0 = np.array([0.5, 0.0, 0.0, 0.5, 0.0])  # H1, H2, H3, H4, H5
G0 = np.array([  # §8.1 (fila = se rechaza; columna = recibe)
    [0.0, 0.5, 0.0, 0.5, 0.0],
    [0.0, 0.0, 0.5, 0.0, 0.5],
    [0.0, 0.0, 0.0, 0.5, 0.5],
    [1.0, 0.0, 0.0, 0.0, 0.0],
    [0.0, 0.0, 0.5, 0.5, 0.0],
])
ALFA = 0.05
MARGEN_TOST = 0.05
UMBRAL_ENTRENAMIENTO = 0.85
SEMILLA_AUDITORIA = P.SEMILLAS["auditoria"]
N_AUDITORIA = 20


# ============================================================================== estadístico (copiado de simulacion_prereg.py)


def t_studentizado(S, m):
    Fc = S.size
    n = m.sum()
    th = S.sum() / n
    if Fc < 2:
        return th, float("nan"), float("nan")
    ss = ((S - m * th) ** 2).sum()
    se = math.sqrt(Fc / (Fc - 1) * ss) / n
    return th, se, (th / se if se > 0 else 0.0)


def p_exhaustiva(S, m, bloque=512):
    """p registrada (§7): #{|t*| ≥ |t|} / 2^F con los 2^F vectores, identidad incluida. Por simetría t(−s) = −t(s) se
    fija el signo del cluster 0 (2^(F−1) vectores) y el resto se parte en dos mitades (meet-in-the-middle)."""
    Fc = S.size
    if Fc < 2:
        return float("nan")
    n = m.sum()
    _, _, t0 = t_studentizado(S, m)
    c = n ** 2 * (Fc - 1) / Fc
    sumS2, M2 = (S ** 2).sum(), (m ** 2).sum()
    resto = np.arange(1, Fc)
    izq, der = resto[: (Fc - 1) // 2], resto[(Fc - 1) // 2:]

    def combos(idx):
        k = idx.size
        E = 1.0 - 2.0 * ((np.arange(2 ** k)[:, None] >> np.arange(k)[None, :]) & 1)
        return E @ S[idx], E @ (S[idx] * m[idx])
    a1, a2 = combos(izq)
    a1 = a1 + S[0]; a2 = a2 + S[0] * m[0]
    b1, b2 = combos(der)
    umbral = t0 ** 2 * (1 - 1e-9)
    cuenta = 0
    for i in range(0, a1.size, bloque):
        L1 = a1[i:i + bloque, None] + b1[None, :]
        L2 = a2[i:i + bloque, None] + b2[None, :]
        th = L1 / n
        ss = sumS2 - 2 * th * L2 + th * th * M2
        cuenta += int(np.count_nonzero(th * th * c >= umbral * ss))
    return cuenta / 2 ** (Fc - 1)


def t_critico(df: int, q: float = 0.975) -> float:
    try:
        from scipy import stats
        return float(stats.t.ppf(q, df))
    except ImportError:  # sin scipy: aproximación de Cornish–Fisher de la t (error < 0,01 para df ≥ 5)
        z = 1.959963984540054 if q == 0.975 else 1.6448536269514722
        g1 = (z ** 3 + z) / 4
        g2 = (5 * z ** 5 + 16 * z ** 3 + 3 * z) / 96
        g3 = (3 * z ** 7 + 19 * z ** 5 + 17 * z ** 3 - 15 * z) / 384
        return z + g1 / df + g2 / df ** 2 + g3 / df ** 3


def ic_wald(th: float, se: float, Fc: int) -> tuple[float, float]:
    if Fc < 2 or not math.isfinite(se):
        return float("nan"), float("nan")
    tc = t_critico(Fc - 1)
    return th - tc * se, th + tc * se


# ============================================================================== grafo de α (§8.1, opción A; B-c)


def _quitar(j, w, G, activo, pasar):
    """Paso de Bretz et al. (2009, alg. 1) al sacar Hj. pasar=False descarta su peso (rechazo en dirección contraria)."""
    idx = [l for l in range(5) if activo[l] and l != j]
    w2, G2 = w.copy(), np.zeros_like(G)
    for l in idx:
        if pasar:
            w2[l] = w[l] + w[j] * G[j, l]
        for k in idx:
            if k == l:
                continue
            den = 1.0 - G[l, j] * G[j, l]
            G2[l, k] = (G[l, k] + G[l, j] * G[j, k]) / den if den > 1e-12 else 0.0
    w2[j] = 0.0
    activo[j] = False
    return w2, G2


def grafo(p: list[float], dir_ok: list[bool], h4_evaluable: bool, alfa: float = ALFA) -> dict:
    """§8.1 + regla de dirección + orden de procesamiento (B-c): en cada paso, entre las hipótesis con p_j ≤ w_j·α, se
    procesa la de menor p_j / w_j; si su estimación va en la dirección prevista, su peso se propaga; si no, se registra
    y su peso se pierde. H4 no evaluable sale con su peso hacia H1. Devuelve rechazadas, niveles locales y el orden."""
    p = [float(x) if x is not None and not (isinstance(x, float) and math.isnan(x)) else 1.0 for x in p]
    w, G = PESOS0.copy(), G0.copy()
    activo = np.ones(5, bool)
    rech, contra = np.zeros(5, bool), np.zeros(5, bool)
    nivel = w * alfa
    orden = []
    if not h4_evaluable:
        w, G = _quitar(3, w, G, activo, pasar=True)
        nivel = np.maximum(nivel, w * alfa); nivel[3] = 0.0
    while True:
        cand = [j for j in range(5) if activo[j] and w[j] > 0 and p[j] <= w[j] * alfa]
        if not cand:
            break
        j = min(cand, key=lambda j: p[j] / w[j])
        rech[j] = True
        contra[j] = not dir_ok[j]
        orden.append({"hipotesis": HIP[j], "p": p[j], "alfa_local": float(w[j] * alfa), "direccion_prevista": bool(dir_ok[j]),
                      "propaga": bool(dir_ok[j])})
        w, G = _quitar(j, w, G, activo, pasar=bool(dir_ok[j]))
        nivel = np.maximum(nivel, w * alfa)
    return {"rechazadas": {HIP[j]: bool(rech[j]) for j in range(5)}, "rechazo_en_contra": {HIP[j]: bool(contra[j]) for j in range(5)},
            "alfa_local": {HIP[j]: float(nivel[j]) for j in range(5)}, "orden": orden, "h4_evaluable": h4_evaluable,
            "no_alcanzadas": [HIP[j] for j in range(5) if not rech[j] and nivel[j] == 0.0 and (h4_evaluable or j != 3)]}


# ============================================================================== datos


def _leer_jsonl(ruta: Path) -> list[dict]:
    return [json.loads(l) for l in Path(ruta).read_text(encoding="utf-8").splitlines() if l.strip()] if Path(ruta).exists() else []


def cargar(fase2: Path, anexo: Path, fase1: Path | None = None) -> dict:
    fase2, anexo = Path(fase2), Path(anexo)
    j = lambda f: json.loads(f.read_text(encoding="utf-8"))
    res_f = fase2 / "resultados_finales.jsonl"
    filas = _leer_jsonl(res_f if res_f.exists() else fase2 / "resultados.jsonl")
    rec = fase2 / "enmiendas" / "recorte.json"
    d = {"resultados": [r for r in filas if "resuelto" in r], "recortadas": [r for r in filas if "recortada" in r],
         "cola": j(fase2 / "cola.json"), "plan": j(anexo / "plan.json"), "exclusion": j(anexo / "exclusion.json"),
         "h4": j(anexo / "h4_familias.json"), "martillo": j(anexo / "martillo_cuaderno.json") if (anexo / "martillo_cuaderno.json").exists() else {},
         "pasos_recorte": j(rec).get("pasos", []) if rec.exists() else [], "fuente_resultados": res_f.name if res_f.exists() else "resultados.jsonl",
         "entrenamiento": {}}
    if fase1 and (Path(fase1) / "construcciones.jsonl").exists():
        por_fam: dict[str, list[int]] = defaultdict(list)
        for r in _leer_jsonl(Path(fase1) / "construcciones.jsonl"):
            if "resuelto" in r:
                por_fam[r["familia"]].append(int(r["resuelto"]))
        d["entrenamiento"] = {f: sum(v) / len(v) for f, v in por_fam.items() if v}
    return d


def celdas_primarias(d: dict) -> tuple[list[dict], dict]:
    """Las celdas que entran al análisis primario y el conteo de las que se apartan (recortes 3 y 4 ya corridas)."""
    pasos = d["pasos_recorte"]
    entran, apartadas = [], defaultdict(int)
    for r in d["resultados"]:
        if "tope_familia_30" in pasos and not r.get("en_prefijo_30", True):
            apartadas["tope_familia_30"] += 1
            continue
        if "quitar_s3" in pasos and r["rama"] in ("SC", "D100", "D100-texto", "R-texto") and r["semilla"] == 3:
            apartadas["quitar_s3"] += 1
            continue
        entran.append(r)
    return entran, dict(apartadas)


def tasas(celdas: list[dict]) -> dict[tuple[str, str], tuple[float, int]]:
    """(tarea, rama) → (tasa media sobre las semillas completadas, nº de semillas completadas)."""
    acc: dict[tuple[str, str], list[int]] = defaultdict(list)
    for r in celdas:
        acc[(r["tarea"], r["rama"])].append(int(bool(r["resuelto"])))
    return {k: (sum(v) / len(v), len(v)) for k, v in acc.items()}


def perdidas_por_rama(d: dict) -> dict:
    """Celdas planificadas (no recortadas) sin resultado: tope duro o detención (§11)."""
    pasos = d["pasos_recorte"]
    hechas = {r["celda"] for r in d["resultados"]} | {r["celda"] for r in d["recortadas"]}
    out = defaultdict(int)
    from .fase2 import celda_recortada
    for c in d["cola"]["celdas"]:
        if c["celda"] not in hechas and not celda_recortada(c, pasos):
            out[c["rama"]] += 1
    return dict(out)


# ============================================================================== contrastes


def contraste(tasas_: dict, A: str, B: str, familia_de: dict[str, str], cluster_de: dict[str, str] | None = None,
              excluir_tareas: set[str] | None = None, solo_familias: set[str] | None = None, peso: str = "tarea") -> dict:
    """θ̂, SE_CR1, t, p exhaustiva e IC 95 % de la diferencia A − B por tarea (media sobre semillas completadas), con
    clusters = familias (o `cluster_de`). `peso='familia'` es la sensibilidad «media ponderada por familia»."""
    excluir_tareas = excluir_tareas or set()
    cluster_de = cluster_de or familia_de
    difs: dict[str, list[float]] = defaultdict(list)
    n_tareas = 0
    for (tarea, rama), (tasa, _) in tasas_.items():
        if rama != A or tarea in excluir_tareas or (tarea, B) not in tasas_:
            continue
        fam = familia_de.get(tarea)
        if fam is None or (solo_familias is not None and fam not in solo_familias):
            continue
        difs[cluster_de[tarea]].append(tasa - tasas_[(tarea, B)][0])
        n_tareas += 1
    clusters = sorted(difs)
    if not clusters:
        return {"A": A, "B": B, "n_tareas": 0, "F": 0, "theta": None, "se": None, "t": None, "p": None, "ic95": None, "direccion_prevista": False, "por_cluster": {}}
    if peso == "familia":
        S = np.array([sum(difs[f]) / len(difs[f]) for f in clusters]); m = np.ones(len(clusters))
    else:
        S = np.array([sum(difs[f]) for f in clusters]); m = np.array([float(len(difs[f])) for f in clusters])
    th, se, t = t_studentizado(S, m)
    p = p_exhaustiva(S, m) if len(clusters) >= 2 else float("nan")
    lo, hi = ic_wald(th, se, len(clusters))
    return {"A": A, "B": B, "n_tareas": n_tareas, "F": len(clusters), "theta": float(th), "se": None if not math.isfinite(se) else float(se),
            "t": None if not math.isfinite(t) else float(t), "p": None if not math.isfinite(p) else float(p),
            "ic95": None if not math.isfinite(lo) else [float(lo), float(hi)], "direccion_prevista": bool(th > 0),
            "por_cluster": {f: {"m": len(difs[f]), "S": float(sum(difs[f]))} for f in clusters}}


def tost(c: dict, margen: float = MARGEN_TOST) -> dict | None:
    if c.get("ic95") is None:
        return None
    lo, hi = c["ic95"]
    return {"margen_pp": margen * 100, "ic95": [lo, hi], "equivalente": bool(lo > -margen and hi < margen)}


def analizar(d: dict, calibracion: set[str] | None = None) -> dict:
    plan = d["plan"]
    familia_de = {i: t["familia"] for i, t in plan["tareas"].items()}
    etp_cluster = {i: ("etp" if t["fuente"] == "etp" else t["familia"]) for i, t in plan["tareas"].items()}
    entran, apartadas = celdas_primarias(d)
    T = tasas(entran)
    h4_ok = bool(d["h4"].get("evaluable"))
    fams_h4 = set(d["h4"].get("familias_h4", []))
    prim = {}
    for H, (A, B) in CONTRASTE.items():
        prim[H] = contraste(T, A, B, familia_de, solo_familias=fams_h4 if H == "H4" else None)
    g = grafo([prim[H]["p"] for H in HIP], [prim[H]["direccion_prevista"] for H in HIP], h4_ok)
    tosts = {H: tost(prim[H]) for H in HIP if not g["rechazadas"][H] and g["alfa_local"][H] > 0}
    sens = {"ponderada_por_familia": {H: contraste(T, A, B, familia_de, solo_familias=fams_h4 if H == "H4" else None, peso="familia") for H, (A, B) in CONTRASTE.items()}}
    faciles = {f for f, v in d.get("entrenamiento", {}).items() if v >= UMBRAL_ENTRENAMIENTO}
    sens["sin_familias_entrenamiento_ge_085"] = {"familias_excluidas": sorted(faciles),
                                                 **{H: contraste(T, A, B, familia_de, solo_familias=(fams_h4 if H == "H4" else set(plan["familias"])) - faciles)
                                                    for H, (A, B) in CONTRASTE.items()}}
    sens["etp_un_cluster"] = {H: contraste(T, A, B, familia_de, cluster_de=etp_cluster, solo_familias=fams_h4 if H == "H4" else None) for H, (A, B) in CONTRASTE.items()}
    cerrables = {i for i, v in d.get("martillo", {}).items() if v.get("cerrable")}
    sens["sin_estrato_martillo_cuaderno"] = {"tareas_excluidas": len(cerrables),
                                             **{H: contraste(T, A, B, familia_de, excluir_tareas=cerrables, solo_familias=fams_h4 if H == "H4" else None)
                                                for H, (A, B) in CONTRASTE.items()}}
    if calibracion:
        sens["sin_calibracion_17_14"] = {"tareas_excluidas": len(calibracion & set(familia_de)),
                                         **{H: contraste(T, A, B, familia_de, excluir_tareas=calibracion, solo_familias=fams_h4 if H == "H4" else None)
                                            for H, (A, B) in CONTRASTE.items()}}
    secundarios = {k: contraste(T, A, B, familia_de) for k, (A, B) in SECUNDARIOS.items()}
    completas = defaultdict(int)
    for (tarea, rama), (_, n) in T.items():
        completas[rama] += n
    return {"fuente_resultados": d["fuente_resultados"], "celdas_que_entran": len(entran), "celdas_apartadas_por_recorte": apartadas,
            "pasos_recorte": d["pasos_recorte"], "celdas_recortadas": len(d["recortadas"]), "celdas_perdidas_por_rama": perdidas_por_rama(d),
            "semillas_completadas_por_rama": dict(completas), "h4_evaluable": h4_ok, "familias_h4": sorted(fams_h4),
            "primario": prim, "grafo": g, "tost": tosts, "sensibilidades": sens, "secundarios": secundarios,
            "nota": "La decisión la da la permutación (p) con el α local del grafo; el IC es descriptivo; el TOST no está cubierto por el grafo."}


# ============================================================================== auditoría a mano (§5, semilla 20261034)


def muestra_auditoria(d: dict, n: int = N_AUDITORIA, semilla: int = SEMILLA_AUDITORIA) -> dict:
    """20 pruebas aceptadas por rama (ciega a la rama: se barajan y se listan sin la rama en `ciega`) más todas las
    STATEMENT_DRIFT (las celdas con `statement_drift` > 0, si el arnés lo anota)."""
    rng = random.Random(semilla)
    por_rama: dict[str, list[str]] = defaultdict(list)
    for r in sorted(d["resultados"], key=lambda r: r["celda"]):
        if r.get("resuelto"):
            por_rama[r["rama"]].append(r["celda"])
    muestra = {}
    for rama in sorted(por_rama):
        cs = list(por_rama[rama])
        rng.shuffle(cs)
        muestra[rama] = sorted(cs[:n])
    todas = [c for cs in muestra.values() for c in cs]
    rng.shuffle(todas)
    drift = sorted(r["celda"] for r in d["resultados"] if r.get("statement_drift"))
    return {"semilla": semilla, "n_por_rama": n, "por_rama": muestra, "ciega": todas, "statement_drift": drift}


def informe_md(a: dict) -> str:
    L = ["# Análisis confirmatorio (arnés v6)", "", f"Celdas que entran: {a['celdas_que_entran']}; recortadas: {a['celdas_recortadas']}; "
         f"apartadas por recortes 3–4: {a['celdas_apartadas_por_recorte']}; perdidas por rama: {a['celdas_perdidas_por_rama']}.", "",
         "| H | contraste | n | F | θ̂ (pp) | SE | t | p exh. | IC 95 % | α local | rechaza | en contra |", "|---|---|---:|---:|---:|---:|---:|---:|---|---:|---|---|"]
    for H in HIP:
        c, g = a["primario"][H], a["grafo"]
        f = lambda x, k=3: "—" if x is None else f"{x:.{k}f}"
        ic = "—" if not c["ic95"] else f"[{100 * c['ic95'][0]:.1f}, {100 * c['ic95'][1]:.1f}]"
        L.append(f"| {H} | {c['A']} − {c['B']} | {c['n_tareas']} | {c['F']} | {f(100 * c['theta'] if c['theta'] is not None else None, 1)} | {f(c['se'], 4)} | "
                 f"{f(c['t'])} | {f(c['p'], 4)} | {ic} | {g['alfa_local'][H]:.4f} | {g['rechazadas'][H]} | {g['rechazo_en_contra'][H]} |")
    L += ["", f"Orden de procesamiento del grafo: {[(o['hipotesis'], round(o['p'], 4), o['propaga']) for o in a['grafo']['orden']]}",
          f"TOST (±5 pp, IC 95 %) en las contrastadas no rechazadas: {a['tost']}", ""]
    return "\n".join(L) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m unirl.analisis_v6", description=__doc__.split("\n")[0])
    ap.add_argument("--fase2", required=True); ap.add_argument("--anexo", required=True); ap.add_argument("--fase1", default=None)
    ap.add_argument("--calibracion", default=None, help="muestra JSON de la calibración, para la sensibilidad de §17.14")
    ap.add_argument("--salida", default=None)
    a = ap.parse_args(argv)
    d = cargar(Path(a.fase2), Path(a.anexo), Path(a.fase1) if a.fase1 else None)
    cal = set(json.loads(Path(a.calibracion).read_text(encoding="utf-8")).get("ids", [])) if a.calibracion else None
    res = analizar(d, cal)
    res["auditoria"] = muestra_auditoria(d)
    txt = json.dumps(res, ensure_ascii=False, indent=1)
    if a.salida:
        Path(a.salida).write_text(txt, encoding="utf-8")
        Path(a.salida).with_suffix(".md").write_text(informe_md(res), encoding="utf-8")
    print(informe_md(res))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
