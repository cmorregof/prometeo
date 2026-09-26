"""Corpus de teoremas para el aprendizaje por refuerzo verbal (PLAN_rl_verbal.md, Etapa 1).

Cada entrada de `corpus/<tema>/<id>.json` es un peldaño en el formato del juez de teorema. Solo los peldaños con
`estado == "aprobado"` (aprobados por Carlos) se pueden usar en una corrida: `usables()` es la única puerta.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent  # rl_metodos/
CORPUS = BASE / "corpus" / "curado"  # los peldaños aprobados a mano; corpus/existencia queda para la tesis
ESTADOS = ("aprobado", "pendiente_revision", "conjetura")
SPLITS = ("train", "test")
CAMPOS = ("id", "name", "kind", "metodo", "peldano", "split", "estado", "dificultad", "fuente", "dependencias", "imports",
          "session_parent", "prelude", "fixes", "assumes", "concl", "statement_es", "frozen_hash")
HASH_FIELDS = ("imports", "prelude", "fixes", "assumes", "concl")  # los mismos que TheoremVerifier._hash


def huella(e: dict) -> str:
    frozen = {k: e.get(k, "") for k in HASH_FIELDS}
    return hashlib.sha256(json.dumps(frozen, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16]


def cargar(tema: str = "raices", base: Path | None = None) -> list[dict]:
    """Todas las entradas del tema, validadas. Lanza ValueError ante cualquier inconsistencia."""
    ents = []
    for f in sorted(((base or CORPUS) / tema).glob("*.json")):
        if f.name.startswith("validacion_"):  # resultados de validación, no peldaños
            continue
        e = json.loads(f.read_text(encoding="utf-8"))
        faltan = [c for c in CAMPOS if c not in e]
        if faltan:
            raise ValueError(f"{f.name}: faltan campos {faltan}")
        if e["id"] != f.stem or e["name"] != e["id"]:
            raise ValueError(f"{f.name}: el id no coincide con el nombre del archivo")
        if e["estado"] not in ESTADOS or e["split"] not in SPLITS:
            raise ValueError(f"{f.name}: estado o split inválido")
        if huella(e) != e["frozen_hash"]:
            raise ValueError(f"{f.name}: el enunciado cambió y el hash no ({huella(e)} ≠ {e['frozen_hash']})")
        ents.append(e)
    ids = {e["id"] for e in ents}
    for e in ents:
        for d in e["dependencias"]:
            if d not in ids:
                raise ValueError(f"{e['id']}: dependencia desconocida {d}")
    return ents


class NoAprobado(PermissionError):
    """Se pidió usar un peldaño que Carlos no ha aprobado."""


def usables(tema: str = "raices", split: str | None = None, base: Path | None = None) -> list[dict]:
    """Solo peldaños aprobados por Carlos (y del split pedido). Única puerta de entrada a las corridas."""
    return [e for e in cargar(tema, base) if e["estado"] == "aprobado" and (split is None or e["split"] == split)]


def exigir_usable(id_: str, tema: str = "raices", base: Path | None = None) -> dict:
    """El peldaño `id_` si está aprobado; si no (pendiente de revisión, conjetura o inexistente), NoAprobado."""
    for e in cargar(tema, base):
        if e["id"] == id_:
            if e["estado"] != "aprobado":
                raise NoAprobado(f"{id_} está en estado {e['estado']!r}: necesita la aprobación de Carlos")
            return e
    raise NoAprobado(f"{id_} no existe en el corpus {tema}")
