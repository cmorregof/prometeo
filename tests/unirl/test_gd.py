"""Juez de teorema de stepsize (unirl/gd_isabelle.py). Rápidas: sin Isabelle. Las marcadas `isabelle` compilan."""

import json
import shutil
import sys
from fractions import Fraction
from pathlib import Path

import pytest

from unirl.gd_isabelle import FINAL_THEOREM, TheoremVerifier, check_lemma_block, check_proof, fill_lines, translate_errors
from unirl.verifiers import TARGETS, make_verifier

HERE = Path(__file__).resolve().parent.parent
GD = ["gd_n1", "gd_const_n2", "gd_const_textbook", "gd_const_dt"]


@pytest.mark.parametrize("name", GD)
def test_objetivos_cargan_con_su_hash(name):
    v = TheoremVerifier(name)
    assert v.target()["hash"] == json.loads((TARGETS / f"{name}.json").read_text())["frozen_hash"]
    cfg = {"judge": "isabelle_theorem", "target": name}
    assert make_verifier(cfg).name == "isabelle_teorema"
    assert ("n :: nat" in v.spec["fixes"]) == (name in ("gd_const_textbook", "gd_const_dt"))


@pytest.mark.parametrize("texto,etiqueta", [
    ("sorry", "UNSOUND"), ("by simp oops", "UNSOUND"), ("proof - show ?thesis sorry qed", "UNSOUND"),
    ("ML \\<open>val x = 1\\<close> by simp", "STATEMENT_DRIFT"), ("using [[quick_and_dirty]] by simp", "STATEMENT_DRIFT"),
    ("by simp\nend\ntheorem x: True by simp", "STATEMENT_DRIFT"), ("by simp notation foo (\"x\")", "STATEMENT_DRIFT"),
    ("by (tactic all_tac)", "STATEMENT_DRIFT"), ("by simp __OUT__", "STATEMENT_DRIFT"),
    ("lemma foo: True by simp", "INVALID_PROPOSAL"), ("", "INVALID_PROPOSAL"), ("sledgehammer", "INVALID_PROPOSAL"),
    ('if "False" by simp', "STATEMENT_DRIFT"), ("‹x› by simp", "STATEMENT_DRIFT"),
])
def test_filtro_proof(texto, etiqueta):
    assert check_proof(texto)[0] == etiqueta


@pytest.mark.parametrize("texto", ["by simp", "proof -\n  have h: \"True\" by simp\n  show ?thesis using interp opt by simp\nqed",
                                   "using interp[of x0 xs] opt\n  apply simp\n  done", "unfolding power2_norm_eq_inner by simp"])
def test_filtro_proof_admite(texto):
    assert check_proof(texto) is None


def test_nombres_reservados_en_lemas():
    assert check_lemma_block('lemma interp: "True" by simp')[0] == "INVALID_PROPOSAL"
    assert check_lemma_block('lemma isarl_target: "True" by simp')[0] == "INVALID_PROPOSAL"
    assert check_lemma_block('lemma mio: "f xs \\<le> f x0 + 1" using interp opt by simp') is None


def test_ensamblado_en_una_pasada():
    thy, starts = fill_lines(FINAL_THEOREM, {"IMPORTS": "I", "PRELUDE": "P", "FIXES": "F", "ASSUMES": "A", "CONCL": "C",
                                             "OUT": "/o", "TARGETOUT": "/t", "INST": "f = f", "AGENTLEMMAS": "", "AGENTPROOF": "by (simp add: __CONCL__ __OUT__)"})
    assert "by (simp add: __CONCL__ __OUT__)" in thy
    assert thy.splitlines()[starts["AGENTPROOF"] - 1] == "by (simp add: __CONCL__ __OUT__)"


def test_traduccion_de_lineas():
    log = '*** Failed to finish proof (line 12 of "/tmp/gd-final-x/Final.thy"):\n*** Undefined fact (line 99 of "/tmp/Other.thy")'
    out = translate_errors(log, "Final", proof_first=10, proof="a\nb\nc\nd")
    assert "línea 3 de tu PROOF" in out[0] and "Other.thy" in out[1]


def test_parse_colision_de_cierre():
    v = TheoremVerifier("gd_n1")
    p = v.parse("PROOF: <<< by (simp add: foo \\<rceil>>>>\nLEMMAS: <<< lemma a: True by simp >>>")
    assert p["proof"].endswith("\\<rceil>") and p["lemmas"].startswith("lemma a")


def _fin(**kw):
    base = {"rc": 0, "final_json": True, "oracles": [], "skip_proof": False, "axioms_ok": True, "export_ok": True,
            "target": {"prop_ok": True, "oracles": [], "skip_proof": False}, "cheating": False}
    base.update(kw)
    return base


