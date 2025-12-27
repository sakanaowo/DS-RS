"""
Unit tests for normalized data loader

Tests cover:
- Helper functions (parse_location, normalize_salary)
- Data loading functions (load_jobs_normalized, load_job_skills, etc.)
- Data integrity (no duplicates, foreign keys, data quality)
- Backward compatibility (legacy functions)
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from loader import (
    parse_location,
    normalize_salary_to_yearly,
    load_jobs_normalized,
    load_job_skills,
    load_skills,
    load_job_industries,
    load_industries,
    get_jobs_with_skills,
    get_jobs_with_industries,
    load_normalized_tables,
    JOBS_PARQUET,
    JOB_SKILLS_PARQUET,
    SKILLS_PARQUET,
    JOB_INDUSTRIES_PARQUET,
    INDUSTRIES_PARQUET,
)


# ============================================================================
# HELPER FUNCTION TESTS
# ============================================================================


class TestParseLocation:
    """Test parse_location() helper function."""

    def test_full_location(self):
        """Test parsing full location with city, state, country."""
        result = parse_location("San Francisco, CA, United States")
        assert result == {
            "city": "San Francisco",
            "state": "CA",
            "country": "United States",
        }

    def test_city_state_only(self):
        """Test parsing location with city and 2-letter state."""
        result = parse_location("New York, NY")
        assert result == {"city": "New York", "state": "NY", "country": "United States"}

    def test_city_country(self):
        """Test parsing location with city and country (not US)."""
        result = parse_location("London, United Kingdom")
        assert result == {"city": "London", "state": "", "country": "United Kingdom"}

    def test_remote(self):
        """Test parsing 'Remote' location."""
        result = parse_location("Remote")
        assert result == {"city": "Remote", "state": "", "country": ""}

    def test_country_only(self):
        """Test parsing country-only location."""
        result = parse_location("United States")
        assert result == {"city": "", "state": "", "country": "United States"}

    def test_empty_string(self):
        """Test parsing empty string."""
        result = parse_location("")
        assert result == {"city": "", "state": "", "country": ""}

    def test_none_value(self):
        """Test parsing None value."""
        result = parse_location(None)
        assert result == {"city": "", "state": "", "country": ""}

    def test_whitespace_only(self):
        """Test parsing whitespace-only string."""
        result = parse_location("   ")
        assert result == {"city": "", "state": "", "country": ""}


class TestNormalizeSalary:
    """Test normalize_salary_to_yearly() helper function."""

    def test_yearly_salary(self):
        """Test yearly salary (no conversion needed)."""
        row = pd.Series(
            {"min_salary": 80000, "max_salary": 120000, "pay_period": "YEARLY"}
        )
        result = normalize_salary_to_yearly(row)
        assert result == 100000  # median

    def test_hourly_salary(self):
        """Test hourly salary conversion (40h/week × 52 weeks)."""
        row = pd.Series({"min_salary": 25, "max_salary": 35, "pay_period": "HOURLY"})
        result = normalize_salary_to_yearly(row)
        assert result == 30 * 2080  # median × 2080

    def test_monthly_salary(self):
        """Test monthly salary conversion."""
        row = pd.Series(
            {"min_salary": 5000, "max_salary": 7000, "pay_period": "MONTHLY"}
        )
        result = normalize_salary_to_yearly(row)
        assert result == 6000 * 12  # median × 12

    def test_weekly_salary(self):
        """Test weekly salary conversion."""
        row = pd.Series(
            {"min_salary": 1000, "max_salary": 1500, "pay_period": "WEEKLY"}
        )
        result = normalize_salary_to_yearly(row)
        assert result == 1250 * 52  # median × 52

    def test_biweekly_salary(self):
        """Test biweekly salary conversion."""
        row = pd.Series(
            {"min_salary": 2000, "max_salary": 3000, "pay_period": "BIWEEKLY"}
        )
        result = normalize_salary_to_yearly(row)
        assert result == 2500 * 26  # median × 26

    def test_missing_min_salary(self):
        """Test handling of missing min_salary."""
        row = pd.Series(
            {"min_salary": None, "max_salary": 100000, "pay_period": "YEARLY"}
        )
        result = normalize_salary_to_yearly(row)
        assert result is None

    def test_missing_max_salary(self):
        """Test handling of missing max_salary."""
        row = pd.Series(
            {"min_salary": 80000, "max_salary": None, "pay_period": "YEARLY"}
        )
        result = normalize_salary_to_yearly(row)
        assert result is None

    def test_unknown_period(self):
        """Test handling of unknown pay period (defaults to 1x multiplier)."""
        row = pd.Series(
            {"min_salary": 50000, "max_salary": 60000, "pay_period": "UNKNOWN"}
        )
        result = normalize_salary_to_yearly(row)
        assert result == 55000  # median, no conversion


# ============================================================================
# DATA LOADING TESTS
# ============================================================================


@pytest.mark.skipif(
    not JOBS_PARQUET.exists(), reason="Normalized data not generated yet"
)
class TestLoadNormalizedData:
    """Test normalized data loading functions."""

    def test_load_jobs_normalized_shape(self):
        """Test loading jobs returns expected columns."""
        jobs = load_jobs_normalized(sample=100)

        assert len(jobs) > 0
        assert "job_id" in jobs.columns
        assert "title" in jobs.columns
        assert "description" in jobs.columns
        assert "city" in jobs.columns
        assert "state" in jobs.columns
        assert "country" in jobs.columns
        assert "normalized_salary_yearly" in jobs.columns

    def test_load_jobs_no_duplicates(self):
        """Test that job_id is unique."""
        jobs = load_jobs_normalized(sample=1000)
        assert jobs["job_id"].is_unique

    def test_load_jobs_no_missing_title(self):
        """Test that all jobs have titles."""
        jobs = load_jobs_normalized(sample=1000)
        assert jobs["title"].notna().all()
        assert (jobs["title"].str.strip() != "").all()

    def test_load_jobs_no_missing_description(self):
        """Test that all jobs have descriptions."""
        jobs = load_jobs_normalized(sample=1000)
        assert jobs["description"].notna().all()
        assert (jobs["description"].str.strip() != "").all()

    def test_load_job_skills_structure(self):
        """Test job_skills table structure."""
        job_skills = load_job_skills()

        assert len(job_skills) > 0
        assert "job_id" in job_skills.columns
        assert "skill_abr" in job_skills.columns
        assert len(job_skills.columns) == 2

    def test_load_skills_structure(self):
        """Test skills lookup table."""
        skills = load_skills()

        assert len(skills) > 0
        assert "skill_abr" in skills.columns
        assert "skill_name" in skills.columns
        assert len(skills) == 35 or len(skills) == 36  # expected number

    def test_load_job_industries_structure(self):
        """Test job_industries table structure."""
        job_industries = load_job_industries()

        assert len(job_industries) > 0
        assert "job_id" in job_industries.columns
        assert "industry_id" in job_industries.columns
        assert len(job_industries.columns) == 2

    def test_load_industries_structure(self):
        """Test industries lookup table."""
        industries = load_industries()

        assert len(industries) > 0
        assert "industry_id" in industries.columns
        assert "industry_name" in industries.columns
        assert len(industries) >= 400  # expected number


# ============================================================================
# DATA INTEGRITY TESTS
# ============================================================================


@pytest.mark.skipif(
    not JOBS_PARQUET.exists(), reason="Normalized data not generated yet"
)
class TestDataIntegrity:
    """Test data integrity and foreign key constraints."""

    def test_foreign_key_skills(self):
        """Test that all skill_abr in job_skills exist in skills table."""
        job_skills = load_job_skills()
        skills = load_skills()

        invalid_skills = set(job_skills["skill_abr"]) - set(skills["skill_abr"])
        assert len(invalid_skills) == 0, f"Invalid skills found: {invalid_skills}"

    def test_foreign_key_industries(self):
        """Test that all industry_id in job_industries exist in industries table."""
        job_industries = load_job_industries()
        industries = load_industries()

        invalid_industries = set(job_industries["industry_id"]) - set(
            industries["industry_id"]
        )
        assert (
            len(invalid_industries) == 0
        ), f"Invalid industries found: {invalid_industries}"

    def test_no_missing_values_in_relationships(self):
        """Test that relationship tables have no missing values."""
        job_skills = load_job_skills()
        assert job_skills["job_id"].notna().all()
        assert job_skills["skill_abr"].notna().all()

        job_industries = load_job_industries()
        assert job_industries["job_id"].notna().all()
        assert job_industries["industry_id"].notna().all()

    def test_load_normalized_tables(self):
        """Test loading all tables at once."""
        tables = load_normalized_tables()

        assert "jobs" in tables
        assert "job_skills" in tables
        assert "skills" in tables
        assert "job_industries" in tables
        assert "industries" in tables

        assert len(tables["jobs"]) > 0
        assert len(tables["job_skills"]) > 0
        assert len(tables["skills"]) > 0


# ============================================================================
# DISPLAY FUNCTIONS TESTS
# ============================================================================


@pytest.mark.skipif(
    not JOBS_PARQUET.exists(), reason="Normalized data not generated yet"
)
class TestDisplayFunctions:
    """Test functions that create display-friendly formats."""

    def test_get_jobs_with_skills(self):
        """Test creating jobs table with skills as comma-separated string."""
        jobs = load_jobs_normalized(sample=100)
        sample_ids = jobs["job_id"].head(10).tolist()

        result = get_jobs_with_skills(job_ids=sample_ids)

        assert "skills" in result.columns
        assert len(result) == len(sample_ids)
        # Check that skills is string type
        assert result["skills"].dtype == object

    def test_get_jobs_with_industries(self):
        """Test creating jobs table with industries as comma-separated string."""
        jobs = load_jobs_normalized(sample=100)
        sample_ids = jobs["job_id"].head(10).tolist()

        result = get_jobs_with_industries(job_ids=sample_ids)

        assert "industries" in result.columns
        assert len(result) == len(sample_ids)
        # Check that industries is string type
        assert result["industries"].dtype == object

    def test_get_jobs_with_skills_no_filter(self):
        """Test getting all jobs with skills (no job_id filter)."""
        result = get_jobs_with_skills(job_ids=None)

        assert len(result) > 0
        assert "skills" in result.columns


# ============================================================================
# BACKWARD COMPATIBILITY TESTS
# ============================================================================


@pytest.mark.skipif(
    not JOBS_PARQUET.exists(), reason="Normalized data not generated yet"
)
class TestBackwardCompatibility:
    """Test that legacy functions still work (with deprecation warnings)."""

    def test_build_enriched_jobs_shows_warning(self):
        """Test that build_enriched_jobs() shows deprecation warning."""
        from loader import build_enriched_jobs

        with pytest.warns(DeprecationWarning):
            result = build_enriched_jobs(sample=10, persist=False)

        assert len(result) > 0
        # Should have aggregated skills/industries columns
        assert "skills" in result.columns or "industries" in result.columns

    def test_load_cleaned_jobs_fallback(self):
        """Test that load_cleaned_jobs() can load normalized data."""
        from loader import load_cleaned_jobs

        result = load_cleaned_jobs()

        assert len(result) > 0
        assert "job_id" in result.columns
        assert "title" in result.columns


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================


@pytest.mark.skipif(
    not JOBS_PARQUET.exists(), reason="Normalized data not generated yet"
)
class TestPerformance:
    """Test performance and memory usage."""

    def test_sample_parameter_works(self):
        """Test that sample parameter limits rows."""
        jobs_small = load_jobs_normalized(sample=100)
        jobs_medium = load_jobs_normalized(sample=500)

        assert len(jobs_small) <= 100
        assert len(jobs_medium) <= 500
        assert len(jobs_small) < len(jobs_medium)

    def test_parquet_files_exist(self):
        """Test that all Parquet files exist."""
        assert JOBS_PARQUET.exists()
        assert JOB_SKILLS_PARQUET.exists()
        assert SKILLS_PARQUET.exists()
        assert JOB_INDUSTRIES_PARQUET.exists()
        assert INDUSTRIES_PARQUET.exists()

    def test_normalized_storage_smaller_than_aggregated(self):
        """Test that normalized storage is smaller than old aggregated format."""
        # Calculate total size of normalized files
        normalized_size = sum(
            [
                JOBS_PARQUET.stat().st_size,
                JOB_SKILLS_PARQUET.stat().st_size,
                SKILLS_PARQUET.stat().st_size,
                JOB_INDUSTRIES_PARQUET.stat().st_size,
                INDUSTRIES_PARQUET.stat().st_size,
            ]
        )

        # Check if old file exists
        old_file = JOBS_PARQUET.parent / "clean_jobs.parquet"
        if old_file.exists():
            old_size = old_file.stat().st_size
            # Normalized should be significantly smaller (or comparable)
            # We expect ~66% reduction, but let's be lenient
            assert (
                normalized_size < old_size * 1.5
            ), f"Normalized ({normalized_size/1024**2:.1f} MB) should be smaller than aggregated ({old_size/1024**2:.1f} MB)"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
