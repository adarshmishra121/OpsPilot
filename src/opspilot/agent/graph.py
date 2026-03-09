"""LangGraph state machine for incident analysis."""

import json
from typing import Any, Dict, List, TypedDict

from langgraph.graph import END, StateGraph

from opspilot.agent.prompts import SYSTEM_PROMPT
from opspilot.agent.safety import validate_grounded_actions
from opspilot.agent.tools import anomaly_score, call_llm, retrieve_runbooks


# ── State schema ──────────────────────────────────────────────


class AgentState(TypedDict):
    """Typed state container passed between graph nodes."""

    incident: Dict[str, Any]
    query: str
    log_lines: List[str]
    anomaly_result: Dict[str, Any]
    retrieved_chunks: List[Dict[str, Any]]
    draft_response: Dict[str, Any]
    final_response: Dict[str, Any]


# ── Node functions ────────────────────────────────────────────


def parse_node(state: AgentState) -> dict:
    """Extract query and log lines from the incident request."""
    inc = state["incident"]
    query = f"{inc.get('alert_title', '')} {inc.get('service', '')}".strip()
    return {"query": query, "log_lines": inc.get("log_lines", [])}


def anomaly_node(state: AgentState) -> dict:
    """Score log lines for anomalies."""
    if not state["log_lines"]:
        return {"anomaly_result": {"score": 0.0, "top_templates": []}}
    return {"anomaly_result": anomaly_score(state["log_lines"])}


def retrieve_node(state: AgentState) -> dict:
    """Retrieve relevant runbook chunks via hybrid search."""
    chunks = retrieve_runbooks(state["query"], top_k=6)
    return {"retrieved_chunks": chunks}


def draft_node(state: AgentState) -> dict:
    """Fill the system prompt with context and call the LLM."""
    context_text = "\n---\n".join(
        f"[{c['doc_id']}] {c.get('text', '')}" for c in state["retrieved_chunks"]
    )
    prompt = SYSTEM_PROMPT.format(
        anomaly_score=state["anomaly_result"].get("score", 0),
        top_templates=state["anomaly_result"].get("top_templates", []),
        retrieved_context=context_text,
        incident_details=json.dumps(state["incident"], default=str),
    )
    raw = call_llm(prompt)

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = {
            "summary": raw,
            "actions": [],
            "verification_steps": [],
            "fallback_plan": [],
            "postmortem_markdown": "",
        }

    return {"draft_response": parsed}


def validate_node(state: AgentState) -> dict:
    """Filter actions to only those grounded in retrieved evidence."""
    known_ids = {c["doc_id"] for c in state["retrieved_chunks"]}
    draft = state["draft_response"]

    grounded_actions = validate_grounded_actions(draft.get("actions", []), known_ids)
    draft["actions"] = grounded_actions
    return {"final_response": draft}


# ── Graph assembly ────────────────────────────────────────────


def build_graph() -> StateGraph:
    """Construct the LangGraph agent pipeline."""
    graph = StateGraph(AgentState)

    graph.add_node("parse", parse_node)
    graph.add_node("anomaly", anomaly_node)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("draft", draft_node)
    graph.add_node("validate", validate_node)

    graph.set_entry_point("parse")
    graph.add_edge("parse", "anomaly")
    graph.add_edge("anomaly", "retrieve")
    graph.add_edge("retrieve", "draft")
    graph.add_edge("draft", "validate")
    graph.add_edge("validate", END)

    return graph.compile()
