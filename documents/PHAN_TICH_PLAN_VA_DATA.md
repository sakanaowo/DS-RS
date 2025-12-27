# PHÂN TÍCH PLAN VÀ DATA ĐÃ TIỀN XỬ LÝ

**Ngày phân tích**: 27/12/2025  
**Mục đích**: So sánh plan redesign với data hiện tại, xác định gap và action items

---

## 📊 1. TỔNG QUAN DATA HIỆN TẠI

### 1.1 Raw Data Structure

**Dữ liệu gốc** (trong `data/raw/`):
```
data/raw/
├── postings.csv                    # Main table - 123,849 jobs
├── jobs/
│   ├── job_skills.csv             # Many-to-many: job → skills
│   ├── job_industries.csv         # Many-to-many: job → industries
│   ├── benefits.csv               # Job benefits
│   └── salaries.csv               # Salary info
├── companies/
│   ├── companies.csv              # Company metadata
│   ├── company_specialities.csv   # Company tags
│   ├── company_industries.csv     # Company industries
│   └── employee_counts.csv        # Employee count history
└── mappings/
    ├── skills.csv                 # skill_abr → skill_name (36 skills)
    └── industries.csv             # industry_id → industry_name (422 industries)
```

**Tổng số dòng**: ~3.8M rows (tất cả files combined)

**Kích thước**:
- `data/processed/clean_jobs.parquet`: **675 MB** (aggregated)
- Raw CSVs: Chưa xác định chính xác (cần check)

### 1.2 Processed Data (Hiện tại)

**File**: `data/processed/clean_jobs.parquet` (675 MB)

**Cách xử lý hiện tại** (trong `src/loader.py`):
```python
# ❌ PROBLEM: Aggregation - mất cấu trúc quan hệ
def build_enriched_jobs():
    # Skills: JOIN nhiều rows → gộp thành 1 string
    skill_agg = (
        skills.groupby("job_id")["skill_name"]
        .apply(_collapse_unique)  # "Python, Java, SQL"
        .reset_index()
    )
    
    # Industries: JOIN nhiều rows → gộp thành 1 string  
    industry_agg = (
        job_ind.groupby("job_id")["industry_name"]
        .apply(_collapse_unique)  # "IT, Healthcare, Finance"
        .reset_index()
    )
    
    # Benefits, Company specs: cũng bị gộp string
    # ...
    
    # Merge tất cả vào 1 table lớn
    enriched = postings.merge(skill_agg, on="job_id")
                      .merge(industry_agg, on="job_id")
                      .merge(benefits_agg, on="job_id")
                      # ... 8 JOINs
```

**Kết quả**: 
- ✅ Có 1 table duy nhất → dễ query
- ❌ Skills/industries thành string → **không filter chính xác được**
- ❌ Duplicate data (skills "Python" lặp lại trong nhiều jobs)
- ❌ 675 MB (lớn, tốn memory)

---

## 🎯 2. YÊU CẦU TỪ REDESIGN PLAN

### 2.1 Data Architecture Mới

**Plan yêu cầu** (từ REDESIGN_COMPLETE_PLAN.md):

```python
# ✅ SOLUTION: Normalized tables - GIỮ NGUYÊN quan hệ
tables = {
    'jobs': {
        'size': '~50 MB',
        'rows': 123_842,
        'columns': ['job_id', 'title', 'description', 'company_id', 
                    'location', 'city', 'state', 'country',
                    'work_type', 'experience_level', 'remote_allowed',
                    'min_salary', 'max_salary', 'normalized_salary_yearly']
    },
    'job_skills': {
        'size': '~3 MB', 
        'rows': 213_768,  # Estimated
        'columns': ['job_id', 'skill_abr']
    },
    'skills': {
        'size': '<1 MB',
        'rows': 36,
        'columns': ['skill_abr', 'skill_name']
    },
    'job_industries': {
        'size': '~3 MB',
        'rows': 164_808,  # Estimated
        'columns': ['job_id', 'industry_id']
    },
    'industries': {
        'size': '<1 MB',
        'rows': 422,
        'columns': ['industry_id', 'industry_name']
    }
}
```

