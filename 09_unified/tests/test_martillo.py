"""Etapa 3: martillo (caché, pasos), consulta (saneado y tope) y errores del cuaderno sembrados del glosario."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from unirl import cuaderno, martillo as m
from unirl.gd_isabelle import TheoremVerifier

HERE = Path(__file__).resolve().parent
PRIV = HERE / "fixtures" / "pruebas_privadas"
SPEC = {"imports": '"HOL-Analysis.Analysis"', "prelude": "", "fixes": "x :: real", "assumes": 'h: "0 \\<le> x"',
        "concl": "0 \\<le> x"}


def juez_falso(tmp_path, build=None):
    """Juez mínimo: sin Isabelle. `build` decide qué pasa si alguien intenta compilar."""
    def no_compiles(*_a, **_k):
        raise AssertionError("no debía compilar")
    return SimpleNamespace(spec=SPEC, frozen_hash="abc123", _workdir=lambda prefijo: Path(tmp_path),
                           build=build or no_compiles, metadatos=lambda: {"carga_1_5_15": [0.0, 0.0, 0.0]})


def test_metodo_de_linea():
    assert m.metodo_de_linea("by simp") == "simp"
    assert m.metodo_de_linea("using a b by blast") == "(use a b in blast)"
    assert m.metodo_de_linea("by (smt (verit) x y)") == "(smt (verit) x y)"
    assert m.metodo_de_linea("apply simp") is None


def test_marcar_pasos_numera_cada_marca():
    marcada, n = m.marcar_pasos('have "a" by martillo\nhave "b" using h by martillo\nshow ?thesis by simp')
    assert n == 2 and "by (martillo 1)" in marcada and "by (martillo 2)" in marcada and "by simp" in marcada


def test_linea_de():
    assert m.linea_de({"fuente": "try0", "linea": "by simp"}) == "by simp"
    assert m.linea_de({"fuente": "cache", "linea": "by auto"}) == "by auto"
    assert m.linea_de({"fuente": "sledgehammer", "encontrado": False, "mensaje": ""}) is None


def test_cache_devuelve_la_linea_guardada(tmp_path):
    c = m.Cache(tmp_path / "c.sqlite")
    c.guardar(m.Cache.clave("paso", "ctx", "meta 1"), "paso", {"contexto": "ctx", "meta": "meta 1", "linea": "by simp"})
    c.guardar(m.Cache.clave("paso", "otro", "meta 2"), "paso", {"contexto": "otro", "meta": "meta 2", "linea": "by auto"})
    assert c.lineas_de("ctx") == [("meta 1", "by simp")]
    assert c.leer(m.Cache.clave("paso", "ctx", "meta 1"))["linea"] == "by simp"
    assert c.leer(m.Cache.clave("paso", "ctx", "meta 3")) is None


def test_martillo_solo_usa_la_cache_sin_compilar(tmp_path):
    c = m.Cache(tmp_path / "c.sqlite")
    j = juez_falso(tmp_path)
    guardado = {"resuelto_por_martillo": True, "linea": "by simp", "fuente": "try0", "veredicto_juez": "ACCEPTED"}
    c.guardar(m.Cache.clave("solo", m._contexto(j, "")), "solo", guardado)
    r = m.martillo_solo(j, cache=c)
    assert r["desde_cache"] and r["linea"] == "by simp" and r["resuelto_por_martillo"]
    # otro cuaderno, otra clave: ya no está en la caché e intentaría compilar
    with pytest.raises(AssertionError, match="no debía compilar"):
        m.martillo_solo(j, cuaderno_hash="cuaderno-nuevo", cache=c)


def test_martillo_solo_no_guarda_fallos_de_infraestructura(tmp_path):
    llamadas = []
    j = juez_falso(tmp_path, build=lambda *a, **k: llamadas.append(1) or (1, "*** algo falló"))
    c = m.Cache(tmp_path / "c.sqlite")
    r1 = m.martillo_solo(j, cache=c)
    r2 = m.martillo_solo(j, cache=c)
    assert r1["fuente"] == "error" and not r1["resuelto_por_martillo"] and not r2["desde_cache"] and len(llamadas) == 2


def test_martillo_solo_no_guarda_una_busqueda_con_la_maquina_suspendida(tmp_path, monkeypatch):
    def build(w, thy, nombre, t):
        (Path(w) / "martillo.json").write_text(json.dumps(
            {"resultado": {"fuente": "sledgehammer", "encontrado": False, "resultado": "timeout", "ms": "196500"}}))
        return 0, ""
    monkeypatch.setattr(m.Reloj, "suspension_s", lambda self: 134.0)
    c = m.Cache(tmp_path / "c.sqlite")
    r = m.martillo_solo(juez_falso(tmp_path, build=build), cache=c)
    assert r["invalido"] and r["suspension_s"] == 134.0 and r["sh_ms_pared"] == 196500
    assert c.leer(m.Cache.clave("solo", m._contexto(juez_falso(tmp_path), ""))) is None
    monkeypatch.setattr(m.Reloj, "suspension_s", lambda self: 0.0)
    r2 = m.martillo_solo(juez_falso(tmp_path, build=build), cache=c)
    assert not r2["invalido"] and c.leer(m.Cache.clave("solo", m._contexto(juez_falso(tmp_path), ""))) is not None


@pytest.mark.parametrize("tipo,texto", [
    ("buscar", 'ML \\<open>OS.Process.system "ls"\\<close>'),
    ("buscar", "name: MVT (* hola *)"),
    ("buscar", "a\nb"),
    ("buscar", "\\<open>x\\<close>"),
    ("metodo", "simp add: foo"),
    ("programa", "MVT"),
    ("buscar", "x" * 201),
])
def test_consulta_rechaza_ml_cartuchos_y_basura(tipo, texto):
    assert m.sanear_consulta(tipo, texto) is not None


@pytest.mark.parametrize("tipo,texto", [("buscar", "name: MVT"), ("buscar", '"_ * _ \\<le> _ * _"'),
                                        ("hecho", "mult_left_mono"), ("metodo", "linarith")])
def test_consulta_admite_patrones_y_nombres(tipo, texto):
    assert m.sanear_consulta(tipo, texto) is None


def test_consulta_respeta_el_tope_sin_descartar_en_silencio(tmp_path):
    escritas = {}

    def build(w, thy, nombre, t):
        escritas["consultas"] = (Path(w) / "consultas.txt").read_text()
        (Path(w) / "consulta.json").write_text(json.dumps(
            [{"tipo": "hecho", "consulta": f"h{i}", "existe": True} for i in range(m.MAX_CONSULTAS_POR_LOTE)]))
        return 0, ""
    j = juez_falso(tmp_path, build=build)
    pedidas = [{"tipo": "hecho", "texto": f"h{i}"} for i in range(m.MAX_CONSULTAS_POR_LOTE + 2)]
    res = m.consultar(j, pedidas)
    assert len(escritas["consultas"].splitlines()) == m.MAX_CONSULTAS_POR_LOTE
    assert len(res) == len(pedidas)
    assert sum("excede el tope" in r.get("error", "") for r in res) == 2


def test_consulta_rechazada_no_compila(tmp_path):
    res = m.consultar(juez_falso(tmp_path), [{"tipo": "buscar", "texto": "ML \\<open>x\\<close>"}])
    assert res[0]["error"]


# ------------------------------------------------------------------------------------ glosario y errores


def glosario_de_prueba(tmp_path, ok=True, alterar=False):
    g = {"fuente": "prueba", "entradas": [{"lean": "nlinarith", "tipo": "metodo", "isabelle": [
        {"tipo": "metodo", "nombre": "linarith"}], "nota": "No existe.", "visto_en": "Luna"}]}
    rg = tmp_path / "glosario.json"
    rg.write_text(json.dumps(g))
    v = {"ok": ok, "fecha": "2026-09-24T00:00:00", "isabelle": "Isabelle2025", "glosario_hash": cuaderno._hash(rg),
         "filas": [{"lean": "nlinarith", "lean_existe_en_isabelle": False, "alternativas": {"linarith": ok}, "ok": ok}]}
    rv = tmp_path / "verif.json"
    rv.write_text(json.dumps(v))
    if alterar:
        rg.write_text(json.dumps({**g, "fuente": "otra"}))
    return rg, rv


def test_errores_se_siembran_del_glosario_comprobado(tmp_path):
    rg, rv = glosario_de_prueba(tmp_path)
    doc = cuaderno.sembrar_errores(rg, rv)
    assert [e["id"] for e in doc["errores"]] == ["E001"]
    assert doc["errores"][0]["contadores"] == {"apariciones": 0, "ultimo_episodio": None}
    md = cuaderno.render_errores(doc)
    assert "`nlinarith` no existe" in md and "método `linarith`" in md


@pytest.mark.parametrize("ok,alterar,motivo", [(False, False, "no pasaron"), (True, True, "otra versión")])
def test_errores_rechaza_glosario_sin_comprobar(tmp_path, ok, alterar, motivo):
    rg, rv = glosario_de_prueba(tmp_path, ok=ok, alterar=alterar)
    with pytest.raises(cuaderno.GlosarioSinVerificar, match=motivo):
        cuaderno.sembrar_errores(rg, rv)


def test_errores_contadores_solo_train(tmp_path):
    rg, rv = glosario_de_prueba(tmp_path)
    doc = cuaderno.sembrar_errores(rg, rv)
    cuaderno.registrar_aparicion(doc, "E001", "ep-1", "train")
    assert doc["errores"][0]["contadores"] == {"apariciones": 1, "ultimo_episodio": "ep-1"}
    with pytest.raises(ValueError):
        cuaderno.registrar_aparicion(doc, "E001", "ep-2", "test")


def test_glosario_del_repo_comprobado_y_al_dia():
    v = json.loads(cuaderno.VERIFICACION.read_text())
    assert v["ok"] and v["glosario_hash"] == cuaderno._hash(cuaderno.GLOSARIO)
    assert all(f["ok"] for f in v["filas"])


def test_errores_md_del_repo_coincide_con_su_fuente():
    doc = json.loads(cuaderno.ERRORES_JSON.read_text())
    assert cuaderno.ERRORES_MD.read_text() == cuaderno.render_errores(doc)
    assert len(doc["errores"]) == len(json.loads(cuaderno.GLOSARIO.read_text())["entradas"])


# ------------------------------------------------------------------------------------ con Isabelle


@pytest.mark.isabelle
def test_isabelle_martillo_en_pasos_y_cache(tmp_path):
    j = TheoremVerifier.desde_corpus("orden_1_lineal")
    prueba = (PRIV / "orden_1_lineal.txt").read_text().replace("by (rule mult_left_mono)", "by martillo")
    c = m.Cache(tmp_path / "c.sqlite")
    r1 = m.martillo_en_pasos(j, prueba, cache=c)
    assert r1["cerradas"] == r1["marcas"] == 1 and r1["veredicto_juez"] == "ACCEPTED", r1
    r2 = m.martillo_en_pasos(j, prueba, cache=c)
    assert [p["resultado"]["fuente"] for p in r2["pasos"]] == ["cache"] and r2["veredicto_juez"] == "ACCEPTED"


@pytest.mark.isabelle
def test_isabelle_consulta_y_glosario(tmp_path):
    j = TheoremVerifier.desde_corpus("orden_1_lineal")
    res = m.consultar(j, [{"tipo": "buscar", "texto": "name: MVT"}, {"tipo": "metodo", "texto": "nlinarith"},
                          {"tipo": "hecho", "texto": "mult_left_mono"}])
    assert res[0]["resultados"] and res[1]["existe"] is False and res[2]["existe"] is True
    v = m.verificar_glosario(j, salida=tmp_path / "v.json")
    assert v["ok"], [f for f in v["filas"] if not f["ok"]]
