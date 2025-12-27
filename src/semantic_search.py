"""
Semantic Job Search Engine using Sentence Transformers

Day 4 Implementation - Semantic search with embeddings

Features:
- Use sentence-transformers for semantic similarity
- Generate embeddings for job titles and descriptions
- Cosine similarity search
- Cache embeddings for fast retrieval
- Handle synonyms and semantic relationships

Model: all-MiniLM-L6-v2 (lightweight, fast, 384-dim embeddings)
"""

from pathlib import Path
from typing import List, Dict, Optional, Tuple
import time
import pickle

import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from .loader import load_normalized_tables, PROCESSED_DIR


class SemanticJobSearch:
    """
    Semantic search engine using sentence embeddings.

    Architecture:
    1. Load pre-trained sentence transformer model
    2. Generate embeddings for job titles + descriptions
    3. Search using cosine similarity
    4. Cache embeddings to disk for fast loading

    Model: all-MiniLM-L6-v2 (22MB, 384-dim, fast)
    """

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        verbose: bool = True,
        sample_size: Optional[int] = None,
    ):
        """
        Initialize semantic search engine.

        Args:
            model_name: Sentence transformer model name
            verbose: If True, print loading progress
            sample_size: If set, use only this many jobs (for testing)
        """
        self.model_name = model_name
        self.verbose = verbose
        self.sample_size = sample_size

        self.model = None
        self.jobs = None
        self.embeddings = None

        # Cache paths
        self.embeddings_cache_path = (
            PROCESSED_DIR / f"embeddings_{model_name.split('/')[-1]}.pkl"
        )

    def load_model(self):
        """Load sentence transformer model."""
        if self.verbose:
            print(f"Loading sentence transformer model: {self.model_name}")

        start_time = time.time()
        self.model = SentenceTransformer(self.model_name)
        elapsed = time.time() - start_time

        if self.verbose:
            print(f"✓ Model loaded in {elapsed:.2f}s")

    def load_data(self):
        """Load job data."""
        if self.verbose:
            print("Loading job data...")

        tables = load_normalized_tables()
        self.jobs = tables["jobs"]

        # Apply sampling if specified
        if self.sample_size is not None and self.sample_size < len(self.jobs):
            if self.verbose:
                print(f"⚠️  SAMPLING: Using {self.sample_size:,} jobs")
            self.jobs = self.jobs.head(self.sample_size).copy()

        if self.verbose:
            print(f"✓ Loaded {len(self.jobs):,} jobs")

    def _create_search_text(self, row: pd.Series) -> str:
        """
        Create search text from job row.

        Combines title (3x weight) + description (1x weight).

        Args:
            row: Job row

        Returns:
            Combined search text
        """
        title = str(row["title"]) if pd.notna(row["title"]) else ""
        description = str(row["description"]) if pd.notna(row["description"]) else ""

        # Weight title 3x by repeating
        search_text = f"{title} {title} {title} {description}"

        return search_text

    def encode_jobs(self, force_recompute: bool = False):
        """
        Generate embeddings for all jobs.

        Args:
            force_recompute: If True, recompute even if cache exists
        """
        # Check cache
        if not force_recompute and self.embeddings_cache_path.exists():
            if self.verbose:
                print(f"Loading cached embeddings from {self.embeddings_cache_path}")

            with open(self.embeddings_cache_path, "rb") as f:
                cache_data = pickle.load(f)

            # Verify cache matches current jobs
            cached_job_ids = cache_data.get("job_ids", [])
            current_job_ids = self.jobs["job_id"].tolist()

            if cached_job_ids == current_job_ids:
                self.embeddings = cache_data["embeddings"]
                if self.verbose:
                    print(f"✓ Loaded {len(self.embeddings)} cached embeddings")
                return
            else:
                if self.verbose:
                    print("⚠️  Cache mismatch, recomputing...")

        # Compute embeddings
        if self.verbose:
            print("Generating embeddings...")

        start_time = time.time()

        # Create search texts
        search_texts = self.jobs.apply(self._create_search_text, axis=1).tolist()

        # Encode
        if self.verbose:
            print(f"  Encoding {len(search_texts):,} job descriptions...")

        self.embeddings = self.model.encode(
            search_texts,
            show_progress_bar=self.verbose,
            batch_size=32,
            convert_to_numpy=True,
        )

        elapsed = time.time() - start_time

        if self.verbose:
            print(f"✓ Generated {len(self.embeddings)} embeddings in {elapsed:.2f}s")
            print(f"  Embedding dim: {self.embeddings.shape[1]}")

        # Save to cache
        if self.verbose:
            print(f"Saving embeddings to cache...")

        cache_data = {
            "job_ids": self.jobs["job_id"].tolist(),
            "embeddings": self.embeddings,
            "model_name": self.model_name,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        with open(self.embeddings_cache_path, "wb") as f:
            pickle.dump(cache_data, f)

        if self.verbose:
            print(f"✓ Cached to {self.embeddings_cache_path}")

    def search(
        self, query: str, top_k: int = 10, filters: Optional[Dict] = None
    ) -> pd.DataFrame:
        """
        Search for jobs using semantic similarity.

        Args:
            query: Search query
            top_k: Number of results to return
            filters: Optional filters (not implemented for semantic-only search)

        Returns:
            DataFrame with top-k jobs and similarity scores
        """
        if self.embeddings is None:
            raise RuntimeError("Embeddings not loaded. Call encode_jobs() first.")

        if not query or query.strip() == "":
            # Empty query - return random sample
            sample_size = min(top_k, len(self.jobs))
            sample_jobs = self.jobs.sample(n=sample_size)
            sample_jobs["semantic_score"] = 0.0
            return sample_jobs

        start_time = time.time()

        # Encode query
        query_embedding = self.model.encode([query], convert_to_numpy=True)

        # Calculate cosine similarity
        similarities = cosine_similarity(query_embedding, self.embeddings)[0]

        # Get top-k
        top_k = min(top_k, len(similarities))
        top_indexes = np.argsort(similarities)[::-1][:top_k]

        # Create results DataFrame
        results_df = self.jobs.iloc[top_indexes].copy()
        results_df["semantic_score"] = similarities[top_indexes]

        elapsed = time.time() - start_time

        if self.verbose:
            print(f"✓ Found {len(results_df)} results in {elapsed:.3f}s")

        return results_df


def demo_semantic_search():
    """Demo function to test semantic search."""
    print("\n" + "=" * 60)
    print("SEMANTIC JOB SEARCH - DEMO")
    print("=" * 60)

    # Initialize
    print("\nInitializing semantic search (may take a minute first time)...")
    searcher = SemanticJobSearch(sample_size=10000, verbose=True)
    searcher.load_model()
    searcher.load_data()
    searcher.encode_jobs()

    print("\n" + "=" * 60)
    print("TEST 1: Semantic Similarity - Synonyms")
    print("=" * 60)

    # Test synonym matching (developer vs engineer)
    queries = ["software developer", "software engineer"]

    for query in queries:
        print(f"\nQuery: '{query}'")
        results = searcher.search(query, top_k=3)

        for idx, row in results.iterrows():
            print(f"  {row['title']}")
            print(f"    Score: {row['semantic_score']:.3f}")
            print(f"    Company: {row['company_name']}")

    print("\n" + "=" * 60)
    print("TEST 2: Semantic Understanding")
    print("=" * 60)

    # Test semantic understanding
    queries = [
        "machine learning expert",  # Should match data scientist, ML engineer
        "frontend UI designer",  # Should match UI/UX, web designer
        "sales account executive",  # Should match account manager, sales rep
    ]

    for query in queries:
        print(f"\nQuery: '{query}'")
        results = searcher.search(query, top_k=3)

        for idx, row in results.iterrows():
            print(f"  {row['title']}")
            print(f"    Score: {row['semantic_score']:.3f}")

    print("\n" + "=" * 60)
    print("✓ DEMO COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    demo_semantic_search()
