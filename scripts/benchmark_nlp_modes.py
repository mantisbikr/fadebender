#!/usr/bin/env python3
"""
Benchmark NLP mode performance: regex_first vs llm_first

Runs representative commands through both modes and compares:
- Average latency
- Pipeline usage (regex vs llm)
- Cache hit rates
- Success rates

Usage:
    python3 scripts/benchmark_nlp_modes.py
    python3 scripts/benchmark_nlp_modes.py --queries 100  # Run 100 queries
"""
import argparse
import json
import os
import sys
import time
from collections import defaultdict
from typing import List, Dict, Any

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'nlp-service'))

from llm_daw import interpret_daw_command


# Representative test queries - ABSOLUTE commands only with typos
TEST_QUERIES = [
    # Simple mixer commands (no typos - baseline)
    "set track 1 volume to -12 dB",
    "set track 2 volume to -6 dB",
    "solo track 3",
    "mute return A",
    "set track 4 pan to 25% left",
    "set track 1 send A to -18 dB",
    "set return A volume to -6 dB",

    # Simple device commands (no typos - baseline)
    "set return A reverb decay to 2.5 s",
    "set return B delay feedback to 50%",
    "set return A reverb predelay to 20 ms",

    # Mixer commands WITH TYPOS (tests typo correction - ABSOLUTE only)
    "set tack 1 vilme to -6 dB",           # tack→track, vilme→volume
    "set retun A volme to -3 dB",          # retun→return, volme→volume (changed to absolute)
    "set track 2 paning to 50% right",     # paning→pan
    "set track 1 sennd A to -12 dB",       # sennd→send

    # Device commands WITH TYPOS (tests typo correction)
    "set return A revreb dcay to 2 s",     # revreb→reverb, dcay→decay
    "set return A reverb predlay to 15 ms", # predlay→predelay
]


