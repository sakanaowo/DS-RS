#!/bin/bash
# Quick start script with better feedback

echo "🚀 Starting Job Search Engine..."
echo ""
echo "📋 Startup checklist:"
echo "  ✓ Activating conda environment..."

# Activate conda
eval "$(conda shell.bash hook)"
conda activate base

echo "  ✓ Starting Streamlit server..."
echo ""
echo "⏳ IMPORTANT: First startup takes 2-5 minutes"
echo "   - Loading 50K job index"
echo "   - Generating semantic embeddings (CPU intensive)"
echo "   - Building search cache"
echo ""
echo "📊 Progress will show in logs below..."
echo "🌐 Once ready, open: http://localhost:8501"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Run with unbuffered output
PYTHONUNBUFFERED=1 streamlit run app.py --server.port 8501 --server.headless=true 2>&1 | while IFS= read -r line; do
    echo "$line"
    
    # Highlight key progress points
    if [[ "$line" == *"BM25 engine initialized"* ]]; then
        echo "✅ Step 1/3: BM25 search ready"
    elif [[ "$line" == *"Semantic model loaded"* ]]; then
        echo "✅ Step 2/3: AI model loaded"
    elif [[ "$line" == *"Encoding completed"* ]]; then
        echo "✅ Step 3/3: Embeddings generated"
        echo ""
        echo "🎉 READY! Open http://localhost:8501 in your browser"
        echo ""
    fi
done
