"""Etapas 6 y 7 de PLAN_rl_verbal.md: construir el cuaderno (train) y evaluar (test), por fases, con topes.

    python -m unirl.experimentos humo      [--modelo gpt-6-luna] [--peldano orden_1_lineal] [--config C]
    python -m unirl.experimentos cuaderno  [--modelo gpt-6-luna]            # train, config F, en serie; se reanuda
    python -m unirl.experimentos evaluar   --configs B0,B,C [--episodios 2] [--paralelo 4] [--cuaderno <hash>]
    python -m unirl.experimentos linea-base --cuaderno <hash> [--config E]  # martillo solo con los lemas del cuaderno
    python -m unirl.experimentos medir-sol                                  # 3 llamadas de Sol (PLAN §9.3)
    python -m unirl.experimentos resumen   runs/rl_verbal/<fase>/<corrida>

Cada fase tiene su tope de llamadas en el libro de gastos (PLAN §9): cuaderno 236, evaluacion 614, pareada_luna 154,
pareada_sol 154, medicion_sol 3, humo 12; y el tope global en dólares (25; 28 solo si Sol lo requiere). Toda corrida
larga va bajo `caffeinate -i`. Registro por llamada en <corrida>/llamadas.jsonl y por episodio en episodios.jsonl.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import statistics
import sys
import time
import traceback
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

from . import corpus, cuaderno as C, martillo as M
from .gd_isabelle import TheoremVerifier
from .loop import ProviderFatal, complete_with_retries
from .recompensa import ruta_linea_base, resueltos_por_martillo
from .reflexion import CONFIGS, Config, episodio, escribir

BASE = Path(__file__).resolve().parent.parent
RUNS = BASE / "runs" / "unirl" / "rl_verbal"
TOPES = {"humo": 12, "cuaderno": 236, "evaluacion": 614, "pareada_luna": 154, "pareada_sol": 154, "medicion_sol": 3}
DESTILAR_CADA = 6
MAX_LEMAS_POR_EPISODIO = 4
ORDEN_TRAIN = ("biseccion", "punto_fijo", "ordenes", "newton")


def proveedor(modelo: str, fase: str, corrida: str, effort: str = "high"):
    from .cli import make_provider
    return make_provider({"provider": "openai", "model": modelo, "effort": effort, "fase": fase, "name": corrida,
                          "tope_llamadas": TOPES.get(fase)})


def _orden(p: dict):
    m = re.match(r"(\d+)(.*)", str(p["peldano"]))
    return (int(m.group(1)), m.group(2)) if m else (99, str(p["peldano"]))


def peldanos(split: str, ids: list[str] | None = None) -> list[dict]:
    ps = [p for p in corpus.usables(split=split) if not ids or p["id"] in ids]
    if split == "train":
        ps.sort(key=lambda p: (ORDEN_TRAIN.index(p["metodo"]) if p["metodo"] in ORDEN_TRAIN else 9, _orden(p)))
    else:
        ps.sort(key=lambda p: (p["metodo"], _orden(p)))
    return ps


def nueva_corrida(fase: str, modelo: str, extra: dict) -> Path:
    from .cli import code_fingerprint
    out = RUNS / fase / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{modelo}"
    out.mkdir(parents=True, exist_ok=False)
    (out / "meta.json").write_text(json.dumps({"fase": fase, "modelo": modelo, "inicio": datetime.now().isoformat(timespec="seconds"),
                                               "tope_llamadas": TOPES.get(fase), "codigo": code_fingerprint(), **extra},
                                              ensure_ascii=False, indent=1), encoding="utf-8")
    return out


def _resumen_episodio(ep: dict) -> dict:
    return {k: v for k, v in ep.items() if k not in ("historia", "seleccion")}


# ----------------------------------------------------------------------------- construir el cuaderno (train)


def actualizar_cuaderno(cuad: C.Cuaderno, ep: dict, llamadas: list[dict], modelo: str) -> dict:
    """Escrituras de un episodio de train: contadores de errores y estrategias, y lemas admitidos por el kernel."""
    errores = [e for r in llamadas if r.get("tipo") == "intento" for e in (r.get("errores") or [])]
    vistos = cuad.registrar_errores_de_intentos(errores, ep["episodio_id"], "train")
    for e in ep["seleccion"]["estrategias"]:  # los mismos objetos del cuaderno: se actualizan en su lugar
        C.registrar_uso_estrategia(e, ep["aceptado"], "train")
    candidatos, nombres = [], {l["nombre"] for l in cuad.lemas}
    for r in llamadas:
        for lem in r.get("lemas_verificados") or []:
            if lem["name"] not in nombres and lem["name"] not in {c["name"] for c in candidatos}:
                candidatos.append(lem)
    admitidos, rechazados = [], []
    for lem in candidatos[:MAX_LEMAS_POR_EPISODIO]:
        esc, _ = C.alcance(lem["text"], ep["metodo"])
        gen, met = cuad.cuaderno_de(esc or "general")
        a = C.admitir_lema(lem["text"], ep["metodo"], gen, met, split="train")
        if a["admitido"]:
            cuad.agregar_lema(a, {"peldano": ep["peldano"], "episodio": ep["episodio_id"], "modelo": modelo,
                                  "fecha": time.strftime("%Y-%m-%dT%H:%M:%S")})
            admitidos.append(a["nombre"])
        else:
            rechazados.append({"nombre": lem["name"], "motivo": a["motivo"]})
    cuad.guardar()
    return {"errores_vistos": vistos, "lemas_admitidos": admitidos, "lemas_rechazados": rechazados,
            "lemas_candidatos_descartados_por_tope": max(0, len(candidatos) - MAX_LEMAS_POR_EPISODIO)}


PROMPT_DESTILAR = """Eres el cuaderno de un matemático que aprende a demostrar teoremas en Isabelle/HOL. Abajo están los \
últimos episodios de entrenamiento (enunciado, si se aceptó, los errores del kernel, las reflexiones y la prueba \
aceptada si la hubo). Destila lo que sirva para OTROS teoremas (otros métodos numéricos), no para estos mismos:

