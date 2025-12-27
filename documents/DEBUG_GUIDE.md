# Debug Guide for Streamlit UI

## Current Status

**Issue:** Streamlit app loads but UI không hiện ra gì cả

**Debug Steps Completed:**

1. ✅ Thêm debug logging vào `app.py`
2. ✅ Thêm debug logging vào `src/hybrid_search.py`  
3. ✅ Tạo `app_simple.py` (BM25 only - for quick testing)

## Debug Logs Added

### app.py
- Import tracking
- Function entry/exit logging
- Exception handling với full traceback
- Stage-by-stage rendering logs

### src/hybrid_search.py
- Initialization progress tracking
- Component loading status
- Timing information

## How to Debug

### Option 1: Check Full App (với Hybrid Search)
```bash
cd /home/sakana/Code/DS-RS
source ~/miniconda3/etc/profile.d/conda.sh
conda activate base
streamlit run app.py --server.port 8501 2>&1 | tee debug.log
```

Sau đó mở browser: http://localhost:8501
Xem logs trong terminal để biết app đang ở stage nào

### Option 2: Test Simple App (BM25 only - nhanh hơn)
```bash
cd /home/sakana/Code/DS-RS
source ~/miniconda3/etc/profile.d/conda.sh
conda activate base
streamlit run app_simple.py --server.port 8502 2>&1 | tee debug_simple.log
```

Mở browser: http://localhost:8502
Nếu simple app hoạt động → Issue là ở semantic search loading

### Option 3: Use start_server.sh
```bash
cd /home/sakana/Code/DS-RS
./start_server.sh
```

## Expected Debug Output

Nếu app hoạt động bình thường, log sẽ như sau:

```
[DEBUG] app.py starting...
[DEBUG] __main__ block executing...
[DEBUG] main() called
[DEBUG] Rendering header...
[DEBUG] Header rendered
[DEBUG] Initializing search engine...
[DEBUG] initialize_search_engine() called
[DEBUG] Creating HybridJobSearch...
[DEBUG] Calling hybrid.initialize()...
[DEBUG] HybridJobSearch.initialize() starting...
[DEBUG] Initializing BM25 engine...
[DEBUG] BM25 engine initialized
[DEBUG] Initializing Semantic engine...
[DEBUG] SemanticJobSearch created
[DEBUG] Semantic model loaded
[DEBUG] Semantic data loaded
[DEBUG] Semantic jobs encoded
[DEBUG] HybridJobSearch.initialize() completed in XX.XXs
[DEBUG] Search engine initialized: <class 'src.hybrid_search.HybridJobSearch'>
[DEBUG] Rendering sidebar...
[DEBUG] Rendering search input...
[DEBUG] Query: ''
[DEBUG] Displaying welcome message...
[DEBUG] Welcome message displayed
```

## Common Issues

### 1. UI không hiện gì (blank page)
- **Symptom:** Browser shows blank page, no error
- **Cause:** Có thể app đang stuck ở loading stage
- **Check:** Xem debug logs để biết đang stuck ở đâu
- **Fix:** 
  - Nếu stuck ở "Semantic jobs encoded" → Đợi thêm (có thể mất 1-2 phút cho 50K jobs)
  - Nếu stuck ở stage khác → Check traceback

### 2. Semantic search quá lâu
- **Symptom:** App load > 5 minutes
- **Cause:** Đang generate embeddings cho 50K jobs lần đầu
- **Fix:** Đợi xong lần đầu, sau đó sẽ dùng cache (~10s)
- **Alternative:** Dùng `app_simple.py` (BM25 only) trong lúc chờ

### 3. Memory error
- **Symptom:** Process killed hoặc out of memory
- **Cause:** 50K embeddings cần ~8GB RAM
- **Fix:** Giảm sample_size trong `app.py` line 89:
  ```python
  hybrid = HybridJobSearch(
      sample_size=10000,  # Thay vì None
      verbose=False
  )
  ```

## Next Steps

1. **Check browser console** (F12) xem có JavaScript error không
2. **Check terminal logs** để xem app đang ở stage nào
3. **Try simple app** để verify BM25 hoạt động
4. **Wait patiently** cho semantic embeddings generate (1st time only)

## Log Files

- `debug.log` - Full app output
- `debug_simple.log` - Simple app output
- Check with: `tail -f debug.log`
