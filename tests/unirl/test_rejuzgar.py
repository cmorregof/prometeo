"""unirl/tools/rejuzgar.py: la referencia independiente que vuelve a juzgar los intentos (8 oct 2026).

Sin Isabelle: el filtro mínimo, el ensamblado de la teoría, la reconstrucción de la biblioteca contra su hash, la
atribución de errores, las categorías, los episodios auditados, el McNemar y el circuito completo con un `isabelle`
falso. Con Isabelle (marca `isabelle`): la referencia acepta una prueba que el juez aceptó en la ronda 1, también con
sign_step a nivel de teoría (formato cruzado), rechaza una definición del agente (axioma nuevo) y ya no tropieza con la
biblioteca donde el juez de la ronda 1 sí tropezaba."""

import importlib.util
import json
import stat
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("rejuzgar", RAIZ / "unirl" / "tools" / "rejuzgar.py")
R = importlib.util.module_from_spec(_spec)
sys.modules["rejuzgar"] = R  # dataclasses busca el módulo en sys.modules
_spec.loader.exec_module(R)

SPEC = {"id": "toy", "name": "toy", "kind": "theorem", "imports": '"HOL-Analysis.Analysis"', "session_parent": "HOL-Analysis",
        "prelude": 'definition dobla :: "real \\<Rightarrow> real" where "dobla t = 2 * t"',
        "fixes": "x y :: real", "assumes": 'xy: "x \\<le> y"', "concl": "dobla x \\<le> dobla y"}
SIGN = 'lemma sign_step:\n  fixes x y z :: real\n  assumes "x * z \\<le> 0"\n  shows "True"\n  by simp'


def _intento(**kw) -> "R.Intento":
    base = dict(fase="evaluacion_E", corrida="20260927-090507-gpt-6-luna", modelo="gpt-6-luna", config="E",
                episodio_id="secante_2_cociente#E#1", peldano="secante_2_cociente", split="test", dificultad=2, intento=1,
                llamada=1, linea=1, etiqueta="PROOF_FAILED", prueba="by simp", lemas="", respuesta="", feedback="",
                errores=[], biblioteca_hash="", nombres_biblioteca=[], marcas=0, cerradas=0, objetivo_hash="",
                limite_juez=300.0, version_juez="teorema-2026-09-24", cuaderno_hash="")
    base.update(kw)
    return R.Intento(**base)


# ----------------------------------------------------------------------------- filtro mínimo y texto


@pytest.mark.parametrize("texto, esperado", [
    ("by simp", None),
    ("using foo sorry", "sorry"),
    ("(* aquí no hay sorry *) by simp", None),
    ('have h: "sorry = (1::nat)" by simp', None),
    ("ML \\<open>val x = 1\\<close>", "ML"),
    ("ML_val \\<open>1\\<close>", "ML_val"),
    ('txt \\<open>@{ML "1"}\\<close>', "ML"),
    ("using [[quick_and_dirty]] by simp", "quick_and_dirty"),
    ('lemma cu_setup_cota: "True" by simp', None),
    ("apply (tactic \\<open>all_tac\\<close>)", "tactic"),
    ("by (rule_tac x = 1 in exI) simp", None),
    ("axiomatization where ax: False", "axiomatization"),
])
def test_filtro_minimo(texto, esperado):
    assert R.prohibida(texto) == esperado


def test_biblioteca_sin_redefinidos_y_nombres():
    otro = 'lemma cu_otro: "(0::real) \\<le> 1"\n  by simp'
    lib = SIGN + "\n\n" + otro
    assert R.nombres_de_lemas(lib) == ["sign_step", "cu_otro"]
    assert R.biblioteca_sin_redefinidos(lib, "") == lib
    assert R.biblioteca_sin_redefinidos(lib, 'lemma cu_otro: "True" by simp') == SIGN  # gana la versión del agente
    assert R.biblioteca_sin_redefinidos("", 'lemma a: "True" by simp') == ""


