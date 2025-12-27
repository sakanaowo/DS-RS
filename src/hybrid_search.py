"""
Hybrid Job Search Engine - Combines BM25 + Semantic Search

Day 4 Implementation - Best of both worlds

Architecture:
- BM25 (70%): Fast, exact matching, keyword-based
- Semantic (30%): Handles synonyms, semantic similarity

Approach:
1. Run BM25 search → Get top-N candidates
2. Run semantic search → Get top-N candidates
3. Merge results with weighted scores
4. Re-rank by combined score

Benefits:
- Maintains BM25 precision for exact matches
- Adds semantic coverage for edge cases
- Handles synonyms (developer ↔ engineer)
- Better performance on generic queries
"""

from typing import List, Dict, Optional, Tuple
import time
import warnings

warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np

from .recommender import JobRecommender
from .semantic_search import SemanticJobSearch


class HybridJobSearch:
    """
    Hybrid search combining BM25 and semantic search.

    Weighting strategy:
    - BM25: 70% (maintains precision)
    - Semantic: 30% (improves recall)

    These weights were chosen based on:
    - BM25 achieves P@5=88% (strong baseline)
    - Semantic helps with edge cases (synonyms, generic queries)
    - 70/30 split maintains BM25 strength while adding semantic coverage
    """

    def __init__(
        self,
        bm25_weight: float = 0.7,
        semantic_weight: float = 0.3,
        sample_size: Optional[int] = None,
        verbose: bool = False,
    ):
        """
        Initialize hybrid search engine.

        Args:
            bm25_weight: Weight for BM25 scores (default 0.7)
            semantic_weight: Weight for semantic scores (default 0.3)
            sample_size: If set, use only this many jobs (for testing)
            verbose: If True, print progress
        """
        if abs(bm25_weight + semantic_weight - 1.0) > 0.001:
            raise ValueError(
                f"Weights must sum to 1.0, got {bm25_weight + semantic_weight}"
            )

        self.bm25_weight = bm25_weight
        self.semantic_weight = semantic_weight
        self.sample_size = sample_size
        self.verbose = verbose

        # Initialize engines
        self.bm25_engine = None
        self.semantic_engine = None
        self._is_ready = False

    def initialize(self):
        """Initialize both search engines."""
        import sys

        print(
            "[DEBUG] HybridJobSearch.initialize() starting...",
            file=sys.stderr,
            flush=True,
        )

        if self.verbose:
            print("Initializing hybrid search engine...")
            print(f"  BM25 weight: {self.bm25_weight}")
            print(f"  Semantic weight: {self.semantic_weight}")

        start_time = time.time()

        # Initialize BM25
        print("[DEBUG] Initializing BM25 engine...", file=sys.stderr, flush=True)
        if self.verbose:
            print("\n1. Initializing BM25 engine...")

        self.bm25_engine = JobRecommender(auto_load=True)
        print("[DEBUG] BM25 engine initialized", file=sys.stderr, flush=True)

        # Initialize Semantic
        print("[DEBUG] Initializing Semantic engine...", file=sys.stderr, flush=True)
        if self.verbose:
            print("\n2. Initializing Semantic engine...")

        self.semantic_engine = SemanticJobSearch(
            sample_size=self.sample_size, verbose=self.verbose
        )
        print("[DEBUG] SemanticJobSearch created", file=sys.stderr, flush=True)

        self.semantic_engine.load_model()
        print("[DEBUG] Semantic model loaded", file=sys.stderr, flush=True)

        self.semantic_engine.load_data()
        print("[DEBUG] Semantic data loaded", file=sys.stderr, flush=True)

        self.semantic_engine.encode_jobs()
        print("[DEBUG] Semantic jobs encoded", file=sys.stderr, flush=True)

        elapsed = time.time() - start_time
        self._is_ready = True

        print(
            f"[DEBUG] HybridJobSearch.initialize() completed in {elapsed:.2f}s",
            file=sys.stderr,
            flush=True,
        )

        if self.verbose:
            print(f"\n✓ Hybrid search initialized in {elapsed:.2f}s")

    def _normalize_scores(self, scores: np.ndarray) -> np.ndarray:
        """
        Normalize scores to [0, 1] range using min-max normalization.

        Args:
            scores: Raw scores

        Returns:
            Normalized scores in [0, 1]
        """
        if len(scores) == 0:
            return scores

        min_score = scores.min()
        max_score = scores.max()

        if max_score == min_score:
            # All scores are the same
            return np.ones_like(scores) * 0.5

        normalized = (scores - min_score) / (max_score - min_score)
        return normalized

    def search(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict] = None,
        bm25_candidates: int = 100,
        semantic_candidates: int = 100,
    ) -> pd.DataFrame:
        """
        Hybrid search with BM25 + Semantic.

        Algorithm:
        1. Get top-N candidates from BM25
        2. Get top-N candidates from Semantic
        3. Merge and deduplicate by job_id
        4. Calculate combined score: 0.7*BM25 + 0.3*Semantic
        5. Re-rank by combined score
        6. Return top-k

        Args:
            query: Search query
            top_k: Number of final results
            filters: Optional filters (location, salary, etc.)
            bm25_candidates: Number of candidates from BM25 (default 100)
            semantic_candidates: Number of candidates from Semantic (default 100)

        Returns:
            DataFrame with top-k jobs and scores
        """
        if not self._is_ready:
            raise RuntimeError(
                "Hybrid search not initialized. Call initialize() first."
            )

        start_time = time.time()

        # Get BM25 results (using tfidf method for BM25-like behavior)
        bm25_results = self.bm25_engine.get_recommendations(
            query=query,
            top_k=bm25_candidates,
            method="tfidf",
            filters=filters,
            enable_fallback=False,
        )

        # Rename score column
        if "similarity_score" in bm25_results.columns:
            bm25_results = bm25_results.rename(
                columns={"similarity_score": "bm25_score"}
            )
        elif "score" in bm25_results.columns:
            bm25_results = bm25_results.rename(columns={"score": "bm25_score"})
        else:
            # No score column, add default
            bm25_results["bm25_score"] = 1.0

        # Get Semantic results
        semantic_results = self.semantic_engine.search(
            query=query, top_k=semantic_candidates, filters=filters
        )

        # Create score dictionaries
        bm25_scores = dict(zip(bm25_results["job_id"], bm25_results["bm25_score"]))

        semantic_scores = dict(
            zip(semantic_results["job_id"], semantic_results["semantic_score"])
        )

        # Get all unique job IDs
        all_job_ids = set(bm25_scores.keys()) | set(semantic_scores.keys())

        # Collect scores for each job
        job_data = []
        for job_id in all_job_ids:
            bm25_score = bm25_scores.get(job_id, 0.0)
            semantic_score = semantic_scores.get(job_id, 0.0)

            job_data.append(
                {
                    "job_id": job_id,
                    "bm25_score": bm25_score,
                    "semantic_score": semantic_score,
                }
            )

        # Create DataFrame
        scores_df = pd.DataFrame(job_data)

        # Normalize scores to [0, 1] range
        scores_df["bm25_norm"] = self._normalize_scores(scores_df["bm25_score"].values)
        scores_df["semantic_norm"] = self._normalize_scores(
            scores_df["semantic_score"].values
        )

        # Calculate combined score
        scores_df["hybrid_score"] = (
            self.bm25_weight * scores_df["bm25_norm"]
            + self.semantic_weight * scores_df["semantic_norm"]
        )

        # Sort by hybrid score
        scores_df = scores_df.sort_values("hybrid_score", ascending=False)

        # Get top-k job IDs
        top_job_ids = scores_df.head(top_k)["job_id"].tolist()

        # Get full job details from BM25 engine (has all data)
        # First, try from BM25 results
        results_list = []
        for job_id in top_job_ids:
            # Try BM25 results first
            bm25_match = bm25_results[bm25_results["job_id"] == job_id]
            if not bm25_match.empty:
                results_list.append(bm25_match.iloc[0])
            else:
                # Fall back to semantic results
                semantic_match = semantic_results[semantic_results["job_id"] == job_id]
                if not semantic_match.empty:
                    results_list.append(semantic_match.iloc[0])

        results_df = pd.DataFrame(results_list)

        # Add scores
        results_df = results_df.merge(
            scores_df[["job_id", "bm25_score", "semantic_score", "hybrid_score"]],
            on="job_id",
            how="left",
        )

        # Sort by hybrid score
        results_df = results_df.sort_values("hybrid_score", ascending=False)

        elapsed = time.time() - start_time

        if self.verbose:
            print(f"✓ Found {len(results_df)} results in {elapsed:.3f}s")
            print(f"  BM25 candidates: {len(bm25_results)}")
            print(f"  Semantic candidates: {len(semantic_results)}")
            print(f"  Merged unique jobs: {len(all_job_ids)}")

        return results_df


