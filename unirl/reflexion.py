"""Etapa 5 de PLAN_rl_verbal.md: el episodio con reflexión (estilo Reflexion) sobre un peldaño del corpus.

Un episodio tiene hasta K intentos. En cada llamada el modelo responde, en un solo mensaje, con uno de:
  * CONSULTAS: <<< buscar: patrón | hecho: nombre | metodo: nombre >>>  (sin PROOF) → turno de consulta: el juez ejecuta
    hasta MAX_CONSULTAS_POR_LOTE consultas en el contexto del peldaño y devuelve los resultados; no gasta intento, pero
    sí una llamada, y hay un tope de turnos por episodio;
  * [REFLEXION: <<< … >>>] [LEMMAS: <<< … >>>] PROOF: <<< … >>>  → intento: el martillo cierra las marcas `by martillo`
    (en serie), el juez compila y r_V se calcula (solo métrica).
Tras un intento fallido el modelo ve los errores del kernel y las marcas que el martillo no cerró, y escribe su
reflexión junto con la prueba nueva (una sola llamada). Todo se registra en JSONL, llamada por llamada.
La verdad la decide el kernel; los pesos del modelo no cambian.
"""

from __future__ import annotations

import json
import re
import threading
import time
from dataclasses import dataclass
from pathlib import Path

from . import martillo as M
from .cuaderno import hash_texto
from .gd_isabelle import TheoremVerifier, fallo_de_biblioteca
from .loop import ProviderFatal, complete_with_retries
from .recompensa import LineaBaseDesactualizada, recompensa, resueltos_por_martillo

MAX_REFLEXION_PALABRAS = 150
MAX_RESPUESTA_REGISTRO = 30000
_cerrojo_registro = threading.Lock()

SISTEMA = """Eres un matemático que escribe demostraciones en Isabelle/HOL (no en Lean: la sintaxis y los nombres de \
Lean y Mathlib no existen aquí). Un verificador independiente, el kernel de Isabelle, decide si tu demostración es \
correcta; tú nunca lo afirmas. Escribe demostraciones inteligibles para una persona: Isar estructurado \
(proof … qed, have/show, also/finally, obtain), un paso por idea matemática, las hipótesis citadas por su nombre, y \
un comentario breve en español (* … *) antes de cada paso no trivial."""


@dataclass
class Config:
    nombre: str
    intentos: int = 4
    turnos_consulta: int = 2
    glosario: bool = True
    consulta: bool = True
    reflexion: bool = True
    partes: tuple[str, ...] = ()  # del cuaderno: "errores", "lemas", "estrategias"
    pedir_lemas: bool = False  # ronda 2 (27 sep 2026): en el entrenamiento se piden de 1 a 3 lemas reutilizables por intento


CONFIGS = {
    "B0": Config("B0", intentos=1, turnos_consulta=0, glosario=False, consulta=False, reflexion=False),
    "B": Config("B", intentos=1, turnos_consulta=2, reflexion=False),
    "C": Config("C"),
    "D": Config("D", partes=("errores",)),
    # E redefinida el 26 sep 2026, antes de lanzar la primera ronda (decisión (b) de Carlos): solo los lemas
    # certificados por el kernel, sin notas de error ni estrategias. Ninguna corrida de E anterior existe.
    "E": Config("E", partes=("lemas",)),
    # F (entrenamiento del cuaderno): desde la ronda 2 pide lemas reutilizables; en la ronda 1 los lemas solo se
    # cosechaban de los LEMMAS que el modelo escribía por iniciativa propia (2 de 10 pruebas aceptadas; 1 admitido)
    "F": Config("F", partes=("errores", "lemas", "estrategias"), pedir_lemas=True),
    # comparación entre modelos con el mismo presupuesto (PLAN §9.4): K = 3 y un turno de consulta
    "C3": Config("C3", intentos=3, turnos_consulta=1),
    "E3": Config("E3", intentos=3, turnos_consulta=1, partes=("lemas",)),  # E con K = 3: misma redefinición
}


# ----------------------------------------------------------------------------- respuesta del modelo


def _bloque(nombre: str, texto: str) -> str | None:
    m = re.search(rf"\b{nombre}:\s*<<<(.*?)>>>(?!>)", texto or "", re.S)
    return m.group(1).strip() if m else None


_ROTULOS = r"(?:REFLEXI[OÓ]N|LEMMAS|PROOF|CONSULTAS)"


