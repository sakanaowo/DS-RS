# Recommendation System Strategies - Best Practices Analysis

**Date**: November 27, 2025  
**Context**: Phân tích chiến lược recommendation của các hệ thống lớn để áp dụng vào Job Recommendation System

---

## I. PHÂN TÍCH CÁC HỆ THỐNG LỚN

### 1. **LinkedIn Jobs** (Tương tự nhất với project)

#### Strategy Stack (Multi-layered Fallback)

```
Layer 1: Personalized Semantic Search
├─ Vector similarity (user skills × job embeddings)
├─ Collaborative filtering (users with similar profiles)
└─ If insufficient results → Layer 2

Layer 2: Demographic Matching
├─ Location-based filtering
├─ Experience level matching
├─ Industry similarity
└─ If insufficient results → Layer 3

Layer 3: Popular Jobs (Trending)
├─ Most viewed jobs in location
├─ Most applied jobs in industry
├─ Recently posted jobs
└─ If insufficient results → Layer 4

Layer 4: Expanded Search
├─ Relax location constraint (nearby cities)
├─ Relax experience level (±1 level)
├─ Show "remote jobs" regardless of location
└─ Always return results
```

**Missing Data Handling**:

- **No salary data**: Show anyway, mark "Salary not provided"
- **No location**: Default to "Remote" or "United States"
- **No skills**: Use job title for semantic search
- **No experience level**: Mark "Not specified", don't filter

---

### 2. **Indeed.com**

#### Strategy Stack

```
Layer 1: Exact Match + Semantic
├─ Query parsing (job title, skills, location)
├─ TF-IDF keyword matching
├─ Semantic embedding similarity
└─ Minimum 20 results required

Layer 2: Partial Match
├─ Remove least important filter (salary first)
├─ Relax location (expand radius)
├─ Relax keywords (synonyms)
└─ Minimum 10 results required

Layer 3: Related Jobs
├─ "Jobs similar to this search"
├─ Same industry, different titles
├─ Same location, different skills
└─ Always show results

Layer 4: Sponsored Jobs (Business Model)
├─ Companies pay for visibility
├─ Mixed with organic results
└─ Guaranteed never empty
```

**Missing Data Handling**:

- **No salary**: Don't filter, show "Competitive salary"
- **No remote flag**: Assume "On-site" (safer default)
- **No company info**: Show "Hiring Company"
- **Incomplete description**: Use title + industry for search

---

### 3. **Netflix** (Reference for Recommendation Logic)

#### Hybrid Strategy

```
1. Content-Based Filtering (50%)
   ├─ Genre similarity
   ├─ Director/Actor overlap
   ├─ Year/Duration match
   └─ TF-IDF on descriptions

2. Collaborative Filtering (30%)
   ├─ Users who watched X also watched Y
   ├─ Implicit feedback (watch time, completion rate)
   └─ Matrix factorization

3. Trending/Popular (20%)
   ├─ Time-decay popularity
   ├─ Regional trending
   └─ New releases boost
```

**Missing Data Handling**:

- **No user history**: Start with popular items
- **New user (cold start)**: Ask preferences → instant personalization
- **New item (cold start)**: Boost visibility for first 48h
- **No genre tags**: Use description embeddings

---

### 4. **Amazon** (E-commerce Recommendation)

#### Multi-Algorithm Approach

```
1. Item-to-Item Collaborative Filtering (Primary)
   └─ "Customers who bought X also bought Y"

2. Content-Based (Fallback)
   └─ Product attributes, category, brand

3. Context-Aware
   ├─ Time of day (breakfast → coffee)
   ├─ Season (winter → heaters)
   └─ Current cart items

4. Social Proof
   ├─ "Bestseller in category"
   ├─ "Highly rated"
   └─ "Trending now"
```

---

## II. CHIẾN LƯỢC CHO JOB RECOMMENDATION SYSTEM

### Recommended Strategy Stack (LinkedIn-inspired)

```python
def get_recommendations_with_fallback(query, filters, top_k=20):
    """
    Multi-layer recommendation với automatic fallback
    """

    # LAYER 1: SEMANTIC SEARCH với tất cả filters
    results = semantic_search(query, filters, fetch_k=top_k * 15)
    if len(results) >= top_k:
        return results.head(top_k)

    # LAYER 2: RELAX SALARY FILTER (least reliable data)
    if 'min_salary' in filters or 'max_salary' in filters:
        relaxed_filters = {k: v for k, v in filters.items()
                          if k not in ['min_salary', 'max_salary']}
        results = semantic_search(query, relaxed_filters, fetch_k=top_k * 12)
        if len(results) >= top_k:
            return results.head(top_k)

    # LAYER 3: RELAX EXPERIENCE LEVEL
    if 'experience_level' in filters:
        relaxed_filters = {k: v for k, v in filters.items()
                          if k != 'experience_level'}
        results = semantic_search(query, relaxed_filters, fetch_k=top_k * 10)
        if len(results) >= top_k:
            return results.head(top_k)

    # LAYER 4: LOCATION EXPANSION (nearby cities)
    if 'location' in filters:
        expanded_filters = filters.copy()
        expanded_filters['location'] = expand_location(filters['location'])
        results = semantic_search(query, expanded_filters, fetch_k=top_k * 8)
        if len(results) >= top_k:
            return results.head(top_k)

    # LAYER 5: QUERY-ONLY (no filters)
    results = semantic_search(query, filters={}, fetch_k=top_k * 5)
    if len(results) >= top_k:
        return results.head(top_k)

    # LAYER 6: POPULAR JOBS (last resort)
    return get_popular_jobs_in_category(query, top_k)
```

