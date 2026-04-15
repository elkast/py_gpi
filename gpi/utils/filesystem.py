# gpi/utils/filesystem.py
"""Opérations fichiers sécurisées pour GPI."""

from pathlib import Path


def ecrire_fichier(chemin: str | Path, contenu: str, encoding: str = "utf-8") -> Path:
    """Écrit un fichier en créant les dossiers parents si nécessaire.

    Args:
        chemin: Chemin du fichier à créer
        contenu: Contenu à écrire
        encoding: Encodage (défaut: utf-8)

    Returns:
        Chemin absolu du fichier créé
    """
    p = Path(chemin)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(contenu, encoding=encoding)
    return p.resolve()


def lire_fichier(chemin: str | Path, encoding: str = "utf-8") -> str:
    """Lit un fichier texte.

    Args:
        chemin: Chemin du fichier à lire
        encoding: Encodage (défaut: utf-8)

    Returns:
        Contenu du fichier

    Raises:
        FileNotFoundError: Si le fichier n'existe pas
    """
    return Path(chemin).read_text(encoding=encoding)
