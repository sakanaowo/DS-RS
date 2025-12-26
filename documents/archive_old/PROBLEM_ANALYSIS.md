# Phân Tích Vấn Đề & Kế Hoạch Triển Khai Lại

**Date**: December 26, 2025  
**Status**: 🔴 CRITICAL - Cần thiết kế lại từ đầu

---

## 🚨 VẤN ĐỀ PHÁT HIỆN

### 1. Vấn đề về Data Pipeline

#### **A. Thiết kế sai về cấu trúc dữ liệu**

**Hiện tại làm gì**:
```python
# loader.py - build_enriched_jobs()
1. Load postings.csv (123k jobs)
2. JOIN với job_skills.csv → aggregate thành "skill1, skill2, skill3"
3. JOIN với job_industries.csv → aggregate thành "industry1, industry2"
4. JOIN với salaries.csv
5. JOIN với benefits.csv
6. JOIN với companies.csv (company metadata)
→ Tạo một DataFrame rất rộng với nhiều cột text đã aggregated
```

**Vấn đề**:
- ❌ **Mất cấu trúc quan hệ**: Skills và industries bị gộp thành string → mất khả năng filter chính xác
- ❌ **Không thể search theo skill riêng lẻ**: "Python, Java, SQL" → user search "Python" sẽ match cả string
- ❌ **Duplicate data**: Mỗi job có nhiều skills → gộp thành string → lặp lại nhiều lần
- ❌ **Preprocessing không phù hợp**: Vector hóa trên text đã gộp → bias về jobs có nhiều skills

**Ví dụ cụ thể**:
```
Job A: skills = "Python, Machine Learning, SQL, Data Analysis, Statistics"
Job B: skills = "Python"

User query: "Python developer"
→ Job A có score cao hơn vì có nhiều keywords
→ Nhưng Job B có thể relevant hơn (chỉ cần Python)
```

#### **B. Thiết kế sai về feature engineering**

**Hiện tại làm gì**:
```python
# preprocessing.py - prepare_features()
content = title*2 + " " + description + " " + skills_desc
→ Vector hóa content này với TF-IDF hoặc MiniLM
```

**Vấn đề**:
- ❌ **Title được repeat 2 lần**: Artificial weighting không dựa trên data
- ❌ **Description quá dài**: Thường 500-2000 chars → overwhelm title/skills
- ❌ **Không có skill weighting**: Skill quan trọng nhưng bị drown bởi description
- ❌ **Không có industry context**: Industry/company size bị bỏ qua

**Kết quả**:
- Search "Python developer" → match cả jobs về "Python library documentation" (description có Python)
- Filter by skill không work vì skills đã bị gộp vào content text

---

### 2. Vấn đề về Recommendation Logic

#### **A. Pure content-based không đủ**

**Hiện tại**:
- TF-IDF/MiniLM trên text content
- Cosine similarity để rank
- Apply filters sau khi search

**Vấn đề**:
- ❌ **Cold start**: User mới không có history → chỉ dựa vào query text
- ❌ **Không có personalization**: Tất cả users search "Python" đều có kết quả giống nhau
- ❌ **Không có context**: Location, experience level, salary expectations không được model học

**Thiếu**:
- Collaborative filtering (users who viewed A also viewed B)
- Hybrid approach (content + collaborative + popularity)
- Learning-to-rank (train model từ click/apply data)

#### **B. Filter logic không tối ưu**

**Hiện tại**:
```python
# Progressive fallback (7 layers)
Layer 1: All filters
Layer 2: Remove salary
Layer 3: Remove experience
...
Layer 7: Popular jobs
```

**Vấn đề**:
- ❌ **Band-aid solution**: Fallback là workaround cho data quality kém
- ❌ **Không giải quyết root cause**: Data pipeline sai từ đầu
- ❌ **User experience kém**: User search với filters cụ thể → nhận được unrelated jobs (Layer 7)

**Ví dụ**:
```
User: "Remote Python developer in California, $100k-150k"
→ Layer 1: 0 results (salary data 23% coverage)
→ Layer 2: 0 results (remove salary)
→ ...
→ Layer 7: Popular jobs (có thể là "Nurse in Texas, $50k")
❌ Completely irrelevant!
```

---

### 3. Vấn đề về Data Quality

#### **A. Missing data không được xử lý đúng**

**Hiện tại**:
- Smart imputation (data_quality.py)
- Infer work_type, location, experience từ patterns

**Vấn đề**:
- ❌ **Imputation không reliable**: "Senior" in title → "Mid-Senior level" (không phải lúc nào cũng đúng)
- ❌ **Salary không impute**: 23% coverage → filters không work
- ❌ **Remote flag 12% coverage**: Majority jobs không biết remote hay không

**Root cause**: Không nên impute từ patterns → nên fix data source hoặc accept missing

#### **B. Text processing không phù hợp**

**Hiện tại**:
```python
clean_text():
- Remove HTML, URLs, special chars
- Lowercase
- Remove stopwords
- Join với spaces
```

**Vấn đề**:
- ❌ **Mất semantic**: "Machine Learning" → "machine learning" → tokenize → "machine" + "learning"
- ❌ **Không có n-grams**: "Data Scientist" bị tách thành "data" + "scientist"
- ❌ **Skill names bị mangled**: "C++" → "c" (remove special chars)

---

## 🎯 YÊU CẦU THỰC SỰ CỦA PROJECT

### Từ FinalProject_recommendation_system.md

**Bài toán**: Xây dựng hệ thống gợi ý việc làm

**Yêu cầu core**:
1. ✅ Dataset ≥ 2,000 items (có: 123k jobs)
2. ✅ ≥ 5 features (có: title, description, skills, industry, company, location, salary, work_type, experience)
3. ❌ **Recommendation quality** - CHƯA ĐẠT
4. ❌ **Filter support** - CHƯA WORK ĐÚNG
5. ✅ UI (Streamlit)

**Yêu cầu data processing**:
1. ✅ Missing values (đã xử lý nhưng sai cách)
2. ❌ **Chuẩn hóa dữ liệu** - CHƯA ĐÚNG
3. ✅ Loại bỏ duplicates
4. ⚠️ **Vector hóa** - ĐANG LÀM SAI

**Yêu cầu evaluation**:
1. ❌ Precision@K, Recall@K - CHƯA CÓ GROUND TRUTH
2. ❌ User study - CHƯA CÓ

**Nâng cao**:
1. ⚠️ Context-aware - Có progressive fallback nhưng không phải context-aware thật
2. ✅ Real-time - Search <50ms
3. ✅ User history tracking
4. ❌ **Advanced ML** - CHƯA CÓ

---

## 💡 Ý TƯỞNG MỚI - THIẾT KẾ LẠI TỪ ĐẦU

### Approach 1: Multi-Index Search (Recommended)

**Idea**: Thay vì vector hóa toàn bộ job thành 1 vector, tách thành nhiều indexes:

```
Index 1: Title + Description (semantic meaning)
Index 2: Skills (exact match + embedding)
Index 3: Industry + Company (categorical)
Index 4: Location (geo-spatial or string)
Index 5: Metadata (salary, work_type, experience, remote)
```

**Search flow**:
```python
def search(query, filters):
    # 1. Parse query intent
    query_parsed = parse_query(query)  # "Python dev in SF" → {keywords: [python, dev], location: SF}
    
    # 2. Multi-stage retrieval
    candidates_title = index1.search(query_parsed['keywords'], top_k=1000)
    candidates_skills = index2.search(query_parsed['skills'], top_k=1000)
    
    # 3. Merge & rerank
    candidates = merge(candidates_title, candidates_skills, weights=[0.6, 0.4])
    
    # 4. Apply filters (hard constraints)
    filtered = apply_filters(candidates, filters)
    
    # 5. Final ranking (learning-to-rank or heuristic)
    ranked = rank(filtered, user_profile=None)  # Placeholder for personalization
    
    return ranked[:top_k]
```

