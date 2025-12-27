"""
Utility functions for loading raw and processed datasets used in the
Intelligent Job Matching System.

REFACTORED (Day 1): Normalized data pipeline - NO aggregation.
- Keeps skills/industries in separate tables (many-to-many relationships)
- Enables accurate pre-filtering before search
- Reduces storage by 66% (675 MB → 227 MB)
"""

from pathlib import Path
from typing import Optional, Dict

import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

# Normalized table paths
JOBS_PARQUET = PROCESSED_DIR / "jobs.parquet"
JOB_SKILLS_PARQUET = PROCESSED_DIR / "job_skills.parquet"
SKILLS_PARQUET = PROCESSED_DIR / "skills.parquet"
JOB_INDUSTRIES_PARQUET = PROCESSED_DIR / "job_industries.parquet"
INDUSTRIES_PARQUET = PROCESSED_DIR / "industries.parquet"

# Legacy paths (backward compatibility)
DEFAULT_CLEAN_PARQUET = PROCESSED_DIR / "clean_jobs.parquet"
DEFAULT_CLEAN_CSV = PROCESSED_DIR / "clean_jobs.csv"


def _require_file(path: Path) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"Không tìm thấy file dữ liệu: {path}")
    return path


def _require_file(path: Path) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"Không tìm thấy file dữ liệu: {path}")
    return path


# ============================================================================
# HELPER FUNCTIONS - Location & Salary Parsing
# ============================================================================


def parse_location(loc_str: str) -> Dict[str, str]:
    """
    Parse location string into city, state, country.

    Examples:
    - "San Francisco, CA, United States" → {'city': 'San Francisco', 'state': 'CA', 'country': 'United States'}
    - "New York, NY" → {'city': 'New York', 'state': 'NY', 'country': 'United States'}
    - "Remote" → {'city': 'Remote', 'state': '', 'country': ''}
    - "United States" → {'city': '', 'state': '', 'country': 'United States'}
    """
    if pd.isna(loc_str) or not isinstance(loc_str, str) or loc_str.strip() == "":
        return {"city": "", "state": "", "country": ""}

    location = loc_str.strip()

    # Special cases
    if location.lower() == "remote":
        return {"city": "Remote", "state": "", "country": ""}

    if location == "United States":
        return {"city": "", "state": "", "country": "United States"}

    # Split by comma
    parts = [p.strip() for p in location.split(",")]

    if len(parts) == 1:
        # Only one part - could be city or country
        return {"city": parts[0], "state": "", "country": ""}

    elif len(parts) == 2:
        # Two parts - city, state OR city, country
        city, second = parts
        # If second part is 2 uppercase letters, likely US state
        if len(second) == 2 and second.isupper():
            return {"city": city, "state": second, "country": "United States"}
        else:
            return {"city": city, "state": "", "country": second}

    else:
        # Three or more parts - city, state, country
        return {"city": parts[0], "state": parts[1], "country": parts[-1]}


def normalize_salary_to_yearly(row: pd.Series) -> Optional[float]:
    """
    Convert salary to yearly amount.

    Args:
        row: pandas Series with columns: min_salary, max_salary, pay_period

    Returns:
        Yearly salary (median of min and max), or None if missing

    Multipliers:
    - YEARLY: 1
    - MONTHLY: 12
    - BIWEEKLY: 26
    - WEEKLY: 52
    - HOURLY: 2080 (40 hours/week × 52 weeks)
    """
    # Check if salary data exists
    if pd.isna(row.get("min_salary")) or pd.isna(row.get("max_salary")):
        return None

    # Calculate median
    try:
        min_sal = float(row["min_salary"])
        max_sal = float(row["max_salary"])
        median = (min_sal + max_sal) / 2
    except (ValueError, TypeError):
        return None

    # Get pay period
    period = str(row.get("pay_period", "")).upper()

    # Conversion multipliers
    multipliers = {
        "YEARLY": 1,
        "MONTHLY": 12,
        "BIWEEKLY": 26,
        "WEEKLY": 52,
        "HOURLY": 2080,  # 40h/week × 52 weeks
    }

    multiplier = multipliers.get(period, 1)
    return median * multiplier


