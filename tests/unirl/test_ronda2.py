"""Ronda 2 (27 sep 2026): lo que las enmiendas prerregistradas exigen de unirl: F pide lemas reutilizables, la
destilación admite lemas que el kernel verifica, un lema sin identificadores en común con el teorema no se muestra, el
cuaderno se construye en pasadas y el McNemar se calcula por dificultad. Sin Isabelle ni API."""

import importlib.util
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from unirl import corpus, cuaderno as C, experimentos as X, martillo as M, reflexion as RF

RAIZ = Path(__file__).resolve().parents[2]
TOOLS = RAIZ / "unirl" / "tools"


@pytest.fixture(autouse=True)
def cuaderno_real_intacto():
    """Ninguna prueba puede escribir en el cuaderno real."""
    def foto():
        return {f.name: f.read_bytes() for f in C.DIR.iterdir() if f.is_file()} if C.DIR.exists() else {}
    antes = foto()
    yield
    assert foto() == antes, "una prueba modificó el cuaderno real"


class Simulado:
    model = "simulado"

    def __init__(self, respuestas):
        self.respuestas, self.prompts, self.ultimo_uso = list(respuestas), [], {"usd": 0.001}
        self.libro = SimpleNamespace(total=lambda: 0.0)

    def complete(self, system, user):
        self.prompts.append(user)
        return self.respuestas.pop(0)


def _acepta_si(marca: str):
    def f(juez, prueba, cuaderno_hash="", cache=None, lemas="", biblioteca=""):
        ok = marca in prueba
        o = SimpleNamespace(outcome_label="ACCEPTED" if ok else "PROOF_FAILED", accepted=ok, cost_s=1.0,
                            raw={"errors": [] if ok else ['*** Undefined method: "nlinarith"'], "verified_lemmas": [],
                                 "veredicto": {"carga_1_5_15": [1.0, 1.0, 1.0]}, "reason": "x"})
        return {"marcas": 0, "cerradas": 0, "pasos": [], "prueba_final": prueba, "outcome": o,
                "veredicto_juez": o.outcome_label, "martillo_s": 0.0, "espera_candado_s": 0.0, "suspension_s": 0.0,
                "errores": []}
    return f