### Missing Data Handling Strategies

```python
class DataQualityHandler:
    """Handle missing/incomplete data gracefully"""

    @staticmethod
    def handle_missing_salary(job_row):
        """Salary missing: don't exclude, mark as 'Not specified'"""
        if pd.isna(job_row['salary_median']):
            job_row['salary_display'] = "Competitive salary"
            job_row['has_salary_info'] = False
        else:
            job_row['salary_display'] = format_salary(job_row)
            job_row['has_salary_info'] = True
        return job_row

    @staticmethod
    def handle_missing_location(job_row):
        """Location missing: infer or default"""
        if pd.isna(job_row['location']):
            # Strategy 1: Infer from company
            if pd.notna(job_row['company_city']):
                job_row['location'] = job_row['company_city']
            # Strategy 2: Check remote flag
            elif job_row.get('remote_allowed') == 1:
                job_row['location'] = "Remote"
            # Strategy 3: Default
            else:
                job_row['location'] = "United States"
        return job_row

    @staticmethod
    def handle_missing_work_type(job_row):
        """Work type missing: infer from other fields"""
        if pd.isna(job_row['formatted_work_type']):
            # Strategy 1: Check original work_type
            if pd.notna(job_row.get('work_type')):
                job_row['formatted_work_type'] = standardize_work_type(
                    job_row['work_type']
                )
            # Strategy 2: Infer from compensation
            elif 'hourly' in str(job_row.get('pay_period', '')).lower():
                job_row['formatted_work_type'] = "Part-time"
            # Strategy 3: Default to most common
            else:
                job_row['formatted_work_type'] = "Full-time"
        return job_row

    @staticmethod
    def handle_missing_skills(job_row):
        """Skills missing: extract from description"""
        if pd.isna(job_row['skills']) or job_row['skills'] == "":
            # Extract skills from description using NLP
            extracted = extract_skills_from_text(
                job_row['title'] + " " + job_row['description']
            )
            job_row['skills'] = ", ".join(extracted) if extracted else "Not specified"
            job_row['skills_source'] = "extracted"
        else:
            job_row['skills_source'] = "original"
        return job_row

    @staticmethod
    def handle_missing_experience(job_row):
        """Experience level missing: infer from title"""
        if pd.isna(job_row['formatted_experience_level']):
            title_lower = str(job_row['title']).lower()

            # Pattern matching
            if any(word in title_lower for word in ['senior', 'sr.', 'lead', 'principal']):
                job_row['formatted_experience_level'] = "Mid-Senior level"
            elif any(word in title_lower for word in ['junior', 'jr.', 'entry', 'associate']):
                job_row['formatted_experience_level'] = "Entry level"
            elif any(word in title_lower for word in ['director', 'vp', 'head of', 'chief']):
                job_row['formatted_experience_level'] = "Director"
            elif 'intern' in title_lower:
                job_row['formatted_experience_level'] = "Internship"
            else:
                job_row['formatted_experience_level'] = "Mid-Senior level"  # Most common
        return job_row
```

---

## III. IMPLEMENTATION PRIORITIES

### Phase 1: Critical Missing Data Handling (NOW)

1. **Auto-fill missing work_type** ✅

   ```python
   df['formatted_work_type'] = df['formatted_work_type'].fillna('Full-time')
   ```

2. **Auto-fill missing location** ✅

   ```python
   df['location'] = df.apply(lambda x:
       x['company_city'] if pd.isna(x['location']) and pd.notna(x['company_city'])
       else 'Remote' if x.get('remote_allowed') == 1
       else 'United States'
       , axis=1)
   ```

3. **Auto-fill missing experience** ✅
   ```python
   df['formatted_experience_level'] = df.apply(
       infer_experience_from_title, axis=1
   )
   ```

### Phase 2: Fallback Strategy (NEXT)

1. **Implement progressive filter relaxation**

   - Start with all filters
   - Remove salary → experience → location
   - Always return results

2. **Add "Related Jobs" section**

   - Show jobs even when primary search fails
   - "Jobs similar to your search"

3. **Popular jobs fallback**
   - Cache trending jobs daily
   - Use when filters too restrictive

### Phase 3: Advanced Features (FUTURE)

1. **Smart defaults based on query**

   ```python
   if "remote" in query.lower():
       filters['remote_allowed'] = True
   if "senior" in query.lower():
       filters['experience_level'] = "Mid-Senior level"
   ```

