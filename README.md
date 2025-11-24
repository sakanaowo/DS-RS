# DS-RS - Intelligent Job Matching System

Hệ thống gợi ý việc làm dựa trên nội dung (Content-Based Filtering) sử dụng Vector Search và Embeddings.

## 🎯 Project Overview

- **Dataset:** LinkedIn Job Postings (~124K jobs)
- **Tech Stack:** Python, Pandas, Scikit-learn, Sentence-Transformers, Streamlit
- **Approach:** Content-based recommendation với TF-IDF hoặc semantic embeddings
- **UI:** Streamlit web application với filters và explainability

## 📁 Project Structure

```
DS-RS/
├── data/
│   ├── archive/           # Original dataset snapshot
│   ├── raw/               # Working copy of data
│   └── processed/         # Cleaned data & vector cache
├── documents/
│   ├── plan.md            # Main project specification & timeline
│   ├── day1/              # Day 1 audit documentation (if exists)
│   └── day2/              # Day 2 cleaning documentation
│       ├── README.md                  # Quick start guide
│       ├── day2_completion_summary.md # Detailed summary
│       ├── logic_verification.md      # Code review
│       └── verification_report.md     # Compliance check
├── notebooks/
│   ├── 1_data_cleaning.ipynb     # Data audit & cleaning
│   ├── 2_eda_visualization.ipynb # Exploratory analysis
│   └── 3_model_experiment.ipynb  # Model development
├── scripts/
│   ├── README.md          # Scripts documentation
│   └── run_cleaning.py    # CLI for data cleaning pipeline
├── src/
│   ├── loader.py          # Data loading & enrichment
│   ├── preprocessing.py   # Text cleaning & feature engineering
│   ├── recommender.py     # Recommendation engine
│   └── vector_store.py    # Embeddings cache (TBD)
├── reports/               # Generated reports (audit, EDA, etc.)
├── images/                # Visualizations & charts
├── app.py                 # Streamlit application (main entry point)
└── requirements.txt       # Python dependencies
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run Data Cleaning (Day 2)

```bash
# Quick test with sample
python scripts/run_cleaning.py --sample 5000

# Process full dataset
python scripts/run_cleaning.py
```

**Output:** `data/processed/clean_jobs.parquet` (~40-60 MB)

### 3. Explore Data (Day 3)

```bash
jupyter lab notebooks/2_eda_visualization.ipynb
```

### 4. Launch Web App (Day 7+)

```bash
streamlit run app.py
```

## 📚 Documentation

- **[Project Plan](documents/plan.md)** - Complete specification & timeline
- **[Day 2 Guide](documents/day2/README.md)** - Data cleaning quick start
- **[Copilot Instructions](.github/copilot_instructions.md)** - Development guidelines
- **[Data Audit](reports/data_audit.md)** - Dataset analysis (auto-generated)

## 🗓️ Progress Tracker

- [x] **Day 1:** Setup & Data Audit
- [x] **Day 2:** Data Cleaning
- [ ] **Day 3:** EDA & Visualization
- [ ] **Day 4-6:** Model Building
- [ ] **Day 7-9:** UI & Reporting
- [ ] **Day 10:** Packaging & Delivery

## 🔧 Development Guidelines

- Follow PEP8 conventions (snake_case, proper spacing)
- Use relative paths (no hardcoded absolute paths)
- Scripts go in `scripts/`, modules in `src/`
- Day-specific docs in `documents/dayX/`
- Keep `plan.md` synchronized with progress
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
