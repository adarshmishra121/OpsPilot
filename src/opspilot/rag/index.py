"""FAISS vector index: build, persist, and search over document embeddings."""

import json
import os
from typing import Any, Dict, List

import faiss

from opspilot.embeddings.encoder import Embedder


class FaissStore:
    """Manages a FAISS IndexFlatIP index with JSONL metadata sidecar."""

    def __init__(self, index_path: str, embed_model_name: str | None = None):
        self.index_path = index_path
        self.embedder = Embedder(embed_model_name)
        self.faiss_file = os.path.join(index_path, "index.faiss")
        self.meta_file = os.path.join(index_path, "meta.jsonl")
        self._index: faiss.IndexFlatIP | None = None
        self._meta: List[Dict[str, Any]] = []

    def load(self) -> "FaissStore":
        """Load an existing index from disk, or initialise an empty one."""
        if os.path.exists(self.faiss_file):
            self._index = faiss.read_index(self.faiss_file)
        else:
            self._index = faiss.IndexFlatIP(self.embedder.dim)

        if os.path.exists(self.meta_file):
            with open(self.meta_file, "r", encoding="utf-8") as f:
                self._meta = [json.loads(line) for line in f]
        return self

    def build(self, docs: List[Dict[str, Any]]) -> None:
        """Build the index from a list of documents.

        Each doc must have at least a 'text' key. All other keys are
        stored as metadata and returned on search.
        """
        os.makedirs(self.index_path, exist_ok=True)
        texts = [d["text"] for d in docs]
        vecs = self.embedder.encode(texts)

        self._index = faiss.IndexFlatIP(vecs.shape[1])
        self._index.add(vecs)
        faiss.write_index(self._index, self.faiss_file)

        with open(self.meta_file, "w", encoding="utf-8") as f:
            for doc in docs:
                f.write(json.dumps(doc, ensure_ascii=False) + "\n")
        self._meta = docs

    def search(self, query: str, top_k: int = 6) -> List[Dict[str, Any]]:
        """Return the top-k most similar documents for a query string."""
        if self._index is None or self._index.ntotal == 0:
            return []

        vec = self.embedder.encode([query])
        scores, indices = self._index.search(vec, min(top_k, self._index.ntotal))

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            entry = dict(self._meta[idx])
            entry["score"] = float(score)
            results.append(entry)
        return results
