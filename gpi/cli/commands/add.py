# gpi/cli/commands/add.py
"""Commande gpi add — ajoute un module à un projet GPI existant."""

import typer
from rich.console import Console
from pathlib import Path

console = Console()


def add_module(
    module_id: str = typer.Argument(..., help="ID du module à ajouter (ex: cache-redis)"),
    project_path: str = typer.Option(".", "--path", "-p", help="Chemin vers le projet"),
) -> None:
    """Ajoute un module à un projet GPI existant.

    Lit le gpi.lock, résout les nouvelles dépendances et écrit les fichiers.

    Exemples :
        gpi add cache-redis
        gpi add monitoring-prometheus --path ./monprojet
    """
    from gpi.core.lock import LockFile
    from gpi.core.resolver import Resolver
    from gpi.core.composer import Composer
    from gpi.core.writer import Writer
    from gpi.modules.registry import ModuleRegistry

    chemin_lock = Path(project_path) / LockFile.FILENAME

    if not chemin_lock.exists():
        console.print(
            f"[red]❌ Fichier gpi.lock introuvable dans '{project_path}'.[/red]\n"
            "Ce dossier n'est pas un projet GPI, ou le gpi.lock a été supprimé."
        )
        raise typer.Exit(1)

    # Lecture de la configuration existante
    donnees_lock = LockFile.read(str(chemin_lock))
    config = LockFile.to_config(donnees_lock)

    # Vérification si le module est déjà installé
    if module_id in config.modules:
        console.print(f"[yellow]⚠ Le module '{module_id}' est déjà installé.[/yellow]")
        raise typer.Exit(0)

    config.modules.append(module_id)

    # Résolution et composition
    registry = ModuleRegistry()
    resolver = Resolver(registry)

    with console.status(f"[bold green]Résolution de '{module_id}'...[/bold green]"):
        try:
            result = resolver.resolve(config)
        except Exception as e:
            console.print(f"[red]❌ {e}[/red]")
            raise typer.Exit(1)

    for avertissement in result.warnings:
        console.print(f"[yellow]ℹ {avertissement}[/yellow]")

    # Application des modifications
    composer = Composer(registry)
    with console.status("[bold green]Application des modifications...[/bold green]"):
        nouveaux_fichiers = composer.get_new_files(module_id, config)
        composer.apply_to_existing(nouveaux_fichiers, project_path)
        LockFile.write(
            LockFile.create(config, result, composer.get_all_dependencies(result)),
            project_path,
        )

    console.print(f"[green]✅ Module '{module_id}' ajouté avec succès.[/green]")

    # Instructions post-installation
    module = registry.get(module_id)
    if module:
        for instruction in module.post_generate_instructions():
            console.print(f"   → {instruction}")
