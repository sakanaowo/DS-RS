# Job Recommendation System - Redesign Plan

**Date**: December 26, 2025  
**Status**: 🔄 REDESIGN IN PROGRESS  
**Approach**: Hybrid (BM25 + Optional Embeddings)

---

## 📋 EXECUTIVE SUMMARY

### Current Problems
1. ❌ **Data pipeline aggregates relationships** → Skills/industries gộp thành strings
2. ❌ **Filters applied post-search** → Poor performance, unreliable results
3. ❌ **Progressive fallback is band-aid** → Doesn't fix root cause
4. ❌ **Vector embeddings on concatenated text** → Loses structure

### New Design
1. ✅ **Keep normalized tables** → Proper relational structure
2. ✅ **BM25 with field weights** → Title^3, Skills^2, Description^1
3. ✅ **Filters as query clauses** → Hard constraints at query time
4. ✅ **Optional embeddings layer** → Hybrid scoring (0.7 BM25 + 0.3 semantic)

---

## 🎯 DESIGN PRINCIPLES

1. **Simplicity First**: BM25 baseline before adding complexity
2. **Filters Must Work**: Filters as query clauses, not post-processing
3. **Honest UX**: 0 results is OK if filters too strict (no misleading fallbacks)
4. **Measurable**: Every change must improve Precision@K
5. **Maintainable**: Clear code, good tests, documentation

---

## 📊 NEW DATA SCHEMA

### Core Tables (Normalized)

```python
# 1. jobs (main table)
jobs = pd.DataFrame({
    'job_id': int,
    'title': str,
    'description': str,
    'company_id': int,
    'company_name': str,
    'location': str,
    'city': str,
    'state': str,
    'country': str,
    'work_type': str,  # Full-time, Part-time, Contract, etc.
    'experience_level': str,  # Entry, Mid-Senior, Director, Executive
    'remote_allowed': bool,
    'min_salary': float,  # Nullable
    'max_salary': float,  # Nullable
    'pay_period': str,  # YEARLY, HOURLY, MONTHLY
    'normalized_salary_yearly': float,  # Calculated field
    'views': int,
    'applies': int,
    'listed_time': datetime,
    'closed_time': datetime,  # Nullable
})

# 2. job_skills (many-to-many)
job_skills = pd.DataFrame({
    'job_id': int,
    'skill_id': int,
})

# 3. skills (lookup)
skills = pd.DataFrame({
    'skill_id': int,
    'skill_abr': str,  # 'IT', 'SALE', 'MGMT', etc.
    'skill_name': str,  # 'Information Technology', 'Sales', etc.
})

# 4. job_industries (many-to-many)
job_industries = pd.DataFrame({
    'job_id': int,
    'industry_id': int,
})

# 5. industries (lookup)
industries = pd.DataFrame({
    'industry_id': int,
    'industry_name': str,  # 'Hospitals and Health Care', 'IT Services', etc.
})

# 6. job_benefits (many-to-many)
job_benefits = pd.DataFrame({
    'job_id': int,
    'benefit_type': str,  # '401(k)', 'Medical insurance', etc.
})

# 7. companies (metadata)
companies = pd.DataFrame({
    'company_id': int,
    'company_name': str,
    'description': str,
    'company_size': int,
    'employee_count': int,
    'follower_count': int,
    'city': str,
    'state': str,
    'country': str,
    'specialities': str,  # Comma-separated (OK here since display only)
})
```

### Why This Schema?

**Advantages**:
- ✅ **No data duplication**: Skills/industries not repeated in every row
- ✅ **Exact filtering**: Can filter by skill_id = 'IT' without string matching
- ✅ **Efficient storage**: 213k job_skills rows vs 123k jobs with concatenated strings
- ✅ **Query flexibility**: Can join on demand, or use separate indexes

**Storage Estimate**:
```
jobs:           123k rows × 25 cols ≈ 50 MB
job_skills:     213k rows × 2 cols ≈ 3 MB
job_industries: 164k rows × 2 cols ≈ 3 MB
job_benefits:   67k rows × 2 cols ≈ 1 MB
companies:      24k rows × 15 cols ≈ 10 MB
------------------------
Total:          ~70 MB (vs current 493 MB postings.csv)
```

