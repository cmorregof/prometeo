"""Interfaz en vivo genérica para los episodios históricos (rich)."""

from __future__ import annotations

from rich.console import Group, RenderableType
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .core import Trainer

SPARK = "▁▂▃▄▅▆▇█"


def fmt_time(t: float) -> str:
    m, s = divmod(t, 60)
    return f"{int(m):02d}:{s:05.2f}"


def sparkline(values: list[float], width: int, lo: float = 0.0, hi: float = 1.0) -> str:
    vals = values[-width:]
    if not vals:
        return ""
    out = []
    for v in vals:
        k = 0 if hi == lo else int((v - lo) / (hi - lo) * (len(SPARK) - 1))
        out.append(SPARK[max(0, min(len(SPARK) - 1, k))])
    return "".join(out)


# ---------------------------------------------------------------------------
# Fase 1
# ---------------------------------------------------------------------------
def phase1_panel(tr: Trainer, width: int, height: int) -> Panel:
    ep = tr.ep
    if not tr.has_phase1:
        return Panel(Text("este episodio sólo tiene fase de demostración", style="dim"),
                     title="Fase 1", border_style="grey50")
    env = tr.env1
    active = tr.phase == 1
    head = Text.from_markup(env.headline(), overflow="ellipsis")
    head.no_wrap = True
    act = Text(f"acción: {env.action_names[tr.last_action1] if tr.last_action1 >= 0 else '—'}", style="dim")
    inner_h = max(6, height - 5)
    body = Group(head, act, env.render(max(20, width - 4), inner_h))
    title = ep.fase1_titulo + ("" if active else " · completada ✔")
    return Panel(body, title=title, border_style="yellow" if active else "green", padding=(0, 1))


def policy_panel(tr: Trainer, width: int) -> Panel:
    if not tr.has_phase1:
        return Panel(Text(""), title="Lo aprendido", border_style="grey50")
    body = tr.env1.policy_summary(tr.agent1, width - 4)
    return Panel(body, title="Lo que aprendió a hacer", border_style="yellow" if tr.phase == 1 else "green", padding=(0, 1))


# ---------------------------------------------------------------------------
# Fase 2
# ---------------------------------------------------------------------------
def proof_lines(tr: Trainer, attempts: list[tuple[int, bool]], max_lines: int, tail: bool = True) -> Text:
    kb = tr.ep.kb
    t = Text(no_wrap=True, overflow="ellipsis")
    if tail:
        shown = attempts[-max_lines:]
        if len(attempts) > max_lines:
            t.append(f"  … {len(attempts) - max_lines} intentos anteriores\n", style="dim")
    else:
        shown = attempts[:max_lines]
    n = 0
    for a, ok in shown:
        st = kb.steps[a]
        if ok:
            n += 1
            if st.is_qed:
                style = "bold green"
            elif st.externo:
                style = "bold yellow"
            else:
                style = "green"
            t.append(f"{n:>2}. ", style="dim")
            t.append(f"{st.key:<8}", style=style)
            if st.externo:
                t.append("⚠ postulado/cita: ", style="yellow")
            t.append(f"{st.text[:90]}", style="white" if st.is_qed else ("yellow" if st.externo else ""))
        else:
            t.append(" ✗  ", style="red")
            t.append(f"{st.key:<8}", style="red")
            t.append(f"{st.text[:80]}", style="dim red strike")
        t.append("\n")
    if not tail and len(attempts) > max_lines:
        t.append(f"  … {len(attempts) - max_lines} intentos más", style="dim")
    return t


def dependency_progress(tr: Trainer, mask_keys: set[str]) -> Text:
    kb = tr.ep.kb
    t = Text(no_wrap=True, overflow="ellipsis")
    for st in kb.steps:
        if st.distractor:
            continue
        done = st.key in mask_keys
        if done and st.externo:
            style = "black on yellow"
        elif done:
            style = "black on green"
        else:
            style = "dim on grey23"
        t.append(st.key, style=style)
        t.append(" ")
    return t


def phase2_panel(tr: Trainer, height: int) -> Panel:
    env = tr.env2
    if tr.phase == 1:
        return Panel(Text("en espera de la fase 1…", style="dim"), title=tr.ep.fase2_titulo, border_style="grey50")
    n_valid = len(env.proof_keys)
    n_ext = sum(1 for k in env.proof_keys if tr.ep.kb.by_key(k).externo)
    head = Text.from_markup(
        f"intento actual · [green]{n_valid}[/] pasos válidos · [yellow]{n_ext}[/] postulados · "
        f"[red]{env.n_invalid}[/] saltos lógicos" + ("  [bold green]∎ QED[/]" if env.finished else ""))
    prog = dependency_progress(tr, set(env.proof_keys))
    lines = proof_lines(tr, env.attempts, max_lines=max(4, height - 6))
    active = tr.phase == 2 and not tr.done
    return Panel(Group(head, prog, lines), title=tr.ep.fase2_titulo + ("" if active else " · completada ✔"),
                 border_style="magenta" if active else "green", padding=(0, 1))


