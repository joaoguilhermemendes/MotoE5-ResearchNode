# ⚡ Research Node

**Moto E5 Bioinfo Dashboard** — TUI para monitorar pipelines de bioinfo, métricas de sistema e automações.

```
┌───────────────────────────────────────────┐
│  ⚡ RESEARCH NODE     e5  Termux/Moto E5  │
├───────────────┬───────────────────────────┤
│     CPU       │   CPU / MEMORY HISTORY    │
│  [██████░░░░] │  CPU  ▂▃▅▇▆▅▄▃▂▃▅▆▇▅▄▃   │
│   45.2%       │  RAM  ▅▅▅▅▆▆▆▇▇▇▆▆▅▅▅▅   │
├───────────────┤                           │
│     RAM       │   avg 42.3% max 78.1%     │
│  [████░░░░░░] ├───────────────────────────┤
│  812/2048 MB  │   TOP PROCESSES           │
├───────────────┴───────────────────────────┤
│  DATA PIPELINES                           │
│  ● dengue_analysis    OK                  │
│  ● backup             OK                  │
│  ● github_sync        OK                  │
│  ● variant_calling    FAILED              │
├───────────────────────────────────────────┤
│  EVENT LOG                                │
│  14:32:01 variant_calling FAILED          │
│  14:31:45 dengue_analysis recovered → OK  │
└───────────────────────────────────────────┘
```

## Quick Start

### No Termux (Moto E5)

```bash
# 1. Instala o Termux (F-Droid)
# 2. Abra o Termux e rode:
pkg install git
git clone <seu-repo> ~/research-node
cd ~/research-node
bash install.sh

# 3. Roda o dashboard:
python research_node.py
```

### No PC (Linux/Mac)

```bash
git clone <seu-repo>
cd research-node
pip install -r requirements.txt
python research_node.py
```

## Modos de Uso

```bash
# Dashboard live (atualiza a cada 3s)
python research_node.py

# Apenas uma captura
python research_node.py --once

# Só verifica pipelines
python research_node.py --pipelines

# Refresh mais rápido (1s)
python research_node.py --refresh 1

# Sem cores (para logs)
python research_node.py --no-color > dashboard.log
```

## Configuração

Edite `config.py` para:

- **Adicionar pipelines** — adicione dicts na lista `PIPELINES`
- **Ajustar thresholds** — CPU/RAM alertas
- **SSH remoto** — monitorar o PC do celular
- **Intervalo de refresh**

### Exemplo de pipeline

```python
# Em config.py → PIPELINES
{
    "name": "my_pipeline",
    "command": "bash pipelines/check_my_pipeline.sh",  # exit 0=OK, 1=FAIL
    "run_cmd": "bash pipelines/run_my_pipeline.sh",    # opcional
    "category": "bioinfo",
    "enabled": True,
}
```

### SSH: PC → Celular

Configure SSH para rodar o dashboard no celular **pelo computador**.

**No celular (Termux):**
```bash
cd ~/research-node
bash tools/ssh-setup.sh
```

**No computador (PowerShell):**
```powershell
cd research-node
.\tools\ssh-connect.ps1 -PhoneIp 192.168.1.50
# Na primeira vez, vai pedir a senha do celular (1x só)
# Depois conecta sem senha automaticamente
```

Procura o celular automaticamente:
```powershell
.\tools\ssh-connect.ps1 -Scan
```

### Monitorar PC remotamente

```bash
export RN_SSH_HOST=192.168.1.100
export RN_SSH_USER=joao
export RN_SSH_KEY=~/.ssh/id_rsa
```

## Stream Deck (controle o PC com um toque)

Rodar `python app.py` abre um painel com **botões que executam comandos no seu PC via SSH** (backup, pipelines, abrir programas) direto do Termux.

```bash
# No Termux:
python app.py
# 1ª vez: tela de setup → IP do PC, usuário e porta SSH
# Depois: clique nos botões para rodar comandos no PC
```

### Configurar o PC (uma vez)

- Instale o **OpenSSH Server** no Windows (Configurações → Apps → Recursos Opcionais).
- Garanta que `sshd` está rodando (Porta 22).
- O usuário/senha é o mesmo da conta do Windows (ou monte chaves SSH).

### Editar os botões

Os botões ficam em `config.py` → `STREAM_DECK`. Cada botão tem `label` (nome) e `command` (comando rodado NO PC):

```python
STREAM_DECK = [
    {
        "category": "Automation",
        "buttons": [
            {"label": "Backup", "command": "powershell -NoProfile -Command Write-Host backup-ok"},
        ],
    },
]
```

## Estrutura

```
research-node/
├── research_node.py      # Entry point (dashboard Rich)
├── app.py                # Stream Deck (Textual) — controla o PC via SSH
├── styles.css            # Estilos do app.py
├── config.py             # Configuração (edite este!)
├── collectors/
│   ├── system.py         # CPU, RAM, uptime, processos
│   └── pipelines.py      # Status dos pipelines
├── ui/
│   └── dashboard.py      # Rich TUI dashboard
├── pipelines/            # Scripts de check/run
│   ├── check_dengue.sh
│   ├── run_dengue.sh
│   ├── check_backup.sh
│   ├── run_backup.sh
│   ├── check_github.sh
│   ├── run_github.sh
│   ├── check_variant.sh
│   ├── run_variant.sh
│   ├── check_qc.sh
│   └── run_qc.sh
├── data/                 # Dados e histórico
├── tools/                # Scripts auxiliares
│   ├── ssh-setup.sh      # Configura SSH no Termux
│   └── ssh-connect.ps1   # Conecta do PC ao celular
├── install.sh            # Instalador Termux
└── requirements.txt
```

## Pipelines Incluídos

| Pipeline | Categoria | Descrição |
|----------|-----------|-----------|
| `dengue_analysis` | bioinfo | Análise de dados de dengue |
| `backup` | automation | Backup automático |
| `github_sync` | automation | Sincronização de repos |
| `variant_calling` | bioinfo | Chamada de variantes (VCF) |
| `quality_check` | bioinfo | QC com FastQC (desativado) |

## Personalize

### Adicionar seus próprios pipelines

1. Crie `pipelines/check_meupipeline.sh`:
```bash
#!/bin/bash
# Seu health check aqui
if [condição]; then
    echo "OK: tudo certo"
    exit 0
else
    echo "FAIL: algo errado"
    exit 1
fi
```

2. Crie `pipelines/run_meupipeline.sh`:
```bash
#!/bin/bash
# Seu pipeline aqui
python3 meu_pipeline.py --input dados.fastq
```

3. Adicione em `config.py`:
```python
{
    "name": "meupipeline",
    "command": "bash pipelines/check_meupipeline.sh",
    "run_cmd": "bash pipelines/run_meupipeline.sh",
    "category": "bioinfo",
    "enabled": True,
}
```

## Tech Stack

- **Python 3** — linguagem principal
- **Rich** — TUI framework (termos, painéis, layouts)
- **Textual** — Stream Deck (botões, telas, worker threads)
- **psutil** (opcional) — métricas de sistema (fallback: /proc)
- **Termux** — terminal no Android
- **Bash** — scripts de pipeline

## License

MIT — faça o que quiser!
