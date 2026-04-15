# gpi/modules/database/sqlite.py
"""Module base de données SQLite — développement et tests."""

from gpi.modules.base import Module, ModuleMetadata
from gpi.core.config import ProjectConfig


_DATABASE_PY = '''\
"""Configuration de la base de données SQLite.

Généré par GPI v2
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# URL SQLite depuis les variables d\'environnement
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./{{ project_name }}.db")

# Moteur SQLAlchemy — check_same_thread=False requis pour SQLite avec FastAPI
moteur = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

# Factory de sessions
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

_MODEL_CATALOGUE = '''\
"""Modèle SQLAlchemy pour le domaine Catalogue.

Généré par GPI v2
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, func
from database import Base


class ArticleCatalogue(Base):
    """Modèle pour la table catalogue_articles."""

    __tablename__ = "catalogue_articles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nom = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(String(500), nullable=True)
    prix = Column(Float, nullable=False)
    stock = Column(Integer, nullable=False, default=0)

    # Timestamps automatiques
    cree_le = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    modifie_le = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<ArticleCatalogue(id={self.id}, nom=\'{self.nom}\', prix={self.prix})>"
'''

_SCHEMAS_CATALOGUE = '''\
"""Schémas Pydantic pour le domaine Catalogue.

Séparation claire entre les schémas d\'entrée et de sortie.
Généré par GPI v2
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Generic, TypeVar
from datetime import datetime

T = TypeVar("T")


class ArticleCatalogueBase(BaseModel):
    """Champs communs à la création et à la mise à jour."""
    nom: str = Field(..., min_length=1, max_length=100, description="Nom de l\'article")
    description: Optional[str] = Field(None, max_length=500)
    prix: float = Field(..., gt=0, description="Prix en euros, doit être positif")
    stock: int = Field(0, ge=0, description="Quantité en stock")


class ArticleCatalogueCreer(ArticleCatalogueBase):
    """Schéma pour la création d\'un article (POST)."""
    pass


class ArticleCatalogueRemplacer(ArticleCatalogueBase):
    """Schéma pour le remplacement complet (PUT). Tous les champs sont requis."""
    pass


class ArticleCatalogueModifier(BaseModel):
    """Schéma pour la modification partielle (PATCH). Tous les champs sont optionnels."""
    nom: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    prix: Optional[float] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)


class ArticleCatalogueReponse(ArticleCatalogueBase):
    """Schéma de réponse — inclut les champs générés par la DB."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    cree_le: datetime
    modifie_le: datetime


class ReponsePaginee(BaseModel, Generic[T]):
    """Réponse paginée générique."""
    total: int
    debut: int
    limite: int
    articles: list[T]
'''

_CREATE_PY = '''\
"""Opération CREATE — Catalogue.

Crée un nouvel article dans le catalogue.
HTTP Method : POST
Endpoint    : /catalogue/

Généré par GPI v2
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import obtenir_db
from models.catalogue import ArticleCatalogue
from schemas.catalogue import ArticleCatalogueCreer, ArticleCatalogueReponse

router = APIRouter()


@router.post(
    "/",
    response_model=ArticleCatalogueReponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un article",
    description="Crée un nouvel article dans le catalogue et retourne l\'article créé.",
)
def creer_article(
    article: ArticleCatalogueCreer,
    db: Session = Depends(obtenir_db),
) -> ArticleCatalogueReponse:
    """Crée un article dans le catalogue.

    - **nom** : Nom de l\'article (obligatoire, 1-100 caractères)
    - **description** : Description optionnelle
    - **prix** : Prix en euros (doit être positif)
    - **stock** : Quantité en stock (entier >= 0)
    """
    # Vérification de l\'unicité du nom
    existant = db.query(ArticleCatalogue).filter(
        ArticleCatalogue.nom == article.nom
    ).first()
    if existant:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Un article nommé \'{article.nom}\' existe déjà.",
        )

    db_article = ArticleCatalogue(**article.model_dump())
    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    return db_article
'''

_READ_PY = '''\
"""Opération READ — Catalogue.

Récupère un ou plusieurs articles du catalogue.
HTTP Methods : GET /catalogue/        Tous les articles (avec pagination)
               GET /catalogue/{id}    Un article par ID

Généré par GPI v2
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import obtenir_db
from models.catalogue import ArticleCatalogue
from schemas.catalogue import ArticleCatalogueReponse, ReponsePaginee

router = APIRouter()


@router.get(
    "/",
    response_model=ReponsePaginee[ArticleCatalogueReponse],
    summary="Lister tous les articles",
    description="Retourne la liste paginée des articles du catalogue.",
)
def lister_articles(
    debut: int = Query(0, ge=0, description="Nombre d\'articles à ignorer (pagination)"),
    limite: int = Query(20, ge=1, le=100, description="Nombre max d\'articles retournés"),
    db: Session = Depends(obtenir_db),
) -> ReponsePaginee[ArticleCatalogueReponse]:
    """Liste tous les articles avec pagination offset/limit."""
    total = db.query(ArticleCatalogue).count()
    articles = db.query(ArticleCatalogue).offset(debut).limit(limite).all()
    return ReponsePaginee(total=total, debut=debut, limite=limite, articles=articles)


@router.get(
    "/{article_id}",
    response_model=ArticleCatalogueReponse,
    summary="Récupérer un article",
    description="Retourne un article spécifique par son identifiant.",
    responses={404: {"description": "Article non trouvé"}},
)
def obtenir_article(
    article_id: int,
    db: Session = Depends(obtenir_db),
) -> ArticleCatalogueReponse:
    """Récupère un article par son ID."""
    article = db.query(ArticleCatalogue).filter(ArticleCatalogue.id == article_id).first()
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article avec l\'ID {article_id} introuvable.",
        )
    return article
'''

_UPDATE_PY = '''\
"""Opération UPDATE — Catalogue.

