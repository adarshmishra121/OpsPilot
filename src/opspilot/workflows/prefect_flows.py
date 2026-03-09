"""Prefect flows for scheduled maintenance tasks."""

import subprocess
import structlog
from prefect import flow, task
from prefect.tasks import task_input_hash
from datetime import timedelta

log = structlog.get_logger()


@task(retries=2, retry_delay_seconds=30)
def download_data():
    """Pull latest runbooks and log data."""
    log.info("workflow.download.start")
    subprocess.run(["python", "scripts/data/download_all.py"], check=True)
    log.info("workflow.download.complete")


@task(retries=1, retry_delay_seconds=60)
def parse_logs():
    """Parse raw logs into templates."""
    log.info("workflow.parse.start")
    subprocess.run(["python", "scripts/features/parse_logs.py"], check=True)
    log.info("workflow.parse.complete")


@task(retries=1, retry_delay_seconds=60)
def build_features():
    """Convert templates to feature vectors."""
    log.info("workflow.features.start")
    subprocess.run(["python", "scripts/features/build_features.py"], check=True)
    log.info("workflow.features.complete")


@task(retries=1, retry_delay_seconds=60)
def train_model():
    """Train anomaly detection model."""
    log.info("workflow.train.start")
    subprocess.run(["python", "scripts/train/train_anomaly.py"], check=True)
    log.info("workflow.train.complete")


@task(retries=1, retry_delay_seconds=60)
def rebuild_index():
    """Rebuild FAISS vector index from runbooks."""
    log.info("workflow.index.start")
    subprocess.run(["python", "scripts/rag/build_index.py"], check=True)
    log.info("workflow.index.complete")


@task(retries=1)
def run_evaluation():
    """Run RAG evaluation against gold set."""
    log.info("workflow.eval.start")
    subprocess.run(["python", "scripts/eval/run_eval.py"], check=True)
    log.info("workflow.eval.complete")


@flow(name="nightly-reindex", log_prints=True)
def nightly_reindex():
    """Nightly flow: pull latest runbooks and rebuild the search index."""
    download_data()
    rebuild_index()
    run_evaluation()


@flow(name="weekly-retrain", log_prints=True)
def weekly_retrain():
    """Weekly flow: retrain anomaly model with latest log data."""
    download_data()
    parse_logs()
    build_features()
    train_model()


@flow(name="full-pipeline", log_prints=True)
def full_pipeline():
    """Full end-to-end pipeline: download → parse → train → index → eval."""
    download_data()
    parse_logs()
    build_features()
    train_model()
    rebuild_index()
    run_evaluation()


if __name__ == "__main__":
    full_pipeline()
