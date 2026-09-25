"""Líneas base puras de 02, 04 y 05: el método sin agente, en el mismo banco de problemas que ve el agente.

Las cifras «un α fijo converge ~35 %» (02), «Newton puro converge ~73 %» (04) y «la secante pura converge ~69 %, la
regula falsi pura ~63 %, la bisección siempre, pero con ~32 evaluaciones» (05) están escritas como texto fijo en
report.py y trainer.py de cada paquete y en sus README; ninguna corrida las mide. Este script las mide sin tocar los
paquetes: mismo entorno, misma semilla y tolerancia que la configuración por defecto de la CLI (así son los mismos
3000 problemas que ve el agente en la fase 1), y una acción constante hasta que el episodio termina.

    python resultados/corridas_locales/lineas_base_puras.py > resultados/corridas_locales/lineas_base_puras.json
"""

from __future__ import annotations

import json
import statistics
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
N, SEMILLA = 3000, 0


def medir(env, accion: int, contador: str) -> dict:
    fin, costo = Counter(), []
    for _ in range(N):
        env.reset()
        hecho, info = False, ""
        while not hecho:
            _, _, hecho, info = env.step(accion)
        fin[info] += 1
        if info == "converged":
            costo.append(getattr(env, contador))
    return {"problemas": N, "convergen": fin["converged"], "tasa": round(fin["converged"] / N, 4),
            f"{contador}_media_si_converge": round(statistics.mean(costo), 2) if costo else None,
            "finales": dict(fin)}


def main() -> None:
    for p in ("02_punto_fijo", "04_newton", "05_secante"):
        sys.path.insert(0, str(ROOT / p))
    from fixpointrl.env_fixpoint import ACTION_NAMES as A02, FixpointEnv
    from newtonrl.env_newton import ACTION_NAMES as A04, NewtonEnv
    from secantrl.env_secant import ACTION_NAMES as A05, SecantEnv

    salida = {"semilla": SEMILLA, "problemas": N, "resultados": []}
    casos = [("02_punto_fijo", "α fijo (siempre «" + A02[0] + "»)", lambda: FixpointEnv(tol=1e-6, seed=SEMILLA), 0, "n_iter"),
             ("04_newton", "Newton puro (siempre «" + A04[0] + "»)", lambda: NewtonEnv(tol=1e-9, seed=SEMILLA), 0, "n_evals"),
             ("05_secante", "secante pura (siempre «" + A05[0] + "»)", lambda: SecantEnv(tol=1e-9, seed=SEMILLA), 0, "n_evals"),
             ("05_secante", "regula falsi pura (siempre «" + A05[1] + "»)", lambda: SecantEnv(tol=1e-9, seed=SEMILLA), 1, "n_evals"),
             ("05_secante", "bisección pura (siempre «" + A05[2] + "»)", lambda: SecantEnv(tol=1e-9, seed=SEMILLA), 2, "n_evals")]
    for proyecto, estrategia, hacer_env, accion, contador in casos:
        salida["resultados"].append({"proyecto": proyecto, "estrategia": estrategia, **medir(hacer_env(), accion, contador)})
    print(json.dumps(salida, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