def _suelto(nombre: str, texto: str) -> str | None:
    """Respaldo cuando el modelo olvida los delimitadores: `NOMBRE:` seguido del texto hasta el siguiente rótulo
    (al inicio de una línea) o el final. Solo se usa si no hay bloque `NOMBRE: <<< … >>>`."""
    m = re.search(rf"(?m)^\s*{nombre}:[ \t]*(?!\s*<<<)(.*?)(?=^\s*{_ROTULOS}:|\Z)", texto or "", re.S)
    return m.group(1).strip().removeprefix("```isabelle").removeprefix("```").removesuffix("```").strip() if m else None


def leer_respuesta(juez: TheoremVerifier, texto: str) -> dict:
    """{proof, lemmas, reflexion, consultas: [{tipo, texto}], formato_estricto} de la respuesta del modelo. Si faltan los
    delimitadores <<< >>>, se lee el bloque suelto (24 sep, humo: Luna escribió así una prueba correcta y la perdió)."""
    p = juez.parse(texto)
    estricto = True
    if not p["proof"] and (suelto := _suelto("PROOF", texto)):
        from .verifiers import IsabelleVerifier
        p["proof"], estricto = IsabelleVerifier._close_symbol(suelto), False
    if not p["lemmas"] and (suelto := _suelto("LEMMAS", texto)):
        from .verifiers import IsabelleVerifier
        p["lemmas"], estricto = IsabelleVerifier._close_symbol(suelto), False
    consultas = []
    bloque = _bloque("CONSULTAS", texto)
    if bloque:
        for linea in re.split(r"\n|\s\|\s", bloque):
            m = re.match(r"\s*-?\s*(buscar|hecho|metodo|método)\s*:\s*(.+?)\s*$", linea)
            if m:
                consultas.append({"tipo": m.group(1).replace("método", "metodo"), "texto": m.group(2)})
            elif linea.strip():
                consultas.append({"tipo": "?", "texto": linea.strip()})
    reflexion = (_bloque("REFLEXION", texto) or _bloque("REFLEXIÓN", texto) or _suelto("REFLEXION", texto)
                 or _suelto("REFLEXIÓN", texto) or "")
    palabras = reflexion.split()
    if len(palabras) > MAX_REFLEXION_PALABRAS:
        reflexion = " ".join(palabras[:MAX_REFLEXION_PALABRAS]) + " […]"
    return {"proof": p["proof"], "lemmas": p["lemmas"], "reflexion": reflexion, "consultas": consultas,
            "formato_estricto": estricto}


# ----------------------------------------------------------------------------- prompt


def describir(spec: dict, cfg: Config, turnos_restantes: int, intento: int) -> str:
    fixes = " ".join(spec["fixes"].split())
    lineas = [
        f"TEOREMA {spec['id']} (método: {spec['metodo']}): {spec['statement_es']}",
        "",
        f"Teoría: imports {spec['imports']} (Complex_Main y análisis real: derivadas, continuidad, límites, sumas).",
    ]
    if spec["prelude"].strip():
        lineas += ["", "Preludio congelado (definiciones del método, antes del contexto):", spec["prelude"].strip()]
    lineas += [
        "", "Contexto congelado:", f"  fixes {fixes}", f"  assumes {spec['assumes']}",
        "", "Enunciado a demostrar dentro de ese contexto:", f"  theorem isarl_target: \"{spec['concl']}\"",
        "",
        "Formato de un INTENTO:",
        "  PROOF: <<< … >>>  (obligatorio) el texto que va justo después de esa línea: `proof … qed`, `by …`, `apply … done`.",
        "  LEMMAS: <<< lemma nombre: \"…\" <prueba> >>>  (opcional) lemas auxiliares con su prueba completa; se compilan en el",
        "     mismo contexto antes del teorema. Cita las hipótesis por su etiqueta (las que aparecen en assumes).",
    ]
    if cfg.pedir_lemas:
        lineas += [
            "  En este teorema (entrenamiento del cuaderno) incluye en LEMMAS de 1 a 3 lemas auxiliares REUTILIZABLES en otros",
            "     teoremas: enunciados generales, sin las constantes del preludio si puedes, cada uno con su prueba completa y",
            "     con un nombre que empiece por cu_. El kernel los verifica junto con tu intento; los verificados entran al cuaderno.",
        ]
    if cfg.reflexion and intento > 1:
        lineas.append(f"  REFLEXION: <<< … >>>  (obligatorio desde el segundo intento) qué falló y qué cambias, en "
                      f"español, máximo {MAX_REFLEXION_PALABRAS} palabras.")
    lineas += [
        "",
        "El martillo: puedes cerrar un paso con `by martillo`. El juez intenta cerrarlo con try0 (5 s) y Sledgehammer (60 s)",
        "y pega la línea que encuentre; si no la encuentra, verás cuál marca quedó abierta. Úsalo para pasos rutinarios:",
        "la estructura de la demostración la pones tú. Una prueba que sea solo `by martillo`, o una sola línea smt/metis con",
        "muchos hechos, puede pasar el kernel pero no cuenta como demostración inteligible.",
    ]
    if cfg.consulta and turnos_restantes > 0:
        lineas += [
            "",
            f"CONSULTAS (te quedan {turnos_restantes} turnos; no gastan intentos): responde SOLO con",
            "  CONSULTAS: <<< buscar: <patrón o name: parte_del_nombre> | hecho: <nombre> | metodo: <nombre> >>>",
            f"  (hasta {M.MAX_CONSULTAS_POR_LOTE} por turno, separadas por '|' o en líneas) y sin PROOF. `buscar` usa find_theorems en",
            "  el contexto de este teorema (p. ej. `buscar: name: mono` o `buscar: \"_ * _ \\<le> _ * _\"`); `hecho` y `metodo`",
            "  dicen si un nombre existe. Si mandas PROOF, el mensaje es un intento y las consultas se ignoran.",
        ]
    lineas += [
        "",
        "Reglas (un filtro las comprueba antes de compilar): sin sorry ni oops; sin definiciones, notación, declare, ML ni",
        "[[ ]]; sin cartuchos (\\<open>…\\<close>, ‹…›) ni comillas invertidas; símbolos en ASCII de Isabelle (\\<le>, \\<bar>,",
        "\\<Longrightarrow>, \\<And>, \\<^sup>2); los comentarios van entre (* y *). Tus lemas no pueden llamarse como las",
        "etiquetas de las hipótesis, las constantes del preludio ni isarl*.",
    ]
    return "\n".join(lineas)


def construir_prompt(spec: dict, cfg: Config, glosario: str, cuaderno_txt: str, consultas_hechas: list[dict],
                     historia: list[dict], turnos_restantes: int, intento: int) -> str:
    partes = [describir(spec, cfg, turnos_restantes, intento)]
    if cfg.glosario and glosario:
        partes.append("ERRORES FRECUENTES DE LEAN EN ISABELLE (cada nombre se comprobó en Isabelle2025):\n" + glosario)
    if cuaderno_txt:
        partes.append("CUADERNO (de episodios anteriores en otros teoremas; solo entra lo que el juez verificó):\n" + cuaderno_txt)
    if consultas_hechas:
        partes.append("RESULTADOS DE TUS CONSULTAS:\n" + "\n".join(_render_consulta(c) for c in consultas_hechas))
    if historia:
        partes.append(f"TUS INTENTOS ANTERIORES ({len(historia)} de {cfg.intentos}):")
        for h in historia:
            s = f"--- intento {h['intento']}"
            if h.get("reflexion"):
                s += f"\nreflexión: {h['reflexion']}"
            s += f"\nPROOF:\n{h['proof'][:3000]}"
            if h.get("lemmas"):
                s += f"\nLEMMAS:\n{h['lemmas'][:2000]}"
            s += f"\nresultado: {h['feedback'][:2500]}"
            partes.append(s)
        partes.append("Escribe ahora REFLEXION y la PROOF corregida." if cfg.reflexion else "Escribe ahora la PROOF corregida.")
    elif cfg.consulta and turnos_restantes > 0:
        partes.append("Escribe tu demostración (o, si te sirve, haz primero CONSULTAS).")
    else:
        partes.append("Escribe tu demostración.")
    return "\n\n".join(partes)


def _render_consulta(r: dict) -> str:
    cab = f"- {r.get('tipo')}: {r.get('consulta')}"
    if r.get("error"):
        return cab + f" → error: {r['error']}"
    if "existe" in r:
        return cab + (" → existe" if r["existe"] else " → NO existe")
    res = r.get("resultados") or []
    cuerpo = "\n".join(f"    {x['nombre']}: {x['enunciado'][:220]}" for x in res[:12])
    total = r.get("total")
    return cab + f" → {len(res)} de {total if total is not None else '?'} resultados" + (f"\n{cuerpo}" if cuerpo else "")


# ----------------------------------------------------------------------------- evaluación de un intento


