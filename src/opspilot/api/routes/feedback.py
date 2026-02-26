"""Feedback endpoint: persist human evaluations of analysis quality."""

from fastapi import APIRouter, Depends
from sqlmodel import Session

from opspilot.api.schemas import FeedbackRequest, FeedbackResponse
from opspilot.storage.db import get_session, init_db
from opspilot.storage.models import FeedbackRow

router = APIRouter()

# Ensure the feedback table exists on first import
init_db()


@router.post("/", response_model=FeedbackResponse)
def submit_feedback(
    req: FeedbackRequest,
    session: Session = Depends(get_session),
):
    """Save engineer feedback and return the persisted record ID."""
    row = FeedbackRow(
        incident_id=req.incident_id,
        helpful=req.helpful,
        tags=req.tags,
        comment=req.comment,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return FeedbackResponse(id=row.id, status="saved")
