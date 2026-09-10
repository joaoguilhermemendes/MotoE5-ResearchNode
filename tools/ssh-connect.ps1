<#
╔══════════════════════════════════════════════════════════╗
║  Research Node — SSH Connect (roda NO COMPUTADOR)       ║
╚══════════════════════════════════════════════════════════╝

  Conecta do PC ao celular (Moto E5 via Termux).

  Uso:
    .\tools\ssh-connect.ps1 -PhoneIp 192.168.1.50
    .\tools\ssh-connect.ps1 -PhoneIp 192.168.1.50 -User u0_a514
    .\tools\ssh-connect.ps1 -PhoneIp 192.168.1.50 -Port 8022 -NoKeyCopy
    .\tools\ssh-connect.ps1 -Scan            # procura o celular na rede

  Comportamento:
    1. Gera uma chave SSH no PC (se não existir)
    2. Copia a chave pública pro celular (pede senha 1x)
    3. Conecta via SSH (sem senha a partir de agora)
#>

param(
    [string]$PhoneIp = "",
    [string]$User = "",
    [int]$Port = 8022,
    [switch]$Scan,
    [switch]$NoKeyCopy
)

$ErrorActionPreference = "Stop"

# ── Helpers ──────────────────────────────────────────────
function Write-Info($msg)  { Write-Host "▸ $msg" -ForegroundColor Cyan }
function Write-Ok($msg)    { Write-Host "✓ $msg" -ForegroundColor Green }
function Write-WarnMsg($m) { Write-Host "! $m" -ForegroundColor Yellow }

function Test-SshPort([string]$HostName, [int]$PortNum) {
    # Testa se a porta SSH responde (com timeout curto)
    $client = New-Object Net.Sockets.TcpClient
    try {
        $result = $client.BeginConnect($HostName, $PortNum, $null, $null)
        $ok = $result.AsyncWaitHandle.WaitOne(400, $false)
        if ($ok) { $client.EndConnect($result); return $true }
        return $false
    } catch {
        return $false
    } finally {
        $client.Close()
    }
}

function Scan-Subnet([int]$PortNum) {
    # Varre o /24 local em paralelo procurando a porta SSH
    $localIp = (Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
        Where-Object { $_.IPAddress -notlike '169.*' -and $_.IPAddress -ne '127.0.0.1' } |
        Select-Object -First 1).IPAddress

    if (-not $localIp) {
        Write-WarnMsg "Não achei IP local da máquina. Digite o IP manualmente."
        return @()
    }

    $prefix = ($localIp -split '\.')[0..2] -join '.'
    Write-Info "Vasculhando $prefix.1-254 na porta $PortNum..."

    # Abre conexões em paralelo
    $clients = @()
    $results = @()
    foreach ($i in 1..254) {
        $target = "$prefix.$i"
        $c = New-Object Net.Sockets.TcpClient
        $ar = $c.BeginConnect($target, $PortNum, $null, $null)
        $clients += $c
        $results += $ar
    }

    $found = @()
    for ($i = 0; $i -lt $results.Count; $i++) {
        if ($results[$i].AsyncWaitHandle.WaitOne(400, $false)) {
            try {
                $clients[$i].EndConnect($results[$i])
                $found += ($prefix + "." + ($i + 1))
            } catch { }
        }
        $clients[$i].Close()
    }
    return $found
}

function Get-OrCreateKey {
    # Acha (ou cria) uma chave SSH no PC
    $keyDir = "$env:USERPROFILE\.ssh"
    $keys = Get-ChildItem -Path $keyDir -Filter "*.pub" -ErrorAction SilentlyContinue
    if ($keys) {
        return $keys[0].FullName
    }
    New-Item -ItemType Directory -Force -Path $keyDir | Out-Null
    $keyFile = "$keyDir\id_ed25519"
    Write-Info "Gerando chave SSH (ed25519)..."
    ssh-keygen -t ed25519 -f $keyFile -N '""' -q
    Write-Ok "Chave criada em $keyFile"
    return "$keyFile.pub"
}

# ── 1. Descobre IP ───────────────────────────────────────
if (-not $PhoneIp -and $Scan) {
    $candidates = Scan-Subnet $Port
    if ($candidates) {
        Write-Ok "Encontrei: $($candidates -join ', ')"
        $PhoneIp = $candidates[0]
    } else {
        Write-WarnMsg "Nenhuma porta 8022 aberta na rede."
        Write-WarnMsg "Confirme que rodou: bash tools/ssh-setup.sh no celular, ou rode `sshd` no Termux."
        exit 1
    }
}

if (-not $PhoneIp) {
    throw "Faltou -PhoneIp. Rode: .\tools\ssh-connect.ps1 -PhoneIp 192.168.1.50"
}

# ── 2. Testa se o alvo responde ──────────────────────────
Write-Info "Testando $PhoneIp : $Port ..."
if (-not (Test-SshPort $PhoneIp $Port)) {
    Write-WarnMsg "Porta $Port não responde em $PhoneIp."
    Write-WarnMsg "  1) No celular rode: sshd  (ou bash tools/ssh-setup.sh)"
    Write-WarnMsg "  2) Confira que celular e PC estão na MESMA rede Wi-Fi"
    exit 1
}
Write-Ok "Porta OK — sshd rodando em $PhoneIp"

# ── 3. Descobre usuário (se não passou) ──────────────────
if (-not $User) {
    $User = Read-Host "Usuário do Termux (no celular rode 'whoami')"
    if (-not $User) { throw "Usuário obrigatório." }
}

# ── 4. Gera/copia chave (one-time) ───────────────────────
if (-not $NoKeyCopy) {
    $pubKey = Get-OrCreateKey
    $content = Get-Content -Raw $pubKey | ForEach-Object { $_.TrimEnd() }
    Write-Info "Copiando chave pública pro celular..."
    Write-WarnMsg "Vai pedir a SENHA que você definiu no celular. Digite e Enter."
    Write-Host ""
    $cmd = "$content | ssh -p $Port $User@$PhoneIp `"mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys`""
    try {
        Invoke-Expression $cmd
        Write-Ok "Chave copiada. Próximas conexões sem senha!"
    } catch {
        Write-WarnMsg "Cópia de chave falhou (mas ainda dá pra conectar com senha)."
    }
}

# ── 5. Conecta no dashboard ──────────────────────────────
Write-Info "Conectando em $User@$PhoneIp : $Port ..."
Write-Host ""
ssh -t -p $Port "$User@$PhoneIp" "cd ~/research-node 2>/dev/null && python research_node.py || bash"