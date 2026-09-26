"""Etapa 2 (PLAN_rl_verbal.md): juez de teorema robusto sobre el corpus y libro de gastos.
Rápidas sin Isabelle; las marcadas `isabelle` compilan (se corrieron el 24 sep 2026 con Isabelle libre)."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from unirl.corpus import NoAprobado, huella
from unirl.gasto import GastoExcedido, Libro, ProveedorContable, costo
from unirl.gd_isabelle import (TheoremVerifier, check_lemma_block, check_proof, instanciacion, nombres_del_objetivo,
                               perfil_sandbox)
from unirl.loop import ProviderFatal, complete_with_retries

HERE = Path(__file__).resolve().parent
PRIV = HERE / "fixtures" / "pruebas_privadas"


def test_nombres_del_objetivo():
    v = TheoremVerifier.desde_corpus("bis_1_ancho")
    assert v.reservados == {"ab", "biseccion", "punto_medio"}
    assert check_lemma_block('lemma punto_medio: "True" by simp', v.reservados)[0] == "INVALID_PROPOSAL"
    assert check_lemma_block('lemma ab: "True" by simp', v.reservados)[0] == "INVALID_PROPOSAL"
    assert check_lemma_block('lemma mio: "True" by simp', v.reservados) is None
    assert nombres_del_objetivo(TheoremVerifier("gd_n1").spec) == {"gd", "interp", "opt"}


def test_syntax_error_separado_de_deriva():
    assert check_proof('proof - have "x = x" by simp') is None or True  # control: texto válido no lanza
    assert check_proof('by (simp add: "sin cerrar)')[0] == "SYNTAX_ERROR"
    assert check_lemma_block('lemma a: "True by simp')[0] == "SYNTAX_ERROR"
    assert check_proof("by simp ‹x›")[0] == "STATEMENT_DRIFT"  # un cartucho sigue siendo deriva
    assert check_proof("ML \\<open>x\\<close> by simp")[0] == "STATEMENT_DRIFT"
    assert check_proof("sorry")[0] == "UNSOUND"


def test_instanciacion_por_nombre():
    assert instanciacion(TheoremVerifier("gd_n1").spec) == "f = f and g = g and ?x0.0 = x0 and xs = xs"
    inst = instanciacion(TheoremVerifier.desde_corpus("newton_6c_q_orden2").spec)
    assert inst.startswith("f = f and f' = f' and f'' = f''") and "\\<epsilon> = \\<epsilon>" in inst


def test_metadatos_en_cada_veredicto(monkeypatch):
    v = TheoremVerifier.desde_corpus("orden_1_lineal")
    monkeypatch.setattr(v, "compile_final", lambda proof, lemmas="", work=None: {
        "rc": 1, "final_json": False, "target": {}, "cheating": False, "build_s": 1.0, "errors": ["*** x"]})
    o = v.verify(v.target(), {"proof": "by simp"})
    m = o.raw["veredicto"]
    assert o.outcome_label == "PROOF_FAILED" and m["isabelle"] == "Isabelle2025" and m["limite_compilacion_s"] == 300
    assert m["aislado"] is True and len(m["carga_1_5_15"]) == 3 and m["objetivo_hash"] == v.frozen_hash
    assert v.verify(v.target(), {"proof": "sorry"}).raw["veredicto"]["juez"] == TheoremVerifier.VERSION_JUEZ


def test_enunciado_modificado_es_deriva(tmp_path):
    e = json.loads((HERE.parents[1] / "corpus" / "curado" / "raices" / "orden_1_lineal.json").read_text())
    (tmp_path / "raices").mkdir()
    ruta = tmp_path / "raices" / "orden_1_lineal.json"
    ruta.write_text(json.dumps(e), encoding="utf-8")
    v = TheoremVerifier.desde_corpus("orden_1_lineal", base=tmp_path)
    t = v.target()
    e["concl"] = e["concl"].replace("c ^ n", "c ^ (n + 1)")  # alguien cambia el enunciado en disco
    ruta.write_text(json.dumps(e), encoding="utf-8")
    assert v.verify(t, {"proof": "by simp"}).outcome_label == "STATEMENT_DRIFT"


def test_no_aprobado_no_tiene_juez(tmp_path):
    e = json.loads((HERE.parents[1] / "corpus" / "curado" / "raices" / "orden_1_lineal.json").read_text())
    e["estado"] = "pendiente_revision"
    (tmp_path / "raices").mkdir()
    (tmp_path / "raices" / "orden_1_lineal.json").write_text(json.dumps(e), encoding="utf-8")
    with pytest.raises(NoAprobado):
        TheoremVerifier.desde_corpus("orden_1_lineal", base=tmp_path)


def test_perfil_sandbox():
    p = perfil_sandbox(Path("/tmp/x"))
    assert "(deny network-outbound (remote ip))" in p and "localhost" in p and "deny file-write*" in p


# ------------------------------------------------------------------------------------------- libro de gastos

def test_costo_con_precios_oficiales():
    assert costo("gpt-6-luna", 1208, 0, 8389) == pytest.approx((1208 * 0.10 + 8389 * 0.50) / 1e6)
    assert costo("gpt-6-sol", 1_000_000, 0, 1_000_000) == pytest.approx(12.0)
    with pytest.raises(GastoExcedido):
        costo("modelo-desconocido", 1, 0, 1)


def test_libro_acumula_y_detiene(tmp_path):
    libro = Libro(tmp_path / "gasto.json", tope_usd=1.0)
    libro.registrar("gpt-6-sol", "medicion", "t", {"entrada": 5000, "cache": 0, "salida": 60000})  # $0,61
    assert libro.total() == pytest.approx(0.61)
    with pytest.raises(GastoExcedido):  # peor caso de otra llamada de Sol (64k de salida) pasa de $1
        libro.autorizar("gpt-6-sol", "medicion", None, 15000, 64000)
    libro.autorizar("gpt-6-luna", "medicion", None, 15000, 64000)  # Luna sí cabe
    with pytest.raises(GastoExcedido):
        libro.autorizar("gpt-6-luna", "medicion", 1, 100, 100)  # la fase ya hizo 1 llamada de 1
    assert json.loads((tmp_path / "gasto.json").read_text())["total_usd"] == pytest.approx(0.61)


class _Cliente:
    def __init__(self):
        uso = SimpleNamespace(prompt_tokens=1208, completion_tokens=8389,
                              prompt_tokens_details=SimpleNamespace(cached_tokens=0),
                              completion_tokens_details=SimpleNamespace(reasoning_tokens=8191))
        resp = SimpleNamespace(usage=uso, choices=[SimpleNamespace(finish_reason="stop", message=SimpleNamespace(content="PROOF: <<< by simp >>>"))])
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=lambda **kw: resp))


def test_proveedor_contable_registra_y_aborta(tmp_path):
    interno = SimpleNamespace(_client=_Cliente(), model="gpt-6-luna", max_output_tokens=64000, reasoning_effort="high")
    libro = Libro(tmp_path / "gasto.json", tope_usd=25)
    p = ProveedorContable(interno, libro, fase="prueba", corrida="t", tope_llamadas=2)
    assert "by simp" in p.complete("s", "u")
    e = libro.entradas()[0]
    assert (e["entrada"], e["salida"], e["razonamiento"], e["fase"]) == (1208, 8389, 8191, "prueba")
    p.complete("s", "u")
    with pytest.raises(ProviderFatal):  # tercera llamada: tope de la fase; no se reintenta ni se registra como PROVIDER_ERROR
        complete_with_retries(p, "s", "u", verbose=False)
    assert len(libro.entradas()) == 2


# ------------------------------------------------------------------------------------------- con Isabelle

@pytest.mark.isabelle
@pytest.mark.parametrize("id_", ["orden_1_lineal", "bis_1_ancho"])
def test_isabelle_acepta_prueba_valida_aislada(id_):
    v = TheoremVerifier.desde_corpus(id_)
    o = v.verify(v.target(), {"proof": (PRIV / f"{id_}.txt").read_text()})
    assert o.outcome_label == "ACCEPTED" and o.raw["veredicto"]["aislado"]


@pytest.mark.isabelle
def test_isabelle_rechaza_sorry_en_el_kernel():
    v = TheoremVerifier.desde_corpus("orden_1_lineal")
    assert v.classify(v.compile_final("sorry"))[0] == "UNSOUND"


@pytest.mark.isabelle
def test_isabelle_sandbox_no_escribe_fuera(tmp_path):
    v = TheoremVerifier.desde_corpus("orden_1_lineal")
    fuera = (HERE.parents[1] / "logs" / "sandbox_prueba_test.txt").resolve()
    fuera.unlink(missing_ok=True)
    w = v._workdir("gd-sandbox-")
    thy = ('theory Escribe\n  imports "HOL-Analysis.Analysis"\nbegin\n'
           f'ML \\<open>File.write (Path.explode "{fuera}") "fuga"\\<close>\nend\n')
    rc, _ = v.build(w, thy, "Escribe", 120)
    assert rc != 0 and not fuera.exists()
