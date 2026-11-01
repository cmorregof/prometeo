"""Fase 1 del confirmatorio (prerregistro v2, §3.2, §3.5, §2.4, §9, §10) y todo lo que sigue a la fase 1 sin API.

Guardia (§0 del prerregistro: «antes de la primera llamada a la API de la fase 1»): `construir` no arranca sin un
archivo `PRERREGISTRO_REGISTRADO` (JSON con `osf` —URL o DOI de OSF Registries—, `sha256_prerregistro` y `fecha`;
opcionalmente `tag_git`). Si se da la ruta del prerregistro congelado, su SHA-256 debe coincidir.

Construcción (§3.2, §3.5): CC en línea, en serie dentro de cada construcción; dos construcciones independientes por
pliegue (c = 1, 2; orden de tareas Random(20261031 + c)); familias en orden Random(20261033); tope 24 USD con la regla
de §3.5: cada construcción se completa entera; antes de empezar una familia se comprueba que el gasto más el costo
proyectado de sus episodios (costo medio realizado por episodio, o 0,012 USD si aún no hay) no pase del tope; si no,
esa familia y las siguientes quedan fuera sin haber corrido ninguna celda. El tope duro del libro (24 USD, fase
`confirmatorio:fase1`) es la segunda barrera: si salta a mitad de una construcción, la familia queda incompleta y
fuera (se declara en estado.json). Todo se guarda y es reanudable (`continuar=True`).

Post-fase 1, sin API, con Lean:
  * `rechazados`: propuestas `cu_` cuyo enunciado elabora y cuya prueba el kernel rechazó (PROOF_FAILED), fuera los
    errores de sintaxis (mensajes del parser) y las palabras prohibidas; deduplicadas por α-equivalencia (la
    normalización del censo sobre el tipo que imprime #check) y fuera las α-equivalentes a un certificado de la misma
    construcción (§3.2).
  * `filtrar_bloque`: filtro de compilación «contexto de la tarea + bloque» con el timeout de §4; caen las entradas
    con error; iterativo (una entrada puede depender de otra caída); agrupado por SHA del contexto compilable.
  * `exclusion_previa` (§2.4): `first | exact L | exact L .. | simpa using L` sobre el enunciado de T, para cada L de las dos
    construcciones del otro pliegue; familia sigue con ≥ 10 tareas.
  * `martillo_cuaderno` (§9): la batería del martillo v2 (rfl, decide, norm_num, simp, omega, aesop; evidencia
    positiva por #print axioms) con el bloque D100 declarado, más `simp [lemas]` y `simp_all`.
  * `fondos`: P (certificados de familias de OTRA fuente, igualados en tokens al D100 filtrado de esa tarea y
    construcción, Random(20261029)), R-texto (rechazados del otro pliegue y la misma construcción, igualados igual),
    D50 (ceil(50 %) de las entradas del D100 filtrado, Random(20261032), con filtro de compilación).
  * `lista_h4` (regla del 80 %), `evaluar_plan_b` (§10) y `escribir_anexo` (anexo mecánico con SHA256SUMS).
"""

from __future__ import annotations

import concurrent.futures as cf
import hashlib
import json
import math
import random
import re
import threading
from datetime import datetime
from pathlib import Path

from . import corpus_confirmatorio as K
from . import frontera as F
from . import plan_v6 as P
from . import prompts_v6 as PR
from .gasto import GastoExcedido
from .loop import ProviderFatal
from .tokens_api import Conteos

TOPE_FASE1_USD = 24.0
COSTO_EPISODIO_ESTIMADO = 0.012  # §11
TIMEOUT_FILTRO_S = 300.0         # §4
TIMEOUT_EXCLUSION_S = 10.0       # §2.4, por lema
TOLERANCIA = 0.05                # §3.3: objetivo ± 5 %
UMBRAL_H4 = 0.80
MIN_H4 = 12
MEDIANA_MINIMA_LEMAS = 3
TACTICAS_MARTILLO = ["rfl", "decide", "norm_num", "simp", "omega", "aesop"]  # martillo_corpus_v2.py, literal
AXIOMAS_OK = F.AXIOMAS_OK
_AX = re.compile(r"'([^']+)' (?:depends on axioms: \[([^\]]*)\]|does not depend on any axioms)")
_SINTAXIS = re.compile(r"unexpected token|expected (?:term|token|command|'|\")|unterminated|missing end of")
_OSF = re.compile(r"(?:https?://)?(?:www\.)?osf\.io/[A-Za-z0-9]{4,}|10\.17605/OSF\.IO/[A-Za-z0-9]{4,}", re.I)


def _sha(t: str) -> str:
    return hashlib.sha256(t.encode()).hexdigest()


def cid(clave: str, pliegue: int, c: int) -> str:
    return f"{clave}__p{pliegue}_c{c}"


# ============================================================================== guardia del registro


def verificar_registro(marcador: Path, prerregistro: Path | None = None) -> dict:
    """El JSON del marcador, o ValueError con el motivo. La fase 1 no arranca sin esto."""
    marcador = Path(marcador)
    if not marcador.exists():
        raise ValueError(f"no existe {marcador}: la fase 1 no arranca sin el registro en OSF (DOI/URL y SHA-256 del prerregistro congelado)")
    try:
        d = json.loads(marcador.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"{marcador} no es JSON válido: {e}")
    osf = str(d.get("osf", "")).strip()
    if not _OSF.search(osf):
        raise ValueError("el marcador no trae una URL o DOI de OSF reconocible en `osf` (osf.io/<id> o 10.17605/OSF.IO/<id>)")
    sha = str(d.get("sha256_prerregistro", "")).strip().lower()
    if not re.fullmatch(r"[0-9a-f]{64}", sha):
        raise ValueError("el marcador no trae `sha256_prerregistro` (64 hex)")
    if not d.get("fecha"):
        raise ValueError("el marcador no trae `fecha`")
    if prerregistro is not None:
        real = hashlib.sha256(Path(prerregistro).read_bytes()).hexdigest()
        if real != sha:
            raise ValueError(f"el SHA-256 de {prerregistro} ({real[:12]}…) no es el registrado ({sha[:12]}…): el prerregistro cambió")
    return d


# ============================================================================== construcción (fase 1)


def _leer_jsonl(ruta: Path) -> list[dict]:
    return [json.loads(l) for l in ruta.read_text(encoding="utf-8").splitlines() if l.strip()] if ruta.exists() else []


def construcciones_de(plan: dict) -> list[tuple[str, str, int, int]]:
    """(familia, cid, pliegue, c) en el orden de la fase 1: familias Random(20261033), dentro p1c1, p1c2, p2c1, p2c2."""
    out = []
    for fam in P.orden_familias_fase1(plan):
        clave = plan["familias"][fam]["clave"]
        for p in (1, 2):
            for c in (1, 2):
                out.append((fam, cid(clave, p, c), p, c))
    return out


