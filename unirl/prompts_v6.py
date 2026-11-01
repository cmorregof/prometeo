"""Prompts literales de la v6 (Anexo B del prerregistro), las ramas de §3.3 y el episodio de test.

El juez no cambia: se reutilizan `juzgar_principal`, `segundo_testigo`, `F.admitir_bloque` y `F.evaluar_evals` de la
v5. Lo que cambia respecto de `corpus_confirmatorio.episodio` es solo lo que el prerregistro manda cambiar:

  * SISTEMA de test con la frase de «tareas futuras» neutralizada (§4). En la fase 1 (CC en línea) la frase es
    verdadera y se usa el SISTEMA de la v5 tal cual (`SISTEMA_FASE1`).
  * Cabecera del cuaderno invocable (D100, P, D50) sin el campo «origen» (§3.3): solo nombre y enunciado.
  * Cabecera de pistas de texto (D100-texto, R-texto): IDÉNTICA en las dos ramas, con la instrucción literal de que
    son enunciados no declarados que hay que volver a demostrar (invocarlos da `unknown identifier`). Nada en el
    prompt dice si una pista fue certificada o rechazada, ni de qué familia o tarea viene.
  * La lista de lemas/pistas se renderiza con `lineas_bloque`, que es exactamente lo que se cuenta en tokens (§3.3,
    «tal como lo ve el modelo»).
  * El episodio registra por llamada el `model` devuelto por la API (VigiaModelo detiene la corrida si cambia), los
    tokens (entrada con caché, salida con pensamiento), si la llamada fue facturada (ITT, §5), los `stop_reason`
    (§4) y los timeouts de Lean por rama.
"""

from __future__ import annotations

import re
import threading
import time
import types
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from . import corpus_confirmatorio as K
from . import frontera as F
from .loop import ProviderFatal, Rechazo, complete_with_retries

DORMIR = time.sleep  # las esperas de los reintentos (loop.ESPERAS_REINTENTO); las pruebas lo sustituyen

SISTEMA_FASE1 = K.SISTEMA  # la v5, literal: en la construcción en línea los lemas sí entran al cuaderno de la familia

_FRASE_V5 = ("Un LEMA que el kernel acepta entra al cuaderno y queda disponible por su nombre en todo lo que sigue (en la condición "
             "con cuaderno, también en tareas futuras).")
_FRASE_TEST = "Un LEMA que el kernel acepta queda disponible por su nombre en todo lo que sigue de este episodio."
assert _FRASE_V5 in K.SISTEMA, "el SISTEMA de la v5 cambió: revisar la neutralización"
SISTEMA_TEST = K.SISTEMA.replace(_FRASE_V5, _FRASE_TEST)

TITULO_CUADERNO = "# El cuaderno"
INSTRUCCION_CUADERNO = "Lemas certificados por el kernel de Lean, ya declarados en el archivo (úsalos por su nombre):"
TITULO_TEXTO = "# Pistas"
INSTRUCCION_TEXTO = ("Enunciados en texto, NO declarados en el archivo: no existen en Lean y no se pueden invocar por su nombre "
                     "(hacerlo da `unknown identifier`). Si alguno te sirve, tienes que volver a demostrarlo tú como LEMA, con un "
                     "nombre cu_ nuevo, antes de usarlo. Son solo pistas: no se garantiza que sean ciertos ni demostrables.")


def linea_lema(nombre: str, enunciado: str) -> str:
    return f"- `{nombre}` : {enunciado}"


def lineas_bloque(entradas: list[dict]) -> list[str]:
    """Las líneas del bloque tal como las ve el modelo (y tal como se cuentan en tokens): una por teorema, sin origen.
    Cada entrada tiene `teoremas` y `enunciados` (formato de frontera.incorporar y de los rechazados de la fase 1)."""
    return [linea_lema(x, e["enunciados"][x]) for e in entradas for x in e["teoremas"]]


def lean_de_entradas(entradas: list[dict]) -> str:
    """El cuaderno congelado como contexto Lean, SIN el comentario de origen de Cuaderno.lean()."""
    return "\n\n".join(e["bloque"].strip() for e in entradas)


def cabecera(rama: str, entradas: list[dict]) -> list[str]:
    """La sección del prompt propia de la rama (vacía en SC y SC_ig). «CC» es la construcción en línea de la fase 1:
    cuaderno invocable, misma cabecera que D100."""
    r = RAMA_CC if rama == "CC" else RAMAS[rama]
    if not entradas or (not r.invocable and not r.texto):
        return []
    if r.invocable:
        return [TITULO_CUADERNO, "", INSTRUCCION_CUADERNO] + lineas_bloque(entradas) + [""]
    return [TITULO_TEXTO, "", INSTRUCCION_TEXTO] + lineas_bloque(entradas) + [""]


