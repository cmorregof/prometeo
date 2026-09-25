"""Etapa 1 del informe: consolida todos los registros de rl_metodos en resultados/metricas.csv y resultados/resumen.json.

Solo lee. Cada fila lleva su fuente (ruta relativa al repo), la huella SHA-256 de esa fuente (16 dígitos) y la
identidad del código que la produjo: el commit (01–07, inferido por la fecha de la corrida cuando la corrida no lo
anota) o la huella de `unirl` que registra su meta.json (09). Estados: terminado, en curso, interrumpida por error y
planeado; `incluida` dice si la fila entra en los análisis (las carpetas `_*` de 09 están archivadas con su LEEME.md).

    09_unified/.venv/bin/python resultados/consolidar.py
"""

from __future__ import annotations

import csv
import glob
import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "resultados"
U = ROOT / "09_unified"

CAMPOS = ["subproyecto", "experimento", "estado", "incluida", "corrida", "fecha", "configuracion", "modelo", "tarea",
          "episodio", "exito", "intentos_usados", "intento_exito", "tiempo_pared_s", "llamadas_api", "costo_usd",
          "etiqueta", "notas", "fuente", "fuente_sha256", "codigo"]

_sha: dict[str, str] = {}


def sha(p: Path) -> str:
    k = str(p)
    if k not in _sha:
        _sha[k] = hashlib.sha256(p.read_bytes()).hexdigest()[:16]
    return _sha[k]


def rel(p: Path) -> str:
    return str(Path(p).resolve().relative_to(ROOT))


