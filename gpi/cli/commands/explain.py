# gpi/cli/commands/explain.py
"""Commande gpi explain — explication IA du projet généré."""

import typer
from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown

console = Console()


def explain(
    project_path: str = typer.Argument(".", help="Chemin vers le projet généré"),
) -> None:
    """Demande à l'IA Groq d'expliquer le projet généré en langage clair.

    Nécessite GROQ_API_KEY dans l'environnement.
    """
    from gpi.ai.client import GpiGroqClient
    from gpi.ai.explainer import explain_project

    client = GpiGroqClient()

    if not client.is_available:
        console.print(
            "[yellow]⚠ GROQ_API_KEY non configurée. "
            "Ajoutez votre clé pour utiliser gpi explain.[/yellow]"
        )
        raise typer.Exit(1)

    if not Path(project_path).is_dir():
        console.print(f"[red]❌ Dossier introuvable : {project_path}[/red]")
        raise typer.Exit(1)

    with console.status("[bold green]L'IA analyse votre projet...[/bold green]"):
        explication = explain_project(project_path, client)

    console.print(Markdown(explication))
