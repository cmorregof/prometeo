#!/usr/bin/env python3
"""Ayudante de `lanzar_ronda.sh` (26 sep 2026). Toda la lógica de reanudación de la ronda vive aquí y en el guion, no en
`unirl`: `unirl.experimentos evaluar` crea siempre una corrida nueva y recorre todos sus trabajos, así que la reanudación
se hace por peldaño: se calcula qué peldaños aún no tienen todos sus episodios válidos en las corridas de la ronda y se
relanza `evaluar --ids` con ellos. Un episodio es válido si al menos uno de sus intentos no fue PROVIDER_ERROR (los que
murieron por la red se repiten). En la fusión final, si un episodio aparece dos veces, cuenta el primero válido.

Subcomandos:
  pendientes --fase F --modelo M --configs C1,C2 --episodios K --desde ISO   → ids de test con episodios que faltan
  carpeta-cuaderno --desde ISO --modelo M                                    → carpeta de la corrida `cuaderno` de la ronda
  hash-congelado --desde ISO --modelo M                                      → hash del cuaderno congelado (FIN.json)
  hash-lemas --desde ISO --modelo M                                          → hash de los lemas del cuaderno congelado ("" si no hay)
  ultimo-aborto --fase F --desde ISO --despues EPOCH                         → última línea de ABORTADA.txt posterior a EPOCH
  red                                                                        → «ok» o «caida» (api.openai.com alcanzable)
  gasto                                                                      → total y por fase del libro de la ronda
  exec [--dry-run] -- <argumentos de unirl.experimentos>                     → ejecuta experimentos (en seco: con parches)
  informe --ronda ID --desde ISO --estado terminada|incompleta [--motivo T] → resultados/RONDA_<ESTADO>.md

Variables de entorno: RONDA_RUNS (raíz de las corridas; por defecto runs/unirl/rl_verbal), RONDA_RESULTADOS,
RONDA_IDS (solo en seco: peldaños permitidos), UNIRL_LIBRO (libro de la ronda).
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
RUNS = Path(os.environ.get("RONDA_RUNS") or RAIZ / "runs" / "unirl" / "rl_verbal")
RESULTADOS = Path(os.environ.get("RONDA_RESULTADOS") or RAIZ / "resultados")
SPLIT_TEST = "test"


def _jl(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []


def _meta(d: Path) -> dict | None:
    f = d / "meta.json"
    try:
        return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None
    except json.JSONDecodeError:
        return None


def corridas(fase: str, desde: str, modelo: str | None = None) -> list[Path]:
    """Carpetas de la fase creadas desde el inicio de la ronda, en orden cronológico."""
    base = RUNS / fase
    out = []
    for d in sorted(base.iterdir()) if base.exists() else []:
        m = _meta(d)
        if not m or m.get("inicio", "") < desde:
            continue
        if modelo and m.get("modelo") != modelo:
            continue
        out.append(d)
    return out


def ids_test() -> list[str]:
    from unirl import corpus
    ids = [p["id"] for p in corpus.usables(split=SPLIT_TEST)]
    permitidos = [x for x in os.environ.get("RONDA_IDS", "").split(",") if x]
    return [i for i in ids if not permitidos or i in permitidos]


def episodios_validos(fase: str, desde: str, modelo: str, configs: list[str]) -> dict[str, dict]:
    """episodio_id → fila, tomando el primer episodio válido de cada id entre las corridas de la ronda."""
    validos: dict[str, dict] = {}
    for d in corridas(fase, desde, modelo):
        m = _meta(d) or {}
        cfgs = m.get("configs") or ([m["config"]] if m.get("config") else [])  # la corrida `cuaderno` guarda `config`
        if not set(configs) <= set(cfgs):
            continue
        intentos_por_ep: dict[str, list[dict]] = {}
        for r in _jl(d / "llamadas.jsonl"):
            if r.get("tipo") == "intento":
                intentos_por_ep.setdefault(r.get("episodio_id"), []).append(r)
        for ep in _jl(d / "episodios.jsonl"):
            eid = ep["episodio_id"]
            ep = {**ep, "config": ep.get("config") or (cfgs[0] if len(cfgs) == 1 else None)}
            if eid in validos:
                continue
            ints = intentos_por_ep.get(eid, [])
            solo_red = bool(ints) and all(r.get("etiqueta") == "PROVIDER_ERROR" for r in ints)
            if solo_red:
                continue
            validos[eid] = {**ep, "corrida": d.name}
    return validos


def pendientes(fase: str, desde: str, modelo: str, configs: list[str], episodios: int) -> list[str]:
    validos = episodios_validos(fase, desde, modelo, configs)
    out = []
    for pid in ids_test():
        if any(f"{pid}#{c}#{k}" not in validos for c in configs for k in range(1, episodios + 1)):
            out.append(pid)
    return out


def carpeta_cuaderno(desde: str, modelo: str) -> Path | None:
    cs = corridas("cuaderno", desde, modelo)
    return cs[0] if cs else None


def red_ok(timeout: float = 10.0) -> bool:
    import urllib.error
    import urllib.request
    try:
        urllib.request.urlopen(urllib.request.Request("https://api.openai.com/v1/models", method="HEAD"), timeout=timeout)
        return True
    except urllib.error.HTTPError:
        return True  # 401 sin clave: el servidor responde
    except Exception:
        return False


# ----------------------------------------------------------------------------- ejecución (normal y en seco)


class MockRonda:
    """Proveedor del ensayo en seco: nunca llama a la API. Devuelve un intento que Isabelle rechaza (`by simp`), así el
    juez, el martillo, la reflexión, los registros y el libro se ejercitan de verdad, sin gastar."""
    model = "mock"

    def __init__(self, libro):
        self.libro, self.calls, self.ultimo_uso = libro, 0, None

    def complete(self, system: str, user: str) -> str:
        self.calls += 1
        return "REFLEXION: <<<\nEnsayo en seco: se intenta de nuevo con simp.\n>>>\nPROOF: <<<\nby simp\n>>>"


def ejecutar(args: list[str], dry_run: bool) -> int:
    import unirl.experimentos as E
    if dry_run:
        import unirl.cuaderno as C
        import unirl.gasto as G
        import unirl.recompensa as Rc
        E.RUNS = RUNS
        C.DIR = Path(os.environ["RONDA_CUADERNO"])
        C.CONGELADOS = C.DIR / "congelados"
        Rc.RESULTADOS = RESULTADOS
        permitidos = [x for x in os.environ.get("RONDA_IDS", "").split(",") if x]
        original = E.peldanos

        def peldanos_filtrados(split, ids=None):
            return [p for p in original(split, ids) if not permitidos or p["id"] in permitidos]

        E.peldanos = peldanos_filtrados
        libro = G.Libro()
        E.proveedor = lambda modelo, fase, corrida, effort="high": MockRonda(libro)
    return E.main(args)


# ----------------------------------------------------------------------------- informe final


def _mcnemar(pares: list[tuple[int, int]]) -> dict:
    """pares (y_C, y_E) → b = E gana, b' = C gana, p exacto bilateral bajo Bin(b + b', 1/2)."""
    b = sum(1 for c, e in pares if e == 1 and c == 0)
    bp = sum(1 for c, e in pares if e == 0 and c == 1)
    n = b + bp
    if n == 0:
        return {"n": len(pares), "b": b, "b_prima": bp, "p": None}
    try:
        from scipy.stats import binomtest
        p = binomtest(b, n, 0.5).pvalue
    except Exception:
        from math import comb
        k = min(b, bp)
        p = min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2**n)
    return {"n": len(pares), "b": b, "b_prima": bp, "p": round(float(p), 4)}


def pares_mcnemar(Y: dict, ids: list[str], tstar, peld: dict, fc: str, cfc: str, fe: str, cfe: str, kk: int, filtro) -> list[tuple[int, int]]:
    """Pares (y_C, y_E) por peldaño y episodio, sobre T* (si hay línea base) y los peldaños cuya dificultad pasa `filtro`."""
    pares = []
    for pid in ids:
        if (tstar is not None and pid not in tstar) or not filtro(peld[pid]["dificultad"]):
            continue
        for k in range(1, kk + 1):
            a, b = Y.get((fc, cfc, pid, k)), Y.get((fe, cfe, pid, k))
            if a is not None and b is not None:
                pares.append((a, b))
    return pares


# análisis primario de H2 desde la ronda 2 (prerregistrado el 27 sep 2026): dificultad ≤ 3; en la ronda 1 fue todo T*
CONJUNTOS_MCNEMAR = [("primario: dificultad ≤ 3", lambda d: d <= 3), ("secundario: todo T*", lambda d: True),
                     ("secundario: dificultad 4–5", lambda d: d >= 4)]


def informe(ronda: str, desde: str, estado: str, motivo: str) -> Path:
    from unirl import corpus
    from unirl.gasto import Libro
    libro = Libro()
    fases = [("cuaderno", "gpt-6-luna", ["F"], 1), ("evaluacion", "gpt-6-luna", ["B0", "B", "C"], 2),
             ("pareada_luna", "gpt-6-luna", ["C3"], 1), ("pareada_sol", "gpt-6-sol", ["C3"], 1),
             ("evaluacion_E", "gpt-6-luna", ["E"], 2), ("pareada_luna", "gpt-6-luna", ["E3"], 1), ("pareada_sol", "gpt-6-sol", ["E3"], 1)]
    peld = {p["id"]: p for p in corpus.usables(split=SPLIT_TEST)}
    ids = ids_test()
    lin = [f"# Ronda {ronda}: {'TERMINADA' if estado == 'terminada' else 'INCOMPLETA'}", "",
           f"Inicio {desde}; informe {datetime.now().isoformat(timespec='seconds')}. Libro de la ronda: `{libro.ruta.relative_to(RAIZ) if str(libro.ruta).startswith(str(RAIZ)) else libro.ruta}` "
           f"(total ${libro.total():.4f} de ${libro.tope_usd:.2f}).", ""]
    if estado != "terminada":
        lin += ["## Dónde quedó y por qué", "", motivo or "(sin motivo registrado)", "",
                "Para continuar: volver a lanzar `unirl/tools/lanzar_ronda.sh`; salta las fases hechas y relanza los peldaños que faltan.", ""]
    # cuaderno
    cc = carpeta_cuaderno(desde, "gpt-6-luna")
    fin = json.loads((cc / "FIN.json").read_text()) if cc and (cc / "FIN.json").exists() else None
    lin += ["## Cuaderno", ""]
    if cc:
        eps = _jl(cc / "episodios.jsonl")
        lin.append(f"Corrida `{cc.name}`: {len(eps)} episodios de train registrados, {sum(1 for e in eps if e.get('aceptado'))} aceptados"
                   + (f"; congelado con hash `{fin['cuaderno']}` (lemas `{fin.get('hash_lemas') or 'ninguno'}`)." if fin else "; **no congelado**."))
    else:
        lin.append("Sin corrida de cuaderno en esta ronda.")
    # H1
    lin += ["", "## H1: margen del martillo con el cuaderno congelado", ""]
    tstar = None
    if fin:
        hl = fin.get("hash_lemas") or ""
        f = RESULTADOS / (f"martillo_linea_base_{hl}.json" if hl else "martillo_linea_base.json")
        if f.exists():
            filas = json.loads(f.read_text())["filas"]
            abiertos = [x["id"] for x in filas if not x["resuelto_por_martillo"] and x["id"] in ids]
            tstar = set(abiertos)
            lin.append(f"Línea base A con el cuaderno (`{f.name}`): el martillo deja sin cerrar **{len(abiertos)} de {len(ids)}** peldaños de test. "
                       f"Criterio prerregistrado |T*_test| ≥ 12: **{'se cumple' if len(abiertos) >= 12 else 'NO se cumple'}**"
                       + (" (ensayo en seco con pocos peldaños: no interpretar)." if len(ids) < 16 else "."))
        else:
            lin.append(f"No hay línea base con el cuaderno (`{f.name}`).")
    else:
        lin.append("No evaluable: no hay cuaderno congelado.")
    # por configuración y por peldaño
    Y: dict[tuple[str, str, str, int], int] = {}  # (fase, config, id, k) → 1/0
    lin += ["", "## Episodios válidos por fase y configuración", "", "| fase | modelo | config | episodios | aceptados | tasa | sobre T* | sobre T*, dif. ≤ 3 | corridas |", "|---|---|---|---|---|---|---|---|---|"]
    for fase, modelo, configs, k in fases:
        val = episodios_validos(fase, desde, modelo, configs)
        for c in configs:
            es = [e for e in val.values() if e.get("config") == c]
            for e in es:
                Y[(fase, c, e["peldano"] if "peldano" in e else e["episodio_id"].split("#")[0], int(e["episodio_id"].split("#")[-1]))] = int(bool(e.get("aceptado")))
            ok = sum(1 for e in es if e.get("aceptado"))
            en_t = [e for e in es if tstar is not None and e["episodio_id"].split("#")[0] in tstar]
            okt = sum(1 for e in en_t if e.get("aceptado"))
            en_t3 = [e for e in en_t if peld[e["episodio_id"].split("#")[0]]["dificultad"] <= 3]
            okt3 = sum(1 for e in en_t3 if e.get("aceptado"))
            ncarp = len({e["corrida"] for e in es})
            lin.append(f"| {fase} | {modelo} | {c} | {len(es)} | {ok} | {ok / len(es):.2f} | " + (f"{okt}/{len(en_t)} | {okt3}/{len(en_t3)}" if tstar is not None else "— | —") + f" | {ncarp} |" if es else f"| {fase} | {modelo} | {c} | 0 | — | — | — | — | 0 |")
    lin += ["", "Un episodio es válido si alguno de sus intentos no fue PROVIDER_ERROR; si un episodio se repitió al reanudar, cuenta el primero válido.", ""]
    # McNemar
    lin += ["## McNemar (pareado por peldaño y episodio; H2)", "", "| comparación | conjunto | pares | b (E gana) | b' (C gana) | p exacto bilateral |", "|---|---|---|---|---|---|"]
    for titulo, fc, cfc, fe, cfe, kk in [("Luna: C frente a E (2 episodios)", "evaluacion", "C", "evaluacion_E", "E", 2),
                                          ("Luna: C3 frente a E3", "pareada_luna", "C3", "pareada_luna", "E3", 1),
                                          ("Sol: C3 frente a E3", "pareada_sol", "C3", "pareada_sol", "E3", 1)]:
        for conjunto, filtro in CONJUNTOS_MCNEMAR:
            r = _mcnemar(pares_mcnemar(Y, ids, tstar, peld, fc, cfc, fe, cfe, kk, filtro))
            lin.append(f"| {titulo} | {conjunto} | {r['n']} | {r['b']} | {r['b_prima']} | {r['p'] if r['p'] is not None else '—'} |")
    lin += ["", "Sobre T*_test (peldaños que el martillo con cuaderno no cierra) cuando hay línea base; si no, sobre todos. "
            "Análisis primario de H2 desde la ronda 2 (prerregistrado el 27 sep 2026): dificultad ≤ 3; secundarios: todo T*_test y "
            "dificultad 4–5. En la ronda 1 el primario fue todo T*_test (su RONDA_TERMINADA.md se generó con la versión anterior de este informe).", ""]
    # por peldaño
    cols = [("evaluacion", "B0", 2), ("evaluacion", "B", 2), ("evaluacion", "C", 2), ("evaluacion_E", "E", 2), ("pareada_luna", "C3", 1), ("pareada_luna", "E3", 1), ("pareada_sol", "C3", 1), ("pareada_sol", "E3", 1)]
    lin += ["## Por peldaño (1 = aceptado, 0 = no, · = sin episodio; dos episodios se muestran como «xy»)", "",
            "| peldaño | dif. | en T* | " + " | ".join(f"{c} ({f.replace('evaluacion_E', 'E').replace('evaluacion', 'eval').replace('pareada_', '')})" for f, c, _ in cols) + " |",
            "|---|---|---|" + "---|" * len(cols)]
    for pid in ids:
        celdas = []
        for f, c, kmax in cols:
            celdas.append("".join("·" if Y.get((f, c, pid, k)) is None else str(Y[(f, c, pid, k)]) for k in range(1, kmax + 1)))
        lin.append(f"| {pid} | {peld[pid]['dificultad']} | " + ("sí" if tstar is not None and pid in tstar else ("no" if tstar is not None else "—")) + " | " + " | ".join(celdas) + " |")
    # gasto
    lin += ["", "## Gasto de la ronda por fase", "", "| fase | llamadas | $ |", "|---|---|---|"]
    por = {}
    for e in libro.entradas():
        por.setdefault(e.get("fase"), [0, 0.0]); por[e.get("fase")][0] += 1; por[e.get("fase")][1] += e["usd"]
    for f, (n, usd) in sorted(por.items()):
        lin.append(f"| {f} | {n} | {usd:.4f} |")
    lin.append(f"| **total** | {sum(v[0] for v in por.values())} | **{libro.total():.4f}** |")
    nombre = "RONDA_TERMINADA.md" if estado == "terminada" else "RONDA_INCOMPLETA.md"
    out = RESULTADOS / nombre
    out.write_text("\n".join(lin) + "\n", encoding="utf-8")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="ronda.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pendientes"); p.add_argument("--fase", required=True); p.add_argument("--modelo", required=True)
    p.add_argument("--configs", required=True); p.add_argument("--episodios", type=int, required=True); p.add_argument("--desde", required=True)
    p = sub.add_parser("carpeta-cuaderno"); p.add_argument("--desde", required=True); p.add_argument("--modelo", default="gpt-6-luna")
    p = sub.add_parser("hash-congelado"); p.add_argument("--desde", required=True); p.add_argument("--modelo", default="gpt-6-luna")
    p = sub.add_parser("hash-lemas"); p.add_argument("--desde", required=True); p.add_argument("--modelo", default="gpt-6-luna")
    p = sub.add_parser("ultimo-aborto"); p.add_argument("--fase", required=True); p.add_argument("--desde", required=True); p.add_argument("--despues", type=float, default=0.0)
    sub.add_parser("red")
    sub.add_parser("gasto")
    p = sub.add_parser("exec"); p.add_argument("--dry-run", action="store_true"); p.add_argument("resto", nargs=argparse.REMAINDER)
    p = sub.add_parser("informe"); p.add_argument("--ronda", required=True); p.add_argument("--desde", required=True)
    p.add_argument("--estado", choices=["terminada", "incompleta"], required=True); p.add_argument("--motivo", default="")
    a = ap.parse_args(argv)
    if a.cmd == "pendientes":
        print(",".join(pendientes(a.fase, a.desde, a.modelo, a.configs.split(","), a.episodios)))
    elif a.cmd == "carpeta-cuaderno":
        c = carpeta_cuaderno(a.desde, a.modelo); print(c if c else "")
    elif a.cmd == "hash-congelado":
        c = carpeta_cuaderno(a.desde, a.modelo)
        print(json.loads((c / "FIN.json").read_text())["cuaderno"] if c and (c / "FIN.json").exists() else "")
    elif a.cmd == "hash-lemas":
        c = carpeta_cuaderno(a.desde, a.modelo)
        print((json.loads((c / "FIN.json").read_text()).get("hash_lemas") or "") if c and (c / "FIN.json").exists() else "")
    elif a.cmd == "ultimo-aborto":
        for d in reversed(corridas(a.fase, a.desde)):
            f = d / "ABORTADA.txt"
            if f.exists() and f.stat().st_mtime >= a.despues:
                print(f.read_text(encoding="utf-8").strip().splitlines()[-1][:300]); break
    elif a.cmd == "red":
        print("ok" if red_ok() else "caida")
    elif a.cmd == "gasto":
        from unirl.gasto import Libro
        lb = Libro(); por = {}
        for e in lb.entradas():
            por[e.get("fase")] = por.get(e.get("fase"), 0.0) + e["usd"]
        print(f"total={lb.total():.4f} " + " ".join(f"{k}={v:.4f}" for k, v in sorted(por.items())))
    elif a.cmd == "exec":
        resto = a.resto[1:] if a.resto and a.resto[0] == "--" else a.resto
        return ejecutar(resto, a.dry_run)
    elif a.cmd == "informe":
        print(informe(a.ronda, a.desde, a.estado, a.motivo))
    return 0


if __name__ == "__main__":
    sys.exit(main())
