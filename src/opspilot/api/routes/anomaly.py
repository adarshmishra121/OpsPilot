"""Anomaly scoring endpoint: IsolationForest over Drain3 templates."""

from fastapi import APIRouter

from opspilot.anomaly.infer import score_logs
from opspilot.api.schemas import AnomalyReport, AnomalyScoreRequest

router = APIRouter()


@router.post("/score", response_model=AnomalyReport)
def anomaly_score(req: AnomalyScoreRequest):
    """Score raw log lines for anomalies using the trained IsolationForest model."""
    result = score_logs(req.log_lines)
    return AnomalyReport(**result)
