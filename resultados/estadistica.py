"""Etapa 2 del informe: estadística sobre las corridas TERMINADAS (lee resultados/resumen.json y metricas.csv).

Solo lo que pide la formulación (formulacion_rl_verbal.tex) o el pedido de Carlos:
* tasas de éxito con intervalo exacto de Clopper–Pearson al 95 %, donde las unidades son intentos independientes;
* prueba exacta de McNemar para C frente a E pareadas: hoy no evaluable (E no se ha corrido);
* resultados por dificultad y por método (línea base A);
* acuerdo entre dos episodios por peldaño: hoy no evaluable (la única corrida con dos episodios se interrumpió);
* umbrales de la prueba de McNemar prerregistrada según el número de pares discordantes (verifica el párrafo de
  potencia de la formulación: es aritmética de la prueba, no una prueba nueva).
Las corridas interrumpidas por error no entran en ningún intervalo.

    09_unified/.venv/bin/python resultados/estadistica.py
"""

from __future__ import annotations

import csv
import json
from datetime import datetime
from math import comb
from pathlib import Path

from scipy.stats import beta

OUT = Path(__file__).resolve().parent
ALFA = 0.05


def cp(x: int, n: int) -> dict:
    """Intervalo exacto de Clopper–Pearson al 95 % para x éxitos en n intentos."""
    lo = 0.0 if x == 0 else float(beta.ppf(ALFA / 2, x, n - x + 1))
    hi = 1.0 if x == n else float(beta.ppf(1 - ALFA / 2, x + 1, n - x))
    return {"exitos": x, "n": n, "tasa": round(x / n, 4) if n else None, "ic95": [round(lo, 4), round(hi, 4)]}


def mcnemar_exacta(b: int, b2: int) -> float:
    """p bilateral exacto: b ~ Bin(b + b', 1/2) bajo H0."""
    n, k = b + b2, max(b, b2)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k, n + 1)) / 2 ** n)


def main() -> None:
    R = json.loads((OUT / "resumen.json").read_text(encoding="utf-8"))
    filas = list(csv.DictReader(open(OUT / "metricas.csv", encoding="utf-8")))
    est: dict = {"generado": datetime.now().isoformat(timespec="seconds"), "nivel": "95 %, Clopper–Pearson exacto",
                 "fuentes": {"resumen.json": R["generado"], "commit": R["commit"]}}

    # A: martillo solo, sin cuaderno (terminado, 24 sep). Cada peldaño es una tarea distinta; el martillo es
    # determinista salvo por el tiempo real.
    A = {tuple(g["grupo"]): (g["resueltos"], g["n"]) for g in R["linea_base_A"]["grupos"]}
    est["A_sin_cuaderno"] = {
        "todos": cp(*A[("todos",)]), "train": cp(*A[("split", "train")]), "test": cp(*A[("split", "test")]),
        "por_metodo": {g[1]: cp(*v) for g, v in A.items() if g[0] == "metodo"},
        "por_dificultad": {f"{g[1]} d{g[2]}": cp(*v) for g, v in A.items() if g[0] == "dificultad"},
        "T_estrella_test_sin_cuaderno": A[("split", "test")][1] - A[("split", "test")][0],
        "nota": ("H1 se decide con el cuaderno congelado (criterio prerregistrado: |T*_test| ≥ 12 de 16); aún no hay "
                 "cuaderno. Sin cuaderno, el martillo solo no cierra ninguno de los 16 de test."),
    }

    # jueces del 23–24 sep: solo episodios independientes. Con memoria entre episodios (memory = run) solo el
    # primero es independiente: los siguientes ven lo anterior (en el PEP, la solución: la fuga del 15/15).
    def jueces(juez: str, primero_solo: bool) -> dict:
        grupos: dict = {}
        for f in filas:
            if f["experimento"] != f"juez {juez}" or f["incluida"] != "sí":
                continue
            memoria = "memoria run" in f["configuracion"]
            if (primero_solo or memoria) and f["episodio"] not in ("1", "1.0"):
                continue
            k = f"{f['tarea']} | {f['modelo']}"
            x, n = grupos.get(k, (0, 0))
            grupos[k] = (x + int(f["exito"] or 0), n + 1)
        return grupos

    vg = jueces("lemma_graph", primero_solo=False)
    est["V_G_grafo"] = {"por_metodo": {k: cp(*v) for k, v in vg.items()},
                        "conjunto": cp(sum(v[0] for v in vg.values()), sum(v[1] for v in vg.values())),
                        "nota": "20 episodios independientes por método (sin memoria). El juez es el grafo escrito a mano: no demuestra nada por sí mismo."}
    pep = jueces("pep", primero_solo=True)
    por_modelo: dict = {}
    for k, (x, n) in pep.items():
        m = k.split(" | ")[1]
        a = por_modelo.get(m, (0, 0))
        por_modelo[m] = (a[0] + x, a[1] + n)
    est["V_P_PEP"] = {"primer_episodio_por_variante": {k: cp(*v) for k, v in pep.items()},
                      "por_modelo": {m: cp(*v) for m, v in por_modelo.items()},
                      "nota": ("Solo el episodio 1 de cada variante es independiente: en los episodios 2 y 3 el modelo vio el "
                               "programa certificado (15/15 de Astra = 5 descubrimientos + 10 repeticiones).")}
    vi = jueces("isabelle", primero_solo=False)
    est["V_I_biseccion"] = {k: cp(*v) for k, v in vi.items()}
    gd = jueces("isabelle_teorema", primero_solo=True)
    est["stepsize_isabelle"] = {k: cp(*v) for k, v in gd.items()}

    # primera ronda del RL verbal: nada terminado
    est["primera_ronda"] = {
        "terminadas": [c["corrida"] for c in R["rl_verbal"] if c["estado"] == "terminado" and c["fase"] not in ("humo", "medicion_sol")],
        "interrumpidas": [c["corrida"] for c in R["rl_verbal"] if c["estado"] == "interrumpida por error"],
        "tasas_por_configuracion": "no evaluable: ninguna corrida de evaluación terminó",
        "mcnemar_C_frente_a_E": "no evaluable: E no se ha corrido (necesita el cuaderno congelado)",
        "acuerdo_entre_dos_episodios": "no evaluable: la única corrida con dos episodios por peldaño se interrumpió",
        "por_dificultad_y_metodo_en_test": "no evaluable hasta que termine la evaluación",
    }

    # la prueba prerregistrada: con cuántos pares discordantes puede rechazar al 5 % bilateral
    umbrales = []
    for n in range(1, 17):
        minimo = next((b for b in range(n + 1) if mcnemar_exacta(b, n - b) < ALFA and b >= n - b), None)
        umbrales.append({"pares_discordantes": n, "b_minimo_a_favor_de_E": minimo,
                         "p_si_todos_a_favor": round(mcnemar_exacta(n, 0), 5)})
    est["mcnemar_umbrales"] = {"tabla": umbrales,
                               "comprobacion_formulacion": {"p(5 de 5)": mcnemar_exacta(5, 0), "p(6 de 6)": mcnemar_exacta(6, 0),
                                                            "minimo_de_pares_para_rechazar": next(u["pares_discordantes"] for u in umbrales if u["b_minimo_a_favor_de_E"] is not None)}}
    (OUT / "estadistica.json").write_text(json.dumps(est, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in est.items() if k in ("A_sin_cuaderno",)}, ensure_ascii=False)[:600])


if __name__ == "__main__":
    main()
