# gpi/utils/display.py
"""Fonctions d'affichage Rich pour GPI — panels, progress, tables."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def afficher_succes(message: str) -> None:
    """Affiche un message de succès en vert."""
    console.print(f"[bold green]✅ {message}[/bold green]")


def afficher_erreur(message: str) -> None:
    """Affiche un message d'erreur en rouge."""
    console.print(f"[bold red]❌ {message}[/bold red]")


def afficher_avertissement(message: str) -> None:
    """Affiche un avertissement en jaune."""
    console.print(f"[yellow]⚠ {message}[/yellow]")


def afficher_info(message: str) -> None:
    """Affiche une information en cyan."""
    console.print(f"[cyan]ℹ {message}[/cyan]")


def afficher_panel(titre: str, contenu: str) -> None:
    """Affiche un panel Rich avec titre et contenu."""
    console.print(Panel(contenu, title=titre))
