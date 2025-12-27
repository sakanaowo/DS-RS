"""
Streamlit UI for Job Search System

Day 4 Implementation - Production UI

Features:
- Clean, modern interface
- Search with filters
- Hybrid search (BM25 + Semantic)
- Pagination
- Job details view
- Performance metrics
"""

import streamlit as st
import pandas as pd
import time
import traceback
import sys
from typing import Optional, Dict

from src.hybrid_search import HybridJobSearch

# Debug logging
print("[DEBUG] app.py starting...", file=sys.stderr, flush=True)


# Page config
st.set_page_config(
    page_title="Job Search Engine",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown(
    """
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .job-card {
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        margin-bottom: 1rem;
        background-color: #f9f9f9;
    }
    .job-title {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2c3e50;
        margin-bottom: 0.5rem;
    }
    .job-company {
        font-size: 1.1rem;
        color: #7f8c8d;
        margin-bottom: 0.5rem;
    }
    .job-location {
        font-size: 1rem;
        color: #95a5a6;
    }
    .score-badge {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        font-size: 0.9rem;
        font-weight: bold;
        margin-right: 0.5rem;
    }
    .score-high {
        background-color: #d4edda;
        color: #155724;
    }
    .score-medium {
        background-color: #fff3cd;
        color: #856404;
    }
    .score-low {
        background-color: #f8d7da;
        color: #721c24;
    }
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_resource(show_spinner=False)
def initialize_search_engine():
    """Initialize hybrid search engine (cached)."""
    print("[DEBUG] initialize_search_engine() called", file=sys.stderr, flush=True)
    try:
        with st.spinner(
            "🚀 Loading search engine (matching BM25's 50K indexed jobs)..."
        ):
            print("[DEBUG] Creating HybridJobSearch...", file=sys.stderr, flush=True)
            # IMPORTANT: sample_size=None will auto-match BM25's 50K sample
            # semantic_search.py loads same sample_indices as BM25
            hybrid = HybridJobSearch(
                sample_size=None,  # Will use BM25's 50K sample
                verbose=True,  # Show progress
            )
            print("[DEBUG] Calling hybrid.initialize()...", file=sys.stderr, flush=True)
            hybrid.initialize()
            print("[DEBUG] Initialization complete!", file=sys.stderr, flush=True)
        return hybrid
    except Exception as e:
        print(f"[ERROR] Failed to initialize: {e}", file=sys.stderr, flush=True)
        print(
            f"[ERROR] Traceback: {traceback.format_exc()}", file=sys.stderr, flush=True
        )
        raise


def format_score_badge(score: float) -> str:
    """Format score as colored badge."""
    if score >= 0.7:
        css_class = "score-high"
        label = "High Match"
    elif score >= 0.4:
        css_class = "score-medium"
        label = "Medium Match"
    else:
        css_class = "score-low"
        label = "Low Match"

    return f'<span class="score-badge {css_class}">{label} ({score:.2f})</span>'


def display_job_card(job: pd.Series, rank: int):
    """Display a job posting as a card."""
    # Score badge
    score_html = format_score_badge(job.get("hybrid_score", 0.0))

    # Job card
    st.markdown(
        f"""
    <div class="job-card">
        <div class="job-title">#{rank}. {job['title']}</div>
        <div class="job-company">🏢 {job.get('company_name', 'N/A')}</div>
        <div class="job-location">📍 {job.get('location', 'N/A')}</div>
        <div style="margin-top: 1rem;">
            {score_html}
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Expandable details
    with st.expander("📄 View Details"):
        col1, col2 = st.columns(2)

        with col1:
            st.write("**Work Type:**", job.get("formatted_work_type", "N/A"))
            st.write(
                "**Experience Level:**", job.get("formatted_experience_level", "N/A")
            )
            st.write(
                "**Remote Allowed:**",
                "✅ Yes" if job.get("remote_allowed") else "❌ No",
            )

        with col2:
            st.write("**BM25 Score:**", f"{job.get('bm25_score', 0):.3f}")
            st.write("**Semantic Score:**", f"{job.get('semantic_score', 0):.3f}")
            st.write("**Hybrid Score:**", f"{job.get('hybrid_score', 0):.3f}")

        # Description
        st.write("**Description:**")
        description = job.get("description", "No description available")
        if len(description) > 500:
            description = description[:500] + "..."
        st.write(description)


def main():
    """Main Streamlit app."""
    print("[DEBUG] main() called", file=sys.stderr, flush=True)

    # Header
    try:
        print("[DEBUG] Rendering header...", file=sys.stderr, flush=True)
        st.markdown(
            '<div class="main-header">🔍 Job Search Engine</div>',
            unsafe_allow_html=True,
        )
        st.markdown("---")
        print("[DEBUG] Header rendered", file=sys.stderr, flush=True)
    except Exception as e:
        print(f"[ERROR] Header rendering failed: {e}", file=sys.stderr, flush=True)
        st.error(f"Header error: {e}")

    # Initialize search engine
    try:
        print("[DEBUG] Initializing search engine...", file=sys.stderr, flush=True)
        hybrid = initialize_search_engine()
        print(
            f"[DEBUG] Search engine initialized: {type(hybrid)}",
            file=sys.stderr,
            flush=True,
        )
    except Exception as e:
        print(f"[ERROR] Search engine init failed: {e}", file=sys.stderr, flush=True)
        print(
            f"[ERROR] Traceback: {traceback.format_exc()}", file=sys.stderr, flush=True
        )
        st.error(f"❌ Failed to initialize search engine: {str(e)}")
        st.error(f"Details: {traceback.format_exc()}")
        st.stop()

    # Sidebar - Filters
    print("[DEBUG] Rendering sidebar...", file=sys.stderr, flush=True)
    st.sidebar.header("🎯 Search Filters")

    # Search query
    print("[DEBUG] Rendering search input...", file=sys.stderr, flush=True)
    query = st.text_input(
        "🔎 Search Query",
        placeholder="e.g., Python developer, Data scientist, Product manager",
        help="Enter keywords to search for jobs",
    )
    print(f"[DEBUG] Query: '{query}'", file=sys.stderr, flush=True)

    # Advanced filters
    with st.sidebar.expander("🔧 Advanced Filters", expanded=False):
        location = st.text_input("📍 Location", placeholder="e.g., New York, Remote")

        work_types = st.multiselect(
            "💼 Work Type",
            options=["Full-time", "Part-time", "Contract", "Internship"],
            default=[],
        )

        experience_levels = st.multiselect(
            "📊 Experience Level",
            options=["Entry level", "Mid-Senior level", "Director", "Executive"],
            default=[],
        )

        remote_only = st.checkbox("🏠 Remote Only", value=False)

    # Search settings
    with st.sidebar.expander("⚙️ Search Settings", expanded=False):
        top_k = st.slider(
            "Number of results", min_value=5, max_value=50, value=10, step=5
        )

        st.write("**Score Weights:**")
        bm25_weight = st.slider(
            "BM25 Weight", min_value=0.0, max_value=1.0, value=0.7, step=0.1
        )
        semantic_weight = 1.0 - bm25_weight
        st.write(f"Semantic Weight: {semantic_weight:.1f}")

    # Update weights
    hybrid.bm25_weight = bm25_weight
    hybrid.semantic_weight = semantic_weight

    # Search button
    search_clicked = st.button("🔍 Search", type="primary", use_container_width=True)

    # Perform search
    if search_clicked or query:
        if not query or query.strip() == "":
            st.warning("⚠️ Please enter a search query")
            st.stop()

        # Build filters
        filters = {}
        if location:
            filters["location"] = location
        if work_types:
            filters["work_type"] = work_types
        if experience_levels:
            filters["experience_level"] = experience_levels
        if remote_only:
            filters["remote_allowed"] = True

        # Search
        with st.spinner("🔎 Searching..."):
            start_time = time.time()

            try:
                results = hybrid.search(
                    query=query, top_k=top_k, filters=filters if filters else None
                )

                search_time = time.time() - start_time

            except Exception as e:
                st.error(f"❌ Search failed: {str(e)}")
                st.stop()

        # Display results
        st.markdown("---")

        # Stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📊 Results Found", len(results))
        with col2:
            st.metric("⏱️ Search Time", f"{search_time:.2f}s")
        with col3:
            avg_score = results["hybrid_score"].mean() if len(results) > 0 else 0
            st.metric("📈 Avg Score", f"{avg_score:.2f}")
        with col4:
            st.metric(
                "🎯 BM25/Semantic", f"{int(bm25_weight*100)}/{int(semantic_weight*100)}"
            )

        st.markdown("---")

        # Results
        if len(results) == 0:
            st.warning("😔 No results found. Try different keywords or filters.")
        else:
            st.subheader(f"🎯 Top {len(results)} Results")

            # Display jobs
            for idx, (_, job) in enumerate(results.iterrows(), start=1):
                display_job_card(job, idx)

            # Download results
            st.markdown("---")
            st.download_button(
                label="📥 Download Results (CSV)",
                data=results.to_csv(index=False),
                file_name=f"job_search_{query[:30]}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
            )

    else:
        # Welcome message
        print("[DEBUG] Displaying welcome message...", file=sys.stderr, flush=True)
        st.info(
            """
        👋 **Welcome to the Job Search Engine!**
        
        This system uses **hybrid search** combining:
        - **BM25** (70%): Fast keyword matching
        - **Semantic Search** (30%): Understands synonyms and context
        
        **How to use:**
        1. Enter your search query (e.g., "Python developer")
        2. Optionally add filters (location, work type, etc.)
        3. Click "Search" to find relevant jobs
        
        **Tips:**
        - Use natural language: "machine learning engineer remote"
        - Try synonyms: "developer" and "engineer" work similarly
        - Adjust weights in settings for different search strategies
        """
        )
        print("[DEBUG] Welcome message displayed", file=sys.stderr, flush=True)


if __name__ == "__main__":
    print("[DEBUG] __main__ block executing...", file=sys.stderr, flush=True)
    try:
        main()
        print("[DEBUG] main() completed successfully", file=sys.stderr, flush=True)
    except Exception as e:
        print(
            f"[FATAL ERROR] Unhandled exception in main: {e}",
            file=sys.stderr,
            flush=True,
        )
        print(
            f"[FATAL ERROR] Traceback: {traceback.format_exc()}",
            file=sys.stderr,
            flush=True,
        )
        st.error(f"💥 Fatal error: {e}")
        st.code(traceback.format_exc())
