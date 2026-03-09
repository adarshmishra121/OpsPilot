"""Pydantic schemas for API request/response validation."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Shared models ─────────────────────────────────────────


class TimeRange(BaseModel):
    """ISO-8601 time window for scoping log queries."""

    start: str
    end: str


class RetrievedChunk(BaseModel):
    """Single chunk returned by the RAG retriever."""

    doc_id: str
    title: str
    text: str
    score: float


class RecommendedAction(BaseModel):
    """Agent-suggested mitigation step, grounded in retrieved evidence."""

    action: str
    evidence_doc_ids: List[str] = Field(default_factory=list)
    rationale: str = ""


class AnomalyReport(BaseModel):
    """Anomaly detection results from IsolationForest scoring."""

    score: float = 0.0
    top_templates: List[str] = Field(default_factory=list)
    details: Dict[str, Any] = Field(default_factory=dict)


# ── Incident ──────────────────────────────────────────────


class IncidentRequest(BaseModel):
    """Incoming incident payload submitted by on-call engineer or alerting system."""

    incident_id: str
    alert_title: str
    service: Optional[str] = None
    environment: Optional[str] = None
    log_lines: List[str] = Field(default_factory=list)
    time_range: Optional[TimeRange] = None
    user_notes: Optional[str] = None


class IncidentAnalysisResponse(BaseModel):
    """Full analysis output from the agent orchestrator."""

    summary: str
    anomaly_report: AnomalyReport
    retrieved_context: List[RetrievedChunk]
    actions: List[RecommendedAction]
    verification_steps: List[str]
    fallback_plan: List[str]
    postmortem_markdown: str
    trace: Dict[str, Any] = Field(default_factory=dict)


# ── RAG ───────────────────────────────────────────────────


class RagSearchRequest(BaseModel):
    """Query payload for hybrid retrieval (vector + BM25)."""

    query: str
    top_k: int = 6


class RagSearchResponse(BaseModel):
    """Ranked list of relevant runbook chunks."""

    chunks: List[RetrievedChunk]


# ── Anomaly ───────────────────────────────────────────────


class AnomalyScoreRequest(BaseModel):
    """Raw log lines to score for anomalies."""

    log_lines: List[str]


# ── Feedback ──────────────────────────────────────────────


class FeedbackRequest(BaseModel):
    """Human feedback on analysis quality, used to improve the system."""

    incident_id: str
    helpful: bool
    tags: List[str] = Field(default_factory=list)
    comment: Optional[str] = None


class FeedbackResponse(BaseModel):
    """Confirmation that feedback was persisted."""

    id: int
    status: str = "saved"
