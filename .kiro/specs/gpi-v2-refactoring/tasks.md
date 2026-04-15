# Plan d'implémentation : GPI v2 — Refactoring Majeur

## Vue d'ensemble

Refactoring complet de `py_gpi` v0.1 → v2 : remplacement de l'architecture générateurs statiques
par un compositeur de projets modulaire (Module ABC, ModuleRegistry, Resolver, Validator, Composer,
Writer, LockFile), intégration Groq AI optionnelle, CLI v2 avec nouvelles commandes, API Python
publique et système de plugins via `entry_points`. Python 3.9+, Pydantic v2, Jinja2, Typer+Rich.

## Tâches

- [x] 1. Mettre à jour `pyproject.toml` pour les dépendances v2
  - Passer `requires-python` à `>=3.9`
  - Ajouter `groq>=0.4.0`, `httpx>=0.24.0`, `packaging>=23.0`
  - Ajouter `tomli>=2.0.0; python_version < "3.11"` (dépendance conditionnelle)
  - Mettre à jour le point d'entrée CLI : `gpi.cli.app:app`
  - Ajouter la section `[tool.pytest.ini_options]` avec `--cov-fail-under=90`
  - Ajouter les dépendances optionnelles `[project.optional-dependencies]` : `ai` et `dev`
  - Déclarer le groupe `[project.entry-points."gpi.modules"]` (vide, pour les plugins)
  - _Exigences : 17.1, 17.2_


- [x] 2. Créer la hiérarchie d'exceptions `gpi/core/exceptions.py`
  - Définir `GpiError(Exception)` comme classe de base
  - Définir `ValidationError(GpiError)`, `ModuleNotFoundError(GpiError)`, `ModuleConflictError(GpiError)`
  - Définir `ModuleIncompatibleError(GpiError)`, `CircularDependencyError(GpiError)`
  - Définir `LockFileError(GpiError)`, `GroqAIError(GpiError)`
  - Supprimer l'ancien `gpi/core/config.py` v0.1 (champs `niveau`, `bilingue`, `route_org`)
  - _Exigences : 16.1–16.8_

- [x] 3. Implémenter le nouveau `ProjectConfig` Pydantic v2 dans `gpi/core/config.py`
  - [x] 3.1 Écrire la classe `ProjectConfig(BaseModel)` avec les champs v2
    - Champs : `framework`, `name`, `architecture`, `modules`, `description`, `language`, `port`, `services`, `use_groq_ai`
    - Supprimer les champs v0.1 : `niveau`, `bilingue`, `route_org`, `auth`, `database`, `redis`, `queue`, `monitoring`, `local_ip`, `secret_key`
    - _Exigences : 1.1–1.3, 2.1–2.6_
  - [x] 3.2 Écrire les tests de propriété pour `ProjectConfig`
    - **Property 1 : Validation du framework — rejet des valeurs invalides**
    - **Validates : Exigences 2.1**
    - **Property 2 : Validation du nom de projet — contrat regex**
    - **Validates : Exigences 2.3**
    - **Property 3 : Validation du port — plage autorisée**
    - **Validates : Exigences 2.5**
    - **Property 4 : Services par défaut en microservices**
    - **Validates : Exigences 2.6**
  - [x] 3.3 Implémenter `from_yaml()` et `from_toml()` (tomllib stdlib Python 3.11+ / tomli fallback)
    - _Exigences : 2.7, 2.8, 2.9_
  - [x] 3.4 Écrire le test de propriété round-trip YAML
    - **Property 5 : Round-trip YAML — ProjectConfig**
    - **Validates : Exigences 2.7**


- [x] 4. Implémenter `Module` (ABC) et `ModuleMetadata` dans `gpi/modules/base.py`
  - Créer le répertoire `gpi/modules/` avec `__init__.py`
  - Définir `ModuleMetadata` (dataclass) avec tous les champs : `id`, `name`, `version`, `description`, `frameworks`, `architectures`, `requires`, `conflicts`, `optional`, `tags`
  - Définir `Module(ABC)` avec les méthodes abstraites `metadata`, `get_dependencies()`, `get_files(config)`
  - Implémenter les méthodes par défaut : `get_env_vars()`, `get_env_example_vars()`, `post_generate_instructions()`
  - _Exigences : 3.1–3.6_

