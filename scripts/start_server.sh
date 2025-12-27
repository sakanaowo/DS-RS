#!/bin/bash
# Start Streamlit server with conda environment

# Source conda
eval "$(conda shell.bash hook)"
conda activate base

# Run streamlit
echo "🚀 Starting Streamlit on http://localhost:8501"
echo "⏳ First load may take 2-5 minutes (generating embeddings)..."
echo ""
streamlit run app.py --server.port 8501 --server.headless=true