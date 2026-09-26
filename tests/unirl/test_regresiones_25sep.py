"""Regresiones de las corridas del 25 sep 2026 (Etapa 7), que se detuvieron por dos errores del código.

1. El caché SQLite del martillo se creaba en el hilo principal y la evaluación lo usaba desde hilos trabajadores:
   `Cache.lineas_de` lanzaba sqlite3.ProgrammingError en todo episodio con marcas `by martillo`. Como `evaluar` solo
   capturaba ProviderFatal, esos episodios morían sin registro y la corrida seguía hasta el final (63 de 128 perdidos).
2. La destilación añade errores «aprendidos», que no tienen `en_su_lugar`, y `render_errores` (errores.md) fallaba
   con KeyError al guardar el cuaderno (la construcción se detuvo tras 6 de 32 episodios).
"""

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from unirl import cuaderno as C, experimentos as X, martillo as M
from unirl.gd_isabelle import TheoremVerifier

HERE = Path(__file__).resolve().parent
PRIV = HERE / "fixtures" / "pruebas_privadas"

# una prueba de orden_1_lineal con el paso inductivo marcado para el martillo (pasa los filtros del juez)
PRUEBA_CON_MARCA = ("proof (induction n)\n  case 0\n  then show ?case by simp\nnext\n  case (Suc n)\n"
                    "  then show ?case by martillo\nqed")


@pytest.fixture(autouse=True)
def cuaderno_real_intacto():
    """Ninguna prueba puede escribir en el cuaderno real."""
    def foto():
        return {f.name: f.read_bytes() for f in C.DIR.iterdir() if f.is_file()} if C.DIR.exists() else {}
    antes = foto()
    yield
    assert foto() == antes, "una prueba modificó el cuaderno real"


# ----------------------------------------------------------------------------- 1. el martillo desde hilos trabajadores


def test_cache_del_martillo_desde_hilos_trabajadores(tmp_path):
    """Un caché creado en el hilo principal, como en `evaluar`, usado a la vez desde cuatro hilos."""
    cache = M.Cache(tmp_path / "c.sqlite")

    def trabajo(i):
        clave = M.Cache.clave("paso", str(i))
        cache.guardar(clave, "paso", {"contexto": "ctx", "meta": f"meta {i}", "linea": f"by simp {i}"})
        assert cache.leer(clave)["linea"] == f"by simp {i}"
        return len(cache.lineas_de("ctx"))

    with ThreadPoolExecutor(max_workers=4) as ex:
        vistos = list(ex.map(trabajo, range(40)))
    assert max(vistos) == 40 and len(cache.lineas_de("ctx")) == 40


class _Alto(Exception):
    """Corta martillo_en_pasos justo después de consultar el caché, antes de llamar a Isabelle."""


def test_martillo_en_pasos_consulta_el_cache_desde_un_hilo_trabajador(tmp_path, monkeypatch):
    """El camino exacto que falló el 25 sep: una prueba con `by martillo`, en un hilo trabajador, con el caché creado
    en el hilo principal. Sin Isabelle: se detiene al pedir el directorio de trabajo, que va después del caché."""
    juez = TheoremVerifier.desde_corpus("orden_1_lineal")
    monkeypatch.setattr(juez, "_workdir", lambda *a, **k: (_ for _ in ()).throw(_Alto()))
    cache = M.Cache(tmp_path / "c.sqlite")
    with ThreadPoolExecutor(max_workers=1) as ex:
        futuro = ex.submit(M.martillo_en_pasos, juez, PRUEBA_CON_MARCA, cache=cache)
        with pytest.raises(_Alto):
            futuro.result()


@pytest.mark.isabelle
def test_isabelle_martillo_en_pasos_en_dos_hilos_trabajadores(tmp_path):
    """Dos episodios a la vez, como `evaluar --paralelo 2`: cada hilo corre el martillo por pasos de verdad (con su
    candado entre procesos) sobre el mismo caché, creado en el hilo principal. Los dos deben aceptar."""
    if not (PRIV / "orden_1_lineal.txt").exists():
        pytest.skip("falta la prueba de referencia privada (no se versiona)")
    prueba = (PRIV / "orden_1_lineal.txt").read_text().replace("by (rule mult_left_mono)", "by martillo")
    cache = M.Cache(tmp_path / "c.sqlite")

    def uno(_):
        return M.martillo_en_pasos(TheoremVerifier.desde_corpus("orden_1_lineal"), prueba, cache=cache)

    with ThreadPoolExecutor(max_workers=2) as ex:
        rs = list(ex.map(uno, range(2)))
    assert all(r["marcas"] == r["cerradas"] == 1 and r["veredicto_juez"] == "ACCEPTED" for r in rs), rs


# ----------------------------------------------------------------------------- 1'. un error del código detiene evaluar