**Tổng dung lượng mới**: ~70 MB (giảm 90% từ 675 MB)

### 2.2 So sánh Approach

| Aspect | Hiện tại (❌) | Plan mới (✅) |
|--------|---------------|----------------|
| **Data Structure** | Aggregated (1 table) | Normalized (5+ tables) |
| **Skills storage** | `"Python, Java, SQL"` string | `job_skills` table (job_id, skill_abr) |
| **Filter logic** | Post-processing (sau search) | Pre-filtering (JOIN trước search) |
| **Storage** | 675 MB | ~70 MB |
| **Filter accuracy** | Không chính xác (string matching) | 100% chính xác (relational JOIN) |
| **Search method** | TF-IDF + FAISS (vector) | BM25 (keyword) + optional embeddings |

---

## 🔍 3. VẤN ĐỀ CỤ THỂ TRONG DATA HIỆN TẠI

### 3.1 Problem 1: Skills Aggregation

**Code hiện tại** (`src/loader.py:103`):
```python
def _collapse_unique(values: pd.Series) -> Optional[str]:
    """Convert a series of categorical values into a sorted, comma-separated string."""
    cleaned = {str(v).strip() for v in values if isinstance(v, str) and v.strip()}
    return ", ".join(sorted(cleaned)) if cleaned else None
```

**Ví dụ kết quả**:
```
job_id=12345 → skills = "Business Development, Information Technology, Python Programming"
```

**Tại sao đây là vấn đề?**

1. **Không filter chính xác**:
   ```python
   # User filter: "Python"
   # Current: string contains "Python" → MATCH
   # But also matches: "Python Script Writer", "Python Documentation"
   # → SAI!
   ```

2. **Không thể AND logic**:
   ```python
   # User muốn: jobs có CẢ "Python" VÀ "SQL"
   # Current: check if "Python" in string AND "SQL" in string
   # Problem: "Python, SQL Analysis" → SQL Analysis không phải SQL skill
   ```

3. **Duplicate data**:
   ```
   Job 1: "Python, Java, SQL"
   Job 2: "Python, JavaScript, SQL"  
   Job 3: "Python, C++, SQL"
   
   → "Python" và "SQL" được lưu 3 lần (lặp)
   → Tốn storage + memory
   ```

### 3.2 Problem 2: Location Parsing Không Đồng nhất

**Code hiện tại** (`src/preprocessing.py:143`):
```python
def parse_location(location: str) -> dict:
    # Split by comma
    parts = [p.strip() for p in location.split(",")]
    
    if len(parts) == 2:
        # Two parts - city, state or city, country
        city, state_or_country = parts
        if len(state_or_country) == 2 and state_or_country.isupper():
            return {"city": city, "state": state_or_country, "country": "United States"}
        else:
            return {"city": city, "state": None, "country": state_or_country}
```

**Vấn đề**:
- Không handle edge cases:
  - `"New York, NY, United States"` → OK
  - `"New York"` → country="New York" (SAI!)
  - `"Remote"` → country="Remote" (SAI!)
  - `"United States"` → handled riêng (inconsistent)

**Plan yêu cầu**:
```python
# Cần parsing tốt hơn với:
# 1. Handle "Remote" special case
# 2. City/State/Country standardization
# 3. Fallback values hợp lý
```

### 3.3 Problem 3: Salary Normalization

**Data audit** (`reports/data_audit.md`):
```
Salary coverage:
- min_salary: 75.9% thiếu (chỉ 24% có)
- max_salary: 75.9% thiếu
- med_salary: 94.9% thiếu
- pay_period: 70.9% thiếu

Pay period phân bố:
- YEARLY: 20,628 (16.7%)
- HOURLY: 14,741 (11.9%)
- MONTHLY: 518 (0.4%)
```

**Vấn đề**:
1. **23% coverage rất thấp** → filter by salary = 0 results thường xuyên
2. **Conversion factors** cần chuẩn hóa:
   ```python
   # Current (chưa rõ ràng):
   # HOURLY → YEARLY: multiply by ???
   # Plan yêu cầu: 2080 hours/year (40h/week × 52 weeks)
   ```

