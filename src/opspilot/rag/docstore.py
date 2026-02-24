"""JSONL-backed document store keyed by doc_id."""

import json
import os
from typing import Any, Dict, List, Tuple


class DocStore:
    """Stores and retrieves document metadata from a JSONL file."""

    def __init__(self, path: str):
        self.path = path
        self._docs: Dict[str, Dict[str, Any]] = {}
        if os.path.exists(path):
            self._load()

    def _load(self) -> None:
        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                doc = json.loads(line)
                self._docs[doc["doc_id"]] = doc

    def get(self, doc_id: str) -> Dict[str, Any] | None:
        """Look up a single document by its ID."""
        return self._docs.get(doc_id)

    def all_texts_and_ids(self) -> Tuple[List[str], List[str]]:
        """Return parallel lists of (texts, doc_ids) for BM25 indexing."""
        texts, ids = [], []
        for doc_id, doc in self._docs.items():
            texts.append(doc.get("text", ""))
            ids.append(doc_id)
        return texts, ids

    def count(self) -> int:
        return len(self._docs)
