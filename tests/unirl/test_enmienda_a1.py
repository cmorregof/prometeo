"""Enmienda A1: leer resultados.jsonl mientras otro hilo escribe no debe crear filas falsas de resultado."""

import json
import time

from test_v6 import LakeV6, _anexo_en_disco, mundo  # noqa: F401  (mundo es un fixture)

from unirl import fase1 as F1
from unirl import fase2 as F2
from unirl import frontera as F
from unirl import prompts_v6 as PR


def _registrar_en_dos_partes(ruta, d):
    """Deja visible una línea a medio escribir, que es lo que un lector puede encontrar en Linux."""
    txt = json.dumps(d, ensure_ascii=False) + "\n"
    with ruta.open("a", encoding="utf-8") as fh:
        fh.write(txt[: len(txt) // 2])
        fh.flush()
        time.sleep(0.002)
        fh.write(txt[len(txt) // 2 :])


def test_a1_lectura_durante_una_escritura_no_crea_filas_falsas(mundo, tmp_path, monkeypatch):  # noqa: F811
    monkeypatch.setattr(F, "_registrar", _registrar_en_dos_partes)
    _, anexo = _anexo_en_disco(mundo, tmp_path)
    f2 = tmp_path / "f2"
    estado = F2.correr(f2, anexo, mundo["tareas"], LakeV6(), PR.ProveedorSecoV6, paralelo=4, exigir_registro=False, exigir_api_conteos=False)
    assert estado["motivo_fin"].startswith("RETENIDA")
    assert not (f2 / "errores.jsonl").exists()
    celdas = [r["celda"] for r in F1._leer_jsonl(f2 / "resultados.jsonl") if "resuelto" in r]
    assert len(celdas) == len(set(celdas))
