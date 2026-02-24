"""Prometheus metrics instrumentation for FastAPI."""

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

_instrumentator = Instrumentator(
    should_group_status_codes=False,
    excluded_handlers=["/health"],
)


def instrument_app(app: FastAPI) -> None:
    """Attach Prometheus metrics middleware and expose /metrics endpoint.

    Automatically tracks request count, latency, and status codes
    for all API routes. Excludes /health to avoid noise.
    """
    _instrumentator.instrument(app).expose(app)
