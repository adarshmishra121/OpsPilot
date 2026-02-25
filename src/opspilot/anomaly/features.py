"""Online log featurizer: Drain3 template extraction + fixed-vocab frequency vector."""

import json
import os
from collections import Counter
from typing import List, Tuple

import numpy as np
from drain3 import TemplateMiner
from drain3.template_miner_config import TemplateMinerConfig


class LogFeaturizer:
    """Converts raw log lines into a fixed-size feature vector at inference time.

    Uses the same vocabulary built during offline training to ensure
    feature positions are consistent with the trained model.
    """

    def __init__(self, vocab_path: str | None = None):
        vocab_path = vocab_path or os.getenv(
            "VOCAB_PATH", "artifacts/anomaly_vocab.json"
        )
        with open(vocab_path, "r") as f:
            self.vocab: List[int] = json.load(f)
        self._vocab_set = set(self.vocab)

        cfg = TemplateMinerConfig()
        cfg.load(os.getenv("DRAIN3_CONFIG", "drain3.ini"))
        self.miner = TemplateMiner(config=cfg)

    def featurize(self, lines: List[str]) -> Tuple[np.ndarray, List[str]]:
        """Parse log lines and return (feature_vector, top_templates).

        Returns a 1-D array of template counts aligned with the training
        vocabulary, plus the most common templates for display.
        """
        cluster_ids = []
        templates = []
        for line in lines:
            result = self.miner.add_log_message(line.strip())
            cluster_ids.append(result["cluster_id"])
            templates.append(result["template_mined"])

        counts = Counter(c for c in cluster_ids if c in self._vocab_set)
        vec = np.array([counts.get(v, 0) for v in self.vocab], dtype=np.float32)

        # Top templates for human-readable output
        template_counts = Counter(templates)
        top = [t for t, _ in template_counts.most_common(5)]

        return vec, top