---

## 🔍 NEW SEARCH ARCHITECTURE

### Component 1: BM25 Index (Primary)

**Library**: `rank_bm25` (simple, pure Python)

**Index Structure**:
```python
from rank_bm25 import BM25Okapi

# Separate corpus for each field
corpus_title = [job['title'] for job in jobs]
corpus_description = [job['description'] for job in jobs]
corpus_skills = [get_skills_text(job['job_id']) for job in jobs]  # Join from job_skills

# Build indexes
bm25_title = BM25Okapi(tokenize(corpus_title))
bm25_description = BM25Okapi(tokenize(corpus_description))
bm25_skills = BM25Okapi(tokenize(corpus_skills))
```

**Scoring**:
```python
def bm25_search(query, top_k=1000):
    query_tokens = tokenize(query)
    
    # Score each field
    scores_title = bm25_title.get_scores(query_tokens)
    scores_description = bm25_description.get_scores(query_tokens)
    scores_skills = bm25_skills.get_scores(query_tokens)
    
    # Weighted combination
    final_scores = (
        3.0 * scores_title +
        1.0 * scores_description +
        2.0 * scores_skills
    )
    
    # Get top-K
    top_indices = np.argsort(final_scores)[-top_k:][::-1]
    return jobs.iloc[top_indices], final_scores[top_indices]
```

**Field Weights Rationale**:
- **Title: 3.0** → Most important (concise, descriptive)
- **Skills: 2.0** → Very important for matching
- **Description: 1.0** → Less important (noisy, long)

---

### Component 2: Filters (Hard Constraints)

**Apply filters BEFORE ranking, not after**:

```python
def apply_filters(jobs_df, filters):
    """Apply filters as boolean masks (hard constraints)."""
    filtered = jobs_df.copy()
    
    # Location filter
    if 'location' in filters:
        loc = filters['location'].lower()
        mask = (
            filtered['city'].str.lower().str.contains(loc, na=False) |
            filtered['state'].str.lower().str.contains(loc, na=False) |
            filtered['country'].str.lower().str.contains(loc, na=False)
        )
        filtered = filtered[mask]
    
    # Work type filter
    if 'work_type' in filters:
        work_types = filters['work_type']
        if isinstance(work_types, str):
            work_types = [work_types]
        filtered = filtered[filtered['work_type'].isin(work_types)]
    
    # Experience filter
    if 'experience_level' in filters:
        filtered = filtered[filtered['experience_level'] == filters['experience_level']]
    
    # Remote filter
    if 'remote_allowed' in filters:
        filtered = filtered[filtered['remote_allowed'] == filters['remote_allowed']]
    
    # Salary range filter
    if 'min_salary' in filters and 'max_salary' in filters:
        # Only filter jobs that HAVE salary info
        has_salary = filtered['normalized_salary_yearly'].notna()
        in_range = (
            (filtered['normalized_salary_yearly'] >= filters['min_salary']) &
            (filtered['normalized_salary_yearly'] <= filters['max_salary'])
        )
        filtered = filtered[has_salary & in_range]
    
    # Skills filter (requires JOIN)
    if 'skills' in filters:
        required_skills = filters['skills']
        if isinstance(required_skills, str):
            required_skills = [required_skills]
        
        # Get jobs that have ALL required skills
        job_ids_with_skills = (
            job_skills[job_skills['skill_abr'].isin(required_skills)]
            .groupby('job_id')
            .size()
        )
        job_ids_with_all = job_ids_with_skills[job_ids_with_skills == len(required_skills)].index
        filtered = filtered[filtered['job_id'].isin(job_ids_with_all)]
    
    return filtered
```

**Key Change**: Filters applied BEFORE search or as pre-filter → Much more efficient

---

### Component 3: Semantic Layer (Optional)

**Only if time permits, for "Nâng cao" points**

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

# Pre-compute embeddings (offline)
embeddings = model.encode(corpus_content, show_progress_bar=True)
np.save('models/semantic_embeddings.npy', embeddings)

