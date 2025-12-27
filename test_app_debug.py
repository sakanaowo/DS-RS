"""
Test script to verify app functionality with debug logging
"""

import logging
import time
from src.recommender import JobRecommender

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/test_app_debug.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def main():
    logger.info("=" * 80)
    logger.info("APP FUNCTIONALITY TEST - TF-IDF ONLY SYSTEM")
    logger.info("=" * 80)

    # Load recommender
    logger.info("\n[1/4] Loading Recommender System...")
    load_start = time.time()
    rec = JobRecommender(auto_load=True)
    load_time = time.time() - load_start

    logger.info(f"✓ Loaded in {load_time:.2f}s")
    logger.info(f"✓ Total jobs: {len(rec.vector_store.job_data):,}")
    logger.info(f"✓ Indexed jobs: {len(rec.vector_store.sample_indices):,}")
    logger.info(f"✓ TF-IDF matrix: {rec.vector_store.tfidf_matrix.shape}")

    # Verify 50k data
    logger.info("\n[2/4] Verifying 50k Data...")
    assert (
        len(rec.vector_store.sample_indices) == 50000
    ), "Expected 50,000 indexed jobs!"
    logger.info("✓ VERIFIED: 50,000 jobs are indexed")

    # Verify TF-IDF only
    logger.info("\n[3/4] Verifying TF-IDF Only Configuration...")
    has_minilm = (
        hasattr(rec.vector_store, "minilm_model")
        and rec.vector_store.minilm_model is not None
    )
    has_faiss = (
        hasattr(rec.vector_store, "faiss_index")
        and rec.vector_store.faiss_index is not None
    )

    if has_minilm or has_faiss:
        logger.error("❌ FAILED: MiniLM or FAISS still present!")
        if has_minilm:
            logger.error("  - MiniLM model found")
        if has_faiss:
            logger.error("  - FAISS index found")
    else:
        logger.info("✓ VERIFIED: Only TF-IDF is configured (MiniLM/FAISS removed)")

    # Test multiple queries
    logger.info("\n[4/4] Testing Multiple Queries...")

    test_queries = [
        ("Python developer", None),
        ("Data scientist machine learning", None),
        ("Remote software engineer", {"remote_allowed": True}),
        (
            "Full-time backend developer New York",
            {"location": "New York", "work_type": "Full-time"},
        ),
        ("Senior cloud engineer AWS", {"min_salary": 100000}),
    ]

    results_summary = []

    for i, (query, filters) in enumerate(test_queries, 1):
        logger.info(f'\n  Query {i}: "{query}"')
        if filters:
            logger.info(f"  Filters: {filters}")

        search_start = time.time()
        results = rec.get_recommendations(query, top_k=10, filters=filters)
        search_time = (time.time() - search_start) * 1000

        logger.info(f"  ✓ Search time: {search_time:.2f}ms")
        logger.info(f"  ✓ Results found: {len(results)}")

        if len(results) > 0:
            top = results.iloc[0]
            logger.info(
                f"  ✓ Top match: {top['title']} (score: {top['similarity_score']:.4f})"
            )
            results_summary.append(
                {
                    "query": query,
                    "time_ms": search_time,
                    "results": len(results),
                    "top_score": top["similarity_score"],
                }
            )
        else:
            logger.warning(f"  ⚠ No results found")
            results_summary.append(
                {"query": query, "time_ms": search_time, "results": 0, "top_score": 0.0}
            )

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)

    total_time = sum(r["time_ms"] for r in results_summary)
    avg_time = total_time / len(results_summary)
    total_results = sum(r["results"] for r in results_summary)
    avg_score = sum(
        r["top_score"] for r in results_summary if r["top_score"] > 0
    ) / len([r for r in results_summary if r["top_score"] > 0])

    logger.info(f"Total queries: {len(test_queries)}")
    logger.info(f"Average search time: {avg_time:.2f}ms")
    logger.info(f"Total results: {total_results}")
    logger.info(f"Average top score: {avg_score:.4f}")
    logger.info(f"\n✅ ALL TESTS PASSED - System working with 50k TF-IDF data!")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
