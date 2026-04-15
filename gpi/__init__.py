# gpi/__init__.py
"""GPI — Générateur de Projet Intelligent.

Compositeur de projets backend Python.

Usage CLI : gpi init
Usage API  : import gpi; project = gpi.compose(...)
"""

__version__ = "2.0.5"
__author__ = "SOSSOU Elkast Orsini"

from gpi.core.config import ProjectConfig
from gpi.core.resolver import Resolver, ResolutionResult
from gpi.core.composer import Composer
from gpi.core.writer import Writer
from gpi.core.lock import LockFile
from gpi.modules.registry import ModuleRegistry


def compose(
    name: str,
    framework: str = "fastapi",
    architecture: str = "monolithic",
    modules: list[str] | None = None,
    description: str = "",
    language: str = "fr",
    port: int = 8000,
    use_groq_ai: bool = False,
) -> "GenerationPlan":
    """Crée un plan de génération de projet.

    Args:
        name        : Nom du projet (lettres/chiffres/underscores, 2-49 chars)
        framework   : "fastapi" | "flask" | "django"
        architecture: "monolithic" | "microservices"
        modules     : Liste d'IDs de modules (ex: ["auth-jwt", "database-postgres"])
        description : Description du projet
        language    : "fr" | "en"
        port        : Port d'écoute (défaut: 8000)
        use_groq_ai : Active les suggestions IA

    Returns:
        GenerationPlan avec méthode .generate(output_dir)

    Example:
        import gpi
        project = gpi.compose(
            name="monapi",
            framework="fastapi",
            modules=["auth-jwt", "database-postgres"],
        )
        project.generate("./output")
    """
    config = ProjectConfig(
        name=name,
        framework=framework,
        architecture=architecture,
        modules=modules or [],
        description=description,
        language=language,
        port=port,
        use_groq_ai=use_groq_ai,
    )
    return GenerationPlan(config)


def from_yaml(path: str) -> "GenerationPlan":
    """Charge une configuration depuis un fichier gpi.yaml.

    Args:
        path: Chemin vers le fichier YAML

    Returns:
        GenerationPlan prêt à générer
    """
    return GenerationPlan(ProjectConfig.from_yaml(path))


def from_toml(path: str) -> "GenerationPlan":
    """Charge une configuration depuis un fichier gpi.toml.

    Args:
        path: Chemin vers le fichier TOML

    Returns:
        GenerationPlan prêt à générer
    """
    return GenerationPlan(ProjectConfig.from_toml(path))


class GenerationPlan:
    """Plan de génération d'un projet GPI.

    Retourné par gpi.compose(), gpi.from_yaml() et gpi.from_toml().
    Encapsule la configuration et le pipeline de génération.
    """

    def __init__(self, config: ProjectConfig) -> None:
        self.config = config
        self._registry = ModuleRegistry()
        self._resolver = Resolver(self._registry)
        self._resolution: ResolutionResult | None = None

    def resolve(self) -> ResolutionResult:
        """Résoud les modules sans générer de fichiers.

        Returns:
            ResolutionResult avec l'ordre de résolution, les modules auto-ajoutés
            et les avertissements
        """
        self._resolution = self._resolver.resolve(self.config)
        return self._resolution

    def generate(self, output_dir: str) -> str:
        """Génère le projet dans le dossier spécifié.

        Args:
            output_dir: Chemin du dossier de sortie (créé si inexistant)

        Returns:
            Chemin absolu du projet généré
        """
        if self._resolution is None:
            self.resolve()

        composer = Composer(self._registry)
        fichiers = composer.compose(self.config, self._resolution)

        writer = Writer()
        chemin = writer.write(
            fichiers, output_dir, self.config, self._resolution, self._registry
        )
        return str(chemin)
