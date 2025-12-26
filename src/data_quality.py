"""
Smart Data Quality Handler for Job Recommendation System

Handles missing data with intelligent imputation strategies
based on LinkedIn, Indeed, and Netflix best practices.
"""

import re
import pandas as pd
from typing import Dict, List, Optional, Any


class DataQualityHandler:
    """
    Xử lý missing data với các chiến lược thông minh.

    Strategies:
    - Work type: Infer from pay_period or default to Full-time
    - Location: Company city → Remote flag → Default
    - Experience: Extract from job title patterns
    - Skills: Extract from description (optional)
    - Salary: Mark as missing, don't exclude
    """

    # Common patterns for experience level detection
    EXPERIENCE_PATTERNS = {
        "Internship": ["intern", "internship", "trainee"],
        "Entry level": ["junior", "jr.", "jr ", "entry", "associate", "graduate"],
        "Mid-Senior level": ["senior", "sr.", "sr ", "lead", "principal", "staff"],
        "Director": ["director", "vp", "vice president", "head of", "chief", "c-level"],
        "Executive": ["ceo", "cto", "cfo", "coo", "president", "founder"],
    }

    # Work type inference patterns
    WORK_TYPE_PATTERNS = {
        "Contract": ["contract", "contractor", "freelance", "consultant"],
        "Part-time": ["part-time", "part time", "hourly"],
        "Temporary": ["temporary", "temp", "seasonal"],
        "Internship": ["intern", "internship"],
    }

    @classmethod
    def infer_work_type(cls, row: pd.Series) -> str:
        """
        Infer work type from available data.

        Strategy:
        1. Check original work_type column
        2. Check pay_period (hourly → Part-time)
        3. Check title for keywords
        4. Default to Full-time (most common: 80%)
        """
        # Already has formatted value
        if pd.notna(row.get("formatted_work_type")):
            return row["formatted_work_type"]

        # Check original work_type
        if pd.notna(row.get("work_type")):
            return cls._standardize_work_type(str(row["work_type"]))

        # Check pay_period
        pay_period = str(row.get("pay_period", "")).lower()
        if "hourly" in pay_period:
            return "Part-time"
        elif "contractor" in pay_period:
            return "Contract"

        # Check title for patterns
        title = str(row.get("title", "")).lower()
        for work_type, patterns in cls.WORK_TYPE_PATTERNS.items():
            if any(pattern in title for pattern in patterns):
                return work_type

        # Default to most common
        return "Full-time"

    @staticmethod
    def _standardize_work_type(work_type: str) -> str:
        """Standardize work type variations."""
        wt_lower = work_type.lower().strip()

        if "full" in wt_lower:
            return "Full-time"
        elif "part" in wt_lower:
            return "Part-time"
        elif "contract" in wt_lower or "freelance" in wt_lower:
            return "Contract"
        elif "temp" in wt_lower or "seasonal" in wt_lower:
            return "Temporary"
        elif "intern" in wt_lower:
            return "Internship"
        elif "volunteer" in wt_lower:
            return "Volunteer"
        else:
            return "Other"

    @classmethod
    def infer_location(cls, row: pd.Series) -> str:
        """
        Infer location from available data.

        Strategy:
        1. Use existing location if present
        2. Infer from company city/state
        3. Check remote flag
        4. Default to "United States"
        """
        # Already has location
        if pd.notna(row.get("location")) and str(row["location"]).strip():
            return str(row["location"]).strip()

        # Try company location
        if pd.notna(row.get("company_city")) and pd.notna(row.get("company_state")):
            city = str(row["company_city"]).strip()
            state = str(row["company_state"]).strip()
            if city and state:
                return f"{city}, {state}"

        if pd.notna(row.get("company_city")):
            return str(row["company_city"]).strip()

        if pd.notna(row.get("company_state")):
            return str(row["company_state"]).strip()

        # Check remote flag
        if row.get("remote_allowed") == 1:
            return "Remote"

        # Default
        return "United States"

    @classmethod
    def infer_experience_level(cls, row: pd.Series) -> str:
        """
        Infer experience level from job title.

        Strategy:
        1. Use existing if present
        2. Pattern matching on title
        3. Default to Mid-Senior level (most common)
        """
        # Already has value
        if pd.notna(row.get("formatted_experience_level")):
            return row["formatted_experience_level"]

        # Extract from title
        title = str(row.get("title", "")).lower()

        # Check patterns in priority order (most specific first)
        for level, patterns in cls.EXPERIENCE_PATTERNS.items():
            if any(pattern in title for pattern in patterns):
                return level

        # Default to most common
        return "Mid-Senior level"

    @staticmethod
    def mark_salary_availability(row: pd.Series) -> Dict[str, Any]:
        """
        Mark salary data availability without imputing.

        Strategy: Don't impute salary (unreliable), just mark availability
        """
        has_salary = (
            pd.notna(row.get("salary_median"))
            or pd.notna(row.get("min_salary"))
            or pd.notna(row.get("max_salary"))
        )

        return {
            "has_salary_info": has_salary,
            "salary_display": (
                DataQualityHandler._format_salary_display(row)
                if has_salary
                else "Competitive salary"
            ),
        }

    @staticmethod
    def _format_salary_display(row: pd.Series) -> str:
        """Format salary for display."""
        if pd.notna(row.get("min_salary")) and pd.notna(row.get("max_salary")):
            return f"${row['min_salary']:,.0f} - ${row['max_salary']:,.0f}"
        elif pd.notna(row.get("salary_median")):
            return f"${row['salary_median']:,.0f}"
        elif pd.notna(row.get("min_salary")):
            return f"From ${row['min_salary']:,.0f}"
        elif pd.notna(row.get("max_salary")):
            return f"Up to ${row['max_salary']:,.0f}"
        return "Competitive salary"

    @classmethod
    def apply_all_strategies(cls, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply all data quality strategies to dataframe.

        Args:
            df: Raw job dataframe

        Returns:
            Enhanced dataframe with imputed values
        """
        df = df.copy()

        print("Applying data quality strategies...")

        # 1. Work type
        missing_work_type = df["formatted_work_type"].isna().sum()
        if missing_work_type > 0:
            print(f"  - Inferring work type for {missing_work_type:,} jobs...")
            df["formatted_work_type"] = df.apply(cls.infer_work_type, axis=1)

        # 2. Location
        missing_location = df["location"].isna().sum()
        if missing_location > 0:
            print(f"  - Inferring location for {missing_location:,} jobs...")
            df["location"] = df.apply(cls.infer_location, axis=1)

        # 3. Experience level
        missing_exp = df["formatted_experience_level"].isna().sum()
        if missing_exp > 0:
            print(f"  - Inferring experience level for {missing_exp:,} jobs...")
            df["formatted_experience_level"] = df.apply(
                cls.infer_experience_level, axis=1
            )

        # 4. Salary availability (don't impute, just mark)
        print(f"  - Marking salary availability...")
        salary_info = df.apply(
            cls.mark_salary_availability, axis=1, result_type="expand"
        )
        df["has_salary_info"] = salary_info["has_salary_info"]
        df["salary_display"] = salary_info["salary_display"]

        print("✓ Data quality strategies applied!")
        return df


def get_data_quality_report(df: pd.DataFrame) -> Dict:
    """
    Generate data quality report.

    Args:
        df: Dataframe to analyze

    Returns:
        Dictionary with coverage stats
    """
    total = len(df)

    # Check which salary columns are available
    salary_coverage = 0.0
    if "has_salary_info" in df.columns:
        salary_coverage = df["has_salary_info"].sum() / total * 100
    elif "salary_median" in df.columns:
        salary_coverage = df["salary_median"].notna().sum() / total * 100

    return {
        "total_jobs": total,
        "coverage": {
            "title": (df["title"].notna().sum() / total * 100),
            "location": (df["location"].notna().sum() / total * 100),
            "work_type": (df["formatted_work_type"].notna().sum() / total * 100),
            "experience": (
                df["formatted_experience_level"].notna().sum() / total * 100
            ),
            "salary": salary_coverage,
            "skills": (
                (df["skills"].notna().sum() / total * 100)
                if "skills" in df.columns
                else 0.0
            ),
            "industries": (
                (df["industries"].notna().sum() / total * 100)
                if "industries" in df.columns
                else 0.0
            ),
            "remote_flag": (
                (df["remote_allowed"].notna().sum() / total * 100)
                if "remote_allowed" in df.columns
                else 0.0
            ),
        },
        "distribution": {
            "work_types": df["formatted_work_type"].value_counts().to_dict(),
            "experience_levels": df["formatted_experience_level"]
            .value_counts()
            .to_dict(),
            "top_locations": df["location"].value_counts().head(10).to_dict(),
        },
    }
