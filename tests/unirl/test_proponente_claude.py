"""17 oct 2026: Claude Sonnet 5.5 y Opus 5.5 como proponentes de unirl, sin llamar a la API.

El proveedor de Anthropic de steprl va sin fallback (un experimento tiene un solo proponente) y en streaming;
unirl.gasto.ProveedorContable registra su uso en el libro antes de juzgar la respuesta, como con OpenAI."""

from types import SimpleNamespace

import anthropic
import pytest

import steprl.providers as P
from unirl import experimentos as X
from unirl.gasto import GastoExcedido, Libro, ProveedorContable, costo
from unirl.loop import clasificar_error, complete_with_retries


def _resp(stop="end_turn", texto="PROOF: <<< by simp >>>", entrada=1000, lectura=200, escritura=0, salida=5000,
          pensamiento=4000, categoria=None):
    uso = SimpleNamespace(input_tokens=entrada, cache_read_input_tokens=lectura, cache_creation_input_tokens=escritura,
                          output_tokens=salida, output_tokens_details=SimpleNamespace(thinking_tokens=pensamiento))
    bloques = [SimpleNamespace(type="thinking", thinking="")] + ([SimpleNamespace(type="text", text=texto)] if texto else [])
    return SimpleNamespace(usage=uso, stop_reason=stop, content=bloques,
                           stop_details=SimpleNamespace(category=categoria) if categoria else None)


class _Stream:
    def __init__(self, resp):
        self.resp = resp

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def get_final_message(self):
        return self.resp


class _Cliente:
    """Lo mínimo de anthropic.Anthropic: messages.stream y beta.messages.create; anota cada llamada."""

    def __init__(self, resp):
        self.llamadas = []

        def stream(**kw):
            self.llamadas.append(("stream", kw))
            return _Stream(resp)

        def beta(**kw):
            self.llamadas.append(("beta", kw))
            return resp

        self.messages = SimpleNamespace(stream=stream)
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=beta))


@pytest.fixture
def cliente(monkeypatch):
    """Un proveedor de Anthropic sin red ni .env: devuelve el cliente simulado y una función para fijar su respuesta."""
    estado = {"cliente": _Cliente(_resp())}
    monkeypatch.setattr(P, "load_dotenv", lambda *a, **k: [])
    monkeypatch.setattr(anthropic, "Anthropic", lambda *a, **k: estado["cliente"])

    def con(resp):
        estado["cliente"] = _Cliente(resp)
        return estado["cliente"]
    return con


def test_precios_de_claude():
    assert costo("claude-sonnet-5-5", 1_000_000, 0, 1_000_000) == pytest.approx(12.0)
    assert costo("claude-opus-5-5", 1_000_000, 0, 1_000_000) == pytest.approx(24.0)
    assert costo("claude-sonnet-5-5", 1_000_000, 1_000_000, 0) == pytest.approx(0.10)  # lectura de la caché
    assert costo("claude-opus-5-5", 1_000_000, 0, 0, 1_000_000) == pytest.approx(5.0)  # escritura: 1,25 × 4
    assert costo("gpt-6-luna", 1208, 0, 8389) == pytest.approx((1208 * 0.10 + 8389 * 0.50) / 1e6)  # OpenAI, igual que antes


def test_el_modelo_elige_el_proveedor():
    assert X.proveedor_de("claude-sonnet-5-5") == X.proveedor_de("claude-opus-5-5") == "anthropic"
    assert X.proveedor_de("gpt-6-luna") == X.proveedor_de("gpt-6-sol") == "openai"


def test_sin_fallback_va_en_streaming_y_el_fallback_solo_si_se_pide(cliente):
    c = cliente(_resp())
    p = P.AnthropicProvider(model="claude-sonnet-5-5", effort="high", fallback_model=None, max_output_tokens=64000)
    assert "by simp" in p.complete("s", "u")
    (tipo, kw), = c.llamadas
    assert tipo == "stream" and kw["model"] == "claude-sonnet-5-5" and kw["max_tokens"] == 64000
    assert kw["output_config"] == {"effort": "high"} and "thinking" not in kw and "fallbacks" not in kw
    assert kw["system"] == [{"type": "text", "text": "s", "cache_control": {"type": "ephemeral"}}]
    assert kw["messages"] == [{"role": "user", "content": "u"}]
    c = cliente(_resp())
    # el fallback de servidor solo si se pide (desde el 17 oct no hay modelo ni fallback por defecto)
    P.AnthropicProvider(model="claude-fable-5-1", fallback_model="claude-opus-4-8").complete("s", "u")
    (tipo, kw), = c.llamadas
    assert tipo == "beta" and kw["model"] == "claude-fable-5-1" and kw["fallbacks"] == [{"model": "claude-opus-4-8"}]


