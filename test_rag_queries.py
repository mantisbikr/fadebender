#!/usr/bin/env python3
"""
Comprehensive RAG Test Query Suite
Test various query types across all RAG modes (assistants, hybrid, vertex)
"""

import os
import json
import time
import requests
from typing import Dict, Any, List

# Comprehensive test queries covering different use cases
TEST_QUERIES = [
    # === Simple Factual Queries ===
    {
        "category": "Simple Factual",
        "query": "how many reverb presets are available?",
        "expected": "Should return specific count (52 reverb presets)",
        "user_id": "test-factual-1"
    },
    {
        "category": "Simple Factual",
        "query": "what parameters can I control on the compressor?",
        "expected": "List of compressor parameters",
        "user_id": "test-factual-2"
    },
    {
        "category": "Simple Factual",
        "query": "how do I load a reverb preset on track 1?",
        "expected": "Command syntax and example",
        "user_id": "test-factual-3"
    },

    # === Purpose-Based Queries ===
    {
        "category": "Purpose-Based",
        "query": "what reverb presets are best for vocals?",
        "expected": "Reverb presets suitable for vocal processing",
        "user_id": "test-purpose-vocals"
    },
    {
        "category": "Purpose-Based",
        "query": "which delay presets work well for drums?",
        "expected": "Delay presets suitable for drums",
        "user_id": "test-purpose-drums"
    },
    {
        "category": "Purpose-Based",
        "query": "recommend reverb presets for acoustic guitar",
        "expected": "Reverb presets suitable for acoustic guitar",
        "user_id": "test-purpose-guitar"
    },
    {
        "category": "Purpose-Based",
        "query": "what compressor settings are good for mixing bass?",
        "expected": "Compressor presets/settings for bass",
        "user_id": "test-purpose-bass"
    },

    # === Parameter-Constrained Queries ===
    {
        "category": "Parameter-Constrained",
        "query": "show me reverb presets with decay time less than 1 second",
        "expected": "Reverb presets filtered by decay time < 1s",
        "user_id": "test-param-decay"
    },
    {
        "category": "Parameter-Constrained",
        "query": "which reverb presets have large room sizes?",
        "expected": "Reverb presets with room size > certain threshold",
        "user_id": "test-param-roomsize"
    },
    {
        "category": "Parameter-Constrained",
        "query": "find delay presets with feedback under 50%",
        "expected": "Delay presets filtered by feedback parameter",
        "user_id": "test-param-feedback"
    },
    {
        "category": "Parameter-Constrained",
        "query": "what compressor presets have a ratio of 4:1 or higher?",
        "expected": "Compressor presets filtered by ratio",
        "user_id": "test-param-ratio"
    },

    # === Comparison Queries ===
    {
        "category": "Comparison",
        "query": "compare Cathedral and Church reverb presets",
        "expected": "Detailed parameter comparison with key differences",
        "user_id": "test-compare-1"
    },
    {
        "category": "Comparison",
        "query": "what's the difference between Tape Delay and Filter Delay?",
        "expected": "Technical differences and use cases",
        "user_id": "test-compare-2"
    },
    {
        "category": "Comparison",
        "query": "compare Plate and Hall reverb types",
        "expected": "Differences in reverb types and characteristics",
        "user_id": "test-compare-3"
    },

    # === Complex List Queries ===
    {
        "category": "Complete List",
        "query": "list all reverb presets with their IDs",
        "expected": "All 52 reverb presets with preset IDs",
        "user_id": "test-list-reverb"
    },
    {
        "category": "Complete List",
        "query": "show me every delay preset available",
        "expected": "Complete list of all delay presets",
        "user_id": "test-list-delay"
    },
    {
        "category": "Complete List",
        "query": "list all compressor presets",
        "expected": "Complete list of compressor presets",
        "user_id": "test-list-comp"
    },

    # === Semantic Understanding Queries ===
    {
        "category": "Semantic Understanding",
        "query": "I need a subtle reverb for intimate vocals, what should I use?",
        "expected": "Context-aware recommendation based on 'subtle' and 'intimate'",
        "user_id": "test-semantic-1"
    },
    {
        "category": "Semantic Understanding",
        "query": "suggest a big, spacious reverb for orchestral strings",
        "expected": "Large hall/cathedral type reverbs",
        "user_id": "test-semantic-2"
    },
    {
        "category": "Semantic Understanding",
        "query": "what delay creates a vintage tape echo sound?",
        "expected": "Tape delay presets with character description",
        "user_id": "test-semantic-3"
    },

    # === Workflow/Command Queries ===
    {
        "category": "Workflow",
        "query": "how do I automate the reverb decay time?",
        "expected": "Instructions for parameter automation",
        "user_id": "test-workflow-1"
    },
    {
        "category": "Workflow",
        "query": "can I load multiple effects on the same track?",
        "expected": "Device chain explanation",
        "user_id": "test-workflow-2"
    },
    {
        "category": "Workflow",
        "query": "what's the command to set send level to a return track?",
        "expected": "Command syntax for send levels",
        "user_id": "test-workflow-3"
    },
]


