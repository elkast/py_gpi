# PY_GPI — Générateur de Projet Intelligent v2

**PY_GPI** est un compositeur de projets backend Python modulaire. Il résout les dépendances entre modules, garantit la reproductibilité via `gpi.lock`, et intègre une assistance IA Groq optionnelle.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)

## Installation

```bash
pip install py_gpi
```

Avec support IA Groq :

```bash
pip install "py_gpi[ai]"
```

## Démarrage rapide

### CLI interactive

```bash
gpi init
```

### Depuis un fichier de configuration

```yaml
# gpi.yaml
name: monapi
framework: fastapi
architecture: monolithic
modules:
  - auth-jwt
  - database-postgres
  - docker
language: fr
port: 8000
```

```bash
gpi init -c gpi.yaml
```

### API Python

```python
import gpi

project = gpi.compose(
    name="monapi",
    framework="fastapi",
    modules=["auth-jwt", "database-postgres"],
)
project.generate("./output")
```

## Commandes CLI

| Commande | Description |
|----------|-------------|
| `gpi init` | Génère un nouveau projet (interactif ou depuis fichier) |
| `gpi init -c gpi.yaml` | Génère depuis un fichier YAML ou TOML |
| `gpi add <module>` | Ajoute un module à un projet existant |
| `gpi upgrade [module]` | Met à jour un ou tous les modules |
| `gpi upgrade --dry-run` | Aperçu des changements sans écriture |
| `gpi replay gpi.lock` | Reproduit un projet depuis son lock |
| `gpi replay gpi.lock --check` | Valide le lock sans générer |
| `gpi explain [path]` | Explique le projet via IA (nécessite GROQ_API_KEY) |
| `gpi plugin list` | Liste tous les modules disponibles |
| `gpi plugin install <pkg>` | Installe un plugin depuis PyPI |
| `gpi plugin uninstall <pkg>` | Désinstalle un plugin |
| `gpi version` | Affiche la version de GPI |

## Modules disponibles

### Frameworks
- `framework-fastapi` — FastAPI (async, recommandé pour API REST)
- `framework-flask` — Flask (léger, prototypes)
- `framework-django` — Django (tout-en-un)

### Authentification
- `auth-jwt` — JWT avec python-jose (FastAPI, Flask, Django)
- `auth-sessions` — Sessions (Flask, Django)
- `auth-oauth2` — OAuth2 avec scopes (FastAPI uniquement)

### Base de données
- `database-sqlite` — SQLite + SQLAlchemy + CRUD atomisé
- `database-postgres` — PostgreSQL + SQLAlchemy + Alembic
- `database-mysql` — MySQL/MariaDB + SQLAlchemy

### Cache & Files
- `cache-redis` — Redis
- `queue-celery` — Celery (requiert cache-redis)
- `queue-rq` — Redis Queue (requiert cache-redis)

### Infrastructure
- `docker` — Dockerfile + .dockerignore
- `docker-compose` — docker-compose.yml
- `github-actions` — CI/CD GitHub Actions

### Qualité & Monitoring
- `tests-pytest` — Pytest + pytest-cov
- `monitoring-prometheus` — Prometheus + Grafana (FastAPI, Flask)

## Format gpi.yaml

```yaml
name: monprojet          # Obligatoire : lettres/chiffres/underscores, 2-49 chars
framework: fastapi       # fastapi | flask | django
architecture: monolithic # monolithic | microservices
modules:
  - auth-jwt
  - database-postgres
description: "Mon API REST"
language: fr             # fr | en
port: 8000               # 1024-65535
use_groq_ai: false       # Active les suggestions IA
```

## Reproductibilité avec gpi.lock

Chaque projet généré contient un `gpi.lock` versionnable :

```bash
# Reproduire exactement un projet
gpi replay gpi.lock --output ./nouveau_dossier

# Valider l'intégrité du lock
gpi replay gpi.lock --check
```

## Intégration IA Groq (optionnelle)

```bash
export GROQ_API_KEY=votre-cle-groq

# Suggestions de modules basées sur la description
gpi init  # Active use_groq_ai: true dans la config

# Explication du projet généré
gpi explain ./monprojet
```

GPI fonctionne entièrement hors-ligne sans `GROQ_API_KEY`.

## Système de plugins

Créez et publiez vos propres modules GPI :

```toml
# pyproject.toml de votre plugin
[project.entry-points."gpi.modules"]
mon_module = "mon_package:MonModule"
```

```python
# mon_package/__init__.py
from gpi.modules.base import Module, ModuleMetadata

class MonModule(Module):
    @property
    def metadata(self):
        return ModuleMetadata(
            id="mon-module",
            name="Mon Module",
            version="1.0.0",
            description="Description",
            frameworks=["fastapi"],
            architectures=["monolithic"],
        )

    def get_dependencies(self):
        return ["ma-dependance>=1.0.0"]

    def get_files(self, config):
        return {"mon_fichier.py": "# Contenu"}
```

```bash
pip install mon-plugin-gpi
gpi plugin list  # Votre module apparaît automatiquement
```

## Développement

```bash
git clone https://github.com/sossou-elkast/py_gpi
cd py_gpi
pip install -e ".[dev]"
pytest tests/ -v
```
