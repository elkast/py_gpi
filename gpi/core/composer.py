# gpi/core/composer.py
"""Assemblage des fichiers de tous les modules résolus.

Rend les templates Jinja2 avec le contexte du projet et produit
un dictionnaire {chemin_relatif: contenu_final} prêt à être écrit.
"""

from pathlib import Path
from jinja2 import Environment, BaseLoader

from gpi.core.config import ProjectConfig
from gpi.core.resolver import ResolutionResult
from gpi.modules.registry import ModuleRegistry


class Composer:
    """Assemble les fichiers de tous les modules résolus.

    Rend les templates Jinja2 avec le contexte du projet.
    En cas de conflit de chemin, le dernier module dans l'ordre de
    résolution gagne (comportement prévisible et documenté).
    """

    def __init__(self, registry: ModuleRegistry) -> None:
        self.registry = registry
        # Environnement Jinja2 pour le rendu des templates inline
        self._jinja_env = Environment(loader=BaseLoader(), autoescape=False)

    def compose(
        self,
        config: ProjectConfig,
        resolution: ResolutionResult,
    ) -> dict[str, str]:
        """Assemble tous les fichiers du projet.

        Args:
            config: Configuration du projet
            resolution: Résultat de la résolution des modules

        Returns:
            Dictionnaire {chemin_relatif: contenu_rendu}
        """
        fichiers: dict[str, str] = {}
        contexte = self._construire_contexte(config, resolution)

        for module_id in resolution.modules:
            module = self.registry.get(module_id)
            if module is None:
                continue

            fichiers_module = module.get_files(config)
            for chemin, contenu in fichiers_module.items():
                # Rendu Jinja2 du contenu avec le contexte du projet
                fichiers[chemin] = self._rendre(contenu, contexte)

        return fichiers

    def get_new_files(
        self,
        module_id: str,
        config: ProjectConfig,
    ) -> dict[str, str]:
        """Retourne uniquement les fichiers d'un module spécifique.

        Utilisé par `gpi add` pour ajouter un module à un projet existant.
        """
        module = self.registry.get(module_id)
        if module is None:
            return {}
        contexte = self._construire_contexte(config, ResolutionResult())
        return {
            chemin: self._rendre(contenu, contexte)
            for chemin, contenu in module.get_files(config).items()
        }

    def get_all_dependencies(self, resolution: ResolutionResult) -> list[str]:
        """Collecte tous les packages Python de tous les modules résolus.

        Retourne une liste triée et dédupliquée.
        Utilisé pour générer requirements.txt et gpi.lock.
        """
        deps: list[str] = []
        for module_id in resolution.modules:
            module = self.registry.get(module_id)
            if module:
                deps.extend(module.get_dependencies())
        return sorted(set(deps))

    def apply_to_existing(
        self,
        new_files: dict[str, str],
        project_path: str,
    ) -> None:
        """Applique de nouveaux fichiers à un projet existant.

        Crée les dossiers parents si nécessaire.
        N'écrase pas les fichiers existants.
        """
        for chemin_relatif, contenu in new_files.items():
            chemin_complet = Path(project_path) / chemin_relatif
            chemin_complet.parent.mkdir(parents=True, exist_ok=True)
            if not chemin_complet.exists():
                chemin_complet.write_text(contenu, encoding="utf-8")

    def _construire_contexte(
        self,
        config: ProjectConfig,
        resolution: ResolutionResult,
    ) -> dict:
        """Construit le contexte Jinja2 à partir de la configuration."""
        return {
            "project_name": config.name,
            "description": config.description or config.name,
            "framework": config.framework,
            "architecture": config.architecture,
            "language": config.language,
            "port": config.port,
            "modules": resolution.modules,
            "services": config.services,
            "is_microservices": config.architecture == "microservices",
        }

    def _rendre(self, template_str: str, contexte: dict) -> str:
        """Rend un template Jinja2 avec le contexte donné.

        En cas d'erreur de rendu, retourne le contenu brut sans lever d'exception.
        """
        try:
            template = self._jinja_env.from_string(template_str)
            return template.render(**contexte)
        except Exception:
            return template_str  # Retourne le contenu brut si le rendu échoue