def construir(plan: dict, tareas: dict[str, dict], salida: Path, lake, hacer_proveedor, registro: dict,
              tope_usd: float = TOPE_FASE1_USD, paralelo: int = 4, continuar: bool = False, sistema: str = PR.SISTEMA_FASE1,
              costo_estimado: float = COSTO_EPISODIO_ESTIMADO, familias: list[str] | None = None) -> dict:
    """Las 4 construcciones de cada familia (en paralelo entre sí, hasta `paralelo`), familia por familia."""
    if not registro:
        raise ValueError("construir: hace falta el registro verificado (verificar_registro)")
    salida = Path(salida)
    salida.mkdir(parents=True, exist_ok=True)
    (salida / "plan.json").write_text(P.texto_plan(plan), encoding="utf-8")
    (salida / "registro.json").write_text(json.dumps(registro, ensure_ascii=False, indent=1), encoding="utf-8")
    (salida / "sistema_fase1.txt").write_text(sistema, encoding="utf-8")
    f_res = salida / "construcciones.jsonl"
    hechos = {(r["cid"], r["tarea"]) for r in _leer_jsonl(f_res) if "resuelto" in r} if continuar else set()
    if not continuar and f_res.exists():
        raise ValueError(f"{f_res} ya existe: usa continuar=True o una carpeta nueva")
    estado_p = salida / "estado.json"
    estado = json.loads(estado_p.read_text(encoding="utf-8")) if (continuar and estado_p.exists()) else {}
    estado.update({"tope_usd": tope_usd, "inicio": estado.get("inicio") or datetime.now().isoformat(timespec="seconds"),
                   "familias_fuera_por_tope": estado.get("familias_fuera_por_tope", []),
                   "familias_incompletas": estado.get("familias_incompletas", []), "construcciones": estado.get("construcciones", {})})
    f_modelo = salida / "modelo_api.txt"
    vigia_modelo = PR.VigiaModelo(f_modelo.read_text(encoding="utf-8").strip() if f_modelo.exists() else None, f_modelo)
    prov = hacer_proveedor()
    vigia = K.Vigia() if getattr(prov, "model", "") != "seco" else None
    refs = salida / "referencias"
    detener = threading.Event()
    motivo_fin = ["completo"]
    lock = threading.Lock()

    def gastado() -> float:
        libro = getattr(prov, "libro", None)
        if libro is not None:
            return float(libro.gastado(prov.fase))
        return float(sum(r.get("usd", 0) for r in _leer_jsonl(f_res)))

    def costo_medio() -> float:
        rs = [r for r in _leer_jsonl(f_res) if "usd" in r]
        return (sum(r["usd"] for r in rs) / len(rs)) if rs else costo_estimado

    def una_construccion(fam: str, c_id: str, p: int, c: int) -> dict:
        clave = plan["familias"][fam]["clave"]
        cuad = F.Cuaderno(salida / "cuadernos" / clave / f"p{p}_c{c}")
        orden = P.orden_construccion(plan, fam, p, c)
        lock_cuad = threading.Lock()
        n_ok = 0
        for pos, i in enumerate(orden):
            if (c_id, i) in hechos:
                n_ok += 1
                continue
            if detener.is_set():
                break
            try:
                t = K.tarea_de(tareas[i])
                ref = K.referencia(t, lake, refs)
            except ValueError as e:
                K._registrar(f_res, {"cid": c_id, "familia": fam, "pliegue": p, "c": c, "tarea": i, "posicion": pos,
                                     "error_referencia": str(e)[:400]})
                continue
            try:
                res = PR.episodio_v6(t, "CC", F.CONFIGS["CC"], prov, lake, [], salida, f"{c_id}#{i}#pos{pos}", ref, sistema=sistema,
                                     cuad=cuad, lock_cuad=lock_cuad, parar=detener, vigia=vigia, vigia_modelo=vigia_modelo)
            except (K.CorridaDetenida, ProviderFatal) as e:  # incluye GastoExcedido y CambioDeModelo
                detener.set()
                motivo_fin[0] = f"{type(e).__name__}: {e}"[:400]
                break
            except Exception as e:
                K._registrar(salida / "errores.jsonl", {"cid": c_id, "tarea": i, "error": f"{type(e).__name__}: {e}"[:800]})
                continue
            if res.get("interrumpido"):
                K._registrar(salida / "interrumpidos.jsonl", {**res, "cid": c_id})
                break
            res.update({"cid": c_id, "familia": fam, "pliegue": p, "c": c, "posicion": pos})
            K._registrar(f_res, res)
            n_ok += 1
        completa = n_ok == len(orden)
        with lock:
            estado["construcciones"][c_id] = {"familia": fam, "pliegue": p, "c": c, "n_tareas": len(orden), "episodios": n_ok,
                                              "completa": completa, "n_lemas": len(cuad.entradas), "hash": cuad.hash()}
            estado_p.write_text(json.dumps(estado, ensure_ascii=False, indent=1), encoding="utf-8")
        return estado["construcciones"][c_id]

    orden_fams = [f for f in P.orden_familias_fase1(plan) if familias is None or f in familias]
    pendientes = [(fam, [x for x in construcciones_de(plan) if x[0] == fam]) for fam in orden_fams]
    for k_f, (fam, cons) in enumerate(pendientes):
        if detener.is_set():
            break
        restantes = sum(1 for _, c_id, p, c in cons for i in plan["familias"][fam]["pliegues"][str(p)] if (c_id, i) not in hechos)
        proyeccion = gastado() + restantes * costo_medio()
        if proyeccion > tope_usd and restantes > 0:
            fuera = [f for f, _ in pendientes[k_f:]]
            estado["familias_fuera_por_tope"] = sorted(set(estado["familias_fuera_por_tope"]) | set(fuera))
            motivo_fin[0] = (f"tope: gastado {gastado():.3f} + {restantes} episodios × {costo_medio():.4f} = {proyeccion:.2f} > {tope_usd} USD "
                             f"antes de {fam}: {len(fuera)} familias quedan fuera")
            break
        with cf.ThreadPoolExecutor(max(1, min(paralelo, 4))) as ex:
            resultados = list(ex.map(lambda x: una_construccion(*x), cons))
        if not all(r["completa"] for r in resultados):
            estado["familias_incompletas"] = sorted(set(estado["familias_incompletas"]) | {fam})
    if detener.is_set():  # el tope duro (o una detención) saltó a mitad de una familia: las que no empezaron quedan fuera
        empezadas = {v["familia"] for v in estado["construcciones"].values()}
        estado["familias_fuera_por_tope"] = sorted(set(estado["familias_fuera_por_tope"]) | {f for f in orden_fams if f not in empezadas})
    estado.update({"fin": datetime.now().isoformat(timespec="seconds"), "motivo_fin": motivo_fin[0], "usd": gastado(),
                   "modelo_api": vigia_modelo.esperado,
                   "familias_completas": sorted({v["familia"] for v in estado["construcciones"].values()}
                                                - set(estado["familias_incompletas"]) - set(estado["familias_fuera_por_tope"]))})
    estado_p.write_text(json.dumps(estado, ensure_ascii=False, indent=1), encoding="utf-8")
    return estado


