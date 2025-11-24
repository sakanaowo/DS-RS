from __future__ import annotations

import re
import unicodedata
from typing import Iterable, Optional, Tuple

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

_WORD_PATTERN = re.compile(r"[^a-z0-9\s]+")
_HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
_URL_PATTERN = re.compile(r"https?://\S+|www\.\S+")
_NEWLINE_PATTERN = re.compile(r"[\r\n]+")

# Common English stopwords
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "he",
    "in",
    "is",
    "it",
    "its",
    "of",
    "on",
    "that",
    "the",
    "to",
    "was",
    "will",
    "with",
    "the",
    "this",
    "but",
    "they",
    "have",
    "had",
    "what",
    "when",
    "where",
    "who",
    "which",
    "why",
    "how",
}


def remove_html_tags(text: str) -> str:
    """Remove HTML tags from text."""
    if not isinstance(text, str):
        return ""
    return _HTML_TAG_PATTERN.sub(" ", text)


def remove_urls(text: str) -> str:
    """Remove URLs from text."""
    if not isinstance(text, str):
        return ""
    return _URL_PATTERN.sub(" ", text)


def normalize_unicode(text: str) -> str:
    """Normalize unicode characters to ASCII."""
    if not isinstance(text, str):
        return ""
    # Normalize to NFKD form and encode to ASCII, ignoring non-ASCII characters
    normalized = unicodedata.normalize("NFKD", text)
    return normalized.encode("ascii", "ignore").decode("ascii")


def remove_extra_whitespace(text: str) -> str:
    """Collapse multiple whitespaces and newlines into single spaces."""
    if not isinstance(text, str):
        return ""
    # Replace newlines with spaces
    text = _NEWLINE_PATTERN.sub(" ", text)
    # Collapse multiple spaces
    return re.sub(r"\s+", " ", text).strip()


def remove_stopwords(text: str, stopwords: Optional[set] = None) -> str:
    """Remove common stopwords from text."""
    if not isinstance(text, str):
        return ""
    if stopwords is None:
        stopwords = STOPWORDS
    words = text.split()
    filtered = [w for w in words if w not in stopwords]
    return " ".join(filtered)


def clean_text(text: str, remove_stops: bool = False) -> str:
    """
    Comprehensive text cleaning pipeline:
    1. Remove HTML tags
    2. Remove URLs
    3. Normalize unicode to ASCII
    4. Convert to lowercase
    5. Remove special characters and punctuation
    6. Remove extra whitespace
    7. Optionally remove stopwords
    """
    if not isinstance(text, str):
        return ""

    # Step 1: Remove HTML tags
    text = remove_html_tags(text)

    # Step 2: Remove URLs
    text = remove_urls(text)

    # Step 3: Normalize unicode
    text = normalize_unicode(text)

    # Step 4: Lowercase
    text = text.lower()

    # Step 5: Remove special characters (keep alphanumeric and spaces)
    text = _WORD_PATTERN.sub(" ", text)

    # Step 6: Remove extra whitespace
    text = remove_extra_whitespace(text)

    # Step 7: Optionally remove stopwords
    if remove_stops:
        text = remove_stopwords(text)

    return text


def parse_location(location: str) -> dict:
    """
    Parse location string into city, state, and country components.

    Examples:
        "New York, NY" -> {"city": "New York", "state": "NY", "country": "United States"}
        "United States" -> {"city": None, "state": None, "country": "United States"}
        "London, England" -> {"city": "London", "state": "England", "country": "United Kingdom"}
    """
    if not isinstance(location, str) or not location.strip():
        return {"city": None, "state": None, "country": "Unknown"}

    location = location.strip()

    # Handle "United States" case (just country)
    if location == "United States":
        return {"city": None, "state": None, "country": "United States"}

    # Split by comma
    parts = [p.strip() for p in location.split(",")]

    if len(parts) == 1:
        # Only one part - assume it's country
        return {"city": None, "state": None, "country": parts[0]}
    elif len(parts) == 2:
        # Two parts - city, state or city, country
        city, state_or_country = parts
        # If second part is 2 letters, likely a US state
        if len(state_or_country) == 2 and state_or_country.isupper():
            return {"city": city, "state": state_or_country, "country": "United States"}
        else:
            return {"city": city, "state": None, "country": state_or_country}
    else:
        # Three or more parts - take first as city, second as state, last as country
        return {
            "city": parts[0],
            "state": parts[1] if len(parts) > 1 else None,
            "country": parts[-1],
        }


def prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Comprehensive data cleaning and feature preparation pipeline:
    1. Handle missing values
    2. Remove duplicates
    3. Clean text fields
    4. Parse and standardize location
    5. Create derived features

    Args:
        df: Raw DataFrame with job postings

    Returns:
        Cleaned DataFrame ready for vectorization
    """
    print(f"Starting with {len(df):,} rows...")

    # Create a copy to avoid modifying original
    cleaned = df.copy()

    # 1. Filter out jobs missing critical fields (title or description)
    required_cols = ["title", "description"]
    for col in required_cols:
        if col in cleaned.columns:
            before = len(cleaned)
            cleaned = cleaned[cleaned[col].notna() & (cleaned[col].str.strip() != "")]
            dropped = before - len(cleaned)
            if dropped > 0:
                print(f"Dropped {dropped:,} rows with missing/empty '{col}'")

    # 2. Remove duplicates based on job_id (if available) or title + company
    if "job_id" in cleaned.columns:
        before = len(cleaned)
        cleaned = cleaned.drop_duplicates(subset=["job_id"], keep="first")
        dropped = before - len(cleaned)
        if dropped > 0:
            print(f"Dropped {dropped:,} duplicate job_id rows")
    else:
        # Fallback to title + company_id if job_id not available
        dup_cols = ["title"]
        if "company_id" in cleaned.columns:
            dup_cols.append("company_id")
        before = len(cleaned)
        cleaned = cleaned.drop_duplicates(subset=dup_cols, keep="first")
        dropped = before - len(cleaned)
        if dropped > 0:
            print(f"Dropped {dropped:,} duplicate rows based on {dup_cols}")

    # 3. Clean text fields
    text_fields = ["title", "description", "skills_desc"]
    for field in text_fields:
        if field in cleaned.columns:
            print(f"Cleaning text field: {field}")
            cleaned[f"{field}_clean"] = (
                cleaned[field]
                .fillna("")
                .apply(lambda x: clean_text(x, remove_stops=False))
            )

    # 4. Create combined content field for vectorization
    # Combine title (weighted higher) + description + skills
    content_parts = []
    if "title_clean" in cleaned.columns:
        # Repeat title 2x to give it more weight
        content_parts.append(cleaned["title_clean"] + " " + cleaned["title_clean"])
    if "description_clean" in cleaned.columns:
        content_parts.append(cleaned["description_clean"])
    if "skills_desc_clean" in cleaned.columns:
        content_parts.append(cleaned["skills_desc_clean"])

    if content_parts:
        cleaned["content"] = content_parts[0]
        for part in content_parts[1:]:
            cleaned["content"] = cleaned["content"] + " " + part
        print("Created combined 'content' field")

    # 5. Parse and standardize location
    if "location" in cleaned.columns:
        print("Parsing location field...")
        location_parsed = cleaned["location"].fillna("Unknown").apply(parse_location)
        cleaned["city"] = location_parsed.apply(lambda x: x["city"])
        cleaned["state"] = location_parsed.apply(lambda x: x["state"])
        cleaned["country"] = location_parsed.apply(lambda x: x["country"])

    # 6. Standardize categorical fields
    if "formatted_work_type" in cleaned.columns:
        # Convert category to string first to allow fillna with new value
        if cleaned["formatted_work_type"].dtype.name == "category":
            cleaned["work_type"] = (
                cleaned["formatted_work_type"].astype(str).replace("nan", "Unknown")
            )
        else:
            cleaned["work_type"] = cleaned["formatted_work_type"].fillna("Unknown")

    if "formatted_experience_level" in cleaned.columns:
        # Convert category to string first to allow fillna with new value
        if cleaned["formatted_experience_level"].dtype.name == "category":
            cleaned["experience_level"] = (
                cleaned["formatted_experience_level"]
                .astype(str)
                .replace("nan", "Unknown")
            )
        else:
            cleaned["experience_level"] = cleaned["formatted_experience_level"].fillna(
                "Unknown"
            )

    # 7. Create binary flags for missing data
    if "min_salary" in cleaned.columns or "max_salary" in cleaned.columns:
        has_salary = False
        if "min_salary" in cleaned.columns:
            has_salary = cleaned["min_salary"].notna()
        if "max_salary" in cleaned.columns:
            has_salary = has_salary | cleaned["max_salary"].notna()
        cleaned["has_salary_info"] = has_salary.astype(int)

    if "remote_allowed" in cleaned.columns:
        cleaned["has_remote_flag"] = cleaned["remote_allowed"].notna().astype(int)
        # Fill NA before converting to avoid ValueError with nullable Int8
        cleaned["is_remote"] = (cleaned["remote_allowed"].fillna(0) == 1).astype(int)

    # 8. Normalize salary to yearly for comparison
    if all(col in cleaned.columns for col in ["med_salary", "pay_period"]):

        def normalize_salary(row):
            salary = row.get("med_salary")
            period = row.get("pay_period")

            if pd.isna(salary) or pd.isna(period):
                return None

            # Convert to yearly
            multipliers = {
                "YEARLY": 1,
                "MONTHLY": 12,
                "BIWEEKLY": 26,
                "WEEKLY": 52,
                "HOURLY": 2080,  # Assuming 40 hours/week, 52 weeks/year
            }

            return salary * multipliers.get(period, 1)

        cleaned["normalized_salary"] = cleaned.apply(normalize_salary, axis=1)
        print("Created normalized_salary field")

    print(f"Cleaning complete. Final dataset: {len(cleaned):,} rows")
    return cleaned


def preprocess_dataframe(
    df: pd.DataFrame, *, text_col: str = "description", cleaned_col: str = "clean_text"
) -> pd.DataFrame:
    """Create a cleaned text column on the DataFrame."""
    if text_col not in df.columns:
        raise KeyError(f"Expected '{text_col}' column in the DataFrame")

    processed = df.copy()
    processed[cleaned_col] = processed[text_col].fillna("").apply(clean_text)
    return processed


def build_vectorizer(
    corpus: Iterable[str], *, max_features: int = 5000
) -> Tuple[TfidfVectorizer, object]:
    """Fit a TF-IDF vectorizer on the provided corpus."""
    corpus_list = list(corpus)
    has_content = any(isinstance(text, str) and text.strip() for text in corpus_list)
    if not has_content:
        raise ValueError(
            "Corpus is empty after cleaning; add descriptions before training."
        )

    vectorizer = TfidfVectorizer(stop_words="english", max_features=max_features)
    tfidf_matrix = vectorizer.fit_transform(corpus_list)
    return vectorizer, tfidf_matrix