3. **Missing strategy**: Plan yêu cầu KHÔNG impute salary (giữ NULL)
   - Hiện tại: Có thể đã impute (cần check)

---

## ⚠️ 4. GAPS GIỮA PLAN VÀ IMPLEMENTATION HIỆN TẠI

### 4.1 Data Pipeline Gaps

| Feature | Plan yêu cầu | Hiện tại | Gap |
|---------|--------------|----------|-----|
| **Normalized tables** | ✅ Cần | ❌ Không có | **CRITICAL** |
| **Skills table** | Riêng biệt (job_skills) | Aggregated string | **CRITICAL** |
| **Industries table** | Riêng biệt (job_industries) | Aggregated string | **CRITICAL** |
| **Location parsing** | city, state, country fields | Có nhưng inconsistent | MEDIUM |
| **Salary normalization** | normalized_salary_yearly | Có partial | MEDIUM |
| **No aggregation** | Keep many-to-many | Aggregated everywhere | **CRITICAL** |

### 4.2 Search Architecture Gaps

| Component | Plan yêu cầu | Hiện tại | Gap |
|-----------|--------------|----------|-----|
| **Search method** | BM25 (keyword) | TF-IDF + FAISS (vector) | **MAJOR** |
| **Filter timing** | Pre-filtering (trước search) | Post-filtering (sau search) | **CRITICAL** |
| **Filter accuracy** | 100% (relational JOIN) | String matching (~60%) | **CRITICAL** |
| **Fallback** | NO fallback (honest 0 results) | 7-layer progressive fallback | MAJOR |
| **Field weights** | Title^3, Skills^2, Desc^1 | Equal weights (TF-IDF) | MEDIUM |

### 4.3 Code Gaps

| File | Plan yêu cầu | Hiện tại | Status |
|------|--------------|----------|--------|
| `src/loader_v2.py` | Load normalized (no aggregate) | ❌ Chưa có | **TODO** |
| `src/bm25_search.py` | BM25 + pre-filters | ❌ Chưa có | **TODO** |
| `src/hybrid_search.py` | Hybrid (BM25 + semantic) | ❌ Chưa có | **TODO** |
| `src/evaluation.py` | Manual labeling framework | ❌ Chưa có | **TODO** |
| `app_v2.py` | UI mới (honest UX) | `app.py` (có fallback) | **TODO** |
| `src/loader.py` | → Deprecated | ✅ Có (353 lines) | **REPLACE** |
| `src/preprocessing.py` | → Keep some utils | ✅ Có (368 lines) | **REFACTOR** |
| `src/recommender.py` | → Deprecated | ✅ Có (623 lines) | **REPLACE** |

---

## 📋 5. ACTION ITEMS - ƯU TIÊN

### 5.1 CRITICAL (Day 1) - Data Pipeline

**Mục tiêu**: Tạo normalized tables từ raw CSVs

**Tasks**:

1. **Tạo `src/loader_v2.py`** (2-3 giờ):
   ```python
   def load_jobs_normalized() -> pd.DataFrame:
       """Load jobs table - NO aggregation."""
       # Read postings.csv
       # Select columns cần thiết
       # Clean: drop missing title/description
       # Remove duplicates by job_id
       # Parse location → city, state, country
       # Normalize salary → normalized_salary_yearly
       # Return: 123,842 rows × 25 columns (~50 MB)
   
   def load_job_skills() -> pd.DataFrame:
       """Load job-skill relationships."""
       # Read jobs/job_skills.csv
       # Keep: job_id, skill_abr
       # Return: 213,768 rows × 2 columns (~3 MB)
   
   def load_skills() -> pd.DataFrame:
       """Load skills lookup."""
       # Read mappings/skills.csv
       # Return: 36 rows
   
   def load_job_industries() -> pd.DataFrame:
       """Load job-industry relationships."""
       # Read jobs/job_industries.csv
       # Keep: job_id, industry_id
       # Return: 164,808 rows × 2 columns (~3 MB)
   
   def load_industries() -> pd.DataFrame:
       """Load industries lookup."""
       # Read mappings/industries.csv
       # Return: 422 rows
   ```

