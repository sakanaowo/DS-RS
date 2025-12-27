"""
Evaluation Metrics for Information Retrieval

Implements standard IR metrics:
- Precision@K: What fraction of top-K results are relevant?
- Recall@K: What fraction of all relevant items are in top-K?
- NDCG@K: Normalized Discounted Cumulative Gain (position-aware)
- MRR: Mean Reciprocal Rank (first relevant result position)
- MAP: Mean Average Precision

These metrics help evaluate the quality of search results.
"""

from typing import List, Dict, Tuple
import numpy as np
import pandas as pd


def precision_at_k(relevant: List[int], k: int) -> float:
    """
    Calculate Precision@K.

    Precision@K = (# relevant items in top-K) / K

    Args:
        relevant: List of relevance labels (1=relevant, 0=not) for ranked results
        k: Cutoff position

    Returns:
        Precision@K score (0.0 to 1.0)

    Example:
        relevant = [1, 1, 0, 1, 0, 0, 1, 0, 0, 0]
        precision_at_k(relevant, 5) = 3/5 = 0.6
    """
    if k <= 0 or len(relevant) == 0:
        return 0.0

    # Take top-K
    top_k = relevant[:k]

    # Count relevant
    num_relevant = sum(top_k)

    return num_relevant / k


def recall_at_k(relevant: List[int], k: int) -> float:
    """
    Calculate Recall@K.

    Recall@K = (# relevant items in top-K) / (total # relevant items)

    Args:
        relevant: List of relevance labels (1=relevant, 0=not) for ranked results
        k: Cutoff position

    Returns:
        Recall@K score (0.0 to 1.0)

    Example:
        relevant = [1, 1, 0, 1, 0, 0, 1, 0, 0, 0]
        recall_at_k(relevant, 5) = 3/4 = 0.75 (3 found out of 4 total)
    """
    if len(relevant) == 0:
        return 0.0

    total_relevant = sum(relevant)

    if total_relevant == 0:
        return 0.0

    # Take top-K
    top_k = relevant[:k]

    # Count relevant in top-K
    num_relevant_in_k = sum(top_k)

    return num_relevant_in_k / total_relevant


def dcg_at_k(relevant: List[int], k: int) -> float:
    """
    Calculate Discounted Cumulative Gain at K.

    DCG@K = Σ(rel_i / log2(i+1)) for i=1 to K

    Higher-ranked relevant items contribute more to the score.

    Args:
        relevant: List of relevance labels for ranked results
        k: Cutoff position

    Returns:
        DCG@K score
    """
    if k <= 0 or len(relevant) == 0:
        return 0.0

    # Take top-K
    top_k = relevant[:k]

    # Calculate DCG
    dcg = 0.0
    for i, rel in enumerate(top_k, start=1):
        dcg += rel / np.log2(i + 1)

    return dcg


def ndcg_at_k(relevant: List[int], k: int) -> float:
    """
    Calculate Normalized Discounted Cumulative Gain at K.

    NDCG@K = DCG@K / IDCG@K

    where IDCG@K is the DCG of the ideal ranking (all relevant first).

    Args:
        relevant: List of relevance labels for ranked results
        k: Cutoff position

    Returns:
        NDCG@K score (0.0 to 1.0)

    Example:
        relevant = [1, 0, 1, 0, 1]
        # Actual DCG: 1/log2(2) + 1/log2(4) + 1/log2(6) = 1.0 + 0.5 + 0.387 = 1.887
        # Ideal DCG: 1/log2(2) + 1/log2(3) + 1/log2(4) = 1.0 + 0.631 + 0.5 = 2.131
        # NDCG = 1.887 / 2.131 = 0.885
    """
    if k <= 0 or len(relevant) == 0:
        return 0.0

    # Calculate actual DCG
    actual_dcg = dcg_at_k(relevant, k)

    # Calculate ideal DCG (sorted descending)
    ideal_relevant = sorted(relevant, reverse=True)
    ideal_dcg = dcg_at_k(ideal_relevant, k)

    if ideal_dcg == 0.0:
        return 0.0

    return actual_dcg / ideal_dcg


def reciprocal_rank(relevant: List[int]) -> float:
    """
    Calculate Reciprocal Rank.

    RR = 1 / rank_of_first_relevant_item

    Args:
        relevant: List of relevance labels for ranked results

    Returns:
        Reciprocal Rank (0.0 to 1.0)

    Example:
        relevant = [0, 0, 1, 0, 1]
        RR = 1/3 = 0.333 (first relevant at position 3)
    """
    for i, rel in enumerate(relevant, start=1):
        if rel == 1:
            return 1.0 / i
    return 0.0


