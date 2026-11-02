"""Etapa 4: recompensa r_V (métrica), legibilidad y reglas de admisión al cuaderno."""

from pathlib import Path

import pytest

from unirl import cuaderno, recompensa as R

HERE = Path(__file__).resolve().parent
PRIV = HERE / "fixtures" / "pruebas_privadas"
SMT7 = "by (smt (verit, del_insts) contr fp fq hp hq k1 mult_le_cancel_right1)"
NADIE = set()  # línea base en la que el martillo no resuelve nada


# ----------------------------------------------------------------------------- legibilidad y opacidad


@pytest.mark.parametrize("prueba,opaca", [
    (SMT7, True),
    ("proof -\n  show ?thesis by (smt (verit) a b c d e)\nqed", True),               # envuelta
    ("proof -\n  have \"P\" by (smt a b c d e)\n  then show ?thesis by simp\nqed", True),  # + cierre trivial
    ("using a b c by (metis d e)", True),                                           # los del using cuentan
    ("apply (smt a b c d e)\ndone", True),
    ("by (metis mult_left_mono)", False),                                           # pocos hechos
    ("by (smt a b c d)", False),                                                    # justo en el umbral (4)
    ("by (induction n) simp_all", False),                                           # una línea legible
    ("apply (induction n)\n apply simp\n apply (smt a b c d e)\ndone", False),       # guion con inducción
    ("proof -\n  have \"P\" by (smt a b c d e)\n  have \"Q\" by (metis a b c d e f)\n  show ?thesis using P Q by linarith\nqed", False),
])
def test_una_linea_opaca(prueba, opaca):
    assert R.legibilidad(prueba)["una_linea_opaca"] is opaca


def test_legibilidad_de_una_prueba_estructurada():
    if not (PRIV / "orden_1_lineal.txt").exists():
        pytest.skip("falta la prueba de referencia privada (no se versiona)")
    leg = R.legibilidad((PRIV / "orden_1_lineal.txt").read_text())
    assert leg["pasos_explicitos"] == 4 and leg["invocaciones"] == 4 and leg["opacas"] == 0
    assert leg["invocaciones_no_triviales"] == 3 and not leg["una_linea"] and not leg["una_linea_opaca"]


def test_opacidad_cuenta_hechos_con_atributos_y_opciones():
    toks = __import__("unirl.verifiers", fromlist=["tokenize_outer"]).tokenize_outer(
        "(metis (no_types, lifting) a[of x] b(2) c[symmetric] d e)")
    assert R.opacidad(toks[1:-1]) == (True, 5)


def test_martillo_en_la_meta():
    assert R.martillo_en_la_meta("by martillo") and R.martillo_en_la_meta("by (martillo 1)")
    assert not R.martillo_en_la_meta("proof (induction n)\n  case 0 show ?case by martillo\nnext\n  case (Suc n) show ?case by simp\nqed")


# ----------------------------------------------------------------------------- recompensa


def test_recompensa_aceptada_legible():
    if not (PRIV / "orden_1_lineal.txt").exists():
        pytest.skip("falta la prueba de referencia privada (no se versiona)")
    r = R.recompensa("orden_1_lineal", "ACCEPTED", (PRIV / "orden_1_lineal.txt").read_text(), resueltos=NADIE)
    assert r["r"] == 1 + R.BONO and r["motivo"] == "aceptada" and r["rho"] == 1


def test_recompensa_cero_si_el_martillo_resuelve_el_peldano():
    r = R.recompensa("pf_3_unicidad", "ACCEPTED", "proof -\n  show ?thesis by simp\nqed", resueltos={"pf_3_unicidad"})
    assert r["r"] == 0 and r["motivo"] == "resuelto_por_martillo"


def test_recompensa_cero_por_una_linea_opaca_aunque_el_kernel_la_acepte():
    r = R.recompensa("orden_1_lineal", "ACCEPTED", SMT7, resueltos=NADIE)
    assert r["r"] == 0 and r["motivo"] == "una_linea_opaca" and r["aceptada"]