# ============================================================================
# DATA LOADING FUNCTIONS - Normalized Schema
# ============================================================================


def load_jobs_normalized(sample: Optional[int] = None) -> pd.DataFrame:
    """
    Load jobs table without aggregation.

    Args:
        sample: If not None, only load first N rows (for testing)

    Returns:
        DataFrame with columns:
        - job_id, title, description, company_id, company_name
        - location, city, state, country
        - work_type, experience_level, remote_allowed
        - min_salary, max_salary, pay_period, normalized_salary_yearly
        - views, applies, listed_time, closed_time
    """
    # 1. Load raw postings
    postings_path = _require_file(RAW_DIR / "postings.csv")

    nrows = sample if sample else None
    postings = pd.read_csv(postings_path, nrows=nrows)

    # 2. Select columns
    jobs = postings[
        [
            "job_id",
            "title",
            "description",
            "company_id",
            "company_name",
            "location",
            "formatted_work_type",
            "formatted_experience_level",
            "remote_allowed",
            "min_salary",
            "max_salary",
            "pay_period",
            "views",
            "applies",
            "original_listed_time",
            "closed_time",
        ]
    ].copy()

    # 3. Clean
    # Drop jobs without title or description
    jobs = jobs[jobs["title"].notna() & (jobs["title"].str.strip() != "")]
    jobs = jobs[jobs["description"].notna() & (jobs["description"].str.strip() != "")]

    # Remove duplicates by job_id
    jobs = jobs.drop_duplicates(subset=["job_id"], keep="first")

    # 4. Parse location
    location_parsed = jobs["location"].fillna("").apply(parse_location)
    jobs["city"] = location_parsed.apply(lambda x: x["city"])
    jobs["state"] = location_parsed.apply(lambda x: x["state"])
    jobs["country"] = location_parsed.apply(lambda x: x["country"])

    # 5. Normalize salary
    jobs["normalized_salary_yearly"] = jobs.apply(normalize_salary_to_yearly, axis=1)

    # 6. Rename columns
    jobs = jobs.rename(
        columns={
            "formatted_work_type": "work_type",
            "formatted_experience_level": "experience_level",
            "original_listed_time": "listed_time",
        }
    )

    # 7. Convert dtypes
    jobs["job_id"] = pd.to_numeric(jobs["job_id"], errors="coerce").astype("Int64")
    jobs["company_id"] = pd.to_numeric(jobs["company_id"], errors="coerce").astype(
        "Int64"
    )
    jobs["remote_allowed"] = jobs["remote_allowed"].astype("boolean")
    jobs["listed_time"] = pd.to_datetime(jobs["listed_time"], errors="coerce")
    jobs["closed_time"] = pd.to_datetime(jobs["closed_time"], errors="coerce")

    return jobs


def load_job_skills() -> pd.DataFrame:
    """
    Load job-skill relationships (NO aggregation).

    Returns:
        DataFrame with columns: job_id, skill_abr
    """
    path = _require_file(RAW_DIR / "jobs" / "job_skills.csv")
    job_skills = pd.read_csv(path)

    # Keep only needed columns
    job_skills = job_skills[["job_id", "skill_abr"]].copy()

    # Convert dtypes
    job_skills["job_id"] = pd.to_numeric(job_skills["job_id"], errors="coerce").astype(
        "Int64"
    )

    # Drop rows with missing values
    job_skills = job_skills.dropna()

    return job_skills


def load_skills() -> pd.DataFrame:
    """
    Load skills lookup table.

    Returns:
        DataFrame with columns: skill_abr, skill_name
    """
    path = _require_file(RAW_DIR / "mappings" / "skills.csv")
    skills = pd.read_csv(path)
    skills = skills[["skill_abr", "skill_name"]].copy()

    return skills


