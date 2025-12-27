#!/usr/bin/env python3
"""Quick test to verify semantic search loads 50K jobs"""

from src.semantic_search import SemanticJobSearch

print("Testing semantic search fix...")
print()

searcher = SemanticJobSearch(sample_size=None, verbose=True)
print("1. Created searcher")

searcher.load_data()
print(f"2. Loaded {len(searcher.jobs):,} jobs")
print()

if len(searcher.jobs) == 50000:
    print("✅ SUCCESS: Matches BM25's 50K sample!")
elif len(searcher.jobs) == 123842:
    print("❌ ERROR: Still loading full 123K dataset")
    print("   Fix did not apply correctly")
else:
    print(f"⚠️  Loaded {len(searcher.jobs):,} jobs (unexpected)")

print()
print("Sample job IDs:", searcher.jobs['job_id'].head(3).tolist())
