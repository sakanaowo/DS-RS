"""
Vector Store Module for Job Recommendation System

This module handles loading and managing vectorized job data,
including TF-IDF matrices, MiniLM embeddings, and FAISS indices.
"""

from __future__ import annotations

import pickle
from pathlib import Path
from typing import List, Tuple, Optional, Literal

import faiss
import numpy as np
import pandas as pd
from scipy.sparse import load_npz, csr_matrix
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .preprocessing import clean_text


class VectorStore:
    """
    Manages vector representations of job postings and performs similarity search.

    Supports three search methods:
    - TF-IDF: Traditional keyword-based sparse vectors
    - MiniLM: Semantic embeddings using sentence-transformers
    - FAISS: Fast approximate nearest neighbor search
    """

    def __init__(
        self, models_dir: Path | str = "models", data_dir: Path | str = "data/processed"
    ):
        """
        Initialize VectorStore.

        Args:
            models_dir: Directory containing saved models and vectors
            data_dir: Directory containing processed data files
        """

        # Find project root (directory containing both 'models' and 'data' folders)
        def find_project_root():
            """Find project root by looking for models and data directories."""
            current = Path.cwd()
            # Try current directory and parents
            for path in [current] + list(current.parents):
                if (path / "models").exists() and (path / "data").exists():
                    return path
            # If not found, assume we're already in the right place
            return current

        project_root = find_project_root()

        # Convert to absolute paths
        self.models_dir = Path(models_dir)
        if not self.models_dir.is_absolute():
            self.models_dir = project_root / models_dir

        self.data_dir = Path(data_dir)
        if not self.data_dir.is_absolute():
            self.data_dir = project_root / data_dir  # Initialize empty attributes
        self.tfidf_vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix: Optional[csr_matrix] = None
        self.minilm_model: Optional[SentenceTransformer] = None
        self.minilm_embeddings: Optional[np.ndarray] = None
        self.faiss_index: Optional[faiss.IndexFlatIP] = None
        self.job_data: Optional[pd.DataFrame] = None
        self.sample_indices: Optional[List[int]] = None

    def load_tfidf(self) -> None:
        """Load TF-IDF vectorizer and matrix."""
        print("Loading TF-IDF vectorizer...")
        vectorizer_path = self.models_dir / "tfidf_vectorizer.pkl"
        with open(vectorizer_path, "rb") as f:
            self.tfidf_vectorizer = pickle.load(f)

        print("Loading TF-IDF matrix...")
        matrix_path = self.models_dir / "tfidf_matrix.npz"
        self.tfidf_matrix = load_npz(matrix_path)

        print(f"✓ TF-IDF loaded: {self.tfidf_matrix.shape} matrix")

    def load_minilm(
        self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    ) -> None:
        """
        Load MiniLM model and embeddings.

        Args:
            model_name: HuggingFace model identifier
        """
        print(f"Loading MiniLM model ({model_name})...")
        self.minilm_model = SentenceTransformer(model_name)

        print("Loading MiniLM embeddings...")
        embeddings_path = self.models_dir / "minilm_embeddings.npy"
        self.minilm_embeddings = np.load(embeddings_path)

        print(f"✓ MiniLM loaded: {self.minilm_embeddings.shape} embeddings")

    def load_faiss(self) -> None:
        """Load FAISS index for fast similarity search."""
        print("Loading FAISS index...")
        index_path = self.models_dir / "faiss_index.bin"
        self.faiss_index = faiss.read_index(str(index_path))

        print(f"✓ FAISS loaded: {self.faiss_index.ntotal} vectors indexed")

    def load_job_data(self) -> None:
        """Load processed job data."""
        print("Loading job data...")
        data_path = self.data_dir / "clean_jobs.parquet"
        self.job_data = pd.read_parquet(data_path)

        # Create clean_text if not exists
        if "clean_text" not in self.job_data.columns:
            print("Creating clean_text column...")
            self.job_data["clean_text"] = (
                self.job_data["title_clean"].fillna("")
                + " "
                + self.job_data["description_clean"].fillna("")
                + " "
                + self.job_data["skills_desc_clean"].fillna("")
            ).str.strip()

        print(f"✓ Job data loaded: {len(self.job_data):,} jobs")

    def load_sample_indices(self) -> None:
        """Load indices of sampled jobs used for training."""
        print("Loading sample indices...")
        indices_path = self.models_dir / "sample_indices.pkl"
        with open(indices_path, "rb") as f:
            self.sample_indices = pickle.load(f)

        print(f"✓ Sample indices loaded: {len(self.sample_indices):,} indices")

    def load_all(self) -> None:
        """Load all components (convenience method)."""
        self.load_job_data()
        self.load_sample_indices()
        self.load_tfidf()
        self.load_minilm()
        self.load_faiss()
        print("\n✓ All components loaded successfully!")

    def search_tfidf(
        self, query: str, top_k: int = 10, preprocess: bool = True
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Search using TF-IDF vectorization.

        Args:
            query: Search query text
            top_k: Number of results to return
            preprocess: Whether to clean the query text

        Returns:
            Tuple of (indices, similarities) arrays
        """
        if self.tfidf_vectorizer is None or self.tfidf_matrix is None:
            raise ValueError("TF-IDF not loaded. Call load_tfidf() first.")

        # Preprocess query
        if preprocess:
            query = clean_text(query)

        # Vectorize query
        query_vec = self.tfidf_vectorizer.transform([query])

        # Compute similarities
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()

        # Get top-K indices
        top_indices = similarities.argsort()[::-1][:top_k]
        top_scores = similarities[top_indices]

        return top_indices, top_scores

    def search_minilm(
        self, query: str, top_k: int = 10, preprocess: bool = True
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Search using MiniLM embeddings.

        Args:
            query: Search query text
            top_k: Number of results to return
            preprocess: Whether to clean the query text

        Returns:
            Tuple of (indices, similarities) arrays
        """
        if self.minilm_model is None or self.minilm_embeddings is None:
            raise ValueError("MiniLM not loaded. Call load_minilm() first.")

        # Preprocess query
        if preprocess:
            query = clean_text(query)

        # Encode query
        query_emb = self.minilm_model.encode([query], normalize_embeddings=True)

        # Compute similarities (dot product since normalized)
        similarities = np.dot(self.minilm_embeddings, query_emb.T).flatten()

        # Get top-K indices
        top_indices = similarities.argsort()[::-1][:top_k]
        top_scores = similarities[top_indices]

        return top_indices, top_scores

    def search_faiss(
        self, query: str, top_k: int = 10, preprocess: bool = True
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Search using FAISS index (fastest method).

        Args:
            query: Search query text
            top_k: Number of results to return
            preprocess: Whether to clean the query text

        Returns:
            Tuple of (indices, similarities) arrays
        """
        if self.faiss_index is None or self.minilm_model is None:
            raise ValueError(
                "FAISS not loaded. Call load_faiss() and load_minilm() first."
            )

        # Preprocess query
        if preprocess:
            query = clean_text(query)

        # Encode query
        query_emb = self.minilm_model.encode([query], normalize_embeddings=True).astype(
            "float32"
        )

        # Search
        similarities, indices = self.faiss_index.search(query_emb, top_k)

        return indices[0], similarities[0]

    def search(
        self,
        query: str,
        top_k: int = 10,
        method: Literal["tfidf", "minilm", "faiss"] = "faiss",
        preprocess: bool = True,
    ) -> pd.DataFrame:
        """
        Search for similar jobs using specified method.

        Args:
            query: Search query text
            top_k: Number of results to return
            method: Search method ("tfidf", "minilm", or "faiss")
            preprocess: Whether to clean the query text

        Returns:
            DataFrame with search results and metadata
        """
        if self.job_data is None:
            raise ValueError("Job data not loaded. Call load_job_data() first.")

        if self.sample_indices is None:
            raise ValueError(
                "Sample indices not loaded. Call load_sample_indices() first."
            )

        # Perform search
        if method == "tfidf":
            indices, scores = self.search_tfidf(query, top_k, preprocess)
        elif method == "minilm":
            indices, scores = self.search_minilm(query, top_k, preprocess)
        elif method == "faiss":
            indices, scores = self.search_faiss(query, top_k, preprocess)
        else:
            raise ValueError(
                f"Unknown method: {method}. Use 'tfidf', 'minilm', or 'faiss'."
            )

        # Map sample indices to original dataset
        original_indices = [self.sample_indices[i] for i in indices]

        # Get job data
        results = self.job_data.loc[original_indices].copy()
        results["similarity_score"] = scores
        results["rank"] = range(1, len(results) + 1)

        # Reorder columns for better display
        display_cols = [
            "rank",
            "similarity_score",
            "title",
            "company_name_x",
            "location",
            "work_type",
            "formatted_experience_level",
            "skills",
            "industries",
            "salary_median",
            "remote_allowed",
        ]

        # Only include columns that exist
        available_cols = [col for col in display_cols if col in results.columns]
        other_cols = [col for col in results.columns if col not in available_cols]
        results = results[available_cols + other_cols]

        return results


# Convenience function for quick testing
def quick_search(
    query: str, top_k: int = 5, method: Literal["tfidf", "minilm", "faiss"] = "faiss"
) -> pd.DataFrame:
    """
    Quick search function for testing.

    Args:
        query: Search query
        top_k: Number of results
        method: Search method

    Returns:
        DataFrame with results
    """
    store = VectorStore()
    store.load_all()
    return store.search(query, top_k, method)
