"""
BM25 Search Engine for Job Recommendation System

Day 2 Implementation - BM25 with Pre-filtering

Features:
- BM25 algorithm with field weights (Title^3, Skills^2, Description^1)
- Pre-filtering with normalized tables (100% accurate)
- Query parsing and tokenization
- Fast search (<100ms target)
- Handles missing salary data gracefully
"""

from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple
import time

import pandas as pd
import numpy as np
from rank_bm25 import BM25Okapi

from .loader import (
    load_normalized_tables,
    JOBS_PARQUET,
    JOB_SKILLS_PARQUET,
    SKILLS_PARQUET,
    JOB_INDUSTRIES_PARQUET,
    INDUSTRIES_PARQUET,
)


class BM25JobSearch:
    """
    BM25-based job search engine with pre-filtering.

    Architecture:
    1. Load normalized tables (jobs, job_skills, skills, etc.)
    2. Build BM25 indexes for each field (title, skills, description)
    3. Apply filters BEFORE search (pre-filtering)
    4. Search with weighted BM25 scores
    5. Return ranked results

    Field Weights:
    - Title: 3x (most important)
    - Skills: 2x (second most important)
    - Description: 1x (base weight)
    """

    def __init__(self, verbose: bool = True, sample_size: Optional[int] = None):
        """
        Initialize BM25 search engine.

        Args:
            verbose: If True, print loading progress
            sample_size: If set, use only this many jobs (for testing/development)
        """
        self.verbose = verbose
        self.sample_size = sample_size
        self.jobs = None
        self.job_skills = None
        self.skills = None
        self.job_industries = None
        self.industries = None

        # BM25 indexes
        self.bm25_title = None
        self.bm25_skills = None
        self.bm25_description = None

        # Mappings
        self.job_id_to_idx = {}  # job_id → index in jobs DataFrame
        self.idx_to_job_id = {}  # index → job_id

        # Precomputed data
        self.job_skills_dict = {}  # job_id → list of skill_abr
        self.job_industries_dict = {}  # job_id → list of industry_id

    def load_data(self):
        """Load normalized tables and build indexes."""
        if self.verbose:
            print("=" * 60)
            print("LOADING DATA FOR BM25 SEARCH")
            print("=" * 60)

        start_time = time.time()

        # Load normalized tables
        if self.verbose:
            print("Loading normalized tables...")

        tables = load_normalized_tables()
        self.jobs = tables["jobs"]
        self.job_skills = tables["job_skills"]
        self.skills = tables["skills"]
        self.job_industries = tables["job_industries"]
        self.industries = tables["industries"]

        # Apply sampling if specified (for testing/development)
        if self.sample_size is not None and self.sample_size < len(self.jobs):
            if self.verbose:
                print(
                    f"\n⚠️  SAMPLING: Using {self.sample_size:,} jobs (out of {len(self.jobs):,})"
                )

            # Sample jobs
            self.jobs = self.jobs.head(self.sample_size).copy()
            sampled_job_ids = set(self.jobs["job_id"])

            # Filter related tables
            self.job_skills = self.job_skills[
                self.job_skills["job_id"].isin(sampled_job_ids)
            ]
            self.job_industries = self.job_industries[
                self.job_industries["job_id"].isin(sampled_job_ids)
            ]

        if self.verbose:
            print(f"  ✓ Jobs: {len(self.jobs):,}")
            print(f"  ✓ Job-Skills: {len(self.job_skills):,}")
            print(f"  ✓ Skills: {len(self.skills):,}")
            print(f"  ✓ Job-Industries: {len(self.job_industries):,}")
            print(f"  ✓ Industries: {len(self.industries):,}")

        # Build mappings
        if self.verbose:
            print("\nBuilding index mappings...")

        self.job_id_to_idx = {
            job_id: idx for idx, job_id in enumerate(self.jobs["job_id"])
        }
        self.idx_to_job_id = {idx: job_id for job_id, idx in self.job_id_to_idx.items()}

        # Precompute job-skills mapping
        if self.verbose:
            print("Precomputing job-skills mapping...")

        self.job_skills_dict = (
            self.job_skills.groupby("job_id")["skill_abr"].apply(list).to_dict()
        )

        # Precompute job-industries mapping
        if self.verbose:
            print("Precomputing job-industries mapping...")

        self.job_industries_dict = (
            self.job_industries.groupby("job_id")["industry_id"].apply(list).to_dict()
        )

        # Build BM25 indexes
        if self.verbose:
            print("\nBuilding BM25 indexes...")

        self._build_bm25_indexes()

        elapsed = time.time() - start_time

        if self.verbose:
            print(f"\n✓ Data loaded in {elapsed:.2f}s")
            print("=" * 60)

    def _tokenize(self, text: str) -> List[str]:
        """
        Simple tokenization: lowercase + split by whitespace.

        Args:
            text: Input text

        Returns:
            List of tokens
        """
        if pd.isna(text) or not isinstance(text, str):
            return []

        # Lowercase and split
        tokens = text.lower().split()

        # Remove very short tokens (< 2 chars)
        tokens = [t for t in tokens if len(t) >= 2]

        return tokens

    def _build_bm25_indexes(self):
        """Build BM25 indexes for title, skills, description."""
        # Prepare skill name lookup
        skill_map = self.skills.set_index("skill_abr")["skill_name"].to_dict()

        # Build documents for each field
        if self.verbose:
            print("  Building title index...")

        title_docs = [self._tokenize(title) for title in self.jobs["title"]]
        self.bm25_title = BM25Okapi(title_docs)

        if self.verbose:
            print("  Building skills index...")

        # Skills: convert skill abbreviations to skill names
        skills_docs = []
        for job_id in self.jobs["job_id"]:
            skill_abrs = self.job_skills_dict.get(job_id, [])
            skill_names = [skill_map.get(abr, "") for abr in skill_abrs]
            skill_text = " ".join(skill_names)
            skills_docs.append(self._tokenize(skill_text))

        self.bm25_skills = BM25Okapi(skills_docs)

        if self.verbose:
            print("  Building description index...")

        description_docs = [self._tokenize(desc) for desc in self.jobs["description"]]
        self.bm25_description = BM25Okapi(description_docs)

        if self.verbose:
            print("  ✓ All indexes built")

    def apply_filters(
        self,
        skills: Optional[List[str]] = None,
        location: Optional[str] = None,
        work_type: Optional[str] = None,
        experience_level: Optional[str] = None,
        remote_allowed: Optional[bool] = None,
        salary_min: Optional[float] = None,
        salary_max: Optional[float] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        country: Optional[str] = None,
    ) -> Set[int]:
        """
        Apply filters to get candidate job_ids BEFORE search (pre-filtering).

        This is the key improvement over old system:
        - Filters applied BEFORE search (not after)
        - Uses normalized tables with JOINs (100% accurate)
        - Returns set of valid job_ids

        Args:
            skills: List of required skill abbreviations (e.g., ['python', 'java'])
            location: Generic location string (fallback if city/state/country not specified)
            work_type: Work type (e.g., 'Full-time', 'Part-time', 'Contract')
            experience_level: Experience level (e.g., 'Entry level', 'Mid-Senior level')
            remote_allowed: Filter for remote jobs only
            salary_min: Minimum yearly salary
            salary_max: Maximum yearly salary
            city: Specific city filter
            state: Specific state filter
            country: Specific country filter

        Returns:
            Set of job_ids that pass all filters
        """
        # Start with all jobs
        valid_ids = set(self.jobs["job_id"])

        # Filter by skills (AND logic - must have ALL skills)
        if skills:
            for skill_abr in skills:
                skill_abr = skill_abr.lower()
                # Get jobs that have this skill
                jobs_with_skill = set(
                    self.job_skills[
                        self.job_skills["skill_abr"].str.lower() == skill_abr
                    ]["job_id"]
                )
                # Intersect with valid_ids (AND logic)
                valid_ids &= jobs_with_skill

        # Filter by location
        if city:
            valid_ids &= set(
                self.jobs[self.jobs["city"].str.lower() == city.lower()]["job_id"]
            )

        if state:
            valid_ids &= set(
                self.jobs[self.jobs["state"].str.upper() == state.upper()]["job_id"]
            )

        if country:
            valid_ids &= set(
                self.jobs[self.jobs["country"].str.lower() == country.lower()]["job_id"]
            )

        # Generic location fallback (search in city, state, or country)
        if location and not (city or state or country):
            location_lower = location.lower()
            location_ids = set(
                self.jobs[
                    (self.jobs["city"].str.lower() == location_lower)
                    | (self.jobs["state"].str.lower() == location_lower)
                    | (self.jobs["country"].str.lower() == location_lower)
                ]["job_id"]
            )
            valid_ids &= location_ids

        # Filter by work type
        if work_type:
            valid_ids &= set(
                self.jobs[self.jobs["work_type"].str.lower() == work_type.lower()][
                    "job_id"
                ]
            )

        # Filter by experience level
        if experience_level:
            valid_ids &= set(
                self.jobs[
                    self.jobs["experience_level"].str.lower()
                    == experience_level.lower()
                ]["job_id"]
            )

        # Filter by remote
        if remote_allowed is not None:
            valid_ids &= set(
                self.jobs[self.jobs["remote_allowed"] == remote_allowed]["job_id"]
            )

        # Filter by salary (only jobs that have salary data)
        if salary_min is not None or salary_max is not None:
            salary_jobs = self.jobs[self.jobs["normalized_salary_yearly"].notna()]

            if salary_min is not None:
                salary_jobs = salary_jobs[
                    salary_jobs["normalized_salary_yearly"] >= salary_min
                ]

            if salary_max is not None:
                salary_jobs = salary_jobs[
                    salary_jobs["normalized_salary_yearly"] <= salary_max
                ]

            valid_ids &= set(salary_jobs["job_id"])

        return valid_ids

    def search(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict] = None,
        title_weight: float = 3.0,
        skills_weight: float = 2.0,
        description_weight: float = 1.0,
    ) -> pd.DataFrame:
        """
        Search for jobs using BM25 with pre-filtering.

        Process:
        1. Apply filters to get candidate job_ids (pre-filtering)
        2. Search within candidates using BM25
        3. Combine scores with weights
        4. Return top-k results

        Args:
            query: Search query (e.g., "Python developer machine learning")
            top_k: Number of results to return
            filters: Optional dict of filters (see apply_filters() for keys)
            title_weight: Weight for title field (default 3.0)
            skills_weight: Weight for skills field (default 2.0)
            description_weight: Weight for description field (default 1.0)

        Returns:
            DataFrame with top-k jobs and their scores
        """
        if self.jobs is None:
            raise RuntimeError("Data not loaded. Call load_data() first.")

        start_time = time.time()

        # Step 1: Apply filters (pre-filtering)
        if filters:
            valid_ids = self.apply_filters(**filters)
        else:
            valid_ids = set(self.jobs["job_id"])

        # Convert to indexes
        valid_indexes = [
            self.job_id_to_idx[job_id]
            for job_id in valid_ids
            if job_id in self.job_id_to_idx
        ]

        if len(valid_indexes) == 0:
            # No jobs pass filters
            if self.verbose:
                print(
                    f"⚠️ No jobs match filters (search time: {time.time() - start_time:.3f}s)"
                )
            return pd.DataFrame()

        # Step 2: Tokenize query
        query_tokens = self._tokenize(query)

        if len(query_tokens) == 0:
            # Empty query - return random sample of filtered jobs
            sample_size = min(top_k, len(valid_indexes))
            sample_indexes = np.random.choice(
                valid_indexes, size=sample_size, replace=False
            )
            results_df = self.jobs.iloc[sample_indexes].copy()
            results_df["bm25_score"] = 0.0
            results_df["title_score"] = 0.0
            results_df["skills_score"] = 0.0
            results_df["description_score"] = 0.0
            return results_df

        # Step 3: Calculate BM25 scores for each field
        # Optimization: If we have many candidates, calculate for all and filter
        # If we have few candidates (<10% of corpus), calculate only for candidates

        if len(valid_indexes) < len(self.jobs) * 0.1:
            # Few candidates: calculate only for them (slower but saves memory)
            title_scores_all = self.bm25_title.get_scores(query_tokens)
            skills_scores_all = self.bm25_skills.get_scores(query_tokens)
            description_scores_all = self.bm25_description.get_scores(query_tokens)

            title_scores = title_scores_all[valid_indexes]
            skills_scores = skills_scores_all[valid_indexes]
            description_scores = description_scores_all[valid_indexes]
        else:
            # Many candidates: calculate for all (faster with NumPy vectorization)
            title_scores_all = self.bm25_title.get_scores(query_tokens)
            skills_scores_all = self.bm25_skills.get_scores(query_tokens)
            description_scores_all = self.bm25_description.get_scores(query_tokens)

            title_scores = title_scores_all[valid_indexes]
            skills_scores = skills_scores_all[valid_indexes]
            description_scores = description_scores_all[valid_indexes]

        # Step 4: Combine with weights
        combined_scores = (
            title_weight * title_scores
            + skills_weight * skills_scores
            + description_weight * description_scores
        )

        # Step 5: Get top-k
        top_k = min(top_k, len(valid_indexes))
        top_indexes_local = np.argsort(combined_scores)[::-1][:top_k]

        # Map back to original DataFrame indexes
        top_indexes_global = [valid_indexes[i] for i in top_indexes_local]

        # Step 6: Create results DataFrame
        results_df = self.jobs.iloc[top_indexes_global].copy()
        results_df["bm25_score"] = combined_scores[top_indexes_local]
        results_df["title_score"] = title_scores[top_indexes_local]
        results_df["skills_score"] = skills_scores[top_indexes_local]
        results_df["description_score"] = description_scores[top_indexes_local]

        elapsed = time.time() - start_time

        if self.verbose:
            print(
                f"✓ Found {len(results_df)} results in {elapsed:.3f}s "
                f"(filtered from {len(self.jobs):,} → {len(valid_indexes):,} candidates)"
            )

        return results_df

    def get_job_skills(self, job_id: int) -> List[str]:
        """
        Get skill names for a job.

        Args:
            job_id: Job ID

        Returns:
            List of skill names
        """
        skill_abrs = self.job_skills_dict.get(job_id, [])
        skill_map = self.skills.set_index("skill_abr")["skill_name"].to_dict()
        return [skill_map.get(abr, abr) for abr in skill_abrs]

    def get_job_industries(self, job_id: int) -> List[str]:
        """
        Get industry names for a job.

        Args:
            job_id: Job ID

        Returns:
            List of industry names
        """
        industry_ids = self.job_industries_dict.get(job_id, [])
        industry_map = self.industries.set_index("industry_id")[
            "industry_name"
        ].to_dict()
        return [industry_map.get(iid, str(iid)) for iid in industry_ids]