# At search time
def semantic_search(query, top_k=1000):
    query_embedding = model.encode([query])
    scores = cosine_similarity(query_embedding, embeddings)[0]
    top_indices = np.argsort(scores)[-top_k:][::-1]
    return jobs.iloc[top_indices], scores[top_indices]
```

**Hybrid Scoring**:
```python
def hybrid_search(query, filters, top_k=20, alpha=0.7):
    """
    Hybrid: BM25 (70%) + Semantic (30%)
    
    Args:
        alpha: Weight for BM25 (1-alpha for semantic)
    """
    # 1. Apply filters first
    filtered_jobs = apply_filters(jobs, filters)
    
    if len(filtered_jobs) == 0:
        return pd.DataFrame()  # Honest: 0 results
    
    # 2. BM25 search on filtered subset
    bm25_results, bm25_scores = bm25_search(query, filtered_jobs)
    
    # 3. Semantic search on filtered subset (optional)
    if use_semantic:
        semantic_results, semantic_scores = semantic_search(query, filtered_jobs)
        
        # Normalize scores
        bm25_scores_norm = (bm25_scores - bm25_scores.min()) / (bm25_scores.max() - bm25_scores.min())
        semantic_scores_norm = (semantic_scores - semantic_scores.min()) / (semantic_scores.max() - semantic_scores.min())
        
        # Hybrid
        final_scores = alpha * bm25_scores_norm + (1 - alpha) * semantic_scores_norm
    else:
        final_scores = bm25_scores
    
    # 4. Rank and return
    top_indices = np.argsort(final_scores)[-top_k:][::-1]
    results = filtered_jobs.iloc[top_indices].copy()
    results['score'] = final_scores[top_indices]
    results['rank'] = range(1, len(results) + 1)
    
    return results
```

---

## 🛠️ IMPLEMENTATION PLAN

### Phase 1: Data Pipeline Refactor (Day 1)

**File**: `src/loader_v2.py` (new file, keep old for reference)

```python
"""
loader_v2.py - Normalized data loading (no aggregation)
"""

def load_jobs_normalized():
    """Load jobs table (main facts)."""
    postings = pd.read_csv('data/raw/postings.csv')
    
    # Select relevant columns
    jobs = postings[[
        'job_id', 'title', 'description', 'company_id', 'company_name',
        'location', 'formatted_work_type', 'formatted_experience_level',
        'remote_allowed', 'min_salary', 'max_salary', 'pay_period',
        'views', 'applies', 'original_listed_time', 'closed_time'
    ]].copy()
    
    # Clean
    jobs = jobs[jobs['title'].notna() & jobs['description'].notna()]
    jobs = jobs.drop_duplicates(subset=['job_id'])
    
    # Parse location
    jobs[['city', 'state', 'country']] = jobs['location'].apply(parse_location_to_dict).apply(pd.Series)
    
    # Normalize salary
    jobs['normalized_salary_yearly'] = jobs.apply(normalize_salary, axis=1)
    
    # Rename columns
    jobs = jobs.rename(columns={
        'formatted_work_type': 'work_type',
        'formatted_experience_level': 'experience_level',
        'original_listed_time': 'listed_time'
    })
    
    return jobs


def load_job_skills():
    """Load job-skill relationships (many-to-many)."""
    job_skills = pd.read_csv('data/raw/jobs/job_skills.csv')
    job_skills = job_skills[['job_id', 'skill_abr']].copy()
    return job_skills


def load_skills_lookup():
    """Load skills lookup table."""
    skills = pd.read_csv('data/raw/mappings/skills.csv')
    return skills


def load_job_industries():
    """Load job-industry relationships."""
    job_industries = pd.read_csv('data/raw/jobs/job_industries.csv')
    return job_industries


def load_industries_lookup():
    """Load industries lookup table."""
    industries = pd.read_csv('data/raw/mappings/industries.csv')
    return industries


