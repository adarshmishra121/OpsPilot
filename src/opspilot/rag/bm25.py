"""BM25 lexical retrieval index for keyword-based document search."""

from typing import Dict, List

from rank_bm25 import BM25Okapi


class BM25Index:
    """Thin wrapper around BM25Okapi for ranked keyword retrieval."""

    def __init__(self, texts: List[str], doc_ids: List[str]):
        self._doc_ids = doc_ids
        tokenised = [t.lower().split() for t in texts]
        self._bm25 = BM25Okapi(tokenised)

    def search(self, query: str, top_k: int = 6) -> Dict[str, float]:
        """Return {doc_id: score} for the top-k keyword matches."""
        tokens = query.lower().split()
        scores = self._bm25.get_scores(tokens)

        ranked = sorted(
            zip(self._doc_ids, scores), key=lambda x: x[1], reverse=True
        )
        return {doc_id: float(s) for doc_id, s in ranked[:top_k] if s > 0}
