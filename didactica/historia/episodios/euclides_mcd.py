"""Euclides, *Elementos* VII.1–2: medir un segmento con otro (antifairesis).

Fase 1. Dos segmentos de longitudes enteras a ≥ b. El agente no conoce el
algoritmo. Acciones:

  0  quitar b de a UNA vez               (lo que hace Euclides con el compás)
  1  quitar b de a TODAS las veces que quepa (quedarse con el residuo)
  2  declarar: "b mide a a" — b es la medida común

Recompensa: −1 por cada acción; +20 si la declaración es correcta (b | a);
−10 y fin si declara en falso. Si tras quitar el par queda a < b, se
intercambian solos (el menor pasa a medir al mayor). Aprende: si b divide a,
declarar; si no, quedarse con el residuo. Eso ES el algoritmo de Euclides.

Fase 2. Demostrar que el proceso termina y que el último resto no nulo es la
mayor medida común.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from rich.table import Table
from rich.text import Text

from ..core import Episodio, ProofKB, Raster, Step

ONE, ALL, DECLARE = 0, 1, 2


@dataclass
class EuclidEnv:
    seed: int = 0
    n_actions: int = 3
    action_names: list[str] = field(default_factory=lambda: ["quitar b una vez", "quitar b hasta el residuo", "declarar: b mide a a"])
    rng: random.Random = field(init=False)
    a0: int = 0
    b0: int = 0
    a: int = 0
    b: int = 0
    n: int = 0
    history: list[tuple[int, int]] = field(default_factory=list)
    last: str = ""

    def __post_init__(self) -> None:
        self.rng = random.Random(self.seed)
        self.reset()

    # estado: ¿cuántas veces cabe b en a? (1, 2, 3+) y ¿cabe exacto?
    def state(self):
        q = self.a // self.b
        return (min(q, 3), self.a % self.b == 0)

    def reset(self):
        self.a = self.rng.randint(8, 90)
        self.b = self.rng.randint(3, self.a)
        if self.a == self.b:
            self.b -= 1
        self.a0, self.b0 = self.a, self.b
        self.n = 0
        self.history = [(self.a, self.b)]
        self.last = ""
        return self.state()

    def _normalize(self) -> None:
        if self.a < self.b:
            self.a, self.b = self.b, self.a

    def step(self, action: int):
        self.n += 1
        if action == DECLARE:
            if self.a % self.b == 0:
                self.last = "ok"
                return self.state(), -1.0 + 20.0, True, "ok"
            self.last = "falso"
            return self.state(), -1.0 - 10.0, True, "falso"
        if action == ONE:
            self.a -= self.b
            if self.a == 0:  # b cabía exactamente: queda (b, b)
                self.a = self.b
        else:
            self.a %= self.b
            if self.a == 0:   # quitó todo: b mide a a exactamente; queda (b, b)
                self.a = self.b
        self._normalize()
        self.history.append((self.a, self.b))
        self.last = "resta"
        if self.n >= 40:
            return self.state(), -1.0, True, "timeout"
        return self.state(), -1.0, False, "step"

    def optimal_steps(self) -> int | None:
        a, b = self.a0, self.b0
        n = 0
        while a % b != 0:
            a, b = b, a % b
            n += 1
        return n + 1  # +1 por la declaración

    def gcd(self) -> int:
        return math.gcd(self.a0, self.b0)

    def headline(self) -> str:
        st = {"ok": "[bold green]✔ medida común[/]", "falso": "[bold red]✘ declaró en falso[/]",
              "resta": "[cyan]… midiendo[/]", "": ""}[self.last]
        return (f"[bold]a = {self.a0}, b = {self.b0}[/]   mcd real = {self.gcd()}   "
                f"paso {self.n:>2}   ahora ({self.a}, {self.b})   {st}")

    def render(self, width: int, height: int):
        r = Raster(width, height)
        scale = (width - 12) / self.a0
        rows = min(len(self.history), max(1, height // 2))
        hist = self.history[-rows:]
        y = 0
        for i, (a, b) in enumerate(hist):
            last = i == len(hist) - 1
            la, lb = max(1, round(a * scale)), max(1, round(b * scale))
            r.text(0, y, f"{a:>3}", "dim")
            for x in range(la):
                r.put(4 + x, y, "█", "bold yellow" if last else "dark_orange")
            r.text(0, y + 1, f"{b:>3}", "dim")
            for x in range(lb):
                r.put(4 + x, y + 1, "█", "bold cyan" if last else "steel_blue")
            # marcas de "cuántas veces cabe b en a"
            if b > 0:
                k = 1
                while k * b < a and 4 + round(k * b * scale) < width:
                    r.put(4 + round(k * b * scale), y, "┃", "bold white")
                    k += 1
            y += 2
            if y >= height:
                break
        return r.to_text()

    def snapshot(self) -> dict:
        return {"a0": self.a0, "b0": self.b0, "history": self.history[-12:], "last": self.last, "gcd": self.gcd(), "n": self.n}

    def policy_rows(self, agent) -> list[dict]:
        labels = {1: "cabe 1 vez", 2: "cabe 2 veces", 3: "cabe 3+ veces"}
        rows = []
        for exact in (True, False):
            for q in (1, 2, 3):
                s = (q, exact)
                if s not in agent.q:
                    continue
                row = agent.q[s]
                a = max(range(3), key=row.__getitem__)
                rows.append({"estado": f"{labels[q]}, {'exacto' if exact else 'sobra'}", "accion": self.action_names[a],
                             "ok": a == (DECLARE if exact else ALL), "q": [round(v, 2) for v in row]})
        return rows

    def policy_summary(self, agent, width: int):
        t = Text(no_wrap=True, overflow="ellipsis")
        t.append("regla aprendida (estado → acción con mayor Q):\n", style="dim")
        labels = {1: "cabe 1 vez", 2: "cabe 2 veces", 3: "cabe 3+ veces"}
        for exact in (True, False):
            for q in (1, 2, 3):
                s = (q, exact)
                if s not in agent.q:
                    continue
                row = agent.q[s]
                a = max(range(3), key=row.__getitem__)
                correct = DECLARE if exact else ALL
                ok = a == correct
                t.append(f"  {labels[q]:<14}{'exacto  ' if exact else 'sobra   '}→ ", style="")
                t.append(f"{self.action_names[a]:<26}", style="green" if ok else "red")
                t.append("✔\n" if ok else "✘\n", style="green" if ok else "red")
                t.append("     Q = " + "  ".join(f"{v:+.1f}" for v in row) + "\n", style="dim")
        return t

    def milestones(self, tr) -> list[str]:
        out = []
        ag = tr.agent1
        good = 0
        for exact in (True, False):
            for q in (1, 2, 3):
                s = (q, exact)
                if s in ag.q:
                    a = max(range(3), key=ag.q[s].__getitem__)
                    good += a == (DECLARE if exact else ALL)
        if good == 6 and tr.ep1 > 50:
            out.append("regla completa: si b mide exacto, declarar; si sobra, quedarse con el residuo. ESTO es el algoritmo de Euclides")
        if len(tr.ratio_curve) >= 100:
            recent = [v for v in tr.ratio_curve[-100:] if v > 0]
            if len(recent) >= 90 and sum(recent) / len(recent) < 1.02:
                out.append("mide con el mínimo de pasos posible en el 90 % de los casos")
        return out


THEOREM = ("Sean a ≥ b enteros positivos. El proceso a ← a mod b (intercambiando cuando haga falta) "
           "termina, y el último resto no nulo d divide a a y a b y es el mayor entero con esa propiedad.")

STEPS = [
    Step("H1", "Hipótesis", "a y b son enteros positivos con a ≥ b."),
    Step("DEF", "Definición", "r₀ = a, r₁ = b, y rₖ₊₁ = rₖ₋₁ mod rₖ mientras rₖ ≠ 0.", ("H1",)),
    Step("DEC", "Decrecimiento", "0 ≤ rₖ₊₁ < rₖ: los residuos son enteros no negativos estrictamente decrecientes.", ("DEF",)),
    Step("TERM", "Terminación", "Una sucesión estrictamente decreciente de enteros ≥ 0 es finita: existe n con rₙ₊₁ = 0. Sea d = rₙ.", ("DEC",)),
    Step("LIN", "Relación lineal", "rₖ₋₁ = qₖ·rₖ + rₖ₊₁ para algún entero qₖ (definición de resto).", ("DEF",)),
    Step("DIVA", "d divide hacia atrás", "d | rₙ y d | rₙ₊₁ = 0; por LIN e inducción descendente, d | rₖ para todo k. En particular d | a y d | b.", ("TERM", "LIN")),
    Step("DIVC", "Todo divisor común baja", "Si c | a y c | b, por LIN e inducción c | rₖ para todo k; luego c | d.", ("H1", "LIN", "TERM")),
    Step("MAX", "Maximalidad", "c | d con d > 0 implica c ≤ d: d es el mayor divisor común.", ("DIVC",)),
    Step("QED", "Conclusión", "El proceso termina y d = mcd(a, b). ∎", ("DIVA", "MAX"), is_qed=True),
    # distractores
    Step("D_COP", "Distractor", "a y b son coprimos, luego d = 1.", distractor=True),
    Step("D_PRIMO", "Distractor", "d es primo.", distractor=True),
    Step("D_IRR", "Distractor", "√2 es irracional, luego el proceso no termina.", distractor=True),
    Step("D_MIN", "Distractor", "Tomemos el menor divisor común de a y b.", distractor=True),
    Step("D_BOLZ", "Non sequitur", "Por Bolzano existe una raíz, luego el algoritmo converge.", distractor=True),
    Step("D_INF", "Distractor", "Como hay infinitos enteros, el proceso puede seguir indefinidamente.", distractor=True),
]

EPISODIO = Episodio(
    slug="euclides",
    titulo="Euclides · medir un segmento con otro (Elementos VII.1–2)",
    subtitulo="el agente redescubre la antifairesis: quedarse con el residuo hasta que uno mida al otro",
    fase1_titulo="Fase 1 · aprendiendo a medir (antifairesis)",
    fase2_titulo="Fase 2 · demostrando que el proceso termina y da la mayor medida común",
    kb=ProofKB(THEOREM, STEPS),
    make_phase1=lambda seed: EuclidEnv(seed=seed),
    episodes1=2000,
    episodes2=3000,
    agent1_kwargs=dict(gamma=0.95, eps_decay=0.996, eps_end=0.05, ucb_c=0.8),
    lectura=("El agente nunca vio la palabra 'residuo'. Con −1 por paso descubrió que quitar b una sola vez "
             "es un desperdicio y que quitar todas las que quepan llega antes: la división con resto emerge "
             "de la economía de pasos. Y descubrió cuándo parar: cuando b mide exacto. La fase 2 ordena la "
             "prueba de que ese proceso termina (buen orden) y que lo que queda es la mayor medida común. "
             "Miren que el paso más profundo es MAX, y que el distractor D_INF ('hay infinitos enteros, puede "
             "seguir') es exactamente lo que el buen orden refuta."),
)
