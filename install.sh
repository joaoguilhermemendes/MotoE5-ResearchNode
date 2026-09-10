#!/bin/bash
# ╔══════════════════════════════════════════════════════════════╗
# ║  Research Node — Instalador para Termux (Moto E5)          ║
# ╚══════════════════════════════════════════════════════════════╝
#
# Roda este script no Termux para instalar tudo:
#   bash install.sh
#
# Pré-requisitos:
#   - Termux instalado (F-Droid ou GitHub)
#   - Conexão com internet
#

set -e

echo ""
echo "⚡ Research Node — Installer"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ── Cores ──────────────────────────────────────────────
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${CYAN}▸${NC} $1"; }
ok()    { echo -e "${GREEN}✓${NC} $1"; }
warn()  { echo -e "${YELLOW}!${NC} $1"; }

# ── 1. Atualiza pacotes ───────────────────────────────
info "Atualizando pacotes..."
pkg update -y 2>/dev/null || apt update -y

# ── 2. Instala dependências do sistema ────────────────
info "Instalando dependências do sistema..."
pkg install -y python git curl 2>/dev/null || true

# ── 3. Instala pip se não existe ──────────────────────
if ! command -v pip &>/dev/null; then
    info "Instalando pip..."
    python -m ensurepip --upgrade 2>/dev/null || {
        curl -sS https://bootstrap.pypa.io/get-pip.py | python
    }
fi

# ── 4. Instala dependências Python ────────────────────
info "Instalando dependências Python..."
pip install --upgrade pip 2>/dev/null || true
pip install rich psutil 2>/dev/null || pip3 install rich psutil

# ── 5. Torna scripts executáveis ──────────────────────
info "Configurando scripts..."
chmod +x research_node.py
chmod +x pipelines/*.sh

# ── 6. Cria diretórios de dados ───────────────────────
mkdir -p data
mkdir -p ~/data/dengue
mkdir -p ~/data/variants
mkdir -p ~/data/qc
mkdir -p ~/backups
mkdir -p ~/repos

# ── 7. Verifica instalação ────────────────────────────
echo ""
info "Verificando instalação..."
python -c "import rich; print(f'  rich {rich.__version__}')" 2>/dev/null && ok "rich OK" || warn "rich não instalado"
python -c "import psutil; print(f'  psutil {psutil.__version__}')" 2>/dev/null && ok "psutil OK" || warn "psutil não instalado (OK, usa /proc)"

# ── 8. Testa o dashboard ──────────────────────────────
echo ""
info "Testando dashboard (modo --once)..."
echo ""
python research_node.py --once 2>/dev/null || {
    warn "Erro ao rodar. Verifique os erros acima."
}

# ── Pronto! ───────────────────────────────────────────
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✓ Research Node instalado!${NC}"
echo ""
echo "  Para rodar:"
echo "    python research_node.py"
echo ""
echo "  Para rodar e ver apenas pipelines:"
echo "    python research_node.py --pipelines"
echo ""
echo "  Para rodar uma vez e sair:"
echo "    python research_node.py --once"
echo ""
echo "  ParaSSH do PC para o celular:"
echo "    ssh -p 8022 user@<ip-do-celular>"
echo "    cd ~/research-node && python research_node.py"
echo ""
echo -e "${CYAN}⚡ Happy hacking!${NC}"
echo ""
