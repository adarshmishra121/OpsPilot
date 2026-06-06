"""Tool functions available to the OpsPilot agent."""

import json
import os
from functools import lru_cache
from typing import Any, Dict, List

import httpx

from opspilot.anomaly.infer import score_logs
from opspilot.rag.docstore import DocStore
from opspilot.rag.index import FaissStore
from opspilot.rag.retriever import HybridRetriever

INDEX_PATH = os.getenv("VECTOR_INDEX_PATH", "artifacts/vector_index")
META_PATH = os.path.join(INDEX_PATH, "meta.jsonl")
ALPHA = float(os.getenv("HYBRID_ALPHA", "0.6"))
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "mock")
OLLAMA_BASE = os.getenv("OLLAMA_HOST", os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")


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


def call_llm(prompt: str, retries: int = 3, retry_delay: float = 30.0) -> str:
    """Call the configured LLM provider (mock or Ollama)."""
    if LLM_PROVIDER == "mock":
        return _mock_response()

    import time
    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            # Stream tokens to avoid hard response timeout on slow CPU inference
            chunks = []
            with httpx.stream(
                "POST",
                f"{OLLAMA_BASE}/api/generate",
                json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": True},
                timeout=httpx.Timeout(connect=10.0, read=1800.0, write=10.0, pool=10.0),
            ) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines():
                    if line:
                        data = json.loads(line)
                        chunks.append(data.get("response", ""))
                        if data.get("done"):
                            break
            return "".join(chunks)
        except (httpx.TimeoutException, httpx.HTTPStatusError) as exc:
            last_exc = exc
            if attempt < retries - 1:
                time.sleep(retry_delay)
    raise RuntimeError(f"Ollama call failed after {retries} attempts") from last_exc


def _mock_response() -> str:
    """Return a deterministic mock response for testing."""
    return json.dumps(
        {
            "summary": "Mock analysis: elevated error rates detected in log patterns.",
            "actions": [
                {
                    "action": "Review disk usage and clear temporary files on affected nodes.",
                    "evidence_doc_ids": ["runbook:mock:0"],
                }
            ],
            "verification_steps": [
                "Check disk usage with df -h",
                "Verify service health",
            ],
            "fallback_plan": [
                "Escalate to on-call lead",
                "Roll back recent deployments",
            ],
            "postmortem_markdown": "## Incident Summary\n\nMock postmortem for testing.",
        }
    )
