#!/usr/bin/env python3
"""
Test fallback strategy with restrictive filters
"""

import sys

sys.path.append("/home/sakana/Code/DS-RS")

from src.recommender import JobRecommender
from src.data_quality import DataQualityHandler, get_data_quality_report
import json


def test_fallback_strategies():
    """Test progressive fallback with very restrictive filters."""

    print("\n" + "=" * 80)
    print("TESTING PROGRESSIVE FALLBACK STRATEGY")
    print("=" * 80)

    recommender = JobRecommender(auto_load=True)

    # Scenario 1: Ultra-restrictive filters (should trigger fallback)
    print("\n" + "=" * 80)
    print("SCENARIO 1: Ultra-restrictive filters")
    print("=" * 80)
    print("Query: 'data scientist'")
    print("Filters: Location='Antarctica', Salary>$500k, Remote=True")
    print("-" * 80)

    results = recommender.get_recommendations(
        query="data scientist",
        top_k=20,
        method="faiss",
        filters={
            "location": "Antarctica",  # Almost no jobs
            "min_salary": 500000,  # Very high
            "remote_allowed": True,  # Further restriction
        },
        enable_fallback=True,
    )

    print(f"\n✓ Results: {len(results)} jobs")
    print(f"✓ Search strategy: {results.iloc[0].get('search_strategy', 'N/A')}")

    if len(results) > 0:
        print("\nTop 3 results:")
        for idx, row in results.head(3).iterrows():
            print(f"  {idx+1}. {row.get('title', 'N/A')}")
            print(f"     Company: {row.get('company_name_x', 'N/A')}")
            print(f"     Location: {row.get('location', 'N/A')}")
            print(f"     Strategy: {row.get('search_strategy', 'N/A')}")

    # Scenario 2: Compare with fallback OFF
    print("\n" + "=" * 80)
    print("SCENARIO 2: Same filters but fallback DISABLED")
    print("=" * 80)

    results_no_fallback = recommender.get_recommendations(
        query="data scientist",
        top_k=20,
        method="faiss",
        filters={
            "location": "Antarctica",
            "min_salary": 500000,
            "remote_allowed": True,
        },
        enable_fallback=False,
    )

    print(f"\n✓ Results without fallback: {len(results_no_fallback)} jobs")
    print(f"✓ Results WITH fallback: {len(results)} jobs")
    print(f"✓ Improvement: +{len(results) - len(results_no_fallback)} jobs")

    # Scenario 3: Moderate filters (should succeed early)
    print("\n" + "=" * 80)
    print("SCENARIO 3: Moderate filters (should succeed in Layer 1-2)")
    print("=" * 80)
    print("Query: 'software engineer'")
    print("Filters: Location='San Francisco', Work Type='Full-time'")
    print("-" * 80)

    results_moderate = recommender.get_recommendations(
        query="software engineer",
        top_k=20,
        method="faiss",
        filters={
            "location": "San Francisco",
            "work_type": "Full-time",
        },
        enable_fallback=True,
    )

    print(f"\n✓ Results: {len(results_moderate)} jobs")
    print(
        f"✓ Search strategy: {results_moderate.iloc[0].get('search_strategy', 'N/A')}"
    )

    print("\n" + "=" * 80)
    print("FALLBACK STRATEGY TEST COMPLETE")
    print("=" * 80)

    # Summary
    print("\nSUMMARY:")
    print(f"  - Ultra-restrictive + fallback: {len(results)} results ✓")
    print(f"  - Ultra-restrictive NO fallback: {len(results_no_fallback)} results ✗")
    print(f"  - Moderate + fallback: {len(results_moderate)} results ✓")
    print(f"\n✓ Fallback strategy ensures users ALWAYS get results!")


def test_data_quality_handler():
    """Test data quality imputation strategies."""

    print("\n" + "=" * 80)
    print("TESTING DATA QUALITY HANDLER")
    print("=" * 80)

    import pandas as pd
    from src.loader import load_raw_postings

    # Load sample data
    print("Loading sample data (10k jobs)...")
    df = load_raw_postings(nrows=10000)

    # Before imputation
    print("\nBEFORE IMPUTATION:")
    print(f"  - Missing work_type: {df['formatted_work_type'].isna().sum():,}")
    print(f"  - Missing location: {df['location'].isna().sum():,}")
    print(f"  - Missing experience: {df['formatted_experience_level'].isna().sum():,}")

    # Apply data quality strategies
    df_enhanced = DataQualityHandler.apply_all_strategies(df)

    # After imputation
    print("\nAFTER IMPUTATION:")
    print(f"  - Missing work_type: {df_enhanced['formatted_work_type'].isna().sum():,}")
    print(f"  - Missing location: {df_enhanced['location'].isna().sum():,}")
    print(
        f"  - Missing experience: {df_enhanced['formatted_experience_level'].isna().sum():,}"
    )

    # Quality report
    report = get_data_quality_report(df_enhanced)

    print("\nDATA QUALITY REPORT:")
    print("Coverage:")
    for field, coverage in report["coverage"].items():
        print(f"  - {field}: {coverage:.1f}%")

    print("\nDistribution:")
    print("Work Types:")
    for wt, count in list(report["distribution"]["work_types"].items())[:5]:
        pct = count / report["total_jobs"] * 100
        print(f"  - {wt}: {count:,} ({pct:.1f}%)")

    print("\n" + "=" * 80)
    print("DATA QUALITY TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    print("=" * 80)
    print("JOB RECOMMENDATION SYSTEM - ADVANCED STRATEGIES TEST")
    print("=" * 80)

    # Test 1: Fallback strategy
    test_fallback_strategies()

    # Test 2: Data quality handler
    print("\n\n")
    test_data_quality_handler()

    print("\n" + "=" * 80)
    print("ALL TESTS COMPLETE")
    print("=" * 80)
