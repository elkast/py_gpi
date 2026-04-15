# gpi/cli/commands/plugin.py
"""Commande gpi plugin — gestion des plugins GPI."""

import subprocess
import sys
import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="Gestion des plugins GPI")
console = Console()


@app.command("install")
def install_plugin(
    package: str = typer.Argument(..., help="Nom du package PyPI à installer"),
) -> None:
    """Installe un plugin GPI depuis PyPI."""
    console.print(f"[bold green]Installation de '{package}'...[/bold green]")
    resultat = subprocess.run(
        [sys.executable, "-m", "pip", "install", package],
        capture_output=True,
        text=True,
    )
    if resultat.returncode == 0:
        console.print(f"[green]✅ Plugin '{package}' installé avec succès.[/green]")
        console.print("[yellow]ℹ Redémarrez GPI pour charger le nouveau plugin.[/yellow]")
    else:
        console.print(f"[red]❌ Erreur lors de l'installation :\n{resultat.stderr}[/red]")
        raise typer.Exit(1)


@app.command("list")
def list_plugins() -> None:
    """Liste tous les modules disponibles (natifs + plugins installés)."""
    from gpi.modules.registry import ModuleRegistry

    registry = ModuleRegistry()
    modules = registry.list_all()

    table = Table(title="Modules GPI disponibles", show_header=True)
    table.add_column("ID", style="cyan")
    table.add_column("Nom", style="white")
    table.add_column("Version", style="dim")
    table.add_column("Frameworks", style="green")
    table.add_column("Description", style="dim")

    for module in sorted(modules, key=lambda m: m.metadata.id):
        table.add_row(
            module.metadata.id,
            module.metadata.name,
            module.metadata.version,
            ", ".join(module.metadata.frameworks),
            module.metadata.description[:50] + "..." if len(module.metadata.description) > 50 else module.metadata.description,
        )

    console.print(table)


@app.command("uninstall")
def uninstall_plugin(
    package: str = typer.Argument(..., help="Nom du package PyPI à désinstaller"),
) -> None:
    """Désinstalle un plugin GPI."""
    resultat = subprocess.run(
        [sys.executable, "-m", "pip", "uninstall", "-y", package],
        capture_output=True,
        text=True,
    )
    if resultat.returncode == 0:
        console.print(f"[green]✅ Plugin '{package}' désinstallé.[/green]")
    else:
        console.print(f"[red]❌ Erreur : {resultat.stderr}[/red]")
        raise typer.Exit(1)


@app.command("publish")
def publish_plugin(
    plugin_path: str = typer.Argument(".", help="Chemin vers le dossier du plugin"),
) -> None:
    """Guide interactif pour publier un plugin sur PyPI."""
    console.print("[bold]Guide de publication d'un plugin GPI[/bold]\n")
    console.print("1. Assurez-vous que votre pyproject.toml déclare :")
    console.print('   [project.entry-points."gpi.modules"]')
    console.print('   mon_module = "mon_package:MonModule"\n')
    console.print("2. Construisez le package : python -m build")
    console.print("3. Publiez sur PyPI : twine upload dist/*")
    console.print("\nDocumentation : https://github.com/sossou-elkast/py_gpi/wiki/plugins")