def test_query(query_info: Dict[str, str], base_url: str = "http://localhost:8722") -> Dict[str, Any]:
    """
    Test a single query and return detailed metrics

    Args:
        query_info: Dictionary with query, category, expected, user_id
        base_url: Server base URL

    Returns:
        Dictionary with timing, response, and metadata
    """
    url = f"{base_url}/help"
    payload = {
        "query": query_info["query"],
        "context": {"userId": query_info["user_id"]}
    }

    start_time = time.time()
    try:
        response = requests.post(url, json=payload, timeout=60)
        total_time = time.time() - start_time

        if response.status_code != 200:
            return {
                "ok": False,
                "error": f"HTTP {response.status_code}",
                "total_time": total_time,
                "category": query_info["category"],
                "query": query_info["query"]
            }

        data = response.json()

        return {
            "ok": data.get("ok", False),
            "category": query_info["category"],
            "query": query_info["query"],
            "expected": query_info["expected"],
            "mode": data.get("mode"),
            "rag_mode": data.get("rag_mode"),
            "timing": data.get("timing", {}),
            "total_time": total_time,
            "model_complexity": data.get("model_complexity"),
            "answer": data.get("answer", ""),
            "answer_length": len(data.get("answer", "")),
            "sources_count": len(data.get("sources", [])),
            "thread_id": data.get("thread_id")
        }
    except requests.exceptions.Timeout:
        return {
            "ok": False,
            "error": "Request timeout (60s)",
            "total_time": 60.0,
            "category": query_info["category"],
            "query": query_info["query"]
        }
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "total_time": time.time() - start_time,
            "category": query_info["category"],
            "query": query_info["query"]
        }


