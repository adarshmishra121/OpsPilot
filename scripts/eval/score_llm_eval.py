"""Aggregate manual scores from llm_eval_results.json and print a report.

After running run_llm_eval.py and filling in scores in artifacts/llm_eval_results.json,
run this script:
    python scripts/eval/score_llm_eval.py
"""

import json
import statistics
from pathlib import Path

RESULTS_PATH = "artifacts/llm_eval_results.json"
DIMENSIONS = ["relevance", "correctness", "hallucination", "completeness"]


def main() -> None:
    if not Path(RESULTS_PATH).exists():
        print(f"Not found: {RESULTS_PATH}")
        print("Run scripts/eval/run_llm_eval.py first.")
        return

    with open(RESULTS_PATH) as f:
        results = json.load(f)

    scored = [r for r in results if all(r["scores"].get(d) for d in DIMENSIONS)]
    unscored = len(results) - len(scored)

    if not scored:
        print(f"No scored entries found. Open {RESULTS_PATH} and fill in scores (1-5).")
        return

    print(f"\n{'='*60}")
    print(f"  LLM EVALUATION REPORT — {len(scored)} incidents scored")
    if unscored:
        print(f"  ({unscored} unscored entries skipped)")
    print(f"{'='*60}\n")

    # Per-dimension averages
    dim_scores: dict = {d: [] for d in DIMENSIONS}
    latencies = []

    for r in scored:
        for d in DIMENSIONS:
            dim_scores[d].append(r["scores"][d])
        if r.get("latency_ms"):
            latencies.append(r["latency_ms"])

    print("  DIMENSION AVERAGES (1=worst, 5=best):")
    print(f"  {'Dimension':<20} {'Mean':>6} {'Median':>8} {'Min':>6} {'Max':>6}")
    print(f"  {'-'*50}")
    overall = []
    for d in DIMENSIONS:
        vals = dim_scores[d]
        mean = statistics.mean(vals)
        median = statistics.median(vals)
        overall.append(mean)
        print(f"  {d:<20} {mean:>6.2f} {median:>8.2f} {min(vals):>6} {max(vals):>6}")

    print(f"\n  OVERALL SCORE: {statistics.mean(overall):.2f} / 5.00")

    if latencies:
        print("\n  LATENCY:")
        latencies.sort()
        p50 = statistics.median(latencies)
        p95 = latencies[int(len(latencies) * 0.95)]
        print(f"  P50: {p50}ms  P95: {p95}ms  Max: {max(latencies)}ms")

    # Per-incident breakdown
    print("\n  PER-INCIDENT SCORES:")
    print(f"  {'ID':<12} {'Alert':<35} {'Rel':>4} {'Cor':>4} {'Hal':>4} {'Com':>4} {'Avg':>5}")
    print(f"  {'-'*70}")
    for r in scored:
        s = r["scores"]
        avg = statistics.mean([s[d] for d in DIMENSIONS])
        alert = r["alert_title"][:33]
        print(
            f"  {r['incident_id']:<12} {alert:<35} "
            f"{s['relevance']:>4} {s['correctness']:>4} "
            f"{s['hallucination']:>4} {s['completeness']:>4} {avg:>5.1f}"
        )

    # Save aggregate metrics
    agg = {
        "n_scored": len(scored),
        "overall": round(statistics.mean(overall), 3),
        "dimensions": {d: round(statistics.mean(dim_scores[d]), 3) for d in DIMENSIONS},
    }
    if latencies:
        agg["latency_p50_ms"] = int(statistics.median(latencies))
        agg["latency_p95_ms"] = int(latencies[int(len(latencies) * 0.95)])

    with open("artifacts/llm_eval_summary.json", "w") as f:
        json.dump(agg, f, indent=2)
    print("\n  Summary saved to artifacts/llm_eval_summary.json")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
