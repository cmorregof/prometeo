"""30 sep 2026: los lemas del cuaderno se compilan a nivel de teoría, antes del contexto del peldaño, y con los lemas
del cuaderno que sus pruebas citan, en el orden del cuaderno.

En la ronda 1 iban dentro del contexto: `sign_step` (fixes x y z) chocaba con secante_1 a secante_4, que fijan x y, y
todo intento de E y E3 ahí fallaba con «Duplicate fixed variable» antes de que Isabelle mirara la prueba
(resultados/mcnemar_ronda_20260926.md, sección 3). Los lemas del agente siguen dentro del contexto."""

import json
from pathlib import Path

import pytest

from unirl import cuaderno as C, corpus, gd_isabelle as G, martillo as M
from unirl.gd_isabelle import TheoremVerifier

RAIZ = Path(__file__).resolve().parents[2]
CON_FIXES = 'lemma cu_conmuta:\n  fixes x y :: real\n  shows "x * y = y * x"\n  by (simp add: mult.commute)'
OTRO = 'lemma cu_otro: "(0::real) \\<le> 1"\n  by simp'
DEP_A = 'lemma cu_dep_a:\n  fixes x :: real\n  shows "x \\<le> x"\n  by simp'
DEP_B = 'lemma cu_dep_b:\n  fixes x :: real\n  shows "x \\<le> x \\<and> x \\<le> x"\n  using cu_dep_a by simp'


def _lema(nombre: str, texto: str) -> dict:
    return {"nombre": nombre, "texto": texto, "alcance": "general", "procedencia": {}}


def _linea(thy: str, texto: str) -> int:
    return next(i for i, l in enumerate(thy.splitlines(), 1) if l == texto)


# ----------------------------------------------------------------------------- sin Isabelle


@pytest.mark.parametrize("nombre, plantilla", [("gd.LEMMAS_THEOREM", G.LEMMAS_THEOREM), ("gd.FINAL_THEOREM", G.FINAL_THEOREM),
                                               ("martillo.TEORIA_SOLO", M.TEORIA_SOLO), ("martillo.TEORIA_PASOS", M.TEORIA_PASOS),
                                               ("martillo.TEORIA_CONSULTA", M.TEORIA_CONSULTA)])
def test_la_biblioteca_va_antes_del_contexto_en_todas_las_plantillas(nombre, plantilla):
    assert plantilla.count("__LIBRARY__") == 1, nombre
    assert plantilla.index("__PRELUDE__") < plantilla.index("__LIBRARY__") < plantilla.index("\ncontext\n") \
        < plantilla.index("__AGENTLEMMAS__"), nombre


def test_final_y_lemas_ubican_cada_bloque(tmp_path):
    v = TheoremVerifier.desde_corpus("secante_1_inyectiva")
    agente = 'lemma mio: "(1::real) \\<le> 2"\n  by simp'
    thy, st = v.final_theory("by simp", agente, tmp_path / "o.json", tmp_path / "t.json", library=CON_FIXES)
    ctx = _linea(thy, "context")
    assert thy.splitlines()[st["LIBRARY"] - 1] == "lemma cu_conmuta:" and st["LIBRARY"] < ctx
    assert thy.splitlines()[st["AGENTLEMMAS"] - 1] == 'lemma mio: "(1::real) \\<le> 2"' and st["AGENTLEMMAS"] > ctx
    thy, st = v.lemmas_theory(agente, tmp_path, library=CON_FIXES)
    assert st["LIBRARY"] < _linea(thy, "context") < st["AGENTLEMMAS"]
    thy, st = v.final_theory("by simp", agente, tmp_path / "o.json", tmp_path / "t.json")  # sin biblioteca: igual que antes
    assert "cu_conmuta" not in thy and st["AGENTLEMMAS"] > _linea(thy, "context")


def test_biblioteca_sin_redefinidos():
    lib = CON_FIXES + "\n\n" + OTRO
    assert G.biblioteca_sin_redefinidos(lib, "") == lib
    assert G.biblioteca_sin_redefinidos(lib, 'lemma cu_otro: "True" by simp') == CON_FIXES  # gana la versión del agente
    assert G.biblioteca_sin_redefinidos("", 'lemma a: "True" by simp') == ""


