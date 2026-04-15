# gpi/modules/auth/sessions.py
"""Module authentification par sessions — Flask et Django uniquement."""

from gpi.modules.base import Module, ModuleMetadata
from gpi.core.config import ProjectConfig


class SessionsAuthModule(Module):
    """Module authentification par sessions côté serveur.

    Compatible Flask et Django uniquement (pas FastAPI).
    """

    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            id="auth-sessions",
            name="Authentification Sessions",
            version="1.0.0",
            description="Authentification par sessions côté serveur",
            frameworks=["flask", "django"],
            architectures=["monolithic"],
            conflicts=["auth-jwt", "auth-oauth2"],
            tags=["auth", "sessions", "cookies"],
        )

    def get_dependencies(self) -> list[str]:
        return ["flask-login>=0.6.0"]

    def get_files(self, config: ProjectConfig) -> dict[str, str]:
        return {
            "auth/__init__.py": "",
            "auth/routes.py": _ROUTES_FLASK if config.framework == "flask" else "",
        }


_ROUTES_FLASK = '''\
"""Routes d\'authentification par sessions — Flask.

Généré par GPI v2
"""

from flask import Blueprint, request, jsonify, session

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

# Stockage en mémoire pour la démonstration
_utilisateurs: dict[str, str] = {}


@auth_bp.post("/inscription")
def inscription():
    """Inscrit un nouvel utilisateur."""
    donnees = request.get_json()
    email = donnees.get("email")
    mot_de_passe = donnees.get("mot_de_passe")
    if email in _utilisateurs:
        return jsonify({"erreur": "Email déjà utilisé"}), 409
    _utilisateurs[email] = mot_de_passe
    return jsonify({"message": "Compte créé"}), 201


@auth_bp.post("/connexion")
def connexion():
    """Authentifie un utilisateur et crée une session."""
    donnees = request.get_json()
    email = donnees.get("email")
    mot_de_passe = donnees.get("mot_de_passe")
    if _utilisateurs.get(email) != mot_de_passe:
        return jsonify({"erreur": "Identifiants incorrects"}), 401
    session["utilisateur"] = email
    return jsonify({"message": "Connecté"})


@auth_bp.post("/deconnexion")
def deconnexion():
    """Déconnecte l\'utilisateur en supprimant la session."""
    session.pop("utilisateur", None)
    return jsonify({"message": "Déconnecté"})
'''