def familias_construidas(estado: dict, plan: dict) -> list[str]:
    """Las familias cuyas 4 construcciones están completas: las únicas que siguen al test (§3.5)."""
    completas = {c_id for c_id, v in estado.get("construcciones", {}).items() if v.get("completa")}
    out = []
    for fam, d in plan["familias"].items():
        if all(cid(d["clave"], p, c) in completas for p in (1, 2) for c in (1, 2)):
            out.append(fam)
    return sorted(out)


def cargar_cuadernos(salida: Path, plan: dict, familias: list[str]) -> dict[str, list[dict]]:
    """cid → entradas (en el orden en que el kernel las certificó)."""
    out = {}
    for fam in familias:
        clave = plan["familias"][fam]["clave"]
        for p in (1, 2):
            for c in (1, 2):
                f = Path(salida) / "cuadernos" / clave / f"p{p}_c{c}" / "entradas.json"
                out[cid(clave, p, c)] = json.loads(f.read_text(encoding="utf-8")) if f.exists() else []
    return out


# ============================================================================== compilaciones auxiliares (sin API)


def _rangos(prefijo_lineas: int, trozos: list[str]) -> list[tuple[int, int]]:
    """Rangos de líneas (1-based, inclusivos) de cada trozo si se concatenan con '\\n\\n' tras `prefijo_lineas` líneas."""
    out, linea = [], prefijo_lineas + 1
    for tr in trozos:
        n = tr.count("\n") + 1
        out.append((linea, linea + n - 1))
        linea += n + 1
    return out


def _compilar_con(lake, texto: str, timeout_s: float | None) -> dict:
    """Compila con otro timeout si el lake lo admite (atributo timeout_s), restaurándolo después."""
    if timeout_s is None or not hasattr(lake, "timeout_s"):
        return lake.compilar(texto)
    viejo = lake.timeout_s
    try:
        lake.timeout_s = timeout_s
        return lake.compilar(texto)
    finally:
        lake.timeout_s = viejo


def filtrar_bloque(lake, t: dict, entradas: list[dict], timeout_s: float = TIMEOUT_FILTRO_S, ref: str | None = None,
                   _prof: int = 0, _deriva: bool = True) -> tuple[list[dict], list[dict]]:
    """(entradas que compilan en el contexto de t SIN cambiar el enunciado aprobado, caídas con motivo).

    Dos etapas. (1) Compilación: iterativa (tras quitar las entradas con error se vuelve a compilar, porque una
    entrada puede depender de otra caída); si el archivo entero agota el tiempo se bisecta. (2) Deriva del enunciado
    (ronda 2, C2): con el bloque delante, la referencia del kernel y `unirl_chk` del enunciado aprobado deben seguir
    elaborando y el `#check` debe imprimir el mismo tipo que la referencia (`ref`, si se da). Un `instance`/`def` del
    bloque que cambie el significado del enunciado compilaría sin error pero volvería STATEMENT_DRIFT toda prueba;
    aquí se detecta y se quita la entrada responsable (probándolas una a una); si la deriva es solo conjunta, cae todo."""
    entradas = list(entradas)
    caidas: list[dict] = []
    for _ in range(len(entradas) + 1):
        if not entradas:
            break
        trozos = [e["bloque"].strip() for e in entradas]
        pre = t["prefijo"] + "\n"
        texto = pre + "\n\n".join(trozos) + '\n\n#eval IO.println "UNIRL_FILTRO_FIN"\n' + t["cierre"]
        c = _compilar_con(lake, texto, timeout_s)
        if c["rc"] == -9:
            if len(entradas) == 1 or _prof > 6:
                caidas += [{"nombre": e["nombre"], "motivo": "timeout del filtro"} for e in entradas]
                return [], caidas
            mitad = len(entradas) // 2
            a, ca = filtrar_bloque(lake, t, entradas[:mitad], timeout_s, ref, _prof + 1, _deriva=False)
            b, cb = filtrar_bloque(lake, t, entradas[mitad:], timeout_s, ref, _prof + 1, _deriva=False)
            u, cu = filtrar_bloque(lake, t, a + b, timeout_s, ref, _prof + 1, _deriva)
            return u, caidas + ca + cb + cu
        errs = K._lineas_con_error(c["salida"])
        if c["rc"] == 0 and not errs and "UNIRL_FILTRO_FIN" in c["salida"]:
            break
        rangos = _rangos(pre.count("\n"), trozos)
        malas = {k for k, (a, b) in enumerate(rangos) if any(a <= l <= b for l in errs)}
        if not malas:
            # error fuera de las entradas (contexto o cierre), o Lean murió sin veredicto: nada entra, y se dice
            caidas += [{"nombre": e["nombre"], "motivo": f"error fuera del bloque o sin veredicto (rc={c['rc']})"} for e in entradas]
            return [], caidas
        for k in sorted(malas):
            caidas.append({"nombre": entradas[k]["nombre"], "motivo": "no compila en el contexto de la tarea",
                           "errores": [x for x in F.errores(c["salida"], rangos[k][0]) if "de tu prueba" in x][:3]})
        entradas = [e for k, e in enumerate(entradas) if k not in malas]
    if not entradas or not _deriva:
        return entradas, caidas
    ok, c2 = filtrar_deriva(lake, t, entradas, ref, timeout_s)
    return ok, caidas + c2


def filtrar_deriva(lake, t: dict, entradas: list[dict], ref: str | None = None, timeout_s: float = TIMEOUT_FILTRO_S) -> tuple[list[dict], list[dict]]:
    """Etapa (2) del filtro: quita las entradas que cambian el enunciado aprobado (C2). Depende del enunciado de la
    tarea, no solo de su contexto: se cachea aparte."""
    if not entradas or not deriva_enunciado(lake, t, entradas, ref, timeout_s):
        return list(entradas), []
    culpables = {e["nombre"] for e in entradas if deriva_enunciado(lake, t, [e], ref, timeout_s)}
    caidas = [{"nombre": n, "motivo": "cambia el enunciado aprobado (deriva de la referencia del kernel o del tipo impreso)"} for n in sorted(culpables)]
    resto = [e for e in entradas if e["nombre"] not in culpables]
    if resto and deriva_enunciado(lake, t, resto, ref, timeout_s):
        caidas += [{"nombre": e["nombre"], "motivo": "deriva del enunciado solo en conjunto: cae todo el bloque"} for e in resto]
        return [], caidas
    return resto, caidas


def deriva_enunciado(lake, t: dict, entradas: list[dict], ref: str | None = None, timeout_s: float = TIMEOUT_FILTRO_S) -> bool:
    """True si, con el bloque declarado antes del enunciado, la referencia del kernel y `unirl_chk` no elaboran o el
    `#check` del enunciado aprobado imprime otro tipo que `ref`. Mismo mecanismo que el juez (archivo_principal), con
    el cuerpo del enunciado sustituido por el axioma auxiliar (sin prueba: solo se compara el TIPO)."""
    nonce = "0000000000c2c2c2"
    decl, _, chk, _ = K._ref_y_chk(t, nonce)
    cab = t["cabecera_enunciado"]
    i = cab.rfind(":= by")
    enunciado = cab[:i] + f":= unirl_sorry_{nonce}" if i >= 0 else cab
    texto = (t["prefijo"] + "\n" + decl + "\n\n" + PR.lean_de_entradas(entradas) + "\n\n" + enunciado + "\n\n" + chk
             + f'\n\n#eval IO.println "UNIRL_DERIVA_{nonce}"\n#check @{K.nombre_root(t)}\n#eval IO.println "UNIRL_DERIVAFIN_{nonce}"\n' + t["cierre"])
    c = _compilar_con(lake, texto, timeout_s)
    if c["rc"] != 0 or re.search(r":\d+:\d+: error", c["salida"]) or f"UNIRL_DERIVAFIN_{nonce}" not in c["salida"]:
        return True
    if ref is not None:
        tipo = K._texto_tras(c["salida"], f"UNIRL_DERIVA_{nonce}", f"UNIRL_DERIVAFIN_{nonce}")
        return tipo != ref
    return False


