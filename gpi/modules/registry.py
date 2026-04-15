# gpi/modules/registry.py
"""Registre central de tous les modules GPI — natifs et plugins.

Charge les modules natifs au démarrage, puis les plugins via entry_points.
Point d'accès unique pour le Resolver et le Composer.
"""

import importlib.metadata
from gpi.modules.base import Module


class ModuleRegistry:
    """Registre central de tous les modules GPI.

    Charge les modules natifs embarqués dans le package, puis les plugins
    installés via le groupe entry_points "gpi.modules".

    Les erreurs de chargement des plugins sont silencieuses — un plugin
    défectueux n'empêche pas GPI de fonctionner.
    """

    ENTRY_POINT_GROUP = "gpi.modules"  # Groupe entry_point pour les plugins tiers

    def __init__(self) -> None:
        self._modules: dict[str, Module] = {}
        self._load_builtin_modules()
        self._load_plugin_modules()

    def _load_builtin_modules(self) -> None:
        """Charge les 17 modules natifs embarqués dans le package GPI."""
        from gpi.modules.framework.fastapi import FastAPIModule
        from gpi.modules.framework.flask import FlaskModule
        from gpi.modules.framework.django import DjangoModule
        from gpi.modules.auth.jwt import JWTAuthModule
        from gpi.modules.auth.sessions import SessionsAuthModule
        from gpi.modules.auth.oauth2 import OAuth2Module
        from gpi.modules.database.sqlite import SQLiteModule
        from gpi.modules.database.postgres import PostgresModule
        from gpi.modules.database.mysql import MySQLModule
        from gpi.modules.cache.redis import RedisModule
        from gpi.modules.queue.celery import CeleryModule
        from gpi.modules.queue.rq import RQModule
        from gpi.modules.infra.docker import DockerModule
        from gpi.modules.infra.docker_compose import DockerComposeModule
        from gpi.modules.infra.github_actions import GitHubActionsModule
        from gpi.modules.testing.pytest import PytestModule
        from gpi.modules.monitoring.prometheus_grafana import PrometheusModule

        for classe_module in [
            FastAPIModule, FlaskModule, DjangoModule,
            JWTAuthModule, SessionsAuthModule, OAuth2Module,
            SQLiteModule, PostgresModule, MySQLModule,
            RedisModule, CeleryModule, RQModule,
            DockerModule, DockerComposeModule, GitHubActionsModule,
            PytestModule, PrometheusModule,
        ]:
            instance = classe_module()
            self._modules[instance.metadata.id] = instance

    def _load_plugin_modules(self) -> None:
        """Charge les plugins installés via entry_points Python.

        Un plugin déclare dans son pyproject.toml :
            [project.entry-points."gpi.modules"]
            mon_module = "mon_package:MonModule"

        Les erreurs de chargement sont silencieuses (plugin défectueux ignoré).
        """
        try:
            eps = importlib.metadata.entry_points(group=self.ENTRY_POINT_GROUP)
            for ep in eps:
                try:
                    classe_module = ep.load()
                    instance = classe_module()
                    self._modules[instance.metadata.id] = instance
                except Exception as e:
                    # Avertissement non bloquant — plugin défectueux ignoré
                    print(f"⚠ Plugin '{ep.name}' ignoré : {e}")
        except Exception:
            pass  # Aucun plugin installé

    def get(self, module_id: str) -> Module | None:
        """Retourne un module par son ID, ou None s'il n'existe pas."""
        return self._modules.get(module_id)

    def list_all(self) -> list[Module]:
        """Retourne tous les modules disponibles (natifs + plugins)."""
        return list(self._modules.values())

    def search(self, query: str) -> list[Module]:
        """Recherche dans les IDs, noms, descriptions et tags.

        Args:
            query: Terme de recherche (insensible à la casse)

        Returns:
            Liste des modules dont l'ID, le nom, la description ou un tag
            contient le terme de recherche.
        """
        q = query.lower()
        return [
            m for m in self._modules.values()
            if (
                q in m.metadata.id.lower()
                or q in m.metadata.name.lower()
                or q in m.metadata.description.lower()
                or any(q in tag for tag in m.metadata.tags)
            )
        ]
