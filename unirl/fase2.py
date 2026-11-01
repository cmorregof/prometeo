"""Fase 2 del confirmatorio (prerregistro v2, §3.3–§3.5, §4, §5, §11): las celdas tarea × rama × semilla.

  * Celdas: para cada tarea de test (familias que siguen tras la exclusión previa y con las 4 construcciones
    completas; tareas no excluidas) y cada rama de §3.3, k semillas. R-texto solo en las familias de H4 (y solo si H4
    es evaluable, §10). La construcción de cada celda es la del contrabalanceo de §3.3 (`fase1.construccion_asignada`):
    D100, P, D100-texto, R-texto y D50 usan la misma en la misma (tarea, semilla).
  * Orden: todas las celdas salvo SC_ig se barajan con Random(20261028); las primeras ceil(10 % · N) son el tramo donde
    se mide K_ig; el 90 % restante más las celdas de SC_ig se vuelven a barajar con Random(20261028) (§3.4). Una sola
    cola (cola.json), reanudable: resultados.jsonl indexa por celda.
  * SC_ig: retenida hasta que exista enmiendas/K_ig.json (`calcular_k_ig` lo escribe a partir de las celdas de D100 y
    SC del primer 10 %: r = tokens por intento (entrada con caché + salida con pensamiento) D100 / SC; K_ig =
    mín(12, máx(4, redondeo(4·r)))). La cola no pasa del índice n10 sin K_ig.
  * ITT (§5, §4): una celda sin ninguna llamada facturada se reprograma UNA vez al final de la ventana; si vuelve a
    fallar, cuenta como no resuelta. Un episodio interrumpido se repite desde cero una vez; a la segunda, no resuelta.
  * Tope 260 USD (fase `confirmatorio:fase2` del libro) y `proyectar_gasto`: lee SOLO el libro de gasto (cada llamada
    lleva en `corrida` el id de su celda) y la cola; tras el 10 % de las celdas, si la proyección supera el tope aplica
    en orden los recortes de §11 (quitar D50; P de k = 2 a 1; tope por familia 40 → 30, el prefijo de la permutación)
    y escribe cada paso como enmienda. La cola lee las enmiendas antes de cada celda.
  * Modelo: el primer `model` devuelto se compara con el de la fase 1 (anexo); cualquier cambio detiene la corrida
    (VigiaModelo) y queda en cambio_modelo.json.
  * Rejuicio SIN_SALIDA_LEAN con 900 s (`rejuzgar_sin_salida`): solo el juez, sin API.
"""

from __future__ import annotations

import json
import math
import random
import re
import threading
from datetime import datetime
from pathlib import Path

from . import corpus_confirmatorio as K
from . import fase1 as F1
from . import plan_v6 as P
from . import prompts_v6 as PR
from .loop import ProviderFatal
from .tokens_api import verificar_conteos

TOPE_FASE2_USD = 260.0
FRACCION_KIG = 0.10
NOMBRE_FASE2 = "fase2"
PASOS_RECORTE = ("quitar_D50", "P_k1", "tope_familia_30", "quitar_s3")  # §11 pasos 1–4 (ronda 2, B-b)
RAMAS_S3 = ("SC", "D100", "D100-texto", "R-texto")  # paso 4: se quita la semilla 3 (la sorteada) de estas ramas
CLAVE_BLOQUE = {"D100": "D100", "D100-texto": "D100-texto", "P": "P", "R-texto": "R-texto", "D50": "D50"}


def celda_id(tarea: str, rama: str, semilla: int) -> str:
    return f"{tarea}|{rama}|s{semilla}"


def partes_celda(c_id: str) -> tuple[str, str, int]:
    tarea, rama, s = c_id.rsplit("|", 2)
    return tarea, rama, int(s[1:])


def celdas(plan: dict, anexo: dict) -> list[dict]:
    """Todas las celdas de test a partir del anexo (familias construidas, exclusión, H4)."""
    familias = [f for f in anexo["familias_construidas"] if anexo["exclusion"]["por_familia"].get(f, {}).get("sigue")]
    h4_ok = anexo["h4"]["evaluable"]
    h4 = set(anexo["h4"]["familias_h4"]) if h4_ok else set()
    out = []
    for fam in sorted(familias):
        d = plan["familias"][fam]
        for i in d["tareas"]:
            if anexo["exclusion"]["por_tarea"].get(i, {}).get("excluida"):
                continue
            for nombre, r in PR.RAMAS.items():
                if nombre == "R-texto" and fam not in h4:
                    continue
                for s in range(1, r.k + 1):
                    c = F1.construccion_asignada(i, s) if nombre in PR.RAMAS_CON_CONSTRUCCION else None
                    out.append({"celda": celda_id(i, nombre, s), "tarea": i, "rama": nombre, "semilla": s, "c": c, "familia": fam,
                                "en_prefijo_30": plan["tareas"][i]["en_prefijo_30"]})
    return out


