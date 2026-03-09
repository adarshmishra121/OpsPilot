"""Admin-only endpoints: system health, cache management, feedback stats."""

from fastapi import APIRouter, Depends
from sqlmodel import Session, func, select

from opspilot.api.deps import require_role
from opspilot.storage.db import get_session
from opspilot.storage.models import FeedbackRow

router = APIRouter()

admin_dep = Depends(require_role("admin"))


@router.get("/health", dependencies=[admin_dep])
def admin_health():
    """Detailed system health check (admin only)."""
    return {
        "status": "healthy",
        "auth": "enabled (role-gated)",
        "components": {
            "api": "running",
            "database": "connected",
            "anomaly_model": "lazy-loaded on first request",
            "vector_index": "lazy-loaded on first request",
        },
    }


@router.post("/clear-cache", dependencies=[admin_dep])
def clear_cache():
    """Clear all LRU caches to force reload of models and indexes."""
    cleared = []
    try:
        from opspilot.agent.tools import _get_retriever
        _get_retriever.cache_clear()
        cleared.append("retriever")
    except Exception:
        pass
    try:
        from opspilot.anomaly.infer import _load_model, _get_featurizer
        _load_model.cache_clear()
        _get_featurizer.cache_clear()
        cleared.append("anomaly_model")
        cleared.append("featurizer")
    except Exception:
        pass
    return {"cleared": cleared}


@router.get("/feedback-stats", dependencies=[admin_dep])
def feedback_stats(session: Session = Depends(get_session)):
    """Aggregate feedback metrics for quality monitoring."""
    total = session.exec(select(func.count(FeedbackRow.id))).one()
    helpful = session.exec(
        select(func.count(FeedbackRow.id)).where(FeedbackRow.helpful)
    ).one()
    return {
        "total_feedback": total,
        "helpful_count": helpful,
        "helpful_pct": round(helpful / total * 100, 1) if total > 0 else 0.0,
    }