def test_ensamblar_ubica_los_bloques_y_no_reexamina_el_texto(tmp_path):
    agente = 'lemma mio: "(1::real) \\<le> 2"\n  by simp'
    prueba = "unfolding dobla_def using xy by simp\n(* __CONCL__ queda literal *)"
    thy, tr = R.ensamblar(SPEC, SIGN, agente, prueba, tmp_path, "rjabcdefghij")
    lineas = thy.splitlines()
    ctx = lineas.index("context") + 1
    assert lineas[tr["preludio"][0] - 1].startswith("definition dobla")
    assert lineas[tr["biblioteca"][0] - 1] == "lemma sign_step:" and tr["biblioteca"][1] < ctx
    assert lineas[tr["lemas"][0] - 1] == 'lemma mio: "(1::real) \\<le> 2"' and tr["lemas"][0] > ctx
    assert lineas[tr["enunciado"][0] - 1] == 'theorem rjabcdefghij_objetivo: "dobla x \\<le> dobla y"'
    assert lineas[tr["prueba"][0] - 1] == "unfolding dobla_def using xy by simp" and tr["prueba"][0] == tr["enunciado"][0] + 1
    assert "(* __CONCL__ queda literal *)" in thy  # una sola pasada
    assert f'Path.explode "{tmp_path}/objetivo.txt"' in thy and "rjabcdefghij_ax1" in thy
    assert thy.index("rjabcdefghij_ax0") < thy.index("lemma sign_step") < thy.index("rjabcdefghij_ax1") < thy.index("\ncontext\n")


def test_los_errores_se_atribuyen_a_su_bloque(tmp_path):
    thy, tr = R.ensamblar(SPEC, SIGN, "", "by simp", tmp_path, "rjabcdefghij")
    a = tr["biblioteca"][0]
    p = tr["prueba"][0]
    log = (f'*** Duplicate fixed variable(s): "x"\n*** At command "lemma" (line {a} of "{tmp_path}/Rejuicio.thy")\n'
           f'*** Failed to finish proof (line {p} of "{tmp_path}/Rejuicio.thy")\n*** otra cosa (line 3 of "/x/Otra.thy")')
    errores, bloques = R.errores_de_log(log, tr)
    assert len(errores) == 4 and bloques == ["biblioteca", "prueba"]


def test_reconstruye_la_biblioteca_contra_su_hash(tmp_path):
    d = tmp_path / "congelados" / "h1"
    d.mkdir(parents=True)
    (d / "lemas.json").write_text(json.dumps({"lemas": [{"nombre": "a", "texto": "lemma a: A"},
                                                        {"nombre": "b", "texto": "lemma b: B"}]}), encoding="utf-8")
    (tmp_path / "lemas.json").write_text(json.dumps({"lemas": [{"nombre": "a", "texto": "lemma a: A2"}]}), encoding="utf-8")
    L = R.Lemas(base=tmp_path)
    assert L.biblioteca(["a", "b"], R.hash_texto("lemma a: A\n\nlemma b: B")) == "lemma a: A\n\nlemma b: B"
    assert L.biblioteca(["a", "b"], R.hash_texto("lemma a: A2\n\nlemma b: B")) == "lemma a: A2\n\nlemma b: B"
    assert L.biblioteca(["b", "a"], R.hash_texto("lemma a: A\n\nlemma b: B")) is None  # el orden importa
    assert L.biblioteca(["c"], "abc") is None and L.biblioteca([], "") == ""


def test_hash_del_objetivo_igual_que_el_juez():
    G = pytest.importorskip("unirl.gd_isabelle")  # la referencia no lo importa; aquí solo se comparan los hashes
    assert R.hash_objetivo(SPEC) == G.TheoremVerifier._hash(SPEC)
    C = pytest.importorskip("unirl.cuaderno")
    assert R.hash_texto(SIGN) == C.hash_texto(SIGN) and R.hash_texto("  ") == C.hash_texto("  ") == ""


# ----------------------------------------------------------------------------- categorías


