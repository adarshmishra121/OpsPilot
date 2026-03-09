"""Incident analysis endpoint: orchestrates the full agent pipeline."""

from fastapi import APIRouter

from opspilot.agent.graph import build_graph
from opspilot.api.schemas import (
    AnomalyReport,
    IncidentAnalysisResponse,
    IncidentRequest,
    RecommendedAction,
    RetrievedChunk,
)

router = APIRouter()
agent = build_graph()


@router.post("/analyze", response_model=IncidentAnalysisResponse)
def analyze_incident(req: IncidentRequest):
    """Run the full OpsPilot agent pipeline on an incident."""
    result = agent.invoke({"incident": req.model_dump()})
    final = result["final_response"]

    return IncidentAnalysisResponse(
        summary=final.get("summary", ""),
        anomaly_report=AnomalyReport(**result.get("anomaly_result", {})),
        retrieved_context=[
            RetrievedChunk(**c) for c in result.get("retrieved_chunks", [])
        ],
        actions=[RecommendedAction(**a) for a in final.get("actions", [])],
        verification_steps=final.get("verification_steps", []),
        fallback_plan=final.get("fallback_plan", []),
        postmortem_markdown=final.get("postmortem_markdown", ""),
        trace={"nodes_executed": ["parse", "anomaly", "retrieve", "draft", "validate"]},
    )
