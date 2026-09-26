"""Rutas y versiones fijadas. Todo se puede sobreescribir con variables de entorno."""

from __future__ import annotations

import os
from pathlib import Path

HOME = Path.home()
ISABELLE_ROOT = Path(os.environ.get("ISARL_ISABELLE_ROOT", HOME / "isabelle"))
ISABELLE_BIN = Path(os.environ.get("ISARL_ISABELLE", ISABELLE_ROOT / "Isabelle2025.app" / "bin" / "isabelle"))
PAPER_REPO = Path(os.environ.get("ISARL_PAPER_REPO", ISABELLE_ROOT / "Verified_Numerical_Methods"))
UTP_REPO = Path(os.environ.get("ISARL_UTP_REPO", ISABELLE_ROOT / "CyPhyAssure"))
SCRATCH = Path(os.environ.get("ISARL_SCRATCH", ISABELLE_ROOT / "scratch"))
HERE = Path(__file__).resolve().parent.parent
TARGETS_DIR = HERE / "isabelle" / "Targets"

PAPER_COMMIT = "0e7830d1e58726698a1316ceaa25892dcbcce366"
UTP_COMMIT = "a41662b8201e92bd3ae3dcfe1094be2d0256dfac"
ISABELLE_VERSION = "Isabelle2025"
PAPER_SESSION = "Numerical_Methods_Paper"

# Variables de entorno de Isabelle que dicen qué provers externos hay instalados.
PROVER_ENV_VARS = ["E_HOME", "VAMPIRE_HOME", "Z3_SOLVER", "CVC5_SOLVER", "SPASS_HOME", "ZIPPERPOSITION_HOME", "ISABELLE_VERIT"]


def session_dirs() -> list[str]:
    return [str(UTP_REPO), str(PAPER_REPO)]
