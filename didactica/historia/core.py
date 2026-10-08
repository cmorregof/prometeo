"""Motor común de los episodios históricos.

Un *episodio* tiene dos fases, igual que BisectRL:

* **Fase 1 (hacer)**: un entorno procedimental donde el agente aprende un
  método (medir un segmento con otro, cuadrar una figura, trazar paralelas).
  Cada episodio dibuja su propio panel.
* **Fase 2 (demostrar)**: un grafo de lemas con dependencias y distractores.
  El agente aprende un orden topológico válido y a rechazar los distractores.

Novedad respecto de BisectRL: un paso puede ser un **postulado o cita externa**
(``externo=True``). Es válido sin dependencias, pero el verificador lo pinta en
ámbar y le cobra más caro: se puede usar, no se deriva. Sirve para mostrar
en pantalla cuándo una demostración *se apoya* en algo que no demuestra
(Lindemann para π, el axioma de infinitud en Russell, el quinto postulado).
"""

from __future__ import annotations

import math
import random
import time
from collections import Counter, deque
from dataclasses import dataclass, field
from typing import Any, Callable, Hashable, Iterator, Protocol

try:  # el Q-agent compartido del repo
    from ..qagent import QAgent  # type: ignore
except Exception:  # pragma: no cover - respaldo autocontenido

    class QAgent:  # type: ignore[no-redef]
        """Q-learning tabular con ε-greedy, tasa 1/N opcional y bono UCB."""

        def __init__(self, n_actions: int, alpha: float | None = 0.3, gamma: float = 0.97,
                     eps_start: float = 1.0, eps_decay: float = 0.997, eps_end: float = 0.02,
                     ucb_c: float = 1.0, seed: int = 0) -> None:
            self.n = n_actions
            self.alpha, self.gamma = alpha, gamma
            self.eps, self.eps_decay, self.eps_end = eps_start, eps_decay, eps_end
            self.ucb_c = ucb_c
            self.rng = random.Random(seed)
            self.q: dict[Hashable, list[float]] = {}
            self.nvis: dict[Hashable, list[int]] = {}
            self.updates = 0

        def _row(self, s: Hashable) -> list[float]:
            if s not in self.q:
                self.q[s] = [0.0] * self.n
                self.nvis[s] = [0] * self.n
            return self.q[s]

        def greedy(self, s: Hashable) -> int:
            q = self._row(s)
            best = max(q)
            cands = [i for i, v in enumerate(q) if v == best]
            return cands[0] if len(cands) == 1 else self.rng.choice(cands)

        def act(self, s: Hashable) -> int:
            q = self._row(s)
            if self.rng.random() < self.eps:
                return self.rng.randrange(self.n)
            n = self.nvis[s]
            tot = sum(n) + 1
            score = [q[i] + self.ucb_c * math.sqrt(math.log(tot) / (n[i] + 1)) for i in range(self.n)]
            best = max(score)
            cands = [i for i, v in enumerate(score) if v == best]
            return self.rng.choice(cands)

        def learn(self, s: Hashable, a: int, r: float, s2: Hashable, done: bool) -> None:
            q = self._row(s)
            self.nvis[s][a] += 1
            target = r if done else r + self.gamma * max(self._row(s2))
            lr = self.alpha if self.alpha is not None else 1.0 / self.nvis[s][a]
            q[a] += lr * (target - q[a])
            self.updates += 1

        def decay(self) -> None:
            self.eps = max(self.eps_end, self.eps * self.eps_decay)


# ---------------------------------------------------------------------------
# Fase 2: base de conocimiento y verificador
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Step:
    key: str
    title: str
    text: str
    deps: tuple[str, ...] = field(default_factory=tuple)
    distractor: bool = False
    is_qed: bool = False
    externo: bool = False  # postulado / cita: válido, pero no derivado (ámbar)