def test_recompensa_cero_por_martillo_en_la_meta():
    r = R.recompensa("orden_1_lineal", "ACCEPTED", "by martillo", prueba_final="by (induction n) simp_all",
                     marcas=1, cerradas=1, resueltos=NADIE)
    assert r["r"] == 0 and r["motivo"] == "martillo_en_la_meta"


def test_recompensa_parcial_por_pasos_cerrados():
    p = "proof -\n  have \"P\" by martillo\n  have \"Q\" by martillo\n  show ?thesis by martillo\nqed"
    r = R.recompensa("orden_1_lineal", "PROOF_FAILED", p, marcas=3, cerradas=2, resueltos=NADIE)
    assert r["motivo"] == "parcial" and r["r"] == pytest.approx(2 / 3, abs=1e-4) and r["bono"] == 0


@pytest.mark.parametrize("etiqueta", ["STATEMENT_DRIFT", "UNSOUND", "SYNTAX_ERROR", "INVALID_PROPOSAL"])
def test_recompensa_cero_sin_credito(etiqueta):
    r = R.recompensa("orden_1_lineal", etiqueta, "by martillo\n", marcas=2, cerradas=2, resueltos=NADIE)
    assert r["r"] == 0


def test_recompensa_texto_ilegible_no_rompe():
    r = R.recompensa("orden_1_lineal", "SYNTAX_ERROR", 'by (simp add: "sin cerrar)', resueltos=NADIE)
    assert r["r"] == 0 and r["legibilidad"] is None


def test_linea_base_de_otro_cuaderno_no_sirve(tmp_path, monkeypatch):
    monkeypatch.setattr(R, "RESULTADOS", tmp_path)
    with pytest.raises(R.LineaBaseDesactualizada):
        R.resueltos_por_martillo("abc123")
    (tmp_path / "martillo_linea_base_abc123.json").write_text(
        '{"cuaderno": "abc123", "filas": [{"id": "a", "resuelto_por_martillo": true}]}')
    assert R.resueltos_por_martillo("abc123", ["a"]) == {"a"}
    with pytest.raises(R.LineaBaseDesactualizada, match="no tiene"):
        R.resueltos_por_martillo("abc123", ["a", "b"])


def test_linea_base_del_repo_completa():
    from unirl import corpus
    ids = [p["id"] for p in corpus.usables()]
    assert R.resueltos_por_martillo("", ids) == {"pf_3_unicidad"}


# ----------------------------------------------------------------------------- admisión al cuaderno (sin Isabelle)


def test_alcance_de_un_lema():
    assert cuaderno.alcance('lemma l: "(x::real) <= x" by simp', "secante") == ("general", "")
    assert cuaderno.alcance('lemma l: "fst (biseccion f a b 0) = a" by simp', "biseccion")[0] == "biseccion"
    assert cuaderno.alcance('lemma l: "paso_newton f g x = x" by simp', "biseccion")[0] is None


@pytest.mark.parametrize("lema,motivo", [
    ('lemma a: "True" by simp\nlemma b: "True" by simp', "un lema a la vez"),
    ('lemma l: "True" sorry', "UNSOUND"),
    ('lemma ab: "True" by simp', "reservado"),             # etiqueta de una hipótesis del corpus
    ('lemma isarl_x: "True" by simp', "nombre no admitido"),
    ('lemma l: "paso_newton f g x = x" by simp', "constantes de newton"),
])
def test_admitir_lema_rechaza_sin_compilar(lema, motivo):
    r = cuaderno.admitir_lema(lema, "biseccion", juez=object())  # un juez que no sirve: no debe llegar a compilar
    assert not r["admitido"] and motivo in r["motivo"]


