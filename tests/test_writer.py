# tests/test_writer.py
"""Tests unitaires pour le Writer GPI."""

import pytest
from pathlib import Path

from gpi.core.writer import Writer
from gpi.core.config import ProjectConfig
from gpi.core.resolver import ResolutionResult


class TestWriter:
    """Tests de l'écriture des fichiers sur disque."""

    def test_write_cree_dossier_sortie(self, tmp_path):
        """write() doit créer le dossier de sortie s'il n'existe pas."""
        dossier = tmp_path / "nouveau_projet"
        writer = Writer()
        writer.write({}, str(dossier))
        assert dossier.exists()

    def test_write_cree_tous_les_fichiers(self, tmp_path):
        """write() doit créer tous les fichiers du dictionnaire."""
        fichiers = {
            "main.py": "# main",
            "sous_dossier/config.py": "# config",
        }
        writer = Writer()
        writer.write(fichiers, str(tmp_path))

        assert (tmp_path / "main.py").exists()
        assert (tmp_path / "sous_dossier" / "config.py").exists()

    def test_write_contenu_correct(self, tmp_path):
        """write() doit écrire le contenu correct dans chaque fichier."""
        fichiers = {"test.py": "print('bonjour')"}
        writer = Writer()
        writer.write(fichiers, str(tmp_path))

        contenu = (tmp_path / "test.py").read_text(encoding="utf-8")
        assert contenu == "print('bonjour')"

    def test_write_retourne_chemin_absolu(self, tmp_path):
        """write() doit retourner le chemin absolu du dossier de sortie."""
        writer = Writer()
        chemin = writer.write({}, str(tmp_path))
        assert chemin.is_absolute()

    def test_write_genere_lock_si_config_fournie(self, tmp_path):
        """write() doit générer gpi.lock si config + resolution + registry fournis."""
        from gpi.modules.registry import ModuleRegistry

        config = ProjectConfig(name="test", framework="fastapi", modules=[])
        resolution = ResolutionResult(
            modules=["framework-fastapi"],
            auto_added=[],
            warnings=[],
        )
        registry = ModuleRegistry()

        writer = Writer()
        writer.write({}, str(tmp_path), config, resolution, registry)

        assert (tmp_path / "gpi.lock").exists()


# ============================================================
# Tests de propriété (Property-Based Testing) avec Hypothesis
# ============================================================

from hypothesis import given, settings
from hypothesis import strategies as st
from gpi.modules.registry import ModuleRegistry
from gpi.core.resolver import Resolver
from gpi.core.composer import Composer
from hypothesis.stateful import RuleBasedStateMachine
from hypothesis import HealthCheck
import tempfile
import os


# Stratégie pour des noms de fichiers valides
NOMS_FICHIERS = st.from_regex(r"[a-zA-Z][a-zA-Z0-9_]{0,20}\.(py|txt|md|yml)", fullmatch=True)
CONTENUS = st.text(min_size=0, max_size=200)


class TestWriterProperties:
    """Tests de propriété pour le Writer."""

    # Property 14 : Writer crée tous les fichiers dans le répertoire de sortie
    @given(
        fichiers=st.dictionaries(
            keys=NOMS_FICHIERS,
            values=CONTENUS,
            min_size=1, max_size=5,
        )
    )
    @settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_writer_cree_tous_fichiers(self, fichiers, tmp_path):
        """Property 14 : write() crée exactement les fichiers du dictionnaire."""
        writer = Writer()
        dossier = tmp_path / "output"
        writer.write(fichiers, str(dossier))

        for chemin_relatif in fichiers:
            assert (dossier / chemin_relatif).exists(), f"Fichier '{chemin_relatif}' manquant"

    @given(
        fichiers=st.dictionaries(
            keys=NOMS_FICHIERS,
            values=CONTENUS,
            min_size=1, max_size=5,
        )
    )
    @settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_writer_contenu_correct(self, fichiers, tmp_path):
        """Property 14b : Le contenu écrit correspond exactement au contenu fourni."""
        # Sur Windows, le système de fichiers est insensible à la casse.
        # On déduplique les clés en gardant la dernière valeur (comportement du Writer).
        fichiers_dedup = {}
        for k, v in fichiers.items():
            fichiers_dedup[k.lower()] = (k, v)
        fichiers_normalises = {k: v for k, (_, v) in fichiers_dedup.items()}

        writer = Writer()
        dossier = tmp_path / "output2"
        # Écrire avec les clés normalisées
        writer.write(fichiers_normalises, str(dossier))

        for chemin_relatif, contenu_attendu in fichiers_normalises.items():
            contenu_lu = (dossier / chemin_relatif).read_text(encoding="utf-8", errors="replace")
            # Normaliser les fins de ligne pour la comparaison cross-platform
            assert contenu_lu.replace("\r\n", "\n").replace("\r", "\n") == contenu_attendu.replace("\r\n", "\n").replace("\r", "\n")

    @given(
        modules=st.lists(
            st.sampled_from(["auth-jwt", "database-sqlite", "docker", "tests-pytest"]),
            min_size=0, max_size=3, unique=True,
        )
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    def test_property_writer_genere_lock_avec_config(self, modules, tmp_path):
        """Property 14c : write() avec config génère toujours gpi.lock."""
        registry = ModuleRegistry()
        config = ProjectConfig(name="testprop", framework="fastapi", modules=modules)
        resolution = Resolver(registry).resolve(config)
        fichiers = Composer(registry).compose(config, resolution)

        writer = Writer()
        dossier = tmp_path / "proj"
        writer.write(fichiers, str(dossier), config, resolution, registry)

        assert (dossier / "gpi.lock").exists()