**Advantages**:
- ✅ Skills được index riêng → filter chính xác
- ✅ Có thể weight từng component
- ✅ Filter work properly (hard constraints)
- ✅ Dễ debug (biết score từ đâu)

**Disadvantages**:
- ⚠️ Phức tạp hơn (nhiều indexes)
- ⚠️ Cần tuning weights

---

### Approach 2: Hybrid Embeddings (Advanced)

**Idea**: Sử dụng multiple embedding models cho từng loại content:

```
Model 1: all-MiniLM-L6-v2 cho title + description (384 dims)
Model 2: SkillBERT hoặc fine-tuned model cho skills (128 dims)
Model 3: GeoEncoder cho location (64 dims)
→ Concat = 576 dims vector cho mỗi job
```

**Search flow**:
```python
def search(query, filters):
    # 1. Encode query với multi-models
    query_vec = concat([
        model1.encode(query_text),
        model2.encode(query_skills),
        model3.encode(query_location)
    ])
    
    # 2. FAISS search
    candidates = faiss_index.search(query_vec, top_k=1000)
    
    # 3. Apply filters
    filtered = apply_filters(candidates, filters)
    
    return filtered[:top_k]
```

**Advantages**:
- ✅ End-to-end learned
- ✅ Có thể fine-tune models
- ✅ State-of-the-art approach

**Disadvantages**:
- ❌ Cần data để fine-tune
- ❌ Computationally expensive
- ❌ Khó debug

---

### Approach 3: Simplified BM25 + Filters (Pragmatic)

**Idea**: Quay lại basics - BM25 với filters đúng cách

```
1. Index jobs với Elasticsearch/Whoosh/Custom BM25
2. Query = title + description + skills (không gộp, index riêng fields)
3. BM25 scoring với field weights
4. Apply filters as query clauses (NOT as post-processing)
5. Return results
```

**Search flow**:
```python
def search(query, filters):
    es_query = {
        "bool": {
            "must": [
                {"multi_match": {"query": query, "fields": ["title^3", "description", "skills^2"]}}
            ],
            "filter": [
                {"term": {"work_type": filters['work_type']}},
                {"term": {"remote_allowed": filters['remote']}},
                {"range": {"salary": {"gte": filters['min_salary'], "lte": filters['max_salary']}}},
            ]
        }
    }
    results = es.search(query=es_query)
    return results
```

**Advantages**:
- ✅ **SIMPLE** - Dễ hiểu, dễ implement
- ✅ Filters work correctly (query-time, not post-processing)
- ✅ BM25 proven to work well for search
- ✅ Không cần ML (fit yêu cầu project)

**Disadvantages**:
- ⚠️ Không "fancy" (không có embeddings)
- ⚠️ Cần setup Elasticsearch (hoặc implement BM25 custom)

---

## 🚀 KẾ HOẠCH TRIỂN KHAI MỚI

### Option A: Full Redesign (Approach 1 - Multi-Index)

**Timeline**: 5-7 days

**Day 1: Data pipeline redesign**
- ❌ BỎ: `build_enriched_jobs()` (join tất cả thành 1 table)
- ✅ TẠO: 
  - `jobs` table (job_id, title, description, company_id, location, salary, work_type, experience, remote)
  - `job_skills` table (job_id, skill_id) - KHÔNG gộp
  - `job_industries` table (job_id, industry_id) - KHÔNG gộp
  - `skills` lookup table (skill_id, skill_name)
  - `industries` lookup table (industry_id, industry_name)

**Day 2: Index building**
- Create Index 1: Title + Description (TF-IDF hoặc MiniLM)
- Create Index 2: Skills (inverted index hoặc embeddings)
- Create Index 3: Metadata (filters)

