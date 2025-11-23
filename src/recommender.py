from __future__ import annotations

from typing import Optional

import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from .preprocessing import clean_text


class JobRecommender:
    """Recommend similar job postings using cosine similarity over TF-IDF vectors."""

    def __init__(self, *, vectorizer, tfidf_matrix, jobs_df: pd.DataFrame, text_col: str = "clean_text"):
        self.vectorizer = vectorizer
        self.tfidf_matrix = tfidf_matrix
        self.jobs_df = jobs_df.reset_index(drop=True)
        self.text_col = text_col

    def recommend(self, query: str, top_k: int = 5) -> pd.DataFrame:
        if self.jobs_df.empty:
            return self.jobs_df.copy()

        cleaned_query = clean_text(query)
        if not cleaned_query:
            return self.jobs_df.iloc[0:0].assign(score=[])

        query_vector = self.vectorizer.transform([cleaned_query])
        scores = cosine_similarity(query_vector, self.tfidf_matrix).flatten()

        top_indices = scores.argsort()[::-1][:top_k]
        results = self.jobs_df.iloc[top_indices].copy()
        results["score"] = scores[top_indices]
        return results

    def describe(self) -> str:
        """Short string describing the current model state."""
        total_docs = self.tfidf_matrix.shape[0]
        total_terms = self.tfidf_matrix.shape[1]
        return f"TF-IDF matrix: {total_docs} documents x {total_terms} terms"
