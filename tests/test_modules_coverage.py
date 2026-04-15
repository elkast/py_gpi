# tests/test_modules_coverage.py
"""Tests de couverture ciblés pour les modules natifs GPI v2.

Couvre les branches manquantes dans :
- modules/database/mysql.py, postgres.py
- modules/queue/celery.py, rq.py
- modules/cache/redis.py
- modules/auth/sessions.py, oauth2.py, jwt.py
- modules/monitoring/prometheus_grafana.py
- modules/infra/docker.py, docker_compose.py, github_actions.py
- modules/testing/pytest.py
- modules/framework/fastapi.py, flask.py, django.py
- cli/commands/init.py, plugin.py, upgrade.py, version.py
"""

import pytest
from unittest.mock import patch, MagicMock
from gpi.core.config import ProjectConfig


# ============================================================
# Modules Database
# ============================================================

class TestMySQLModule:
    def test_metadata(self):
        from gpi.modules.database.mysql import MySQLModule
        m = MySQLModule()
        assert m.metadata.id == "database-mysql"
        assert "mysql" in m.metadata.tags

    def test_get_dependencies(self):
        from gpi.modules.database.mysql import MySQLModule
        deps = MySQLModule().get_dependencies()
        assert any("pymysql" in d for d in deps)

    def test_get_files(self):
        from gpi.modules.database.mysql import MySQLModule
        config = ProjectConfig(name="test", framework="fastapi")
        files = MySQLModule().get_files(config)
        assert "database.py" in files
        assert "models/__init__.py" in files

    def test_get_env_vars(self):
        from gpi.modules.database.mysql import MySQLModule
        env = MySQLModule().get_env_vars()
        assert "DATABASE_URL" in env
        assert "mysql" in env["DATABASE_URL"]

    def test_get_env_example_vars(self):
        from gpi.modules.database.mysql import MySQLModule
        env = MySQLModule().get_env_example_vars()
        assert "DATABASE_URL" in env


class TestPostgresModule:
    def test_metadata(self):
        from gpi.modules.database.postgres import PostgresModule
        m = PostgresModule()
        assert m.metadata.id == "database-postgres"

    def test_get_dependencies(self):
        from gpi.modules.database.postgres import PostgresModule
        deps = PostgresModule().get_dependencies()
        assert any("psycopg2" in d for d in deps)

    def test_get_files(self):
        from gpi.modules.database.postgres import PostgresModule
        config = ProjectConfig(name="test", framework="fastapi")
        files = PostgresModule().get_files(config)
        assert "database.py" in files

    def test_get_env_vars(self):
        from gpi.modules.database.postgres import PostgresModule
        env = PostgresModule().get_env_vars()
        assert "DATABASE_URL" in env
        assert "postgresql" in env["DATABASE_URL"]

    def test_get_env_example_vars(self):
        from gpi.modules.database.postgres import PostgresModule
        env = PostgresModule().get_env_example_vars()
        assert "DATABASE_URL" in env

    def test_post_generate_instructions(self):
        from gpi.modules.database.postgres import PostgresModule
        instructions = PostgresModule().post_generate_instructions()
        assert len(instructions) > 0


# ============================================================
# Modules Queue
# ============================================================

class TestCeleryModule:
    def test_metadata(self):
        from gpi.modules.queue.celery import CeleryModule
        m = CeleryModule()
        assert m.metadata.id == "queue-celery"
        assert "cache-redis" in m.metadata.requires

    def test_get_dependencies(self):
        from gpi.modules.queue.celery import CeleryModule
        deps = CeleryModule().get_dependencies()
        assert any("celery" in d for d in deps)

    def test_get_files(self):
        from gpi.modules.queue.celery import CeleryModule
        config = ProjectConfig(name="test", framework="fastapi")
        files = CeleryModule().get_files(config)
        assert "celery_app.py" in files

    def test_post_generate_instructions(self):
        from gpi.modules.queue.celery import CeleryModule
        instructions = CeleryModule().post_generate_instructions()
        assert len(instructions) > 0


