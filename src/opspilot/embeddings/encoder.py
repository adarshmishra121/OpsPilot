"""Text embedding encoder using SentenceTransformers with disk caching."""

import hashlib
import os
from typing import List

import numpy as np
from diskcache import Cache
from sentence_transformers import SentenceTransformer

_CACHE_DIR = os.getenv("EMBED_CACHE_DIR", ".cache/embeddings")


class Embedder:
    """Encodes text into dense vectors using a SentenceTransformer model.

    Embeddings are cached to disk so repeated calls for the same text
    are nearly free. Vectors are L2-normalised for cosine similarity
    via FAISS IndexFlatIP.
    """

    def __init__(self, model_name: str | None = None):
        name = model_name or os.getenv(
            "EMBED_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2"
        )
        self.model = SentenceTransformer(name)
        self.dim = self.model.get_sentence_embedding_dimension()
        self._cache = Cache(_CACHE_DIR)

    def _cache_key(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def encode(self, texts: List[str]) -> np.ndarray:
        """Encode a batch of texts, returning an (N, dim) float32 array."""
        results = []
        to_encode, to_encode_idx = [], []

        for i, t in enumerate(texts):
            key = self._cache_key(t)
            cached = self._cache.get(key)
            if cached is not None:
                results.append((i, cached))
            else:
                to_encode.append(t)
                to_encode_idx.append(i)

        if to_encode:
            vecs = self.model.encode(
                to_encode, normalize_embeddings=True, show_progress_bar=False
            )
            for idx, vec in zip(to_encode_idx, vecs):
                v = vec.astype(np.float32)
                self._cache.set(self._cache_key(texts[idx]), v)
                results.append((idx, v))

        results.sort(key=lambda x: x[0])
        return np.vstack([v for _, v in results])
