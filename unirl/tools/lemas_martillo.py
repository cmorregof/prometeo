"""¿El martillo solo demuestra cada lema del cuaderno congelado 835d3070e3b0c3b1? (auditoría de la ronda 2, 14 oct 2026)

Para cada lema: su enunciado sin la prueba, a nivel de teoría (como en la admisión: HOL-Analysis, el preludio de su
método si no es general, sin el resto del cuaderno), cerrado con el mismo martillo de la ronda (try0 5 s y, si no
cierra, Sledgehammer 60 s; el ML y el método `martillo` se copian en ejecución de unirl.martillo.TEORIA_PASOS, sin
tocar unirl/). Pasada 1 con quick_and_dirty, como martillo_en_pasos; si encuentra una línea, pasada 2 sin atajos con la
plantilla de admisión del cuaderno (rc = 0, sin oráculos, sin skip_proof, sin axiomas nuevos). No usa la caché ni el
candado del martillo (logs/), no llama a la API y solo escribe en la carpeta de salida y en ~/isabelle/scratch.
Reanudable: los lemas que ya tienen fila en el archivo de salida no se repiten.

  python unirl/tools/lemas_martillo.py . resultados/rejuicio/ronda2 [tope]
  LEMAS_SOLO=a,b LEMAS_SALIDA=lemas_martillo_repeticion.jsonl python unirl/tools/lemas_martillo.py . resultados/rejuicio/ronda2

Historia (resultados/rejuicio/ronda2/): la primera corrida (14 oct, 13:26–16:21) cerraba solo la primera meta
(`by (martillo 1)`); el 15 oct se repitieron 20 lemas con `by (martillo 1)+` y una línea por meta en la pasada 2: los «no»
con más de 5 s de suspensión (el Mac se durmió con la tapa cerrada) y cu_abs_distance_between, que tiene dos conclusiones.
"""

import json
import os
import re
import sys
import time
from pathlib import Path

RAIZ, SALIDA = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
TOPE = int(sys.argv[3]) if len(sys.argv) > 3 else None  # como mucho N lemas nuevos (para probar)
SOLO = set(filter(None, os.environ.get("LEMAS_SOLO", "").split(",")))  # repetir solo estos lemas
ARCHIVO = os.environ.get("LEMAS_SALIDA", "lemas_martillo.jsonl")
sys.path.insert(0, str(RAIZ))

from unirl import cuaderno as Cu  # noqa: E402
from unirl import martillo as M  # noqa: E402
from unirl.gd_isabelle import TheoremVerifier, fill_lines  # noqa: E402

CONGELADO = RAIZ / "runs" / "unirl" / "cuaderno" / "congelados" / "835d3070e3b0c3b1" / "lemas.json"
PRUEBA_E = [RAIZ / "runs/unirl/rl_verbal/evaluacion_E/20261013-221752-gpt-6-luna/llamadas.jsonl",
            RAIZ / "runs/unirl/rl_verbal/pareada_luna/20261013-221752-gpt-6-luna/llamadas.jsonl"]
CLAVES_PRUEBA = ("proof", "by", "using", "unfolding", "apply", "including", "supply")


def separar(texto: str) -> tuple[str, str]:
    """(enunciado, prueba): corta en la primera palabra clave de prueba fuera de cadenas, cartuchos y comentarios."""
    i, n, cad, cart, com = 0, len(texto), False, 0, 0
    while i < n:
        if com:
            if texto.startswith("*)", i):
                com -= 1; i += 2; continue
            if texto.startswith("(*", i):
                com += 1; i += 2; continue
            i += 1; continue
        if cad:
            if texto[i] == "\\" and i + 1 < n and texto[i + 1] == '"':
                i += 2; continue
            if texto[i] == '"':
                cad = False
            i += 1; continue
        if texto.startswith("\\<open>", i):
            cart += 1; i += 7; continue
        if texto.startswith("\\<close>", i):
            cart -= 1; i += 8; continue
        if cart:
            i += 1; continue
        if texto.startswith("(*", i):
            com += 1; i += 2; continue
        if texto[i] == '"':
            cad = True; i += 1; continue
        m = re.match(r"[A-Za-z_]+", texto[i:])
        if m:
            w = m.group(0)
            antes = texto[i - 1] if i else " "
            if w in CLAVES_PRUEBA and not (antes.isalnum() or antes in "_'.") and i > 0:
                return texto[:i].rstrip(), texto[i:]
            i += len(w); continue
        i += 1
    raise ValueError("no encontré dónde empieza la prueba")


# el ML del martillo y el método `martillo k`, copiados de la plantilla de la ronda (desde el primer ML hasta method_setup)
_P = M.TEORIA_PASOS
_ini = _P.index("ML \\<open>")
_fin = _P.index("\n", _P.index("method_setup martillo"))
CABECERA_ML = _P[_ini:_fin + 1]