@pytest.mark.parametrize("fin,etiqueta", [
    (_fin(), "ACCEPTED"),
    (_fin(oracles=["skip_proof"]), "UNSOUND"),
    (_fin(axioms_ok=False), "UNSOUND"),
    (_fin(target={"prop_ok": False, "oracles": [], "skip_proof": False}), "STATEMENT_DRIFT"),
    (_fin(rc=1, final_json=False, target={"prop_ok": False}), "STATEMENT_DRIFT"),
    (_fin(rc=1, final_json=False, target={}), "PROOF_FAILED"),
    (_fin(rc=1, final_json=False, cheating=True, target={}), "UNSOUND"),
    (_fin(rc=-9, final_json=False), "TIMEOUT"),
    (_fin(final_json=False), "STATEMENT_DRIFT"),
])
def test_clasificacion(fin, etiqueta):
    assert TheoremVerifier.classify(fin)[0] == etiqueta


def test_verify_caminos_sin_isabelle(monkeypatch):
    v = TheoremVerifier("gd_n1")
    t = v.target()
    monkeypatch.setattr(v, "compile_final", lambda proof, lemmas="", work=None: {**_fin(), "build_s": 1.0, "errors": []})
    assert v.verify(t, {"proof": "by simp"}).outcome_label == "ACCEPTED"
    monkeypatch.setattr(v, "compile_final", lambda proof, lemmas="", work=None: {**_fin(rc=1, final_json=False, target={}), "build_s": 1.0, "errors": ["*** x"]})
    assert v.verify(t, {"proof": "by simp"}).outcome_label == "PROOF_FAILED"
    monkeypatch.setattr(v, "check_lemmas_in_kernel", lambda lemmas: ("failed", ["*** e"], [{"name": "a", "text": "lemma a: True by simp"}]))
    o = v.verify(t, {"proof": "by simp", "lemmas": 'lemma a: "True" by simp\nlemma b: "False" by simp'})
    assert o.outcome_label == "LEMMA_FAILED" and o.raw["verified_lemmas"][0]["name"] == "a" and o.raw["kind"] == "theorem"


def test_objetivo_modificado_en_disco(tmp_path, monkeypatch):
    v = TheoremVerifier("gd_n1")
    t = v.target()
    spec = dict(v.spec, concl=v.spec["concl"].replace("1/8", "1/7"))
    monkeypatch.setattr(v, "_load_spec", lambda: spec)
    assert v.verify(t, {"proof": "by simp"}).outcome_label == "STATEMENT_DRIFT"


def test_certificados_exactos():
    sys.path.insert(0, str(HERE / "tools"))
    import gd_certificados as gc
    for obj in ("gd_n1", "gd_const_n2", "gd_const_n3"):
        cert = gc.cargar(obj)
        assert gc.verificar(cert) == (True, "certificado válido")
        assert gc.identidad_aleatoria(cert)[0]


def test_demostraciones_generadas_pasan_el_filtro():
    for obj in ("gd_n1", "gd_const_n2"):
        for v in "ABC":
            p = TARGETS / "gd_cert" / f"{obj}.proof_{v}.txt"
            txt = p.read_text()
            assert check_proof(txt) is None, p
            assert txt.count("(") == txt.count(")") and txt.count('"') % 2 == 0


@pytest.mark.isabelle
def test_isabelle_cota_superior_gd_n1():
    v = TheoremVerifier("gd_n1")
    t = v.target()
    oks = [v.verify(t, {"proof": p.read_text()}).outcome_label for p in sorted((TARGETS / "gd_cert").glob("gd_n1.proof_*.txt"))]
    assert "ACCEPTED" in oks


@pytest.mark.isabelle
def test_isabelle_controles():
    v = TheoremVerifier("gd_n1")
    t = v.target()
    assert v.verify(t, {"proof": "by simp"}).outcome_label == "PROOF_FAILED"
    assert v.classify(v.compile_final("sorry"))[0] == "UNSOUND"


def test_cortesia_espera_compilaciones_ajenas(monkeypatch):
    v = TheoremVerifier("gd_n1")
    estados = iter([True, True, False, False, False, False, False, False, False, False, False, False])
    monkeypatch.setattr(TheoremVerifier, "compilaciones_ajenas", staticmethod(lambda: next(estados)))
    monkeypatch.setattr("unirl.gd_isabelle.time.sleep", lambda s: None)
    assert v.esperar_turno(quieto_s=4, paso_s=2) >= 0
    assert TheoremVerifier("gd_n1", cortesia=False).esperar_turno() == 0.0


def test_parse_lemmas_mal_cerrado_no_se_come_la_prueba():
    v = TheoremVerifier("gd_n1")
    p = v.parse("LEMMAS: <<<>>\nPROOF: <<< proof -\n  show ?thesis by simp\nqed >>>")
    assert p["lemmas"] == "" and p["proof"].startswith("proof -") and p["proof"].endswith("qed")
    p = v.parse("PROOF: <<< by simp >>>\nLEMMAS: <<< lemma a: True by simp >>>")
    assert p["proof"] == "by simp" and p["lemmas"].startswith("lemma a")
    assert check_lemma_block(">>\nPROOF: <<< by simp")[0] == "INVALID_PROPOSAL"