def construir_prompt(t: dict, rama: str, entradas: list[dict], locales: list[dict], historia: list[dict],
                     intentos_rest: int, turnos_rest: int) -> str:
    p = [f"# La tarea: {t['id']}", "", "El contexto aprobado (no se puede cambiar):", F._md(t["prefijo"], 8000), "",
         "Demuestra este teorema (escribe solo las tácticas en PRUEBA):", F._md(t["cabecera_enunciado"], 4000), ""]
    p += cabecera(rama, entradas)
    if locales:
        p += ["# Lemas certificados en este episodio", ""] + [linea_lema(x, l["enunciados"][x]) for l in locales
                                                              for x in l["teoremas"]] + [""]
    if historia:
        p += ["# Lo que pasó en este episodio", ""]
        for h in historia[-F.MAX_HISTORIA:]:
            p += [f"## {h['tipo']} {h.get('n', '')}", h["resumen"], ""]
    p += ["# Presupuesto", f"Te quedan {intentos_rest} intentos y {turnos_rest} turnos de exploración.", ""]
    return "\n".join(p)


# ============================================================================== ramas (§3.3)


@dataclass(frozen=True)
class Rama:
    nombre: str
    k: int                 # semillas (réplicas)
    intentos: int          # K; en SC_ig se sustituye por K_ig
    invocable: bool        # el bloque va declarado en el archivo Lean y en la cabecera de cuaderno
    texto: bool            # el bloque va solo como pistas de texto
    fuente: str            # "ninguna" | "propio" | "placebo" | "rechazados" | "d50"
    papel: str


RAMAS = {
    "SC": Rama("SC", 3, 4, False, False, "ninguna", "control de H1 y H3"),
    "D100": Rama("D100", 3, 4, True, False, "propio", "tratamiento"),
    "P": Rama("P", 2, 4, True, False, "placebo", "control de H2"),
    "D100-texto": Rama("D100-texto", 3, 4, False, True, "propio", "tratamiento de H4; control de H5"),
    "R-texto": Rama("R-texto", 3, 4, False, True, "rechazados", "control de H4"),
    "SC_ig": Rama("SC_ig", 2, 4, False, False, "ninguna", "control de H3 (K_ig intentos)"),
    "D50": Rama("D50", 1, 4, True, False, "d50", "secundaria: dosis exógena"),
}
RAMA_CC = Rama("CC", 0, 4, True, False, "propio", "fase 1: construcción en línea")
RAMAS_CON_CONSTRUCCION = ("D100", "P", "D100-texto", "R-texto", "D50")
RAMAS_FASE1 = ("CC",)
NUNCA_SE_RECORTAN = ("SC", "D100", "D100-texto", "R-texto", "SC_ig")
K_IG_MIN, K_IG_MAX = 4, 12


def k_ig(r: float) -> int:
    """K_ig = mín(12, máx(4, redondeo(4·r))) (§3.4). Redondeo = round half to even de Python (se declara)."""
    return int(min(K_IG_MAX, max(K_IG_MIN, round(4 * r))))


def config_de(rama: str, k_ig_valor: int | None = None) -> F.ConfigFrontera:
    r = RAMAS[rama]
    intentos = r.intentos
    if rama == "SC_ig":
        if k_ig_valor is None:
            raise ValueError("SC_ig necesita K_ig fijado (enmienda mecánica, §3.4)")
        intentos = int(k_ig_valor)
    return F.ConfigFrontera(rama, intentos=intentos, usa_cuaderno=r.invocable)


# ============================================================================== vigilancia del modelo (§3.5)


class CambioDeModelo(ProviderFatal):
    """El `model` devuelto por la API cambió respecto del registrado: se detiene la corrida."""


class VigiaModelo:
    def __init__(self, esperado: str | None = None, registro: Path | None = None):
        self.esperado, self.registro = esperado, registro
        self._lock = threading.Lock()

    def anotar(self, modelo_api: str | None) -> None:
        if not modelo_api:
            return
        with self._lock:
            if self.esperado is None:
                self.esperado = modelo_api
                if self.registro:
                    self.registro.write_text(modelo_api + "\n", encoding="utf-8")
            elif modelo_api != self.esperado:
                raise CambioDeModelo(f"la API devolvió el modelo {modelo_api!r} y la corrida está registrada con {self.esperado!r}")