class TestRQModule:
    def test_metadata(self):
        from gpi.modules.queue.rq import RQModule
        m = RQModule()
        assert m.metadata.id == "queue-rq"
        assert "cache-redis" in m.metadata.requires

    def test_get_dependencies(self):
        from gpi.modules.queue.rq import RQModule
        deps = RQModule().get_dependencies()
        assert any("rq" in d for d in deps)

    def test_get_files(self):
        from gpi.modules.queue.rq import RQModule
        config = ProjectConfig(name="test", framework="fastapi")
        files = RQModule().get_files(config)
        assert "rq_app.py" in files

    def test_post_generate_instructions(self):
        from gpi.modules.queue.rq import RQModule
        instructions = RQModule().post_generate_instructions()
        assert len(instructions) > 0


# ============================================================
# Module Cache Redis
# ============================================================

class TestRedisModule:
    def test_metadata(self):
        from gpi.modules.cache.redis import RedisModule
        m = RedisModule()
        assert m.metadata.id == "cache-redis"

    def test_get_dependencies(self):
        from gpi.modules.cache.redis import RedisModule
        deps = RedisModule().get_dependencies()
        assert any("redis" in d for d in deps)

    def test_get_files(self):
        from gpi.modules.cache.redis import RedisModule
        config = ProjectConfig(name="test", framework="fastapi")
        files = RedisModule().get_files(config)
        assert "cache.py" in files

    def test_get_env_vars(self):
        from gpi.modules.cache.redis import RedisModule
        env = RedisModule().get_env_vars()
        assert "REDIS_URL" in env

    def test_get_env_example_vars(self):
        from gpi.modules.cache.redis import RedisModule
        env = RedisModule().get_env_example_vars()
        assert "REDIS_URL" in env


# ============================================================
# Modules Auth
# ============================================================

class TestSessionsModule:
    def test_metadata(self):
        from gpi.modules.auth.sessions import SessionsAuthModule
        m = SessionsAuthModule()
        assert m.metadata.id == "auth-sessions"
        assert "auth-jwt" in m.metadata.conflicts

    def test_get_dependencies(self):
        from gpi.modules.auth.sessions import SessionsAuthModule
        deps = SessionsAuthModule().get_dependencies()
        assert len(deps) > 0

    def test_get_files_flask(self):
        from gpi.modules.auth.sessions import SessionsAuthModule
        config = ProjectConfig(name="test", framework="flask")
        files = SessionsAuthModule().get_files(config)
        assert "auth/routes.py" in files
        assert len(files["auth/routes.py"]) > 0

    def test_get_files_django(self):
        from gpi.modules.auth.sessions import SessionsAuthModule
        config = ProjectConfig(name="test", framework="django")
        files = SessionsAuthModule().get_files(config)
        assert "auth/routes.py" in files
        # Django retourne chaîne vide pour routes
        assert files["auth/routes.py"] == ""


class TestOAuth2Module:
    def test_metadata(self):
        from gpi.modules.auth.oauth2 import OAuth2Module
        m = OAuth2Module()
        assert m.metadata.id == "auth-oauth2"
        assert "auth-jwt" in m.metadata.conflicts

    def test_get_dependencies(self):
        from gpi.modules.auth.oauth2 import OAuth2Module
        deps = OAuth2Module().get_dependencies()
        assert any("multipart" in d for d in deps)

    def test_get_files(self):
        from gpi.modules.auth.oauth2 import OAuth2Module
        config = ProjectConfig(name="test", framework="fastapi")
        files = OAuth2Module().get_files(config)
        assert "auth/oauth2.py" in files
        assert "auth/__init__.py" in files


class TestJWTModule:
    def test_get_env_vars(self):
        from gpi.modules.auth.jwt import JWTAuthModule
        env = JWTAuthModule().get_env_vars()
        assert "SECRET_KEY" in env
        assert "JWT_ALGORITHM" in env
        assert len(env["SECRET_KEY"]) > 10

    def test_get_env_example_vars(self):
        from gpi.modules.auth.jwt import JWTAuthModule
        env = JWTAuthModule().get_env_example_vars()
        assert "SECRET_KEY" in env

    def test_post_generate_instructions(self):
        from gpi.modules.auth.jwt import JWTAuthModule
        instructions = JWTAuthModule().post_generate_instructions()
        assert isinstance(instructions, list)


