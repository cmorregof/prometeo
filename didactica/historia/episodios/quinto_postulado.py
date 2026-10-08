"""El quinto postulado: 2 200 años de intentos y un disco que los deshace.

Fase 1. El agente cae en un mundo que no conoce: unas veces el plano de
Euclides, otras el disco de Klein (la geometría hiperbólica dibujada dentro
de un círculo: las "rectas" son cuerdas). Hay una recta L y un punto P fuera
de ella. Acciones: trazar por P una recta con uno de 9 ángulos, o declarar
"por P pasa UNA sola paralela" / "por P pasan INFINITAS paralelas".
Recompensa: −1 por trazo, +20 si declara bien, −10 si declara mal.
Lo que aprende: trazar unas pocas, contar cuántas no cortan a L, y declarar.
En el plano sólo una no corta; en el disco, varias.

Fase 2. Intentar demostrar el V postulado a partir de I–IV, como Proclo,
Wallis, Saccheri, Lambert y Legendre. El grafo está armado como estaba la
historia: la conclusión necesita un paso "puente" y TODOS los puentes son
postulados equivalentes al V (ámbar). El agente puede llegar a ∎, pero sólo
apoyándose en un paso ámbar. No hay demostración limpia. Ese es el teorema
de Beltrami (1868) contado en colores.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from rich.text import Text

from ..core import Episodio, ProofKB, Raster, Step

ANGLES = [-60, -40, -20, -8, 0, 8, 20, 40, 60]   # grados respecto de L
DECL_ONE, DECL_MANY = 9, 10
MAX_DRAWS = 9


def _chord(px: float, py: float, theta: float) -> tuple[tuple[float, float], tuple[float, float]]:
    """Cuerda del disco unidad por (px,py) con ángulo theta."""
    dx, dy = math.cos(theta), math.sin(theta)
    # |p + t d|² = 1
    b = 2 * (px * dx + py * dy)
    c = px * px + py * py - 1
    disc = math.sqrt(max(0.0, b * b - 4 * c))
    t1, t2 = (-b - disc) / 2, (-b + disc) / 2
    return (px + t1 * dx, py + t1 * dy), (px + t2 * dx, py + t2 * dy)


def _seg_intersect(a, b, c, d) -> bool:
    def orient(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    o1, o2, o3, o4 = orient(a, b, c), orient(a, b, d), orient(c, d, a), orient(c, d, b)
    return (o1 * o2 < 0) and (o3 * o4 < 0)


@dataclass
class ParallelEnv:
    seed: int = 0
    n_actions: int = 11
    action_names: list[str] = field(default_factory=lambda: [f"trazar a {a:+d}°" for a in ANGLES] + ["declarar: UNA paralela", "declarar: INFINITAS paralelas"])
    rng: random.Random = field(init=False)
    world: str = "plano"
    px: float = 0.0
    py: float = 0.45
    L: tuple = ((-1, 0), (1, 0))
    drawn: list[tuple[float, bool]] = field(default_factory=list)  # (ángulo, ¿corta a L?)
    n: int = 0
    last: str = ""
    ok_by_world: dict = field(default_factory=lambda: {"plano": 0, "disco": 0})

    def __post_init__(self) -> None:
        self.rng = random.Random(self.seed)
        self.reset()

    def reset(self):
        self.world = "plano" if self.rng.random() < 0.5 else "disco"
        self.py = self.rng.uniform(0.3, 0.6) if self.world == "disco" else 0.45
        self.px = self.rng.uniform(-0.2, 0.2) if self.world == "disco" else 0.0
        self.L = ((-1.0, 0.0), (1.0, 0.0))
        self.drawn = []
        self.n = 0
        self.last = ""
        return self.state()

    def parallels(self) -> int:
        return sum(1 for _, cut in self.drawn if not cut)

    def state(self):
        return (min(len(self.drawn), 4), min(self.parallels(), 3))

    def _cuts(self, theta_deg: float) -> bool:
        th = math.radians(theta_deg)
        if self.world == "plano":
            return abs(theta_deg) > 1e-9   # sólo la horizontal no corta (L es horizontal, infinita)
        a, b = _chord(self.px, self.py, th)
        return _seg_intersect(a, b, self.L[0], self.L[1])

    def step(self, action: int):
        self.n += 1
        if action >= DECL_ONE:
            correct = (self.world == "plano" and action == DECL_ONE) or (self.world == "disco" and action == DECL_MANY)
            evidence = len(self.drawn) >= 2
            if correct and evidence:
                self.last = "ok"
                self.ok_by_world[self.world] += 1
                return self.state(), -1.0 + 20.0, True, "ok"
            self.last = "falso" if not correct else "adivinó"
            return self.state(), -1.0 - 10.0, True, "falso"
        ang = ANGLES[action]
        if any(abs(a - ang) < 1e-9 for a, _ in self.drawn):
            return self.state(), -2.0, False, "repite"
        self.drawn.append((ang, self._cuts(ang)))
        self.last = "traza"
        if len(self.drawn) >= MAX_DRAWS:
            return self.state(), -1.0, True, "timeout"
        return self.state(), -1.0, False, "step"

    def optimal_steps(self) -> int | None:
        return 3  # dos trazos con evidencia + declarar

    def headline(self) -> str:
        st = {"ok": "[bold green]✔ declaró bien[/]", "falso": "[bold red]✘ declaró mal[/]",
              "adivinó": "[bold red]✘ declaró sin evidencia[/]", "traza": "[cyan]… trazando[/]", "": ""}[self.last]
        return (f"mundo oculto: [bold]{self.world}[/]   trazos {len(self.drawn)}   "
                f"no cortan a L: [bold]{self.parallels()}[/]   {st}")

    def render(self, width: int, height: int):
        r = Raster(width, height)
        cx, cy = width / 2, height / 2
        # los caracteres son ~2.1 veces más altos que anchos
        sy = min(height / 2 - 1.5, (width / 2 - 2) / 2.1)
        sx = sy * 2.1

        def to_scr(x, y):
            return cx + x * sx, cy - y * sy

        if self.world == "disco":
            r.circle(cx, cy, sx, sy, "·", "grey62")
        else:
            for x in range(width):
                r.put(x, 0, "─", "grey30"); r.put(x, height - 1, "─", "grey30")
        # recta L
        (x0, y0), (x1, y1) = self.L
        if self.world == "plano":
            x0, x1 = -1.4, 1.4
        a, b = to_scr(x0, y0), to_scr(x1, y1)
        r.line(a[0], a[1], b[0], b[1], "═", "bold white")
        # trazos
        for i, (ang, cut) in enumerate(self.drawn):
            th = math.radians(ang)
            if self.world == "disco":
                p, q = _chord(self.px, self.py, th)
            else:
                dx, dy = math.cos(th), math.sin(th)
                t = 1.6
                p, q = (self.px - t * dx, self.py - t * dy), (self.px + t * dx, self.py + t * dy)
            a, b = to_scr(*p), to_scr(*q)
            last = i == len(self.drawn) - 1
            r.line(a[0], a[1], b[0], b[1], "•" if cut else "●", ("bold " if last else "") + ("red" if cut else "green"))
        # punto P
        p = to_scr(self.px, self.py)
        r.put(round(p[0]), round(p[1]), "◆", "bold magenta")
        r.text(0, 1 if self.world == "plano" else 0, f"{'plano euclidiano' if self.world == 'plano' else 'disco de Klein'}", "dim")
        r.text(0, height - 2 if self.world == "plano" else height - 1, "● no corta a L   • corta a L", "dim")
        return r.to_text()

    def snapshot(self) -> dict:
        chords = []
        for ang, cut in self.drawn:
            th = math.radians(ang)
            if self.world == "disco":
                p, q = _chord(self.px, self.py, th)
            else:
                dx, dy = math.cos(th), math.sin(th)
                p, q = (self.px - 1.6 * dx, self.py - 1.6 * dy), (self.px + 1.6 * dx, self.py + 1.6 * dy)
            chords.append({"ang": ang, "cut": cut, "p": [round(p[0], 4), round(p[1], 4)], "q": [round(q[0], 4), round(q[1], 4)]})
        return {"world": self.world, "px": round(self.px, 4), "py": round(self.py, 4), "chords": chords,
                "parallels": self.parallels(), "last": self.last, "n": self.n}

    def policy_rows(self, agent) -> list[dict]:
        rows = []
        for drawn in range(2, 5):
            for par in range(0, 4):
                s = (drawn, par)
                if s not in agent.q or all(v == 0 for v in agent.q[s]):
                    continue
                a = max(range(11), key=agent.q[s].__getitem__)
                ok = (a == DECL_ONE and par == 1 and drawn >= 2) or (a == DECL_MANY and par >= 2) or a < 9
                rows.append({"estado": f"{drawn} trazos, {par} no cortan", "accion": self.action_names[a], "ok": ok,
                             "q": [round(agent.q[s][a], 2)]})
        return rows

    def policy_summary(self, agent, width: int):
        t = Text(no_wrap=True, overflow="ellipsis")
        t.append("tras 2+ trazos: (trazos, no cortan) → acción con mayor Q\n", style="dim")
        for drawn in range(2, 5):
            for par in range(0, 4):
                s = (drawn, par)
                if s not in agent.q or all(v == 0 for v in agent.q[s]):
                    continue
                a = max(range(11), key=agent.q[s].__getitem__)
                name = self.action_names[a]
                style = "green" if (a == DECL_ONE and par == 1 and drawn >= 2) or (a == DECL_MANY and par >= 2) else ("cyan" if a < 9 else "red")
                t.append(f"  {drawn} trazos, {par} paralelas → ", style="")
                t.append(f"{name}\n", style=style)
        return t

    def milestones(self, tr) -> list[str]:
        out = []
        ag = tr.agent1
        s_many = (2, 2)
        s_one = (2, 1)
        if s_many in ag.q and max(range(11), key=ag.q[s_many].__getitem__) == DECL_MANY and tr.ep1 > 100:
            out.append("con dos rectas que no cortan ya declara INFINITAS paralelas: distingue el disco (Lobachevski, Bolyai)")
        if s_one in ag.q and max(range(11), key=ag.q[s_one].__getitem__) == DECL_ONE and tr.ep1 > 100:
            out.append("con varios trazos y una sola que no corta declara UNA paralela: reconoce el plano de Euclides")
        if self.ok_by_world["disco"] >= 200 and self.ok_by_world["plano"] >= 200:
            out.append("200 aciertos en cada mundo: los dos son consistentes con lo que se ve desde dentro")
        return out


THEOREM = ("Intento histórico: el quinto postulado (por un punto exterior a una recta pasa exactamente una "
           "paralela) se deduce de los postulados I–IV.")

STEPS = [
    Step("P1", "Postulado I", "Por dos puntos pasa una recta.", externo=True),
    Step("P2", "Postulado II", "Toda recta se prolonga indefinidamente.", externo=True),
    Step("P3", "Postulado III", "Con cualquier centro y radio hay un círculo.", externo=True),
    Step("P4", "Postulado IV", "Todos los ángulos rectos son iguales.", externo=True),
    Step("I16", "Ángulo exterior (I.16)", "El ángulo exterior de un triángulo es mayor que cada interior no adyacente. Usa I.10 (bisecar), que usa I.1 (círculos, P3).", ("P1", "P2", "P3")),
    Step("I27", "Existe una paralela (I.27–31)", "Si los alternos internos son iguales, las rectas no se cortan: por P pasa AL MENOS una paralela.", ("I16",)),
    Step("SACC", "Saccheri (1733)", "En el cuadrilátero birrectángulo isósceles los ángulos superiores son iguales, y son rectos, obtusos o agudos.", ("P4", "I16")),
    Step("OBT", "Se descarta el obtuso", "La hipótesis del ángulo obtuso contradice I.16 (con P2).", ("SACC", "P2")),
    Step("PUENTE", "Postulado equivalente", "Se admite UNA de estas: Proclo (paralelas a distancia acotada), Wallis (hay triángulos semejantes no congruentes), Playfair (a lo sumo una paralela), Legendre (suma de ángulos = 180°). Cada una equivale al V.", externo=True),
    Step("AGU", "Se descarta el agudo", "Con el PUENTE, la hipótesis del ángulo agudo lleva a contradicción.", ("OBT", "PUENTE")),
    Step("UNICA", "Unicidad", "Queda el ángulo recto: por P pasa A LO SUMO una paralela.", ("AGU",)),
    Step("QED", "Conclusión", "Existe y es única: el V postulado 'se sigue' de I–IV. ∎  (miren el ámbar)", ("I27", "UNICA"), is_qed=True),
    # distractores
    Step("D_REP", "Saccheri, el paso final", "La hipótesis del ángulo agudo es 'repugnante a la naturaleza de la línea recta', luego es falsa.", distractor=True),
    Step("D_KANT", "Distractor", "El espacio es euclidiano a priori (Kant), luego el V es necesario.", distractor=True),
    Step("D_EVID", "Distractor", "Euclides lo pone como postulado, luego es evidente y no hay que demostrarlo.", distractor=True),
    Step("D_FIS", "Distractor", "Gauss midió el triángulo Brocken–Hohehagen–Inselsberg y dio 180°, luego el V es verdadero.", distractor=True),
    Step("D_BOLZ", "Non sequitur", "Por Bolzano existe una raíz, luego el método converge.", distractor=True),
]

EPISODIO = Episodio(
    slug="quinto",
    titulo="El quinto postulado · de Euclides a Lobachevski",
    subtitulo="en el disco caben infinitas paralelas; y toda 'demostración' del V se apoya en un postulado ámbar",
    fase1_titulo="Fase 1 · ¿en qué mundo estoy? trazando paralelas por P",
    fase2_titulo="Fase 2 · intentando deducir el V postulado de I–IV",
    kb=ProofKB(THEOREM, STEPS),
    make_phase1=lambda seed: ParallelEnv(seed=seed),
    episodes1=2500,
    episodes2=3000,
    agent1_kwargs=dict(gamma=0.95, eps_decay=0.996, eps_end=0.05, ucb_c=0.8),
    agent2_kwargs=dict(gamma=0.97, eps_decay=0.997),
    lectura=("Fase 1: el agente aprende a reconocer desde dentro si está en el plano o en el disco, y en los dos "
             "acierta. Ninguno de los dos mundos lo expulsa: los dos son coherentes con lo que se ve. Fase 2: "
             "llega a ∎, pero fíjense en la demostración voraz: siempre pasa por PUENTE, en ámbar. Es Beltrami "
             "(1868): el V no se deduce de I–IV porque el disco satisface I–IV y viola el V. Dos mil años de "
             "'demostraciones' eran dos mil años de puentes. Saccheri tenía la geometría no euclidiana en las "
             "manos y la llamó repugnante: ese es el distractor D_REP."),
)
