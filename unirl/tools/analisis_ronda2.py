"""Puntos 3, 4 y 5 de la auditoría de la ronda 20261008-2003 (14–15 oct 2026), solo desde archivos; no compila ni llama
a la API. Lee resultados/rejuicio/ronda2/ (rejuicio.jsonl de rejuzgar.py, lemas_martillo*.jsonl de lemas_martillo.py) y
los llamadas.jsonl de E y E3; la nota de ejecución del encabezado es la de esa auditoría.

  python unirl/tools/analisis_ronda2.py .      → imprime y escribe resultados/rejuicio/ronda2/auditoria.md
"""

import json
import re
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(RAIZ))
from unirl.tools import rejuzgar as rj  # noqa: E402

DIR = RAIZ / "resultados" / "rejuicio" / "ronda2"
FILAS = rj.leer_jsonl(DIR / "rejuicio.jsonl")
CORPUS = {f.stem: json.loads(f.read_text()) for f in (RAIZ / "corpus/curado/raices").glob("*.json")}
ORDEN = [("gpt-6-luna", c) for c in ("B0", "B", "C", "E", "F", "C3", "E3")]
L: list[str] = []


def p(s=""):
    print(s)
    L.append(s)


def fmt_p(x):
    return "—" if x is None else f"{x:.4f}".replace(".", ",")


def limpia(s, n=110):
    return (s or "").replace("|", "/").replace("\n", " ")[:n]


# ---------------------------------------------------------------------------------------------------- punto 3
eps = rj.episodios(FILAS)
p("# Auditoría de la ronda 20261008-2003 (rejuzgar, referencia R)")
p()
p(f"Fuente: `resultados/rejuicio/ronda2/rejuicio.jsonl` ({len(FILAS)} intentos, {len(eps)} episodios). Episodio: la "
  "primera corrida en que terminó (regla de `ronda.py`). «En K»: antes del primer intento válido según R (o en "
  "cualquiera, si no hay válido) hubo uno «concordante_contaminado» o «indeterminado». Y: veredicto del juez; Y^a: el "
  "auditado (R).")
p()
p("Ejecución (Mac, sin API): `rejuzgar` juzgó 739 intentos el 14 oct de 01:37 a 07:09 con `--paralelo 2 --hilos 2`; el "
  "Mac se reinició a la fuerza a las 08:04 (`panic … btn_rst`); los 10 restantes (todos de E3) se juzgaron de 13:09 a "
  "13:10 con `--paralelo 1`. `parametros.json` conserva solo la fecha de la reanudación (no guarda paralelo ni hilos). "
  "`cruzado`: 13:20–13:25. Lemas del cuaderno: ver la sección 5.")
