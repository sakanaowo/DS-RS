#!/usr/bin/env python3
"""
Quick script to run the Day 2 data cleaning pipeline.

Usage:
    python run_cleaning.py                 # Process full dataset
    python run_cleaning.py --sample 5000   # Test with 5000 jobs
    python run_cleaning.py --help          # Show help
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from loader import build_and_clean_jobs


def main():
    parser = argparse.ArgumentParser(
        description="Run data cleaning pipeline for job recommendation system"
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=None,
        help="Number of jobs to process (default: all ~124K jobs)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="clean_jobs.parquet",
        help="Output filename (default: clean_jobs.parquet)",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save output (useful for testing)",
    )

    args = parser.parse_args()

    print("=" * 80)
    print("JOB RECOMMENDATION SYSTEM - DATA CLEANING PIPELINE")
    print("=" * 80)
    print(f"\nConfiguration:")
    print(f"  Sample size: {args.sample if args.sample else 'All (~124K jobs)'}")
    print(
        f"  Output file: {args.output if not args.no_save else 'Not saving (test mode)'}"
    )
    print(f"  Save output: {not args.no_save}")
    print()

    try:
        cleaned_df = build_and_clean_jobs(
            sample=args.sample,
            persist=not args.no_save,
            output_name=args.output,
        )

        print("\n" + "=" * 80)
        print("✅ CLEANING COMPLETE")
        print("=" * 80)
        print(f"\nFinal dataset shape: {cleaned_df.shape}")
        print(f"Columns: {len(cleaned_df.columns)}")

        if not args.no_save:
            output_path = PROJECT_ROOT / "data" / "processed" / args.output
            print(f"\n📁 Output saved to: {output_path}")
            print(f"   File size: {output_path.stat().st_size / 1e6:.1f} MB")

        print("\n✨ Next steps:")
        print("   1. Run notebooks/1_data_cleaning.ipynb to see visualizations")
        print("   2. Check reports/data_cleaning_report.md for summary")
        print("   3. Proceed to Day 3: EDA & Visualization")

        return 0

    except Exception as e:
        print(f"\n❌ ERROR: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
