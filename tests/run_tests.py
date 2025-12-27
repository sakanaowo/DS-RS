"""
Simple test runner for normalized data pipeline

Run this to verify the refactored loader works correctly.
"""

import sys
from pathlib import Path

# Add parent directory to path so we can import from src
sys.path.insert(0, str(Path(__file__).parents[1]))


def test_parse_location():
    """Test location parsing."""
    from src.loader import parse_location

    print("Testing parse_location()...")
    test_cases = [
        (
            "San Francisco, CA, United States",
            {"city": "San Francisco", "state": "CA", "country": "United States"},
        ),
        (
            "New York, NY",
            {"city": "New York", "state": "NY", "country": "United States"},
        ),
        ("Remote", {"city": "Remote", "state": "", "country": ""}),
        ("", {"city": "", "state": "", "country": ""}),
    ]

    for loc_str, expected in test_cases:
        result = parse_location(loc_str)
        assert result == expected, f"Failed for '{loc_str}': {result} != {expected}"

    print("  ✓ All location parsing tests passed")


def test_normalize_salary():
    """Test salary normalization."""
    from src.loader import normalize_salary_to_yearly
    import pandas as pd

    print("Testing normalize_salary_to_yearly()...")

    # Test yearly
    row = pd.Series({"min_salary": 80000, "max_salary": 120000, "pay_period": "YEARLY"})
    result = normalize_salary_to_yearly(row)
    assert result == 100000, f"Yearly test failed: {result}"

    # Test hourly
    row = pd.Series({"min_salary": 25, "max_salary": 35, "pay_period": "HOURLY"})
    result = normalize_salary_to_yearly(row)
    assert result == 30 * 2080, f"Hourly test failed: {result}"

    # Test missing
    row = pd.Series({"min_salary": None, "max_salary": 100000, "pay_period": "YEARLY"})
    result = normalize_salary_to_yearly(row)
    assert result is None, f"Missing test failed: {result}"

    print("  ✓ All salary normalization tests passed")


def test_load_functions():
    """Test data loading functions."""
    from src.loader import (
        load_jobs_normalized,
        load_job_skills,
        load_skills,
        get_jobs_with_skills,
    )

    print("Testing data loading functions...")

    # Test jobs
    jobs = load_jobs_normalized(sample=100)
    assert len(jobs) > 0, "No jobs loaded"
    assert jobs["job_id"].is_unique, "job_id not unique"
    assert "city" in jobs.columns, "Missing city column"
    print(f"  ✓ Loaded {len(jobs)} jobs")

    # Test skills
    job_skills = load_job_skills()
    assert len(job_skills) > 0, "No job_skills loaded"
    print(f"  ✓ Loaded {len(job_skills):,} job-skill relationships")

    skills = load_skills()
    assert len(skills) > 0, "No skills loaded"
    print(f"  ✓ Loaded {len(skills)} skills")

    # Test display function
    sample_ids = jobs["job_id"].head(5).tolist()
    jobs_display = get_jobs_with_skills(job_ids=sample_ids)
    assert "skills" in jobs_display.columns, "Missing skills column"
    print(f"  ✓ Created display format with skills")


def test_data_integrity():
    """Test data integrity constraints."""
    from src.loader import (
        load_job_skills,
        load_skills,
        load_job_industries,
        load_industries,
    )

    print("Testing data integrity...")

    # Foreign key: job_skills → skills
    job_skills = load_job_skills()
    skills = load_skills()
    invalid_skills = set(job_skills["skill_abr"]) - set(skills["skill_abr"])
    assert len(invalid_skills) == 0, f"Invalid skills: {invalid_skills}"
    print("  ✓ All skills have valid foreign keys")

    # Foreign key: job_industries → industries
    job_industries = load_job_industries()
    industries = load_industries()
    invalid_industries = set(job_industries["industry_id"]) - set(
        industries["industry_id"]
    )
    assert len(invalid_industries) == 0, f"Invalid industries: {invalid_industries}"
    print("  ✓ All industries have valid foreign keys")


def main():
    """Run all tests."""
    print("=" * 60)
    print("RUNNING NORMALIZED DATA PIPELINE TESTS")
    print("=" * 60)
    print()

    try:
        test_parse_location()
        print()

        test_normalize_salary()
        print()

        test_load_functions()
        print()

        test_data_integrity()
        print()

        print("=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)
        return 0

    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("\nRun this first to generate normalized data:")
        print("  jupyter notebook notebooks/day1_data_pipeline_v2.ipynb")
        return 1

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
