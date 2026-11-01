"""Conteo de tokens para la igualación de largo (§3.3, §17.7): `count_tokens` de la API de Anthropic, aislado.

Es la ÚNICA llamada a la API fuera de los episodios. No cuesta dinero, pero es una llamada de red: por eso vive aquí,
el resto del arnés recibe un objeto con `.contar(texto) -> int` y las pruebas usan `ContadorFalso`. Los conteos se
guardan en `conteos_tokens.json` (texto → tokens, con el modelo y el método) y la fase 2 exige que ese archivo exista
y cubra todas las líneas de todos los bloques (`verificar_conteos`).

Qué se cuenta (ronda 2, C3). `count_tokens` cuenta un MENSAJE completo, y cada mensaje lleva un armazón fijo de unos
pocos tokens. Por eso:
  * el largo de un bloque es el conteo del bloque ENTERO como un solo mensaje (`tokens_bloque`: las líneas unidas por
    saltos de línea, tal como van en el prompt), menos el armazón;
  * el armazón se mide UNA vez: `armazon = contar("x") − 1` (la letra «x» es un token);
  * los costos por lema que usa la selección (`tokens_linea`) son conteos por línea menos el armazón, y son solo una
    guía: el total que decide «ok / corto» y el que se reporta es siempre el del bloque entero.
"""

from __future__ import annotations

import hashlib
import json
import threading
from pathlib import Path

MODELO_CONTEO = "claude-haiku-5-5"
METODO_API = "anthropic.messages.count_tokens"
SONDA_ARMAZON = "x"


def _sha(t: str) -> str:
    return hashlib.sha256(t.encode()).hexdigest()


class Conteos:
    """Caché persistente texto → tokens crudos (lo que devuelve la API). `contador` es cualquier objeto con
    `.contar(texto) -> int` y `.metodo`."""

    def __init__(self, ruta: Path, contador=None, modelo: str = MODELO_CONTEO):
        self.ruta, self.contador, self.modelo = Path(ruta), contador, modelo
        self._lock = threading.Lock()
        if self.ruta.exists():
            d = json.loads(self.ruta.read_text(encoding="utf-8"))
            self.datos = d.get("conteos", {})
            self.meta = d.get("meta", {})
        else:
            self.datos, self.meta = {}, {}

    def tokens(self, texto: str) -> int:
        """Conteo crudo (con armazón) de `texto` como un mensaje."""
        k = _sha(texto)
        with self._lock:
            if k in self.datos:
                return int(self.datos[k]["tokens"])
        if self.contador is None:
            raise KeyError(f"sin conteo para un texto y sin contador: {texto[:80]!r}")
        n = int(self.contador.contar(texto))
        with self._lock:
            self.datos[k] = {"tokens": n, "texto": texto}
            self.meta.update({"modelo": self.modelo, "metodo": getattr(self.contador, "metodo", "?")})
        return n

    def armazon(self) -> int:
        """Tokens fijos de un mensaje: contar("x") − 1, medido una vez y guardado en meta."""
        if "armazon" not in self.meta:
            self.meta["armazon"] = max(0, self.tokens(SONDA_ARMAZON) - 1)
        return int(self.meta["armazon"])

    def tokens_linea(self, linea: str) -> int:
        """Costo aproximado de una línea (sin armazón), para la selección; nunca menor que 1."""
        return max(1, self.tokens(linea) - self.armazon())

    def tokens_bloque(self, lineas: list[str]) -> int:
        """El largo del bloque como lo ve el modelo: un solo mensaje con las líneas unidas, sin armazón. Vacío = 0."""
        if not lineas:
            return 0
        return max(0, self.tokens("\n".join(lineas)) - self.armazon())

    def cubre(self, textos: list[str]) -> list[str]:
        """Los textos que NO tienen conteo (vacío = todo cubierto)."""
        return [t for t in textos if _sha(t) not in self.datos]

    def guardar(self) -> str:
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        txt = json.dumps({"meta": self.meta, "n": len(self.datos), "conteos": self.datos}, ensure_ascii=False, indent=0, sort_keys=True)
        self.ruta.write_text(txt, encoding="utf-8")
        return _sha(txt)


class ContadorFalso:
    """Para pruebas: tokens ≈ palabras + signos + un armazón fijo por mensaje (determinista, sin red)."""
    metodo = "falso:palabras"

    def __init__(self, armazon: int = 0):
        self.armazon = armazon

    def contar(self, texto: str) -> int:
        import re
        return self.armazon + max(1, len(re.findall(r"\w+|[^\w\s]", texto)))


class ContadorAPI:
    """`client.messages.count_tokens` del SDK de Anthropic (sin costo). Solo se construye cuando se va a usar."""
    metodo = METODO_API

    def __init__(self, modelo: str = MODELO_CONTEO):
        import anthropic  # importado aquí: el resto del arnés no necesita el SDK para probarse
        self.modelo = modelo
        self._client = anthropic.Anthropic()

    def contar(self, texto: str) -> int:
        r = self._client.messages.count_tokens(model=self.modelo, messages=[{"role": "user", "content": texto}])
        return int(r.input_tokens)


def verificar_conteos(ruta: Path, lineas_necesarias: list[str], exigir_api: bool = True, bloques_necesarios: list[list[str]] | None = None) -> list[str]:
    """Motivos por los que la fase 2 NO puede arrancar con estos conteos (vacío = todo bien): método de la API, modelo,
    armazón medido, y conteo de cada línea y de cada bloque entero que figura en el anexo."""
    ruta = Path(ruta)
    if not ruta.exists():
        return [f"no existe {ruta}"]
    c = Conteos(ruta)
    motivos = []
    if exigir_api and c.meta.get("metodo") != METODO_API:
        motivos.append(f"los conteos no vienen de {METODO_API} (método: {c.meta.get('metodo')!r})")
    if c.meta.get("modelo") != MODELO_CONTEO:
        motivos.append(f"los conteos no son de {MODELO_CONTEO} (modelo: {c.meta.get('modelo')!r})")
    if "armazon" not in c.meta:
        motivos.append("falta el armazón medido (contar('x') − 1)")
    faltan = c.cubre(lineas_necesarias)
    if faltan:
        motivos.append(f"faltan conteos para {len(faltan)} líneas (p. ej. {faltan[0][:80]!r})")
    if bloques_necesarios:
        faltan_b = c.cubre(["\n".join(b) for b in bloques_necesarios if b])
        if faltan_b:
            motivos.append(f"faltan conteos de {len(faltan_b)} bloques enteros")
    return motivos
