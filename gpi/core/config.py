# gpi/core/config.py
"""Modèle de configuration Pydantic v2 pour GPI.

Remplace l'ancien ProjectConfig v0.1 qui contenait des champs obsolètes
(niveau, route_org, bilingue, auth, database, redis, queue, monitoring).
"""

import re
from pydantic import BaseModel, field_validator, model_validator


class ProjectConfig(BaseModel):
    """Configuration complète d'un projet GPI.

    Source de vérité unique — validée dès la construction.
    Tous les champs v0.1 obsolètes ont été supprimés.
    """

    # Champs obligatoires
    framework: str                    # "fastapi" | "flask" | "django"
    name: str                         # Nom du projet (regex validé)

    # Champs avec valeurs par défaut
    architecture: str = "monolithic"  # "monolithic" | "microservices"
    modules: list[str] = []           # IDs des modules demandés
    description: str = ""
    language: str = "fr"              # "fr" | "en" (bilingue supprimé)
    port: int = 8000
    services: list[str] = []          # Noms des services (microservices uniquement)
    use_groq_ai: bool = False         # Active les suggestions IA

    @field_validator("framework")
    @classmethod
    def validate_framework(cls, v: str) -> str:
        """Valide que le framework est l'un des frameworks supportés."""
        allowed = ["fastapi", "flask", "django"]
        if v not in allowed:
            raise ValueError(f"framework doit être l'un de: {allowed}")
        return v

    @field_validator("architecture")
    @classmethod
    def validate_architecture(cls, v: str) -> str:
        """Valide que l'architecture est monolithique ou microservices."""
        allowed = ["monolithic", "microservices"]
        if v not in allowed:
            raise ValueError(f"architecture doit être l'une de: {allowed}")
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Valide le nom du projet contre la regex stricte (anti path-traversal)."""
        if not re.match(r"^[a-zA-Z][a-zA-Z0-9_]{1,48}$", v):
            raise ValueError(
                "Le nom doit commencer par une lettre, "
                "contenir uniquement lettres/chiffres/underscores, "
                "et faire entre 2 et 49 caractères."
            )
        return v

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        """Valide la langue — bilingue supprimé, seuls fr et en sont valides."""
        allowed = ["fr", "en"]
        if v not in allowed:
            raise ValueError(f"language doit être l'un de: {allowed}")
        return v

    @field_validator("port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        """Valide que le port est dans la plage autorisée [1024, 65535]."""
        if not (1024 <= v <= 65535):
            raise ValueError("port doit être entre 1024 et 65535")
        return v

    @model_validator(mode="after")
    def validate_microservices_services(self) -> "ProjectConfig":
        """Injecte des services par défaut si microservices sans services déclarés."""
        if self.architecture == "microservices" and not self.services:
            self.services = ["auth", "users", "products"]
        return self

    @classmethod
    def from_yaml(cls, path: str) -> "ProjectConfig":
        """Charge une configuration depuis un fichier gpi.yaml."""
        import yaml
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls(**data)

    @classmethod
    def from_toml(cls, path: str) -> "ProjectConfig":
        """Charge une configuration depuis un fichier gpi.toml.

        Utilise tomllib (stdlib Python 3.11+) ou tomli (Python 3.9/3.10).
        """
        try:
            import tomllib          # Python 3.11+
        except ImportError:
            import tomli as tomllib  # type: ignore[no-redef]  # Python 3.9/3.10
        with open(path, "rb") as f:
            data = tomllib.load(f)
        return cls(**data)
