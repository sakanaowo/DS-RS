"""
Utility functions for loading raw and processed datasets used in the
Intelligent Job Matching System.

Day 1 deliverable: provide a single module that can (1) inspect raw CSVs under
`data/raw` and (2) assemble an enriched jobs dataframe by joining postings with
skills, industries, salaries, benefits and company metadata.
"""

import gc
from pathlib import Path
from typing import Optional, Sequence

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
DEFAULT_CLEAN_PARQUET = PROCESSED_DIR / "clean_jobs.parquet"
DEFAULT_CLEAN_CSV = PROCESSED_DIR / "clean_jobs.csv"


def _require_file(path: Path) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"Không tìm thấy file dữ liệu: {path}")
    return path


def _collapse_unique(values: pd.Series) -> Optional[str]:
    """Convert a series of categorical values into a sorted, comma-separated string."""
    cleaned = {str(v).strip() for v in values if isinstance(v, str) and v.strip()}
    return ", ".join(sorted(cleaned)) if cleaned else None


def load_raw_postings(
    columns: Optional[Sequence[str]] = None,
    nrows: Optional[int] = None,
) -> pd.DataFrame:
    """
    Đọc bảng postings từ `data/raw`. Có thể truyền `columns` và `nrows`
    để giảm bộ nhớ khi khám phá.
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
    Join postings với skills, industries, benefits, salaries và company metadata.

    Args:
        sample: nếu khác None, chỉ lấy n dòng đầu để thử nghiệm.
        persist: nếu True thì lưu lại file vào `data/processed/{output_name}`.
        output_name: tên file đầu ra (hỗ trợ .csv hoặc .parquet).
    """
    postings = load_raw_postings().copy()
    if sample:
        postings = postings.head(sample).copy()

    postings["job_id"] = pd.to_numeric(postings["job_id"], errors="coerce").astype(
        "Int64"
    )
    postings["company_id"] = pd.to_numeric(
        postings["company_id"], errors="coerce"
    ).astype("Int64")

    # Skills
    skills = pd.read_csv(_require_file(RAW_DIR / "jobs/job_skills.csv"))
    skills["job_id"] = pd.to_numeric(skills["job_id"], errors="coerce").astype("Int64")
    skill_map = pd.read_csv(_require_file(RAW_DIR / "mappings/skills.csv")).set_index(
        "skill_abr"
    )["skill_name"]
    skills["skill_name"] = skills["skill_abr"].map(skill_map)
    skill_agg = (
        skills.groupby("job_id")["skill_name"]
        .apply(_collapse_unique)
        .reset_index()
        .rename(columns={"skill_name": "skills"})
    )

    # Industries
    job_ind = pd.read_csv(_require_file(RAW_DIR / "jobs/job_industries.csv"))
    job_ind["job_id"] = pd.to_numeric(job_ind["job_id"], errors="coerce").astype(
        "Int64"
    )
    industry_map = pd.read_csv(
        _require_file(RAW_DIR / "mappings/industries.csv")
    ).set_index("industry_id")["industry_name"]
    job_ind["industry_name"] = job_ind["industry_id"].map(industry_map)
    industry_agg = (
        job_ind.groupby("job_id")["industry_name"]
        .apply(_collapse_unique)
        .reset_index()
        .rename(columns={"industry_name": "industries"})
    )

    # Benefits
    benefits = pd.read_csv(_require_file(RAW_DIR / "jobs/benefits.csv"))
    benefits["job_id"] = pd.to_numeric(benefits["job_id"], errors="coerce").astype(
        "Int64"
    )
    benefits_agg = (
        benefits.groupby("job_id")["type"]
        .apply(_collapse_unique)
        .reset_index()
        .rename(columns={"type": "benefits"})
    )

    # Salaries
    salaries = pd.read_csv(_require_file(RAW_DIR / "jobs/salaries.csv"))
    salaries["job_id"] = pd.to_numeric(salaries["job_id"], errors="coerce").astype(
        "Int64"
    )
    for col in ["min_salary", "med_salary", "max_salary"]:
        if col in salaries.columns:
            salaries[col] = pd.to_numeric(salaries[col], errors="coerce")
    salary_agg = (
        salaries.sort_values(["job_id", "salary_id"])
        .groupby("job_id")
        .agg(
            salary_min=("min_salary", "min"),
            salary_median=("med_salary", "mean"),
            salary_max=("max_salary", "max"),
            salary_currency=("currency", "first"),
            salary_period=("pay_period", "first"),
            salary_type=("compensation_type", "first"),
        )
        .reset_index()
    )

    # Company metadata
    company_cols = [
        "company_id",
        "name",
        "description",
        "company_size",
        "state",
        "country",
        "city",
        "zip_code",
        "url",
    ]
    companies = pd.read_csv(
        _require_file(RAW_DIR / "companies/companies.csv"), usecols=company_cols
    )
    companies = companies.rename(
        columns={
            "name": "company_name",
            "description": "company_description",
            "state": "company_state",
            "country": "company_country",
            "city": "company_city",
            "zip_code": "company_zip",
            "url": "company_url",
        }
    )

    company_specs = pd.read_csv(
        _require_file(RAW_DIR / "companies/company_specialities.csv")
    )
    company_specs_agg = (
        company_specs.groupby("company_id")["speciality"]
        .apply(_collapse_unique)
        .reset_index()
        .rename(columns={"speciality": "company_specialities"})
    )

    company_industry_tags = pd.read_csv(
        _require_file(RAW_DIR / "companies/company_industries.csv")
    )
    company_industry_agg = (
        company_industry_tags.groupby("company_id")["industry"]
        .apply(_collapse_unique)
        .reset_index()
        .rename(columns={"industry": "company_industries"})
    )

    employee_counts = pd.read_csv(
        _require_file(RAW_DIR / "companies/employee_counts.csv")
    )
    employee_latest = employee_counts.sort_values("time_recorded").drop_duplicates(
        "company_id", keep="last"
    )
    employee_latest = employee_latest.rename(
        columns={
            "employee_count": "company_employee_count",
            "follower_count": "company_follower_count",
        }
    )

    enriched = postings.merge(skill_agg, on="job_id", how="left")
    del skill_agg
    gc.collect()

    enriched = enriched.merge(industry_agg, on="job_id", how="left")
    del industry_agg
    gc.collect()

    enriched = enriched.merge(benefits_agg, on="job_id", how="left")
    del benefits_agg
    gc.collect()

    enriched = enriched.merge(salary_agg, on="job_id", how="left")
    del salary_agg
    gc.collect()

    enriched = enriched.merge(companies, on="company_id", how="left")
    del companies
    gc.collect()

    enriched = enriched.merge(company_specs_agg, on="company_id", how="left")
    del company_specs_agg
    gc.collect()

    enriched = enriched.merge(company_industry_agg, on="company_id", how="left")
    del company_industry_agg
    gc.collect()

    enriched = enriched.merge(employee_latest, on="company_id", how="left")
    del employee_latest
    gc.collect()

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
    Complete pipeline: build enriched jobs then apply cleaning.

    This is the main entry point for Day 2 data cleaning workflow.

    Args:
        sample: if not None, only process first n rows (for testing)
        persist: if True, save to data/processed/
        output_name: output filename (supports .csv or .parquet)

    Returns:
        Cleaned and enriched DataFrame ready for vectorization
    """
    # Import preprocessing module - handle both relative and absolute imports
    try:
        from . import preprocessing
    except ImportError:
        # Fallback for notebook/script context where relative imports don't work
        import preprocessing

    print("Step 1: Building enriched jobs dataset...")
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


def load_cleaned_jobs(path: Optional[Path] = None) -> pd.DataFrame:
    """
    Đọc file đã làm sạch (ưu tiên Parquet, fallback CSV).
    """
    candidates = []
    if path:
        candidates.append(Path(path))
    candidates.extend([DEFAULT_CLEAN_PARQUET, DEFAULT_CLEAN_CSV])

    for candidate in candidates:
        if candidate.exists():
            if candidate.suffix == ".parquet":
                try:
                    df = pd.read_parquet(candidate)
                except Exception as exc:  # pragma: no cover - pyarrow optional
                    raise RuntimeError(f"Không thể đọc {candidate}: {exc}") from exc
            else:
                df = pd.read_csv(candidate)
            break
    else:
        raise FileNotFoundError(
            "Không tìm thấy dữ liệu đã làm sạch. Hãy chạy notebook 1_data_cleaning.ipynb để tạo `clean_jobs`."
        )

    for col in ["title", "description", "skills", "content"]:
        if col in df.columns:
            df[col] = df[col].fillna("")
    return df


if __name__ == "__main__":
    try:
        # Test with small sample
        print("Testing enriched jobs pipeline...")
        snapshot = build_enriched_jobs(sample=1000, persist=False)
        print(f"✓ Enriched sample shape: {snapshot.shape}")
        print(snapshot[["job_id", "title", "skills", "industries"]].head())

        print("\n" + "=" * 60)
        print("Testing full cleaning pipeline...")
        cleaned = build_and_clean_jobs(sample=1000, persist=False)
        print(f"✓ Cleaned sample shape: {cleaned.shape}")
        if "content" in cleaned.columns:
            print(
                f"✓ Content field created with avg length: {cleaned['content'].str.len().mean():.0f} chars"
            )
    except FileNotFoundError as err:
        print(f"❌ Error: {err}")
    except ImportError as err:
        print(f"❌ Import Error: {err}")
        print("Make sure to run from project root or have src/ in PYTHONPATH")