- [x] 5. Implémenter les modules natifs — Framework
  - [x] 5.1 Créer `gpi/modules/framework/fastapi.py` — `FastAPIModule`
    - `metadata.id = "framework-fastapi"`, frameworks=["fastapi"], architectures=["monolithic","microservices"]
    - `get_dependencies()` : fastapi, uvicorn[standard], python-dotenv
    - `get_files()` : `main.py`, `requirements.txt`, `.env`, `.env.example`, `.gitignore`, `README.md`
    - _Exigences : 4.1, 15.1–15.6_
  - [x] 5.2 Créer `gpi/modules/framework/flask.py` — `FlaskModule`
    - `metadata.id = "framework-flask"`, frameworks=["flask"]
    - `get_dependencies()` : flask, python-dotenv
    - `get_files()` : `app.py`, `requirements.txt`, fichiers communs
    - _Exigences : 4.1_
  - [x] 5.3 Créer `gpi/modules/framework/django.py` — `DjangoModule`
    - `metadata.id = "framework-django"`, frameworks=["django"]
    - `get_dependencies()` : django, python-dotenv
    - `get_files()` : `manage.py`, `settings.py`, `urls.py`, fichiers communs
    - _Exigences : 4.1_

- [x] 6. Implémenter les modules natifs — Auth
  - [x] 6.1 Créer `gpi/modules/auth/jwt.py` — `JWTAuthModule`
    - `metadata.id = "auth-jwt"`, frameworks=["fastapi","flask","django"], conflicts=["auth-oauth2","auth-sessions"]
    - `get_dependencies()` : python-jose[cryptography], passlib[bcrypt]
    - `get_files()` : `auth/security.py`, `auth/routes.py`
    - `get_env_vars()` : SECRET_KEY (via secrets.token_urlsafe), JWT_ALGORITHM
    - _Exigences : 4.1, 17.5_
  - [x] 6.2 Créer `gpi/modules/auth/sessions.py` — `SessionsAuthModule`
    - `metadata.id = "auth-sessions"`, frameworks=["flask","django"], conflicts=["auth-jwt","auth-oauth2"]
    - _Exigences : 4.1_
  - [x] 6.3 Créer `gpi/modules/auth/oauth2.py` — `OAuth2Module`
    - `metadata.id = "auth-oauth2"`, frameworks=["fastapi"], conflicts=["auth-jwt","auth-sessions"]
    - `get_dependencies()` : python-multipart
    - _Exigences : 4.1_


- [x] 7. Implémenter les modules natifs — Database, Cache, Queue
  - [x] 7.1 Créer `gpi/modules/database/sqlite.py` — `SQLiteModule`
    - `metadata.id = "database-sqlite"`, frameworks=["fastapi","flask","django"]
    - `get_dependencies()` : sqlalchemy, alembic
    - `get_files()` : `database.py`, `models/catalogue.py`, `schemas/catalogue.py`
    - `get_files()` : fichiers CRUD atomisés `app/catalogue/create.py`, `read.py`, `update.py`, `delete.py`
    - _Exigences : 4.1, 14.1–14.8_
  - [x] 7.2 Créer `gpi/modules/database/postgres.py` — `PostgresModule`
    - `metadata.id = "database-postgres"`, `get_dependencies()` : sqlalchemy, alembic, psycopg2-binary
    - `get_env_vars()` : DATABASE_URL avec URL PostgreSQL
    - _Exigences : 4.1_
  - [x] 7.3 Créer `gpi/modules/database/mysql.py` — `MySQLModule`
    - `metadata.id = "database-mysql"`, `get_dependencies()` : sqlalchemy, alembic, pymysql
    - _Exigences : 4.1_
  - [x] 7.4 Créer `gpi/modules/cache/redis.py` — `RedisModule`
    - `metadata.id = "cache-redis"`, `get_dependencies()` : redis
    - `get_env_vars()` : REDIS_URL
    - _Exigences : 4.1_
  - [x] 7.5 Créer `gpi/modules/queue/celery.py` — `CeleryModule`
    - `metadata.id = "queue-celery"`, requires=["cache-redis"], frameworks=["fastapi","flask"]
    - `get_dependencies()` : celery[redis]
    - _Exigences : 4.1_
  - [x] 7.6 Créer `gpi/modules/queue/rq.py` — `RQModule`
    - `metadata.id = "queue-rq"`, requires=["cache-redis"], frameworks=["fastapi","flask"]
    - `get_dependencies()` : rq
    - _Exigences : 4.1_

