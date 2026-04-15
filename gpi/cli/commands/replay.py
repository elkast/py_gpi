# gpi/cli/commands/replay.py
"""Commande gpi replay — reproduit un projet depuis son gpi.lock."""

import typer
from rich.console import Console

console = Console()


def replay_lock(
    lock_path: str = typer.Argument(..., help="Chemin vers le fichier gpi.lock"),
    output: str = typer.Option(".", "--output", "-o", help="Dossier de sortie"),
    check: bool = typer.Option(False, "--check", help="Valider uniquement sans générer"),
) -> None:
    """Reproduit exactement un projet depuis son fichier gpi.lock.

    Valide le checksum SHA-256 avant de régénérer.
    """
    from gpi.core.lock import LockFile
    from gpi.core.resolver import ResolutionResult
    from gpi.core.composer import Composer
    from gpi.core.writer import Writer
    from gpi.modules.registry import ModuleRegistry

    # Lecture et validation du lock
    try:
        donnees_lock = LockFile.read(lock_path)
    except ValueError as e:
        console.print(f"[red]❌ {e}[/red]")
        raise typer.Exit(1)
    except FileNotFoundError:
        console.print(f"[red]❌ Fichier introuvable : {lock_path}[/red]")
        raise typer.Exit(1)

    console.print("[green]✅ Checksum validé — gpi.lock intègre[/green]")

    if check:
        console.print("[green]✅ Vérification terminée (--check : aucun fichier généré)[/green]")
        return

    # Reconstruction de la config et régénération
    config = LockFile.to_config(donnees_lock)
    modules_resolus = [m["id"] for m in donnees_lock.get("resolved_modules", [])]
    auto_ajoutes = [m["id"] for m in donnees_lock.get("resolved_modules", []) if m.get("auto")]

    resolution = ResolutionResult(
        modules=modules_resolus,
        auto_added=auto_ajoutes,
        warnings=[],
    )

    registry = ModuleRegistry()
    composer = Composer(registry)

    with console.status("[bold green]Régénération du projet...[/bold green]"):
        fichiers = composer.compose(config, resolution)
        Writer().write(fichiers, output, config, resolution, registry)

    console.print(f"[green]✅ Projet reproduit à l'identique dans '{output}'[/green]")
