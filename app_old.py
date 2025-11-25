from __future__ import annotations

import argparse
from pathlib import Path

from src.loader import load_jobs
from src.preprocessing import build_vectorizer, preprocess_dataframe
from src.recommender import JobRecommender
from src.utils import default_processed_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Minimal job recommender runner")
    parser.add_argument(
        "--data",
        default=str(default_processed_path()),
        help="Path to a processed CSV that contains job descriptions.",
    )
    parser.add_argument(
        "--text-column",
        default="description",
        help="Column name that contains the job description text.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of recommendations to return.",
    )
    parser.add_argument(
        "--query",
        required=True,
        help="Free-text query to find similar job descriptions for.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data_path = Path(args.data)

    if not data_path.exists():
        print(f"Processed data not found at {data_path}.")
        print("Place a CSV with job descriptions there or pass --data to point to your file.")
        return

    jobs_df = load_jobs(data_path)
    processed_df = preprocess_dataframe(jobs_df, text_col=args.text_column, cleaned_col="clean_text")

    if processed_df.empty:
        print("No rows found in the dataset after preprocessing.")
        return

    try:
        vectorizer, tfidf_matrix = build_vectorizer(processed_df["clean_text"])
    except ValueError as exc:
        print(f"Vectorization failed: {exc}")
        return
    recommender = JobRecommender(
        vectorizer=vectorizer,
        tfidf_matrix=tfidf_matrix,
        jobs_df=processed_df,
        text_col="clean_text",
    )

    results = recommender.recommend(args.query, top_k=args.top_k)

    if results.empty:
        print("No recommendations found. Check that your dataset has populated descriptions.")
        return

    print(f"Query: {args.query}")
    print(recommender.describe())
    print("Top matches:")
    for _, row in results.iterrows():
        title = row.get("title") or "Untitled role"
        score = row["score"]
        print(f"- {title} (score={score:.3f})")


if __name__ == "__main__":
    main()
