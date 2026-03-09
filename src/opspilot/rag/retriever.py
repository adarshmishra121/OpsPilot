"""Hybrid retriever: fuses FAISS vector search with BM25 keyword search."""

from typing import Any, Dict, List

from opspilot.rag.bm25 import BM25Index
from opspilot.rag.docstore import DocStore
from opspilot.rag.index import FaissStore


class HybridRetriever:
    """Score-fusion retriever combining dense (vector) and sparse (BM25) signals.

    Final score = alpha * normalised_vector + (1 - alpha) * normalised_bm25.
    """

    def __init__(self, faiss_store: FaissStore, docstore: DocStore, alpha: float = 0.6):
        self.faiss = faiss_store
        self.docstore = docstore
        self.alpha = alpha

        texts, ids = self.docstore.all_texts_and_ids()
        self.bm25 = BM25Index(texts, ids)

    @staticmethod
    def _normalize(scores: Dict[str, float]) -> Dict[str, float]:
        """Min-max normalise scores to [0, 1]."""
        if not scores:
            return {}
        mx = max(scores.values()) or 1.0
        return {k: v / mx for k, v in scores.items()}

    def retrieve(self, query: str, top_k: int = 6) -> List[Dict[str, Any]]:
        """Run hybrid retrieval and return top-k fused results."""
        # Dense retrieval (FAISS)
        faiss_hits = self.faiss.search(query, top_k=top_k * 2)
        vec_scores = {h["doc_id"]: h["score"] for h in faiss_hits}

        # Sparse retrieval (BM25)
        bm25_scores = self.bm25.search(query, top_k=top_k * 2)

        # Normalise both score distributions
        vec_norm = self._normalize(vec_scores)
        bm25_norm = self._normalize(bm25_scores)

        # Fuse: alpha * vector + (1 - alpha) * bm25
        all_ids = set(vec_norm) | set(bm25_norm)
        fused = {}
        for doc_id in all_ids:
            fused[doc_id] = self.alpha * vec_norm.get(doc_id, 0.0) + (
                1 - self.alpha
            ) * bm25_norm.get(doc_id, 0.0)

        ranked = sorted(fused.items(), key=lambda x: x[1], reverse=True)[:top_k]

        results = []
        for doc_id, score in ranked:
            doc = self.docstore.get(doc_id) or {}
            results.append(
                {
                    "doc_id": doc_id,
                    "title": doc.get("title", ""),
                    "text": doc.get("text", ""),
                    "score": round(score, 4),
                }
            )
        return results
