# gpi/core/exceptions.py
"""Hiérarchie d'exceptions personnalisées pour GPI v2."""


class GpiError(Exception):
    """Classe de base pour toutes les erreurs GPI."""
    pass


class ValidationError(GpiError):
    """Configuration invalide (règle métier violée)."""
    pass


class ModuleNotFoundError(GpiError):
    """Module demandé introuvable dans le registre."""
    pass


class ModuleConflictError(GpiError):
    """Deux modules incompatibles ont été demandés simultanément."""
    pass


class ModuleIncompatibleError(GpiError):
    """Module incompatible avec le framework ou l'architecture choisis."""
    pass


class CircularDependencyError(GpiError):
    """Dépendance circulaire détectée entre modules."""
    pass


class LockFileError(GpiError):
    """Erreur liée au fichier gpi.lock (corrompu, manquant, version incompatible)."""
    pass


class GroqAIError(GpiError):
    """Erreur lors de l'appel à l'API Groq."""
    pass
