# gpi/modules/cache/redis.py
"""Module cache Redis."""

from gpi.modules.base import Module, ModuleMetadata
from gpi.core.config import ProjectConfig


_CACHE_PY = '''\
"""Configuration du cache Redis.

Généré par GPI v2
"""

import os
import redis

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

# Client Redis — connexion lazy
_client: redis.Redis | None = None


def obtenir_client() -> redis.Redis:
    """Retourne le client Redis (singleton)."""
    global _client
    if _client is None:
        _client = redis.from_url(REDIS_URL, decode_responses=True)
    return _client


def mettre_en_cache(cle: str, valeur: str, expiration: int = 300) -> None:
    """Met une valeur en cache avec une expiration en secondes."""
    obtenir_client().setex(cle, expiration, valeur)


def obtenir_du_cache(cle: str) -> str | None:
    """Récupère une valeur du cache. Retourne None si absente ou expirée."""
    return obtenir_client().get(cle)


def invalider_cache(cle: str) -> None:
    """Supprime une clé du cache."""
    obtenir_client().delete(cle)
'''


class RedisModule(Module):
    """Module cache Redis."""

    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            id="cache-redis",
            name="Redis Cache",
            version="1.0.0",
            description="Cache Redis pour les performances",
            frameworks=["fastapi", "flask", "django"],
            architectures=["monolithic", "microservices"],
            tags=["cache", "redis", "performance"],
        )

    def get_dependencies(self) -> list[str]:
        return ["redis>=5.0.0"]

    def get_files(self, config: ProjectConfig) -> dict[str, str]:
        return {"cache.py": _CACHE_PY}

    def get_env_vars(self) -> dict[str, str]:
        return {"REDIS_URL": "redis://localhost:6379/0"}

    def get_env_example_vars(self) -> dict[str, str]:
        return {"REDIS_URL": "redis://localhost:6379/0"}