def ordenar_celdas(cs: list[dict]) -> dict:
    """§3.4/§3.5: orden aleatorio único; SC_ig solo en el 90 % restante."""
    sin_ig = sorted((c for c in cs if c["rama"] != "SC_ig"), key=lambda c: c["celda"])
    ig = sorted((c for c in cs if c["rama"] == "SC_ig"), key=lambda c: c["celda"])
    random.Random(P.SEMILLAS["celdas"]).shuffle(sin_ig)
    n_total = len(cs)
    n10 = math.ceil(FRACCION_KIG * n_total)
    primeras, resto = sin_ig[:n10], sin_ig[n10:] + ig
    random.Random(P.SEMILLAS["celdas"]).shuffle(resto)
    orden = primeras + resto
    for k, c in enumerate(orden):
        c["indice"] = k
    return {"celdas": orden, "n10": n10, "n_total": n_total, "semilla": P.SEMILLAS["celdas"],
            "por_rama": {r: sum(1 for c in orden if c["rama"] == r) for r in PR.RAMAS}}


def cargar_anexo(anexo_dir: Path) -> dict:
    a = Path(anexo_dir)
    j = lambda n: json.loads((a / n).read_text(encoding="utf-8"))
    return {"plan": j("plan.json"), "bloques": j("bloques.json"), "exclusion": j("exclusion.json"), "h4": j("h4_familias.json"),
            "plan_b": j("evaluacion_plan_b.json"), "modelo_api": j("modelo_api.json").get("modelo_api_fase1"),
            "familias_construidas": j("familias_construidas.json"), "dir": a}


def lineas_necesarias(anexo: dict) -> list[str]:
    out = set()
    for bl in anexo["bloques"].values():
        for c in bl.values():
            for k in CLAVE_BLOQUE.values():
                if c.get(k):
                    out |= set(PR.lineas_bloque(c[k]))
    return sorted(out)


def bloques_necesarios(anexo: dict) -> list[list[str]]:
    """Los bloques enteros cuyo conteo (un solo mensaje) decide la igualación: D100, D100-texto, P y R-texto (C3)."""
    out = []
    for bl in anexo["bloques"].values():
        for c in bl.values():
            for k in ("D100", "D100-texto", "P", "R-texto"):
                if c.get(k):
                    out.append(PR.lineas_bloque(c[k]))
    return out


def verificar_antes_de_fase2(anexo_dir: Path, exigir_registro: bool = True, exigir_api_conteos: bool = True, ignorar_plan_b: bool = False) -> list[str]:
    """Motivos por los que la fase 2 NO puede arrancar: anexo íntegro, conteos de count_tokens completos, marcador
    ANEXO_REGISTRADO (fecha + URL del anexo registrado + SHA de SHA256SUMS), sin plan B pendiente."""
    anexo_dir = Path(anexo_dir)
    motivos = F1.verificar_anexo(anexo_dir)
    if motivos:
        return motivos
    anexo = cargar_anexo(anexo_dir)
    motivos += verificar_conteos(anexo_dir / "conteos_tokens.json", lineas_necesarias(anexo), exigir_api=exigir_api_conteos,
                                 bloques_necesarios=bloques_necesarios(anexo))
    if anexo["plan_b"].get("plan_b") and not ignorar_plan_b:
        motivos.append("evaluacion_plan_b.json dice plan B: este diseño no se corre (§10)")
    if exigir_registro:
        m = anexo_dir / "ANEXO_REGISTRADO"
        if not m.exists():
            motivos.append(f"no existe {m}: el anexo debe registrarse (fecha, URL, SHA de SHA256SUMS) antes de la fase 2")
        else:
            try:
                d = json.loads(m.read_text(encoding="utf-8"))
                sha = K._sha((anexo_dir / "SHA256SUMS").read_text(encoding="utf-8"))
                if d.get("sha256_SHA256SUMS") != sha:
                    motivos.append("ANEXO_REGISTRADO no coincide con el SHA-256 de SHA256SUMS")
                if not d.get("url") or not d.get("fecha"):
                    motivos.append("ANEXO_REGISTRADO sin url o sin fecha")
            except json.JSONDecodeError:
                motivos.append("ANEXO_REGISTRADO no es JSON")
    return motivos


