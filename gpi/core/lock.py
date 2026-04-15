# gpi/core/lock.py
"""Gestion du fichier gpi.lock — reproductibilité des projets générés.

Format JSON lisible par un humain, versionnable dans Git.
Contient : version GPI, config, modules résolus, dépendances Python, checksum SHA-256.
"""

import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path

from gpi.core.config import ProjectConfig
from gpi.core.resolver import ResolutionResult


class LockFile:
    """Gestion du fichier gpi.lock.

    Garantit l'intégrité via un checksum SHA-256.
    Permet de reproduire exactement un projet généré via `gpi replay`.
    """

    FILENAME = "gpi.lock"

    @staticmethod
    def create(
        config: ProjectConfig,
        resolution: ResolutionResult,
        dependencies: list[str],
    ) -> dict:
        """Crée le contenu du fichier gpi.lock.

        Args:
            config: Configuration du projet
            resolution: Résultat de la résolution
            dependencies: Liste des packages Python (requirements.txt)

        Returns:
            Dictionnaire prêt à sérialiser en JSON (avec checksum)

        Note:
            GROQ_API_KEY n'est jamais incluse dans le lock.
        """
        # Import ici pour éviter les imports circulaires
        try:
            import gpi as _gpi
            version = _gpi.__version__
        except Exception:
            version = "2.0.0"

        donnees = {
            "gpi_version": version,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "config": config.model_dump(),
            "resolved_modules": [
                {
                    "id": module_id,
                    "version": "1.0.0",
                    "auto": module_id in resolution.auto_added,
                }
                for module_id in resolution.modules
            ],
            "python_dependencies": sorted(dependencies),
        }

        # Calcul du checksum SHA-256 pour détecter les modifications manuelles
        contenu = json.dumps(donnees, sort_keys=True, ensure_ascii=False)
        donnees["checksum"] = f"sha256:{hashlib.sha256(contenu.encode()).hexdigest()}"
        return donnees

    @staticmethod
    def write(data: dict, output_dir: str) -> Path:
        """Écrit le fichier gpi.lock dans le dossier de sortie.

        Args:
            data: Dictionnaire créé par LockFile.create()
            output_dir: Dossier de destination

        Returns:
            Chemin absolu du fichier gpi.lock créé
        """
        chemin_lock = Path(output_dir) / LockFile.FILENAME
        with open(chemin_lock, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return chemin_lock

    @staticmethod
    def read(path: str) -> dict:
        """Lit et valide un fichier gpi.lock.

        Args:
            path: Chemin vers le fichier gpi.lock

        Returns:
            Dictionnaire des données du lock

        Raises:
            ValueError: Si le checksum est invalide (fichier corrompu ou modifié)
        """
        with open(path, "r", encoding="utf-8") as f:
            donnees = json.load(f)

        # Validation du checksum SHA-256
        checksum = donnees.pop("checksum", None)
        if checksum:
            contenu = json.dumps(donnees, sort_keys=True, ensure_ascii=False)
            attendu = f"sha256:{hashlib.sha256(contenu.encode()).hexdigest()}"
            if checksum != attendu:
                raise ValueError(
                    "Le fichier gpi.lock est corrompu ou a été modifié manuellement. "
                    "Régénérez-le avec `gpi init` ou `gpi replay gpi.yaml`."
                )
            donnees["checksum"] = checksum

        return donnees

    @staticmethod
    def to_config(lock_data: dict) -> ProjectConfig:
        """Reconstruit une ProjectConfig depuis les données d'un gpi.lock.

        Args:
            lock_data: Dictionnaire lu par LockFile.read()

        Returns:
            ProjectConfig équivalente à la configuration originale
        """
        return ProjectConfig(**lock_data["config"])
