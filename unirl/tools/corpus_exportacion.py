"""Comprueba, para cada peldaño del corpus, que la teoría final del juez compila y exporta el teorema al contexto
global con sus hipótesis (`isarl_export`), usando `sorry` en modo quick_and_dirty SOLO en esta comprobación.
No demuestra nada: detecta enunciados cuya exportación el juez no sabría hacer (como el «OF: multiple unifiers»
del 24 sep 2026). Uso: .venv/bin/python tools/corpus_exportacion.py
"""

from __future__ import annotations

import json
import sys
import time
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parents[2]  # rl_metodos/
sys.path.insert(0, str(HERE))
from unirl.corpus import cargar  # noqa: E402
from unirl.gd_isabelle import TheoremVerifier  # noqa: E402


def main() -> int:
    ents = cargar("raices")
    v0 = TheoremVerifier.desde_corpus(ents[0]["id"])
    work = v0._workdir("gd-exportacion-")
    nombres = []
    for e in ents:
        v = TheoremVerifier.desde_corpus(e["id"])
        out, tout = work / f"{e['id']}.final.json", work / f"{e['id']}.target.json"
        thy, _ = v.final_theory("sorry", "", out, tout)
        nombre = f"Final_{e['id']}"
        (work / f"{nombre}.thy").write_text(thy.replace("theory Final\n", f"theory {nombre}\n", 1), encoding="utf-8")
        nombres.append(nombre)
    sesion = f"IsaRL_GD_{uuid.uuid4().hex[:10]}"
    (work / "ROOT").write_text(f'session {sesion} = "HOL-Analysis" +\n  options [document = false, timeout = 0, quick_and_dirty = true]\n'
                               "  theories\n" + "".join(f"    {n}\n" for n in nombres), encoding="utf-8")
    import subprocess
    cmd = [str(v0.config08.ISABELLE_BIN), "build", "-o", "document=false", "-d", str(work), sesion]
    t = time.perf_counter()
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=3600)
    res = {}
    for e in ents:
        f = work / f"{e['id']}.final.json"
        d = json.loads(f.read_text()) if f.exists() else None
        res[e["id"]] = {"exporta": bool(d and d.get("export_ok")), "skip_proof_detectado": bool(d and d.get("skip_proof"))}
    malos = [k for k, r in res.items() if not r["exporta"]]
    print(f"[exportacion] rc={p.returncode} en {time.perf_counter() - t:.0f} s; exportan {len(ents) - len(malos)}/{len(ents)}; "
          f"sorry detectado como skip_proof en {sum(r['skip_proof_detectado'] for r in res.values())}/{len(ents)}")
    for l in [l for l in p.stdout.splitlines() if l.startswith("***")][:10]:
        print("   ", l[:200])
    (HERE / "corpus" / "curado" / "raices" / "validacion_exportacion.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    return 0 if not malos else 2


if __name__ == "__main__":
    raise SystemExit(main())