# ============================================================================== libro por celda


class ProveedorPorCelda(K.ProveedorContableReservas):
    """La `corrida` que va al libro es el id de la celda del hilo actual: así el script de proyección de gasto puede
    leer SOLO el libro y saber cuántas celdas tienen llamadas y cuánto costó cada rama."""

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self._celda = threading.local()

    @property
    def corrida(self) -> str:
        return getattr(self._celda, "id", None) or self._corrida_base

    @corrida.setter
    def corrida(self, v: str) -> None:
        self._corrida_base = v

    def celda(self, c_id: str | None) -> None:
        self._celda.id = c_id


def proveedor_fase2(modelo: str, tope_usd: float = TOPE_FASE2_USD):
    base = K.hacer_proveedor(modelo, NOMBRE_FASE2, tope_usd, effort=None, recorte=None, task_budget=None)
    return ProveedorPorCelda(base.interno, base.libro, fase=base.fase, corrida=base.corrida)


# ============================================================================== enmiendas mecánicas


def leer_recorte(enmiendas: Path) -> list[str]:
    f = Path(enmiendas) / "recorte.json"
    return json.loads(f.read_text(encoding="utf-8")).get("pasos", []) if f.exists() else []


def celda_recortada(c: dict, pasos: list[str]) -> str | None:
    if "quitar_D50" in pasos and c["rama"] == "D50":
        return "quitar_D50"
    if "P_k1" in pasos and c["rama"] == "P" and c["semilla"] == 2:
        return "P_k1"
    if "tope_familia_30" in pasos and not c["en_prefijo_30"]:
        return "tope_familia_30"
    if "quitar_s3" in pasos and c["rama"] in RAMAS_S3 and c["semilla"] == 3:
        return "quitar_s3"
    return None


def leer_k_ig(enmiendas: Path) -> int | None:
    f = Path(enmiendas) / "K_ig.json"
    return int(json.loads(f.read_text(encoding="utf-8"))["K_ig"]) if f.exists() else None


def _tokens_por_intento(rs: list[dict]) -> float | None:
    tk = sum(r["tokens"]["entrada"] + r["tokens"]["salida"] for r in rs)
    it = sum(r["intentos"] for r in rs)
    return (tk / it) if it else None


