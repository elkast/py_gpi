# tests/test_config.py
"""Tests unitaires pour ProjectConfig (Pydantic v2)."""

import pytest
from pydantic import ValidationError as PydanticValidationError

from gpi.core.config import ProjectConfig


class TestProjectConfigValidation:
    """Tests de validation des champs de ProjectConfig."""

    def test_framework_valide(self):
        """Les frameworks valides doivent être acceptés."""
        for fw in ["fastapi", "flask", "django"]:
            config = ProjectConfig(name="test", framework=fw)
            assert config.framework == fw

    def test_framework_invalide(self):
        """Un framework invalide doit lever ValueError."""
        with pytest.raises(PydanticValidationError):
            ProjectConfig(name="test", framework="rails")

    def test_nom_valide(self):
        """Les noms valides doivent être acceptés."""
        for nom in ["monapi", "MonApi2", "mon_api", "ab"]:
            config = ProjectConfig(name=nom, framework="fastapi")
            assert config.name == nom

    def test_nom_invalide_commence_par_chiffre(self):
        """Un nom commençant par un chiffre doit être rejeté."""
        with pytest.raises(PydanticValidationError):
            ProjectConfig(name="1api", framework="fastapi")

    def test_nom_invalide_trop_court(self):
        """Un nom d'un seul caractère doit être rejeté."""
        with pytest.raises(PydanticValidationError):
            ProjectConfig(name="a", framework="fastapi")

    def test_nom_invalide_avec_tiret(self):
        """Un nom avec tiret doit être rejeté."""
        with pytest.raises(PydanticValidationError):
            ProjectConfig(name="mon-api", framework="fastapi")

    def test_port_valide(self):
        """Les ports dans la plage [1024, 65535] doivent être acceptés."""
        config = ProjectConfig(name="test", framework="fastapi", port=3000)
        assert config.port == 3000

    def test_port_invalide_trop_bas(self):
        """Un port < 1024 doit être rejeté."""
        with pytest.raises(PydanticValidationError):
            ProjectConfig(name="test", framework="fastapi", port=80)

    def test_port_invalide_trop_haut(self):
        """Un port > 65535 doit être rejeté."""
        with pytest.raises(PydanticValidationError):
            ProjectConfig(name="test", framework="fastapi", port=99999)

    def test_language_invalide(self):
        """Une langue invalide (bilingue supprimé) doit être rejetée."""
        with pytest.raises(PydanticValidationError):
            ProjectConfig(name="test", framework="fastapi", language="bilingue")

    def test_architecture_invalide(self):
        """Une architecture invalide doit être rejetée."""
        with pytest.raises(PydanticValidationError):
            ProjectConfig(name="test", framework="fastapi", architecture="serverless")

    def test_services_par_defaut_microservices(self):
        """Les services par défaut doivent être injectés en microservices."""
        config = ProjectConfig(
            name="test",
            framework="fastapi",
            architecture="microservices",
            modules=["auth-jwt", "database-postgres"],
        )
        assert len(config.services) > 0
        assert "auth" in config.services

    def test_services_non_injectes_si_fournis(self):
        """Les services fournis ne doivent pas être remplacés."""
        config = ProjectConfig(
            name="test",
            framework="fastapi",
            architecture="microservices",
            modules=["auth-jwt", "database-postgres"],
            services=["api", "worker"],
        )
        assert config.services == ["api", "worker"]


class TestProjectConfigYaml:
    """Tests de chargement depuis YAML."""

    def test_from_yaml(self, tmp_path):
        """Chargement depuis un fichier YAML valide."""
        yaml_content = """
name: monapi
framework: fastapi
architecture: monolithic
modules:
  - auth-jwt
language: fr
port: 8000
"""
        yaml_file = tmp_path / "gpi.yaml"
        yaml_file.write_text(yaml_content)

        config = ProjectConfig.from_yaml(str(yaml_file))
        assert config.name == "monapi"
        assert config.framework == "fastapi"
        assert "auth-jwt" in config.modules


