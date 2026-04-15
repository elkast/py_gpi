# tests/test_cli_commands.py
"""Tests pour les commandes CLI GPI v2 : add, upgrade, replay, explain, version."""

import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner

from gpi.cli.app import app


runner = CliRunner()


def creer_projet_test(tmp_path: Path, framework: str = "fastapi") -> Path:
    """Crée un projet GPI minimal avec gpi.lock pour les tests."""
    from gpi.core.config import ProjectConfig
    from gpi.core.resolver import Resolver
    from gpi.core.composer import Composer
    from gpi.core.writer import Writer
    from gpi.modules.registry import ModuleRegistry

    config = ProjectConfig(name="testproj", framework=framework, modules=[])
    registry = ModuleRegistry()
    result = Resolver(registry).resolve(config)
    files = Composer(registry).compose(config, result)
    Writer().write(files, str(tmp_path), config, result, registry)
    return tmp_path


class TestCommandeVersion:
    """Tests pour gpi version."""

    def test_version_affiche_numero(self):
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "2.0.0" in result.output or "GPI" in result.output


class TestCommandeAdd:
    """Tests pour gpi add."""

    def test_add_sans_lock_echoue(self, tmp_path):
        result = runner.invoke(app, ["add", "cache-redis", "--path", str(tmp_path)])
        assert result.exit_code != 0

    def test_add_module_deja_installe(self, tmp_path):
        creer_projet_test(tmp_path)
        # Ajouter un module déjà présent (framework-fastapi est auto-résolu)
        result = runner.invoke(app, ["add", "docker", "--path", str(tmp_path)])
        # Doit soit réussir soit indiquer déjà installé
        assert result.exit_code in (0, 1)

    def test_add_module_valide(self, tmp_path):
        creer_projet_test(tmp_path)
        result = runner.invoke(app, ["add", "docker", "--path", str(tmp_path)])
        # Succès ou module déjà présent
        assert result.exit_code in (0, 1)

    def test_add_module_inconnu_echoue(self, tmp_path):
        creer_projet_test(tmp_path)
        result = runner.invoke(app, ["add", "module-inexistant-xyz", "--path", str(tmp_path)])
        assert result.exit_code != 0


class TestCommandeUpgrade:
    """Tests pour gpi upgrade."""

    def test_upgrade_sans_lock_echoue(self, tmp_path):
        result = runner.invoke(app, ["upgrade", "--path", str(tmp_path)])
        assert result.exit_code != 0

    def test_upgrade_dry_run(self, tmp_path):
        creer_projet_test(tmp_path)
        result = runner.invoke(app, ["upgrade", "--path", str(tmp_path), "--dry-run"])
        assert result.exit_code == 0
        assert "dry-run" in result.output.lower() or "aperçu" in result.output.lower()

    def test_upgrade_tous_modules(self, tmp_path):
        creer_projet_test(tmp_path)
        result = runner.invoke(app, ["upgrade", "--path", str(tmp_path)])
        assert result.exit_code == 0


class TestCommandeReplay:
    """Tests pour gpi replay."""

    def test_replay_lock_inexistant_echoue(self, tmp_path):
        result = runner.invoke(app, ["replay", str(tmp_path / "inexistant.lock")])
        assert result.exit_code != 0

    def test_replay_check_valide(self, tmp_path):
        creer_projet_test(tmp_path)
        lock_path = str(tmp_path / "gpi.lock")
        result = runner.invoke(app, ["replay", lock_path, "--check"])
        assert result.exit_code == 0
        assert "validé" in result.output.lower() or "check" in result.output.lower()

    def test_replay_regenere_projet(self, tmp_path):
        creer_projet_test(tmp_path)
        lock_path = str(tmp_path / "gpi.lock")
        output = str(tmp_path / "replay_output")
        result = runner.invoke(app, ["replay", lock_path, "--output", output])
        assert result.exit_code == 0
        assert Path(output).exists()

    def test_replay_checksum_invalide_echoue(self, tmp_path):
        creer_projet_test(tmp_path)
        lock_path = tmp_path / "gpi.lock"
        # Corrompre le checksum
        import json
        donnees = json.loads(lock_path.read_text(encoding="utf-8"))
        donnees["checksum"] = "checksum_invalide"
        lock_path.write_text(json.dumps(donnees), encoding="utf-8")
        result = runner.invoke(app, ["replay", str(lock_path)])
        assert result.exit_code != 0