def filtrar_texto(lake, t: dict, entradas: list[dict], timeout_s: float = TIMEOUT_FILTRO_S) -> tuple[list[dict], list[dict]]:
    """Filtro de las ramas de TEXTO (ronda 2, C4), igual para D100-texto y R-texto: cada enunciado, tal como se
    imprime en el prompt (`enunciados[x]`, solo nombre y enunciado, sin las `def`s de su bloque), tiene que elaborar
    SOLO en el contexto de la tarea de test. Una entrada entra si todos sus teoremas elaboran; si no, cae y se reporta."""
    if not entradas:
        return [], []
    nonce = "0000000000c4c4c4"
    nombres, trozos = [], []
    for j, e in enumerate(entradas):
        for k, x in enumerate(e["teoremas"]):
            n = f"cu_tx_{j}_{k}"
            nombres.append((j, n))
            trozos.append(f"theorem {n} {e['enunciados'][x]} := unirl_sorry_{nonce}\n"
                          f'#eval IO.println "UNIRL_CHK_{n}_INI"\n#check @{n}\n#eval IO.println "UNIRL_CHK_{n}_FIN"')
    texto = (t["prefijo"] + "\n" + K._axioma_aux(nonce) + "\n\n" + "\n\n".join(trozos)
             + '\n\n#eval IO.println "UNIRL_TX_FIN"\n' + t["cierre"])
    c = _compilar_con(lake, texto, timeout_s)
    if "UNIRL_TX_FIN" not in c["salida"]:
        return [], [{"nombre": e["nombre"], "motivo": "sin veredicto del filtro de texto (timeout o salida incompleta)"} for e in entradas]
    tipos = _tipos_check(c["salida"])
    # Lean recupera los errores de elaboración (p. ej. `unknown identifier`) con `sorry` y AÑADE la declaración, así que
    # `#check` imprime un tipo aunque el enunciado no elabore (lo detectó el humo con Lean real, 26 oct). Por eso un
    # enunciado cae también si hay un error en SUS líneas o si su tipo impreso contiene `sorry`.
    errs = K._lineas_con_error(c["salida"])
    pre_lineas = (t["prefijo"] + "\n" + K._axioma_aux(nonce) + "\n\n").count("\n")
    rangos = _rangos(pre_lineas, trozos)
    malos = {j for (j, n), (a, b) in zip(nombres, rangos)
             if n not in tipos or "sorry" in tipos.get(n, "") or any(a <= l <= b for l in errs)}
    ok = [e for j, e in enumerate(entradas) if j not in malos]
    caidas = [{"nombre": entradas[j]["nombre"], "motivo": "el enunciado no elabora solo en el contexto de la tarea de test"} for j in sorted(malos)]
    return ok, caidas


def sha_contexto(t: dict) -> str:
    """Las tareas con el mismo contexto compilable comparten los resultados del filtro (§3.2)."""
    return _sha(t["prefijo"] + "\n" + t["cola"] + "\n" + t["cierre"])[:24]


class FiltroCompilacion:
    """Los dos filtros con caché por (SHA del contexto, SHA de la lista de entradas); persistente en filtro_cache.json.
    Las tareas con el mismo contexto compilable (y la misma referencia) comparten el resultado (§3.2)."""

    def __init__(self, lake, cache: Path | None = None, timeout_s: float = TIMEOUT_FILTRO_S):
        self.lake, self.cache_p, self.timeout_s = lake, cache, timeout_s
        self.cache = json.loads(cache.read_text(encoding="utf-8")) if cache and cache.exists() else {}
        self._lock = threading.Lock()

    def _clave(self, clase: str, t: dict, entradas: list[dict], extra: str = "") -> str:
        return clase + ":" + sha_contexto(t) + ":" + _sha(extra)[:12] + ":" + _sha("\n".join(e.get("sha") or _sha(e["bloque"]) for e in entradas))[:24]

    def _con_cache(self, clave: str, entradas: list[dict], calcular):
        with self._lock:
            if clave in self.cache:
                ok = set(self.cache[clave]["ok"])
                return [e for e in entradas if e["nombre"] in ok], self.cache[clave]["caidas"]
        ok, caidas = calcular()
        with self._lock:
            self.cache[clave] = {"ok": [e["nombre"] for e in ok], "caidas": caidas}
            if self.cache_p:
                self.cache_p.parent.mkdir(parents=True, exist_ok=True)
                self.cache_p.write_text(json.dumps(self.cache, ensure_ascii=False), encoding="utf-8")
        return ok, caidas

    def filtrar(self, t: dict, entradas: list[dict], ref: str | None = None) -> tuple[list[dict], list[dict]]:
        """Compilación (caché por contexto: las tareas con el mismo contexto comparten, §3.2) + deriva del enunciado
        (caché por contexto y enunciado) para los bloques invocables: D100, P, D50."""
        ok1, c1 = self._con_cache(self._clave("lean", t, entradas), entradas,
                                  lambda: filtrar_bloque(self.lake, t, entradas, self.timeout_s, ref, _deriva=False))
        ok2, c2 = self._con_cache(self._clave("deriva", t, ok1, t["enunciado"] + (ref or "")), ok1,
                                  lambda: filtrar_deriva(self.lake, t, ok1, ref, self.timeout_s))
        return ok2, c1 + c2

    def filtrar_texto(self, t: dict, entradas: list[dict]) -> tuple[list[dict], list[dict]]:
        """Elaboración de los enunciados solos (ramas de texto: D100-texto, R-texto)."""
        return self._con_cache(self._clave("texto", t, entradas), entradas, lambda: filtrar_texto(self.lake, t, entradas, self.timeout_s))


def _copias(t: dict, pruebas: list[str], prefijo_nombre: str) -> list[tuple[str, str]]:
    """(nombre, texto) de copias del enunciado aprobado con otro nombre y la prueba dada (como martillo_corpus.variantes)."""
    st = t["cabecera_enunciado"]  # con la cola del contexto delante y `:= by` al final
    m = K.NOMBRE.search(st)
    out = []
    for k, pr in enumerate(pruebas):
        nombre = f"{prefijo_nombre}_{k}"
        out.append((nombre, st[:m.start(2)] + nombre + st[m.end(2):] + "\n" + F._indentar(pr)))
    return out


