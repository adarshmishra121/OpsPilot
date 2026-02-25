"""Convert parsed log templates into windowed feature vectors for anomaly detection."""

import json
import os
from collections import Counter

import pandas as pd

PARSED_LOGS = os.getenv("PARSED_LOGS", "data/processed/parsed_logs.parquet")
OUT = os.getenv("FEATURES_OUT", "data/features/features.parquet")
VOCAB_OUT = os.getenv("VOCAB_OUT", "artifacts/anomaly_vocab.json")
WINDOW_SIZE = int(os.getenv("WINDOW_SIZE", "500"))
TOP_K_TEMPLATES = int(os.getenv("TOP_K_TEMPLATES", "300"))


def main() -> None:
    """Build fixed-size feature vectors from template frequency counts per window."""
    df = pd.read_parquet(PARSED_LOGS)

    # Select top-K most frequent templates as the vocabulary
    vocab = df["cluster_id"].value_counts().head(TOP_K_TEMPLATES).index.tolist()
    vocab_set = set(vocab)

    # Slide a fixed-size window over the log stream
    windows = []
    for start in range(0, len(df), WINDOW_SIZE):
        chunk = df.iloc[start : start + WINDOW_SIZE]
        counts = Counter(c for c in chunk["cluster_id"] if c in vocab_set)
        vec = [counts.get(v, 0) for v in vocab]
        windows.append({"window_start": start, "vec": vec})

    out_df = pd.DataFrame(windows)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    out_df.to_parquet(OUT, index=False)

    # Save vocab for the online featurizer to use at inference time
    os.makedirs(os.path.dirname(VOCAB_OUT), exist_ok=True)
    with open(VOCAB_OUT, "w") as f:
        json.dump(vocab, f)

    print(f"Built {len(windows)} windows, vocab size {len(vocab)} → {OUT}")
    print(f"Saved vocab → {VOCAB_OUT}")


if __name__ == "__main__":
    main()
