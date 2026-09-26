"""Un solo MDP para los tres jueces.

estado  = (enunciado del target, lemas/VCs disponibles, historial de resultados)
acción  = propuesta (formato del juez)
episodio: termina en ACCEPTED o al agotar el presupuesto de pasos B
recompensa base = 1 si ACCEPTED, 0 en otro caso.
recompensa moldeada (shaped=True): r + β·partial·[no aceptada], β ∈ [0, 0.5].
deriva: STATEMENT_DRIFT recibe 0 por defecto; con drift_penalty = δ > 0 recibe −δ (experimentos de control).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .verifiers import Outcome, Verifier


@dataclass
class Observation:
    target: dict
    history: list[dict] = field(default_factory=list)  # [{proposal, outcome_label, feedback}]
    step: int = 0


def reward(out: Outcome, shaped: bool = False, beta: float = 0.5, drift_penalty: float = 0.0) -> float:
    if out.accepted:
        return 1.0
    if out.outcome_label == "STATEMENT_DRIFT" and drift_penalty > 0:
        return -drift_penalty
    return beta * out.partial_credit if shaped else 0.0


class ProofEnv:
    def __init__(self, verifier: Verifier, budget: int = 5, shaped: bool = False, beta: float = 0.5, drift_penalty: float = 0.0):
        if not 0.0 <= beta <= 0.5:
            raise ValueError("β debe estar en [0, 0.5]")
        self.verifier = verifier
        self.budget = budget
        self.shaped = shaped
        self.beta = beta
        self.drift_penalty = drift_penalty
        self._target = verifier.target()
        self.obs: Observation | None = None

    def reset(self) -> Observation:
        self.obs = Observation(target=self._target)
        return self.obs

    def step(self, proposal: Any, extra: dict | None = None) -> tuple[Observation, float, bool, Outcome]:
        """`extra` se añade a la propuesta solo para verificarla (p. ej. la biblioteca de lemas de la memoria);
        el historial guarda la propuesta del agente tal cual."""
        assert self.obs is not None, "llama a reset() primero"
        out = self.verifier.verify(self._target, {**proposal, **extra} if extra and isinstance(proposal, dict) else proposal)
        r = reward(out, self.shaped, self.beta, self.drift_penalty)
        self.obs.step += 1
        self.obs.history.append({"proposal": proposal, "outcome_label": out.outcome_label, "feedback": self.verifier.feedback(proposal, out)})
        done = out.accepted or self.obs.step >= self.budget
        return self.obs, r, done, out