def demo_hybrid_search():
    """Demo function to compare BM25, Semantic, and Hybrid search."""
    print("\n" + "=" * 70)
    print("HYBRID SEARCH COMPARISON - BM25 vs Semantic vs Hybrid")
    print("=" * 70)

    # Initialize
    print("\nInitializing hybrid search...")
    hybrid = HybridJobSearch(sample_size=5000, verbose=True)
    hybrid.initialize()

    print("\n" + "=" * 70)
    print("TEST 1: Synonym Handling")
    print("=" * 70)
    print("Query: 'software developer' (synonym of 'engineer')")

    # Search with all three methods
    bm25_results = hybrid.bm25_engine.search("software developer", top_k=5)
    semantic_results = hybrid.semantic_engine.search("software developer", top_k=5)
    hybrid_results = hybrid.search("software developer", top_k=5)

    print("\nBM25 Top-3:")
    for idx, row in bm25_results.head(3).iterrows():
        print(f"  {row['title']}")
        print(f"    BM25: {row['bm25_score']:.3f}")

    print("\nSemantic Top-3:")
    for idx, row in semantic_results.head(3).iterrows():
        print(f"  {row['title']}")
        print(f"    Semantic: {row['semantic_score']:.3f}")

    print("\nHybrid Top-3:")
    for idx, row in hybrid_results.head(3).iterrows():
        print(f"  {row['title']}")
        print(
            f"    Hybrid: {row['hybrid_score']:.3f} (BM25: {row['bm25_score']:.3f}, Semantic: {row['semantic_score']:.3f})"
        )

    print("\n" + "=" * 70)
    print("TEST 2: Exact Match")
    print("=" * 70)
    print("Query: 'Data Scientist' (exact title match)")

    bm25_results = hybrid.bm25_engine.search("Data Scientist", top_k=5)
    semantic_results = hybrid.semantic_engine.search("Data Scientist", top_k=5)
    hybrid_results = hybrid.search("Data Scientist", top_k=5)

    print("\nBM25 Top-3:")
    for idx, row in bm25_results.head(3).iterrows():
        print(f"  {row['title']}")
        print(f"    BM25: {row['bm25_score']:.3f}")

    print("\nHybrid Top-3:")
    for idx, row in hybrid_results.head(3).iterrows():
        print(f"  {row['title']}")
        print(f"    Hybrid: {row['hybrid_score']:.3f}")

    print("\n" + "=" * 70)
    print("✓ DEMO COMPLETE")
    print("=" * 70)
    print("\nKey Insights:")
    print("- BM25: Best for exact keyword matches")
    print("- Semantic: Best for synonyms and semantic similarity")
    print("- Hybrid: Combines strengths of both approaches")


if __name__ == "__main__":
    demo_hybrid_search()
