"""Demostración de `martillo_en_pasos` (Etapa 3): la prueba privada de orden_1_lineal con su paso inductivo cambiado
por `by martillo`. Corre dos veces con una caché nueva (la segunda debe salir de la caché) y escribe
resultados/martillo_pasos_demo.json. La prueba privada no sale de tests/fixtures: solo se registran la línea y los tiempos.

Uso: .venv/bin/python tools/martillo_pasos_demo.py   (en serie: no correr junto a la línea base del martillo)
"""

from __future__ import annotations

import json
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parents[2]  # rl_metodos/
sys.path.insert(0, str(HERE))
from unirl import martillo as m  # noqa: E402
from unirl.gd_isabelle import TheoremVerifier  # noqa: E402

PELDANO = "orden_1_lineal"
PRUEBA = HERE / "tests" / "fixtures" / "pruebas_privadas" / "orden_1_lineal.txt"
PASO = "by (rule mult_left_mono)"


def main() -> int:
    juez = TheoremVerifier.desde_corpus(PELDANO)
    prueba = PRUEBA.read_text(encoding="utf-8")
    assert PASO in prueba, "la prueba privada cambió"
    prueba = prueba.replace(PASO, "by martillo")
    with tempfile.TemporaryDirectory() as d:
        cache = m.Cache(Path(d) / "cache.sqlite")
        vueltas = []
        for _ in range(2):
            t = time.perf_counter()
            r = m.martillo_en_pasos(juez, prueba, cache=cache)
            vueltas.append({"s": round(time.perf_counter() - t, 1), "fuentes": [p["resultado"].get("fuente") for p in r["pasos"]],
                            "lineas": [p.get("linea") for p in r["pasos"]], "cerradas": r["cerradas"], "marcas": r["marcas"],
                            "veredicto_juez": r["veredicto_juez"], "errores_pasada1": r["errores_pasada1"]})
    a, b = vueltas
    out = {"peldano": PELDANO, "prueba": f"{PRUEBA.relative_to(HERE)} con `{PASO}` cambiado por `by martillo`",
           "marcas": a["marcas"], "cerradas": a["cerradas"], "fuente_primera": (a["fuentes"] or [None])[0],
           "linea": (a["lineas"] or [None])[0], "veredicto_juez": a["veredicto_juez"], "s_primera": a["s"],
           "fuente_segunda": (b["fuentes"] or [None])[0], "veredicto_segunda": b["veredicto_juez"], "s_cache": b["s"],
           "fecha": time.strftime("%Y-%m-%dT%H:%M"), "vueltas": vueltas, "veredicto_meta": juez.metadatos()}
    (HERE / "resultados").mkdir(exist_ok=True)
    (HERE / "resultados" / "martillo_pasos_demo.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("cerradas", "marcas", "fuente_primera", "linea", "veredicto_juez", "s_primera",
                                          "fuente_segunda", "veredicto_segunda", "s_cache")}, ensure_ascii=False))
    ok = a["veredicto_juez"] == "ACCEPTED" and b["veredicto_juez"] == "ACCEPTED" and b["fuentes"] == ["cache"]
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
