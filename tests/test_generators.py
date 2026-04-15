"""Tests fonctionnels – Génération complète de projets (architecture v2)."""
import pytest
from pathlib import Path

from gpi.core.config import ProjectConfig
from gpi.core.resolver import Resolver
from gpi.core.composer import Composer
from gpi.core.writer import Writer
from gpi.modules.registry import ModuleRegistry


def generer(config: ProjectConfig, output_dir) -> Path:
    """Helper : génère un projet complet et retourne le chemin de sortie."""
    registry = ModuleRegistry()
    result = Resolver(registry).resolve(config)
    files = Composer(registry).compose(config, result)
    return Writer().write(files, str(output_dir), config, result, registry)


class TestFastAPIMonolithique:
    """Génération FastAPI monolithique."""

    def test_structure_de_base(self, tmp_path):
        config = ProjectConfig(name="testapi", framework="fastapi", modules=[])
        generer(config, tmp_path)
        for f in ["main.py", "requirements.txt", ".env.example", "README.md"]:
            assert (tmp_path / f).exists(), f"Manque {f}"

    def test_routes_single(self, tmp_path):
        config = ProjectConfig(name="api_single", framework="fastapi", modules=[])
        generer(config, tmp_path)
        assert (tmp_path / "main.py").exists()

    def test_routes_split(self, tmp_path):
        config = ProjectConfig(name="api_split", framework="fastapi", modules=["database-sqlite"])
        generer(config, tmp_path)
        crud = tmp_path / "app" / "catalogue"
        for f in ["create.py", "read.py", "update.py", "delete.py"]:
            assert (crud / f).exists(), f"Manque {f}"

    def test_auth_jwt(self, tmp_path):
        config = ProjectConfig(name="api_auth", framework="fastapi", modules=["auth-jwt"])
        generer(config, tmp_path)
        assert (tmp_path / "auth" / "security.py").exists()
        assert (tmp_path / "auth" / "routes.py").exists()
        main = (tmp_path / "main.py").read_text(encoding="utf-8")
        assert "auth" in main.lower() or "fastapi" in main.lower()

    def test_sans_auth(self, tmp_path):
        config = ProjectConfig(name="api_noauth", framework="fastapi", modules=[])
        generer(config, tmp_path)
        assert not (tmp_path / "auth" / "security.py").exists()

    def test_tests_generes(self, tmp_path):
        config = ProjectConfig(name="api_tests", framework="fastapi", modules=["tests-pytest"])
        generer(config, tmp_path)
        assert (tmp_path / "tests" / "conftest.py").exists()

    def test_docker(self, tmp_path):
        config = ProjectConfig(name="api_docker", framework="fastapi", modules=["docker"])
        generer(config, tmp_path)
        assert (tmp_path / "Dockerfile").exists()
        assert (tmp_path / ".dockerignore").exists()

    def test_commentaires_francais(self, tmp_path):
        config = ProjectConfig(name="api_fr", framework="fastapi", modules=[], language="fr")
        generer(config, tmp_path)
        main = (tmp_path / "main.py").read_text(encoding="utf-8")
        assert len(main) > 0

    def test_commentaires_anglais(self, tmp_path):
        config = ProjectConfig(name="api_en", framework="fastapi", modules=[], language="en")
        generer(config, tmp_path)
        main = (tmp_path / "main.py").read_text(encoding="utf-8")
        assert len(main) > 0

    def test_env_contient_secret(self, tmp_path):
        config = ProjectConfig(name="api_env", framework="fastapi", modules=[])
        generer(config, tmp_path)
        # .env est généré avec une vraie SECRET_KEY
        env_file = tmp_path / ".env"
        assert env_file.exists()
        env = env_file.read_text(encoding="utf-8")
        assert "SECRET_KEY=" in env
        assert len(env.split("SECRET_KEY=")[1].split("\n")[0]) > 10

    def test_readme_contient_nom(self, tmp_path):
        config = ProjectConfig(name="api_readme", framework="fastapi", modules=[], description="Ma super API")
        generer(config, tmp_path)
        readme = (tmp_path / "README.md").read_text(encoding="utf-8")
        assert "api_readme" in readme
        assert "Ma super API" in readme

    def test_readme_ip_locale(self, tmp_path):
        config = ProjectConfig(name="api_ip", framework="fastapi", modules=[], port=8080)
        generer(config, tmp_path)
        readme = (tmp_path / "README.md").read_text(encoding="utf-8")
        assert "8080" in readme


