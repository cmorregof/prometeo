"""Lo que el guion de la ronda (unirl/tools/lanzar_ronda.sh) exige de unirl: la política de reintentos y los topes."""

import json
import os

import pytest

from unirl import gasto as G
from unirl.loop import ESPERAS_REINTENTO, ProviderFatal, clasificar_error, complete_with_retries


class _Exc(Exception):
    def __init__(self, msg, status=None):
        super().__init__(msg)
        if status is not None:
            self.status_code = status


class _Prov:
    def __init__(self, fallos):
        self.fallos, self.calls = list(fallos), 0

    def complete(self, system, user):
        self.calls += 1
        if self.fallos:
            raise self.fallos.pop(0)
        return "OK"


def test_clasificacion_de_errores():
    assert clasificar_error(_Exc("Error code: 429 - insufficient_quota", 429)) == "fatal"   # créditos, aunque sea 429
    assert clasificar_error(_Exc("Incorrect API key provided", 401)) == "fatal"
    assert clasificar_error(_Exc("Rate limit reached", 429)) == "transitorio"
    assert clasificar_error(_Exc("Internal server error", 500)) == "transitorio"
    assert clasificar_error(_Exc("Connection error.")) == "transitorio"
    assert clasificar_error(_Exc("la respuesta se cortó por longitud")) == "otro"


def test_reintenta_cinco_veces_con_espera_exponencial_y_luego_desiste():
    esperas = []
    prov = _Prov([_Exc("Connection error.")] * 7)
    assert complete_with_retries(prov, "s", "u", verbose=False, dormir=esperas.append) is None
    assert prov.calls == 6 and esperas == list(ESPERAS_REINTENTO) == [2, 5, 11, 26, 60]


def test_reintento_exitoso_y_fatal_inmediato():
    esperas = []
    prov = _Prov([_Exc("Rate limit reached", 429), _Exc("Bad gateway", 502)])
    assert complete_with_retries(prov, "s", "u", verbose=False, dormir=esperas.append) == "OK" and esperas == [2, 5]
    prov = _Prov([_Exc("You exceeded your current quota (insufficient_quota)", 429)])
    with pytest.raises(ProviderFatal):
        complete_with_retries(prov, "s", "u", verbose=False, dormir=esperas.append)
    assert prov.calls == 1


def test_libro_propio_y_topes_por_fase(tmp_path, monkeypatch):
    libro = G.Libro(ruta=tmp_path / "gasto_ronda.json", tope_usd=12.0, topes_fase={"pareada_sol": 6.0, "linea_base": 0.0})
    assert libro.total() == 0.0
    libro.registrar("gpt-6-sol", "pareada_sol", "c1", {"entrada": 1_000_000, "cache": 0, "salida": 300_000})  # $2 + $3 = $5
    assert libro.gastado("pareada_sol") == 5.0 and libro.total() == 5.0
    with pytest.raises(G.GastoExcedido):  # el peor caso de la llamada siguiente pasa del tope de la fase
        libro.autorizar("gpt-6-sol", "pareada_sol", None, chars_entrada=3000, max_salida=200_000)
    libro.autorizar("gpt-6-luna", "cuaderno", None, chars_entrada=3000, max_salida=64_000)  # otra fase: sin tope propio
    with pytest.raises(G.GastoExcedido):
        libro.autorizar("gpt-6-luna", "linea_base", None, chars_entrada=30, max_salida=1)  # tope $0: nada de API
    datos = json.loads((tmp_path / "gasto_ronda.json").read_text())
    assert datos["total_usd"] == 5.0 and datos["tope_usd"] == 12.0


def test_variables_de_entorno_del_libro(tmp_path, monkeypatch):
    monkeypatch.setenv("UNIRL_TOPES_FASE_USD", json.dumps({"evaluacion_E": 2.0}))
    assert G.topes_fase_usd() == {"evaluacion_E": 2.0}
    assert G.Libro(ruta=tmp_path / "x.json").topes_fase == {"evaluacion_E": 2.0}
    monkeypatch.delenv("UNIRL_TOPES_FASE_USD")
    assert G.Libro(ruta=tmp_path / "x.json").topes_fase == {}