2. **Save normalized tables** (30 phút):
   ```python
   def save_normalized_data():
       # Save to data/processed/
       jobs.to_parquet('data/processed/jobs.parquet')
       job_skills.to_parquet('data/processed/job_skills.parquet')
       skills.to_parquet('data/processed/skills.parquet')
       job_industries.to_parquet('data/processed/job_industries.parquet')
       industries.to_parquet('data/processed/industries.parquet')
   ```

3. **Unit tests** (1 giờ):
   ```python
   # tests/test_loader_v2.py
   def test_load_jobs_normalized():
       assert jobs['job_id'].is_unique
       assert jobs['title'].notna().all()
       assert len(jobs) > 100000
   
   def test_load_job_skills():
       assert 'job_id' in job_skills.columns
       assert 'skill_abr' in job_skills.columns
   ```

**Kiểm tra thành công**:
- ✅ `data/processed/jobs.parquet` (~50 MB) tồn tại
- ✅ `data/processed/job_skills.parquet` (~3 MB) tồn tại
- ✅ `jobs['job_id'].is_unique == True`
- ✅ No duplicates
- ✅ No missing title/description
- ✅ Location parsed correctly (spot check)

### 5.2 HIGH (Day 2) - BM25 Search

**Mục tiêu**: Implement BM25 search với pre-filtering

**Tasks**:

1. **Install dependency**:
   ```bash
   pip install rank-bm25
   ```

2. **Implement `src/bm25_search.py`** (3-4 giờ):
   ```python
   class BM25JobSearch:
       def __init__(self, jobs, job_skills, skills):
           # Build 3 separate BM25 indexes:
           # - Title corpus
           # - Description corpus  
           # - Skills corpus (JOIN job_skills → skills)
       
       def search(self, query, top_k=1000):
           # Get scores from 3 indexes
           # Weighted combination: 3×title + 2×skills + 1×desc
           # Return top-K
   
   def apply_filters(jobs, filters, job_skills=None):
       # Pre-filter BEFORE search:
       # 1. Location (fuzzy string match)
       # 2. Work type (exact)
       # 3. Experience level (exact)
       # 4. Remote (boolean)
       # 5. Salary range (numeric)
       # 6. Skills (JOIN job_skills)
       # Return: filtered DataFrame
   ```

3. **Test và benchmark** (1 giờ):
   ```python
   # Test queries
   queries = [
       "Python developer",
       "Data scientist machine learning",
       "Frontend engineer React"
   ]
   
   # Measure search time
   for q in queries:
       start = time.time()
       results = searcher.search(q, top_k=20)
       print(f"{q}: {(time.time()-start)*1000:.1f}ms")
   
   # Target: <100ms per query
   ```

**Kiểm tra thành công**:
- ✅ BM25 search trả về kết quả
- ✅ Search time <100ms
- ✅ Filters hoạt động (test từng loại)
- ✅ Skills filter chính xác (exact match)

### 5.3 MEDIUM (Day 3) - Evaluation

**Mục tiêu**: Tạo test set và đo Precision@K

**Tasks**:

1. **Tạo test queries** (1 giờ):
   ```json
   // data/test_queries.json
   [
     {
       "query_id": 1,
       "query": "Python backend developer",
       "filters": {"work_type": "Full-time"},
       "relevant_job_ids": []  // Fill sau
     },
     // ... 19 queries nữa
   ]
   ```

2. **Manual labeling** (2-3 giờ):
   - Chạy mỗi query
   - Review top-10 results
   - Label: 2=perfect, 1=partial, 0=not relevant
   - Ghi job_ids relevant

3. **Implement metrics** (1 giờ):
   ```python
   # src/evaluation.py
   def precision_at_k(retrieved, relevant, k):
       top_k = retrieved[:k]
       return len(set(top_k) & set(relevant)) / k
   
   def evaluate_test_set(searcher, test_queries):
       # Run all queries
       # Calculate P@5, P@10, R@5, R@10
       # Return: DataFrame với results
   ```

