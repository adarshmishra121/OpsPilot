"""Tool functions available to the OpsPilot agent."""

import json
import os
from functools import lru_cache
from typing import Any, Dict, List

import httpx

from opspilot.anomaly.infer import score_logs
from opspilot.rag.retriever import HybridRetriever
from opspilot.rag.index import FaissStore
from opspilot.rag.docstore import DocStore

INDEX_PATH = os.getenv("VECTOR_INDEX_PATH", "artifacts/vector_index")
META_PATH = os.path.join(INDEX_PATH, "meta.jsonl")
ALPHA = float(os.getenv("HYBRID_ALPHA", "0.6"))
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "mock")
OLLAMA_BASE = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b-instruct-q4_K_M")


@lru_cache
def _get_retriever() -> HybridRetriever:
    """Load retriever once (cached)."""
    store = FaissStore(INDEX_PATH).load()
    docstore = DocStore(META_PATH)
    return HybridRetriever(store, docstore, alpha=ALPHA)


def retrieve_runbooks(query: str, top_k: int = 6) -> List[Dict[str, Any]]:
    """Retrieve relevant runbook chunks using hybrid search."""
    retriever = _get_retriever()
    return retriever.retrieve(query, top_k=top_k)


def anomaly_score(log_lines: List[str]) -> Dict[str, Any]:
    """Score log lines for anomalies."""
    return score_logs(log_lines)


def call_llm(prompt: str) -> str:
    """Call the configured LLM provider (mock or Ollama)."""
    if LLM_PROVIDER == "mock":
        return _mock_response()

    resp = httpx.post(
        f"{OLLAMA_BASE}/api/generate",
        json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
        timeout=120.0,
    )
    resp.raise_for_status()
    return resp.json()["response"]


def _mock_response() -> str:
    """Return a deterministic mock response for testing."""
    return json.dumps({
        "summary": "Mock analysis: elevated error rates detected in log patterns.",
        "actions": [
            {
                "action": "Review disk usage and clear temporary files on affected nodes.",
                "evidence_doc_ids": ["runbook:mock:0"],
            }
        ],
        "verification_steps": ["Check disk usage with df -h", "Verify service health"],
        "fallback_plan": ["Escalate to on-call lead", "Roll back recent deployments"],
        "postmortem_markdown": "## Incident Summary\n\nMock postmortem for testing.",
    })
