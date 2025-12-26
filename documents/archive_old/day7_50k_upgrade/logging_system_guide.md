# Comprehensive Logging System - Debug Guide

**Date**: November 27, 2025  
**Purpose**: Trace toàn bộ luồng từ Frontend (Streamlit) đến Backend (Recommender) để debug search issues

---

## Logging Architecture

### 1. Log Files

```
logs/
├── app_debug.log          # Main application logs (FE + BE combined)
├── test_debug.log         # Test script logs
└── query_history.json     # User query analytics
```

### 2. Log Levels & Format

```python
# Format: timestamp - module - level - [file:line] - message
2025-11-27 18:22:36 - src.recommender - INFO - [recommender.py:81] - Query: 'software engineer'
```

**Levels Used**:

- `INFO`: Normal flow (search requests, filter applications, results)
- `WARNING`: Potential issues (0 results, missing data)
- `DEBUG`: Detailed trace (urllib, tensor operations)

---

## Frontend Logging (app.py)

### Load Phase

```python
logger.info("=" * 80)
logger.info("LOADING RECOMMENDER SYSTEM")
logger.info("=" * 80)

# Logs:
✓ Recommender loaded in 8.23s
✓ Total jobs in dataset: 123,842
✓ Total indexed jobs: 50,000
✓ Available columns: [list of 67 columns]
```

### Search Phase

```python
logger.info("NEW SEARCH REQUEST FROM FRONTEND")
logger.info(f"Query: '{query}'")

# For each filter applied:
logger.info(f"Filter - Location: {location}")
logger.info(f"Filter - Work Type: {work_type}")
logger.info(f"Total Filters Applied: {len(filters)}")
```

**Example Output**:

```
Query: 'software engineer'
Filter - Location: New York
Filter - Work Type: Full-time
Total Filters Applied: 2
Filters Dict: {'location': 'New York', 'work_type': 'Full-time'}
```

### Results Phase

```python
logger.info(f"<<< Recommender returned {len(results)} results in {search_time:.2f}ms")

# If results > 0:
logger.info(f"First result preview:")
logger.info(f"  - Title: {results.iloc[0].get('title')}")
logger.info(f"  - Location: {results.iloc[0].get('location')}")

# If results == 0:
logger.warning("⚠️ ZERO RESULTS RETURNED - Potential Issue!")
```

---

## Backend Logging (recommender.py)

### get_recommendations() Entry

```python
logger.info("=" * 80)
logger.info("BACKEND: get_recommendations() CALLED")
logger.info("=" * 80)
logger.info(f"Query: '{query}'")
logger.info(f"top_k: {top_k}")
logger.info(f"method: {method}")
logger.info(f"filters: {filters}")
logger.info(f"Calculated fetch_k: {fetch_k}")
```

**Example**:

```
Query: 'software engineer'
top_k: 10
method: faiss
filters: {'location': 'New York', 'work_type': 'Full-time'}
Calculated fetch_k: 120 (filters present: True)
```

### Vector Search Phase

```python
logger.info(f">>> Calling vector_store.search() with fetch_k={fetch_k}...")
# ... search happens ...
logger.info(f"<<< vector_store.search() returned {len(results)} results")
logger.info(f"Before filtering - shape: {results.shape}")
logger.info(f"Before filtering - columns: {results.columns.tolist()}")
```

### Filter Application Phase

Each filter logs:

```python
logger.info("  " + "-" * 76)
logger.info("  APPLYING FILTERS")
logger.info(f"  Starting with {len(results)} results")

# Location filter
logger.info(f"  FILTER: Location = ['New York']")
logger.info(f"    - Available locations sample: [first 10 locations]")
logger.info(f"    - Unique locations count: {count}")
logger.info(f"    - Results after location filter: {len(filtered)} (removed {removed})")

# Work type filter
logger.info(f"  FILTER: Work Type = ['Full-time']")
logger.info(f"    - Column name: 'formatted_work_type'")
logger.info(f"    - Available work types: {value_counts_dict}")
logger.info(f"    - Searching for (lowercase): ['full-time']")
logger.info(f"    - Results after work_type filter: {len(filtered)} (removed {removed})")
```

**Example Output**:

```
  ----------------------------------------------------------------------------
  APPLYING FILTERS
  Starting with 120 results

  FILTER: Location = ['New York']
    - Available locations sample: ['NYC', 'San Francisco', ...]
    - Unique locations count: 67
    - Results after location filter: 15 (removed 105)

  FILTER: Work Type = ['Full-time']
    - Column name: 'formatted_work_type'
    - Available work types: {'Full-time': 12, 'Contract': 3}
    - Searching for (lowercase): ['full-time']
    - Results after work_type filter: 12 (removed 3)

  ----------------------------------------------------------------------------
  FILTERING COMPLETE: 120 → 12 results
  Filters applied: ['location', 'work_type']
```

---

## Test Results Analysis

### Test Script: `test_search_debug.py`

**Scenarios Tested**:

1. **Simple search (no filters)**

   - Query: "software engineer"
   - Results: ✅ **10 jobs found**