def demo_search():
    """Demo function to test BM25 search."""
    print("\n" + "=" * 60)
    print("BM25 JOB SEARCH - DEMO")
    print("=" * 60)

    # Initialize
    searcher = BM25JobSearch(verbose=True)
    searcher.load_data()

    print("\n" + "=" * 60)
    print("TEST 1: Simple Query (No Filters)")
    print("=" * 60)
    print("Query: 'Python developer'")

    results = searcher.search("Python developer", top_k=5)
    print(f"\nTop 5 Results:")
    for idx, row in results.iterrows():
        print(f"\n{idx+1}. {row['title']}")
        print(f"   Company: {row['company_name']}")
        print(f"   Location: {row['city']}, {row['state']}")
        print(f"   BM25 Score: {row['bm25_score']:.2f}")
        skills = searcher.get_job_skills(row["job_id"])
        print(f"   Skills: {', '.join(skills[:5])}")

    print("\n" + "=" * 60)
    print("TEST 2: With Filters")
    print("=" * 60)
    print("Query: 'machine learning engineer'")
    print("Filters: skills=['python'], city='San Francisco', remote_allowed=True")

    results = searcher.search(
        "machine learning engineer",
        top_k=5,
        filters={"skills": ["python"], "city": "San Francisco", "remote_allowed": True},
    )

    if len(results) > 0:
        print(f"\nTop {len(results)} Results:")
        for idx, row in results.iterrows():
            print(f"\n{idx+1}. {row['title']}")
            print(f"   Company: {row['company_name']}")
            print(f"   Remote: {row['remote_allowed']}")
            print(f"   BM25 Score: {row['bm25_score']:.2f}")
    else:
        print("\n⚠️ No results found (filters too strict)")

    print("\n" + "=" * 60)
    print("✓ DEMO COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    demo_search()
