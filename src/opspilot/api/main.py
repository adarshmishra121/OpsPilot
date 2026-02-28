"""
OpsPilot API — application entry point.

Start with: uvicorn opspilot.api.main:app --reload --port 8000
"""

from fastapi import FastAPI

from opspilot.api.routes.health import router as health_router
from opspilot.api.routes.incident import router as incident_router
from opspilot.api.routes.rag import router as rag_router
from opspilot.api.routes.anomaly import router as anomaly_router
from opspilot.api.routes.feedback import router as feedback_router
from opspilot.api.routes.admin import router as admin_router
from opspilot.observability.logging import configure_logging
from opspilot.observability.metrics import instrument_app


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    configure_logging()

    app = FastAPI(
        title="OpsPilot API",
        version="0.1.0",
        description="Incident Response Copilot — AIOps + RAG + Tool-Using Agents",
    )

    app.include_router(health_router)
    app.include_router(incident_router, prefix="/incident", tags=["incident"])
    app.include_router(rag_router, prefix="/rag", tags=["rag"])
    app.include_router(anomaly_router, prefix="/anomaly", tags=["anomaly"])
    app.include_router(feedback_router, prefix="/feedback", tags=["feedback"])
    app.include_router(admin_router, prefix="/admin", tags=["admin"])

    instrument_app(app)
    return app


app = create_app()