def test_categorias():
    lib = dict(biblioteca_hash="2b6d69992bce9f0d", nombres_biblioteca=["sign_step"])
    dup = ['*** Duplicate fixed variable(s): "x"', '*** At command "lemma" (lema sign_step, línea 1)']
    acepta, rechaza = {"veredicto": "acepta", "build_s": 100.0}, {"veredicto": "rechaza", "motivo": "kernel"}
    assert R.categorizar(_intento(etiqueta="ACCEPTED"), acepta)[0] == "concordante"
    assert R.categorizar(_intento(etiqueta="ACCEPTED"), rechaza)[0] == "FP"
    assert R.categorizar(_intento(etiqueta="LEMMA_FAILED", errores=dup, **lib), acepta) == \
        ("FN", "biblioteca: el juez culpó a un lema del cuaderno")
    assert R.categorizar(_intento(etiqueta="LEMMA_FAILED", errores=dup, **lib), rechaza)[0] == "concordante_contaminado"
    # el mismo error en un lema que definió el agente no es culpa del cuaderno
    propio = _intento(etiqueta="LEMMA_FAILED", errores=dup, lemas=SIGN, **lib)
    assert R.categorizar(propio, rechaza)[0] == "concordante" and R.categorizar(propio, acepta)[1].startswith("otro")
    assert R.categorizar(_intento(etiqueta="LEMMA_FAILED", errores=["*** x (lema cu_a del cuaderno, línea 2)"]),
                         rechaza)[0] == "concordante_contaminado"
    assert R.categorizar(_intento(etiqueta="STATEMENT_DRIFT", feedback="la PROOF usa 'notation'"), acepta)[0] == "regla_estricta"
    assert R.categorizar(_intento(etiqueta="TIMEOUT"), acepta)[0] == "FN"
    assert R.categorizar(_intento(etiqueta="TIMEOUT"), {"veredicto": "acepta", "build_s": 500.0})[0] == "tiempo"
    assert R.categorizar(_intento(), {"veredicto": "indeterminado", "motivo": "m"}) == ("indeterminado", "m")
    assert R.y_referencia("FN", _intento()) == 1 and R.y_referencia("regla_estricta", _intento()) == 0
    assert R.y_referencia("concordante", _intento(etiqueta="ACCEPTED")) == 1 and R.y_referencia("indeterminado", _intento()) is None


def test_marcas_abiertas():
    assert R.marcas_abiertas(_intento(marcas=2, cerradas=1))
    assert R.marcas_abiertas(_intento(prueba="proof -\n  have a: \"True\" by (martillo 1)\n  show ?thesis by simp\nqed",
                                      marcas=None, cerradas=None))
    assert not R.marcas_abiertas(_intento(marcas=2, cerradas=2, prueba="by simp"))


# ----------------------------------------------------------------------------- episodios y McNemar


def _fila(config, pid, k, intento, y_juez, cat, y_ref, corrida="c1", modelo="m"):
    return {"modelo": modelo, "config": config, "episodio_id": f"{pid}#{config}#{k}", "corrida": corrida,
            "fase": "f", "peldano": pid, "split": "test", "k": k, "dificultad": 2, "intento": intento,
            "y_juez": y_juez, "y_ref": y_ref, "categoria": cat}


def test_episodios_y_mcnemar():
    filas = [
        _fila("C", "p1", 1, 1, 1, "concordante", 1),
        _fila("E", "p1", 1, 1, 0, "FN", 1),                       # el juez se equivocó: el episodio sí era válido
        _fila("C", "p2", 1, 1, 1, "concordante", 1),
        _fila("E", "p2", 1, 1, 0, "concordante_contaminado", 0),
        _fila("E", "p2", 1, 2, 0, "concordante", 0),              # contaminado: la retroalimentación culpó al cuaderno
        _fila("C", "p3", 1, 1, 0, "concordante", 0),
        _fila("E", "p3", 1, 1, 0, "indeterminado", None),
        _fila("E", "p3", 1, 1, 1, "concordante", 1, corrida="c2"),  # repetido en otra corrida: cuenta el primero
    ]
    eps = R.episodios(filas)
    e1, e2, e3 = (eps[("m", "E", f"p{i}#E#1")] for i in (1, 2, 3))
    assert (e1["y_juez"], e1["y_ref"], e1["contaminado"]) == (0, 1, False)
    assert (e2["y_juez"], e2["y_ref"], e2["contaminado"]) == (0, 0, True)
    assert (e3["y_juez"], e3["y_ref"], e3["corrida"]) == (0, None, "c1")
    ps = R.pares(eps, "m", "C", "E", "episodio", "excluir")
    assert ps["juez"] == [(1, 0), (1, 0), (0, 0)] and ps["ref"] == [(1, 1), (1, 0)]
    assert R.pares(eps, "m", "C", "E", "episodio", "1")["ref"] == [(1, 1), (1, 0), (0, 1)]
    assert R.p_mcnemar(0, 2) == 0.5 and R.p_mcnemar(0, 6) == pytest.approx(0.03125) and R.p_mcnemar(0, 0) is None
    assert R.cota_regla_de_tres(100) == pytest.approx(0.0295, abs=1e-3)


