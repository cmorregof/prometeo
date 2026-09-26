"""Línea base de `martillo_solo` (configuración A) sobre los peldaños aprobados, EN SERIE y con caché.

Para cada peldaño: try0 (5 s) y Sledgehammer (60 s) sobre la meta; la línea encontrada solo cuenta si el juez la acepta
en el kernel. Los peldaños resueltos así se marcan `resuelto_por_martillo`: en la Etapa 4 no dan crédito.
Se recalcula cada vez que cambia `cuaderno/Cuaderno.thy` (su hash entra en la clave de la caché).
Escribe resultados/martillo_linea_base[_<hash del cuaderno>].{json,csv,md}; se puede interrumpir y reanudar (la caché guarda cada peldaño).

Si la máquina se suspende durante una búsqueda sin resultado (reloj de pared frente a monótono), el resultado no vale:
no se guarda y el peldaño se repite (hasta REINTENTOS veces). Correr bajo `caffeinate -i` para que no se suspenda.

Uso: .venv/bin/python tools/linea_base_martillo.py [--solo id1,id2] [--rehacer id1,id2] [--sin-cache]
  --rehacer: ignora la caché solo en esos peldaños (el resto sale de la caché) y reescribe la tabla completa.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parents[2]  # rl_metodos/
sys.path.insert(0, str(HERE))
from unirl import corpus  # noqa: E402
from unirl.gd_isabelle import TheoremVerifier  # noqa: E402
from unirl.martillo import Cache, martillo_solo  # noqa: E402
from unirl.recompensa import ruta_linea_base  # noqa: E402

CUADERNO = HERE / "runs" / "unirl" / "cuaderno" / "Cuaderno.thy"
CAMPOS = ["id", "metodo", "split", "dificultad", "version", "resuelto_por_martillo", "fuente", "resultado_sh",
          "veredicto_juez", "s", "sh_s_pared", "suspension_s", "intentos", "desde_cache", "carga_1", "linea"]
REINTENTOS = 2


def hash_cuaderno() -> str:
    return hashlib.sha256(CUADERNO.read_bytes()).hexdigest()[:16] if CUADERNO.exists() else ""


def fila(p: dict, r: dict) -> dict:
    carga = (r.get("veredicto_meta") or {}).get("carga_1_5_15") or [None]
    return {"id": p["id"], "metodo": p["metodo"], "split": p["split"], "dificultad": p["dificultad"],
            "version": p.get("version"), "resuelto_por_martillo": r["resuelto_por_martillo"], "fuente": r.get("fuente"),
            "resultado_sh": r.get("resultado_sh"), "veredicto_juez": r.get("veredicto_juez"),
            "s": round((r.get("ms") or 0) / 1000, 1),
            "sh_s_pared": round(r["sh_ms_pared"] / 1000, 1) if r.get("sh_ms_pared") is not None else None,
            "suspension_s": r.get("suspension_s"), "intentos": r.get("intentos", 1), "desde_cache": r.get("desde_cache"),
            "carga_1": carga[0], "linea": r.get("linea") or ""}


def informe(filas: list[dict], ch: str) -> str:
    res = [f for f in filas if f["resuelto_por_martillo"]]
    out = ["# Línea base: martillo solo (configuración A)", "",
           f"Fecha: {time.strftime('%Y-%m-%d %H:%M')}. Cuaderno: {ch or 'sin cuaderno'}. try0 5 s, Sledgehammer 60 s, "
           "en serie. Una línea cuenta solo si el juez la acepta en el kernel.", "",
           f"**Resueltos por el martillo: {len(res)} de {len(filas)}.** Estos peldaños no dan crédito en la Etapa 4.", ""]
    sin_medir = [f for f in filas if f.get("suspension_s") is None]
    if sin_medir:
        out += [f"{len(sin_medir)} filas salen de la caché de la primera corrida (24 sep 2026, 14:03–15:13), anterior al registro "
                "automático de suspensiones. Una auditoría posterior comparó, peldaño a peldaño, el tiempo de pared de "
                "Sledgehammer (su JSON) con el tiempo monótono medido en Python: solo secante_4c, secante_5, secante_5c y "
                "secante_6 tuvieron la máquina suspendida durante la búsqueda, y se rehicieron (más secante_6c, con una "
                "suspensión fuera de Sledgehammer).", ""]
    repetidos = [f for f in filas if (f.get("intentos") or 1) > 1]
    if repetidos:
        out += [f"Repetidos por suspensión de la máquina: {', '.join(f['id'] for f in repetidos)}.", ""]
    for split in ("train", "test"):
        fs = [f for f in filas if f["split"] == split]
        out.append(f"* {split}: {sum(f['resuelto_por_martillo'] for f in fs)} de {len(fs)}")
    out += ["", "| peldaño | método | split | dif. | versión | resuelto | fuente | Sledgehammer | juez | s | carga |",
            "|---|---|---|---|---|---|---|---|---|---|---|"]
    for f in filas:
        out.append(f"| {f['id']} | {f['metodo']} | {f['split']} | {f['dificultad']} | {f['version']} | "
                   f"{'**sí**' if f['resuelto_por_martillo'] else 'no'} | {f['fuente']} | {f['resultado_sh'] or ''} | "
                   f"{f['veredicto_juez'] or ''} | {f['s']} | {f['carga_1']} |")
    if res:
        out += ["", "## Líneas aceptadas", ""]
        out += [f"* `{f['id']}`: `{f['linea']}`" for f in res]
    return "\n".join(out) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--solo")
    ap.add_argument("--sin-cache", action="store_true")
    ap.add_argument("--rehacer", default="")
    a = ap.parse_args()
    peldanos = corpus.usables()
    if a.solo:
        ids = set(a.solo.split(","))
        peldanos = [p for p in peldanos if p["id"] in ids]
    ch = hash_cuaderno()
    SALIDA = ruta_linea_base(ch).with_suffix("")  # una línea base por cuaderno: la recompensa exige la del suyo
    cache = Cache()
    filas = []
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    for i, p in enumerate(peldanos, 1):
        juez = TheoremVerifier.desde_corpus(p["id"])
        rehacer = p["id"] in set(filter(None, a.rehacer.split(",")))
        r = martillo_solo(juez, cuaderno_hash=ch, cache=cache, usar_cache=not (a.sin_cache or rehacer))
        intentos = 1
        while r.get("invalido") and intentos <= REINTENTOS:
            print(f"    {p['id']}: resultado inválido (suspensión {r.get('suspension_s')} s o fallo de infraestructura); se repite",
                  flush=True)
            r = martillo_solo(juez, cuaderno_hash=ch, cache=cache, usar_cache=False)
            intentos += 1
        r["intentos"] = r.get("intentos", intentos) if r.get("desde_cache") else intentos
        f = fila(p, r)
        filas.append(f)
        print(f"[{i}/{len(peldanos)}] {p['id']}: {'RESUELTO' if f['resuelto_por_martillo'] else 'no'} "
              f"({f['fuente']}, {f['resultado_sh'] or '-'}, juez {f['veredicto_juez']}, {f['s']} s"
              f"{', caché' if f['desde_cache'] else ''}{', suspensión ' + str(f['suspension_s']) + ' s' if f['suspension_s'] else ''})",
              flush=True)
        # se escribe tras cada peldaño: si se interrumpe, lo hecho queda y la caché permite reanudar
        (SALIDA.with_suffix(".json")).write_text(json.dumps({"cuaderno": ch or "sin-cuaderno", "filas": filas},
                                                            ensure_ascii=False, indent=1), encoding="utf-8")
    with open(SALIDA.with_suffix(".csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=CAMPOS)
        w.writeheader()
        w.writerows(filas)
    SALIDA.with_suffix(".md").write_text(informe(filas, ch), encoding="utf-8")
    print(f"resueltos por el martillo: {sum(f['resuelto_por_martillo'] for f in filas)} de {len(filas)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