- [x] 8. Implémenter les modules natifs — Infra, Testing, Monitoring
  - [x] 8.1 Créer `gpi/modules/infra/docker.py` — `DockerModule`
    - `metadata.id = "docker"`, `get_files()` : `Dockerfile`, `.dockerignore`
    - _Exigences : 4.1_
  - [x] 8.2 Créer `gpi/modules/infra/docker_compose.py` — `DockerComposeModule`
    - `metadata.id = "docker-compose"`, `get_files()` : `docker-compose.yml`
    - _Exigences : 4.1_
  - [x] 8.3 Créer `gpi/modules/infra/github_actions.py` — `GitHubActionsModule`
    - `metadata.id = "github-actions"`, `get_files()` : `.github/workflows/ci.yml`
    - _Exigences : 4.1_
  - [x] 8.4 Créer `gpi/modules/testing/pytest.py` — `PytestModule`
    - `metadata.id = "tests-pytest"`, `get_dependencies()` : pytest, pytest-cov, httpx
    - `get_files()` : `tests/__init__.py`, `tests/conftest.py`
    - _Exigences : 4.1_
  - [x] 8.5 Créer `gpi/modules/monitoring/prometheus_grafana.py` — `PrometheusModule`
    - `metadata.id = "monitoring-prometheus"`, frameworks=["fastapi","flask"]
    - `get_dependencies()` : prometheus-fastapi-instrumentator
    - _Exigences : 4.1_


- [x] 9. Implémenter `ModuleRegistry` dans `gpi/modules/registry.py`
  - [x] 9.1 Écrire la classe `ModuleRegistry` avec `_load_builtin_modules()` chargeant les 17 modules natifs
    - Indexer par `module.metadata.id` dans `self._modules: dict[str, Module]`
    - _Exigences : 4.1_
  - [x] 9.2 Implémenter `_load_plugin_modules()` via `importlib.metadata.entry_points(group="gpi.modules")`
    - Erreurs de chargement silencieuses : `print(f"⚠ Plugin '{ep.name}' ignoré : {e}")` et continuer
    - _Exigences : 4.2, 4.3, 13.1, 13.2_
  - [x] 9.3 Implémenter `get()`, `list_all()`, `search()` (recherche insensible à la casse dans id/name/description/tags)
    - _Exigences : 4.4, 4.5, 4.6_
  - [x] 9.4 Écrire les tests unitaires pour `ModuleRegistry`
    - Vérifier que les 17 modules natifs sont chargés
    - Tester `get()` avec ID connu et inconnu (None)
    - Tester `search()` avec correspondance partielle
    - _Exigences : 4.1, 4.4, 4.5_
  - [x] 9.5 Écrire le test de propriété pour la recherche dans le registre
    - **Property 18 : Recherche dans le registre — cohérence des résultats**
    - **Validates : Exigences 4.6**
  - [x] 9.6 Écrire le test de propriété pour l'isolation des plugins défectueux
    - **Property 21 : Plugin défectueux — isolation des erreurs**
    - **Validates : Exigences 4.3, 13.4**

