# gpi/modules/testing/pytest.py
"""Module tests Pytest — génère la configuration et les fixtures de base."""

from gpi.modules.base import Module, ModuleMetadata
from gpi.core.config import ProjectConfig


_CONFTEST_PY = '''\
"""Fixtures pytest partagées pour {{ project_name }}.

Généré par GPI v2
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def client():
    """Client de test FastAPI — réutilisé pour toute la session de tests."""
    from main import app
    with TestClient(app) as c:
        yield c
'''

_TEST_INIT = ""

_TEST_SANTE = '''\
"""Tests de santé de l\'API {{ project_name }}.

Généré par GPI v2
"""


def test_racine(client):
    """L\'endpoint racine doit retourner HTTP 200."""
    reponse = client.get("/")
    assert reponse.status_code == 200
    assert reponse.json()["statut"] == "ok"
'''


class PytestModule(Module):
    """Module tests Pytest avec fixtures de base."""

    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            id="tests-pytest",
            name="Pytest",
            version="1.0.0",
            description="Tests automatisés avec Pytest",
            frameworks=["fastapi", "flask", "django"],
            architectures=["monolithic", "microservices"],
            tags=["tests", "pytest", "testing", "coverage"],
        )

    def get_dependencies(self) -> list[str]:
        return [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "httpx>=0.26.0",
        ]

    def get_files(self, config: ProjectConfig) -> dict[str, str]:
        return {
            "tests/__init__.py": _TEST_INIT,
            "tests/conftest.py": _CONFTEST_PY,
            "tests/test_sante.py": _TEST_SANTE,
        }

    def post_generate_instructions(self) -> list[str]:
        return ["Lancez les tests : pytest tests/ -v --cov=."]
