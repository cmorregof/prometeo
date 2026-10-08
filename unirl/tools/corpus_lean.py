"""Genera el corpus `guardarrailes` (juez de Lean) a partir de `VelveteenRisk.lean`.

El archivo fuente es el modelo verificado de la puerta de riesgo de VelveteenTrade (repo Alpaca/VelveteenTrade,
`verification/lean/`, commit 9e3614d), copiado en `corpus/curado/guardarrailes/fuente_VelveteenRisk.lean`.

Cada teorema del archivo se vuelve un peldaño:
  * contexto  = todo el archivo antes del teorema (definiciones y lemas anteriores, con sus pruebas);
  * enunciado = el teorema hasta su `:=` (lo que el agente debe copiar tal cual);
  * la prueba de referencia va a `tests/unirl/fixtures/pruebas_privadas/guardarrailes/<id>.lean` (no versionada).
Además:
  * `g_cycle_safe_directo`: `cycle_safe` con un contexto de solo definiciones (sin la escalera de lemas);
  * cuatro CONTROLES FALSOS (`verdadero: false`): enunciados que no tienen prueba. Su refutación en Lean también va a
    las pruebas privadas y las pruebas de `tests/unirl/test_juez_lean.py` comprueban que compila: así la falsedad
    no depende de nuestra palabra. Un juez que acepte una «prueba» de un control falso tiene un hueco.

Todos los peldaños nacen en estado `pendiente_revision`: solo Carlos los aprueba (corpus.NoAprobado si no).

Uso:
  python -m unirl.tools.corpus_lean            # escribe los .json y las pruebas privadas
  python -m unirl.tools.corpus_lean --revisar  # solo dice qué cambiaría
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
DIR = BASE / "corpus" / "curado" / "guardarrailes"
FUENTE = DIR / "fuente_VelveteenRisk.lean"
PRIVADAS = BASE / "tests" / "unirl" / "fixtures" / "pruebas_privadas" / "guardarrailes"
TOOLCHAIN = "leanprover/lean4:v4.34.1"
ORIGEN = "VelveteenTrade, verification/lean/VelveteenRisk.lean (commit 9e3614d, 8 oct 2026)"
HASH_FIELDS = ("contexto", "enunciado", "toolchain")

ANCLAS = ("/-!", "/--", "namespace ", "end ", "structure ", "inductive ", "def ", "theorem ", "omit ", "example",
          "variable ")

# id → (dificultad 1–5, enunciado en español). Las dificultades son una estimación a priori, no una medición.
TEOREMAS = {
    "roundQty_spec": (2, "El redondeo de cantidades de risk.py (piso a 3 decimales, nunca negativo) redondea hacia abajo."),
    "stopPrice_ge": (1, "El stop redondeado hacia arriba al centavo nunca queda por debajo de precio − distancia."),
    "mul_le_of_le_div": (1, "Si a ≤ b/p con p > 0, entonces a·p ≤ b."),
    "div_lt_of_lt_mul": (1, "Si b < a·p con p > 0, entonces b/p < a."),
    "trim_spec": (3, "Cada tope solo achica la cantidad y, si queda positiva, la deja dentro de ese tope."),
    "cap_mono": (1, "Si una cantidad cabe bajo un tope, cualquier cantidad menor también cabe."),
    "buySize_caps": (3, "El tamaño final de una compra respeta a la vez los topes de posición, bruto y sector."),
    "buySize_risk": (3, "El tamaño de una compra por la distancia al stop no supera el presupuesto de riesgo."),
    "hold_never_orders": (1, "HOLD nunca produce una orden ni cambia la cartera."),
    "sell_only_closes": (2, "Una venta aprobada cierra una posición existente por exactamente la cantidad del bróker."),
    "buy_risk_le_budget": (3, "Una compra aprobada arriesga a lo sumo equity × riesgo × convicción/5 hasta su stop."),
    "stop_loss_le_budget": (2, "Si se sale en el stop congelado o por encima, la pérdida queda dentro del presupuesto."),
    "step_preserves": (4, "Una decisión cualquiera de la puerta preserva el invariante de topes."),
    "cycle_safe": (1, "Para cualquier lista de propuestas, una cartera que empieza dentro de sus topes termina dentro."),
    "velveteen_cycle_safe": (1, "cycle_safe con el redondeo real de risk.py."),
    "demoStart_inv": (2, "La cartera de ejemplo (7 posiciones al 68,6 %) cumple el invariante."),
    "old_gate_unsafe": (3, "La puerta anterior al arreglo viola el invariante: existe un contraejemplo."),
}

# Controles falsos: (id, dificultad, enunciado Lean, enunciado en español, refutación privada en Lean)
FALSOS = [
    ("f_viejo_ciclo", 3,
     "theorem f_viejo_ciclo (ds : List (Proposal Nat)) {st : Shadow Nat Nat}\n"
     "    (hinv : Inv 100000 demoLimits st) :\n"
     "    Inv 100000 demoLimits (runOld roundQty 100000 demoLimits id st st ds)",
     "La puerta ANTERIOR al arreglo también preserva el invariante (falso: es el error que se corrigió).",
     "theorem refuta_f_viejo_ciclo :\n"
     "    ¬ (∀ (ds : List (Proposal Nat)) (st : Shadow Nat Nat), Inv 100000 demoLimits st →\n"
     "        Inv 100000 demoLimits (runOld roundQty 100000 demoLimits id st st ds)) := by\n"
     "  intro h\n"
     "  obtain ⟨st, ds, h1, h2⟩ := old_gate_unsafe\n"
     "  exact h2 (h ds st h1)\n"),
    ("f_ciclo_sin_hipotesis", 2,
     "theorem f_ciclo_sin_hipotesis {rq : Rat → Rat} (hrq : RoundDown rq) {E : Rat} {L : Limits}\n"
     "    {sec : σ → κ} (ds : List (Proposal σ)) (st : Shadow σ κ) :\n"
     "    Inv E L (run rq E L sec st ds)",
     "cycle_safe sin la hipótesis de que la cartera empieza dentro de sus topes (falso).",
     "theorem refuta_f_ciclo_sin_hipotesis :\n"
     "    ¬ (∀ (ds : List (Proposal Nat)) (st : Shadow Nat Nat),\n"
     "        Inv 100000 demoLimits (run roundQty 100000 demoLimits (id : Nat → Nat) st ds)) := by\n"
     "  intro h\n"
     "  have := (h [] { demoStart with gross := 1000000 }).gross_le\n"
     "  revert this\n"
     "  decide +kernel\n"),
    ("f_trim_sin_signo", 2,
     "theorem f_trim_sin_signo {rq : Rat → Rat} (hrq : RoundDown rq) {cap base p q : Rat}\n"
     "    (hp : 0 < p) :\n"
     "    0 ≤ trim rq cap base p q ∧ trim rq cap base p q ≤ q ∧\n"
     "    (0 < trim rq cap base p q → base + trim rq cap base p q * p ≤ cap)",
     "trim_spec sin la hipótesis 0 ≤ q (falso: una cantidad negativa pasa sin recortar).",
     "theorem refuta_f_trim_sin_signo :\n"
     "    ¬ (∀ cap base p q : Rat, 0 < p → 0 ≤ trim roundQty cap base p q) := by\n"
     "  intro h\n"
     "  have := h 10 0 1 (-1) (by decide +kernel)\n"
     "  revert this\n"
     "  decide +kernel\n"),
    ("f_stop_con_gap", 2,
     "theorem f_stop_con_gap {q p sd budget exit : Rat} (hq : 0 ≤ q)\n"
     "    (hrisk : q * sd ≤ budget) :\n"
     "    q * (p - exit) ≤ budget",
     "La pérdida queda dentro del presupuesto aunque la salida atraviese el stop (falso: un gap la rompe).",
     "theorem refuta_f_stop_con_gap :\n"
     "    ¬ (∀ q p sd budget exit : Rat, 0 ≤ q → q * sd ≤ budget → q * (p - exit) ≤ budget) := by\n"
     "  intro h\n"
     "  have := h 1 100 1 1 0 (by decide +kernel) (by decide +kernel)\n"
     "  revert this\n"
     "  decide +kernel\n"),
]


def huella(e: dict) -> str:
    return hashlib.sha256(json.dumps({k: e.get(k, "") for k in HASH_FIELDS}, ensure_ascii=False,
                                     sort_keys=True).encode()).hexdigest()[:16]


def _fin_firma(texto: str, desde: int) -> int:
    """Índice del `:=` que cierra la firma: el primero a profundidad 0 de paréntesis desde `desde`."""
    prof, i = 0, desde
    while i < len(texto) - 1:
        c = texto[i]
        if c in "([{⟨":
            prof += 1
        elif c in ")]}⟩":
            prof -= 1
        elif c == ":" and texto[i + 1] == "=" and prof == 0:
            return i
        i += 1
    raise ValueError("firma sin `:=`")


def items(lineas: list[str]) -> list[dict]:
    """Declaraciones de nivel superior: {tipo, nombre, ini, decl, fin} en índices de línea. `ini` incluye el `omit`
    y el docstring que la preceden; `decl` es la línea de `theorem`/`def`/…; `fin` es exclusivo."""
    anclas = [i for i, l in enumerate(lineas) if l.startswith(ANCLAS)]
    out, usados = [], set()
    for k, i in enumerate(anclas):
        l = lineas[i]
        if not l.startswith(("theorem ", "def ", "structure ", "inductive ", "example")):
            continue
        ini = i
        j = k - 1
        while j >= 0 and anclas[j] not in usados and lineas[anclas[j]].startswith(("/--", "omit ")):
            ini = anclas[j]
            j -= 1
        # el siguiente ítem empieza en su omit o docstring: el fin es la primera ancla posterior
        fin = anclas[k + 1] if k + 1 < len(anclas) else len(lineas)
        usados.update(range(ini, i + 1))
        tipo = l.split()[0]
        nombre = l.split()[1] if tipo != "example" else None
        out.append({"tipo": tipo, "nombre": nombre, "ini": ini, "decl": i, "fin": fin})
    return out


def _docstring(lineas: list[str], it: dict) -> str:
    bloque = "\n".join(lineas[it["ini"]:it["decl"]])
    m = re.search(r"/--(.*?)-/", bloque, re.S)
    return " ".join(m.group(1).split()) if m else ""


def _peldano(id_: str, nombre: str, contexto: str, enunciado: str, dificultad: int, es: str, verdadero: bool,
             descripcion_en: str = "", notas: str = "") -> dict:
    e = {"id": id_, "name": id_, "kind": "lean_theorem", "metodo": "guardarrailes", "peldano": nombre,
         "split": "test", "estado": "pendiente_revision", "dificultad": str(dificultad), "fuente": ORIGEN,
         "dependencias": [], "verdadero": verdadero, "nombre_lean": nombre, "toolchain": TOOLCHAIN,
         "statement_es": es, "descripcion_en": descripcion_en, "notas": notas,
         "redactado_por": "Claude (Opus 5.5), 8 oct 2026", "aprobacion": None,
         "contexto": contexto, "enunciado": enunciado}
    e["frozen_hash"] = huella(e)
    return e


def generar(fuente: Path = FUENTE) -> tuple[list[dict], dict[str, str]]:
    """(peldaños, pruebas privadas {id: texto Lean que va después del contexto})."""
    texto = fuente.read_text(encoding="utf-8")
    lineas = texto.split("\n")
    its = items(lineas)
    fin_ns = max(i for i, l in enumerate(lineas) if l.startswith("end Velveteen"))
    peldanos, privadas = [], {}
    for it in its:
        if it["tipo"] != "theorem" or it["nombre"] not in TEOREMAS:
            continue
        contexto = "\n".join(lineas[:it["ini"]]).rstrip() + "\n"
        cuerpo = "\n".join(lineas[it["ini"]:it["fin"]]).rstrip()
        # sin el docstring: el agente copia solo omit/theorem y la firma
        sin_doc = re.sub(r"/--.*?-/\n", "", cuerpo, count=1, flags=re.S)
        ini_thm = sin_doc.index("theorem ")
        k = _fin_firma(sin_doc, ini_thm)
        enunciado = sin_doc[:k].rstrip()
        prueba = sin_doc[k + 2:].strip("\n")
        dif, es = TEOREMAS[it["nombre"]]
        id_ = f"g_{it['nombre']}"
        peldanos.append(_peldano(id_, it["nombre"], contexto, enunciado, dif, es, True, _docstring(lineas, it)))
        privadas[id_] = f"{enunciado} :={'' if prueba.startswith(chr(10)) else ' '}{prueba}\n"
        if it["nombre"] == "cycle_safe":
            # la misma meta sin la escalera: el contexto conserva definiciones y comentarios, no los teoremas
            quitar = set()
            for o in its:
                if o["tipo"] == "theorem" and o["fin"] <= it["ini"]:
                    quitar.update(range(o["ini"], o["fin"]))
            solo_defs = "\n".join(l for i, l in enumerate(lineas[:it["ini"]]) if i not in quitar)
            solo_defs = re.sub(r"\n{3,}", "\n\n", solo_defs).rstrip() + "\n"
            peldanos.append(_peldano("g_cycle_safe_directo", "cycle_safe", solo_defs, enunciado, 5,
                                     es + " Sin los lemas intermedios en el contexto.", True, _docstring(lineas, it),
                                     "Mismo enunciado que g_cycle_safe; contexto de solo definiciones."))
            privadas["g_cycle_safe_directo"] = None  # se completa abajo: necesita los lemas como `have` o auxiliares
    contexto_total = "\n".join(lineas[:fin_ns]).rstrip() + "\n"
    for id_, dif, enun, es, refuta in FALSOS:
        peldanos.append(_peldano(id_, id_, contexto_total, enun, dif, es, False,
                                 notas="CONTROL FALSO: no tiene prueba. Su refutación privada compila en Lean."))
        privadas[id_] = refuta
    # cycle_safe directo: la prueba de referencia trae la escalera como texto previo (solo para comprobar que el
    # enunciado es demostrable en ese contexto; el agente no ve esto)
    escalera = [o for o in its if o["tipo"] == "theorem" and o["nombre"] in
                ("mul_le_of_le_div", "div_lt_of_lt_mul", "trim_spec", "cap_mono", "buySize_caps", "step_preserves")]
    previo = "\n\n".join(re.sub(r"/--.*?-/\n", "", "\n".join(lineas[o["ini"]:o["fin"]]).rstrip(), count=1, flags=re.S)
                         for o in escalera)
    privadas["g_cycle_safe_directo"] = previo + "\n\n" + privadas["g_cycle_safe"]
    return peldanos, privadas


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--fuente", type=Path, default=FUENTE)
    ap.add_argument("--revisar", action="store_true", help="no escribe; dice qué cambiaría")
    a = ap.parse_args(argv)
    peldanos, privadas = generar(a.fuente)
    cambios = 0
    for e in peldanos:
        ruta = DIR / f"{e['id']}.json"
        nuevo = json.dumps(e, ensure_ascii=False, indent=1) + "\n"
        if ruta.exists():
            viejo = json.loads(ruta.read_text(encoding="utf-8"))
            if viejo.get("frozen_hash") == e["frozen_hash"]:
                continue
            if viejo.get("estado") == "aprobado":
                print(f"!! {e['id']}: está aprobado y el enunciado cambiaría ({viejo['frozen_hash']} → {e['frozen_hash']}); no se toca")
                continue
        cambios += 1
        print(f"{'(revisar) ' if a.revisar else ''}{e['id']}: {e['frozen_hash']} ({'verdadero' if e['verdadero'] else 'FALSO'})")
        if not a.revisar:
            ruta.write_text(nuevo, encoding="utf-8")
    if not a.revisar:
        PRIVADAS.mkdir(parents=True, exist_ok=True)
        for id_, txt in privadas.items():
            (PRIVADAS / f"{id_}.lean").write_text(txt, encoding="utf-8")
    print(f"{len(peldanos)} peldaños ({sum(not e['verdadero'] for e in peldanos)} controles falsos); {cambios} cambios")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
