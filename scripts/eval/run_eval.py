"""Evaluate RAG retrieval quality against a gold-standard set."""

import json
import sys
from pathlib import Path

from opspilot.rag.docstore import DocStore
from opspilot.rag.index import FaissStore
from opspilot.rag.retriever import HybridRetriever

GOLD_PATH = Path("data/eval/rag_gold.jsonl")
INDEX_PATH = "artifacts/vector_index"
META_PATH = f"{INDEX_PATH}/meta.jsonl"
TOP_K = 6


def load_gold(path: Path) -> list[dict]:
    """Load gold-standard evaluation queries."""
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def evaluate():
    """Run retrieval evaluation and print metrics."""
    gold = load_gold(GOLD_PATH)
    if not gold:
        print("❌ No evaluation queries found in", GOLD_PATH)
        sys.exit(1)

    store = FaissStore(INDEX_PATH).load()
    docstore = DocStore(META_PATH)
    retriever = HybridRetriever(store, docstore, alpha=0.6)

    reciprocal_ranks = []
    recalls = []

    for item in gold:
        query = item["query"]
        expected = set(item["expected_doc_ids"])

        results = retriever.retrieve(query, top_k=TOP_K)
        retrieved_ids = [r["doc_id"] for r in results]

        # MRR: 1 / rank of first hit
        rr = 0.0
        for rank, doc_id in enumerate(retrieved_ids, 1):
            if doc_id in expected:
                rr = 1.0 / rank
                break
        reciprocal_ranks.append(rr)

        # Recall@K: fraction of expected docs found
        hits = len(expected & set(retrieved_ids))
        recall = hits / len(expected) if expected else 0.0
        recalls.append(recall)

        print(f"  Query: {query[:60]:<60} MRR={rr:.3f}  Recall@{TOP_K}={recall:.3f}")

    mrr = sum(reciprocal_ranks) / len(reciprocal_ranks)
    avg_recall = sum(recalls) / len(recalls)

    print(f"\n{'=' * 60}")
    print(f"  MRR:        {mrr:.4f}")
    print(f"  Recall@{TOP_K}:  {avg_recall:.4f}")
    print(f"  Queries:    {len(gold)}")
    print(f"{'=' * 60}")

    # Write metrics for DVC tracking
    metrics = {
        "mrr": round(mrr, 4),
        "recall_at_k": round(avg_recall, 4),
        "k": TOP_K,
        "n_queries": len(gold),
    }
    Path("artifacts").mkdir(exist_ok=True)
    with open("artifacts/eval_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
    print("\n✅ Metrics saved to artifacts/eval_metrics.json")


if __name__ == "__main__":
    evaluate()