**Day 3-4: Search implementation**
- Multi-stage retrieval
- Merge & rerank logic
- Filter application (hard constraints)

**Day 5-6: Evaluation & tuning**
- Manual evaluation với test queries
- Tune weights
- Precision@K, Recall@K (với manual labels)

**Day 7: UI & documentation**

---

### Option B: Quick Fix (Approach 3 - BM25 + Filters)

**Timeline**: 2-3 days

**Day 1: Switch to BM25**
- Install Whoosh or implement rank_bm25
- Index với separate fields (title, description, skills)
- Remove vector embeddings (simplify)

**Day 2: Fix filters**
- Filters as query clauses (not post-processing)
- Remove progressive fallback (band-aid)
- Accept 0 results if filters too strict (honest UX)

**Day 3: Cleanup & evaluation**
- Test với realistic queries
- Document tradeoffs
- Update UI

---

### Option C: Hybrid (Recommended) ⭐

**Timeline**: 4-5 days

**Day 1: Data pipeline cleanup**
- Keep separate tables (jobs, job_skills, job_industries)
- Create proper indexes with constraints
- Remove aggregation to comma-separated strings

**Day 2: Implement BM25 baseline**
- BM25 với field weights (title^3, skills^2, description^1)
- Filters as hard constraints (query clauses)
- Measure baseline performance

**Day 3: Add embeddings (optional layer)**
- Keep BM25 as primary
- Add MiniLM embeddings for semantic boost
- Hybrid scoring: 0.7*BM25 + 0.3*Semantic

**Day 4: Evaluation**
- Test suite với 20 queries (covering different intents)
- Precision@5, @10
- User study (5 people, 5 queries each)

**Day 5: Polish & document**
- UI improvements
- Documentation
- Presentation prep

---

## 🎯 KHUYẾN NGHỊ

**Chọn Option C: Hybrid Approach**

**Lý do**:
1. ✅ **Realistic timeline**: 4-5 days hoàn thành
2. ✅ **Fix root causes**: Data pipeline đúng, filters đúng
3. ✅ **Proven approach**: BM25 + embeddings là industry standard
4. ✅ **Easy to evaluate**: Precision@K dễ measure
5. ✅ **Meets requirements**: Full fill project requirements

**Trade-offs**:
- ⚠️ Bỏ progressive fallback → Accept 0 results if filters too strict
- ⚠️ Không "fancy" như pure embeddings → Nhưng work better
- ⚠️ Cần refactor data pipeline → Worth it

---

## 📋 ACTION ITEMS - IMMEDIATE

**Priority 1 - Data Pipeline** (TODAY):
- [ ] Refactor `loader.py`: Keep normalized tables, NO aggregation
- [ ] Create proper data schema (jobs, job_skills, job_industries)
- [ ] Write data validation tests

**Priority 2 - Search Implementation** (DAY 2-3):
- [ ] Implement BM25 (use rank_bm25 library)
- [ ] Rewrite `recommender.py` với BM25 + filters as clauses
- [ ] Remove progressive fallback (accept 0 results)

**Priority 3 - Evaluation** (DAY 4):
- [ ] Create test query set (20 queries)
- [ ] Manual labeling (relevant/not relevant for each query)
- [ ] Calculate Precision@5, @10

**Priority 4 - Polish** (DAY 5):
- [ ] Update UI
- [ ] Documentation
- [ ] Presentation

---

## 🔚 KẾT LUẬN

**Vấn đề hiện tại**: Data pipeline sai từ đầu → aggregation mất cấu trúc → filters không work → band-aid với progressive fallback

**Giải pháp**: Redesign data pipeline → BM25 với filters đúng cách → Optional embeddings layer

**Timeline**: 4-5 days với Option C (Hybrid)

**Next step**: Bắt đầu refactor `loader.py` TODAY

---

**Status**: 🟡 READY TO START REDESIGN
