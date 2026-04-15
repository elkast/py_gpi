# tests/test_integration.py
"""Tests d'intégration — génération complète de projets GPI v2."""

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


def generer_projet(config: ProjectConfig, output_dir: str) -> Path:
    """Helper : génère un projet complet et retourne le chemin de sortie."""
    registry = ModuleRegistry()
    result = Resolver(registry).resolve(config)
    files = Composer(registry).compose(config, result)
    return Writer().write(files, output_dir, config, result, registry)


class TestGenerationFastAPI:
    """Tests de génération de projets FastAPI."""

    def test_projet_minimal_fichiers_essentiels(self, temp_output):
        """Un projet FastAPI minimal doit générer les fichiers essentiels."""
        config = ProjectConfig(name="testapi", framework="fastapi", modules=[])
        generer_projet(config, temp_output)

        out = Path(temp_output)
        assert (out / "main.py").exists()
        assert (out / "requirements.txt").exists()
        assert (out / ".env.example").exists()
        assert (out / "README.md").exists()
        assert (out / "gpi.lock").exists()

    def test_fastapi_avec_jwt_genere_auth(self, temp_output):
        """FastAPI + JWT doit générer les fichiers d'authentification."""
        config = ProjectConfig(name="testapi", framework="fastapi", modules=["auth-jwt"])
        generer_projet(config, temp_output)

        out = Path(temp_output)
        assert (out / "auth" / "security.py").exists()
        assert (out / "auth" / "routes.py").exists()

    def test_fastapi_avec_sqlite_genere_crud(self, temp_output):
        """FastAPI + SQLite doit générer les fichiers CRUD atomisés."""
        config = ProjectConfig(name="testapi", framework="fastapi", modules=["database-sqlite"])
        generer_projet(config, temp_output)

        out = Path(temp_output)
        crud_dir = out / "app" / "catalogue"
        assert (crud_dir / "create.py").exists()
        assert (crud_dir / "read.py").exists()
        assert (crud_dir / "update.py").exists()
        assert (crud_dir / "delete.py").exists()

    def test_gpi_lock_valide(self, temp_output):
        """Le gpi.lock généré doit être valide (checksum correct)."""
        from gpi.core.lock import LockFile

        config = ProjectConfig(name="testapi", framework="fastapi", modules=["auth-jwt"])
        generer_projet(config, temp_output)

        # LockFile.read() valide le checksum — si ça passe, c'est valide
        donnees = LockFile.read(str(Path(temp_output) / "gpi.lock"))
        assert donnees["config"]["name"] == "testapi"
        assert donnees["config"]["framework"] == "fastapi"

    def test_fastapi_avec_docker(self, temp_output):
        """FastAPI + Docker doit générer Dockerfile et .dockerignore."""
        config = ProjectConfig(name="testapi", framework="fastapi", modules=["docker"])
        generer_projet(config, temp_output)

        out = Path(temp_output)
        assert (out / "Dockerfile").exists()
        assert (out / ".dockerignore").exists()


class TestGenerationFlask:
    """Tests de génération de projets Flask."""

    def test_projet_flask_minimal(self, temp_output):
        """Un projet Flask minimal doit générer app.py."""
        config = ProjectConfig(name="testflask", framework="flask", modules=[])
        generer_projet(config, temp_output)

        out = Path(temp_output)
        assert (out / "app.py").exists()
        assert (out / "requirements.txt").exists()
        assert (out / "gpi.lock").exists()


class TestGenerationDjango:
    """Tests de génération de projets Django."""

    def test_projet_django_minimal(self, temp_output):
        """Un projet Django minimal doit générer manage.py."""
        config = ProjectConfig(name="testdjango", framework="django", modules=[])
        generer_projet(config, temp_output)

        out = Path(temp_output)
        assert (out / "manage.py").exists()
        assert (out / "requirements.txt").exists()
        assert (out / "gpi.lock").exists()