def evaluar_intento(juez: TheoremVerifier, spec: dict, propuesta: dict, biblioteca: str, hash_bib: str,
                    resueltos: set[str], cache: M.Cache) -> dict:
    """Martillo por pasos + juez + r_V. Devuelve el registro del intento (sin la parte del modelo)."""
    reloj = M.Reloj()
    rv = M.martillo_en_pasos(juez, propuesta["proof"], cuaderno_hash=hash_bib, cache=cache, lemas=propuesta["lemmas"],
                             biblioteca=biblioteca)
    o = rv["outcome"]
    if o is not None:
        etiqueta, raw = o.outcome_label, o.raw
        feedback = juez.feedback({"proof": rv["prueba_final"], "lemmas": propuesta["lemmas"]}, o)
        juez_s = round(o.cost_s, 1)
    else:  # alguna marca `by martillo` no cerró: no hubo pasada 2
        etiqueta, raw, juez_s = "PROOF_FAILED", {"errors": rv["errores"], "verified_lemmas": []}, 0.0
        abiertas = rv.get("marcas_abiertas") or []
        feedback = (f"PROOF_FAILED: el martillo no cerró {len(abiertas)} de {rv['marcas']} marcas `by martillo` "
                    f"(número {', '.join(map(str, abiertas))} en orden de aparición)")
        metas = {int(p["k"]): p["meta"] for p in rv["pasos"]}
        for k in abiertas[:4]:
            if k in metas:
                feedback += f"\n  marca {k}, meta: {metas[k][:400]}"
        if rv["errores"]:
            feedback += "\nErrores de Isabelle en la pasada de búsqueda (literales):\n" + "\n".join(rv["errores"][:10])
    r = recompensa(spec["id"], etiqueta, propuesta["proof"], rv["prueba_final"], rv["marcas"], rv["cerradas"], resueltos)
    return {"etiqueta": etiqueta, "aceptada": etiqueta == "ACCEPTED", "feedback": feedback, "r_V": r["r"],
            "motivo_r": r["motivo"], "legibilidad": r["legibilidad"], "marcas": rv["marcas"], "cerradas": rv["cerradas"],
            "lineas_martillo": [p.get("linea") for p in rv["pasos"]], "prueba_final": rv["prueba_final"],
            "juez_s": juez_s, "martillo_s": rv.get("martillo_s", 0.0), "espera_candado_s": rv.get("espera_candado_s", 0.0),
            "suspension_s": max(rv.get("suspension_s") or 0.0, reloj.suspension_s()),
            "lemas_verificados": raw.get("verified_lemmas") or [], "errores": (raw.get("errors") or [])[:20],
            # 30 sep 2026: el intento no se pudo juzgar porque un lema del cuaderno no compiló en este peldaño
            "biblioteca_fallo": bool(raw.get("biblioteca_fallo")) or fallo_de_biblioteca(rv.get("errores") or []),
            "veredicto_meta": raw.get("veredicto") or juez.metadatos(), "intento_s": round(reloj.ms() / 1000, 1)}


# ----------------------------------------------------------------------------- episodio


def escribir(ruta: Path, registro: dict) -> None:
    with _cerrojo_registro:
        ruta.parent.mkdir(parents=True, exist_ok=True)
        with ruta.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(registro, ensure_ascii=False, default=str) + "\n")


