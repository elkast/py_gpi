# gpi/modules/queue/celery.py
"""Module file de tâches Celery — nécessite Redis comme broker."""

from gpi.modules.base import Module, ModuleMetadata
from gpi.core.config import ProjectConfig


_CELERY_PY = '''\
"""Configuration Celery pour {{ project_name }}.

Généré par GPI v2
"""

import os
from celery import Celery

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

# Application Celery avec Redis comme broker et backend de résultats
app_celery = Celery(
    "{{ project_name }}",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["taches"],
)

app_celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Paris",
    enable_utc=True,
)


@app_celery.task
def tache_exemple(x: int, y: int) -> int:
    """Tâche exemple — additionne deux nombres de façon asynchrone."""
    return x + y
'''


class CeleryModule(Module):
    """Module file de tâches Celery avec Redis comme broker."""

    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            id="queue-celery",
            name="Celery",
            version="1.0.0",
            description="File de tâches asynchrones Celery",
            frameworks=["fastapi", "flask"],
            architectures=["monolithic", "microservices"],
            requires=["cache-redis"],  # Redis requis comme broker
            tags=["queue", "celery", "async", "tasks", "worker"],
        )

    def get_dependencies(self) -> list[str]:
        return ["celery[redis]>=5.3.0", "flower>=2.0.0"]

    def get_files(self, config: ProjectConfig) -> dict[str, str]:
        return {"celery_app.py": _CELERY_PY}

    def post_generate_instructions(self) -> list[str]:
        return [
            "Démarrez le worker : celery -A celery_app worker --loglevel=info",
            "Démarrez Flower (monitoring) : celery -A celery_app flower",
        ]