# ============================================================================== el episodio v6


def _resumen(reg: dict) -> str:
    return K._resumen(reg)


def _tokens_de(uso: dict) -> dict:
    """Entrada total (incluye lecturas y escrituras de caché, como las cuenta gasto.py), salida (incluye el
    pensamiento) y lecturas de caché, para r de K_ig (§3.4)."""
    return {"entrada": int(uso.get("entrada", 0) or 0), "salida": int(uso.get("salida", 0) or 0),
            "cache": int(uso.get("cache", 0) or 0)}


def episodio_v6(t: dict, rama: str, cfg: F.ConfigFrontera, proveedor, lake, entradas: list[dict], carpeta: Path, ep_id: str,
                ref: str, sistema: str = SISTEMA_TEST, cuad: F.Cuaderno | None = None, lock_cuad=None,
                parar: threading.Event | None = None, vigia: K.Vigia | None = None, vigia_modelo: VigiaModelo | None = None) -> dict:
    """Un episodio sobre la tarea t en la rama dada.

    * Test (fase 2): `entradas` es el bloque CONGELADO de la celda (D100/P/D50: se declara en Lean y en la cabecera de
      cuaderno; D100-texto/R-texto: solo cabecera de pistas; SC/SC_ig: nada). Nada entra al bloque.
    * Fase 1 (CC en línea): `cuad` es el Cuaderno vivo de la construcción; `entradas` se ignora y se toma del cuaderno
      bajo cerrojo en cada llamada; los lemas aceptados entran con K._incorporar_cc.
    Misma lógica de intentos, turnos, EVAL, lemas locales, juicio y segundo testigo que la v5."""
    r = RAMAS[rama] if rama in RAMAS else None
    en_linea = cuad is not None
    invocable = en_linea or (r is not None and r.invocable)
    historia, locales = [], []
    intentos, turnos, llamadas = 0, cfg.turnos_exploracion, 0
    res = {"episodio": ep_id, "tarea": t["id"], "rama": rama, "config": cfg.nombre, "resuelto": False, "lemas_admitidos": [],
           "intentos": 0, "usd": 0.0, "tokens": {"entrada": 0, "salida": 0, "cache": 0}, "llamadas": 0,
           "llamadas_facturadas": 0, "fallos_proveedor": 0, "refusals": 0, "max_tokens": 0, "timeouts_lean": 0,
           "sin_salida_lean": 0, "modelos_api": [], "cita_bloque": []}
    lock = lock_cuad or threading.Lock()
    if en_linea:
        with lock:
            res["cuaderno_inicio"] = {"n": len(cuad.entradas), "hash": cuad.hash()}
    while intentos < cfg.intentos:
        if parar is not None and parar.is_set():
            res["interrumpido"] = True
            break
        if en_linea:
            with lock:
                entradas_vistas = list(cuad.entradas)
                persistente = lean_de_entradas(entradas_vistas)
                en_bloque = cuad.nombres()
                hash_cuad = cuad.hash()
        else:
            entradas_vistas = list(entradas)
            persistente = lean_de_entradas(entradas_vistas) if invocable else ""
            en_bloque = {d for e in entradas_vistas for d in e.get("declara", e["teoremas"])} if invocable else set()
            hash_cuad = ""
        contexto = "\n\n".join(x for x in [persistente] + [l["bloque"] for l in locales if not set(l["nombres"]) <= en_bloque] if x)
        prompt = construir_prompt(t, "CC" if en_linea else rama, entradas_vistas, locales, historia, cfg.intentos - intentos, turnos)
        try:
            texto, rechazo = complete_with_retries(proveedor, sistema, prompt, propagar_rechazo=True, dormir=DORMIR), None
        except Rechazo as e:
            texto, rechazo = None, str(e)
        llamadas += 1
        uso = getattr(proveedor, "ultimo_uso", None) or {}
        res["usd"] += float(uso.get("usd", 0) or 0)
        for k_, v_ in _tokens_de(uso).items():
            res["tokens"][k_] += v_
        if uso:
            res["llamadas_facturadas"] += 1
        if uso.get("modelo_api") and uso["modelo_api"] not in res["modelos_api"]:
            res["modelos_api"].append(uso["modelo_api"])
        if uso.get("stop_reason") == "max_tokens":
            res["max_tokens"] += 1
        K._registrar(carpeta / "llamadas.jsonl", {"episodio": ep_id, "llamada": llamadas, "prompt_sha": K._sha(prompt), "prompt": prompt,
                                                  "respuesta": texto, "rechazo": rechazo, "uso": uso,
                                                  "fecha": datetime.now().isoformat(timespec="seconds")})
        if vigia_modelo is not None:
            vigia_modelo.anotar(uso.get("modelo_api"))  # CambioDeModelo (ProviderFatal) detiene la corrida
        if texto is None and rechazo is None:
            res["fallos_proveedor"] += 1
        if rechazo is not None:
            res["refusals"] += 1
        if vigia is not None:
            vigia.anotar(texto is not None or rechazo is not None)
        if texto is None:
            intentos += 1
            historia.append({"tipo": "Intento", "n": intentos, "resumen": "REFUSAL o PROVIDER_ERROR"})
            continue
        rr = F.leer(texto)
        if rr["evals"] and not rr["lemas"] and not rr["prueba"]:
            if turnos <= 0:
                historia.append({"tipo": "Exploración", "resumen": "No quedan turnos de exploración: manda un intento."})
                intentos += 1
                continue
            turnos -= 1
            salidas = []
            for cod in rr["evals"][:cfg.max_evals_por_turno]:
                if motivo := K.prohibido_en(cod, extra=False, eval_=True):
                    salidas.append({"codigo": cod, "salida": f"RECHAZADO: {motivo}", "s": 0.0})
                else:
                    salidas += F.evaluar_evals(t, lake, contexto, [cod])
            res["timeouts_lean"] += sum(1 for s in salidas if s["salida"].startswith("TIEMPO AGOTADO"))
            K._registrar(carpeta / "intentos.jsonl", {"episodio": ep_id, "tipo": "exploracion", "evals": salidas})
            historia.append({"tipo": "Exploración", "resumen": "\n\n".join(
                F._md(s["codigo"], 1500) + "\nSalida:\n" + F._md(s["salida"], 2500) for s in salidas)})
            continue
        intentos += 1
        reg = {"episodio": ep_id, "tipo": "intento", "n": intentos, "llamada": llamadas, "reflexion": rr["reflexion"], "lemas": []}
        nombres_previos = en_bloque | {n for l in locales for n in l["nombres"]}
        for bloque in rr["lemas"][:cfg.max_lemas_por_intento]:
            if motivo := K.prohibido_en(bloque):
                rb = {"etiqueta": "FORBIDDEN", "motivo": motivo, "nombres": []}
            else:
                rb = F.admitir_bloque(t, lake, contexto, bloque, nombres_previos)
            if rb["etiqueta"] == "TIMEOUT":
                res["timeouts_lean"] += 1
            reg["lemas"].append({"bloque": bloque, "resultado": rb})
            if rb["etiqueta"] == "ACCEPTED":
                locales.append({"bloque": bloque.strip(), **rb})
                contexto = "\n\n".join(x for x in [contexto, bloque.strip()] if x)
                nombres_previos |= set(rb["nombres"])
                res["lemas_admitidos"] += rb["teoremas"]
                if en_linea:
                    reg["lemas"][-1]["cuaderno"] = K._incorporar_cc(t, lake, cuad, lock, hash_cuad, bloque, rb,
                                                                    origen=f"{t['id']}, {ep_id}, intento {intentos}", ep_id=ep_id)
                elif invocable:
                    reg["lemas"][-1]["cuaderno"] = "no incorporado: bloque congelado"
        if rr["prueba"]:
            pr = K.juzgar_principal(t, lake, contexto, rr["aux"], rr["prueba"], ref)
            reg["principal"] = {k_: v_ for k_, v_ in pr.items() if k_ != "archivo"}
            if pr["etiqueta"] == K.SIN_SALIDA:
                res["sin_salida_lean"] += 1
            if pr["etiqueta"] == "TIMEOUT":
                res["timeouts_lean"] += 1
            if pr["etiqueta"] == "ACCEPTED":
                t2 = K.segundo_testigo(t, lake, contexto, rr["aux"], rr["prueba"], ref)
                reg["segundo_testigo"] = t2["etiqueta"]
                if t2["etiqueta"] != "ACCEPTED":
                    reg["segundo_testigo_detalle"] = {k_: v_ for k_, v_ in t2.items() if k_ != "archivo"}
                    K._registrar(carpeta / "intentos.jsonl", reg)
                    raise K.CorridaDetenida(f"{t['id']}: el segundo testigo dio {t2['etiqueta']} sobre una prueba aceptada")
                (carpeta / "aceptadas").mkdir(exist_ok=True)
                (carpeta / "aceptadas" / f"{re.sub(r'[^A-Za-z0-9_.-]', '_', ep_id)[:150]}.lean").write_text(pr["archivo"], encoding="utf-8")
                res["cita_bloque"] = sorted({n for e in entradas_vistas for n in e["teoremas"]
                                             if re.search(rf"\b{re.escape(n)}\b", rr["prueba"] + "\n" + rr["aux"])})
        K._registrar(carpeta / "intentos.jsonl", reg)
        historia.append({"tipo": "Intento", "n": intentos, "resumen": _resumen(reg)})
        if reg.get("principal", {}).get("etiqueta") == "ACCEPTED":
            res["resuelto"] = True
            break
    if en_linea:
        with lock:
            res["cuaderno_fin"] = {"n": len(cuad.entradas), "hash": cuad.hash()}
    res.update({"intentos": intentos, "llamadas": llamadas, "usd": round(res["usd"], 6), "k": cfg.intentos})
    return res


