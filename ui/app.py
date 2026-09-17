import os
import time
from pathlib import Path

from rich import box
from rich.align import Align
from rich.console import Console, Group
from rich.panel import Panel
from rich.progress import (
    BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
)
from rich.table import Table
from rich.text import Text

from core.wordlist import load_wordlist
from core.auditor import audit_passwords, audit_usernames, recent_results
from core.ssh import test_credentials

console = Console()
BASE = Path(__file__).resolve().parent.parent

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def banner():
    title = Text()
    title.append("SSH ", style="bold cyan")
    title.append("AUDITOR", style="bold white")
    title.append("  v1.0", style="dim")
    subtitle = Text("Authorized Security Testing Console", style="bright_black")
    console.print(Panel(Align.center(Group(title, subtitle)), box=box.DOUBLE, padding=(1, 2)))

def pause():
    console.input("\n[dim]Press ENTER to continue...[/dim]")

def ask(prompt, default=None, secret=False):
    suffix = f" [{default}]" if default is not None else ""
    if secret:
        return console.input(f"[bold cyan]{prompt}{suffix}:[/bold cyan] ", password=True) or (default or "")
    return console.input(f"[bold cyan]{prompt}{suffix}:[/bold cyan] ") or (default or "")

def target_config():
    clear(); banner()
    table = Table(title="Target Configuration", box=box.ROUNDED)
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")
    host = ask("Target IP / hostname")
    port = int(ask("SSH port", 22))
    timeout = float(ask("Timeout (seconds)", 5))
    delay = float(ask("Delay between attempts", 0.5))
    max_attempts = int(ask("Maximum attempts (0 = wordlist)", 0))
    table.add_row("Target", f"{host}:{port}")
    table.add_row("Timeout", str(timeout))
    table.add_row("Delay", str(delay))
    table.add_row("Max attempts", str(max_attempts or "Unlimited (wordlist size)"))
    console.print(table)
    return host, port, timeout, delay, max_attempts

def connection_test():
    host, port, timeout, _, _ = target_config()
    username = ask("Username")
    password = ask("Password", secret=True)
    clear(); banner()
    with console.status("[bold cyan]Connecting to SSH server...[/bold cyan]", spinner="dots"):
        status, error = test_credentials(host, port, username, password, timeout)
    if status == "success":
        console.print(Panel("[bold green]✓ SSH authentication accepted[/bold green]", box=box.DOUBLE))
    elif status == "failed":
        console.print(Panel("[bold yellow]✗ Authentication rejected[/bold yellow]", box=box.ROUNDED))
    else:
        console.print(Panel(f"[bold red]Connection error:[/bold red] {error}", box=box.ROUNDED))
    pause()

def run_audit(mode):
    host, port, timeout, delay, max_attempts = target_config()
    if mode == "password":
        username = ask("Username")
        wordlist = ask("Password wordlist", str(BASE / "wordlists" / "passwords.txt"))
        label = "PASSWORD AUDIT"
    else:
        password = ask("Password", secret=True)
        wordlist = ask("Username wordlist", str(BASE / "wordlists" / "users.txt"))
        label = "USERNAME AUDIT"

    try:
        items = load_wordlist(wordlist)
    except FileNotFoundError:
        console.print(f"[bold red]Wordlist not found:[/bold red] {wordlist}")
        pause(); return
    if not items:
        console.print("[bold red]Wordlist is empty.[/bold red]")
        pause(); return

    clear(); banner()
    console.print(Panel(
        f"[cyan]Target:[/cyan] {host}:{port}\n"
        f"[cyan]Mode:[/cyan] {label}\n"
        f"[cyan]Candidates:[/cyan] {len(items)}",
        title=label, box=box.ROUNDED
    ))

    progress = Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        TimeElapsedColumn(),
    )
    task = progress.add_task("Testing credentials", total=min(max_attempts, len(items)) if max_attempts else len(items))

    last = {"status": ""}

    def on_attempt(idx, total, user, pwd, status, error):
        progress.update(task, completed=idx, description=f"Testing {user}")
        last["status"] = status

    with progress:
        if mode == "password":
            result = audit_passwords(host, port, username, items, timeout, delay, max_attempts, on_attempt)
        else:
            result = audit_usernames(host, port, password, items, timeout, delay, max_attempts, on_attempt)

    if result["status"] == "success":
        console.print(Panel(
            f"[bold green]✓ VALID CREDENTIALS FOUND[/bold green]\n\n"
            f"Target   : {host}:{port}\n"
            f"Username : {result['username']}\n"
            f"Password : {result['password']}\n"
            f"Attempts : {result['attempts']}",
            box=box.DOUBLE
        ))
    elif result["status"] == "error":
        console.print(Panel(f"[bold red]Stopped due to connection error[/bold red]\n{result.get('error','')}", box=box.ROUNDED))
    else:
        console.print(Panel(
            f"[yellow]No valid credentials found.[/yellow]\nAttempts: {result['attempts']}",
            box=box.ROUNDED
        ))
    pause()

def results():
    clear(); banner()
    rows = recent_results()
    table = Table(title="Recent Audit Results", box=box.SIMPLE_HEAVY)
    table.add_column("Time", style="dim")
    table.add_column("Target")
    table.add_column("Status")
    table.add_column("Attempts")
    for p in rows[:12]:
        import json
        data = json.loads(p.read_text(encoding="utf-8"))
        status = data.get("status", "?")
        style = "green" if status == "success" else "yellow" if status == "not_found" else "red"
        table.add_row(
            data.get("timestamp","")[:19].replace("T"," "),
            data.get("target",""),
            f"[{style}]{status}[/{style}]",
            str(data.get("attempts",""))
        )
    if not rows:
        console.print("[dim]No audit results yet.[/dim]")
    else:
        console.print(table)
    pause()

def main_menu():
    while True:
        clear(); banner()
        table = Table(box=box.ROUNDED, show_header=False, padding=(0, 2))
        table.add_column("Key", style="bold cyan", width=6)
        table.add_column("Operation", style="white")
        table.add_row("[1]", "Password Audit")
        table.add_row("[2]", "Username Audit")
        table.add_row("[3]", "SSH Connection Test")
        table.add_row("[4]", "View Recent Results")
        table.add_row("[0]", "Exit")
        console.print(Align.center(table))
        choice = console.input("\n[bold cyan]Select operation ► [/bold cyan]").strip().lower()

        if choice == "1": run_audit("password")
        elif choice == "2": run_audit("username")
        elif choice == "3": connection_test()
        elif choice == "4": results()
        elif choice == "0":
            clear()
            console.print(Panel("[bold cyan]Session closed. Stay authorized.[/bold cyan]", box=box.ROUNDED))
            break
        else:
            console.print("[red]Invalid option.[/red]")
            time.sleep(0.7)

def run():
    main_menu()