# ============================================================
# Tests de propriété (Property-Based Testing) avec Hypothesis
# ============================================================

from hypothesis import given, settings, assume, HealthCheck
from hypothesis import strategies as st
import re
import yaml


# Stratégies réutilisables
FRAMEWORKS = st.sampled_from(["fastapi", "flask", "django"])
ARCHITECTURES = st.sampled_from(["monolithic", "microservices"])
VALID_NAMES = st.from_regex(r"^[a-zA-Z][a-zA-Z0-9_]{1,48}$", fullmatch=True)
INVALID_FRAMEWORKS = st.text(min_size=1).filter(lambda x: x not in ["fastapi", "flask", "django"])
INVALID_PORTS = st.one_of(st.integers(max_value=1023), st.integers(min_value=65536))
VALID_PORTS = st.integers(min_value=1024, max_value=65535)


class TestProjectConfigProperties:
    """Tests de propriété pour ProjectConfig."""

    # Property 1 : Validation du framework — rejet des valeurs invalides
    @given(framework=INVALID_FRAMEWORKS)
    @settings(max_examples=50)
    def test_property_framework_invalide_rejete(self, framework):
        """Property 1 : Tout framework non supporté doit lever ValidationError."""
        with pytest.raises(PydanticValidationError):
            ProjectConfig(name="testprop", framework=framework)

    # Property 2 : Validation du nom de projet — contrat regex
    @given(name=VALID_NAMES, framework=FRAMEWORKS)
    @settings(max_examples=50)
    def test_property_nom_valide_accepte(self, name, framework):
        """Property 2 : Tout nom correspondant au regex doit être accepté."""
        config = ProjectConfig(name=name, framework=framework)
        assert config.name == name

    # Property 3 : Validation du port — plage autorisée
    @given(port=VALID_PORTS, framework=FRAMEWORKS)
    @settings(max_examples=50)
    def test_property_port_valide_accepte(self, port, framework):
        """Property 3 : Tout port dans [1024, 65535] doit être accepté."""
        config = ProjectConfig(name="testprop", framework=framework, port=port)
        assert config.port == port

    @given(port=INVALID_PORTS, framework=FRAMEWORKS)
    @settings(max_examples=50)
    def test_property_port_invalide_rejete(self, port, framework):
        """Property 3b : Tout port hors [1024, 65535] doit être rejeté."""
        with pytest.raises(PydanticValidationError):
            ProjectConfig(name="testprop", framework=framework, port=port)

    # Property 4 : Services par défaut en microservices
    @given(framework=st.sampled_from(["fastapi", "flask"]))
    @settings(max_examples=20)
    def test_property_services_defaut_microservices(self, framework):
        """Property 4 : Microservices sans services → services par défaut injectés."""
        config = ProjectConfig(
            name="testprop",
            framework=framework,
            architecture="microservices",
            modules=["auth-jwt", "database-postgres"],
            services=[],
        )
        assert len(config.services) > 0

    # Property 5 : Round-trip YAML — ProjectConfig
    @given(
        name=VALID_NAMES,
        framework=FRAMEWORKS,
        port=VALID_PORTS,
    )
    @settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_roundtrip_yaml(self, name, framework, port, tmp_path):
        """Property 5 : Round-trip YAML — from_yaml(to_yaml(config)) == config."""
        import tempfile, os
        # Créer la config originale
        config_originale = ProjectConfig(name=name, framework=framework, port=port)

        # Sérialiser en YAML dans un fichier temporaire
        donnees = config_originale.model_dump()
        yaml_content = yaml.dump(donnees, allow_unicode=True)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8") as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            config_rechargee = ProjectConfig.from_yaml(yaml_path)
        finally:
            os.unlink(yaml_path)

        # Vérifier l'équivalence
        assert config_rechargee.name == config_originale.name
        assert config_rechargee.framework == config_originale.framework
        assert config_rechargee.port == config_originale.port
        assert config_rechargee.architecture == config_originale.architecture
