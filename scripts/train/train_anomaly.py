"""Train IsolationForest on log feature vectors and log results to MLflow."""


import os
import time

import joblib
import mlflow
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

FEATURES = os.getenv("FEATURES_PATH", "data/features/features.parquet")
MODEL_OUT = os.getenv("MODEL_OUT", "models/anomaly_model.pkl")
N_ESTIMATORS = int(os.getenv("N_ESTIMATORS", "150"))
CONTAMINATION = float(os.getenv("CONTAMINATION", "0.01"))


def main() -> None:
    """Train IsolationForest and log experiment to MLflow."""
    df = pd.read_parquet(FEATURES)
    X = np.vstack(df["vec"].values)

    mlflow.set_experiment("opspilot-anomaly")
    with mlflow.start_run(run_name="isolation-forest"):
        mlflow.log_params({
            "n_estimators": N_ESTIMATORS,
            "contamination": CONTAMINATION,
            "n_samples": len(X),
            "n_features": X.shape[1],
        })

        t0 = time.time()
        model = IsolationForest(
            n_estimators=N_ESTIMATORS,
            contamination=CONTAMINATION,
            random_state=42,
            n_jobs=-1,
        )
        model.fit(X)
        train_time = time.time() - t0

        scores = model.decision_function(X)
        mlflow.log_metrics({
            "train_time_s": round(train_time, 2),
            "mean_score": float(np.mean(scores)),
            "std_score": float(np.std(scores)),
            "anomaly_pct": float((model.predict(X) == -1).mean()),
        })

        os.makedirs(os.path.dirname(MODEL_OUT), exist_ok=True)
        joblib.dump(model, MODEL_OUT)
        mlflow.log_artifact(MODEL_OUT)

        print(f"Trained IsolationForest in {train_time:.1f}s → {MODEL_OUT}")
        print(f"Anomaly %: {(model.predict(X) == -1).mean():.2%}")


if __name__ == "__main__":
    main()
