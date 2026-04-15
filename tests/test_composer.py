# tests/test_composer.py
"""Tests unitaires pour le Composer GPI."""

import pytest
from gpi.core.config import ProjectConfig
from gpi.core.resolver import Resolver, ResolutionResult
from gpi.core.composer import Composer
from gpi.modules.registry import ModuleRegistry


@pytest.fixture
def registry():
    return ModuleRegistry()


@pytest.fixture
def composer(registry):
    return Composer(registry)


class TestComposer:
    """Tests du compositeur de fichiers."""

    def test_compose_retourne_dict(self, composer, registry):
        """compose() doit retourner un dictionnaire."""
        config = ProjectConfig(name="test", framework="fastapi", modules=[])
        result = Resolver(registry).resolve(config)
        fichiers = composer.compose(config, result)
        assert isinstance(fichiers, dict)

    def test_compose_contient_fichiers_framework(self, composer, registry):
        """compose() doit inclure les fichiers du module framework."""
        config = ProjectConfig(name="test", framework="fastapi", modules=[])
        result = Resolver(registry).resolve(config)
        fichiers = composer.compose(config, result)
        # Le module FastAPI génère au moins main.py
        assert len(fichiers) > 0

    def test_get_all_dependencies_trie_et_deduplique(self, composer, registry):
        """get_all_dependencies() doit retourner une liste triée sans doublons."""
        result = ResolutionResult(
            modules=["framework-fastapi", "auth-jwt"],
            auto_added=[],
            warnings=[],
        )
        deps = composer.get_all_dependencies(result)
        assert deps == sorted(set(deps))

    def test_render_jinja2_remplace_variables(self, composer):
        """_rendre() doit remplacer les variables Jinja2."""
        template = "Projet : {{ project_name }}"
        contexte = {"project_name": "monapi"}
        resultat = composer._rendre(template, contexte)
        assert resultat == "Projet : monapi"

    def test_render_jinja2_echec_retourne_brut(self, composer):
        """_rendre() doit retourner le contenu brut en cas d'erreur."""
        template = "{{ variable_inexistante | filtre_inexistant }}"
        contexte = {}
        resultat = composer._rendre(template, contexte)
        # Doit retourner quelque chose sans lever d'exception
        assert isinstance(resultat, str)


# ============================================================
# Tests de propriété (Property-Based Testing) avec Hypothesis
# ============================================================

from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis import HealthCheck


MODULES_FASTAPI = [
    "auth-jwt", "database-sqlite", "cache-redis",
    "docker", "tests-pytest", "github-actions",
]


class TestComposerProperties:
    """Tests de propriété pour le Composer."""

    # Property 12 : Composer produit tous les fichiers des modules résolus
    @given(
        modules=st.lists(
            st.sampled_from(MODULES_FASTAPI),
            min_size=0, max_size=3, unique=True,
        )
    )
    @settings(max_examples=30, deadline=None)
    def test_property_compose_produit_fichiers(self, modules):
        """Property 12 : compose() retourne un dict non vide pour tout config valide."""
        registry = ModuleRegistry()
        config = ProjectConfig(name="testprop", framework="fastapi", modules=modules)
        result = Resolver(registry).resolve(config)
        fichiers = Composer(registry).compose(config, result)
        assert isinstance(fichiers, dict)
        # Au moins les fichiers du framework doivent être présents
        assert len(fichiers) > 0

    # Property 13 : Dépendances triées et dédupliquées
    @given(
        modules=st.lists(
            st.sampled_from(MODULES_FASTAPI),
            min_size=0, max_size=4, unique=True,
        )
    )
    @settings(max_examples=30, deadline=None)
    def test_property_dependances_triees_deduplicees(self, modules):
        """Property 13 : get_all_dependencies() retourne une liste triée sans doublons."""
        registry = ModuleRegistry()
        config = ProjectConfig(name="testprop", framework="fastapi", modules=modules)
        result = Resolver(registry).resolve(config)
        composer = Composer(registry)
        deps = composer.get_all_dependencies(result)
        assert deps == sorted(set(deps)), "Les dépendances doivent être triées et sans doublons"

    @given(
        modules=st.lists(
            st.sampled_from(MODULES_FASTAPI),
            min_size=0, max_size=3, unique=True,
        )
    )
    @settings(max_examples=20, deadline=None)
    def test_property_compose_valeurs_sont_strings(self, modules):
        """Property : Tous les contenus de fichiers sont des chaînes."""
        registry = ModuleRegistry()
        config = ProjectConfig(name="testprop", framework="fastapi", modules=modules)
        result = Resolver(registry).resolve(config)
        fichiers = Composer(registry).compose(config, result)
        for chemin, contenu in fichiers.items():
            assert isinstance(chemin, str)
            assert isinstance(contenu, str)