# ============================================================================== proveedor seco con «facturación» simulada


class ProveedorSecoV6:
    """Sin API. Como K.ProveedorSeco (una exploración, un lema verdadero, dos pruebas que no sirven) pero con un
    `ultimo_uso` como el de la API (tokens, usd, modelo_api, stop_reason), para probar ITT, K_ig, la proyección de
    gasto y la vigilancia del modelo sin gastar un centavo. `fallar_en` simula llamadas sin factura."""
    model = "seco"

    def __init__(self, modelo_api: str = "seco-1", usd_por_llamada: float = 0.001, fallar_en: set[int] | None = None,
                 cambiar_modelo_en: int | None = None, libro=None, fase: str = "", resolver: bool = False, tope_usd: float | None = None):
        self.n, self.modelo_api, self.usd, self.fallar_en = 0, modelo_api, usd_por_llamada, set(fallar_en or ())
        self.cambiar_modelo_en, self.libro, self.fase, self.resolver = cambiar_modelo_en, libro, fase, resolver
        self.tope_usd, self.gastado = tope_usd, 0.0  # tope duro simulado, como el del libro (GastoExcedido)
        self._local = threading.local()
        self._lock = threading.Lock()
        self._corrida_base = "seco"

    @property
    def corrida(self) -> str:
        return getattr(self._local, "celda", None) or self._corrida_base

    def celda(self, c_id):
        self._local.celda = c_id

    @property
    def ultimo_uso(self):
        return getattr(self._local, "uso", None)

    def complete(self, system: str, user: str) -> str:
        with self._lock:
            self.n += 1
            n = self.n
        self._local.uso = None
        if n in self.fallar_en:
            raise RuntimeError("simulado: el proveedor no respondió (error no transitorio: sin reintento)")
        with self._lock:
            if self.tope_usd is not None and self.gastado + self.usd > self.tope_usd:
                from .gasto import GastoExcedido
                raise GastoExcedido(f"tope simulado de {self.tope_usd} USD")
            self.gastado += self.usd
        modelo = self.modelo_api if (self.cambiar_modelo_en is None or n < self.cambiar_modelo_en) else self.modelo_api + "-nuevo"
        uso = {"entrada": 1000 + 10 * (len(user) // 100), "cache": 500, "cache_escritura": 0, "salida": 300, "razonamiento": 100,
               "usd": self.usd, "modelo_api": modelo, "respuesta_id": f"seco-{n}", "stop_reason": "end_turn"}
        if self.libro is not None:  # simula el libro real: una línea por llamada, con la celda en `corrida`
            from .gasto import PRECIOS
            PRECIOS.setdefault("claude-haiku-5-5", (0.10, 0.10, 0.50))
            self.libro.registrar("claude-haiku-5-5", self.fase, self.corrida,
                                 {k: v for k, v in uso.items() if k in ("entrada", "cache", "cache_escritura", "salida", "razonamiento")})
        self._local.uso = uso
        if n % 4 == 1:
            return "EVAL: <<<\n#eval (2 + 2 : Nat)\n>>>"
        if n % 4 == 2:
            return "LEMA: <<<\ntheorem cu_seco : (2 : Nat) + 2 = 4 := by decide\n>>>\nPRUEBA: <<<\n" + ("decide" if self.resolver else "exact absurd rfl rfl") + "\n>>>"
        return "REFLEXION: <<< ensayo en seco >>>\nPRUEBA: <<<\nexact absurd rfl rfl\n>>>"


def vista(entradas: list[dict]):
    return types.SimpleNamespace(entradas=entradas)
