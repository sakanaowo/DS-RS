"""
Simple Streamlit UI for Quick Testing

Minimal version without semantic search to test if UI works
"""

import streamlit as st
import pandas as pd
import time
import traceback
import sys

from src.recommender import JobRecommender

print("[DEBUG] app_simple.py starting...", file=sys.stderr, flush=True)

st.set_page_config(page_title="Job Search (Simple)", page_icon="🔍", layout="wide")


@st.cache_resource(show_spinner=False)
def initialize_search():
    """Initialize BM25 search only."""
    print("[DEBUG] Initializing BM25 only...", file=sys.stderr, flush=True)
    with st.spinner("Loading search engine..."):
        recommender = JobRecommender(auto_load=True)
    print("[DEBUG] BM25 initialized!", file=sys.stderr, flush=True)
    return recommender


def main():
    print("[DEBUG] main() called", file=sys.stderr, flush=True)

    st.title("🔍 Job Search Engine (Simple)")
    st.markdown("**BM25 Search Only** - For testing")
    st.markdown("---")

    # Initialize
    try:
        recommender = initialize_search()
        st.success("✅ Search engine loaded!")
    except Exception as e:
        st.error(f"❌ Failed to load: {e}")
        st.code(traceback.format_exc())
        st.stop()

    # Search
    query = st.text_input("🔎 Search Query", placeholder="e.g., software engineer")

    if query:
        with st.spinner("Searching..."):
            try:
                results = recommender.get_recommendations(
                    query=query, top_k=10, method="tfidf", enable_fallback=False
                )

                st.success(f"✅ Found {len(results)} results")

                # Display
                for idx, row in results.head(5).iterrows():
                    with st.container():
                        st.subheader(f"{row['title']}")
                        st.write(f"🏢 {row.get('company_name', 'N/A')}")
                        st.write(f"📍 {row.get('location', 'N/A')}")
                        st.markdown("---")

            except Exception as e:
                st.error(f"Search failed: {e}")
                st.code(traceback.format_exc())
    else:
        st.info("👋 Enter a search query to get started!")


if __name__ == "__main__":
    print("[DEBUG] Running main...", file=sys.stderr, flush=True)
    main()
    print("[DEBUG] Main completed", file=sys.stderr, flush=True)