def jl(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []


def commit_en(fecha: str, ruta: str) -> str:
    """Último commit que tocó `ruta` antes de `fecha` (para corridas que no anotan su commit)."""
    r = subprocess.run(["git", "-C", str(ROOT), "log", "-1", "--format=%h", f"--before={fecha}", "--", ruta],
                       capture_output=True, text=True)
    return (r.stdout.strip() + " (inferido por fecha)") if r.stdout.strip() else "sin commit anterior"


def fila(**kw) -> dict:
    d = {c: "" for c in CAMPOS}
    d.update({k: ("" if v is None else v) for k, v in kw.items()})
    return d


def fecha_de_carpeta(nombre: str) -> str:
    try:
        return datetime.strptime(nombre[:15], "%Y%m%d-%H%M%S").isoformat(timespec="seconds")
    except ValueError:
        return ""


# ----------------------------------------------------------------------------- 01–05 y 07: Q-agent tabular

PAQUETES = {"01_biseccion": "bisectrl", "02_punto_fijo": "fixpointrl", "03_taylor": "taylorrl", "04_newton": "newtonrl",
            "05_secante": "secantrl", "07_interpolacion": "interprl"}


def qagent(filas: list[dict], resumen: dict) -> None:
    corridas = []
    for proyecto in PAQUETES:
        rutas = sorted(glob.glob(str(ROOT / proyecto / "runs" / "*" / "historia.json")))
        rutas += sorted(glob.glob(str(OUT / "corridas_locales" / (proyecto + "*") / "*" / "historia.json")))
        for r in map(Path, rutas):
            h = json.loads(r.read_text(encoding="utf-8"))
            cfg, nombre = h.get("config", {}), r.parent.name
            fecha = fecha_de_carpeta(nombre)
            local = "corridas_locales" in str(r)
            codigo = commit_en(fecha or "now", f"{proyecto}/{PAQUETES[proyecto]}") if not local else _head() + " (HEAD)"
            e1 = next((v for k, v in cfg.items() if k.startswith("episodes_") and k != "episodes_proof"), None)
            p1, p2 = h.get("phase1", {}), h.get("phase2", {})
            n1 = {k: v for k, v in p1.items() if isinstance(v, (int, float))}
            hitos = [{"fase": m.get("phase"), "generacion": m.get("episode"), "texto": m.get("text")} for m in h.get("milestones", [])]
            conf = f"fase 1 {e1} + fase 2 {cfg.get('episodes_proof')} generaciones, semilla {cfg.get('seed')}, tol {cfg.get('tol')}"
            comun = dict(subproyecto=proyecto[:2], experimento="Q-agent tabular", estado="terminado", incluida="sí",
                         corrida=nombre, fecha=fecha, configuracion=conf, modelo="Q-learning tabular",
                         fuente=rel(r), fuente_sha256=sha(r), codigo=codigo, llamadas_api=0, costo_usd=0)
            filas.append(fila(**comun, tarea="fase 1 (método)", tiempo_pared_s=round(h.get("phase1_time", 0), 2),
                              notas="; ".join(f"{k}={v}" for k, v in n1.items())))
            filas.append(fila(**comun, tarea="fase 2 (demostración, grafo de lemas)", tiempo_pared_s=round(h.get("phase2_time", 0), 2),
                              notas=f"completas={p2.get('qed_total')}; mínimas={p2.get('minimal_total')}"))
            corridas.append({"proyecto": proyecto, "corrida": nombre, "local": local, "config": cfg, "fase1": n1,
                             "completas": p2.get("qed_total"), "minimas": p2.get("minimal_total"),
                             "tiempo_s": round(h.get("elapsed", 0), 2), "hitos": hitos, "fuente": rel(r), "sha": sha(r),
                             "codigo": codigo})
    resumen["qagent"] = corridas


_HEAD = None


def _head() -> str:
    global _HEAD
    if _HEAD is None:
        _HEAD = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    return _HEAD


# ----------------------------------------------------------------------------- 06: evolve, referencias, certificados


def stepsizes(filas: list[dict], resumen: dict) -> None:
    ev = []
    for r in sorted(map(Path, glob.glob(str(ROOT / "06_stepsizes" / "runs" / "2026*" / "evolucion.json")))):
        d = json.loads(r.read_text(encoding="utf-8"))
        gens = next((v for v in d.values() if isinstance(v, list)), [])
        nombre, fecha = r.parent.name, fecha_de_carpeta(r.parent.name)
        codigo = commit_en(fecha, "06_stepsizes/steprl")
        llm = gens[2:]  # las dos primeras entradas son las líneas base (silver y paso constante)
        for g in gens:
            base = g in gens[:2]
            filas.append(fila(subproyecto="06", experimento="evolve (LLM propone, PEP certifica)", estado="terminado", incluida="sí",
                              corrida=nombre, fecha=fecha, configuracion=f"objetivo {d.get('objective')}; target_p {d.get('target_p', '—')}",
                              modelo="línea base" if base else d.get("model"), tarea=g.get("name") or f"generación {g.get('generation')}",
                              episodio=g.get("generation"), exito="" if base else int(not g.get("error")),
                              tiempo_pared_s=round(g.get("seconds") or 0, 1), llamadas_api="" if base else 1,
                              costo_usd="" if base else "no medido", etiqueta="error" if g.get("error") else "válida",
                              notas=(g.get("error") or "")[:120] or "; ".join(
                                  f"{k}={round(g[k], 4)}" for k in ("fixed_ratio", "anytime_p", "doubling_p", "C_target") if isinstance(g.get(k), (int, float))),
                              fuente=rel(r), fuente_sha256=sha(r), codigo=codigo))
        ev.append({"corrida": nombre, "modelo": d.get("model"), "objetivo": d.get("objective"), "generaciones_llm": len(llm),
                   "validas": sum(1 for g in llm if not g.get("error")),
                   "errores": dict(Counter((g.get("error") or "")[:40] for g in llm if g.get("error"))),
                   "mejor_C_target": min((g["C_target"] for g in llm if isinstance(g.get("C_target"), (int, float)) and not g.get("error")), default=None),
                   "fuente": rel(r), "sha": sha(r), "codigo": codigo})
    certs = []
    for r in sorted(map(Path, glob.glob(str(ROOT / "06_stepsizes" / "certificados" / "*.json")) + glob.glob(str(ROOT / "06_stepsizes" / "runs" / "cert-*.json")))):
        d = json.loads(r.read_text(encoding="utf-8"))
        fecha = datetime.fromtimestamp(r.stat().st_mtime).isoformat(timespec="seconds")
        tarea = f"{d.get('objective')}, μ = {d.get('mu')}, n = {len(d.get('h', []))}"
        filas.append(fila(subproyecto="06", experimento="certificado racional exacto", estado="terminado", incluida="sí",
                          corrida=r.name, fecha=fecha, configuracion=f"δ = {d.get('delta')}, {d.get('digits')} dígitos",
                          modelo="—", tarea=tarea, exito=int(bool(d.get("ok"))), llamadas_api=0, costo_usd=0,
                          etiqueta=d.get("message"), notas=f"tau_cert={d.get('tau_float')}; tau_sdp={d.get('tau_sdp')}",
                          fuente=rel(r), fuente_sha256=sha(r), codigo=commit_en(fecha, "06_stepsizes/steprl")))
        certs.append({"archivo": rel(r), "tarea": tarea, "tau_cert": d.get("tau_float"), "tau_sdp": d.get("tau_sdp"),
                      "ok": d.get("ok"), "sha": sha(r)})
    refs = json.loads((ROOT / "06_stepsizes" / "steprl" / "refs.json").read_text(encoding="utf-8"))
    resumen["stepsizes"] = {"evolve": ev, "certificados": certs,
                            "referencias": {"instancias": len(refs), "fuentes": dict(Counter(v["source"] for v in refs.values())),
                                            "fuente": "06_stepsizes/steprl/refs.json", "sha": sha(ROOT / "06_stepsizes/steprl/refs.json")}}


# ----------------------------------------------------------------------------- 08: reproducción de la Tabla 1


def isabelle08(filas: list[dict], resumen: dict) -> None:
    r = ROOT / "08_isabelle" / "runs" / "repro_bisection.json"
    d = json.loads(r.read_text(encoding="utf-8"))["result"]
    g = U / "runs" / "_baseline" / "given_smt_08.json"
    dada = {v["index"]: v["given"] for v in json.loads(g.read_text(encoding="utf-8"))["vcs"]}
    fecha = datetime.fromtimestamp(r.stat().st_mtime).isoformat(timespec="seconds")
    cuenta = Counter()
    for v in d["vcs"]:
        linea = v.get("one_liner") or ""
        con_lema = "bisect_root_extract" in linea
        sola = bool(linea) and not con_lema
        cuenta["sola"] += sola
        cuenta["con_lema"] += con_lema
        cuenta["abierta"] += not linea
        cuenta["smt_del_articulo"] += bool(dada.get(v["index"], {}).get("closed"))
        filas.append(fila(subproyecto="08", experimento="reproducción de la Tabla 1 (bisección)", estado="terminado", incluida="sí",
                          corrida="repro_bisection", fecha=fecha, configuracion="vcg; try0 5 s y Sledgehammer 60 s por VC; 7 demostradores",
                          modelo="automatización (sin LLM)", tarea=f"VC {v['index']}", exito=int(sola),
                          tiempo_pared_s=round(((v.get("sh_ms") or 0) + (v.get("try0_ms") or 0)) / 1000, 1),
                          llamadas_api=0, costo_usd=0, etiqueta=v.get("method"),
                          notas=("línea con bisect_root_extract: " if con_lema else "") + linea[:110] +
                                (f" | smt del artículo: cierra en {dada[v['index']]['ms']} ms" if v["index"] in dada else ""),
                          fuente=rel(r), fuente_sha256=sha(r), codigo="08_isabelle sin versionar el 23 sep; código versionado sin cambios en 9b5e3fe"))
    resumen["tabla1_biseccion"] = {"vcs": d["n_vcs"], "automatizacion_sola": cuenta["sola"],
                                   "solo_con_bisect_root_extract": cuenta["con_lema"], "abiertas_60s": cuenta["abierta"],
                                   "abiertas_cerradas_por_la_smt_del_articulo": cuenta["smt_del_articulo"],
                                   "con_prueba_de_una_linea_verificada": cuenta["sola"] + cuenta["smt_del_articulo"],
                                   "articulo_auto": 13, "segundos": round(json.loads(r.read_text())["seconds"], 1),
                                   "fuentes": {rel(r): sha(r), rel(g): sha(g),
                                               rel(ROOT / "08_isabelle/runs/repro_vc4_240s.json"): sha(ROOT / "08_isabelle/runs/repro_vc4_240s.json"),
                                               rel(U / "runs/_baseline/sh_goals.json"): sha(U / "runs/_baseline/sh_goals.json"),
                                               rel(U / "runs/_baseline/upper_bound.json"): sha(U / "runs/_baseline/upper_bound.json")}}


# ----------------------------------------------------------------------------- 09: jueces del 23–24 sep


def jueces09(filas: list[dict], resumen: dict) -> None:
    agregados = []
    for m in sorted(map(Path, glob.glob(str(U / "runs" / "**" / "meta.json"), recursive=True))):
        if "/rl_verbal/" in str(m) or not (m.parent / "attempts.jsonl").exists():
            continue
        meta = json.loads(m.read_text(encoding="utf-8"))
        a_f = m.parent / "attempts.jsonl"
        intentos = jl(a_f)
        archivada = any(part.startswith("_") for part in m.relative_to(U / "runs").parts[:-1])
        entorno = meta.get("env") or (meta.get("config") or {}).get("name")
        juez = meta.get("judge")
        codigo = (meta.get("code") or {}).get("unirl_sha256", "")
        corrida = str(m.parent.relative_to(U / "runs"))
        eps = defaultdict(list)
        for a in intentos:
            eps[a.get("episode")].append(a)
        for e, v in sorted(eps.items(), key=lambda kv: (kv[0] is None, kv[0])):
            ok = [x for x in v if x.get("accepted")]
            etiquetas = Counter(x.get("outcome_label") for x in v)
            notas = "; ".join(f"{k} {c}" for k, c in etiquetas.most_common())
            if juez == "pep" and ok:
                raw = ok[0].get("raw") or {}
                notas += f"; tau={raw.get('tau')}; tau_ref={raw.get('tau_ref')}; h={[round(x, 6) for x in raw.get('h', [])]}"
            solo_proveedor = all(x.get("outcome_label") == "PROVIDER_ERROR" for x in v)
            incl = "no" if archivada else ("no (solo errores del proveedor; el episodio se repitió)" if solo_proveedor else "sí")
            filas.append(fila(subproyecto="09", experimento=f"juez {juez}", estado="terminado", incluida=incl,
                              corrida=corrida, fecha=meta.get("started"), configuracion=f"{entorno}; B = {meta.get('budget')}; memoria {(meta.get('config') or {}).get('memory', 'no')}",
                              modelo=f"{meta.get('model')} ({meta.get('effort')})", tarea=entorno, episodio=e,
                              exito=int(bool(ok)), intentos_usados=len(v), intento_exito=min(x["step"] for x in ok) if ok else "",
                              tiempo_pared_s=round(sum((x.get("llm_s") or 0) + (x.get("cost_s") or 0) for x in v), 1),
                              llamadas_api=len(v), costo_usd="no medido", etiqueta=v[-1].get("outcome_label"), notas=notas,
                              fuente=rel(a_f), fuente_sha256=sha(a_f), codigo=f"unirl {codigo}"))
        agregados.append({"corrida": corrida, "archivada": archivada, "juez": juez, "entorno": entorno, "modelo": meta.get("model"),
                          "episodios": len(eps), "aceptados": sum(1 for v in eps.values() if any(x.get("accepted") for x in v)),
                          "intentos": len(intentos), "etiquetas": dict(Counter(x.get("outcome_label") for x in intentos)),
                          "fuente": rel(a_f), "sha": sha(a_f), "codigo": codigo})
    resumen["jueces_09"] = agregados


# ----------------------------------------------------------------------------- 09: corpus, línea base A, RL verbal, gasto


def corpus09(resumen: dict) -> list[dict]:
    rows = [json.loads(Path(f).read_text(encoding="utf-8")) for f in sorted(glob.glob(str(U / "corpus/raices/*.json"))) if "validacion" not in f]
    tabla = defaultdict(Counter)
    for r in rows:
        tabla[(r["split"], r["metodo"])][r["dificultad"]] += 1
    resumen["corpus"] = {
        "peldanos": len(rows), "estados": dict(Counter(r["estado"] for r in rows)), "splits": dict(Counter(r["split"] for r in rows)),
        "versiones": dict(Counter(r["version"] for r in rows)),
        "por_metodo": [{"split": s, "metodo": m, **{f"d{i}": c.get(i, 0) for i in range(1, 6)}, "total": sum(c.values())}
                       for (s, m), c in sorted(tabla.items())],
        "numerica": {"todos_cumplen": all(r["comprobacion_numerica"]["casos"] == r["comprobacion_numerica"]["cumplen"] for r in rows),
                     "menos_de_400": {r["id"]: r["comprobacion_numerica"]["casos"] for r in rows if r["comprobacion_numerica"]["casos"] < 400}},
        "aprobados_por": dict(Counter(r["aprobacion"]["por"] + " " + r["aprobacion"]["fecha"] for r in rows)),
        "con_referencia_privada": [r["id"] for r in rows if r.get("referencia_privada")],
        "validacion_isabelle": {k: v["ok"] for k, v in json.loads((U / "corpus/raices/validacion_isabelle.json").read_text()).items()},
        "exportacion_y_sorry": sum(1 for v in json.loads((U / "corpus/raices/validacion_exportacion.json").read_text()).values()
                                   if v["exporta"] and v["skip_proof_detectado"]),
        "fuentes": {rel(U / "corpus/raices/validacion_isabelle.json"): sha(U / "corpus/raices/validacion_isabelle.json"),
                    rel(U / "corpus/raices/validacion_exportacion.json"): sha(U / "corpus/raices/validacion_exportacion.json"),
                    rel(U / "corpus/raices/revision_enunciados.md"): sha(U / "corpus/raices/revision_enunciados.md")}}
    return rows


def linea_base(filas: list[dict], resumen: dict, corpus: list[dict]) -> None:
    r = U / "resultados" / "martillo_linea_base.json"
    d = json.loads(r.read_text(encoding="utf-8"))
    por_id = {c["id"]: c for c in corpus}
    for f in d["filas"]:
        filas.append(fila(subproyecto="09", experimento="A: martillo solo (línea base)", estado="terminado", incluida="sí",
                          corrida="martillo_linea_base (sin cuaderno)", fecha="2026-09-24T16:54", configuracion="try0 5 s + Sledgehammer 60 s, en serie",
                          modelo="automatización (sin LLM)", tarea=f["id"], exito=int(f["resuelto_por_martillo"]), intentos_usados=f.get("intentos"),
                          tiempo_pared_s=f.get("s"), llamadas_api=0, costo_usd=0, etiqueta=f.get("resultado_sh"),
                          notas=f"{f['metodo']}; {f['split']}; dif. {f['dificultad']}; {f['version']}; carga {f.get('carga_1')}" + (f"; {f['linea']}" if f.get("linea") else ""),
                          fuente=rel(r), fuente_sha256=sha(r), codigo="unirl (Etapa 3, 24 sep; sin huella en el archivo)"))
    grupos = defaultdict(lambda: [0, 0])
    for f in d["filas"]:
        for clave in (("todos",), ("split", f["split"]), ("metodo", f["metodo"]), ("dificultad", f["split"], f["dificultad"])):
            grupos[clave][0] += int(f["resuelto_por_martillo"])
            grupos[clave][1] += 1
    resumen["linea_base_A"] = {"cuaderno": d.get("cuaderno"), "fecha": "2026-09-24T16:54",
                               "grupos": [{"grupo": list(k), "resueltos": v[0], "n": v[1]} for k, v in sorted(grupos.items(), key=str)],
                               "segundos": {"media": round(sum(f["s"] for f in d["filas"]) / len(d["filas"]), 1),
                                            "min": min(f["s"] for f in d["filas"]), "max": max(f["s"] for f in d["filas"])},
                               "fuente": rel(r), "sha": sha(r)}


RL = U / "runs" / "rl_verbal"


def rl_verbal(filas: list[dict], resumen: dict, corpus: list[dict]) -> None:
    test = sorted(c["id"] for c in corpus if c["split"] == "test")
    train = [c["id"] for c in corpus if c["split"] == "train"]
    info = {c["id"]: c for c in corpus}
    corridas = []
    for m in sorted(map(Path, glob.glob(str(RL / "*" / "*" / "meta.json")))):
        meta = json.loads(m.read_text(encoding="utf-8"))
        d, fase = m.parent, meta["fase"]
        estado = "interrumpida por error" if (d / "INTERRUMPIDA.md").exists() else (
            "terminado" if (d / "resumen.md").exists() or (d / "FIN.json").exists() or fase in ("humo", "medicion_sol") else "en curso")
        eps = jl(d / "episodios.jsonl")
        lls_f = d / "llamadas.jsonl"
        codigo = f"unirl {meta['codigo']['unirl_sha256']}"
        fuente_e = d / "episodios.jsonl"
        for e in eps:
            filas.append(fila(subproyecto="09", experimento=f"RL verbal: {fase}", estado=estado, incluida="no" if estado != "terminado" else "sí",
                              corrida=d.name, fecha=meta["inicio"], configuracion=e.get("config"), modelo=meta["modelo"], tarea=e["peldano"],
                              episodio=e.get("episodio_k", 1), exito=int(bool(e["aceptado"])), intentos_usados=e.get("intentos"),
                              intento_exito=e.get("intento_exito"), llamadas_api=e.get("llamadas"), costo_usd=e.get("usd"),
                              etiqueta="aceptado" if e["aceptado"] else "no aceptado",
                              notas=f"{e.get('metodo')}; {e.get('split')}; dif. {e.get('dificultad')}; consultas {e.get('consultas')}; r_V máx {e.get('r_V_max')}",
                              fuente=rel(fuente_e), fuente_sha256=sha(fuente_e), codigo=codigo))
        if not eps:  # la medición de Sol: llamadas sin episodio
            for i, x in enumerate(jl(lls_f), 1):
                u = x.get("uso") or {}
                filas.append(fila(subproyecto="09", experimento=f"RL verbal: {fase}", estado=estado, incluida="sí", corrida=d.name,
                                  fecha=meta["inicio"], configuracion="C3, sin juez ni martillo: solo el costo por llamada",
                                  modelo=meta["modelo"], tarea=meta.get("peldano"), episodio=i, tiempo_pared_s=x.get("llm_s"),
                                  llamadas_api=1, costo_usd=u.get("usd"),
                                  notas=f"entrada {u.get('entrada')}, salida {u.get('salida')} (razonamiento {u.get('razonamiento')})",
                                  fuente=rel(lls_f), fuente_sha256=sha(lls_f), codigo=codigo))
        plan = []
        if fase in ("evaluacion", "pareada_luna", "pareada_sol"):
            plan = [f"{p}#{c}#{k}" for p in test for c in meta["configs"] for k in range(1, meta["episodios_por_peldano"] + 1)]
        elif fase == "cuaderno":
            plan = [f"{p}#1" for p in train]
        hechos = {e["episodio_id"] for e in eps}
        perdidos = [j for j in plan if j not in hechos] if estado == "interrumpida por error" and fase != "cuaderno" else []
        for j in perdidos:
            p, c, k = j.split("#")
            filas.append(fila(subproyecto="09", experimento=f"RL verbal: {fase}", estado=estado, incluida="no", corrida=d.name,
                              fecha=meta["inicio"], configuracion=c, modelo=meta["modelo"], tarea=p, episodio=int(k),
                              etiqueta="perdido: el episodio murió por el error del código y no quedó registrado",
                              notas=f"{info[p]['metodo']}; test; dif. {info[p]['dificultad']}",
                              fuente=rel(fuente_e) if fuente_e.exists() else rel(m), fuente_sha256=sha(fuente_e) if fuente_e.exists() else sha(m), codigo=codigo))
        por_conf = defaultdict(lambda: {"planeados": 0, "registrados": 0, "aceptados_entre_registrados": 0})
        for j in plan:
            por_conf[j.split("#")[1] if fase != "cuaderno" else meta.get("config", "F")]["planeados"] += 1
        for e in eps:
            c = e.get("config")
            por_conf[c]["registrados"] += 1
            por_conf[c]["aceptados_entre_registrados"] += int(bool(e["aceptado"]))
        corridas.append({"corrida": d.name, "fase": fase, "modelo": meta["modelo"], "estado": estado, "inicio": meta["inicio"],
                         "codigo": meta["codigo"], "por_config": dict(por_conf), "perdidos": len(perdidos),
                         "llamadas_registradas": len(jl(lls_f)) if lls_f.exists() else None,
                         "fuentes": {rel(x): sha(x) for x in (m, fuente_e, lls_f) if x.exists()}})
    resumen["rl_verbal"] = corridas


def gasto(resumen: dict) -> None:
    r = U / "logs" / "gasto.json"
    g = json.loads(r.read_text(encoding="utf-8"))
    por = defaultdict(lambda: {"llamadas": 0, "usd": 0.0})
    for c in g["llamadas"]:
        k = f"{c['fase']}|{c['corrida']}|{c['modelo']}"
        por[k]["llamadas"] += 1
        por[k]["usd"] = round(por[k]["usd"] + c["usd"], 6)
    modelos = defaultdict(lambda: {"llamadas": 0, "usd": 0.0})
    for c in g["llamadas"]:
        modelos[c["modelo"]]["llamadas"] += 1
        modelos[c["modelo"]]["usd"] = round(modelos[c["modelo"]]["usd"] + c["usd"], 6)
    resumen["gasto"] = {"tope_usd": g["tope_usd"], "total_usd": round(g["total_usd"], 6), "llamadas": len(g["llamadas"]),
                        "primera": g["llamadas"][0]["fecha"] if g["llamadas"] else None, "ultima": g["llamadas"][-1]["fecha"] if g["llamadas"] else None,
                        "por_corrida": dict(por), "por_modelo": dict(modelos), "restante_usd": round(g["tope_usd"] - g["total_usd"], 6),
                        "fuente": rel(r), "sha": sha(r),
                        "nota": "Empieza el 25 sep 07:24. Las corridas anteriores (06 del 9–10 sep; 09 del 23–24 sep) no registraron tokens: su costo no está medido."}


def main() -> None:
    filas: list[dict] = []
    resumen: dict = {"generado": datetime.now().isoformat(timespec="seconds"), "commit": _head(),
                     "estados": ["terminado", "en curso", "interrumpida por error", "planeado"]}
    qagent(filas, resumen)
    stepsizes(filas, resumen)
    isabelle08(filas, resumen)
    jueces09(filas, resumen)
    corpus = corpus09(resumen)
    linea_base(filas, resumen, corpus)
    rl_verbal(filas, resumen, corpus)
    gasto(resumen)
    orden = lambda f: (f["subproyecto"], f["experimento"], f["corrida"], str(f["tarea"]), str(f["episodio"]).zfill(4))
    with open(OUT / "metricas.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=CAMPOS)
        w.writeheader()
        w.writerows(sorted(filas, key=orden))
    (OUT / "resumen.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"metricas.csv: {len(filas)} filas; resumen.json: {', '.join(k for k in resumen if k not in ('generado', 'commit', 'estados'))}")


if __name__ == "__main__":
    main()
