"""Libro de gastos: costo real de cada llamada a la API y topes que abortan antes de pasarse (PLAN_rl_verbal.md §9).

Cada llamada se registra con los tokens que devuelve la API (entrada, entrada en caché, salida y razonamiento) y
su costo con los precios oficiales. Antes de cada llamada, `autorizar` exige que el total gastado más el peor caso
de la llamada siguiente (entrada estimada + máximo de salida) no pase del tope en dólares, y que la fase no haya
agotado su tope de llamadas. Si no, lanza GastoExcedido, que aborta la corrida (no se registra como PROVIDER_ERROR).
El libro persiste en logs/gasto.json: el tope es para todo el proyecto, no por corrida.
"""

from __future__ import annotations

import contextlib
import fcntl
import json
import os
import tempfile
import threading
import time
from pathlib import Path

from .loop import ProviderFatal

BASE = Path(__file__).resolve().parent.parent
LIBRO = BASE / "logs" / "gasto.json"

# USD por millón de tokens: (entrada, entrada en caché, salida). Página de precios de OpenAI, consultada el 24 sep 2026.
PRECIOS = {
    "gpt-6-luna": (0.10, 0.01, 0.50),
    "gpt-6-sol": (2.00, 0.20, 10.00),
    "gpt-6-astra": (10.00, 1.00, 50.00),
    "gpt-5.6-terra": (2.00, 0.20, 12.00),
}
TOPE_USD = 25.0  # decisión de Carlos (24 sep 2026); puede subir a 28 solo si el costo medido de Sol lo requiere


class GastoExcedido(ProviderFatal):
    """La llamada siguiente podría pasar del tope en dólares, o la fase agotó su tope de llamadas."""


def costo(modelo: str, tokens_entrada: int, tokens_cache: int, tokens_salida: int) -> float:
    if modelo not in PRECIOS:
        raise GastoExcedido(f"sin precio registrado para {modelo}: no se autoriza la llamada")
    pe, pc, ps = PRECIOS[modelo]
    return ((tokens_entrada - tokens_cache) * pe + tokens_cache * pc + tokens_salida * ps) / 1e6


class _CerrojoLibro:
    """Candado de hilos y de procesos (archivo) para el libro: dos corridas en terminales distintas no se pisan."""
    _hilos = threading.Lock()

    def __init__(self, ruta: Path):
        self.ruta = Path(str(ruta) + ".lock")

    @contextlib.contextmanager
    def __call__(self):
        with self._hilos:
            self.ruta.parent.mkdir(parents=True, exist_ok=True)
            with open(self.ruta, "w") as fh:
                fcntl.flock(fh, fcntl.LOCK_EX)
                try:
                    yield
                finally:
                    fcntl.flock(fh, fcntl.LOCK_UN)


class Libro:

    def __init__(self, ruta: Path | None = None, tope_usd: float = TOPE_USD):
        self.ruta = Path(ruta) if ruta else LIBRO
        self.tope_usd = float(tope_usd)
        self._cerrojo = _CerrojoLibro(self.ruta)

    def entradas(self) -> list[dict]:
        if not self.ruta.exists():
            return []
        return json.loads(self.ruta.read_text(encoding="utf-8")).get("llamadas", [])

    def total(self) -> float:
        return round(sum(e["usd"] for e in self.entradas()), 6)

    def llamadas(self, fase: str) -> int:
        return sum(1 for e in self.entradas() if e.get("fase") == fase)

    def autorizar(self, modelo: str, fase: str, tope_llamadas: int | None, chars_entrada: int, max_salida: int) -> float:
        """Peor caso de la llamada siguiente; GastoExcedido si con él se pasa del tope o la fase agotó sus llamadas."""
        peor = costo(modelo, chars_entrada // 3 + 1, 0, max_salida)
        with self._cerrojo():
            gastado = self.total()
            if gastado + peor > self.tope_usd:
                raise GastoExcedido(f"tope de ${self.tope_usd:.2f}: gastado ${gastado:.4f}, la llamada siguiente puede costar hasta ${peor:.4f}")
            if tope_llamadas is not None and self.llamadas(fase) >= tope_llamadas:
                raise GastoExcedido(f"la fase {fase!r} agotó su tope de {tope_llamadas} llamadas")
        return peor

    def registrar(self, modelo: str, fase: str, corrida: str, uso: dict) -> float:
        usd = costo(modelo, uso.get("entrada", 0), uso.get("cache", 0), uso.get("salida", 0))
        with self._cerrojo():
            datos = {"llamadas": self.entradas()}
            datos["llamadas"].append({"fecha": time.strftime("%Y-%m-%dT%H:%M:%S"), "modelo": modelo, "fase": fase, "corrida": corrida,
                                      **uso, "usd": round(usd, 6)})
            datos["total_usd"] = round(sum(e["usd"] for e in datos["llamadas"]), 6)
            datos["tope_usd"] = self.tope_usd
            self.ruta.parent.mkdir(parents=True, exist_ok=True)
            fd, tmp = tempfile.mkstemp(dir=str(self.ruta.parent), prefix=".gasto-")
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(datos, fh, ensure_ascii=False, indent=1)
            os.replace(tmp, self.ruta)  # escritura atómica: dos corridas en paralelo no corrompen el libro
        return usd


class ProveedorContable:
    """Envuelve el proveedor OpenAI del 06 (sin modificarlo): hace la misma llamada, lee `usage` y la registra en el
    libro, autorizando antes cada llamada contra los topes."""

    def __init__(self, interno, libro: Libro, fase: str, corrida: str, tope_llamadas: int | None = None):
        if not hasattr(interno, "_client"):
            raise GastoExcedido("el libro de gastos solo sabe contabilizar el proveedor OpenAI")
        self.interno, self.libro, self.fase, self.corrida, self.tope_llamadas = interno, libro, fase, corrida, tope_llamadas
        self.model = interno.model
        self.calls = 0
        self._local = threading.local()  # uso de la última llamada, por hilo (episodios en paralelo)

    def complete(self, system: str, user: str) -> str:
        max_salida = int(getattr(self.interno, "max_output_tokens", 64000))
        self.libro.autorizar(self.model, self.fase, self.tope_llamadas, len(system) + len(user), max_salida)
        kwargs = {}
        if getattr(self.interno, "reasoning_effort", None):
            kwargs["reasoning_effort"] = self.interno.reasoning_effort
        resp = self.interno._client.chat.completions.create(
            model=self.model, messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            max_completion_tokens=max_salida, **kwargs)
        u = resp.usage
        det_e, det_s = getattr(u, "prompt_tokens_details", None), getattr(u, "completion_tokens_details", None)
        uso = {"entrada": int(u.prompt_tokens or 0), "cache": int(getattr(det_e, "cached_tokens", 0) or 0),
               "salida": int(u.completion_tokens or 0), "razonamiento": int(getattr(det_s, "reasoning_tokens", 0) or 0)}
        usd = self.libro.registrar(self.model, self.fase, self.corrida, uso)  # se registra aunque la respuesta sea inútil: se pagó
        self.calls += 1
        self._local.uso = {**uso, "usd": round(usd, 6)}  # el episodio lo copia en el registro de cada llamada
        choice = resp.choices[0]
        text = choice.message.content or ""
        if choice.finish_reason == "length" and not text.strip():
            raise RuntimeError("la respuesta se cortó por longitud")
        return text

    @property
    def ultimo_uso(self) -> dict | None:
        return getattr(self._local, "uso", None)