class ProofKB:
    def __init__(self, theorem: str, steps: list[Step]) -> None:
        self.theorem = theorem
        self.steps = steps
        self.index = {s.key: i for i, s in enumerate(steps)}
        self.n = len(steps)
        self.deps_mask = [self._mask(s) for s in steps]
        qed = [s.key for s in steps if s.is_qed]
        self.qed_key = qed[0] if qed else None
        self.qed_index = self.index[self.qed_key] if self.qed_key else -1
        self.required: frozenset[str] = frozenset(self._closure(self.qed_key, set())) if self.qed_key else frozenset()
        self.min_len = len(self.required)
        self.core_keys = [s.key for s in steps if not s.distractor]

    def _mask(self, s: Step) -> int:
        m = 0
        for d in s.deps:
            m |= 1 << self.index[d]
        return m

    def _closure(self, key: str | None, acc: set[str]) -> set[str]:
        if key is None:
            return acc
        acc.add(key)
        for d in self.by_key(key).deps:
            self._closure(d, acc)
        return acc

    def by_key(self, key: str) -> Step:
        return self.steps[self.index[key]]

    def depth(self) -> dict[str, int]:
        memo: dict[str, int] = {}

        def d(k: str) -> int:
            if k not in memo:
                st = self.by_key(k)
                memo[k] = 0 if not st.deps else 1 + max(d(x) for x in st.deps)
            return memo[k]

        return {k: d(k) for k in self.required}


REWARD_VALID = -0.5
REWARD_EXTERNO = -3.0   # apoyarse en un postulado cuesta seis líneas
REWARD_INVALID = -2.0
REWARD_QED = 20.0


@dataclass
class ProofEnv:
    kb: ProofKB
    max_len: int = 30
    mask: int = field(init=False, default=0)
    attempts: list[tuple[int, bool]] = field(init=False, default_factory=list)

    def reset(self) -> int:
        self.mask = 0
        self.attempts = []
        return self.mask

    def is_valid(self, action: int, mask: int | None = None) -> bool:
        mask = self.mask if mask is None else mask
        st = self.kb.steps[action]
        if st.distractor or (mask >> action) & 1:
            return False
        return (self.kb.deps_mask[action] & mask) == self.kb.deps_mask[action]

    def step(self, action: int) -> tuple[int, float, bool, str]:
        ok = self.is_valid(action)
        self.attempts.append((action, ok))
        if not ok:
            return self.mask, REWARD_INVALID, len(self.attempts) >= self.max_len, "invalid"
        self.mask |= 1 << action
        st = self.kb.steps[action]
        if action == self.kb.qed_index:
            return self.mask, REWARD_VALID + REWARD_QED, True, "qed"
        r = REWARD_EXTERNO if st.externo else REWARD_VALID
        return self.mask, r, len(self.attempts) >= self.max_len, ("externo" if st.externo else "valid")

    @property
    def proof_keys(self) -> list[str]:
        return [self.kb.steps[a].key for a, ok in self.attempts if ok]

    @property
    def n_invalid(self) -> int:
        return sum(1 for _, ok in self.attempts if not ok)

    @property
    def finished(self) -> bool:
        return self.kb.qed_index >= 0 and (self.mask >> self.kb.qed_index) & 1 == 1


# ---------------------------------------------------------------------------
# Fase 1: protocolo que cumple cada entorno histórico
# ---------------------------------------------------------------------------
class Phase1(Protocol):
    n_actions: int
    action_names: list[str]

    def reset(self) -> Hashable: ...
    def step(self, action: int) -> tuple[Hashable, float, bool, str]: ...
    def render(self, width: int, height: int) -> Any: ...          # rich renderable del "tablero"
    def policy_summary(self, agent: QAgent, width: int) -> Any: ...  # rich renderable de lo aprendido
    def milestones(self, tr: "Trainer") -> list[str]: ...           # hitos nuevos detectados tras el episodio
    def headline(self) -> str: ...                                  # una línea: estado actual
    def optimal_steps(self) -> int | None: ...