def calcular_k_ig(fase2: Path, escribir: bool = True) -> dict:
    """r sobre las celdas de D100 y SC del primer 10 % (n10) con resultado; exige que todas esas celdas estén hechas
    (o reprogramadas por falta de llamada). Escribe enmiendas/K_ig.json (enmienda mecánica, §3.4)."""
    fase2 = Path(fase2)
    cola = json.loads((fase2 / "cola.json").read_text(encoding="utf-8"))
    primeras = {c["celda"]: c for c in cola["celdas"][: cola["n10"]]}
    res = {r["celda"]: r for r in F1._leer_jsonl(fase2 / "resultados.jsonl") if "resuelto" in r}
    sin_llamada = {r["celda"] for r in F1._leer_jsonl(fase2 / "reprogramar.jsonl")}
    pend = [c for c in primeras if c not in res and c not in sin_llamada]
    if pend:
        raise ValueError(f"K_ig: faltan {len(pend)} celdas del primer 10 % (p. ej. {pend[0]})")
    d100 = [res[c] for c in primeras if c in res and primeras[c]["rama"] == "D100" and res[c]["intentos"] > 0]
    sc = [res[c] for c in primeras if c in res and primeras[c]["rama"] == "SC" and res[c]["intentos"] > 0]
    a, b = _tokens_por_intento(d100), _tokens_por_intento(sc)
    if not a or not b:
        raise ValueError("K_ig: no hay celdas de D100 o de SC con intentos en el primer 10 %")
    r = a / b
    out = {"K_ig": PR.k_ig(r), "r": r, "tokens_por_intento_D100": a, "tokens_por_intento_SC": b, "n_celdas_D100": len(d100), "n_celdas_SC": len(sc),
           "n10": cola["n10"], "formula": "K_ig = min(12, max(4, round(4·r))); r = tokens por intento (entrada con caché + salida con pensamiento) D100/SC",
           "fecha": datetime.now().isoformat(timespec="seconds"), "enmienda": "mecánica, prevista en §15"}
    if escribir:
        (fase2 / "enmiendas").mkdir(exist_ok=True)
        (fase2 / "enmiendas" / "K_ig.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


def proyectar_gasto(libro: Path, cola: Path, enmiendas: Path, tope_usd: float = TOPE_FASE2_USD, fase: str = f"confirmatorio:{NOMBRE_FASE2}",
                    escribir: bool = True) -> dict:
    """Lee SOLO el libro de gasto (y la cola, que es el plan de celdas, no un resultado). Por rama: costo medio por
    celda observada × celdas planificadas (bajo los recortes ya vigentes). Ramas sin observación: el costo medio
    global × K/4 (SC_ig con K_ig si está; si no, 1,5 como §11). Aplica los pasos de §11 en orden hasta caber."""
    libro, cola, enmiendas = Path(libro), Path(cola), Path(enmiendas)
    entradas = json.loads(libro.read_text(encoding="utf-8")).get("llamadas", []) if libro.exists() else []
    plan_celdas = json.loads(cola.read_text(encoding="utf-8"))
    pasos = leer_recorte(enmiendas)
    k_ig = leer_k_ig(enmiendas)
    por_celda: dict[str, float] = {}
    for e in entradas:
        if e.get("fase") == fase and "|" in str(e.get("corrida", "")):
            por_celda[e["corrida"]] = por_celda.get(e["corrida"], 0.0) + float(e["usd"])
    gastado = round(sum(float(e["usd"]) for e in entradas if e.get("fase") == fase), 4)
    n_obs = len(por_celda)
    if n_obs < plan_celdas["n10"]:
        return {"decision": "aun_no", "celdas_con_llamada": n_obs, "n10": plan_celdas["n10"], "gastado": gastado, "pasos_vigentes": pasos}
    por_rama: dict[str, list[float]] = {}
    for c_id, usd in por_celda.items():
        _, rama, _ = partes_celda(c_id)
        por_rama.setdefault(rama, []).append(usd)
    media_global = sum(por_celda.values()) / n_obs
    medias = {r: sum(v) / len(v) for r, v in por_rama.items()}

    def costo_rama(r: str) -> float:
        if r in medias:
            return medias[r]
        k = (k_ig if (r == "SC_ig" and k_ig) else None)
        return media_global * ((k / 4) if k else (1.5 if r == "SC_ig" else 1.0))

    def proyeccion(pasos_: list[str]) -> float:
        total = 0.0
        for c in plan_celdas["celdas"]:
            if celda_recortada(c, pasos_):
                continue
            total += por_celda.get(c["celda"], costo_rama(c["rama"]))
        return round(total, 2)

    nuevos = list(pasos)
    proy = proyeccion(nuevos)
    aplicados = []
    for paso in PASOS_RECORTE:
        if proy <= tope_usd:
            break
        if paso in nuevos:
            continue
        nuevos.append(paso)
        aplicados.append({"paso": paso, "proyeccion_antes": proy, "proyeccion_despues": proyeccion(nuevos),
                          "fecha": datetime.now().isoformat(timespec="seconds"), "gastado": gastado, "celdas_con_llamada": n_obs})
        proy = proyeccion(nuevos)
    out = {"decision": "recortar" if aplicados else "sin_cambio", "gastado": gastado, "celdas_con_llamada": n_obs, "tope": tope_usd,
           "proyeccion": proy, "sigue_sobre_el_tope": proy > tope_usd, "medias_por_rama": medias, "pasos_vigentes": nuevos, "pasos_aplicados_ahora": aplicados,
           "fuente": "solo logs/gasto_confirmatorio.json + cola.json", "fecha": datetime.now().isoformat(timespec="seconds")}
    if escribir and aplicados:
        enmiendas.mkdir(exist_ok=True)
        f = enmiendas / "recorte.json"
        prev = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {"pasos": [], "historial": []}
        prev["pasos"] = nuevos
        prev["historial"] = prev.get("historial", []) + aplicados
        f.write_text(json.dumps(prev, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


# ============================================================================== la cola de celdas


def entradas_de_celda(anexo: dict, c: dict) -> list[dict]:
    """El bloque congelado de la celda, por NOMBRE de rama (D100-texto tiene su propio bloque filtrado, C4)."""
    if c["rama"] not in CLAVE_BLOQUE:
        return []
    bl = anexo["bloques"][c["tarea"]][str(c["c"])]
    ent = bl.get(CLAVE_BLOQUE[c["rama"]])
    if ent is None:
        raise ValueError(f"{c['celda']}: el anexo no trae el bloque {CLAVE_BLOQUE[c['rama']]} de la construcción {c['c']}")
    return ent


def correr(fase2: Path, anexo_dir: Path, tareas: dict[str, dict], lake, hacer_proveedor, paralelo: int = 4, continuar: bool = False,
           exigir_registro: bool = True, exigir_api_conteos: bool = True, limite: int | None = None, sistema: str = PR.SISTEMA_TEST,
           ignorar_plan_b: bool = False, libro_ruta: Path | None = None, tope_usd: float = TOPE_FASE2_USD) -> dict:
    """La cola de la fase 2.

    * Retención de SC_ig (C1): al llegar a la primera celda de SC_ig sin K_ig se deja de DESPACHAR, pero las celdas en
      curso terminan; eso no es una interrupción. `detener` (interrupción real) solo lo activan CorridaDetenida,
      ProviderFatal (tope duro, cambio de modelo) y el fin de la cola.
    * Proyección de gasto (C6, §11): la hace el propio arnés UNA vez, cuando las n10 primeras celdas de la cola tienen
      resultado; lee el libro (`libro_ruta`) y la cola; escribe enmiendas/proyeccion_n10.json y, si recorta,
      enmiendas/recorte.json. Nadie la lanza a mano.
    * Tope duro (B-b): GastoExcedido detiene la corrida; las celdas no corridas quedan sin correr y se cuentan por rama
      en estado.json («perdidas»)."""
    fase2, anexo_dir = Path(fase2), Path(anexo_dir)
    motivos = verificar_antes_de_fase2(anexo_dir, exigir_registro, exigir_api_conteos, ignorar_plan_b)
    if motivos:
        raise ValueError("la fase 2 no arranca: " + "; ".join(motivos))
    anexo = cargar_anexo(anexo_dir)
    plan = anexo["plan"]
    fase2.mkdir(parents=True, exist_ok=True)
    f_cola, f_res, f_int, f_rep = fase2 / "cola.json", fase2 / "resultados.jsonl", fase2 / "interrumpidos.jsonl", fase2 / "reprogramar.jsonl"
    enmiendas = fase2 / "enmiendas"
    enmiendas.mkdir(exist_ok=True)
    if f_cola.exists():
        if not continuar:
            raise ValueError(f"{f_cola} ya existe: usa continuar=True")
        cola = json.loads(f_cola.read_text(encoding="utf-8"))
    else:
        cola = ordenar_celdas(celdas(plan, anexo))
        cola["anexo_sha256sums"] = K._sha((anexo_dir / "SHA256SUMS").read_text(encoding="utf-8"))
        cola["codigo"] = K._huella_codigo()
        cola["tope_usd"] = tope_usd
        f_cola.write_text(json.dumps(cola, ensure_ascii=False, indent=1), encoding="utf-8")
    (fase2 / "sistema_test.txt").write_text(sistema, encoding="utf-8")
    hechas = {r["celda"] for r in F1._leer_jsonl(f_res) if "resuelto" in r or "recortada" in r}
    interrumpidas: dict[str, int] = {}
    for r in F1._leer_jsonl(f_int):
        interrumpidas[r["celda"]] = interrumpidas.get(r["celda"], 0) + 1
    reprogramadas: dict[str, int] = {}
    for r in F1._leer_jsonl(f_rep):
        reprogramadas[r["celda"]] = reprogramadas.get(r["celda"], 0) + 1
    f_modelo = fase2 / "modelo_api.txt"
    esperado = anexo["modelo_api"] or (f_modelo.read_text(encoding="utf-8").strip() if f_modelo.exists() else None)
    vigia_modelo = PR.VigiaModelo(esperado, f_modelo)
    prov = hacer_proveedor()
    vigia = K.Vigia() if getattr(prov, "model", "") != "seco" else None
    libro_ruta = Path(libro_ruta) if libro_ruta else (Path(prov.libro.ruta) if getattr(prov, "libro", None) is not None else K.LIBRO)
    refs = fase2 / "referencias"
    detener = threading.Event()      # interrupción real: corta los episodios en curso
    no_despachar = threading.Event() # retención (K_ig) o fin de cola: los episodios en curso terminan
    motivo_fin = ["completo"]
    lock = threading.Lock()
    k_ig = [leer_k_ig(enmiendas)]
    pendientes = [c for c in cola["celdas"] if c["celda"] not in hechas and reprogramadas.get(c["celda"], 0) == 0]
    if limite:
        pendientes = pendientes[:limite]
    cursor = [0]
    primeras = [c["celda"] for c in cola["celdas"][: cola["n10"]]]
    proyeccion_hecha = [(enmiendas / "proyeccion_n10.json").exists()]

    def _n10_completo() -> bool:
        con_resultado = {r["celda"] for r in F1._leer_jsonl(f_res) if "resuelto" in r or "recortada" in r} | set(reprogramadas) \
            | {r["celda"] for r in F1._leer_jsonl(f_rep)}
        return all(c in con_resultado for c in primeras)

    def proyectar_si_toca() -> None:
        """Una sola vez, justo al completarse el primer 10 % (§11, C6)."""
        with lock:
            if proyeccion_hecha[0] or not _n10_completo():
                return
            proyeccion_hecha[0] = True
        out = proyectar_gasto(libro_ruta, f_cola, enmiendas, tope_usd, escribir=True)
        out["automatica"] = True
        (enmiendas / "proyeccion_n10.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"proyección de gasto en n10: {out['decision']} ({out.get('proyeccion')} USD proyectados; pasos {out.get('pasos_vigentes')})", flush=True)

    def siguiente() -> dict | None:
        with lock:
            while cursor[0] < len(pendientes):
                if detener.is_set() or no_despachar.is_set():
                    return None
                c = pendientes[cursor[0]]
                pasos = leer_recorte(enmiendas)
                if (paso := celda_recortada(c, pasos)):
                    cursor[0] += 1
                    K._registrar(f_res, {**c, "recortada": paso, "fecha": datetime.now().isoformat(timespec="seconds")})
                    continue
                if c["rama"] == "SC_ig":
                    if k_ig[0] is None:
                        k_ig[0] = leer_k_ig(enmiendas)
                    if k_ig[0] is None:
                        motivo_fin[0] = f"RETENIDA en el índice {c['indice']}: hace falta K_ig (enmiendas/K_ig.json; `kig`) antes de la primera celda de SC_ig"
                        no_despachar.set()  # las celdas en curso terminan: no es una interrupción
                        return None
                if interrumpidas.get(c["celda"], 0) >= 2:
                    cursor[0] += 1
                    K._registrar(f_res, {**c, "resuelto": False, "motivo": "interrumpida dos veces: cuenta como no resuelta (§4)", "intentos": 0,
                                         "llamadas_facturadas": 0, "tokens": {"entrada": 0, "salida": 0, "cache": 0}, "usd": 0.0})
                    continue
                cursor[0] += 1
                return c
            return None

    def correr_celda(c: dict, reprogramacion: bool) -> None:
        t = K.tarea_de(tareas[c["tarea"]])
        ref = K.referencia(t, lake, refs)
        cfg = PR.config_de(c["rama"], k_ig[0])
        entradas = entradas_de_celda(anexo, c)
        if hasattr(prov, "celda"):
            prov.celda(c["celda"])
        ep_id = c["celda"] + ("#R" if reprogramacion else "")
        try:
            res = PR.episodio_v6(t, c["rama"], cfg, prov, lake, entradas, fase2, ep_id, ref, sistema=sistema, parar=detener,
                                 vigia=vigia, vigia_modelo=vigia_modelo)
        finally:
            if hasattr(prov, "celda"):
                prov.celda(None)
        res.update({k_: c[k_] for k_ in ("celda", "semilla", "c", "familia", "indice", "en_prefijo_30")})
        res["reprogramacion"] = reprogramacion
        res["n_bloque"] = sum(len(e["teoremas"]) for e in entradas)
        if res.get("interrumpido"):
            K._registrar(f_int, res)
            return
        if res["llamadas_facturadas"] == 0 and not reprogramacion:
            K._registrar(f_rep, res)  # ITT: una reprogramación al final de la ventana
        else:
            if res["llamadas_facturadas"] == 0:
                res.update({"resuelto": False, "motivo": "sin llamada facturada también en la reprogramación: no resuelta (§5)"})
            K._registrar(f_res, res)
            print(f"{c['celda']} [{c['indice']}]: resuelto={res['resuelto']} intentos={res['intentos']} usd={res['usd']:.4f}", flush=True)
        proyectar_si_toca()

    def trabajador() -> None:
        while not detener.is_set():
            c = siguiente()
            if c is None:
                return
            try:
                correr_celda(c, reprogramacion=False)
            except (K.CorridaDetenida, ProviderFatal) as e:
                detener.set()
                motivo_fin[0] = f"{type(e).__name__}: {e}"[:400]
                if isinstance(e, PR.CambioDeModelo):
                    (fase2 / "cambio_modelo.json").write_text(json.dumps({"motivo": str(e), "celda": c["celda"], "indice": c["indice"],
                                                                         "fecha": datetime.now().isoformat(timespec="seconds")}, ensure_ascii=False, indent=1), encoding="utf-8")
                return
            except Exception as e:
                K._registrar(fase2 / "errores.jsonl", {**c, "error": f"{type(e).__name__}: {e}"[:800]})
                K._registrar(f_res, {**c, "resuelto": False, "motivo": f"error de programa: {type(e).__name__}", "intentos": 0, "llamadas_facturadas": 0,
                                     "tokens": {"entrada": 0, "salida": 0, "cache": 0}, "usd": 0.0})

    hilos = [threading.Thread(target=trabajador, daemon=True) for _ in range(max(1, paralelo))]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()
    # final de la ventana: UNA reprogramación de las celdas sin llamada facturada (si la cola terminó sin detenerse ni retenerse)
    reprog_hechas = 0
    if not detener.is_set() and not no_despachar.is_set() and cursor[0] >= len(pendientes) and not limite:
        ya = {r["celda"] for r in F1._leer_jsonl(f_res) if "resuelto" in r}
        por_celda = {}
        for r in F1._leer_jsonl(f_rep):
            por_celda.setdefault(r["celda"], []).append(r)
        for c_id, rs in por_celda.items():
            if c_id in ya or len(rs) > 1:
                continue
            c = next(x for x in cola["celdas"] if x["celda"] == c_id)
            try:
                correr_celda(c, reprogramacion=True)
                reprog_hechas += 1
            except (K.CorridaDetenida, ProviderFatal) as e:
                detener.set(); motivo_fin[0] = f"{type(e).__name__}: {e}"[:400]; break
    filas = F1._leer_jsonl(f_res)
    res_all = [r for r in filas if "resuelto" in r]
    recortadas = {r["celda"] for r in filas if "recortada" in r}
    hechas_fin = {r["celda"] for r in res_all} | recortadas
    pasos = leer_recorte(enmiendas)
    perdidas = {r: 0 for r in PR.RAMAS}
    for c in cola["celdas"]:  # planificadas bajo los recortes vigentes y sin resultado: quedan sin correr (tope duro o detención)
        if c["celda"] not in hechas_fin and not celda_recortada(c, pasos):
            perdidas[c["rama"]] += 1
    estado = {"fin": datetime.now().isoformat(timespec="seconds"), "motivo_fin": motivo_fin[0], "celdas_hechas": len(res_all),
              "celdas_recortadas": len(recortadas), "n_total": cola["n_total"], "n10": cola["n10"],
              "reprogramaciones": reprog_hechas, "modelo_api": vigia_modelo.esperado, "K_ig": k_ig[0], "pasos_recorte": pasos,
              "proyeccion_n10_hecha": proyeccion_hecha[0], "celdas_perdidas_por_rama": perdidas, "celdas_perdidas": sum(perdidas.values()),
              "por_rama": {r: {"hechas": sum(1 for x in res_all if x["rama"] == r), "resueltas": sum(1 for x in res_all if x["rama"] == r and x["resuelto"]),
                               "sin_llamada": sum(1 for x in F1._leer_jsonl(f_rep) if x["rama"] == r),
                               "interrumpidas": sum(1 for x in F1._leer_jsonl(f_int) if x["rama"] == r),
                               "timeouts_lean": sum(x.get("timeouts_lean", 0) for x in res_all if x["rama"] == r),
                               "max_tokens": sum(x.get("max_tokens", 0) for x in res_all if x["rama"] == r),
                               "tokens": sum(x["tokens"]["entrada"] + x["tokens"]["salida"] for x in res_all if x["rama"] == r)} for r in PR.RAMAS},
              "usd": getattr(getattr(prov, "libro", None), "gastado", lambda f: None)(getattr(prov, "fase", "")) if getattr(prov, "libro", None) is not None else None}
    (fase2 / "estado.json").write_text(json.dumps(estado, ensure_ascii=False, indent=1), encoding="utf-8")
    return estado


# ============================================================================== rejuicio SIN_SALIDA_LEAN (§4)


def rejuzgar_sin_salida(fase2: Path, anexo_dir: Path, tareas: dict[str, dict], lake900) -> dict:
    """Para cada celda con algún principal SIN_SALIDA_LEAN y no resuelta: se vuelve a juzgar esa prueba con 900 s (solo
    el juez, sin API). Si da ACCEPTED y el segundo testigo también, la celda pasa a resuelta en rejuicios.jsonl y en
    resultados_finales.jsonl; si no, queda como estaba. Una sola vez por celda."""
    fase2 = Path(fase2)
    anexo = cargar_anexo(anexo_dir)
    res = {r["celda"]: r for r in F1._leer_jsonl(fase2 / "resultados.jsonl") if "resuelto" in r}
    ya = {r["celda"] for r in F1._leer_jsonl(fase2 / "rejuicios.jsonl")}
    llamadas = {}
    for l in F1._leer_jsonl(fase2 / "llamadas.jsonl"):
        llamadas.setdefault(l["episodio"], []).append(l)
    intentos = {}
    for r in F1._leer_jsonl(fase2 / "intentos.jsonl"):
        if r.get("tipo") == "intento":
            intentos.setdefault(r["episodio"], []).append(r)
    cola = {c["celda"]: c for c in json.loads((fase2 / "cola.json").read_text(encoding="utf-8"))["celdas"]}
    n = 0
    for c_id, r in res.items():
        if r["resuelto"] or c_id in ya or not r.get("sin_salida_lean"):
            continue
        ep = c_id + ("#R" if r.get("reprogramacion") else "")
        c = cola[c_id]
        t = K.tarea_de(tareas[c["tarea"]])
        ref = K.referencia(t, lake900, fase2 / "referencias")
        entradas = entradas_de_celda(anexo, c)
        contexto_base = PR.lean_de_entradas(entradas) if PR.RAMAS[c["rama"]].invocable else ""
        veredicto = {"celda": c_id, "rejuzgadas": [], "resuelto": False}
        por_llamada = {l["llamada"]: l for l in llamadas.get(ep, [])}
        lemas_ok = []
        for reg in sorted(intentos.get(ep, []), key=lambda x: x["n"]):
            for l in reg.get("lemas", []):
                if l["resultado"].get("etiqueta") == "ACCEPTED":
                    lemas_ok.append(l["bloque"].strip())
            if reg.get("principal", {}).get("etiqueta") != K.SIN_SALIDA:
                continue
            l = por_llamada.get(reg.get("llamada"))
            if not l or not l.get("respuesta"):
                veredicto["rejuzgadas"].append({"intento": reg["n"], "etiqueta": "sin_respuesta_registrada"})
                continue
            rr = F.leer(l["respuesta"])
            contexto = "\n\n".join(x for x in [contexto_base] + lemas_ok if x)
            v = K.juzgar_principal(t, lake900, contexto, rr["aux"], rr["prueba"], ref)
            fila = {"intento": reg["n"], "etiqueta": v["etiqueta"], "s": v.get("s"), "timeout_s": getattr(lake900, "timeout_s", None)}
            if v["etiqueta"] == "ACCEPTED":
                t2 = K.segundo_testigo(t, lake900, contexto, rr["aux"], rr["prueba"], ref)
                fila["segundo_testigo"] = t2["etiqueta"]
                if t2["etiqueta"] == "ACCEPTED":
                    veredicto["resuelto"] = True
            veredicto["rejuzgadas"].append(fila)
            if veredicto["resuelto"]:
                break
        K._registrar(fase2 / "rejuicios.jsonl", veredicto)
        n += 1
        if veredicto["resuelto"]:
            res[c_id] = {**r, "resuelto": True, "rejuicio_900s": True}
    (fase2 / "resultados_finales.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in res.values()), encoding="utf-8")
    return {"rejuzgadas": n, "resueltas_por_rejuicio": sum(1 for r in res.values() if r.get("rejuicio_900s"))}


F = K.F  # frontera, para F.leer en el rejuicio
