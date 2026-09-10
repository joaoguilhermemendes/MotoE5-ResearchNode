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

### Monitorar PC remotamente via SSH

```bash
# No Termux, configure:
export RN_SSH_HOST=192.168.1.100
export RN_SSH_USER=joao
export RN_SSH_KEY=~/.ssh/id_rsa

# Ou edite config.py diretamente
```

## Estrutura

```
research-node/
├── research_node.py      # Entry point
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
- **psutil** (opcional) — métricas de sistema (fallback: /proc)
- **Termux** — terminal no Android
- **Bash** — scripts de pipeline

## License

MIT — faça o que quiser!
