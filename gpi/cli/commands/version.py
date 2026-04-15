# gpi/cli/commands/version.py
"""Commande gpi version — affiche la version du package."""

import typer
from rich.console import Console

console = Console()


def show_version() -> None:
    """Affiche la version actuelle de GPI."""
    try:
        import gpi
        version = gpi.__version__
    except Exception:
        version = "inconnue"
    console.print(f"[bold green]GPI[/bold green] v{version}")