def _falso_episodio(corridos: list[str], falla_en: str):
    def f(spec, cfg, prov, llamadas_f, meta, **kw):
        corridos.append(spec["id"])
        if spec["id"] == falla_en:
            raise RuntimeError("fallo simulado del código")
        return {"episodio_id": meta["episodio_id"], "peldano": spec["id"], "metodo": "m", "split": "test",
                "dificultad": 1, "config": cfg.nombre if hasattr(cfg, "nombre") else "B0", "aceptado": False,
                "intento_exito": None, "intentos": 1, "llamadas": 1, "consultas": 0, "r_V_max": 0.0, "usd": 0.0}
    return f


def _evaluar_simulado(tmp_path, monkeypatch, falla_en: str, paralelo: int):
    specs = [{"id": f"p{i}", "metodo": "m", "split": "test", "dificultad": 1} for i in range(6)]
    corridos: list[str] = []
    monkeypatch.setattr(X, "RUNS", tmp_path / "runs")
    monkeypatch.setattr(X, "peldanos", lambda split, ids=None: specs)
    monkeypatch.setattr(X, "proveedor", lambda *a, **k: object())
    monkeypatch.setattr(X, "resueltos_por_martillo", lambda clave, ids: set())
    monkeypatch.setattr(X.M, "Cache", lambda *a, **k: None)  # el episodio simulado no lo usa
    monkeypatch.setattr(X, "episodio", _falso_episodio(corridos, falla_en))
    out = X.evaluar("simulado", ["B0"], 1, paralelo, "ninguno", verbose=False)
    return out, corridos


def test_evaluar_se_detiene_ante_un_error_del_codigo(tmp_path, monkeypatch):
    out, corridos = _evaluar_simulado(tmp_path, monkeypatch, falla_en="p1", paralelo=1)
    assert corridos == ["p0", "p1"]  # tras el fallo no se lanza ningún episodio más
    abortada = (out / "ABORTADA.txt").read_text(encoding="utf-8")
    assert "fallo simulado del código" in abortada and "Traceback" in abortada
    eps = [json.loads(l) for l in (out / "episodios.jsonl").read_text().splitlines()]
    assert [e["peldano"] for e in eps] == ["p0"] and (out / "resumen.md").exists()


def test_main_devuelve_error_si_la_corrida_se_detuvo(tmp_path, monkeypatch):
    """Para encadenar etapas con &&: una corrida detenida sale con código distinto de cero."""
    specs = [{"id": "p0", "metodo": "m", "split": "test", "dificultad": 1}]
    monkeypatch.setattr(X, "RUNS", tmp_path / "runs")
    monkeypatch.setattr(X, "peldanos", lambda split, ids=None: specs)
    monkeypatch.setattr(X, "proveedor", lambda *a, **k: object())
    monkeypatch.setattr(X, "resueltos_por_martillo", lambda clave, ids: set())
    monkeypatch.setattr(X.M, "Cache", lambda *a, **k: None)
    monkeypatch.setattr(X, "episodio", _falso_episodio([], falla_en="p0"))
    assert X.main(["evaluar", "--configs", "B0", "--episodios", "1", "--paralelo", "1"]) == 1


# ----------------------------------------------------------------------------- 2. errores aprendidos en errores.md


def _aprendido(texto: str, afirma: list[dict]) -> dict:
    return {"texto": texto, "afirma": afirma, "contadores": {"apariciones": 0, "ultimo_episodio": None}}


def test_render_errores_con_errores_aprendidos():
    doc = C.sembrar_errores()
    n_glosario = len(doc["errores"])
    c = C.Cuaderno.__new__(C.Cuaderno)
    c.errores, c.lemas, c.estrategias = doc, [], []
    c.agregar_error(_aprendido("Se invocó un hecho no disponible con el nombre `mult_commute`.",
                               [{"tipo": "hecho", "nombre": "mult_commute", "existe": False}]), {"destilacion": "t"})
    c.agregar_error(_aprendido("`smt` no dedujo el signo del producto.", []), {"destilacion": "t"})
    md = C.render_errores(doc)
    assert "mult_commute" in md and "`smt` no dedujo el signo del producto." in md
    assert md.count("\n## ") == n_glosario + 2  # una sección por error, glosario y aprendidos


def test_guardar_el_cuaderno_con_errores_aprendidos_escribe_errores_md(tmp_path, monkeypatch):
    vivo = tmp_path / "cuaderno"
    vivo.mkdir()
    monkeypatch.setattr(C, "DIR", vivo)
    c = C.Cuaderno()
    c.errores = C.sembrar_errores()
    c.agregar_error(_aprendido("Isabelle rechazó el método `nlinarith` como indefinido.",
                               [{"tipo": "metodo", "nombre": "nlinarith", "existe": False}]), {"destilacion": "t"})
    c.guardar()
    md = (vivo / "errores.md").read_text(encoding="utf-8")
    assert md == C.render_errores(c.errores) and "nlinarith` como indefinido" in md