TEORIA = r'''theory LemaMartillo
  imports "HOL-Analysis.Analysis"
begin

__PRELUDE__

''' + CABECERA_ML + r'''
__ENUNCIADO__
  by (martillo 1)+

ML \<open>File.write (Path.explode "__OUT__") (jlist (rev (!isarl_pasos)))\<close>

end
'''


def mostrados_en_prueba() -> dict[str, set[str]]:
    d: dict[str, set[str]] = {}
    for f in PRUEBA_E:
        for l in f.open(encoding="utf-8"):
            r = json.loads(l)
            if r.get("tipo") == "intento":
                for nm in r.get("lemas_mostrados") or []:
                    d.setdefault(nm, set()).add(r["peldano"])
    return d


def main() -> int:
    SALIDA.mkdir(parents=True, exist_ok=True)
    out_jsonl = SALIDA / ARCHIVO
    hechos = {json.loads(l)["nombre"] for l in out_jsonl.open(encoding="utf-8")} if out_jsonl.exists() else set()
    lemas = json.loads(CONGELADO.read_text(encoding="utf-8"))["lemas"]
    mostrados = mostrados_en_prueba()
    juez = TheoremVerifier.desde_corpus("orden_1_lineal")
    preludios = Cu.preludios()
    nuevos = 0
    for k, lema in enumerate(lemas, 1):
        if lema["nombre"] in hechos or (SOLO and lema["nombre"] not in SOLO):
            continue
        if TOPE is not None and nuevos >= TOPE:
            break
        nuevos += 1
        enunciado, _ = separar(lema["texto"])
        etiquetas = ['"assms"'] if re.search(r"\bassumes\b", enunciado) else []
        pre = preludios[lema["alcance"]] if lema["alcance"] != "general" else ""
        w = juez._workdir("lema-martillo-")
        (w / "cache_pasos.txt").write_text("", encoding="utf-8")
        tabla = {"PRELUDE": pre, "ENUNCIADO": enunciado, "OUT": str(w / "pasos.json"), "CACHEIN": str(w / "cache_pasos.txt"),
                 "ETIQUETAS": ", ".join(etiquetas), "SH": str(M.SH_TIMEOUT), "TRYCERO": str(M.TRY0_TIMEOUT)}
        thy, _ = fill_lines(TEORIA, tabla)
        reloj = M.Reloj()
        rc1, log1 = M._build_quick(juez, w, thy, "LemaMartillo", M.SH_TIMEOUT + M.TRY0_TIMEOUT + 240)
        pasos = json.loads((w / "pasos.json").read_text()) if (w / "pasos.json").exists() else []
        res = pasos[0]["resultado"] if pasos else None
        lineas = [M.linea_de(x["resultado"]) for x in pasos]
        if len(pasos) > 1:  # varias conclusiones: una línea por meta, aplicadas en orden
            metodos = [M.metodo_de_linea(x) if x else None for x in lineas]
            linea = ("\n".join(f"  apply {m}" for m in metodos) + "\n  done").lstrip() if all(metodos) else None
        else:
            linea = lineas[0] if lineas else None
        fila = {"k": k, "nombre": lema["nombre"], "alcance": lema["alcance"], "origen": lema["procedencia"].get("peldano"),
                "mostrado_en_prueba": sorted(mostrados.get(lema["nombre"], set())), "rc_pasada1": rc1,
                "fuente": (res or {}).get("fuente"), "metas": len(pasos), "linea": linea, "pasada2": None, "demuestra_el_martillo": False,
                "errores_pasada1": [x for x in log1.splitlines() if x.startswith("***")][:4],
                "s_pasada1": round(reloj.ms() / 1000, 1), "suspension_s": reloj.suspension_s(),
                "trabajo": str(w), "fecha": time.strftime("%Y-%m-%dT%H:%M:%S")}
        if linea:
            w2 = juez._workdir("lema-martillo-p2-")
            out2 = w2 / "admision.json"
            thy2, _ = fill_lines(Cu.LEMA_ADMISION, {"PRELUDE": pre, "CUADERNO": "", "NOMBRE": lema["nombre"],
                                                    "LEMA": enunciado + "\n  " + linea, "OUT": str(out2)})
            rc2, log2 = juez.build(w2, thy2, "Admision", 300)
            d = json.loads(out2.read_text()) if rc2 == 0 and out2.exists() else None
            ok = bool(d) and not d["oracles"] and not d["skip_proof"] and d["axioms_ok"]
            fila["pasada2"] = {"rc": rc2, "admision": d, "errores": [x for x in log2.splitlines() if x.startswith("***")][:4]}
            fila["demuestra_el_martillo"] = ok
        with out_jsonl.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(fila, ensure_ascii=False) + "\n")
        print(f"[lemas] {k}/{len(lemas)} {lema['nombre']}: {fila['fuente']} → "
              f"{'lo demuestra' if fila['demuestra_el_martillo'] else 'no'} ({fila['s_pasada1']} s)", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