def test_errores_de_la_biblioteca_se_nombran_y_se_detectan():
    log = ('*** Duplicate fixed variable(s): "x" (line 11 of "/tmp/gd-final-x/Final.thy")\n'
           '*** Failed to finish proof (line 30 of "/tmp/gd-final-x/Final.thy")')
    errs = G.translate_errors(log, "Final", proof_first=30, proof="by simp", library_first=10, library=CON_FIXES)
    assert "(lema cu_conmuta del cuaderno, línea 2)" in errs[0] and "(línea 1 de tu PROOF)" in errs[1]
    assert G.fallo_de_biblioteca(errs) and not G.fallo_de_biblioteca(errs[1:])
    # un lema del agente con el mismo error NO es falla de la biblioteca: es feedback para el agente
    assert not G.fallo_de_biblioteca(G.translate_errors(log, "Final", lemmas_first=10, lemmas=CON_FIXES))


def test_verify_pasa_la_biblioteca_aparte_y_marca_su_falla(monkeypatch):
    v = TheoremVerifier.desde_corpus("secante_1_inyectiva")
    llamadas = {}

    def lemas(agente, library=""):
        llamadas["lemas"] = (agente, library)
        return "ok", [], []

    def final(proof, lemmas="", work=None, library=""):
        llamadas["final"] = (proof, lemmas, library)
        return {"rc": 1, "final_json": False, "target": {}, "cheating": False, "build_s": 1.0, "errors": ["*** x"]}
    monkeypatch.setattr(v, "check_lemmas_in_kernel", lemas)
    monkeypatch.setattr(v, "compile_final", final)
    agente = 'lemma mio: "(1::real) \\<le> 2"\n  by simp'
    o = v.verify(v.target(), {"proof": "by simp", "lemmas": agente, "lemmas_library": CON_FIXES})
    assert llamadas["lemas"] == (agente, CON_FIXES) and llamadas["final"] == ("by simp", agente, CON_FIXES)
    assert o.outcome_label == "PROOF_FAILED" and o.raw["biblioteca_fallo"] is False
    # sin lemas del agente, la biblioteca igual se compila (en la etapa de lemas) y va aparte en la Final
    v.verify(v.target(), {"proof": "by simp", "lemmas_library": CON_FIXES})
    assert llamadas["lemas"] == ("", CON_FIXES) and llamadas["final"] == ("by simp", "", CON_FIXES)
    # si falla un lema del cuaderno, el intento no se pudo juzgar y queda marcado
    monkeypatch.setattr(v, "check_lemmas_in_kernel", lambda agente, library="": (
        "failed", ['*** Duplicate fixed variable(s): "x" (lema cu_conmuta del cuaderno, línea 2)'], []))
    o = v.verify(v.target(), {"proof": "by simp", "lemmas_library": CON_FIXES})
    assert o.outcome_label == "LEMMA_FAILED" and o.raw["biblioteca_fallo"] is True and "cuaderno" in o.raw["reason"]
    assert o.raw["veredicto"]["juez"] == "teorema-2026-09-30"


def test_clave_del_martillo_distingue_la_biblioteca_a_nivel_de_teoria():
    j = TheoremVerifier.desde_corpus("secante_1_inyectiva")
    assert M._contexto(j, "").split("|")[1] == "sin-cuaderno"  # sin cuaderno, la clave no cambia: la caché sigue valiendo
    assert M._contexto(j, "abc").split("|")[1] == "abc@teoria"  # con cuaderno, no se reutiliza lo de antes del arreglo


def test_la_biblioteca_lleva_las_dependencias_en_el_orden_del_cuaderno():
    a, ab = _lema("cu_dep_a", DEP_A), _lema("cu_dep_ab", 'lemma cu_dep_ab: "(1::real) \\<le> 1"\n  by simp')
    b, c = _lema("cu_dep_b", DEP_B), _lema("cu_dep_c", 'lemma cu_dep_c: "True"\n  using cu_dep_b by simp')
    todos = [a, ab, b, c]
    nombres = lambda xs: [x["nombre"] for x in xs]
    assert nombres(C.cierre_de_dependencias([c], todos)) == ["cu_dep_a", "cu_dep_b", "cu_dep_c"]  # transitivo
    assert nombres(C.cierre_de_dependencias([b, a], todos)) == ["cu_dep_a", "cu_dep_b"]  # orden del cuaderno, no del ranking
    assert nombres(C.cierre_de_dependencias([ab], todos)) == ["cu_dep_ab"]  # cu_dep_a no se confunde con cu_dep_ab


