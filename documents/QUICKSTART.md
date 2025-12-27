# 🚀 Quick Start Guide

## Start Server

```bash
# Option 1: Start with progress indicators (RECOMMENDED)
./start_with_progress.sh

# Option 2: Basic start
./start_server.sh

# Option 3: Manual start
source ~/miniconda3/etc/profile.d/conda.sh
conda activate base
streamlit run app.py --server.port 8501
```

## Important Notes

### ⏳ First Startup (2-5 minutes)
The app needs to:
1. **Load 50K job index** (~20s)
2. **Load AI model** (~10s)  
3. **Generate embeddings** (2-4 minutes) ← SLOWEST STEP

**Progress in logs:**
```
[DEBUG] BM25 engine initialized          ← Step 1 done
[DEBUG] Semantic model loaded            ← Step 2 done
[DEBUG] Starting embeddings generation   ← Step 3 starting (WAIT HERE)
[DEBUG] Encoding completed!              ← Step 3 done - READY!
```

### ⚡ Subsequent Startups (~30s)
After first run, embeddings are cached:
- No regeneration needed
- Loads from disk in ~10s
- Total startup ~30s

## URLs

- **Main App:** http://localhost:8501 (Hybrid Search)
- **Simple App:** http://localhost:8502 (BM25 only, faster)

## Test Simple Version (No AI, Fast)

```bash
streamlit run app_simple.py --server.port 8502
```
- Opens in 10 seconds
- BM25 search only
- Good for quick testing

## Troubleshooting

### Problem: Script says "source: not found"
**Fix:** Use `./start_with_progress.sh` (fixed)

### Problem: Stuck at "Semantic data loaded"
**Status:** Normal! Encoding embeddings takes 2-4 minutes
**Action:** Wait patiently, watch for "[DEBUG] Encoding completed!"

### Problem: Out of memory
**Fix:** Edit app.py line 89:
```python
hybrid = HybridJobSearch(
    sample_size=10000,  # Use smaller sample
    verbose=False
)
```

### Problem: Taking too long (>10 min)
**Action:** 
1. Stop with Ctrl+C
2. Run simple version: `streamlit run app_simple.py --server.port 8502`
3. Check system resources: `htop` or `top`

## Debug Commands

```bash
# Check if running
ps aux | grep streamlit

# Kill streamlit
pkill -f streamlit

# View logs
tail -f debug.log

# Check embeddings cache
ls -lh data/processed/embeddings_*.pkl
```

## Next Steps After Startup

Once you see "🎉 READY!" or "[DEBUG] Encoding completed!":

1. Open http://localhost:8501
2. Try searches:
   - "software engineer"
   - "data scientist remote"
   - "python developer machine learning"
3. Adjust BM25/Semantic weights in sidebar
4. Compare results with different weights

## Performance Tips

- First search may be slow (cache warmup)
- Subsequent searches: <1 second
- Use filters to narrow results
- Download results as CSV for analysis
