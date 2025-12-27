"""
Automated Pseudo-Labeling for Demo Purposes

Since manual labeling takes 1-2 hours, this script generates pseudo-labels
using heuristics for demonstration and testing purposes.

Heuristics:
1. Title similarity (Jaccard similarity)
2. BM25 score threshold
3. Skills filter compliance
4. Category matching

Note: In production, real manual labels should be used for accurate evaluation.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set


def tokenize(text: str) -> Set[str]:
    """Simple tokenization for title matching."""
    if not text:
        return set()
    # Lowercase, remove special chars, split
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    tokens = set(text.split())
    # Remove very short tokens
    tokens = {t for t in tokens if len(t) >= 2}
    return tokens


def jaccard_similarity(set1: Set[str], set2: Set[str]) -> float:
    """Calculate Jaccard similarity between two sets."""
    if not set1 or not set2:
        return 0.0
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union > 0 else 0.0


def title_similarity(query: str, job_title: str) -> float:
    """Calculate similarity between query and job title."""
    query_tokens = tokenize(query)
    title_tokens = tokenize(job_title)
    return jaccard_similarity(query_tokens, title_tokens)


def is_relevant(query_obj: Dict, result: Dict) -> int:
    """
    Determine if result is relevant using heuristics.
    
    Returns:
        1 = Relevant
        0 = Not relevant
    """
    query = query_obj['query']
    filters = query_obj['filters']
    category = query_obj['category']
    
    job_title = result['title']
    bm25_score = result['bm25_score']
    rank = result['rank']
    
    # Edge case: empty query
    if not query or query.strip() == '':
        # Random results are "not relevant" for empty query
        return 0
    
    # Edge case: nonsense query
    if category == 'edge_cases' and 'notarealjobtitle' in query:
        # Any result for nonsense query is "not relevant"
        return 0
    
    # Calculate title similarity
    sim = title_similarity(query, job_title)
    
    # Heuristic rules
    # 1. High similarity (>0.3) + high rank (top 5) = Relevant
    if sim > 0.3 and rank <= 5:
        return 1
    
    # 2. Medium similarity (>0.2) + high BM25 score (>10) = Relevant
    if sim > 0.2 and bm25_score > 10:
        return 1
    
    # 3. Low similarity (<0.15) = Not relevant
    if sim < 0.15:
        return 0
    
    # 4. Low rank (>7) + low similarity (<0.25) = Not relevant
    if rank > 7 and sim < 0.25:
        return 0
    
    # 5. Skills filter check
    if filters and 'skills' in filters:
        required_skills = set(filters['skills'])
        job_skills = set(result['skills'])
        if not required_skills.issubset(job_skills):
            # Filter violation = Not relevant
            return 0
    
    # 6. For generic queries, top 3 are usually relevant
    if category == 'job_titles' and rank <= 3 and sim > 0.15:
        return 1
    
    # 7. For combined filters, top 5 with filters match = Relevant
    if category == 'combined' and rank <= 5:
        if filters:
            # Check filter compliance (simplified)
            if filters.get('remote_allowed') == True and result['remote_allowed'] == False:
                return 0
            # If passed filters, likely relevant
            return 1
    
    # Default: Medium similarity (0.15-0.3) = Relevant if top 6, else not relevant
    if 0.15 <= sim <= 0.3:
        return 1 if rank <= 6 else 0
    
    # Fallback: Not relevant
    return 0


def generate_pseudo_labels():
    """Generate pseudo-labels for all search results."""
    print("=" * 70)
    print("GENERATING PSEUDO-LABELS (AUTOMATED)")
    print("=" * 70)
    print("\n⚠️  Note: These are heuristic-based labels for demo purposes.")
    print("    In production, use real manual labels for accurate evaluation.\n")
    
    # Load search results
    results_path = Path(__file__).resolve().parents[1] / "data" / "search_results_for_labeling.json"
    with open(results_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    all_results = data['results']
    
    labels = []
    stats = {'total': 0, 'relevant': 0, 'not_relevant': 0}
    
    for query_obj in all_results:
        query_id = query_obj['query_id']
        query = query_obj['query']
        filters = query_obj['filters']
        category = query_obj['category']
        
        print(f"\nQuery {query_id:2d} ({category}): '{query}'")
        
        query_relevant = 0
        for result in query_obj['results']:
            job_id = result['job_id']
            rank = result['rank']
            job_title = result['title']
            
            # Determine relevance
            relevance = is_relevant(query_obj, result)
            
            # Create label entry
            label_entry = {
                "query_id": query_id,
                "query": query,
                "filters": filters,
                "job_id": job_id,
                "rank": rank,
                "relevance": relevance,
                "title": job_title,
                "company": result['company_name'],
                "bm25_score": result['bm25_score'],
                "labeling_method": "automated_heuristic"
            }
            
            labels.append(label_entry)
            
            # Update stats
            stats['total'] += 1
            if relevance == 1:
                stats['relevant'] += 1
                query_relevant += 1
            else:
                stats['not_relevant'] += 1
        
        precision = query_relevant / len(query_obj['results']) * 100
        print(f"  Relevant: {query_relevant}/10 ({precision:.0f}%)")
    
    # Save labels
    output = {
        "metadata": {
            "created_date": "2024-12-27",
            "labeling_method": "automated_heuristic",
            "note": "Pseudo-labels generated for demo purposes. Use manual labels in production.",
            "total_labels": len(labels)
        },
        "labels": labels
    }
    
    labels_path = Path(__file__).resolve().parents[1] / "data" / "relevance_labels.json"
    with open(labels_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total labels: {stats['total']}")
    print(f"Relevant: {stats['relevant']} ({stats['relevant']/stats['total']*100:.1f}%)")
    print(f"Not relevant: {stats['not_relevant']} ({stats['not_relevant']/stats['total']*100:.1f}%)")
    print(f"\n✓ Saved to: {labels_path}")
    print("=" * 70)


if __name__ == "__main__":
    generate_pseudo_labels()