2. **Location filter**

   - Query: "software engineer" + Location: "New York"
   - Results: ✅ **8 jobs found**
   - Log shows: 120 candidates → 8 after location filter

3. **Work type filter**

   - Query: "software engineer" + Work Type: "Full-time"
   - Results: ✅ **10 jobs found**
   - Log shows: 120 candidates → 87 Full-time → top 10 returned

4. **Multiple filters**

   - Query: "python developer" + SF + Full-time
   - Results: ✅ **2 jobs found**
   - Log trace:
     ```
     120 candidates
     → 3 after location filter (San Francisco)
     → 2 after work_type filter (Full-time)
     ```

5. **Salary filter**
   - Query: "data scientist" + Min Salary: $80k
   - Results: ⚠️ **0 jobs found**
   - **Root Cause** (from logs):
     ```
     Jobs with salary data: 1 (out of 120)
     Salary range: $55000 - $55000
     Results after min_salary filter: 0 (removed 120)
     ```
   - **Issue**: Indexed jobs thiếu salary data (chỉ 1/120 có salary info)

---

## Key Insights from Logs

### 1. System Performance

```
✓ 50k indexed jobs loaded successfully
✓ Search speed: 13-18ms (FAISS)
✓ Filter speed: <5ms per filter
✓ Total query time: 20-25ms (acceptable)
```

### 2. Data Distribution (from 50k indexed)

**Locations**:

```
United States      3,270 jobs
New York, NY       1,118 jobs
Chicago, IL          758 jobs
Houston, TX          737 jobs
```

**Work Types**:

```
Full-time     39,956 (79.9%)
Contract       4,843 (9.7%)
Part-time      3,908 (7.8%)
Temporary        476 (1.0%)
```

**Salary Coverage**: ⚠️ **Very Low** (~1-2% of results have salary data)

### 3. Filter Effectiveness

- **Location filter**: ✅ Works (regex partial match)
- **Work type filter**: ✅ Works (exact match on formatted_work_type)
- **Experience filter**: ✅ Works (regex partial match)
- **Remote filter**: ✅ Works (boolean 0/1)
- **Salary filter**: ⚠️ Works but limited by data availability

---

## Debug Workflow

### When User Reports "No Results"

1. **Check logs/app_debug.log**:

   ```bash
   tail -100 logs/app_debug.log | grep "SEARCH REQUEST"
   ```

2. **Identify the search**:

   ```
   Query: 'xxx'
   Filters: {...}
   ```

3. **Trace filter application**:

   ```
   Starting with: X results
   After location filter: Y results (removed Z)
   After work_type filter: W results (removed V)
   FINAL: W results
   ```

4. **Check data distribution**:
   ```
   Available work types: {...}
   Unique locations: N
   Jobs with salary data: M
   ```

### Common Issues & Solutions

#### Issue 1: "0 results with valid query"

**Log Pattern**:

```
<<< vector_store.search() returned 120 results
After location filter: 0 (removed 120)
```

**Diagnosis**: Filter value không match với data
**Solution**: Check "Available locations sample" in logs

#### Issue 2: "0 results with salary filter"

**Log Pattern**:

```
Jobs with salary data: 1
Salary range: $X - $Y
Results after min_salary filter: 0
```

**Diagnosis**: Thiếu salary data trong indexed jobs
**Solution**:

- Increase fetch_k multiplier
- Or disable salary filter UI
- Or re-index with jobs that have salary

#### Issue 3: "Slow search (>100ms)"

**Log Pattern**:

```
Calculated fetch_k: 2000 (filters present: True)
<<< vector_store.search() returned 2000 results
```

**Diagnosis**: fetch_k quá cao (nhiều filters + high top_k)
**Solution**: Adjust multiplier từ 12x → 10x

---

## Log Monitoring Commands

### Real-time monitoring

```bash
# Watch app logs
tail -f logs/app_debug.log

# Filter for warnings
tail -f logs/app_debug.log | grep WARNING

# Filter for zero results
tail -f logs/app_debug.log | grep "ZERO RESULTS"
```

### Analytics

```bash
# Count searches per hour
grep "NEW SEARCH REQUEST" logs/app_debug.log | wc -l

# Most common queries
grep "Query:" logs/app_debug.log | sort | uniq -c | sort -rn | head -10

# Average search time
grep "returned.*results in" logs/app_debug.log | awk '{print $NF}' | sed 's/ms//' | awk '{sum+=$1; n++} END {print sum/n "ms"}'
```

---

## Conclusion

✅ **Logging system hoạt động hoàn hảo**:

- Trace toàn bộ luồng từ FE → BE
- Chi tiết từng bước filter application
- Hiển thị data distribution để debug

✅ **Search system với 50k data hoạt động tốt**:

- Location filters: ✅
- Work type filters: ✅
- Multiple filters: ✅
- Performance: 20-25ms (excellent)

⚠️ **Issue thực sự**: **Thiếu salary data** trong indexed jobs, không phải bug tìm kiếm!

**Recommendation**:

1. ✅ Keep current logging (very helpful)
2. ⚠️ Consider hiding salary filter in UI (data coverage too low)
3. ✅ 50k index is production-ready for location/work_type/experience filters
