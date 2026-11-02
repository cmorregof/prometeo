"""Sortea las 400 falsas del banco de Tantalus: las 200 del ETP completas y 200 de las 249 computacionales.

Nadie elige la semilla: es el SHA-256 del corpus congelado. Cada tarea recibe la nota SHA-256(semilla + ":" + id) y
entran las 200 notas más bajas, así que el resultado no depende de la versión de Python. El sorteo no mira si la tarea
ya tiene refutación. Kourovka 19.25 queda fuera porque sale del conjunto certificado.

Uso: python3 sorteo_400_falsas.py     Escribe banco_400_falsas.jsonl. Solo lee el corpus.
"""
import collections, hashlib, json
from pathlib import Path

AQUI = Path(__file__).resolve().parent
CORPUS = AQUI.parent.parent / "corpus_compilar" / "FINAL" / "corpus_compilado.jsonl"
CERTIFICADAS = AQUI.parent.parent / "corpus_compilar" / "sin_api_2026-11-02" / "certificadas.jsonl"
CUANTAS = 200


def sha(b):
    return hashlib.sha256(b).hexdigest()


def main():
    semilla = sha(CORPUS.read_bytes())
    filas = [json.loads(l) for l in CORPUS.read_text(encoding="utf-8").splitlines()]
    falsas = [r for r in filas if r.get("verdad") == "falso"]
    etp = [r for r in falsas if r["fuente"] == "etp"]
    comp = [r for r in falsas if r["fuente"] == "computacionales"]
    assert len(etp) == 200 and len(comp) == 249 and len(falsas) == 450
    nota = {r["id"]: sha(f"{semilla}:{r['id']}".encode()) for r in comp}
    elegidas = set(sorted(nota, key=lambda i: (nota[i], i))[:CUANTAS])
    ya = {json.loads(l)["id"] for l in CERTIFICADAS.read_text(encoding="utf-8").splitlines()}
    banco = etp + [r for r in comp if r["id"] in elegidas]
    with open(AQUI / "banco_400_falsas.jsonl", "w", encoding="utf-8") as f:
        for r in banco:
            f.write(json.dumps({"id": r["id"], "fuente": r["fuente"], "familia": r["familia"],
                                "subfamilia": r.get("subfamilia"), "sha256_tarea": r["sha256_tarea"],
                                "como_entra": "completa" if r["fuente"] == "etp" else "sorteo",
                                "nota_sorteo": nota.get(r["id"])}, ensure_ascii=False) + "\n")
    print("semilla (SHA-256 del corpus):", semilla)
    print("banco:", len(banco), "| ETP:", len(etp), "| computacionales sorteadas:", len(elegidas))
    print("computacionales sorteadas con refutación certificada en sin_api:", len(elegidas & ya), "| sin ella:", len(elegidas - ya))
    print("fuera del sorteo:", sorted(set(nota) - elegidas))
    print("por familia:", sorted(collections.Counter(r["familia"] for r in comp if r["id"] in elegidas).items()))
    print("de las 249, por familia:", sorted(collections.Counter(r["familia"] for r in comp).items()))
    print("sha256 banco:", sha((AQUI / "banco_400_falsas.jsonl").read_bytes()))


if __name__ == "__main__":
    main()
