#!/usr/bin/env python3
"""
Debug script to test search functionality and analyze logs
"""

import sys

sys.path.append("/home/sakana/Code/DS-RS")

import logging
from src.recommender import JobRecommender

# Setup logging to see all debug output
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
    handlers=[logging.FileHandler("logs/test_debug.log"), logging.StreamHandler()],
)

logger = logging.getLogger(__name__)


def test_search_scenarios():
    """Test different search scenarios to debug the issue."""

    print("\n" + "=" * 80)
    print("LOADING RECOMMENDER SYSTEM")
    print("=" * 80)

    recommender = JobRecommender(auto_load=True)

    print(f"\n✓ Total jobs in dataset: {len(recommender.vector_store.job_data):,}")
    print(f"✓ Total indexed jobs: {len(recommender.vector_store.sample_indices):,}")

    # Test scenarios
    scenarios = [
        {
            "name": "1. Simple search (no filters)",
            "query": "software engineer",
            "filters": {},
        },
        {
            "name": "2. Search with location filter",
            "query": "software engineer",
            "filters": {"location": "New York"},
        },
        {
            "name": "3. Search with work type filter",
            "query": "software engineer",
            "filters": {"work_type": "Full-time"},
        },
        {
            "name": "4. Search with multiple filters",
            "query": "python developer",
            "filters": {"location": "San Francisco", "work_type": "Full-time"},
        },
        {
            "name": "5. Search with salary filter",
            "query": "data scientist",
            "filters": {"min_salary": 80000},
        },
    ]

    for scenario in scenarios:
        print("\n" + "=" * 80)
        print(f"SCENARIO: {scenario['name']}")
        print("=" * 80)
        print(f"Query: '{scenario['query']}'")
        print(f"Filters: {scenario['filters']}")
        print("-" * 80)

        results = recommender.get_recommendations(
            query=scenario["query"],
            top_k=10,
            method="faiss",
            filters=scenario["filters"] if scenario["filters"] else None,
        )

        print(f"\n✓ Results: {len(results)} jobs found")

        if len(results) > 0:
            print("\nTop 3 results:")
            for idx, row in results.head(3).iterrows():
                print(
                    f"  {idx+1}. {row.get('title', 'N/A')} at {row.get('company_name_x', 'N/A')}"
                )
                print(f"     Location: {row.get('location', 'N/A')}")
                print(f"     Work Type: {row.get('formatted_work_type', 'N/A')}")
                print(f"     Similarity: {row.get('similarity_score', 0):.4f}")
                print()
        else:
            print("\n⚠️  NO RESULTS - This is the issue!")
            print("\nDebugging info:")

            # Check what's in the indexed data
            sample_df = recommender.vector_store.job_data.loc[
                recommender.vector_store.sample_indices
            ]

            if "location" in sample_df.columns:
                print(f"\nTop 10 locations in indexed data:")
                print(sample_df["location"].value_counts().head(10))

            if "formatted_work_type" in sample_df.columns:
                print(f"\nWork types in indexed data:")
                print(sample_df["formatted_work_type"].value_counts())

            print(f"\nSample of indexed data columns:")
            print(sample_df.columns.tolist())

    print("\n" + "=" * 80)
    print("TEST COMPLETE - Check logs/test_debug.log for detailed trace")
    print("=" * 80)


if __name__ == "__main__":
    test_search_scenarios()
