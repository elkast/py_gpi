# gpi/cli/commands/init.py
"""Commande gpi init — assistant interactif ou depuis fichier de config."""

import typer
from rich.console import Console
from typing import Optional

app = typer.Typer()
console = Console()


@app.callback(invoke_without_command=True)
def init(
    config_file: Optional[str] = typer.Option(
        None, "--config", "-c", help="Fichier de configuration YAML ou TOML"
    ),
    output: str = typer.Option(".", "--output", "-o", help="Dossier de sortie"),
    no_network: bool = typer.Option(False, "--no-network", help="Désactive la détection IP"),
) -> None:
    """Génère un nouveau projet backend Python.

    Sans --config : lance le questionnaire interactif.
    Avec --config : charge la configuration depuis un fichier YAML ou TOML.
    """
    from gpi.core.validator import Validator
    from gpi.core.resolver import Resolver
    from gpi.core.composer import Composer
    from gpi.core.writer import Writer
    from gpi.core.exceptions import ValidationError, GpiError
    from gpi.modules.registry import ModuleRegistry
    from gpi.core.config import ProjectConfig

    # Chargement de la configuration
    if config_file:
        try:
            if config_file.endswith(".toml"):
                config = ProjectConfig.from_toml(config_file)
            else:
                config = ProjectConfig.from_yaml(config_file)
            console.print(f"[green]✅ Configuration chargée depuis '{config_file}'[/green]")
        except Exception as e:
            console.print(f"[red]❌ Erreur de configuration : {e}[/red]")
            raise typer.Exit(1)
    else:
        from gpi.cli.interactive import collecter_config
        try:
            config = collecter_config()
        except KeyboardInterrupt:
            console.print("\n[yellow]Annulé.[/yellow]")
            raise typer.Exit(0)

    # Suggestions IA si disponible
    if config.use_groq_ai:
        from gpi.ai.client import GpiGroqClient
        from gpi.ai.suggestions import suggest_modules
        client = GpiGroqClient()
        if client.is_available and config.description:
            with console.status("[bold green]L'IA analyse votre projet...[/bold green]"):
                suggestions = suggest_modules(
                    config.description, config.framework, config.architecture, client
                )
            if suggestions:
                console.print(f"[cyan]✨ Suggestions IA : {', '.join(suggestions)}[/cyan]")
                for s in suggestions:
                    if s not in config.modules:
                        config.modules.append(s)

    # Validation
    validator = Validator()
    try:
        avertissements = validator.validate(config)
    except ValidationError as e:
        console.print(f"[red]❌ Configuration invalide : {e}[/red]")
        raise typer.Exit(1)

    for avert in avertissements:
        console.print(f"[yellow]⚠ {avert}[/yellow]")

    # Résolution des modules
    registry = ModuleRegistry()
    resolver = Resolver(registry)

    console.print("\n[bold]⏳ Résolution des modules...[/bold]")
    try:
        result = resolver.resolve(config)
    except GpiError as e:
        console.print(f"[red]❌ {e}[/red]")
        raise typer.Exit(1)

    for module_id in result.modules:
        statut = "ℹ️ " if module_id in result.auto_added else "✅"
        suffixe = " (ajouté automatiquement)" if module_id in result.auto_added else ""
        console.print(f"   {statut} {module_id}{suffixe}")

    # Composition et écriture
    composer = Composer(registry)
    writer = Writer()

    dossier_sortie = f"{output}/{config.name}" if output == "." else output

    console.print("\n[bold]⏳ Génération en cours...[/bold]")
    fichiers = composer.compose(config, result)
    writer.write(fichiers, dossier_sortie, config, result, registry)

    # Détection IP réseau (sauf --no-network)
    ip_reseau = None
    if not no_network:
        try:
            from gpi.utils.network import detecter_ip
            ip_reseau = detecter_ip()
        except Exception:
            pass

    console.print(f"\n[bold green]✅ Projet généré avec succès dans '{dossier_sortie}/'[/bold green]")
    console.print(f"\n[bold]🚀 Pour démarrer :[/bold]")
    console.print(f"   cd {dossier_sortie}")
    console.print(f"   pip install -r requirements.txt")

    if config.framework == "fastapi":
        console.print(f"   uvicorn main:app --reload")
        console.print(f"   # Swagger : http://localhost:{config.port}/docs")
    elif config.framework == "flask":
        console.print(f"   python app.py")
    elif config.framework == "django":
        console.print(f"   python manage.py migrate && python manage.py runserver 0.0.0.0:{config.port}")

    if ip_reseau:
        console.print(f"\n[bold]📱 Test mobile (même réseau Wi-Fi) :[/bold]")
        console.print(f"   http://{ip_reseau}:{config.port}")

    # Instructions post-génération
    for module_id in result.modules:
        module = registry.get(module_id)
        if module:
            for instruction in module.post_generate_instructions():
                console.print(f"   → {instruction}")
