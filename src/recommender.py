"""
Job Recommendation Module

This module provides the main recommendation engine that uses VectorStore
for similarity search and applies filters to refine results.
"""

from __future__ import annotations

from typing import Optional, List, Dict, Any, Literal

import pandas as pd
import numpy as np

from .vector_store import VectorStore
from .preprocessing import clean_text


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
    ) -> pd.DataFrame:
        """
        Get job recommendations based on query and filters.

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

        Returns:
            DataFrame with recommended jobs, sorted by relevance
        """
        # Get initial candidates (fetch more for filtering)
        # With 50k indexed jobs, we can use lower multiplier than with 10k
        if filters and len(filters) > 0:
            # Fetch 10-15x more to ensure enough candidates after filtering
            # Reduced from 20x since we have 5x more coverage (50k vs 10k)
            fetch_k = top_k * 12
        else:
            fetch_k = top_k

        results = self.vector_store.search(query, top_k=fetch_k, method=method)

        # Apply filters
        if filters:
            results = self._apply_filters(results, filters)

        # Rerank if requested
        if rerank and method == "faiss":
            results = self._hybrid_rerank(query, results, top_k)

        # Return top-K
        return results.head(top_k)

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
        filtered = results.copy()

        # Location filter
        if "location" in filters and filters["location"]:
            locations = filters["location"]
            if isinstance(locations, str):
                locations = [locations]

            # Case-insensitive partial match
            mask = filtered["location"].str.contains(
                "|".join(locations), case=False, na=False, regex=True
            )
            filtered = filtered[mask]

        # Work type filter
        if "work_type" in filters and filters["work_type"]:
            work_types = filters["work_type"]
            if isinstance(work_types, str):
                work_types = [work_types]

            mask = (
                filtered["formatted_work_type"]
                .str.lower()
                .isin([wt.lower() for wt in work_types])
            )
            filtered = filtered[mask]

        # Experience level filter
        if "experience_level" in filters and filters["experience_level"]:
            exp_levels = filters["experience_level"]
            if isinstance(exp_levels, str):
                exp_levels = [exp_levels]

            mask = filtered["formatted_experience_level"].str.contains(
                "|".join(exp_levels), case=False, na=False, regex=True
            )
            filtered = filtered[mask]

        # Remote filter
        if "remote_allowed" in filters and filters["remote_allowed"]:
            filtered = filtered[filtered["remote_allowed"] == 1]

        # Salary filters
        if "min_salary" in filters and filters["min_salary"] is not None:
            min_sal = filters["min_salary"]
            filtered = filtered[
                (filtered["salary_median"].notna())
                & (filtered["salary_median"] >= min_sal)
            ]

        if "max_salary" in filters and filters["max_salary"] is not None:
            max_sal = filters["max_salary"]
            filtered = filtered[
                (filtered["salary_median"].notna())
                & (filtered["salary_median"] <= max_sal)
            ]

        # Industries filter
        if "industries" in filters and filters["industries"]:
            industries = filters["industries"]
            if isinstance(industries, str):
                industries = [industries]

            mask = filtered["industries"].str.contains(
                "|".join(industries), case=False, na=False, regex=True
            )
            filtered = filtered[mask]

        # Skills filter
        if "skills" in filters and filters["skills"]:
            skills = filters["skills"]
            if isinstance(skills, str):
                skills = [skills]

            mask = filtered["skills"].str.contains(
                "|".join(skills), case=False, na=False, regex=True
            )
            filtered = filtered[mask]

        # Reset rank
        filtered = filtered.copy()
        filtered["rank"] = range(1, len(filtered) + 1)

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
