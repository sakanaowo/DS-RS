from __future__ import annotations

import re
from typing import Iterable, Tuple

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

_WORD_PATTERN = re.compile(r"[^a-z0-9\s]+")


def clean_text(text: str) -> str:
    """Normalize text by lowercasing and removing punctuation."""
    if not isinstance(text, str):
        return ""

    lowered = text.lower()
    cleaned = _WORD_PATTERN.sub(" ", lowered)
    collapsed = re.sub(r"\s+", " ", cleaned).strip()
    return collapsed


def preprocess_dataframe(df: pd.DataFrame, *, text_col: str = "description", cleaned_col: str = "clean_text") -> pd.DataFrame:
    """Create a cleaned text column on the DataFrame."""
    if text_col not in df.columns:
        raise KeyError(f"Expected '{text_col}' column in the DataFrame")

    processed = df.copy()
    processed[cleaned_col] = processed[text_col].fillna("").apply(clean_text)
    return processed


def build_vectorizer(corpus: Iterable[str], *, max_features: int = 5000) -> Tuple[TfidfVectorizer, object]:
    """Fit a TF-IDF vectorizer on the provided corpus."""
    corpus_list = list(corpus)
    has_content = any(isinstance(text, str) and text.strip() for text in corpus_list)
    if not has_content:
        raise ValueError("Corpus is empty after cleaning; add descriptions before training.")

    vectorizer = TfidfVectorizer(stop_words="english", max_features=max_features)
    tfidf_matrix = vectorizer.fit_transform(corpus_list)
    return vectorizer, tfidf_matrix
