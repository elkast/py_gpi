# Document d'Exigences : GPI v2 — Refactoring Majeur

## Introduction

Ce document définit les exigences fonctionnelles et non-fonctionnelles du refactoring GPI v0.1 → v2.
GPI (Générateur de Projet Intelligent) v2 transforme un générateur de templates statiques en un
**compositeur de projets modulaire** : résolution de dépendances entre modules, reproductibilité
via `gpi.lock`, intégration IA Groq optionnelle, API Python publique et système de plugins.

Les exigences sont dérivées du document de conception approuvé (`design.md`) et couvrent :
- La suppression des incohérences v0.1 (niveaux, bilingue, microservices non bloqués)
- Le moteur de modules (Module ABC, ModuleRegistry, Resolver, Validator, Composer, Writer)
- Le système `gpi.lock` et la reproductibilité
- L'intégration Groq AI optionnelle
- Les nouvelles commandes CLI (add, upgrade, replay, explain, plugin)
- L'API Python publique
- Le système de plugins via `entry_points`
- Le CRUD atomisé par fichier
- La couverture de tests ≥ 90 %

---

## Glossaire

- **GPI** : Générateur de Projet Intelligent — le package Python `py_gpi`
- **Module** : Unité fonctionnelle indépendante (ex : `auth-jwt`, `database-postgres`)
- **ModuleRegistry** : Registre central indexant tous les modules natifs et plugins
- **Resolver** : Composant résolvant les dépendances entre modules (tri topologique DFS)
- **Validator** : Composant validant les combinaisons de modules selon des règles déclaratives
- **Composer** : Composant assemblant les fichiers de tous les modules résolus
- **Writer** : Composant écrivant les fichiers sur disque et générant `gpi.lock`
- **LockFile** : Gestionnaire du fichier `gpi.lock` (création, lecture, validation checksum)
- **ProjectConfig** : Modèle Pydantic v2 représentant la configuration complète d'un projet
- **GenerationPlan** : Objet retourné par l'API publique `gpi.compose()`
- **Plugin** : Package Python tiers exposant un `Module` via `entry_points`
- **CRUD** : Create, Read, Update, Delete — opérations de base sur les données
- **CQRS** : Command Query Responsibility Segregation — séparation commandes/requêtes
- **CLI** : Interface en ligne de commande GPI (`gpi init`, `gpi add`, etc.)
- **Groq_AI** : Service d'inférence IA Groq (optionnel, activé par `GROQ_API_KEY`)
- **ResolutionResult** : Résultat du Resolver (modules résolus, auto-ajoutés, avertissements)
- **ValidationError** : Exception levée par le Validator pour une règle bloquante
- **GpiError** : Classe de base de toutes les exceptions GPI

---

## Exigences

### Exigence 1 : Suppression des incohérences v0.1

**User Story :** En tant que développeur utilisant GPI, je veux une interface sans options
paternalistes ni incohérentes, afin de déclarer mes besoins réels sans m'auto-évaluer.

#### Critères d'acceptation

1. THE ProjectConfig SHALL NOT expose a `niveau` field (`debutant`, `intermediaire`, `expert`).
2. THE ProjectConfig SHALL NOT expose a `bilingue` language option — valid values are `"fr"` and `"en"` only.
3. THE ProjectConfig SHALL NOT expose a `route_org` field.
4. WHEN `architecture` is `"microservices"` and fewer than 2 modules are declared, THE Validator SHALL raise a `ValidationError` with a descriptive message.
5. THE CLI SHALL NOT display level-based prompts during the interactive questionnaire.
6. WHEN `language` is set to a value other than `"fr"` or `"en"`, THE ProjectConfig SHALL raise a `ValueError` with the list of valid values.

---

### Exigence 2 : Modèle de configuration `ProjectConfig`

**User Story :** En tant que développeur, je veux une configuration validée dès la construction,
afin de détecter les erreurs avant que la génération commence.

#### Critères d'acceptation

