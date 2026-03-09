"""Data drift detection using Evidently for anomaly model monitoring."""

import json
from pathlib import Path

import pandas as pd
import structlog

try:
    from evidently.report import Report
    from evidently.metric_preset import DataDriftPreset
except ImportError:
    Report = None
    DataDriftPreset = None

log = structlog.get_logger()

REFERENCE_PATH = Path("artifacts/features.parquet")
REPORT_PATH = Path("artifacts/drift_report.json")


def detect_drift(current_df: pd.DataFrame | None = None) -> dict:
    """Compare current feature distribution against training reference.

    Args:
        current_df: Recent feature vectors. If None, uses last 20% of
                     reference data as a simulated current set.

    Returns:
        Dict with drift_detected (bool), drift_score, and per-feature details.
    """
    if Report is None:
        log.warning("drift.skip", reason="Evidently not installed. Run: poetry install --with workflows")
        return {"drift_detected": False, "reason": "evidently not installed"}

    if not REFERENCE_PATH.exists():
        log.warning("drift.skip", reason="Reference features not found")
        return {"drift_detected": False, "reason": "no reference data"}

    reference = pd.read_parquet(REFERENCE_PATH)
    log.info("drift.reference_loaded", shape=reference.shape)

    if current_df is None:
        # Simulate: split reference into "training" and "current"
        split = int(len(reference) * 0.8)
        current_df = reference.iloc[split:].reset_index(drop=True)
        reference = reference.iloc[:split].reset_index(drop=True)
        log.info("drift.simulated_split", ref_size=len(reference), cur_size=len(current_df))

    # Ensure matching columns
    common_cols = list(set(reference.columns) & set(current_df.columns))
    reference = reference[common_cols]
    current_df = current_df[common_cols]

    report = Report(metrics=[DataDriftPreset()])
    report.run(reference_data=reference, current_data=current_df)
    result = report.as_dict()

    # Extract summary
    drift_info = result.get("metrics", [{}])[0].get("result", {})
    summary = {
        "drift_detected": drift_info.get("dataset_drift", False),
        "drift_score": drift_info.get("share_of_drifted_columns", 0.0),
        "n_features": len(common_cols),
        "n_drifted": drift_info.get("number_of_drifted_columns", 0),
    }

    # Save report
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w") as f:
        json.dump(summary, f, indent=2)
    log.info("drift.complete", **summary)

    return summary


if __name__ == "__main__":
    result = detect_drift()
    print(json.dumps(result, indent=2))
