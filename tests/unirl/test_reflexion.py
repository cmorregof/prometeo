"""Etapas 5 y 6: episodio con reflexión (proponente simulado, sin costo), cuaderno (recuperación, contadores,
congelado) y destilación."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from unirl import corpus, cuaderno as C, experimentos as X, martillo as M, reflexion as RF
from unirl.gd_isabelle import TheoremVerifier
from unirl.loop import ProviderFatal

HERE = Path(__file__).resolve().parent
PRIV = HERE / "fixtures" / "pruebas_privadas"


class Simulado:
    """Proponente simulado: devuelve respuestas en orden y guarda los prompts que vio."""
    model = "simulado"

    def __init__(self, respuestas):
        self.respuestas, self.prompts, self.ultimo_uso = list(respuestas), [], {"usd": 0.001}

    def complete(self, system, user):
        self.prompts.append(user)
        r = self.respuestas.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


def falso_martillo(aceptar_si: str):
    """martillo_en_pasos sin Isabelle: acepta si la prueba contiene `aceptar_si`."""
    def f(juez, prueba, cuaderno_hash="", cache=None, lemas="", biblioteca=""):
        ok = aceptar_si in prueba
        o = SimpleNamespace(outcome_label="ACCEPTED" if ok else "PROOF_FAILED", accepted=ok, cost_s=1.0,
                            raw={"errors": [] if ok else ['*** Undefined method: "nlinarith"'], "verified_lemmas": [],
                                 "veredicto": {"carga_1_5_15": [1.0, 1.0, 1.0]}, "reason": "x"})
        return {"marcas": 0, "cerradas": 0, "pasos": [], "prueba_final": prueba, "outcome": o,
                "veredicto_juez": o.outcome_label, "martillo_s": 0.0, "espera_candado_s": 0.0, "suspension_s": 0.0,
                "errores": []}
    return f


@pytest.fixture(autouse=True)
def cuaderno_real_intacto():
    """Ninguna prueba puede escribir en el cuaderno real (25 sep: una lo hizo por un valor por defecto mal ligado)."""
    def foto():
        return {f.name: f.read_bytes() for f in C.DIR.iterdir() if f.is_file()} if C.DIR.exists() else {}
    antes = foto()
    yield
    assert foto() == antes, "una prueba modificó el cuaderno real"


@pytest.fixture
def spec():
    return corpus.exigir_usable("orden_1_lineal")


@pytest.fixture
def sin_isabelle(monkeypatch):
    monkeypatch.setattr(M, "martillo_en_pasos", falso_martillo("BIEN"))
    consultas = []
    monkeypatch.setattr(M, "consultar", lambda juez, cs, tope=4, biblioteca="": consultas.append(cs) or
                        [{"tipo": c["tipo"], "consulta": c["texto"], "existe": True} for c in cs[:tope]])
    return consultas


# ----------------------------------------------------------------------------- respuesta y prompt


def test_leer_respuesta():
    juez = TheoremVerifier.desde_corpus("orden_1_lineal")
    r = RF.leer_respuesta(juez, "CONSULTAS: <<< buscar: name: mono | hecho: mult_left_mono\nmetodo: argo >>>")
    assert [c["tipo"] for c in r["consultas"]] == ["buscar", "hecho", "metodo"] and not r["proof"]
    r = RF.leer_respuesta(juez, "REFLEXION: <<< faltó la inducción >>>\nLEMMAS: <<< lemma l: \"True\" by simp >>>\n"
                                "PROOF: <<< by (induction n) simp_all >>>")
    assert r["reflexion"] == "faltó la inducción" and r["proof"].startswith("by (induction") and r["lemmas"].startswith("lemma")
    largo = RF.leer_respuesta(juez, "REFLEXION: <<< " + "palabra " * 400 + ">>> PROOF: <<< by simp >>>")
    assert len(largo["reflexion"].split()) == RF.MAX_REFLEXION_PALABRAS + 1


def test_leer_respuesta_sin_delimitadores():
    """Así respondió Luna en el humo del 25 sep: REFLEXION y PROOF sin <<< >>>."""
    juez = TheoremVerifier.desde_corpus("orden_1_lineal")
    texto = ("REFLEXION: El segundo paso repetía el término inicial.\n\nPROOF:\nproof (induction n)\n  case 0\n"
             "  then show ?case by simp\nnext\n  case (Suc n)\n  show ?case by simp\nqed\n")
    r = RF.leer_respuesta(juez, texto)
    assert r["proof"].startswith("proof (induction n)") and r["proof"].endswith("qed") and not r["formato_estricto"]
    assert r["reflexion"] == "El segundo paso repetía el término inicial."
    r2 = RF.leer_respuesta(juez, "PROOF: <<< by simp >>>\nLEMMAS:\nlemma l: \"True\" by simp")
    assert r2["proof"] == "by simp" and r2["lemmas"].startswith("lemma l") and not r2["formato_estricto"]
    assert RF.leer_respuesta(juez, "REFLEXION: <<< x >>>\nPROOF: <<< by simp >>>")["formato_estricto"]
    r3 = RF.leer_respuesta(juez, "PROOF:\n```isabelle\nby simp\n```")
    assert r3["proof"] == "by simp"


def test_prompt_por_configuracion(spec):
    g = C.Cuaderno().glosario_compacto()
    b0 = RF.construir_prompt(spec, RF.CONFIGS["B0"], g, "", [], [], 0, 1)
    b = RF.construir_prompt(spec, RF.CONFIGS["B"], g, "", [], [], 2, 1)
    c2 = RF.construir_prompt(spec, RF.CONFIGS["C"], g, "", [], [{"intento": 1, "proof": "by simp", "feedback": "PROOF_FAILED: x"}], 2, 2)
    assert "nlinarith" not in b0 and "CONSULTAS" not in b0 and "REFLEXION" not in b0
    assert "nlinarith" in b and "CONSULTAS (te quedan 2 turnos" in b
    assert "REFLEXION: <<<" in c2 and "intento 1" in c2 and "PROOF_FAILED: x" in c2
    for p in (b0, b, c2):
        assert spec["concl"] in p and "by martillo" in p
    assert "comentario breve en español" in RF.SISTEMA


# ----------------------------------------------------------------------------- episodio


def test_episodio_consulta_falla_y_acepta(tmp_path, spec, sin_isabelle):
    prov = Simulado(["CONSULTAS: <<< hecho: mult_left_mono >>>",
                     "PROOF: <<< by nlinarith >>>",
                     "REFLEXION: <<< nlinarith no existe >>>\nPROOF: <<< proof -\n  (* BIEN *)\n  show ?thesis by simp\nqed >>>"])
    reg = tmp_path / "llamadas.jsonl"
    ep = RF.episodio(spec, RF.CONFIGS["C"], prov, reg, {"corrida": "t"}, resueltos=set(), verbose=False)
    assert ep["aceptado"] and ep["intento_exito"] == 2 and ep["llamadas"] == 3 and ep["consultas"] == 1
    lineas = [json.loads(l) for l in reg.read_text().splitlines()]
    assert [l["tipo"] for l in lineas] == ["consulta", "intento", "intento"]
    assert lineas[2]["reflexion"] == "nlinarith no existe" and lineas[2]["r_V"] == 2.0
    assert "RESULTADOS DE TUS CONSULTAS" in prov.prompts[1] and "mult_left_mono → existe" in prov.prompts[1]
    assert "Undefined method" in prov.prompts[2]  # el error del kernel vuelve al modelo


def test_episodio_respeta_turnos_de_consulta_y_k(tmp_path, spec, sin_isabelle):
    prov = Simulado(["CONSULTAS: <<< hecho: a >>>"] * 3 + ["PROOF: <<< by simp >>>"] * 4)
    ep = RF.episodio(spec, RF.CONFIGS["C"], prov, tmp_path / "r.jsonl", {}, resueltos=set(), verbose=False)
    # 2 turnos de consulta; la 3.ª respuesta con solo CONSULTAS gasta un intento (INVALID_PROPOSAL)
    assert ep["consultas"] == 2 and ep["intentos"] == 4 and not ep["aceptado"] and ep["llamadas"] == 6
    assert len(sin_isabelle) == 2


def test_episodio_b0_un_intento_sin_consultas(tmp_path, spec, sin_isabelle):
    prov = Simulado(["CONSULTAS: <<< hecho: a >>>"])
    ep = RF.episodio(spec, RF.CONFIGS["B0"], prov, tmp_path / "r.jsonl", {}, resueltos=set(), verbose=False)
    assert ep["llamadas"] == 1 and ep["intentos"] == 1 and ep["consultas"] == 0 and not sin_isabelle


def test_episodio_error_de_proveedor(tmp_path, spec, sin_isabelle, monkeypatch):
    monkeypatch.setattr(RF, "complete_with_retries", lambda p, s, u, verbose=True: None)
    ep = RF.episodio(spec, RF.CONFIGS["C"], Simulado([]), tmp_path / "r.jsonl", {}, resueltos=set(), verbose=False)
    assert ep["intentos"] == 4 and not ep["aceptado"]
    monkeypatch.setattr(RF, "complete_with_retries", lambda *a, **k: (_ for _ in ()).throw(ProviderFatal("sin créditos")))
    with pytest.raises(ProviderFatal):
        RF.episodio(spec, RF.CONFIGS["C"], Simulado([]), tmp_path / "r.jsonl", {}, resueltos=set(), verbose=False)


def test_episodio_sin_credito_si_el_martillo_resuelve(tmp_path, spec, sin_isabelle):
    prov = Simulado(["PROOF: <<< proof -\n  (* BIEN *)\n  show ?thesis by simp\nqed >>>"])
    ep = RF.episodio(spec, RF.CONFIGS["C"], prov, tmp_path / "r.jsonl", {}, resueltos={"orden_1_lineal"}, verbose=False)
    assert ep["aceptado"] and ep["r_V_max"] == 0


# ----------------------------------------------------------------------------- cuaderno


def _cuaderno(tmp_path) -> C.Cuaderno:
    c = C.Cuaderno(tmp_path)
    c.errores = C.Cuaderno().errores  # el glosario sembrado
    c.lemas = [{"nombre": "abs_mult_mono", "texto": 'lemma abs_mult_mono: "0 \\<le> (c::real) \\<Longrightarrow> '
                "\\<bar>x\\<bar> \\<le> y \\<Longrightarrow> c * \\<bar>x\\<bar> \\<le> c * y\"\n  by (rule mult_left_mono)",
                "alcance": "general", "procedencia": {}},
               {"nombre": "bis_cero", "texto": 'lemma bis_cero: "biseccion f a b 0 = (a, b)"\n  by simp',
                "alcance": "biseccion", "procedencia": {}}]
    c.estrategias = [{"texto": "inducción sobre n con el paso de la recurrencia", "topico": "induccion",
                      "contadores": {"intentos": 0, "exitos": 0}}]
    return c


def test_recuperacion_respeta_alcance_y_presupuesto(tmp_path, spec):
    c = _cuaderno(tmp_path)
    sel = c.recuperar(spec, ("errores", "lemas", "estrategias"))
    assert [l["nombre"] for l in sel["lemas"]] == ["abs_mult_mono"]  # bis_cero es de bisección: no aplica a órdenes
    assert sel["estrategias"] and "abs_mult_mono" in C.Cuaderno.biblioteca(sel)
    txt = C.Cuaderno.render(sel)
    assert 'lemma abs_mult_mono: "0' in txt and "by (rule mult_left_mono)" not in txt  # se muestra el enunciado
    bis = corpus.exigir_usable("bis_1_ancho")
    assert {l["nombre"] for l in c.recuperar(bis, ("lemas",))["lemas"]} == {"abs_mult_mono", "bis_cero"}
    assert not c.recuperar(spec, ())["lemas"]


def test_congelar_es_de_solo_lectura_y_conserva_el_hash(tmp_path, monkeypatch):
    monkeypatch.setattr(C, "CONGELADOS", tmp_path / "congelados")
    c = _cuaderno(tmp_path / "vivo")
    c.guardar()
    f = c.congelar()
    assert f.hash() == c.hash() and f.solo_lectura and f.hash_lemas() == c.hash_lemas() != ""
    with pytest.raises(PermissionError):
        f.guardar()


def test_contadores_de_errores_por_mensaje_del_kernel(tmp_path):
    c = _cuaderno(tmp_path)
    vistos = c.registrar_errores_de_intentos(['*** Undefined method: "nlinarith" (line 3)', "*** Undefined fact: \"sq_nonneg\""],
                                             "ep1", "train")
    assert set(vistos) == {"E001", next(e["id"] for e in c.errores["errores"] if e.get("lean") == "sq_nonneg")}
    assert not c.registrar_errores_de_intentos(['*** Undefined method: "nlinarith"'], "ep2", "test")


def test_destilacion_admite_solo_lo_comprobado(tmp_path, monkeypatch):
    c = _cuaderno(tmp_path)
    real = {"positivity": False, "mult_left_mono": True}  # lo que diría Isabelle
    original = C.admitir_error
    monkeypatch.setattr(C, "admitir_error", lambda e, split: original(
        e, split, comprobar=lambda xs: {(x["tipo"], x["nombre"]): real[x["nombre"]] for x in xs}))
    prov = Simulado(["ERRORES: <<<\ntexto: positivity no existe; usa zero_le_power2 || afirma: no_existe metodo positivity\n"
                     "texto: mult_left_mono no existe || afirma: no_existe hecho mult_left_mono\n>>>\n"
                     "ESTRATEGIAS: <<<\norigen: a#1 || topico: induccion || texto: inducción con also/finally\n"
                     "origen: b#1 || topico: acotar || texto: acotar por valor medio\n>>>"])
    eps = [{"episodio_id": "a#1", "peldano": "a", "aceptado": True, "intento_exito": 1},
           {"episodio_id": "b#1", "peldano": "b", "aceptado": False, "intento_exito": None}]
    monkeypatch.setattr(X, "complete_with_retries", lambda p, s, u, **k: p.complete(s, u))
    res = X.destilar(prov, c, eps, [], tmp_path / "r.jsonl", {"corrida": "t"})
    assert res["errores_admitidos"] == ["positivity no existe; usa zero_le_power2"]
    assert res["estrategias_admitidas"] == ["inducción con also/finally"]  # b#1 no se aceptó ni aportó lemas
    assert c.estrategias[-1]["topico"] == "induccion" and c.errores["errores"][-1]["clase"] == "aprendido"


def test_orden_de_train_y_test():
    tr = X.peldanos("train")
    assert [p["metodo"] for p in tr][:1] == ["biseccion"] and len(tr) == 32
    assert tr.index(next(p for p in tr if p["id"] == "bis_5_cota")) < tr.index(next(p for p in tr if p["id"] == "bis_5c_cota_uniforme"))
    assert len(X.peldanos("test")) == 16


# ----------------------------------------------------------------------------- con Isabelle (sin costo)


@pytest.mark.isabelle
def test_isabelle_episodio_simulado_con_martillo_y_consulta(tmp_path, spec):
    """Episodio real (juez, martillo, consulta) con respuestas escritas a mano: un intento que falla y la prueba de
    referencia con su paso inductivo marcado `by martillo`."""
    buena = (PRIV / "orden_1_lineal.txt").read_text().replace("by (rule mult_left_mono)", "by martillo")
    prov = Simulado(["CONSULTAS: <<< buscar: name: mult_left_mono | metodo: nlinarith >>>",
                     "PROOF: <<< by nlinarith >>>",
                     f"REFLEXION: <<< nlinarith es de Lean; hace falta inducción >>>\nPROOF: <<< {buena} >>>"])
    reg = tmp_path / "llamadas.jsonl"
    ep = RF.episodio(spec, RF.CONFIGS["C"], prov, reg, {"corrida": "t"}, cache=M.Cache(tmp_path / "c.sqlite"),
                     resueltos=set(), verbose=False)
    lineas = [json.loads(l) for l in reg.read_text().splitlines()]
    assert ep["aceptado"] and ep["intento_exito"] == 2, lineas[-1].get("feedback")
    consulta = lineas[0]["resultados"]
    assert consulta[0]["resultados"] and consulta[1]["existe"] is False
    assert lineas[1]["etiqueta"] == "PROOF_FAILED" and "nlinarith" in lineas[1]["feedback"]
    assert lineas[2]["marcas"] == 1 and lineas[2]["cerradas"] == 1 and lineas[2]["r_V"] == 2.0
    assert lineas[2]["legibilidad"]["opacas"] == 0


def test_construir_cuaderno_de_punta_a_punta_simulado(tmp_path, monkeypatch, sin_isabelle):
    """Dos peldaños de train con el proponente simulado: episodios, destilación, congelado y reanudación."""
    import shutil
    vivo = tmp_path / "cuaderno"
    vivo.mkdir()
    shutil.copy2(C.DIR / "errores.json", vivo / "errores.json")
    monkeypatch.setattr(C, "DIR", vivo)
    monkeypatch.setattr(C, "CONGELADOS", vivo / "congelados")
    monkeypatch.setattr(X, "RUNS", tmp_path / "runs")
    monkeypatch.setattr(X, "DESTILAR_CADA", 2)
    respuestas = ["PROOF: <<< proof -\n  (* BIEN *)\n  show ?thesis by simp\nqed >>>",       # bis_1: aceptado
                  "PROOF: <<< by nlinarith >>>",                                            # bis_2: falla ×4
                  "REFLEXION: <<< x >>>\nPROOF: <<< by nlinarith >>>", "PROOF: <<< by nlinarith >>>",
                  "PROOF: <<< by nlinarith >>>",
                  "ERRORES: <<<\n>>>\nESTRATEGIAS: <<<\norigen: bis_1_ancho#1 || topico: induccion || texto: inducir sobre n\n>>>"]
    prov = Simulado(respuestas)
    prov.libro = SimpleNamespace(total=lambda: 0.0)
    monkeypatch.setattr(X, "proveedor", lambda *a, **k: prov)
    monkeypatch.setattr(X, "complete_with_retries", lambda p, s, u, **k: p.complete(s, u))
    out = X.construir_cuaderno("simulado", ids=["bis_1_ancho", "bis_2_encaje"], verbose=False)
    eps = [json.loads(l) for l in (out / "episodios.jsonl").read_text().splitlines()]
    assert [e["peldano"] for e in eps] == ["bis_1_ancho", "bis_2_encaje"] and eps[0]["aceptado"] and not eps[1]["aceptado"]
    assert eps[1]["errores_vistos"] == ["E001"]  # Undefined method "nlinarith", contado en train
    fin = json.loads((out / "FIN.json").read_text())
    congelado = C.Cuaderno(Path(fin["carpeta"]), solo_lectura=True)
    assert congelado.hash() == fin["cuaderno"] and [e["texto"] for e in congelado.estrategias] == ["inducir sobre n"]
    assert congelado.errores["errores"][0]["contadores"]["apariciones"] == 1  # por episodio, no por intento
    # reanudar no repite peldaños ya hechos (no quedan respuestas: si llamara al modelo, fallaría)
    X.construir_cuaderno("simulado", ids=["bis_1_ancho", "bis_2_encaje"], reanudar=out, verbose=False)