Modifie un article existant du catalogue.
HTTP Methods : PUT   /catalogue/{id}   Remplacement complet
               PATCH /catalogue/{id}   Modification partielle

Généré par GPI v2
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import obtenir_db
from models.catalogue import ArticleCatalogue
from schemas.catalogue import (
    ArticleCatalogueRemplacer,
    ArticleCatalogueModifier,
    ArticleCatalogueReponse,
)

router = APIRouter()


@router.put(
    "/{article_id}",
    response_model=ArticleCatalogueReponse,
    summary="Remplacer un article (remplacement complet)",
)
def remplacer_article(
    article_id: int,
    donnees: ArticleCatalogueRemplacer,
    db: Session = Depends(obtenir_db),
) -> ArticleCatalogueReponse:
    """PUT — Remplacement complet de l\'article. Tous les champs sont mis à jour."""
    db_article = db.query(ArticleCatalogue).filter(ArticleCatalogue.id == article_id).first()
    if not db_article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article avec l\'ID {article_id} introuvable.",
        )
    for champ, valeur in donnees.model_dump().items():
        setattr(db_article, champ, valeur)
    db.commit()
    db.refresh(db_article)
    return db_article


@router.patch(
    "/{article_id}",
    response_model=ArticleCatalogueReponse,
    summary="Modifier partiellement un article",
)
def modifier_article(
    article_id: int,
    donnees: ArticleCatalogueModifier,
    db: Session = Depends(obtenir_db),
) -> ArticleCatalogueReponse:
    """PATCH — Modification partielle. Seuls les champs fournis sont mis à jour."""
    db_article = db.query(ArticleCatalogue).filter(ArticleCatalogue.id == article_id).first()
    if not db_article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article avec l\'ID {article_id} introuvable.",
        )
    # exclude_unset=True ignore les champs non fournis
    for champ, valeur in donnees.model_dump(exclude_unset=True).items():
        setattr(db_article, champ, valeur)
    db.commit()
    db.refresh(db_article)
    return db_article
'''

_DELETE_PY = '''\
"""Opération DELETE — Catalogue.

Supprime un article du catalogue.
HTTP Method : DELETE /catalogue/{id}

Généré par GPI v2
"""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from database import obtenir_db
from models.catalogue import ArticleCatalogue

router = APIRouter()


@router.delete(
    "/{article_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer un article",
    description="Supprime définitivement un article. Retourne HTTP 204 en cas de succès.",
    responses={
        204: {"description": "Article supprimé avec succès"},
        404: {"description": "Article non trouvé"},
    },
)
def supprimer_article(
    article_id: int,
    db: Session = Depends(obtenir_db),
) -> Response:
    """Supprime un article par son ID. Retourne 404 si l\'article n\'existe pas."""
    db_article = db.query(ArticleCatalogue).filter(ArticleCatalogue.id == article_id).first()
    if not db_article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article avec l\'ID {article_id} introuvable.",
        )
    db.delete(db_article)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
'''


class SQLiteModule(Module):
    """Module base de données SQLite avec CRUD atomisé par fichier."""

    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            id="database-sqlite",
            name="SQLite",
            version="1.0.0",
            description="Base de données SQLite pour le développement",
            frameworks=["fastapi", "flask", "django"],
            architectures=["monolithic", "microservices"],
            tags=["database", "sqlite", "sqlalchemy", "orm"],
        )

    def get_dependencies(self) -> list[str]:
        return ["sqlalchemy>=2.0.0", "alembic>=1.13.0"]

    def get_files(self, config: ProjectConfig) -> dict[str, str]:
        """Génère database.py, modèles, schémas et fichiers CRUD atomisés."""
        return {
            "database.py": _DATABASE_PY,
            "models/__init__.py": "",
            "models/catalogue.py": _MODEL_CATALOGUE,
            "schemas/__init__.py": "",
            "schemas/catalogue.py": _SCHEMAS_CATALOGUE,
            "app/__init__.py": "",
            "app/catalogue/__init__.py": "",
            "app/catalogue/create.py": _CREATE_PY,
            "app/catalogue/read.py": _READ_PY,
            "app/catalogue/update.py": _UPDATE_PY,
            "app/catalogue/delete.py": _DELETE_PY,
        }

    def get_env_vars(self) -> dict[str, str]:
        return {"DATABASE_URL": "sqlite:///./app.db"}

    def get_env_example_vars(self) -> dict[str, str]:
        return {"DATABASE_URL": "sqlite:///./app.db"}

    def post_generate_instructions(self) -> list[str]:
        return [
            "Initialisez Alembic : alembic init alembic",
            "Créez la première migration : alembic revision --autogenerate -m 'init'",
            "Appliquez les migrations : alembic upgrade head",
        ]
