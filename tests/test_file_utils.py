"""Tests unitaires – Utilitaires fichiers."""
import pytest
from pathlib import Path
from gpi.utils.file_utils import (
    rendre_template, ecrire_fichier, generer_fichiers,
    est_admin, verifier_permissions,
)


class TestRendreTemplate:
    def test_template_simple(self):
        """Rendu d'un template avec variables."""
        result = rendre_template("Hello {{ name }}!", {"name": "GPI"})
        assert result == "Hello GPI!"

    def test_template_condition(self):
        """Rendu avec condition Jinja2."""
        tpl = "{% if actif %}ON{% else %}OFF{% endif %}"
        assert rendre_template(tpl, {"actif": True}) == "ON"
        assert rendre_template(tpl, {"actif": False}) == "OFF"

    def test_template_boucle(self):
        """Rendu avec boucle."""
        tpl = "{% for x in items %}{{ x }} {% endfor %}"
        result = rendre_template(tpl, {"items": ["a", "b", "c"]})
        assert "a" in result and "b" in result

    def test_template_vide(self):
        """Template vide → string vide."""
        assert rendre_template("", {}) == ""


class TestEcrireFichier:
    def test_creation_fichier(self, tmp_path):
        """Crée un fichier avec le bon contenu."""
        f = tmp_path / "test.txt"
        ecrire_fichier(f, "contenu")
        assert f.read_text(encoding="utf-8") == "contenu"

    def test_creation_sous_dossiers(self, tmp_path):
        """Crée les dossiers parents automatiquement."""
        f = tmp_path / "a" / "b" / "c" / "test.py"
        ecrire_fichier(f, "# test")
        assert f.exists()
        assert f.read_text(encoding="utf-8") == "# test"


class TestGenererFichiers:
    def test_generation_multiple(self, tmp_path):
        """Génère plusieurs fichiers d'un coup."""
        fichiers = {
            "main.py": "# {{ nom }}",
            "config/settings.py": "SECRET = '{{ secret }}'",
        }
        generer_fichiers(tmp_path, fichiers, {"nom": "app", "secret": "xyz"})
        assert (tmp_path / "main.py").read_text(encoding="utf-8") == "# app"
        assert "xyz" in (tmp_path / "config" / "settings.py").read_text(encoding="utf-8")


class TestPermissions:
    def test_est_admin_retourne_bool(self):
        """est_admin() retourne toujours un booléen."""
        assert isinstance(est_admin(), bool)

    def test_verifier_permissions_tmp(self, tmp_path):
        """On peut écrire dans un dossier temporaire."""
        assert verifier_permissions(tmp_path) is True
