"""
Streamlit UI for Job Recommendation System
Day 7 Implementation - Enhanced Features
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import time
import json
from datetime import datetime
from typing import Dict, List, Optional
import plotly.express as px
import plotly.graph_objects as go

from src.recommender import JobRecommender

# Page config
st.set_page_config(
    page_title="Job Recommendation System",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown(
    """
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .job-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .job-title {
        font-size: 1.3rem;
        font-weight: bold;
        color: #2c3e50;
        margin-bottom: 0.5rem;
    }
    .job-company {
        font-size: 1.1rem;
        color: #34495e;
        margin-bottom: 0.3rem;
    }
    .job-meta {
        color: #7f8c8d;
        font-size: 0.9rem;
        margin-bottom: 0.5rem;
    }
    .score-badge {
        background-color: #2ecc71;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        font-weight: bold;
        display: inline-block;
        margin-top: 0.5rem;
    }
    .skill-tag {
        background-color: #3498db;
        color: white;
        padding: 0.2rem 0.6rem;
        border-radius: 10px;
        font-size: 0.85rem;
        display: inline-block;
        margin: 0.2rem;
    }
    .stat-box {
        background-color: #ecf0f1;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        margin-bottom: 1rem;
    }
    .stat-number {
        font-size: 2rem;
        font-weight: bold;
        color: #2c3e50;
    }
    .stat-label {
        color: #7f8c8d;
        font-size: 0.9rem;
    }
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_resource
def load_recommender() -> JobRecommender:
    """Load and cache the recommender system."""
    with st.spinner("🔧 Loading recommendation system..."):
        recommender = JobRecommender(auto_load=True)
    return recommender


def log_query(
    query: str, method: str, filters: Dict, num_results: int, search_time: float
):
    """Log search queries for analytics."""
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "query": query,
        "method": method,
        "filters": filters,
        "num_results": num_results,
        "search_time_ms": search_time,
    }

    log_file = logs_dir / "query_history.json"

    # Append to log file
    try:
        if log_file.exists():
            with open(log_file, "r") as f:
                logs = json.load(f)
        else:
            logs = []

        logs.append(log_entry)

        with open(log_file, "w") as f:
            json.dump(logs, f, indent=2)
    except Exception as e:
        st.warning(f"Could not save query log: {e}")


def export_to_csv(results: pd.DataFrame, query: str, method: str, filters: Dict) -> str:
    """Export results to CSV format."""
    export_df = results.copy()

    # Select key columns
    export_cols = [
        "title",
        "company_name_x",
        "location",
        "work_type",
        "experience_level",
        "min_salary",
        "max_salary",
        "similarity_score",
    ]
    available_cols = [col for col in export_cols if col in export_df.columns]

    export_df = export_df[available_cols]

    # Create metadata header
    metadata = f"# Search Query: {query}\n# Method: {method}\n# Filters: {filters}\n# Export Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

    return metadata + export_df.to_csv(index=False)


def export_to_json(
    results: pd.DataFrame, query: str, method: str, filters: Dict, search_time: float
) -> str:
    """Export results to JSON format."""
    export_data = {
        "metadata": {
            "query": query,
            "method": method,
            "filters": filters,
            "export_time": datetime.now().isoformat(),
            "search_time_ms": search_time,
            "num_results": len(results),
        },
        "results": [],
    }

    for idx, (_, job) in enumerate(results.iterrows(), 1):
        job_data = {
            "rank": idx,
            "title": job.get("title", "N/A"),
            "company": job.get("company_name_x", "N/A"),
            "location": job.get("location", "N/A"),
            "work_type": job.get("work_type", "N/A"),
            "experience_level": job.get("experience_level", "N/A"),
            "salary_range": format_salary(job),
            "similarity_score": (
                float(job.get("similarity_score", 0))
                if "similarity_score" in job.index
                else 0
            ),
        }
        export_data["results"].append(job_data)

    return json.dumps(export_data, indent=2)


