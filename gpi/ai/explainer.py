# gpi/ai/explainer.py
"""Explication pédagogique du code généré via Groq AI."""

from pathlib import Path
from gpi.ai.client import GpiGroqClient


def explain_project(project_path: str, client: GpiGroqClient) -> str:
    """Génère une explication pédagogique du projet généré.

    Collecte les fichiers .py principaux (max 10, 500 chars chacun)
    et demande à Groq d'expliquer le projet en langage naturel.

    Args:
        project_path: Chemin vers le dossier du projet généré
        client: Client Groq initialisé

    Returns:
        Explication markdown du projet
    """
    chemin = Path(project_path)

    # Collecte des fichiers principaux pour le contexte
    fichiers_contenu: dict[str, str] = {}
    for fichier in chemin.rglob("*.py"):
        if not any(p in str(fichier) for p in ["__pycache__", ".pyc", "venv", ".venv"]):
            try:
                contenu = fichier.read_text(encoding="utf-8")
                chemin_relatif = str(fichier.relative_to(chemin))
                fichiers_contenu[chemin_relatif] = contenu[:500]  # Limite pour le contexte
            except Exception:
                pass

    # Limite à 10 fichiers pour ne pas dépasser le contexte du modèle
    resume_fichiers = "\n".join(
        f"--- {chemin_f} ---\n{contenu}"
        for chemin_f, contenu in list(fichiers_contenu.items())[:10]
    )

    prompt = f"""
Voici la structure d'un projet backend Python généré par GPI :

{resume_fichiers}

Explique ce projet de façon pédagogique pour un étudiant ou débutant :
1. Ce que fait chaque fichier principal (2-3 phrases par fichier)
2. Comment les fichiers interagissent
3. Comment lancer le projet
4. 3 étapes pour commencer à développer

Sois concis, clair, et pratique. Langage : français.
"""

    return client.complete(
        prompt=prompt,
        system="Tu es un professeur Python bienveillant et pédagogue.",
        max_tokens=1500,
        temperature=0.4,
    )
