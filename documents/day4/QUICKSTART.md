# Day 4: Quick Start Guide

## 🚀 Run Notebook (Recommended)

```bash
# Open Jupyter notebook
code notebooks/3_model_experiment.ipynb

# Run all cells (Shift+Enter on each cell)
# OR: Run > Run All Cells
```

**Runtime**: 2-5 minutes  
**Output**: Models in `models/`, plot in `images/`

---

## 🐍 Run Python Script (Alternative)

```bash
# 10k sample (fast, ~2 mins)
python src/vectorize.py --sample 10000

# Full dataset (slow, ~15 mins)
python src/vectorize.py --full
```

---

## 📊 What Gets Created

```
models/
├── tfidf_vectorizer.pkl      # TF-IDF model
├── tfidf_matrix.npz          # Sparse vectors
├── minilm_embeddings.npy     # Dense embeddings
├── faiss_index.bin           # Fast search index
└── sample_indices.pkl        # Job IDs

images/
└── model_comparison.png      # Benchmark plot
```

---

## ✅ Verify Success

```bash
# Check models created
ls -lh models/

# Should see 5 files, ~46 MB total
# tfidf_vectorizer.pkl, tfidf_matrix.npz,
# minilm_embeddings.npy, faiss_index.bin,
# sample_indices.pkl
```

---

## 🔍 Test Search

```python
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer

# Load models
with open('models/tfidf_vectorizer.pkl', 'rb') as f:
    tfidf = pickle.load(f)

embeddings = np.load('models/minilm_embeddings.npy')
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

# Search
query = "Python developer with machine learning"
query_emb = model.encode([query], normalize_embeddings=True)
similarities = np.dot(embeddings, query_emb.T).flatten()
top_5 = similarities.argsort()[::-1][:5]

print(f"Top 5 job indices: {top_5}")
```

---

## 🐛 Troubleshooting

**Error**: `ModuleNotFoundError: sentence_transformers`  
**Fix**: `pip install sentence-transformers`

**Error**: `No module named 'faiss'`  
**Fix**: `pip install faiss-cpu`

**Error**: `Out of memory`  
**Fix**: Reduce sample size in notebook cell 6:

```python
SAMPLE_SIZE = 5000  # Instead of 10000
```

---

## 📚 Next: Day 5

After completing Day 4, proceed to:

1. Create `src/vector_store.py` (load models)
2. Create `src/recommender.py` (search + filters)
3. Write unit tests
4. Evaluate Precision@K

**Estimated Time**: 6-8 hours

---

## 📖 Full Documentation

- **Complete Guide**: `documents/day4/README.md`
- **Summary**: `documents/day4/completion_summary.md`
- **Notebook**: `notebooks/3_model_experiment.ipynb`
- **Script**: `src/vectorize.py`