- [x] 10. Implémenter `Resolver` et `ResolutionResult` dans `gpi/core/resolver.py`
  - [x] 10.1 Définir `ResolutionResult` (dataclass) avec `modules`, `auto_added`, `warnings`
    - _Exigences : 5.9_
  - [x] 10.2 Implémenter `Resolver.resolve()` avec DFS (visiting/visited sets, détection cycles)
    - Le framework est toujours résolu en premier (nœud racine `framework-{config.framework}`)
    - Lever `ModuleNotFoundError`, `ModuleIncompatibleError`, `ModuleConflictError`, `CircularDependencyError`
    - Ajouter les dépendances manquantes dans `auto_added` avec avertissement
    - _Exigences : 5.1–5.8_
  - [x] 10.3 Écrire les tests unitaires pour `Resolver`
    - Tester résolution simple, auto-ajout de dépendances, module inconnu, conflit, cycle
    - _Exigences : 5.1–5.7_
  - [x] 10.4 Écrire les tests de propriété pour `Resolver`
    - **Property 6 : Framework toujours en premier dans la résolution**
    - **Validates : Exigences 5.1**
    - **Property 7 : Dépendances automatiquement ajoutées**
    - **Validates : Exigences 5.2**
    - **Property 8 : Module inconnu → ModuleNotFoundError**
    - **Validates : Exigences 5.3**
    - **Property 9 : Modules en conflit → ModuleConflictError**
    - **Validates : Exigences 5.6**


- [x] 11. Implémenter `Validator` et `VALIDATION_RULES` dans `gpi/core/validator.py`
  - [x] 11.1 Définir `VALIDATION_RULES` comme liste de dicts `{condition, message, blocking}`
    - Règles bloquantes : microservices < 2 modules, auth-jwt + auth-oauth2, monitoring-prometheus + django
    - Règles non-bloquantes : celery sans redis, django + jwt, microservices + django, sessions + fastapi
    - _Exigences : 6.1–6.8_
  - [x] 11.2 Implémenter `Validator.validate(config)` → `list[str]` (avertissements) ou lève `ValidationError`
    - _Exigences : 6.9_
  - [x] 11.3 Écrire les tests de propriété pour `Validator`
    - **Property 10 : Règle bloquante → ValidationError**
    - **Validates : Exigences 6.1, 6.2, 6.7**
    - **Property 11 : Règle non-bloquante → avertissement retourné**
    - **Validates : Exigences 6.3, 6.4, 6.5, 6.6**

- [x] 12. Implémenter `Composer` dans `gpi/core/composer.py`
  - [x] 12.1 Implémenter `Composer.compose(config, resolution)` → `dict[str, str]`
    - Itérer sur `resolution.modules`, appeler `module.get_files(config)`, rendre chaque fichier via Jinja2
    - Dernier module gagne en cas de conflit de chemin
    - _Exigences : 7.1, 7.2, 7.3_
  - [x] 12.2 Implémenter `_render()` avec fallback sur contenu brut si Jinja2 échoue
    - _Exigences : 7.4_
  - [x] 12.3 Implémenter `get_new_files()`, `get_all_dependencies()`, `apply_to_existing()`
    - `get_all_dependencies()` : `sorted(set(deps))` sur tous les modules résolus
    - `apply_to_existing()` : écriture sans écraser les fichiers existants
    - _Exigences : 7.5, 7.6, 7.7_
  - [x] 12.4 Écrire les tests de propriété pour `Composer`
    - **Property 12 : Composer produit tous les fichiers des modules résolus**
    - **Validates : Exigences 7.1**
    - **Property 13 : Dépendances triées et dédupliquées**
    - **Validates : Exigences 7.6**

- [x] 13. Implémenter `Writer` dans `gpi/core/writer.py`
  - [x] 13.1 Implémenter `Writer.write(files, output_dir, config, resolution, registry)` → `Path`
    - Créer `output_dir` et tous les dossiers parents si inexistants
    - Écrire chaque fichier du dict `files`
    - Si `config + resolution + registry` fournis : générer `gpi.lock` via `LockFile`
    - Retourner le chemin absolu du dossier de sortie
    - _Exigences : 8.1–8.5_
  - [x] 13.2 Écrire le test de propriété pour `Writer`
    - **Property 14 : Writer crée tous les fichiers dans le répertoire de sortie**
    - **Validates : Exigences 8.3**


