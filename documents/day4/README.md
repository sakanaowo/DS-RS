# Day 4: Model Experimentation - Vectorization

**Status**: ✅ Notebook Created  
**Date**: November 24, 2025  
**Notebook**: `notebooks/3_model_experiment.ipynb`

## Overview

This notebook implements and compares two vectorization approaches for job recommendation:

1. **TF-IDF (Baseline)**: Traditional keyword-based vectorization
2. **MiniLM (Advanced)**: Semantic embeddings using sentence-transformers
3. **FAISS**: Fast similarity search indexing

## Notebook Structure

### 1. Setup & Configuration (Cell 1-3)

- Import libraries (pandas, numpy, scikit-learn, matplotlib, seaborn)
- Configure paths (data, models, images)
- Setup display options

### 2. Load Cleaned Dataset (Cell 4-5)

- Load `data/processed/clean_jobs.parquet` (123,842 jobs)
- Check data quality and memory usage
- Inspect sample job

### 3. TF-IDF Baseline (Cells 6-10)

- Create 10k sample for fast iteration
- Fit TF-IDF vectorizer (5000 features, bigrams)
- Compute similarity matrix
- Test search function
- Benchmark performance

### 4. Sentence-Transformers MiniLM (Cells 11-15)

- Install sentence-transformers library
- Load `all-MiniLM-L6-v2` model (384 dimensions)
- Encode all documents to embeddings
- Test semantic search
- Compare with TF-IDF

### 5. Comparison & Visualization (Cells 16-17)

- Create benchmark table
- Visualize training time, memory usage, dimensions
- Save plot to `images/model_comparison.png`

### 6. Quality Evaluation (Cell 18)

- Test 5 diverse queries
- Compare TF-IDF vs MiniLM results
- Evaluate relevance

### 7. Save Models & Embeddings (Cell 19)

- Save TF-IDF vectorizer → `models/tfidf_vectorizer.pkl`
- Save TF-IDF matrix → `models/tfidf_matrix.npz`
- Save MiniLM embeddings → `models/minilm_embeddings.npy`
- Save sample indices → `models/sample_indices.pkl`

### 8. FAISS Integration (Cells 20-24)

- Install FAISS library
- Build IndexFlatIP for inner product search
- Test FAISS search (sub-millisecond latency)
- Save index → `models/faiss_index.bin`

### 9. Summary (Cell 25)

- Print comprehensive summary
- List all saved artifacts
- Recommend next steps for Day 5

## Expected Results

### Performance Benchmarks (10k jobs)

| Method | Training Time | Vector Dim | Memory | Search Speed | Sparse |
| ------ | ------------- | ---------- | ------ | ------------ | ------ |
| TF-IDF | ~2-3s         | 5000       | ~15 MB | ~10ms        | Yes    |
| MiniLM | ~30-60s       | 384        | ~15 MB | ~5ms         | No     |
| FAISS  | ~0.1s         | 384        | ~15 MB | <1ms         | No     |

### Key Findings

1. **TF-IDF**:

   - ✓ Fast training
   - ✓ Low memory (sparse)
   - ✗ Keyword-only matching
   - ✗ No semantic understanding

2. **MiniLM**:

   - ✓ Semantic understanding
   - ✓ Better relevance
   - ✗ Slower encoding
   - ✓ Dense vectors

3. **FAISS**:
   - ✓ Ultra-fast search (<1ms)
   - ✓ Scalable to millions
   - ✓ Multiple index types
   - ✓ Production-ready

## How to Run

### Prerequisites

```bash
# Ensure Day 2 cleaning is complete
ls data/processed/clean_jobs.parquet  # Should exist (707 MB)
```

### Run Notebook

1. Open `notebooks/3_model_experiment.ipynb`
2. Run all cells sequentially (Runtime: ~2-5 minutes for 10k sample)
3. Check `models/` directory for saved artifacts
4. Check `images/model_comparison.png` for visualization

### Expected Outputs

**Files Created**:

- `models/tfidf_vectorizer.pkl` (~1 MB)
- `models/tfidf_matrix.npz` (~15 MB)
- `models/minilm_embeddings.npy` (~15 MB)
- `models/sample_indices.pkl` (~100 KB)
- `models/faiss_index.bin` (~15 MB)
- `images/model_comparison.png` (~100 KB)

**Total**: ~46 MB

## Sample Queries

The notebook tests with these queries:

1. "Python backend developer with API experience"
2. "Registered nurse with emergency room experience"
3. "Sales manager with B2B software experience"
4. "Data scientist machine learning deep learning"
5. "Project manager agile scrum certification"

## Dependencies

Required packages (will be auto-installed in notebook):

```
pandas>=2.0.0
numpy>=1.24.0
scikit-learn>=1.3.0
matplotlib>=3.7.0
seaborn>=0.12.0
sentence-transformers>=2.2.0
faiss-cpu>=1.7.4
```

## Next Steps (Day 5)

After completing this notebook:

1. **Create `src/vector_store.py`**:

   - Load saved models
   - Implement `VectorStore` class
   - Add `search()` method with filtering

2. **Create `src/recommender.py`**:

   - Implement `get_recommendations()` function
   - Add hybrid ranking (TF-IDF + MiniLM)
   - Support filters (location, work_type, salary)

3. **Write Unit Tests**:

   - Test vector store loading
   - Test search accuracy
   - Test filter logic

4. **Evaluate Precision@K**:
   - Create labeled test set
   - Compute Precision@5, Precision@10
   - Compare TF-IDF vs MiniLM vs Hybrid

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'sentence_transformers'"

**Solution**: The notebook auto-installs it. If that fails, run:

```bash
pip install sentence-transformers
```

### Issue: "FAISS not found"

**Solution**: Install CPU version:

```bash
pip install faiss-cpu
```

### Issue: "Out of memory"

**Solution**: Reduce `SAMPLE_SIZE` in cell 6:

```python
SAMPLE_SIZE = 5000  # Instead of 10000
```

### Issue: "Model download slow"

**Solution**: sentence-transformers downloads ~90MB model on first run. Be patient or use offline model.

## Notes

- **Sample Size**: Notebook uses 10k jobs for speed. For production, encode all 123k jobs (~10-15 minutes)
- **GPU Support**: MiniLM can use GPU if available (`device='cuda'`)
- **Model Choice**: MiniLM-L6-v2 is small (90MB) and fast. For better quality, try `all-mpnet-base-v2` (420MB)
- **FAISS Index**: Using FlatIP for accuracy. For speed on large datasets, use `IndexIVFFlat` or `IndexHNSWFlat`

## References

- [sentence-transformers](https://www.sbert.net/)
- [FAISS](https://github.com/facebookresearch/faiss)
- [TF-IDF](https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html)

---

**Status**: Ready to run ✅  
**Estimated Time**: 2-5 minutes  
**Next**: Day 5 - Recommendation Engine