def test_lo_mostrado_no_cambia_y_lo_compilado_lleva_las_dependencias(tmp_path):
    cu = C.Cuaderno(tmp_path)
    cu.errores = C.Cuaderno().errores
    usa_biseccion = 'lemma cu_bis_dep: "fst (biseccion f a b 0) = a"\n  using cu_dep_a by simp'
    cu.lemas = [_lema("cu_dep_a", DEP_A), _lema("cu_bis_dep", usa_biseccion)]
    sel = cu.recuperar(corpus.exigir_usable("bis_1_ancho"), ("lemas",))
    assert [l["nombre"] for l in sel["lemas"]] == ["cu_bis_dep"]  # cu_dep_a no comparte identificadores: no se muestra
    assert [l["nombre"] for l in sel["biblioteca"]] == ["cu_dep_a", "cu_bis_dep"]
    assert C.Cuaderno.biblioteca(sel).startswith("lemma cu_dep_a:") and "cu_dep_a:" not in C.Cuaderno.render(sel)


# ----------------------------------------------------------------------------- con Isabelle


def _sign_step() -> str:
    f = RAIZ / "runs" / "unirl" / "cuaderno" / "congelados" / "fbd88bf0474ad117" / "lemas.json"
    if not f.exists():
        pytest.skip("no está el cuaderno congelado de la ronda 1")
    (lema,) = [l for l in json.loads(f.read_text(encoding="utf-8"))["lemas"] if l["nombre"] == "sign_step"]
    return lema["texto"]


@pytest.mark.isabelle
def test_isabelle_sign_step_del_cuaderno_ya_no_choca_con_secante_1():
    v = TheoremVerifier.desde_corpus("secante_1_inyectiva")
    sign = _sign_step()
    o = v.verify(v.target(), {"proof": "by simp", "lemmas_library": sign})
    errs = o.raw.get("errors") or []
    assert o.raw["stage"] == "final" and o.outcome_label != "LEMMA_FAILED", (o.outcome_label, errs[:3])
    assert not any("Duplicate fixed variable" in e for e in errs) and o.raw["biblioteca_fallo"] is False
    # el mismo lema escrito por el agente sigue dentro del contexto: ahí choca, y es feedback para el agente
    o = v.verify(v.target(), {"proof": "by simp", "lemmas": sign})
    assert o.outcome_label == "LEMMA_FAILED" and any('Duplicate fixed variable(s): "x"' in e for e in o.raw["errors"])
    assert o.raw["biblioteca_fallo"] is False


@pytest.mark.isabelle
def test_isabelle_consulta_con_la_biblioteca_en_secante_1():
    j = TheoremVerifier.desde_corpus("secante_1_inyectiva")
    (r,) = M.consultar(j, [{"tipo": "hecho", "texto": "sign_step"}], biblioteca=_sign_step())
    assert "error" not in r and r.get("existe") is True, r


@pytest.mark.isabelle
def test_isabelle_dependencias_de_la_biblioteca():
    v = TheoremVerifier.desde_corpus("secante_1_inyectiva")  # fija x: la biblioteca, a nivel de teoría, no choca
    o = v.verify(v.target(), {"proof": "by simp", "lemmas_library": DEP_A + "\n\n" + DEP_B})
    assert o.raw["stage"] == "final" and o.raw["biblioteca_fallo"] is False, (o.outcome_label, o.raw.get("errors", [])[:3])
    o = v.verify(v.target(), {"proof": "by simp", "lemmas_library": DEP_B})  # sin su dependencia: el intento no se juzga
    assert o.outcome_label == "LEMMA_FAILED" and o.raw["biblioteca_fallo"] is True
    assert any("Undefined fact" in e and "del cuaderno" in e for e in o.raw["errors"])