def belief_panel(tr: Trainer, height: int) -> Panel:
    kb = tr.ep.kb
    if tr.phase == 1:
        return Panel(Text(""), title="Lo que el agente cree ahora", border_style="grey50")
    g = tr.greedy_proof
    keys = [kb.steps[a].key for a, ok in g if ok]
    clean = all(ok for _, ok in g)
    finished = kb.qed_key in keys
    n_ext = sum(1 for k in keys if kb.by_key(k).externo)
    if finished and clean and len(keys) == kb.min_len:
        verdict = "[bold green]demostración mínima y correcta ✔[/]"
    elif finished:
        verdict = "[green]completa[/]" + ("" if clean else " [red]con saltos lógicos[/]")
    else:
        verdict = "[yellow]incompleta: no llega a ∎[/]"
    if finished and n_ext:
        verdict += f"  [bold yellow]⚠ apoyada en {n_ext} postulado(s)/cita(s)[/]"
    head = Text.from_markup(f"política voraz (sin explorar): {verdict}")
    thm = Text(f"Teorema. {kb.theorem}", style="italic dim", overflow="ellipsis")
    thm.no_wrap = True
    lines = proof_lines(tr, g, max_lines=max(4, height - 6), tail=False)
    return Panel(Group(head, thm, lines), title="Lo que el agente cree ahora", border_style="magenta", padding=(0, 1))


# ---------------------------------------------------------------------------
# Pie
# ---------------------------------------------------------------------------
def stats_panel(tr: Trainer) -> Panel:
    tb = Table.grid(padding=(0, 1))
    for _ in range(2):
        tb.add_column(style="dim", no_wrap=True)
        tb.add_column(justify="right", no_wrap=True)
    p1_rate = f"{100 * tr.success_curve[-1]:.0f}%" if tr.success_curve else "—"
    p2_rate = f"{100 * sum(tr.finished2) / len(tr.finished2):.0f}%" if tr.finished2 else "—"
    eps = tr.agent1.eps if (tr.phase == 1 and tr.has_phase1) else tr.agent2.eps
    gen = tr.ep1 if tr.phase == 1 else tr.ep2
    tb.add_row("⏱ tiempo", f"[bold]{fmt_time(tr.elapsed)}[/]", "generación", f"[bold]{gen}[/]")
    tb.add_row("fase", f"[bold]{tr.phase}/2[/]", "ε exploración", f"{eps:.3f}")
    fails = f"[red]{tr.fail_total}[/]" + (f" [yellow]+{tr.imposible_total} imposibles[/]" if tr.imposible_total else "")
    tb.add_row("F1 logros", f"[green]{tr.ok_total}[/]", "F1 fracasos", fails)
    tb.add_row("F1 éxito/100", p1_rate, "F1 tiempo", fmt_time(tr.phase1_time) if tr.phase1_time else "—")
    tb.add_row("F2 completas", f"[green]{tr.qed_total}[/]", "F2 mínimas", f"[bold green]{tr.minimal_total}[/]")
    tb.add_row("F2 éxito/100", p2_rate, "F2 mejor", f"{tr.best_reward:+.1f}" if tr.best_reward > -1e9 else "—")
    n_upd = (tr.agent1.updates if tr.has_phase1 else 0) + tr.agent2.updates
    if tr.reward_curve:
        lo, hi = min(tr.reward_curve[-60:]), max(tr.reward_curve[-60:])
        tb.add_row("Q updates", f"{n_upd:,}", "F2 retorno", sparkline(tr.reward_curve, 22, lo, hi))
    elif tr.success_curve:
        tb.add_row("Q updates", f"{n_upd:,}", "F1 éxito", sparkline(tr.success_curve, 22))
    return Panel(tb, title="Marcador", border_style="blue", padding=(0, 1))


def log_panel(tr: Trainer, n: int) -> Panel:
    t = Text(no_wrap=True, overflow="ellipsis")
    for line in tr.log[-n:]:
        if "postulado" in line or "NUNCA" in line or "nunca" in line:
            style = "bold yellow"
        elif any(w in line for w in ("∎", "mínima", "ESTO", "redescubrió", "distingue", "reconoce", "regla completa")):
            style = "bold green"
        else:
            style = ""
        t.append(line + "\n", style=style)
    return Panel(t, title="Bitácora de hitos", border_style="blue", padding=(0, 1))


def header(tr: Trainer) -> Panel:
    gen = tr.ep1 if tr.phase == 1 else tr.ep2
    txt = Text.from_markup(
        f"[bold white]{tr.ep.titulo}[/]   [dim]{tr.ep.subtitulo}[/]   "
        f"[bold yellow]⏱ {fmt_time(tr.elapsed)}[/]   "
        + ("[bold green]ENTRENAMIENTO TERMINADO[/]" if tr.done else f"[bold]Fase {tr.phase}[/] · generación [bold]{gen}[/]"),
        overflow="ellipsis")
    txt.no_wrap = True
    return Panel(txt, style="on grey11")


def build_layout(tr: Trainer, width: int, height: int) -> Layout:
    root = Layout()
    footer_h = 11 if height >= 42 else 9
    body_h = max(20, height - 3 - footer_h)
    root.split_column(
        Layout(header(tr), name="header", size=3),
        Layout(name="body", size=body_h),
        Layout(name="footer", size=footer_h),
    )
    root["body"].split_row(Layout(name="left"), Layout(name="right"))
    left_w = width // 2
    if tr.has_phase1:
        pol_h = min(13, body_h // 3 + 2)
        root["left"].split_column(
            Layout(phase1_panel(tr, left_w, body_h - pol_h), name="plot"),
            Layout(policy_panel(tr, left_w), name="policy", size=pol_h),
        )
    else:
        root["left"].update(belief_panel(tr, body_h))
    if tr.has_phase1:
        root["right"].split_column(
            Layout(phase2_panel(tr, body_h // 2), name="proof"),
            Layout(belief_panel(tr, body_h - body_h // 2), name="belief"),
        )
    else:
        root["right"].update(phase2_panel(tr, body_h))
    root["footer"].split_row(Layout(stats_panel(tr), ratio=2), Layout(log_panel(tr, footer_h - 2), ratio=3))
    return root
