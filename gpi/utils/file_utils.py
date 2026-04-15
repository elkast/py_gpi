"""Utilitaires de création de fichiers et dossiers."""
from __future__ import annotations
import os
import sys
import ctypes
from pathlib import Path
from jinja2 import Environment, BaseLoader
from rich.console import Console

console = Console()
_env = Environment(loader=BaseLoader(), keep_trailing_newline=True)


def est_admin() -> bool:
    """Vérifie si le script tourne avec les droits admin."""
    try:
        if sys.platform == "win32":
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        return os.geteuid() == 0  # type: ignore[attr-defined]
    except (AttributeError, OSError):
        return False


def verifier_permissions(chemin: Path) -> bool:
    """Vérifie que l'on peut écrire dans le dossier cible."""
    dossier = chemin.parent if not chemin.is_dir() else chemin
    dossier.mkdir(parents=True, exist_ok=True)
    test = dossier / ".gpi_write_test"
    try:
        test.write_text("test", encoding="utf-8")
        test.unlink()
        return True
    except PermissionError:
        return False


def rendre_template(tpl: str, ctx: dict) -> str:
    """Rend un template Jinja2 inline."""
    return _env.from_string(tpl).render(**ctx)


def ecrire_fichier(chemin: Path, contenu: str) -> None:
    """Crée le fichier et ses dossiers parents. Gère les permissions."""
    chemin.parent.mkdir(parents=True, exist_ok=True)
    try:
        chemin.write_text(contenu, encoding="utf-8")
    except PermissionError:
        console.print(f"[red]❌ Permission refusée pour écrire : {chemin}[/]")
        if sys.platform == "win32":
            console.print("[yellow]💡 Relancez le terminal en tant qu'Administrateur :[/]")
            console.print("   Clic droit → Exécuter en tant qu'administrateur")
        else:
            console.print("[yellow]💡 Relancez avec sudo ou changez de répertoire :[/]")
            console.print("   sudo gpi init")
            console.print("   cd ~/mes_projets && gpi init")
        raise


def generer_fichiers(racine: Path, fichiers: dict[str, str], ctx: dict) -> None:
    """Génère un ensemble de fichiers {chemin_relatif: template_string}."""
    for chemin_rel, tpl in fichiers.items():
        contenu = rendre_template(tpl, ctx)
        ecrire_fichier(racine / chemin_rel, contenu)


def verifier_dossier(chemin: Path) -> str | None:
    """Vérifie si le dossier existe. Retourne le nom final ou None si annulé."""
    if not chemin.exists():
        return chemin.name

    from rich.prompt import Prompt
    console.print(f'\n[yellow]⚠️  Le dossier "{chemin.name}" existe déjà.[/]')
    choix = Prompt.ask("  (1) Écraser  (2) Renommer  (3) Annuler",
                       choices=["1", "2", "3"], default="3")
    if choix == "1":
        import shutil
        shutil.rmtree(chemin)
        return chemin.name
    elif choix == "2":
        nouveau = Prompt.ask("  Nouveau nom")
        return nouveau
    return None
