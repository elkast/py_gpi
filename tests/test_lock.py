# tests/test_lock.py
"""Tests unitaires pour LockFile."""

import json
import pytest
from pathlib import Path

from gpi.core.config import ProjectConfig
from gpi.core.resolver import ResolutionResult
from gpi.core.lock import LockFile


@pytest.fixture
def config_simple():
    return ProjectConfig(name="testapi", framework="fastapi", modules=["auth-jwt"])


@pytest.fixture
def resolution_simple():
    return ResolutionResult(
        modules=["framework-fastapi", "auth-jwt"],
        auto_added=[],
        warnings=[],
    )


class TestLockFile:
    """Tests du gestionnaire de fichier gpi.lock."""

    def test_create_contient_champs_requis(self, config_simple, resolution_simple):
        """Le lock créé doit contenir tous les champs requis."""
        donnees = LockFile.create(config_simple, resolution_simple, ["fastapi>=0.109.0"])
        assert "gpi_version" in donnees
        assert "generated_at" in donnees
        assert "config" in donnees
        assert "resolved_modules" in donnees
        assert "python_dependencies" in donnees
        assert "checksum" in donnees

    def test_create_checksum_sha256(self, config_simple, resolution_simple):
        """Le checksum doit commencer par 'sha256:'."""
        donnees = LockFile.create(config_simple, resolution_simple, [])
        assert donnees["checksum"].startswith("sha256:")

    def test_write_et_read_roundtrip(self, config_simple, resolution_simple, tmp_path):
        """Écriture puis lecture doit retourner les mêmes données."""
        donnees = LockFile.create(config_simple, resolution_simple, ["fastapi>=0.109.0"])
        LockFile.write(donnees, str(tmp_path))

        chemin_lock = tmp_path / "gpi.lock"
        assert chemin_lock.exists()

        donnees_lues = LockFile.read(str(chemin_lock))
        assert donnees_lues["config"]["name"] == "testapi"
        assert donnees_lues["config"]["framework"] == "fastapi"

    def test_read_checksum_invalide_leve_erreur(self, tmp_path):
        """Un lock modifié manuellement doit lever ValueError."""
        # Créer un lock valide
        config = ProjectConfig(name="test", framework="fastapi", modules=[])
        resolution = ResolutionResult(modules=["framework-fastapi"], auto_added=[], warnings=[])
        donnees = LockFile.create(config, resolution, [])
        LockFile.write(donnees, str(tmp_path))

        # Modifier le fichier manuellement
        chemin_lock = tmp_path / "gpi.lock"
        contenu = json.loads(chemin_lock.read_text())
        contenu["config"]["name"] = "modifie"
        chemin_lock.write_text(json.dumps(contenu))

        with pytest.raises(ValueError, match="corrompu"):
            LockFile.read(str(chemin_lock))

    def test_to_config_reconstruit_config(self, config_simple, resolution_simple, tmp_path):
        """to_config doit reconstruire une config équivalente à l'originale."""
        donnees = LockFile.create(config_simple, resolution_simple, [])
        LockFile.write(donnees, str(tmp_path))

        donnees_lues = LockFile.read(str(tmp_path / "gpi.lock"))
        config_reconstruite = LockFile.to_config(donnees_lues)

        assert config_reconstruite.name == config_simple.name
        assert config_reconstruite.framework == config_simple.framework
        assert config_reconstruite.modules == config_simple.modules

    def test_dependencies_triees(self, config_simple, resolution_simple):
        """Les dépendances doivent être triées dans le lock."""
        deps = ["zlib>=1.0", "aiohttp>=3.0", "fastapi>=0.109.0"]
        donnees = LockFile.create(config_simple, resolution_simple, deps)
        assert donnees["python_dependencies"] == sorted(deps)


# ============================================================
# Tests de propriété (Property-Based Testing) avec Hypothesis
# ============================================================

from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis import HealthCheck
from gpi.core.config import ProjectConfig
from gpi.core.resolver import ResolutionResult
import tempfile
import os


FRAMEWORKS = st.sampled_from(["fastapi", "flask", "django"])
VALID_NAMES = st.from_regex(r"^[a-zA-Z][a-zA-Z0-9_]{1,20}$", fullmatch=True)
VALID_PORTS = st.integers(min_value=1024, max_value=65535)


class TestLockFileProperties:
    """Tests de propriété pour LockFile."""

    # Property 15 : Round-trip LockFile — create → to_config
    @given(
        name=VALID_NAMES,
        framework=FRAMEWORKS,
        port=VALID_PORTS,
    )
    @settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_roundtrip_create_to_config(self, name, framework, port, tmp_path):
        """Property 15 : create() → write() → read() → to_config() == config originale."""
        config_originale = ProjectConfig(name=name, framework=framework, port=port)
        resolution = ResolutionResult(
            modules=[f"framework-{framework}"],
            auto_added=[],
            warnings=[],
        )

        donnees = LockFile.create(config_originale, resolution, [])
        LockFile.write(donnees, str(tmp_path))

        donnees_lues = LockFile.read(str(tmp_path / "gpi.lock"))
        config_reconstruite = LockFile.to_config(donnees_lues)

        assert config_reconstruite.name == config_originale.name
        assert config_reconstruite.framework == config_originale.framework
        assert config_reconstruite.port == config_originale.port

    # Property 16 : Checksum invalide → ValueError
    @given(
        name=VALID_NAMES,
        framework=FRAMEWORKS,
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_checksum_invalide_leve_erreur(self, name, framework, tmp_path):
        """Property 16 : Toute modification du lock invalide le checksum."""
        import json

        config = ProjectConfig(name=name, framework=framework)
        resolution = ResolutionResult(
            modules=[f"framework-{framework}"],
            auto_added=[],
            warnings=[],
        )
        donnees = LockFile.create(config, resolution, [])
        LockFile.write(donnees, str(tmp_path))

        # Modifier le fichier pour invalider le checksum
        chemin_lock = tmp_path / "gpi.lock"
        contenu = json.loads(chemin_lock.read_text())
        contenu["gpi_version"] = "0.0.0-tampered"
        chemin_lock.write_text(json.dumps(contenu))

        with pytest.raises(ValueError):
            LockFile.read(str(chemin_lock))

    @given(
        deps=st.lists(
            st.from_regex(r"[a-z][a-z0-9-]{2,10}>=[0-9]\.[0-9]\.[0-9]", fullmatch=True),
            min_size=0, max_size=5,
        )
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_property_dependances_toujours_triees(self, deps):
        """Property : Les dépendances dans le lock sont toujours triées."""
        config = ProjectConfig(name="testprop", framework="fastapi")
        resolution = ResolutionResult(modules=["framework-fastapi"], auto_added=[], warnings=[])
        donnees = LockFile.create(config, resolution, deps)
        assert donnees["python_dependencies"] == sorted(deps)
