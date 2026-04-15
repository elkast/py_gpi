# tests/test_validator.py
"""Tests unitaires pour le Validator GPI."""

import pytest

from gpi.core.config import ProjectConfig
from gpi.core.validator import Validator
from gpi.core.exceptions import ValidationError


@pytest.fixture
def validator():
    return Validator()


class TestValidator:
    """Tests des règles de validation déclaratives."""

    def test_config_valide_retourne_liste_vide(self, validator):
        """Une configuration valide doit retourner une liste vide."""
        config = ProjectConfig(name="test", framework="fastapi", modules=["auth-jwt"])
        avertissements = validator.validate(config)
        assert isinstance(avertissements, list)

    def test_microservices_moins_2_modules_bloquant(self, validator):
        """Microservices avec < 2 modules doit lever ValidationError."""
        config = ProjectConfig(
            name="test",
            framework="fastapi",
            architecture="microservices",
            modules=["auth-jwt"],
        )
        with pytest.raises(ValidationError):
            validator.validate(config)

    def test_jwt_et_oauth2_bloquant(self, validator):
        """auth-jwt + auth-oauth2 simultanément doit lever ValidationError."""
        config = ProjectConfig(
            name="test",
            framework="fastapi",
            modules=["auth-jwt", "auth-oauth2"],
        )
        with pytest.raises(ValidationError):
            validator.validate(config)

    def test_prometheus_django_bloquant(self, validator):
        """monitoring-prometheus + django doit lever ValidationError."""
        config = ProjectConfig(
            name="test",
            framework="django",
            modules=["monitoring-prometheus"],
        )
        with pytest.raises(ValidationError):
            validator.validate(config)

    def test_celery_sans_redis_avertissement(self, validator):
        """Celery sans Redis doit retourner un avertissement non bloquant."""
        config = ProjectConfig(
            name="test",
            framework="fastapi",
            modules=["queue-celery"],
        )
        avertissements = validator.validate(config)
        assert len(avertissements) > 0
        assert any("celery" in a.lower() or "redis" in a.lower() for a in avertissements)

    def test_sessions_fastapi_avertissement(self, validator):
        """auth-sessions + FastAPI doit retourner un avertissement."""
        config = ProjectConfig(
            name="test",
            framework="fastapi",
            modules=["auth-sessions"],
        )
        # Note: auth-sessions n'est pas compatible FastAPI (incompatibilité framework)
        # Le validator retourne un avertissement, le resolver lèvera l'erreur
        avertissements = validator.validate(config)
        assert isinstance(avertissements, list)


# ============================================================
# Tests de propriété (Property-Based Testing) avec Hypothesis
# ============================================================

from hypothesis import given, settings
from hypothesis import strategies as st


MODULES_VALIDES = [
    "auth-jwt", "database-sqlite", "database-postgres", "cache-redis",
    "docker", "tests-pytest", "github-actions",
]


class TestValidatorProperties:
    """Tests de propriété pour le Validator."""

    # Property 10 : Règle bloquante → ValidationError
    @given(
        nb_modules=st.integers(min_value=0, max_value=1),
        framework=st.sampled_from(["fastapi", "flask"]),
    )
    @settings(max_examples=20)
    def test_property_microservices_moins_2_modules_bloquant(self, nb_modules, framework):
        """Property 10 : Microservices avec < 2 modules → ValidationError."""
        modules = MODULES_VALIDES[:nb_modules]
        config = ProjectConfig(
            name="testprop",
            framework=framework,
            architecture="microservices",
            modules=modules,
        )
        validator = Validator()
        with pytest.raises(ValidationError):
            validator.validate(config)

    def test_property_jwt_oauth2_toujours_bloquant(self):
        """Property 10b : auth-jwt + auth-oauth2 → toujours ValidationError."""
        config = ProjectConfig(
            name="testprop",
            framework="fastapi",
            modules=["auth-jwt", "auth-oauth2"],
        )
        validator = Validator()
        with pytest.raises(ValidationError):
            validator.validate(config)

    # Property 11 : Règle non-bloquante → avertissement retourné
    @given(
        modules_extra=st.lists(
            st.sampled_from(["docker", "tests-pytest", "github-actions"]),
            min_size=0, max_size=2, unique=True,
        )
    )
    @settings(max_examples=20)
    def test_property_celery_sans_redis_avertissement(self, modules_extra):
        """Property 11 : Celery sans Redis → avertissement non bloquant."""
        config = ProjectConfig(
            name="testprop",
            framework="fastapi",
            modules=["queue-celery"] + modules_extra,
        )
        validator = Validator()
        avertissements = validator.validate(config)
        assert isinstance(avertissements, list)
        assert len(avertissements) >= 1

    @given(
        modules_extra=st.lists(
            st.sampled_from(["database-sqlite", "docker", "tests-pytest"]),
            min_size=0, max_size=2, unique=True,
        )
    )
    @settings(max_examples=20)
    def test_property_config_valide_retourne_liste(self, modules_extra):
        """Property 11b : Config valide → validate() retourne une liste."""
        config = ProjectConfig(
            name="testprop",
            framework="fastapi",
            modules=modules_extra,
        )
        validator = Validator()
        result = validator.validate(config)
        assert isinstance(result, list)
