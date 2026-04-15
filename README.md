# GPI — Générateur de Projet Intelligent

<p align="center">
  <img src="https://img.shields.io/pypi/v/py_gpi?color=dc2626&label=PyPI&style=for-the-badge" alt="PyPI"/>
  <img src="https://img.shields.io/pypi/pyversions/py_gpi?color=3b82f6&style=for-the-badge" alt="Python"/>
  <img src="https://img.shields.io/pypi/dm/py_gpi?color=10b981&style=for-the-badge" alt="Downloads"/>
  <img src="https://img.shields.io/github/stars/elkast/py_gpi?style=for-the-badge&color=f59e0b" alt="Stars"/>
</p>

<p align="center">
  <b>Générez un projet backend Python complet en 30 secondes.</b><br/>
  FastAPI · Flask · Django · Monolithique · Microservices · Docker · JWT · PostgreSQL · Redis · Celery
</p>

---

## Pourquoi GPI ?

La mise en place d'un projet backend Python prend des heures : structure de dossiers, configuration de la base de données, authentification, Docker, CI/CD... **GPI automatise tout ça** en posant quelques questions simples.

- **Modulaire** — choisissez exactement les modules dont vous avez besoin
- **Reproductible** — le fichier `gpi.lock` garantit des projets identiques à chaque génération
- **Extensible** — créez vos propres modules et publiez-les sur PyPI
- **IA optionnelle** — suggestions intelligentes via Groq (fonctionne 100% hors-ligne sans clé)

---

## Installation

```bash
pip install py_gpi
```

Avec support IA Groq :

```bash
pip install "py_gpi[ai]"
```

Vérifier l'installation :

```bash
gpi version
# GPI v2.0.4
```

---

## Démarrage rapide

### Mode interactif

```bash
gpi init
```

GPI vous guide étape par étape :

```
Nom du projet : monapi
Framework : 1. fastapi  2. flask  3. django  → 1
Architecture : 1. monolithic  2. microservices  → 1
Modules à inclure : 1,5,10  → auth-jwt, database-postgres, docker
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
  - tests-pytest
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
    modules=["auth-jwt", "database-postgres", "docker"],
)
project.generate("./output")
```

---

## Architectures supportées

### Monolithique (recommandé pour débuter)

Tout le code dans un seul projet. Idéal pour les APIs REST, les prototypes et les projets de taille moyenne.

#### FastAPI monolithique

```bash
gpi init
# framework: fastapi | architecture: monolithic
# modules: auth-jwt, database-postgres, docker, tests-pytest
```

Structure générée :

