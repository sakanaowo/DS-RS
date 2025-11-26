source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate
streamlit run app.py --server.port 8501 --server.headless=true