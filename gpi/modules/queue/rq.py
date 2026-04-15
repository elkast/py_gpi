# gpi/modules/queue/rq.py
"""Module file de tâches RQ (Redis Queue) — plus simple que Celery."""

from gpi.modules.base import Module, ModuleMetadata
from gpi.core.config import ProjectConfig


_RQ_PY = '''\
"""Configuration RQ (Redis Queue) pour {{ project_name }}.

Généré par GPI v2
"""

import os
from redis import Redis
from rq import Queue

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

# Connexion Redis et file de tâches
connexion_redis = Redis.from_url(REDIS_URL)
file_taches = Queue(connection=connexion_redis)


def tache_exemple(x: int, y: int) -> int:
    """Tâche exemple — additionne deux nombres de façon asynchrone."""
    return x + y


# Exemple d\'utilisation :
# job = file_taches.enqueue(tache_exemple, 1, 2)
'''


class RQModule(Module):
    """Module file de tâches RQ — plus simple que Celery."""

    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            id="queue-rq",
            name="RQ (Redis Queue)",
            version="1.0.0",
            description="File de tâches Redis Queue — plus simple que Celery",
            frameworks=["fastapi", "flask"],
            architectures=["monolithic"],
            requires=["cache-redis"],
            tags=["queue", "rq", "redis", "tasks"],
        )

    def get_dependencies(self) -> list[str]:
        return ["rq>=1.16.0"]

    def get_files(self, config: ProjectConfig) -> dict[str, str]:
        return {"rq_app.py": _RQ_PY}

    def post_generate_instructions(self) -> list[str]:
        return ["Démarrez le worker : rq worker --with-scheduler"]