- [x] 14. Implémenter `LockFile` dans `gpi/core/lock.py`
  - [x] 14.1 Implémenter `LockFile.create(config, resolution, dependencies)` → `dict`
    - Champs : `gpi_version`, `generated_at` (ISO 8601 UTC), `config` (model_dump), `resolved_modules`, `python_dependencies`, `checksum` (SHA-256)
    - Ne jamais inclure `GROQ_API_KEY` dans le lock
    - _Exigences : 9.1, 17.6_
  - [x] 14.2 Implémenter `LockFile.write()`, `LockFile.read()` (validation checksum), `LockFile.to_config()`
    - `read()` : lever `ValueError` si checksum invalide
    - _Exigences : 9.2, 9.3, 9.4, 9.5_
  - [x] 14.3 Écrire les tests de propriété pour `LockFile`
    - **Property 15 : Round-trip LockFile — create → to_config**
    - **Validates : Exigences 9.5, 9.6**
    - **Property 16 : Checksum invalide → ValueError**
    - **Validates : Exigences 9.4**

- [x] 15. Checkpoint — Vérifier que le moteur de base fonctionne
  - S'assurer que tous les tests passent, demander à l'utilisateur si des questions se posent.

- [x] 16. Créer les templates Jinja2 dans `gpi/templates/`
  - [x] 16.1 Créer les templates communs dans `gpi/templates/common/`
    - `README.md.j2` : titre, description, instructions de lancement selon framework
    - `.env.j2` : SECRET_KEY (secrets.token_urlsafe), DATABASE_URL conditionnel, PORT, DEBUG
    - `.env.example.j2` : valeurs fictives/vides pour documentation
    - `.gitignore.j2` : __pycache__, .env, *.db, .venv/, dist/, *.egg-info/
    - `requirements.txt.j2` : liste des dépendances injectée par le Composer
    - _Exigences : 15.2–15.6_
  - [x] 16.2 Créer les templates FastAPI monolithique dans `gpi/templates/fastapi/monolithic/`
    - `main.py.j2` : app FastAPI, inclusion des routers CRUD séparés via `app.include_router()`
    - `database.py.j2` : connexion SQLAlchemy, SessionLocal, Base
    - `crud/create.py.j2`, `crud/read.py.j2`, `crud/update.py.j2`, `crud/delete.py.j2`
    - `models/catalogue.py.j2` : modèle SQLAlchemy CatalogueItem
    - `schemas/catalogue.py.j2` : schémas Pydantic (Create/Update/PartialUpdate/Response/Paginated)
    - _Exigences : 14.1–14.8_
  - [x] 16.3 Créer les templates FastAPI microservices dans `gpi/templates/fastapi/microservices/`
    - `docker-compose.yml.j2` : services dynamiques selon `config.services`
    - `services/{service}/main.py.j2`, `services/{service}/crud/*.j2`
    - _Exigences : 14.7_
  - [x] 16.4 Créer les templates Flask et Django dans `gpi/templates/flask/` et `gpi/templates/django/`
    - Templates minimaux pour `app.py` (Flask) et `manage.py`/`settings.py`/`urls.py` (Django)
    - _Exigences : 4.1_


