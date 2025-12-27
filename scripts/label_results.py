"""
Manual Labeling Interface for Search Results

This script provides a simple CLI interface to label search results as relevant/not relevant.

Usage:
    python scripts/label_results.py

Features:
- Load search results from data/search_results_for_labeling.json
- Display job info clearly
- Allow binary rating: relevant (1) or not relevant (0)
- Save labels to data/relevance_labels.json
- Resume from last position if interrupted
- Show progress

Rating Guidelines:
- Relevant (1): Job title matches query intent, skills/requirements align
- Not Relevant (0): Job title doesn't match, wrong category, or misleading

Examples:
- Query: "Software Engineer" → "Senior Software Engineer" = RELEVANT
- Query: "Software Engineer" → "Software Sales Engineer" = NOT RELEVANT (sales, not dev)
- Query: "Data Scientist" → "Data Analyst" = MARGINAL (analyst ≠ scientist, but close)
- Query: "Marketing Manager" → "Marketing Coordinator" = NOT RELEVANT (coordinator ≠ manager)
"""

import json
import sys
from pathlib import Path
from typing import Dict, List


def load_search_results():
    """Load search results to label."""
    results_path = (
        Path(__file__).resolve().parents[1]
        / "data"
        / "search_results_for_labeling.json"
    )
    with open(results_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["results"]


def load_existing_labels():
    """Load existing labels if any."""
    labels_path = Path(__file__).resolve().parents[1] / "data" / "relevance_labels.json"
    if labels_path.exists():
        with open(labels_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"labels": []}


def save_labels(labels_data):
    """Save labels to file."""
    labels_path = Path(__file__).resolve().parents[1] / "data" / "relevance_labels.json"
    with open(labels_path, "w", encoding="utf-8") as f:
        json.dump(labels_data, f, indent=2, ensure_ascii=False)


def get_labeled_set(labels_data):
    """Get set of (query_id, job_id) already labeled."""
    labeled = set()
    for label in labels_data["labels"]:
        labeled.add((label["query_id"], label["job_id"]))
    return labeled


def display_job(result: Dict, rank: int):
    """Display job information clearly."""
    print(f"\n{'='*70}")
    print(f"Rank #{rank} | BM25 Score: {result['bm25_score']:.2f}")
    print(f"{'='*70}")
    print(f"Title:   {result['title']}")
    print(f"Company: {result['company_name']}")
    print(f"Location: {result['city']}, {result['state']}, {result['country']}")
    print(f"Work Type: {result['work_type']} | Remote: {result['remote_allowed']}")
    print(f"Skills: {', '.join(result['skills'][:5])}")
    print(f"Industries: {', '.join(result['industries'])}")
    print(f"\nDescription:")
    print(f"  {result['description_snippet']}")
    print(f"{'='*70}")


def label_results():
    """Main labeling interface."""
    print("\n" + "=" * 70)
    print(" " * 20 + "MANUAL LABELING INTERFACE")
    print("=" * 70)

    # Load data
    print("\nLoading data...")
    all_results = load_search_results()
    labels_data = load_existing_labels()

    # Get already labeled
    labeled_set = get_labeled_set(labels_data)

    total_to_label = sum(len(q["results"]) for q in all_results)
    already_labeled = len(labeled_set)

    print(f"✓ Total results: {total_to_label}")
    print(f"✓ Already labeled: {already_labeled}")
    print(f"✓ Remaining: {total_to_label - already_labeled}")

    if already_labeled == total_to_label:
        print("\n✓ All results have been labeled!")
        return

    print("\n" + "=" * 70)
    print("LABELING GUIDELINES:")
    print("=" * 70)
    print("  1 = RELEVANT   : Job matches query intent")
    print("  0 = NOT RELEVANT : Job doesn't match query")
    print("\n  Commands:")
    print("    's' = Skip this result")
    print("    'q' = Quit and save progress")
    print("=" * 70)

    labeled_count = 0

    try:
        for query_obj in all_results:
            query_id = query_obj["query_id"]
            query = query_obj["query"]
            filters = query_obj["filters"]
            category = query_obj["category"]
            results = query_obj["results"]

            print(f"\n\n{'#'*70}")
            print(f"Query {query_id}/20 ({category})")
            print(f"{'#'*70}")
            print(f"Query: '{query}'")
            if filters:
                print(f"Filters: {filters}")
            print(f"Results: {len(results)}")

            for result in results:
                job_id = result["job_id"]
                rank = result["rank"]

                # Skip if already labeled
                if (query_id, job_id) in labeled_set:
                    continue

                # Display job
                display_job(result, rank)

                # Get label
                while True:
                    label_input = (
                        input(f"\nIs this RELEVANT? (1=yes, 0=no, s=skip, q=quit): ")
                        .strip()
                        .lower()
                    )

                    if label_input == "q":
                        print("\n✓ Quitting and saving progress...")
                        save_labels(labels_data)
                        print(f"✓ Saved {len(labels_data['labels'])} labels")
                        return

                    if label_input == "s":
                        print("⊳ Skipped")
                        break

                    if label_input in ["0", "1"]:
                        relevance = int(label_input)

                        # Save label
                        label_entry = {
                            "query_id": query_id,
                            "query": query,
                            "filters": filters,
                            "job_id": job_id,
                            "rank": rank,
                            "relevance": relevance,
                            "title": result["title"],
                            "company": result["company_name"],
                        }

                        labels_data["labels"].append(label_entry)
                        labeled_set.add((query_id, job_id))
                        labeled_count += 1

                        # Auto-save every 10 labels
                        if labeled_count % 10 == 0:
                            save_labels(labels_data)
                            print(f"\n✓ Auto-saved ({labeled_count} labels)")

                        break

                    print("Invalid input. Please enter 1, 0, s, or q.")

        # Final save
        save_labels(labels_data)
        print("\n" + "=" * 70)
        print(f"✓ LABELING COMPLETE!")
        print(f"✓ Total labels: {len(labels_data['labels'])}")
        print(f"✓ Saved to: data/relevance_labels.json")
        print("=" * 70)

    except KeyboardInterrupt:
        print("\n\n✓ Interrupted. Saving progress...")
        save_labels(labels_data)
        print(f"✓ Saved {len(labels_data['labels'])} labels")


def show_stats():
    """Show labeling statistics."""
    labels_data = load_existing_labels()
    labels = labels_data["labels"]

    if not labels:
        print("No labels found.")
        return

    total = len(labels)
    relevant = sum(1 for l in labels if l["relevance"] == 1)
    not_relevant = total - relevant

    print("\n" + "=" * 70)
    print("LABELING STATISTICS")
    print("=" * 70)
    print(f"Total labels: {total}")
    print(f"Relevant: {relevant} ({relevant/total*100:.1f}%)")
    print(f"Not relevant: {not_relevant} ({not_relevant/total*100:.1f}%)")

    # By query
    by_query = {}
    for label in labels:
        qid = label["query_id"]
        if qid not in by_query:
            by_query[qid] = {"total": 0, "relevant": 0}
        by_query[qid]["total"] += 1
        if label["relevance"] == 1:
            by_query[qid]["relevant"] += 1

    print(f"\nBy query:")
    for qid in sorted(by_query.keys()):
        stats = by_query[qid]
        precision = stats["relevant"] / stats["total"] * 100
        print(
            f"  Query {qid:2d}: {stats['relevant']:2d}/{stats['total']:2d} relevant ({precision:.0f}%)"
        )

    print("=" * 70)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "stats":
        show_stats()
    else:
        label_results()