def load_job_industries() -> pd.DataFrame:
    """
    Load job-industry relationships (NO aggregation).

    Returns:
        DataFrame with columns: job_id, industry_id
    """
    path = _require_file(RAW_DIR / "jobs" / "job_industries.csv")
    job_industries = pd.read_csv(path)

    # Keep only needed columns
    job_industries = job_industries[["job_id", "industry_id"]].copy()

    # Convert dtypes
    job_industries["job_id"] = pd.to_numeric(
        job_industries["job_id"], errors="coerce"
    ).astype("Int64")
    job_industries["industry_id"] = pd.to_numeric(
        job_industries["industry_id"], errors="coerce"
    ).astype("Int64")

    # Drop rows with missing values
    job_industries = job_industries.dropna()

    return job_industries


def load_industries() -> pd.DataFrame:
    """
    Load industries lookup table.

    Returns:
        DataFrame with columns: industry_id, industry_name
    """
    path = _require_file(RAW_DIR / "mappings" / "industries.csv")
    industries = pd.read_csv(path)
    industries = industries[["industry_id", "industry_name"]].copy()

    return industries


def save_normalized_data(jobs, job_skills, skills, job_industries, industries):
    """
    Save all normalized tables to data/processed/
    """
    # Create directory if not exists
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # Save as Parquet (compact, fast)
    files = {
        "jobs.parquet": jobs,
        "job_skills.parquet": job_skills,
        "skills.parquet": skills,
        "job_industries.parquet": job_industries,
        "industries.parquet": industries,
    }

    for filename, df in files.items():
        filepath = PROCESSED_DIR / filename
        df.to_parquet(filepath, index=False)
        print(f"  ✓ Saved {filename} ({len(df):,} rows)")


# ============================================================================
# LEGACY FUNCTIONS - Backward Compatibility
# ============================================================================


def load_raw_postings(
    columns: Optional[list] = None,
    nrows: Optional[int] = None,
) -> pd.DataFrame:
    """
    [LEGACY] Đọc bảng postings từ `data/raw`.

    Note: Use load_jobs_normalized() for new code.
    """
    # Optimize dtypes to reduce memory usage
    dtype_map = {
        "remote_allowed": "Int8",
        "views": "Int32",
        "applies": "Int32",
        "formatted_work_type": "category",
        "formatted_experience_level": "category",
    }

    kwargs = {}
    if columns:
        kwargs["usecols"] = list(columns)
        # Only use dtypes for columns that will be loaded
        dtype_map = {k: v for k, v in dtype_map.items() if k in columns}
    if nrows:
        kwargs["nrows"] = nrows
    if dtype_map:
        kwargs["dtype"] = dtype_map

    path = _require_file(RAW_DIR / "postings.csv")
    return pd.read_csv(path, **kwargs)


