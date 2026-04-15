# gpi/modules/infra/github_actions.py
"""Module GitHub Actions — CI/CD automatisé."""

from gpi.modules.base import Module, ModuleMetadata
from gpi.core.config import ProjectConfig


_CI_YML = '''\
# .github/workflows/ci.yml
# Pipeline CI/CD pour {{ project_name }}
# Généré par GPI v2

name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  tests:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.9", "3.10", "3.11", "3.12"]

    steps:
      - uses: actions/checkout@v4

      - name: Configurer Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Installer les dépendances
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Lancer les tests
        run: pytest tests/ -v --cov={{ project_name }} --cov-report=xml

      - name: Envoyer la couverture
        uses: codecov/codecov-action@v4
        with:
          token: ${{ secrets.CODECOV_TOKEN }}
          fail_ci_if_error: false
'''


class GitHubActionsModule(Module):
    """Module GitHub Actions — pipeline CI/CD."""

    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            id="github-actions",
            name="GitHub Actions",
            version="1.0.0",
            description="Pipeline CI/CD GitHub Actions",
            frameworks=["fastapi", "flask", "django"],
            architectures=["monolithic", "microservices"],
            tags=["ci", "cd", "github", "actions", "devops"],
        )

    def get_dependencies(self) -> list[str]:
        return []

    def get_files(self, config: ProjectConfig) -> dict[str, str]:
        return {".github/workflows/ci.yml": _CI_YML}
