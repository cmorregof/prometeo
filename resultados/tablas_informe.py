"""Genera resultados/tablas/*.tex para el informe de estado: macros con cada cifra del texto y las tablas.

Todo número del informe sale de resumen.json, estadistica.json, metricas.csv o del libro de gastos, nunca de una
transcripción a mano. Hay que regenerar (y recompilar) si cambia un registro.

    09_unified/.venv/bin/python resultados/consolidar.py
    09_unified/.venv/bin/python resultados/estadistica.py
    09_unified/.venv/bin/python resultados/tablas_informe.py
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent
T = OUT / "tablas"


def tex(s) -> str:
    s = str(s)
    for a, b in (("\\", r"\textbackslash{}"), ("&", r"\&"), ("%", r"\%"), ("$", r"\$"), ("#", r"\#"), ("_", r"\_"),
                 ("{", r"\{"), ("}", r"\}"), ("~", r"\textasciitilde{}"), ("^", r"\textasciicircum{}")):
        s = s.replace(a, b)
    return s


def num(x, d: int = 1) -> str:
    """Número con coma decimal (convención del informe)."""
    if isinstance(x, int):
        return f"{x:,}".replace(",", r"\,")
    return f"{x:.{d}f}".replace(".", "{,}")


def pct(x: float, d: int = 1) -> str:
    return num(100 * x, d) + r"\,\%"


def ic(v: dict, d: int = 3) -> str:
    """Intervalo con 3 decimales; 4 si el extremo es menor que 0,01 (no redondear 0,0005 a 0,001); 0 y 1 sin decimales."""
    def f(x: float) -> str:
        if x in (0, 0.0):
            return "0"
        if x in (1, 1.0):
            return "1"
        return num(x, 4 if x < 0.01 else d)
    lo, hi = v["ic95"]
    return f"[{f(lo)};\\ {f(hi)}]"


def usd(x: float, d: int = 2) -> str:
    return r"\$" + num(x, d)


def main() -> None:
    T.mkdir(exist_ok=True)
    R = json.loads((OUT / "resumen.json").read_text(encoding="utf-8"))
    E = json.loads((OUT / "estadistica.json").read_text(encoding="utf-8"))
    head = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    M: dict[str, str] = {"CommitDatos": R["commit"], "CommitTablas": head, "GeneradoDatos": R["generado"].replace("T", " ")}

    # ------------------------------------------------------------------ línea base A (resultado principal)
    A = E["A_sin_cuaderno"]
    M.update({"AtodosX": str(A["todos"]["exitos"]), "AtodosN": str(A["todos"]["n"]), "AtodosIC": ic(A["todos"]),
              "AtrainX": str(A["train"]["exitos"]), "AtrainN": str(A["train"]["n"]), "AtrainIC": ic(A["train"]),
              "AtestX": str(A["test"]["exitos"]), "AtestN": str(A["test"]["n"]), "AtestIC": ic(A["test"]),
              "AtestNoCerrados": str(A["T_estrella_test_sin_cuaderno"]),
              "Amedia": num(R["linea_base_A"]["segundos"]["media"]), "Amin": num(R["linea_base_A"]["segundos"]["min"]),
              "Amax": num(R["linea_base_A"]["segundos"]["max"])})
    nombres = {"biseccion": "bisección", "punto_fijo": "punto fijo", "ordenes": "órdenes", "newton": "Newton",
               "secante": "secante", "regula_falsi": "regula falsi"}
    split_de = {"biseccion": "train", "punto_fijo": "train", "ordenes": "train", "newton": "train", "secante": "test", "regula_falsi": "test"}
    filas = []
    for m in ("biseccion", "punto_fijo", "ordenes", "newton", "secante", "regula_falsi"):
        v = A["por_metodo"][m]
        filas.append(f"{nombres[m]} & {split_de[m]} & {v['exitos']} de {v['n']} & {ic(v)} \\\\")
    (T / "linea_base_metodo.tex").write_text(
        "\\begin{tabular}{@{}llrr@{}}\n\\toprule\nMétodo & Partición & Cerrados por el martillo & IC 95\\,\\% (Clopper--Pearson)\\\\\n\\midrule\n"
        + "\n".join(filas) + f"\n\\midrule\ntrain & & {A['train']['exitos']} de {A['train']['n']} & {ic(A['train'])}\\\\\n"
        f"test & & {A['test']['exitos']} de {A['test']['n']} & {ic(A['test'])}\\\\\n"
        f"total & & {A['todos']['exitos']} de {A['todos']['n']} & {ic(A['todos'])}\\\\\n\\bottomrule\n\\end{{tabular}}\n", encoding="utf-8")
    dif = A["por_dificultad"]
    fl = []
    for s in ("train", "test"):
        celdas = []
        for d in range(1, 6):
            v = dif.get(f"{s} d{d}")
            celdas.append(f"{v['exitos']}/{v['n']}" if v else "---")
        fl.append(f"{s} & " + " & ".join(celdas) + " \\\\")
    (T / "linea_base_dificultad.tex").write_text(
        "\\begin{tabular}{@{}lccccc@{}}\n\\toprule\n & \\multicolumn{5}{c}{Dificultad}\\\\\n\\cmidrule(l){2-6}\nPartición & 1 & 2 & 3 & 4 & 5\\\\\n\\midrule\n"
        + "\n".join(fl) + "\n\\bottomrule\n\\end{tabular}\n", encoding="utf-8")

    # ------------------------------------------------------------------ corpus
    C = R["corpus"]
    M.update({"CorpusN": str(C["peldanos"]), "CorpusTrain": str(C["splits"]["train"]), "CorpusTest": str(C["splits"]["test"]),
              "CorpusClasicas": str(C["versiones"]["clasica"]), "CorpusDebilitadas": str(C["versiones"]["debilitada"]),
              "CorpusExporta": str(C["exportacion_y_sorry"]), "CorpusRefPrivada": str(len(C["con_referencia_privada"])),
              "CorpusIsabelleOK": str(sum(C["validacion_isabelle"].values())), "CorpusIsabelleN": str(len(C["validacion_isabelle"]))})
    orden = [("train", "biseccion"), ("train", "punto_fijo"), ("train", "ordenes"), ("train", "newton"), ("test", "secante"), ("test", "regula_falsi")]
    por = {(r["split"], r["metodo"]): r for r in C["por_metodo"]}
    fl, tot = [], {s: [0] * 6 for s in ("train", "test")}
    for s, m in orden:
        r = por[(s, m)]
        fl.append(f"{nombres[m]} & {s} & " + " & ".join(str(r[f'd{i}']) for i in range(1, 6)) + f" & {r['total']}\\\\")
        for i in range(1, 6):
            tot[s][i - 1] += r[f"d{i}"]
        tot[s][5] += r["total"]
    fl.insert(4, "\\midrule")
    fl.append("\\midrule")
    for s in ("train", "test"):
        fl.append(f"\\textit{{total {s}}} & & " + " & ".join(str(x) for x in tot[s]) + "\\\\")
    (T / "corpus.tex").write_text(
        "\\begin{tabular}{@{}llcccccr@{}}\n\\toprule\n & & \\multicolumn{5}{c}{Dificultad estimada} & \\\\\n\\cmidrule(lr){3-7}\n"
        "Método & Partición & 1 & 2 & 3 & 4 & 5 & Peldaños\\\\\n\\midrule\n" + "\n".join(fl) + "\n\\bottomrule\n\\end{tabular}\n", encoding="utf-8")
    menos = ", ".join(f"\\texttt{{{tex(k)}}} ({v})" for k, v in sorted(C["numerica"]["menos_de_400"].items()))
    M["CorpusMenos"] = menos

    # ------------------------------------------------------------------ Tabla 1 (08)
    B = R["tabla1_biseccion"]
    M.update({"TunoVC": str(B["vcs"]), "TunoSola": str(B["automatizacion_sola"]), "TunoLema": str(B["solo_con_bisect_root_extract"]),
              "TunoAbiertas": str(B["abiertas_60s"]), "TunoSmt": str(B["abiertas_cerradas_por_la_smt_del_articulo"]),
              "TunoUnaLinea": str(B["con_prueba_de_una_linea_verificada"]), "TunoArticulo": str(B["articulo_auto"]),
              "TunoSegundos": num(B["segundos"])})

    # ------------------------------------------------------------------ jueces del 23–24 sep
    vg = E["V_G_grafo"]["conjunto"]
    pep = E["V_P_PEP"]["por_modelo"]
    M.update({"VGx": str(vg["exitos"]), "VGn": str(vg["n"]), "VGic": ic(vg),
              "PEPAstraX": str(pep["gpt-6-astra (high)"]["exitos"]), "PEPAstraN": str(pep["gpt-6-astra (high)"]["n"]),
              "PEPAstraIC": ic(pep["gpt-6-astra (high)"]), "PEPLunaX": str(pep["gpt-6-luna (high)"]["exitos"]),
              "PEPLunaN": str(pep["gpt-6-luna (high)"]["n"]), "PEPLunaIC": ic(pep["gpt-6-luna (high)"])})
    import csv
    validos: dict[str, list[int]] = {}
    notas_cont: dict[str, str] = {}
    for f in csv.DictReader(open(OUT / "metricas.csv", encoding="utf-8")):
        if f["experimento"].startswith("juez ") and f["incluida"] == "sí":
            v = validos.setdefault(f["corrida"], [0, 0])
            v[0] += int(f["exito"] or 0)
            v[1] += 1
            if "continuación" in f["configuracion"]:
                notas_cont[f["corrida"]] = "\\textsuperscript{b}"
        elif f["experimento"].startswith("juez ") and f["incluida"].startswith("no ("):
            notas_cont.setdefault(f["corrida"], "\\textsuperscript{a}")
    j = {a["corrida"]: a for a in R["jueces_09"] if not a["archivada"]}
    fl = []
    for a in sorted(j.values(), key=lambda a: (a["juez"], a["entorno"], a["modelo"], a["corrida"])):
        et = ", ".join(f"{tex(k)} {v}" for k, v in sorted(a["etiquetas"].items(), key=lambda kv: -kv[1]))
        x, n = validos.get(a["corrida"], [0, 0])
        fl.append(f"{tex(a['juez'])} & {tex(a['entorno'])} & {tex(a['modelo'])} & {x} de {n}{notas_cont.get(a['corrida'], '')} & {{\\footnotesize {et}}}\\\\")
    (T / "jueces.tex").write_text(
        "\\begin{tabular}{@{}lllr>{\\raggedright\\arraybackslash}p{5.0cm}@{}}\n\\toprule\nJuez & Entorno & Modelo & Episodios aceptados & Etiquetas de los intentos\\\\\n\\midrule\n"
        + "\n".join(fl) + "\n\\bottomrule\n\\end{tabular}\n", encoding="utf-8")

    # ------------------------------------------------------------------ gasto
    G = R["gasto"]
    por_modelo = G["por_modelo"]
    M.update({"GastoTotal": usd(G["total_usd"], 2), "GastoTope": usd(G["tope_usd"], 0), "GastoRestante": usd(G["restante_usd"], 2),
              "GastoLlamadas": str(G["llamadas"]),
              "GastoLuna": usd(por_modelo["gpt-6-luna"]["usd"], 2), "GastoLunaN": str(por_modelo["gpt-6-luna"]["llamadas"]),
              "GastoSol": usd(por_modelo["gpt-6-sol"]["usd"], 2), "GastoSolN": str(por_modelo["gpt-6-sol"]["llamadas"])})
    eps_usd = {}
    for c in R["rl_verbal"]:
        ef = next((k for k in c["fuentes"] if k.endswith("episodios.jsonl")), None)
        tot_ep = 0.0
        if ef:
            for l in (ROOT / ef).read_text(encoding="utf-8").splitlines():
                tot_ep += json.loads(l).get("usd", 0.0)
        eps_usd[c["corrida"]] = tot_ep
    fl, sin_resultado = [], 0.0
    etiquetas_fase = {"humo": "humo", "cuaderno": "cuaderno (F, train)", "evaluacion": "evaluación B0, B, C", "medicion_sol": "medición de Sol",
                      "pareada_luna": "pareada C3", "pareada_sol": "pareada C3"}
    for c in sorted(R["rl_verbal"], key=lambda c: c["inicio"]):
        k = f"{c['fase']}|{c['corrida']}|{c['modelo']}"
        g = G["por_corrida"][k]
        perdido = 0.0 if c["fase"] in ("humo", "medicion_sol") else round(g["usd"] - eps_usd[c["corrida"]], 6)
        sin_resultado += perdido
        fl.append(f"{etiquetas_fase[c['fase']]} & {tex(c['modelo'])} & {c['estado']} & {g['llamadas']} & {usd(g['usd'], 4)} & "
                  + (usd(perdido, 4) if perdido else "---") + "\\\\")
    fl.append(f"\\midrule\n\\textit{{total}} & & & {G['llamadas']} & {usd(G['total_usd'], 4)} & {usd(sin_resultado, 4)}\\\\")
    M["GastoSinResultado"] = usd(sin_resultado, 2)
    (T / "gasto.tex").write_text(
        "\\begin{tabular}{@{}lllrrr@{}}\n\\toprule\nCorrida (25 sep) & Modelo & Estado & Llamadas & Costo & En episodios no cerrados\\\\\n\\midrule\n"
        + "\n".join(fl) + "\n\\bottomrule\n\\end{tabular}\n", encoding="utf-8")

    # ------------------------------------------------------------------ corridas interrumpidas: solo conteos
    fl = []
    for c in sorted(R["rl_verbal"], key=lambda c: c["inicio"]):
        if c["estado"] != "interrumpida por error":
            continue
        for conf, v in sorted(c["por_config"].items()):
            fl.append(f"{etiquetas_fase[c['fase']]} & {tex(c['modelo'])} & {tex(conf)} & {v['planeados']} & {v['registrados']} & "
                      f"{v['planeados'] - v['registrados']} & {v['aceptados_entre_registrados']}\\\\")
    (T / "interrumpidas.tex").write_text(
        "\\begin{tabular}{@{}lllrrrr@{}}\n\\toprule\nCorrida & Modelo & Config. & Planeados & Registrados & Sin registro & Aceptados\\\\\n\\midrule\n"
        + "\n".join(fl) + "\n\\bottomrule\n\\end{tabular}\n", encoding="utf-8")

    # ------------------------------------------------------------------ McNemar: umbrales
    U = E["mcnemar_umbrales"]["tabla"]
    fila_n = " & ".join(str(u["pares_discordantes"]) for u in U[3:12])
    fila_b = " & ".join(str(u["b_minimo_a_favor_de_E"]) if u["b_minimo_a_favor_de_E"] is not None else "---" for u in U[3:12])
    (T / "mcnemar.tex").write_text(
        "\\begin{tabular}{@{}l" + "c" * 9 + "@{}}\n\\toprule\nPares discordantes $b+b'$ & " + fila_n + "\\\\\n\\midrule\n"
        "Mínimo $b$ a favor de E para $p<0{,}05$ & " + fila_b + "\\\\\n\\bottomrule\n\\end{tabular}\n", encoding="utf-8")

    # ------------------------------------------------------------------ procedencia
    def sha(ruta: str) -> str:
        import hashlib
        return hashlib.sha256((ROOT / ruta).read_bytes()).hexdigest()[:16]
    fuentes = [
        ("Estado del proyecto (Tabla~\\ref{tab:estado})", "resultados/resumen.json", "varios", R["generado"][:10]),
        ("Línea base A (Tablas~\\ref{tab:lineabase} y~\\ref{tab:lineabase-dif})", "09_unified/resultados/martillo_linea_base.json", "unirl de la Etapa 3 (sin huella en el archivo); versionado en 9b5e3fe", "2026-09-24 16:54"),
        ("Intervalos y umbrales (Tablas~\\ref{tab:lineabase} y~\\ref{tab:mcnemar})", "resultados/estadistica.json", head, E["generado"][:10]),
        ("Reproducción de la Tabla 1 del artículo", "08_isabelle/runs/repro_bisection.json", "08 sin versionar; versionado sin cambios en 9b5e3fe", "2026-09-23 15:00"),
        ("Línea smt del artículo", "09_unified/runs/_baseline/given_smt_08.json", "ídem", "2026-09-23 19:37"),
        ("Corpus (Tabla~\\ref{tab:corpus})", "09_unified/corpus/raices/revision_enunciados.md", "9b5e3fe", "2026-09-24"),
        ("Validación del corpus en Isabelle", "09_unified/corpus/raices/validacion_isabelle.json", "9b5e3fe", "2026-09-24"),
        ("Exportación y sorry del corpus", "09_unified/corpus/raices/validacion_exportacion.json", "9b5e3fe", "2026-09-24"),
        ("Jueces del 23--24 sep (Tabla~\\ref{tab:jueces})", "resultados/metricas.csv", "unirl por corrida (columna código)", "2026-09-23/24"),
        ("Gasto (Tabla~\\ref{tab:gasto})", "09_unified/logs/gasto.json", "unirl 5ef59e25793670fb", "2026-09-25 07:24--09:27"),
        ("Corridas interrumpidas (Tabla~\\ref{tab:interrumpidas})", "09_unified/runs/rl_verbal/evaluacion/20260925-073228-gpt-6-luna/episodios.jsonl", "unirl 5ef59e25793670fb", "2026-09-25"),
        ("", "09_unified/runs/rl_verbal/pareada_luna/20260925-073939-gpt-6-luna/episodios.jsonl", "unirl 5ef59e25793670fb", "2026-09-25"),
        ("", "09_unified/runs/rl_verbal/pareada_sol/20260925-073936-gpt-6-sol/episodios.jsonl", "unirl 5ef59e25793670fb", "2026-09-25"),
        ("", "09_unified/runs/rl_verbal/cuaderno/20260925-073216-gpt-6-luna/episodios.jsonl", "unirl 5ef59e25793670fb", "2026-09-25"),
        ("PEP: episodios repetidos", "09_unified/runs/pep_gradnorm_n4/20260924-060127-gpt-6-astra-high/attempts.jsonl", "unirl de esa corrida (meta.json)", "2026-09-24"),
        ("Tácticas de Lean", "09_unified/runs/gd_const_textbook/20260924-082858-gpt-6-luna-high/attempts.jsonl", "ídem", "2026-09-24"),
        ("Auditoría de cifras", "resultados/auditoria_cifras.md", head, "2026-09-25"),
        ("Líneas base puras de 02, 04 y 05", "resultados/corridas_locales/lineas_base_puras.json", "e419660", "2026-09-25"),
        ("Formulación con el umbral de H1", "09_unified/docs/nota/formulacion_rl_verbal.tex", "b9d850f", "2026-09-25 14:30"),
    ]
    fl = [f"{q} & \\path{{{ruta}}} & \\texttt{{{sha(ruta)}}} & {tex(c)} & {tex(f)}\\\\" for q, ruta, c, f in fuentes]
    (T / "procedencia.tex").write_text(
        "\\begin{longtable}{@{}>{\\raggedright\\arraybackslash}p{3.0cm}>{\\raggedright\\arraybackslash}p{5.45cm}p{2.45cm}>{\\raggedright\\arraybackslash}p{2.9cm}>{\\raggedright\\arraybackslash}p{1.7cm}@{}}\n\\toprule\nQué & Archivo & SHA-256 (16) & Código & Fecha\\\\\n\\midrule\n\\endhead\n"
        + "\n".join(fl) + "\n\\bottomrule\n\\end{longtable}\n", encoding="utf-8")

    # ------------------------------------------------------------------ cifras del texto (también desde archivos)
    import csv, glob, re, statistics
    import xml.etree.ElementTree as ET
    mejoras = []
    for f in csv.DictReader(open(OUT / "metricas.csv", encoding="utf-8")):
        if f["experimento"] == "juez pep" and f["incluida"] == "sí" and f["episodio"] == "1" and f["exito"] == "1":
            tau = float(re.search(r"tau=([0-9.e-]+)", f["notas"]).group(1))
            ref = float(re.search(r"tau_ref=([0-9.e-]+)", f["notas"]).group(1))
            mejoras.append(1 - tau / ref)
    M.update({"PEPMejoraMin": num(100 * min(mejoras), 2) + r"\,\%", "PEPMejoraMax": num(100 * max(mejoras), 2) + r"\,\%"})
    lean = {"nlinarith": 0, "ring": 0, "field_simp": 0, "omega": 0, "positivity": 0}
    por_modelo_lean = {"gpt-6-luna": 0, "gpt-6-astra": 0}
    for fa in glob.glob(str(ROOT / "09_unified/runs/*/*/attempts.jsonl")):
        if "/runs/_" in fa:
            continue
        for l in open(fa, encoding="utf-8"):
            a = json.loads(l)
            if a.get("judge") not in ("isabelle", "isabelle_teorema"):
                continue
            vistos = set(re.findall(r'Undefined method: \\?"?([A-Za-z_]+)', json.dumps(a.get("raw"), ensure_ascii=False)))
            for mth in vistos & set(lean):
                lean[mth] += 1
                por_modelo_lean[a.get("model")] = por_modelo_lean.get(a.get("model"), 0) + 1
    M.update({f"Lean{k.replace('_', '')}": str(v) for k, v in lean.items()})
    M.update({"LeanTotal": str(sum(lean.values())), "LeanLuna": str(por_modelo_lean.get("gpt-6-luna", 0)),
              "LeanAstra": str(por_modelo_lean.get("gpt-6-astra", 0))})
    perd = sum(c["perdidos"] for c in R["rl_verbal"] if c["estado"] == "interrumpida por error")
    plan = sum(v["planeados"] for c in R["rl_verbal"] if c["estado"] == "interrumpida por error" and c["fase"] != "cuaderno"
               for v in c["por_config"].values())
    cuad = next(c for c in R["rl_verbal"] if c["fase"] == "cuaderno")
    M.update({"PerdidosEval": str(perd), "PlaneadosEval": str(plan),
              "CuadernoHechos": str(sum(v["registrados"] for v in cuad["por_config"].values())),
              "CuadernoPlan": str(sum(v["planeados"] for v in cuad["por_config"].values()))})
    medias = {m: v["usd"] / v["llamadas"] for m, v in por_modelo.items()}
    maximos = {"gpt-6-luna": 198 + 320 + 192 + 64 + 64, "gpt-6-sol": 64 + 64}  # RELANZAMIENTO.md: llamadas máximas por paso
    cota = sum(medias[m] * n for m, n in maximos.items())
    M.update({"CotaRelanzamiento": usd(cota, 2), "MediaLuna": usd(medias["gpt-6-luna"], 5), "MediaSol": usd(medias["gpt-6-sol"], 4)})
    pruebas = {}
    for x in sorted(glob.glob(str(OUT / "corridas_locales/pytest/*.xml"))):
        su = ET.parse(x).getroot()
        su = su if su.tag == "testsuite" else su.find("testsuite")
        pruebas[Path(x).stem] = (int(su.get("tests")), int(su.get("failures")) + int(su.get("errors")))
    M.update({"PruebasRapidasNueve": str(pruebas["09_unified_rapidas"][0]), "PruebasIsabelleNueve": str(pruebas["09_unified_isabelle"][0]),
              "PruebasIsabelleNueveFallas": str(pruebas["09_unified_isabelle"][1]), "PruebasSeis": str(pruebas["06_stepsizes"][0]),
              "PruebasUnoSieteTotal": str(sum(pruebas[k][0] for k in pruebas if k[:2] in ("01", "02", "03", "04", "05", "07")))})

    # veredictos de la auditoría de cifras, contados desde el archivo (primer símbolo de la última columna)
    cuenta = {"✓": 0, "≈": 0, "✗": 0, "pendiente": 0}
    for linea in (OUT / "auditoria_cifras.md").read_text(encoding="utf-8").splitlines():
        if linea.startswith("| ") and linea.split("|")[1].strip().isdigit():
            ultima = linea.rstrip().rstrip("|").split("|")[-1].strip()
            clave = next(k for k in cuenta if ultima.startswith(k))
            cuenta[clave] += 1
    M.update({"AudTotal": str(sum(cuenta.values())), "AudSi": str(cuenta["✓"]), "AudMatiz": str(cuenta["≈"]),
              "AudNo": str(cuenta["✗"]), "AudPend": str(cuenta["pendiente"])})

    (T / "macros.tex").write_text("% Generado por resultados/tablas_informe.py. No editar a mano.\n"
                                  + "\n".join(f"\\newcommand{{\\{k}}}{{{v}}}" for k, v in M.items()) + "\n", encoding="utf-8")
    print(f"{len(M)} macros y {len(list(T.glob('*.tex')))} archivos en {T.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
