"""Parse raw HDFS logs with Drain3 to extract log templates."""

import os

import pandas as pd
from drain3 import TemplateMiner
from drain3.template_miner_config import TemplateMinerConfig

LOG_FILE = os.getenv("LOG_FILE", "data/raw/hdfs/HDFS.log")
OUT = os.getenv("PARSED_LOGS_OUT", "data/processed/parsed_logs.parquet")
MAX_LINES = int(os.getenv("MAX_LOG_LINES", "500000"))


def main() -> None:
    """Run Drain3 template mining on raw log lines."""
    cfg = TemplateMinerConfig()
    cfg.load("drain3.ini")
    miner = TemplateMiner(config=cfg)

    records = []
    with open(LOG_FILE, "r", encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f):
            if i >= MAX_LINES:
                break
            line = line.strip()
            if not line:
                continue
            result = miner.add_log_message(line)
            records.append({
                "line": line,
                "cluster_id": result["cluster_id"],
                "template": result["template_mined"],
            })

    df = pd.DataFrame(records)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    df.to_parquet(OUT, index=False)

    n_templates = df["cluster_id"].nunique()
    print(f"Parsed {len(df)} lines → {n_templates} templates → {OUT}")


if __name__ == "__main__":
    main()
