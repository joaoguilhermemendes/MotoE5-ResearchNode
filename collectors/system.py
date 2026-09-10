"""
Research Node — System Metrics Collector
Coleta CPU, RAM, uptime, e processos do sistema.
Funciona tanto no Termux (Android) quanto em Linux desktop.
"""
import os
import time
import subprocess
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SystemMetrics:
    """Snapshot de métricas do sistema."""
    cpu_percent: float = 0.0
    ram_percent: float = 0.0
    ram_used_mb: float = 0.0
    ram_total_mb: float = 0.0
    uptime_seconds: int = 0
    hostname: str = ""
    platform: str = ""
    top_processes: list = field(default_factory=list)
    timestamp: float = 0.0

    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()

    @property
    def uptime_str(self) -> str:
        """Uptime formatado como 'Xd HHh MMm'."""
        delta = timedelta(seconds=self.uptime_seconds)
        days = delta.days
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        if days > 0:
            return f"{days}d {hours:02d}h {minutes:02d}m"
        elif hours > 0:
            return f"{hours}h {minutes:02d}m"
        else:
            return f"{minutes}m"

    @property
    def cpu_bar(self) -> str:
        """Barra visual de CPU."""
        filled = int(self.cpu_percent / 5)
        return f"[{'█' * filled}{'░' * (20 - filled)}] {self.cpu_percent:.1f}%"

    @property
    def ram_bar(self) -> str:
        """Barra visual de RAM."""
        filled = int(self.ram_percent / 5)
        used = f"{self.ram_used_mb:.0f}MB"
        total = f"{self.ram_total_mb:.0f}MB"
        return f"[{'█' * filled}{'░' * (20 - filled)}] {used}/{total}"