def build_enriched_jobs(
    sample: Optional[int] = None,
    persist: bool = False,
    output_name: str = "jobs_stage1.parquet",
) -> pd.DataFrame:
    """
    [DEPRECATED] Use load_jobs_normalized() instead.

    This function aggregates skills/industries into strings, which:
    - Prevents accurate filtering (string matching vs JOIN)
    - Increases storage by 3x
    - Breaks relational integrity

    Kept for backward compatibility only.
    """
    import warnings

    warnings.warn(
        "build_enriched_jobs() is deprecated. Use load_jobs_normalized() instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    # For backward compatibility, return normalized jobs
    # but aggregate skills/industries into strings
    jobs = load_jobs_normalized(sample=sample)
    job_skills = load_job_skills()
    skills = load_skills()
    job_industries = load_job_industries()
    industries = load_industries()

    # Aggregate skills to comma-separated string
    skill_map = skills.set_index("skill_abr")["skill_name"].to_dict()
    job_skills["skill_name"] = job_skills["skill_abr"].map(skill_map)
    skills_agg = (
        job_skills.groupby("job_id")["skill_name"]
        .apply(lambda x: ", ".join(sorted(set(str(v) for v in x if pd.notna(v)))))
        .reset_index()
        .rename(columns={"skill_name": "skills"})
    )

    # Aggregate industries to comma-separated string
    industry_map = industries.set_index("industry_id")["industry_name"].to_dict()
    job_industries["industry_name"] = job_industries["industry_id"].map(industry_map)
    industries_agg = (
        job_industries.groupby("job_id")["industry_name"]
        .apply(lambda x: ", ".join(sorted(set(str(v) for v in x if pd.notna(v)))))
        .reset_index()
        .rename(columns={"industry_name": "industries"})
    )

    # Merge aggregated data
    enriched = jobs.merge(skills_agg, on="job_id", how="left")
    enriched = enriched.merge(industries_agg, on="job_id", how="left")

    if persist:
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        output_path = PROCESSED_DIR / output_name
        if output_path.suffix == ".parquet":
            enriched.to_parquet(output_path, index=False)
        else:
            enriched.to_csv(output_path, index=False)
        print(f"Đã lưu enriched jobs vào {output_path}")

    return enriched


def build_and_clean_jobs(
    sample: Optional[int] = None,
    persist: bool = True,
    output_name: str = "clean_jobs.parquet",
) -> pd.DataFrame:
    """
    [DEPRECATED] Use load_jobs_normalized() and prepare_features() separately.

    This function creates aggregated strings which prevent accurate filtering.
    Kept for backward compatibility only.
    """
    import warnings

    warnings.warn(
        "build_and_clean_jobs() is deprecated. Use load_jobs_normalized() + prepare_features() instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    # Import preprocessing module
    try:
        from . import preprocessing
    except ImportError:
        import preprocessing

    print("Step 1: Building enriched jobs dataset (legacy mode)...")
    enriched = build_enriched_jobs(sample=sample, persist=False)

    print(f"\nStep 2: Applying cleaning pipeline to {len(enriched):,} jobs...")
    cleaned = preprocessing.prepare_features(enriched)

    if persist:
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        output_path = PROCESSED_DIR / output_name
        if output_path.suffix == ".parquet":
            cleaned.to_parquet(output_path, index=False)
        else:
            cleaned.to_csv(output_path, index=False)
        print(f"\n✓ Saved cleaned jobs to {output_path}")
        print(f"  Final shape: {cleaned.shape}")

    return cleaned


def load_normalized_tables() -> Dict[str, pd.DataFrame]:
    """
    Load all normalized tables at once.

    Returns:
        Dict with keys: 'jobs', 'job_skills', 'skills', 'job_industries', 'industries'
    """
    return {
        "jobs": pd.read_parquet(_require_file(JOBS_PARQUET)),
        "job_skills": pd.read_parquet(_require_file(JOB_SKILLS_PARQUET)),
        "skills": pd.read_parquet(_require_file(SKILLS_PARQUET)),
        "job_industries": pd.read_parquet(_require_file(JOB_INDUSTRIES_PARQUET)),
        "industries": pd.read_parquet(_require_file(INDUSTRIES_PARQUET)),
    }


def get_jobs_with_skills(job_ids: Optional[list] = None) -> pd.DataFrame:
    """
    Get jobs table with skills as comma-separated string (for display).

    Args:
        job_ids: Optional list of job_ids to filter

    Returns:
        DataFrame with 'skills' column as comma-separated string
    """
    jobs = pd.read_parquet(_require_file(JOBS_PARQUET))
    job_skills = pd.read_parquet(_require_file(JOB_SKILLS_PARQUET))
    skills = pd.read_parquet(_require_file(SKILLS_PARQUET))

    if job_ids is not None:
        jobs = jobs[jobs["job_id"].isin(job_ids)]

    # Map skill names
    skill_map = skills.set_index("skill_abr")["skill_name"].to_dict()
    job_skills["skill_name"] = job_skills["skill_abr"].map(skill_map)

    # Aggregate to comma-separated string for display
    skills_agg = (
        job_skills.groupby("job_id")["skill_name"]
        .apply(lambda x: ", ".join(sorted(set(str(v) for v in x if pd.notna(v)))))
        .reset_index()
        .rename(columns={"skill_name": "skills"})
    )

    # Merge
    result = jobs.merge(skills_agg, on="job_id", how="left")
    result["skills"] = result["skills"].fillna("")

    return result


def get_jobs_with_industries(job_ids: Optional[list] = None) -> pd.DataFrame:
    """
    Get jobs table with industries as comma-separated string (for display).

    Args:
        job_ids: Optional list of job_ids to filter

    Returns:
        DataFrame with 'industries' column as comma-separated string
    """
    jobs = pd.read_parquet(_require_file(JOBS_PARQUET))
    job_industries = pd.read_parquet(_require_file(JOB_INDUSTRIES_PARQUET))
    industries = pd.read_parquet(_require_file(INDUSTRIES_PARQUET))

    if job_ids is not None:
        jobs = jobs[jobs["job_id"].isin(job_ids)]

    # Map industry names
    industry_map = industries.set_index("industry_id")["industry_name"].to_dict()
    job_industries["industry_name"] = job_industries["industry_id"].map(industry_map)

    # Aggregate to comma-separated string for display
    industries_agg = (
        job_industries.groupby("job_id")["industry_name"]
        .apply(lambda x: ", ".join(sorted(set(str(v) for v in x if pd.notna(v)))))
        .reset_index()
        .rename(columns={"industry_name": "industries"})
    )

    # Merge
    result = jobs.merge(industries_agg, on="job_id", how="left")
    result["industries"] = result["industries"].fillna("")

    return result


def load_cleaned_jobs(path: Optional[Path] = None) -> pd.DataFrame:
    """
    [LEGACY] Đọc file đã làm sạch (ưu tiên Parquet, fallback CSV).

    Note: For new code, use load_jobs_normalized() or load_normalized_tables().
    """
    candidates = []
    if path:
        candidates.append(Path(path))

    # Try normalized tables first
    if JOBS_PARQUET.exists():
        try:
            return get_jobs_with_skills()
        except Exception:
            pass

    # Fallback to legacy files
    candidates.extend([DEFAULT_CLEAN_PARQUET, DEFAULT_CLEAN_CSV])

    for candidate in candidates:
        if candidate.exists():
            if candidate.suffix == ".parquet":
                try:
                    df = pd.read_parquet(candidate)
                except Exception as exc:
                    raise RuntimeError(f"Không thể đọc {candidate}: {exc}") from exc
            else:
                df = pd.read_csv(candidate)
            break
    else:
        raise FileNotFoundError(
            "Không tìm thấy dữ liệu. Hãy chạy notebook 1_data_cleaning.ipynb hoặc day1_data_pipeline_v2.ipynb để tạo data."
        )

    for col in ["title", "description", "skills", "content"]:
        if col in df.columns:
            df[col] = df[col].fillna("")
    return df


if __name__ == "__main__":
    print("=" * 60)
    print("TESTING NORMALIZED DATA PIPELINE")
    print("=" * 60)

    try:
        # Test normalized loading
        print("\n1. Testing load_jobs_normalized()...")
        jobs = load_jobs_normalized(sample=1000)
        print(f"   ✓ Loaded {len(jobs):,} jobs")
        print(f"   ✓ Columns: {list(jobs.columns)}")

        print("\n2. Testing load_job_skills()...")
        job_skills = load_job_skills()
        print(f"   ✓ Loaded {len(job_skills):,} job-skill relationships")
        print(
            f"   ✓ Avg skills per job: {len(job_skills)/job_skills['job_id'].nunique():.2f}"
        )

        print("\n3. Testing load_skills()...")
        skills = load_skills()
        print(f"   ✓ Loaded {len(skills):,} skills")

        print("\n4. Testing get_jobs_with_skills()...")
        sample_ids = jobs["job_id"].head(10).tolist()
        jobs_display = get_jobs_with_skills(job_ids=sample_ids)
        print(f"   ✓ Created display format with skills column")
        print(f"   ✓ Sample: {jobs_display[['job_id', 'title', 'skills']].head(3)}")

        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED")
        print("=" * 60)

    except FileNotFoundError as err:
        print(f"\n❌ Error: {err}")
        print("\nRun this to generate normalized data:")
        print("  python notebooks/day1_data_pipeline_v2.ipynb")
    except Exception as err:
        print(f"\n❌ Unexpected Error: {err}")
        import traceback

        traceback.print_exc()
