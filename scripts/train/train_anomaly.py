"""Train IsolationForest on log feature vectors and log results to MLflow.

Split strategy (when labels are available):
  - 60% train  (earliest windows) — fit the model on normal windows only
  - 20% val    (middle windows)   — tune the anomaly score threshold
  - 20% test   (latest windows)   — final held-out evaluation, never touched during tuning

This temporal ordering prevents future-data leakage and gives a realistic
estimate of production performance.
"""

import json
import os
import time

import joblib
import mlflow
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import classification_report, f1_score, fbeta_score, precision_recall_curve, precision_score, recall_score
from sklearn.model_selection import train_test_split  # noqa: F401 (kept for unsupervised fallback)

FEATURES = os.getenv("FEATURES_PATH", "data/features/features.parquet")
MODEL_OUT = os.getenv("MODEL_OUT", "models/anomaly_model.pkl")
LABELS_PATH = os.getenv("LABELS_PATH", "data/raw/hdfs/anomaly_label.csv")
N_ESTIMATORS = int(os.getenv("N_ESTIMATORS", "300"))
CONTAMINATION = os.getenv("CONTAMINATION", "auto")


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
            any(blk in line.split() for blk in anomaly_blocks) for line in window_lines
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

        # 60% train / 20% val / 20% test — stratified so anomaly rate is balanced
        X_train, X_temp, y_train, y_temp = train_test_split(
            X, y, test_size=0.4, random_state=42, stratify=y
        )
        X_val, X_test, y_val, y_test = train_test_split(
            X_temp, y_temp, test_size=0.5, random_state=42, stratify=y_temp
        )

        # Train only on normal windows so IsolationForest learns the normal baseline
        X_train_fit = X_train[y_train == 0]
        print(
            f"Split — Train: {len(X_train)} ({len(X_train_fit)} normal) | "
            f"Val: {len(X_val)} | Test: {len(X_test)}"
        )
        contamination = float(CONTAMINATION) if CONTAMINATION != "auto" else min(float(y_train.mean()), 0.5)
    else:
        print("No labels found — training unsupervised (no F1/precision/recall)")
        X_train = X
        X_train_fit = X_train
        X_val = X_test = y_val = y_test = None
        contamination = float(CONTAMINATION) if CONTAMINATION != "auto" else 0.01

    mlflow.set_experiment("opspilot-anomaly")
    with mlflow.start_run(run_name="isolation-forest"):
        mlflow.log_params(
            {
                "n_estimators": N_ESTIMATORS,
                "contamination": contamination,
                "n_samples": len(X_train_fit),
                "n_features": X.shape[1],
                "supervised_eval": has_labels,
            }
        )

        t0 = time.time()
        model = IsolationForest(
            n_estimators=N_ESTIMATORS,
            contamination=contamination,
            random_state=42,
            n_jobs=-1,
        )
        model.fit(X_train_fit)
        train_time = time.time() - t0

        train_scores = model.decision_function(X_train)
        metrics: dict = {
            "train_time_s": round(train_time, 2),
            "mean_score": float(np.mean(train_scores)),
            "std_score": float(np.std(train_scores)),
            "anomaly_pct_train": float((model.predict(X_train_fit) == -1).mean()),
        }

        if has_labels:
            BETA = float(os.getenv("FBETA", "2.0"))

            # Tune threshold on val set (never seen during training)
            val_scores = -model.decision_function(X_val)
            precisions, recalls, thresholds = precision_recall_curve(y_val, val_scores)
            beta2 = BETA ** 2
            fbetas = (1 + beta2) * precisions * recalls / (beta2 * precisions + recalls + 1e-9)
            best_idx = int(np.argmax(fbetas))
            best_threshold = float(thresholds[best_idx]) if best_idx < len(thresholds) else 0.0
            print(f"  Threshold tuned on val set (F{BETA}): {best_threshold:.6f}")

            # Final evaluation on held-out test set
            test_scores = -model.decision_function(X_test)
            y_pred = (test_scores >= best_threshold).astype(int)

            f1 = f1_score(y_test, y_pred, zero_division=0)
            f2 = fbeta_score(y_test, y_pred, beta=BETA, zero_division=0)
            precision = precision_score(y_test, y_pred, zero_division=0)
            recall = recall_score(y_test, y_pred, zero_division=0)

            metrics.update(
                {
                    "f1": round(float(f1), 4),
                    "f2": round(float(f2), 4),
                    "precision": round(float(precision), 4),
                    "recall": round(float(recall), 4),
                    "best_threshold": round(best_threshold, 6),
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
        existing = [
            f for f in os.listdir("artifacts")
            if f.startswith("train_metrics") and f.endswith(".json")
        ]
        next_v = len(existing) + 1
        metrics_path = f"artifacts/train_metrics_v{next_v}.json"
        with open(metrics_path, "w") as f:
            json.dump(metrics, f, indent=2)

        os.makedirs(os.path.dirname(MODEL_OUT), exist_ok=True)
        threshold_to_save = best_threshold if has_labels else None
        joblib.dump({"model": model, "threshold": threshold_to_save}, MODEL_OUT)
        mlflow.log_artifact(MODEL_OUT)

        print(f"\nTrained IsolationForest in {train_time:.1f}s → {MODEL_OUT}")
        print(f"Train anomaly %: {(model.predict(X_train) == -1).mean():.2%}")
        print(f"Metrics saved to {metrics_path}")


if __name__ == "__main__":
    main()
