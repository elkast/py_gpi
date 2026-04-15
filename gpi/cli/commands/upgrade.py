# gpi/cli/commands/upgrade.py
"""Commande gpi upgrade — met à jour les modules d'un projet existant."""

import typer
from rich.console import Console
from pathlib import Path
from typing import Optional

console = Console()


def upgrade_modules(
    module_id: Optional[str] = typer.Argument(None, help="Module spécifique à mettre à jour"),
    project_path: str = typer.Option(".", "--path", "-p", help="Chemin vers le projet"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Aperçu sans application"),
) -> None:
    """Met à jour un ou tous les modules d'un projet GPI existant.

    Exemples :
        gpi upgrade
        gpi upgrade auth-jwt
        gpi upgrade --dry-run
    """
    from gpi.core.lock import LockFile
    from gpi.core.resolver import Resolver
    from gpi.core.composer import Composer
    from gpi.core.writer import Writer
    from gpi.modules.registry import ModuleRegistry

    chemin_lock = Path(project_path) / LockFile.FILENAME

    if not chemin_lock.exists():
        console.print(f"[red]❌ Fichier gpi.lock introuvable dans '{project_path}'.[/red]")
        raise typer.Exit(1)

    donnees_lock = LockFile.read(str(chemin_lock))
    config = LockFile.to_config(donnees_lock)

    if dry_run:
        console.print("[yellow]Mode --dry-run : aucun fichier ne sera modifié.[/yellow]")

    registry = ModuleRegistry()
    resolver = Resolver(registry)

    with console.status("[bold green]Résolution des modules...[/bold green]"):
        try:
            result = resolver.resolve(config)
        except Exception as e:
            console.print(f"[red]❌ {e}[/red]")
            raise typer.Exit(1)

    modules_a_mettre_a_jour = [module_id] if module_id else config.modules
    console.print(f"[green]Modules à mettre à jour : {', '.join(modules_a_mettre_a_jour)}[/green]")

    if dry_run:
        console.print("[yellow]✅ Aperçu terminé (--dry-run : aucune modification appliquée)[/yellow]")
        return

    composer = Composer(registry)
    writer = Writer()

    for mid in modules_a_mettre_a_jour:
        fichiers = composer.get_new_files(mid, config)
        for chemin, contenu in fichiers.items():
            chemin_complet = Path(project_path) / chemin
            chemin_complet.parent.mkdir(parents=True, exist_ok=True)
            chemin_complet.write_text(contenu, encoding="utf-8")
        console.print(f"[green]✅ Module '{mid}' mis à jour[/green]")

    # Mise à jour du gpi.lock
    LockFile.write(
        LockFile.create(config, result, composer.get_all_dependencies(result)),
        project_path,
    )
    console.print("[green]✅ gpi.lock mis à jour[/green]")
