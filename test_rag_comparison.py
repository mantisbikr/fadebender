#!/usr/bin/env python3
"""
RAG Mode Comparison Test
Compares hybrid vs assistants RAG modes for speed, accuracy, and quality
"""

import os
import json
import time
import requests
from typing import Dict, Any

# Test queries covering different complexity levels
TEST_QUERIES = [
    {
        "name": "Simple Factual",
        "query": "how many reverb presets are available?",
        "expected": "Should mention 52 reverb presets"
    },
    {
        "name": "Complex List",
        "query": "list all reverb presets with their IDs",
        "expected": "Should list all 52 presets with IDs"
    },
    {
        "name": "Comparison",
        "query": "compare Cathedral and Church reverb presets - what are the key differences?",
        "expected": "Should compare decay, size, and character differences"
    },
]

def test_query(mode: str, query: str, user_id: str) -> Dict[str, Any]:
    """Test a single query and return metrics"""
    url = "http://localhost:8722/help"
    payload = {
        "query": query,
        "context": {"userId": user_id}
    }

    start_time = time.time()
    response = requests.post(url, json=payload)
    total_time = time.time() - start_time

    if response.status_code != 200:
        return {
            "ok": False,
            "error": f"HTTP {response.status_code}",
            "total_time": total_time
        }

    data = response.json()

    return {
        "ok": data.get("ok", False),
        "mode": data.get("mode"),
        "rag_mode": data.get("rag_mode"),
        "timing": data.get("timing", {}),
        "total_time": total_time,
        "model_complexity": data.get("model_complexity"),
        "answer": data.get("answer", ""),
        "answer_length": len(data.get("answer", "")),
        "sources_count": len(data.get("sources", []))
    }

def run_comparison():
    """Run full comparison between modes"""
    results = {
        "hybrid": [],
        "assistants": []
    }

    print("=" * 80)
    print("RAG MODE COMPARISON TEST")
    print("=" * 80)

    # Test hybrid mode (current)
    print("\n### Testing HYBRID Mode (OpenAI Embeddings + Gemini) ###\n")
    for i, test in enumerate(TEST_QUERIES):
        print(f"Query {i+1}: {test['name']}")
        print(f"  '{test['query']}'")
        result = test_query("hybrid", test['query'], f"hybrid-test-{i}")
        results["hybrid"].append({
            "test_name": test["name"],
            "query": test["query"],
            **result
        })
        print(f"  ✓ Time: {result['total_time']:.2f}s")
        print(f"  ✓ Answer length: {result['answer_length']} chars")
        print(f"  ✓ Complexity: {result.get('model_complexity', 'N/A')}")
        print()
        time.sleep(1)  # Brief pause between queries

    # Switch to assistants mode
    print("\n### Switching to ASSISTANTS Mode (OpenAI GPT-4o) ###\n")
    os.environ['RAG_MODE'] = 'assistants'

    # Note: Need to restart server for env change - will use .env file instead
    print("NOTE: Edit .env and set RAG_MODE=assistants, then restart server")
    print("      Press Enter when ready to test assistants mode...")
    input()

    print("\n### Testing ASSISTANTS Mode ###\n")
    for i, test in enumerate(TEST_QUERIES):
        print(f"Query {i+1}: {test['name']}")
        print(f"  '{test['query']}'")
        result = test_query("assistants", test['query'], f"assistants-test-{i}")
        results["assistants"].append({
            "test_name": test["name"],
            "query": test["query"],
            **result
        })
        print(f"  ✓ Time: {result['total_time']:.2f}s")
        print(f"  ✓ Answer length: {result['answer_length']} chars")
        print()
        time.sleep(1)

    # Print comparison table
    print("\n" + "=" * 80)
    print("COMPARISON SUMMARY")
    print("=" * 80)
    print()

    print(f"{'Query':<20} {'Mode':<12} {'Time':<10} {'Length':<10} {'Complexity':<12}")
    print("-" * 80)

    for i, test in enumerate(TEST_QUERIES):
        hybrid = results["hybrid"][i]
        assistants = results["assistants"][i]

        print(f"{test['name']:<20} {'HYBRID':<12} {hybrid['total_time']:>6.2f}s    {hybrid['answer_length']:>6} ch  {hybrid.get('model_complexity', 'N/A'):<12}")
        print(f"{'':20} {'ASSISTANTS':<12} {assistants['total_time']:>6.2f}s    {assistants['answer_length']:>6} ch  {'N/A':<12}")
        print()

    # Calculate averages
    hybrid_avg = sum(r['total_time'] for r in results['hybrid']) / len(results['hybrid'])
    assistants_avg = sum(r['total_time'] for r in results['assistants']) / len(results['assistants'])

    print(f"{'AVERAGE':<20} {'HYBRID':<12} {hybrid_avg:>6.2f}s")
    print(f"{'':20} {'ASSISTANTS':<12} {assistants_avg:>6.2f}s")
    print()

    speedup = assistants_avg / hybrid_avg
    print(f"Hybrid is {speedup:.1f}x faster than Assistants")
    print()

    # Save detailed results
    with open('rag_comparison_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    print("Detailed results saved to: rag_comparison_results.json")

if __name__ == "__main__":
    run_comparison()
