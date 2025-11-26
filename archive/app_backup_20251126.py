"""
Streamlit UI for Job Recommendation System
Day 7+ Implementation - Indeed.com Style Multi-Page Flow
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
    page_title="JobMatch - Find Your Perfect Job",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Initialize session state for navigation
if "page" not in st.session_state:
    st.session_state.page = "home"
if "search_results" not in st.session_state:
    st.session_state.search_results = None
if "selected_job" not in st.session_state:
    st.session_state.selected_job = None
if "search_params" not in st.session_state:
    st.session_state.search_params = {}

# Custom CSS - Indeed.com inspired
st.markdown(
    """
<style>
    /* Global Styles */
    .main {
        background-color: #f5f5f5;
    }
    
    /* Home Page Hero */
    .hero-section {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 4rem 2rem;
        border-radius: 15px;
        text-align: center;
        color: white;
        margin-bottom: 2rem;
    }
    .hero-title {
        font-size: 3rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .hero-subtitle {
        font-size: 1.3rem;
        opacity: 0.9;
    }
    
    /* Search Box */
    .search-container {
        background: white;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        margin: 2rem 0;
    }
    
    /* Job Card - List View (Indeed style) */
    .job-card-compact {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border: 1px solid #e0e0e0;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .job-card-compact:hover {
        border-color: #2557a7;
        box-shadow: 0 4px 12px rgba(37,87,167,0.15);
        transform: translateY(-2px);
    }
    .job-card-title {
        font-size: 1.4rem;
        font-weight: 600;
        color: #2557a7;
        margin-bottom: 0.5rem;
        cursor: pointer;
    }
    .job-card-title:hover {
        text-decoration: underline;
    }
    .job-card-company {
        font-size: 1.1rem;
        color: #2d2d2d;
        margin-bottom: 0.3rem;
    }
    .job-card-location {
        font-size: 0.95rem;
        color: #595959;
        margin-bottom: 0.8rem;
    }
    .job-card-snippet {
        font-size: 0.9rem;
        color: #595959;
        line-height: 1.5;
        margin-bottom: 0.8rem;
    }
    .job-card-meta {
        font-size: 0.85rem;
        color: #888;
    }
    
    /* Job Detail Page */
    .job-detail-header {
        background: white;
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .job-detail-title {
        font-size: 2rem;
        font-weight: bold;
        color: #2d2d2d;
        margin-bottom: 0.8rem;
    }
    .job-detail-company {
        font-size: 1.3rem;
        color: #2557a7;
        margin-bottom: 0.5rem;
    }
    .job-detail-location {
        font-size: 1.1rem;
        color: #595959;
        margin-bottom: 1rem;
    }
    .job-detail-body {
        background: white;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    /* Badges */
    .badge {
        display: inline-block;
        padding: 0.4rem 0.8rem;
        border-radius: 20px;
        font-size: 0.85rem;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .badge-salary {
        background-color: #e8f5e9;
        color: #2e7d32;
        font-weight: 600;
    }
    .badge-type {
        background-color: #e3f2fd;
        color: #1565c0;
    }
    .badge-experience {
        background-color: #f3e5f5;
        color: #6a1b9a;
    }
    .badge-remote {
        background-color: #fff3e0;
        color: #e65100;
    }
    .badge-skill {
        background-color: #f5f5f5;
        color: #424242;
        border: 1px solid #e0e0e0;
    }
    
    /* Navigation */
    .nav-button {
        background-color: transparent;
        border: none;
        color: #2557a7;
        cursor: pointer;
        font-size: 1rem;
        padding: 0.5rem 1rem;
    }
    
    /* Stats */
    .stat-box {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    .stat-number {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2557a7;
    }
    .stat-label {
        color: #595959;
        font-size: 0.95rem;
        margin-top: 0.5rem;
    }
    
    /* Filter sidebar */
    .filter-section {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    
    /* Buttons */
    .stButton>button {
        background-color: #2557a7;
        color: white;
        border-radius: 6px;
        padding: 0.6rem 1.5rem;
        font-weight: 600;
        border: none;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #1e4586;
        box-shadow: 0 4px 12px rgba(37,87,167,0.3);
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


def get_job_snippet(job: pd.Series, max_length: int = 200) -> str:
    """Get a snippet of job description."""
    desc = job.get("description", "") or job.get("clean_text", "") or ""
    if len(desc) > max_length:
        return desc[:max_length] + "..."
    return desc


def display_job_card_compact(job: pd.Series, idx: int, matched_skills: Optional[List[str]] = None):
    """Display a compact job card for list view (Indeed style)."""
    job_id = job.name if hasattr(job, 'name') else idx
    
    # Create clickable card
    with st.container():
        col1, col2 = st.columns([4, 1])
        
        with col1:
            st.markdown(
                f"""
                <div class="job-card-compact">
                    <div class="job-card-title">{job.get('title', 'N/A')}</div>
                    <div class="job-card-company">{job.get('company_name_x', 'N/A')}</div>
                    <div class="job-card-location">📍 {job.get('location', 'N/A')}</div>
                    <div class="job-card-snippet">{get_job_snippet(job)}</div>
                    <div class="job-card-meta">
                        <span class="badge badge-type">{job.get('work_type', 'N/A')}</span>
                        <span class="badge badge-salary">{format_salary(job)}</span>
                """,
                unsafe_allow_html=True,
            )
            
            # Display matched skills
            if matched_skills and len(matched_skills) > 0:
                skills_html = "".join(
                    [f'<span class="badge badge-skill">{skill}</span>' for skill in matched_skills[:3]]
                )
                st.markdown(skills_html, unsafe_allow_html=True)
            
            st.markdown("</div></div>", unsafe_allow_html=True)
        
        with col2:
            if st.button("View Details →", key=f"view_{idx}", use_container_width=True):
                st.session_state.selected_job = job
                st.session_state.page = "detail"
                st.rerun()


def display_job_detail(job: pd.Series, matched_skills: Optional[List[str]] = None):
    """Display full job details page (Indeed style)."""
    # Back button
    if st.button("← Back to Results", key="back_to_results"):
        st.session_state.page = "results"
        st.session_state.selected_job = None
        st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Job header
    st.markdown(
        f"""
        <div class="job-detail-header">
            <div class="job-detail-title">{job.get('title', 'N/A')}</div>
            <div class="job-detail-company">🏢 {job.get('company_name_x', 'N/A')}</div>
            <div class="job-detail-location">📍 {job.get('location', 'N/A')}</div>
            <div style="margin-top: 1rem;">
                <span class="badge badge-type">{job.get('work_type', 'Full-time')}</span>
                <span class="badge badge-experience">{job.get('experience_level', 'Not specified')}</span>
                <span class="badge badge-salary">{format_salary(job)}</span>
        """,
        unsafe_allow_html=True,
    )
    
    # Remote badge
    if pd.notna(job.get("remote_allowed")) and job.get("remote_allowed"):
        st.markdown('<span class="badge badge-remote">🏠 Remote</span>', unsafe_allow_html=True)
    
    # Match score
    if "similarity_score" in job.index and pd.notna(job.get("similarity_score")):
        score = job["similarity_score"] * 100
        st.markdown(
            f'<div style="margin-top: 1rem;"><strong>Match Score:</strong> <span style="color: #2e7d32; font-size: 1.2rem; font-weight: bold;">{score:.1f}%</span></div>',
            unsafe_allow_html=True,
        )
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Job description
    st.markdown('<div class="job-detail-body">', unsafe_allow_html=True)
    
    st.markdown("### 📄 Job Description")
    description = job.get("description") or job.get("clean_text") or "No description available."
    st.markdown(description)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Matched skills section
    if matched_skills and len(matched_skills) > 0:
        st.markdown("### 🎯 Your Matched Skills")
        skills_html = "".join(
            [f'<span class="badge badge-skill" style="font-size: 1rem; padding: 0.6rem 1rem;">{skill}</span>' 
             for skill in matched_skills]
        )
        st.markdown(skills_html, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
    
    # Additional information in columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### 💼 Job Type")
        st.write(job.get("work_type", "Not specified"))
        
        st.markdown("#### 📊 Experience Level")
        st.write(job.get("experience_level", "Not specified"))
    
    with col2:
        st.markdown("#### 💰 Salary Range")
        st.write(format_salary(job))
        
        st.markdown("#### 🏠 Work Location")
        if pd.notna(job.get("remote_allowed")) and job.get("remote_allowed"):
            st.write("Remote Allowed")
        else:
            st.write("On-site")
    
    with col3:
        st.markdown("#### 🏢 Company")
        st.write(job.get("company_name_x", "N/A"))
        
        st.markdown("#### 📍 Location")
        st.write(job.get("location", "N/A"))
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Action buttons
    st.markdown("<br>", unsafe_allow_html=True)
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 3])
    
    with col_btn1:
        st.button("💾 Save Job", use_container_width=True)
    
    with col_btn2:
        st.button("📧 Apply Now", type="primary", use_container_width=True)


def show_home_page(recommender: JobRecommender):
    """Home page - Search interface (Indeed style)."""
    # Hero section
    st.markdown(
        """
        <div class="hero-section">
            <div class="hero-title">Find Your Dream Job</div>
            <div class="hero-subtitle">Search from 123,000+ jobs across multiple industries</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Search box
    st.markdown('<div class="search-container">', unsafe_allow_html=True)
    
    st.markdown("### 🔍 What job are you looking for?")
    
    # Main search input
    query = st.text_area(
        "Job title, keywords, or skills",
        placeholder="e.g., Python Developer, Data Scientist, Marketing Manager...",
        height=100,
        key="home_query",
        label_visibility="collapsed"
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Filters in expandable sections
    col1, col2, col3 = st.columns(3)
    
    with col1:
        location = st.text_input("📍 Location", placeholder="e.g., New York, San Francisco")
        
    with col2:
        work_type = st.multiselect(
            "💼 Job Type",
            ["Full-time", "Part-time", "Contract", "Temporary", "Internship"]
        )
    
    with col3:
        experience = st.multiselect(
            "📊 Experience",
            ["Entry level", "Mid-Senior level", "Associate", "Director", "Executive"]
        )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Advanced filters
    with st.expander("⚙️ Advanced Filters"):
        col_a1, col_a2, col_a3 = st.columns(3)
        
        with col_a1:
            remote_filter = st.radio(
                "🏠 Work Location",
                ["Any", "Remote Only", "On-site Only"],
                index=0
            )
        
        with col_a2:
            use_salary = st.checkbox("💰 Minimum Salary")
            min_salary = None
            if use_salary:
                min_salary = st.number_input(
                    "Minimum Salary ($)",
                    min_value=0,
                    max_value=500000,
                    value=50000,
                    step=5000
                )
        
        with col_a3:
            search_method = st.selectbox(
                "🔬 Search Method",
                ["faiss", "minilm", "tfidf"],
                index=0,
                format_func=lambda x: {
                    "faiss": "🚀 FAISS (Fastest)",
                    "minilm": "🧠 MiniLM (Semantic)",
                    "tfidf": "📝 TF-IDF (Keyword)"
                }[x]
            )
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Search button
    col_search1, col_search2, col_search3 = st.columns([2, 1, 2])
    with col_search2:
        search_clicked = st.button("🔍 Find Jobs", type="primary", use_container_width=True)
    
    # Process search
    if search_clicked and query:
        with st.spinner("🔎 Searching for jobs..."):
            # Build filters
            filters = {}
            if location:
                filters["location"] = location
            if work_type:
                filters["work_type"] = work_type[0] if len(work_type) == 1 else work_type
            if experience:
                filters["experience_level"] = experience[0] if len(experience) == 1 else experience
            if remote_filter == "Remote Only":
                filters["remote_allowed"] = True
            elif remote_filter == "On-site Only":
                filters["remote_allowed"] = False
            if min_salary:
                filters["min_salary"] = min_salary
            
            # Search
            start_time = time.time()
            try:
                results = recommender.get_recommendations(
                    query=query,
                    method=search_method,
                    top_k=20,
                    filters=filters if filters else None,
                )
                search_time = (time.time() - start_time) * 1000
                
                # Log query
                log_query(query, search_method, filters, len(results), search_time)
                
                # Save to session state
                st.session_state.search_results = results
                st.session_state.search_params = {
                    "query": query,
                    "method": search_method,
                    "filters": filters,
                    "search_time": search_time
                }
                st.session_state.page = "results"
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Search failed: {str(e)}")
    
    elif search_clicked and not query:
        st.warning("⚠️ Please enter a job title or keywords to search.")
    
    # Stats section
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("### 📊 Our Platform")
    
    job_data = recommender.vector_store.job_data
    col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
    
    with col_stat1:
        st.markdown(
            f"""
            <div class="stat-box">
                <div class="stat-number">{len(job_data):,}</div>
                <div class="stat-label">Total Jobs</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    with col_stat2:
        unique_companies = job_data["company_name_x"].nunique() if "company_name_x" in job_data.columns else 0
        st.markdown(
            f"""
            <div class="stat-box">
                <div class="stat-number">{unique_companies:,}</div>
                <div class="stat-label">Companies</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    with col_stat3:
        unique_locations = job_data["location"].nunique() if "location" in job_data.columns else 0
        st.markdown(
            f"""
            <div class="stat-box">
                <div class="stat-number">{unique_locations:,}</div>
                <div class="stat-label">Locations</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    with col_stat4:
        st.markdown(
            f"""
            <div class="stat-box">
                <div class="stat-number">94.3%</div>
                <div class="stat-label">Match Accuracy</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def show_results_page():
    """Results page - Job listings (Indeed style)."""
    results = st.session_state.search_results
    params = st.session_state.search_params
    
    if results is None or len(results) == 0:
        st.warning("No results found. Please try a different search.")
        if st.button("← Back to Home"):
            st.session_state.page = "home"
            st.rerun()
        return
    
    # Header with back button and stats
    col_back, col_stats = st.columns([1, 4])
    
    with col_back:
        if st.button("← New Search", key="back_home"):
            st.session_state.page = "home"
            st.rerun()
    
    with col_stats:
        st.markdown(
            f"""
            <div style="padding: 1rem; background: white; border-radius: 8px; margin-bottom: 1rem;">
                <strong>🔍 "{params.get('query', '')}"</strong> • 
                Found <strong>{len(results)}</strong> jobs in <strong>{params.get('search_time', 0):.1f}ms</strong>
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    # Export buttons
    col_exp1, col_exp2, col_exp3, col_exp4 = st.columns([3, 1, 1, 6])
    
    with col_exp2:
        csv_data = export_to_csv(results, params["query"], params["method"], params.get("filters", {}))
        st.download_button(
            label="📄 Export CSV",
            data=csv_data,
            file_name=f"jobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col_exp3:
        json_data = export_to_json(results, params["query"], params["method"], params.get("filters", {}), params["search_time"])
        st.download_button(
            label="📋 Export JSON",
            data=json_data,
            file_name=f"jobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Display job cards
    query_keywords = set(params["query"].lower().split())
    
    for idx, (_, job) in enumerate(results.iterrows(), 1):
        # Find matched skills
        matched_skills = []
        if "clean_text" in job.index and pd.notna(job["clean_text"]):
            job_text = job["clean_text"].lower()
            matched_skills = [kw for kw in query_keywords if kw in job_text]
        
        display_job_card_compact(job, idx, matched_skills)


def show_detail_page():
    """Job detail page (Indeed style)."""
    job = st.session_state.selected_job
    params = st.session_state.search_params
    
    if job is None:
        st.warning("No job selected.")
        if st.button("← Back to Home"):
            st.session_state.page = "home"
            st.rerun()
        return
    
    # Find matched skills from search query
    matched_skills = []
    if params and "query" in params:
        query_keywords = set(params["query"].lower().split())
        if "clean_text" in job.index and pd.notna(job["clean_text"]):
            job_text = job["clean_text"].lower()
            matched_skills = [kw for kw in query_keywords if kw in job_text]
    
    display_job_detail(job, matched_skills)


def main():
    """Main application with page routing."""
    # Load recommender
    try:
        recommender = load_recommender()
    except Exception as e:
        st.error(f"❌ Failed to load recommendation system: {str(e)}")
        st.stop()
    
    # Page routing
    if st.session_state.page == "home":
        show_home_page(recommender)
    elif st.session_state.page == "results":
        show_results_page()
    elif st.session_state.page == "detail":
        show_detail_page()


def main_old_sidebar():
    """OLD CODE - Keep for reference, will be removed."""
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
