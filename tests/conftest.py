# tests/conftest.py
"""Fixtures pytest partagées pour les tests GPI v2."""

import pytest
import tempfile
from pathlib import Path

from gpi.core.config import ProjectConfig
from gpi.modules.registry import ModuleRegistry
from gpi.core.resolver import Resolver
from gpi.core.composer import Composer
from gpi.core.writer import Writer


@pytest.fixture
def registry():
    """Registre de modules GPI."""
    return ModuleRegistry()


@pytest.fixture
def resolver(registry):
    """Resolver GPI avec le registre natif."""
    return Resolver(registry)


@pytest.fixture
def composer(registry):
    """Composer GPI avec le registre natif."""
    return Composer(registry)


@pytest.fixture
def config_fastapi_minimal():
    """Configuration FastAPI minimale sans modules."""
    return ProjectConfig(name="testapi", framework="fastapi", modules=[])


@pytest.fixture
def temp_dir():
    """Dossier temporaire pour les tests d'écriture."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir
