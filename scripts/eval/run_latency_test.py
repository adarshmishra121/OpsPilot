"""Standalone latency smoke test — run locally when the API is up.

Usage:
    python scripts/eval/run_latency_test.py           # 20 requests, threshold 3s
    python scripts/eval/run_latency_test.py --n 50    # 50 requests
    python scripts/eval/run_latency_test.py --threshold 5000  # 5s threshold

Prerequisites:
    1. Ollama running: ollama serve
    2. Model pulled: ollama pull qwen2.5:7b
    3. API running: uvicorn opspilot.api.main:app --port 8000
       OR: docker compose up
"""

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

import httpx

API_URL = "http://localhost:8000/incident/analyze"

TEST_PAYLOADS = [
    {
        "incident_id": "LATENCY-001",
        "alert_title": "NodeFilesystemSpaceFillingUp",
        "service": "payment-api",
        "log_lines": ["ERROR disk at 95%", "WARN inode exhaustion approaching"],
    },
    {
        "incident_id": "LATENCY-002",
        "alert_title": "KubePodCrashLooping",
        "service": "order-service",
        "log_lines": ["ERROR OOMKilled", "WARN pod restarted 12 times"],
    },
    {
        "incident_id": "LATENCY-003",
        "alert_title": "CPUThrottlingHigh",
        "service": "analytics",
        "log_lines": ["WARN CPU throttling 85%", "INFO latency P99 2400ms"],
    },
    {
        "incident_id": "LATENCY-004",
        "alert_title": "etcdNoLeader",
        "service": "etcd",
        "log_lines": ["ERROR etcd cluster has no leader", "WARN quorum lost"],
    },
    {
        "incident_id": "LATENCY-005",
        "alert_title": "KubeAPIDown",
        "service": "kube-apiserver",
        "log_lines": ["ERROR connection refused :6443", "WARN apiserver unreachable"],
    },
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=20, help="Number of requests")
    parser.add_argument("--threshold", type=int, default=3000, help="P95 threshold ms")
    args = parser.parse_args()

    # Check API is reachable
    try:
        resp = httpx.get("http://localhost:8000/health", timeout=5)
        resp.raise_for_status()
        provider = resp.json().get("llm_provider", "unknown")
        print(f"✓ API reachable | LLM provider: {provider}")
    except Exception as e:
        print(f"✗ API not reachable: {e}")
        sys.exit(1)

    print(f"Running {args.n} requests, P95 threshold: {args.threshold}ms\n")

    latencies = []
    errors = 0

    for i in range(args.n):
        payload = TEST_PAYLOADS[i % len(TEST_PAYLOADS)]
        payload = {**payload, "incident_id": f"LATENCY-{i+1:03d}"}

        t0 = time.perf_counter()
        try:
            resp = httpx.post(API_URL, json=payload, timeout=120)
            resp.raise_for_status()
            ms = int((time.perf_counter() - t0) * 1000)
            latencies.append(ms)
            bar = "█" * min(40, ms // 100)
            print(f"  [{i+1:02d}/{args.n}] {ms:5d}ms {bar}")
        except Exception as e:
            ms = int((time.perf_counter() - t0) * 1000)
            errors += 1
            print(f"  [{i+1:02d}/{args.n}] ERROR after {ms}ms: {e}")

    if not latencies:
        print("\n✗ All requests failed")
        sys.exit(1)

    latencies.sort()
    p50 = int(statistics.median(latencies))
    p95 = latencies[max(0, int(len(latencies) * 0.95) - 1)]
    p99 = latencies[max(0, int(len(latencies) * 0.99) - 1)]
    mean = int(statistics.mean(latencies))

    print(f"\n{'='*50}")
    print(f"  LATENCY RESULTS ({len(latencies)} successful, {errors} errors)")
    print(f"{'='*50}")
    print(f"  Mean: {mean}ms")
    print(f"  P50:  {p50}ms")
    print(f"  P95:  {p95}ms  (threshold: {args.threshold}ms)")
    print(f"  P99:  {p99}ms")
    print(f"  Min:  {latencies[0]}ms  Max: {latencies[-1]}ms")

    passed = p95 <= args.threshold
    op = "<=" if passed else ">"
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"\n  {status}: P95 {p95}ms {op} {args.threshold}ms")
    print(f"{'='*50}")

    # Save metrics
    metrics = {
        "n_requests": len(latencies),
        "n_errors": errors,
        "mean_ms": mean,
        "p50_ms": p50,
        "p95_ms": p95,
        "p99_ms": p99,
        "threshold_ms": args.threshold,
        "passed": passed,
    }
    Path("artifacts").mkdir(exist_ok=True)
    with open("artifacts/latency_results.json", "w") as f:
        json.dump(metrics, f, indent=2)
    print("\n  Results saved to artifacts/latency_results.json")

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