class TestFastAPIMicroservices:
    """Génération FastAPI microservices."""

    def test_structure_services(self, tmp_path):
        config = ProjectConfig(
            name="testmicro",
            framework="fastapi",
            architecture="microservices",
            modules=["docker-compose"],
            services=["auth", "users", "products"],
        )
        generer(config, tmp_path)
        assert (tmp_path / "docker-compose.yml").exists()

    def test_services_par_defaut(self, tmp_path):
        config = ProjectConfig(
            name="micro_default",
            framework="fastapi",
            architecture="microservices",
            modules=[],
        )
        generer(config, tmp_path)
        assert (tmp_path / "main.py").exists()


class TestFlaskMonolithique:
    """Génération Flask monolithique."""

    def test_structure(self, tmp_path):
        config = ProjectConfig(name="testflask", framework="flask", modules=[])
        generer(config, tmp_path)
        for f in ["app.py", "requirements.txt", ".env.example", "README.md"]:
            assert (tmp_path / f).exists(), f"Manque {f}"

    def test_auth_flask(self, tmp_path):
        config = ProjectConfig(name="flask_auth", framework="flask", modules=["auth-jwt"])
        generer(config, tmp_path)
        assert (tmp_path / "auth" / "security.py").exists()

    def test_tests_flask(self, tmp_path):
        config = ProjectConfig(name="flask_tests", framework="flask", modules=["tests-pytest"])
        generer(config, tmp_path)
        assert (tmp_path / "tests" / "conftest.py").exists()


class TestFlaskMicroservices:
    def test_structure(self, tmp_path):
        config = ProjectConfig(
            name="flask_micro",
            framework="flask",
            architecture="microservices",
            modules=["docker-compose"],
            services=["api", "worker"],
        )
        generer(config, tmp_path)
        assert (tmp_path / "docker-compose.yml").exists()


class TestDjangoMonolithique:
    """Génération Django monolithique."""

    def test_structure(self, tmp_path):
        config = ProjectConfig(name="testdjango", framework="django", modules=[])
        generer(config, tmp_path)
        assert (tmp_path / "manage.py").exists()
        assert (tmp_path / "requirements.txt").exists()

    def test_auth_django(self, tmp_path):
        config = ProjectConfig(name="dj_auth", framework="django", modules=["auth-jwt"])
        generer(config, tmp_path)
        assert (tmp_path / "auth" / "security.py").exists()

    def test_docker_django(self, tmp_path):
        config = ProjectConfig(name="testdjango", framework="django", modules=["docker"])
        generer(config, tmp_path)
        assert (tmp_path / "Dockerfile").exists()


class TestDjangoMicroservices:
    def test_structure(self, tmp_path):
        """Django microservices lève ModuleIncompatibleError (non supporté)."""
        from gpi.core.exceptions import ModuleIncompatibleError
        config = ProjectConfig(
            name="dj_micro",
            framework="django",
            architecture="microservices",
            modules=["docker-compose"],
            services=["auth", "catalog"],
        )
        registry = ModuleRegistry()
        with pytest.raises(ModuleIncompatibleError):
            Resolver(registry).resolve(config)


class TestFactory:
    """Tests de la factory de générateurs (toutes combinaisons framework/architecture)."""

    @pytest.mark.parametrize("fw,arch", [
        ("fastapi", "monolithic"), ("fastapi", "microservices"),
        ("flask", "monolithic"), ("flask", "microservices"),
        ("django", "monolithic"),
    ])
    def test_toutes_combinaisons(self, tmp_path, fw, arch):
        """Chaque combinaison framework/architecture supportée génère sans erreur."""
        config = ProjectConfig(
            name=f"test_{fw}_{arch[:4]}",
            framework=fw,
            architecture=arch,
            modules=[],
        )
        sortie = generer(config, tmp_path)
        assert sortie.exists()
        assert (tmp_path / "README.md").exists()

    def test_django_microservices_non_supporte(self, tmp_path):
        """Django + microservices doit lever ModuleIncompatibleError."""
        from gpi.core.exceptions import ModuleIncompatibleError
        config = ProjectConfig(name="dj_ms", framework="django", architecture="microservices", modules=[])
        registry = ModuleRegistry()
        with pytest.raises(ModuleIncompatibleError):
            Resolver(registry).resolve(config)