@dataclass
class Episodio:
    """Todo lo que la interfaz necesita saber de una parada histórica."""
    slug: str
    titulo: str            # "Euclides · medir un segmento con otro"
    subtitulo: str         # qué aprende el agente, en una línea
    fase1_titulo: str
    fase2_titulo: str
    kb: ProofKB
    make_phase1: Callable[[int], Phase1] | None   # seed -> entorno; None si sólo hay fase 2
    episodes1: int = 2500
    episodes2: int = 3000
    agent1_kwargs: dict[str, Any] = field(default_factory=dict)
    agent2_kwargs: dict[str, Any] = field(default_factory=dict)
    lectura: str = ""      # párrafo final para el informe: qué significa lo que se vio


# ---------------------------------------------------------------------------
# Entrenador genérico
# ---------------------------------------------------------------------------
@dataclass
class Milestone:
    phase: int
    episode: int
    t: float
    text: str


@dataclass
class Trainer:
    ep: Episodio
    seed: int = 0
    t0: float = field(default_factory=time.perf_counter)
    phase: int = 1
    milestones: list[Milestone] = field(default_factory=list)
    log: list[str] = field(default_factory=list)

    env1: Any = field(init=False, default=None)
    agent1: Any = field(init=False, default=None)
    ep1: int = 0
    outcomes1: deque = field(default_factory=lambda: deque(maxlen=100))
    success_curve: list[float] = field(default_factory=list)
    ratio_curve: list[float] = field(default_factory=list)
    steps1_total: int = 0
    ok_total: int = 0
    fail_total: int = 0
    imposible_total: int = 0
    last_info1: str = ""
    last_action1: int = -1
    phase1_time: float = 0.0

    env2: ProofEnv = field(init=False)
    agent2: Any = field(init=False, default=None)
    ep2: int = 0
    rewards2: deque = field(default_factory=lambda: deque(maxlen=100))
    finished2: deque = field(default_factory=lambda: deque(maxlen=100))
    reward_curve: list[float] = field(default_factory=list)
    best_reward: float = float("-inf")
    best_proof: list[tuple[int, bool]] = field(default_factory=list)
    greedy_proof: list[tuple[int, bool]] = field(default_factory=list)
    first_valid: dict[str, int] = field(default_factory=dict)
    first_greedy: dict[str, int] = field(default_factory=dict)
    step_usage: Counter = field(default_factory=Counter)
    invalid_usage: Counter = field(default_factory=Counter)
    externo_usage: Counter = field(default_factory=Counter)
    qed_total: int = 0
    minimal_total: int = 0
    phase2_time: float = 0.0
    done: bool = False

    def __post_init__(self) -> None:
        kb = self.ep.kb
        if self.ep.make_phase1 is not None:
            self.env1 = self.ep.make_phase1(self.seed)
            kw = dict(alpha=None, gamma=0.9, eps_start=1.0, eps_decay=0.997, eps_end=0.05, ucb_c=0.5, seed=self.seed)
            kw.update(self.ep.agent1_kwargs)
            self.agent1 = QAgent(self.env1.n_actions, **kw)
        else:
            self.phase = 2
        self.env2 = ProofEnv(kb)
        kw2 = dict(alpha=0.3, gamma=0.97, eps_start=1.0, eps_decay=0.997, eps_end=0.02, ucb_c=1.0, seed=self.seed + 1)
        kw2.update(self.ep.agent2_kwargs)
        self.agent2 = QAgent(kb.n, **kw2)

    # ---- utilidades ------------------------------------------------------
    @property
    def elapsed(self) -> float:
        return time.perf_counter() - self.t0

    @property
    def has_phase1(self) -> bool:
        return self.env1 is not None

    def mark(self, text: str) -> None:
        ep = self.ep1 if self.phase == 1 else self.ep2
        self.milestones.append(Milestone(self.phase, ep, self.elapsed, text))
        self.log.append(f"[{self.elapsed:6.1f}s] F{self.phase} gen {ep:>5}: {text}")

    # ---- fase 1 ------------------------------------------------------------
    def run_phase1(self) -> Iterator[str]:
        env, ag = self.env1, self.agent1
        got_first = got_95 = False
        seen: set[str] = set()
        for ep in range(1, self.ep.episodes1 + 1):
            self.ep1 = ep
            s = env.reset()
            done = False
            n = 0
            info = ""
            while not done:
                a = ag.act(s)
                self.last_action1 = a
                s2, r, done, info = env.step(a)
                ag.learn(s, a, r, s2, done)
                s = s2
                n += 1
                self.last_info1 = info
                if ep <= 60 or ep % 50 == 0:
                    yield "iter"
            ag.decay()
            ok = info == "ok"
            self.steps1_total += n
            if info == "imposible":   # tarea sin solución: no cuenta ni como logro ni como fracaso
                self.imposible_total += 1
                self.ratio_curve.append(0.0)
                for text in env.milestones(self):
                    if text not in seen:
                        seen.add(text)
                        self.mark(text)
                yield "episode"
                continue
            self.outcomes1.append(ok)
            if ok:
                self.ok_total += 1
                opt = env.optimal_steps()
                self.ratio_curve.append(n / opt if opt else 0.0)
                if not got_first:
                    got_first = True
                    self.mark(f"primera vez que lo logra ({n} pasos)")
            else:
                self.fail_total += 1
                self.ratio_curve.append(0.0)
            self.success_curve.append(sum(self.outcomes1) / len(self.outcomes1))
            for text in env.milestones(self):
                if text not in seen:
                    seen.add(text)
                    self.mark(text)
            if not got_95 and len(self.outcomes1) == 100 and self.success_curve[-1] >= 0.95:
                got_95 = True
                self.mark("≥95 % de éxito en las últimas 100 generaciones")
            yield "episode"
        self.phase1_time = self.elapsed
        self.mark(f"fase 1 terminada: {self.ok_total} logros, {self.fail_total} fracasos")

    # ---- fase 2 ------------------------------------------------------------
    def greedy_rollout(self) -> list[tuple[int, bool]]:
        env = ProofEnv(self.ep.kb)
        s = env.reset()
        done = False
        while not done:
            a = self.agent2.greedy(s)
            s, _, done, _ = env.step(a)
        return list(env.attempts)

    def run_phase2(self) -> Iterator[str]:
        self.phase = 2
        kb, env, ag = self.ep.kb, self.env2, self.agent2
        got_valid = got_qed = got_clean = got_min = got_greedy = got_ext = got_qed_ext = False
        for ep in range(1, self.ep.episodes2 + 1):
            self.ep2 = ep
            s = env.reset()
            done = False
            total = 0.0
            while not done:
                a = ag.act(s)
                s2, r, done, info = env.step(a)
                ag.learn(s, a, r, s2, done)
                total += r
                s = s2
                st = kb.steps[a]
                if info == "invalid":
                    self.invalid_usage[st.key] += 1
                elif info == "externo":
                    self.externo_usage[st.key] += 1
                    if not got_ext:
                        got_ext = True
                        self.mark(f"se apoyó por primera vez en un postulado/cita: {st.key} ({st.title})")
                if info in ("valid", "externo", "qed") and st.key not in self.first_valid:
                    self.first_valid[st.key] = ep
                    if not got_valid:
                        got_valid = True
                        self.mark(f"primer paso válido: {st.title} ({st.key})")
                if ep <= 25 or ep % 100 == 0:
                    yield "iter2"
            ag.decay()
            self.rewards2.append(total)
            self.reward_curve.append(total)
            self.finished2.append(env.finished)
            if env.finished:
                self.qed_total += 1
                for k in env.proof_keys:
                    self.step_usage[k] += 1
                clean = env.n_invalid == 0
                minimal = clean and len(env.proof_keys) == kb.min_len
                if minimal:
                    self.minimal_total += 1
                ext_keys = [k for k in env.proof_keys if kb.by_key(k).externo]
                if not got_qed:
                    got_qed = True
                    self.mark(f"¡primera demostración completa! {len(env.proof_keys)} pasos, {env.n_invalid} saltos lógicos")
                if ext_keys and not got_qed_ext:
                    got_qed_ext = True
                    self.mark(f"llegó a ∎, pero apoyado en {len(ext_keys)} postulado(s)/cita(s): {', '.join(ext_keys)}")
                if clean and not got_clean:
                    got_clean = True
                    self.mark("primera demostración sin ningún salto lógico")
                if minimal and not got_min:
                    got_min = True
                    self.mark(f"primera demostración mínima ({kb.min_len} pasos, sin desvíos)")
            if total > self.best_reward:
                self.best_reward = total
                self.best_proof = list(env.attempts)
            if ep % 25 == 0 or ep <= 30:
                self.greedy_proof = self.greedy_rollout()
                g_keys = [kb.steps[a].key for a, ok in self.greedy_proof if ok]
                g_clean = all(ok for _, ok in self.greedy_proof)
                for k in g_keys:
                    self.first_greedy.setdefault(k, ep)
                if not got_greedy and g_clean and kb.qed_key in g_keys and len(g_keys) == kb.min_len:
                    got_greedy = True
                    self.mark("la política voraz (sin exploración) ya produce la demostración mínima")
            yield "episode"
        self.phase2_time = self.elapsed - self.phase1_time
        if kb.qed_key is None or self.qed_total == 0:
            self.mark("fase 2 terminada: NUNCA llegó a ∎ — el teorema no se deja demostrar con estos pasos")
        else:
            self.mark(f"fase 2 terminada: {self.qed_total} demostraciones completas, {self.minimal_total} mínimas")
        self.greedy_proof = self.greedy_rollout()
        self.done = True

    def run(self) -> Iterator[str]:
        if self.has_phase1:
            yield from self.run_phase1()
        yield from self.run_phase2()


