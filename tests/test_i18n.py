"""Tests unitaires – Internationalisation."""
from gpi.utils.i18n import cmt, COMMENTAIRES


class TestI18n:
    def test_commentaire_francais(self):
        """Les commentaires FR commencent par #."""
        result = cmt("main_app", "fr")
        assert result.startswith("#")
        assert "principal" in result.lower() or "application" in result.lower()

    def test_commentaire_anglais(self):
        """Les commentaires EN sont en anglais."""
        result = cmt("main_app", "en")
        assert "Main" in result or "entry" in result.lower()

    def test_commentaire_bilingue(self):
        """Le mode bilingue contient les deux langues."""
        result = cmt("main_app", "bilingue")
        assert "#" in result
        # Doit contenir les deux versions
        lines = result.strip().split("\n")
        assert len(lines) == 2

    def test_cle_inconnue(self):
        """Une clé inconnue retourne un commentaire par défaut."""
        result = cmt("cle_qui_existe_pas", "fr")
        assert "#" in result

    def test_toutes_cles_ont_fr_et_en(self):
        """Chaque entrée a fr et en."""
        for cle, traductions in COMMENTAIRES.items():
            assert "fr" in traductions, f"Clé {cle} manque 'fr'"
            assert "en" in traductions, f"Clé {cle} manque 'en'"
