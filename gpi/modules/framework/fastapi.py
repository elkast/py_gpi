# gpi/modules/framework/fastapi.py
"""Module framework FastAPI — génère la structure de base d'un projet FastAPI."""

import secrets
from gpi.modules.base import Module, ModuleMetadata
from gpi.core.config import ProjectConfig


# Template du point d'entrée FastAPI
_MAIN_PY = '''\
"""Point d\'entrée de l\'application {{ project_name }}.

Généré par GPI v2 — https://github.com/elkast/py_gpi
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="{{ project_name }}",
    description="{{ description }}",
    version="1.0.0",
)

# Middleware CORS — à configurer selon vos besoins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Santé"])
def racine():
    """Point de contrôle de santé de l\'API."""
    return {"statut": "ok", "projet": "{{ project_name }}"}
'''

_REQUIREMENTS_TXT = '''\
# Dépendances de {{ project_name }}
# Généré par GPI v2

fastapi>=0.109.0
uvicorn[standard]>=0.27.0
python-dotenv>=1.0.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
'''

_ENV = '''\
# Variables d\'environnement — NE PAS COMMITTER CE FICHIER
DEBUG=true
PORT={{ port }}
SECRET_KEY={{ secret_key }}
'''

_ENV_EXAMPLE = '''\
# Variables d\'environnement — Copiez ce fichier en .env et remplissez les valeurs
DEBUG=true
PORT={{ port }}
SECRET_KEY=changez-moi-avec-une-valeur-secrete
'''

_GITIGNORE = '''\
# Python
__pycache__/
*.py[cod]
*.pyo
.venv/
venv/
env/

# Environnement
.env

# Base de données
*.db
*.sqlite3

# Distribution
dist/
build/
*.egg-info/

# Tests
.pytest_cache/
htmlcov/
.coverage

# IDE
.vscode/
.idea/
'''

_README = '''\
# {{ project_name }}

{{ description }}

*Généré avec [GPI](https://github.com/elkast/py_gpi) v2*

## Installation rapide

```bash
cd {{ project_name }}
pip install -r requirements.txt
cp .env.example .env
```

## Lancer le projet

```bash
uvicorn main:app --reload --host 0.0.0.0 --port {{ port }}
```

Documentation interactive : http://localhost:{{ port }}/docs

## Tests

```bash
pytest tests/ -v
```
'''

_DOCKER_COMPOSE = '''\
version: "3.9"

services:
{% for service in services %}
  {{ service }}:
    build: ./services/{{ service }}
    ports:
      - "{{ port + loop.index0 * 100 }}:8000"
    environment:
      - SECRET_KEY=${SECRET_KEY}
{% endfor %}
'''


class FastAPIModule(Module):
    """Module framework FastAPI.

    Génère la structure de base d\'un projet FastAPI :
    main.py, requirements.txt, .env, .env.example, .gitignore, README.md.
    """

    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            id="framework-fastapi",
            name="FastAPI",
            version="1.0.0",
            description="Framework moderne asynchrone pour API REST Python",
            frameworks=["fastapi"],
            architectures=["monolithic", "microservices"],
            tags=["framework", "fastapi", "async", "rest"],
        )

    def get_dependencies(self) -> list[str]:
        return [
            "fastapi>=0.109.0",
            "uvicorn[standard]>=0.27.0",
            "python-dotenv>=1.0.0",
            "pydantic>=2.0.0",
            "pydantic-settings>=2.0.0",
        ]

    def get_files(self, config: ProjectConfig) -> dict[str, str]:
        """Génère les fichiers de base du projet FastAPI."""
        secret_key = secrets.token_urlsafe(32)
        fichiers = {
            ".env": _ENV.replace("{{ secret_key }}", secret_key),
            ".env.example": _ENV_EXAMPLE,
            ".gitignore": _GITIGNORE,
            "README.md": _README,
        }

        if config.architecture == "microservices":
            # Un main.py + requirements.txt par service
            for service in config.services:
                contenu = _MAIN_PY.replace("{{ project_name }}", config.name)
                contenu = contenu.replace("{{ description }}", config.description or config.name)
                fichiers[f"services/{service}/main.py"] = contenu
                fichiers[f"services/{service}/requirements.txt"] = _REQUIREMENTS_TXT
                fichiers[f"services/{service}/__init__.py"] = ""
            # docker-compose.yml à la racine
            fichiers["docker-compose.yml"] = _DOCKER_COMPOSE
        else:
            fichiers["main.py"] = _MAIN_PY
            fichiers["requirements.txt"] = _REQUIREMENTS_TXT

        return fichiers

    def get_env_vars(self) -> dict[str, str]:
        return {
            "SECRET_KEY": secrets.token_urlsafe(32),
            "DEBUG": "true",
        }

    def get_env_example_vars(self) -> dict[str, str]:
        return {
            "SECRET_KEY": "changez-moi",
            "DEBUG": "true",
        }
