import json
import os
import time
from pathlib import Path

from rich import box
from rich.align import Align
from rich.console import Console, Group
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from core.auditor import audit_passwords, audit_usernames, recent_results
from core.ssh import test_credentials
from core.wordlist import load_wordlist

console = Console()
BASE = Path(__file__).resolve().parent.parent
DEFAULT_PASSWORD_LIST = BASE / "wordlists" / "passwords.txt"
DEFAULT_USERNAME_LIST = BASE / "wordlists" / "usernames.txt"


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def banner():
    title = Text()
    title.append("SSH ", style="bold cyan")
    title.append("AUDITOR", style="bold white")
    title.append("  v1.1", style="dim")
    subtitle = Text("Authorized Security Testing Console", style="bright_black")
    console.print(
        Panel(Align.center(Group(title, subtitle)), box=box.DOUBLE, padding=(1, 2))
    )


def pause():
    console.input(Text("\nPress ENTER to continue...", style="dim"))


def ask(prompt, default=None, secret=False):
    suffix = f" [{default}]" if default is not None else ""
    prompt_text = Text()
    prompt_text.append(prompt, style="bold cyan")
    prompt_text.append(suffix, style="dim")
    prompt_text.append(": ", style="bold cyan")
    value = console.input(prompt_text, password=secret).strip()
    return value if value else (str(default) if default is not None else "")


def ask_int(prompt, default, minimum=None):
    while True:
        value = ask(prompt, default)
        try:
            number = int(value)
        except ValueError:
            console.print("[red]Please enter a whole number.[/red]")
            continue
        if minimum is not None and number < minimum:
            console.print(f"[red]Value must be at least {minimum}.[/red]")
            continue
        return number


def ask_float(prompt, default, minimum=None):
    while True:
        value = ask(prompt, default)
        try:
            number = float(value)
        except ValueError:
            console.print("[red]Please enter a number.[/red]")
            continue
        if minimum is not None and number < minimum:
            console.print(f"[red]Value must be at least {minimum}.[/red]")
            continue
        return number


def target_config():
    clear()
    banner()
    console.print(
        Panel("Enter the SSH server details.", title="TARGET", box=box.ROUNDED)
    )
    host = ask("Target IP / hostname")
    while not host:
        console.print("[red]Target cannot be empty.[/red]")
        host = ask("Target IP / hostname")

    port = ask_int("SSH port", 22, minimum=1)
    if port > 65535:
        console.print("[red]Port must be between 1 and 65535.[/red]")
        port = ask_int("SSH port", 22, minimum=1)
        while port > 65535:
            console.print("[red]Port must be between 1 and 65535.[/red]")
            port = ask_int("SSH port", 22, minimum=1)

    timeout = ask_float("Timeout (seconds)", 5, minimum=0.1)
    delay = ask_float("Delay between attempts", 0.5, minimum=0)
    max_attempts = ask_int("Maximum attempts (0 = wordlist)", 0, minimum=0)

    table = Table(title="Configuration", box=box.ROUNDED)
    table.add_column("Setting", style="cyan")
    table.add_column("Value")
    table.add_row("Target", f"{host}:{port}")
    table.add_row("Timeout", f"{timeout}s")
    table.add_row("Delay", f"{delay}s")
    table.add_row(
        "Maximum attempts", str(max_attempts or "Wordlist size")
    )
    console.print(table)
    return host, port, timeout, delay, max_attempts


def connection_test():
    host, port, timeout, _, _ = target_config()
    username = ask("Username")
    password = ask("Password", secret=True)

    if not username:
        console.print("[red]Username cannot be empty.[/red]")
        pause()
        return

    clear()
    banner()
    with console.status(
        "[bold cyan]Connecting to SSH server...[/bold cyan]", spinner="dots"
    ):
        status, error = test_credentials(
            host, port, username, password, timeout
        )

    if status == "success":
        console.print(
            Panel(
                "[bold green]✓ SSH authentication accepted[/bold green]",
                box=box.DOUBLE,
            )
        )
    elif status == "failed":
        console.print(
            Panel(
                "[bold yellow]✗ Authentication rejected[/bold yellow]",
                box=box.ROUNDED,
            )
        )
    else:
        console.print(
            Panel(
                f"[bold red]Connection error[/bold red]\n{error or 'Unknown error'}",
                box=box.ROUNDED,
            )
        )
    pause()


