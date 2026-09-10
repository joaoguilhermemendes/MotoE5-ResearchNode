#!/bin/bash
# ╔══════════════════════════════════════════════════════════╗
# ║  Research Node — SSH Setup (roda NO CELULAR no Termux)  ║
# ╚══════════════════════════════════════════════════════════╝
#
#  Uso:
#    cd ~/research-node
#    bash tools/ssh-setup.sh
#
#  Isso:
#    1. Instala o openssh
#    2. Pede pra você definir uma senha
#    3. Configura o sshd pra ligar automaticamente
#    4. Liga o servidor SSH agora
#    5. Mostra o IP e as instruções pro PC
#
set -e

GREEN='\033[0;32m'; CYAN='\033[0;36m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info() { echo -e "${CYAN}▸${NC} $1"; }
ok()   { echo -e "${GREEN}✓${NC} $1"; }
warn() { echo -e "${YELLOW}!${NC} $1"; }

echo ""
echo "⚡ SSH Setup — Research Node (Termux)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ── 1. Instala openssh ─────────────────────────────────────
info "Instalando openssh..."
pkg install -y openssh
ok "openssh instalado"

# ── 2. Define senha do usuário SSH ─────────────────────────
echo ""
warn "Agora defina uma SENHA para o usuário SSH do Termux."
warn "Coloque algo tipo '1234' ou 'moto5' (vai usar no PC)."
echo ""
info "Rodando 'passwd' (digite a senha 2x)..."
echo ""
passwd
echo ""
ok "Senha definida"

# ── 3. Prepara ~/.ssh ──────────────────────────────────────
mkdir -p "$HOME/.ssh" && chmod 700 "$HOME/.ssh"
touch "$HOME/.ssh/authorized_keys" && chmod 600 "$HOME/.ssh/authorized_keys"
ok "Pasta ~/.ssh pronta"

# ── 4. Auto-start do sshd ──────────────────────────────────
if grep -q "^sshd" "$HOME/.bashrc" 2>/dev/null; then
    ok "sshd já configurado no .bashrc"
else
    echo "sshd" >> "$HOME/.bashrc"
    ok "sshd vai ligar automaticamente ao abrir o Termux (.bashrc)"
fi

# ── 5. Liga o servidor agora ───────────────────────────────
info "Ligando sshd na porta 8022..."
if pkill -f "^sshd" 2>/dev/null; then
    sleep 1
fi
sshd
ok "sshd rodando na porta 8022"

# ── 6. Descobre IP do celular ──────────────────────────────
info "Descobrindo IP na rede Wi-Fi..."
IP=""
IP=$(getprop dhcp.wlan0.ipaddress 2>/dev/null) || true
[ -z "$IP" ] && IP=$(ip addr show wlan0 2>/dev/null | grep -oP 'inet \K[\d.]+' | head -1) || true
[ -z "$IP" ] && IP=$(ifconfig wlan0 2>/dev/null | grep -oP 'inet addr:\K[\d.]+' | head -1) || true

USERNAME=$(whoami)

# ── 7. Resumo final ────────────────────────────────────────
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✓ SSH pronto! Dados pra usar no PC:${NC}"
echo ""
echo "  IP do celular: ${CYAN}${IP:-[não detectou — veja note abaixo]}${NC}"
echo "  Usuário:       ${CYAN}${USERNAME}${NC}"
echo "  Porta:         ${CYAN}8022${NC}"
echo "  Senha:         a que você acabou de definir"
echo ""
echo "  No PC (PowerShell), rode:"
echo -e "     ${YELLOW}ssh ${USERNAME}@${IP:-IP_DO_CELULAR} -p 8022${NC}"
echo ""
echo "  Ou use nosso script do PC (gera chave + conecta):"
echo -e "     ${YELLOW}cd research-node; .\\tools\\ssh-connect.ps1 -PhoneIp ${IP:-IP_DO_CELULAR}${NC}"
echo ""

if [ -z "$IP" ]; then
    warn "Não consegui detectar o IP automaticamente."
    warn "Descubra em: Configurações → Wi-Fi → (rede) → IP"
    warn "Ou rode: ip addr show wlan0"
fi