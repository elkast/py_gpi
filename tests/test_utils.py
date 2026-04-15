# tests/test_utils.py
"""Tests pour les utilitaires GPI v2 : filesystem, network, display, ai/completion."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestFilesystem:
    """Tests pour gpi/utils/filesystem.py."""

    def test_ecrire_fichier_cree_fichier(self, tmp_path):
        from gpi.utils.filesystem import ecrire_fichier
        chemin = tmp_path / "test.txt"
        ecrire_fichier(chemin, "bonjour")
        assert chemin.exists()
        assert chemin.read_text(encoding="utf-8") == "bonjour"

    def test_ecrire_fichier_cree_dossiers_parents(self, tmp_path):
        from gpi.utils.filesystem import ecrire_fichier
        chemin = tmp_path / "a" / "b" / "c.txt"
        ecrire_fichier(chemin, "contenu")
        assert chemin.exists()

    def test_ecrire_fichier_retourne_chemin_absolu(self, tmp_path):
        from gpi.utils.filesystem import ecrire_fichier
        chemin = tmp_path / "f.txt"
        resultat = ecrire_fichier(chemin, "x")
        assert resultat.is_absolute()

    def test_lire_fichier(self, tmp_path):
        from gpi.utils.filesystem import lire_fichier
        chemin = tmp_path / "test.txt"
        chemin.write_text("contenu test", encoding="utf-8")
        assert lire_fichier(chemin) == "contenu test"

    def test_lire_fichier_inexistant_leve_erreur(self, tmp_path):
        from gpi.utils.filesystem import lire_fichier
        with pytest.raises(FileNotFoundError):
            lire_fichier(tmp_path / "inexistant.txt")


class TestNetwork:
    """Tests pour gpi/utils/network.py."""

    def test_detecter_ip_retourne_string(self):
        from gpi.utils.network import detecter_ip
        ip = detecter_ip()
        assert isinstance(ip, str)
        assert len(ip) > 0

    def test_detecter_ip_format_valide(self):
        from gpi.utils.network import detecter_ip
        ip = detecter_ip()
        # Doit être une IP valide ou 127.0.0.1
        parties = ip.split(".")
        assert len(parties) == 4

    def test_detecter_ip_fallback_sur_erreur(self):
        """En cas d'erreur réseau, retourne 127.0.0.1."""
        from gpi.utils import network
        with patch("socket.socket") as mock_socket:
            mock_socket.return_value.__enter__.return_value.connect.side_effect = OSError
            with patch("socket.gethostbyname", side_effect=OSError):
                ip = network.detecter_ip()
                assert ip == "127.0.0.1"


class TestDisplay:
    """Tests pour gpi/utils/display.py."""

    def test_afficher_succes(self, capsys):
        from gpi.utils.display import afficher_succes
        # Ne doit pas lever d'exception
        afficher_succes("Projet généré avec succès")

    def test_afficher_erreur(self, capsys):
        from gpi.utils.display import afficher_erreur
        afficher_erreur("Une erreur est survenue")

    def test_afficher_avertissement(self, capsys):
        from gpi.utils.display import afficher_avertissement
        afficher_avertissement("Attention !")

    def test_afficher_info(self, capsys):
        from gpi.utils.display import afficher_info
        afficher_info("Information")

    def test_afficher_panel(self, capsys):
        from gpi.utils.display import afficher_panel
        afficher_panel("Titre", "Contenu du panel")


class TestCompletion:
    """Tests pour gpi/ai/completion.py."""

    def test_completer_description_echec_silencieux_sans_cle(self):
        """Sans clé API, retourne une chaîne vide (échec silencieux)."""
        from gpi.ai.completion import completer_description
        from gpi.ai.client import GpiGroqClient
        client = GpiGroqClient(api_key=None)
        result = completer_description("monapi", "fastapi", ["auth-jwt"], client)
        assert result == ""

    def test_completer_description_retourne_string(self):
        """completer_description() retourne toujours une str."""
        from gpi.ai.completion import completer_description
        from gpi.ai.client import GpiGroqClient
        client = GpiGroqClient(api_key=None)
        result = completer_description("test", "flask", [], client)
        assert isinstance(result, str)

    def test_completer_description_avec_mock(self):
        """Avec un mock, retourne la réponse du modèle."""
        from gpi.ai.completion import completer_description
        from gpi.ai.client import GpiGroqClient

        client = GpiGroqClient(api_key="test-key")
        mock_groq = MagicMock()
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "  API e-commerce FastAPI  "
        mock_groq.chat.completions.create.return_value = mock_response

        with patch("gpi.ai.client.GpiGroqClient._get_client", return_value=mock_groq):
            result = completer_description("shop", "fastapi", ["database-postgres"], client)
            assert result == "API e-commerce FastAPI"
