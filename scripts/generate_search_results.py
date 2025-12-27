"""
Generate search results for all test queries.

This script:
1. Loads test queries from data/test_queries.json
2. Runs BM25 search for each query
3. Gets top-10 results for each
4. Saves results to data/search_results_for_labeling.json

Output format:
{
  "query_id": 1,
  "query": "Software Engineer",
  "filters": null,
  "results": [
    {
      "rank": 1,
      "job_id": 12345,
      "title": "Senior Software Engineer",
      "company_name": "Tech Corp",
      "city": "San Francisco",
      "state": "CA",
      "bm25_score": 45.23,
      "description_snippet": "First 200 chars...",
      "skills": ["IT", "ENG"],
      "industries": ["Technology"]
    },
    ...
  ]
}
"""

import json
import sys
from pathlib import Path
from typing import List, Dict

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.bm25_search import BM25JobSearch


def truncate_text(text: str, max_length: int = 200) -> str:
    """Truncate text to max_length characters."""
    if not text or len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def generate_search_results():
    """Generate search results for all test queries."""
    print("=" * 70)
    print("GENERATING SEARCH RESULTS FOR EVALUATION")
    print("=" * 70)
    
    # Load test queries
    queries_path = Path(__file__).resolve().parents[1] / "data" / "test_queries.json"
    with open(queries_path, 'r') as f:
        queries_data = json.load(f)
    
    queries = queries_data['queries']
    print(f"\n✓ Loaded {len(queries)} test queries")
    
    # Initialize BM25 search
    print("\nInitializing BM25 search engine...")
    searcher = BM25JobSearch(verbose=False)
    searcher.load_data()
    print("✓ Search engine ready")
    
    # Generate results for each query
    all_results = []
    
    print(f"\nGenerating search results (top-10 for each query)...")
    print("-" * 70)
    
    for query_obj in queries:
        query_id = query_obj['id']
        query = query_obj['query']
        filters = query_obj['filters']
        category = query_obj['category']
        
        print(f"\nQuery {query_id:2d} ({category}): '{query}'")
        if filters:
            print(f"  Filters: {filters}")
        
        # Run search
        results_df = searcher.search(query, top_k=10, filters=filters)
        
        # Format results
        results_list = []
        for rank, (idx, row) in enumerate(results_df.iterrows(), start=1):
            job_id = int(row['job_id'])
            
            # Get skills and industries
            skills = searcher.get_job_skills(job_id)
            industries = searcher.get_job_industries(job_id)
            
            # Handle NA values properly
            import pandas as pd
            
            result = {
                "rank": rank,
                "job_id": job_id,
                "title": str(row['title']),
                "company_name": str(row['company_name']),
                "city": str(row.get('city', 'N/A')) if pd.notna(row.get('city')) else 'N/A',
                "state": str(row.get('state', 'N/A')) if pd.notna(row.get('state')) else 'N/A',
                "country": str(row.get('country', 'N/A')) if pd.notna(row.get('country')) else 'N/A',
                "work_type": str(row.get('work_type', 'N/A')) if pd.notna(row.get('work_type')) else 'N/A',
                "remote_allowed": bool(row.get('remote_allowed', False)) if pd.notna(row.get('remote_allowed')) else False,
                "bm25_score": float(row['bm25_score']),
                "description_snippet": truncate_text(row.get('description', ''), 200),
                "skills": skills,
                "industries": industries[:3]  # Top 3 industries
            }
            results_list.append(result)
        
        query_result = {
            "query_id": query_id,
            "query": query,
            "filters": filters,
            "category": category,
            "description": query_obj['description'],
            "num_results": len(results_list),
            "results": results_list
        }
        
        all_results.append(query_result)
        
        print(f"  → Found {len(results_list)} results")
    
    # Save to file
    output_path = Path(__file__).resolve().parents[1] / "data" / "search_results_for_labeling.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            "metadata": {
                "created_date": "2024-12-27",
                "total_queries": len(all_results),
                "total_results": sum(len(q['results']) for q in all_results),
                "search_engine": "BM25JobSearch",
                "top_k": 10
            },
            "results": all_results
        }, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 70)
    print(f"✓ Saved {len(all_results)} queries with results")
    print(f"✓ Total results to label: {sum(len(q['results']) for q in all_results)}")
    print(f"✓ Output: {output_path}")
    print("=" * 70)


if __name__ == "__main__":
    generate_search_results()
