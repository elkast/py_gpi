# gpi/modules/framework/django.py
"""Module framework Django — génère la structure de base d'un projet Django."""

import secrets
from gpi.modules.base import Module, ModuleMetadata
from gpi.core.config import ProjectConfig


_MANAGE_PY = '''\
#!/usr/bin/env python
"""Utilitaire de gestion Django pour {{ project_name }}."""

import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "{{ project_name }}.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError("Django introuvable. Installez-le avec : pip install django") from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
'''

_SETTINGS_PY = '''\
"""Configuration Django pour {{ project_name }}.

Généré par GPI v2 — https://github.com/elkast/py_gpi
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("SECRET_KEY", "{{ secret_key }}")
DEBUG = os.environ.get("DEBUG", "true").lower() == "true"
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "{{ project_name }}.urls"
WSGI_APPLICATION = "{{ project_name }}.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Europe/Paris"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
'''

_URLS_PY = '''\
"""Configuration des URLs de {{ project_name }}."""

from django.contrib import admin
from django.urls import path
from django.http import JsonResponse


def racine(request):
    """Point de contrôle de santé."""
    return JsonResponse({"statut": "ok", "projet": "{{ project_name }}"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", racine),
]
'''

_REQUIREMENTS_TXT = '''\
# Dépendances de {{ project_name }}
django>=5.0.0
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
db.sqlite3
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
python manage.py migrate
python manage.py createsuperuser
```

## Lancer le projet

```bash
python manage.py runserver 0.0.0.0:{{ port }}
```

Admin : http://localhost:{{ port }}/admin
'''


class DjangoModule(Module):
    """Module framework Django."""

    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            id="framework-django",
            name="Django",
            version="1.0.0",
            description="Framework tout-en-un pour applications web Python",
            frameworks=["django"],
            architectures=["monolithic"],
            tags=["framework", "django", "web", "orm"],
        )

    def get_dependencies(self) -> list[str]:
        return ["django>=5.0.0", "python-dotenv>=1.0.0"]

    def get_files(self, config: ProjectConfig) -> dict[str, str]:
        secret_key = secrets.token_urlsafe(32)
        name = config.name
        return {
            "manage.py": _MANAGE_PY,
            f"{name}/settings.py": _SETTINGS_PY.replace("{{ secret_key }}", secret_key),
            f"{name}/urls.py": _URLS_PY,
            f"{name}/__init__.py": "",
            f"{name}/wsgi.py": f'import os\nfrom django.core.wsgi import get_wsgi_application\nos.environ.setdefault("DJANGO_SETTINGS_MODULE", "{name}.settings")\napplication = get_wsgi_application()\n',
            "requirements.txt": _REQUIREMENTS_TXT,
            ".env": _ENV.replace("{{ secret_key }}", secret_key),
            ".env.example": _ENV_EXAMPLE,
            ".gitignore": _GITIGNORE,
            "README.md": _README,
        }

    def post_generate_instructions(self) -> list[str]:
        return [
            "Appliquez les migrations : python manage.py migrate",
            "Créez un superutilisateur : python manage.py createsuperuser",
        ]