def test_candidatos_del_formato_cruzado(tmp_path):
    (tmp_path / "congelados" / "h").mkdir(parents=True)
    (tmp_path / "congelados" / "h" / "lemas.json").write_text(
        json.dumps({"lemas": [{"nombre": "sign_step", "texto": SIGN}]}), encoding="utf-8")
    lib = dict(biblioteca_hash=R.hash_texto(SIGN), nombres_biblioteca=["sign_step"])
    its = [_intento(config="C", episodio_id="p1#C#1", peldano="p1", etiqueta="ACCEPTED", prueba="by simp"),
           _intento(config="C", episodio_id="p1#C#2", peldano="p1", etiqueta="ACCEPTED", prueba="by simp"),  # repetida
           _intento(config="C", episodio_id="p2#C#1", peldano="p2", etiqueta="ACCEPTED", prueba="by auto"),  # sin E en p2
           _intento(config="C", episodio_id="p1#C#3", peldano="p1", etiqueta="PROOF_FAILED", prueba="by auto"),
           _intento(config="E", episodio_id="p1#E#1", peldano="p1", etiqueta="ACCEPTED", prueba="by blast", **lib)]
    unicos, bibs = R.candidatos_cruzado(its, R.Lemas(base=tmp_path))
    assert [u.episodio_id for u in unicos] == ["p1#C#1"] and bibs == {"p1": SIGN}


# ----------------------------------------------------------------------------- circuito completo, con un isabelle falso


FALSO = r'''
import re, sys
from pathlib import Path
args = sys.argv[1:]
work = Path(args[args.index("-d") + 1])
thy = (work / "Rejuicio.thy").read_text(encoding="utf-8")
out = re.search(r'Path.explode "([^"]*)/objetivo.txt"', thy).group(1)
lineas = thy.splitlines()
mala = next((i for i, l in enumerate(lineas, 1) if "FALLA" in l), None)
if mala:
    print(f'*** Failed to finish proof (line {mala} of "{work}/Rejuicio.thy")')
    sys.exit(1)
Path(out, "objetivo.txt").write_text("prop_ok=1\noraculos=\nskip_proof=0\n")
Path(out, "axiomas.txt").write_text("biblioteca=\nagente=" + ("Rejuicio.c_def" if "definition" in thy.split("context", 1)[1] else "") + "\n")
'''


def _corrida(tmp_path: Path, fase: str, corrida: str, inicio: str, filas: list[dict]) -> None:
    d = tmp_path / "runs" / fase / corrida
    d.mkdir(parents=True)
    (d / "meta.json").write_text(json.dumps({"inicio": inicio, "modelo": "m", "configs": ["C", "E"]}), encoding="utf-8")
    (d / "llamadas.jsonl").write_text("\n".join(json.dumps(f) for f in filas) + "\n", encoding="utf-8")


def _llamada(eid, intento, etiqueta, prueba, **kw):
    pid, config, _ = eid.split("#")
    r = {"tipo": "intento", "modelo": "m", "config": config, "episodio_id": eid, "peldano": pid, "split": "test",
         "dificultad": 2, "intento": intento, "etiqueta": etiqueta, "proof": prueba, "prueba_final": prueba,
         "lemmas": "", "marcas": 0, "cerradas": 0, "errores": [], "feedback": "",
         "veredicto_meta": {"objetivo_hash": R.hash_objetivo(SPEC), "limite_compilacion_s": 300, "juez": "teorema-2026-09-24"}}
    r.update(kw)
    return r