def compilar_copias(lake, t: dict, contexto_lean: str, pruebas: list[str], prefijo_nombre: str, timeout_s: float,
                    exigir_axiomas: bool = True) -> list[str]:
    """Para cada prueba, «cierra» (sin error en su rango y, si se exige, evidencia positiva de #print axioms con
    axiomas estándar), «falla» o «sin_dato» (Lean no llegó: salida incompleta o timeout del archivo)."""
    copias = _copias(t, pruebas, prefijo_nombre)
    pre = t["prefijo"] + "\n" + (contexto_lean.strip() + "\n\n" if contexto_lean.strip() else "")
    trozos = [txt + (f"\n#print axioms {nombre}" if exigir_axiomas else "") for nombre, txt in copias]
    texto = pre + "\n\n".join(trozos) + '\n\n#eval IO.println "UNIRL_COPIAS_FIN"\n' + t["cierre"]
    c = _compilar_con(lake, texto, timeout_s)
    if c["rc"] == -9 or "UNIRL_COPIAS_FIN" not in c["salida"]:
        return ["sin_dato"] * len(pruebas)
    errs = K._lineas_con_error(c["salida"])
    rangos = _rangos(pre.count("\n"), trozos)
    axiomas: dict[str, set[str] | None] = {}
    for m in _AX.finditer(c["salida"]):
        axiomas[m.group(1).split(".")[-1]] = {x.strip() for x in (m.group(2) or "").split(",") if x.strip()}
    out = []
    for (nombre, _), (a, b) in zip(copias, rangos):
        if any(a <= l <= b for l in errs):
            out.append("falla")
        elif not exigir_axiomas:
            out.append("cierra")
        elif nombre in axiomas and axiomas[nombre] <= AXIOMAS_OK:
            out.append("cierra")
        elif nombre in axiomas:
            out.append("falla")
        else:
            out.append("sin_dato")
    return out


# ============================================================================== rechazados (§3.2)


def _es_sintaxis(rb: dict) -> bool:
    return any(_SINTAXIS.search(e) for e in rb.get("errores") or [])


def candidatos_rechazados(salida: Path) -> dict[str, list[dict]]:
    """cid → propuestas rechazadas por el kernel (PROOF_FAILED; fuera sintaxis y prohibidas), con su origen."""
    out: dict[str, list[dict]] = {}
    for reg in _leer_jsonl(Path(salida) / "intentos.jsonl"):
        if reg.get("tipo") != "intento":
            continue
        c_id, tarea = reg["episodio"].split("#")[0], reg["episodio"].split("#")[1]
        for l in reg.get("lemas", []):
            rb = l["resultado"]
            if rb.get("etiqueta") != "PROOF_FAILED" or _es_sintaxis(rb):
                continue
            m = re.match(r"^(\S+): ", rb.get("motivo", ""))
            nombre = m.group(1) if m else (rb.get("nombres") or [None])[-1]
            if not nombre:
                continue
            enunciado = F._enunciado_de(l["bloque"], nombre)
            if enunciado == "?":
                continue
            out.setdefault(c_id, []).append({"nombre": nombre, "enunciado": enunciado, "bloque": l["bloque"].strip(), "tarea": tarea,
                                             "origen": f"{tarea}, {reg['episodio']}, intento {reg['n']}"})
    return out


def _tipos_check(salida_lean: str) -> dict[str, str]:
    """nombre → texto que imprimió `#check @nombre` (tras la marca de cada uno)."""
    out = {}
    for m in re.finditer(r"UNIRL_CHK_(\w+?)_INI(.*?)UNIRL_CHK_\1_FIN", salida_lean, re.S):
        tramo = m.group(2)
        if re.search(r":\d+:\d+: error", tramo):  # `unknown identifier` u otro error: el enunciado no elaboró
            continue
        txt = K._texto_tras(m.group(0), f"UNIRL_CHK_{m.group(1)}_INI", f"UNIRL_CHK_{m.group(1)}_FIN")
        if txt:
            out[m.group(1)] = txt
    return out


def rechazados(salida: Path, lake, tareas: dict[str, dict], cuadernos: dict[str, list[dict]], timeout_s: float = TIMEOUT_FILTRO_S) -> dict[str, dict]:
    """cid → {"entradas": [...], "descartados": {...}}. Las entradas tienen el formato de las del cuaderno (teoremas,
    enunciados, origen) para que `lineas_bloque` las renderice igual que a los certificados."""
    cands = candidatos_rechazados(salida)
    out = {}
    for c_id, lista in cands.items():
        entradas_cuad = cuadernos.get(c_id, [])
        cuaderno_lean = PR.lean_de_entradas(entradas_cuad)
        por_tarea: dict[str, list[dict]] = {}
        for x in lista:
            por_tarea.setdefault(x["tarea"], []).append(x)
        tipos_cert: set[str] = set()
        elaboran: list[tuple[dict, str]] = []
        desc = {"no_elabora": 0, "alfa_duplicado": 0, "alfa_certificado": 0, "sin_dato": 0}
        for tarea_id, xs in por_tarea.items():
            t = K.tarea_de(tareas[tarea_id])
            nonce = "00000000deadbeef"
            decl = K._axioma_aux(nonce)
            trozos = []
            for k, x in enumerate(xs):
                nombre = f"cu_rtx_{k}"
                # solo la declaración del teorema: las `def`s de su bloque no se incluyen (misma regla que filtrar_texto
                # aplica después a las DOS ramas de texto en el contexto de la tarea de test; aquí sirve para la deduplicación α)
                trozos.append(f"theorem {nombre} {x['enunciado']} := unirl_sorry_{nonce}\n"
                              f'#eval IO.println "UNIRL_CHK_{nombre}_INI"\n#check @{nombre}\n#eval IO.println "UNIRL_CHK_{nombre}_FIN"')
            checks_cert = "\n".join(f'#eval IO.println "UNIRL_CHK_cert{k}_INI"\n#check @{n}\n#eval IO.println "UNIRL_CHK_cert{k}_FIN"'
                                    for k, n in enumerate(x_ for e in entradas_cuad for x_ in e["teoremas"]))
            texto = (t["prefijo"] + "\n" + decl + "\n\n" + cuaderno_lean + "\n\n" + checks_cert + "\n\n" + "\n\n".join(trozos)
                     + '\n\n#eval IO.println "UNIRL_RTX_FIN"\n' + t["cierre"])
            c = _compilar_con(lake, texto, timeout_s)
            tipos = _tipos_check(c["salida"])
            if "UNIRL_RTX_FIN" not in c["salida"]:
                desc["sin_dato"] += len(xs)
                continue
            tipos_cert |= {P.normalizar(v) for k, v in tipos.items() if k.startswith("cert")}
            for k, x in enumerate(xs):
                tipo = tipos.get(f"cu_rtx_{k}")
                if not tipo:
                    desc["no_elabora"] += 1
                    continue
                elaboran.append((x, P.normalizar(tipo)))
        vistos: set[str] = set()
        entradas = []
        for x, norm in elaboran:
            if norm in tipos_cert:
                desc["alfa_certificado"] += 1
                continue
            if norm in vistos:
                desc["alfa_duplicado"] += 1
                continue
            vistos.add(norm)
            entradas.append({"nombre": x["nombre"], "teoremas": [x["nombre"]], "declara": [x["nombre"]], "enunciados": {x["nombre"]: x["enunciado"]},
                             "bloque": x["bloque"], "origen": x["origen"], "sha": _sha(x["bloque"]), "tipo_normalizado": norm})
        out[c_id] = {"entradas": entradas, "descartados": desc, "candidatos": len(lista)}
    return out


