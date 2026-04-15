# tests/test_groq_client.py
"""Tests unitaires pour GpiGroqClient et suggest_modules()."""

import pytest
from unittest.mock import MagicMock, patch

from gpi.ai.client import GpiGroqClient
from gpi.ai.suggestions import suggest_modules


class TestGpiGroqClient:
    """Tests du client Groq."""

    def test_is_available_sans_cle(self):
        """is_available doit retourner False sans GROQ_API_KEY."""
        client = GpiGroqClient(api_key=None)
        with patch.dict("os.environ", {}, clear=True):
            client2 = GpiGroqClient()
            assert not client2.is_available

    def test_is_available_avec_cle(self):
        """is_available doit retourner True avec une clé."""
        client = GpiGroqClient(api_key="test-key-123")
        assert client.is_available

    def test_complete_sans_cle_leve_runtime_error(self):
        """complete() sans clé doit lever RuntimeError."""
        client = GpiGroqClient(api_key=None)
        with patch.dict("os.environ", {}, clear=True):
            client2 = GpiGroqClient()
            with pytest.raises(RuntimeError, match="GROQ_API_KEY"):
                client2.complete("test prompt")

    def test_lazy_init_client_non_cree_sans_appel(self):
        """Le client Groq ne doit pas être créé avant le premier appel."""
        client = GpiGroqClient(api_key="test-key")
        assert client._client is None

    def test_complete_erreur_connexion(self):
        """APIConnectionError doit lever une Exception avec message réseau."""
        client = GpiGroqClient(api_key="test-key")

        # Créer une vraie classe dont le nom contient "APIConnectionError"
        class APIConnectionError(Exception):
            pass

        mock_groq_client = MagicMock()
        mock_groq_client.chat.completions.create.side_effect = APIConnectionError("connexion échouée")

        with patch("gpi.ai.client.GpiGroqClient._get_client", return_value=mock_groq_client):
            with pytest.raises(Exception, match="connexion"):
                client.complete("test")

    def test_complete_rate_limit(self):
        """RateLimitError doit lever une Exception avec message retry."""
        client = GpiGroqClient(api_key="test-key")

        # Créer une vraie classe dont le nom contient "RateLimitError"
        class RateLimitError(Exception):
            pass

        mock_groq_client = MagicMock()
        mock_groq_client.chat.completions.create.side_effect = RateLimitError("rate limit")

        with patch("gpi.ai.client.GpiGroqClient._get_client", return_value=mock_groq_client):
            with pytest.raises(Exception, match="taux|Réessayez"):
                client.complete("test")

    def test_complete_succes_avec_mock(self):
        """complete() doit retourner la réponse du modèle."""
        client = GpiGroqClient(api_key="test-key")

        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Réponse du modèle"

        mock_groq_client = MagicMock()
        mock_groq_client.chat.completions.create.return_value = mock_response

        with patch("gpi.ai.client.GpiGroqClient._get_client", return_value=mock_groq_client):
            result = client.complete("test prompt")
            assert result == "Réponse du modèle"

    def test_modeles_definis(self):
        """Les constantes MODEL et FAST_MODEL doivent être définies."""
        assert GpiGroqClient.MODEL == "llama-3.3-70b-versatile"
        assert GpiGroqClient.FAST_MODEL == "llama-3.1-8b-instant"


class TestSuggestModules:
    """Tests de suggest_modules()."""

    def test_suggest_modules_retourne_liste_vide_si_exception(self):
        """suggest_modules() doit retourner [] en cas d'exception."""
        client = GpiGroqClient(api_key=None)
        result = suggest_modules("description", "fastapi", "monolithic", client)
        assert result == []

    def test_suggest_modules_retourne_liste_vide_si_erreur_json(self):
        """suggest_modules() doit retourner [] si la réponse n'est pas du JSON valide."""
        client = GpiGroqClient(api_key="test-key")

        mock_groq_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Pas du JSON valide"
        mock_groq_client.chat.completions.create.return_value = mock_response

        with patch("gpi.ai.client.GpiGroqClient._get_client", return_value=mock_groq_client):
            result = suggest_modules("description", "fastapi", "monolithic", client)
            assert result == []

    def test_suggest_modules_retourne_liste_si_succes(self):
        """suggest_modules() doit retourner la liste de modules si succès."""
        import json
        client = GpiGroqClient(api_key="test-key")

        mock_groq_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            "modules": ["auth-jwt", "database-postgres"],
            "reasoning": "Test"
        })
        mock_groq_client.chat.completions.create.return_value = mock_response

        with patch("gpi.ai.client.GpiGroqClient._get_client", return_value=mock_groq_client):
            result = suggest_modules("API e-commerce", "fastapi", "monolithic", client)
            assert "auth-jwt" in result
            assert "database-postgres" in result


# ============================================================
# Tests de propriété (Property-Based Testing) avec Hypothesis
# ============================================================

from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st


class TestSuggestModulesProperties:
    """Tests de propriété pour suggest_modules()."""

    # Property 17 : suggest_modules() — échec silencieux
    @given(
        description=st.text(min_size=0, max_size=100),
        framework=st.sampled_from(["fastapi", "flask", "django"]),
        architecture=st.sampled_from(["monolithic", "microservices"]),
    )
    @settings(max_examples=30, suppress_health_check=[HealthCheck.too_slow])
    def test_property_suggest_modules_echec_silencieux(self, description, framework, architecture):
        """Property 17 : suggest_modules() retourne toujours une liste, jamais d'exception."""
        # Client sans clé → toujours une exception interne
        client = GpiGroqClient(api_key=None)
        result = suggest_modules(description, framework, architecture, client)
        assert isinstance(result, list)

    @given(
        description=st.text(min_size=0, max_size=100),
        framework=st.sampled_from(["fastapi", "flask", "django"]),
    )
    @settings(max_examples=20)
    def test_property_suggest_modules_retourne_liste(self, description, framework):
        """Property 17b : suggest_modules() retourne toujours une liste."""
        client = GpiGroqClient(api_key=None)
        result = suggest_modules(description, framework, "monolithic", client)
        assert isinstance(result, list)
