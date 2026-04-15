# gpi/modules/framework/flask.py
"""Module framework Flask — génère la structure de base d'un projet Flask."""

import secrets
from gpi.modules.base import Module, ModuleMetadata
from gpi.core.config import ProjectConfig


_APP_PY = '''\
"""Point d\'entrée de l\'application {{ project_name }}.

Généré par GPI v2 — https://github.com/elkast/py_gpi
"""

from flask import Flask, jsonify
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret")
app.config["DEBUG"] = os.environ.get("DEBUG", "true").lower() == "true"


@app.route("/", methods=["GET"])
def racine():
    """Point de contrôle de santé de l\'API."""
    return jsonify({"statut": "ok", "projet": "{{ project_name }}"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", {{ port }}))
    app.run(host="0.0.0.0", port=port, debug=app.config["DEBUG"])
'''

_REQUIREMENTS_TXT = '''\
# Dépendances de {{ project_name }}
flask>=3.0.0
python-dotenv>=1.0.0
'''

_ENV = '''\
DEBUG=true
PORT={{ port }}
SECRET_KEY={{ secret_key }}
'''

_ENV_EXAMPLE = '''\
DEBUG=true
PORT={{ port }}
SECRET_KEY=changez-moi
'''

_GITIGNORE = '''\
__pycache__/
*.py[cod]
.venv/
venv/
.env
*.db
dist/
*.egg-info/
.pytest_cache/
htmlcov/
.coverage
'''

_README = '''\
# {{ project_name }}

{{ description }}

*Généré avec [GPI](https://github.com/elkast/py_gpi) v2*

## Installation rapide

```bash
pip install -r requirements.txt
cp .env.example .env
```

## Lancer le projet

```bash
python app.py
```

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
      - "{{ port + loop.index0 * 100 }}:5000"
    environment:
      - SECRET_KEY=${SECRET_KEY}
{% endfor %}
'''


class FlaskModule(Module):
    """Module framework Flask."""

    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            id="framework-flask",
            name="Flask",
            version="1.0.0",
            description="Framework léger et flexible pour Python",
            frameworks=["flask"],
            architectures=["monolithic", "microservices"],
            tags=["framework", "flask", "web"],
        )

    def get_dependencies(self) -> list[str]:
        return ["flask>=3.0.0", "python-dotenv>=1.0.0"]

    def get_files(self, config: ProjectConfig) -> dict[str, str]:
        secret_key = secrets.token_urlsafe(32)
        fichiers = {
            ".env": _ENV.replace("{{ secret_key }}", secret_key),
            ".env.example": _ENV_EXAMPLE,
            ".gitignore": _GITIGNORE,
            "README.md": _README,
        }

        if config.architecture == "microservices":
            for service in config.services:
                contenu = _APP_PY.replace("{{ project_name }}", config.name)
                contenu = contenu.replace("{{ port }}", str(config.port))
                fichiers[f"services/{service}/app.py"] = contenu
                fichiers[f"services/{service}/requirements.txt"] = _REQUIREMENTS_TXT
                fichiers[f"services/{service}/__init__.py"] = ""
            fichiers["docker-compose.yml"] = _DOCKER_COMPOSE
        else:
            fichiers["app.py"] = _APP_PY
            fichiers["requirements.txt"] = _REQUIREMENTS_TXT

        return fichiers