2. **Location expansion**

   ```python
   NEARBY_CITIES = {
       'San Francisco': ['San Jose', 'Oakland', 'Palo Alto', 'Bay Area'],
       'New York': ['Brooklyn', 'Queens', 'Manhattan', 'NYC'],
   }
   ```

3. **Skill synonym matching**
   ```python
   SKILL_SYNONYMS = {
       'python': ['py', 'python3', 'django', 'flask'],
       'javascript': ['js', 'react', 'angular', 'vue'],
   }
   ```

---

## IV. ĐÁNH GIÁ VỚI YÊU CẦU PROJECT

### Yêu cầu từ FinalProject_recommendation_system.md

| Yêu cầu                             | Hiện tại                   | Cần thêm                |
| ----------------------------------- | -------------------------- | ----------------------- |
| **2. Làm sạch dữ liệu (3/7 tasks)** | ✅                         |                         |
| - Missing values                    | ✅ Fill Unknown            | ⚠️ Cần smart imputation |
| - Chuẩn hóa                         | ✅ Text cleaning           | ✅                      |
| - Loại bỏ duplicates                | ✅                         | ✅                      |
| - Vector hóa                        | ✅ TF-IDF + MiniLM         | ✅                      |
| **3. EDA (3/4 tasks)**              | ✅                         |                         |
| - Phân bố                           | ✅ Work type, location     | ✅                      |
| - Top items                         | ✅ Skills, industries      | ✅                      |
| - Heatmap/charts                    | ✅                         | ✅                      |
| **4. Xây dựng hệ gợi ý**            | ✅                         | ⚠️                      |
| - Model                             | ✅ TF-IDF + MiniLM + FAISS | ✅                      |
| - **Fallback strategy**             | ❌ **THIẾU**               | 🔴 **CRITICAL**         |
| **5. Đánh giá**                     | ✅                         |                         |
| - Precision@K                       | ✅ P@5: 94.3%, P@10: 90%   | ✅                      |
| **6. Giao diện**                    | ✅                         |                         |
| - Streamlit                         | ✅ Indeed-style UI         | ✅                      |
| **Nâng cao**                        |                            |                         |
| - Embeddings                        | ✅ MiniLM                  | ✅                      |
| - Real-time                         | ✅ FAISS <20ms             | ✅                      |
| - Lịch sử                           | ✅ query_history.json      | ✅                      |
| - Context-aware                     | ❌                         | 🟡 Optional             |

---

## V. KHUYẾN NGHỊ TRIỂN KHAI

### Immediate (Day 7+)

1. ✅ **Add progressive filter relaxation** (30 mins)
2. ✅ **Implement smart missing data imputation** (1 hour)
3. ✅ **Add "no results" fallback to popular jobs** (30 mins)

### Short-term (Day 8)

1. **Location expansion logic** (1 hour)
2. **Experience level inference from title** (30 mins)
3. **Skill extraction from description** (1 hour)

### Long-term (Post-submission)

1. **Collaborative filtering** (users with similar profiles)
2. **Time-decay popularity ranking**
3. **A/B testing framework**

---

## VI. CODE EXAMPLES

### Example 1: Progressive Filter Relaxation

```python
def get_recommendations_smart(query, filters, top_k=20):
    """Progressively relax filters until sufficient results"""

    filter_priority = [
        'min_salary',      # Relax first (least reliable)
        'max_salary',
        'experience_level',
        'remote_allowed',
        'location',        # Relax last (most important)
    ]

    # Try with all filters
    results = search_with_filters(query, filters, top_k * 12)
    if len(results) >= top_k:
        return results.head(top_k), "exact_match"

    # Progressively remove filters
    working_filters = filters.copy()
    for filter_key in filter_priority:
        if filter_key in working_filters:
            removed_value = working_filters.pop(filter_key)
            results = search_with_filters(query, working_filters, top_k * 10)

            if len(results) >= top_k:
                return results.head(top_k), f"relaxed_{filter_key}"

    # Last resort: no filters
    results = search_with_filters(query, {}, top_k * 5)
    return results.head(top_k), "query_only"
```

### Example 2: Smart Missing Data Handler

```python
def preprocess_with_smart_imputation(df):
    """Apply smart imputation strategies"""

    # 1. Work type
    df['formatted_work_type'] = df.apply(
        lambda x: infer_work_type(x) if pd.isna(x['formatted_work_type'])
        else x['formatted_work_type'],
        axis=1
    )

    # 2. Location
    df['location'] = df.apply(infer_location, axis=1)

    # 3. Experience
    df['formatted_experience_level'] = df.apply(
        infer_experience, axis=1
    )

    # 4. Salary (mark as missing, don't impute)
    df['has_salary'] = df['salary_median'].notna()

    return df
```

---

## Conclusion

**Current Gap**: Hệ thống thiếu fallback strategies → User trải nghiệm kém khi filters quá strict.

**Best Practice**: LinkedIn/Indeed approach với multi-layer fallback.

**Action Items**:

1. Implement progressive filter relaxation
2. Add smart missing data imputation
3. Always return results (never empty state)
