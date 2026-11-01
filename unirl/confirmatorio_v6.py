"""Arnés v6 del estudio confirmatorio: la línea de comandos que ejecuta el prerregistro (borrador v2, 26 oct 2026).

Módulos: plan_v6 (población y pliegues), prompts_v6 (prompts literales, ramas, episodio), tokens_api (count_tokens),
fase1 (construcción y post-fase 1 sin API), fase2 (celdas). El juez es el de la v5 (corpus_confirmatorio.py), sin cambios.

Orden de uso (detallado en ORDEN_COMANDOS_V6.md):
    python -m unirl.confirmatorio_v6 prompts                                   # Anexo B: SISTEMA y cabeceras literales
    python -m unirl.confirmatorio_v6 humo [ids…]                               # Lean real, sin API: cada rama en seco
    python -m unirl.confirmatorio_v6 plan --censo DIR --salida v6/plan.json    # población y pliegues (sin Lean ni API)
    python -m unirl.confirmatorio_v6 fase1 --plan … --registro PRERREGISTRO_REGISTRADO --salida v6/fase1 [--continuar]
    python -m unirl.confirmatorio_v6 anexo --fase1 v6/fase1 --anexo v6/anexo_fase1 --contador api   # sin API salvo count_tokens
    python -m unirl.confirmatorio_v6 celdas --anexo v6/anexo_fase1             # vista previa de la cola (sin API)
    python -m unirl.confirmatorio_v6 fase2 --anexo … --salida v6/fase2 [--continuar] [--paralelo N]
    python -m unirl.confirmatorio_v6 kig --fase2 v6/fase2                      # enmienda mecánica K_ig
    python -m unirl.confirmatorio_v6 proyeccion --fase2 v6/fase2               # solo el libro: regla de recorte de §11
    python -m unirl.confirmatorio_v6 rejuzgar --fase2 v6/fase2 --anexo …       # SIN_SALIDA_LEAN con 900 s, sin API

Claude no lanza corridas con API sin la autorización explícita de Carlos registrada en aprobados/FECHA, y la fase 1
no arranca sin PRERREGISTRO_REGISTRADO (DOI/URL de OSF + SHA-256 del prerregistro congelado).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

from . import corpus_confirmatorio as K
from . import fase1 as F1
from . import fase2 as F2
from . import frontera as F
from . import plan_v6 as P
from . import prompts_v6 as PR
from .tokens_api import ContadorAPI, ContadorFalso, Conteos

RAIZ_V6 = K.RUNS / "v6"
FLAGS_LITERALES = {
    "modelo": "claude-haiku-5-5", "max_tokens": 32000, "thinking": "no se envía (adaptativo por omisión)",
    "output_config.effort": "no se envía (Haiku sin esfuerzo)", "temperature": "no se envía (la de la API por omisión)",
    "--recorte": "ninguno", "--task-budget": 0, "UNIRL_TIMEOUT_LEAN": 300, "rejuicio_SIN_SALIDA": 900,
    "reintentos": "loop.complete_with_retries, ESPERAS_REINTENTO = (2, 5, 11, 26, 60) s, iguales en todas las ramas",
    "K": 4, "turnos_exploracion": 3, "max_evals_por_turno": 2, "max_lemas_por_intento": 4,
    "tope_fase1_usd": F1.TOPE_FASE1_USD, "tope_fase2_usd": F2.TOPE_FASE2_USD,
    "libro": str(K.LIBRO), "UNIRL_TOPE_CONFIRMATORIO_USD": "gastado previo + 24 (fase 1); gastado previo + 260 (fase 2) (§17.15)",
    "--paralelo": 4, "recorte_automatico": "una sola vez al completarse n10, dentro de fase2 (§11, C6); pasos D50 → P k=1 → tope 30 → sin semilla 3",
    "tolerancia_igualacion": "máx(5 %, mediana de tokens por lema del bloque objetivo) (§17.7)",
    "conteo_tokens": "bloque entero como un solo mensaje, menos el armazón medido una vez (C3)",
}


def _lake(timeout: float | None = None):
    return K.LakeSinSecretos(raiz=K.LEAN_CORPUS, timeout_s=float(timeout or os.environ.get("UNIRL_TIMEOUT_LEAN", 300)))


# ============================================================================== prompts (Anexo B)


def _tarea_ejemplo() -> dict:
    ctx = "namespace Ejemplo\n\ndef doble (n : Nat) : Nat := 2 * n"
    st = "theorem doble_par (n : Nat) : doble n % 2 = 0 := by sorry"
    return K.tarea_de({"id": "ejemplo:doble_par", "sha256_tarea": K._sha(ctx + "\n\n" + st), "familia": "ejemplo", "fuente": "ejemplo",
                       "verdad": "verdadero", "imports": ["Mathlib"], "dependencias": ["Mathlib"], "contexto_lean": ctx, "enunciado_lean": st})


def entradas_ejemplo() -> list[dict]:
    return [{"nombre": "cu_doble_eq", "declara": ["cu_doble_eq"], "teoremas": ["cu_doble_eq"], "enunciados": {"cu_doble_eq": "(n : Nat) : doble n = 2 * n"},
             "bloque": "theorem cu_doble_eq (n : Nat) : doble n = 2 * n := by rfl", "origen": "oculto", "sha": "x"},
            {"nombre": "cu_dos_mul_mod", "declara": ["cu_dos_mul_mod"], "teoremas": ["cu_dos_mul_mod"],
             "enunciados": {"cu_dos_mul_mod": "(n : Nat) : 2 * n % 2 = 0"}, "bloque": "theorem cu_dos_mul_mod (n : Nat) : 2 * n % 2 = 0 := by omega",
             "origen": "oculto", "sha": "y"}]


def texto_anexo_b() -> str:
    t = _tarea_ejemplo()
    ent = entradas_ejemplo()
    L = ["# Anexo B — Prompts y flags literales del arnés v6", "",
         "Generado por `python -m unirl.confirmatorio_v6 prompts`. Los textos de abajo son los que el arnés envía, byte a byte, "
         "sobre una tarea de ejemplo (`ejemplo:doble_par`) con dos lemas de ejemplo. En las celdas reales cambian solo la tarea, "
         "los lemas/pistas, los lemas locales, la historia y el presupuesto.", "",
         "## B.1 SISTEMA de test (fase 2, todas las ramas)", "", "```", PR.SISTEMA_TEST, "```", "",
         "## B.2 SISTEMA de la fase 1 (construcción CC en línea; la v5 literal: ahí la frase sobre tareas futuras es verdadera)", "",
         "```", PR.SISTEMA_FASE1, "```", "",
         "Diferencia exacta: «" + PR._FRASE_V5 + "» → «" + PR._FRASE_TEST + "».", ""]
    for rama in PR.RAMAS:
        L += [f"## B.3 Prompt de usuario, rama {rama} (primera llamada: sin lemas locales ni historia)", "", "````",
              PR.construir_prompt(t, rama, ent if PR.RAMAS[rama].fuente != "ninguna" else [], [], [], PR.RAMAS[rama].intentos, 3), "````", ""]
    L += ["## B.4 Cabeceras literales", "", f"Cuaderno invocable (D100, P, D50; también la construcción CC de la fase 1):", "```",
          "\n".join(PR.cabecera("D100", ent)).rstrip(), "```", "", "Pistas de texto (D100-texto y R-texto, idéntica en las dos):", "```",
          "\n".join(PR.cabecera("D100-texto", ent)).rstrip(), "```", "",
          f"Comprobación mecánica: `cabecera('D100-texto', x) == cabecera('R-texto', x)` para todo x → {PR.cabecera('D100-texto', ent) == PR.cabecera('R-texto', ent)}.",
          "La línea de cada lema/pista es `prompts_v6.linea_lema(nombre, enunciado)` = «- `nombre` : enunciado». El largo de un bloque es el conteo "
          "(`count_tokens`) de sus líneas unidas por saltos de línea como UN solo mensaje, menos el armazón del mensaje medido una vez (C3).", "",
          "## B.5 Flags y parámetros literales de la corrida", "", "```", json.dumps(FLAGS_LITERALES, ensure_ascii=False, indent=1), "```", "",
          "## B.6 Ramas (§3.3)", "", "| rama | k | K | invocable | texto | fuente del bloque |", "|---|---:|---:|---|---|---|"]
    L += [f"| {r.nombre} | {r.k} | {'K_ig' if r.nombre == 'SC_ig' else r.intentos} | {r.invocable} | {r.texto} | {r.fuente} |" for r in PR.RAMAS.values()]
    L += ["", f"SHA-256 del SISTEMA de test: `{K._sha(PR.SISTEMA_TEST)}`; de la fase 1: `{K._sha(PR.SISTEMA_FASE1)}`."]
    return "\n".join(L) + "\n"


def cmd_prompts(a) -> int:
    txt = texto_anexo_b()
    if a.salida:
        Path(a.salida).write_text(txt, encoding="utf-8")
        print(f"escrito {a.salida} ({K._sha(txt)[:16]})")
    else:
        print(txt)
    return 0


# ============================================================================== plan


def cmd_plan(a) -> int:
    censo = P.leer_censo(Path(a.censo))
    corpus = None
    if not a.sin_corpus:
        corpus = K.cargar_corpus(a.version)
    excluir = set()
    if a.excluir:
        excluir = set(json.loads(Path(a.excluir).read_text(encoding="utf-8")).get("ids", []))
    plan = P.construir_plan(censo, corpus, excluir)
    sha = P.escribir_plan(plan, Path(a.salida))
    print(f"F = {plan['F']} familias, {plan['n_tareas']} tareas; plan en {a.salida} sha256 {sha}")
    for fam, d in plan["familias"].items():
        print(f"  {fam}: {d['n_distintas']} distintas, {d['n_tope']} con tope, pliegues {len(d['pliegues']['1'])}/{len(d['pliegues']['2'])}, "
              f"grupos de implicación fundidos {d['grupos_implicacion_fundidos']}, duplicados {sum(len(v) for v in d['duplicados'].values())}")
    for av in plan["avisos"]:
        print("  aviso:", av)
    return 0


# ============================================================================== fase 1


def _hacer_prov_real(modelo: str, corrida: str, tope: float):
    return lambda: K.hacer_proveedor(modelo, corrida, tope, effort=None, recorte=None, task_budget=None)


def cmd_fase1(a) -> int:
    registro = F1.verificar_registro(Path(a.registro), Path(a.prerregistro) if a.prerregistro else None)
    plan, sha = P.cargar_plan(Path(a.plan))
    tareas = K.cargar_corpus(a.version)
    lake = _lake()
    if a.seco:
        hacer = lambda: PR.ProveedorSecoV6()
    else:
        hacer = _hacer_prov_real(a.modelo, "fase1", a.tope_usd)
    familias = a.familias.split(",") if a.familias else None
    estado = F1.construir(plan, tareas, Path(a.salida), lake, hacer, registro, tope_usd=a.tope_usd, paralelo=a.paralelo,
                          continuar=a.continuar, familias=familias)
    print(json.dumps({k: v for k, v in estado.items() if k != "construcciones"}, ensure_ascii=False, indent=1))
    return 0 if estado["motivo_fin"] == "completo" else 1


def cmd_anexo(a) -> int:
    """Todo lo post-fase 1: rechazados, filtro, conteos, fondos, exclusión, martillo, H4, plan B, anexo con SHA256SUMS."""
    fase1 = Path(a.fase1)
    plan, _ = P.cargar_plan(fase1 / "plan.json")
    estado = json.loads((fase1 / "estado.json").read_text(encoding="utf-8"))
    tareas = K.cargar_corpus(a.version)
    familias = F1.familias_construidas(estado, plan)
    print(f"{len(familias)} familias con las 4 construcciones completas")
    lake = _lake()
    cuadernos = F1.cargar_cuadernos(fase1, plan, familias)
    anexo = Path(a.anexo)
    anexo.mkdir(parents=True, exist_ok=True)
    contador = ContadorAPI() if a.contador == "api" else ContadorFalso()
    conteos = Conteos(anexo / "conteos_tokens.json", contador)
    print("rechazados…", flush=True)
    rechaz = F1.rechazados(fase1, lake, tareas, cuadernos)
    filtro = F1.FiltroCompilacion(lake, anexo / "filtro_cache.json")
    print("fondos (filtro de compilación + deriva + texto + igualación)…", flush=True)
    fondos_ = F1.fondos(plan, tareas, cuadernos, rechaz, filtro, conteos, familias, refs=fase1 / "referencias")
    conteos.guardar()
    bl_d100 = {i: {c: v["D100"] for c, v in bl.items()} for i, bl in fondos_["bloques"].items()}
    print("exclusión previa…", flush=True)
    exclusion = F1.exclusion_previa(plan, tareas, lake, bl_d100, familias)
    siguen = F1.familias_que_siguen(exclusion, familias)
    print(f"martillo con cuaderno… ({len(siguen)} familias siguen tras la exclusión)", flush=True)
    martillo = F1.martillo_cuaderno(plan, tareas, lake, bl_d100, siguen)
    h4 = F1.lista_h4(plan, cuadernos, rechaz, conteos, siguen)  # C7: sobre las que siguen
    plan_b = F1.evaluar_plan_b(plan, cuadernos, exclusion, h4, familias)
    drift = F1.drift_fase1(fase1)
    sha = F1.escribir_anexo(anexo, plan, estado, cuadernos, rechaz, fondos_, exclusion, martillo, h4, plan_b, conteos, familias, drift)
    print(json.dumps({"anexo": str(anexo), "sha256_SHA256SUMS": sha, "h4": {k: v for k, v in h4.items() if k != "detalle"}, "plan_b": plan_b,
                      "excluidas": sum(1 for v in exclusion["por_tarea"].values() if v["excluida"]),
                      "caidas_por_familia": fondos_["caidas_por_familia"]}, ensure_ascii=False, indent=1))
    return 0


def cmd_celdas(a) -> int:
    anexo = F2.cargar_anexo(Path(a.anexo))
    cola = F2.ordenar_celdas(F2.celdas(anexo["plan"], anexo))
    print(json.dumps({k: v for k, v in cola.items() if k != "celdas"}, ensure_ascii=False, indent=1))
    for c in cola["celdas"][: a.n]:
        print(c["indice"], c["celda"], c["c"])
    return 0


def cmd_fase2(a) -> int:
    tareas = K.cargar_corpus(a.version)
    lake = _lake()
    libro_ruta = None
    if a.seco:  # el seco escribe un libro PROPIO (nunca el real) para que la proyección automática en n10 se ejercite
        libro_ruta = Path(a.salida) / "gasto_seco.json"
        libro_seco = K.Libro(ruta=libro_ruta, tope_usd=1e9, topes_fase={})
        hacer = lambda: PR.ProveedorSecoV6(libro=libro_seco, fase=f"confirmatorio:{F2.NOMBRE_FASE2}")
    else:
        hacer = lambda: F2.proveedor_fase2(a.modelo, a.tope_usd)
    estado = F2.correr(Path(a.salida), Path(a.anexo), tareas, lake, hacer, paralelo=a.paralelo, continuar=a.continuar,
                       exigir_registro=not a.sin_registro_anexo, exigir_api_conteos=not a.seco, limite=a.limite or None,
                       ignorar_plan_b=bool(a.seco and a.ignorar_plan_b), tope_usd=a.tope_usd, libro_ruta=libro_ruta)
    print(json.dumps(estado, ensure_ascii=False, indent=1))
    return 0 if estado["motivo_fin"] == "completo" else 1


def cmd_kig(a) -> int:
    print(json.dumps(F2.calcular_k_ig(Path(a.fase2)), ensure_ascii=False, indent=1))
    return 0


def cmd_proyeccion(a) -> int:
    """Solo lectura: la proyección que DECIDE la hace el arnés dentro de fase2, una vez, al completarse n10 (C6)."""
    fase2 = Path(a.fase2)
    out = F2.proyectar_gasto(Path(a.libro) if a.libro else K.LIBRO, fase2 / "cola.json", fase2 / "enmiendas", a.tope_usd, escribir=False)
    out["nota"] = "informativa: no escribe enmiendas; la decisión registrada está en enmiendas/proyeccion_n10.json"
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


def cmd_rejuzgar(a) -> int:
    tareas = K.cargar_corpus(a.version)
    print(json.dumps(F2.rejuzgar_sin_salida(Path(a.fase2), Path(a.anexo), tareas, _lake(900)), ensure_ascii=False, indent=1))
    return 0


# ============================================================================== humo por rama (Lean real, sin API)


def humo_rama(t: dict, lake, carpeta: Path, entradas: list[dict], ref: str) -> tuple[bool, list[str]]:
    """Cada rama en seco sobre la tarea t: el prompt y el archivo Lean tienen lo que la rama manda y nada más."""
    bien, notas = True, []
    hdr_texto = None
    for rama, r in PR.RAMAS.items():
        cfg = PR.config_de(rama, 4 if rama == "SC_ig" else None)
        ent = entradas if r.fuente != "ninguna" else []
        prov = PR.ProveedorSecoV6()
        res = PR.episodio_v6(t, rama, cfg, prov, lake, ent, carpeta, f"humo#{t['id']}#{rama}", ref, parar=None)
        prompts = [json.loads(l)["prompt"] for l in (carpeta / "llamadas.jsonl").read_text(encoding="utf-8").splitlines()
                   if json.loads(l)["episodio"] == f"humo#{t['id']}#{rama}"]
        p0 = prompts[0]
        if r.fuente == "ninguna":
            ok = PR.TITULO_CUADERNO not in p0 and PR.TITULO_TEXTO not in p0
        elif r.invocable:
            ok = PR.TITULO_CUADERNO in p0 and PR.TITULO_TEXTO not in p0 and "(oculto)" not in p0 and "oculto" not in p0
        else:
            ok = PR.TITULO_TEXTO in p0 and PR.TITULO_CUADERNO not in p0
            h = "\n".join(PR.cabecera(rama, ent))
            if hdr_texto is None:
                hdr_texto = h
            ok &= h == hdr_texto
        ok &= res["lemas_admitidos"][:1] == ["cu_seco"] and not res["resuelto"] and res["llamadas_facturadas"] == res["llamadas"]
        # el archivo Lean de los lemas (admitir_bloque) lleva el bloque solo en las ramas invocables
        archivos = getattr(lake, "archivos", None)
        notas.append(f"  {rama}: prompt ok={ok} intentos={res['intentos']} lemas={res['lemas_admitidos']} facturadas={res['llamadas_facturadas']}")
        bien &= ok
    return bien, notas


def cmd_humo(a) -> int:
    tareas = K.cargar_corpus(a.version)
    lake = _lake()
    print(f"lake: {lake.lake} ({lake.version()}) en {K.LEAN_CORPUS}")
    ids = a.ids or sorted(tareas)[:2]
    carpeta = RAIZ_V6 / "humo" / datetime.now().strftime("%Y%m%d-%H%M%S")
    carpeta.mkdir(parents=True)
    bien = True
    for i in ids:
        t = K.tarea_de(tareas[i])
        ref = K.referencia(t, lake)
        rb = F.admitir_bloque(t, lake, "", "theorem cu_humo_v6 : (2 : Nat) + 2 = 4 := by decide", set())
        bien &= rb["etiqueta"] == "ACCEPTED"
        ent = [{"nombre": "cu_humo_v6", "declara": rb["nombres"], "teoremas": rb["teoremas"], "enunciados": rb["enunciados"],
                "bloque": "theorem cu_humo_v6 : (2 : Nat) + 2 = 4 := by decide", "origen": "oculto", "sha": K._sha("humo")}]
        malo = [{"nombre": "cu_humo_malo", "declara": ["cu_humo_malo"], "teoremas": ["cu_humo_malo"], "enunciados": {"cu_humo_malo": ": (2 : Nat) + 2 = 5"},
                 "bloque": "theorem cu_humo_malo : (2 : Nat) + 2 = 5 := by decide", "origen": "oculto", "sha": K._sha("malo")}]
        ok, caidas = F1.filtrar_bloque(lake, t, ent + malo)
        print(f"{i}\n  filtro de compilación: quedan {[e['nombre'] for e in ok]}, caen {[c['nombre'] for c in caidas]}")
        bien &= [e["nombre"] for e in ok] == ["cu_humo_v6"] and len(caidas) == 1
        # exclusión previa sobre un enunciado que simp NO cierra solo (a + b = b + a): el lema idéntico debe cerrar
        # (`exact cu_mismo`); el distractor cu_humo_v6 no. Sobre 0 + n = n (que simp cierra solo) `simpa using L` cerraría
        # con cualquier L: por eso la población excluye antes lo trivial para el martillo (ver REVISION_V6.md).
        ts = K._tarea_sintetica(t, "unirl_humo_excl", "(a b : Nat) : a + b = b + a")
        ent_excl = ent + [{"nombre": "cu_mismo", "declara": ["cu_mismo"], "teoremas": ["cu_mismo"], "enunciados": {"cu_mismo": "(a b : Nat) : a + b = b + a"},
                           "bloque": "theorem cu_mismo (a b : Nat) : a + b = b + a := by omega", "origen": "oculto", "sha": K._sha("mismo")}]
        res = F1.compilar_copias(lake, ts, PR.lean_de_entradas(ent_excl), ["first | exact cu_humo_v6 | exact cu_humo_v6 .. | simpa using cu_humo_v6", "first | exact cu_mismo | exact cu_mismo .. | simpa using cu_mismo"],
                                 "unirl_excl", 120, exigir_axiomas=False)
        print(f"  exclusión previa sobre a + b = b + a: cu_humo_v6 (distractor) → {res[0]}, cu_mismo (idéntico) → {res[1]}")
        bien &= res == ["falla", "cierra"]
        ts = K._tarea_sintetica(t, "unirl_humo_mt", "(n : Nat) : 0 + n = n")
        # C2: una instancia HAdd que cambia el enunciado 0 + n = n debe caer en el filtro de deriva; cu_humo_v6 no
        ref_s = K.referencia(ts, lake)
        inst = [{"nombre": "cu_bad", "declara": ["cu_bad"], "teoremas": [], "enunciados": {}, "origen": "oculto", "sha": K._sha("bad"),
                 "bloque": "instance cu_bad : HAdd Nat Nat Nat := ⟨fun _ b => b⟩"}]
        deriva = [F1.deriva_enunciado(lake, ts, inst, ref_s), F1.deriva_enunciado(lake, ts, ent, ref_s)]
        print(f"  filtro de deriva (C2) sobre 0 + n = n: instancia HAdd → {'deriva' if deriva[0] else 'NO deriva (mal)'}; cu_humo_v6 → {'deriva (mal)' if deriva[1] else 'no deriva'}")
        bien &= deriva == [True, False]
        # C4: el filtro de texto deja el enunciado que elabora solo y quita el que depende de una def no declarada
        tx_ok, tx_ca = F1.filtrar_texto(lake, t, ent + [{"nombre": "cu_dep", "declara": ["cu_dep"], "teoremas": ["cu_dep"], "origen": "oculto", "sha": K._sha("dep"),
                                                         "enunciados": {"cu_dep": "(n : Nat) : cu_nada_declarado n = 0"}, "bloque": "theorem cu_dep (n : Nat) : cu_nada_declarado n = 0 := by rfl"}])
        print(f"  filtro de texto (C4): quedan {[e['nombre'] for e in tx_ok]}, caen {[c['nombre'] for c in tx_ca]}")
        bien &= [e["nombre"] for e in tx_ok] == ["cu_humo_v6"] and len(tx_ca) == 1
        mt = F1.compilar_copias(lake, ts, PR.lean_de_entradas(ent), F1.TACTICAS_MARTILLO + ["simp [cu_humo_v6]", "simp_all"], "unirl_mt", 300)
        print(f"  martillo con cuaderno sobre 0 + n = n: {dict(zip(F1.TACTICAS_MARTILLO + ['simp [cu_humo_v6]', 'simp_all'], mt))}")
        bien &= "cierra" in mt and "sin_dato" not in mt
        ok_r, notas = humo_rama(t, lake, carpeta, ent, ref)
        print("\n".join(notas))
        bien &= ok_r
    print("HUMO OK" if bien else "HUMO FALLÓ: revisar antes de gastar un dólar")
    return 0 if bien else 1


# ============================================================================== main


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m unirl.confirmatorio_v6", description=__doc__.split("\n")[0])
    ap.add_argument("--version", type=int, default=1)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("prompts"); s.add_argument("--salida", default=None)
    s = sub.add_parser("humo"); s.add_argument("ids", nargs="*")
    s = sub.add_parser("plan"); s.add_argument("--censo", required=True); s.add_argument("--salida", required=True)
    s.add_argument("--sin-corpus", action="store_true", help="ordenar por SHA del id (sin sha256_tarea del corpus)")
    s.add_argument("--excluir", default=None, help="JSON con ids que no pueden ser de test (solo se anotan)")
    s = sub.add_parser("fase1")
    s.add_argument("--plan", required=True); s.add_argument("--registro", required=True)
    s.add_argument("--prerregistro", default=None, help="ruta del prerregistro congelado (obligatoria salvo --seco): se comprueba su SHA")
    s.add_argument("--salida", default=str(RAIZ_V6 / "fase1")); s.add_argument("--modelo", default="claude-haiku-5-5")
    s.add_argument("--tope-usd", type=float, default=F1.TOPE_FASE1_USD); s.add_argument("--paralelo", type=int, default=4)
    s.add_argument("--continuar", action="store_true"); s.add_argument("--seco", action="store_true")
    s.add_argument("--familias", default=None, help="solo estas familias (humo); separadas por coma")
    s = sub.add_parser("anexo"); s.add_argument("--fase1", required=True); s.add_argument("--anexo", required=True)
    s.add_argument("--contador", choices=("api", "falso"), default="api", help="falso solo para humo: la fase 2 exige api")
    s = sub.add_parser("celdas"); s.add_argument("--anexo", required=True); s.add_argument("--n", type=int, default=20)
    s = sub.add_parser("fase2")
    s.add_argument("--anexo", required=True); s.add_argument("--salida", default=str(RAIZ_V6 / "fase2")); s.add_argument("--modelo", default="claude-haiku-5-5")
    s.add_argument("--tope-usd", type=float, default=F2.TOPE_FASE2_USD); s.add_argument("--paralelo", type=int, default=4)
    s.add_argument("--continuar", action="store_true"); s.add_argument("--seco", action="store_true"); s.add_argument("--limite", type=int, default=0)
    s.add_argument("--sin-registro-anexo", action="store_true", help="solo humo: no exigir ANEXO_REGISTRADO")
    s.add_argument("--ignorar-plan-b", action="store_true", help="solo con --seco (humo sobre pocas familias): no exigir que §10 no diga plan B")
    s = sub.add_parser("kig"); s.add_argument("--fase2", required=True)
    s = sub.add_parser("proyeccion"); s.add_argument("--fase2", required=True); s.add_argument("--libro", default=None)
    s.add_argument("--tope-usd", type=float, default=F2.TOPE_FASE2_USD)
    s = sub.add_parser("rejuzgar"); s.add_argument("--fase2", required=True); s.add_argument("--anexo", required=True)
    a = ap.parse_args(argv)
    if a.cmd == "fase1" and not a.seco and not a.prerregistro:
        ap.error("fase1: hace falta --prerregistro (el SHA del archivo congelado se comprueba contra el marcador); solo --seco puede omitirlo")
    if a.cmd == "plan" and a.sin_corpus:
        print("aviso: --sin-corpus ordena por el SHA del id; la corrida real debe usar el sha256_tarea del corpus (§17.3)", flush=True)
    return {"prompts": cmd_prompts, "humo": cmd_humo, "plan": cmd_plan, "fase1": cmd_fase1, "anexo": cmd_anexo, "celdas": cmd_celdas,
            "fase2": cmd_fase2, "kig": cmd_kig, "proyeccion": cmd_proyeccion, "rejuzgar": cmd_rejuzgar}[a.cmd](a)


if __name__ == "__main__":
    raise SystemExit(main())
