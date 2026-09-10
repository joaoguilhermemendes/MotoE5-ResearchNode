"""
Research Node — Pipeline Status Monitor
Monitora o status de pipelines de bioinfo e automação.
"""
import os
import time
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum


class PipelineStatus(Enum):
    OK = "ok"
    FAILED = "failed"
    WARNING = "warning"
    DISABLED = "disabled"
    UNKNOWN = "unknown"

    @property
    def icon(self) -> str:
        return {
            PipelineStatus.OK: "[green]●[/green]",
            PipelineStatus.FAILED: "[red]●[/red]",
            PipelineStatus.WARNING: "[yellow]●[/yellow]",
            PipelineStatus.DISABLED: "[dim]○[/dim]",
            PipelineStatus.UNKNOWN: "[dim]?[/dim]",
        }[self]

    @property
    def label(self) -> str:
        return {
            PipelineStatus.OK: "[green]OK[/green]",
            PipelineStatus.FAILED: "[red]FAILED[/red]",
            PipelineStatus.WARNING: "[yellow]WARN[/yellow]",
            PipelineStatus.DISABLED: "[dim]OFF[/dim]",
            PipelineStatus.UNKNOWN: "[dim]?[/dim]",
        }[self]


@dataclass
class PipelineResult:
    """Resultado do check de um pipeline."""
    name: str
    status: PipelineStatus = PipelineStatus.UNKNOWN
    category: str = "general"
    last_check: float = 0.0
    last_run: float = 0.0
    error_msg: str = ""
    enabled: bool = True

    @property
    def last_check_str(self) -> str:
        if self.last_check == 0:
            return "never"
        elapsed = time.time() - self.last_check
        if elapsed < 60:
            return f"{int(elapsed)}s ago"
        elif elapsed < 3600:
            return f"{int(elapsed / 60)}m ago"
        else:
            return f"{int(elapsed / 3600)}h ago"

    @property
    def last_run_str(self) -> str:
        if self.last_run == 0:
            return "never"
        dt = datetime.fromtimestamp(self.last_run)
        return dt.strftime("%H:%M")


class PipelineMonitor:
    """Monitora pipelines definidos na configuração."""

    def __init__(self, pipeline_defs: list):
        """
        pipeline_defs: lista de dicts do config.PIPELINES
        """
        self.definitions = {p["name"]: p for p in pipeline_defs}
        self.results: dict[str, PipelineResult] = {}
        self.events: list[str] = []
        self._init_results()

    def _init_results(self) -> None:
        """Inicializa resultados para todos os pipelines."""
        for name, defn in self.definitions.items():
            enabled = defn.get("enabled", True)
            self.results[name] = PipelineResult(
                name=name,
                status=PipelineStatus.DISABLED if not enabled else PipelineStatus.UNKNOWN,
                category=defn.get("category", "general"),
                enabled=enabled,
            )

    def check_all(self) -> dict:
        """
        Verifica o status de todos os pipelines habilitados.
        Retorna dict com nome -> PipelineResult.
        """
        for name, defn in self.definitions.items():
            if not defn.get("enabled", True):
                continue
            self._check_pipeline(name, defn)
        return self.results

    def _check_pipeline(self, name: str, defn: dict) -> None:
        """Executa o check command de um pipeline."""
        result = self.results[name]
        command = defn.get("command", "")

        if not command:
            result.status = PipelineStatus.UNKNOWN
            return

        try:
            proc = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
            )
            result.last_check = time.time()

            if proc.returncode == 0:
                if result.status != PipelineStatus.OK:
                    self._log_event(f"{name} recovered → OK")
                result.status = PipelineStatus.OK
                result.error_msg = ""
            elif proc.returncode == 1:
                if result.status != PipelineStatus.FAILED:
                    self._log_event(f"{name} FAILED")
                result.status = PipelineStatus.FAILED
                result.error_msg = proc.stderr.strip()[:100] if proc.stderr else ""
            else:
                if result.status != PipelineStatus.WARNING:
                    self._log_event(f"{name} WARNING (exit {proc.returncode})")
                result.status = PipelineStatus.WARNING
                result.error_msg = proc.stderr.strip()[:100] if proc.stderr else ""

        except subprocess.TimeoutExpired:
            result.status = PipelineStatus.WARNING
            result.error_msg = "timeout (>30s)"
            result.last_check = time.time()
        except Exception as e:
            result.status = PipelineStatus.FAILED
            result.error_msg = str(e)[:100]
            result.last_check = time.time()

    def run_pipeline(self, name: str) -> bool:
        """
        Executa o run_cmd de um pipeline.
        Retorna True se o comando foi iniciado com sucesso.
        """
        defn = self.definitions.get(name)
        if not defn:
            return False

        run_cmd = defn.get("run_cmd")
        if not run_cmd:
            self._log_event(f"{name}: no run_cmd defined")
            return False

        try:
            self._log_event(f"{name}: started manually")
            # Executa em background (não bloqueia o dashboard)
            subprocess.Popen(
                run_cmd,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self.results[name].last_run = time.time()
            return True
        except Exception as e:
            self._log_event(f"{name}: run failed — {e}")
            return False

    def _log_event(self, msg: str) -> None:
        """Adiciona um evento ao log."""
        ts = datetime.now().strftime("%H:%M:%S")
        self.events.append(f"[dim]{ts}[/dim] {msg}")
        # Mantém apenas os últimos N eventos
        if len(self.events) > 20:
            self.events = self.events[-20:]

    @property
    def summary(self) -> dict:
        """Retorna contadores de status."""
        counts = {s: 0 for s in PipelineStatus}
        for r in self.results.values():
            counts[r.status] += 1
        return counts

    @property
    def ordered_results(self) -> list:
        """Retorna resultados ordenados: FAILED > WARNING > OK > DISABLED."""
        order = [
            PipelineStatus.FAILED,
            PipelineStatus.WARNING,
            PipelineStatus.UNKNOWN,
            PipelineStatus.OK,
            PipelineStatus.DISABLED,
        ]
        return sorted(
            self.results.values(),
            key=lambda r: order.index(r.status) if r.status in order else 99,
        )