p()
p("## 3. Por configuración")
p()
p("| config | intentos | FP | FN | sin juicio | contaminados | indeterminados | regla estricta | tiempo | episodios | en K | fuera de K | Y = 1 | Y^a = 1 | Y^a indet. |")
p("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
for m, c in ORDEN:
    fs = [f for f in FILAS if f["modelo"] == m and f["config"] == c]
    cc = Counter(f["categoria"] for f in fs)
    es = [e for e in eps.values() if e["modelo"] == m and e["config"] == c]
    k = sum(e["contaminado"] for e in es)
    p(f"| {c} | {len(fs)} | {cc['FP']} | {cc['FN']} | {cc['sin_juicio']} | {cc['concordante_contaminado']} | "
      f"{cc['indeterminado']} | {cc['regla_estricta']} | {cc['tiempo']} | {len(es)} | {k} | {len(es) - k} | "
      f"{sum(e['y_juez'] for e in es)} | {sum(1 for e in es if e['y_ref'] == 1)} | {sum(1 for e in es if e['y_ref'] is None)} |")
p()
p("Contaminados, indeterminados y las demás categorías cuentan intentos; «en K» y las columnas Y cuentan episodios.")
p()
raros = [f for f in FILAS if f["categoria"] not in ("concordante", "sin_juicio")]
if raros:
    p("Intentos no concordantes (ni «sin juicio»):")
    p()
    p("| config | episodio | intento | juez | categoría | detalle | primer error del juez | primer error de R |")
    p("|---|---|---|---|---|---|---|---|")
    for f in raros:
        p(f"| {f['config']} | {f['episodio_id']} | {f['intento']} | {f['etiqueta_juez']} | {f['categoria']} | "
          f"{limpia(f.get('detalle'), 90)} | {limpia(f.get('primer_error_juez'))} | {limpia(f.get('primer_error_ref'))} |")
    p()

dif3 = sorted({e["peldano"] for e in eps.values() if e["split"] == "test" and e["dificultad"] <= 3})
p(f"### McNemar C frente a E, pareado por tarea y episodio, en los {len(dif3)} peldaños de dificultad ≤ 3")
p()
p(f"Peldaños: {', '.join(dif3)}. b = gana E, b' = gana C; p exacto bilateral (`rejuzgar.p_mcnemar`).")
p()
p("| veredicto | indeterminados de Y^a | pares | b (E gana) | b' (C gana) | p |")
p("|---|---|---|---|---|---|")
sub = {k: e for k, e in eps.items() if e["peldano"] in dif3}
for campo, nombre, indets in (("juez", "Y (juez)", ["excluir"]), ("ref", "Y^a (auditado)", ["excluir", "0", "1"])):
    for ind in indets:
        pr = rj.pares(sub, "gpt-6-luna", "C", "E", "episodio", ind)[campo]
        b = sum(1 for yc, ye in pr if ye == 1 and yc == 0)
        bp = sum(1 for yc, ye in pr if yc == 1 and ye == 0)
        p(f"| {nombre} | {ind if campo == 'ref' else '—'} | {len(pr)} | {b} | {bp} | {fmt_p(rj.p_mcnemar(b, bp))} |")
# sensibilidad, no prerregistrada: válido para el kernel aunque viole una regla declarada o el límite de tiempo del juez
FILAS_K = [{**f, "y_ref": 1} if f["categoria"] in ("regla_estricta", "tiempo") else f for f in FILAS]
eps_k = rj.episodios(FILAS_K)
sub_k = {k: e for k, e in eps_k.items() if e["peldano"] in dif3}
for ind in ("excluir", "0", "1"):
    pr = rj.pares(sub_k, "gpt-6-luna", "C", "E", "episodio", ind)["ref"]
    b = sum(1 for yc, ye in pr if ye == 1 and yc == 0)
    bp = sum(1 for yc, ye in pr if yc == 1 and ye == 0)
    p(f"| Y^R (kernel, sin reglas declaradas; no prerregistrado) | {ind} | {len(pr)} | {b} | {bp} | {fmt_p(rj.p_mcnemar(b, bp))} |")
p()
p("Pares discordantes (peldaño, episodio → C, E) con Y y con Y^R:")
p()
for nombre, ee in (("Y", sub), ("Y^R", sub_k)):
    A = {(e["peldano"], e["k"]): e for e in ee.values() if e["config"] == "C" and e["split"] == "test"}
    B = {(e["peldano"], e["k"]): e for e in ee.values() if e["config"] == "E" and e["split"] == "test"}
    campo = "y_juez" if nombre == "Y" else "y_ref"
    dis = [f"{c[0]}#{c[1]} → {A[c][campo]}, {B[c][campo]}" for c in sorted(set(A) & set(B)) if A[c][campo] != B[c][campo]]
    p(f"- {nombre}: {'; '.join(dis) or 'ninguno'}")
p()

# ---------------------------------------------------------------------------------------------------- punto 4
p("## 4. Intentos de E y E3 que citan un lema del cuaderno")
p()
por_archivo = {f["archivo"]: f for f in FILAS}
corridas = {"E": "evaluacion_E/20261013-221752-gpt-6-luna", "E3": "pareada_luna/20261013-221752-gpt-6-luna"}
p("| config | episodio | intento | lemas citados | juez | R | categoría | primer error del juez | primer error de R | ¿prueba o arnés? |")
p("|---|---|---|---|---|---|---|---|---|---|")
resumen4 = Counter()
for cfg, cor in corridas.items():
    ruta = RAIZ / "runs/unirl/rl_verbal" / cor / "llamadas.jsonl"
    for i, l in enumerate(ruta.open(encoding="utf-8"), 1):
        r = json.loads(l)
        if r.get("tipo") != "intento":
            continue
        txt = (r.get("proof") or "") + "\n" + (r.get("lemmas") or "")
        cit = sorted(n for n in (r.get("lemas_biblioteca") or []) if re.search(r"\b" + re.escape(n) + r"\b", txt))
        if not cit:
            continue
        f = por_archivo.get(f"{cor}/llamadas.jsonl:{i}")
        cat = f["categoria"] if f else "sin fila"
        ref = (f or {}).get("ref", {}).get("veredicto", "—")
        ej = (f or {}).get("primer_error_juez") or next((x for x in r.get("errores") or [] if x.startswith("***")), "")
        er = (f or {}).get("primer_error_ref") or (f or {}).get("detalle") or ""
        if cat in ("FN", "regla_estricta", "tiempo", "indeterminado", "concordante_contaminado") or r.get("biblioteca_fallo"):
            quien = "arnés"
        elif cat == "concordante" and "Duplicate fixed variable" in (ej + " " + er):
            quien = "arnés por diseño (su lema, dentro del contexto, choca con el `fixes` del peldaño)"
        elif cat == "sin_juicio":
            quien = "prueba (marcas sin cerrar)"
        elif cat == "concordante":
            quien = "prueba"
        else:
            quien = cat
        resumen4[quien] += 1
        p(f"| {cfg} | {r['episodio_id']} | {r['intento']} | {', '.join(cit)} | {r['etiqueta']} | {ref} | {cat} | "
          f"{limpia(ej)} | {limpia(er)} | {quien} |")
p()
p(f"Resumen: {dict(resumen4)}. «Prueba»: el juez y R rechazan por un error del texto del agente; «marcas sin cerrar»: "
  "el martillo no cerró algún `by martillo` y nadie vio una prueba completa; «arnés»: FN, regla estricta, tiempo, "
  "indeterminado, contaminado o falla de biblioteca.")
p()

# ---------------------------------------------------------------------------------------------------- punto 5
lm = DIR / "lemas_martillo.jsonl"
rep = DIR / "lemas_martillo_repeticion.jsonl"
if lm.exists():
    filas = [json.loads(x) for x in lm.open(encoding="utf-8")]
    repetidos = {}
    if rep.exists():
        for x in rep.open(encoding="utf-8"):
            r = json.loads(x)
            repetidos[r["nombre"]] = {**r, "repetido": True}
    filas = [repetidos.get(f["nombre"], f) for f in filas]
    dudosos = [f for f in filas if not f["demuestra_el_martillo"] and (f.get("suspension_s") or 0) > 5]
    met = lambda peld: (CORPUS.get(peld) or {}).get("metodo", "?")
    p("## 5. Los lemas del cuaderno 835d3070e3b0c3b1")
    p()
    p(f"Fuente: `resultados/rejuicio/ronda2/lemas_martillo.jsonl` ({len(filas)} lemas). Martillo de la ronda: try0 5 s "
      "y Sledgehammer 60 s sobre el enunciado a nivel de teoría, sin el resto del cuaderno; «sí» si la línea encontrada "
      "compila sin atajos en la plantilla de admisión del cuaderno. «Mostrado»: el lema apareció en `lemas_mostrados` "
      "de algún intento de E o E3.")
    p()
    dem = [f for f in filas if f["demuestra_el_martillo"]]
    most = [f for f in filas if f["mostrado_en_prueba"]]
    p(f"- Alcance: {dict(Counter(f['alcance'] for f in filas))}; método de origen: "
      f"{dict(Counter(met(f['origen']) for f in filas))}.")
    p(f"- Mostrados en algún peldaño de prueba: {len(most)}; nunca: {len(filas) - len(most)}.")
    p(f"- El martillo solo los demuestra: {len(dem)} de {len(filas)} (try0: {sum(1 for f in dem if f['fuente'] == 'try0')}, "
      f"Sledgehammer: {sum(1 for f in dem if f['fuente'] == 'sledgehammer')}); entre los mostrados: "
      f"{sum(1 for f in dem if f['mostrado_en_prueba'])} de {len(most)}.")
    p(f"- Repetidos (`lemas_martillo_repeticion.jsonl`, 15 oct): {len(repetidos)}: los «no» de la primera corrida con más "
      "de 5 s de suspensión (el Mac se durmió con la tapa cerrada a las 13:39 del 14 oct; un «no» bajo suspensión puede "
      "ser un tiempo agotado) y `cu_abs_distance_between` (dos conclusiones: la primera corrida solo cerraba una). Un «sí» "
      "con suspensión vale: la línea se comprobó sin atajos.")
    p(f"- «No» que siguen dudosos (suspensión > 5 s también al repetir): {len(dudosos)}"
      f"{': ' + ', '.join(f['nombre'] for f in dudosos) if dudosos else ''}; "
      f"línea encontrada que no compila en la pasada 2: {sum(1 for f in filas if f['linea'] and not f['demuestra_el_martillo'])}.")
    p()
    p("| # | lema | alcance | origen | peldaños de prueba donde se mostró | ¿el martillo solo? | línea |")
    p("|---|---|---|---|---|---|---|")
    for f in filas:
        p(f"| {f['k']} | {f['nombre']} | {f['alcance']} | {f['origen']} ({met(f['origen'])}) | "
          f"{len(f['mostrado_en_prueba'])}{': ' + ', '.join(f['mostrado_en_prueba']) if f['mostrado_en_prueba'] else ''} | "
          f"{'sí' if f['demuestra_el_martillo'] else 'no'} | {limpia(f['linea'], 70)} |")
    p()

(DIR / "auditoria.md").write_text("\n".join(L) + "\n", encoding="utf-8")
print(f"\n[escrito] {DIR / 'auditoria.md'}")
