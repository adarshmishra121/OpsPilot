"""Anomaly scoring using a trained IsolationForest model."""

import os
from functools import lru_cache
from typing import Any, Dict, List

import joblib
import numpy as np

from opspilot.anomaly.features import LogFeaturizer


@lru_cache
def _load_model():
    """Load the trained IsolationForest model from disk (cached)."""
    path = os.getenv("ANOMALY_MODEL_PATH", "models/anomaly_model.pkl")
    return joblib.load(path)


@lru_cache
def _get_featurizer() -> LogFeaturizer:
    """Load the log featurizer with shared vocabulary (cached)."""
    return LogFeaturizer()


def score_logs(log_lines: List[str]) -> Dict[str, Any]:
    """Score a batch of log lines for anomalies.

    Returns a dict with anomaly score (0-1), top templates,
    and raw model details for transparency.
    """
    featurizer = _get_featurizer()
    vec, top_templates = featurizer.featurize(log_lines)

    model = _load_model()
    raw = float(model.decision_function(vec.reshape(1, -1))[0])

    # Normalise: sklearn returns negative=anomalous, flip to 0-1
    score = max(0.0, min(1.0, 0.5 - raw))

    return {
        "score": round(score, 4),
        "top_templates": top_templates,
        "details": {
            "raw_isolation_score": round(raw, 4),
            "n_lines": len(log_lines),
            "n_features": len(vec),
        },
    }
