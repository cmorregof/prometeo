"""Configuración común de las pruebas.

Las pruebas marcadas `lean` necesitan Lean ≥ 4.32.2 (`unirl.juez_lean.lean_bin`: $UNIRL_LEAN, ~/.elan/bin/lean o el
PATH) y se omiten igual si no está. Las marcadas `isabelle` necesitan Isabelle2025 (`~/isabelle/Isabelle2025.app`, o la ruta de la variable
`ISARL_ISABELLE`) y tardan minutos. Si no está instalada se omiten con esa marca, en lugar de fallar: así
`pytest` completo pasa en cualquier máquina y el CI corre `-m "not isabelle"`.
"""

import os
from pathlib import Path

import pytest

ISABELLE = Path(os.environ.get("ISARL_ISABELLE", Path.home() / "isabelle" / "Isabelle2025.app" / "bin" / "isabelle"))


def pytest_collection_modifyitems(config, items):
    from unirl.juez_lean import lean_bin

    sin_isabelle = pytest.mark.skip(reason=f"Isabelle2025 no está en {ISABELLE}")
    sin_lean = pytest.mark.skip(reason="no se encontró Lean ($UNIRL_LEAN, ~/.elan/bin/lean o PATH)")
    hay_lean = lean_bin() is not None
    for item in items:
        if "isabelle" in item.keywords and not ISABELLE.exists():
            item.add_marker(sin_isabelle)
        if "lean" in item.keywords and not hay_lean:
            item.add_marker(sin_lean)
