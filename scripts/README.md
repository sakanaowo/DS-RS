# Scripts Directory

This directory contains utility scripts for the Intelligent Job Matching System project.

## Available Scripts

### `run_cleaning.py`

Execute the Day 2 data cleaning pipeline from command line.

**Usage:**

```bash
# Test with sample
python scripts/run_cleaning.py --sample 5000

# Process full dataset
python scripts/run_cleaning.py

# Show help
python scripts/run_cleaning.py --help
```

**Options:**

- `--sample N`: Process only N jobs (default: all ~124K)
- `--output FILE`: Output filename (default: clean_jobs.parquet)
- `--no-save`: Don't save output (test mode)

**Example:**

```bash
# Quick test
python scripts/run_cleaning.py --sample 1000 --no-save

# Save as CSV instead of parquet
python scripts/run_cleaning.py --output clean_jobs.csv
```

## Guidelines

- Scripts in this directory are **utilities**, not core modules
- Core modules belong in `src/` directory
- Scripts should import from `src/` and provide CLI interfaces
- All scripts should have proper argparse help documentation