1. THE ProjectConfig SHALL validate `framework` against `["fastapi", "flask", "django"]` and raise `ValueError` for any other value.
2. THE ProjectConfig SHALL validate `architecture` against `["monolithic", "microservices"]` and raise `ValueError` for any other value.
3. THE ProjectConfig SHALL validate `name` against the regex `^[a-zA-Z][a-zA-Z0-9_]{1,48}$` and raise `ValueError` for non-matching values.
4. THE ProjectConfig SHALL validate `language` against `["fr", "en"]` and raise `ValueError` for any other value.
5. THE ProjectConfig SHALL validate `port` in the range `[1024, 65535]` and raise `ValueError` for out-of-range values.
6. WHEN `architecture` is `"microservices"` and `services` is empty, THE ProjectConfig SHALL inject `["auth", "users", "products"]` as default services.
7. WHEN a valid YAML file is provided, THE ProjectConfig SHALL load and validate the configuration via `ProjectConfig.from_yaml(path)`.
8. WHEN a valid TOML file is provided, THE ProjectConfig SHALL load and validate the configuration via `ProjectConfig.from_toml(path)`.
9. THE ProjectConfig SHALL use `tomllib` (stdlib) on Python 3.11+ and `tomli` on Python 3.9/3.10.

---

### Exigence 3 : Classe de base `Module` et `ModuleMetadata`

**User Story :** En tant que développeur de module ou de plugin, je veux un contrat clair à
implémenter, afin de créer des modules compatibles avec le moteur GPI.

#### Critères d'acceptation

1. THE Module ABC SHALL declare `metadata` as an abstract property returning a `ModuleMetadata` instance.
2. THE Module ABC SHALL declare `get_dependencies()` as an abstract method returning `list[str]` of pip specifications.
3. THE Module ABC SHALL declare `get_files(config)` as an abstract method returning `dict[str, str]` mapping relative paths to file contents.
4. THE Module ABC SHALL provide default implementations for `get_env_vars()`, `get_env_example_vars()`, and `post_generate_instructions()` returning empty collections.
5. THE ModuleMetadata SHALL include fields: `id`, `name`, `version`, `description`, `frameworks`, `architectures`, `requires`, `conflicts`, `optional`, `tags`.
6. THE ModuleMetadata `id` field SHALL use kebab-case format (ex: `"auth-jwt"`).

---

### Exigence 4 : `ModuleRegistry` — Registre central

**User Story :** En tant que composant du moteur GPI, je veux accéder à tous les modules
disponibles via un registre unique, afin de résoudre et composer les projets.

#### Critères d'acceptation

1. WHEN the ModuleRegistry is instantiated, THE ModuleRegistry SHALL load all builtin modules including: `framework-fastapi`, `framework-flask`, `framework-django`, `auth-jwt`, `auth-sessions`, `auth-oauth2`, `database-sqlite`, `database-postgres`, `database-mysql`, `cache-redis`, `queue-celery`, `queue-rq`, `docker`, `docker-compose`, `tests-pytest`, `monitoring-prometheus`, `github-actions`.
2. WHEN plugins are installed via `entry_points` group `"gpi.modules"`, THE ModuleRegistry SHALL load them automatically at instantiation.
3. WHEN a plugin raises an exception during loading, THE ModuleRegistry SHALL log a warning and continue loading remaining modules without raising.
4. THE ModuleRegistry.get(module_id) SHALL return the Module instance for a known ID, or `None` for an unknown ID.
5. THE ModuleRegistry.list_all() SHALL return all loaded modules (builtin + plugins).
6. WHEN a search query is provided, THE ModuleRegistry.search(query) SHALL return all modules where the query appears (case-insensitive) in `id`, `name`, `description`, or any `tags` element.

---

### Exigence 5 : `Resolver` — Résolution des dépendances

**User Story :** En tant que moteur GPI, je veux résoudre automatiquement les dépendances
entre modules, afin de garantir un ordre de génération cohérent et sans conflit.

#### Critères d'acceptation

