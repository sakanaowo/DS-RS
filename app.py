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
        position: relative;
    }
    .job-card-compact:hover {
        border-color: #2557a7;
        box-shadow: 0 4px 12px rgba(37,87,167,0.15);
        transform: translateY(-2px);
    }
    .job-card-selected {
        border-left: 4px solid #2557a7;
        background: #f8f9ff;
        box-shadow: 0 2px 8px rgba(37,87,167,0.12);
    }
    /* Elegant view button positioned top-right */
    .view-btn-container {
        position: absolute;
        top: 1rem;
        right: 1rem;
        z-index: 10;
    }
    .view-btn-container button {
        background: transparent;
        border: 1px solid #e0e0e0;
        color: #2557a7;
        border-radius: 6px;
        padding: 0.4rem 0.8rem;
        font-size: 0.9rem;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    .view-btn-container button:hover {
        background: #2557a7;
        color: white;
        border-color: #2557a7;
        box-shadow: 0 2px 6px rgba(37,87,167,0.25);
    }
    .view-btn-selected button {
        background: #2557a7;
        color: white;
        border-color: #2557a7;
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
    
    /* Split View - Independent Scrolling */
    .jobs-list-container {
        height: calc(100vh - 250px);
        overflow-y: auto;
        overflow-x: hidden;
        padding-right: 1rem;
    }
    .job-detail-container {
        height: calc(100vh - 250px);
        overflow-y: auto;
        overflow-x: hidden;
        padding-left: 1rem;
        position: sticky;
        top: 0;
    }
    
    /* Custom scrollbar */
    .jobs-list-container::-webkit-scrollbar,
    .job-detail-container::-webkit-scrollbar {
        width: 8px;
    }
    .jobs-list-container::-webkit-scrollbar-track,
    .job-detail-container::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 10px;
    }
    .jobs-list-container::-webkit-scrollbar-thumb,
    .job-detail-container::-webkit-scrollbar-thumb {
        background: #888;
        border-radius: 10px;
    }
    .jobs-list-container::-webkit-scrollbar-thumb:hover,
    .job-detail-container::-webkit-scrollbar-thumb:hover {
        background: #555;
    }
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_resource
def load_recommender() -> JobRecommender:
    """Load and cache the recommender system (50k indexed jobs, ~207 MB)."""
    with st.spinner(
        "🔧 Loading recommendation system... (50k jobs, this may take 5-10 seconds)"
    ):
        recommender = JobRecommender(auto_load=True)
    return recommender


@st.cache_data
def get_top_locations(_recommender: JobRecommender, top_n: int = 50) -> List[str]:
    """Get top N most common locations from job data."""
    job_data = _recommender.vector_store.job_data
    if "location" in job_data.columns:
        # Get top cities
        top_locs = job_data["location"].value_counts().head(top_n).index.tolist()
        return ["Any"] + top_locs
    return ["Any"]


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
    """Create performance comparison chart for TF-IDF."""
    methods_data = {
        "Method": ["TF-IDF"],
        "Speed (ms)": [49.1],
        "Precision@5 (%)": [86.7],
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


# Function removed - using inline card rendering in show_results_page() with clickable cards


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
        st.markdown(
            '<span class="badge badge-remote">🏠 Remote</span>', unsafe_allow_html=True
        )

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
    description = (
        job.get("description") or job.get("clean_text") or "No description available."
    )
    st.markdown(description)

    st.markdown("<br>", unsafe_allow_html=True)

    # Matched skills section
    if matched_skills and len(matched_skills) > 0:
        st.markdown("### 🎯 Your Matched Skills")
        skills_html = "".join(
            [
                f'<span class="badge badge-skill" style="font-size: 1rem; padding: 0.6rem 1rem;">{skill}</span>'
                for skill in matched_skills
            ]
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
            <div class="hero-subtitle">Search 50,000+ indexed jobs from 123K+ total postings</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Search box
    # st.markdown('<div class="search-container">', unsafe_allow_html=True)

    st.markdown("### 🔍 What job are you looking for?")

    # Main search input
    query = st.text_area(
        "Job title, keywords, or skills",
        placeholder="e.g., Python Developer, Data Scientist, Marketing Manager...",
        height=100,
        key="home_query",
        label_visibility="collapsed",
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # Filters in expandable sections
    col1, col2, col3 = st.columns(3)

    # Get top locations
    top_locations = get_top_locations(recommender, top_n=50)

    with col1:
        location = st.selectbox(
            "📍 Location",
            options=top_locations,
            index=0,
        )

    with col2:
        work_type = st.multiselect(
            "💼 Job Type",
            ["Full-time", "Part-time", "Contract", "Temporary", "Internship"],
        )

    with col3:
        experience = st.multiselect(
            "📊 Experience",
            ["Entry level", "Mid-Senior level", "Associate", "Director", "Executive"],
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Advanced filters
    with st.expander("⚙️ Advanced Filters"):
        col_a1, col_a2 = st.columns(2)

        with col_a1:
            remote_filter = st.radio(
                "🏠 Work Location", ["Any", "Remote Only", "On-site Only"], index=0
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
                    step=5000,
                )

    st.markdown("</div>", unsafe_allow_html=True)

    # Search button
    col_search1, col_search2, col_search3 = st.columns([2, 1, 2])
    with col_search2:
        search_clicked = st.button(
            "🔍 Find Jobs", type="primary", use_container_width=True
        )

    # Process search
    if search_clicked and query:
        with st.spinner("🔎 Searching for jobs..."):
            # Build filters
            filters = {}
            if location and location != "Any":
                filters["location"] = location
            if work_type:
                filters["work_type"] = (
                    work_type[0] if len(work_type) == 1 else work_type
                )
            if experience:
                filters["experience_level"] = (
                    experience[0] if len(experience) == 1 else experience
                )
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
                    top_k=20,
                    filters=filters if filters else None,
                )
                search_time = (time.time() - start_time) * 1000

                # Log query
                log_query(query, "tfidf", filters, len(results), search_time)

                # Save to session state
                st.session_state.search_results = results
                st.session_state.search_params = {
                    "query": query,
                    "method": "tfidf",
                    "filters": filters,
                    "search_time": search_time,
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
                <div class="stat-label">Total Dataset</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_stat2:
        # Show indexed count
        indexed_count = (
            len(recommender.vector_store.sample_indices)
            if recommender.vector_store.sample_indices
            else 50000
        )
        st.markdown(
            f"""
            <div class="stat-box">
                <div class="stat-number">{indexed_count:,}</div>
                <div class="stat-label">Searchable Jobs</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_stat3:
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

    with col_stat4:
        unique_locations = (
            job_data["location"].nunique() if "location" in job_data.columns else 0
        )
        st.markdown(
            f"""
            <div class="stat-box">
                <div class="stat-number">{unique_locations:,}</div>
                <div class="stat-label">US Locations</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # EDA Insights Section
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("### 📈 Market Insights")

    # Top Industries & Skills
    col_ins1, col_ins2 = st.columns(2)

    with col_ins1:
        st.markdown("#### 🏢 Top Industries")
        if "industries" in job_data.columns:
            # Parse industries (comma-separated)
            all_industries = []
            for ind_str in job_data["industries"].dropna():
                if isinstance(ind_str, str):
                    all_industries.extend([i.strip() for i in ind_str.split(",")])

            if all_industries:
                from collections import Counter

                top_industries = Counter(all_industries).most_common(5)
                for idx, (industry, count) in enumerate(top_industries, 1):
                    pct = (count / len(job_data)) * 100
                    st.markdown(f"**{idx}.** {industry} — {count:,} jobs ({pct:.1f}%)")
        else:
            st.info("Industry data not available")

    with col_ins2:
        st.markdown("#### 💡 Top Skills")
        if "skills" in job_data.columns:
            # Parse skills (comma-separated)
            all_skills = []
            for skill_str in job_data["skills"].dropna():
                if isinstance(skill_str, str):
                    all_skills.extend([s.strip() for s in skill_str.split(",")])

            if all_skills:
                from collections import Counter

                top_skills = Counter(all_skills).most_common(5)
                for idx, (skill, count) in enumerate(top_skills, 1):
                    pct = (count / len(job_data)) * 100
                    st.markdown(f"**{idx}.** {skill} — {count:,} jobs ({pct:.1f}%)")
        else:
            st.info("Skills data not available")

    # Salary & Work Type Distribution
    st.markdown("<br>", unsafe_allow_html=True)
    col_ins3, col_ins4 = st.columns(2)

    with col_ins3:
        st.markdown("#### 💰 Salary Insights")
        if "salary_median" in job_data.columns:
            salary_data = job_data["salary_median"].dropna()
            if len(salary_data) > 0:
                avg_salary = salary_data.mean()
                median_salary = salary_data.median()
                st.markdown(f"**Average:** ${avg_salary:,.0f}/year")
                st.markdown(f"**Median:** ${median_salary:,.0f}/year")
                st.markdown(
                    f"**Range:** ${salary_data.min():,.0f} - ${salary_data.max():,.0f}"
                )
            else:
                st.info("Salary data limited")
        else:
            st.info("Salary data not available")

    with col_ins4:
        st.markdown("#### 🔄 Work Type Distribution")
        if "formatted_work_type" in job_data.columns:
            work_type_counts = job_data["formatted_work_type"].value_counts().head(4)
            for work_type, count in work_type_counts.items():
                pct = (count / len(job_data)) * 100
                st.markdown(f"**{work_type}:** {count:,} ({pct:.1f}%)")
        else:
            st.info("Work type data not available")


def show_results_page():
    """Results page - Job listings (Indeed style split view)."""
    results = st.session_state.search_results
    params = st.session_state.search_params

    if results is None or len(results) == 0:
        st.warning("No results found. Please try a different search.")
        if st.button("← Back to Home"):
            st.session_state.page = "home"
            st.rerun()
        return

    # Initialize selected job (first job by default)
    if "selected_job_idx" not in st.session_state:
        st.session_state.selected_job_idx = 0

    # Header with back button and stats
    col_back, col_stats, col_export = st.columns([1, 3, 1])

    with col_back:
        if st.button("← New Search", key="back_home"):
            st.session_state.page = "home"
            st.rerun()

    with col_stats:
        st.markdown(
            f"""
            <div style="padding: 0.5rem; background: white; border-radius: 6px;">
                <strong>🔍 "{params.get('query', '')}"</strong> • 
                <strong>{len(results)}</strong> jobs
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_export:
        with st.popover("📥 Export"):
            csv_data = export_to_csv(
                results, params["query"], params["method"], params.get("filters", {})
            )
            st.download_button(
                label="📄 CSV",
                data=csv_data,
                file_name=f"jobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True,
            )
            json_data = export_to_json(
                results,
                params["query"],
                params["method"],
                params.get("filters", {}),
                params["search_time"],
            )
            st.download_button(
                label="📋 JSON",
                data=json_data,
                file_name=f"jobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # Split view: Jobs list (left) + Job detail (right)
    col_list, col_detail = st.columns([1.8, 3.2], gap="medium")

    query_keywords = set(params["query"].lower().split())

    with col_list:
        st.markdown(f"### {len(results)} jobs")

        # Container with larger height for scrolling
        list_container = st.container(height=750, border=False)

        with list_container:
            # Job cards list - styled like Indeed with adaptive fields
            for idx, (_, job) in enumerate(results.iterrows()):
                # Card styling based on selection
                is_selected = idx == st.session_state.selected_job_idx

                # Clean and validate fields
                def clean_field(value):
                    """Clean field value, return None if invalid"""
                    if pd.isna(value) or value is None:
                        return None
                    str_value = str(value).strip()
                    if str_value.lower() in ["nan", "none", "n/a", ""]:
                        return None
                    return str_value

                # Extract and clean fields
                title = clean_field(job.get("title")) or "Untitled Position"
                company = clean_field(job.get("company_name_x")) or "Company"
                location = clean_field(job.get("location")) or "Location not specified"

                # Build salary info
                salary_info = None
                if pd.notna(job.get("salary_median")):
                    try:
                        salary_info = f"${float(job['salary_median']):,.0f}"
                    except:
                        pass
                elif pd.notna(job.get("min_salary")) and pd.notna(
                    job.get("max_salary")
                ):
                    try:
                        salary_info = f"${float(job['min_salary']):,.0f} - ${float(job['max_salary']):,.0f}"
                    except:
                        pass

                # Build metadata
                work_type = clean_field(job.get("work_type")) or clean_field(
                    job.get("formatted_work_type")
                )
                experience = clean_field(job.get("formatted_experience_level"))

                # Metadata line
                metadata_parts = []
                if work_type:
                    metadata_parts.append(work_type)
                if experience:
                    metadata_parts.append(experience)

                # Card container with columns: content + button
                card_col, btn_col = st.columns([6, 1])

                with card_col:
                    # Card styling classes
                    card_class = (
                        "job-card-compact job-card-selected"
                        if is_selected
                        else "job-card-compact"
                    )

                    # Build HTML for card content
                    html_parts = []
                    html_parts.append(
                        f'<div class="{card_class}" style="margin-bottom: 0;">'
                    )

                    # Title
                    html_parts.append(
                        f'<div style="font-size: 1.05rem; font-weight: 600; color: #2557a7; margin-bottom: 0.4rem; line-height: 1.3;">{title}</div>'
                    )

                    # Company
                    html_parts.append(
                        f'<div style="font-size: 0.9rem; color: #2d2d2d; margin-bottom: 0.3rem;">{company}</div>'
                    )

                    # Location
                    html_parts.append(
                        f'<div style="font-size: 0.85rem; color: #666; margin-bottom: 0.3rem;">📍 {location}</div>'
                    )

                    # Salary (optional)
                    if salary_info:
                        html_parts.append(
                            f'<div style="font-size: 0.85rem; color: #2d7738; font-weight: 600; margin-bottom: 0.3rem;">💰 {salary_info}</div>'
                        )

                    # Metadata (optional)
                    if metadata_parts:
                        metadata_text = " • ".join(metadata_parts)
                        html_parts.append(
                            f'<div style="font-size: 0.8rem; color: #888;">{metadata_text}</div>'
                        )

                    # Selection indicator
                    if is_selected:
                        html_parts.append(
                            '<div style="margin-top: 0.5rem; font-size: 0.75rem; color: #2557a7; font-weight: 600;">👁️ Viewing</div>'
                        )

                    html_parts.append("</div>")

                    # Render card content
                    st.markdown("".join(html_parts), unsafe_allow_html=True)

                with btn_col:
                    # Elegant button aligned to center
                    st.markdown(
                        '<div style="display: flex; align-items: center; height: 100%; padding-top: 1.5rem;">',
                        unsafe_allow_html=True,
                    )
                    if st.button(
                        "→",
                        key=f"job_{idx}",
                        help=f"View {title}",
                        disabled=is_selected,
                        use_container_width=True,
                    ):
                        st.session_state.selected_job_idx = idx
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)

    with col_detail:
        # Container with larger height for scrolling
        detail_container = st.container(height=750, border=False)

        with detail_container:
            # Display selected job detail
            selected_job = results.iloc[st.session_state.selected_job_idx]

            # Job title and company
            st.markdown(f"## {selected_job.get('title', 'N/A')}")

            # Company with rating
            company_name = selected_job.get("company_name_x", "N/A")
            st.markdown(f"### {company_name} ⭐ 4.1")

            # Location
            st.markdown(f"📍 {selected_job.get('location', 'N/A')}")

            st.markdown("<br>", unsafe_allow_html=True)

            # Action buttons
            col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)
            with col_btn1:
                st.button(
                    "💼 Apply",
                    type="primary",
                    use_container_width=True,
                    key="apply_btn",
                )
            with col_btn2:
                st.button("💾 Save", use_container_width=True, key="save_btn")
            with col_btn3:
                st.button(
                    "🚫 Not interested",
                    use_container_width=True,
                    key="not_interested_btn",
                )
            with col_btn4:
                st.button("🔗 Share", use_container_width=True, key="share_btn")

            st.markdown("<br>", unsafe_allow_html=True)

            # Job details
            st.markdown("### Full job description")

            # Work type and experience
            col_info1, col_info2 = st.columns(2)
            with col_info1:
                work_type = selected_job.get(
                    "work_type", selected_job.get("formatted_work_type", "N/A")
                )
                st.markdown(f"**Work Type:** {work_type}")
            with col_info2:
                experience = selected_job.get("formatted_experience_level", "N/A")
                st.markdown(f"**Experience:** {experience}")

            # Salary
            if pd.notna(selected_job.get("salary_median")):
                st.markdown(f"**💰 Salary:** ${selected_job['salary_median']:,.0f}")

            # Remote
            if pd.notna(selected_job.get("remote_allowed")):
                remote = (
                    "✅ Remote allowed"
                    if selected_job["remote_allowed"]
                    else "🏢 On-site"
                )
                st.markdown(f"**{remote}**")

            st.markdown("---")

            # Description
            if pd.notna(selected_job.get("description")):
                st.markdown("#### Description")
                st.write(
                    selected_job["description"][:1000] + "..."
                    if len(str(selected_job["description"])) > 1000
                    else selected_job["description"]
                )

            # Skills
            if pd.notna(selected_job.get("skills")):
                st.markdown("#### Required Skills")
                skills = str(selected_job["skills"]).split(",")[:10]
                for skill in skills:
                    st.markdown(f"• {skill.strip()}")

            # Industries
            if pd.notna(selected_job.get("industries")):
                st.markdown("#### Industries")
                industries = str(selected_job["industries"]).split(",")[:5]
                for industry in industries:
                    st.markdown(f"• {industry.strip()}")


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


if __name__ == "__main__":
    main()
