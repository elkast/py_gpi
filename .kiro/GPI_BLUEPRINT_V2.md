# GPI v2 — Blueprint de Spécification Complète
## Document de référence pour implémentation par IA — Version définitive

> **Usage de ce document** : Ce fichier est la spécification technique exhaustive de GPI v2. Une IA qui reçoit ce document doit être capable de produire l'intégralité du code source, des tests, de la documentation et du packaging PyPI sans aucune information supplémentaire. Rien n'est omis volontairement.

---

## Table des matières

1. [Vision et positionnement](#1-vision-et-positionnement)
2. [Analyse critique de la v0.1](#2-analyse-critique-de-la-v01)
3. [Architecture globale du package](#3-architecture-globale-du-package)
4. [Contraintes système](#4-contraintes-système)
5. [Structure des fichiers du package](#5-structure-des-fichiers-du-package)
6. [Le moteur de modules](#6-le-moteur-de-modules)
7. [Le système CRUD académique — philosophie et implémentation](#7-le-système-crud-académique--philosophie-et-implémentation)
8. [L'intégration Groq AI](#8-lintégration-groq-ai)
9. [Interfaces utilisateur — CLI, API Python, YAML](#9-interfaces-utilisateur--cli-api-python-yaml)
10. [Le fichier gpi.lock et la reproductibilité](#10-le-fichier-gpilock-et-la-reproductibilité)
11. [Commandes gpi add et gpi upgrade](#11-commandes-gpi-add-et-gpi-upgrade)
12. [Le système de plugins](#12-le-système-de-plugins)
13. [Génération de projets — templates détaillés](#13-génération-de-projets--templates-détaillés)
14. [Tests du package GPI lui-même](#14-tests-du-package-gpi-lui-même)
15. [Packaging et déploiement PyPI](#15-packaging-et-déploiement-pypi)
16. [Documentation utilisateur générée](#16-documentation-utilisateur-générée)
17. [Roadmap versionnée](#17-roadmap-versionnée)

---

## 1. Vision et positionnement

### 1.1 Définition

GPI (Générateur de Projet Intelligent) est un **compositeur de projets backend Python** à interface CLI, API Python et fichier de configuration déclaratif. Il ne copie pas des templates statiques — il **compose** un projet à partir de modules indépendants, résoud leurs dépendances, et génère un projet production-ready cohérent.

### 1.2 Positionnement concurrentiel

| Outil | Approche | Mise à jour | Modules | IA intégrée |
|-------|----------|-------------|---------|-------------|
| Cookiecutter | Templates Jinja2, copie statique | ❌ | ❌ | ❌ |
| Copier | Templates avec updates | ✅ partiel | ❌ | ❌ |
| Django startproject | Monolithique Django uniquement | ❌ | ❌ | ❌ |
| **GPI v2** | **Compositeur modulaire** | **✅ complet** | **✅ résolution** | **✅ Groq** |

### 1.3 La promesse centrale

> "Génère ton projet en 30 secondes. Fais-le évoluer en une commande. Laisse l'IA compléter ce que tu n'as pas défini."

GPI doit être à Python backend ce que `create-react-app` était à React — mais avec la capacité unique de **mettre à jour** un projet existant, chose qu'aucun outil ne fait bien aujourd'hui.

### 1.4 Cibles utilisateurs

- **Étudiant / débutant** : premier projet FastAPI sans se perdre dans la configuration
- **Développeur junior** : projet avec auth, DB, tests, prêt à déployer
- **Développeur senior** : scaffold production-ready, microservices, monitoring
- **Enseignant Python** : démonstration pédagogique du CRUD en microservices
- **Équipe** : template d'équipe standardisé, reproductible via `gpi.lock`

---

## 2. Analyse critique de la v0.1

### 2.1 Incohérences identifiées

**Problème 1 — Niveaux arbitraires**
Les niveaux `debutant / intermediaire / expert` sont une interface paternaliste. Un développeur ne devrait pas s'auto-évaluer — il devrait déclarer ses besoins. À supprimer complètement.

**Problème 2 — `route_org: single | split` non documenté**
Cette option est listée dans la référence YAML mais jamais expliquée. Ni l'interface CLI ni la documentation ne précisent ce qu'elle change. C'est soit à documenter exhaustivement, soit à retirer.

**Problème 3 — `langue: bilingue` n'a pas de sens**
Un projet de code n'est pas "bilingue". Les commentaires en deux langues créent du bruit. Cette option doit être retirée. Les options valides sont `fr` (commentaires en français) et `en` (commentaires en anglais).

**Problème 4 — Microservices "déconseillé pour débutants" mais disponible**
Si c'est dangereux pour un débutant, le moteur doit bloquer avec un message clair, pas juste une note dans un tableau markdown. La v2 gère cela via la validation du moteur de résolution.

**Problème 5 — Pas de reproductibilité**
Aucun mécanisme pour reproduire exactement un projet généré 6 mois plus tard. La v2 introduit `gpi.lock`.

**Problème 6 — Templates statiques**
Le code généré est copié tel quel, sans composition ni résolution de dépendances entre modules. Un projet FastAPI + JWT + PostgreSQL + Redis est aujourd'hui un template monolithique, pas la composition de 4 modules.

### 2.2 Ce qui fonctionne et doit être conservé

- L'interface CLI interactive (à améliorer, pas à remplacer)
- Le support de FastAPI, Flask, Django
- La détection IP réseau pour les tests mobiles
- Le mode fichier de configuration YAML
- La génération de Docker, tests pytest, README

---

## 3. Architecture globale du package

### 3.1 Vue d'ensemble des couches

```
┌─────────────────────────────────────────────────────┐
│                   INTERFACE UTILISATEUR              │
│  CLI interactive  │  gpi.yaml/toml  │  API Python   │
├─────────────────────────────────────────────────────┤
│                  MOTEUR DE RÉSOLUTION                │
│  Validation des modules  │  Résolution des deps      │
│  Détection des conflits  │  Validation des combos   │
├─────────────────────────────────────────────────────┤
│               REGISTRE DE MODULES                    │
│  auth-jwt  │  database-postgres  │  cache-redis      │
│  queue-celery  │  docker  │  tests-pytest  │  ...   │
├─────────────────────────────────────────────────────┤
│                   MOTEUR GROQ AI                     │
│  Suggestions  │  Complétion  │  Explication code    │
├─────────────────────────────────────────────────────┤
│                   COMPOSITEUR                        │
│  Assemblage  │  Injection deps  │  Rendu templates  │
├─────────────────────────────────────────────────────┤
│                    SORTIE                            │
│  Projet généré  │  gpi.lock  │  README.md généré   │
└─────────────────────────────────────────────────────┘
```

### 3.2 Flux de données

```
Entrée utilisateur
        │
        ▼
┌───────────────┐
│ Config Parser │  ← CLI interactive OU gpi.yaml OU API Python
└───────┬───────┘
        │
        ▼
┌───────────────┐
│   Validator   │  ← Vérifie les combos valides (ex: microservices + débutant = ERREUR)
└───────┬───────┘
        │
        ▼
┌───────────────┐
│ Groq AI       │  ← Si GROQ_API_KEY présent : suggestions, complétion des champs vides
│ (optionnel)   │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│ Resolver      │  ← Résoud les dépendances inter-modules
└───────┬───────┘
        │
        ▼
┌───────────────┐
│ Composer      │  ← Assemble les fichiers depuis les modules
└───────┬───────┘
        │
        ▼
┌───────────────┐
│ Writer        │  ← Écrit les fichiers + génère gpi.lock
└───────────────┘
```

---

## 4. Contraintes système

### 4.1 Python

- **Version minimale supportée** : Python 3.9
- **Version recommandée** : Python 3.11+
- **Raison** : `tomllib` (stdlib) disponible dès 3.11 ; typing améliorée depuis 3.9

### 4.2 Systèmes d'exploitation

| OS | Supporté | Notes |
|----|----------|-------|
| Windows 10/11 | ✅ | PATH doit inclure `Scripts/` Python |
| macOS 12+ | ✅ | |
| Ubuntu 20.04+ | ✅ | |
| Debian 11+ | ✅ | |
| WSL2 | ✅ | Traité comme Linux |
| Windows 7/8 | ❌ | Non supporté |

### 4.3 Dépendances du package GPI lui-même

```toml
# pyproject.toml [project.dependencies]
dependencies = [
    "typer[all]>=0.9.0",          # CLI avec rich
    "rich>=13.0.0",                # Affichage terminal
    "jinja2>=3.1.0",               # Rendu de templates
    "pyyaml>=6.0",                 # Parsing YAML
    "tomli>=2.0.0; python_version < '3.11'",  # TOML pour Python < 3.11
    "pydantic>=2.0.0",             # Validation de la configuration
    "groq>=0.4.0",                 # SDK Groq officiel (optionnel à l'usage)
    "httpx>=0.24.0",               # Requêtes HTTP (détection IP, appels Groq)
    "packaging>=23.0",             # Comparaison de versions pour gpi.lock
]
```

### 4.4 Dépendances optionnelles

```toml
[project.optional-dependencies]
ai = ["groq>=0.4.0"]              # Fonctionnalités Groq AI
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "pytest-asyncio>=0.21",
    "black>=23.0",
    "ruff>=0.1.0",
    "mypy>=1.0",
]
```

### 4.5 Variables d'environnement reconnues par GPI

| Variable | Usage | Obligatoire |
|----------|-------|-------------|
| `GROQ_API_KEY` | Active les fonctionnalités IA | Non |
| `GPI_NO_NETWORK` | Désactive la détection IP | Non |
| `GPI_DEFAULT_FRAMEWORK` | Framework par défaut | Non |
| `GPI_TEMPLATES_DIR` | Répertoire de templates personnalisés | Non |
| `GPI_PLUGINS_DIR` | Répertoire de plugins locaux | Non |

### 4.6 Contraintes de naming des projets

Un nom de projet valide doit respecter :
```
^[a-zA-Z][a-zA-Z0-9_]{1,48}$
```

Règles :
- Commence par une lettre
- Contient uniquement lettres, chiffres, underscores
- Longueur : 2 à 49 caractères
- Pas d'espace, pas de tiret, pas de caractère spécial
- Le nom sera utilisé comme nom de dossier et nom de module Python

### 4.7 Contraintes réseau

- La détection IP utilise `socket.gethostbyname(socket.gethostname())` — ne nécessite pas internet
- L'appel Groq AI nécessite internet et une clé API valide
- GPI fonctionne **entièrement hors-ligne** si `GROQ_API_KEY` absent

---

## 5. Structure des fichiers du package

### 5.1 Structure complète du repository GPI

```
py_gpi/                              ← Racine du repository GitHub
│
├── pyproject.toml                   ← Configuration du package (PEP 517/518)
├── README.md                        ← Documentation principale
├── CHANGELOG.md                     ← Historique des versions
├── LICENSE                          ← MIT
├── .gitignore
├── .github/
│   └── workflows/
│       ├── test.yml                 ← CI : tests sur Python 3.9, 3.10, 3.11, 3.12
│       └── publish.yml              ← CD : publication PyPI sur tag
│
├── gpi/                             ← Package Python principal
│   ├── __init__.py                  ← Version, exports publics
│   ├── __main__.py                  ← Permet `python -m gpi`
│   │
│   ├── cli/                         ← Interface ligne de commande
│   │   ├── __init__.py
│   │   ├── app.py                   ← Application Typer principale
│   │   ├── commands/
│   │   │   ├── __init__.py
│   │   │   ├── init.py              ← Commande `gpi init`
│   │   │   ├── add.py               ← Commande `gpi add <module>`
│   │   │   ├── upgrade.py           ← Commande `gpi upgrade`
│   │   │   ├── replay.py            ← Commande `gpi replay gpi.lock`
│   │   │   ├── plugin.py            ← Commande `gpi plugin`
│   │   │   └── version.py           ← Commande `gpi version`
│   │   └── interactive.py           ← Assistant interactif (questionnaire)
│   │
│   ├── core/                        ← Logique métier centrale
│   │   ├── __init__.py
│   │   ├── config.py                ← Modèles Pydantic de configuration
│   │   ├── resolver.py              ← Moteur de résolution des dépendances
│   │   ├── validator.py             ← Validation des combinaisons de modules
│   │   ├── composer.py              ← Assemblage du projet final
│   │   ├── writer.py                ← Écriture des fichiers sur disque
│   │   └── lock.py                  ← Gestion de gpi.lock
│   │
│   ├── modules/                     ← Registre des modules disponibles
│   │   ├── __init__.py              ← Registre central
│   │   ├── registry.py              ← Chargement et indexation des modules
│   │   ├── base.py                  ← Classe de base Module
│   │   │
│   │   ├── framework/               ← Modules framework
│   │   │   ├── fastapi.py
│   │   │   ├── flask.py
│   │   │   └── django.py
│   │   │
│   │   ├── auth/                    ← Modules authentification
│   │   │   ├── jwt.py
│   │   │   ├── sessions.py
│   │   │   └── oauth2.py
│   │   │
│   │   ├── database/               ← Modules base de données
│   │   │   ├── sqlite.py
│   │   │   ├── postgres.py
│   │   │   └── mysql.py
│   │   │
│   │   ├── cache/
│   │   │   └── redis.py
│   │   │
│   │   ├── queue/
│   │   │   ├── celery.py
│   │   │   └── rq.py
│   │   │
│   │   ├── infra/
│   │   │   ├── docker.py
│   │   │   ├── docker_compose.py
│   │   │   └── github_actions.py
│   │   │
│   │   ├── testing/
│   │   │   └── pytest.py
│   │   │
│   │   └── monitoring/
│   │       └── prometheus_grafana.py
│   │
│   ├── templates/                   ← Templates Jinja2
│   │   ├── fastapi/
│   │   │   ├── monolithic/          ← Structure monolithique FastAPI
│   │   │   └── microservices/       ← Structure microservices FastAPI
│   │   ├── flask/
│   │   │   ├── monolithic/
│   │   │   └── microservices/
│   │   └── django/
│   │       └── monolithic/
│   │
│   ├── ai/                          ← Intégration Groq
│   │   ├── __init__.py
│   │   ├── client.py                ← Client Groq avec gestion d'erreurs
│   │   ├── suggestions.py           ← Suggestions de modules
│   │   ├── completion.py            ← Complétion des champs manquants
│   │   └── explainer.py             ← Explication du code généré
│   │
│   └── utils/
│       ├── __init__.py
│       ├── network.py               ← Détection IP réseau
│       ├── filesystem.py            ← Opérations fichiers sécurisées
│       └── display.py               ← Affichage Rich
│
└── tests/                           ← Tests du package GPI
    ├── __init__.py
    ├── conftest.py
    ├── test_config.py
    ├── test_resolver.py
    ├── test_validator.py
    ├── test_composer.py
    ├── test_lock.py
    ├── test_cli.py
    ├── test_ai.py
    └── integration/
        ├── test_fastapi_generation.py
        ├── test_flask_generation.py
        ├── test_django_generation.py
        └── test_microservices.py
```

---

## 6. Le moteur de modules

### 6.1 Classe de base `Module`

```python
# gpi/modules/base.py

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ModuleMetadata:
    """Métadonnées d'un module GPI."""
    id: str                          # Ex: "auth-jwt"
    name: str                        # Ex: "Authentification JWT"
    version: str                     # Ex: "1.0.0"
    description: str
    frameworks: list[str]            # ["fastapi", "flask", "django"] ou sous-ensemble
    architectures: list[str]         # ["monolithic", "microservices"] ou sous-ensemble
    requires: list[str] = field(default_factory=list)   # Modules requis
    conflicts: list[str] = field(default_factory=list)  # Modules incompatibles
    optional: list[str] = field(default_factory=list)   # Modules optionnels suggérés
    tags: list[str] = field(default_factory=list)       # Pour la recherche


class Module(ABC):
    """Classe de base pour tous les modules GPI."""

    @property
    @abstractmethod
    def metadata(self) -> ModuleMetadata:
        """Retourne les métadonnées du module."""
        ...

    @abstractmethod
    def get_dependencies(self) -> list[str]:
        """
        Retourne la liste des packages Python à ajouter à requirements.txt.
        Ex: ["python-jose[cryptography]>=3.3.0", "passlib[bcrypt]>=1.7.4"]
        """
        ...

    @abstractmethod
    def get_files(self, config: "ProjectConfig") -> dict[str, str]:
        """
        Retourne un dictionnaire {chemin_relatif: contenu_du_fichier}.
        Le contenu peut être une chaîne Jinja2 ou du texte brut.
        Ex: {"auth/security.py": "...", "auth/routes.py": "..."}
        """
        ...

    def get_env_vars(self) -> dict[str, str]:
        """
        Retourne les variables d'environnement à ajouter au .env.
        Ex: {"SECRET_KEY": "your-secret-key-here", "JWT_ALGORITHM": "HS256"}
        """
        return {}

    def get_env_example_vars(self) -> dict[str, str]:
        """Retourne les variables pour .env.example (valeurs fictives/vides)."""
        return {}

    def post_generate_instructions(self) -> list[str]:
        """
        Instructions affichées à l'utilisateur après la génération.
        Ex: ["Initialisez la base: python manage.py migrate"]
        """
        return []
```

### 6.2 Le Resolver — résolution des dépendances

```python
# gpi/core/resolver.py

from dataclasses import dataclass
from typing import Optional
from gpi.modules.registry import ModuleRegistry
from gpi.core.config import ProjectConfig
from gpi.core.exceptions import (
    ModuleNotFoundError,
    ModuleConflictError,
    ModuleIncompatibleError,
    CircularDependencyError,
)


@dataclass
class ResolutionResult:
    modules: list[str]          # Ordre de résolution final
    auto_added: list[str]       # Modules ajoutés automatiquement
    warnings: list[str]         # Avertissements non bloquants


class Resolver:
    """
    Résoud les dépendances entre modules GPI.
    Algorithme : tri topologique avec détection de cycles.
    """

    def __init__(self, registry: ModuleRegistry):
        self.registry = registry

    def resolve(self, config: ProjectConfig) -> ResolutionResult:
        """
        Résoud la liste de modules demandés + leurs dépendances.

        Étapes :
        1. Validation existence de chaque module
        2. Validation compatibilité framework/architecture
        3. Résolution récursive des dépendances (DFS)
        4. Détection de conflits
        5. Détection de cycles
        6. Tri topologique final
        """
        requested = set(config.modules)
        resolved = []
        auto_added = []
        warnings = []
        visiting = set()
        visited = set()

        def visit(module_id: str, required_by: Optional[str] = None):
            if module_id in visited:
                return
            if module_id in visiting:
                raise CircularDependencyError(
                    f"Dépendance circulaire détectée impliquant '{module_id}'"
                )

            module = self.registry.get(module_id)
            if module is None:
                raise ModuleNotFoundError(
                    f"Module '{module_id}' introuvable dans le registre"
                )

            # Vérification framework
            if config.framework not in module.metadata.frameworks:
                raise ModuleIncompatibleError(
                    f"Le module '{module_id}' ne supporte pas le framework "
                    f"'{config.framework}'. Frameworks supportés : "
                    f"{module.metadata.frameworks}"
                )

            # Vérification architecture
            if config.architecture not in module.metadata.architectures:
                raise ModuleIncompatibleError(
                    f"Le module '{module_id}' ne supporte pas l'architecture "
                    f"'{config.architecture}'"
                )

            # Vérification conflits
            for conflict in module.metadata.conflicts:
                if conflict in requested or conflict in auto_added:
                    raise ModuleConflictError(
                        f"'{module_id}' est incompatible avec '{conflict}'"
                    )

            visiting.add(module_id)

            # Résolution récursive des dépendances
            for dep in module.get_dependencies():
                if dep not in requested and dep not in auto_added:
                    auto_added.append(dep)
                    warnings.append(
                        f"Module '{dep}' ajouté automatiquement "
                        f"(requis par '{module_id}')"
                    )
                visit(dep)

            visiting.remove(module_id)
            visited.add(module_id)
            resolved.append(module_id)

        # Toujours résoudre le framework en premier
        visit(f"framework-{config.framework}")

        # Résoudre chaque module demandé
        for module_id in config.modules:
            visit(module_id)

        return ResolutionResult(
            modules=resolved,
            auto_added=auto_added,
            warnings=warnings,
        )
```

### 6.3 Le Validator — règles métier

```python
# gpi/core/validator.py

from gpi.core.config import ProjectConfig
from gpi.core.exceptions import ValidationError


# Règles de validation exprimées de façon déclarative
VALIDATION_RULES = [
    {
        "condition": lambda c: c.architecture == "microservices" and len(c.modules) < 2,
        "message": (
            "L'architecture microservices nécessite au moins 2 services. "
            "Ajoutez des modules (ex: auth-jwt, database-postgres) ou "
            "utilisez l'architecture monolithique."
        ),
        "blocking": True,
    },
    {
        "condition": lambda c: "auth-oauth2" in c.modules and "auth-jwt" in c.modules,
        "message": "Choisissez un seul mécanisme d'authentification : auth-jwt OU auth-oauth2.",
        "blocking": True,
    },
    {
        "condition": lambda c: "queue-celery" in c.modules and "cache-redis" not in c.modules,
        "message": (
            "Celery nécessite un broker. Le module cache-redis sera ajouté "
            "automatiquement comme broker Celery."
        ),
        "blocking": False,  # Avertissement, pas erreur bloquante
    },
    {
        "condition": lambda c: c.framework == "django" and "auth-jwt" in c.modules,
        "message": (
            "Django dispose d'un système d'auth intégré. "
            "auth-jwt utilisera djangorestframework-simplejwt."
        ),
        "blocking": False,
    },
    {
        "condition": lambda c: (
            c.architecture == "microservices" and
            c.framework == "django"
        ),
        "message": (
            "Django en microservices est une architecture avancée. "
            "FastAPI est recommandé pour les microservices Python."
        ),
        "blocking": False,
    },
]


class Validator:
    def validate(self, config: ProjectConfig) -> list[str]:
        """
        Valide la configuration. Lève une ValidationError si bloquant.
        Retourne la liste des avertissements non bloquants.
        """
        warnings = []

        for rule in VALIDATION_RULES:
            if rule["condition"](config):
                if rule["blocking"]:
                    raise ValidationError(rule["message"])
                else:
                    warnings.append(rule["message"])

        return warnings
```

### 6.4 Modèle de configuration Pydantic

```python
# gpi/core/config.py

from pydantic import BaseModel, field_validator, model_validator
from typing import Optional
import re


class ProjectConfig(BaseModel):
    """Configuration complète d'un projet GPI."""

    # Champs obligatoires
    framework: str                           # "fastapi" | "flask" | "django"
    architecture: str = "monolithic"         # "monolithic" | "microservices"
    name: str                                # Nom du projet
    modules: list[str] = []                  # Liste des modules

    # Champs optionnels avec valeurs par défaut
    description: str = ""
    language: str = "fr"                     # "fr" | "en"
    port: int = 8000
    services: list[str] = []                 # Pour microservices uniquement
    use_groq_ai: bool = False                # Active l'assistance IA

    @field_validator("framework")
    @classmethod
    def validate_framework(cls, v: str) -> str:
        allowed = ["fastapi", "flask", "django"]
        if v not in allowed:
            raise ValueError(f"framework doit être l'un de: {allowed}")
        return v

    @field_validator("architecture")
    @classmethod
    def validate_architecture(cls, v: str) -> str:
        allowed = ["monolithic", "microservices"]
        if v not in allowed:
            raise ValueError(f"architecture doit être l'une de: {allowed}")
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        pattern = r"^[a-zA-Z][a-zA-Z0-9_]{1,48}$"
        if not re.match(pattern, v):
            raise ValueError(
                "Le nom du projet doit commencer par une lettre, "
                "contenir uniquement des lettres/chiffres/underscores, "
                "et faire entre 2 et 49 caractères."
            )
        return v

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        allowed = ["fr", "en"]
        if v not in allowed:
            raise ValueError(f"language doit être l'un de: {allowed}")
        return v

    @field_validator("port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        if not (1024 <= v <= 65535):
            raise ValueError("port doit être entre 1024 et 65535")
        return v

    @model_validator(mode="after")
    def validate_microservices_services(self) -> "ProjectConfig":
        if self.architecture == "microservices" and not self.services:
            # Valeurs par défaut pour les microservices
            self.services = ["auth", "users", "products"]
        return self

    @classmethod
    def from_yaml(cls, path: str) -> "ProjectConfig":
        """Charge une configuration depuis un fichier YAML."""
        import yaml
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls(**data)

    @classmethod
    def from_toml(cls, path: str) -> "ProjectConfig":
        """Charge une configuration depuis un fichier TOML."""
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib
        with open(path, "rb") as f:
            data = tomllib.load(f)
        return cls(**data)
```

---

## 7. Le système CRUD académique — philosophie et implémentation

### 7.1 Le concept : CRUD atomisé par fichier

L'idée fondamentale est d'**enseigner le CRUD comme des opérations séparées et indépendantes**, chacune dans son propre fichier. C'est une décision pédagogique forte et validée par la pratique :

**Pourquoi séparer les fichiers ?**
- Un étudiant ouvre `create.py` et voit uniquement la logique de création. Pas de bruit.
- Un professeur peut demander "implémentez la suppression" et l'étudiant sait exactement où aller.
- Les tests unitaires mappent parfaitement : `test_create.py` teste `create.py`.
- En microservices réels, certaines opérations peuvent être scalées indépendamment.
- Correspond au pattern **CQRS** (Command Query Responsibility Segregation) — séparation des commandes (create/update/delete) et des requêtes (read).

**Validation académique de l'approche :**
Le pattern CRUD atomisé par fichier est utilisé dans des projets open source réels (voir `github.com/EigenvectorsAndChill/fastapi_crud`) et correspond à l'architecture recommandée par Microsoft pour les microservices .NET (eShopOnContainers).

### 7.2 Structure CRUD dans un projet monolithique

```
monapi/
├── app/
│   └── catalogue/                   ← Domaine "catalogue" (ou tout autre domaine)
│       ├── __init__.py
│       ├── create.py                ← POST   /catalogue/           Créer un item
│       ├── read.py                  ← GET    /catalogue/           Lister tous
│       │                            ← GET    /catalogue/{id}       Lire un item
│       ├── update.py                ← PUT    /catalogue/{id}       Remplacer
│       │                            ← PATCH  /catalogue/{id}       Modifier partiellement
│       └── delete.py                ← DELETE /catalogue/{id}       Supprimer
```

### 7.3 Contenu de `create.py` (FastAPI)

```python
# app/catalogue/create.py
"""
Opération CREATE — Catalogue
Crée un nouvel item dans le catalogue.
HTTP Method : POST
Endpoint    : /catalogue/
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.catalogue import CatalogueItem
from app.schemas.catalogue import CatalogueItemCreate, CatalogueItemResponse

router = APIRouter()


@router.post(
    "/",
    response_model=CatalogueItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un item",
    description="Crée un nouvel item dans le catalogue et retourne l'item créé.",
)
def create_item(
    item: CatalogueItemCreate,
    db: Session = Depends(get_db),
) -> CatalogueItemResponse:
    """
    Crée un item dans le catalogue.

    - **name** : Nom de l'item (obligatoire, 1-100 caractères)
    - **description** : Description optionnelle
    - **price** : Prix en nombre décimal positif
    - **stock** : Quantité en stock (entier >= 0)
    """
    # Vérification de l'unicité du nom
    existing = db.query(CatalogueItem).filter(
        CatalogueItem.name == item.name
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Un item nommé '{item.name}' existe déjà.",
        )

    db_item = CatalogueItem(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    return db_item
```

### 7.4 Contenu de `read.py` (FastAPI)

```python
# app/catalogue/read.py
"""
Opération READ — Catalogue
Récupère un ou plusieurs items du catalogue.
HTTP Methods : GET
Endpoints    : /catalogue/          Tous les items (avec pagination)
               /catalogue/{id}      Un item par ID
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.catalogue import CatalogueItem
from app.schemas.catalogue import CatalogueItemResponse, PaginatedResponse

router = APIRouter()


@router.get(
    "/",
    response_model=PaginatedResponse[CatalogueItemResponse],
    summary="Lister tous les items",
    description="Retourne la liste paginée des items du catalogue.",
)
def list_items(
    skip: int = Query(0, ge=0, description="Nombre d'items à ignorer (pagination)"),
    limit: int = Query(20, ge=1, le=100, description="Nombre max d'items retournés"),
    db: Session = Depends(get_db),
) -> PaginatedResponse[CatalogueItemResponse]:
    """Liste tous les items avec pagination offset/limit."""
    total = db.query(CatalogueItem).count()
    items = db.query(CatalogueItem).offset(skip).limit(limit).all()

    return PaginatedResponse(
        total=total,
        skip=skip,
        limit=limit,
        items=items,
    )


@router.get(
    "/{item_id}",
    response_model=CatalogueItemResponse,
    summary="Récupérer un item",
    description="Retourne un item spécifique par son identifiant.",
    responses={
        404: {"description": "Item non trouvé"},
    },
)
def get_item(
    item_id: int,
    db: Session = Depends(get_db),
) -> CatalogueItemResponse:
    """Récupère un item par son ID."""
    item = db.query(CatalogueItem).filter(CatalogueItem.id == item_id).first()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item avec l'ID {item_id} introuvable.",
        )

    return item
```

### 7.5 Contenu de `update.py` (FastAPI)

```python
# app/catalogue/update.py
"""
Opération UPDATE — Catalogue
Modifie un item existant du catalogue.
HTTP Methods : PUT   /catalogue/{id}   Remplacement complet
               PATCH /catalogue/{id}   Modification partielle
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.catalogue import CatalogueItem
from app.schemas.catalogue import (
    CatalogueItemUpdate,
    CatalogueItemPartialUpdate,
    CatalogueItemResponse,
)

router = APIRouter()


@router.put(
    "/{item_id}",
    response_model=CatalogueItemResponse,
    summary="Remplacer un item (remplacement complet)",
    description=(
        "Remplace entièrement un item. Tous les champs doivent être fournis. "
        "Les champs non fournis seront réinitialisés à leur valeur par défaut."
    ),
)
def replace_item(
    item_id: int,
    item_data: CatalogueItemUpdate,
    db: Session = Depends(get_db),
) -> CatalogueItemResponse:
    """PUT — Remplacement complet de l'item."""
    db_item = db.query(CatalogueItem).filter(CatalogueItem.id == item_id).first()

    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item avec l'ID {item_id} introuvable.",
        )

    # Remplacement complet : tous les champs sont mis à jour
    for field, value in item_data.model_dump().items():
        setattr(db_item, field, value)

    db.commit()
    db.refresh(db_item)
    return db_item


@router.patch(
    "/{item_id}",
    response_model=CatalogueItemResponse,
    summary="Modifier partiellement un item",
    description=(
        "Modifie uniquement les champs fournis. "
        "Les champs non fournis restent inchangés."
    ),
)
def partial_update_item(
    item_id: int,
    item_data: CatalogueItemPartialUpdate,
    db: Session = Depends(get_db),
) -> CatalogueItemResponse:
    """PATCH — Modification partielle de l'item."""
    db_item = db.query(CatalogueItem).filter(CatalogueItem.id == item_id).first()

    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item avec l'ID {item_id} introuvable.",
        )

    # Modification partielle : exclude_unset=True ignore les champs non fournis
    update_data = item_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(db_item, field, value)

    db.commit()
    db.refresh(db_item)
    return db_item
```

### 7.6 Contenu de `delete.py` (FastAPI)

```python
# app/catalogue/delete.py
"""
Opération DELETE — Catalogue
Supprime un item du catalogue.
HTTP Method : DELETE
Endpoint    : /catalogue/{id}
"""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.catalogue import CatalogueItem

router = APIRouter()


@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer un item",
    description=(
        "Supprime définitivement un item du catalogue. "
        "Retourne HTTP 204 (No Content) en cas de succès."
    ),
    responses={
        204: {"description": "Item supprimé avec succès"},
        404: {"description": "Item non trouvé"},
    },
)
def delete_item(
    item_id: int,
    db: Session = Depends(get_db),
) -> Response:
    """
    Supprime un item par son ID.

    Note : DELETE est idempotent par nature REST.
    Retourner 404 si l'item n'existe pas est une décision de design valide.
    Retourner 204 même si l'item n'existe pas (idempotence totale) est aussi valide.
    GPI choisit de retourner 404 pour la clarté des erreurs.
    """
    db_item = db.query(CatalogueItem).filter(CatalogueItem.id == item_id).first()

    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item avec l'ID {item_id} introuvable.",
        )

    db.delete(db_item)
    db.commit()

    # HTTP 204 : succès sans contenu de réponse
    return Response(status_code=status.HTTP_204_NO_CONTENT)
```

### 7.7 Assemblage des routers dans `main.py`

```python
# main.py
"""
Point d'entrée de l'application FastAPI.
Les opérations CRUD sont importées depuis leurs fichiers respectifs.
"""

from fastapi import FastAPI

# Import des routers CRUD séparés
from app.catalogue.create import router as catalogue_create_router
from app.catalogue.read import router as catalogue_read_router
from app.catalogue.update import router as catalogue_update_router
from app.catalogue.delete import router as catalogue_delete_router

app = FastAPI(
    title="{{ project_name }}",
    description="{{ project_description }}",
    version="1.0.0",
)

# Chaque opération CRUD est montée séparément
# Cela permet de désactiver/activer chaque opération indépendamment
app.include_router(catalogue_create_router, prefix="/catalogue", tags=["Catalogue — Create"])
app.include_router(catalogue_read_router,   prefix="/catalogue", tags=["Catalogue — Read"])
app.include_router(catalogue_update_router, prefix="/catalogue", tags=["Catalogue — Update"])
app.include_router(catalogue_delete_router, prefix="/catalogue", tags=["Catalogue — Delete"])
```

### 7.8 Structure CRUD en microservices

En mode microservices, **chaque service a son propre dossier CRUD** mais le principe reste identique :

```
monprojet/
├── docker-compose.yml
└── services/
    ├── catalogue/                   ← Service "catalogue" complet et autonome
    │   ├── main.py                  ← FastAPI app du service catalogue
    │   ├── database.py              ← DB propre au service (isolation)
    │   ├── models.py                ← Modèles SQLAlchemy
    │   ├── schemas.py               ← Schémas Pydantic
    │   ├── crud/                    ← Dossier CRUD atomisé
    │   │   ├── __init__.py
    │   │   ├── create.py            ← Logique + router CREATE
    │   │   ├── read.py              ← Logique + router READ
    │   │   ├── update.py            ← Logique + router UPDATE
    │   │   └── delete.py            ← Logique + router DELETE
    │   ├── Dockerfile
    │   ├── requirements.txt
    │   └── tests/
    │       ├── test_create.py
    │       ├── test_read.py
    │       ├── test_update.py
    │       └── test_delete.py
    │
    ├── auth/                        ← Service d'authentification (même structure)
    │   ├── main.py
    │   ├── crud/
    │   │   ├── create.py            ← Inscription
    │   │   ├── read.py              ← Récupérer profil
    │   │   ├── update.py            ← Modifier profil
    │   │   └── delete.py            ← Supprimer compte
    │   └── ...
    │
    └── users/                       ← Service utilisateurs
        └── ...
```

### 7.9 Schémas Pydantic du domaine catalogue

```python
# app/schemas/catalogue.py
"""
Schémas Pydantic pour le domaine Catalogue.
Séparation claire entre les schémas d'entrée et de sortie.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Generic, TypeVar
from datetime import datetime

T = TypeVar("T")


class CatalogueItemBase(BaseModel):
    """Champs communs à la création et à la mise à jour."""
    name: str = Field(..., min_length=1, max_length=100, description="Nom de l'item")
    description: Optional[str] = Field(None, max_length=500)
    price: float = Field(..., gt=0, description="Prix en euros, doit être positif")
    stock: int = Field(0, ge=0, description="Quantité en stock")


class CatalogueItemCreate(CatalogueItemBase):
    """Schéma pour la création d'un item (POST)."""
    pass


class CatalogueItemUpdate(CatalogueItemBase):
    """Schéma pour le remplacement complet (PUT). Tous les champs sont requis."""
    pass


class CatalogueItemPartialUpdate(BaseModel):
    """Schéma pour la modification partielle (PATCH). Tous les champs sont optionnels."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)


class CatalogueItemResponse(CatalogueItemBase):
    """Schéma de réponse — inclut les champs générés par la DB."""
    model_config = ConfigDict(from_attributes=True)  # Pydantic v2

    id: int
    created_at: datetime
    updated_at: datetime


class PaginatedResponse(BaseModel, Generic[T]):
    """Réponse paginée générique."""
    total: int
    skip: int
    limit: int
    items: list[T]
```

### 7.10 Modèle SQLAlchemy du catalogue

```python
# app/models/catalogue.py

from sqlalchemy import Column, Integer, String, Float, DateTime, func
from app.database import Base


class CatalogueItem(Base):
    """Modèle SQLAlchemy pour la table catalogue."""
    __tablename__ = "catalogue_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(String(500), nullable=True)
    price = Column(Float, nullable=False)
    stock = Column(Integer, nullable=False, default=0)

    # Timestamps automatiques
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<CatalogueItem(id={self.id}, name='{self.name}', price={self.price})>"
```

### 7.11 Tests CRUD séparés par opération

```python
# tests/test_create.py
"""Tests pour l'opération CREATE du catalogue."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from main import app

# Base de données de test en mémoire
SQLALCHEMY_TEST_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_TEST_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


class TestCreateCatalogue:
    """Tests pour POST /catalogue/"""

    def test_create_item_success(self, client):
        """Création d'un item valide."""
        payload = {"name": "Laptop Pro", "price": 1299.99, "stock": 5}
        response = client.post("/catalogue/", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Laptop Pro"
        assert data["price"] == 1299.99
        assert data["stock"] == 5
        assert "id" in data
        assert "created_at" in data

    def test_create_item_duplicate_name(self, client):
        """La création avec un nom dupliqué retourne 409."""
        payload = {"name": "Laptop Pro", "price": 999.0, "stock": 1}
        client.post("/catalogue/", json=payload)  # Premier item

        response = client.post("/catalogue/", json=payload)  # Doublon
        assert response.status_code == 409
        assert "existe déjà" in response.json()["detail"]

    def test_create_item_invalid_price(self, client):
        """Prix négatif ou zéro retourne 422."""
        payload = {"name": "Item Invalide", "price": -10.0, "stock": 1}
        response = client.post("/catalogue/", json=payload)
        assert response.status_code == 422

    def test_create_item_missing_required_field(self, client):
        """Champ obligatoire manquant retourne 422."""
        payload = {"price": 99.0}  # 'name' manquant
        response = client.post("/catalogue/", json=payload)
        assert response.status_code == 422
```

---

## 8. L'intégration Groq AI

### 8.1 Principe

Groq fournit une inférence LLM ultra-rapide (modèles Llama 3, Mixtral). L'intégration dans GPI est **optionnelle** et se déclenche uniquement si la variable `GROQ_API_KEY` est définie dans l'environnement. GPI reste 100% fonctionnel sans clé Groq.

### 8.2 Fonctionnalités IA de GPI

| Fonctionnalité | Commande | Description |
|----------------|----------|-------------|
| Suggestions de modules | `gpi init` (automatique) | Suggère des modules pertinents selon le projet décrit |
| Complétion de description | `gpi init` | Améliore la description du projet |
| Nommage de services | `gpi init --arch microservices` | Suggère des noms de services cohérents |
| Explication du projet généré | `gpi explain` | Explique le code généré en langage naturel |
| Révision de config | `gpi review gpi.yaml` | Analyse le fichier YAML et suggère des améliorations |

### 8.3 Client Groq

```python
# gpi/ai/client.py

import os
from typing import Optional
from groq import Groq, APIConnectionError, RateLimitError, APIStatusError


class GpiGroqClient:
    """
    Client Groq pour GPI.
    Gère l'authentification, les erreurs, les retries.
    """

    MODEL = "llama-3.3-70b-versatile"  # Modèle par défaut (équilibre vitesse/qualité)
    FAST_MODEL = "llama-3.1-8b-instant"  # Pour les requêtes rapides

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        self._client: Optional[Groq] = None

    @property
    def is_available(self) -> bool:
        """Retourne True si la clé API est configurée."""
        return bool(self.api_key)

    def _get_client(self) -> Groq:
        if not self.is_available:
            raise RuntimeError(
                "GROQ_API_KEY non configurée. "
                "Ajoutez 'GROQ_API_KEY=votre-cle' à votre fichier .env "
                "ou définissez la variable d'environnement."
            )
        if self._client is None:
            self._client = Groq(api_key=self.api_key)
        return self._client

    def complete(
        self,
        prompt: str,
        system: str = "Tu es un expert en développement backend Python.",
        model: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.3,
    ) -> str:
        """
        Envoie un prompt au modèle Groq et retourne la réponse.

        Args:
            prompt: Le message utilisateur
            system: Le message système (contexte)
            model: Le modèle à utiliser (défaut: MODEL)
            max_tokens: Nombre maximum de tokens en sortie
            temperature: Créativité (0 = déterministe, 1 = créatif)

        Returns:
            La réponse textuelle du modèle

        Raises:
            RuntimeError: Si la clé API n'est pas configurée
            Exception: En cas d'erreur API Groq
        """
        client = self._get_client()

        try:
            response = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                model=model or self.MODEL,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.choices[0].message.content

        except APIConnectionError:
            raise Exception(
                "Impossible de contacter l'API Groq. Vérifiez votre connexion internet."
            )
        except RateLimitError:
            raise Exception(
                "Limite de taux Groq atteinte. Réessayez dans quelques secondes."
            )
        except APIStatusError as e:
            raise Exception(f"Erreur Groq API (status {e.status_code}): {e.message}")
```

### 8.4 Suggestions de modules

```python
# gpi/ai/suggestions.py

import json
from gpi.ai.client import GpiGroqClient


SYSTEM_PROMPT = """Tu es un expert en architecture backend Python.
Tu dois suggérer des modules GPI pertinents pour un projet donné.
Tu ne réponds qu'en JSON valide, sans explication supplémentaire.
Les modules disponibles sont :
- auth-jwt : Authentification JSON Web Token
- auth-sessions : Authentification par sessions
- database-sqlite : Base de données SQLite (développement)
- database-postgres : Base de données PostgreSQL (production)
- cache-redis : Cache Redis
- queue-celery : File de tâches Celery
- queue-rq : File de tâches RQ (plus simple que Celery)
- docker : Containerisation Docker
- docker-compose : Orchestration multi-conteneurs
- tests-pytest : Tests automatisés Pytest
- monitoring-prometheus : Métriques Prometheus + Grafana
- github-actions : CI/CD GitHub Actions
"""


def suggest_modules(
    description: str,
    framework: str,
    architecture: str,
    client: GpiGroqClient,
) -> list[str]:
    """
    Suggère des modules GPI basé sur la description du projet.

    Returns:
        Liste d'IDs de modules suggérés
    """
    prompt = f"""
Analyse ce projet et suggère les modules GPI appropriés :

Description : {description}
Framework   : {framework}
Architecture: {architecture}

Réponds avec un JSON de ce format exact :
{{
  "modules": ["auth-jwt", "database-postgres"],
  "reasoning": "Courte explication en 1 phrase"
}}

Ne suggère que les modules vraiment nécessaires. Évite la surIngénierie.
"""
    try:
        response = client.complete(
            prompt=prompt,
            system=SYSTEM_PROMPT,
            model=GpiGroqClient.FAST_MODEL,
            max_tokens=256,
            temperature=0.1,
        )
        data = json.loads(response.strip())
        return data.get("modules", [])
    except (json.JSONDecodeError, KeyError):
        return []  # Échec silencieux — GPI continue sans suggestion
```

### 8.5 Explication du code généré

```python
# gpi/ai/explainer.py

from pathlib import Path
from gpi.ai.client import GpiGroqClient


def explain_project(project_path: str, client: GpiGroqClient) -> str:
    """
    Génère une explication pédagogique du projet généré.
    Utile pour les enseignants et les étudiants.
    """
    path = Path(project_path)

    # Collecte des fichiers principaux pour le contexte
    files_content = {}
    for file in path.rglob("*.py"):
        if not any(p in str(file) for p in ["__pycache__", ".pyc", "venv"]):
            try:
                content = file.read_text(encoding="utf-8")
                rel_path = str(file.relative_to(path))
                files_content[rel_path] = content[:500]  # Limite pour le contexte
            except Exception:
                pass

    files_summary = "\n".join(
        f"--- {path} ---\n{content}"
        for path, content in list(files_content.items())[:10]
    )

    prompt = f"""
Voici la structure d'un projet backend Python généré par GPI :

{files_summary}

Explique ce projet de façon pédagogique pour un étudiant ou débutant :
1. Ce que fait chaque fichier principal (2-3 phrases par fichier)
2. Comment les fichiers interagissent
3. Comment lancer le projet
4. 3 étapes pour commencer à développer

Sois concis, clair, et pratique. Langage : français.
"""

    return client.complete(
        prompt=prompt,
        system="Tu es un professeur Python bienveillant et pédagogue.",
        max_tokens=1500,
        temperature=0.4,
    )
```

### 8.6 Commande `gpi explain`

```python
# gpi/cli/commands/explain.py

import typer
from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown
from gpi.ai.client import GpiGroqClient
from gpi.ai.explainer import explain_project

app = typer.Typer()
console = Console()


@app.command("explain")
def explain(
    project_path: str = typer.Argument(".", help="Chemin vers le projet généré"),
):
    """
    Demande à l'IA Groq d'expliquer le projet généré en langage clair.
    Nécessite GROQ_API_KEY dans l'environnement.
    """
    client = GpiGroqClient()

    if not client.is_available:
        console.print(
            "[yellow]⚠ GROQ_API_KEY non configurée. "
            "Ajoutez votre clé pour utiliser gpi explain.[/yellow]"
        )
        raise typer.Exit(1)

    if not Path(project_path).is_dir():
        console.print(f"[red]❌ Dossier introuvable : {project_path}[/red]")
        raise typer.Exit(1)

    with console.status("[bold green]L'IA analyse votre projet...[/bold green]"):
        explanation = explain_project(project_path, client)

    console.print(Markdown(explanation))
```

---

## 9. Interfaces utilisateur — CLI, API Python, YAML

### 9.1 Application CLI principale (Typer)

```python
# gpi/cli/app.py

import typer
from gpi.cli.commands import init, add, upgrade, replay, plugin, version, explain

app = typer.Typer(
    name="gpi",
    help="GPI — Générateur de Projet Intelligent pour Python backend",
    add_completion=True,
    no_args_is_help=True,
)

# Enregistrement des commandes
app.add_typer(init.app, name="init")
app.command("add")(add.add_module)
app.command("upgrade")(upgrade.upgrade_modules)
app.command("replay")(replay.replay_lock)
app.command("version")(version.show_version)
app.command("explain")(explain.explain)
app.add_typer(plugin.app, name="plugin")


def main():
    """Point d'entrée du package (défini dans pyproject.toml)."""
    app()
```

### 9.2 Interface YAML de configuration

Format complet du fichier `gpi.yaml` :

```yaml
# gpi.yaml — Configuration déclarative GPI v2
# Documentation complète : https://github.com/sossou-elkast/py_gpi

# ─── Informations du projet ───────────────────────────────────────────────────
name: monapi                         # Obligatoire. Lettres/chiffres/underscores.
description: "API de gestion de catalogue produits"
language: fr                         # "fr" | "en"

# ─── Architecture ─────────────────────────────────────────────────────────────
framework: fastapi                   # "fastapi" | "flask" | "django"
architecture: monolithic             # "monolithic" | "microservices"
port: 8000

# ─── Modules à inclure ────────────────────────────────────────────────────────
# Listez uniquement ce dont vous avez besoin.
# GPI résoudra les dépendances automatiquement.
modules:
  - auth-jwt
  - database-postgres
  - cache-redis
  - docker
  - tests-pytest

# ─── Configuration microservices (si architecture: microservices) ──────────────
services:
  - auth
  - catalogue
  - users
  - orders

# ─── Intégration IA ───────────────────────────────────────────────────────────
use_groq_ai: false                   # Active les suggestions IA si GROQ_API_KEY définie
```

### 9.3 Format TOML alternatif

```toml
# gpi.toml — Alternative YAML en TOML (Python 3.11+ natif)

name = "monapi"
description = "API de gestion de catalogue produits"
language = "fr"
framework = "fastapi"
architecture = "monolithic"
port = 8000
modules = ["auth-jwt", "database-postgres", "docker", "tests-pytest"]
```

### 9.4 API Python publique

```python
# Usage programmatique — intégration dans d'autres outils

import gpi

# Méthode 1 : génération directe
project = gpi.compose(
    name="monapi",
    framework="fastapi",
    architecture="monolithic",
    modules=["auth-jwt", "database-postgres", "docker"],
    description="Mon API REST",
    language="fr",
)
project.generate("./output")

# Méthode 2 : depuis un fichier de config
project = gpi.from_yaml("./gpi.yaml")
project.generate("./output")

# Méthode 3 : ajout de module à un projet existant
project = gpi.open("./monapi")  # Lit gpi.lock
project.add_module("cache-redis")
project.apply()  # Applique les modifications

# Méthode 4 : inspection
project = gpi.from_yaml("./gpi.yaml")
result = project.resolve()  # Retourne ResolutionResult
print(result.modules)       # Liste ordonnée des modules
print(result.auto_added)    # Modules ajoutés automatiquement
print(result.warnings)      # Avertissements
```

### 9.5 Interface interactive CLI détaillée

```
GPI — Générateur de Projet Intelligent v2.0
============================================

🤖 Mode IA actif (GROQ_API_KEY détectée)

Décrivez votre projet en quelques mots (optionnel, l'IA suggèrera les modules) :
→ API de gestion d'un catalogue de produits avec authentification

✨ L'IA suggère les modules suivants pour votre projet :
   • auth-jwt          — Authentification sécurisée par token
   • database-postgres — Base de données robuste pour la production
   • tests-pytest      — Tests automatisés
   Confirmer ces suggestions ? [O/n] : O

Quel framework souhaitez-vous utiliser ?
  1. fastapi  — Moderne, asynchrone, idéal pour API REST (recommandé)
  2. flask    — Léger et flexible, parfait pour prototypes
  3. django   — Tout-en-un, idéal pour applications complexes
  Votre choix [1] : 1

Quelle architecture ?
  1. monolithique   — Un seul projet, simple à démarrer (recommandé)
  2. microservices  — Plusieurs services indépendants (avancé)
  Votre choix [1] : 1

Nom du projet : mon_catalogue
Port d'écoute [8000] :

⏳ Résolution des modules...
   ✅ framework-fastapi   — inclus
   ✅ auth-jwt            — inclus
   ✅ database-postgres   — inclus
   ✅ tests-pytest        — inclus
   ℹ️  docker             — ajouté automatiquement (recommandé pour PostgreSQL)

⏳ Génération en cours...
   ✅ Structure de dossiers créée
   ✅ Fichiers CRUD générés (create.py, read.py, update.py, delete.py)
   ✅ Authentification JWT configurée
   ✅ SQLAlchemy + Alembic configurés
   ✅ Tests pytest générés
   ✅ Docker & docker-compose configurés
   ✅ README.md généré
   ✅ gpi.lock créé

✅ Projet généré avec succès dans "mon_catalogue/"

🚀 Pour démarrer :
   cd mon_catalogue
   pip install -r requirements.txt
   uvicorn main:app --reload
   # Swagger : http://localhost:8000/docs

📱 Test mobile (même réseau Wi-Fi) :
   http://192.168.1.42:8000

🤖 Pour une explication du code généré :
   gpi explain mon_catalogue/
```

---

## 10. Le fichier gpi.lock et la reproductibilité

### 10.1 Format du fichier gpi.lock

```json
{
  "gpi_version": "2.0.0",
  "generated_at": "2025-01-15T10:30:00Z",
  "config": {
    "name": "mon_catalogue",
    "framework": "fastapi",
    "architecture": "monolithic",
    "modules": ["auth-jwt", "database-postgres", "tests-pytest"],
    "language": "fr",
    "port": 8000
  },
  "resolved_modules": [
    {"id": "framework-fastapi", "version": "1.0.0", "auto": false},
    {"id": "auth-jwt",          "version": "1.2.0", "auto": false},
    {"id": "database-postgres", "version": "1.1.0", "auto": false},
    {"id": "tests-pytest",      "version": "1.0.0", "auto": false},
    {"id": "docker",            "version": "1.0.0", "auto": true}
  ],
  "python_dependencies": [
    "fastapi==0.109.0",
    "uvicorn[standard]==0.27.0",
    "sqlalchemy==2.0.25",
    "psycopg2-binary==2.9.9",
    "python-jose[cryptography]==3.3.0",
    "passlib[bcrypt]==1.7.4",
    "alembic==1.13.1",
    "pytest==7.4.4",
    "httpx==0.26.0"
  ],
  "checksum": "sha256:abc123def456..."
}
```

### 10.2 Commande `gpi replay`

```bash
# Reproduit exactement le projet original depuis le gpi.lock
gpi replay gpi.lock

# Dans un nouveau dossier
gpi replay gpi.lock --output ./nouveau_projet

# Vérification uniquement (sans génération)
gpi replay gpi.lock --check
```

### 10.3 Implémentation de gpi.lock

```python
# gpi/core/lock.py

import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from gpi.core.config import ProjectConfig
from gpi.core.resolver import ResolutionResult
import gpi


class LockFile:
    """Gestion du fichier gpi.lock."""

    FILENAME = "gpi.lock"

    @staticmethod
    def create(
        config: ProjectConfig,
        resolution: ResolutionResult,
        dependencies: list[str],
    ) -> dict:
        """Crée le contenu du fichier gpi.lock."""
        data = {
            "gpi_version": gpi.__version__,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "config": config.model_dump(),
            "resolved_modules": [
                {
                    "id": module_id,
                    "version": "1.0.0",  # Version du module dans le registre
                    "auto": module_id in resolution.auto_added,
                }
                for module_id in resolution.modules
            ],
            "python_dependencies": sorted(dependencies),
        }
        # Calcul du checksum pour intégrité
        content = json.dumps(data, sort_keys=True, ensure_ascii=False)
        data["checksum"] = f"sha256:{hashlib.sha256(content.encode()).hexdigest()}"
        return data

    @staticmethod
    def write(data: dict, output_dir: str) -> Path:
        """Écrit le fichier gpi.lock dans le dossier de sortie."""
        lock_path = Path(output_dir) / LockFile.FILENAME
        with open(lock_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return lock_path

    @staticmethod
    def read(path: str) -> dict:
        """Lit et valide un fichier gpi.lock."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Validation du checksum
        checksum = data.pop("checksum", None)
        if checksum:
            content = json.dumps(data, sort_keys=True, ensure_ascii=False)
            expected = f"sha256:{hashlib.sha256(content.encode()).hexdigest()}"
            if checksum != expected:
                raise ValueError(
                    "Le fichier gpi.lock est corrompu ou a été modifié manuellement."
                )
            data["checksum"] = checksum

        return data

    @staticmethod
    def to_config(lock_data: dict) -> ProjectConfig:
        """Reconstruit une ProjectConfig depuis un gpi.lock."""
        return ProjectConfig(**lock_data["config"])
```

---

## 11. Commandes `gpi add` et `gpi upgrade`

### 11.1 `gpi add` — Ajouter un module à un projet existant

```python
# gpi/cli/commands/add.py

import typer
from rich.console import Console
from pathlib import Path
from gpi.core.lock import LockFile
from gpi.core.resolver import Resolver
from gpi.core.composer import Composer
from gpi.modules.registry import ModuleRegistry

console = Console()


def add_module(
    module_id: str = typer.Argument(..., help="ID du module à ajouter (ex: cache-redis)"),
    project_path: str = typer.Option(".", "--path", "-p", help="Chemin vers le projet"),
):
    """
    Ajoute un module à un projet GPI existant.

    Exemples :
        gpi add cache-redis
        gpi add monitoring-prometheus --path ./monprojet
    """
    lock_path = Path(project_path) / LockFile.FILENAME

    if not lock_path.exists():
        console.print(
            f"[red]❌ Fichier gpi.lock introuvable dans '{project_path}'.[/red]\n"
            "Ce dossier n'est pas un projet GPI, ou le gpi.lock a été supprimé."
        )
        raise typer.Exit(1)

    # Lecture de la configuration existante
    lock_data = LockFile.read(str(lock_path))
    config = LockFile.to_config(lock_data)

    # Ajout du module
    if module_id in config.modules:
        console.print(f"[yellow]⚠ Le module '{module_id}' est déjà installé.[/yellow]")
        raise typer.Exit(0)

    config.modules.append(module_id)

    # Résolution et composition
    registry = ModuleRegistry()
    resolver = Resolver(registry)

    with console.status(f"[bold green]Résolution de '{module_id}'...[/bold green]"):
        result = resolver.resolve(config)

    for warning in result.warnings:
        console.print(f"[yellow]ℹ {warning}[/yellow]")

    # Application des modifications
    composer = Composer(registry)
    with console.status("[bold green]Application des modifications...[/bold green]"):
        new_files = composer.get_new_files(module_id, config)
        composer.apply_to_existing(new_files, project_path)
        LockFile.write(
            LockFile.create(config, result, composer.get_all_dependencies(result)),
            project_path,
        )

    console.print(f"[green]✅ Module '{module_id}' ajouté avec succès.[/green]")

    # Instructions post-installation
    module = registry.get(module_id)
    if module:
        for instruction in module.post_generate_instructions():
            console.print(f"   → {instruction}")
```

### 11.2 `gpi upgrade` — Mettre à jour les modules

```bash
# Mise à jour de tous les modules vers leurs dernières versions
gpi upgrade

# Mise à jour d'un module spécifique
gpi upgrade auth-jwt

# Voir ce qui serait mis à jour sans appliquer
gpi upgrade --dry-run
```

---

## 12. Le système de plugins

### 12.1 Architecture des plugins

Un plugin GPI est un package Python qui expose une classe héritant de `Module`. Il est déclaré via un `entry_point` dans son `pyproject.toml`.

```toml
# pyproject.toml d'un plugin tiers (ex: gpi-stripe)
[project.entry-points."gpi.modules"]
stripe = "gpi_stripe.module:StripeModule"
```

### 12.2 Commandes de gestion des plugins

```bash
# Installer un plugin depuis PyPI
gpi plugin install gpi-stripe

# Lister les plugins installés
gpi plugin list

# Désinstaller
gpi plugin uninstall gpi-stripe

# Publier son propre plugin (guide interactif)
gpi plugin publish ./mon-plugin
```

### 12.3 Registre des modules — chargement des plugins

```python
# gpi/modules/registry.py

import importlib.metadata
from gpi.modules.base import Module


class ModuleRegistry:
    """
    Registre central de tous les modules GPI (natifs + plugins).
    Charge les plugins via les entry_points Python.
    """

    ENTRY_POINT_GROUP = "gpi.modules"

    def __init__(self):
        self._modules: dict[str, Module] = {}
        self._load_builtin_modules()
        self._load_plugin_modules()

    def _load_builtin_modules(self):
        """Charge les modules natifs de GPI."""
        from gpi.modules.framework.fastapi import FastAPIModule
        from gpi.modules.framework.flask import FlaskModule
        from gpi.modules.framework.django import DjangoModule
        from gpi.modules.auth.jwt import JWTAuthModule
        from gpi.modules.database.postgres import PostgresModule
        from gpi.modules.database.sqlite import SQLiteModule
        from gpi.modules.cache.redis import RedisModule
        from gpi.modules.infra.docker import DockerModule
        from gpi.modules.testing.pytest import PytestModule

        for module_class in [
            FastAPIModule, FlaskModule, DjangoModule,
            JWTAuthModule, PostgresModule, SQLiteModule,
            RedisModule, DockerModule, PytestModule,
        ]:
            instance = module_class()
            self._modules[instance.metadata.id] = instance

    def _load_plugin_modules(self):
        """Charge les plugins installés via entry_points."""
        try:
            eps = importlib.metadata.entry_points(group=self.ENTRY_POINT_GROUP)
            for ep in eps:
                try:
                    module_class = ep.load()
                    instance = module_class()
                    self._modules[instance.metadata.id] = instance
                except Exception as e:
                    print(f"⚠ Impossible de charger le plugin '{ep.name}': {e}")
        except Exception:
            pass  # Pas de plugins installés

    def get(self, module_id: str) -> Module | None:
        return self._modules.get(module_id)

    def list_all(self) -> list[Module]:
        return list(self._modules.values())

    def search(self, query: str) -> list[Module]:
        """Recherche dans les tags, noms et descriptions."""
        query_lower = query.lower()
        return [
            m for m in self._modules.values()
            if (
                query_lower in m.metadata.id.lower() or
                query_lower in m.metadata.name.lower() or
                query_lower in m.metadata.description.lower() or
                any(query_lower in tag for tag in m.metadata.tags)
            )
        ]
```

---

## 13. Génération de projets — templates détaillés

### 13.1 Template `database.py` pour FastAPI + PostgreSQL

```python
# Template Jinja2 → gpi/templates/fastapi/monolithic/database.py.j2

"""
Configuration de la base de données.
Framework : FastAPI
Base      : {{ database }}
ORM       : SQLAlchemy 2.x
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import NullPool

# URL de connexion depuis les variables d'environnement
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    {% if database == "sqlite" %}
    "sqlite:///./{{ project_name }}.db"
    {% elif database == "postgresql" %}
    "postgresql://user:password@localhost:5432/{{ project_name }}"
    {% elif database == "mysql" %}
    "mysql+pymysql://user:password@localhost:3306/{{ project_name }}"
    {% endif %}
)

# Création du moteur SQLAlchemy
engine = create_engine(
    DATABASE_URL,
    {% if database == "sqlite" %}
    connect_args={"check_same_thread": False},
    {% else %}
    pool_pre_ping=True,   # Vérification de la connexion avant usage
    pool_size=10,         # Taille du pool de connexions
    max_overflow=20,      # Connexions additionnelles autorisées
    {% endif %}
)

# Factory de sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Classe de base pour tous les modèles SQLAlchemy."""
    pass


def get_db():
    """
    Dépendance FastAPI : fournit une session DB et la ferme après la requête.

    Usage dans un router :
        @router.get("/items")
        def list_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### 13.2 Template `docker-compose.yml`

```yaml
# Template Jinja2 → gpi/templates/fastapi/monolithic/docker-compose.yml.j2

version: "3.9"

services:
  app:
    build: .
    ports:
      - "{{ port }}:{{ port }}"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/{{ project_name }}
      {% if "cache-redis" in modules %}
      - REDIS_URL=redis://redis:6379/0
      {% endif %}
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
    command: uvicorn main:app --host 0.0.0.0 --port {{ port }} --reload

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
```

### 13.3 Template `requirements.txt`

```
# Template Jinja2 → gpi/templates/fastapi/monolithic/requirements.txt.j2

# Framework
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
python-dotenv>=1.0.0

# Validation
pydantic>=2.0.0
pydantic-settings>=2.0.0

{% if "database-sqlite" in modules or "database-postgres" in modules or "database-mysql" in modules %}
# Base de données
sqlalchemy>=2.0.0
alembic>=1.13.0
{% endif %}

{% if "database-postgres" in modules %}
psycopg2-binary>=2.9.0
{% endif %}

{% if "database-mysql" in modules %}
pymysql>=1.1.0
{% endif %}

{% if "auth-jwt" in modules %}
# Authentification JWT
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.7
{% endif %}

{% if "cache-redis" in modules %}
# Cache Redis
redis>=5.0.0
{% endif %}

{% if "queue-celery" in modules %}
# File de tâches
celery>=5.3.0
flower>=2.0.0  # Interface de monitoring Celery
{% endif %}

{% if "tests-pytest" in modules %}
# Tests
pytest>=7.4.0
pytest-cov>=4.1.0
httpx>=0.26.0
{% endif %}
```

### 13.4 Template `README.md` généré

```markdown
# Template Jinja2 → gpi/templates/common/README.md.j2

# {{ project_name }}

{{ description }}

*Généré avec [GPI](https://github.com/sossou-elkast/py_gpi) v{{ gpi_version }}*

## Installation rapide

\```bash
cd {{ project_name }}
pip install -r requirements.txt
cp .env.example .env  # Configurez vos variables d'environnement
\```

{% if "database-postgres" in modules %}
### Configuration de la base de données

1. Démarrez PostgreSQL (ou utilisez Docker)
2. Créez la base de données :
\```bash
createdb {{ project_name }}
\```
3. Appliquez les migrations :
\```bash
alembic upgrade head
\```
{% endif %}

## Lancer le projet

{% if framework == "fastapi" %}
\```bash
uvicorn main:app --reload --host 0.0.0.0 --port {{ port }}
\```
Documentation interactive : http://localhost:{{ port }}/docs
{% elif framework == "flask" %}
\```bash
python run.py
\```
{% elif framework == "django" %}
\```bash
python manage.py migrate
python manage.py runserver 0.0.0.0:{{ port }}
\```
Admin : http://localhost:{{ port }}/admin
{% endif %}

{% if "docker" in modules %}
## Avec Docker

\```bash
docker-compose up --build
\```
{% endif %}

## Structure du projet

\```
{{ project_name }}/
{% if architecture == "monolithic" %}
├── main.py              ← Point d'entrée
├── database.py          ← Connexion SQLAlchemy
├── app/
│   └── catalogue/       ← Domaine catalogue (exemple)
│       ├── create.py    ← POST  /catalogue/
│       ├── read.py      ← GET   /catalogue/ et /catalogue/{id}
│       ├── update.py    ← PUT/PATCH /catalogue/{id}
│       └── delete.py    ← DELETE /catalogue/{id}
├── models/              ← Modèles SQLAlchemy
├── schemas/             ← Schémas Pydantic
{% if "auth-jwt" in modules %}
├── auth/
│   ├── security.py      ← Hachage + JWT
│   └── routes.py        ← /auth/register, /auth/login
{% endif %}
{% if "tests-pytest" in modules %}
├── tests/
│   ├── test_create.py
│   ├── test_read.py
│   ├── test_update.py
│   └── test_delete.py
{% endif %}
├── .env
├── .env.example
├── requirements.txt
└── gpi.lock             ← Snapshot de génération (ne pas modifier)
{% endif %}
\```

## Tests

\```bash
pytest tests/ -v --cov=.
\```

## Tester sur mobile

Connectez votre mobile au même réseau Wi-Fi :

```
http://{{ network_ip }}:{{ port }}
```

---

Généré le {{ generated_at }} avec GPI v{{ gpi_version }}
Pour mettre à jour votre projet : \`gpi upgrade\`
```

---

## 14. Tests du package GPI lui-même

### 14.1 Stratégie de tests

- **Tests unitaires** : chaque composant isolé (Resolver, Validator, Composer, LockFile)
- **Tests d'intégration** : génération complète de projet + vérification de la structure
- **Tests CLI** : utilisation de `typer.testing.CliRunner`
- **Coverage cible** : ≥ 90%

### 14.2 Tests du Resolver

```python
# tests/test_resolver.py

import pytest
from gpi.core.config import ProjectConfig
from gpi.core.resolver import Resolver
from gpi.modules.registry import ModuleRegistry
from gpi.core.exceptions import ModuleNotFoundError, ModuleConflictError


@pytest.fixture
def resolver():
    return Resolver(ModuleRegistry())


class TestResolver:

    def test_resolve_simple_config(self, resolver):
        config = ProjectConfig(
            name="testapi",
            framework="fastapi",
            modules=["auth-jwt"],
        )
        result = resolver.resolve(config)
        assert "framework-fastapi" in result.modules
        assert "auth-jwt" in result.modules

    def test_resolve_auto_adds_dependencies(self, resolver):
        """Celery doit ajouter redis automatiquement."""
        config = ProjectConfig(
            name="testapi",
            framework="fastapi",
            modules=["queue-celery"],
        )
        result = resolver.resolve(config)
        assert "cache-redis" in result.modules
        assert "cache-redis" in result.auto_added

    def test_resolve_unknown_module_raises(self, resolver):
        config = ProjectConfig(
            name="testapi",
            framework="fastapi",
            modules=["module-inexistant"],
        )
        with pytest.raises(ModuleNotFoundError):
            resolver.resolve(config)

    def test_resolve_conflict_raises(self, resolver):
        config = ProjectConfig(
            name="testapi",
            framework="fastapi",
            modules=["auth-jwt", "auth-oauth2"],
        )
        with pytest.raises(ModuleConflictError):
            resolver.resolve(config)

    def test_resolve_framework_incompatibility_raises(self, resolver):
        """Un module Django-uniquement ne doit pas fonctionner avec FastAPI."""
        config = ProjectConfig(
            name="testapi",
            framework="fastapi",
            modules=["django-admin"],  # Module hypothétique Django uniquement
        )
        with pytest.raises(Exception):
            resolver.resolve(config)
```

### 14.3 Tests d'intégration de génération

```python
# tests/integration/test_fastapi_generation.py

import pytest
import tempfile
from pathlib import Path
from gpi.core.config import ProjectConfig
from gpi.core.resolver import Resolver
from gpi.core.composer import Composer
from gpi.core.writer import Writer
from gpi.modules.registry import ModuleRegistry


@pytest.fixture
def temp_output():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


class TestFastAPIGeneration:

    def test_minimal_fastapi_project(self, temp_output):
        """Un projet FastAPI minimal doit générer les fichiers essentiels."""
        config = ProjectConfig(
            name="testapi",
            framework="fastapi",
            modules=[],
        )
        registry = ModuleRegistry()
        resolver = Resolver(registry)
        result = resolver.resolve(config)

        composer = Composer(registry)
        files = composer.compose(config, result)

        writer = Writer()
        writer.write(files, temp_output)

        output = Path(temp_output)
        assert (output / "main.py").exists()
        assert (output / "requirements.txt").exists()
        assert (output / ".env.example").exists()
        assert (output / "README.md").exists()
        assert (output / "gpi.lock").exists()

    def test_fastapi_with_jwt_generates_auth_files(self, temp_output):
        """FastAPI + JWT doit générer les fichiers d'authentification."""
        config = ProjectConfig(
            name="testapi",
            framework="fastapi",
            modules=["auth-jwt"],
        )
        registry = ModuleRegistry()
        result = Resolver(registry).resolve(config)
        files = Composer(registry).compose(config, result)
        Writer().write(files, temp_output)

        output = Path(temp_output)
        assert (output / "auth" / "security.py").exists()
        assert (output / "auth" / "routes.py").exists()

    def test_fastapi_crud_generates_separate_files(self, temp_output):
        """Les fichiers CRUD doivent être séparés par opération."""
        config = ProjectConfig(
            name="testapi",
            framework="fastapi",
            modules=["database-sqlite"],
        )
        registry = ModuleRegistry()
        result = Resolver(registry).resolve(config)
        files = Composer(registry).compose(config, result)
        Writer().write(files, temp_output)

        output = Path(temp_output)
        crud_dir = output / "app" / "catalogue"
        assert (crud_dir / "create.py").exists()
        assert (crud_dir / "read.py").exists()
        assert (crud_dir / "update.py").exists()
        assert (crud_dir / "delete.py").exists()

    def test_gpi_lock_is_valid(self, temp_output):
        """Le fichier gpi.lock doit être valide et reproductible."""
        from gpi.core.lock import LockFile

        config = ProjectConfig(
            name="testapi",
            framework="fastapi",
            modules=["auth-jwt"],
        )
        registry = ModuleRegistry()
        result = Resolver(registry).resolve(config)
        files = Composer(registry).compose(config, result)
        Writer().write(files, temp_output)

        # Le lock doit être lisible et valide (checksum)
        lock_data = LockFile.read(str(Path(temp_output) / "gpi.lock"))
        assert lock_data["config"]["name"] == "testapi"
        assert lock_data["config"]["framework"] == "fastapi"
```

### 14.4 Configuration pytest

```toml
# pyproject.toml [tool.pytest.ini_options]
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--cov=gpi",
    "--cov-report=term-missing",
    "--cov-report=html",
    "--cov-fail-under=90",
    "-v",
]
```

---

## 15. Packaging et déploiement PyPI

### 15.1 `pyproject.toml` complet

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "py_gpi"
version = "2.0.0"
description = "GPI — Générateur de Projet Intelligent pour Python backend"
readme = "README.md"
license = { file = "LICENSE" }
requires-python = ">=3.9"
authors = [
    { name = "SOSSOU Elkast Orsini", email = "votre-email@example.com" },
]
keywords = [
    "project-generator", "scaffolding", "fastapi", "flask", "django",
    "backend", "python", "cli", "microservices", "crud", "boilerplate",
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Software Development :: Code Generators",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Environment :: Console",
]
dependencies = [
    "typer[all]>=0.9.0",
    "rich>=13.0.0",
    "jinja2>=3.1.0",
    "pyyaml>=6.0",
    "tomli>=2.0.0; python_version < '3.11'",
    "pydantic>=2.0.0",
    "httpx>=0.24.0",
    "packaging>=23.0",
    "groq>=0.4.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "black>=23.0",
    "ruff>=0.1.0",
    "mypy>=1.0",
]

[project.scripts]
gpi = "gpi.cli.app:main"

[project.entry-points."gpi.modules"]
# Les modules natifs sont chargés directement, pas via entry_points
# Cet espace est réservé aux plugins tiers

[project.urls]
Homepage = "https://github.com/sossou-elkast/py_gpi"
Documentation = "https://py-gpi.readthedocs.io"
Repository = "https://github.com/sossou-elkast/py_gpi"
"Bug Tracker" = "https://github.com/sossou-elkast/py_gpi/issues"
Changelog = "https://github.com/sossou-elkast/py_gpi/blob/main/CHANGELOG.md"

[tool.hatch.build.targets.wheel]
packages = ["gpi"]

[tool.hatch.build.targets.sdist]
include = [
    "gpi/",
    "tests/",
    "README.md",
    "CHANGELOG.md",
    "LICENSE",
    "pyproject.toml",
]

[tool.black]
line-length = 88
target-version = ["py39", "py310", "py311", "py312"]

[tool.ruff]
line-length = 88
select = ["E", "F", "I", "N", "W", "UP"]
ignore = ["E501"]

[tool.mypy]
python_version = "3.9"
strict = true
ignore_missing_imports = true
```

### 15.2 Workflow GitHub Actions — Tests

```yaml
# .github/workflows/test.yml

name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ["3.9", "3.10", "3.11", "3.12"]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          pip install -e ".[dev]"

      - name: Run linting
        run: |
          ruff check gpi/ tests/
          black --check gpi/ tests/

      - name: Run type checking
        run: |
          mypy gpi/

      - name: Run tests
        run: |
          pytest tests/ -v --cov=gpi --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          token: ${{ secrets.CODECOV_TOKEN }}
```

### 15.3 Workflow GitHub Actions — Publication PyPI

```yaml
# .github/workflows/publish.yml

name: Publish to PyPI

on:
  push:
    tags:
      - "v*"  # Se déclenche sur les tags type v2.0.0

jobs:
  publish:
    runs-on: ubuntu-latest
    environment: pypi

    permissions:
      id-token: write  # Pour Trusted Publisher (sans token PyPI secret)

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install build tools
        run: pip install hatch

      - name: Run tests before publish
        run: |
          pip install -e ".[dev]"
          pytest tests/ -v

      - name: Build package
        run: hatch build

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
```

### 15.4 Procédure de release

```bash
# 1. Mettre à jour CHANGELOG.md
# 2. Mettre à jour la version dans gpi/__init__.py
# 3. Commit
git add .
git commit -m "chore: release v2.0.0"

# 4. Créer le tag
git tag v2.0.0
git push origin main --tags

# Le workflow GitHub Actions publie automatiquement sur PyPI
```

---

## 16. Documentation utilisateur générée

### 16.1 Référence des modules disponibles

| ID | Nom | Frameworks | Description |
|----|-----|-----------|-------------|
| `auth-jwt` | Auth JWT | FastAPI, Flask, Django | JSON Web Tokens avec bcrypt |
| `auth-sessions` | Auth Sessions | Flask, Django | Sessions côté serveur |
| `auth-oauth2` | OAuth2 | FastAPI | OAuth2 avec scopes |
| `database-sqlite` | SQLite | Tous | SQLite (développement) |
| `database-postgres` | PostgreSQL | Tous | PostgreSQL production-ready |
| `database-mysql` | MySQL | Tous | MySQL/MariaDB |
| `cache-redis` | Redis Cache | Tous | Cache Redis |
| `queue-celery` | Celery | FastAPI, Flask | Tâches asynchrones Celery |
| `queue-rq` | RQ | FastAPI, Flask | Redis Queue (plus simple) |
| `docker` | Docker | Tous | Dockerfile + .dockerignore |
| `docker-compose` | Docker Compose | Tous | docker-compose.yml multi-services |
| `tests-pytest` | Pytest | Tous | Tests unitaires + intégration |
| `monitoring-prometheus` | Prometheus | FastAPI, Flask | Métriques + Grafana |
| `github-actions` | GitHub Actions | Tous | CI/CD GitHub |

### 16.2 Compatibilités modules/frameworks

| Module | FastAPI | Flask | Django |
|--------|---------|-------|--------|
| auth-jwt | ✅ | ✅ | ✅ (via DRF-simplejwt) |
| auth-sessions | ❌ | ✅ | ✅ (intégré Django) |
| auth-oauth2 | ✅ | ❌ | ❌ |
| database-* | ✅ | ✅ | ✅ |
| cache-redis | ✅ | ✅ | ✅ |
| queue-celery | ✅ | ✅ | ✅ |
| queue-rq | ✅ | ✅ | ❌ |
| monitoring-prometheus | ✅ | ✅ | ❌ |

### 16.3 Référence CLI complète v2

| Commande | Description |
|----------|-------------|
| `gpi init` | Assistant interactif |
| `gpi init -c gpi.yaml` | Depuis fichier de config |
| `gpi init --no-network` | Sans détection IP |
| `gpi add <module>` | Ajoute un module au projet existant |
| `gpi add <module> --path ./monprojet` | Dans un projet spécifique |
| `gpi upgrade` | Met à jour tous les modules |
| `gpi upgrade <module>` | Met à jour un module |
| `gpi upgrade --dry-run` | Aperçu sans application |
| `gpi replay gpi.lock` | Reproduit un projet depuis son lock |
| `gpi replay gpi.lock --output ./nouveau` | Dans un nouveau dossier |
| `gpi explain` | Explication IA du projet courant |
| `gpi explain ./monprojet` | Explication d'un projet spécifique |
| `gpi plugin install <pkg>` | Installe un plugin |
| `gpi plugin list` | Liste les plugins installés |
| `gpi plugin uninstall <pkg>` | Désinstalle un plugin |
| `gpi version` | Affiche la version GPI |
| `gpi --help` | Aide complète |
| `python -m gpi init` | Alternative si gpi non dans PATH |

### 16.4 Résolution de problèmes — guide exhaustif

**"gpi : commande introuvable"**

Windows PowerShell :
```powershell
python -c "import sysconfig; print(sysconfig.get_path('scripts'))"
# Copier le chemin affiché, puis :
$path = "C:\Users\VOTRE_NOM\AppData\Roaming\Python\Python3XX\Scripts"
[Environment]::SetEnvironmentVariable("Path", "$([Environment]::GetEnvironmentVariable('Path','User'));$path", "User")
# Redémarrez le terminal
```

Linux/macOS :
```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

Alternative universelle :
```bash
python -m gpi init
```

**"ModuleNotFoundError" lors du lancement du projet généré**
```bash
pip install -r requirements.txt
```

**"gpi.lock corrompu"**
Le fichier gpi.lock ne doit jamais être modifié manuellement. Pour le régénérer :
```bash
gpi replay gpi.yaml  # Si gpi.yaml existe
# ou
gpi init             # Régénérer depuis zéro
```

**"GROQ_API_KEY non configurée"**
```bash
# Ajouter dans .env :
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx
# Puis :
gpi explain  # Fonctionne maintenant
```

**Port déjà utilisé**
```bash
# FastAPI/Flask
uvicorn main:app --port 8001

# Django
python manage.py runserver 0.0.0.0:8001

# Ou modifier dans .env :
PORT=8001
```

---

## 17. Roadmap versionnée

### v0.2.0 — Corrections immédiates (avant tout nouveau développement)

- [ ] Supprimer les niveaux `debutant/intermediaire/expert`
- [ ] Supprimer `langue: bilingue`
- [ ] Documenter ou supprimer `route_org`
- [ ] Bloquer microservices si configuration invalide (au lieu d'un avertissement)
- [ ] Ajouter validation Pydantic de la configuration YAML
- [ ] Tests unitaires basiques (coverage ≥ 60%)

### v0.5.0 — Fondations de la v2

- [ ] Moteur de modules (classe `Module`, `ModuleRegistry`)
- [ ] Resolver avec résolution de dépendances
- [ ] Validator avec règles déclaratives
- [ ] Système de templates Jinja2
- [ ] Fichier `gpi.lock`
- [ ] Commande `gpi replay`
- [ ] CRUD atomisé par fichier (create.py, read.py, update.py, delete.py)
- [ ] Tests coverage ≥ 80%

### v1.0.0 — Version stable et complète

- [ ] Commande `gpi add <module>`
- [ ] Commande `gpi upgrade`
- [ ] Système de plugins avec `entry_points`
- [ ] Intégration Groq AI (suggestions, explication)
- [ ] Commande `gpi explain`
- [ ] API Python publique
- [ ] Support TOML en plus de YAML
- [ ] Documentation complète ReadTheDocs
- [ ] Tests coverage ≥ 90%
- [ ] Publication PyPI stable (pas alpha/beta)
- [ ] Support Windows/macOS/Linux validé en CI

### v1.5.0 — Écosystème

- [ ] `gpi plugin publish` — guide de publication de plugin
- [ ] Registry public des plugins communautaires
- [ ] Template Django REST Framework complet
- [ ] Module `github-actions` (CI/CD)
- [ ] Module `monitoring-prometheus`
- [ ] `gpi review gpi.yaml` — révision IA de la config

### v2.0.0 — Plateforme

- [ ] Interface web (optionnelle, distincte du CLI)
- [ ] `gpi doctor` — diagnostic de l'installation
- [ ] Support gRPC en plus de REST
- [ ] Templates GraphQL (Strawberry)
- [ ] Génération de documentation API automatique
- [ ] Intégration avec `uv` (gestionnaire de packages moderne)

---

## Annexe A — Exceptions personnalisées

```python
# gpi/core/exceptions.py


class GpiError(Exception):
    """Classe de base pour toutes les erreurs GPI."""
    pass


class ValidationError(GpiError):
    """Configuration invalide."""
    pass


class ModuleNotFoundError(GpiError):
    """Module demandé introuvable dans le registre."""
    pass


class ModuleConflictError(GpiError):
    """Deux modules incompatibles ont été demandés simultanément."""
    pass


class ModuleIncompatibleError(GpiError):
    """Module incompatible avec le framework ou l'architecture choisis."""
    pass


class CircularDependencyError(GpiError):
    """Dépendance circulaire détectée entre modules."""
    pass


class LockFileError(GpiError):
    """Erreur liée au fichier gpi.lock."""
    pass


class GroqAIError(GpiError):
    """Erreur lors de l'appel à l'API Groq."""
    pass
```

## Annexe B — `gpi/__init__.py`

```python
# gpi/__init__.py

"""
GPI — Générateur de Projet Intelligent
Compositeur de projets backend Python.

Usage CLI : gpi init
Usage API  : import gpi; project = gpi.compose(...)
"""

__version__ = "2.0.0"
__author__ = "SOSSOU Elkast Orsini"
__license__ = "MIT"

from gpi.core.config import ProjectConfig
from gpi.core.resolver import Resolver
from gpi.core.composer import Composer
from gpi.core.writer import Writer
from gpi.core.lock import LockFile
from gpi.modules.registry import ModuleRegistry


def compose(
    name: str,
    framework: str = "fastapi",
    architecture: str = "monolithic",
    modules: list[str] | None = None,
    description: str = "",
    language: str = "fr",
    port: int = 8000,
    use_groq_ai: bool = False,
) -> "GenerationPlan":
    """
    Crée un plan de génération de projet.

    Args:
        name        : Nom du projet
        framework   : "fastapi" | "flask" | "django"
        architecture: "monolithic" | "microservices"
        modules     : Liste d'IDs de modules (ex: ["auth-jwt", "database-postgres"])
        description : Description du projet
        language    : "fr" | "en"
        port        : Port d'écoute (défaut: 8000)
        use_groq_ai : Active les suggestions IA

    Returns:
        GenerationPlan avec méthode .generate(output_dir)

    Example:
        import gpi
        project = gpi.compose(
            name="monapi",
            framework="fastapi",
            modules=["auth-jwt", "database-postgres"],
        )
        project.generate("./output")
    """
    config = ProjectConfig(
        name=name,
        framework=framework,
        architecture=architecture,
        modules=modules or [],
        description=description,
        language=language,
        port=port,
        use_groq_ai=use_groq_ai,
    )
    return GenerationPlan(config)


def from_yaml(path: str) -> "GenerationPlan":
    """Charge une configuration depuis un fichier gpi.yaml."""
    config = ProjectConfig.from_yaml(path)
    return GenerationPlan(config)


def from_toml(path: str) -> "GenerationPlan":
    """Charge une configuration depuis un fichier gpi.toml."""
    config = ProjectConfig.from_toml(path)
    return GenerationPlan(config)


class GenerationPlan:
    """Plan de génération d'un projet GPI."""

    def __init__(self, config: ProjectConfig):
        self.config = config
        self._registry = ModuleRegistry()
        self._resolver = Resolver(self._registry)
        self._resolution = None

    def resolve(self):
        """Résoud les modules sans générer."""
        from gpi.core.resolver import ResolutionResult
        self._resolution = self._resolver.resolve(self.config)
        return self._resolution

    def generate(self, output_dir: str) -> str:
        """
        Génère le projet dans le dossier spécifié.

        Returns:
            Chemin absolu du projet généré.
        """
        if self._resolution is None:
            self.resolve()

        composer = Composer(self._registry)
        files = composer.compose(self.config, self._resolution)

        writer = Writer()
        writer.write(files, output_dir)

        return str(output_dir)
```

## Annexe C — Décisions de design justifiées

### Pourquoi Pydantic v2 pour la configuration ?

Pydantic v2 offre une validation stricte avec des messages d'erreur clairs, la conversion automatique des types, et une intégration native avec les outils modernes (FastAPI, etc.). Les erreurs de configuration sont interceptées avant même que la génération commence.

### Pourquoi Jinja2 pour les templates ?

Jinja2 est le standard de facto pour les templates Python. Il est puissant, lisible, et permet les conditions (`{% if %}`) et boucles (`{% for %}`) nécessaires pour générer du code conditionnel selon les modules sélectionnés.

### Pourquoi séparer les fichiers CRUD ?

Voir section 7.1 pour la justification complète. En résumé : pédagogie, maintenabilité, correspondance avec CQRS, testabilité unitaire améliorée.

### Pourquoi Groq plutôt qu'OpenAI ?

Groq offre une inférence ultra-rapide (LPU — Language Processing Unit) avec des modèles open source (Llama 3, Mixtral). Pour un outil CLI où la vitesse de réponse est critique, Groq est supérieur. De plus, Groq propose un tier gratuit généreux, rendant la feature accessible à tous les utilisateurs de GPI.

### Pourquoi `gpi.lock` plutôt qu'un simple hash ?

Un hash ne permet pas de voir ce qui a changé. Le fichier `gpi.lock` est lisible par un humain, versionnable dans Git, et contient suffisamment d'informations pour reproduire exactement le projet ou comprendre pourquoi deux projets diffèrent.

### Pourquoi un système de plugins via `entry_points` ?

Les `entry_points` Python sont le mécanisme standard d'extensibilité des packages (utilisé par pytest, Sphinx, Flask, etc.). Un plugin GPI est un simple package PyPI avec la bonne déclaration — aucune infrastructure supplémentaire nécessaire.

---

*Document rédigé par SOSSOU Elkast Orsini — Référence complète GPI v2*
*Ce document est la source de vérité. Une IA recevant ce document peut coder GPI v2 dans son intégralité.*