**Target**: Precision@5 ≥ 80%

### 5.4 LOW (Day 4-5) - UI + Polish

**Tasks**:
1. Implement hybrid search (BM25 + semantic)
2. Create `app_v2.py` (Streamlit)
3. End-to-end testing
4. Documentation

---

## 🔢 6. EXPECTED STORAGE COMPARISON

### 6.1 Current (Aggregated)

```
data/processed/
└── clean_jobs.parquet    675 MB
    
Memory usage (loaded):
- Pandas DataFrame: ~1.2 GB RAM
- With TF-IDF vectors: +500 MB
- FAISS index: +200 MB
Total: ~1.9 GB RAM
```

### 6.2 Plan (Normalized)

```
data/processed/
├── jobs.parquet           ~50 MB   (123,842 rows)
├── job_skills.parquet      ~3 MB   (213,768 rows)
├── skills.parquet          <1 MB   (36 rows)
├── job_industries.parquet  ~3 MB   (164,808 rows)
├── industries.parquet      <1 MB   (422 rows)
└── companies.parquet      ~10 MB   (24,473 rows)
Total: ~70 MB

Memory usage (loaded):
- All tables: ~150 MB RAM
- BM25 indexes: ~100 MB
- Optional embeddings: ~200 MB (if hybrid)
Total: ~450 MB RAM (giảm 76%)
```

**Savings**:
- Storage: 675 MB → 70 MB (**-90%**)
- RAM: 1.9 GB → 450 MB (**-76%**)

---

## 🎯 7. KẾT LUẬN VÀ KHUYẾN NGHỊ

### 7.1 Tóm tắt Vấn đề

**3 vấn đề nghiêm trọng** trong data hiện tại:

1. **Data aggregation** → Mất cấu trúc quan hệ
   - Skills/industries thành string
   - Không filter chính xác
   - Tốn storage (duplicate)

2. **Post-filtering** → Search không hiệu quả
   - Search tất cả 123k jobs
   - Rồi mới filter
   - Kết quả không đáng tin

3. **Progressive fallback** → UX misleading
   - 0 results → relax filters
   - Trả về jobs không liên quan
   - User bối rối

### 7.2 Khuyến nghị

**Ưu tiên CAO nhất**: Implement Day 1 (Data Pipeline)

**Lý do**:
- Tất cả các component khác phụ thuộc vào normalized data
- Chỉ 3-4 giờ work
- Test được ngay (unit tests)
- Unlock Day 2, 3, 4

**Bước tiếp theo**:
1. ✅ Tạo `src/loader_v2.py` (NGAY BÂY GIỜ)
2. ✅ Test với sample (1000 jobs)
3. ✅ Run full dataset
4. ✅ Save normalized tables
5. ✅ Verify storage (~70 MB)

**Timeline thực tế**:
- Day 1 (hôm nay): Data pipeline (3-4h)
- Day 2 (28/12): BM25 search (4-5h)
- Day 3 (29/12): Evaluation (4-5h)
- Day 4 (30/12): UI + polish (4-5h)
- Day 5 (31/12): Buffer + documentation

**Tổng**: ~20 giờ work (4 days × 5h/day)

---

## 📌 8. NEXT IMMEDIATE ACTIONS

**HÀNH ĐỘNG NGAY** (trong 30 phút):

```bash
# 1. Create file
touch src/loader_v2.py

# 2. Start implementing (copy từ plan):
# - load_jobs_normalized()
# - parse_location()
# - normalize_salary_to_yearly()

# 3. Test với sample
python -c "from src.loader_v2 import load_jobs_normalized; print(load_jobs_normalized().shape)"
```

**READY TO START?** 🚀

---

**Status**: 🔴 DATA PIPELINE CHƯA SẴN SÀNG  
**Blocker**: Cần implement `loader_v2.py` trước  
**ETA**: 3-4 giờ (Day 1)  
**Last Updated**: 27/12/2025
