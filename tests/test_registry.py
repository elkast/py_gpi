# tests/test_registry.py
"""Tests unitaires pour ModuleRegistry."""

import pytest
from gpi.modules.registry import ModuleRegistry


@pytest.fixture
def registry():
    return ModuleRegistry()


class TestModuleRegistry:
    """Tests du registre central des modules."""

    def test_charge_17_modules_natifs(self, registry):
        """Le registre doit charger les 17 modules natifs."""
        modules = registry.list_all()
        assert len(modules) >= 17

    def test_modules_natifs_presents(self, registry):
        """Tous les modules natifs attendus doivent être présents."""
        ids_attendus = [
            "framework-fastapi", "framework-flask", "framework-django",
            "auth-jwt", "auth-sessions", "auth-oauth2",
            "database-sqlite", "database-postgres", "database-mysql",
            "cache-redis", "queue-celery", "queue-rq",
            "docker", "docker-compose", "github-actions",
            "tests-pytest", "monitoring-prometheus",
        ]
        for mid in ids_attendus:
            assert registry.get(mid) is not None, f"Module '{mid}' manquant"

    def test_get_module_connu(self, registry):
        """get() doit retourner le module pour un ID connu."""
        module = registry.get("auth-jwt")
        assert module is not None
        assert module.metadata.id == "auth-jwt"

    def test_get_module_inconnu_retourne_none(self, registry):
        """get() doit retourner None pour un ID inconnu."""
        assert registry.get("module-inexistant") is None

    def test_search_par_id(self, registry):
        """search() doit trouver les modules par ID."""
        resultats = registry.search("auth")
        ids = [m.metadata.id for m in resultats]
        assert "auth-jwt" in ids

    def test_search_insensible_casse(self, registry):
        """search() doit être insensible à la casse."""
        resultats_min = registry.search("fastapi")
        resultats_maj = registry.search("FASTAPI")
        assert len(resultats_min) == len(resultats_maj)

    def test_search_par_tag(self, registry):
        """search() doit trouver les modules par tag."""
        resultats = registry.search("database")
        assert len(resultats) > 0

    def test_search_terme_inexistant(self, registry):
        """search() doit retourner une liste vide pour un terme inexistant."""
        resultats = registry.search("xyzabc123inexistant")
        assert resultats == []


# ============================================================
# Tests de propriété (Property-Based Testing) avec Hypothesis
# ============================================================

from hypothesis import given, settings
from hypothesis import strategies as st
from unittest.mock import patch, MagicMock


class TestModuleRegistryProperties:
    """Tests de propriété pour ModuleRegistry."""

    # Property 18 : Recherche dans le registre — cohérence des résultats
    @given(query=st.text(min_size=1, max_size=20).filter(lambda x: x.strip()))
    @settings(max_examples=50)
    def test_property_search_coherence(self, query):
        """Property 18 : search(q) retourne uniquement des modules contenant q."""
        registry = ModuleRegistry()
        resultats = registry.search(query)
        q = query.lower()
        for module in resultats:
            meta = module.metadata
            assert (
                q in meta.id.lower()
                or q in meta.name.lower()
                or q in meta.description.lower()
                or any(q in tag for tag in meta.tags)
            ), f"Module '{meta.id}' retourné mais ne contient pas '{q}'"

    @given(query=st.text(min_size=1, max_size=20).filter(lambda x: x.strip()))
    @settings(max_examples=30)
    def test_property_search_sous_ensemble_list_all(self, query):
        """Property 18b : search() retourne un sous-ensemble de list_all()."""
        registry = ModuleRegistry()
        tous = {m.metadata.id for m in registry.list_all()}
        resultats = {m.metadata.id for m in registry.search(query)}
        assert resultats.issubset(tous)

    # Property 21 : Plugin défectueux — isolation des erreurs
    def test_property_plugin_defectueux_isole(self):
        """Property 21 : Un plugin défectueux ne doit pas empêcher le chargement des autres."""
        # Simuler un entry_point défectueux
        ep_defectueux = MagicMock()
        ep_defectueux.name = "plugin-defectueux"
        ep_defectueux.load.side_effect = ImportError("Module introuvable")

        with patch("importlib.metadata.entry_points") as mock_eps:
            mock_eps.return_value = [ep_defectueux]
            # Le registre doit se charger sans lever d'exception
            registry = ModuleRegistry()
            # Les 17 modules natifs doivent toujours être présents
            assert len(registry.list_all()) >= 17

    def test_property_plugin_exception_generique_isole(self):
        """Property 21b : Toute exception de plugin est silencieuse."""
        ep_defectueux = MagicMock()
        ep_defectueux.name = "plugin-crash"
        ep_defectueux.load.side_effect = RuntimeError("Crash inattendu")

        with patch("importlib.metadata.entry_points") as mock_eps:
            mock_eps.return_value = [ep_defectueux]
            registry = ModuleRegistry()
            assert registry.get("framework-fastapi") is not None
