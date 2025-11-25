# DS-RS - Intelligent Job Recommendation System

Hệ thống gợi ý việc làm thông minh sử dụng Vector Search và Semantic Embeddings để tìm kiếm công việc phù hợp.

## 🎯 Project Overview

- **Dataset:** LinkedIn Job Postings (123,842 jobs)
- **Tech Stack:** Python, Pandas, Scikit-learn, Sentence-Transformers, FAISS, Streamlit
- **Approach:** Content-based recommendation với 3 phương pháp (TF-IDF, MiniLM, FAISS)
- **Performance:** 94.3% Precision@5, <50ms search time
- **UI:** Streamlit web application với filters và real-time search

## ✨ Features

- 🔍 **3 Search Methods:** TF-IDF (keyword), MiniLM (semantic), FAISS (fast vector search)
- 🎯 **7 Filter Types:** Location, Work Type, Experience, Remote, Salary, Industries, Skills
- ⚡ **Fast Search:** <50ms response time (FAISS: 14.6ms, MiniLM: 13.3ms)
- 🎨 **Interactive UI:** Clean Streamlit interface with job cards and statistics
- 📊 **High Accuracy:** 94.3% P@5 and 90.0% P@10 (exceeds 70% target)
- 💡 **Explainability:** Highlighted matched skills and relevance scores

## 📁 Project Structure

```
DS-RS/
├── data/
│   ├── archive/           # Original dataset snapshot
│   ├── raw/               # Working copy of data
│   └── processed/         # Cleaned data (clean_jobs.parquet)
├── models/                # Saved models & embeddings (42MB)
│   ├── tfidf_vectorizer.pkl
│   ├── tfidf_matrix.npz
│   ├── minilm_embeddings.npy
│   ├── faiss_index.bin
│   └── sample_indices.pkl
├── documents/
│   ├── plan.md            # Main project specification & timeline
│   ├── day2/              # Day 2 cleaning documentation
│   ├── day3/              # Day 3 EDA documentation
│   ├── day4/              # Day 4 model experiments
│   └── day5/              # Day 5 evaluation reports
├── notebooks/
│   ├── 1_data_cleaning.ipynb     # Data audit & cleaning
│   ├── 2_eda_visualization.ipynb # Exploratory analysis
│   ├── 3_model_experiment.ipynb  # Model benchmarking
│   └── 4_evaluation.ipynb        # System evaluation
├── src/
│   ├── loader.py          # Data loading & enrichment
│   ├── preprocessing.py   # Text cleaning & feature engineering
│   ├── vector_store.py    # Vector management (TF-IDF, MiniLM, FAISS)
│   └── recommender.py     # Recommendation engine with filters
├── tests/
│   └── test_recommender.py # Unit tests (20+ tests)
├── reports/               # Generated reports (audit, EDA)
├── images/                # Visualizations & evaluation charts
├── app.py                 # Streamlit web application ⭐
└── requirements.txt       # Python dependencies
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
conda activate base  # Or your preferred environment
pip install -r requirements.txt
```

**Key packages:**

- pandas, numpy, scikit-learn
- sentence-transformers (MiniLM)
- faiss-cpu (fast vector search)
- streamlit (web UI)

### 2. Run the Application

```bash
streamlit run app.py
```

Or with conda:

```bash

```

Access the app at: **http://localhost:8501**

### 3. Use the System

1. **Enter query** in sidebar (e.g., "Python backend developer with API experience")
2. **Select search method:**
   - 🚀 FAISS (recommended) - Fastest & most accurate
   - 🧠 MiniLM - Semantic understanding
   - 📝 TF-IDF - Keyword matching
3. **Apply filters** (optional):
   - Location, Work Type, Experience Level
   - Remote/On-site, Minimum Salary
4. **Click "Search Jobs"** to get recommendations

### 4. Explore Notebooks

```bash
jupyter lab
```

- `1_data_cleaning.ipynb` - Data audit & cleaning
- `2_eda_visualization.ipynb` - Exploratory analysis
- `3_model_experiment.ipynb` - Model benchmarking
- `4_evaluation.ipynb` - System evaluation (7 personas)

## 📊 Performance Metrics

### Precision (7 Test Personas)

- **P@5:** 94.3% (Target: 70% → +34% above)
- **P@10:** 90.0% (Target: 70% → +29% above)
- **Perfect Scores:** 5/7 personas achieved 100% P@5