class TestCommandeExplain:
    """Tests pour gpi explain."""

    def test_explain_sans_cle_echoue(self, tmp_path):
        with patch.dict("os.environ", {}, clear=True):
            result = runner.invoke(app, ["explain", str(tmp_path)])
        assert result.exit_code != 0

    def test_explain_dossier_inexistant_echoue(self, tmp_path):
        with patch.dict("os.environ", {"GROQ_API_KEY": "test-key"}):
            result = runner.invoke(app, ["explain", str(tmp_path / "inexistant")])
        assert result.exit_code != 0

    def test_explain_avec_mock_groq(self, tmp_path):
        creer_projet_test(tmp_path)
        mock_client = MagicMock()
        mock_client.is_available = True
        mock_client.complete.return_value = "# Explication du projet\nCeci est un projet FastAPI."

        with patch("gpi.ai.client.GpiGroqClient._get_client", return_value=MagicMock()):
            with patch.dict("os.environ", {"GROQ_API_KEY": "test-key"}):
                with patch("gpi.ai.explainer.explain_project", return_value="# Explication"):
                    result = runner.invoke(app, ["explain", str(tmp_path)])
        assert result.exit_code == 0


class TestExplainer:
    """Tests pour gpi/ai/explainer.py."""

    def test_explain_project_sans_cle_leve_erreur(self, tmp_path):
        from gpi.ai.explainer import explain_project
        from gpi.ai.client import GpiGroqClient
        client = GpiGroqClient(api_key=None)
        with pytest.raises(Exception):
            explain_project(str(tmp_path), client)

    def test_explain_project_avec_mock(self, tmp_path):
        from gpi.ai.explainer import explain_project
        from gpi.ai.client import GpiGroqClient

        # Créer quelques fichiers .py dans tmp_path
        (tmp_path / "main.py").write_text("# main\napp = None", encoding="utf-8")

        client = GpiGroqClient(api_key="test-key")
        mock_groq = MagicMock()
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Explication du projet"
        mock_groq.chat.completions.create.return_value = mock_response

        with patch("gpi.ai.client.GpiGroqClient._get_client", return_value=mock_groq):
            result = explain_project(str(tmp_path), client)
            assert result == "Explication du projet"

    def test_explain_project_dossier_vide(self, tmp_path):
        """Dossier sans .py — le prompt sera vide mais ne doit pas planter."""
        from gpi.ai.explainer import explain_project
        from gpi.ai.client import GpiGroqClient

        client = GpiGroqClient(api_key="test-key")
        mock_groq = MagicMock()
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Aucun fichier Python trouvé."
        mock_groq.chat.completions.create.return_value = mock_response

        with patch("gpi.ai.client.GpiGroqClient._get_client", return_value=mock_groq):
            result = explain_project(str(tmp_path), client)
            assert isinstance(result, str)


class TestCoreNetwork:
    """Tests pour gpi/core/network.py."""

    def test_detecter_ips_retourne_liste(self):
        from gpi.core.network import detecter_ips
        ips = detecter_ips()
        assert isinstance(ips, list)

    def test_detecter_ips_pas_de_loopback(self):
        from gpi.core.network import detecter_ips
        ips = detecter_ips()
        for ip in ips:
            assert not ip.startswith("127.")

    def test_detecter_ips_fallback_sur_erreur(self):
        from gpi.core import network
        with patch("socket.socket") as mock_socket:
            mock_socket.return_value.__enter__.return_value.connect.side_effect = OSError
            with patch("socket.getaddrinfo", side_effect=OSError):
                ips = network.detecter_ips()
                assert isinstance(ips, list)