# ---------------------------------------------------------------------------
# utilidades de dibujo compartidas por los episodios
# ---------------------------------------------------------------------------
class Raster:
    """Lienzo de caracteres con estilos, para dibujar figuras en la terminal."""

    def __init__(self, width: int, height: int) -> None:
        self.w, self.h = width, height
        self.g = [[" "] * width for _ in range(height)]
        self.s = [[""] * width for _ in range(height)]

    def put(self, x: int, y: int, ch: str, style: str = "") -> None:
        if 0 <= x < self.w and 0 <= y < self.h:
            self.g[y][x] = ch
            self.s[y][x] = style

    def line(self, x0: float, y0: float, x1: float, y1: float, ch: str = "·", style: str = "") -> None:
        n = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
        for i in range(n + 1):
            t = i / n
            self.put(round(x0 + (x1 - x0) * t), round(y0 + (y1 - y0) * t), ch, style)

    def circle(self, cx: float, cy: float, rx: float, ry: float, ch: str = "·", style: str = "") -> None:
        """Elipse sin huecos: barre filas y columnas."""
        for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
            v = 1 - ((y - cy) / ry) ** 2 if ry else -1
            if v >= 0:
                dx = rx * math.sqrt(v)
                self.put(round(cx - dx), y, ch, style)
                self.put(round(cx + dx), y, ch, style)
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            v = 1 - ((x - cx) / rx) ** 2 if rx else -1
            if v >= 0:
                dy = ry * math.sqrt(v)
                self.put(x, round(cy - dy), ch, style)
                self.put(x, round(cy + dy), ch, style)

    def text(self, x: int, y: int, s: str, style: str = "") -> None:
        for i, ch in enumerate(s):
            self.put(x + i, y, ch, style)

    def to_text(self):  # -> rich.text.Text
        from rich.text import Text

        t = Text()
        for r in range(self.h):
            for c in range(self.w):
                t.append(self.g[r][c], style=self.s[r][c])
            if r < self.h - 1:
                t.append("\n")
        return t
