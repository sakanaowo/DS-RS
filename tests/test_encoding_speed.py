#!/usr/bin/env python3
"""
Test script to verify encoding performance

This tests how long it takes to encode embeddings
"""

import time
import sys
from src.semantic_search import SemanticJobSearch

print("=" * 60)
print("SEMANTIC SEARCH PERFORMANCE TEST")
print("=" * 60)
print()

print("Testing encoding speed for different dataset sizes...")
print()

# Test 1: Small sample (1K jobs)
print("TEST 1: 1,000 jobs")
print("-" * 40)
start = time.time()
searcher = SemanticJobSearch(sample_size=1000, verbose=True)
searcher.load_model()
searcher.load_data()
searcher.encode_jobs(force_recompute=True)
elapsed = time.time() - start
print(f"✓ Completed in {elapsed:.1f}s")
print(f"  Speed: {1000/elapsed:.0f} jobs/sec")
print()

# Test 2: Medium sample (10K jobs)
print("TEST 2: 10,000 jobs")
print("-" * 40)
start = time.time()
searcher = SemanticJobSearch(sample_size=10000, verbose=True)
searcher.load_model()
searcher.load_data()
searcher.encode_jobs(force_recompute=True)
elapsed = time.time() - start
print(f"✓ Completed in {elapsed:.1f}s")
print(f"  Speed: {10000/elapsed:.0f} jobs/sec")
print(f"  Estimated for 50K: {elapsed*5:.1f}s ({elapsed*5/60:.1f} min)")
print()

# Calculate estimates
print("=" * 60)
print("ESTIMATES FOR FULL DATASET")
print("=" * 60)
speed = 10000 / elapsed  # jobs per second
print(f"Encoding speed: ~{speed:.0f} jobs/second")
print()
print(f"50,000 jobs:  ~{50000/speed:.0f}s  ({50000/speed/60:.1f} min)")
print(f"123,000 jobs: ~{123000/speed:.0f}s ({123000/speed/60:.1f} min)")
print()
print("💡 TIP: Using BM25's 50K sample instead of full 123K")
print("    saves ~{:.0f} minutes!".format((123000-50000)/speed/60))
