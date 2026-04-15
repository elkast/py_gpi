# gpi/core/validator.py
"""Validation des combinaisons de modules avant la résolution.

Les règles sont exprimées de façon déclarative (liste de dicts) pour
faciliter l'ajout de nouvelles règles sans modifier la logique.
"""

from gpi.core.config import ProjectConfig
from gpi.core.exceptions import ValidationError


# Règles déclaratives : condition (lambda) + message + blocking (bool)
# blocking=True  → lève ValidationError (arrêt immédiat)
# blocking=False → avertissement affiché, génération continue
VALIDATION_RULES: list[dict] = [
    {
        "condition": lambda c: (
            c.architecture == "microservices" and len(c.modules) < 1
        ),
        "message": (
            "L'architecture microservices nécessite au moins 1 module. "
            "Ajoutez des modules (ex: auth-jwt, database-postgres) ou "
            "utilisez l'architecture monolithique."
        ),
        "blocking": True,
    },
    {
        "condition": lambda c: (
            "auth-oauth2" in c.modules and "auth-jwt" in c.modules
        ),
        "message": (
            "Choisissez un seul mécanisme d'authentification : "
            "auth-jwt OU auth-oauth2."
        ),
        "blocking": True,
    },
    {
        "condition": lambda c: (
            "monitoring-prometheus" in c.modules and c.framework == "django"
        ),
        "message": (
            "Le module monitoring-prometheus ne supporte pas Django. "
            "Utilisez FastAPI ou Flask pour le monitoring Prometheus."
        ),
        "blocking": True,
    },
    {
        "condition": lambda c: (
            "queue-celery" in c.modules and "cache-redis" not in c.modules
        ),
        "message": (
            "Celery nécessite un broker. Le module cache-redis sera ajouté "
            "automatiquement comme broker Celery."
        ),
        "blocking": False,
    },
    {
        "condition": lambda c: (
            c.framework == "django" and "auth-jwt" in c.modules
        ),
        "message": (
            "Django dispose d'un système d'auth intégré. "
            "auth-jwt utilisera djangorestframework-simplejwt."
        ),
        "blocking": False,
    },
    {
        "condition": lambda c: (
            c.architecture == "microservices" and c.framework == "django"
        ),
        "message": (
            "Django en microservices est une architecture avancée. "
            "FastAPI est recommandé pour les microservices Python."
        ),
        "blocking": False,
    },
    {
        "condition": lambda c: (
            "auth-sessions" in c.modules and c.framework == "fastapi"
        ),
        "message": (
            "auth-sessions est conçu pour Flask/Django. "
            "Pour FastAPI, préférez auth-jwt ou auth-oauth2."
        ),
        "blocking": False,
    },
]


class Validator:
    """Valide la configuration avant la résolution des modules.

    Applique les règles déclaratives de VALIDATION_RULES dans l'ordre.
    S'arrête à la première règle bloquante violée.
    """

    def validate(self, config: ProjectConfig) -> list[str]:
        """Valide la configuration.

        Args:
            config: Configuration à valider

        Returns:
            Liste des avertissements non bloquants

        Raises:
            ValidationError: Si une règle bloquante est violée
        """
        avertissements: list[str] = []

        for regle in VALIDATION_RULES:
            if regle["condition"](config):
                if regle["blocking"]:
                    raise ValidationError(regle["message"])
                else:
                    avertissements.append(regle["message"])

        return avertissements
