"""Corpus de búsqueda de raíces: coherencia de las entradas y la puerta de aprobación (sin Isabelle)."""

import json

import pytest

from unirl.corpus import CORPUS, NoAprobado, cargar, exigir_usable, huella, usables

TEST = {"secante", "regula_falsi"}


def test_corpus_carga_y_hashes():
    ents = cargar("raices")
    assert len(ents) == 48
    assert all(huella(e) == e["frozen_hash"] for e in ents)


def test_split_por_metodo_con_peldanos_bajos():
    ents = cargar("raices")
    assert {e["metodo"] for e in ents if e["split"] == "test"} == TEST
    assert all(e["split"] == "test" for e in ents if e["metodo"] in TEST)
    for m in TEST:  # el test incluye los peldaños bajos de cada método, no solo los altos
        assert min(e["dificultad"] for e in ents if e["metodo"] == m) <= 2


def _entrada(id_, estado):
    e = {"id": id_, "name": id_, "kind": "theorem", "metodo": "prueba", "peldano": 1, "split": "train", "estado": estado,
         "dificultad": 1, "fuente": "prueba", "dependencias": [], "imports": '"HOL-Analysis.Analysis"',
         "session_parent": "HOL-Analysis", "prelude": "", "fixes": "x :: real", "assumes": 'h: "0 \\<le> x"',
         "concl": "0 \\<le> x", "statement_es": "prueba"}
    e["frozen_hash"] = huella(e)
    return e


def test_el_cargador_rechaza_lo_no_aprobado(tmp_path):
    (tmp_path / "t").mkdir()
    for id_, estado in (("ok", "aprobado"), ("pendiente", "pendiente_revision"), ("conj", "conjetura")):
        (tmp_path / "t" / f"{id_}.json").write_text(json.dumps(_entrada(id_, estado)), encoding="utf-8")
    assert [e["id"] for e in usables("t", base=tmp_path)] == ["ok"]
    assert exigir_usable("ok", "t", base=tmp_path)["id"] == "ok"
    for id_ in ("pendiente", "conj", "no_existe"):
        with pytest.raises(NoAprobado):
            exigir_usable(id_, "t", base=tmp_path)


def test_el_corpus_real_rechaza_sus_peldanos_no_aprobados():
    for e in cargar("raices"):
        if e["estado"] != "aprobado":
            with pytest.raises(NoAprobado):
                exigir_usable(e["id"])
            assert e["id"] not in {u["id"] for u in usables("raices")}


def test_versiones_clasicas_enlazadas():
    ents = {e["id"]: e for e in cargar("raices")}
    for e in ents.values():
        assert e["version"] in ("clasica", "debilitada")
        if e["version"] == "debilitada":
            assert e["debilitacion"] and ents[e["version_clasica"]]["version"] == "clasica"
            assert e["id"] in ents[e["version_clasica"]]["debil_de"]


def test_comprobaciones_completas():
    ents = cargar("raices")
    val = json.loads((CORPUS / "raices" / "validacion_isabelle.json").read_text(encoding="utf-8"))
    for e in ents:
        assert val[e["metodo"]]["ok"] and e["id"] in val[e["metodo"]]["peldanos"], e["id"]
        cn = e["comprobacion_numerica"]
        assert cn["casos"] > 0 and cn["cumplen"] == cn["casos"], e["id"]


def test_revision_lista_todos():
    rev = (CORPUS / "raices" / "revision_enunciados.md").read_text(encoding="utf-8")
    for e in cargar("raices"):
        assert f"### `{e['id']}`" in rev and e["frozen_hash"] in rev


def test_aprobacion_registrada():
    ents = cargar("raices")
    pend = {e["id"] for e in ents if e["estado"] == "pendiente_revision"}
    assert pend == set()
    assert {e["id"]: e for e in ents}["pf_6p_a_posteriori"]["dependencias"] == ["pf_2_dentro"]
    assert {e["id"]: e for e in ents}["secante_6c_orden_phi"]["analogo"] == "newton_6c_q_orden2"
    for e in ents:
        if e["estado"] == "aprobado":
            assert e["aprobacion"]["por"] == "Carlos Manuel Orrego Franco"
    assert len(usables("raices")) == len(ents) - len(pend)
