"""
Research Node — Dashboard UI
Renderiza o painel principal com Rich (adaptativo ao tamanho da tela).
"""
from collections import deque
from rich.console import Console, group
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align
from rich import box

from collectors.system import SystemMetrics
from collectors.pipelines import PipelineResult, PipelineStatus
import config


# ── Sparkline ────────────────────────────────────────────────
# Blocos Unicode para gráfico (escala 0-100)
SPARK_CHARS = "▁▂▃▄▅▆▇█"


def sparkline(data: list, width: int = 0) -> str:
    """
    Gera uma string sparkline a partir de uma lista de valores.
    Se width > 0 e len(data) > width, amostra para caber.
    """
    if not data:
        return ""

    if width > 0 and len(data) > width:
        step = len(data) / width
        data = [data[int(i * step)] for i in range(width)]

    if len(data) < 2:
        data = data + [data[-1]]

    mn, mx = min(data), max(data)
    rng = mx - mn if mx != mn else 1

    result = []
    for v in data:
        idx = int(((v - mn) / rng) * (len(SPARK_CHARS) - 1))
        result.append(SPARK_CHARS[idx])
    return "".join(result)


def bar(percent: float, width: int = 20) -> str:
    """Barra de progresso Unicode."""
    filled = int(percent / 100 * width)
    return "█" * filled + "░" * (width - filled)