def run_benchmark(mode: str, queries: List[str], iterations: int = 1) -> Dict[str, Any]:
    """Run benchmark for given mode.

    Args:
        mode: NLP mode (regex_first or llm_first)
        queries: List of test queries
        iterations: Number of times to run each query

    Returns:
        Dict with benchmark results
    """
    os.environ["NLP_MODE"] = mode

    results = {
        "mode": mode,
        "total_queries": len(queries) * iterations,
        "latencies": [],
        "pipelines": defaultdict(int),
        "cache_hits": 0,
        "successes": 0,
        "errors": 0,
    }

    print(f"\n{'='*60}")
    print(f"Running benchmark: {mode.upper()}")
    print(f"Queries: {len(queries)} x {iterations} iterations")
    print(f"{'='*60}\n")

    for i in range(iterations):
        for idx, query in enumerate(queries, 1):
            try:
                # Run query
                result = interpret_daw_command(query)

                # Collect metrics
                meta = result.get("meta", {})
                latency = meta.get("latency_ms", 0)
                pipeline = meta.get("pipeline", "unknown")
                cache_hit = meta.get("cache_hit", False)

                results["latencies"].append(latency)
                results["pipelines"][pipeline] += 1
                if cache_hit:
                    results["cache_hits"] += 1

                # Check if successful (not clarification_needed)
                if result.get("intent") != "clarification_needed":
                    results["successes"] += 1

                # Progress indicator
                if idx % 5 == 0:
                    print(f"  Processed {idx}/{len(queries)} queries (iter {i+1}/{iterations})...")

            except Exception as e:
                results["errors"] += 1
                print(f"  ERROR on query '{query}': {e}")

    # Calculate statistics
    if results["latencies"]:
        results["avg_latency_ms"] = sum(results["latencies"]) / len(results["latencies"])
        results["min_latency_ms"] = min(results["latencies"])
        results["max_latency_ms"] = max(results["latencies"])
        results["median_latency_ms"] = sorted(results["latencies"])[len(results["latencies"]) // 2]

    return results


def print_results(regex_results: Dict, llm_results: Dict):
    """Print comparison results."""
    print(f"\n{'='*80}")
    print("BENCHMARK RESULTS")
    print(f"{'='*80}\n")

    # Summary table
    print(f"{'Metric':<30} {'Regex First':>20} {'LLM First':>20}")
    print(f"{'-'*30} {'-'*20} {'-'*20}")

    print(f"{'Total Queries':<30} {regex_results['total_queries']:>20} {llm_results['total_queries']:>20}")
    print(f"{'Successes':<30} {regex_results['successes']:>20} {llm_results['successes']:>20}")
    print(f"{'Errors':<30} {regex_results['errors']:>20} {llm_results['errors']:>20}")
    print()

    print(f"{'Average Latency (ms)':<30} {regex_results.get('avg_latency_ms', 0):>20.2f} {llm_results.get('avg_latency_ms', 0):>20.2f}")
    print(f"{'Median Latency (ms)':<30} {regex_results.get('median_latency_ms', 0):>20.2f} {llm_results.get('median_latency_ms', 0):>20.2f}")
    print(f"{'Min Latency (ms)':<30} {regex_results.get('min_latency_ms', 0):>20.2f} {llm_results.get('min_latency_ms', 0):>20.2f}")
    print(f"{'Max Latency (ms)':<30} {regex_results.get('max_latency_ms', 0):>20.2f} {llm_results.get('max_latency_ms', 0):>20.2f}")
    print()

    # Pipeline breakdown
    print("Pipeline Usage:")
    all_pipelines = set(regex_results["pipelines"].keys()) | set(llm_results["pipelines"].keys())
    for pipeline in sorted(all_pipelines):
        regex_count = regex_results["pipelines"].get(pipeline, 0)
        llm_count = llm_results["pipelines"].get(pipeline, 0)
        regex_pct = (regex_count / regex_results['total_queries'] * 100) if regex_results['total_queries'] else 0
        llm_pct = (llm_count / llm_results['total_queries'] * 100) if llm_results['total_queries'] else 0
        print(f"  {pipeline:<28} {regex_count:>10} ({regex_pct:>5.1f}%)  {llm_count:>10} ({llm_pct:>5.1f}%)")

    # Performance improvement
    if llm_results.get('avg_latency_ms', 0) > 0:
        speedup = llm_results['avg_latency_ms'] / regex_results['avg_latency_ms'] if regex_results.get('avg_latency_ms', 0) > 0 else 0
        improvement = ((llm_results['avg_latency_ms'] - regex_results['avg_latency_ms']) / llm_results['avg_latency_ms'] * 100)

        print(f"\n{'='*80}")
        print(f"PERFORMANCE IMPROVEMENT")
        print(f"{'='*80}")
        print(f"Speedup: {speedup:.2f}x faster")
        print(f"Latency Reduction: {improvement:.1f}%")
        print(f"Time Saved per Query: {llm_results['avg_latency_ms'] - regex_results['avg_latency_ms']:.2f} ms")


def main():
    parser = argparse.ArgumentParser(description="Benchmark NLP mode performance")
    parser.add_argument("--iterations", type=int, default=1, help="Number of iterations per query")
    parser.add_argument("--output", type=str, help="Save results to JSON file")
    args = parser.parse_args()

    print(f"\nNLP MODE BENCHMARK")
    print(f"{'='*80}")
    print(f"Test queries: {len(TEST_QUERIES)}")
    print(f"Iterations: {args.iterations}")
    print(f"Total executions: {len(TEST_QUERIES) * args.iterations * 2} (both modes)")

    # Run benchmarks
    regex_results = run_benchmark("regex_first", TEST_QUERIES, args.iterations)
    llm_results = run_benchmark("llm_first", TEST_QUERIES, args.iterations)

    # Print comparison
    print_results(regex_results, llm_results)

    # Save to file if requested
    if args.output:
        output_data = {
            "timestamp": time.time(),
            "regex_first": regex_results,
            "llm_first": llm_results,
        }
        with open(args.output, 'w') as f:
            json.dump(output_data, f, indent=2)
        print(f"\n✓ Results saved to: {args.output}")


if __name__ == "__main__":
    main()
