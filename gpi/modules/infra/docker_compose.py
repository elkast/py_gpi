# gpi/modules/infra/docker_compose.py
"""Module Docker Compose — génère docker-compose.yml multi-services."""

from gpi.modules.base import Module, ModuleMetadata
from gpi.core.config import ProjectConfig


_DOCKER_COMPOSE = '''\
# docker-compose.yml pour {{ project_name }}
# Généré par GPI v2

version: "3.9"

services:
  app:
    build: .
    ports:
      - "{{ port }}:{{ port }}"
    env_file:
      - .env
    depends_on:
      {% if "database-postgres" in modules %}
      db:
        condition: service_healthy
      {% endif %}
      {% if "cache-redis" in modules %}
      redis:
        condition: service_healthy
      {% endif %}
    volumes:
      - .:/app
    restart: unless-stopped

  {% if "database-postgres" in modules %}
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: {{ project_name }}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5
  {% endif %}

  {% if "cache-redis" in modules %}
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
  {% endif %}

{% if "database-postgres" in modules %}
volumes:
  postgres_data:
{% endif %}
'''


class DockerComposeModule(Module):
    """Module Docker Compose — orchestration multi-conteneurs."""

    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            id="docker-compose",
            name="Docker Compose",
            version="1.0.0",
            description="Orchestration multi-conteneurs avec docker-compose",
            frameworks=["fastapi", "flask", "django"],
            architectures=["monolithic", "microservices"],
            tags=["docker", "compose", "devops", "orchestration"],
        )

    def get_dependencies(self) -> list[str]:
        return []

    def get_files(self, config: ProjectConfig) -> dict[str, str]:
        return {"docker-compose.yml": _DOCKER_COMPOSE}

    def post_generate_instructions(self) -> list[str]:
        return ["Lancez tous les services : docker-compose up --build"]