def test_rejuzgar_de_punta_a_punta_con_isabelle_falso(tmp_path, monkeypatch):
    (tmp_path / "corpus" / "raices").mkdir(parents=True)
    (tmp_path / "corpus" / "raices" / "toy.json").write_text(json.dumps(SPEC), encoding="utf-8")
    (tmp_path / "cuaderno" / "congelados" / "h").mkdir(parents=True)
    (tmp_path / "cuaderno" / "congelados" / "h" / "lemas.json").write_text(
        json.dumps({"lemas": [{"nombre": "sign_step", "texto": SIGN}]}), encoding="utf-8")
    lib = {"biblioteca_hash": R.hash_texto(SIGN), "lemas_mostrados": ["sign_step"]}
    dup = ['*** Duplicate fixed variable(s): "x"', '*** At command "lemma" (lema sign_step, línea 1)']
    _corrida(tmp_path, "evaluacion", "20260926-233322-m", "2026-09-26T23:33:22", [
        _llamada("toy#C#1", 1, "ACCEPTED", "unfolding dobla_def using xy by simp"),
        _llamada("toy#C#2", 1, "PROOF_FAILED", "by FALLA"),
        _llamada("toy#C#3", 1, "PROVIDER_ERROR", ""),
        {"tipo": "consulta", "episodio_id": "toy#C#1"},
    ])
    _corrida(tmp_path, "evaluacion_E", "20260927-090507-m", "2026-09-27T09:05:07", [
        _llamada("toy#E#1", 1, "LEMMA_FAILED", "unfolding dobla_def using xy by simp", errores=dup, **lib),
        _llamada("toy#E#2", 1, "LEMMA_FAILED", "by FALLA", errores=dup, **lib),
        _llamada("toy#E#2", 2, "PROOF_FAILED", "by (martillo 1)", marcas=1, cerradas=0, errores=dup, **lib),
        _llamada("toy#E#3", 1, "STATEMENT_DRIFT", "unfolding dobla_def using xy by simp", **lib),
    ])
    _corrida(tmp_path, "evaluacion", "20260928-000000-m", "2026-09-28T00:00:00", [  # fuera de la ventana
        _llamada("toy#C#9", 1, "ACCEPTED", "by FALLA")])
    falso = tmp_path / "falso.py"
    falso.write_text(FALSO, encoding="utf-8")
    isa = tmp_path / "isabelle"
    isa.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{falso}" "$@"\n', encoding="utf-8")
    isa.chmod(isa.stat().st_mode | stat.S_IEXEC)
    for nombre, valor in (("RUNS", tmp_path / "runs"), ("CORPUS", tmp_path / "corpus"),
                          ("CUADERNO", tmp_path / "cuaderno"), ("RESULTADOS", tmp_path / "resultados")):
        monkeypatch.setattr(R, nombre, valor)
    args = ["rejuzgar", "--desde", "2026-09-26T20:17:27", "--hasta", "2026-09-27T14:03:07", "--etiqueta", "prueba",
            "--fases", "evaluacion,evaluacion_E", "--isabelle", str(isa), "--scratch", str(tmp_path / "scratch"),
            "--sin-sandbox", "--sin-cortesia", "--limite", "60"]
    assert R.main(args) == 0
    filas = R.leer_jsonl(tmp_path / "resultados" / "prueba" / "rejuicio.jsonl")
    cat = {(f["episodio_id"], f["intento"]): f["categoria"] for f in filas}
    assert cat == {("toy#C#1", 1): "concordante", ("toy#C#2", 1): "concordante", ("toy#E#1", 1): "FN",
                   ("toy#E#2", 1): "concordante_contaminado", ("toy#E#2", 2): "indeterminado",
                   ("toy#E#3", 1): "regla_estricta"}
    resumen = (tmp_path / "resultados" / "prueba" / "resumen.md").read_text(encoding="utf-8")
    # C#3 solo tuvo PROVIDER_ERROR: los pares son k = 1 y k = 2. El juez da b' = 1 (k = 1); auditado, k = 1 empata
    # (el intento de E era válido) y k = 2 queda indeterminado (marcas abiertas por la biblioteca rota)
    assert "| m: C frente a E | peldaño y episodio | juez | — | 2 | 0 | 1 | 1,000 |" in resumen
    assert "| m: C frente a E | peldaño y episodio | auditados | excluir | 1 | 0 | 0 | — |" in resumen
    assert "| m: C frente a E | peldaño y episodio | auditados | 1 | 2 | 1 | 0 | 1,000 |" in resumen
    # reanudar no repite nada; un intento nuevo idéntico a uno ya compilado reusa su veredicto
    n = len(filas)
    assert R.main(args) == 0
    assert len(R.leer_jsonl(tmp_path / "resultados" / "prueba" / "rejuicio.jsonl")) == n
    # la definición del agente es un axioma nuevo para la referencia
    _corrida(tmp_path, "evaluacion", "20260927-100000-m", "2026-09-27T10:00:00", [
        _llamada("toy#C#4", 1, "ACCEPTED", "by simp", lemmas='definition c :: real where "c = 0"')])
    assert R.main(args) == 0
    nuevas = {f["episodio_id"]: f for f in R.leer_jsonl(tmp_path / "resultados" / "prueba" / "rejuicio.jsonl")}
    assert nuevas["toy#C#4"]["categoria"] == "FP" and "axiomas nuevos" in nuevas["toy#C#4"]["detalle"]


