"""Informe final en Markdown e historia en JSON."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .core import Trainer


def fmt_time(t: float) -> str:
    m, s = divmod(t, 60)
    return f"{int(m)} min {s:04.1f} s" if m else f"{s:.1f} s"


def proof_markdown(tr: Trainer) -> str:
    kb = tr.ep.kb
    lines = []
    n = 0
    for a, ok in tr.greedy_proof:
        st = kb.steps[a]
        if ok:
            n += 1
            tag = " ⚠ *postulado / cita externa, no derivado*" if st.externo else ""
            lines.append(f"{n}. **{st.title}** ({st.key}). {st.text}{tag}")
        else:
            lines.append(f"   - ✗ *salto lógico:* {st.text}")
    return "\n".join(lines)


def build_report(tr: Trainer) -> str:
    kb = tr.ep.kb
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    depth = kb.depth()
    order_rows = "\n".join(
        f"| {k} | {kb.by_key(k).title} | {depth[k]} | {tr.first_valid.get(k, '—')} | {tr.first_greedy.get(k, '—')} | {tr.step_usage.get(k, 0)} |"
        for k in sorted(kb.required, key=lambda k: (tr.first_greedy.get(k, 10**9), depth[k]))
    )
    inval_rows = "\n".join(f"| {k} | {kb.by_key(k).title} | {v} |" for k, v in tr.invalid_usage.most_common(8)) or "| — | — | — |"
    ext_rows = "\n".join(f"| {k} | {kb.by_key(k).title} | {v} |" for k, v in tr.externo_usage.most_common()) or "| — | — | — |"
    hitos = "\n".join(f"| {m.phase} | {m.episode} | {m.t:.1f} s | {m.text} |" for m in tr.milestones)
    f1 = ""
    if tr.has_phase1:
        f1 = (f"\n## Fase 1 · hacer\n\nLogros: {tr.ok_total} · fracasos: {tr.fail_total} · éxito final (100 últimas): "
              f"{100 * tr.success_curve[-1]:.0f} % · tiempo {fmt_time(tr.phase1_time)}.\n")
    return f"""# {tr.ep.titulo}

*{tr.ep.subtitulo}*

Generado: {now} · semilla {tr.seed} · tiempo total **{fmt_time(tr.elapsed)}**.

## Lectura

{tr.ep.lectura}
{f1}
## Fase 2 · demostración final (política voraz, sin exploración)

**Teorema.** {kb.theorem}

{proof_markdown(tr)}

Demostraciones completas: {tr.qed_total} · mínimas: {tr.minimal_total} · mejor retorno: {tr.best_reward:+.2f}.

### Orden en que se asentó cada paso

| paso | título | profundidad | 1ª vez válido (gen) | entra en política voraz (gen) | usos |
|---|---|---|---|---|---|
{order_rows}

### Postulados y citas externas usados (ámbar)

| paso | título | veces |
|---|---|---|
{ext_rows}

### Saltos lógicos más frecuentes

| paso | título | intentos inválidos |
|---|---|---|
{inval_rows}

## Bitácora de hitos

| fase | generación | tiempo | hito |
|---|---|---|---|
{hitos}
"""


def save_run(tr: Trainer, out_dir: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = out_dir / tr.ep.slug / stamp
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "informe.md").write_text(build_report(tr), encoding="utf-8")
    (run_dir / "demostracion.md").write_text(proof_markdown(tr), encoding="utf-8")
    kb = tr.ep.kb
    history = {
        "episodio": tr.ep.slug, "seed": tr.seed, "elapsed": tr.elapsed,
        "milestones": [m.__dict__ for m in tr.milestones],
        "phase1": {"success_curve": tr.success_curve, "ratio_curve": tr.ratio_curve, "ok": tr.ok_total, "fail": tr.fail_total},
        "phase2": {"reward_curve": tr.reward_curve, "first_valid": tr.first_valid, "first_greedy": tr.first_greedy,
                   "step_usage": dict(tr.step_usage), "invalid_usage": dict(tr.invalid_usage),
                   "externo_usage": dict(tr.externo_usage), "qed_total": tr.qed_total, "minimal_total": tr.minimal_total,
                   "final_proof": [[kb.steps[a].key, ok] for a, ok in tr.greedy_proof]},
    }
    (run_dir / "historia.json").write_text(json.dumps(history, ensure_ascii=False, indent=1), encoding="utf-8")
    return run_dir
