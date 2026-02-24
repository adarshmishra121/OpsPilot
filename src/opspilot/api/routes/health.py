"""Health-check endpoint for liveness and readiness probes."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health", tags=["health"])
def health():
    """Returns 200 if the API is up and accepting requests."""
    return {"status": "ok"}