1. WHEN a valid config is resolved, THE Resolver SHALL include `framework-{config.framework}` as the first element of `ResolutionResult.modules`.
2. WHEN a module declares required dependencies in `metadata.requires`, THE Resolver SHALL add missing dependencies to `ResolutionResult.auto_added` and include them in `ResolutionResult.modules`.
3. WHEN a module ID is not found in the registry, THE Resolver SHALL raise `ModuleNotFoundError` with a message referencing `gpi plugin list`.
4. WHEN a module is incompatible with the chosen `framework`, THE Resolver SHALL raise `ModuleIncompatibleError` listing the supported frameworks.
5. WHEN a module is incompatible with the chosen `architecture`, THE Resolver SHALL raise `ModuleIncompatibleError`.
6. WHEN two conflicting modules are both requested, THE Resolver SHALL raise `ModuleConflictError` naming both modules.
7. WHEN a circular dependency is detected, THE Resolver SHALL raise `CircularDependencyError` naming the involved module.
8. THE Resolver SHALL use a DFS (Depth-First Search) algorithm with O(V+E) complexity for topological sorting.
9. THE ResolutionResult SHALL contain: `modules` (ordered list), `auto_added` (list of automatically added module IDs), `warnings` (list of non-blocking messages).

---

### Exigence 6 : `Validator` — Règles métier déclaratives

**User Story :** En tant que moteur GPI, je veux valider les combinaisons de modules avant
la résolution, afin de bloquer les configurations invalides avec des messages clairs.

#### Critères d'acceptation

1. WHEN `architecture` is `"microservices"` and fewer than 2 modules are declared, THE Validator SHALL raise `ValidationError`.
2. WHEN both `"auth-jwt"` and `"auth-oauth2"` are in `modules`, THE Validator SHALL raise `ValidationError`.
3. WHEN `"queue-celery"` is in `modules` and `"cache-redis"` is not, THE Validator SHALL return a non-blocking warning string.
4. WHEN `framework` is `"django"` and `"auth-jwt"` is in `modules`, THE Validator SHALL return a non-blocking warning string.
5. WHEN `architecture` is `"microservices"` and `framework` is `"django"`, THE Validator SHALL return a non-blocking warning string.
6. WHEN `"auth-sessions"` is in `modules` and `framework` is `"fastapi"`, THE Validator SHALL return a non-blocking warning string.
7. WHEN `"monitoring-prometheus"` is in `modules` and `framework` is `"django"`, THE Validator SHALL raise `ValidationError`.
8. THE Validator SHALL express all rules as a declarative list of dicts with `condition`, `message`, and `blocking` keys.
9. THE Validator.validate() SHALL return a `list[str]` of non-blocking warnings when no blocking rule is violated.

---

### Exigence 7 : `Composer` — Assemblage des fichiers

**User Story :** En tant que moteur GPI, je veux assembler les fichiers de tous les modules
résolus en un dictionnaire unique, afin de les transmettre au Writer pour écriture.

#### Critères d'acceptation

1. THE Composer.compose() SHALL return a `dict[str, str]` containing all files declared by all modules in `ResolutionResult.modules`.
2. WHEN two modules declare the same file path, THE Composer SHALL use the content from the last module in resolution order.
3. THE Composer SHALL render all file contents as Jinja2 templates using the project context.
4. WHEN Jinja2 rendering fails for a file, THE Composer SHALL return the raw content without raising.
5. THE Composer.get_new_files(module_id, config) SHALL return only the files of the specified module, rendered with the project context.
6. THE Composer.get_all_dependencies(resolution) SHALL return a sorted, deduplicated list of all pip specifications from all resolved modules.
7. THE Composer.apply_to_existing(new_files, project_path) SHALL write new files to an existing project directory without overwriting existing files unless explicitly declared by the module.

---

### Exigence 8 : `Writer` — Écriture sur disque

**User Story :** En tant que moteur GPI, je veux écrire les fichiers composés sur le disque
de façon sécurisée, afin de produire un projet prêt à l'emploi avec son `gpi.lock`.

#### Critères d'acceptation

