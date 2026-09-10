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
RED='\033[0;31m'
NC='\033[0m'

info()  { echo -e "${CYAN}▸${NC} $1"; }
ok()    { echo -e "${GREEN}✓${NC} $1"; }
warn()  { echo -e "${YELLOW}!${NC} $1"; }
fail()  { echo -e "${RED}✗${NC} $1"; }

# ── 1. Atualiza pacotes ───────────────────────────────
info "Atualizando pacotes do sistema..."
pkg update -y && pkg upgrade -y

# ── 2. Instala dependências do sistema ────────────────
info "Instalando dependências do sistema..."
pkg install -y python python-pip git curl

# ── 3. Instala dependências Python ────────────────────
info "Instalando dependências Python (rich, psutil)..."
echo "  (pode demorar no primeiro install...)"
echo ""

# Usa python -m pip (mais confiável que pip direto no Termux)
python -m pip install --upgrade pip
python -m pip install rich psutil

# ── 4. Torna scripts executáveis ──────────────────────
info "Configurando scripts..."
chmod +x research_node.py
chmod +x pipelines/*.sh

# ── 5. Cria diretórios de dados ───────────────────────
info "Criando diretórios..."
mkdir -p data
mkdir -p ~/data/dengue
mkdir -p ~/data/variants
mkdir -p ~/data/qc
mkdir -p ~/backups
mkdir -p ~/repos

# ── 6. Verifica instalação ────────────────────────────
echo ""
info "Verificando instalação..."

RICH_OK=false
if python -c "import rich" 2>/dev/null; then
    ok "rich OK"
    RICH_OK=true
else
    fail "rich NÃO instalado"
fi

PSUTIL_OK=false
if python -c "import psutil" 2>/dev/null; then
    ok "psutil OK"
    PSUTIL_OK=true
else
    warn "psutil não instalado (ok, usa /proc)"
fi

if [ "$RICH_OK" = false ]; then
    echo ""
    fail "ERRO: rich não instalado. Roda manualmente:"
    echo "    python -m pip install rich psutil"
    echo ""
    exit 1
fi

# ── 7. Testa o dashboard ──────────────────────────────
echo ""
info "Testando dashboard (modo --once)..."
echo ""
python research_node.py --once

# ── Pronto! ───────────────────────────────────────────
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✓ Research Node instalado!${NC}"
echo ""
echo "  Para rodar:"
echo "    python research_node.py"
echo ""
echo "  Para ver apenas pipelines:"
echo "    python research_node.py --pipelines"
echo ""
echo "  Uma captura e sair:"
echo "    python research_node.py --once"
echo ""
echo -e "${CYAN}⚡ Happy hacking!${NC}"
echo ""