def test_admitir_lema_solo_train_y_sin_nombres_repetidos():
    assert "train" in cuaderno.admitir_lema('lemma l: "True" by simp', None, split="test", juez=object())["motivo"]
    r = cuaderno.admitir_lema('lemma l: "True" by simp', None, cuaderno_general='lemma l: "True" by simp', juez=object())
    assert not r["admitido"] and "ya tiene" in r["motivo"]


def test_admitir_error_comprueba_las_afirmaciones():
    def comprobar(xs):
        return {("metodo", "nlinarith"): False, ("hecho", "mult_left_mono"): True}
    bien = {"texto": "nlinarith no existe; usa mult_left_mono", "afirma": [
        {"tipo": "metodo", "nombre": "nlinarith", "existe": False}, {"tipo": "hecho", "nombre": "mult_left_mono", "existe": True}]}
    assert cuaderno.admitir_error(bien, "train", comprobar)["admitido"]
    falso = {"texto": "mult_left_mono no existe", "afirma": [{"tipo": "hecho", "nombre": "mult_left_mono", "existe": False}]}
    r = cuaderno.admitir_error(falso, "train", comprobar)
    assert not r["admitido"] and "falsa" in r["motivo"]
    assert not cuaderno.admitir_error(bien, "test", comprobar)["admitido"]
    assert not cuaderno.admitir_error({"texto": "x", "afirma": [{"tipo": "hecho", "nombre": "a b", "existe": True}]},
                                      "train", comprobar)["admitido"]


def test_estrategias_admision_contadores_y_descarte():
    assert not cuaderno.admitir_estrategia("inducción sobre n", {"split": "train", "aceptado": False})["admitido"]
    assert not cuaderno.admitir_estrategia("inducción sobre n", {"split": "test", "aceptado": True})["admitido"]
    e = cuaderno.admitir_estrategia("inducción sobre n", {"split": "train", "aceptado": True, "id": "ep1"})
    f = cuaderno.admitir_estrategia("acotar con valor medio", {"split": "train", "lemas_verificados": 1, "id": "ep2"})
    assert e["admitido"] and f["admitido"] and e["contadores"] == {"intentos": 0, "exitos": 0}
    for _ in range(5):
        cuaderno.registrar_uso_estrategia(e, True, "train")
        cuaderno.registrar_uso_estrategia(f, False, "train")
    with pytest.raises(ValueError):
        cuaderno.registrar_uso_estrategia(e, True, "test")
    vig, desc = cuaderno.descartar_estrategias([e, f])
    assert vig == [e] and desc == [f]


# ----------------------------------------------------------------------------- admisión con Isabelle


@pytest.mark.isabelle
def test_isabelle_admite_un_lema_general_verificado():
    r = cuaderno.admitir_lema('lemma prod_abs_mono: "0 \\<le> (c::real) \\<Longrightarrow> \\<bar>x\\<bar> \\<le> y '
                              '\\<Longrightarrow> c * \\<bar>x\\<bar> \\<le> c * y"\n  by (rule mult_left_mono)', "ordenes")
    assert r["admitido"] and r["alcance"] == "general", r


@pytest.mark.isabelle
def test_isabelle_admite_un_lema_de_metodo_con_su_preludio():
    r = cuaderno.admitir_lema('lemma bis_cero: "biseccion f a b 0 = (a, b)"\n  by simp', "biseccion")
    assert r["admitido"] and r["alcance"] == "biseccion", r


@pytest.mark.isabelle
@pytest.mark.parametrize("lema", [
    'lemma falso: "(x::real) \\<le> x - 1"\n  by simp',                     # el cuaderno rechaza un lema no verificado
    'lemma usa_contexto: "(a::real) \\<le> b"\n  using ab by simp',          # dependía de la hipótesis ab del peldaño
    'lemma mult_left_mono: "(0::real) \\<le> 0"\n  by simp',                 # taparía un hecho de Isabelle
])
def test_isabelle_rechaza_lemas_no_independientes(lema):
    r = cuaderno.admitir_lema(lema, "biseccion")
    assert not r["admitido"], r
