"""La cuadratura: del rectángulo (Elementos II.14) al círculo (imposible, 1882).

Fase 1. Se alternan dos tareas. Al agente se le dan longitudes ya trazadas
(la unidad y los lados de la figura) y puede hacer con regla y compás lo que
Euclides permite: sumar, restar, multiplicar y dividir longitudes (por
semejanza) y sacar medias geométricas (VI.13). Debe producir un segmento x tal
que el cuadrado de lado x tenga el área de la figura dada.

  * rectángulo a × b  → x = √(ab): dos pasos (media geométrica, declarar);
  * círculo de radio r → x = r√π: NUNCA se puede. El agente sólo consigue
    aproximaciones cada vez mejores; el marcador de "mejor error" baja y baja
    pero no llega a cero.

Fase 2. Ordenar la demostración moderna de la imposibilidad. Ojo al paso
LIND (π es trascendente, Lindemann 1882): es un teorema que aquí NO se
demuestra; el verificador lo admite como cita externa y lo pinta en ámbar.
Y al distractor D_IRR: "π es irracional, luego no se puede": insuficiente,
√2 también es irracional y se construye con un cuadrado de lado 1.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from rich.text import Text

from ..core import Episodio, ProofKB, Raster, Step

OPS = ["x·y (semejanza)", "x / y (semejanza)", "x + y", "|x − y|", "√x (media con 1)", "√(x·y) (media geom.)", "declarar: lado x"]
MUL, DIV, ADD, SUB, SQRT, GEOM, DECLARE = range(7)
MAX_STEPS = 8


@dataclass
class QuadEnv:
    seed: int = 0
    n_actions: int = 7
    action_names: list[str] = field(default_factory=lambda: list(OPS))
    rng: random.Random = field(init=False)
    task: str = "rect"
    a: float = 1.0
    b: float = 1.0
    area: float = 1.0
    S: list[float] = field(default_factory=list)
    n: int = 0
    last: str = ""
    best_err_circle: float = 1.0
    best_x_circle: float = 0.0
    circle_tries: int = 0
    rect_ok: int = 0

    def __post_init__(self) -> None:
        self.rng = random.Random(self.seed)
        self.reset()

    def reset(self):
        self.task = "rect" if self.rng.random() < 0.5 else "circ"
        if self.task == "rect":
            self.a, self.b = self.rng.randint(1, 6), self.rng.randint(1, 6)
            self.area = self.a * self.b
            self.S = [1.0, float(self.a), float(self.b)]
        else:
            self.a = self.rng.randint(1, 4)
            self.b = 0.0
            self.area = math.pi * self.a * self.a
            self.S = [1.0, float(self.a)]
            self.circle_tries += 1
        self.n = 0
        self.last = ""
        return self.state()

    def rel_err(self) -> float:
        x = self.S[-1]
        return abs(x * x - self.area) / self.area

    def _bucket(self) -> int:
        e = self.rel_err()
        if e < 1e-9:
            return 0
        return min(6, 1 + max(0, int(-math.log10(max(e, 1e-12)))))

    def state(self):
        return (self.task, min(self.n, MAX_STEPS), self._bucket())

    def step(self, action: int):
        self.n += 1
        x = self.S[-1]
        y = self.S[-2] if len(self.S) >= 2 else 1.0
        if action == DECLARE:
            if self.rel_err() < 1e-9:
                self.last = "ok"
                if self.task == "rect":
                    self.rect_ok += 1
                return self.state(), -1.0 + 20.0, True, "ok"
            self.last = "falso"
            return self.state(), -1.0 - 10.0, True, ("imposible" if self.task == "circ" else "falso")
        if action == MUL:
            z = x * y
        elif action == DIV:
            z = x / y if y > 1e-9 else x
        elif action == ADD:
            z = x + y
        elif action == SUB:
            z = abs(x - y) or x
        elif action == SQRT:
            z = math.sqrt(x)
        else:
            z = math.sqrt(x * y)
        z = min(max(z, 1e-6), 1e6)
        self.S.append(z)
        self.last = "traza"
        if self.task == "circ":
            e = self.rel_err()
            if e < self.best_err_circle:
                self.best_err_circle, self.best_x_circle = e, z
        if self.n >= MAX_STEPS:
            return self.state(), -1.0, True, ("imposible" if self.task == "circ" else "timeout")
        return self.state(), -1.0, False, "step"

    def optimal_steps(self) -> int | None:
        return 2 if self.task == "rect" else None

    def headline(self) -> str:
        fig = f"rectángulo {self.a}×{self.b}" if self.task == "rect" else f"círculo de radio {self.a}"
        st = {"ok": "[bold green]✔ cuadrado[/]", "falso": "[bold red]✘ declaró en falso[/]",
              "traza": "[cyan]… trazando[/]", "": ""}[self.last]
        return (f"[bold]{fig}[/]   área = {self.area:.4f}   lado buscado = {math.sqrt(self.area):.6f}   "
                f"paso {self.n}   {st}")

    def render(self, width: int, height: int):
        r = Raster(width, height)
        half = width // 2 - 2
        # figura dada (izquierda)
        scale = min(half - 4, height - 3) / 7.0
        if self.task == "rect":
            w, h = max(1, round(self.a * scale * 2)), max(1, round(self.b * scale))
            for yy in range(h):
                for xx in range(w):
                    r.put(2 + xx, 1 + yy, "▒", "dark_orange")
            r.text(2, 0, f"área {self.area:g}", "dim")
        else:
            rr = self.a * scale
            r.circle(2 + rr * 2 + 1, 1 + rr, rr * 2, rr, "●", "dark_orange")
            r.text(2, 0, f"área πr² = {self.area:.3f}", "dim")
        # cuadrado construido (derecha)
        x = self.S[-1]
        side = min(6.9, x)
        w, h = max(1, round(side * scale * 2)), max(1, round(side * scale))
        ok = self.rel_err() < 1e-9
        for yy in range(h):
            for xx in range(w):
                r.put(half + 4 + xx, 1 + yy, "█", "green" if ok else "steel_blue")
        r.text(half + 4, 0, f"x = {x:.5f}  x² = {x * x:.3f}  err {self.rel_err():.1e}", "dim")
        # longitudes trazadas
        y = height - 2
        r.text(0, y, "trazadas: " + "  ".join(f"{v:.4g}" for v in self.S[-8:]), "dim")
        if self.task == "circ":
            r.text(0, y + 1, f"mejor círculo hasta hoy: x = {self.best_x_circle:.6f}  "
                             f"err {self.best_err_circle:.1e}  (nunca 0)", "bold yellow")
        else:
            r.text(0, y + 1, f"rectángulos cuadrados hasta ahora: {self.rect_ok}", "green")
        return r.to_text()

    def snapshot(self) -> dict:
        return {"task": self.task, "a": self.a, "b": self.b, "area": self.area, "S": [round(v, 6) for v in self.S[-10:]],
                "x": self.S[-1], "err": self.rel_err(), "best_err": self.best_err_circle, "best_x": self.best_x_circle,
                "rect_ok": self.rect_ok, "circle_tries": self.circle_tries, "last": self.last, "n": self.n}

    def policy_rows(self, agent) -> list[dict]:
        rows = []
        for task, label in (("rect", "rectángulo, 1er paso"), ("circ", "círculo, 1er paso")):
            qs = [(k, v) for k, v in agent.q.items() if k[0] == task and k[1] == 0]
            if not qs:
                continue
            q = [sum(v[i] for _, v in qs) / len(qs) for i in range(7)]
            a = max(range(7), key=q.__getitem__)
            rows.append({"estado": label, "accion": OPS[a], "ok": (task == "rect" and a == GEOM) or task == "circ",
                         "q": [round(v, 2) for v in q]})
        return rows

    def policy_summary(self, agent, width: int):
        t = Text(no_wrap=True, overflow="ellipsis")
        for task, label in (("rect", "rectángulo"), ("circ", "círculo")):
            t.append(f"{label}: acción preferida en el primer paso →  ", style="dim")
            s = (task, 0, None)
            rows = [(k, v) for k, v in agent.q.items() if k[0] == task and k[1] == 0]
            if rows:
                q = [sum(v[i] for _, v in rows) / len(rows) for i in range(7)]
                a = max(range(7), key=q.__getitem__)
                t.append(f"{OPS[a]}\n", style="green" if (task == "rect" and a == GEOM) else "cyan")
                t.append("   Q̄ = " + "  ".join(f"{v:+.1f}" for v in q) + "\n", style="dim")
            else:
                t.append("—\n")
        t.append("\n√(x·y) es la media geométrica (VI.13).\n", style="dim")
        t.append("Con x = a, y = b: el cuadrado de lado √(ab)\n", style="dim")
        t.append("tiene el área del rectángulo: eso es II.14.\n", style="dim")
        t.append("Para el círculo no hay secuencia que llegue.", style="dim")
        return t

    def milestones(self, tr) -> list[str]:
        out = []
        ag = tr.agent1
        rows = [(k, v) for k, v in ag.q.items() if k[0] == "rect" and k[1] == 0]
        if rows and tr.ep1 > 100:
            q = [sum(v[i] for _, v in rows) / len(rows) for i in range(7)]
            if max(range(7), key=q.__getitem__) == GEOM:
                out.append("para el rectángulo prefiere la media geométrica: redescubrió Elementos II.14")
        for thr in (1e-1, 1e-2, 1e-3, 1e-4):
            if self.best_err_circle < thr:
                out.append(f"círculo: ya se acerca a menos de {thr:g} del área, y no va a llegar (x = {self.best_x_circle:.5f})")
        if tr.ep1 == tr.ep.episodes1:
            out.append(f"círculo: lo mejor en {tr.ep1} generaciones quedó a {self.best_err_circle:.1e} del área. Nunca 0.")
        if self.circle_tries >= 500 and tr.ep1 > 500:
            out.append("500 círculos intentados, cero cuadrados. Como 2 200 años de geómetras.")
        return out


THEOREM = ("No existe una construcción con regla y compás que, dado un círculo, produzca un cuadrado "
           "de igual área.")

STEPS = [
    Step("H1", "Hipótesis", "Regla y compás: se parte de segmentos dados y se trazan rectas por dos puntos y círculos con centro y radio dados."),
    Step("INT", "Intersecciones", "Cada punto nuevo es intersección recta-recta, recta-círculo o círculo-círculo: resuelve una ecuación de grado ≤ 2 con coeficientes en el cuerpo de las coordenadas ya construidas.", ("H1",)),
    Step("TOR", "Torre", "Las coordenadas de cualquier punto construido viven en una torre ℚ = K₀ ⊂ K₁ ⊂ … ⊂ Kₘ con [Kᵢ₊₁ : Kᵢ] ∈ {1, 2}.", ("INT",)),
    Step("DEG", "Grado", "Toda longitud construible es algebraica sobre ℚ y su grado divide a 2ᵐ (multiplicatividad del grado).", ("TOR",)),
    Step("RED", "Reducción", "Cuadrar el círculo unidad es construir un segmento de longitud √π; entonces √π, y por tanto π = (√π)², sería algebraica.", ("H1",)),
    Step("LIND", "Cita externa", "π es trascendente (Lindemann, 1882). No se demuestra aquí.", externo=True),
    Step("QED", "Conclusión", "π no es algebraica, luego √π no es construible: el círculo no se puede cuadrar. ∎", ("DEG", "RED", "LIND"), is_qed=True),
    # distractores
    Step("D_IRR", "Distractor", "π es irracional, luego √π no es construible.  (√2 también es irracional y se construye.)", distractor=True),
    Step("D_APROX", "Distractor", "El círculo se aproxima por polígonos, luego se cuadra en el límite.", distractor=True),
    Step("D_ARQ", "Distractor", "Arquímedes: π ≈ 22/7, que es construible; luego el círculo se cuadra.", distractor=True),
    Step("D_HIP", "Distractor", "Hipócrates cuadró la lúnula, luego también el círculo.", distractor=True),
    Step("D_GRADO3", "Distractor", "El grado de π sobre ℚ es 3.", distractor=True),
    Step("D_BOLZ", "Non sequitur", "Por Bolzano existe una raíz, luego el método converge.", distractor=True),
]

EPISODIO = Episodio(
    slug="cuadratura",
    titulo="Euclides → Lindemann · cuadrar el rectángulo y no poder cuadrar el círculo",
    subtitulo="el mismo agente, las mismas herramientas: II.14 sale en dos pasos; el círculo, nunca",
    fase1_titulo="Fase 1 · cuadrando con regla y compás",
    fase2_titulo="Fase 2 · demostrando que el círculo NO se puede cuadrar",
    kb=ProofKB(THEOREM, STEPS),
    make_phase1=lambda seed: QuadEnv(seed=seed),
    episodes1=2500,
    episodes2=3000,
    agent1_kwargs=dict(gamma=0.9, eps_decay=0.997, eps_end=0.1, ucb_c=0.8),
    lectura=("Fase 1: con el rectángulo, la media geométrica y a declarar; con el círculo, el 'mejor error' "
             "baja y baja y nunca toca cero. Eso NO demuestra nada: que un agente no encuentre algo no es "
             "una prueba de imposibilidad, igual que 2 200 años de fracasos no lo eran. La fase 2 sí lo "
             "demuestra, pero apoyándose en un paso ámbar: la trascendencia de π, que no se prueba aquí. "
             "Galois y Gödel están en la misma familia: el teorema fuerte es el que dice 'no se puede'."),
)
