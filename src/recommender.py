"""
Job Recommendation Module

This module provides the main recommendation engine that uses VectorStore
for similarity search and applies filters to refine results.
"""

from __future__ import annotations

from typing import Optional, List, Dict, Any, Literal

import pandas as pd
import numpy as np
import logging

from .vector_store import VectorStore
from .preprocessing import clean_text

# Setup logger
logger = logging.getLogger(__name__)


class JobRecommender:
    """
    Main recommendation engine for job postings.

    Uses VectorStore for similarity search and provides filtering
    capabilities based on location, work type, experience, salary, etc.
    """

    def __init__(
        self,
        models_dir: str = "models",
        data_dir: str = "data/processed",
        auto_load: bool = True,
    ):
        """
        Initialize JobRecommender.

        Args:
            models_dir: Directory containing saved models
            data_dir: Directory containing processed data
            auto_load: Whether to automatically load all components
        """
        self.vector_store = VectorStore(models_dir, data_dir)

        if auto_load:
            print("Initializing JobRecommender...")
            self.vector_store.load_all()
            print("✓ JobRecommender ready!\n")

    def get_recommendations(
        self,
        query: str,
        top_k: int = 10,
        method: Literal["tfidf", "minilm", "faiss"] = "faiss",
        filters: Optional[Dict[str, Any]] = None,
        rerank: bool = False,
        enable_fallback: bool = True,
    ) -> pd.DataFrame:
        """
        Get job recommendations based on query and filters.

        Implements progressive fallback strategy (LinkedIn/Indeed-inspired):
        Layer 1: All filters → Layer 2: Relax salary → Layer 3: Relax experience
        → Layer 4: Query only → Layer 5: Popular jobs

        Args:
            query: User's search query (e.g., "Python backend developer")
            top_k: Number of recommendations to return
            method: Search method ("tfidf", "minilm", or "faiss")
            filters: Optional filters dict with keys:
                - location: str or List[str] - City, state, or country
                - work_type: str or List[str] - Full-time, Part-time, Contract, etc.
                - experience_level: str or List[str] - Entry, Mid, Senior, etc.
                - remote_allowed: bool - Remote jobs only
                - min_salary: float - Minimum salary
                - max_salary: float - Maximum salary
                - industries: str or List[str] - Industry names
                - skills: str or List[str] - Required skills
            rerank: Whether to rerank results using hybrid scoring
            enable_fallback: Whether to use progressive fallback strategy

        Returns:
            DataFrame with recommended jobs, sorted by relevance
        """
        logger.info("\n" + "=" * 80)
        logger.info("BACKEND: get_recommendations() CALLED")
        logger.info("=" * 80)
        logger.info(f"Query: '{query}'")
        logger.info(f"top_k: {top_k}")
        logger.info(f"method: {method}")
        logger.info(f"filters: {filters}")
        logger.info(f"rerank: {rerank}")
        logger.info(f"enable_fallback: {enable_fallback}")

        # Try with fallback strategy if enabled
        if enable_fallback and filters:
            return self._search_with_fallback(query, top_k, method, filters, rerank)

        # Original search logic (no fallback)
        return self._search_no_fallback(query, top_k, method, filters, rerank)

    def _search_no_fallback(
        self,
        query: str,
        top_k: int,
        method: str,
        filters: Optional[Dict[str, Any]],
        rerank: bool,
    ) -> pd.DataFrame:
        """Original search without fallback (for backward compatibility)."""
        # Get initial candidates (fetch more for filtering)
        # With 50k indexed jobs, we can use lower multiplier than with 10k
        if filters and len(filters) > 0:
            # Fetch 10-15x more to ensure enough candidates after filtering
            # Reduced from 20x since we have 5x more coverage (50k vs 10k)
            fetch_k = top_k * 12
        else:
            fetch_k = top_k

        logger.info(f"Calculated fetch_k: {fetch_k} (filters present: {bool(filters)})")
        logger.info(f">>> Calling vector_store.search() with fetch_k={fetch_k}...")

        results = self.vector_store.search(query, top_k=fetch_k, method=method)

        logger.info(f"<<< vector_store.search() returned {len(results)} results")
        if len(results) > 0:
            logger.info(f"Before filtering - shape: {results.shape}")
            logger.info(f"Before filtering - columns: {results.columns.tolist()}")
            logger.info(f"Sample data from first result:")
            for col in [
                "title",
                "location",
                "formatted_work_type",
                "formatted_experience_level",
                "remote_allowed",
            ]:
                if col in results.columns:
                    logger.info(f"  - {col}: {results.iloc[0].get(col, 'N/A')}")

        # Apply filters
        if filters:
            logger.info(f">>> Applying filters: {filters}")
            results = self._apply_filters(results, filters)
            logger.info(f"<<< After filtering: {len(results)} results remain")

        # Rerank if requested
        if rerank and method == "faiss":
            logger.info(">>> Applying hybrid reranking...")
            results = self._hybrid_rerank(query, results, top_k)
            logger.info(f"<<< After reranking: {len(results)} results")

        # Return top-K
        final_results = results.head(top_k)
        logger.info(
            f"FINAL RESULTS: Returning {len(final_results)} jobs (requested top_k={top_k})"
        )
        logger.info("=" * 80 + "\n")
        return final_results

    def _search_with_fallback(
        self,
        query: str,
        top_k: int,
        method: str,
        filters: Dict[str, Any],
        rerank: bool,
    ) -> pd.DataFrame:
        """
        Progressive fallback strategy (LinkedIn/Indeed-inspired).

        Layers:
        1. All filters (strict)
        2. Remove salary filters (unreliable data)
        3. Remove experience filter
        4. Remove remote filter
        5. Query only (no filters)
        6. Popular jobs (last resort)
        """
        logger.info("=" * 80)
        logger.info("PROGRESSIVE FALLBACK STRATEGY ENABLED")
        logger.info("=" * 80)

        # Filter priority for progressive relaxation (least important first)
        filter_priority = [
            ("min_salary", "max_salary"),  # Salary (least reliable: ~1-2% coverage)
            ("experience_level",),  # Experience level
            ("remote_allowed",),  # Remote flag
            ("location",),  # Location (relax last, most important)
        ]

        # LAYER 1: Try with ALL filters
        logger.info("LAYER 1: Searching with ALL filters...")
        results = self._search_no_fallback(query, top_k, method, filters, rerank)

        if len(results) >= top_k:
            logger.info(f"✓ LAYER 1 SUCCESS: {len(results)} results (sufficient)")
            results["search_strategy"] = "exact_match"
            return results

        logger.warning(
            f"⚠ LAYER 1 INSUFFICIENT: Only {len(results)} results (need {top_k})"
        )

        # LAYER 2+: Progressive filter relaxation
        working_filters = filters.copy()

        for layer_num, filter_keys in enumerate(filter_priority, start=2):
            # Remove filter(s) from this layer
            removed_filters = []
            for key in filter_keys:
                if key in working_filters:
                    removed_filters.append(f"{key}={working_filters.pop(key)}")

            if not removed_filters:
                continue  # This filter not present, skip

            logger.info(
                f"\nLAYER {layer_num}: Relaxing filters - removing {', '.join(removed_filters)}"
            )
            logger.info(f"Remaining filters: {working_filters}")

            # Search with relaxed filters
            fetch_k = top_k * (12 - layer_num)  # Reduce multiplier as we relax
            fetch_k = max(fetch_k, top_k * 5)  # Minimum 5x multiplier

            results = self.vector_store.search(query, top_k=fetch_k, method=method)
            if working_filters:
                results = self._apply_filters(results, working_filters)

            logger.info(f"LAYER {layer_num} RESULTS: {len(results)} jobs found")

            if len(results) >= top_k:
                logger.info(f"✓ LAYER {layer_num} SUCCESS: Sufficient results!")
                results = results.head(top_k)
                results["search_strategy"] = f"relaxed_layer_{layer_num}"
                return results

            logger.warning(
                f"⚠ LAYER {layer_num} INSUFFICIENT: Only {len(results)} results"
            )

        # LAYER 6: Query only (no filters)
        logger.info("\nLAYER 6: QUERY ONLY (all filters removed)")
        results = self.vector_store.search(query, top_k=top_k * 5, method=method)

        if len(results) >= top_k:
            logger.info(f"✓ LAYER 6 SUCCESS: {len(results)} results")
            results = results.head(top_k)
            results["search_strategy"] = "query_only"
            return results

        # LAYER 7: Popular jobs (last resort)
        logger.warning(f"⚠ ALL LAYERS FAILED - Falling back to POPULAR JOBS")
        popular_jobs = self._get_popular_jobs(top_k)
        popular_jobs["search_strategy"] = "popular_fallback"

        logger.info(f"✓ FALLBACK COMPLETE: Returning {len(popular_jobs)} popular jobs")
        logger.info("=" * 80 + "\n")
        return popular_jobs

    def _get_popular_jobs(self, top_k: int = 20) -> pd.DataFrame:
        """
        Get popular/trending jobs as last resort fallback.

        Strategy:
        - Most viewed jobs
        - Recently posted
        - From top companies
        """
        logger.info("Fetching popular jobs...")

        job_data = self.vector_store.job_data.loc[
            self.vector_store.sample_indices
        ].copy()

        # Score = views (if available) + recency boost
        job_data["popularity_score"] = 0.0

        # 1. Views (if available)
        if "views" in job_data.columns:
            max_views = job_data["views"].max()
            if max_views > 0:
                job_data["popularity_score"] += (
                    job_data["views"].fillna(0) / max_views
                ) * 0.5

        # 2. Recency (if available)
        if "listed_time" in job_data.columns:
            try:
                job_data["listed_timestamp"] = pd.to_datetime(
                    job_data["listed_time"], errors="coerce"
                )
                max_time = job_data["listed_timestamp"].max()
                min_time = job_data["listed_timestamp"].min()
                time_range = (max_time - min_time).total_seconds()

                if time_range > 0:
                    job_data["recency_score"] = (
                        job_data["listed_timestamp"] - min_time
                    ).dt.total_seconds() / time_range
                    job_data["popularity_score"] += (
                        job_data["recency_score"].fillna(0) * 0.3
                    )
            except Exception as e:
                logger.warning(f"Could not parse listed_time: {e}")

        # 3. Random component (diversity)
        import numpy as np

        np.random.seed(42)
        job_data["random_score"] = np.random.random(len(job_data)) * 0.2
        job_data["popularity_score"] += job_data["random_score"]

        # Sort by popularity and return top-K
        popular = job_data.sort_values("popularity_score", ascending=False).head(top_k)
        popular["rank"] = range(1, len(popular) + 1)
        popular["similarity_score"] = 0.0  # No semantic match

        logger.info(f"Selected {len(popular)} popular jobs")
        return popular

    def _apply_filters(
        self, results: pd.DataFrame, filters: Dict[str, Any]
    ) -> pd.DataFrame:
        """
        Apply filters to search results.

        Args:
            results: Search results DataFrame
            filters: Filter criteria

        Returns:
            Filtered DataFrame
        """
        logger.info("  " + "-" * 76)
        logger.info("  APPLYING FILTERS")
        logger.info("  " + "-" * 76)
        logger.info(f"  Starting with {len(results)} results")

        filtered = results.copy()

        # Location filter
        if "location" in filters and filters["location"]:
            locations = filters["location"]
            if isinstance(locations, str):
                locations = [locations]

            logger.info(f"  FILTER: Location = {locations}")
            logger.info(
                f"    - Available locations sample: {filtered['location'].head(10).tolist()}"
            )
            logger.info(
                f"    - Unique locations count: {filtered['location'].nunique()}"
            )

            # Case-insensitive partial match
            mask = filtered["location"].str.contains(
                "|".join(locations), case=False, na=False, regex=True
            )
            before_count = len(filtered)
            filtered = filtered[mask]
            logger.info(
                f"    - Results after location filter: {len(filtered)} (removed {before_count - len(filtered)})"
            )

        # Work type filter
        if "work_type" in filters and filters["work_type"]:
            work_types = filters["work_type"]
            if isinstance(work_types, str):
                work_types = [work_types]

            logger.info(f"  FILTER: Work Type = {work_types}")
            logger.info(f"    - Column name: 'formatted_work_type'")
            logger.info(
                f"    - Available work types: {filtered['formatted_work_type'].value_counts().to_dict()}"
            )
            logger.info(
                f"    - Searching for (lowercase): {[wt.lower() for wt in work_types]}"
            )

            mask = (
                filtered["formatted_work_type"]
                .str.lower()
                .isin([wt.lower() for wt in work_types])
            )
            before_count = len(filtered)
            filtered = filtered[mask]
            logger.info(
                f"    - Results after work_type filter: {len(filtered)} (removed {before_count - len(filtered)})"
            )

        # Experience level filter
        if "experience_level" in filters and filters["experience_level"]:
            exp_levels = filters["experience_level"]
            if isinstance(exp_levels, str):
                exp_levels = [exp_levels]

            logger.info(f"  FILTER: Experience Level = {exp_levels}")
            logger.info(
                f"    - Available experience levels: {filtered['formatted_experience_level'].value_counts().head(10).to_dict()}"
            )

            mask = filtered["formatted_experience_level"].str.contains(
                "|".join(exp_levels), case=False, na=False, regex=True
            )
            before_count = len(filtered)
            filtered = filtered[mask]
            logger.info(
                f"    - Results after experience filter: {len(filtered)} (removed {before_count - len(filtered)})"
            )

        # Remote filter
        if "remote_allowed" in filters and filters["remote_allowed"]:
            logger.info(f"  FILTER: Remote Allowed = {filters['remote_allowed']}")
            logger.info(
                f"    - Remote allowed distribution: {filtered['remote_allowed'].value_counts().to_dict()}"
            )
            before_count = len(filtered)
            filtered = filtered[filtered["remote_allowed"] == 1]
            logger.info(
                f"    - Results after remote filter: {len(filtered)} (removed {before_count - len(filtered)})"
            )

        # Salary filters
        if "min_salary" in filters and filters["min_salary"] is not None:
            min_sal = filters["min_salary"]
            logger.info(f"  FILTER: Min Salary = ${min_sal:,}")
            logger.info(
                f"    - Jobs with salary data: {filtered['salary_median'].notna().sum()}"
            )
            logger.info(
                f"    - Salary range: ${filtered['salary_median'].min():.0f} - ${filtered['salary_median'].max():.0f}"
            )
            before_count = len(filtered)
            filtered = filtered[
                (filtered["salary_median"].notna())
                & (filtered["salary_median"] >= min_sal)
            ]
            logger.info(
                f"    - Results after min_salary filter: {len(filtered)} (removed {before_count - len(filtered)})"
            )

        if "max_salary" in filters and filters["max_salary"] is not None:
            max_sal = filters["max_salary"]
            logger.info(f"  FILTER: Max Salary = ${max_sal:,}")
            before_count = len(filtered)
            filtered = filtered[
                (filtered["salary_median"].notna())
                & (filtered["salary_median"] <= max_sal)
            ]
            logger.info(
                f"    - Results after max_salary filter: {len(filtered)} (removed {before_count - len(filtered)})"
            )

        # Industries filter
        if "industries" in filters and filters["industries"]:
            industries = filters["industries"]
            if isinstance(industries, str):
                industries = [industries]

            logger.info(f"  FILTER: Industries = {industries}")
            before_count = len(filtered)
            mask = filtered["industries"].str.contains(
                "|".join(industries), case=False, na=False, regex=True
            )
            filtered = filtered[mask]
            logger.info(
                f"    - Results after industries filter: {len(filtered)} (removed {before_count - len(filtered)})"
            )

        # Skills filter
        if "skills" in filters and filters["skills"]:
            skills = filters["skills"]
            if isinstance(skills, str):
                skills = [skills]

            logger.info(f"  FILTER: Skills = {skills}")
            before_count = len(filtered)
            skills = [skills]

            mask = filtered["skills"].str.contains(
                "|".join(skills), case=False, na=False, regex=True
            )
            filtered = filtered[mask]
            logger.info(
                f"    - Results after skills filter: {len(filtered)} (removed {before_count - len(filtered)})"
            )

        # Reset rank
        filtered = filtered.copy()
        filtered["rank"] = range(1, len(filtered) + 1)

        logger.info("  " + "-" * 76)
        logger.info(f"  FILTERING COMPLETE: {len(results)} → {len(filtered)} results")
        logger.info(f"  Filters applied: {list(filters.keys())}")
        logger.info("  " + "-" * 76)
        logger.info(f"  Filters applied: {list(filters.keys())}")
        logger.info("  " + "-" * 76)

        return filtered

    def _hybrid_rerank(
        self, query: str, results: pd.DataFrame, top_k: int
    ) -> pd.DataFrame:
        """
        Rerank results using hybrid TF-IDF + MiniLM scoring.

        Args:
            query: Original query
            results: Initial results from FAISS
            top_k: Number of results to return

        Returns:
            Reranked DataFrame
        """
        # Get TF-IDF scores for the candidates
        job_indices = results.index.tolist()

        # Search with TF-IDF among candidates
        tfidf_indices, tfidf_scores = self.vector_store.search_tfidf(
            query, top_k=len(results), preprocess=True
        )

        # Create score mapping
        tfidf_score_map = dict(zip(tfidf_indices, tfidf_scores))

        # Combine scores (0.4 * semantic + 0.6 * keyword)
        results = results.copy()
        results["tfidf_score"] = results.index.map(
            lambda i: tfidf_score_map.get(i, 0.0)
        )
        results["hybrid_score"] = (
            0.4 * results["similarity_score"] + 0.6 * results["tfidf_score"]
        )

        # Rerank by hybrid score
        results = results.sort_values("hybrid_score", ascending=False)
        results["rank"] = range(1, len(results) + 1)

        return results.head(top_k)

    def search_similar_jobs(
        self,
        job_id: int,
        top_k: int = 5,
        method: Literal["tfidf", "minilm", "faiss"] = "faiss",
    ) -> pd.DataFrame:
        """
        Find jobs similar to a given job.

        Args:
            job_id: ID of the reference job
            top_k: Number of similar jobs to return
            method: Search method

        Returns:
            DataFrame with similar jobs
        """
        # Get the job
        job = self.vector_store.job_data[self.vector_store.job_data.index == job_id]

        if job.empty:
            raise ValueError(f"Job ID {job_id} not found")

        # Use job's clean_text as query
        query = job.iloc[0]["clean_text"]

        # Search
        results = self.get_recommendations(
            query=query, top_k=top_k + 1, method=method  # +1 to exclude the job itself
        )

        # Exclude the original job
        results = results[results.index != job_id]

        return results.head(top_k)

    def batch_recommend(
        self,
        queries: List[str],
        top_k: int = 5,
        method: Literal["tfidf", "minilm", "faiss"] = "faiss",
    ) -> Dict[str, pd.DataFrame]:
        """
        Get recommendations for multiple queries.

        Args:
            queries: List of search queries
            top_k: Number of recommendations per query
            method: Search method

        Returns:
            Dict mapping queries to their results
        """
        results = {}
        for query in queries:
            results[query] = self.get_recommendations(
                query=query, top_k=top_k, method=method
            )
        return results

    def describe(self) -> str:
        """Get description of the recommender system."""
        stats = []

        if self.vector_store.job_data is not None:
            stats.append(f"Total jobs: {len(self.vector_store.job_data):,}")

        if self.vector_store.sample_indices is not None:
            stats.append(f"Indexed jobs: {len(self.vector_store.sample_indices):,}")

        if self.vector_store.tfidf_matrix is not None:
            stats.append(f"TF-IDF: {self.vector_store.tfidf_matrix.shape}")

        if self.vector_store.minilm_embeddings is not None:
            stats.append(f"MiniLM: {self.vector_store.minilm_embeddings.shape}")

        if self.vector_store.faiss_index is not None:
            stats.append(f"FAISS: {self.vector_store.faiss_index.ntotal} vectors")

        return "JobRecommender | " + " | ".join(stats)