def create_performance_comparison() -> go.Figure:
    """Create performance comparison chart for 3 methods."""
    methods_data = {
        "Method": ["FAISS", "MiniLM", "TF-IDF"],
        "Speed (ms)": [14.6, 13.3, 49.1],
        "Precision@5 (%)": [93.3, 93.3, 86.7],
    }

    df = pd.DataFrame(methods_data)

    fig = go.Figure()

    # Add speed bars
    fig.add_trace(
        go.Bar(
            name="Speed (ms)",
            x=df["Method"],
            y=df["Speed (ms)"],
            marker_color="#3498db",
            text=df["Speed (ms)"],
            textposition="auto",
            yaxis="y",
        )
    )

    # Add precision line
    fig.add_trace(
        go.Scatter(
            name="Precision@5 (%)",
            x=df["Method"],
            y=df["Precision@5 (%)"],
            mode="lines+markers+text",
            marker_color="#2ecc71",
            line=dict(width=3),
            text=df["Precision@5 (%)"],
            textposition="top center",
            yaxis="y2",
        )
    )

    fig.update_layout(
        title="Method Performance Comparison",
        xaxis=dict(title="Search Method"),
        yaxis=dict(title="Speed (ms)", side="left"),
        yaxis2=dict(
            title="Precision@5 (%)", overlaying="y", side="right", range=[80, 100]
        ),
        legend=dict(x=0.01, y=0.99),
        height=350,
        hovermode="x unified",
    )

    return fig


def format_salary(row: pd.Series) -> str:
    """Format salary information for display."""
    if pd.notna(row.get("min_salary")) and pd.notna(row.get("max_salary")):
        min_sal = f"${row['min_salary']:,.0f}"
        max_sal = f"${row['max_salary']:,.0f}"
        return f"{min_sal} - {max_sal}"
    elif pd.notna(row.get("med_salary")):
        return f"${row['med_salary']:,.0f}"
    return "Not specified"