def test_el_libro_registra_el_uso_de_claude(cliente, tmp_path):
    cliente(_resp())
    interno = P.AnthropicProvider(model="claude-sonnet-5-5", fallback_model=None, max_output_tokens=64000)
    libro = Libro(tmp_path / "gasto.json", tope_usd=25)
    p = ProveedorContable(interno, libro, fase="prueba", corrida="t", tope_llamadas=5)
    assert "by simp" in p.complete("s", "u")
    e = libro.entradas()[0]
    assert (e["modelo"], e["entrada"], e["cache"], e["cache_escritura"], e["salida"], e["razonamiento"]) == \
        ("claude-sonnet-5-5", 1200, 200, 0, 5000, 4000)
    assert e["usd"] == pytest.approx((1000 * 2.00 + 200 * 0.10 + 5000 * 10.00) / 1e6)
    assert p.ultimo_uso["usd"] == e["usd"]


def test_un_rechazo_se_paga_y_no_se_reintenta(cliente, tmp_path):
    c = cliente(_resp(stop="refusal", texto="", categoria="cyber"))
    interno = P.AnthropicProvider(model="claude-opus-5-5")
    libro = Libro(tmp_path / "gasto.json", tope_usd=25)
    p = ProveedorContable(interno, libro, fase="prueba", corrida="t")
    assert complete_with_retries(p, "s", "u", verbose=False, dormir=lambda s: None) is None  # sin propagar_rechazo: None
    assert len(c.llamadas) == 1 and len(libro.entradas()) == 1
    with pytest.raises(P.ProviderError, match="cyber"):
        interno.texto(_resp(stop="refusal", texto="", categoria="cyber"))


def test_corte_por_max_tokens(cliente, tmp_path):
    interno = P.AnthropicProvider(model="claude-sonnet-5-5", fallback_model=None)
    libro = Libro(tmp_path / "gasto.json", tope_usd=25)
    p = ProveedorContable(interno, libro, fase="prueba", corrida="t")
    cliente(_resp(stop="max_tokens", texto="PROOF: <<< by simp >>>"))
    interno._client = anthropic.Anthropic()
    assert "by simp" in p.complete("s", "u")  # como con OpenAI: el texto cortado puede traer la prueba
    cliente(_resp(stop="max_tokens", texto=""))
    interno._client = anthropic.Anthropic()
    assert complete_with_retries(p, "s", "u", verbose=False, dormir=lambda s: None) is None
    assert len(libro.entradas()) == 2  # las dos se pagaron


def test_unirl_crea_el_proponente_claude_sin_fallback_y_con_libro(cliente):
    cliente(_resp())
    p = X.proveedor("claude-opus-5-5", "evaluacion", "t")
    assert isinstance(p, ProveedorContable) and p.model == "claude-opus-5-5" and p.tope_llamadas == X.TOPES["evaluacion"]
    assert (p.interno.fallback_model, p.interno.max_output_tokens, p.interno.effort) == (None, 64000, "high")


def test_el_tope_cuenta_el_peor_caso_de_claude(tmp_path):
    libro = Libro(tmp_path / "gasto.json", tope_usd=0.5)
    with pytest.raises(GastoExcedido):  # 64k de salida de Sonnet 5.5 pueden costar $0,64
        libro.autorizar("claude-sonnet-5-5", "prueba", None, 3000, 64000)
    libro.autorizar("claude-sonnet-5-5", "prueba", None, 3000, 16000)  # $0,16 sí cabe


def test_sin_creditos_de_anthropic_es_fatal():
    assert clasificar_error(Exception("Your credit balance is too low to access the Anthropic API.")) == "fatal"
    assert clasificar_error(Exception("la petición fue rechazada por el modelo (cyber)")) == "otro"