def episodio(spec: dict, cfg: Config, proveedor, registro: Path, meta: dict, cuaderno=None, cache: M.Cache | None = None,
             resueltos: set[str] | None = None, verbose: bool = True) -> dict:
    """Un episodio sobre un peldaño aprobado. `cuaderno`: el objeto Cuaderno (vivo en train, congelado en evaluación)
    o None. `resueltos`: la línea base del martillo con esos lemas (si no se da, se lee; sin ella no hay r_V)."""
    juez = TheoremVerifier.desde_corpus(spec["id"])
    cache = cache or M.Cache()
    sel = cuaderno.recuperar(spec, cfg.partes) if (cuaderno is not None and cfg.partes) else {"errores": [], "lemas": [], "estrategias": []}
    biblioteca = cuaderno.biblioteca(sel) if cuaderno is not None else ""
    hash_bib = hash_texto(biblioteca)  # clave de la caché del martillo: lo que cambia lo que puede cerrar
    if resueltos is None:
        clave = cuaderno.hash_lemas() if (cuaderno is not None and "lemas" in cfg.partes) else ""
        resueltos = resueltos_por_martillo(clave, [spec["id"]])
    glosario = cuaderno.glosario_compacto() if cuaderno is not None else _glosario_base()
    cuaderno_txt = cuaderno.render(sel) if cuaderno is not None else ""
    ep_id = meta.get("episodio_id", f"{spec['id']}#1")
    base = {**meta, "peldano": spec["id"], "metodo": spec["metodo"], "split": spec["split"], "dificultad": spec["dificultad"],
            "version": spec.get("version"), "config": cfg.nombre, "episodio_id": ep_id,
            "cuaderno_hash": getattr(cuaderno, "hash", lambda: "")() if cuaderno is not None else "",
            "biblioteca_hash": hash_bib, "lemas_mostrados": [l["nombre"] for l in sel["lemas"]],
            "lemas_biblioteca": [l["nombre"] for l in sel.get("biblioteca", sel["lemas"])],  # 30 sep: con dependencias
            "estrategias_mostradas": [e["texto"][:80] for e in sel["estrategias"]],
            "errores_mostrados": [e.get("id") for e in sel["errores"]]}
    historia, consultas_hechas = [], []
    turnos = cfg.turnos_consulta if cfg.consulta else 0
    intento, llamada, aceptado, exito_en = 0, 0, False, None
    mejor_r, usd = 0.0, 0.0
    while intento < cfg.intentos:
        prompt = construir_prompt(spec, cfg, glosario, cuaderno_txt, consultas_hechas, historia, turnos, intento + 1)
        t = time.monotonic()
        texto = complete_with_retries(proveedor, SISTEMA, prompt, verbose=verbose)
        llm_s = round(time.monotonic() - t, 1)
        llamada += 1
        uso = getattr(proveedor, "ultimo_uso", None)
        usd += (uso or {}).get("usd", 0.0)
        reg = {**base, "llamada": llamada, "prompt_chars": len(prompt), "llm_s": llm_s, "uso": uso,
               "fecha": time.strftime("%Y-%m-%dT%H:%M:%S")}
        if texto is None:
            intento += 1
            historia.append({"intento": intento, "proof": "", "feedback": "PROVIDER_ERROR: la llamada al modelo falló; "
                             "este intento no se juzgó."})
            escribir(registro, {**reg, "tipo": "intento", "intento": intento, "etiqueta": "PROVIDER_ERROR", "r_V": 0.0})
            continue
        r = leer_respuesta(juez, texto)
        if not r["proof"] and r["consultas"] and turnos > 0:
            turnos -= 1
            t = time.monotonic()
            res = M.consultar(juez, r["consultas"], biblioteca=biblioteca)
            consultas_hechas += res
            escribir(registro, {**reg, "tipo": "consulta", "consultas": r["consultas"], "resultados": res,
                                "consulta_s": round(time.monotonic() - t, 1), "respuesta": texto[:MAX_RESPUESTA_REGISTRO]})
            if verbose:
                print(f"  [{spec['id']} {cfg.nombre}] consulta: {len(r['consultas'])} ({turnos} turnos restantes)", flush=True)
            continue
        intento += 1
        if not r["proof"]:
            fb = ("INVALID_PROPOSAL: falta PROOF: <<< … >>>" + (" (ya no quedan turnos de consulta)" if r["consultas"] else ""))
            historia.append({"intento": intento, "proof": "", "reflexion": r["reflexion"], "feedback": fb})
            escribir(registro, {**reg, "tipo": "intento", "intento": intento, "etiqueta": "INVALID_PROPOSAL", "r_V": 0.0,
                                "feedback": fb, "reflexion": r["reflexion"], "respuesta": texto[:MAX_RESPUESTA_REGISTRO]})
            continue
        ev = evaluar_intento(juez, spec, r, biblioteca, hash_bib, resueltos, cache)
        mejor_r = max(mejor_r, ev["r_V"])
        historia.append({"intento": intento, "proof": r["proof"], "lemmas": r["lemmas"], "reflexion": r["reflexion"],
                         "feedback": ev["feedback"]})
        escribir(registro, {**reg, "tipo": "intento", "intento": intento, "proof": r["proof"], "lemmas": r["lemmas"],
                            "reflexion": r["reflexion"], "formato_estricto": r["formato_estricto"],
                            "respuesta": texto[:MAX_RESPUESTA_REGISTRO], **ev})
        if verbose:
            print(f"  [{spec['id']} {cfg.nombre}] intento {intento}: {ev['etiqueta']} r_V={ev['r_V']} "
                  f"(marcas {ev['cerradas']}/{ev['marcas']}, llm {llm_s} s, juez {ev['juez_s']} s)", flush=True)
        if ev["aceptada"]:
            aceptado, exito_en = True, intento
            break
    return {**base, "aceptado": aceptado, "intento_exito": exito_en, "intentos": intento, "llamadas": llamada,
            "consultas": len(consultas_hechas), "r_V_max": mejor_r, "usd": round(usd, 6),
            "historia": historia, "seleccion": sel}


def _glosario_base() -> str:
    from .cuaderno import Cuaderno
    return Cuaderno().glosario_compacto()