1. THE Writer.write() SHALL create the output directory if it does not exist.
2. THE Writer.write() SHALL create all parent directories for each file path before writing.
3. THE Writer.write() SHALL write all files from the `files` dict to the output directory.
4. WHEN `config`, `resolution`, and `registry` are provided, THE Writer.write() SHALL generate a `gpi.lock` file in the output directory.
5. THE Writer.write() SHALL return the absolute path of the output directory.

---

### Exigence 9 : `LockFile` — Reproductibilité des projets

**User Story :** En tant que développeur, je veux un fichier `gpi.lock` versionnable,
afin de reproduire exactement un projet généré à n'importe quel moment.

#### Critères d'acceptation

1. THE LockFile.create() SHALL produce a dict containing: `gpi_version`, `generated_at` (ISO 8601 UTC), `config` (serialized ProjectConfig), `resolved_modules` (list with `id`, `version`, `auto`), `python_dependencies` (sorted list), `checksum` (SHA-256).
2. THE LockFile.write() SHALL serialize the lock dict as indented JSON (indent=2) to `gpi.lock` in the specified directory.
3. THE LockFile.read() SHALL parse the JSON file and validate the SHA-256 checksum.
4. WHEN the checksum is invalid, THE LockFile.read() SHALL raise `ValueError` with a message suggesting `gpi init` or `gpi replay`.
5. THE LockFile.to_config() SHALL reconstruct a `ProjectConfig` from the `config` field of a lock dict.
6. FOR ALL valid ProjectConfig instances, creating a LockFile then calling to_config() SHALL produce a ProjectConfig equivalent to the original.

---

### Exigence 10 : Intégration Groq AI (optionnelle)

**User Story :** En tant que développeur, je veux une assistance IA optionnelle pour suggérer
des modules et expliquer le code généré, afin d'accélérer mes choix de configuration.

#### Critères d'acceptation

1. WHEN `GROQ_API_KEY` is not set in the environment, THE GpiGroqClient.is_available SHALL return `False`.
2. WHEN `GROQ_API_KEY` is not set and `GpiGroqClient.complete()` is called, THE GpiGroqClient SHALL raise `RuntimeError` with a message explaining how to configure the key.
3. WHEN an `APIConnectionError` occurs during a Groq call, THE GpiGroqClient SHALL raise an `Exception` with a connectivity error message.
4. WHEN a `RateLimitError` occurs during a Groq call, THE GpiGroqClient SHALL raise an `Exception` with a retry message.
5. WHEN `suggest_modules()` encounters any exception (network, JSON parse, API error), THE suggest_modules function SHALL return an empty list without propagating the exception.
6. THE GpiGroqClient SHALL use `"llama-3.3-70b-versatile"` as the default model and `"llama-3.1-8b-instant"` for fast requests (suggestions).
7. WHEN `GROQ_API_KEY` is absent, THE GPI system SHALL function fully offline without any degradation of non-AI features.
8. THE GpiGroqClient SHALL initialize the Groq SDK client lazily (only on first `complete()` call).

---

### Exigence 11 : Interface CLI — Commandes v2

**User Story :** En tant que développeur, je veux des commandes CLI claires et cohérentes,
afin de créer, mettre à jour et reproduire des projets depuis le terminal.

#### Critères d'acceptation

