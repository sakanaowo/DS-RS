"""
Day 4: Vectorization Pipeline
Generate TF-IDF and MiniLM embeddings for job recommendations

Usage:
    python src/vectorize.py --sample 10000  # Use 10k sample
    python src/vectorize.py --full           # Encode all jobs (slower)
"""

from pathlib import Path
import argparse
import time
import pickle
import warnings

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.sparse import save_npz
from sentence_transformers import SentenceTransformer

warnings.filterwarnings("ignore")


def load_data(data_path: Path, sample_size: int = None):
    """Load cleaned jobs data"""
    print(f"Loading cleaned dataset from {data_path}...")
    df = pd.read_parquet(data_path)

    if sample_size and sample_size < len(df):
        df = df.sample(n=sample_size, random_state=42)
        print(f"Using sample of {len(df):,} jobs")
    else:
        print(f"Using full dataset: {len(df):,} jobs")

    return df


def create_tfidf_vectors(texts, models_dir: Path):
    """Create TF-IDF vectors"""
    print("\n[1/3] Creating TF-IDF vectors...")
    start = time.time()

    tfidf = TfidfVectorizer(
        max_features=5000,
        ngram_range=(1, 2),
        min_df=5,
        max_df=0.8,
        stop_words="english",
        lowercase=True,
        dtype=np.float32,
    )

    tfidf_matrix = tfidf.fit_transform(texts)
    elapsed = time.time() - start

    print(f"  ✓ Completed in {elapsed:.2f}s")
    print(f"  - Matrix shape: {tfidf_matrix.shape}")
    print(f"  - Vocabulary: {len(tfidf.vocabulary_):,} terms")
    print(
        f"  - Sparsity: {(1 - tfidf_matrix.nnz / (tfidf_matrix.shape[0] * tfidf_matrix.shape[1])) * 100:.2f}%"
    )
    print(f"  - Memory: {tfidf_matrix.data.nbytes / 1024**2:.1f} MB")

    # Save
    with open(models_dir / "tfidf_vectorizer.pkl", "wb") as f:
        pickle.dump(tfidf, f)
    save_npz(models_dir / "tfidf_matrix.npz", tfidf_matrix)
    print(f"  ✓ Saved to {models_dir}")

    return tfidf, tfidf_matrix


def create_minilm_embeddings(texts, models_dir: Path):
    """Create MiniLM embeddings"""
    print("\n[2/3] Creating MiniLM embeddings...")
    start = time.time()

    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    print(f"  - Model: all-MiniLM-L6-v2")
    print(f"  - Embedding dim: {model.get_sentence_embedding_dimension()}")

    embeddings = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    elapsed = time.time() - start
    print(f"\n  ✓ Completed in {elapsed:.2f}s")
    print(f"  - Embeddings shape: {embeddings.shape}")
    print(f"  - Memory: {embeddings.nbytes / 1024**2:.1f} MB")
    print(f"  - Speed: {len(texts)/elapsed:.0f} docs/sec")

    # Save
    np.save(models_dir / "minilm_embeddings.npy", embeddings)
    print(f"  ✓ Saved to {models_dir}")

    return embeddings


def create_faiss_index(embeddings, models_dir: Path):
    """Create FAISS index"""
    print("\n[3/3] Creating FAISS index...")

    try:
        import faiss
    except ImportError:
        print("  ! FAISS not installed, skipping...")
        return None

    start = time.time()
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings.astype("float32"))
    elapsed = time.time() - start

    print(f"  ✓ Completed in {elapsed:.2f}s")
    print(f"  - Index size: {index.ntotal:,} vectors")
    print(f"  - Index dim: {index.d}")

    # Save
    faiss.write_index(index, str(models_dir / "faiss_index.bin"))
    print(f"  ✓ Saved to {models_dir}")

    return index


def main():
    parser = argparse.ArgumentParser(description="Vectorize jobs for recommendation")
    parser.add_argument(
        "--sample",
        type=int,
        default=10000,
        help="Sample size (default: 10000, use 0 for full dataset)",
    )
    parser.add_argument(
        "--full", action="store_true", help="Use full dataset (same as --sample 0)"
    )
    args = parser.parse_args()

    # Paths
    project_root = Path(__file__).parent.parent
    data_path = project_root / "data" / "processed" / "clean_jobs.parquet"
    models_dir = project_root / "models"
    models_dir.mkdir(exist_ok=True)

    # Sample size
    sample_size = None if args.full else (args.sample if args.sample > 0 else None)

    print("=" * 70)
    print("DAY 4: VECTORIZATION PIPELINE")
    print("=" * 70)

    # Load data
    df = load_data(data_path, sample_size)
    texts = df["clean_text"].fillna("").values

    # Create vectors
    tfidf, tfidf_matrix = create_tfidf_vectors(texts, models_dir)
    embeddings = create_minilm_embeddings(texts, models_dir)
    index = create_faiss_index(embeddings, models_dir)

    # Save metadata
    sample_indices = df.index.tolist()
    with open(models_dir / "sample_indices.pkl", "wb") as f:
        pickle.dump(sample_indices, f)
    print(f"\n✓ Saved sample indices ({len(sample_indices):,} jobs)")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Dataset: {len(df):,} jobs")
    print(
        f"TF-IDF: {tfidf_matrix.shape[1]} features, {tfidf_matrix.data.nbytes/1024**2:.1f} MB"
    )
    print(f"MiniLM: {embeddings.shape[1]} dims, {embeddings.nbytes/1024**2:.1f} MB")
    if index:
        print(f"FAISS: {index.ntotal:,} vectors indexed")

    print(f"\nArtifacts saved to: {models_dir}")
    print("  - tfidf_vectorizer.pkl")
    print("  - tfidf_matrix.npz")
    print("  - minilm_embeddings.npy")
    print("  - faiss_index.bin")
    print("  - sample_indices.pkl")

    print("\n✅ Day 4 Complete - Ready for Recommendation Engine")
    print("=" * 70)


if __name__ == "__main__":
    main()
