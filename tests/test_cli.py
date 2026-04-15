# tests/test_cli.py
"""Tests fonctionnels — CLI GPI v2."""

import pytest
import yaml
from pathlib import Path
from typer.testing import CliRunner

from gpi.cli.app import app

runner = CliRunner()


class TestCLIVersion:
    """Tests de la commande gpi version."""

    def test_version_affiche_numero(self):
        """La commande version doit afficher le numéro de version."""
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "2.0.0" in result.output or "GPI" in result.output

    def test_help_affiche_aide(self):
        """L'aide principale doit s'afficher."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "gpi" in result.output.lower() or "GPI" in result.output


class TestCLIInit:
    """Tests de la commande gpi init."""

    def test_init_avec_config_yaml(self, tmp_path):
        """gpi init -c fichier.yaml doit générer un projet."""
        config_data = {
            "name": "testcli",
            "framework": "fastapi",
            "architecture": "monolithic",
            "modules": [],
            "language": "fr",
            "port": 8000,
        }
        yaml_file = tmp_path / "gpi.yaml"
        yaml_file.write_text(yaml.dump(config_data), encoding="utf-8")

        output_dir = str(tmp_path / "output")
        result = runner.invoke(app, ["init", "-c", str(yaml_file), "-o", output_dir])

        assert result.exit_code == 0
        assert (Path(output_dir) / "main.py").exists()

    def test_init_config_introuvable(self):
        """Un fichier config inexistant doit retourner exit code 1."""
        result = runner.invoke(app, ["init", "-c", "fichier_inexistant.yaml"])
        assert result.exit_code != 0

    def test_init_config_invalide(self, tmp_path):
        """Une config avec framework invalide doit retourner exit code 1."""
        config_data = {"name": "test", "framework": "rails"}
        yaml_file = tmp_path / "bad.yaml"
        yaml_file.write_text(yaml.dump(config_data), encoding="utf-8")

        result = runner.invoke(app, ["init", "-c", str(yaml_file)])
        assert result.exit_code != 0


class TestCLIPluginList:
    """Tests de la commande gpi plugin list."""

    def test_plugin_list_affiche_modules(self):
        """gpi plugin list doit afficher les modules disponibles."""
        result = runner.invoke(app, ["plugin", "list"])
        assert result.exit_code == 0
        assert "framework-fastapi" in result.output or "FastAPI" in result.output


class TestCLIReplay:
    """Tests de la commande gpi replay."""

    def test_replay_check_valide(self, tmp_path):
        """gpi replay --check doit valider un lock valide."""
        from gpi.core.config import ProjectConfig
        from gpi.core.resolver import ResolutionResult
        from gpi.core.lock import LockFile

        config = ProjectConfig(name="replaytest", framework="fastapi")
        resolution = ResolutionResult(modules=["framework-fastapi"], auto_added=[], warnings=[])
        donnees = LockFile.create(config, resolution, [])
        LockFile.write(donnees, str(tmp_path))

        lock_path = str(tmp_path / "gpi.lock")
        result = runner.invoke(app, ["replay", lock_path, "--check"])
        assert result.exit_code == 0
        assert "valid" in result.output.lower() or "✅" in result.output

    def test_replay_lock_inexistant(self):
        """gpi replay avec un lock inexistant doit retourner exit code 1."""
        result = runner.invoke(app, ["replay", "inexistant.lock"])
        assert result.exit_code != 0


class TestCLIExplain:
    """Tests de la commande gpi explain."""

    def test_explain_sans_cle_api(self, tmp_path):
        """gpi explain sans GROQ_API_KEY doit retourner exit code 1."""
        import os
        env_backup = os.environ.pop("GROQ_API_KEY", None)
        try:
            result = runner.invoke(app, ["explain", str(tmp_path)], env={"GROQ_API_KEY": ""})
            assert result.exit_code != 0
        finally:
            if env_backup:
                os.environ["GROQ_API_KEY"] = env_backup