1. THE CLI SHALL expose the command `gpi init` accepting an optional `-c/--config` flag pointing to a YAML or TOML file.
2. WHEN `gpi init` is called without `-c`, THE CLI SHALL launch an interactive questionnaire without level-based prompts.
3. THE CLI SHALL expose the command `gpi add <module>` accepting an optional `--path` flag for the project directory.
4. WHEN `gpi add <module>` is called, THE CLI SHALL read `gpi.lock`, append the module to the config, resolve dependencies, and write new files.
5. THE CLI SHALL expose the command `gpi upgrade [module] [--dry-run]` to update one or all modules.
6. WHEN `--dry-run` is passed to `gpi upgrade`, THE CLI SHALL display planned changes without writing any file.
7. THE CLI SHALL expose the command `gpi replay <lockfile> [--output <dir>] [--check]`.
8. WHEN `gpi replay` is called, THE CLI SHALL read the lock file, validate its checksum, reconstruct the config, and regenerate the project identically.
9. WHEN `--check` is passed to `gpi replay`, THE CLI SHALL validate the lock file integrity without generating any file.
10. THE CLI SHALL expose the command `gpi explain [path]` requiring `GROQ_API_KEY`.
11. WHEN `gpi explain` is called without `GROQ_API_KEY`, THE CLI SHALL display a warning message and exit with code 1.
12. THE CLI SHALL expose the command `gpi plugin` with subcommands `install`, `list`, `uninstall`, `publish`.
13. THE CLI SHALL expose the command `gpi version` displaying the current GPI version.
14. THE CLI SHALL support `python -m gpi` as an alternative invocation.

---

### Exigence 12 : API Python publique

**User Story :** En tant que développeur Python, je veux utiliser GPI comme bibliothèque
dans mes scripts, afin d'automatiser la génération de projets sans passer par le CLI.

#### Critères d'acceptation

1. THE public API SHALL expose `gpi.compose(name, framework, architecture, modules, description, language, port, use_groq_ai)` returning a `GenerationPlan`.
2. THE public API SHALL expose `gpi.from_yaml(path)` returning a `GenerationPlan`.
3. THE public API SHALL expose `gpi.from_toml(path)` returning a `GenerationPlan`.
4. THE GenerationPlan.resolve() SHALL return a `ResolutionResult` without writing any file.
5. THE GenerationPlan.generate(output_dir) SHALL produce the same files as the equivalent CLI workflow and return the absolute output path as a string.
6. FOR ALL valid configurations, `gpi.from_yaml(path)` after writing the config to YAML SHALL produce a GenerationPlan equivalent to `gpi.compose()` with the same parameters.

---

### Exigence 13 : Système de plugins via `entry_points`

**User Story :** En tant que développeur tiers, je veux publier un plugin GPI sur PyPI,
afin d'étendre le registre de modules sans modifier le code source de GPI.

#### Critères d'acceptation

1. THE plugin system SHALL use the `entry_points` group `"gpi.modules"` to discover third-party modules.
2. WHEN a plugin package declares `[project.entry-points."gpi.modules"] my_module = "my_package:MyModule"`, THE ModuleRegistry SHALL load `MyModule` automatically after `pip install`.
3. THE plugin Module class SHALL inherit from `gpi.modules.base.Module` and implement all abstract methods.
4. WHEN a plugin raises any exception during loading, THE ModuleRegistry SHALL print a warning and continue without raising.
5. THE CLI `gpi plugin install <package>` SHALL install the package via `pip install`.
6. THE CLI `gpi plugin list` SHALL display all loaded modules with their ID, name, version, and source (builtin or plugin).
7. THE CLI `gpi plugin uninstall <package>` SHALL uninstall the package via `pip uninstall`.

---

### Exigence 14 : CRUD atomisé par fichier

**User Story :** En tant qu'étudiant ou développeur, je veux que chaque opération CRUD soit
dans son propre fichier, afin de comprendre et modifier chaque opération indépendamment.

#### Critères d'acceptation

1. WHEN a project is generated with a database module, THE Composer SHALL produce separate files: `create.py`, `read.py`, `update.py`, `delete.py` in the CRUD directory.
2. THE `create.py` file SHALL implement the `POST` endpoint for the resource.
3. THE `read.py` file SHALL implement both `GET /resource/` (list with pagination) and `GET /resource/{id}` (single item) endpoints.
4. THE `update.py` file SHALL implement both `PUT /resource/{id}` (full replacement) and `PATCH /resource/{id}` (partial update) endpoints.
5. THE `delete.py` file SHALL implement the `DELETE /resource/{id}` endpoint.
6. WHEN architecture is `"monolithic"`, THE Composer SHALL place CRUD files under `app/{domain}/`.
7. WHEN architecture is `"microservices"`, THE Composer SHALL place CRUD files under `services/{service}/crud/`.
8. THE generated `main.py` SHALL mount each CRUD router separately using `app.include_router()`.

