# gpi/core/writer.py
"""Écriture des fichiers composés sur le disque.

Crée les dossiers parents si nécessaire et génère le gpi.lock.
"""

from pathlib import Path
from typing import Optional

from gpi.core.config import ProjectConfig
from gpi.core.resolver import ResolutionResult


class Writer:
    """Écrit les fichiers composés sur le disque de façon sécurisée.

    Crée les dossiers parents si nécessaire.
    Génère le gpi.lock si config + resolution + registry sont fournis.
    """

    def write(
        self,
        files: dict[str, str],
        output_dir: str,
        config: Optional[ProjectConfig] = None,
        resolution: Optional[ResolutionResult] = None,
        registry=None,
    ) -> Path:
        """Écrit tous les fichiers dans output_dir.

        Args:
            files: Dictionnaire {chemin_relatif: contenu}
            output_dir: Dossier de sortie (créé si inexistant)
            config: Configuration du projet (pour gpi.lock)
            resolution: Résultat de résolution (pour gpi.lock)
            registry: Registre des modules (pour collecter les dépendances)

        Returns:
            Chemin absolu du dossier de sortie
        """
        sortie = Path(output_dir)
        sortie.mkdir(parents=True, exist_ok=True)

        # Écriture de chaque fichier
        for chemin_relatif, contenu in files.items():
            chemin_complet = sortie / chemin_relatif
            chemin_complet.parent.mkdir(parents=True, exist_ok=True)
            chemin_complet.write_text(contenu, encoding="utf-8", newline="")

        # Génération du gpi.lock si toutes les informations sont disponibles
        if config is not None and resolution is not None and registry is not None:
            from gpi.core.composer import Composer
            from gpi.core.lock import LockFile

            compositeur = Composer(registry)
            deps = compositeur.get_all_dependencies(resolution)
            donnees_lock = LockFile.create(config, resolution, deps)
            LockFile.write(donnees_lock, output_dir)

        return sortie.resolve()
