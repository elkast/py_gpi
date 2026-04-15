# gpi/modules/monitoring/prometheus_grafana.py
"""Module monitoring Prometheus + Grafana — FastAPI et Flask uniquement."""

from gpi.modules.base import Module, ModuleMetadata
from gpi.core.config import ProjectConfig


_METRICS_PY = '''\
"""Configuration du monitoring Prometheus pour {{ project_name }}.

Généré par GPI v2
"""

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator


def configurer_monitoring(app: FastAPI) -> None:
    """Configure l\'instrumentation Prometheus sur l\'application FastAPI.

    Expose les métriques sur /metrics (compatible Prometheus/Grafana).
    """
    Instrumentator().instrument(app).expose(app)
'''


class PrometheusModule(Module):
    """Module monitoring Prometheus + Grafana — FastAPI et Flask uniquement."""

    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            id="monitoring-prometheus",
            name="Prometheus + Grafana",
            version="1.0.0",
            description="Métriques Prometheus et tableaux de bord Grafana",
            frameworks=["fastapi", "flask"],
            architectures=["monolithic", "microservices"],
            tags=["monitoring", "prometheus", "grafana", "metrics", "observability"],
        )

    def get_dependencies(self) -> list[str]:
        return ["prometheus-fastapi-instrumentator>=6.0.0"]

    def get_files(self, config: ProjectConfig) -> dict[str, str]:
        return {"monitoring.py": _METRICS_PY}

    def post_generate_instructions(self) -> list[str]:
        return [
            "Appelez configurer_monitoring(app) dans main.py",
            "Métriques disponibles sur : http://localhost:8000/metrics",
            "Configurez Prometheus pour scraper /metrics",
        ]