def display_job_card(
    job: pd.Series, rank: int, matched_skills: Optional[List[str]] = None
):
    """Display a single job result card."""
    with st.container():
        st.markdown(
            f"""
        <div class="job-card">
            <div class="job-title">#{rank}. {job.get('title', 'N/A')}</div>
            <div class="job-company">🏢 {job.get('company_name_x', 'N/A')}</div>
            <div class="job-meta">
                📍 {job.get('location', 'N/A')} | 
                💼 {job.get('work_type', 'N/A')} | 
                💰 {format_salary(job)}
            </div>
        """,
            unsafe_allow_html=True,
        )

        # Display matched skills if available
        if matched_skills and len(matched_skills) > 0:
            st.markdown("<div style='margin-top: 0.5rem;'>", unsafe_allow_html=True)
            st.markdown("**🎯 Matched Skills:**")
            skills_html = "".join(
                [
                    f'<span class="skill-tag">{skill}</span>'
                    for skill in matched_skills[:5]
                ]
            )
            st.markdown(skills_html, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # Similarity score
        if "similarity_score" in job.index:
            score = job["similarity_score"] * 100
            st.markdown(
                f'<span class="score-badge">Match: {score:.1f}%</span>',
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)


def main():
    # Header
    st.markdown(
        '<div class="main-header">💼 Intelligent Job Recommendation System</div>',
        unsafe_allow_html=True,
    )
    st.markdown("---")

    # Load recommender
    try:
        recommender = load_recommender()
        st.success("✅ System ready!")
    except Exception as e:
        st.error(f"❌ Failed to load recommendation system: {str(e)}")
        st.stop()

    # Sidebar - Filters
    st.sidebar.title("🔍 Search & Filters")

    # Query input
    query = st.sidebar.text_area(
        "What job are you looking for?",
        placeholder="e.g., Machine Learning Engineer with Python and TensorFlow",
        height=100,
        help="Describe your ideal job using skills, technologies, or job titles",
    )

    # Search method
    search_method = st.sidebar.selectbox(
        "Search Method",
        ["faiss", "minilm", "tfidf"],
        index=0,
        help="FAISS: Fastest & most accurate | MiniLM: Semantic search | TF-IDF: Keyword matching",
    )

    # Number of results
    top_k = st.sidebar.slider(
        "Number of Results", 5, 20, 10, help="How many job recommendations to show"
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🎛️ Filters")

    # Location filter
    use_location = st.sidebar.checkbox("Filter by Location")
    location = None
    if use_location:
        location = st.sidebar.text_input(
            "Location", placeholder="e.g., New York, San Francisco"
        )

    # Work type filter
    work_type_options = [
        "Full-time",
        "Part-time",
        "Contract",
        "Temporary",
        "Internship",
    ]
    work_type = st.sidebar.multiselect("Work Type", work_type_options)

    # Experience level filter
    experience_options = [
        "Entry level",
        "Mid-Senior level",
        "Associate",
        "Director",
        "Executive",
    ]
    experience = st.sidebar.multiselect("Experience Level", experience_options)

    # Remote filter
    remote_filter = st.sidebar.radio(
        "Remote Work", ["Any", "Remote Only", "On-site Only"], index=0
    )
    remote_allowed = None
    if remote_filter == "Remote Only":
        remote_allowed = True
    elif remote_filter == "On-site Only":
        remote_allowed = False

    # Salary filter
    use_salary = st.sidebar.checkbox("Minimum Salary")
    min_salary = None
    if use_salary:
        min_salary = st.sidebar.number_input(
            "Minimum Salary ($)", min_value=0, max_value=500000, value=50000, step=5000
        )

    # Search button
    search_clicked = st.sidebar.button(
        "🚀 Search Jobs", type="primary", use_container_width=True
    )

    # Performance Comparison (Day 7)
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Performance Metrics")

    show_comparison = st.sidebar.checkbox("Show Method Comparison", value=False)

    if show_comparison:
        st.sidebar.markdown(
            """
        **Average Performance:**
        - 🚀 FAISS: 14.6ms, 93.3% P@5
        - 🧠 MiniLM: 13.3ms, 93.3% P@5  
        - 📝 TF-IDF: 49.1ms, 86.7% P@5
        """
        )

    # Main content area
    col1, col2, col3, col4 = st.columns(4)

    # Dataset statistics
    job_data = recommender.vector_store.job_data

    with col1:
        st.markdown(
            f"""
        <div class="stat-box">
            <div class="stat-number">{len(job_data):,}</div>
            <div class="stat-label">Total Jobs</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        unique_companies = (
            job_data["company_name_x"].nunique()
            if "company_name_x" in job_data.columns
            else 0
        )
        st.markdown(
            f"""
        <div class="stat-box">
            <div class="stat-number">{unique_companies:,}</div>
            <div class="stat-label">Companies</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col3:
        unique_locations = (
            job_data["location"].nunique() if "location" in job_data.columns else 0
        )
        st.markdown(
            f"""
        <div class="stat-box">
            <div class="stat-number">{unique_locations:,}</div>
            <div class="stat-label">Locations</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col4:
        indexed_jobs = (
            len(recommender.vector_store.sample_indices)
            if recommender.vector_store.sample_indices
            else 0
        )
        st.markdown(
            f"""
        <div class="stat-box">
            <div class="stat-number">{indexed_jobs:,}</div>
            <div class="stat-label">Indexed Jobs</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Search results
    if search_clicked and query:
        with st.spinner("🔎 Finding the best matches..."):
            # Build filters dict
            filters = {}
            if location:
                filters["location"] = location
            if work_type:
                filters["work_type"] = (
                    work_type[0] if len(work_type) == 1 else work_type
                )
            if experience:
                filters["experience_level"] = (
                    experience[0] if len(experience) == 1 else experience
                )
            if remote_allowed is not None:
                filters["remote_allowed"] = remote_allowed
            if min_salary:
                filters["min_salary"] = min_salary

            # Get recommendations
            start_time = time.time()
            try:
                results = recommender.get_recommendations(
                    query=query,
                    method=search_method,
                    top_k=top_k,
                    filters=filters if filters else None,
                )
                search_time = (time.time() - start_time) * 1000  # Convert to ms

                # Log query (Day 7)
                log_query(query, search_method, filters, len(results), search_time)

                # Display results
                if len(results) == 0:
                    st.warning(
                        "⚠️ No jobs found matching your criteria. Try adjusting your filters."
                    )
                else:
                    # Success message with export buttons (Day 7)
                    col_msg, col_csv, col_json = st.columns([3, 1, 1])

                    with col_msg:
                        st.success(
                            f"✅ Found {len(results)} jobs in {search_time:.1f}ms"
                        )

                    with col_csv:
                        csv_data = export_to_csv(results, query, search_method, filters)
                        st.download_button(
                            label="📄 CSV",
                            data=csv_data,
                            file_name=f"job_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv",
                            use_container_width=True,
                        )

                    with col_json:
                        json_data = export_to_json(
                            results, query, search_method, filters, search_time
                        )
                        st.download_button(
                            label="📋 JSON",
                            data=json_data,
                            file_name=f"job_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json",
                            use_container_width=True,
                        )

                    # Performance metrics display (Day 7)
                    if show_comparison:
                        st.markdown("### 📊 Performance Analysis")

                        col_chart, col_metrics = st.columns([2, 1])

                        with col_chart:
                            fig = create_performance_comparison()
                            st.plotly_chart(fig, use_container_width=True)

                        with col_metrics:
                            st.metric("Current Search Time", f"{search_time:.1f}ms")
                            st.metric("Results Found", len(results))
                            st.metric("Method Used", search_method.upper())

                            avg_score = (
                                results["similarity_score"].mean() * 100
                                if "similarity_score" in results.columns
                                else 0
                            )
                            st.metric("Avg Relevance", f"{avg_score:.1f}%")

                        st.markdown("---")

                    # Extract matched skills (simple keyword matching)
                    query_keywords = set(query.lower().split())

                    for idx, (_, job) in enumerate(results.iterrows(), 1):
                        # Find matched skills
                        matched_skills = []
                        if "clean_text" in job.index and pd.notna(job["clean_text"]):
                            job_text = job["clean_text"].lower()
                            matched_skills = [
                                kw for kw in query_keywords if kw in job_text
                            ]

                        display_job_card(job, idx, matched_skills)

            except Exception as e:
                st.error(f"❌ Search failed: {str(e)}")

    elif search_clicked and not query:
        st.warning("⚠️ Please enter a job description or keywords to search.")

    else:
        # Welcome message
        st.info(
            """
        👋 **Welcome to the Job Recommendation System!**
        
        This system uses advanced vector search to find jobs that match your skills and preferences.
        
        **How to use:**
        1. Enter your job preferences in the search box (left sidebar)
        2. Choose a search method (FAISS recommended for best results)
        3. Apply filters to narrow down results
        4. Click "Search Jobs" to get recommendations
        
        **Search Methods:**
        - 🚀 **FAISS**: Fastest and most accurate (14.6ms avg)
        - 🧠 **MiniLM**: Semantic understanding (13.3ms avg)
        - 📝 **TF-IDF**: Keyword-based matching (49.1ms avg)
        
        **Example queries:**
        - "Python backend developer with API experience"
        - "Data scientist machine learning deep learning"
        - "DevOps engineer AWS Docker Kubernetes"
        """
        )

        # Show sample jobs
        st.markdown("### 📋 Sample Jobs in Database")
        sample_jobs = job_data.sample(min(5, len(job_data)))
        for idx, (_, job) in enumerate(sample_jobs.iterrows(), 1):
            display_job_card(job, idx)


if __name__ == "__main__":
    main()
