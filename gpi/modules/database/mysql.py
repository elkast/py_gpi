# gpi/modules/database/mysql.py
"""Module base de données MySQL/MariaDB."""

from gpi.modules.base import Module, ModuleMetadata
from gpi.core.config import ProjectConfig


class MySQLModule(Module):
    """Module base de données MySQL/MariaDB."""

    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            id="database-mysql",
            name="MySQL",
            version="1.0.0",
            description="Base de données MySQL/MariaDB",
            frameworks=["fastapi", "flask", "django"],
            architectures=["monolithic", "microservices"],
            tags=["database", "mysql", "mariadb", "sqlalchemy"],
        )

    def get_dependencies(self) -> list[str]:
        return [
            "sqlalchemy>=2.0.0",
            "alembic>=1.13.0",
            "pymysql>=1.1.0",
        ]

    def get_files(self, config: ProjectConfig) -> dict[str, str]:
        return {
            "database.py": _DATABASE_PY,
            "models/__init__.py": "",
            "schemas/__init__.py": "",
        }

    def get_env_vars(self) -> dict[str, str]:
        return {"DATABASE_URL": "mysql+pymysql://user:password@localhost:3306/mondb"}

    def get_env_example_vars(self) -> dict[str, str]:
        return {"DATABASE_URL": "mysql+pymysql://user:password@localhost:3306/mondb"}


_DATABASE_PY = '''\
"""Configuration de la base de données MySQL.

Généré par GPI v2
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "mysql+pymysql://user:password@localhost:3306/{{ project_name }}"
)

moteur = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocale = sessionmaker(autocommit=False, autoflush=False, bind=moteur)


class Base(DeclarativeBase):
    """Classe de base pour tous les modèles SQLAlchemy."""
    pass


def obtenir_db():
    """Dépendance FastAPI — fournit une session DB."""
    db = SessionLocale()
    try:
        yield db
    finally:
        db.close()
'''
