"""Download public datasets: Loghub HDFS logs and Prometheus Operator Runbooks."""

import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXTERNAL = ROOT / "external"
RAW = ROOT / "data" / "raw"


def run(cmd: str) -> None:
    """Run a shell command, raising on failure."""
    subprocess.run(cmd, shell=True, check=True)


def ensure_repo(url: str, dst: Path) -> None:
    """Clone a repo (shallow) or pull if it already exists."""
    if dst.exists() and (dst / ".git").exists():
        run(f"git -C {dst} pull --ff-only")
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        run(f"git clone --depth 1 {url} {dst}")


def copy_loghub_subset(loghub_path: Path) -> None:
    """Copy HDFS log file from the cloned loghub repo into data/raw/."""
    hdfs_dir = RAW / "hdfs"
    hdfs_dir.mkdir(parents=True, exist_ok=True)

    # Loghub stores logs in <Dataset>/<Dataset>.log format
    src = loghub_path / "HDFS" / "HDFS.log"
    if not src.exists():
        # Some loghub versions use HDFS_1/ or HDFS_v1/
        candidates = list(loghub_path.glob("HDFS*/*.log"))
        if candidates:
            src = candidates[0]
        else:
            print(f"WARNING: HDFS.log not found in {loghub_path}")
            return

    dst = hdfs_dir / "HDFS.log"
    if not dst.exists():
        shutil.copy2(src, dst)
        print(f"Copied {src} → {dst}")
    else:
        print(f"Already exists: {dst}")


def copy_runbooks(runbooks_path: Path) -> None:
    """Copy runbook markdown files into data/raw/runbooks/."""
    out = RAW / "runbooks"
    out.mkdir(parents=True, exist_ok=True)

    # Runbooks are in content/runbooks/*.md
    md_dir = runbooks_path / "content" / "runbooks"
    if not md_dir.exists():
        md_dir = runbooks_path
    count = 0
    for f in md_dir.rglob("*.md"):
        dst = out / f.name
        if not dst.exists():
            shutil.copy2(f, dst)
            count += 1
    print(f"Copied {count} runbook files → {out}")


def main() -> None:
    """Download and prepare all datasets."""
    print("=== Downloading Loghub ===")
    loghub = EXTERNAL / "loghub"
    ensure_repo("https://github.com/logpai/loghub.git", loghub)
    copy_loghub_subset(loghub)

    print("\n=== Downloading Prometheus Operator Runbooks ===")
    runbooks = EXTERNAL / "runbooks"
    ensure_repo("https://github.com/prometheus-operator/runbooks.git", runbooks)
    copy_runbooks(runbooks)

    print("\nDone. Raw data is in:", RAW)


if __name__ == "__main__":
    main()
