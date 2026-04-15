# gpi/cli/app.py
"""Application Typer principale — enregistrement de toutes les commandes GPI v2."""

import typer
from gpi.cli.commands.version import show_version
from gpi.cli.commands.add import add_module
from gpi.cli.commands.upgrade import upgrade_modules
from gpi.cli.commands.replay import replay_lock
from gpi.cli.commands.explain import explain
from gpi.cli.commands.init import app as init_app
from gpi.cli.commands.plugin import app as plugin_app

app = typer.Typer(
    name="gpi",
    help="GPI — Générateur de Projet Intelligent pour Python backend",
    add_completion=True,
    no_args_is_help=True,
)

# Enregistrement des commandes
app.add_typer(init_app, name="init", help="Génère un nouveau projet (interactif ou depuis fichier)")
app.command("add")(add_module)
app.command("upgrade")(upgrade_modules)
app.command("replay")(replay_lock)
app.command("explain")(explain)
app.command("version")(show_version)
app.add_typer(plugin_app, name="plugin")


def main() -> None:
    """Point d'entrée du package (défini dans pyproject.toml)."""
    app()