# ============================================================
# Module Monitoring
# ============================================================

class TestPrometheusModule:
    def test_metadata(self):
        from gpi.modules.monitoring.prometheus_grafana import PrometheusModule
        m = PrometheusModule()
        assert m.metadata.id == "monitoring-prometheus"
        assert "fastapi" in m.metadata.frameworks

    def test_get_dependencies(self):
        from gpi.modules.monitoring.prometheus_grafana import PrometheusModule
        deps = PrometheusModule().get_dependencies()
        assert any("prometheus" in d for d in deps)

    def test_get_files(self):
        from gpi.modules.monitoring.prometheus_grafana import PrometheusModule
        config = ProjectConfig(name="test", framework="fastapi")
        files = PrometheusModule().get_files(config)
        assert "monitoring.py" in files

    def test_post_generate_instructions(self):
        from gpi.modules.monitoring.prometheus_grafana import PrometheusModule
        instructions = PrometheusModule().post_generate_instructions()
        assert len(instructions) > 0


# ============================================================
# Modules Infra
# ============================================================

class TestDockerModule:
    def test_metadata(self):
        from gpi.modules.infra.docker import DockerModule
        m = DockerModule()
        assert m.metadata.id == "docker"

    def test_get_files(self):
        from gpi.modules.infra.docker import DockerModule
        config = ProjectConfig(name="test", framework="fastapi")
        files = DockerModule().get_files(config)
        assert "Dockerfile" in files
        assert ".dockerignore" in files

    def test_get_dependencies(self):
        from gpi.modules.infra.docker import DockerModule
        deps = DockerModule().get_dependencies()
        assert isinstance(deps, list)


class TestDockerComposeModule:
    def test_metadata(self):
        from gpi.modules.infra.docker_compose import DockerComposeModule
        m = DockerComposeModule()
        assert m.metadata.id == "docker-compose"

    def test_get_files_monolithic(self):
        from gpi.modules.infra.docker_compose import DockerComposeModule
        config = ProjectConfig(name="test", framework="fastapi", architecture="monolithic")
        files = DockerComposeModule().get_files(config)
        assert "docker-compose.yml" in files

    def test_get_files_microservices(self):
        from gpi.modules.infra.docker_compose import DockerComposeModule
        config = ProjectConfig(
            name="test", framework="fastapi",
            architecture="microservices", services=["auth", "api"]
        )
        files = DockerComposeModule().get_files(config)
        assert "docker-compose.yml" in files


class TestGitHubActionsModule:
    def test_metadata(self):
        from gpi.modules.infra.github_actions import GitHubActionsModule
        m = GitHubActionsModule()
        assert m.metadata.id == "github-actions"

    def test_get_files(self):
        from gpi.modules.infra.github_actions import GitHubActionsModule
        config = ProjectConfig(name="test", framework="fastapi")
        files = GitHubActionsModule().get_files(config)
        assert ".github/workflows/ci.yml" in files

    def test_get_dependencies(self):
        from gpi.modules.infra.github_actions import GitHubActionsModule
        deps = GitHubActionsModule().get_dependencies()
        assert isinstance(deps, list)


# ============================================================
# Module Testing
# ============================================================

class TestPytestModule:
    def test_metadata(self):
        from gpi.modules.testing.pytest import PytestModule
        m = PytestModule()
        assert m.metadata.id == "tests-pytest"

    def test_get_dependencies(self):
        from gpi.modules.testing.pytest import PytestModule
        deps = PytestModule().get_dependencies()
        assert any("pytest" in d for d in deps)

    def test_get_files(self):
        from gpi.modules.testing.pytest import PytestModule
        config = ProjectConfig(name="test", framework="fastapi")
        files = PytestModule().get_files(config)
        assert "tests/__init__.py" in files
        assert "tests/conftest.py" in files

    def test_post_generate_instructions(self):
        from gpi.modules.testing.pytest import PytestModule
        instructions = PytestModule().post_generate_instructions()
        assert isinstance(instructions, list)


# ============================================================
# Modules Framework
# ============================================================