class TestAPIPublique:
    """Tests de l'API Python publique."""

    def test_gpi_compose(self, temp_output):
        """gpi.compose() doit générer un projet valide."""
        import gpi

        project = gpi.compose(
            name="testapi",
            framework="fastapi",
            modules=["auth-jwt"],
        )
        chemin = project.generate(temp_output)
        assert Path(chemin).exists()
        assert (Path(temp_output) / "main.py").exists()

    def test_gpi_from_yaml(self, temp_output, tmp_path):
        """gpi.from_yaml() doit charger et générer depuis un fichier YAML."""
        import gpi

        yaml_content = """
name: testapi
framework: fastapi
architecture: monolithic
modules: []
language: fr
port: 8000
"""
        yaml_file = tmp_path / "gpi.yaml"
        yaml_file.write_text(yaml_content)

        project = gpi.from_yaml(str(yaml_file))
        chemin = project.generate(temp_output)
        assert Path(chemin).exists()


# ============================================================
# Tests de propriété pour l'API publique (Property 20)
# ============================================================

from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st
import yaml


VALID_NAMES = st.from_regex(r"^[a-zA-Z][a-zA-Z0-9_]{1,20}$", fullmatch=True)
FRAMEWORKS = st.sampled_from(["fastapi", "flask", "django"])
VALID_PORTS = st.integers(min_value=1024, max_value=65535)


class TestAPIPubliqueProperties:
    """Tests de propriété pour l'API publique GPI."""

    # Property 20 : API publique — équivalence compose() et from_yaml()
    @given(
        name=VALID_NAMES,
        framework=FRAMEWORKS,
        port=VALID_PORTS,
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    def test_property_compose_equivalent_from_yaml(self, name, framework, port, tmp_path):
        """Property 20 : gpi.compose() et gpi.from_yaml() produisent des plans équivalents."""
        import gpi

        # Créer via compose()
        plan_compose = gpi.compose(name=name, framework=framework, port=port)

        # Créer via from_yaml()
        config_data = {"name": name, "framework": framework, "port": port}
        yaml_file = tmp_path / "gpi.yaml"
        yaml_file.write_text(yaml.dump(config_data), encoding="utf-8")
        plan_yaml = gpi.from_yaml(str(yaml_file))

        # Les deux plans doivent avoir la même config
        assert plan_compose.config.name == plan_yaml.config.name
        assert plan_compose.config.framework == plan_yaml.config.framework
        assert plan_compose.config.port == plan_yaml.config.port

    @given(
        name=VALID_NAMES,
        framework=FRAMEWORKS,
    )
    @settings(max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    def test_property_generate_cree_dossier(self, name, framework, tmp_path):
        """Property 20b : generate() crée toujours le dossier de sortie."""
        import gpi

        plan = gpi.compose(name=name, framework=framework)
        output = str(tmp_path / "output")
        chemin = plan.generate(output)
        assert Path(chemin).exists()


class TestReproductibiliteReplay:
    """Tests de reproductibilité via gpi replay."""

    # Property 19 : gpi replay — reproductibilité identique
    def test_property_replay_reproduit_identique(self, temp_output, tmp_path):
        """Property 19 : replay depuis gpi.lock produit les mêmes fichiers."""
        from gpi.core.lock import LockFile
        from gpi.core.resolver import ResolutionResult
        from gpi.core.composer import Composer
        from gpi.core.writer import Writer
        from gpi.modules.registry import ModuleRegistry

        # Génération initiale
        config = ProjectConfig(name="replaytest", framework="fastapi", modules=["auth-jwt"])
        generer_projet(config, temp_output)

        # Lecture du lock
        lock_path = str(Path(temp_output) / "gpi.lock")
        donnees_lock = LockFile.read(lock_path)
        config_reconstruite = LockFile.to_config(donnees_lock)

        # Régénération depuis le lock
        output2 = str(tmp_path / "replay_output")
        modules_resolus = [m["id"] for m in donnees_lock.get("resolved_modules", [])]
        auto_ajoutes = [m["id"] for m in donnees_lock.get("resolved_modules", []) if m.get("auto")]
        resolution = ResolutionResult(modules=modules_resolus, auto_added=auto_ajoutes, warnings=[])

        registry = ModuleRegistry()
        fichiers = Composer(registry).compose(config_reconstruite, resolution)
        Writer().write(fichiers, output2, config_reconstruite, resolution, registry)

        # Vérifier que les fichiers essentiels sont identiques
        for fichier in ["main.py", "requirements.txt", "README.md"]:
            original = (Path(temp_output) / fichier).read_text(encoding="utf-8")
            rejoue = (Path(output2) / fichier).read_text(encoding="utf-8")
            assert original == rejoue, f"Fichier '{fichier}' différent après replay"
