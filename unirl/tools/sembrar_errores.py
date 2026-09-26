"""Siembra cuaderno/errores.json y errores.md desde el glosario comprobado (Etapa 3).

Primero hay que comprobar el glosario en Isabelle (escribe cuaderno/glosario_verificacion.json con el hash del glosario):
    .venv/bin/python -c "from unirl.martillo import verificar_glosario; print(verificar_glosario()['ok'])"
Si la comprobación falta, es de otra versión del glosario o tiene filas que no pasan, no siembra nada.
No pisa un errores.json con apariciones registradas (eso ya es cuaderno de episodios): usar --forzar.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
from unirl import cuaderno  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--forzar", action="store_true")
    a = ap.parse_args()
    if cuaderno.ERRORES_JSON.exists() and not a.forzar:
        previo = json.loads(cuaderno.ERRORES_JSON.read_text(encoding="utf-8"))
        if any(e["contadores"]["apariciones"] for e in previo.get("errores", [])):
            print("errores.json ya tiene apariciones registradas; usa --forzar para resembrar")
            return 2
    doc = cuaderno.sembrar_errores()
    cuaderno.escribir_errores(doc)
    print(f"sembrados {len(doc['errores'])} errores en {cuaderno.ERRORES_JSON.relative_to(HERE)} y {cuaderno.ERRORES_MD.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
