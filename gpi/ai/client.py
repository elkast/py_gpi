# gpi/ai/client.py
"""Client Groq pour GPI — gestion d'authentification, erreurs et lazy init.

Entièrement optionnel — GPI fonctionne sans clé API.
"""

import os
from typing import Optional

# Chargement automatique du .env si python-dotenv est disponible
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class GpiGroqClient:
    """Client Groq pour GPI.

    Instancié une seule fois (lazy) pour éviter les connexions inutiles.
    Retourne is_available=False si GROQ_API_KEY est absente.
    """

    MODEL = "llama-3.3-70b-versatile"    # Équilibre vitesse/qualité
    FAST_MODEL = "llama-3.1-8b-instant"  # Pour les requêtes rapides (suggestions)

    def __init__(self, api_key: Optional[str] = None) -> None:
        # Priorité : paramètre > variable d'environnement
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        self._client = None  # Lazy initialization

    @property
    def is_available(self) -> bool:
        """True si GROQ_API_KEY est configurée."""
        return bool(self.api_key)

    def _get_client(self):
        """Retourne le client Groq (lazy init).

        Raises:
            RuntimeError: Si GROQ_API_KEY n'est pas configurée
        """
        if not self.is_available:
            raise RuntimeError(
                "GROQ_API_KEY non configurée. "
                "Ajoutez 'GROQ_API_KEY=votre-cle' à votre fichier .env "
                "ou définissez la variable d'environnement."
            )
        if self._client is None:
            try:
                from groq import Groq
                self._client = Groq(api_key=self.api_key)
            except ImportError:
                raise RuntimeError(
                    "Le package 'groq' n'est pas installé. "
                    "Installez-le avec : pip install groq"
                )
        return self._client

    def complete(
        self,
        prompt: str,
        system: str = "Tu es un expert en développement backend Python.",
        model: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.3,
    ) -> str:
        """Envoie un prompt au modèle Groq et retourne la réponse textuelle.

        Args:
            prompt: Message utilisateur
            system: Message système (contexte du modèle)
            model: Modèle à utiliser (défaut: MODEL)
            max_tokens: Nombre maximum de tokens en sortie
            temperature: Créativité (0 = déterministe, 1 = créatif)

        Returns:
            Réponse textuelle du modèle

        Raises:
            RuntimeError: GROQ_API_KEY non configurée
            Exception: Erreur réseau ou API Groq
        """
        client = self._get_client()

        try:
            from groq import APIConnectionError, RateLimitError, APIStatusError

            reponse = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                model=model or self.MODEL,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return reponse.choices[0].message.content

        except Exception as e:
            # Gestion des erreurs Groq spécifiques
            nom_classe = type(e).__name__
            if "APIConnectionError" in nom_classe:
                raise Exception(
                    "Impossible de contacter l'API Groq. Vérifiez votre connexion internet."
                )
            elif "RateLimitError" in nom_classe:
                raise Exception(
                    "Limite de taux Groq atteinte. Réessayez dans quelques secondes."
                )
            elif "APIStatusError" in nom_classe:
                raise Exception(f"Erreur Groq API : {e}")
            raise
