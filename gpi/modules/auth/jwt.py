# gpi/modules/auth/jwt.py
"""Module authentification JWT pour FastAPI, Flask et Django."""

import secrets
from gpi.modules.base import Module, ModuleMetadata
from gpi.core.config import ProjectConfig


_SECURITY_PY = '''\
"""Utilitaires de sécurité JWT — hachage de mots de passe et gestion des tokens.

Généré par GPI v2
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

# Configuration JWT depuis les variables d\'environnement
SECRET_KEY = os.environ.get("SECRET_KEY", "changez-moi")
ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
EXPIRATION_MINUTES = int(os.environ.get("JWT_EXPIRATION_MINUTES", "30"))

# Contexte de hachage bcrypt
contexte_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hacher_mot_de_passe(mot_de_passe: str) -> str:
    """Hache un mot de passe en clair avec bcrypt."""
    return contexte_pwd.hash(mot_de_passe)


def verifier_mot_de_passe(mot_de_passe: str, hash_stocke: str) -> bool:
    """Vérifie un mot de passe contre son hash bcrypt."""
    return contexte_pwd.verify(mot_de_passe, hash_stocke)


def creer_token_acces(donnees: dict, expiration: Optional[timedelta] = None) -> str:
    """Crée un token JWT d\'accès.

    Args:
        donnees: Données à encoder dans le token (ex: {"sub": "user@email.com"})
        expiration: Durée de validité (défaut: JWT_EXPIRATION_MINUTES)

    Returns:
        Token JWT signé
    """
    a_encoder = donnees.copy()
    expire = datetime.now(timezone.utc) + (
        expiration or timedelta(minutes=EXPIRATION_MINUTES)
    )
    a_encoder.update({"exp": expire})
    return jwt.encode(a_encoder, SECRET_KEY, algorithm=ALGORITHM)


def decoder_token(token: str) -> Optional[str]:
    """Décode un token JWT et retourne le sujet (sub).

    Returns:
        Le sujet du token, ou None si invalide/expiré
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None
'''

_ROUTES_PY = '''\
"""Routes d\'authentification JWT — inscription et connexion.

Généré par GPI v2
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr

from auth.security import (
    hacher_mot_de_passe,
    verifier_mot_de_passe,
    creer_token_acces,
    decoder_token,
)

router = APIRouter(prefix="/auth", tags=["Authentification"])
oauth2_schema = OAuth2PasswordBearer(tokenUrl="/auth/connexion")

# Stockage en mémoire pour la démonstration — remplacez par une vraie DB
_utilisateurs: dict[str, dict] = {}


class SchemaInscription(BaseModel):
    """Schéma pour l\'inscription d\'un nouvel utilisateur."""
    email: str
    mot_de_passe: str


class SchemaToken(BaseModel):
    """Schéma de réponse pour un token JWT."""
    access_token: str
    token_type: str = "bearer"


@router.post("/inscription", status_code=status.HTTP_201_CREATED)
def inscription(donnees: SchemaInscription):
    """Inscrit un nouvel utilisateur."""
    if donnees.email in _utilisateurs:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un compte avec cet email existe déjà.",
        )
    _utilisateurs[donnees.email] = {
        "email": donnees.email,
        "hash_mot_de_passe": hacher_mot_de_passe(donnees.mot_de_passe),
    }
    return {"message": "Compte créé avec succès."}


@router.post("/connexion", response_model=SchemaToken)
def connexion(formulaire: OAuth2PasswordRequestForm = Depends()):
    """Authentifie un utilisateur et retourne un token JWT."""
    utilisateur = _utilisateurs.get(formulaire.username)
    if not utilisateur or not verifier_mot_de_passe(
        formulaire.password, utilisateur["hash_mot_de_passe"]
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = creer_token_acces({"sub": formulaire.username})
    return SchemaToken(access_token=token)


def obtenir_utilisateur_courant(token: str = Depends(oauth2_schema)) -> str:
    """Dépendance FastAPI — retourne l\'email de l\'utilisateur authentifié."""
    sujet = decoder_token(token)
    if sujet is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return sujet
'''


class JWTAuthModule(Module):
    """Module authentification JWT.

    Compatible FastAPI, Flask et Django.
    Génère les utilitaires de sécurité et les routes d'authentification.
    """

    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            id="auth-jwt",
            name="Authentification JWT",
            version="1.0.0",
            description="JSON Web Tokens avec hachage bcrypt",
            frameworks=["fastapi", "flask", "django"],
            architectures=["monolithic", "microservices"],
            conflicts=["auth-oauth2", "auth-sessions"],
            tags=["auth", "jwt", "security", "bcrypt"],
        )

    def get_dependencies(self) -> list[str]:
        return [
            "python-jose[cryptography]>=3.3.0",
            "passlib[bcrypt]>=1.7.4",
            "python-multipart>=0.0.7",
        ]

    def get_files(self, config: ProjectConfig) -> dict[str, str]:
        return {
            "auth/__init__.py": "",
            "auth/security.py": _SECURITY_PY,
            "auth/routes.py": _ROUTES_PY,
        }

    def get_env_vars(self) -> dict[str, str]:
        return {
            "SECRET_KEY": secrets.token_urlsafe(32),
            "JWT_ALGORITHM": "HS256",
            "JWT_EXPIRATION_MINUTES": "30",
        }

    def get_env_example_vars(self) -> dict[str, str]:
        return {
            "SECRET_KEY": "changez-moi-avec-une-valeur-secrete",
            "JWT_ALGORITHM": "HS256",
            "JWT_EXPIRATION_MINUTES": "30",
        }

    def post_generate_instructions(self) -> list[str]:
        return [
            "Configurez SECRET_KEY dans votre .env avec une valeur aléatoire sécurisée",
            "Montez le router dans main.py : app.include_router(router)",
        ]
