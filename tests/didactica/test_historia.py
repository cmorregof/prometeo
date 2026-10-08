"""Humo: cada episodio entrena corto sin interfaz y llega a donde debe."""

import pytest

from didactica.historia.core import ProofEnv, Trainer
from didactica.historia.episodios import EPISODIOS


@pytest.mark.parametrize("slug", list(EPISODIOS))
def test_kb_is_acyclic_and_has_qed(slug):
    kb = EPISODIOS[slug].kb
    assert kb.qed_key == "QED"
    assert kb.depth()["QED"] >= 3
    for st in kb.steps:
        for d in st.deps:
            assert d in kb.index, f"{slug}: {st.key} depende de {d}, que no existe"


@pytest.mark.parametrize("slug", list(EPISODIOS))
def test_topological_proof_reaches_qed(slug):
    kb = EPISODIOS[slug].kb
    env = ProofEnv(kb)
    env.reset()
    pending = set(kb.required)
    while pending:
        progressed = False
        for k in sorted(pending):
            i = kb.index[k]
            if env.is_valid(i):
                env.step(i)
                pending.discard(k)
                progressed = True
        assert progressed, f"{slug}: ciclo en las dependencias"
    assert env.finished and env.n_invalid == 0


@pytest.mark.parametrize("slug", list(EPISODIOS))
def test_short_training_learns(slug):
    ep = EPISODIOS[slug]
    ep.episodes1, ep.episodes2 = 800, 1200
    tr = Trainer(ep, seed=3)
    for _ in tr.run():
        pass
    assert tr.qed_total > 0
    if tr.has_phase1:
        assert tr.success_curve[-1] >= 0.5
    if slug == "quinto":
        # nunca hay demostración sin puente: toda ∎ usa PUENTE
        assert tr.step_usage["PUENTE"] == tr.qed_total