class Dashboard:
    """Constrói o layout do dashboard com Rich."""

    def __init__(self):
        self.console = Console()
        self.cpu_history: deque = deque(maxlen=config.HISTORY_MAX_POINTS)
        self.ram_history: deque = deque(maxlen=config.HISTORY_MAX_POINTS)
        self.refresh_count = 0

    @property
    def panel_width(self) -> int:
        """Largura útil dos painéis (console - borders)."""
        return max(20, self.console.width - 2)

    def build(
        self,
        metrics: SystemMetrics,
        pipeline_results: list,
        events: list,
        pipeline_summary: dict,
    ) -> Layout:
        """Constrói o layout completo do dashboard."""
        self.cpu_history.append(metrics.cpu_percent)
        self.ram_history.append(metrics.ram_percent)
        self.refresh_count += 1

        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="metrics"),
            Layout(name="history"),
            Layout(name="pipelines", size=max(5, len(pipeline_results) + 2)),
            Layout(name="footer", size=4),
        )
        layout["footer"].split_row(
            Layout(name="events", ratio=2),
            Layout(name="summary", size=24),
        )

        layout["metrics"].update(self._build_metrics(metrics))
        layout["history"].update(self._build_history(metrics))
        layout["pipelines"].update(self._build_pipelines(pipeline_results))
        layout["events"].update(self._build_events(events))
        layout["summary"].update(self._build_summary(pipeline_summary))
        layout["header"].update(self._build_header(metrics))

        return layout

    # ── Cabeçalho ────────────────────────────────────────────
    def _build_header(self, metrics: SystemMetrics) -> Panel:
        title = Text()
        title.append("  ⚡ ", style="bold cyan")
        title.append(config.DASHBOARD_TITLE, style="bold white")

        info = Text()
        info.append(f" {metrics.hostname}", style="bold white")
        info.append(f"  {metrics.platform}", style="dim cyan")
        info.append(f"  ▲ {metrics.uptime_str}", style="dim green")

        table = Table.grid(expand=True)
        table.add_column(ratio=1)
        table.add_column(justify="right", no_wrap=True)
        table.add_row(title, info)

        return Panel(
            table,
            style="bold blue",
            border_style="bright_blue",
        )

    # ── Métricas (CPU + RAM lado a lado) ─────────────────────
    def _build_metrics(self, metrics: SystemMetrics) -> Panel:
        w = max(8, self.panel_width // 2 - 3)
        cpu_bar_w = min(w, 22)
        ram_bar_w = min(w, 22)

        cpu_color = self._color_for(metrics.cpu_percent)
        ram_color = self._color_for(metrics.ram_percent)

        def cpu_block():
            t = Text("", end="")
            t.append_text(Text.from_markup("[bold]CPU[/bold]\n"))
            t.append(f"{bar(metrics.cpu_percent, cpu_bar_w)}\n", style=cpu_color)
            t.append(f"{metrics.cpu_percent:5.1f}%\n", style=cpu_color)
            s = sparkline(list(self.cpu_history), width=max(10, w - 2))
            if s:
                t.append(s, style="dim cyan")
            return t

        def ram_block():
            t = Text("", end="")
            t.append_text(Text.from_markup("[bold]RAM[/bold]\n"))
            t.append(f"{bar(metrics.ram_percent, ram_bar_w)}\n", style=ram_color)
            t.append(
                f"{metrics.ram_used_mb:5.0f}/{metrics.ram_total_mb:.0f}MB\n",
                style=ram_color,
            )
            s = sparkline(list(self.ram_history), width=max(10, w - 2))
            if s:
                t.append(s, style="dim magenta")
            return t

        table = Table.grid(padding=(0, 2), expand=True)
        table.add_column(justify="left", ratio=1)
        table.add_column(justify="left", ratio=1)
        table.add_row(cpu_block(), ram_block())

        return Panel(
            table,
            title="[bold]SYSTEM[/bold]",
            border_style="bright_blue",
            expand=True,
        )

    # ── Histórico + processos ─────────────────────────────────
    def _build_history(self, metrics: SystemMetrics) -> Panel:
        w = self.panel_width - 4

        content = Text()
        content.append("  CPU / MEMORY HISTORY\n", style="bold")

        cpu_spark = sparkline(list(self.cpu_history), width=w)
        if cpu_spark:
            content.append(f"  CPU  {cpu_spark}\n", style="cyan")
        else:
            content.append("  CPU  collecting...\n", style="dim")

        ram_spark = sparkline(list(self.ram_history), width=w)
        if ram_spark:
            content.append(f"  RAM  {ram_spark}\n", style="magenta")
        else:
            content.append("  RAM  collecting...\n", style="dim")

        if self.cpu_history:
            avg = sum(self.cpu_history) / len(self.cpu_history)
            content.append(
                f"  ─────────────────────────────────"
                f"────────────────────────\n",
                style="dim",
            )

        # Processos
        if metrics.top_processes:
            content.append("  TOP PROCESSES\n", style="bold")
            for p in metrics.top_processes[:5]:
                name = p["name"][:max(10, w - 24)]
                content.append(
                    f"  {name:<{max(10, w - 24)}} "
                    f"[{p['cpu']:5.1f}%  {p['mem']:4.1f}%]\n",
                    style="dim" if p["cpu"] < 30 else "yellow",
                )

        if self.cpu_history:
            content.append(
                f"  avg {avg:.1f}%  max {max(self.cpu_history):.1f}%  "
                f"{len(self.cpu_history)} samples",
                style="dim",
            )

        return Panel(
            content,
            title="[bold]CPU / MEMORY HISTORY[/bold]",
            border_style="blue",
            expand=True,
        )

    # ── Pipelines ─────────────────────────────────────────────
    def _build_pipelines(self, results: list) -> Panel:
        table = Table(
            show_header=True,
            header_style="bold",
            expand=True,
            padding=(0, 1),
            border_style="dim",
            box=box.SIMPLE,
        )
        table.add_column(" ", width=2)
        table.add_column("PIPELINE", no_wrap=True)
        table.add_column("STATUS", width=10)
        table.add_column("CATEGORY", width=10, style="dim")
        table.add_column("CHECK", width=10, style="dim")

        for r in results:
            table.add_row(
                r.status.icon,
                r.name,
                r.status.label,
                r.category,
                r.last_check_str,
            )

        return Panel(
            table,
            title="[bold]DATA PIPELINES[/bold]",
            border_style="blue",
            expand=True,
        )

    # ── Eventos ───────────────────────────────────────────────
    def _build_events(self, events: list) -> Panel:
        content = Text.from_markup("")
        if events:
            for evt in events[-config.EVENT_LOG_MAX:]:
                content.append_text(Text.from_markup(f"  {evt}\n"))
        else:
            content.append("  waiting for events...\n", style="dim")
        return Panel(
            content,
            title="[bold]EVENT LOG[/bold]",
            border_style="dim blue",
            expand=True,
        )

    # ── Summary ───────────────────────────────────────────────
    def _build_summary(self, summary: dict) -> Panel:
        ok = summary.get(PipelineStatus.OK, 0)
        failed = summary.get(PipelineStatus.FAILED, 0)
        warn = summary.get(PipelineStatus.WARNING, 0)

        content = Text()
        content.append(f"  OK     {ok}\n", style="green")
        content.append(f"  WARN   {warn}\n", style="yellow")
        content.append(f"  FAILED {failed}\n", style="red")
        content.append(f"\n  refresh #{self.refresh_count}", style="dim")
        return Panel(
            content,
            title="[bold]SUMMARY[/bold]",
            border_style="dim blue",
            expand=True,
        )

    # ── Helpers ───────────────────────────────────────────────
    def _color_for(self, value: float) -> str:
        if value >= 95:
            return "bold red"
        if value >= 85:
            return "bold yellow"
        return "bold green"