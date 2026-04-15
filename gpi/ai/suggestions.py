# gpi/ai/suggestions.py
"""Suggestions de modules GPI via Groq AI.

Retourne une liste vide en cas d'échec (silencieux) — GPI continue sans suggestion.
"""

import json
from gpi.ai.client import GpiGroqClient


SYSTEM_PROMPT = """Tu es un expert en architecture backend Python.
Tu dois suggérer des modules GPI pertinents pour un projet donné.
Tu ne réponds qu'en JSON valide, sans explication supplémentaire.
Les modules disponibles sont :
- auth-jwt, auth-sessions, auth-oauth2
- database-sqlite, database-postgres, database-mysql
- cache-redis, queue-celery, queue-rq
- docker, docker-compose, tests-pytest
- monitoring-prometheus, github-actions
"""


def suggest_modules(
    description: str,
    framework: str,
    architecture: str,
    client: GpiGroqClient,
) -> list[str]:
    """Suggère des modules GPI basé sur la description du projet.

    Args:
        description: Description libre du projet par l'utilisateur
        framework: Framework choisi
        architecture: Architecture choisie
        client: Client Groq initialisé

    Returns:
        Liste d'IDs de modules suggérés (vide si échec silencieux)
    """
    prompt = f"""
Analyse ce projet et suggère les modules GPI appropriés :

Description : {description}
Framework   : {framework}
Architecture: {architecture}

Réponds avec un JSON de ce format exact :
{{"modules": ["auth-jwt", "database-postgres"], "reasoning": "Courte explication"}}

Ne suggère que les modules vraiment nécessaires. Évite la sur-ingénierie.
"""
    try:
        reponse = client.complete(
            prompt=prompt,
            system=SYSTEM_PROMPT,
            model=GpiGroqClient.FAST_MODEL,
            max_tokens=256,
            temperature=0.1,
        )
        donnees = json.loads(reponse.strip())
        return donnees.get("modules", [])
    except Exception:
        return []  # Échec silencieux — GPI continue sans suggestion
