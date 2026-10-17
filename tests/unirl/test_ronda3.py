"""17 oct 2026: ronda 3, exploratoria y de mecanismo, con Claude Sonnet 5.5 y Opus 5.5 (sin llamar a la API).

Prerregistro: docs/formulacion/formulacion_rl_verbal.tex, párrafo «Ronda 3». Aquí: el lanzador y sus parámetros, el
rechazo del modelo como intento fallido (REFUSAL) que no invalida el episodio, el esfuerzo y la temperatura en cada
llamada, la caché del mensaje de sistema, el modelo obligatorio y la red que vigila la ronda."""

import json
import subprocess
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import anthropic
import pytest

import steprl.providers as P
from unirl import corpus, martillo as M, reflexion as R
from unirl.gasto import Libro, ProveedorContable
from unirl.loop import Rechazo, complete_with_retries
from unirl.tools import ronda

TOOLS = Path(__file__).resolve().parents[2] / "unirl" / "tools"


def _resp(stop="end_turn", texto="PROOF: <<< by simp >>>", categoria=None):
    uso = SimpleNamespace(input_tokens=1000, cache_read_input_tokens=0, cache_creation_input_tokens=0, output_tokens=500,
                          output_tokens_details=SimpleNamespace(thinking_tokens=300))
    bloques = [SimpleNamespace(type="text", text=texto)] if texto else []
    return SimpleNamespace(usage=uso, stop_reason=stop, content=bloques,
                           stop_details=SimpleNamespace(category=categoria) if categoria else None)


class _Cliente:
    def __init__(self, resp):
        self.kw = []

        class _S:
            def __enter__(s):
                return s

            def __exit__(s, *e):
                return False

            def get_final_message(s):
                return resp

        def stream(**kw):
            self.kw.append(kw)
            return _S()
        self.messages = SimpleNamespace(stream=stream)


@pytest.fixture
def anth(monkeypatch):
    estado = {}
    monkeypatch.setattr(P, "load_dotenv", lambda *a, **k: [])
    monkeypatch.setattr(anthropic, "Anthropic", lambda *a, **k: estado["c"])

    def hacer(resp, modelo="claude-opus-5-5"):
        estado["c"] = _Cliente(resp)
        return P.AnthropicProvider(model=modelo, effort="high", max_output_tokens=64000), estado["c"]
    return hacer


# ------------------------------------------------------------------------------------------- el lanzador

def test_lanzador_de_la_ronda_3_con_los_parametros_prerregistrados():
    for g in ("lanzar_ronda3.sh", "preflight.sh"):
        assert subprocess.run(["bash", "-n", str(TOOLS / g)], capture_output=True).returncode == 0, g
    txt = (TOOLS / "lanzar_ronda3.sh").read_text(encoding="utf-8")
    for v in ("MODELO_SONNET=claude-sonnet-5-5", "MODELO_OPUS=claude-opus-5-5", "EPISODIOS=2", "HASH_CUADERNO=835d3070e3b0c3b1",
              "JUEZ=teorema-2026-09-30", "TOPE_TOTAL_USD=75", '"evaluacion": 37.5', '"evaluacion_E": 37.5',
              'RONDA_RED_URL="https://api.anthropic.com/v1/models"', 'MODELO_PREFLIGHT="$MODELO_SONNET,$MODELO_OPUS"',
              'fase_evaluar 01_sonnet_C evaluacion "$MODELO_SONNET" C', 'fase_evaluar 02_sonnet_E evaluacion_E "$MODELO_SONNET" E',
              'fase_evaluar 03_opus_C evaluacion "$MODELO_OPUS" C', 'fase_evaluar 04_opus_E evaluacion_E "$MODELO_OPUS" E',
              "logs/ronda3_actual", "*api-key*"):
        assert v in txt, v
    # la auditoría va antes de cualquier análisis: el lanzador no consolida métricas ni escribe RONDA_TERMINADA.md
    assert "consolidar.py" not in txt and "informe --ronda" not in txt
    # el tope cubre las dos fases: 37,5 + 37,5 = 75
    topes = json.loads(txt.split("TOPES_FASE_JSON='", 1)[1].split("'", 1)[0])
    assert topes["evaluacion"] + topes["evaluacion_E"] == 75 and topes["cuaderno"] == topes["pareada_luna"] == 0


def test_la_red_que_se_vigila_es_la_del_proponente(monkeypatch):
    vistas = []
    monkeypatch.setattr("urllib.request.urlopen", lambda req, timeout: vistas.append(req.full_url))
    monkeypatch.setenv("RONDA_RED_URL", "https://api.anthropic.com/v1/models")
    assert ronda.red_ok() and vistas == ["https://api.anthropic.com/v1/models"]
    monkeypatch.delenv("RONDA_RED_URL")
    assert ronda.red_ok() and vistas[-1] == "https://api.openai.com/v1/models"  # la ronda 2, sin cambios


# ------------------------------------------------------------------------------------------- el proveedor

