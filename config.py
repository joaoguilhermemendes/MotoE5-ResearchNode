"""
Research Node — Configuração
Edita este arquivo para adicionar seus pipelines de bioinfo/automação.
"""
import os
from pathlib import Path

# ─── Diretórios ──────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

HISTORY_FILE = DATA_DIR / "metrics_history.json"
EVENT_LOG_FILE = DATA_DIR / "events.log"

# ─── Dashboard ───────────────────────────────────────────────
REFRESH_INTERVAL = 3          # segundos entre atualizações
HISTORY_MAX_POINTS = 60       # pontos no gráfico de histórico (≈3 min a 3s)
EVENT_LOG_MAX = 8             # quantas linhas de eventos mostrar

# ─── Pipelines ───────────────────────────────────────────────
# Adicione seus pipelines aqui. Cada pipeline é um dict com:
#   name      → nome exibido no dashboard
#   command   → comando bash para verificar status (exit 0 = OK)
#   run_cmd   → (opcional) comando para executar o pipeline
#   category  → "bioinfo" | "automation" | "backup" | custom
#   enabled   → True/False
#
# O command deve retornar exit code 0 = OK, 1 = FAILED, outro = WARNING.
# Use "echo ok" como placeholder até criar os scripts reais.

PIPELINES = [
    {
        "name": "dengue_analysis",
        "command": "bash pipelines/check_dengue.sh",
        "run_cmd": "bash pipelines/run_dengue.sh",
        "category": "bioinfo",
        "enabled": True,
    },
    {
        "name": "backup",
        "command": "bash pipelines/check_backup.sh",
        "run_cmd": "bash pipelines/run_backup.sh",
        "category": "automation",
        "enabled": True,
    },
    {
        "name": "github_sync",
        "command": "bash pipelines/check_github.sh",
        "run_cmd": "bash pipelines/run_github.sh",
        "category": "automation",
        "enabled": True,
    },
    {
        "name": "variant_calling",
        "command": "bash pipelines/check_variant.sh",
        "run_cmd": "bash pipelines/run_variant.sh",
        "category": "bioinfo",
        "enabled": True,
    },
    {
        "name": "quality_check",
        "command": "bash pipelines/check_qc.sh",
        "run_cmd": "bash pipelines/run_qc.sh",
        "category": "bioinfo",
        "enabled": False,  # ative quando precisar
    },
]

# ─── SSH Remoto (pc_monitor) ────────────────────────────────
# Para monitorar o PC remotamente via SSH, preencha:
REMOTE_SSH_HOST = os.environ.get("RN_SSH_HOST", "")
REMOTE_SSH_USER = os.environ.get("RN_SSH_USER", "")
REMOTE_SSH_KEY = os.environ.get("RN_SSH_KEY", "")  # caminho da chave
REMOTE_SSH_INTERVAL = 30  # segundos entre polls do PC remoto

# ─── Alertas ─────────────────────────────────────────────────
CPU_WARN_THRESHOLD = 80       # % para alerta amarelo
CPU_CRIT_THRESHOLD = 95       # % para alerta vermelho
RAM_WARN_THRESHOLD = 75       # %
RAM_CRIT_THRESHOLD = 90       # %

# ─── Estilo ──────────────────────────────────────────────────
DASHBOARD_TITLE = "RESEARCH NODE"
DASHBOARD_SUBTITLE = "Moto E5 — Bioinfo & Automation Hub"