def run_comprehensive_tests(base_url: str = "http://localhost:8722",
                           output_file: str = None,
                           verbose: bool = True) -> Dict[str, List[Dict]]:
    """
    Run all test queries and collect results

    Args:
        base_url: Server base URL
        output_file: Optional JSON file to save results
        verbose: Print progress to console

    Returns:
        Dictionary with results grouped by category
    """
    print("=" * 80)
    print("COMPREHENSIVE RAG TEST SUITE")
    print("=" * 80)
    print(f"Testing {len(TEST_QUERIES)} queries across {len(set(q['category'] for q in TEST_QUERIES))} categories")
    print()

    results_by_category = {}
    all_results = []

    for i, query_info in enumerate(TEST_QUERIES, 1):
        category = query_info["category"]

        if verbose:
            print(f"[{i}/{len(TEST_QUERIES)}] {category}: {query_info['query'][:60]}...")

        result = test_query(query_info, base_url)
        all_results.append(result)

        # Group by category
        if category not in results_by_category:
            results_by_category[category] = []
        results_by_category[category].append(result)

        if verbose:
            if result["ok"]:
                print(f"  ✓ {result['total_time']:.2f}s | {result['answer_length']} chars | {result.get('rag_mode', 'N/A')}")
            else:
                print(f"  ✗ ERROR: {result.get('error', 'Unknown error')}")

        # Brief pause between queries to avoid rate limits
        time.sleep(1)

    # Calculate statistics
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    for category in sorted(results_by_category.keys()):
        category_results = results_by_category[category]
        successful = [r for r in category_results if r["ok"]]
        failed = [r for r in category_results if not r["ok"]]

        print(f"\n{category}:")
        print(f"  Total: {len(category_results)} | Success: {len(successful)} | Failed: {len(failed)}")

        if successful:
            avg_time = sum(r["total_time"] for r in successful) / len(successful)
            avg_length = sum(r["answer_length"] for r in successful) / len(successful)
            print(f"  Avg Time: {avg_time:.2f}s | Avg Length: {avg_length:.0f} chars")

    # Overall statistics
    successful = [r for r in all_results if r["ok"]]
    failed = [r for r in all_results if not r["ok"]]

    print(f"\n{'=' * 80}")
    print("OVERALL STATISTICS")
    print(f"{'=' * 80}")
    print(f"Total Queries: {len(all_results)}")
    print(f"Successful: {len(successful)} ({len(successful)/len(all_results)*100:.1f}%)")
    print(f"Failed: {len(failed)} ({len(failed)/len(all_results)*100:.1f}%)")

    if successful:
        avg_time = sum(r["total_time"] for r in successful) / len(successful)
        min_time = min(r["total_time"] for r in successful)
        max_time = max(r["total_time"] for r in successful)
        print(f"\nTiming Statistics:")
        print(f"  Average: {avg_time:.2f}s")
        print(f"  Min: {min_time:.2f}s")
        print(f"  Max: {max_time:.2f}s")

    # Save results if output file specified
    if output_file:
        output_data = {
            "test_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_queries": len(all_results),
            "successful": len(successful),
            "failed": len(failed),
            "results_by_category": results_by_category,
            "all_results": all_results
        }

        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)

        print(f"\nResults saved to: {output_file}")

    return results_by_category


def compare_rag_modes(assistants_file: str, hybrid_file: str, vertex_file: str = None):
    """
    Compare results across different RAG modes

    Args:
        assistants_file: JSON results from assistants mode
        hybrid_file: JSON results from hybrid mode
        vertex_file: Optional JSON results from vertex mode
    """
    print("=" * 80)
    print("RAG MODE COMPARISON")
    print("=" * 80)

    with open(assistants_file) as f:
        assistants_data = json.load(f)

    with open(hybrid_file) as f:
        hybrid_data = json.load(f)

    vertex_data = None
    if vertex_file and os.path.exists(vertex_file):
        with open(vertex_file) as f:
            vertex_data = json.load(f)

    # Compare by category
    print("\nComparison by Category:")
    print(f"{'Category':<25} {'Assistants':<15} {'Hybrid':<15} {'Vertex':<15}")
    print("-" * 80)

    for category in assistants_data["results_by_category"].keys():
        asst_results = assistants_data["results_by_category"][category]
        hybrid_results = hybrid_data["results_by_category"][category]

        asst_avg = sum(r["total_time"] for r in asst_results if r["ok"]) / len([r for r in asst_results if r["ok"]])
        hybrid_avg = sum(r["total_time"] for r in hybrid_results if r["ok"]) / len([r for r in hybrid_results if r["ok"]])

        vertex_avg = "N/A"
        if vertex_data:
            vertex_results = vertex_data["results_by_category"].get(category, [])
            if vertex_results:
                vertex_avg = f"{sum(r['total_time'] for r in vertex_results if r['ok']) / len([r for r in vertex_results if r['ok']]):.2f}s"

        print(f"{category:<25} {asst_avg:>6.2f}s         {hybrid_avg:>6.2f}s         {vertex_avg:>10}")


if __name__ == "__main__":
    import sys

    # Get RAG mode from environment or command line
    rag_mode = os.getenv("RAG_MODE", "assistants")
    if len(sys.argv) > 1:
        rag_mode = sys.argv[1]

    print(f"Testing RAG mode: {rag_mode}")
    print(f"Ensure RAG_MODE={rag_mode} is set in .env and server is running")
    print()

    # Run tests and save to mode-specific file
    output_file = f"rag_test_results_{rag_mode}.json"
    results = run_comprehensive_tests(
        base_url="http://localhost:8722",
        output_file=output_file,
        verbose=True
    )

    print(f"\nTest complete! Results saved to {output_file}")
    print("\nTo compare modes later:")
    print("  python test_rag_queries.py compare")