### Speed (Average Response Time)

- **FAISS:** 14.6ms ⚡ (6.8x faster than target)
- **MiniLM:** 13.3ms ⚡ (7.5x faster than target)
- **TF-IDF:** 49.1ms ✅ (2.0x faster than target)

### Dataset

- **Total Jobs:** 123,842
- **Indexed Jobs:** 10,000 (sample for faster demos)
- **Companies:** ~30,000
- **Locations:** ~20,000
- **Industries:** 422
- **Skills:** 36 categories

## 📚 Documentation

- **[Project Plan](documents/plan.md)** - Complete specification & timeline
- **[Day 2: Cleaning](documents/day2/)** - Data cleaning process
- **[Day 3: EDA](documents/day3/)** - Exploratory analysis
- **[Day 4: Models](documents/day4/)** - Model experiments
- **[Day 5: Evaluation](documents/day5/)** - System evaluation & benchmarks
- **[Copilot Instructions](.github/copilot_instructions.md)** - Development guidelines

## 🗓️ Progress Tracker

- [x] **Day 1:** Setup & Data Audit
- [x] **Day 2:** Data Cleaning (123K jobs processed)
- [x] **Day 3:** EDA & Visualization (7 charts generated)
- [x] **Day 4:** Model Experiments (TF-IDF, MiniLM, FAISS)
- [x] **Day 5:** Evaluation & Testing (94.3% P@5)
- [x] **Day 6:** Streamlit UI (Complete)
- [ ] **Day 7:** Advanced Features
- [ ] **Day 8:** Final Report
- [ ] **Day 9:** Packaging & Deployment

## 🛠️ Development

### Run Tests

```bash
pytest tests/
```

### Code Structure

```python
from src.recommender import JobRecommender

# Initialize
rec = JobRecommender(auto_load=True)

# Get recommendations
results = rec.get_recommendations(
    query="Machine Learning Engineer with Python",
    method="faiss",
    top_k=10,
    filters={'work_type': 'Full-time', 'min_salary': 80000}
)
```

## 🎯 Use Cases

### Example Queries

- "Python backend developer with API and database experience"
- "Data scientist machine learning deep learning pandas"
- "DevOps engineer AWS Docker Kubernetes CI/CD automation"
- "Frontend developer React JavaScript TypeScript"
- "Registered nurse with patient care and emergency experience"

### Filters

- **Location:** "New York", "San Francisco", "Remote"
- **Work Type:** Full-time, Part-time, Contract, Internship
- **Experience:** Entry level, Mid-Senior level, Director
- **Remote:** Remote Only, On-site Only, Any
- **Salary:** Minimum $50K, $80K, $100K, etc.

## 📈 Technical Highlights

1. **Vector Store:** Efficient management of 3 embedding types
2. **Hybrid Search:** Combines keyword + semantic matching
3. **Smart Filtering:** 7 filter types without sacrificing speed
4. **Caching:** @st.cache_resource for instant UI reload
5. **Scalable:** FAISS index supports millions of jobs

## 🔧 Development Guidelines

- Follow PEP8 conventions (snake_case, proper spacing)
- Use relative paths (no hardcoded absolute paths)
- Scripts go in `scripts/`, modules in `src/`
- Day-specific docs in `documents/dayX/`
- Keep `plan.md` synchronized with progress
- Always activate conda before running commands
- Use Parquet for processed data (smaller, faster)

## 📊 Key Features

### Data Pipeline

- ✅ Comprehensive text cleaning (HTML, URLs, Unicode)
- ✅ Location parsing (city/state/country)
- ✅ Feature engineering (salary normalization, binary flags)
- ✅ Multi-table joins (skills, industries, salaries, companies)

### Recommendation Engine (TBD)

- [ ] TF-IDF or Sentence-Transformer embeddings
- [ ] Cosine similarity search
- [ ] Filter by location, work type, salary, industry
- [ ] Explainability (highlight matching skills/keywords)

### Web Interface (TBD)

- [ ] Search bar for job queries
- [ ] Sidebar filters
- [ ] Job cards with details
- [ ] Dataset summary panel

## 🤝 Contributing

This is a course project. Follow the guidelines in `.github/copilot_instructions.md` when making changes.

## 📄 License

Educational project - for course submission only.