def average_precision(relevant: List[int]) -> float:
    """
    Calculate Average Precision.

    AP = (Σ P(k) × rel(k)) / # relevant items

    where P(k) is precision at position k, rel(k) is relevance at k.

    Args:
        relevant: List of relevance labels for ranked results

    Returns:
        Average Precision (0.0 to 1.0)

    Example:
        relevant = [1, 0, 1, 1, 0]
        P(1) = 1/1 = 1.0, rel(1) = 1 → 1.0
        P(2) = 1/2 = 0.5, rel(2) = 0 → 0.0
        P(3) = 2/3 = 0.67, rel(3) = 1 → 0.67
        P(4) = 3/4 = 0.75, rel(4) = 1 → 0.75
        P(5) = 3/5 = 0.6, rel(5) = 0 → 0.0
        AP = (1.0 + 0.67 + 0.75) / 3 = 0.807
    """
    total_relevant = sum(relevant)

    if total_relevant == 0:
        return 0.0

    ap_sum = 0.0
    num_relevant_so_far = 0

    for i, rel in enumerate(relevant, start=1):
        if rel == 1:
            num_relevant_so_far += 1
            precision_at_i = num_relevant_so_far / i
            ap_sum += precision_at_i

    return ap_sum / total_relevant


def calculate_metrics_for_query(
    relevant: List[int], k_values: List[int] = [1, 3, 5, 10]
) -> Dict[str, float]:
    """
    Calculate all metrics for a single query.

    Args:
        relevant: List of relevance labels for ranked results
        k_values: List of K values to evaluate

    Returns:
        Dictionary of metric names to scores
    """
    metrics = {}

    # Precision@K
    for k in k_values:
        metrics[f"precision@{k}"] = precision_at_k(relevant, k)

    # Recall@K
    for k in k_values:
        metrics[f"recall@{k}"] = recall_at_k(relevant, k)

    # NDCG@K
    for k in k_values:
        metrics[f"ndcg@{k}"] = ndcg_at_k(relevant, k)

    # MRR (single query, so it's just RR)
    metrics["reciprocal_rank"] = reciprocal_rank(relevant)

    # AP
    metrics["average_precision"] = average_precision(relevant)

    return metrics


def calculate_aggregate_metrics(
    all_relevant: List[List[int]], k_values: List[int] = [1, 3, 5, 10]
) -> Dict[str, float]:
    """
    Calculate aggregate metrics across multiple queries.

    Args:
        all_relevant: List of relevance lists, one per query
        k_values: List of K values to evaluate

    Returns:
        Dictionary of metric names to aggregate scores
    """
    if len(all_relevant) == 0:
        return {}

    # Calculate per-query metrics
    per_query_metrics = []
    for relevant in all_relevant:
        metrics = calculate_metrics_for_query(relevant, k_values)
        per_query_metrics.append(metrics)

    # Aggregate across queries (mean)
    aggregate_metrics = {}

    metric_names = per_query_metrics[0].keys()
    for metric_name in metric_names:
        values = [m[metric_name] for m in per_query_metrics]
        aggregate_metrics[metric_name] = np.mean(values)

    # Add MRR (mean of reciprocal ranks)
    aggregate_metrics["mrr"] = aggregate_metrics["reciprocal_rank"]

    # Add MAP (mean of average precisions)
    aggregate_metrics["map"] = aggregate_metrics["average_precision"]

    return aggregate_metrics


def load_labels(labels_path: str) -> pd.DataFrame:
    """
    Load relevance labels from JSON file.

    Returns:
        DataFrame with columns: query_id, job_id, rank, relevance
    """
    import json
    from pathlib import Path

    path = Path(labels_path)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    labels = data["labels"]
    df = pd.DataFrame(labels)

    return df