- [x] 17. Implémenter l'intégration Groq AI dans `gpi/ai/`
  - [x] 17.1 Créer `gpi/ai/__init__.py` et `gpi/ai/client.py` — `GpiGroqClient`
    - Lazy init du client Groq (uniquement au premier appel `complete()`)
    - `is_available` : `bool(self.api_key)` — retourne False si GROQ_API_KEY absente
    - `complete()` : lever `RuntimeError` si clé absente, gérer `APIConnectionError`, `RateLimitError`
    - Modèles : `MODEL = "llama-3.3-70b-versatile"`, `FAST_MODEL = "llama-3.1-8b-instant"`
    - _Exigences : 10.1–10.4, 10.6, 10.8_
  - [x] 17.2 Créer `gpi/ai/suggestions.py` — `suggest_modules()`
    - Retourner `[]` pour toute exception (échec silencieux)
    - Utiliser `FAST_MODEL` pour les suggestions
    - _Exigences : 10.5_
  - [x] 17.3 Créer `gpi/ai/completion.py` et `gpi/ai/explainer.py` — `explain_project()`
    - `explain_project()` : collecter les fichiers .py (max 10, 500 chars chacun), appeler `complete()`
    - _Exigences : 10.6_
  - [x] 17.4 Écrire les tests unitaires pour `GpiGroqClient` (avec mock de l'API Groq)
    - Tester `is_available` sans clé, `complete()` sans clé, erreurs réseau et rate limit
    - _Exigences : 10.1–10.4_
  - [x] 17.5 Écrire le test de propriété pour `suggest_modules()`
    - **Property 17 : suggest_modules() — échec silencieux**
    - **Validates : Exigences 10.5**

- [x] 18. Implémenter la CLI v2 dans `gpi/cli/`
  - [x] 18.1 Créer `gpi/cli/__init__.py`, `gpi/cli/app.py` — application Typer principale
    - Enregistrer toutes les commandes : `init`, `add`, `upgrade`, `replay`, `explain`, `plugin`, `version`
    - Mettre à jour `gpi/__main__.py` pour pointer vers `gpi.cli.app:app`
    - _Exigences : 11.14_
  - [x] 18.2 Créer `gpi/cli/interactive.py` — questionnaire interactif Rich
    - Supprimer les prompts de niveau (`debutant/intermediaire/expert`)
    - Questions : framework, architecture, nom, modules (liste), description, language, port
    - _Exigences : 1.5, 11.2_
  - [x] 18.3 Créer `gpi/cli/commands/init.py` — commande `gpi init`
    - Accepter `-c/--config` (YAML ou TOML), `--no-network`
    - Sans `-c` : lancer `interactive.py`
    - Enchaîner : `Validator.validate()` → `Resolver.resolve()` → `Composer.compose()` → `Writer.write()`
    - _Exigences : 11.1, 11.2_
  - [x] 18.4 Créer `gpi/cli/commands/add.py` — commande `gpi add <module>`
    - Lire `gpi.lock`, reconstruire config, ajouter le module, résoudre, écrire les nouveaux fichiers
    - _Exigences : 11.3, 11.4_
  - [x] 18.5 Créer `gpi/cli/commands/upgrade.py` — commande `gpi upgrade [module] [--dry-run]`
    - `--dry-run` : afficher les changements sans écrire
    - _Exigences : 11.5, 11.6_
  - [x] 18.6 Créer `gpi/cli/commands/replay.py` — commande `gpi replay <lockfile>`
    - Valider le checksum, reconstruire la config, régénérer le projet
    - `--check` : valider uniquement sans générer
    - _Exigences : 11.7, 11.8, 11.9_
  - [x] 18.7 Créer `gpi/cli/commands/explain.py` — commande `gpi explain [path]`
    - Vérifier `GROQ_API_KEY`, afficher avertissement et exit 1 si absente
    - _Exigences : 11.10, 11.11_
  - [x] 18.8 Créer `gpi/cli/commands/plugin.py` — commande `gpi plugin install/list/uninstall/publish`
    - `install` : `pip install <package>` via subprocess
    - `list` : afficher tous les modules avec source (builtin/plugin)
    - `uninstall` : `pip uninstall <package>`
    - _Exigences : 11.12, 13.5, 13.6, 13.7_
  - [x] 18.9 Créer `gpi/cli/commands/version.py` — commande `gpi version`
    - _Exigences : 11.13_


- [x] 19. Implémenter l'API Python publique dans `gpi/__init__.py`
  - Réécrire `gpi/__init__.py` : `__version__ = "2.0.0"`, exposer `compose()`, `from_yaml()`, `from_toml()`
  - Définir `GenerationPlan` avec `resolve()` et `generate(output_dir)`
  - `generate()` enchaîne : `Resolver` → `Composer` → `Writer`
  - _Exigences : 12.1–12.5_
  - [x] 19.1 Écrire le test de propriété pour l'API publique
    - **Property 20 : API publique — équivalence compose() et from_yaml()**
    - **Validates : Exigences 12.6**

- [x] 20. Migrer les utilitaires v0.1 vers la structure v2
  - Déplacer `gpi/core/network.py` → `gpi/utils/network.py` (conserver `detecter_ips()`)
  - Réécrire `gpi/utils/filesystem.py` (remplace `file_utils.py`) : opérations fichiers sécurisées
  - Créer `gpi/utils/display.py` : fonctions Rich (panels, progress, tables) extraites du CLI
  - Mettre à jour `gpi/utils/__init__.py`
  - _Exigences : 17.7_

- [x] 21. Checkpoint — Vérifier l'intégration complète du moteur et de la CLI
  - S'assurer que tous les tests passent, demander à l'utilisateur si des questions se posent.

- [x] 22. Écrire les tests unitaires et d'intégration
  - [x] 22.1 Écrire les tests unitaires dans `tests/unit/`
    - `test_config.py` : ProjectConfig (validation, from_yaml, from_toml)
    - `test_resolver.py` : Resolver (résolution, auto-ajout, erreurs)
    - `test_validator.py` : Validator (règles bloquantes et non-bloquantes)
    - `test_composer.py` : Composer (compose, get_all_dependencies, apply_to_existing)
    - `test_writer.py` : Writer (création dossiers, écriture fichiers, gpi.lock)
    - `test_lock.py` : LockFile (create, write, read, to_config, checksum)
    - `test_registry.py` : ModuleRegistry (chargement, get, list_all, search)
    - `test_groq_client.py` : GpiGroqClient (is_available, erreurs, lazy init)
    - _Exigences : 18.1, 18.2_
  - [x] 22.2 Écrire les tests d'intégration dans `tests/integration/`
    - `test_fastapi_generation.py` : génération FastAPI monolithique (fichiers essentiels, JWT, CRUD, gpi.lock)
    - `test_flask_generation.py` : génération Flask monolithique
    - `test_django_generation.py` : génération Django monolithique
    - `test_microservices_generation.py` : génération FastAPI microservices
    - _Exigences : 18.3, 18.4_
  - [x] 22.3 Écrire le test de propriété pour la reproductibilité `gpi replay`
    - **Property 19 : gpi replay — reproductibilité identique**
    - **Validates : Exigences 11.8**
  - [x] 22.4 Configurer `pytest-cov` avec `--cov-fail-under=90` dans `pyproject.toml`
    - _Exigences : 18.1, 18.5, 18.6_

- [x] 23. Mettre à jour `README.md`
  - Documenter l'installation, les commandes CLI v2, les exemples d'API Python
  - Documenter le format `gpi.yaml`, le système de plugins, la configuration `GROQ_API_KEY`
  - _Exigences : 15.2_

- [x] 24. Checkpoint final — Vérifier la couverture et la qualité
  - S'assurer que tous les tests passent et que la couverture est ≥ 90%, demander à l'utilisateur si des questions se posent.

## Notes

- Les tâches marquées `*` sont optionnelles et peuvent être ignorées pour un MVP rapide
- Chaque tâche référence les exigences spécifiques pour la traçabilité
- Les commentaires dans le code doivent être en français (convention du projet)
- Les propriétés de correction (Property 1–21) sont définies dans `design.md`
- La clé `GROQ_API_KEY` ne doit jamais apparaître dans `gpi.lock` ni dans les fichiers générés
- Les clés secrètes sont générées avec `secrets.token_urlsafe(32)` — jamais hardcodées
