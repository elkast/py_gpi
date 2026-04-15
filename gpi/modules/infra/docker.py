# gpi/modules/infra/docker.py
"""Module Docker — génère Dockerfile et .dockerignore."""

from gpi.modules.base import Module, ModuleMetadata
from gpi.core.config import ProjectConfig


_DOCKERFILE_FASTAPI = '''\
# Dockerfile pour {{ project_name }}
# Généré par GPI v2

FROM python:3.11-slim

WORKDIR /app

# Copie des dépendances en premier (cache Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code source
COPY . .

EXPOSE {{ port }}

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "{{ port }}"]
'''

_DOCKERFILE_FLASK = '''\
# Dockerfile pour {{ project_name }}
# Généré par GPI v2

FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE {{ port }}

CMD ["python", "app.py"]
'''

_DOCKERFILE_DJANGO = '''\
# Dockerfile pour {{ project_name }}
# Généré par GPI v2

FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE {{ port }}

CMD ["python", "manage.py", "runserver", "0.0.0.0:{{ port }}"]
'''

_DOCKERIGNORE = '''\
# Fichiers à exclure de l\'image Docker
__pycache__/
*.py[cod]
.venv/
venv/
.env
*.db
.git/
.gitignore
.pytest_cache/
htmlcov/
dist/
*.egg-info/
README.md
'''


class DockerModule(Module):
    """Module Docker — génère Dockerfile et .dockerignore."""

    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            id="docker",
            name="Docker",
            version="1.0.0",
            description="Containerisation Docker avec Dockerfile optimisé",
            frameworks=["fastapi", "flask", "django"],
            architectures=["monolithic", "microservices"],
            tags=["docker", "container", "devops"],
        )

    def get_dependencies(self) -> list[str]:
        return []  # Docker n'ajoute pas de dépendances Python

    def get_files(self, config: ProjectConfig) -> dict[str, str]:
        """Génère le Dockerfile adapté au framework."""
        dockerfiles = {
            "fastapi": _DOCKERFILE_FASTAPI,
            "flask": _DOCKERFILE_FLASK,
            "django": _DOCKERFILE_DJANGO,
        }
        return {
            "Dockerfile": dockerfiles.get(config.framework, _DOCKERFILE_FASTAPI),
            ".dockerignore": _DOCKERIGNORE,
        }

    def post_generate_instructions(self) -> list[str]:
        return [
            "Construisez l'image : docker build -t nom-projet .",
            "Lancez le conteneur : docker run -p 8000:8000 nom-projet",
        ]