def evaluate_search_results(
    labels_path: str, k_values: List[int] = [1, 3, 5, 10]
) -> Dict:
    """
    Evaluate search results using relevance labels.

    Args:
        labels_path: Path to relevance_labels.json
        k_values: List of K values to evaluate

    Returns:
        Dictionary with:
        - 'aggregate_metrics': Overall metrics across all queries
        - 'per_query_metrics': Metrics for each individual query
        - 'summary': Human-readable summary
    """
    # Load labels
    df = load_labels(labels_path)

    # Group by query
    per_query_relevant = []
    per_query_details = []

    for query_id in sorted(df["query_id"].unique()):
        query_df = df[df["query_id"] == query_id].sort_values("rank")
        relevant = query_df["relevance"].tolist()

        per_query_relevant.append(relevant)

        metrics = calculate_metrics_for_query(relevant, k_values)
        metrics["query_id"] = query_id
        metrics["query"] = query_df["query"].iloc[0]
        metrics["num_relevant"] = sum(relevant)
        metrics["total_results"] = len(relevant)

        per_query_details.append(metrics)

    # Calculate aggregate metrics
    aggregate_metrics = calculate_aggregate_metrics(per_query_relevant, k_values)

    # Create summary
    summary = {
        "total_queries": len(per_query_relevant),
        "total_results": sum(len(r) for r in per_query_relevant),
        "total_relevant": sum(sum(r) for r in per_query_relevant),
        "avg_relevant_per_query": np.mean([sum(r) for r in per_query_relevant]),
        "relevance_rate": sum(sum(r) for r in per_query_relevant)
        / sum(len(r) for r in per_query_relevant),
    }

    return {
        "aggregate_metrics": aggregate_metrics,
        "per_query_metrics": per_query_details,
        "summary": summary,
    }


def print_evaluation_report(results: Dict):
    """Print evaluation results in a nice format."""
    print("\n" + "=" * 70)
    print(" " * 25 + "EVALUATION REPORT")
    print("=" * 70)

    summary = results["summary"]
    print(f"\nDataset Summary:")
    print(f"  Total queries: {summary['total_queries']}")
    print(f"  Total results: {summary['total_results']}")
    print(f"  Total relevant: {summary['total_relevant']}")
    print(f"  Avg relevant per query: {summary['avg_relevant_per_query']:.2f}")
    print(f"  Overall relevance rate: {summary['relevance_rate']*100:.1f}%")

    print(f"\n" + "=" * 70)
    print("AGGREGATE METRICS (Across All Queries)")
    print("=" * 70)

    metrics = results["aggregate_metrics"]

    print(f"\nPrecision@K:")
    for k in [1, 3, 5, 10]:
        key = f"precision@{k}"
        if key in metrics:
            print(f"  P@{k:2d} = {metrics[key]:.3f} ({metrics[key]*100:.1f}%)")

    print(f"\nRecall@K:")
    for k in [1, 3, 5, 10]:
        key = f"recall@{k}"
        if key in metrics:
            print(f"  R@{k:2d} = {metrics[key]:.3f} ({metrics[key]*100:.1f}%)")

    print(f"\nNDCG@K:")
    for k in [1, 3, 5, 10]:
        key = f"ndcg@{k}"
        if key in metrics:
            print(f"  NDCG@{k:2d} = {metrics[key]:.3f} ({metrics[key]*100:.1f}%)")

    print(f"\nOther Metrics:")
    print(f"  MRR (Mean Reciprocal Rank) = {metrics.get('mrr', 0):.3f}")
    print(f"  MAP (Mean Average Precision) = {metrics.get('map', 0):.3f}")

    # Target check
    p5 = metrics.get("precision@5", 0)
    print(f"\n" + "=" * 70)
    print("TARGET EVALUATION")
    print("=" * 70)
    print(f"Target: Precision@5 ≥ 0.80 (80%)")
    print(f"Actual: Precision@5 = {p5:.3f} ({p5*100:.1f}%)")

    if p5 >= 0.80:
        print(f"✓ PASS: Target achieved!")
    else:
        print(f"⚠️  FAIL: Below target by {(0.80-p5)*100:.1f}%")

    print("=" * 70)


if __name__ == "__main__":
    # Example usage
    import sys
    from pathlib import Path

    # Default path
    labels_path = Path(__file__).resolve().parents[1] / "data" / "relevance_labels.json"

    if len(sys.argv) > 1:
        labels_path = sys.argv[1]

    if not Path(labels_path).exists():
        print(f"Error: Labels file not found: {labels_path}")
        print("Please run generate_pseudo_labels.py first.")
        sys.exit(1)

    print(f"Loading labels from: {labels_path}")

    results = evaluate_search_results(str(labels_path))
    print_evaluation_report(results)