ERRORES: errores concretos de Isabelle que se repitieron, en una frase cada uno. Si el error dice que un nombre existe o \
no existe, decláralo en `afirma` (se comprobará en Isabelle; una afirmación falsa descarta el error).
ESTRATEGIAS: maneras de estructurar una demostración que funcionaron en un episodio ACEPTADO (o que produjo lemas \
verificados), en una frase cada una, con el episodio de origen y un tópico de una palabra.

Responde exactamente así (puede haber cero líneas en un bloque):
ERRORES: <<<
texto: <frase> || afirma: no_existe metodo <nombre>; existe hecho <nombre>
>>>
ESTRATEGIAS: <<<
origen: <id del episodio> || topico: <palabra> || texto: <frase>
>>>
"""


def destilar(prov, cuad: C.Cuaderno, episodios: list[dict], llamadas: list[dict], registro: Path, meta: dict) -> dict:
    partes = [PROMPT_DESTILAR]
    for ep in episodios:
        ls = [r for r in llamadas if r.get("episodio_id") == ep["episodio_id"] and r.get("tipo") == "intento"]
        aceptada = next((r for r in ls if r.get("aceptada")), None)
        s = [f"### episodio {ep['episodio_id']}: {ep['statement_es'] if 'statement_es' in ep else ep['peldano']}",
             f"aceptado: {'sí, en el intento ' + str(ep['intento_exito']) if ep['aceptado'] else 'no'}; "
             f"lemas verificados: {sum(len(r.get('lemas_verificados') or []) for r in ls)}"]
        for r in ls:
            if r.get("reflexion"):
                s.append(f"reflexión (intento {r['intento']}): {r['reflexion'][:600]}")
            if not r.get("aceptada") and r.get("errores"):
                s.append(f"errores (intento {r['intento']}): " + " | ".join(r["errores"][:4])[:700])
        if aceptada:
            s.append("prueba aceptada:\n" + aceptada.get("prueba_final", "")[:2500])
        partes.append("\n".join(s))
    t = time.monotonic()
    texto = complete_with_retries(prov, "Destilas un cuaderno de demostración en español, sin inventar.", "\n\n".join(partes))
    uso = getattr(prov, "ultimo_uso", None)
    res = {"errores_admitidos": [], "errores_rechazados": [], "estrategias_admitidas": [], "estrategias_rechazadas": []}
    if texto:
        por_id = {e["episodio_id"]: e for e in episodios}
        errs = re.search(r"ERRORES:\s*<<<(.*?)>>>", texto, re.S)
        for linea in (errs.group(1).splitlines() if errs else []):
            m = re.match(r"\s*-?\s*texto:\s*(.+?)(?:\|\|\s*afirma:\s*(.*))?$", linea)
            if not m:
                continue
            afirma = []
            for a in re.split(r";\s*", (m.group(2) or "").strip()):
                ma = re.match(r"(no_existe|existe)\s+(metodo|método|hecho)\s+(\S+)", a.strip())
                if ma:
                    afirma.append({"tipo": ma.group(2).replace("método", "metodo"), "nombre": ma.group(3).strip("`"),
                                   "existe": ma.group(1) == "existe"})
            texto_e = m.group(1).strip()
            if any(texto_e.lower() == e.get("texto", "").lower() for e in cuad.errores.get("errores", [])):
                continue
            a = C.admitir_error({"texto": texto_e, "afirma": afirma}, "train")
            if a["admitido"]:
                cuad.agregar_error(a, {"destilacion": meta.get("corrida"), "fecha": time.strftime("%Y-%m-%dT%H:%M:%S")})
                res["errores_admitidos"].append(texto_e)
            else:
                res["errores_rechazados"].append({"texto": texto_e, "motivo": a["motivo"]})
        est = re.search(r"ESTRATEGIAS:\s*<<<(.*?)>>>", texto, re.S)
        for linea in (est.group(1).splitlines() if est else []):
            m = re.match(r"\s*-?\s*origen:\s*(\S+)\s*\|\|\s*topico:\s*(\S+)\s*\|\|\s*texto:\s*(.+)$", linea)
            if not m:
                continue
            origen, topico, texto_s = m.group(1), m.group(2), m.group(3).strip()
            if any(texto_s.lower() == e["texto"].lower() for e in cuad.estrategias):
                continue
            ep = por_id.get(origen)
            info = {"split": "train", "id": origen, "aceptado": bool(ep and ep["aceptado"]),
                    "lemas_verificados": ep.get("lemas_admitidos_n", 0) if ep else 0}
            a = C.admitir_estrategia(texto_s, info)
            if a["admitido"]:
                cuad.agregar_estrategia(a, topico, {"destilacion": meta.get("corrida"), "fecha": time.strftime("%Y-%m-%dT%H:%M:%S")})
                res["estrategias_admitidas"].append(texto_s)
            else:
                res["estrategias_rechazadas"].append({"texto": texto_s, "motivo": a["motivo"]})
        vig, desc = C.descartar_estrategias(cuad.estrategias)
        cuad.estrategias[:] = vig
        res["estrategias_descartadas"] = [e["texto"] for e in desc]
        cuad.guardar()
    escribir(registro, {**meta, "tipo": "destilacion", "episodios": [e["episodio_id"] for e in episodios], "uso": uso,
                        "llm_s": round(time.monotonic() - t, 1), "respuesta": (texto or "")[:20000], **res,
                        "fecha": time.strftime("%Y-%m-%dT%H:%M:%S")})
    return res


def construir_cuaderno(modelo: str, ids: list[str] | None = None, reanudar: Path | None = None, config: str = "F",
                       verbose: bool = True) -> Path:
    cfg = CONFIGS[config]
    cuad = C.Cuaderno()
    out = reanudar or nueva_corrida("cuaderno", modelo, {"config": config, "cuaderno_inicial": cuad.hash(),
                                                         "destilar_cada": DESTILAR_CADA})
    prov = proveedor(modelo, "cuaderno", out.name)
    llamadas_f, episodios_f = out / "llamadas.jsonl", out / "episodios.jsonl"
    hechos = {json.loads(l)["peldano"] for l in episodios_f.read_text().splitlines()} if episodios_f.exists() else set()
    resueltos = resueltos_por_martillo("", None)  # en train, r_V usa la línea base sin cuaderno (PLAN §13)
    cache = M.Cache()
    pendientes_destilar: list[dict] = []
    try:
        for spec in peldanos("train", ids):
            if spec["id"] in hechos:
                continue
            meta = {"fase": "cuaderno", "corrida": out.name, "modelo": modelo, "episodio_id": f"{spec['id']}#1"}
            if verbose:
                print(f"[cuaderno] {spec['id']} (dif. {spec['dificultad']}); lemas {len(cuad.lemas)}, estrategias "
                      f"{len(cuad.estrategias)}, gasto ${prov.libro.total():.3f}", flush=True)
            ep = episodio(spec, cfg, prov, llamadas_f, meta, cuaderno=cuad, cache=cache, resueltos=resueltos, verbose=verbose)
            ep["statement_es"] = spec["statement_es"]
            llamadas = [json.loads(l) for l in llamadas_f.read_text().splitlines() if f'"{ep["episodio_id"]}"' in l]
            llamadas = [r for r in llamadas if r.get("episodio_id") == ep["episodio_id"] and r.get("corrida") == out.name]
            act = actualizar_cuaderno(cuad, ep, llamadas, modelo)
            ep["lemas_admitidos_n"] = len(act["lemas_admitidos"])
            fila = {**_resumen_episodio(ep), **act, "cuaderno_hash_despues": cuad.hash()}
            escribir(episodios_f, fila)
            escribir(C.DIR / "episodios.jsonl", fila)
            pendientes_destilar.append(ep)
            if len(pendientes_destilar) >= DESTILAR_CADA:
                todas = [json.loads(l) for l in llamadas_f.read_text().splitlines()]
                r = destilar(prov, cuad, pendientes_destilar, todas, llamadas_f, {"fase": "cuaderno", "corrida": out.name, "modelo": modelo})
                if verbose:
                    print(f"[cuaderno] destilación: +{len(r['errores_admitidos'])} errores, +{len(r['estrategias_admitidas'])} "
                          f"estrategias", flush=True)
                pendientes_destilar = []
        if pendientes_destilar:
            todas = [json.loads(l) for l in llamadas_f.read_text().splitlines()]
            destilar(prov, cuad, pendientes_destilar, todas, llamadas_f, {"fase": "cuaderno", "corrida": out.name, "modelo": modelo})
    except ProviderFatal as e:
        _abortar(out, str(e))
        print(f"Se puede reanudar con --reanudar {out}", flush=True)
        return out
    except Exception:
        # 25 sep: un KeyError al guardar el cuaderno lo dejó a medio escribir sin marca en la corrida
        _abortar(out, f"error del código\n{traceback.format_exc()}")
        print(f"Se puede reanudar con --reanudar {out} después de corregirlo", flush=True)
        return out
    congelado = cuad.congelar()
    (out / "FIN.json").write_text(json.dumps({"fin": datetime.now().isoformat(timespec="seconds"), "cuaderno": congelado.hash(),
                                              "hash_lemas": congelado.hash_lemas(), "carpeta": str(congelado.dir)}, indent=1),
                                  encoding="utf-8")
    print(f"\ncuaderno congelado: {congelado.dir} (hash {congelado.hash()}, lemas {len(congelado.lemas)}, "
          f"errores aprendidos {sum(1 for e in congelado.errores['errores'] if e.get('clase') == 'aprendido')}, "
          f"estrategias {len(congelado.estrategias)})")
    return out


# ----------------------------------------------------------------------------- evaluar (test)


def cargar_congelado(h: str | None) -> C.Cuaderno | None:
    if not h or h == "ninguno":
        return None
    d = C.CONGELADOS / h
    if not d.exists():
        raise SystemExit(f"no hay cuaderno congelado {h} en {C.CONGELADOS}")
    c = C.Cuaderno(d, solo_lectura=True)
    if c.hash() != h:
        raise SystemExit(f"el cuaderno congelado {h} cambió en disco (hash {c.hash()})")
    return c


def linea_base_con_cuaderno(cuad: C.Cuaderno, config: str = "E", split: str = "test") -> Path:
    """Martillo solo en cada peldaño con los lemas que el cuaderno le mostraría (en serie, con caché). Escribe
    resultados/martillo_linea_base_<hash_lemas>.json, que la recompensa exige para evaluar con ese cuaderno."""
    cfg = CONFIGS[config]
    filas, cache = [], M.Cache()
    for spec in peldanos(split):
        sel = cuad.recuperar(spec, cfg.partes)
        bib = cuad.biblioteca(sel)
        juez = TheoremVerifier.desde_corpus(spec["id"])
        r = M.martillo_solo(juez, cuaderno_hash=C.hash_texto(bib), cache=cache, biblioteca=bib)
        intentos = 1
        while r.get("invalido") and intentos <= 2:
            r = M.martillo_solo(juez, cuaderno_hash=C.hash_texto(bib), cache=cache, usar_cache=False, biblioteca=bib)
            intentos += 1
        filas.append({"id": spec["id"], "resuelto_por_martillo": r["resuelto_por_martillo"], "linea": r.get("linea"),
                      "lemas": [l["nombre"] for l in sel["lemas"]], "suspension_s": r.get("suspension_s"),
                      "desde_cache": r.get("desde_cache"), "intentos": intentos})
        print(f"[linea-base] {spec['id']}: {'RESUELTO' if r['resuelto_por_martillo'] else 'no'} (lemas {len(sel['lemas'])})", flush=True)
    ruta = ruta_linea_base(cuad.hash_lemas())
    ruta.write_text(json.dumps({"cuaderno": cuad.hash_lemas() or "sin-cuaderno", "cuaderno_completo": cuad.hash(),
                                "config": config, "filas": filas}, ensure_ascii=False, indent=1), encoding="utf-8")
    return ruta


def evaluar(modelo: str, configs: list[str], episodios_por_peldano: int, paralelo: int, cuaderno_hash: str | None,
            fase: str = "evaluacion", ids: list[str] | None = None, verbose: bool = True) -> Path:
    cuad = cargar_congelado(cuaderno_hash)
    for c in configs:
        if CONFIGS[c].partes and cuad is None:
            raise SystemExit(f"la configuración {c} necesita --cuaderno <hash de un cuaderno congelado>")
    out = nueva_corrida(fase, modelo, {"configs": configs, "episodios_por_peldano": episodios_por_peldano, "paralelo": paralelo,
                                       "cuaderno": cuaderno_hash})
    prov = proveedor(modelo, fase, out.name)
    trabajos = [(spec, c, k) for spec in peldanos("test", ids) for c in configs for k in range(1, episodios_por_peldano + 1)]
    resueltos = {}
    for c in configs:  # la línea base que corresponde a cada configuración (sin lemas del cuaderno, o con ellos)
        clave = cuad.hash_lemas() if (cuad is not None and "lemas" in CONFIGS[c].partes) else ""
        resueltos[c] = resueltos_por_martillo(clave, [s["id"] for s in peldanos("test", ids)])
    cache = M.Cache()
    llamadas_f, episodios_f = out / "llamadas.jsonl", out / "episodios.jsonl"
    detener = []

    def uno(spec, c, k):
        if detener:
            return None
        meta = {"fase": fase, "corrida": out.name, "modelo": modelo, "episodio_id": f"{spec['id']}#{c}#{k}"}
        try:
            ep = episodio(spec, CONFIGS[c], prov, llamadas_f, meta, cuaderno=cuad if CONFIGS[c].partes else None,
                          cache=cache, resueltos=resueltos[c], verbose=verbose)
        except BaseException:
            detener.append(meta["episodio_id"])  # el mismo hilo detiene la corrida antes de tomar otro trabajo
            raise
        escribir(episodios_f, {**_resumen_episodio(ep), "episodio_k": k})
        return ep

    # 25 sep: aquí solo se capturaba ProviderFatal. Un error del código (sqlite desde hilos trabajadores) mataba el
    # episodio sin registro y la corrida seguía hasta el final. Ahora cualquier fallo detiene la corrida: los
    # episodios en curso terminan, no se lanza ninguno más, y ABORTADA.txt guarda el motivo con su traza.
    with ThreadPoolExecutor(max_workers=max(1, paralelo)) as ex:
        futuros = {ex.submit(uno, *t): t for t in trabajos}
        for f in as_completed(futuros):
            try:
                f.result()
            except ProviderFatal as e:
                _abortar(out, str(e))
            except Exception:
                spec, c, k = futuros[f]
                _abortar(out, f"error del código en {spec['id']}#{c}#{k}\n{traceback.format_exc()}")
    resumen(out)
    return out


def _abortar(out: Path, motivo: str) -> None:
    with open(out / "ABORTADA.txt", "a", encoding="utf-8") as fh:
        fh.write(f"{datetime.now().isoformat(timespec='seconds')}: {motivo}\n")
    print(f"\nCORRIDA DETENIDA ({out.name}): {motivo.splitlines()[0]}", file=sys.stderr, flush=True)


# ----------------------------------------------------------------------------- Sol: medición previa


def medir_sol(peldano: str = "secante_1_inyectiva") -> Path:
    """3 llamadas de Sol (config C3, sin juez ni martillo: solo el costo por llamada), en un peldaño de test."""
    out = nueva_corrida("medicion_sol", "gpt-6-sol", {"peldano": peldano})
    prov = proveedor("gpt-6-sol", "medicion_sol", out.name)
    spec = corpus.exigir_usable(peldano)
    from .reflexion import SISTEMA, construir_prompt
    from .cuaderno import Cuaderno
    prompt = construir_prompt(spec, CONFIGS["C3"], Cuaderno().glosario_compacto(), "", [], [], 0, 1)
    for i in range(1, 4):
        t = time.monotonic()
        texto = complete_with_retries(prov, SISTEMA, prompt)
        escribir(out / "llamadas.jsonl", {"llamada": i, "uso": prov.ultimo_uso, "llm_s": round(time.monotonic() - t, 1),
                                          "respuesta": (texto or "")[:20000]})
        print(f"[medir-sol] llamada {i}: {prov.ultimo_uso} en {time.monotonic() - t:.0f} s", flush=True)
    return out


# ----------------------------------------------------------------------------- resumen (markdown + CSV)


def resumen(out: Path) -> Path:
    eps = [json.loads(l) for l in (out / "episodios.jsonl").read_text().splitlines()] if (out / "episodios.jsonl").exists() else []
    lls = [json.loads(l) for l in (out / "llamadas.jsonl").read_text().splitlines()] if (out / "llamadas.jsonl").exists() else []
    intentos = [r for r in lls if r.get("tipo") == "intento"]
    campos = ["episodio_id", "peldano", "metodo", "split", "dificultad", "version", "config", "aceptado", "intento_exito",
              "intentos", "llamadas", "consultas", "r_V_max", "usd"]
    with open(out / "episodios.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=campos, extrasaction="ignore")
        w.writeheader()
        w.writerows(eps)
    usd = sum((r.get("uso") or {}).get("usd", 0.0) for r in lls)
    lin = [f"# Resumen de {out.name}", "", f"Episodios: {len(eps)}; llamadas: {len(lls)}; costo: ${usd:.4f}.", ""]
    por_conf = defaultdict(list)
    for e in eps:
        por_conf[e["config"]].append(e)
    lin += ["| config | episodios | aceptados | éxito en el intento (mediana) | r_V medio | llamadas | $ |", "|---|---|---|---|---|---|---|"]
    for c, es in sorted(por_conf.items()):
        ok = [e for e in es if e["aceptado"]]
        med = statistics.median([e["intento_exito"] for e in ok]) if ok else "—"
        lin.append(f"| {c} | {len(es)} | {len(ok)} | {med} | {statistics.mean(e['r_V_max'] for e in es):.2f} | "
                   f"{sum(e['llamadas'] for e in es)} | {sum(e['usd'] for e in es):.4f} |")
    etiquetas = Counter(r.get("etiqueta") for r in intentos)
    lin += ["", "Etiquetas de los intentos: " + ", ".join(f"{k} {v}" for k, v in etiquetas.most_common()), ""]
    lin += ["| peldaño | dif. | config | aceptado | intento | r_V | motivo |", "|---|---|---|---|---|---|---|"]
    for e in sorted(eps, key=lambda e: (e["peldano"], e["config"], e["episodio_id"])):
        mot = next((r.get("motivo_r") for r in reversed(intentos) if r.get("episodio_id") == e["episodio_id"] and "motivo_r" in r), "")
        lin.append(f"| {e['peldano']} | {e['dificultad']} | {e['config']} | {'sí' if e['aceptado'] else 'no'} | "
                   f"{e['intento_exito'] or '—'} | {e['r_V_max']} | {mot} |")
    ruta = out / "resumen.md"
    ruta.write_text("\n".join(lin) + "\n", encoding="utf-8")
    return ruta


# ----------------------------------------------------------------------------- CLI


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m unirl.experimentos")
    sub = ap.add_subparsers(dest="cmd", required=True)
    h = sub.add_parser("humo")
    h.add_argument("--modelo", default="gpt-6-luna")
    h.add_argument("--peldano", default="orden_1_lineal")
    h.add_argument("--config", default="C")
    cu = sub.add_parser("cuaderno")
    cu.add_argument("--modelo", default="gpt-6-luna")
    cu.add_argument("--ids", default="")
    cu.add_argument("--reanudar", default="")
    ev = sub.add_parser("evaluar")
    ev.add_argument("--modelo", default="gpt-6-luna")
    ev.add_argument("--configs", required=True)
    ev.add_argument("--episodios", type=int, default=2)
    ev.add_argument("--paralelo", type=int, default=4)
    ev.add_argument("--cuaderno", default="ninguno")
    ev.add_argument("--fase", default="evaluacion")
    ev.add_argument("--ids", default="")
    lb = sub.add_parser("linea-base")
    lb.add_argument("--cuaderno", required=True)
    lb.add_argument("--config", default="E")
    sub.add_parser("medir-sol")
    rs = sub.add_parser("resumen")
    rs.add_argument("carpeta")
    a = ap.parse_args(argv)
    if a.cmd == "humo":
        spec = corpus.exigir_usable(a.peldano)
        out = nueva_corrida("humo", a.modelo, {"peldano": a.peldano, "config": a.config})
        prov = proveedor(a.modelo, "humo", out.name)
        ep = episodio(spec, CONFIGS[a.config], prov, out / "llamadas.jsonl",
                      {"fase": "humo", "corrida": out.name, "modelo": a.modelo, "episodio_id": f"{spec['id']}#1"},
                      resueltos=resueltos_por_martillo("", [spec["id"]]))
        escribir(out / "episodios.jsonl", _resumen_episodio(ep))
        print(resumen(out).read_text())
    elif a.cmd == "cuaderno":
        out = construir_cuaderno(a.modelo, [x for x in a.ids.split(",") if x] or None, Path(a.reanudar) if a.reanudar else None)
        return 0 if (out / "FIN.json").exists() else 1  # FIN.json solo existe si el cuaderno quedó congelado
    elif a.cmd == "evaluar":
        out = evaluar(a.modelo, a.configs.split(","), a.episodios, a.paralelo, a.cuaderno, a.fase,
                      [x for x in a.ids.split(",") if x] or None)
        print((out / "resumen.md").read_text())
        if (out / "ABORTADA.txt").exists():  # código distinto de cero, para encadenar etapas con &&
            return 1
    elif a.cmd == "linea-base":
        print(linea_base_con_cuaderno(cargar_congelado(a.cuaderno), a.config))
    elif a.cmd == "medir-sol":
        medir_sol()
    elif a.cmd == "resumen":
        print(resumen(Path(a.carpeta)).read_text())
    return 0


if __name__ == "__main__":
    sys.exit(main())
