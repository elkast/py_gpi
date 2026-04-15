# gpi/cli/interactive.py
"""Questionnaire interactif Rich pour la commande gpi init.

Sans niveaux (debutant/intermediaire/expert) — l'utilisateur déclare ses besoins.
"""

from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel

from gpi.core.config import ProjectConfig

console = Console()

# Modules disponibles avec descriptions courtes
MODULES_DISPONIBLES = {
    "auth-jwt": "Authentification JWT (tokens sécurisés)",
    "auth-sessions": "Authentification par sessions (Flask/Django)",
    "auth-oauth2": "OAuth2 avec scopes (FastAPI uniquement)",
    "database-sqlite": "SQLite (développement local)",
    "database-postgres": "PostgreSQL (production recommandée)",
    "database-mysql": "MySQL/MariaDB",
    "cache-redis": "Cache Redis",
    "queue-celery": "Tâches asynchrones Celery",
    "queue-rq": "Redis Queue (plus simple que Celery)",
    "docker": "Containerisation Docker",
    "docker-compose": "Orchestration Docker Compose",
    "tests-pytest": "Tests automatisés Pytest",
    "monitoring-prometheus": "Métriques Prometheus + Grafana",
    "github-actions": "CI/CD GitHub Actions",
}


def collecter_config() -> ProjectConfig:
    """Lance le questionnaire interactif et retourne une ProjectConfig.

    Aucun niveau (debutant/intermediaire/expert) — l'utilisateur déclare ses besoins.
    """
    console.print(Panel(
        "[bold green]GPI — Générateur de Projet Intelligent v2[/bold green]\n"
        "Répondez aux questions pour configurer votre projet.",
        title="Bienvenue",
    ))

    # Nom du projet
    while True:
        nom = Prompt.ask("\n[cyan]Nom du projet[/cyan]", default="monprojet")
        try:
            ProjectConfig(name=nom, framework="fastapi")  # Validation du nom
            break
        except Exception:
            console.print("[red]❌ Nom invalide. Utilisez uniquement lettres, chiffres et underscores (2-49 chars).[/red]")

    # Framework
    console.print("\n[cyan]Framework :[/cyan]")
    console.print("  1. fastapi  — Moderne, asynchrone, idéal pour API REST [bold](recommandé)[/bold]")
    console.print("  2. flask    — Léger et flexible, parfait pour prototypes")
    console.print("  3. django   — Tout-en-un, idéal pour applications complexes")
    choix_fw = Prompt.ask("Votre choix", choices=["1", "2", "3", "fastapi", "flask", "django"], default="1")
    framework = {"1": "fastapi", "2": "flask", "3": "django"}.get(choix_fw, choix_fw)

    # Architecture
    console.print("\n[cyan]Architecture :[/cyan]")
    console.print("  1. monolithic    — Un seul projet, simple à démarrer [bold](recommandé)[/bold]")
    console.print("  2. microservices — Plusieurs services indépendants (avancé)")
    choix_arch = Prompt.ask("Votre choix", choices=["1", "2", "monolithic", "microservices"], default="1")
    architecture = {"1": "monolithic", "2": "microservices"}.get(choix_arch, choix_arch)

    # Description (optionnelle)
    description = Prompt.ask("\n[cyan]Description du projet[/cyan] (optionnel)", default="")

    # Port
    port_str = Prompt.ask("\n[cyan]Port d'écoute[/cyan]", default="8000")
    try:
        port = int(port_str)
    except ValueError:
        port = 8000

    # Langue
    langue = Prompt.ask("\n[cyan]Langue des commentaires[/cyan]", choices=["fr", "en"], default="fr")

    # Modules — boucle jusqu'à une sélection valide
    module_ids = list(MODULES_DISPONIBLES.keys())
    modules: list[str] = []

    while True:
        console.print("\n[cyan]Modules disponibles :[/cyan]")
        for i, (mid, desc) in enumerate(MODULES_DISPONIBLES.items(), 1):
            console.print(f"  {i:2}. [green]{mid}[/green] — {desc}")

        modules_str = Prompt.ask(
            "\nModules à inclure (numéros ou IDs séparés par des virgules, ou vide pour aucun)",
            default="",
        )

        modules = []
        if modules_str:
            for token in modules_str.split(","):
                token = token.strip()
                if not token:
                    continue
                if token.isdigit():
                    idx = int(token) - 1
                    if 0 <= idx < len(module_ids):
                        modules.append(module_ids[idx])
                    else:
                        console.print(f"[yellow]⚠ Numéro {token} hors plage, ignoré.[/yellow]")
                else:
                    modules.append(token)

        # Validation anticipée : compatibilité framework + résolution
        erreurs = _valider_modules(modules, framework, architecture)
        if not erreurs:
            break
        for err in erreurs:
            console.print(f"[red]❌ {err}[/red]")
        console.print("[yellow]↩ Veuillez choisir à nouveau.[/yellow]")

    # Groq AI
    use_groq = Confirm.ask("\n[cyan]Activer les suggestions IA Groq ?[/cyan]", default=False)

    return ProjectConfig(
        name=nom,
        framework=framework,
        architecture=architecture,
        description=description,
        port=port,
        language=langue,
        modules=modules,
        use_groq_ai=use_groq,
    )


def _valider_modules(modules: list[str], framework: str, architecture: str) -> list[str]:
    """Vérifie la compatibilité des modules avec le framework/architecture choisis.

    Retourne une liste d'erreurs (vide = tout est OK).
    """
    from gpi.modules.registry import ModuleRegistry
    from gpi.core.validator import VALIDATION_RULES
    from gpi.core.config import ProjectConfig

    erreurs: list[str] = []
    registry = ModuleRegistry()

    # Vérification compatibilité framework par module
    for mid in modules:
        module = registry.get(mid)
        if module is None:
            erreurs.append(f"Module '{mid}' introuvable. Vérifiez l'ID ou le numéro.")
            continue
        if framework not in module.metadata.frameworks:
            erreurs.append(
                f"'{mid}' ne supporte pas {framework}. "
                f"Frameworks compatibles : {', '.join(module.metadata.frameworks)}"
            )
        if architecture not in module.metadata.architectures:
            erreurs.append(
                f"'{mid}' ne supporte pas l'architecture {architecture}."
            )

    # Vérification des règles bloquantes du validator
    if not erreurs:
        try:
            config = ProjectConfig(
                name="tmp", framework=framework,
                architecture=architecture, modules=modules,
            )
            for regle in VALIDATION_RULES:
                if regle["blocking"] and regle["condition"](config):
                    erreurs.append(regle["message"])
        except Exception:
            pass

    return erreurs