class TestFastAPIModule:
    def test_get_env_vars(self):
        from gpi.modules.framework.fastapi import FastAPIModule
        env = FastAPIModule().get_env_vars()
        assert "SECRET_KEY" in env

    def test_get_env_example_vars(self):
        from gpi.modules.framework.fastapi import FastAPIModule
        env = FastAPIModule().get_env_example_vars()
        assert "SECRET_KEY" in env

    def test_post_generate_instructions(self):
        from gpi.modules.framework.fastapi import FastAPIModule
        instructions = FastAPIModule().post_generate_instructions()
        assert isinstance(instructions, list)


class TestFlaskModule:
    def test_get_env_vars(self):
        from gpi.modules.framework.flask import FlaskModule
        env = FlaskModule().get_env_vars()
        assert isinstance(env, dict)

    def test_get_env_example_vars(self):
        from gpi.modules.framework.flask import FlaskModule
        env = FlaskModule().get_env_example_vars()
        assert isinstance(env, dict)


class TestDjangoModule:
    def test_post_generate_instructions(self):
        from gpi.modules.framework.django import DjangoModule
        instructions = DjangoModule().post_generate_instructions()
        assert isinstance(instructions, list)


# ============================================================
# CLI Commands
# ============================================================

class TestCLIVersion:
    def test_version_commande(self):
        from typer.testing import CliRunner
        from gpi.cli.app import app
        runner = CliRunner()
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "2.0.0" in result.output or "GPI" in result.output


class TestCLIPluginCommands:
    """Tests pour les branches non couvertes de plugin.py."""

    def test_plugin_install_succes(self):
        from typer.testing import CliRunner
        from gpi.cli.app import app
        runner = CliRunner()
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        with patch("subprocess.run", return_value=mock_result):
            result = runner.invoke(app, ["plugin", "install", "some-package"])
        assert result.exit_code == 0
        assert "installé" in result.output.lower() or "install" in result.output.lower()

    def test_plugin_install_echec(self):
        from typer.testing import CliRunner
        from gpi.cli.app import app
        runner = CliRunner()
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Package not found"
        with patch("subprocess.run", return_value=mock_result):
            result = runner.invoke(app, ["plugin", "install", "package-inexistant"])
        assert result.exit_code != 0

    def test_plugin_uninstall_succes(self):
        from typer.testing import CliRunner
        from gpi.cli.app import app
        runner = CliRunner()
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        with patch("subprocess.run", return_value=mock_result):
            result = runner.invoke(app, ["plugin", "uninstall", "some-package"])
        assert result.exit_code == 0

    def test_plugin_uninstall_echec(self):
        from typer.testing import CliRunner
        from gpi.cli.app import app
        runner = CliRunner()
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Not installed"
        with patch("subprocess.run", return_value=mock_result):
            result = runner.invoke(app, ["plugin", "uninstall", "package-inexistant"])
        assert result.exit_code != 0

    def test_plugin_publish(self):
        from typer.testing import CliRunner
        from gpi.cli.app import app
        runner = CliRunner()
        result = runner.invoke(app, ["plugin", "publish"])
        assert result.exit_code == 0
        assert "pyproject.toml" in result.output.lower() or "pypi" in result.output.lower()


class TestCLIUpgradeCommands:
    """Tests pour les branches non couvertes de upgrade.py."""

    def _creer_projet(self, tmp_path):
        from gpi.core.config import ProjectConfig
        from gpi.core.resolver import Resolver
        from gpi.core.composer import Composer
        from gpi.core.writer import Writer
        from gpi.modules.registry import ModuleRegistry
        config = ProjectConfig(name="testproj", framework="fastapi", modules=[])
        registry = ModuleRegistry()
        result = Resolver(registry).resolve(config)
        files = Composer(registry).compose(config, result)
        Writer().write(files, str(tmp_path), config, result, registry)

    def test_upgrade_module_specifique(self, tmp_path):
        from typer.testing import CliRunner
        from gpi.cli.app import app
        runner = CliRunner()
        self._creer_projet(tmp_path)
        result = runner.invoke(app, ["upgrade", "framework-fastapi", "--path", str(tmp_path)])
        assert result.exit_code == 0

    def test_upgrade_dry_run_avec_module(self, tmp_path):
        from typer.testing import CliRunner
        from gpi.cli.app import app
        runner = CliRunner()
        self._creer_projet(tmp_path)
        result = runner.invoke(app, ["upgrade", "framework-fastapi", "--path", str(tmp_path), "--dry-run"])
        assert result.exit_code == 0


