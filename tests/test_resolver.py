# tests/test_resolver.py
"""Tests unitaires pour le Resolver GPI."""

import pytest

from gpi.core.config import ProjectConfig
from gpi.core.resolver import Resolver
from gpi.modules.registry import ModuleRegistry
from gpi.core.exceptions import (
    ModuleNotFoundError,
    ModuleConflictError,
    ModuleIncompatibleError,
)


@pytest.fixture
def resolver():
    return Resolver(ModuleRegistry())


class TestResolver:
    """Tests du moteur de résolution des dépendances."""

    def test_framework_toujours_en_premier(self, resolver):
        """Le framework doit toujours être le premier module résolu."""
        config = ProjectConfig(name="test", framework="fastapi", modules=["auth-jwt"])
        result = resolver.resolve(config)
        assert result.modules[0] == "framework-fastapi"

    def test_resolution_simple(self, resolver):
        """Résolution basique : framework + un module."""
        config = ProjectConfig(name="test", framework="fastapi", modules=["auth-jwt"])
        result = resolver.resolve(config)
        assert "framework-fastapi" in result.modules
        assert "auth-jwt" in result.modules

    def test_resolution_sans_modules(self, resolver):
        """Résolution sans modules — uniquement le framework."""
        config = ProjectConfig(name="test", framework="fastapi", modules=[])
        result = resolver.resolve(config)
        assert result.modules == ["framework-fastapi"]
        assert result.auto_added == []

    def test_auto_ajout_dependances(self, resolver):
        """Celery doit ajouter cache-redis automatiquement."""
        config = ProjectConfig(name="test", framework="fastapi", modules=["queue-celery"])
        result = resolver.resolve(config)
        assert "cache-redis" in result.modules
        assert "cache-redis" in result.auto_added
        assert len(result.warnings) > 0

    def test_module_inconnu_leve_erreur(self, resolver):
        """Un module inexistant doit lever ModuleNotFoundError."""
        config = ProjectConfig(name="test", framework="fastapi", modules=["module-inexistant"])
        with pytest.raises(ModuleNotFoundError):
            resolver.resolve(config)

    def test_conflit_jwt_oauth2(self, resolver):
        """auth-jwt + auth-oauth2 doivent lever ModuleConflictError."""
        config = ProjectConfig(
            name="test",
            framework="fastapi",
            modules=["auth-jwt", "auth-oauth2"],
        )
        with pytest.raises(ModuleConflictError):
            resolver.resolve(config)

    def test_incompatibilite_framework(self, resolver):
        """auth-sessions ne supporte pas FastAPI."""
        config = ProjectConfig(
            name="test",
            framework="fastapi",
            modules=["auth-sessions"],
        )
        with pytest.raises(ModuleIncompatibleError):
            resolver.resolve(config)

    def test_flask_resolution(self, resolver):
        """Résolution avec Flask."""
        config = ProjectConfig(name="test", framework="flask", modules=["auth-sessions"])
        result = resolver.resolve(config)
        assert "framework-flask" in result.modules
        assert "auth-sessions" in result.modules

    def test_django_resolution(self, resolver):
        """Résolution avec Django."""
        config = ProjectConfig(name="test", framework="django", modules=[])
        result = resolver.resolve(config)
        assert result.modules[0] == "framework-django"


# ============================================================
# Tests de propriété (Property-Based Testing) avec Hypothesis
# ============================================================

from hypothesis import given, settings, assume
from hypothesis import strategies as st
from hypothesis import HealthCheck


# Modules compatibles FastAPI (sans conflits entre eux)
MODULES_FASTAPI_COMPATIBLES = [
    "auth-jwt", "database-sqlite", "database-postgres", "database-mysql",
    "cache-redis", "docker", "docker-compose", "tests-pytest", "github-actions",
]

MODULES_FLASK_COMPATIBLES = [
    "auth-jwt", "auth-sessions", "database-sqlite", "database-postgres",
    "cache-redis", "docker", "tests-pytest",
]


class TestResolverProperties:
    """Tests de propriété pour le Resolver."""

    # Property 6 : Framework toujours en premier dans la résolution
    @given(
        framework=st.sampled_from(["fastapi", "flask"]),
        modules=st.lists(
            st.sampled_from(MODULES_FASTAPI_COMPATIBLES),
            min_size=0, max_size=3, unique=True,
        ),
    )
    @settings(max_examples=40)
    def test_property_framework_toujours_premier(self, framework, modules):
        """Property 6 : Le framework est toujours le premier module résolu."""
        # Filtrer les modules incompatibles avec flask
        if framework == "flask":
            modules = [m for m in modules if m in MODULES_FLASK_COMPATIBLES]

        config = ProjectConfig(name="testprop", framework=framework, modules=modules)
        resolver = Resolver(ModuleRegistry())
        result = resolver.resolve(config)
        assert result.modules[0] == f"framework-{framework}"

    # Property 7 : Dépendances automatiquement ajoutées
    @given(framework=st.sampled_from(["fastapi", "flask"]))
    @settings(max_examples=20)
    def test_property_celery_auto_ajoute_redis(self, framework):
        """Property 7 : queue-celery doit toujours auto-ajouter cache-redis."""
        config = ProjectConfig(
            name="testprop",
            framework=framework,
            modules=["queue-celery"],
        )
        resolver = Resolver(ModuleRegistry())
        result = resolver.resolve(config)
        assert "cache-redis" in result.modules
        assert "cache-redis" in result.auto_added

    # Property 8 : Module inconnu → ModuleNotFoundError
    def test_property_module_inconnu_leve_erreur_fixe(self):
        """Property 8 : Des modules inconnus connus doivent lever ModuleNotFoundError."""
        modules_inconnus = ["module-xyz", "fake-auth", "nonexistent-db", "unknown-cache"]
        resolver = Resolver(ModuleRegistry())
        for module_id in modules_inconnus:
            config = ProjectConfig(name="testprop", framework="fastapi", modules=[module_id])
            with pytest.raises(ModuleNotFoundError):
                resolver.resolve(config)

    # Property 9 : Modules en conflit → ModuleConflictError
    def test_property_conflits_jwt_oauth2(self):
        """Property 9 : auth-jwt + auth-oauth2 → ModuleConflictError."""
        config = ProjectConfig(
            name="testprop",
            framework="fastapi",
            modules=["auth-jwt", "auth-oauth2"],
        )
        resolver = Resolver(ModuleRegistry())
        with pytest.raises(ModuleConflictError):
            resolver.resolve(config)

    @given(
        modules=st.lists(
            st.sampled_from(MODULES_FASTAPI_COMPATIBLES),
            min_size=0, max_size=4, unique=True,
        )
    )
    @settings(max_examples=30)
    def test_property_resolution_sans_doublons(self, modules):
        """Property : La liste résolue ne contient pas de doublons."""
        config = ProjectConfig(name="testprop", framework="fastapi", modules=modules)
        resolver = Resolver(ModuleRegistry())
        result = resolver.resolve(config)
        assert len(result.modules) == len(set(result.modules))