def _ronda_py():
    spec = importlib.util.spec_from_file_location("ronda_tools", TOOLS / "ronda.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ----------------------------------------------------------------------------- 1. F pide lemas reutilizables


def test_f_pide_lemas_reutilizables_y_las_demas_configuraciones_no():
    spec = corpus.exigir_usable("bis_1_ancho")
    g = C.Cuaderno().glosario_compacto()
    f = RF.construir_prompt(spec, RF.CONFIGS["F"], g, "", [], [], 2, 1)
    assert RF.CONFIGS["F"].pedir_lemas and "REUTILIZABLES" in f and "cu_" in f and "LEMMAS: <<<" in f
    for nombre in ("B0", "B", "C", "D", "E", "C3", "E3"):
        assert not RF.CONFIGS[nombre].pedir_lemas
        assert "REUTILIZABLES" not in RF.construir_prompt(spec, RF.CONFIGS[nombre], g, "", [], [], 2, 1)


# ----------------------------------------------------------------------------- 3. umbral de recuperación


def test_identificadores_excluye_los_simbolos_pero_no_sus_nombres():
    assert C.identificadores("x \\<le> y \\<bar>z\\<bar> foo_bar") == {"bar", "foo_bar"}
    assert "\\<le>" in C.claves("x \\<le> y") and "\\<le>" not in C.identificadores("x \\<le> y")


def test_un_lema_sin_identificadores_en_comun_con_el_teorema_no_se_muestra(tmp_path, monkeypatch):
    c = C.Cuaderno(tmp_path)
    c.errores = C.Cuaderno().errores
    # como sign_step de la ronda 1: general, correcto, y sin ningún identificador del teorema (solo comparte \<le>)
    signo = {"nombre": "cu_signo", "alcance": "general", "procedencia": {},
             "texto": 'lemma cu_signo:\n  fixes x y z :: real\n  assumes "x * z \\<le> 0" and "\\<not> x * y \\<le> 0"\n'
                      '  shows "y * z \\<le> 0"\n  by (smt (verit) mult_nonneg_nonpos zero_le_mult_iff)'}
    bis = {"nombre": "cu_bis", "alcance": "biseccion", "procedencia": {},
           "texto": 'lemma cu_bis: "biseccion f a b 0 = (a, b)"\n  by simp'}
    c.lemas = [signo, bis]
    spec = corpus.exigir_usable("bis_1_ancho")
    assert C.MINIMO_IDS_LEMA == 1
    assert [l["nombre"] for l in c.recuperar(spec, ("lemas",))["lemas"]] == ["cu_bis"]  # comparte `biseccion`
    monkeypatch.setattr(C, "MINIMO_IDS_LEMA", 0)  # regla de la ronda 1: se mostraban los dos
    assert {l["nombre"] for l in c.recuperar(spec, ("lemas",))["lemas"]} == {"cu_signo", "cu_bis"}


def test_el_lema_real_de_la_ronda_1_no_se_mostraria_en_ningun_peldano_de_test():
    lemas = RAIZ / "runs" / "unirl" / "cuaderno" / "congelados" / "fbd88bf0474ad117" / "lemas.json"
    if not lemas.exists():
        pytest.skip("no está el cuaderno congelado de la ronda 1")
    c = C.Cuaderno(lemas.parent, solo_lectura=True)
    assert [l["nombre"] for l in c.lemas] == ["sign_step"]
    for spec in corpus.usables(split="test"):
        assert c.recuperar(spec, ("lemas",))["lemas"] == [], spec["id"]


# ----------------------------------------------------------------------------- 1b. lemas desde la destilación


def test_destilacion_admite_solo_lemas_generales_que_el_kernel_verifica(tmp_path, monkeypatch):
    c = C.Cuaderno(tmp_path)
    c.errores = C.Cuaderno().errores
    llamados = []

    def falso_admitir(lema, metodo, gen="", met="", juez=None, split="train"):
        llamados.append((lema, metodo))
        nombre = lema.split()[1].rstrip(":")
        ok = nombre == "cu_bueno"
        return {"admitido": ok, "motivo": "" if ok else "el kernel no verifica el lema como enunciado independiente",
                "nombre": nombre, "alcance": "general", "texto": lema.strip()}
    monkeypatch.setattr(C, "admitir_lema", falso_admitir)
    monkeypatch.setattr(X, "complete_with_retries", lambda p, s, u, **k: p.complete(s, u))
    prov = Simulado(["ERRORES: <<<\n>>>\nESTRATEGIAS: <<<\n>>>\nLEMAS: <<<\n"
                     'lemma cu_bueno: "0 \\<le> (x::real) * x"\n  by simp\n'
                     'lemma cu_malo: "(x::real) < x"\n  by simp\n'
                     'lemma cu_bis: "biseccion f a b 0 = (a, b)"\n  by simp\n>>>'])
    res = X.destilar(prov, c, [], [], tmp_path / "r.jsonl", {"corrida": "t"})
    assert "LEMAS" in X.PROMPT_DESTILAR and "cu_" in X.PROMPT_DESTILAR and "LEMAS" in prov.prompts[0]
    assert res["lemas_admitidos"] == ["cu_bueno"] and [l["nombre"] for l in c.lemas] == ["cu_bueno"]
    assert [r["nombre"] for r in res["lemas_rechazados"]] == ["cu_malo", "cu_bis"]
    assert "solo entran lemas generales" in res["lemas_rechazados"][1]["motivo"]  # constantes de un preludio: sin kernel
    assert [m for _, m in llamados] == [None, None] and len(llamados) == 2
    assert c.lemas[0]["procedencia"]["destilacion"] == "t"
    reg = [json.loads(l) for l in (tmp_path / "r.jsonl").read_text().splitlines()]
    assert reg[-1]["tipo"] == "destilacion" and reg[-1]["lemas_admitidos"] == ["cu_bueno"]


def test_destilacion_sin_bloque_de_lemas_no_cambia_nada(tmp_path, monkeypatch):
    c = C.Cuaderno(tmp_path)
    c.errores = C.Cuaderno().errores
    monkeypatch.setattr(C, "admitir_lema", lambda *a, **k: pytest.fail("no debía llamar al kernel"))
    monkeypatch.setattr(X, "complete_with_retries", lambda p, s, u, **k: p.complete(s, u))
    res = X.destilar(Simulado(["ERRORES: <<<\n>>>\nESTRATEGIAS: <<<\n>>>"]), c, [], [], tmp_path / "r.jsonl", {"corrida": "t"})
    assert res["lemas_admitidos"] == [] and res["lemas_rechazados"] == [] and c.lemas == []


# ----------------------------------------------------------------------------- 2. pasadas del cuaderno


def test_construir_cuaderno_en_dos_pasadas_y_reanudacion(tmp_path, monkeypatch):
    import shutil
    vivo = tmp_path / "cuaderno"
    vivo.mkdir()
    shutil.copy2(C.DIR / "errores.json", vivo / "errores.json")
    monkeypatch.setattr(C, "DIR", vivo)
    monkeypatch.setattr(C, "CONGELADOS", vivo / "congelados")
    monkeypatch.setattr(X, "RUNS", tmp_path / "runs")
    monkeypatch.setattr(X, "DESTILAR_CADA", 2)
    monkeypatch.setattr(M, "martillo_en_pasos", _acepta_si("BIEN"))
    monkeypatch.setattr(M, "consultar", lambda juez, cs, tope=4, biblioteca="": [])
    prov = Simulado(["PROOF: <<< proof -\n  (* BIEN *)\n  show ?thesis by simp\nqed >>>",   # pasada 1
                     "PROOF: <<< proof -\n  (* BIEN *)\n  show ?thesis by simp\nqed >>>",   # pasada 2
                     "ERRORES: <<<\n>>>\nESTRATEGIAS: <<<\n>>>\nLEMAS: <<<\n>>>"])          # destilación
    monkeypatch.setattr(X, "proveedor", lambda *a, **k: prov)
    monkeypatch.setattr(X, "complete_with_retries", lambda p, s, u, **k: p.complete(s, u))
    out = X.construir_cuaderno("simulado", ids=["bis_1_ancho"], verbose=False, pasadas=2)
    eps = [json.loads(l) for l in (out / "episodios.jsonl").read_text().splitlines()]
    assert [e["episodio_id"] for e in eps] == ["bis_1_ancho#1", "bis_1_ancho#2"] and [e["pasada"] for e in eps] == [1, 2]
    assert all(e["aceptado"] for e in eps)
    assert json.loads((out / "meta.json").read_text())["pasadas"] == 2 and (out / "FIN.json").exists()
    assert "REUTILIZABLES" in prov.prompts[0] and not prov.respuestas
    # reanudar con las mismas pasadas no repite nada (no quedan respuestas: si llamara al modelo, fallaría)
    X.construir_cuaderno("simulado", ids=["bis_1_ancho"], reanudar=out, verbose=False, pasadas=2)
    assert len((out / "episodios.jsonl").read_text().splitlines()) == 2


# ----------------------------------------------------------------------------- 4. McNemar por dificultad


def test_pares_de_mcnemar_por_dificultad():
    R = _ronda_py()
    peld = {"a": {"dificultad": 2}, "b": {"dificultad": 3}, "c": {"dificultad": 5}}
    Y = {("evaluacion", "C", "a", 1): 1, ("evaluacion_E", "E", "a", 1): 0,
         ("evaluacion", "C", "b", 1): 0, ("evaluacion_E", "E", "b", 1): 1,
         ("evaluacion", "C", "c", 1): 0, ("evaluacion_E", "E", "c", 1): 0,
         ("evaluacion", "C", "a", 2): 1}  # a#2 sin E: no forma par
    args = (Y, ["a", "b", "c"], {"a", "b", "c"}, peld, "evaluacion", "C", "evaluacion_E", "E", 2)
    filtros = dict(R.CONJUNTOS_MCNEMAR)
    assert [n for n, _ in R.CONJUNTOS_MCNEMAR][0].startswith("primario: dificultad ≤ 3")
    assert R.pares_mcnemar(*args, filtros["primario: dificultad ≤ 3"]) == [(1, 0), (0, 1)]
    assert R.pares_mcnemar(*args, filtros["secundario: todo T*"]) == [(1, 0), (0, 1), (0, 0)]
    assert R.pares_mcnemar(*args, filtros["secundario: dificultad 4–5"]) == [(0, 0)]
    assert R.pares_mcnemar(Y, ["a", "b", "c"], {"b"}, peld, "evaluacion", "C", "evaluacion_E", "E", 2, lambda d: True) == [(0, 1)]
    assert R._mcnemar([(1, 0), (0, 1)]) == {"n": 2, "b": 1, "b_prima": 1, "p": 1.0}
    assert R._mcnemar([(0, 0)])["p"] is None


# ----------------------------------------------------------------------------- 5. guiones de la ronda


def test_guiones_de_la_ronda_2_con_sintaxis_valida_y_parametros():
    for g in ("lanzar_ronda.sh", "preflight.sh"):
        assert subprocess.run(["bash", "-n", str(TOOLS / g)], capture_output=True).returncode == 0, g
    txt = (TOOLS / "lanzar_ronda.sh").read_text(encoding="utf-8")
    for v in ("PASADAS_CUADERNO=3", "CON_SOL=0", "HASH_CUADERNO_INICIO=fbd88bf0474ad117",
              '--pasadas "$PASADAS_CUADERNO"', '"--cuaderno=$HASH_CUADERNO_INICIO"', '[ -z "$P4" ] || wait "$P4"'):
        assert v in txt, v
    assert "--cuaderno=*" in (TOOLS / "preflight.sh").read_text(encoding="utf-8")
    assert X.TOPES["cuaderno"] >= 3 * 150  # tres pasadas: la ronda 1 gastó 150 llamadas en una
