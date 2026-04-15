# gpi/modules/database/postgres.py
"""Module base de données PostgreSQL — production-ready."""

from gpi.modules.base import Module, ModuleMetadata
from gpi.core.config import ProjectConfig


_DATABASE_PY = '''\
"""Configuration de la base de données PostgreSQL.

Généré par GPI v2
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://user:password@localhost:5432/{{ project_name }}"
)

moteur = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,   # Vérification de la connexion avant usage
    pool_size=10,         # Taille du pool de connexions
    max_overflow=20,      # Connexions additionnelles autorisées
)

SessionLocale = sessionmaker(autocommit=False, autoflush=False, bind=moteur)


class Base(DeclarativeBase):
    """Classe de base pour tous les modèles SQLAlchemy."""
    pass


def obtenir_db():
    """Dépendance FastAPI — fournit une session DB et la ferme après la requête."""
    db = SessionLocale()
    try:
        yield db
    finally:
        db.close()
'''


class PostgresModule(Module):
    """Module base de données PostgreSQL production-ready."""

    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            id="database-postgres",
            name="PostgreSQL",
            version="1.0.0",
            description="Base de données PostgreSQL production-ready",
            frameworks=["fastapi", "flask", "django"],
            architectures=["monolithic", "microservices"],
            tags=["database", "postgres", "postgresql", "sqlalchemy"],
        )

    def get_dependencies(self) -> list[str]:
        return [
            "sqlalchemy>=2.0.0",
            "alembic>=1.13.0",
            "psycopg2-binary>=2.9.0",
        ]

    def get_files(self, config: ProjectConfig) -> dict[str, str]:
        return {
            "database.py": _DATABASE_PY,
            "models/__init__.py": "",
            "schemas/__init__.py": "",
            "app/__init__.py": "",
            "app/catalogue/__init__.py": "",
        }

    def get_env_vars(self) -> dict[str, str]:
        return {"DATABASE_URL": "postgresql://user:password@localhost:5432/mondb"}

    def get_env_example_vars(self) -> dict[str, str]:
        return {"DATABASE_URL": "postgresql://user:password@localhost:5432/mondb"}

    def post_generate_instructions(self) -> list[str]:
        return [
            "Démarrez PostgreSQL (ou utilisez Docker)",
            "Créez la base : createdb nom_de_votre_projet",
            "Initialisez Alembic : alembic init alembic",
            "Appliquez les migrations : alembic upgrade head",
        ]
