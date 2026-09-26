"""Prueba mínima de `isarl` (antes 08_isabelle, sin pruebas): el paquete importa sin Isabelle y el registro de la
reproducción de la Tabla 1 del artículo se lee y tiene 15 VCs."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_isarl_importa_sin_isabelle():
    import isarl
    import isarl.config
    import isarl.driver
    import isarl.repro_bisection  # noqa: F401

    assert isarl.config.ISABELLE_ROOT.name  # una ruta, exista o no en esta máquina


def test_repro_bisection_tiene_15_vcs():
    d = json.loads((ROOT / "runs" / "isabelle" / "repro_bisection.json").read_text(encoding="utf-8"))
    vcs = d["result"]["vcs"]
    assert d["result"]["n_vcs"] == 15 and len(vcs) == 15
    assert sorted(v["index"] for v in vcs) == list(range(1, 16))
    # la cifra del informe: la automatización sola (try0 + Sledgehammer) cierra 11 con el lema importado, 9 sin él
    assert d["result"]["n_closed_auto"] == sum(1 for v in vcs if v["one_liner"])