---

### Exigence 15 : Fichiers obligatoires du projet généré

**User Story :** En tant que développeur, je veux que tout projet généré contienne les fichiers
essentiels, afin de pouvoir l'utiliser immédiatement sans configuration supplémentaire.

#### Critères d'acceptation

1. THE Writer SHALL always generate `gpi.lock` in the project root.
2. THE Writer SHALL always generate `README.md` in the project root.
3. THE Writer SHALL always generate `.env.example` in the project root.
4. THE Writer SHALL always generate `requirements.txt` in the project root.
5. THE Writer SHALL always generate `.gitignore` in the project root.
6. THE Writer SHALL always generate `.env` in the project root.

---

### Exigence 16 : Hiérarchie des exceptions

**User Story :** En tant que développeur utilisant GPI comme bibliothèque, je veux une
hiérarchie d'exceptions claire, afin de gérer les erreurs de façon précise dans mon code.

#### Critères d'acceptation

1. THE GPI system SHALL define `GpiError` as the base exception class for all GPI-specific errors.
2. THE GPI system SHALL define `ValidationError(GpiError)` for invalid configuration combinations.
3. THE GPI system SHALL define `ModuleNotFoundError(GpiError)` for unknown module IDs.
4. THE GPI system SHALL define `ModuleConflictError(GpiError)` for incompatible module pairs.
5. THE GPI system SHALL define `ModuleIncompatibleError(GpiError)` for framework/architecture incompatibilities.
6. THE GPI system SHALL define `CircularDependencyError(GpiError)` for circular dependency graphs.
7. THE GPI system SHALL define `LockFileError(GpiError)` for corrupted or missing lock files.
8. THE GPI system SHALL define `GroqAIError(GpiError)` for Groq API failures.

---

### Exigence 17 : Contraintes système et dépendances

**User Story :** En tant qu'utilisateur de GPI, je veux que le package fonctionne sur mon
environnement standard, afin de l'installer sans configuration complexe.

#### Critères d'acceptation

1. THE GPI package SHALL support Python 3.9, 3.10, 3.11, and 3.12.
2. THE GPI package SHALL declare the following runtime dependencies: `typer[all]>=0.9.0`, `rich>=13.0.0`, `jinja2>=3.1.0`, `pyyaml>=6.0`, `pydantic>=2.0.0`, `groq>=0.4.0`, `httpx>=0.24.0`, `packaging>=23.0`, `tomli>=2.0.0` (Python < 3.11 only).
3. THE GPI package SHALL function fully offline when `GROQ_API_KEY` is not set.
4. THE GPI package SHALL validate project names against `^[a-zA-Z][a-zA-Z0-9_]{1,48}$` to prevent path traversal.
5. THE GPI package SHALL generate secret keys using `secrets.token_urlsafe(32)` and never hardcode them.
6. THE GPI package SHALL never include `GROQ_API_KEY` in `gpi.lock` or any generated file.
7. THE GPI package SHALL support Windows 10/11, macOS 12+, Ubuntu 20.04+, Debian 11+, and WSL2.

---

### Exigence 18 : Couverture de tests

**User Story :** En tant que mainteneur de GPI, je veux une suite de tests complète,
afin de garantir la non-régression lors des évolutions du package.

#### Critères d'acceptation

1. THE test suite SHALL achieve a minimum code coverage of 90% measured by `pytest-cov`.
2. THE test suite SHALL include unit tests for: `ProjectConfig`, `Resolver`, `Validator`, `Composer`, `Writer`, `LockFile`, `ModuleRegistry`, `GpiGroqClient`.
3. THE test suite SHALL include integration tests for full project generation with FastAPI, Flask, and Django.
4. THE test suite SHALL include integration tests for microservices architecture generation.
5. THE pytest configuration SHALL use `--cov-fail-under=90` to enforce the coverage threshold in CI.
6. THE test suite SHALL use `pytest-asyncio` for any asynchronous test cases.
