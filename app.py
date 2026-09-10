#!/usr/bin/env python3
"""
Research Node — Stream Deck (Textual)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Controlador de ações no PC via SSH. Botões executam comandos
(backup, pipelines, abrir programas) através de um painel no
Termux do Moto E5.

Uso:
    python app.py

Requer: textual
Instale: python -m pip install textual  (ou bash install.sh)
"""
import sys
import io
import json
import subprocess
from functools import partial
from pathlib import Path

# Força UTF-8 no Windows para emojis funcionarem
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Log, Static

import config

SSH_CONFIG_FILE = Path.home() / ".research-node" / "ssh.json"


def load_ssh_config() -> dict:
    """Carrega a configução SSH do PC salvo em ~/.research-node/ssh.json."""
    try:
        return json.loads(SSH_CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_ssh_config(cfg: dict) -> None:
    """Salva a configuração SSH do PC."""
    SSH_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    SSH_CONFIG_FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8")


def run_on_pc(command: str, ssh_config: dict, timeout: int = 60) -> tuple:
    """Executa um comando no PC via SSH. Retorna (ok, output)."""
    host = ssh_config.get("host")
    user = ssh_config.get("user")
    if not host or not user:
        return False, "SSH não configurado — pressione SSH Setup."

    port = int(ssh_config.get("port") or 22)
    cmd = [
        "ssh",
        "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=10",
        "-p", str(port),
        f"{user}@{host}",
        command,
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        output = (proc.stdout + proc.stderr).strip()
        return proc.returncode == 0, output or "(sem saída)"
    except FileNotFoundError:
        return False, "ssh não encontrado — instale: pkg install openssh"
    except subprocess.TimeoutExpired:
        return False, "timeout: o comando demorou demais no PC"
    except Exception as e:
        return False, str(e)


class SetupScreen(Screen):
    """Tela de configuração da conexão SSH com o PC."""

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="setup"):
            yield Static("[b]⚡ Research Node — SSH Setup[/b]", classes="cat-title")
            yield Static("IP do PC (mesma rede Wi-Fi):", classes="field-label")
            yield Input(placeholder="192.168.1.100", id="pc_ip")
            yield Static("Usuário do PC:", classes="field-label")
            yield Input(placeholder="joao", id="pc_user")
            yield Static("Porta SSH (default 22):", classes="field-label")
            yield Input(placeholder="22", id="pc_port")
            yield Button("Connect", id="connect", variant="primary")
            yield Static("", id="setup_status")
        yield Footer()

    def on_mount(self) -> None:
        ssh = load_ssh_config()
        if ssh.get("host"):
            self.query_one("#pc_ip", Input).value = ssh["host"]
        if ssh.get("user"):
            self.query_one("#pc_user", Input).value = ssh["user"]
        if ssh.get("port"):
            self.query_one("#pc_port", Input).value = str(ssh["port"])

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id != "connect":
            return
        host = self.query_one("#pc_ip", Input).value.strip()
        user = self.query_one("#pc_user", Input).value.strip()
        port = self.query_one("#pc_port", Input).value.strip() or "22"
        status = self.query_one("#setup_status", Static)

        if not host or not user:
            status.update("[red]Preencha IP e usuário do PC.[/red]")
            return

        status.update("[yellow]Conectando ao PC...[/yellow]")
        event.button.disabled = True
        self.run_worker(
            partial(self._test_and_save, host, user, port),
            thread=True,
            name="ssh_connect",
        )

    def _test_and_save(self, host: str, user: str, port: str) -> None:
        cfg = {"host": host, "user": user, "port": int(port)}
        ok, output = run_on_pc("echo RN_OK", cfg, timeout=15)
        self.app.call_from_thread(self._finish, ok, output, cfg)

    def _finish(self, ok: bool, output: str, cfg: dict) -> None:
        status = self.query_one("#setup_status", Static)
        btn = self.query_one("#connect", Button)
        btn.disabled = False
        if ok:
            save_ssh_config(cfg)
            status.update("[green]Conectado! Abrindo Stream Deck...[/green]")
            self.app.switch_screen(StreamDeckScreen())
        else:
            status.update(f"[red]Falha: {output}[/red]")


class StreamDeckScreen(Screen):
    """Tela com botões que executam comandos no PC via SSH."""

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="deck"):
            with Horizontal(id="deck-top"):
                yield Button("SSH Setup", id="btn_setup", classes="deck-util")
                yield Button("Sair", id="btn_quit", classes="deck-util")
            for i, cat in enumerate(config.STREAM_DECK):
                yield Static(f"[b]{cat['category']}[/b]", classes="cat-title")
                with Horizontal():
                    for j, item in enumerate(cat["buttons"]):
                        yield Button(
                            item["label"],
                            id=f"btn_{i}_{j}",
                            classes="deck-btn",
                        )
            yield Log(id="output", classes="output-panel")
            yield Static(
                "[dim]Toque num botão para executar no PC via SSH.[/dim]",
                id="helpers",
            )
        yield Footer()

    def on_mount(self) -> None:
        self._ssh = load_ssh_config()
        if not self._ssh.get("host"):
            self.app.switch_screen(SetupScreen())
            return
        self.query_one("#output", Log).write(
            f"[dim]Conectado: {self._ssh.get('user')}@{self._ssh.get('host')}"
            f":{self._ssh.get('port', 22)}[/dim]"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        self.output = self.query_one("#output", Log)
        if bid == "btn_setup":
            self.app.switch_screen(SetupScreen())
            return
        if bid == "btn_quit":
            self.app.exit()
            return
        if not bid or not bid.startswith("btn_"):
            return

        try:
            _, i, j = bid.split("_")
            item = config.STREAM_DECK[int(i)]["buttons"][int(j)]
        except (ValueError, IndexError, KeyError):
            self.output.write("[red]Botão inválido em config.STREAM_DECK[/red]")
            return

        event.button.disabled = True
        self.output.write(f"[bold]▶ {item['label']}[/bold]  {item['command']}")
        self.run_worker(
            partial(self._execute, item["command"], item["label"], event.button),
            thread=True,
            name=f"cmd_{bid}",
        )

    def _execute(self, command: str, label: str, btn: Button) -> None:
        ok, output = run_on_pc(command, self._ssh)
        self.app.call_from_thread(self._finish, ok, output, label, btn)

    def _finish(self, ok: bool, output: str, label: str, btn: Button) -> None:
        btn.disabled = False
        if ok:
            self.output.write(f"[green]✓ {label} OK[/green]\n{output}")
        else:
            self.output.write(f"[red]✗ {label} falhou[/red]\n{output}")


class ResearchNodeApp(App):
    """App principal do Stream Deck."""

    TITLE = "Research Node"
    SUB_TITLE = "Moto E5 → PC Control"
    CSS_PATH = "styles.css"
    BINDINGS = [
        ("q", "quit", "Sair"),
        ("s", "setup", "SSH Setup"),
    ]

    def get_default_screen(self) -> Screen:
        # Textual monta a primeira tela por aqui — escolhe com base no
        # estado salvo do SSH. Sem config, cai na tela de setup.
        ssh = load_ssh_config()
        if ssh.get("host"):
            return StreamDeckScreen()
        return SetupScreen()

    def action_setup(self) -> None:
        self.switch_screen(SetupScreen())


if __name__ == "__main__":
    ResearchNodeApp().run()