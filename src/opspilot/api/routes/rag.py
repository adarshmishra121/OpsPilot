"""RAG search endpoint: hybrid retrieval over the runbook knowledge base."""

import os
from functools import lru_cache

from fastapi import APIRouter

from opspilot.api.schemas import RagSearchRequest, RagSearchResponse, RetrievedChunk
from opspilot.rag.docstore import DocStore
from opspilot.rag.index import FaissStore
from opspilot.rag.retriever import HybridRetriever

router = APIRouter()

INDEX_PATH = os.getenv("VECTOR_INDEX_PATH", "artifacts/vector_index")
META_PATH = os.path.join(INDEX_PATH, "meta.jsonl")
ALPHA = float(os.getenv("HYBRID_ALPHA", "0.6"))


@lru_cache
def _get_retriever() -> HybridRetriever:
    """Load FAISS index + docstore once, reuse across requests."""
    store = FaissStore(INDEX_PATH).load()
    docstore = DocStore(META_PATH)
    return HybridRetriever(store, docstore, alpha=ALPHA)


@router.post("/search", response_model=RagSearchResponse)
def rag_search(req: RagSearchRequest):
    """Search the runbook knowledge base with hybrid vector + keyword retrieval."""
    retriever = _get_retriever()
    hits = retriever.retrieve(req.query, top_k=req.top_k)

    chunks = [
        RetrievedChunk(
            doc_id=h["doc_id"],
            title=h.get("title", ""),
            text=h.get("text", ""),
            score=h["score"],
        )
        for h in hits
    ]
    return RagSearchResponse(chunks=chunks)
