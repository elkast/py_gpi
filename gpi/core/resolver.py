# gpi/core/resolver.py
"""Moteur de résolution des dépendances entre modules GPI.

Algorithme : DFS (Depth-First Search) avec détection de cycles.
Complexité : O(V + E) où V = modules, E = dépendances.
"""

from dataclasses import dataclass, field
from typing import Optional

from gpi.modules.registry import ModuleRegistry
from gpi.core.config import ProjectConfig
from gpi.core.exceptions import (
    ModuleNotFoundError,
    ModuleConflictError,
    ModuleIncompatibleError,
    CircularDependencyError,
)


@dataclass
class ResolutionResult:
    """Résultat de la résolution des dépendances.

    Attributes:
        modules: Ordre de résolution final (tri topologique) — framework en premier
        auto_added: Modules ajoutés automatiquement (non demandés par l'utilisateur)
        warnings: Avertissements non bloquants
    """

    modules: list[str] = field(default_factory=list)
    auto_added: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class Resolver:
    """Résoud les dépendances entre modules GPI.

    Étapes de résolution :
    1. Validation existence de chaque module dans le registre
    2. Validation compatibilité framework/architecture
    3. Résolution récursive des dépendances (DFS)
    4. Détection de conflits (modules incompatibles)
    5. Détection de cycles (dépendances circulaires)
    6. Tri topologique final (framework en premier)
    """

    def __init__(self, registry: ModuleRegistry) -> None:
        self.registry = registry

    def resolve(self, config: ProjectConfig) -> ResolutionResult:
        """Résoud la liste de modules demandés + leurs dépendances transitives.

        Args:
            config: Configuration du projet avec la liste des modules demandés

        Returns:
            ResolutionResult avec l'ordre de résolution, les modules auto-ajoutés
            et les avertissements

        Raises:
            ModuleNotFoundError: Module introuvable dans le registre
            ModuleIncompatibleError: Module incompatible avec le framework/architecture
            ModuleConflictError: Deux modules incompatibles demandés simultanément
            CircularDependencyError: Dépendance circulaire détectée
        """
        demandes = set(config.modules)
        resolus: list[str] = []
        auto_ajoutes: list[str] = []
        avertissements: list[str] = []
        en_visite: set[str] = set()   # Nœuds en cours de visite (détection cycles)
        visites: set[str] = set()     # Nœuds déjà résolus

        def visiter(module_id: str, requis_par: Optional[str] = None) -> None:
            """Visite récursive DFS pour la résolution des dépendances."""
            if module_id in visites:
                return  # Déjà résolu, on ignore

            if module_id in en_visite:
                raise CircularDependencyError(
                    f"Dépendance circulaire détectée impliquant '{module_id}'"
                )

            module = self.registry.get(module_id)
            if module is None:
                raise ModuleNotFoundError(
                    f"Module '{module_id}' introuvable dans le registre. "
                    f"Utilisez `gpi plugin list` pour voir les modules disponibles."
                )

            # Vérification compatibilité framework
            if config.framework not in module.metadata.frameworks:
                raise ModuleIncompatibleError(
                    f"Le module '{module_id}' ne supporte pas le framework "
                    f"'{config.framework}'. Frameworks supportés : "
                    f"{module.metadata.frameworks}"
                )

            # Vérification compatibilité architecture
            if config.architecture not in module.metadata.architectures:
                raise ModuleIncompatibleError(
                    f"Le module '{module_id}' ne supporte pas l'architecture "
                    f"'{config.architecture}'"
                )

            # Vérification conflits avec les modules déjà connus
            for conflit in module.metadata.conflicts:
                if conflit in demandes or conflit in auto_ajoutes:
                    raise ModuleConflictError(
                        f"'{module_id}' est incompatible avec '{conflit}'. "
                        f"Choisissez l'un ou l'autre."
                    )

            en_visite.add(module_id)

            # Résolution récursive des dépendances (DFS)
            for dep in module.metadata.requires:
                if dep not in demandes and dep not in auto_ajoutes:
                    auto_ajoutes.append(dep)
                    avertissements.append(
                        f"Module '{dep}' ajouté automatiquement "
                        f"(requis par '{module_id}')"
                    )
                visiter(dep, requis_par=module_id)

            en_visite.remove(module_id)
            visites.add(module_id)
            resolus.append(module_id)

        # Le framework est toujours résolu en premier (nœud racine)
        visiter(f"framework-{config.framework}")

        # Résolution de chaque module demandé par l'utilisateur
        for module_id in config.modules:
            visiter(module_id)

        return ResolutionResult(
            modules=resolus,
            auto_added=auto_ajoutes,
            warnings=avertissements,
        )