class SystemCollector:
    """Coleta métricas do sistema de forma multi-plataforma."""

    def __init__(self):
        self._prev_cpu_idle = 0
        self._prev_cpu_total = 0
        self._is_termux = self._detect_termux()

    def _detect_termux(self) -> bool:
        """Detecta se está rodando no Termux."""
        return (
            os.environ.get("TERMUX_VERSION") is not None
            or "/data/data/com.termux" in os.environ.get("PREFIX", "")
            or os.path.exists("/data/data/com.termux/files/usr/bin/bash")
        )

    def collect(self) -> SystemMetrics:
        """Coleta todas as métricas do sistema."""
        metrics = SystemMetrics()
        metrics.hostname = self._get_hostname()
        metrics.platform = self._get_platform()
        metrics.cpu_percent = self._get_cpu_percent()
        metrics.ram_percent, metrics.ram_used_mb, metrics.ram_total_mb = self._get_ram()
        metrics.uptime_seconds = self._get_uptime()
        metrics.top_processes = self._get_top_processes(5)
        return metrics

    def _get_hostname(self) -> str:
        """Obtém o hostname do sistema."""
        try:
            return subprocess.check_output(
                ["hostname"], timeout=3, text=True
            ).strip()
        except Exception:
            return os.environ.get("HOSTNAME", "unknown")

    def _get_platform(self) -> str:
        """Identifica a plataforma."""
        if self._is_termux:
            # Tenta pegar modelo do dispositivo Android
            try:
                model = subprocess.check_output(
                    ["getprop", "ro.product.model"],
                    timeout=3, text=True
                ).strip()
                return f"Termux/{model}"
            except Exception:
                return "Termux/Android"
        try:
            return subprocess.check_output(
                ["uname", "-sr"], timeout=3, text=True
            ).strip()
        except Exception:
            return "Linux"

    def _get_cpu_percent(self) -> float:
        """Calcula CPU% lendo /proc/stat (funciona no Termux/Linux)."""
        try:
            with open("/proc/stat", "r") as f:
                line = f.readline()
            parts = line.split()
            # user, nice, system, idle, iowait, irq, softirq, steal
            values = [int(x) for x in parts[1:9]]
            idle = values[3] + values[4]  # idle + iowait
            total = sum(values)

            diff_idle = idle - self._prev_cpu_idle
            diff_total = total - self._prev_cpu_total

            self._prev_cpu_idle = idle
            self._prev_cpu_total = total

            if diff_total == 0:
                return 0.0

            cpu_percent = (1.0 - diff_idle / diff_total) * 100.0
            return max(0.0, min(100.0, cpu_percent))
        except FileNotFoundError:
            # Fallback para psutil se disponível
            return self._get_cpu_psutil()
        except Exception:
            return 0.0

    def _get_cpu_psutil(self) -> float:
        """Fallback: CPU via psutil."""
        try:
            import psutil
            return psutil.cpu_percent(interval=0.1)
        except ImportError:
            return 0.0

    def _get_ram(self) -> tuple:
        """ Lê /proc/meminfo para RAM. Retorna (percent, used_mb, total_mb)."""
        try:
            with open("/proc/meminfo", "r") as f:
                lines = f.readlines()

            mem = {}
            for line in lines:
                parts = line.split()
                key = parts[0].rstrip(":")
                value = int(parts[1])  # em kB
                mem[key] = value

            total = mem.get("MemTotal", 1)
            available = mem.get("MemAvailable", mem.get("MemFree", 0))
            used = total - available

            percent = (used / total) * 100 if total > 0 else 0
            used_mb = used / 1024
            total_mb = total / 1024

            return percent, used_mb, total_mb
        except Exception:
            return self._get_ram_psutil()

    def _get_ram_psutil(self) -> tuple:
        """Fallback: RAM via psutil."""
        try:
            import psutil
            mem = psutil.virtual_memory()
            return mem.percent, mem.used / (1024 * 1024), mem.total / (1024 * 1024)
        except ImportError:
            return 0.0, 0.0, 0.0

    def _get_uptime(self) -> int:
        """Uptime em segundos (multi-plataforma)."""
        # Linux/Termux: /proc/uptime
        try:
            with open("/proc/uptime", "r") as f:
                return int(float(f.readline().split()[0]))
        except Exception:
            pass

        # Fallback: psutil (Windows e Linux)
        try:
            import psutil
            import time
            return int(time.time() - psutil.boot_time())
        except Exception:
            pass

        # Fallback: uptime -s (Linux)
        try:
            output = subprocess.check_output(
                ["uptime", "-s"], timeout=3, text=True
            ).strip()
            boot_time = datetime.strptime(output, "%Y-%m-%d %H:%M:%S")
            return int((datetime.now() - boot_time).total_seconds())
        except Exception:
            return 0

    def _get_top_processes(self, n: int = 5) -> list:
        """Lista os N processos que mais consomem CPU."""
        # Linux/Termux: via /proc ou ps
        if os.path.exists("/proc"):
            try:
                output = subprocess.check_output(
                    ["ps", "-eo", "pid,pcpu,pmem,comm", "--sort=-pcpu"],
                    timeout=5, text=True
                )
                lines = output.strip().split("\n")
                processes = []
                for line in lines[1:n + 1]:  # pula header
                    parts = line.split(None, 3)
                    if len(parts) >= 4:
                        processes.append({
                            "pid": parts[0],
                            "cpu": float(parts[1]),
                            "mem": float(parts[2]),
                            "name": parts[3][:20],
                        })
                if processes:
                    return processes
            except Exception:
                pass

        # Fallback: psutil (Windows/Linux)
        try:
            import psutil

            # Seed de cpu_percent (primeira chamada retorna 0)
            for proc in psutil.process_iter():
                try:
                    proc.cpu_percent()
                except Exception:
                    pass

            processes = []
            # Normaliza por número de cores (psutil soma por-core)
            cores = psutil.cpu_count() or 1
            for proc in sorted(
                psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]),
                key=lambda p: (p.info.get("cpu_percent") or 0) / cores,
                reverse=True,
            )[:n]:
                info = proc.info
                processes.append({
                    "pid": str(info["pid"]),
                    "cpu": float((info.get("cpu_percent") or 0) / cores),
                    "mem": float(info.get("memory_percent") or 0),
                    "name": (info.get("name") or "?")[:20],
                })
            return processes
        except Exception:
            return []
