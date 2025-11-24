# Hướng dẫn tối ưu bộ nhớ - Day 2 Pipeline

## Nguyên nhân VSCode chiếm ~10GB RAM

### 1. Dataset lớn

- `postings.csv`: 493MB → ~1.5-2.5GB khi load vào pandas
- 8 bảng phụ thêm ~500MB RAM

### 2. Multiple joins không được optimize

- 8 lần merge tạo intermediate DataFrames
- Garbage collector chưa kịp dọn dẹp

### 3. Jupyter kernel cache

- Output của mỗi cell được giữ trong memory
- Biến toàn cục không được giải phóng

### 4. String operations overhead

- Text cleaning tạo nhiều temporary strings
- 124K jobs × 3 text fields × multiple passes

### 5. VSCode extensions overhead

- Pylance cache: ~500MB-1GB
- Jupyter kernel: ~2-3GB
- Variable inspector: giữ references đến tất cả biến

---

## Các giải pháp

### A. Tối ưu code (Ưu tiên cao)

#### 1. Chunk processing trong loader.py

```python
def build_enriched_jobs_chunked(
    sample: Optional[int] = None,
    chunk_size: int = 10000,
    persist: bool = False,
    output_name: str = "jobs_stage1.parquet",
) -> pd.DataFrame:
    """Process data in chunks to reduce memory usage."""
    import gc

    postings = load_raw_postings()
    if sample:
        postings = postings.head(sample)

    total_rows = len(postings)
    chunks = []

    for start in range(0, total_rows, chunk_size):
        end = min(start + chunk_size, total_rows)
        chunk = postings.iloc[start:end].copy()

        # Process chunk (existing join logic)
        enriched_chunk = _enrich_chunk(chunk)
        chunks.append(enriched_chunk)

        # Force garbage collection
        del chunk
        gc.collect()

        print(f"Processed {end:,}/{total_rows:,} rows")

    result = pd.concat(chunks, ignore_index=True)
    del chunks
    gc.collect()

    return result
```

#### 2. Giải phóng memory sau mỗi bước

```python
# Trong build_enriched_jobs()
enriched = postings.merge(skill_agg, on="job_id", how="left")
del skill_agg  # ← Thêm dòng này
gc.collect()

enriched = enriched.merge(industry_agg, on="job_id", how="left")
del industry_agg  # ← Thêm dòng này
gc.collect()
```

#### 3. Sử dụng dtypes tối ưu

```python
# Trong load_raw_postings()
dtype_map = {
    'job_id': 'int64',
    'company_id': 'int64',
    'remote_allowed': 'int8',
    'views': 'int32',
    'applies': 'int32',
    # String fields → category cho các cột có ít unique values
    'formatted_work_type': 'category',
    'formatted_experience_level': 'category',
    'pay_period': 'category',
}

postings = pd.read_csv(path, dtype=dtype_map, **kwargs)
```

#### 4. Tối ưu string cleaning

```python
# Trong prepare_features()
# Thay vì:
cleaned[f"{field}_clean"] = cleaned[field].fillna("").apply(lambda x: clean_text(x))

# Dùng vectorized operations:
cleaned[f"{field}_clean"] = (
    cleaned[field]
    .fillna("")
    .str.replace(_HTML_TAG_PATTERN, " ", regex=True)
    .str.replace(_URL_PATTERN, " ", regex=True)
    .str.normalize("NFKD")
    .str.encode("ascii", errors="ignore")
    .str.decode("ascii")
    .str.lower()
    .str.replace(_WORD_PATTERN, " ", regex=True)
    .str.replace(r"\s+", " ", regex=True)
    .str.strip()
)
```

### B. Tối ưu Jupyter Notebook

#### 1. Clear output thường xuyên

```python
# Thêm vào đầu notebook
from IPython.display import clear_output
import gc

# Sau các cell lớn:
gc.collect()
clear_output(wait=True)
```

#### 2. Xóa biến không cần thiết

```python
# Sau khi xử lý xong sample
del sample_cleaned
gc.collect()
```

#### 3. Giới hạn display output

```python
# Thay vì:
display(full_cleaned.head())

# Dùng:
pd.set_option('display.max_rows', 10)
pd.set_option('display.max_columns', 10)
print(full_cleaned.head().to_string())
```

### C. Cấu hình VSCode

#### 1. Giảm cache của Pylance

Thêm vào `.vscode/settings.json`:

```json
{
  "python.analysis.memory.keepLibraryAst": false,
  "python.analysis.memory.keepLibraryLocalVariables": false,
  "jupyter.variableQueries": [],
  "jupyter.enableCellCodeLens": false
}
```

#### 2. Restart kernel định kỳ

- Sau mỗi 5-10 cells lớn, chọn: `Kernel > Restart Kernel`

#### 3. Tắt Copilot khi chạy heavy cells

- Tạm thời disable Copilot trước khi chạy cell 29 (full processing)

### D. Sử dụng công cụ thay thế

#### 1. Chuyển sang script thay vì notebook

```bash
# Chạy từ terminal thay vì notebook
python scripts/run_cleaning.py --sample 5000
```

#### 2. Sử dụng Dask cho big data

```python
import dask.dataframe as dd

# Thay vì pandas
postings = dd.read_csv(path).compute()
```

#### 3. Sử dụng Parquet ngay từ đầu

```python
# Convert CSV → Parquet một lần
postings.to_parquet('data/raw/postings.parquet', compression='snappy')

# Load nhanh hơn, ít RAM hơn
postings = pd.read_parquet('data/raw/postings.parquet')
```

---

## Checklist tối ưu ngay

- [ ] Thêm `gc.collect()` sau mỗi merge trong `build_enriched_jobs()`
- [ ] Thêm `del` statements để xóa intermediate DataFrames
- [ ] Optimize dtypes cho các cột (category, int8, int32)
- [ ] Clear notebook output sau mỗi cell lớn
- [ ] Tắt Copilot khi chạy full processing
- [ ] Restart kernel trước khi chạy cell 29
- [ ] Chạy script từ terminal nếu notebook quá chậm

---

## Benchmark ước tính

| Phương pháp              | RAM peak | Thời gian |
| ------------------------ | -------- | --------- |
| Original code (notebook) | ~10GB    | 5-10 phút |
| + gc.collect()           | ~7GB     | 5-10 phút |
| + optimized dtypes       | ~5GB     | 4-8 phút  |
| + chunk processing       | ~3GB     | 6-12 phút |
| Script (không notebook)  | ~2.5GB   | 4-8 phút  |
| Dask parallel            | ~2GB     | 3-6 phút  |

---

**Khuyến nghị:** Bắt đầu với việc thêm `gc.collect()` và optimize dtypes (dễ implement, hiệu quả cao).
