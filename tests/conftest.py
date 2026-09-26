"""Configuración común de las pruebas.

Las pruebas marcadas `isabelle` necesitan Isabelle2025 (`~/isabelle/Isabelle2025.app`, o la ruta de la variable
`ISARL_ISABELLE`) y tardan minutos. Si no está instalada se omiten con esa marca, en lugar de fallar: así
`pytest` completo pasa en cualquier máquina y el CI corre `-m "not isabelle"`.
"""

import os
from pathlib import Path

import pytest

ISABELLE = Path(os.environ.get("ISARL_ISABELLE", Path.home() / "isabelle" / "Isabelle2025.app" / "bin" / "isabelle"))


def pytest_collection_modifyitems(config, items):
    if ISABELLE.exists():
        return
    marca = pytest.mark.skip(reason=f"Isabelle2025 no está en {ISABELLE}")
    for item in items:
        if "isabelle" in item.keywords:
            item.add_marker(marca)