# ============================================================================== exclusión previa (§2.4) y martillo (§9)


def exclusion_previa(plan: dict, tareas: dict, lake, bloques_d100: dict[str, dict[str, list[dict]]], familias: list[str],
                     timeout_lema_s: float = TIMEOUT_EXCLUSION_S) -> dict:
    """bloques_d100[tarea][c] = D100 filtrado (del otro pliegue). T se excluye si algún L de cualquiera de las dos
    construcciones cierra `first | exact L | exact L .. | simpa using L`. Devuelve por tarea el veredicto y por familia el conteo."""
    por_tarea, por_fam = {}, {}
    for fam in familias:
        d = plan["familias"][fam]
        excl = []
        for i in d["tareas"]:
            t = K.tarea_de(tareas[i])
            cierran = []
            sin_dato = 0
            for c in ("1", "2"):
                entradas = bloques_d100.get(i, {}).get(c, [])
                lemas = [x for e in entradas for x in e["teoremas"]]
                if not lemas:
                    continue
                pruebas = [f"first | exact {L} | exact {L} .. | simpa using {L}" for L in lemas]  # `L ..`: el enunciado aprobado introduce sus binders
                res = compilar_copias(lake, t, PR.lean_de_entradas(entradas), pruebas, "unirl_excl", timeout_lema_s * len(lemas) + 60,
                                      exigir_axiomas=False)
                cierran += [f"c{c}:{L}" for L, r in zip(lemas, res) if r == "cierra"]
                sin_dato += sum(1 for r in res if r == "sin_dato")
            por_tarea[i] = {"excluida": bool(cierran), "cierran": cierran, "sin_dato": sin_dato}
            if cierran:
                excl.append(i)
        quedan = [i for i in d["tareas"] if i not in excl]
        por_fam[fam] = {"excluidas": len(excl), "quedan": len(quedan), "sigue": len(quedan) >= P.MIN_TRAS_EXCLUSION}
    return {"por_tarea": por_tarea, "por_familia": por_fam, "regla": "first | exact L | exact L .. | simpa using L; familia sigue con ≥ 10"}


def martillo_cuaderno(plan: dict, tareas: dict, lake, bloques_d100: dict[str, dict[str, list[dict]]], familias: list[str],
                      timeout_s: float = TIMEOUT_FILTRO_S) -> dict:
    """Estrato «cerrable por martillo + cuaderno»: la batería v2 con el bloque D100 declarado, más simp [lemas] y simp_all."""
    out = {}
    for fam in familias:
        for i in plan["familias"][fam]["tareas"]:
            t = K.tarea_de(tareas[i])
            r_t = {}
            for c in ("1", "2"):
                entradas = bloques_d100.get(i, {}).get(c, [])
                lemas = [x for e in entradas for x in e["teoremas"]]
                tacticas = list(TACTICAS_MARTILLO) + ([f"simp [{', '.join(lemas)}]", "simp_all"] if lemas else [])
                res = compilar_copias(lake, t, PR.lean_de_entradas(entradas), tacticas, "unirl_mt", timeout_s)
                r_t[c] = {"cierran": [tac for tac, r in zip(tacticas, res) if r == "cierra"], "sin_dato": [tac for tac, r in zip(tacticas, res) if r == "sin_dato"]}
            out[i] = {**r_t, "cerrable": any(v["cierran"] for v in r_t.values())}
    return out


# ============================================================================== fondos e igualación (§3.3)


def tokens_entrada(conteos: Conteos, e: dict) -> int:
    """Costo aproximado de una entrada para la selección (suma de sus líneas sin armazón)."""
    return sum(conteos.tokens_linea(l) for l in PR.lineas_bloque([e]))


