# gpi/modules/auth/oauth2.py
"""Module OAuth2 avec scopes — FastAPI uniquement."""

from gpi.modules.base import Module, ModuleMetadata
from gpi.core.config import ProjectConfig


_OAUTH2_PY = '''\
"""Configuration OAuth2 avec scopes pour FastAPI.

Généré par GPI v2
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from pydantic import BaseModel

oauth2_schema = OAuth2PasswordBearer(
    tokenUrl="/auth/token",
    scopes={
        "lecture": "Accès en lecture",
        "ecriture": "Accès en écriture",
        "admin": "Accès administrateur",
    },
)


class SchemaToken(BaseModel):
    """Schéma de réponse pour un token OAuth2."""
    access_token: str
    token_type: str = "bearer"
    scope: str = ""


def verifier_scopes(
    scopes_requis: SecurityScopes,
    token: str = Depends(oauth2_schema),
) -> str:
    """Vérifie que le token possède les scopes requis."""
    # Implémentez la vérification JWT ici
    return token
'''


class OAuth2Module(Module):
    """Module OAuth2 avec scopes — FastAPI uniquement."""

    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            id="auth-oauth2",
            name="OAuth2",
            version="1.0.0",
            description="OAuth2 avec scopes pour FastAPI",
            frameworks=["fastapi"],
            architectures=["monolithic", "microservices"],
            conflicts=["auth-jwt", "auth-sessions"],
            tags=["auth", "oauth2", "scopes", "security"],
        )

    def get_dependencies(self) -> list[str]:
        return [
            "python-multipart>=0.0.7",
            "python-jose[cryptography]>=3.3.0",
        ]

    def get_files(self, config: ProjectConfig) -> dict[str, str]:
        return {
            "auth/__init__.py": "",
            "auth/oauth2.py": _OAUTH2_PY,
        }
