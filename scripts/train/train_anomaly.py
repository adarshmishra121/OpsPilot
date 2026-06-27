"""Train IsolationForest on log feature vectors and log results to MLflow.

If HDFS anomaly labels are available (data/raw/hdfs/anomaly_label.csv),
performs a proper 80/20 train/test split and computes F1/precision/recall.
Otherwise falls back to unsupervised training metrics only.
"""

import json
import os
import time

import joblib
import mlflow
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import classification_report, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split

FEATURES = os.getenv("FEATURES_PATH", "data/features/features.parquet")
MODEL_OUT = os.getenv("MODEL_OUT", "models/anomaly_model.pkl")
LABELS_PATH = os.getenv("LABELS_PATH", "data/raw/hdfs/anomaly_label.csv")
N_ESTIMATORS = int(os.getenv("N_ESTIMATORS", "150"))
CONTAMINATION = float(os.getenv("CONTAMINATION", "0.01"))


def load_labels(df: pd.DataFrame) -> np.ndarray | None:
    """Try to load HDFS block-level anomaly labels and align to feature windows.

    The HDFS anomaly_label.csv has columns: BlockId, Label (Normal/Anomaly).
    We map each feature window to a label based on which block IDs appear in
    the log lines for that window.
    Returns a binary array (1=anomaly, 0=normal) aligned to df rows, or None.
    """
    if not os.path.exists(LABELS_PATH):
        return None

    label_df = pd.read_csv(LABELS_PATH)
    if "Label" not in label_df.columns:
        return None

    # Build set of anomalous block IDs
    anomaly_blocks = set(
        label_df[label_df["Label"] == "Anomaly"]["BlockId"].astype(str).tolist()
    )

    # Each feature window covers log lines [window_start, window_start+window_size)
    # The parsed_logs parquet has block IDs embedded in log lines — extract them
    parsed_path = os.getenv("PARSED_LOGS_PATH", "data/processed/parsed_logs.parquet")
    if not os.path.exists(parsed_path):
        print("⚠ parsed_logs.parquet not found — skipping label alignment")
        return None

    parsed = pd.read_parquet(parsed_path)
    window_size = int(os.getenv("WINDOW_SIZE", "500"))

    labels = []
    for _, row in df.iterrows():
        start = int(row["window_start"])
        window_lines = parsed.iloc[start : start + window_size]["line"].tolist()
        # Check if any line in this window references an anomalous block
        has_anomaly = any(
            any(blk in line for blk in anomaly_blocks) for line in window_lines
        )
        labels.append(1 if has_anomaly else 0)

    return np.array(labels)


def main() -> None:
    """Train IsolationForest and log experiment to MLflow."""
    df = pd.read_parquet(FEATURES)
    X = np.vstack(df["vec"].values)

    print(f"Loaded {len(X)} feature windows, {X.shape[1]} features each")

    # Try to get labels for supervised evaluation
    y = load_labels(df)
    has_labels = y is not None and len(np.unique(y)) > 1

    if has_labels:
        print(f"Labels loaded — {y.sum()} anomalous / {(y == 0).sum()} normal windows")
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        print(f"Train: {len(X_train)} windows | Test: {len(X_test)} windows")
    else:
        print("No labels found — training unsupervised (no F1/precision/recall)")
        X_train = X

    mlflow.set_experiment("opspilot-anomaly")
    with mlflow.start_run(run_name="isolation-forest"):
        mlflow.log_params(
            {
                "n_estimators": N_ESTIMATORS,
                "contamination": CONTAMINATION,
                "n_samples": len(X_train),
                "n_features": X.shape[1],
                "supervised_eval": has_labels,
            }
        )

        t0 = time.time()
        model = IsolationForest(
            n_estimators=N_ESTIMATORS,
            contamination=CONTAMINATION,
            random_state=42,
            n_jobs=-1,
        )
        model.fit(X_train)
        train_time = time.time() - t0

        train_scores = model.decision_function(X_train)
        metrics: dict = {
            "train_time_s": round(train_time, 2),
            "mean_score": float(np.mean(train_scores)),
            "std_score": float(np.std(train_scores)),
            "anomaly_pct_train": float((model.predict(X_train) == -1).mean()),
        }

        if has_labels:
            # IsolationForest: predict returns 1=normal, -1=anomaly
            # Map to binary: 1=anomaly, 0=normal to match our labels
            y_pred = (model.predict(X_test) == -1).astype(int)

            f1 = f1_score(y_test, y_pred, zero_division=0)
            precision = precision_score(y_test, y_pred, zero_division=0)
            recall = recall_score(y_test, y_pred, zero_division=0)

            metrics.update(
                {
                    "f1": round(float(f1), 4),
                    "precision": round(float(precision), 4),
                    "recall": round(float(recall), 4),
                    "test_anomaly_pct": float(y_test.mean()),
                }
            )

            print("\n" + "=" * 50)
            print("  EVALUATION ON TEST SET (20%)")
            print("=" * 50)
            print(classification_report(y_test, y_pred, target_names=["Normal", "Anomaly"]))
            print(f"  F1:        {f1:.4f}")
            print(f"  Precision: {precision:.4f}")
            print(f"  Recall:    {recall:.4f}")
            print("=" * 50)

        mlflow.log_metrics(metrics)

        os.makedirs("artifacts", exist_ok=True)
        with open("artifacts/train_metrics.json", "w") as f:
            json.dump(metrics, f, indent=2)

        os.makedirs(os.path.dirname(MODEL_OUT), exist_ok=True)
        joblib.dump(model, MODEL_OUT)
        mlflow.log_artifact(MODEL_OUT)

        print(f"\nTrained IsolationForest in {train_time:.1f}s → {MODEL_OUT}")
        print(f"Train anomaly %: {(model.predict(X_train) == -1).mean():.2%}")
        print("Metrics saved to artifacts/train_metrics.json")


if __name__ == "__main__":
    main()