def build_search_corpus(jobs, job_skills, skills):
    """
    Build search corpus for BM25.
    
    Returns:
        corpus_title: List[str]
        corpus_description: List[str]
        corpus_skills: List[str]
    """
    # Join job_skills with skills to get skill names
    job_skills_enriched = job_skills.merge(skills, on='skill_abr', how='left')
    
    # Aggregate skills per job
    skills_by_job = (
        job_skills_enriched
        .groupby('job_id')['skill_name']
        .apply(lambda x: ' '.join(x.dropna()))
        .reindex(jobs['job_id'], fill_value='')
    )
    
    # Build corpus
    corpus_title = jobs['title'].fillna('').tolist()
    corpus_description = jobs['description'].fillna('').tolist()
    corpus_skills = skills_by_job.tolist()
    
    return corpus_title, corpus_description, corpus_skills
```

**Test**:
```python
# test_loader_v2.py
def test_load_jobs_normalized():
    jobs = load_jobs_normalized()
    assert len(jobs) > 100000
    assert 'title' in jobs.columns
    assert 'job_id' in jobs.columns
    assert jobs['job_id'].is_unique
    
def test_load_job_skills():
    job_skills = load_job_skills()
    assert len(job_skills) > 200000
    assert 'job_id' in job_skills.columns
    assert 'skill_abr' in job_skills.columns
```

---

### Phase 2: BM25 Search Implementation (Day 2)

**File**: `src/bm25_search.py` (new file)

```python
"""
bm25_search.py - BM25-based job search
"""

from rank_bm25 import BM25Okapi
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple

class BM25JobSearch:
    def __init__(self, jobs, job_skills, skills):
        """Initialize BM25 indexes."""
        self.jobs = jobs
        self.job_skills = job_skills
        self.skills = skills
        
        # Build corpus
        corpus_title, corpus_description, corpus_skills = build_search_corpus(
            jobs, job_skills, skills
        )
        
        # Tokenize
        self.corpus_title_tokens = [self._tokenize(text) for text in corpus_title]
        self.corpus_desc_tokens = [self._tokenize(text) for text in corpus_description]
        self.corpus_skills_tokens = [self._tokenize(text) for text in corpus_skills]
        
        # Build BM25 indexes
        print("Building BM25 indexes...")
        self.bm25_title = BM25Okapi(self.corpus_title_tokens)
        self.bm25_description = BM25Okapi(self.corpus_desc_tokens)
        self.bm25_skills = BM25Okapi(self.corpus_skills_tokens)
        print("✓ BM25 indexes ready")
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization."""
        return text.lower().split()
    
    def search(
        self,
        query: str,
        filters: Dict[str, Any] = None,
        top_k: int = 20,
        field_weights: Dict[str, float] = None
    ) -> pd.DataFrame:
        """
        Search jobs with BM25 + filters.
        
        Args:
            query: Search query
            filters: Dict with filter conditions
            top_k: Number of results to return
            field_weights: Dict with weights for title/description/skills
        
        Returns:
            DataFrame with ranked results
        """
        if field_weights is None:
            field_weights = {'title': 3.0, 'description': 1.0, 'skills': 2.0}
        
        # 1. Apply filters first
        if filters:
            filtered_jobs = self._apply_filters(self.jobs, filters)
            if len(filtered_jobs) == 0:
                return pd.DataFrame()
            filtered_indices = filtered_jobs.index.tolist()
        else:
            filtered_jobs = self.jobs
            filtered_indices = list(range(len(self.jobs)))
        
        # 2. BM25 search
        query_tokens = self._tokenize(query)
        
        scores_title = self.bm25_title.get_scores(query_tokens)
        scores_description = self.bm25_description.get_scores(query_tokens)
        scores_skills = self.bm25_skills.get_scores(query_tokens)
        
        # 3. Combine scores with weights
        final_scores = (
            field_weights['title'] * scores_title +
            field_weights['description'] * scores_description +
            field_weights['skills'] * scores_skills
        )
        
        # 4. Filter scores to match filtered jobs
        final_scores_filtered = final_scores[filtered_indices]
        
        # 5. Rank
        top_indices = np.argsort(final_scores_filtered)[-top_k:][::-1]
        results = filtered_jobs.iloc[top_indices].copy()
        results['bm25_score'] = final_scores_filtered[top_indices]
        results['rank'] = range(1, len(results) + 1)
        
        return results
    
    def _apply_filters(self, jobs: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
        """Apply filters as boolean masks."""
        filtered = jobs.copy()
        
        # Location
        if 'location' in filters:
            loc = filters['location'].lower()
            mask = (
                filtered['city'].str.lower().str.contains(loc, na=False) |
                filtered['state'].str.lower().str.contains(loc, na=False) |
                filtered['location'].str.lower().str.contains(loc, na=False)
            )
            filtered = filtered[mask]
        
        # Work type
        if 'work_type' in filters:
            work_types = filters['work_type'] if isinstance(filters['work_type'], list) else [filters['work_type']]
            filtered = filtered[filtered['work_type'].isin(work_types)]
        
        # Experience
        if 'experience_level' in filters:
            filtered = filtered[filtered['experience_level'] == filters['experience_level']]
        
        # Remote
        if 'remote_allowed' in filters:
            filtered = filtered[filtered['remote_allowed'] == filters['remote_allowed']]
        
        # Salary range
        if 'min_salary' in filters or 'max_salary' in filters:
            has_salary = filtered['normalized_salary_yearly'].notna()
            filtered = filtered[has_salary]
            
            if 'min_salary' in filters:
                filtered = filtered[filtered['normalized_salary_yearly'] >= filters['min_salary']]
            if 'max_salary' in filters:
                filtered = filtered[filtered['normalized_salary_yearly'] <= filters['max_salary']]
        
        # Skills (requires JOIN)
        if 'skills' in filters:
            required_skills = filters['skills'] if isinstance(filters['skills'], list) else [filters['skills']]
            
            job_ids_with_skills = (
                self.job_skills[self.job_skills['skill_abr'].isin(required_skills)]
                .groupby('job_id')
                .size()
            )
            job_ids_with_all = job_ids_with_skills[job_ids_with_skills == len(required_skills)].index
            filtered = filtered[filtered['job_id'].isin(job_ids_with_all)]
        
        return filtered
```

**Test**:
```python
# test_bm25_search.py
def test_bm25_search_no_filters():
    searcher = BM25JobSearch(jobs, job_skills, skills)
    results = searcher.search("Python developer", top_k=10)
    assert len(results) == 10
    assert 'bm25_score' in results.columns
    assert results['bm25_score'].iloc[0] >= results['bm25_score'].iloc[-1]

def test_bm25_search_with_filters():
    searcher = BM25JobSearch(jobs, job_skills, skills)
    results = searcher.search(
        "Data scientist",
        filters={'location': 'California', 'work_type': 'Full-time'},
        top_k=10
    )
    assert all(results['work_type'] == 'Full-time')
    assert all(results['location'].str.contains('California', case=False, na=False))
```

---

### Phase 3: Evaluation Framework (Day 3)

**File**: `src/evaluation.py`

```python
"""
evaluation.py - Evaluation metrics for job search
"""

from typing import List, Dict, Tuple
import pandas as pd

class SearchEvaluator:
    def __init__(self, searcher):
        self.searcher = searcher
    
    def precision_at_k(
        self,
        query: str,
        relevant_job_ids: List[int],
        filters: Dict = None,
        k: int = 10
    ) -> float:
        """
        Precision@K: proportion of relevant results in top-K.
        
        Args:
            query: Search query
            relevant_job_ids: List of ground truth relevant job IDs
            filters: Optional filters
            k: Number of results to evaluate
        
        Returns:
            Precision@K score (0.0 to 1.0)
        """
        results = self.searcher.search(query, filters=filters, top_k=k)
        
        if len(results) == 0:
            return 0.0
        
        retrieved_ids = results['job_id'].tolist()
        relevant_count = sum(1 for job_id in retrieved_ids if job_id in relevant_job_ids)
        
        return relevant_count / len(retrieved_ids)
    
    def recall_at_k(
        self,
        query: str,
        relevant_job_ids: List[int],
        filters: Dict = None,
        k: int = 10
    ) -> float:
        """
        Recall@K: proportion of relevant docs retrieved in top-K.
        """
        results = self.searcher.search(query, filters=filters, top_k=k)
        
        if len(relevant_job_ids) == 0:
            return 0.0
        
        retrieved_ids = results['job_id'].tolist()
        relevant_count = sum(1 for job_id in retrieved_ids if job_id in relevant_job_ids)
        
        return relevant_count / len(relevant_job_ids)
    
    def evaluate_test_set(
        self,
        test_queries: List[Dict]
    ) -> pd.DataFrame:
        """
        Evaluate on a test set of queries with ground truth.
        
        Args:
            test_queries: List of dicts with 'query', 'filters', 'relevant_ids'
        
        Returns:
            DataFrame with metrics per query
        """
        results = []
        
        for test_case in test_queries:
            query = test_case['query']
            filters = test_case.get('filters')
            relevant_ids = test_case['relevant_ids']
            
            p_at_5 = self.precision_at_k(query, relevant_ids, filters, k=5)
            p_at_10 = self.precision_at_k(query, relevant_ids, filters, k=10)
            r_at_5 = self.recall_at_k(query, relevant_ids, filters, k=5)
            r_at_10 = self.recall_at_k(query, relevant_ids, filters, k=10)
            
            results.append({
                'query': query,
                'precision@5': p_at_5,
                'precision@10': p_at_10,
                'recall@5': r_at_5,
                'recall@10': r_at_10,
            })
        
        df = pd.DataFrame(results)
        
        # Add averages
        avg_row = {
            'query': 'AVERAGE',
            'precision@5': df['precision@5'].mean(),
            'precision@10': df['precision@10'].mean(),
            'recall@5': df['recall@5'].mean(),
            'recall@10': df['recall@10'].mean(),
        }
        df = pd.concat([df, pd.DataFrame([avg_row])], ignore_index=True)
        
        return df
```

**Create Test Set**:
```python
# notebooks/create_test_set.ipynb

test_queries = [
    {
        'query': 'Python backend developer',
        'filters': {'work_type': 'Full-time'},
        'relevant_ids': [12345, 23456, 34567, ...]  # Manually label 10-20 jobs
    },
    {
        'query': 'Data scientist machine learning',
        'filters': {'location': 'California', 'remote_allowed': True},
        'relevant_ids': [...]
    },
    # ... 18 more queries
]

# Save
import json
with open('data/test_queries.json', 'w') as f:
    json.dump(test_queries, f, indent=2)
```

---

### Phase 4: UI Integration (Day 4)

**File**: `app_v2.py` (new file)

```python
"""
app_v2.py - Streamlit UI with BM25 search
"""

import streamlit as st
from src.loader_v2 import load_jobs_normalized, load_job_skills, load_skills_lookup
from src.bm25_search import BM25JobSearch

@st.cache_resource
def load_searcher():
    """Load and cache BM25 searcher."""
    with st.spinner("Loading data and building search index..."):
        jobs = load_jobs_normalized()
        job_skills = load_job_skills()
        skills = load_skills_lookup()
        searcher = BM25JobSearch(jobs, job_skills, skills)
    st.success("✅ Search engine ready!")
    return searcher

def main():
    st.title("🔍 Job Search Engine")
    
    # Load searcher
    searcher = load_searcher()
    
    # Search bar
    query = st.text_input("Search for jobs", placeholder="e.g., Python developer")
    
    # Filters (sidebar)
    with st.sidebar:
        st.header("Filters")
        
        location = st.text_input("Location", placeholder="e.g., California")
        work_type = st.multiselect("Work Type", ['Full-time', 'Part-time', 'Contract', 'Internship'])
        experience = st.selectbox("Experience Level", ['Any', 'Entry level', 'Mid-Senior level', 'Director', 'Executive'])
        remote = st.checkbox("Remote only")
        
        salary_min = st.number_input("Min Salary (yearly)", min_value=0, value=0, step=10000)
        salary_max = st.number_input("Max Salary (yearly)", min_value=0, value=0, step=10000)
    
    # Search button
    if st.button("Search") or query:
        # Build filters
        filters = {}
        if location:
            filters['location'] = location
        if work_type:
            filters['work_type'] = work_type
        if experience != 'Any':
            filters['experience_level'] = experience
        if remote:
            filters['remote_allowed'] = True
        if salary_min > 0:
            filters['min_salary'] = salary_min
        if salary_max > 0:
            filters['max_salary'] = salary_max
        
        # Search
        results = searcher.search(query, filters=filters, top_k=20)
        
        # Display
        st.write(f"### Found {len(results)} results")
        
        if len(results) == 0:
            st.warning("No jobs match your criteria. Try relaxing some filters.")
        else:
            for idx, row in results.iterrows():
                with st.container():
                    st.markdown(f"**{row['rank']}. {row['title']}**")
                    st.write(f"🏢 {row['company_name']} | 📍 {row['location']}")
                    st.write(f"💼 {row['work_type']} | 🎯 {row['experience_level']}")
                    if pd.notna(row['normalized_salary_yearly']):
                        st.write(f"💰 ${row['normalized_salary_yearly']:,.0f}/year")
                    st.write(f"⭐ Score: {row['bm25_score']:.2f}")
                    with st.expander("Description"):
                        st.write(row['description'][:500] + "...")
                    st.markdown("---")

if __name__ == "__main__":
    main()
```

---

## 📝 TIMELINE & DELIVERABLES

### Day 1: Data Pipeline (Dec 26)
- [ ] Create `src/loader_v2.py`
- [ ] Implement normalized data loading
- [ ] Write unit tests
- [ ] Verify data quality

**Deliverable**: Clean normalized tables (jobs, job_skills, skills, industries)

---

### Day 2: BM25 Search (Dec 27)
- [ ] Install `rank-bm25`: `pip install rank-bm25`
- [ ] Create `src/bm25_search.py`
- [ ] Implement BM25JobSearch class
- [ ] Test with sample queries
- [ ] Tune field weights

**Deliverable**: Working BM25 search with filters

---

### Day 3: Evaluation (Dec 28)
- [ ] Create test query set (20 queries)
- [ ] Manual labeling (relevant/not relevant)
- [ ] Implement evaluation.py
- [ ] Calculate Precision@5, @10
- [ ] Compare with current system

**Deliverable**: Evaluation report with metrics

---

### Day 4: UI & Polish (Dec 29)
- [ ] Create app_v2.py
- [ ] Integrate BM25 search
- [ ] Test end-to-end
- [ ] Documentation
- [ ] Presentation prep

**Deliverable**: Working demo + documentation

---

### Day 5: Buffer & Extras (Dec 30)
- [ ] Fix any issues from Day 4
- [ ] Optional: Add semantic layer (embeddings)
- [ ] Optional: Improve UI
- [ ] Final testing

**Deliverable**: Polished final product

---

## 🎯 SUCCESS CRITERIA

### Must Have (Day 1-4)
- ✅ BM25 search working
- ✅ Filters work correctly (as query clauses)
- ✅ Precision@5 ≥ 60% (manual evaluation)
- ✅ UI functional
- ✅ Documentation complete

### Nice to Have (Day 5+)
- ✅ Precision@5 ≥ 80%
- ✅ Hybrid (BM25 + embeddings)
- ✅ Advanced UI features
- ✅ Deploy to cloud

---

## 📊 EXPECTED IMPROVEMENTS

### Current System (with flaws)
- Precision@5: ~50-60% (estimated, no ground truth)
- Filters: Unreliable (post-processing)
- Search time: <50ms (good)
- User satisfaction: Low (0 results fallback to irrelevant)

### New System (target)
- Precision@5: ≥80% (with proper BM25 + filters)
- Filters: Reliable (query-time)
- Search time: <100ms (acceptable)
- User satisfaction: High (honest results, no false positives)

---

## 🔚 NEXT STEPS

**TODAY (Dec 26)**:
1. Review this plan
2. Start implementing `loader_v2.py`
3. Test normalized data loading
4. Create unit tests

**TOMORROW (Dec 27)**:
1. Implement BM25 search
2. Test with sample queries
3. Benchmark performance

Let's get started! 🚀

---

**Status**: 🟢 READY TO BEGIN
