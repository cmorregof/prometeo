"""Validación en Isabelle del corpus de búsqueda de raíces (Etapa 1).

Para cada método compila una teoría con su preludio y, por cada peldaño:
  * un `locale` con sus fixes y assumes (Isabelle lee y tipa las hipótesis);
  * dentro del locale, `@{prop ‹concl›}` en ML (Isabelle lee y tipa la conclusión en ese contexto);
  * una `interpretation` con valores concretos que prueba que las hipótesis se pueden cumplir (no vacuidad).
No demuestra ninguna conclusión: eso es trabajo del proponente. Escribe corpus/raices/validacion_isabelle.json.

Uso: .venv/bin/python tools/corpus_isabelle.py [--metodo biseccion]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parents[2]  # rl_metodos/
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "unirl" / "tools"))
from unirl.gd_isabelle import TheoremVerifier  # noqa: E402
import corpus_raices as cr  # noqa: E402

PRUEBA = "by unfold_locales (auto simp: field_simps intro!: derivative_eq_intros continuous_intros)"
ID = r"(\<lambda>x::real. x)"
N_TEST = [ID, r"(\<lambda>x::real. 1)", r"(\<lambda>x::real. 0)", "0", "1", "1", "0"]
NC_TEST = [ID, r"(\<lambda>x::real. 1)", r"(\<lambda>x::real. 0)", "0", "1"]  # f f' f'' r ε (hipótesis clásicas locales)

# valores de ejemplo, en el orden de los fixes de cada peldaño
TESTIGOS = {
    "bis_1_ancho": [ID, "-1", "1", "0"], "bis_2_encaje": [ID, "-1", "1", "0"], "bis_3_signo": [ID, "-1", "1", "0"],
    "bis_4_raiz": [ID, "-1", "1", "0"], "bis_5_cota": [ID, "-1", "1", "0"], "bis_6_iteraciones": [ID, "-1", "1", "1", "0"],
    "bis_7_convergencia": [ID, "-1", "1"],
    "pf_1_derivada": [r"(\<lambda>x::real. x / 2)", r"(\<lambda>x::real. 1 / 2)", "0", "1", "1 / 2", "0", "1"],
    "pf_2_dentro": [r"(\<lambda>x::real. x / 2)", "0", "1", "1 / 2", "1", "0"],
    "pf_3_unicidad": [r"(\<lambda>x::real. x / 2)", "0", "1", "1 / 2", "1", "0", "0"],
    "pf_4_decaimiento": [r"(\<lambda>x::real. x / 2)", "0", "1", "1 / 2", "1", "0", "0"],
    "pf_5_a_priori": [r"(\<lambda>x::real. x / 2)", "0", "1", "1 / 2", "1", "0", "0"],
    "pf_6_a_priori_x1": [r"(\<lambda>x::real. x / 2)", "0", "1", "1 / 2", "1", "0", "0"],
    "pf_6p_a_posteriori": [r"(\<lambda>x::real. x / 2)", "0", "1", "1 / 2", "1", "0", "0"],
    "pf_7_existencia": [r"(\<lambda>x::real. x / 2)", "0", "1", "1 / 2", "1"],
    "pf_8_convergencia": [r"(\<lambda>x::real. x / 2)", "0", "1", "1 / 2", "1"],
    "pf_9_cuadratico": [r"(\<lambda>x::real. 0)", r"(\<lambda>x::real. 0)", "0", "1", "0", "0", "0"],
    "newton_1_paso": N_TEST + ["0"], "newton_2_contraccion": N_TEST + ["0"], "newton_3_decaimiento": N_TEST + ["0", "0"],
    "newton_4_convergencia": N_TEST + ["0"], "newton_5_orden2": N_TEST + ["0", "0"],
    "orden_1_lineal": [r"(\<lambda>j::nat. 0::real)", "0", "0"], "orden_2_cuadratico_lineal": [r"(\<lambda>j::nat. 0::real)", "0", "0"],
    "orden_3_cuadratico": [r"(\<lambda>j::nat. 0::real)", "0", "0"],
    "secante_1_inyectiva": N_TEST + ["0", "1 / 2"], "secante_2_cociente": N_TEST + ["0", "1 / 2"],
    "secante_3_producto": N_TEST + ["0", "1 / 2"], "secante_4_contraccion": N_TEST + ["0", "1 / 2"],
    "secante_5_convergencia": N_TEST + ["0", "1 / 2"], "secante_6_fibonacci": N_TEST + ["0", "1 / 2", "0"],
    "rf_1_punto": [ID, "-1", "1"], "rf_2_signo": [ID, "-1", "1", "0"], "rf_3_encaje": [ID, "-1", "1", "0"],
    "rf_4_raiz": [ID, "-1", "1", "0"], "rf_5_limites": [ID, "-1", "1"], "rf_6_convergencia": [ID, "-1", "1"],
    # versiones clásicas (24 sep 2026)
    "bis_5c_cota_uniforme": [ID, "-1", "1"],
    "pf_5c_a_priori_max": [r"(\<lambda>x::real. x / 2)", "0", "1", "1 / 2", "1", "0", "0"],
    "pf_9c_cuadratico_medio": [r"(\<lambda>x::real. 0)", r"(\<lambda>x::real. 0)", "0", "1", "0", "0", "0"],
    "newton_2c_contraccion_local": NC_TEST, "newton_4c_convergencia_local": NC_TEST, "newton_5c_orden2_local": NC_TEST,
    "newton_6c_q_orden2": NC_TEST,
    "secante_4c_contraccion_local": NC_TEST, "secante_5c_convergencia_local": NC_TEST,
    # f''(r) ≠ 0 exige una f no lineal: f(x) = x + x², con f' = 1 + 2x y f'' = 2
    "secante_6c_orden_phi": [r"(\<lambda>x::real. x + x * x)", r"(\<lambda>x::real. 1 + 2 * x)", r"(\<lambda>x::real. 2)", "0", "1 / 4"],
    "rf_6c_puntos_convergen": [ID, "-1", "1"],
}


def n_fixes(fixes: str) -> int:
    """Número de variables fijadas: cuenta identificadores antes de cada '::' en cada grupo separado por 'and'."""
    total = 0
    for grupo in re.split(r"\band\b", fixes):
        nombres = grupo.split("::")[0].split()
        total += len(nombres)
    return total


def teoria(metodo: str, peldanos: list[dict]) -> str:
    partes = [f"theory Corpus_{metodo}\n  imports {cr.IMPORTS}\nbegin\n", cr.PRELUDIO[metodo], ""]
    for p in peldanos:
        w = TESTIGOS[p["id"]]
        if len(w) != n_fixes(p["fixes"]):
            raise SystemExit(f"{p['id']}: {len(w)} testigos para {n_fixes(p['fixes'])} variables")
        partes.append(f"locale {p['id']} =\n  fixes {p['fixes']}\n  assumes {p['assumes']}\nbegin\n"
                      f"ML \\<open>val _ = @{{prop \\<open>{p['concl']}\\<close>}}\\<close>\nend\n")
        args = " ".join(f'"{x}"' for x in w)  # cada argumento es un término: va entre comillas
        partes.append(f"interpretation ejemplo_{p['id']}: {p['id']} {args}\n  {PRUEBA}\n")
    partes.append('ML \\<open>File.write (Path.explode "__DIR__/ok") ""\\<close>\n\nend\n')
    return "\n".join(partes)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--metodo")
    a = ap.parse_args()
    v = TheoremVerifier("gd_n1", build_timeout_s=600)
    metodos = [a.metodo] if a.metodo else list(cr.PRELUDIO)
    res = {}
    for m in metodos:
        ps = [p for p in cr.P if p["metodo"] == m]
        w = v._workdir(f"gd-corpus-{m}-")
        thy = teoria(m, ps).replace("__DIR__", str(w))
        t = time.perf_counter()
        rc, log = v.build(w, thy, f"Corpus_{m}", 600)
        ok = rc == 0 and (w / "ok").exists()
        errs = [l for l in log.splitlines() if l.startswith("***")][:12]
        res[m] = {"ok": ok, "peldanos": [p["id"] for p in ps], "s": round(time.perf_counter() - t, 1), "errores": errs,
                  "teoria": str(w / f"Corpus_{m}.thy")}
        print(f"[corpus_isabelle] {m}: {'OK' if ok else 'FALLA'} ({len(ps)} peldaños, {res[m]['s']} s)")
        for e in errs[:8]:
            print("    " + e[:220])
    salida = HERE / "corpus" / "curado" / "raices" / "validacion_isabelle.json"
    salida.parent.mkdir(parents=True, exist_ok=True)
    previo = json.loads(salida.read_text(encoding="utf-8")) if salida.exists() and a.metodo else {}
    previo.update(res)
    salida.write_text(json.dumps(previo, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0 if all(r["ok"] for r in res.values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
