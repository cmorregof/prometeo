"""`python -m didactica.historia <episodio>`  ·  `--list` para verlos todos."""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown

from .core import Trainer
from .episodios import EPISODIOS, ORDEN
from .report import build_report, save_run
from .tui import build_layout


def parse_args(argv=None):
    ap = argparse.ArgumentParser(prog="historia",
        description="Mira en vivo cómo un agente de RL rehace un episodio de la historia de la matemática.")
    ap.add_argument("episodio", nargs="?", choices=ORDEN, help="cuál correr (--list para verlos)")
    ap.add_argument("--list", action="store_true", help="lista los episodios en orden histórico")
    ap.add_argument("--all", action="store_true", help="corre todos, uno tras otro")
    ap.add_argument("--episodes1", type=int, default=None, help="generaciones de la fase 1")
    ap.add_argument("--episodes2", type=int, default=None, help="generaciones de la fase 2")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--speed", type=float, default=1.0, help="multiplicador de velocidad (0.5 = más lento, 2 = más rápido)")
    ap.add_argument("--pausa-hitos", type=float, default=2.5, help="segundos de pausa cuando aparece un hito (0 = sin pausa)")
    ap.add_argument("--fast", action="store_true", help="sin pausas: sólo redibuja")
    ap.add_argument("--no-tui", action="store_true", help="sin interfaz: entrena y escribe el informe")
    ap.add_argument("--fps", type=float, default=30.0)
    ap.add_argument("--out", type=Path, default=Path("runs/historia"))
    ap.add_argument("--record", type=Path, default=None, help="graba el entrenamiento a este JSON (sin interfaz) para el visor web")
    ap.add_argument("--every", type=int, default=2, help="con --record: graba una de cada N generaciones (tras las primeras 60)")
    return ap.parse_args(argv)


def run_one(slug: str, args, console: Console) -> None:
    ep = EPISODIOS[slug]
    if args.episodes1 is not None:
        ep.episodes1 = args.episodes1
    if args.episodes2 is not None:
        ep.episodes2 = args.episodes2
    tr = Trainer(ep, seed=args.seed)
    if args.record is not None:
        from .record import record
        path = args.record if args.record.suffix == ".json" else args.record / f"{slug}.json"
        record(tr, path, every_episode=args.every)
        console.print(f"[bold green]Grabado[/] {path}  ({path.stat().st_size / 1e6:.1f} MB, {len(tr.log)} hitos)")
        return
    if args.no_tui:
        for _ in tr.run():
            pass
    else:
        dwell_of = {"iter": 0.06, "iter2": 0.16, "episode": 0.006}   # segundos por cuadro, a velocidad 1
        pausa = 0.0 if args.fast else args.pausa_hitos
        min_frame = 1.0 / args.fps
        last_render = 0.0
        n_log = len(tr.log)
        size = console.size
        with Live(build_layout(tr, size.width, size.height), console=console, screen=True, auto_refresh=False) as live:
            for kind in tr.run():
                now = time.perf_counter()
                new_milestone = len(tr.log) != n_log
                if now - last_render >= min_frame or new_milestone:
                    size = console.size
                    live.update(build_layout(tr, size.width, size.height), refresh=True)
                    last_render = now
                    n_log = len(tr.log)
                dwell = 0.0 if args.fast else dwell_of.get(kind, 0.0) / args.speed
                if dwell:
                    time.sleep(dwell)
                if new_milestone and pausa:
                    time.sleep(pausa)
            live.update(build_layout(tr, size.width, size.height), refresh=True)
            if not args.fast:
                time.sleep(3.0)
    run_dir = save_run(tr, args.out)
    console.print(Markdown(build_report(tr)))
    console.print(f"\n[bold green]Informe guardado en[/] {run_dir}/informe.md  ·  historia.json  ·  demostracion.md")


def main(argv=None) -> int:
    args = parse_args(argv)
    console = Console()
    if args.list or (not args.episodio and not args.all):
        for i, slug in enumerate(ORDEN, 1):
            e = EPISODIOS[slug]
            console.print(f"[bold]{i}. {slug:<12}[/] {e.titulo}\n   [dim]{e.subtitulo}[/]")
        return 0
    for slug in (ORDEN if args.all else [args.episodio]):
        run_one(slug, args, console)
    return 0
