"""Grabación del entrenamiento a JSON, para reproducirlo en el visor web.

Un cuadro por cada momento que la interfaz de terminal redibujaría, con todo
lo que el visor necesita: tablero de fase 1 (snapshot del entorno), política
aprendida, intento de demostración en curso, demostración voraz, marcador y
bitácora. El visor reproduce los cuadros a la velocidad que quiera el
presentador, con pausa y línea de tiempo.
"""

from __future__ import annotations

import json
from pathlib import Path

from .core import Trainer


def kb_json(tr: Trainer) -> dict:
    kb = tr.ep.kb
    return {
        "theorem": kb.theorem,
        "steps": [{"key": s.key, "title": s.title, "text": s.text, "deps": list(s.deps),
                   "distractor": s.distractor, "qed": s.is_qed, "externo": s.externo} for s in kb.steps],
        "required": sorted(kb.required),
        "min_len": kb.min_len,
        "depth": kb.depth(),
    }


def frame(tr: Trainer, kind: str) -> dict:
    kb = tr.ep.kb
    f: dict = {
        "kind": kind, "phase": tr.phase, "gen": tr.ep1 if tr.phase == 1 else tr.ep2, "t": round(tr.elapsed, 3),
        "eps": round((tr.agent1.eps if (tr.phase == 1 and tr.has_phase1) else tr.agent2.eps), 3),
        "stats": {"ok": tr.ok_total, "fail": tr.fail_total, "imposible": tr.imposible_total,
                  "success100": round(tr.success_curve[-1], 3) if tr.success_curve else None,
                  "qed": tr.qed_total, "minimal": tr.minimal_total,
                  "success2_100": round(sum(tr.finished2) / len(tr.finished2), 3) if tr.finished2 else None,
                  "best_reward": tr.best_reward if tr.best_reward > -1e9 else None,
                  "updates": (tr.agent1.updates if tr.has_phase1 else 0) + tr.agent2.updates},
        "log_len": len(tr.log),
    }
    if tr.has_phase1:
        f["board"] = tr.env1.snapshot()
        f["action1"] = tr.env1.action_names[tr.last_action1] if tr.last_action1 >= 0 else None
        gen = tr.ep1
        if kind in ("episode", "final") and (gen <= 60 or gen % 10 == 0 or tr.phase == 2):
            f["policy1"] = tr.env1.policy_rows(tr.agent1)   # el visor conserva la última recibida
    if tr.phase == 2:
        f["attempt"] = [[kb.steps[a].key, ok] for a, ok in tr.env2.attempts]
        if kind in ("episode", "final") and (tr.ep2 <= 60 or tr.ep2 % 25 == 0):
            f["greedy"] = [[kb.steps[a].key, ok] for a, ok in tr.greedy_proof]   # idem
    return f


def record(tr: Trainer, path: Path, every_episode: int = 1) -> Path:
    """Entrena y graba. `every_episode` = 1 graba todas las generaciones; 5, una de cada cinco."""
    frames: list[dict] = []
    curve_seen = 0
    for kind in tr.run():
        if kind == "episode":
            gen = tr.ep1 if tr.phase == 1 else tr.ep2
            if gen % every_episode != 0 and gen > 60:
                continue
        frames.append(frame(tr, kind))
    frames.append(frame(tr, "final"))
    data = {
        "episodio": {"slug": tr.ep.slug, "titulo": tr.ep.titulo, "subtitulo": tr.ep.subtitulo,
                     "fase1_titulo": tr.ep.fase1_titulo, "fase2_titulo": tr.ep.fase2_titulo,
                     "lectura": tr.ep.lectura, "has_phase1": tr.has_phase1,
                     "action_names": tr.env1.action_names if tr.has_phase1 else []},
        "kb": kb_json(tr),
        "log": tr.log,
        "milestones": [m.__dict__ for m in tr.milestones],
        "curves": {"success1": tr.success_curve, "reward2": tr.reward_curve},
        "frames": frames,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return path