```
monapi/
├── main.py                    # Point d'entrée FastAPI
├── database.py                # Connexion SQLAlchemy
├── auth/
│   ├── security.py            # Hachage bcrypt + JWT
│   └── routes.py              # /auth/inscription, /auth/connexion
├── models/
│   └── catalogue.py           # Modèle SQLAlchemy
├── schemas/
│   └── catalogue.py           # Schémas Pydantic (Create/Read/Update/Delete)
├── app/catalogue/
│   ├── create.py              # POST /catalogue/
│   ├── read.py                # GET  /catalogue/ et /{id}
│   ├── update.py              # PUT/PATCH /catalogue/{id}
│   └── delete.py              # DELETE /catalogue/{id}
├── tests/
│   ├── conftest.py
│   └── test_sante.py
├── Dockerfile
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

Lancer le projet :

```bash
cd monapi
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --host 0.0.0.0 --port 8000
# Swagger : http://localhost:8000/docs
```

#### Flask monolithique

```bash
gpi init
# framework: flask | architecture: monolithic
# modules: auth-sessions, database-sqlite, tests-pytest
```

Structure générée :

```
monapi/
├── app.py                     # Application Flask + routes
├── auth/
│   └── routes.py              # Blueprint auth (sessions)
├── database.py                # SQLAlchemy + SQLite
├── models/catalogue.py
├── schemas/catalogue.py
├── tests/
├── requirements.txt
├── .env
└── README.md
```

Lancer le projet :

```bash
cd monapi
pip install -r requirements.txt
python app.py
# http://localhost:8000
```

#### Django monolithique

```bash
gpi init
# framework: django | architecture: monolithic
# modules: database-postgres, tests-pytest
```

Structure générée :

```
monapi/
├── manage.py
├── monapi/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── requirements.txt
├── .env
└── README.md
```

Lancer le projet :

```bash
cd monapi
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000
# Admin : http://localhost:8000/admin
```

---

### Microservices (avancé)

Chaque service est une API indépendante avec son propre code, sa base de données et son Dockerfile. Orchestrés par `docker-compose.yml`.

#### FastAPI microservices

```bash
gpi init
# framework: fastapi | architecture: microservices
# modules: auth-jwt, database-postgres, cache-redis, docker
```

Structure générée :

```
monapi/
├── docker-compose.yml         # Orchestre tous les services
├── .env
├── services/
│   ├── auth/
│   │   ├── main.py            # API FastAPI indépendante
│   │   ├── requirements.txt
│   │   └── __init__.py
│   ├── users/
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   └── __init__.py
│   └── products/
│       ├── main.py
│       ├── requirements.txt
│       └── __init__.py
├── auth/
│   ├── security.py
│   └── routes.py
├── cache.py
└── README.md
```

Lancer tous les services :

```bash
cd monapi
docker-compose up --build
# auth    : http://localhost:8000
# users   : http://localhost:8100
# products: http://localhost:8200
```

#### Flask microservices

```bash
gpi init
# framework: flask | architecture: microservices
# modules: database-postgres, cache-redis
```

Structure générée :

```
monapi/
├── docker-compose.yml
├── services/
│   ├── auth/
│   │   ├── app.py
│   │   └── requirements.txt
│   └── users/
│       ├── app.py
│       └── requirements.txt
└── .env
```

---

## Modules disponibles

### Frameworks

| ID | Description | Architectures |
|----|-------------|---------------|
| `framework-fastapi` | FastAPI — async, idéal pour API REST | monolithic, microservices |
| `framework-flask` | Flask — léger, parfait pour prototypes | monolithic, microservices |
| `framework-django` | Django — tout-en-un | monolithic |

### Authentification

| ID | Description | Frameworks |
|----|-------------|------------|
| `auth-jwt` | JWT avec bcrypt | fastapi, flask, django |
| `auth-sessions` | Sessions côté serveur | flask, django |
| `auth-oauth2` | OAuth2 avec scopes | fastapi |

### Base de données

| ID | Description | Dépendances |
|----|-------------|-------------|
| `database-sqlite` | SQLite + SQLAlchemy + CRUD atomisé | sqlalchemy, alembic |
| `database-postgres` | PostgreSQL production-ready | sqlalchemy, alembic, psycopg2 |
| `database-mysql` | MySQL/MariaDB | sqlalchemy, alembic, pymysql |

### Cache & Files d'attente

| ID | Description | Prérequis |
|----|-------------|-----------|
| `cache-redis` | Cache Redis | — |
| `queue-celery` | Tâches asynchrones Celery | cache-redis |
| `queue-rq` | Redis Queue (plus simple) | cache-redis |

### Infrastructure

| ID | Description |
|----|-------------|
| `docker` | Dockerfile + .dockerignore |
| `docker-compose` | docker-compose.yml multi-services |
| `github-actions` | Pipeline CI/CD GitHub Actions |

### Qualité & Monitoring

| ID | Description |
|----|-------------|
| `tests-pytest` | Pytest + pytest-cov + fixtures |
| `monitoring-prometheus` | Prometheus + Grafana (FastAPI, Flask) |

---

## Commandes CLI

```bash
gpi init                        # Génère un projet (interactif)
gpi init -c gpi.yaml            # Génère depuis un fichier YAML/TOML
gpi add cache-redis             # Ajoute un module à un projet existant
gpi upgrade                     # Met à jour tous les modules
gpi upgrade auth-jwt            # Met à jour un module spécifique
gpi upgrade --dry-run           # Aperçu sans modification
gpi replay gpi.lock             # Reproduit un projet depuis son lock
gpi replay gpi.lock --check     # Valide le lock sans générer
gpi explain ./monprojet         # Explique le projet via IA (GROQ_API_KEY requis)
gpi plugin list                 # Liste tous les modules disponibles
gpi plugin install mon-plugin   # Installe un plugin depuis PyPI
gpi plugin uninstall mon-plugin # Désinstalle un plugin
gpi version                     # Affiche la version
```

---

## Reproductibilité avec gpi.lock

Chaque projet généré contient un `gpi.lock` versionnable :

```bash
# Reproduire exactement un projet sur une autre machine
gpi replay gpi.lock --output ./nouveau_dossier

# Valider l'intégrité du lock
gpi replay gpi.lock --check
```

Le `gpi.lock` contient la configuration complète, les modules résolus, les dépendances Python et un checksum SHA-256 pour détecter toute modification manuelle.

---

## Intégration IA Groq (optionnelle)

```bash
export GROQ_API_KEY=votre-cle-groq   # Linux/Mac
set GROQ_API_KEY=votre-cle-groq      # Windows CMD
$env:GROQ_API_KEY="votre-cle-groq"   # Windows PowerShell
```

Ou dans un fichier `.env` à la racine de votre projet :

```env
GROQ_API_KEY=votre-cle-groq
```

Fonctionnalités IA :
- **Suggestions de modules** basées sur la description de votre projet
- **Explication du code généré** : `gpi explain ./monprojet`

GPI fonctionne **entièrement hors-ligne** sans `GROQ_API_KEY`.

---

## Système de plugins

Créez et publiez vos propres modules GPI sur PyPI :

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
            description="Description de mon module",
            frameworks=["fastapi"],
            architectures=["monolithic"],
        )

    def get_dependencies(self):
        return ["ma-dependance>=1.0.0"]

    def get_files(self, config):
        return {"mon_fichier.py": "# Contenu généré"}
```

```bash
pip install mon-plugin-gpi
gpi plugin list   # Votre module apparaît automatiquement
```

---

## Format gpi.yaml complet

```yaml
name: monprojet          # Obligatoire : lettres/chiffres/underscores, 2-49 chars
framework: fastapi       # fastapi | flask | django
architecture: monolithic # monolithic | microservices
modules:
  - auth-jwt
  - database-postgres
  - cache-redis
  - docker
  - tests-pytest
description: "Mon API REST"
language: fr             # fr | en
port: 8000               # 1024-65535
use_groq_ai: false       # Active les suggestions IA
```

---

## Développement

```bash
git clone https://github.com/elkast/py_gpi
cd py_gpi
pip install -e ".[dev]"
pytest tests/ -v
```

---

*Créé par **SOSSOU Elkast Orsini** · [GitHub](https://github.com/elkast/py_gpi) · [PyPI](https://pypi.org/project/py-gpi/)*
