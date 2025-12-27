"""
Unit Tests for Evaluation Metrics

Tests all IR metrics with known examples to ensure correctness.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.evaluation import (
    precision_at_k,
    recall_at_k,
    dcg_at_k,
    ndcg_at_k,
    reciprocal_rank,
    average_precision,
    calculate_metrics_for_query,
    calculate_aggregate_metrics
)


def test_precision_at_k():
    """Test Precision@K calculation."""
    print("\n" + "=" * 60)
    print("TEST 1: Precision@K")
    print("=" * 60)
    
    # Test case 1: Perfect precision
    relevant = [1, 1, 1, 1, 1, 0, 0, 0, 0, 0]
    assert precision_at_k(relevant, 5) == 1.0, "Perfect precision@5 should be 1.0"
    print("✓ Test 1.1: Perfect precision")
    
    # Test case 2: 60% precision
    relevant = [1, 1, 0, 1, 0, 0, 1, 0, 0, 0]
    p5 = precision_at_k(relevant, 5)
    assert abs(p5 - 0.6) < 0.01, f"Expected 0.6, got {p5}"
    print(f"✓ Test 1.2: 60% precision (3/5 relevant)")
    
    # Test case 3: Zero precision
    relevant = [0, 0, 0, 0, 0, 1, 1, 1, 1, 1]
    assert precision_at_k(relevant, 5) == 0.0, "No relevant in top-5"
    print("✓ Test 1.3: Zero precision")
    
    # Test case 4: Different K values
    relevant = [1, 0, 1, 0, 1, 0, 0, 0, 0, 0]
    assert precision_at_k(relevant, 1) == 1.0, "P@1 should be 1.0"
    assert precision_at_k(relevant, 3) == 2/3, "P@3 should be 2/3"
    assert precision_at_k(relevant, 5) == 3/5, "P@5 should be 3/5"
    print("✓ Test 1.4: Different K values")
    
    print("✓ Precision@K tests passed")


def test_recall_at_k():
    """Test Recall@K calculation."""
    print("\n" + "=" * 60)
    print("TEST 2: Recall@K")
    print("=" * 60)
    
    # Test case 1: Perfect recall
    relevant = [1, 1, 1, 1, 1, 0, 0, 0, 0, 0]
    assert recall_at_k(relevant, 5) == 1.0, "All relevant in top-5"
    print("✓ Test 2.1: Perfect recall")
    
    # Test case 2: 75% recall
    relevant = [1, 1, 0, 1, 0, 0, 1, 0, 0, 0]
    r5 = recall_at_k(relevant, 5)
    assert abs(r5 - 0.75) < 0.01, f"Expected 0.75 (3/4), got {r5}"
    print(f"✓ Test 2.2: 75% recall (3/4 found)")
    
    # Test case 3: Zero recall
    relevant = [0, 0, 0, 0, 0, 1, 1, 1, 1, 1]
    assert recall_at_k(relevant, 5) == 0.0, "No relevant in top-5"
    print("✓ Test 2.3: Zero recall")
    
    # Test case 4: No relevant items
    relevant = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    assert recall_at_k(relevant, 5) == 0.0, "No relevant items at all"
    print("✓ Test 2.4: No relevant items")
    
    print("✓ Recall@K tests passed")


def test_dcg_and_ndcg():
    """Test DCG and NDCG calculation."""
    print("\n" + "=" * 60)
    print("TEST 3: DCG and NDCG")
    print("=" * 60)
    
    # Test case 1: Perfect ranking
    relevant = [1, 1, 1, 0, 0]
    ndcg = ndcg_at_k(relevant, 5)
    assert ndcg == 1.0, "Perfect ranking should have NDCG=1.0"
    print("✓ Test 3.1: Perfect ranking (NDCG=1.0)")
    
    # Test case 2: Worst ranking
    relevant = [0, 0, 0, 1, 1]
    ndcg = ndcg_at_k(relevant, 5)
    assert ndcg < 1.0, "Worst ranking should have NDCG<1.0"
    print(f"✓ Test 3.2: Worst ranking (NDCG={ndcg:.3f})")
    
    # Test case 3: All zeros
    relevant = [0, 0, 0, 0, 0]
    ndcg = ndcg_at_k(relevant, 5)
    assert ndcg == 0.0, "All zeros should have NDCG=0.0"
    print("✓ Test 3.3: All zeros (NDCG=0.0)")
    
    # Test case 4: DCG calculation
    relevant = [1, 0, 1, 0, 0]
    dcg = dcg_at_k(relevant, 5)
    # DCG = 1/log2(2) + 0 + 1/log2(4) + 0 + 0
    # DCG = 1.0 + 0.5 = 1.5
    assert abs(dcg - 1.5) < 0.01, f"Expected DCG≈1.5, got {dcg}"
    print(f"✓ Test 3.4: DCG calculation (DCG={dcg:.3f})")
    
    print("✓ DCG and NDCG tests passed")


def test_reciprocal_rank():
    """Test Reciprocal Rank calculation."""
    print("\n" + "=" * 60)
    print("TEST 4: Reciprocal Rank")
    print("=" * 60)
    
    # Test case 1: First result relevant
    relevant = [1, 0, 0, 0, 0]
    rr = reciprocal_rank(relevant)
    assert rr == 1.0, "First result relevant → RR=1.0"
    print("✓ Test 4.1: First result relevant (RR=1.0)")
    
    # Test case 2: Third result relevant
    relevant = [0, 0, 1, 0, 0]
    rr = reciprocal_rank(relevant)
    assert abs(rr - 1/3) < 0.01, f"Third result relevant → RR=1/3, got {rr}"
    print(f"✓ Test 4.2: Third result relevant (RR={rr:.3f})")
    
    # Test case 3: No relevant results
    relevant = [0, 0, 0, 0, 0]
    rr = reciprocal_rank(relevant)
    assert rr == 0.0, "No relevant → RR=0.0"
    print("✓ Test 4.3: No relevant (RR=0.0)")
    
    # Test case 4: Fifth result relevant
    relevant = [0, 0, 0, 0, 1]
    rr = reciprocal_rank(relevant)
    assert abs(rr - 0.2) < 0.01, f"Fifth result → RR=1/5=0.2, got {rr}"
    print(f"✓ Test 4.4: Fifth result (RR={rr:.3f})")
    
    print("✓ Reciprocal Rank tests passed")


def test_average_precision():
    """Test Average Precision calculation."""
    print("\n" + "=" * 60)
    print("TEST 5: Average Precision")
    print("=" * 60)
    
    # Test case 1: Perfect ranking
    relevant = [1, 1, 1, 0, 0]
    ap = average_precision(relevant)
    # AP = (1/1 + 2/2 + 3/3) / 3 = (1.0 + 1.0 + 1.0) / 3 = 1.0
    assert ap == 1.0, "Perfect ranking → AP=1.0"
    print("✓ Test 5.1: Perfect ranking (AP=1.0)")
    
    # Test case 2: Mixed ranking
    relevant = [1, 0, 1, 1, 0]
    ap = average_precision(relevant)
    # AP = (1/1 + 2/3 + 3/4) / 3 = (1.0 + 0.667 + 0.75) / 3 = 0.806
    expected_ap = (1.0 + 2/3 + 3/4) / 3
    assert abs(ap - expected_ap) < 0.01, f"Expected {expected_ap:.3f}, got {ap:.3f}"
    print(f"✓ Test 5.2: Mixed ranking (AP={ap:.3f})")
    
    # Test case 3: No relevant
    relevant = [0, 0, 0, 0, 0]
    ap = average_precision(relevant)
    assert ap == 0.0, "No relevant → AP=0.0"
    print("✓ Test 5.3: No relevant (AP=0.0)")
    
    # Test case 4: Worst ranking
    relevant = [0, 0, 0, 1, 1]
    ap = average_precision(relevant)
    # AP = (1/4 + 2/5) / 2 = (0.25 + 0.4) / 2 = 0.325
    expected_ap = (1/4 + 2/5) / 2
    assert abs(ap - expected_ap) < 0.01, f"Expected {expected_ap:.3f}, got {ap:.3f}"
    print(f"✓ Test 5.4: Worst ranking (AP={ap:.3f})")
    
    print("✓ Average Precision tests passed")


def test_calculate_metrics_for_query():
    """Test calculate_metrics_for_query."""
    print("\n" + "=" * 60)
    print("TEST 6: Calculate Metrics for Query")
    print("=" * 60)
    
    relevant = [1, 1, 0, 1, 0, 0, 1, 0, 0, 0]
    metrics = calculate_metrics_for_query(relevant, k_values=[1, 3, 5, 10])
    
    # Check all metrics present
    assert 'precision@1' in metrics, "Should have precision@1"
    assert 'recall@5' in metrics, "Should have recall@5"
    assert 'ndcg@10' in metrics, "Should have ndcg@10"
    assert 'reciprocal_rank' in metrics, "Should have reciprocal_rank"
    assert 'average_precision' in metrics, "Should have average_precision"
    
    # Check values
    assert metrics['precision@1'] == 1.0, "First is relevant"
    assert metrics['precision@5'] == 0.6, "3/5 relevant"
    assert metrics['reciprocal_rank'] == 1.0, "First is relevant"
    
    print("✓ All metrics calculated correctly")
    print(f"  Precision@1: {metrics['precision@1']:.3f}")
    print(f"  Precision@5: {metrics['precision@5']:.3f}")
    print(f"  Recall@5: {metrics['recall@5']:.3f}")
    print(f"  NDCG@5: {metrics['ndcg@5']:.3f}")
    print(f"  RR: {metrics['reciprocal_rank']:.3f}")
    print(f"  AP: {metrics['average_precision']:.3f}")
    
    print("✓ calculate_metrics_for_query tests passed")


def test_calculate_aggregate_metrics():
    """Test calculate_aggregate_metrics."""
    print("\n" + "=" * 60)
    print("TEST 7: Calculate Aggregate Metrics")
    print("=" * 60)
    
    # Two queries
    all_relevant = [
        [1, 1, 0, 1, 0],  # Query 1: 3/5 relevant (60%)
        [1, 0, 1, 0, 1]   # Query 2: 3/5 relevant (60%)
    ]
    
    metrics = calculate_aggregate_metrics(all_relevant, k_values=[5])
    
    # Check aggregate precision@5
    # (0.6 + 0.6) / 2 = 0.6
    assert abs(metrics['precision@5'] - 0.6) < 0.01, f"Expected 0.6, got {metrics['precision@5']}"
    
    # Check MRR
    # Query 1: RR = 1.0 (first is relevant)
    # Query 2: RR = 1.0 (first is relevant)
    # MRR = (1.0 + 1.0) / 2 = 1.0
    assert metrics['mrr'] == 1.0, f"Expected MRR=1.0, got {metrics['mrr']}"
    
    print("✓ Aggregate metrics calculated correctly")
    print(f"  Avg Precision@5: {metrics['precision@5']:.3f}")
    print(f"  Avg Recall@5: {metrics['recall@5']:.3f}")
    print(f"  Avg NDCG@5: {metrics['ndcg@5']:.3f}")
    print(f"  MRR: {metrics['mrr']:.3f}")
    print(f"  MAP: {metrics['map']:.3f}")
    
    print("✓ calculate_aggregate_metrics tests passed")


def test_edge_cases():
    """Test edge cases."""
    print("\n" + "=" * 60)
    print("TEST 8: Edge Cases")
    print("=" * 60)
    
    # Empty list
    assert precision_at_k([], 5) == 0.0, "Empty list → precision=0"
    print("✓ Test 8.1: Empty list")
    
    # K=0
    assert precision_at_k([1, 1, 1], 0) == 0.0, "K=0 → precision=0"
    print("✓ Test 8.2: K=0")
    
    # K > list length
    # When K=10 but list has 3 items, we take min(K, len) for top_k
    # So precision = relevant_in_top_k / K = 2 / 10 = 0.2
    result = precision_at_k([1, 1, 0], 10)
    expected = 2 / 10  # 2 relevant out of K=10
    assert abs(result - expected) < 0.01, f"K > length: expected {expected}, got {result}"
    print("✓ Test 8.3: K > list length")
    
    # All zeros
    assert recall_at_k([0, 0, 0], 5) == 0.0, "All zeros → recall=0"
    print("✓ Test 8.4: All zeros for recall")
    
    print("✓ Edge cases handled correctly")


def run_all_tests():
    """Run all evaluation tests."""
    print("\n" + "=" * 70)
    print(" " * 20 + "EVALUATION METRICS - UNIT TESTS")
    print("=" * 70)
    
    try:
        test_precision_at_k()
        test_recall_at_k()
        test_dcg_and_ndcg()
        test_reciprocal_rank()
        test_average_precision()
        test_calculate_metrics_for_query()
        test_calculate_aggregate_metrics()
        test_edge_cases()
        
        print("\n" + "=" * 70)
        print("✓ ALL TESTS PASSED")
        print("=" * 70)
        
        print("\nSUMMARY:")
        print("  ✓ 8 test groups passed")
        print("  ✓ All metrics working correctly")
        print("  ✓ Edge cases handled")
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
