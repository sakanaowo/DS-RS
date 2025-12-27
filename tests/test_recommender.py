"""
Unit Tests for Vector Store and Recommender (TF-IDF only)

Run with: pytest tests/test_recommender.py -v
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from src.vector_store import VectorStore
from src.recommender import JobRecommender


# Fixtures
@pytest.fixture(scope="module")
def vector_store():
    """Load VectorStore once for all tests."""
    store = VectorStore()
    store.load_all()
    return store


@pytest.fixture(scope="module")
def recommender():
    """Load JobRecommender once for all tests."""
    rec = JobRecommender(auto_load=True)
    return rec


# VectorStore Tests
class TestVectorStore:
    """Test VectorStore functionality."""

    def test_load_components(self, vector_store):
        """Test that all components are loaded."""
        assert vector_store.tfidf_vectorizer is not None
        assert vector_store.tfidf_matrix is not None
        assert vector_store.job_data is not None
        assert vector_store.sample_indices is not None

    def test_tfidf_search(self, vector_store):
        """Test TF-IDF search returns valid results."""
        indices, scores = vector_store.search_tfidf("Python developer", top_k=5)

        assert len(indices) == 5
        assert len(scores) == 5
        assert all(scores >= 0)
        assert all(scores <= 1)
        # Scores should be in descending order
        assert all(scores[i] >= scores[i + 1] for i in range(len(scores) - 1))

    def test_search_with_dataframe(self, vector_store):
        """Test search returns properly formatted DataFrame."""
        results = vector_store.search("software engineer", top_k=3)

        assert isinstance(results, pd.DataFrame)
        assert len(results) == 3
        assert "similarity_score" in results.columns
        assert "rank" in results.columns
        assert "title" in results.columns
        assert all(results["rank"] == [1, 2, 3])


# JobRecommender Tests
class TestJobRecommender:
    """Test JobRecommender functionality."""

    def test_initialization(self, recommender):
        """Test recommender initializes correctly."""
        assert recommender.vector_store is not None
        assert recommender.vector_store.job_data is not None

    def test_basic_recommendations(self, recommender):
        """Test basic recommendation without filters."""
        results = recommender.get_recommendations(
            query="Python backend developer", top_k=5
        )

        assert isinstance(results, pd.DataFrame)
        assert len(results) <= 5
        assert "similarity_score" in results.columns
        assert "rank" in results.columns

    def test_location_filter(self, recommender):
        """Test location filter works."""
        results = recommender.get_recommendations(
            query="software engineer", top_k=10, filters={"location": "New York"}
        )

        # All results should contain "New York" in location
        if not results.empty:
            assert all(
                "new york" in str(loc).lower()
                for loc in results["location"]
                if pd.notna(loc)
            )

    def test_work_type_filter(self, recommender):
        """Test work type filter."""
        results = recommender.get_recommendations(
            query="developer", top_k=10, filters={"work_type": "Full-time"}
        )

        if not results.empty:
            assert all(
                str(wt).lower() == "full-time"
                for wt in results["work_type"]
                if pd.notna(wt)
            )

    def test_remote_filter(self, recommender):
        """Test remote jobs filter."""
        results = recommender.get_recommendations(
            query="remote developer", top_k=10, filters={"remote_allowed": True}
        )

        if not results.empty:
            assert all(results["remote_allowed"] == 1)

    def test_salary_filter(self, recommender):
        """Test salary range filter."""
        results = recommender.get_recommendations(
            query="engineer",
            top_k=10,
            filters={"min_salary": 80000, "max_salary": 150000},
        )

        if not results.empty:
            assert all(
                80000 <= sal <= 150000
                for sal in results["salary_median"]
                if pd.notna(sal)
            )

    def test_multiple_filters(self, recommender):
        """Test combining multiple filters."""
        results = recommender.get_recommendations(
            query="Python developer",
            top_k=10,
            filters={
                "work_type": "Full-time",
                "remote_allowed": True,
                "min_salary": 60000,
            },
        )

        # Should return DataFrame even if no matches
        assert isinstance(results, pd.DataFrame)

    def test_search_similar_jobs(self, recommender):
        """Test finding similar jobs to a given job."""
        # Get a job ID from the sample
        job_id = recommender.vector_store.sample_indices[0]

        results = recommender.search_similar_jobs(job_id=job_id, top_k=5)

        assert isinstance(results, pd.DataFrame)
        assert len(results) <= 5
        # Original job should not be in results
        assert job_id not in results.index

    def test_batch_recommend(self, recommender):
        """Test batch recommendations."""
        queries = ["Python developer", "Data scientist", "Product manager"]

        results = recommender.batch_recommend(queries, top_k=3)

        assert isinstance(results, dict)
        assert len(results) == 3
        for query in queries:
            assert query in results
            assert isinstance(results[query], pd.DataFrame)
            assert len(results[query]) <= 3

    def test_describe(self, recommender):
        """Test describe method."""
        description = recommender.describe()

        assert isinstance(description, str)
        assert "JobRecommender" in description
        assert "jobs" in description.lower()


# Edge Cases
class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_query(self, recommender):
        """Test empty query handling."""
        results = recommender.get_recommendations(query="", top_k=5)
        assert isinstance(results, pd.DataFrame)

    def test_very_long_query(self, recommender):
        """Test with very long query."""
        long_query = " ".join(["Python developer"] * 100)
        results = recommender.get_recommendations(query=long_query, top_k=5)
        assert isinstance(results, pd.DataFrame)

    def test_special_characters(self, recommender):
        """Test query with special characters."""
        results = recommender.get_recommendations(query="C++ developer @#$%", top_k=5)
        assert isinstance(results, pd.DataFrame)

    def test_top_k_larger_than_dataset(self, vector_store):
        """Test requesting more results than available."""
        # Request more than sample size
        results = vector_store.search("developer", top_k=20000)
        # Should return all available
        assert len(results) <= len(vector_store.sample_indices)

    def test_invalid_job_id(self, recommender):
        """Test invalid job ID raises error."""
        with pytest.raises(ValueError):
            recommender.search_similar_jobs(job_id=999999999)


# Performance Tests
class TestPerformance:
    """Test performance characteristics."""

    def test_search_speed(self, recommender):
        """Test that search completes in reasonable time."""
        import time

        start = time.time()
        recommender.get_recommendations("Python developer", top_k=10)
        elapsed = time.time() - start

        # Should complete in under 1 second
        assert elapsed < 1.0

    def test_batch_speed(self, recommender):
        """Test batch processing speed."""
        import time

        queries = ["Python", "Java", "Data", "Manager", "Designer"]

        start = time.time()
        recommender.batch_recommend(queries, top_k=5)
        elapsed = time.time() - start

        # Should complete in under 3 seconds
        assert elapsed < 3.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