def test_el_modelo_es_obligatorio_y_no_hay_fallback(anth):
    with pytest.raises(P.ProviderError, match="indica --model"):
        P.make_provider("anthropic", None)
    with pytest.raises(TypeError):
        P.AnthropicProvider()  # sin Fable 5.1 por defecto
    p, _ = anth(_resp())
    assert p.fallback_model is None


def test_el_sistema_va_con_cache_y_sin_temperatura(anth):
    p, c = anth(_resp())
    p.complete("SISTEMA", "u")
    (kw,) = c.kw
    assert kw["system"] == [{"type": "text", "text": "SISTEMA", "cache_control": {"type": "ephemeral"}}]
    assert "temperature" not in kw and kw["output_config"] == {"effort": "high"} and "fallbacks" not in kw


def test_esfuerzo_y_temperatura_en_cada_llamada(anth, tmp_path):
    p, _ = anth(_resp(), modelo="claude-sonnet-5-5")
    libro = Libro(tmp_path / "gasto.json", tope_usd=25)
    prov = ProveedorContable(p, libro, fase="evaluacion", corrida="t")
    prov.complete("s", "u")
    assert (prov.ultimo_uso["effort"], prov.ultimo_uso["temperatura"]) == ("high", None)
    e = libro.entradas()[0]
    assert (e["effort"], e["temperatura"], e["modelo"]) == ("high", None, "claude-sonnet-5-5")


# ------------------------------------------------------------------------------------------- el rechazo

def test_un_rechazo_se_registra_y_sube_como_rechazo(anth, tmp_path):
    p, c = anth(_resp(stop="refusal", texto="", categoria="cyber"))
    libro = Libro(tmp_path / "gasto.json", tope_usd=25)
    prov = ProveedorContable(p, libro, fase="evaluacion", corrida="t")
    with pytest.raises(Rechazo) as e:
        complete_with_retries(prov, "s", "u", verbose=False, dormir=lambda s: None, propagar_rechazo=True)
    assert e.value.categoria == "cyber" and len(c.kw) == 1 and len(libro.entradas()) == 1  # se pagó, sin reintento
    assert complete_with_retries(prov, "s", "u", verbose=False, dormir=lambda s: None) is None  # sin propagar: None
    assert len(c.kw) == 2


class _Proponente:
    """Rechaza la primera petición y luego responde sin PROOF: REFUSAL y después INVALID_PROPOSAL, sin Isabelle."""
    model = "claude-opus-5-5"

    def __init__(self):
        self.calls, self.ultimo_uso = 0, None

    def complete(self, system, user):
        self.calls += 1
        self.ultimo_uso = {"entrada": 10, "salida": 5, "usd": 0.001, "effort": "high", "temperatura": None}
        if self.calls == 1:
            raise Rechazo("cyber")
        return "Lo siento, no tengo una prueba."


def test_el_episodio_cuenta_el_rechazo_como_intento_fallido(tmp_path):
    spec = corpus.exigir_usable("rf_1_punto")
    cfg = replace(R.CONFIGS["C"], intentos=2, consulta=False)
    registro = tmp_path / "llamadas.jsonl"
    ep = R.episodio(spec, cfg, _Proponente(), registro, {"episodio_id": "rf_1_punto#C#1"},
                    cache=M.Cache(tmp_path / "cache.sqlite"), resueltos=set(), verbose=False)
    filas = [json.loads(l) for l in registro.read_text(encoding="utf-8").splitlines()]
    assert [f["etiqueta"] for f in filas] == ["REFUSAL", "INVALID_PROPOSAL"]
    assert filas[0]["categoria_rechazo"] == "cyber" and filas[0]["uso"]["effort"] == "high"
    assert ep["intentos"] == 2 and ep["aceptado"] is False and "REFUSAL" in ep["historia"][0]["feedback"]


def test_un_episodio_con_rechazos_es_valido_y_uno_solo_de_red_no(tmp_path, monkeypatch):
    d = tmp_path / "evaluacion" / "20261018-100000-claude-opus-5-5"
    d.mkdir(parents=True)
    (d / "meta.json").write_text(json.dumps({"inicio": "2026-10-18T10:00:00", "modelo": "claude-opus-5-5", "configs": ["C"]}))
    ints = [{"tipo": "intento", "episodio_id": "a#C#1", "etiqueta": "REFUSAL"},
            {"tipo": "intento", "episodio_id": "b#C#1", "etiqueta": "PROVIDER_ERROR"}]
    (d / "llamadas.jsonl").write_text("\n".join(json.dumps(x) for x in ints) + "\n")
    (d / "episodios.jsonl").write_text("\n".join(json.dumps({"episodio_id": e, "peldano": e[0], "aceptado": False})
                                                 for e in ("a#C#1", "b#C#1")) + "\n")
    monkeypatch.setattr(ronda, "RUNS", tmp_path)
    val = ronda.episodios_validos("evaluacion", "2026-10-18T00:00:00", "claude-opus-5-5", ["C"])
    assert set(val) == {"a#C#1"}
    assert ronda.episodios_validos("evaluacion", "2026-10-18T00:00:00", "claude-sonnet-5-5", ["C"]) == {}  # otro modelo
