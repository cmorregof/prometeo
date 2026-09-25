"""Validación en Isabelle del juez de teorema de stepsize (docs/diseno_gd_isabelle.md), antes de las corridas gd.

(i)   no vacuidad: las hipótesis interp y opt son satisfacibles (f = x²/2, g = id, xs = 0 en los reales);
(ii)  cota superior: para gd_n1 y gd_const_n2, alguna demostración generada desde el certificado exacto del PEP
      (targets/gd_cert/<objetivo>.proof_{A,B,C}.txt) es ACCEPTED por el juez real, con todos sus filtros;
(iii) controles: 'sorry' lo para el filtro (UNSOUND); 'sorry' saltándose el filtro lo para el kernel (UNSOUND);
      'by simp' no demuestra gd_n1 (PROOF_FAILED).

Escribe logs/gd_validacion.json. Código de salida 0 solo si (i) y (iii) pasan y al menos un objetivo de (ii) queda
ACCEPTED. Opciones: --rapido (solo (i) y (iii)); --solo <objetivo> (solo ese objetivo en (ii)).
Nunca correr mientras corre una bisección en Isabelle (Sledgehammer tiene límite de tiempo real).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
from unirl.gd_isabelle import TheoremVerifier  # noqa: E402

CERT = HERE / "targets" / "gd_cert"
LOG = HERE / "logs" / "gd_validacion.json"

NO_VACUO = r'''theory NoVacuo
  imports "HOL-Analysis.Inner_Product"
begin

lemma isarl_no_vacuo:
  "\<exists>f g (xs::real). (\<forall>x y. f y + inner (g y) (x - y) + (1/2) * (norm (g x - g y))\<^sup>2 \<le> f x) \<and> g xs = 0"
__PROOF__

ML \<open>File.write (Path.explode "__DIR__/novacuo.ok") ""\<close>

end
'''
NO_VACUO_PRUEBAS = [
    '  apply (rule exI[where x = "\\<lambda>x::real. x\\<^sup>2 / 2"])\n  apply (rule exI[where x = "id :: real \\<Rightarrow> real"])\n'
    '  apply (rule exI[where x = "0::real"])\n  apply (simp add: power2_eq_square field_simps)\n  done',
    '  apply (rule exI[where x = "\\<lambda>x::real. x\\<^sup>2 / 2"])\n  apply (rule exI[where x = "id :: real \\<Rightarrow> real"])\n'
    '  apply (rule exI[where x = "0::real"])\n  apply (auto simp: power2_eq_square algebra_simps)\n  done',
]


def log(msg: str) -> None:
    print(f"[gd_validar] {msg}", flush=True)


def no_vacuo(v: TheoremVerifier) -> dict:
    for k, prueba in enumerate(NO_VACUO_PRUEBAS):
        work = v._workdir("gd-novacuo-")
        thy = NO_VACUO.replace("__PROOF__", prueba).replace("__DIR__", str(work))
        t = time.perf_counter()
        rc, out = v.build(work, thy, "NoVacuo", v.build_timeout_s)
        ok = rc == 0 and (work / "novacuo.ok").exists()
        res = {"ok": ok, "prueba": k, "s": round(time.perf_counter() - t, 1),
               "errores": [l for l in out.splitlines() if l.startswith("***")][:8]}
        log(f"no vacuidad (prueba {k}): {'OK' if ok else 'falló'} en {res['s']} s")
        if ok:
            return res
    return res


def control(nombre: str, obtenido: str, esperado: str, s: float, extra: dict | None = None) -> dict:
    ok = obtenido == esperado
    log(f"control {nombre}: {obtenido} (esperado {esperado}) {'OK' if ok else 'FALLA'} en {s:.1f} s")
    return {"ok": ok, "obtenido": obtenido, "esperado": esperado, "s": round(s, 1), **(extra or {})}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rapido", action="store_true")
    ap.add_argument("--solo")
    a = ap.parse_args()
    res: dict = {"inicio": time.strftime("%Y-%m-%d %H:%M:%S")}
    v1 = TheoremVerifier("gd_n1")
    t1 = v1.target()
    res["no_vacuo"] = no_vacuo(v1)

    t = time.perf_counter()
    o = v1.verify(t1, {"proof": "sorry"})
    res["control_filtro_sorry"] = control("filtro sorry", o.outcome_label, "UNSOUND", time.perf_counter() - t)
    t = time.perf_counter()
    fin = v1.compile_final("sorry")
    lab, _ = v1.classify(fin)
    res["control_kernel_sorry"] = control("kernel sorry", lab, "UNSOUND", time.perf_counter() - t, {"errores": fin["errors"][:5]})
    t = time.perf_counter()
    o = v1.verify(t1, {"proof": "by simp"})
    res["control_by_simp"] = control("by simp", o.outcome_label, "PROOF_FAILED", time.perf_counter() - t, {"errores": o.raw.get("errors", [])[:5]})

    res["cota_superior"] = {}
    if not a.rapido:
        for obj in ([a.solo] if a.solo else ["gd_n1", "gd_const_n2"]):
            v = v1 if obj == "gd_n1" else TheoremVerifier(obj)
            tg = v.target()
            intentos = []
            for p in sorted(CERT.glob(f"{obj}.proof_*.txt")):
                t = time.perf_counter()
                o = v.verify(tg, {"proof": p.read_text(encoding="utf-8")})
                s = time.perf_counter() - t
                intentos.append({"variante": p.name, "etiqueta": o.outcome_label, "s": round(s, 1),
                                 "errores": (o.raw.get("errors") or [])[:8], "motivo": o.raw.get("reason")})
                log(f"cota superior {obj} {p.name}: {o.outcome_label} en {s:.1f} s")
                for e in (o.raw.get("errors") or [])[:4]:
                    log(f"    {e[:200]}")
                if o.accepted:
                    break
            res["cota_superior"][obj] = {"aceptada": any(i["etiqueta"] == "ACCEPTED" for i in intentos), "intentos": intentos}

    controles_ok = all(res[k]["ok"] for k in ("control_filtro_sorry", "control_kernel_sorry", "control_by_simp"))
    cota_ok = a.rapido or any(c["aceptada"] for c in res["cota_superior"].values())
    res["ok"] = bool(res["no_vacuo"]["ok"] and controles_ok and cota_ok)
    res["fin"] = time.strftime("%Y-%m-%d %H:%M:%S")
    LOG.parent.mkdir(parents=True, exist_ok=True)
    LOG.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    log(f"resultado global: {'OK' if res['ok'] else 'FALLA'} (detalle en {LOG.relative_to(HERE)})")
    return 0 if res["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
