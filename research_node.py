#!/usr/bin/env python3
import sys
import io
# Força UTF-8 no Windows para emojis funcionarem
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

"""
Research Node — Moto E5 Bioinfo Dashboard
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Dashboard TUI para monitorar pipelines de bioinfo,
métricas de sistema e automações.

Uso:
    python research_node.py              # roda o dashboard
    python research_node.py --once       # imprime uma vez e sai
    python research_node.py --no-color   # saída sem cores (para log)

Requer: rich, psutil (opcional)
Instale: pip install rich psutil
Ou rode: bash install.sh (no Termux)
"""
import sys
import os
import time
import argparse

# Garante que o diretório do projeto está no path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rich.live import Live
from rich.console import Console
from rich.text import Text

import config
from collectors.system import SystemCollector
from collectors.pipelines import PipelineMonitor
from ui.dashboard import Dashboard


def parse_args():
    parser = argparse.ArgumentParser(
        description="Research Node — Bioinfo Dashboard"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Imprime o dashboard uma vez e sai",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Desabilita cores (útil para logs)",
    )
    parser.add_argument(
        "--refresh",
        type=int,
        default=config.REFRESH_INTERVAL,
        help=f"Intervalo de refresh em segundos (default: {config.REFRESH_INTERVAL})",
    )
    parser.add_argument(
        "--pipelines",
        action="store_true",
        help="Apenas verifica status dos pipelines e sai",
    )
    return parser.parse_args()


def print_banner(console: Console):
    """Imprime banner de inicialização."""
    banner = Text()
    banner.append("\n")
    banner.append("  ⚡ RESEARCH NODE\n", style="bold cyan")
    banner.append("  ", style="cyan")
    banner.append("Moto E5 — Bioinfo & Automation Hub\n", style="dim")
    banner.append("  ", style="cyan")
    banner.append(f"  Pipelines: {len(config.PIPELINES)}", style="dim")
    enabled = sum(1 for p in config.PIPELINES if p.get("enabled", True))
    banner.append(f" ({enabled} enabled)\n", style="dim green")
    banner.append("  ", style="cyan")
    banner.append(f"  Refresh: {config.REFRESH_INTERVAL}s\n", style="dim")
    banner.append("  ", style="cyan")
    banner.append("  Press Ctrl+C to exit\n", style="dim yellow")
    banner.append("\n")
    console.print(banner)


def check_pipelines_only():
    """Modo --pipelines: verifica status e imprime."""
    console = Console()
    monitor = PipelineMonitor(config.PIPELINES)

    console.print("[bold cyan]Checking pipelines...[/bold cyan]\n")
    results = monitor.check_all()

    for r in monitor.ordered_results:
        console.print(f"  {r.status.icon}  {r.name:<20} {r.status.label}")

    summary = monitor.summary
    console.print(
        f"\n  [green]OK: {summary.get('ok', 0)}[/green]  "
        f"[red]FAILED: {summary.get('failed', 0)}[/red]  "
        f"[yellow]WARN: {summary.get('warning', 0)}[/yellow]"
    )


def main():
    args = parse_args()
    console = Console(no_color=args.no_color)

    # Modo pipelines-only
    if args.pipelines:
        check_pipelines_only()
        return

    # Inicializa componentes
    collector = SystemCollector()
    monitor = PipelineMonitor(config.PIPELINES)
    dashboard = Dashboard()

    print_banner(console)

    # Coleta inicial
    metrics = collector.collect()
    results = monitor.check_all()

    if args.once:
        # Modo uma vez
        layout = dashboard.build(
            metrics,
            list(results.values()),
            monitor.events,
            monitor.summary,
        )
        console.print(layout)
        return

    # Modo live dashboard
    try:
        with Live(
            console=console,
            refresh_per_second=1,
            screen=True,
        ) as live:
            while True:
                metrics = collector.collect()
                results = monitor.check_all()

                layout = dashboard.build(
                    metrics,
                    list(results.values()),
                    monitor.events,
                    monitor.summary,
                )
                live.update(layout)
                time.sleep(args.refresh)

    except KeyboardInterrupt:
        console.clear()
        console.print(
            "\n[bold cyan]⚡ Research Node[/bold cyan] "
            "[dim]stopped.[/dim]\n"
        )


if __name__ == "__main__":
    main()
