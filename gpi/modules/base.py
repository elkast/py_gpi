# gpi/modules/base.py
"""Classe de base abstraite pour tous les modules GPI.

Tout module natif ou plugin doit hériter de Module et implémenter
les méthodes abstraites : metadata, get_dependencies(), get_files().
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gpi.core.config import ProjectConfig


@dataclass
class ModuleMetadata:
    """Métadonnées déclaratives d'un module GPI.

    Utilisées par le Resolver pour la résolution des dépendances,
    la détection des conflits et la vérification de compatibilité.
    """

    id: str                           # Ex: "auth-jwt" — identifiant unique kebab-case
    name: str                         # Ex: "Authentification JWT" — nom lisible
    version: str                      # Ex: "1.0.0" — version sémantique
    description: str                  # Description courte pour gpi plugin list
    frameworks: list[str]             # Frameworks supportés : ["fastapi", "flask", "django"]
    architectures: list[str]          # Architectures supportées : ["monolithic", "microservices"]
    requires: list[str] = field(default_factory=list)   # Modules requis (dépendances)
    conflicts: list[str] = field(default_factory=list)  # Modules incompatibles
    optional: list[str] = field(default_factory=list)   # Modules optionnels suggérés
    tags: list[str] = field(default_factory=list)       # Tags pour la recherche


class Module(ABC):
    """Classe de base abstraite pour tous les modules GPI.

    Chaque module natif ou plugin doit hériter de cette classe
    et implémenter les trois méthodes abstraites.
    """

    @property
    @abstractmethod
    def metadata(self) -> ModuleMetadata:
        """Retourne les métadonnées du module (id, version, compatibilités...)."""
        ...

    @abstractmethod
    def get_dependencies(self) -> list[str]:
        """Retourne les packages Python à ajouter à requirements.txt.

        Returns:
            Liste de spécifications pip (ex: ["python-jose[cryptography]>=3.3.0"])
        """
        ...

    @abstractmethod
    def get_files(self, config: "ProjectConfig") -> dict[str, str]:
        """Retourne les fichiers à générer pour ce module.

        Args:
            config: Configuration complète du projet

        Returns:
            Dictionnaire {chemin_relatif: contenu_jinja2_ou_texte}
            Ex: {"auth/security.py": "...", "auth/routes.py": "..."}
        """
        ...

    def get_env_vars(self) -> dict[str, str]:
        """Variables d'environnement à ajouter au .env (avec valeurs réelles).

        Ex: {"SECRET_KEY": "generated-secret", "JWT_ALGORITHM": "HS256"}
        """
        return {}

    def get_env_example_vars(self) -> dict[str, str]:
        """Variables pour .env.example (valeurs fictives/vides pour documentation).

        Ex: {"SECRET_KEY": "changez-moi", "JWT_ALGORITHM": "HS256"}
        """
        return {}

    def post_generate_instructions(self) -> list[str]:
        """Instructions affichées à l'utilisateur après la génération.

        Ex: ["Initialisez la base : alembic upgrade head"]
        """
        return []