def tolerancia_de(objetivo: int, entradas_objetivo: list[dict], conteos: Conteos) -> int:
    """§17.7: la tolerancia es el mayor de dos valores: 5 % del objetivo o la mediana de tokens por lema (línea) del
    bloque objetivo."""
    por_lema = sorted(conteos.tokens_linea(l) for l in PR.lineas_bloque(entradas_objetivo))
    mediana = 0.0
    if por_lema:
        k = len(por_lema)
        mediana = por_lema[k // 2] if k % 2 else (por_lema[k // 2 - 1] + por_lema[k // 2]) / 2
    return int(math.ceil(max(TOLERANCIA * objetivo, mediana)))


def igualar(pool: list[dict], objetivo: int, conteos: Conteos, rng: random.Random, nombres_vetados: set[str] | None = None,
            tolerancia: int | None = None) -> dict:
    """Añade entradas enteras del pool, en orden aleatorio, mientras el total estimado no pase de objetivo + tolerancia;
    las que no caben se saltan y se sigue. Después el total REAL se mide con el bloque entero como un solo mensaje
    (C3); si se pasa del límite superior se quitan entradas desde el final hasta caber. Si no se llega a
    objetivo − tolerancia se usa lo que haya y se declara «corto», con la diferencia (§17.7)."""
    pool = list(pool)
    rng.shuffle(pool)
    tol = TOLERANCIA * objetivo if tolerancia is None else tolerancia
    sel, total, usados = [], 0, set(nombres_vetados or ())
    tope = objetivo + tol
    for e in pool:
        nombres = set(e.get("declara", e["teoremas"]))
        if nombres & usados:
            continue
        tk = tokens_entrada(conteos, e)
        if total + tk <= tope:
            sel.append(e)
            total += tk
            usados |= nombres
    real = conteos.tokens_bloque(PR.lineas_bloque(sel))
    while sel and real > tope:
        sel.pop()
        real = conteos.tokens_bloque(PR.lineas_bloque(sel))
    estado = "ok" if real >= objetivo - tol else ("vacio" if objetivo == 0 else "corto")
    return {"entradas": sel, "tokens": real, "tokens_estimado": total, "objetivo": objetivo, "tolerancia": tol, "diferencia": real - objetivo,
            "n": sum(len(e["teoremas"]) for e in sel), "estado": estado}


def fondo_placebo(plan: dict, cuadernos: dict[str, list[dict]], fuente: str, familias: list[str]) -> list[dict]:
    """Unión de los certificados de las dos construcciones (y los dos pliegues) de todas las familias de OTRA fuente."""
    pool = []
    for fam in familias:
        d = plan["familias"][fam]
        if d["fuente"] == fuente:
            continue
        for p in (1, 2):
            for c in (1, 2):
                pool += cuadernos.get(cid(d["clave"], p, c), [])
    return sorted(pool, key=lambda e: e["sha"])


def fondos(plan: dict, tareas: dict, cuadernos: dict[str, list[dict]], rechaz: dict[str, dict], filtro: FiltroCompilacion,
           conteos: Conteos, familias: list[str], refs: Path | None = None) -> dict:
    """Por tarea y construcción c ∈ {1, 2}: D100 (del otro pliegue; filtro de compilación + deriva), D100-texto (los
    enunciados de D100 que elaboran solos en el contexto de test), P (igualado al D100 filtrado, filtrado y completado,
    §17.8), R-texto (rechazados del otro pliegue y la misma construcción, filtrados en el contexto de test con la MISMA
    regla que D100-texto e igualados a D100-texto), D50 (solo la construcción de la semilla 1). `refs`: caché de
    referencias del kernel (fase 1) para la comparación textual del filtro de deriva."""
    bloques, caidas = {}, {}
    for fam in familias:
        d = plan["familias"][fam]
        for i in d["tareas"]:
            t = K.tarea_de(tareas[i])
            try:
                ref = K.referencia(t, filtro.lake, refs)
            except ValueError:
                ref = None
            p_otro = P.otro_pliegue(plan["tareas"][i]["pliegue"])
            c_sem1 = construccion_asignada(i, 1)
            bloques[i] = {}
            pool_p = fondo_placebo(plan, cuadernos, d["fuente"], familias)
            for c in (1, 2):
                src = cid(d["clave"], p_otro, c)
                d100, ca_d = filtro.filtrar(t, cuadernos.get(src, []), ref)
                d100_tx, ca_dtx = filtro.filtrar_texto(t, d100)
                objetivo = conteos.tokens_bloque(PR.lineas_bloque(d100))
                tol = tolerancia_de(objetivo, d100, conteos)
                # P: se selecciona del fondo, se filtra lo seleccionado en el contexto de la tarea y se completa (≤ 3 vueltas)
                rng = random.Random(f"{P.SEMILLAS['fondo_igualacion']}:{i}:{c}")
                sel = igualar(pool_p, objetivo, conteos, rng, tolerancia=tol)
                p_ok, ca_p = filtro.filtrar(t, sel["entradas"], ref)
                vueltas = 0
                while conteos.tokens_bloque(PR.lineas_bloque(p_ok)) < objetivo - tol and vueltas < 3 and ca_p:
                    vueltas += 1
                    ya = {e["sha"] for e in sel["entradas"]} | {x["nombre"] for x in ca_p}
                    resto = [e for e in pool_p if e["sha"] not in ya and e["nombre"] not in ya]
                    tk_ok = conteos.tokens_bloque(PR.lineas_bloque(p_ok))
                    extra = igualar(resto, max(0, objetivo - tk_ok), conteos, rng, {n for e in p_ok for n in e.get("declara", e["teoremas"])}, tolerancia=tol)
                    p2, ca_p2 = filtro.filtrar(t, p_ok + extra["entradas"], ref)
                    sel["entradas"] = sel["entradas"] + extra["entradas"]
                    p_ok, ca_p = p2, ca_p + ca_p2
                tk_p = conteos.tokens_bloque(PR.lineas_bloque(p_ok))
                while p_ok and tk_p > objetivo + tol:  # si el filtro no quitó nada pero el bloque entero mide más de lo estimado
                    p_ok = p_ok[:-1]
                    tk_p = conteos.tokens_bloque(PR.lineas_bloque(p_ok))
                # R-texto: rechazados del otro pliegue, misma construcción; mismo filtro de texto que D100-texto, igualado a D100-texto
                pool_r, ca_r = filtro.filtrar_texto(t, rechaz.get(src, {}).get("entradas", []))
                objetivo_tx = conteos.tokens_bloque(PR.lineas_bloque(d100_tx))
                tol_tx = tolerancia_de(objetivo_tx, d100_tx, conteos)
                r_sel = igualar(pool_r, objetivo_tx, conteos, random.Random(f"{P.SEMILLAS['fondo_igualacion']}:{i}:{c}:R"), tolerancia=tol_tx)
                # D50: submuestra aleatoria del 50 % de las entradas (redondeo hacia arriba) del D100 filtrado, en el orden de certificación; luego filtro
                d50, ca_50 = None, []
                if c == c_sem1 and d100:
                    k50 = math.ceil(len(d100) / 2)
                    idx = sorted(random.Random(f"{P.SEMILLAS['d50']}:{i}:{c}").sample(range(len(d100)), k50))
                    d50, ca_50 = filtro.filtrar(t, [d100[j] for j in idx], ref)
                bloques[i][str(c)] = {
                    "construccion": src, "D100": d100, "D100-texto": d100_tx, "P": p_ok, "R-texto": r_sel["entradas"], "D50": d50,
                    "igualacion": {"objetivo_tokens": objetivo, "tolerancia": tol, "n_d100": sum(len(e["teoremas"]) for e in d100),
                                   "objetivo_tokens_texto": objetivo_tx, "tolerancia_texto": tol_tx, "n_d100_texto": sum(len(e["teoremas"]) for e in d100_tx),
                                   "P": {"tokens": tk_p, "n": sum(len(e["teoremas"]) for e in p_ok), "diferencia": tk_p - objetivo,
                                         "estado": "ok" if objetivo == 0 or tk_p >= objetivo - tol else "corto"},
                                   "R-texto": {k_: v_ for k_, v_ in r_sel.items() if k_ != "entradas"},
                                   "D50": {"n": sum(len(e["teoremas"]) for e in d50)} if d50 is not None else None},
                    "caidas": {"D100": len(ca_d), "D100-texto": len(ca_dtx), "P": len(ca_p), "R-texto": len(ca_r), "D50": len(ca_50),
                               "D100_deriva": sum(1 for x in ca_d if "enunciado" in x.get("motivo", "")),
                               "P_deriva": sum(1 for x in ca_p if "enunciado" in x.get("motivo", ""))},
                    "d100_vacio": not d100}
                caidas.setdefault(fam, {"D100": 0, "D100-texto": 0, "P": 0, "R-texto": 0, "D50": 0, "D100_deriva": 0, "P_deriva": 0, "tareas_d100_vacio": 0})
                for k_ in ("D100", "D100-texto", "P", "R-texto", "D50", "D100_deriva", "P_deriva"):
                    caidas[fam][k_] += bloques[i][str(c)]["caidas"][k_]
                caidas[fam]["tareas_d100_vacio"] += int(not d100)
    return {"bloques": bloques, "caidas_por_familia": caidas}


def construccion_asignada(tarea_id: str, semilla: int) -> int:
    """Contrabalanceo (§3.3, S1): la semilla 1 usa la construcción sorteada con 20261030 para la tarea, la 2 la otra,
    la 3 se sortea."""
    c1 = random.Random(f"{P.SEMILLAS['construccion_asignada']}:{tarea_id}").choice((1, 2))
    if semilla == 1:
        return c1
    if semilla == 2:
        return 3 - c1
    return random.Random(f"{P.SEMILLAS['construccion_asignada']}:{tarea_id}:{semilla}").choice((1, 2))


def familias_que_siguen(exclusion: dict, familias: list[str]) -> list[str]:
    """Las familias con ≥ 10 tareas tras la exclusión previa (§2.4): sobre ellas se calculan H4 (§17.6, ronda 2 C7) y F."""
    return [f for f in familias if exclusion["por_familia"].get(f, {}).get("sigue")]


def drift_fase1(salida: Path) -> dict:
    """Tasa de STATEMENT_DRIFT del juicio principal por construcción en la fase 1 (ronda 2, C2: se reporta)."""
    out: dict[str, dict] = {}
    for reg in _leer_jsonl(Path(salida) / "intentos.jsonl"):
        if reg.get("tipo") != "intento" or "principal" not in reg:
            continue
        c_id = reg["episodio"].split("#")[0]
        d = out.setdefault(c_id, {"juicios": 0, "statement_drift": 0})
        d["juicios"] += 1
        d["statement_drift"] += int(reg["principal"].get("etiqueta") == "STATEMENT_DRIFT")
    return out


def lista_h4(plan: dict, cuadernos: dict, rechaz: dict, conteos: Conteos, familias: list[str]) -> dict:
    """Familias cuyo fondo propio de rechazados (pliegue p, construcción c) alcanza el 80 % de los tokens del cuaderno
    (p, c), para los dos pliegues y las dos construcciones (§3.3, §17.6). `familias` deben ser las que SIGUEN tras la
    exclusión previa (C7). Si menos de 12 cumplen, H4 es no evaluable (§10)."""
    detalle, cumplen = {}, []
    for fam in familias:
        clave = plan["familias"][fam]["clave"]
        ok = True
        det = {}
        for p in (1, 2):
            for c in (1, 2):
                src = cid(clave, p, c)
                tk_c = conteos.tokens_bloque(PR.lineas_bloque(cuadernos.get(src, [])))
                tk_r = conteos.tokens_bloque(PR.lineas_bloque(rechaz.get(src, {}).get("entradas", [])))
                det[src] = {"tokens_cuaderno": tk_c, "tokens_rechazados": tk_r, "cumple": tk_r >= UMBRAL_H4 * tk_c}
                ok &= det[src]["cumple"]
        detalle[fam] = det
        if ok:
            cumplen.append(fam)
    return {"familias_h4": sorted(cumplen), "n": len(cumplen), "evaluable": len(cumplen) >= MIN_H4, "umbral": UMBRAL_H4, "detalle": detalle}


def evaluar_plan_b(plan: dict, cuadernos: dict, exclusion: dict, h4: dict, familias: list[str]) -> dict:
    """§10: mediana de certificados sobre las construcciones de las familias construidas; F tras la exclusión; H4."""
    ns = sorted(len(cuadernos.get(cid(plan["familias"][f]["clave"], p, c), [])) for f in familias for p in (1, 2) for c in (1, 2))
    mediana = (ns[len(ns) // 2] if len(ns) % 2 else (ns[len(ns) // 2 - 1] + ns[len(ns) // 2]) / 2) if ns else 0
    siguen = familias_que_siguen(exclusion, familias)
    return {"n_construcciones": len(ns), "mediana_lemas": mediana, "cuadernos_raquiticos": mediana < MEDIANA_MINIMA_LEMAS,
            "nota": "mediana sobre las construcciones de las familias construidas; H4 sobre las familias que siguen tras la exclusión",
            "F_tras_exclusion": len(siguen), "familias_que_siguen": siguen, "F_menor_que_12": len(siguen) < P.MIN_F,
            "h4_evaluable": h4["evaluable"], "plan_b": (mediana < MEDIANA_MINIMA_LEMAS) or (len(siguen) < P.MIN_F)}


# ============================================================================== anexo mecánico


def escribir_anexo(anexo: Path, plan: dict, estado: dict, cuadernos: dict, rechaz: dict, fondos_: dict, exclusion: dict,
                   martillo: dict, h4: dict, plan_b: dict, conteos: Conteos, familias: list[str], drift: dict | None = None) -> str:
    """Escribe el anexo y SHA256SUMS; devuelve el SHA-256 de SHA256SUMS."""
    anexo = Path(anexo)
    anexo.mkdir(parents=True, exist_ok=True)
    archivos = {
        "plan.json": P.texto_plan(plan),
        "estado_fase1.json": json.dumps(estado, ensure_ascii=False, indent=1, sort_keys=True),
        "familias_construidas.json": json.dumps(familias, ensure_ascii=False, indent=1),
        "cuadernos.json": json.dumps(cuadernos, ensure_ascii=False, indent=1, sort_keys=True),
        "rechazados.json": json.dumps(rechaz, ensure_ascii=False, indent=1, sort_keys=True),
        "bloques.json": json.dumps(fondos_["bloques"], ensure_ascii=False, indent=1, sort_keys=True),
        "caidas_filtro.json": json.dumps(fondos_["caidas_por_familia"], ensure_ascii=False, indent=1, sort_keys=True),
        "exclusion.json": json.dumps(exclusion, ensure_ascii=False, indent=1, sort_keys=True),
        "martillo_cuaderno.json": json.dumps(martillo, ensure_ascii=False, indent=1, sort_keys=True),
        "h4_familias.json": json.dumps(h4, ensure_ascii=False, indent=1, sort_keys=True),
        "evaluacion_plan_b.json": json.dumps(plan_b, ensure_ascii=False, indent=1, sort_keys=True),
        "modelo_api.json": json.dumps({"modelo_api_fase1": estado.get("modelo_api")}, ensure_ascii=False, indent=1),
        "drift_fase1.json": json.dumps(drift or {}, ensure_ascii=False, indent=1, sort_keys=True),
        "familias_que_siguen.json": json.dumps(familias_que_siguen(exclusion, familias), ensure_ascii=False, indent=1),
    }
    for nombre, txt in archivos.items():
        (anexo / nombre).write_text(txt, encoding="utf-8")
    conteos.ruta = anexo / "conteos_tokens.json"
    conteos.guardar()
    sumas = []
    for f in sorted(anexo.iterdir()):
        if f.name != "SHA256SUMS" and f.is_file():
            sumas.append(f"{hashlib.sha256(f.read_bytes()).hexdigest()}  {f.name}")
    txt = "\n".join(sumas) + "\n"
    (anexo / "SHA256SUMS").write_text(txt, encoding="utf-8")
    return _sha(txt)


def verificar_anexo(anexo: Path) -> list[str]:
    """Motivos por los que el anexo no sirve (vacío = íntegro)."""
    anexo = Path(anexo)
    if not (anexo / "SHA256SUMS").exists():
        return [f"no existe {anexo / 'SHA256SUMS'}"]
    motivos = []
    for l in (anexo / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        if not l.strip():
            continue
        sha, nombre = l.split(None, 1)
        f = anexo / nombre.strip()
        if not f.exists():
            motivos.append(f"falta {nombre}")
        elif hashlib.sha256(f.read_bytes()).hexdigest() != sha:
            motivos.append(f"{nombre} no coincide con SHA256SUMS")
    for req in ("plan.json", "bloques.json", "conteos_tokens.json", "h4_familias.json", "evaluacion_plan_b.json", "modelo_api.json",
                "exclusion.json", "familias_construidas.json"):
        if not (anexo / req).exists():
            motivos.append(f"falta {req}")
    return motivos
