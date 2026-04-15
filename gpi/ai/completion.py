# gpi/ai/completion.py
"""Complétion des champs manquants de la configuration via Groq AI."""

import json
from gpi.ai.client import GpiGroqClient


def completer_description(
    nom_projet: str,
    framework: str,
    modules: list[str],
    client: GpiGroqClient,
) -> str:
    """Génère une description de projet basée sur les informations fournies.

    Args:
        nom_projet: Nom du projet
        framework: Framework choisi
        modules: Liste des modules sélectionnés
        client: Client Groq initialisé

    Returns:
        Description générée, ou chaîne vide en cas d'échec
    """
    prompt = f"""
Génère une description courte (1-2 phrases) pour ce projet backend Python :

Nom       : {nom_projet}
Framework : {framework}
Modules   : {', '.join(modules) if modules else 'aucun'}

Réponds uniquement avec la description, sans guillemets ni formatage.
"""
    try:
        return client.complete(
            prompt=prompt,
            system="Tu es un expert en développement backend Python. Sois concis.",
            model=GpiGroqClient.FAST_MODEL,
            max_tokens=100,
            temperature=0.4,
        ).strip()
    except Exception:
        return ""  # Échec silencieux
