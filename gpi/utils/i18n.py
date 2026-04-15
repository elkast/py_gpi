"""Gestion multilingue des commentaires."""
from __future__ import annotations

# Dictionnaire de commentaires fr/en pour chaque clé
COMMENTAIRES: dict[str, dict[str, str]] = {
    # --- Communs ---
    "main_app": {
        "fr": "# Point d'entrée principal de l'application",
        "en": "# Main application entry point",
    },
    "db_config": {
        "fr": "# Configuration de la base de données",
        "en": "# Database configuration",
    },
    "create_tables": {
        "fr": "# Création des tables au démarrage",
        "en": "# Create tables on startup",
    },
    "model_base": {
        "fr": "# Modèle de base avec champs communs",
        "en": "# Base model with common fields",
    },
    "user_model": {
        "fr": "# Modèle utilisateur",
        "en": "# User model",
    },
    "item_model": {
        "fr": "# Modèle d'exemple (à personnaliser)",
        "en": "# Example model (customize as needed)",
    },
    "crud_create": {
        "fr": "# Créer une ressource",
        "en": "# Create a resource",
    },
    "crud_read": {
        "fr": "# Lire une ou plusieurs ressources",
        "en": "# Read one or multiple resources",
    },
    "crud_update": {
        "fr": "# Mettre à jour une ressource",
        "en": "# Update a resource",
    },
    "crud_delete": {
        "fr": "# Supprimer une ressource",
        "en": "# Delete a resource",
    },
    "auth_module": {
        "fr": "# Module d'authentification JWT",
        "en": "# JWT authentication module",
    },
    "hash_password": {
        "fr": "# Hachage et vérification des mots de passe",
        "en": "# Password hashing and verification",
    },
    "create_token": {
        "fr": "# Création du token JWT",
        "en": "# Create JWT token",
    },
    "verify_token": {
        "fr": "# Vérification du token JWT",
        "en": "# Verify JWT token",
    },
    "register_route": {
        "fr": "# Route d'inscription",
        "en": "# Registration route",
    },
    "login_route": {
        "fr": "# Route de connexion",
        "en": "# Login route",
    },
    "protected_route": {
        "fr": "# Route protégée (nécessite un token)",
        "en": "# Protected route (requires token)",
    },
    "env_config": {
        "fr": "# Variables d'environnement",
        "en": "# Environment variables",
    },
    "requirements": {
        "fr": "# Dépendances du projet",
        "en": "# Project dependencies",
    },
    "test_module": {
        "fr": "# Tests unitaires",
        "en": "# Unit tests",
    },
    "dockerfile": {
        "fr": "# Image Docker pour l'application",
        "en": "# Docker image for the application",
    },
    "docker_compose": {
        "fr": "# Orchestration des services avec Docker Compose",
        "en": "# Service orchestration with Docker Compose",
    },
    "schemas": {
        "fr": "# Schémas de validation (entrée/sortie)",
        "en": "# Validation schemas (input/output)",
    },
    "services_layer": {
        "fr": "# Couche de services (logique métier)",
        "en": "# Service layer (business logic)",
    },
    "dependencies": {
        "fr": "# Injection de dépendances",
        "en": "# Dependency injection",
    },
}


def cmt(cle: str, langue: str) -> str:
    """Retourne le commentaire pour la clé et la langue donnée."""
    entry = COMMENTAIRES.get(cle, {})
    if langue == "bilingue":
        en = entry.get("en", "")
        fr = entry.get("fr", "")
        return f"{en}\n{fr}" if en and fr else en or fr
    return entry.get(langue, entry.get("en", f"# {cle}"))