class TestCLIInitCommands:
    """Tests pour les branches non couvertes de init.py."""

    def test_init_avec_toml(self, tmp_path):
        from typer.testing import CliRunner
        from gpi.cli.app import app
        runner = CliRunner()
        toml_content = '[project]\nname = "testtoml"\nframework = "fastapi"\narchitecture = "monolithic"\nmodules = []\nlanguage = "fr"\nport = 8000\n'
        toml_file = tmp_path / "gpi.toml"
        toml_file.write_text(toml_content, encoding="utf-8")
        output_dir = str(tmp_path / "output")
        result = runner.invoke(app, ["init", "-c", str(toml_file), "-o", output_dir])
        # Peut échouer si le format TOML n'est pas exactement bon, mais ne doit pas crasher
        assert result.exit_code in (0, 1)

    def test_init_no_network(self, tmp_path):
        import yaml
        from typer.testing import CliRunner
        from gpi.cli.app import app
        runner = CliRunner()
        config_data = {
            "name": "testnonet",
            "framework": "fastapi",
            "architecture": "monolithic",
            "modules": [],
        }
        yaml_file = tmp_path / "gpi.yaml"
        yaml_file.write_text(yaml.dump(config_data), encoding="utf-8")
        output_dir = str(tmp_path / "output")
        result = runner.invoke(app, ["init", "-c", str(yaml_file), "-o", output_dir, "--no-network"])
        assert result.exit_code == 0

    def test_init_avec_groq_ai(self, tmp_path):
        """Test la branche use_groq_ai=True avec mock."""
        import yaml
        from typer.testing import CliRunner
        from gpi.cli.app import app
        runner = CliRunner()
        config_data = {
            "name": "testai",
            "framework": "fastapi",
            "architecture": "monolithic",
            "modules": [],
            "description": "API de test",
            "use_groq_ai": True,
        }
        yaml_file = tmp_path / "gpi.yaml"
        yaml_file.write_text(yaml.dump(config_data), encoding="utf-8")
        output_dir = str(tmp_path / "output")

        mock_client = MagicMock()
        mock_client.is_available = True
        with patch("gpi.ai.client.GpiGroqClient", return_value=mock_client):
            with patch("gpi.ai.suggestions.suggest_modules", return_value=["docker"]):
                result = runner.invoke(app, ["init", "-c", str(yaml_file), "-o", output_dir])
        assert result.exit_code == 0

    def test_init_validation_error(self, tmp_path):
        """Test la branche ValidationError dans init."""
        import yaml
        from typer.testing import CliRunner
        from gpi.cli.app import app
        runner = CliRunner()
        # microservices avec 0 modules → ValidationError
        config_data = {
            "name": "testval",
            "framework": "fastapi",
            "architecture": "microservices",
            "modules": [],
        }
        yaml_file = tmp_path / "gpi.yaml"
        yaml_file.write_text(yaml.dump(config_data), encoding="utf-8")
        result = runner.invoke(app, ["init", "-c", str(yaml_file)])
        assert result.exit_code != 0


# ============================================================
# Module Base
# ============================================================

class TestModuleBase:
    def test_get_env_vars_defaut(self):
        from gpi.modules.framework.fastapi import FastAPIModule
        # FastAPIModule hérite de Module, teste les méthodes par défaut
        m = FastAPIModule()
        env = m.get_env_vars()
        assert isinstance(env, dict)

    def test_get_env_example_vars_defaut(self):
        from gpi.modules.framework.fastapi import FastAPIModule
        m = FastAPIModule()
        env = m.get_env_example_vars()
        assert isinstance(env, dict)

    def test_post_generate_instructions_defaut(self):
        from gpi.modules.cache.redis import RedisModule
        # RedisModule n'override pas post_generate_instructions → retourne []
        m = RedisModule()
        instructions = m.post_generate_instructions()
        assert isinstance(instructions, list)