def test_ensayo_no_compila_ni_registra(tmp_path, monkeypatch, capsys):
    (tmp_path / "corpus" / "raices").mkdir(parents=True)
    (tmp_path / "corpus" / "raices" / "toy.json").write_text(json.dumps(SPEC), encoding="utf-8")
    _corrida(tmp_path, "evaluacion", "20260926-233322-m", "2026-09-26T23:33:22",
             [_llamada("toy#C#1", 1, "ACCEPTED", "by simp")])
    for nombre, valor in (("RUNS", tmp_path / "runs"), ("CORPUS", tmp_path / "corpus"),
                          ("CUADERNO", tmp_path / "cuaderno"), ("RESULTADOS", tmp_path / "resultados")):
        monkeypatch.setattr(R, nombre, valor)
    assert R.main(["rejuzgar", "--desde", "2026-09-26T00:00:00", "--fases", "evaluacion", "--ensayo",
                   "--scratch", str(tmp_path / "scratch"), "--isabelle", "/no/existe"]) == 0
    assert not (tmp_path / "resultados").exists()
    assert len(list((tmp_path / "scratch").glob("rj-*/Rejuicio.thy"))) == 1
    assert "1 por compilar" in capsys.readouterr().out


# ----------------------------------------------------------------------------- con Isabelle (minutos)


def _aceptado_sin_biblioteca(peldano: str):
    for d in sorted((RAIZ / "runs" / "unirl" / "rl_verbal" / "evaluacion").glob("*")):
        for it in R.intentos_de(d):
            if it.peldano == peldano and it.aceptado and not it.biblioteca_hash and not R.marcas_abiertas(it):
                return it
    pytest.skip(f"no hay un intento aceptado sin biblioteca en {peldano} (los llamadas.jsonl no se versionan)")


def _sign_step() -> str:
    f = RAIZ / "runs" / "unirl" / "cuaderno" / "congelados" / "fbd88bf0474ad117" / "lemas.json"
    if not f.exists():
        pytest.skip("no está el cuaderno congelado de la ronda 1")
    return next(l["texto"] for l in json.loads(f.read_text(encoding="utf-8"))["lemas"] if l["nombre"] == "sign_step")


@pytest.mark.isabelle
def test_isabelle_referencia_acepta_lo_aceptado_con_y_sin_cuaderno():
    it = _aceptado_sin_biblioteca("secante_2_cociente")
    spec = R.leer_objetivo(it.peldano)
    ref = R.Referencia(limite_s=900)
    r = ref.juzgar(spec, "", it.lemas, it.prueba)
    assert r["veredicto"] == "acepta", (r["motivo"], r["errores"][:3])
    r = ref.juzgar(spec, _sign_step(), it.lemas, it.prueba)  # formato cruzado: la biblioteca a nivel de teoría
    assert r["veredicto"] == "acepta", (r["motivo"], r["errores"][:3])
    r = ref.juzgar(spec, "", 'definition rj_c :: real where "rj_c = 0"', it.prueba)
    assert r["veredicto"] == "rechaza" and r["axiomas_agente"], (r["motivo"], r["errores"][:3])


@pytest.mark.isabelle
def test_isabelle_la_biblioteca_ya_no_tumba_los_intentos_de_E_de_la_ronda_1():
    d = RAIZ / "runs" / "unirl" / "rl_verbal" / "evaluacion_E" / "20260927-090507-gpt-6-luna"
    its = [i for i in R.intentos_de(d) if i.peldano.startswith("secante_2") and R.culpa_de_la_biblioteca(i)
           and not R.marcas_abiertas(i)]
    if not its:
        pytest.skip("no están los registros de la ronda 1")
    spec, bib, motivo = R.preparar(its[0], R.Lemas())
    assert motivo is None and bib
    r = R.Referencia(limite_s=900).juzgar(spec, bib, its[0].lemas, its[0].prueba)
    assert r["veredicto"] in ("acepta", "rechaza") and "biblioteca" not in r["bloques_error"], (r["motivo"], r["errores"][:3])