def run_audit(mode):
    host, port, timeout, delay, max_attempts = target_config()

    if mode == "password":
        username = ask("Username")
        if not username:
            console.print("[red]Username cannot be empty.[/red]")
            pause()
            return
        wordlist = ask(
            "Password wordlist", str(DEFAULT_PASSWORD_LIST)
        )
        label = "PASSWORD AUDIT"
    else:
        password = ask("Password", secret=True)
        if not password:
            console.print("[red]Password cannot be empty.[/red]")
            pause()
            return
        wordlist = ask(
            "Username wordlist", str(DEFAULT_USERNAME_LIST)
        )
        label = "USERNAME AUDIT"

    try:
        items = load_wordlist(wordlist)
    except (FileNotFoundError, OSError) as exc:
        console.print(
            Panel(
                f"[bold red]Could not read wordlist[/bold red]\n{exc}",
                box=box.ROUNDED,
            )
        )
        pause()
        return

    if not items:
        console.print(
            Panel(
                "[bold red]The selected wordlist is empty.[/bold red]",
                box=box.ROUNDED,
            )
        )
        pause()
        return

    clear()
    banner()
    console.print(
        Panel(
            f"[cyan]Target:[/cyan] {host}:{port}\n"
            f"[cyan]Mode:[/cyan] {label}\n"
            f"[cyan]Candidates:[/cyan] {len(items)}\n"
            f"[cyan]Wordlist:[/cyan] {wordlist}",
            title=label,
            box=box.ROUNDED,
        )
    )

    total = min(max_attempts, len(items)) if max_attempts else len(items)
    progress = Progress(
        SpinnerColumn(),
        TextColumn("{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        TimeElapsedColumn(),
    )
    task = progress.add_task("Starting audit", total=total)

    def on_attempt(idx, total_count, username, status, error):
        if status == "success":
            description = f"SUCCESS {username}"
        elif status == "error":
            description = f"ERROR {username}"
        else:
            description = f"Testing {username}"
        progress.update(task, completed=idx, description=description)

    try:
        with progress:
            if mode == "password":
                result = audit_passwords(
                    host,
                    port,
                    username,
                    items,
                    timeout,
                    delay,
                    max_attempts,
                    on_attempt,
                )
            else:
                result = audit_usernames(
                    host,
                    port,
                    password,
                    items,
                    timeout,
                    delay,
                    max_attempts,
                    on_attempt,
                )
    except Exception as exc:
        console.print(
            Panel(
                f"[bold red]Audit failed unexpectedly[/bold red]\n{exc}",
                title="ERROR",
                box=box.ROUNDED,
            )
        )
        pause()
        return

    console.print()
    if result["status"] == "success":
        console.print(
            Panel(
                "[bold green]✓ VALID CREDENTIALS FOUND[/bold green]\n\n"
                f"Target   : {host}:{port}\n"
                f"Username : {result['username']}\n"
                f"Password : {result['password']}\n"
                f"Attempts : {result['attempts']}",
                title="SUCCESS",
                box=box.DOUBLE,
            )
        )
    elif result["status"] == "error":
        console.print(
            Panel(
                "[bold red]Stopped due to connection error[/bold red]\n\n"
                f"{result.get('error', 'Unknown error')}",
                title="ERROR",
                box=box.ROUNDED,
            )
        )
    else:
        console.print(
            Panel(
                f"[yellow]No valid credentials found.[/yellow]\n\n"
                f"Attempts: {result['attempts']}",
                title="AUDIT COMPLETE",
                box=box.ROUNDED,
            )
        )
    pause()


def results():
    clear()
    banner()
    files = recent_results()
    if not files:
        console.print(
            Panel(
                "[dim]No audit results yet.[/dim]",
                title="RESULTS",
                box=box.ROUNDED,
            )
        )
        pause()
        return

    table = Table(title="Recent Audit Results", box=box.SIMPLE_HEAVY)
    table.add_column("Time", style="dim")
    table.add_column("Target")
    table.add_column("Status")
    table.add_column("Attempts")

    for path in files[:12]:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            table.add_row(
                "Unreadable",
                path.name,
                "[red]ERROR[/red]",
                "-",
            )
            continue

        status = data.get("status", "?")
        status_text = (
            "[green]SUCCESS[/green]"
            if status == "success"
            else "[yellow]NOT FOUND[/yellow]"
            if status == "not_found"
            else "[red]ERROR[/red]"
        )
        table.add_row(
            str(data.get("timestamp", ""))[:19].replace("T", " "),
            str(data.get("target", "")),
            status_text,
            str(data.get("attempts", "")),
        )

    console.print(table)
    pause()


def main_menu():
    while True:
        clear()
        banner()
        table = Table(
            box=box.ROUNDED, show_header=False, padding=(0, 2)
        )
        table.add_column("Key", style="bold cyan", width=6)
        table.add_column("Operation")
        table.add_row("[1]", "Password Audit")
        table.add_row("[2]", "Username Audit")
        table.add_row("[3]", "SSH Connection Test")
        table.add_row("[4]", "View Recent Results")
        table.add_row("[0]", "Exit")
        console.print(Align.center(table))

        choice = console.input(
            Text("\nSelect operation ► ", style="bold cyan")
        ).strip().lower()

        if choice == "1":
            run_audit("password")
        elif choice == "2":
            run_audit("username")
        elif choice == "3":
            connection_test()
        elif choice == "4":
            results()
        elif choice == "0":
            clear()
            console.print(
                Panel(
                    "[bold cyan]Session closed.[/bold cyan]",
                    box=box.ROUNDED,
                )
            )
            break
        else:
            console.print("[red]Invalid option.[/red]")
            time.sleep(0.7)


def run():
    try:
        main_menu()
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Interrupted by user.[/yellow]")
