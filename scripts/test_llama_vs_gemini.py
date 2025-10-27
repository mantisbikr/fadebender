#!/usr/bin/env python3
"""
Test Llama 3.1 8B vs Gemini 2.5 Flash for intent parsing.

Compares latency and accuracy for DAW command parsing with typos.
"""
import json
import os
import sys
import time
from typing import Dict, Any, List

# Add nlp-service to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'nlp-service'))

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(__file__), '..', 'nlp-service', '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"Loaded environment from: {env_path}\n")
except ImportError:
    pass  # dotenv not installed, use existing environment

from google import genai
from google.genai import types
from prompts.prompt_builder import build_daw_prompt
from fetchers import fetch_devices_cached, fetch_mixer_params_cached


# Test queries with typos from comprehensive tests
TEST_QUERIES = [
    # Mixer with typos
    ("set tack 1 vilme to -20 dB", "Track volume with typos"),
    ("set retun A volme to -6 dB", "Return volume with typos"),
    ("set track 2 paning to 50% right", "Pan with typo"),
    ("set track 1 sennd A to -12 dB", "Send with typo"),

    # Device with typos
    ("set return A revreb dcay to 2 s", "Reverb decay with typos"),
    ("set return A reverb predlay to 15 ms", "Reverb predelay with typo"),

    # Clean commands (baseline)
    ("set track 1 volume to -12 dB", "Clean track volume"),
    ("set return A reverb decay to 2.5 s", "Clean device param"),
]


def test_model(model_name: str, query: str, prompt: str) -> Dict[str, Any]:
    """Test a single query with a specific model.

    Returns dict with: result, latency_ms, error
    """
    try:
        project = os.getenv("LLM_PROJECT_ID", os.getenv("GOOGLE_CLOUD_PROJECT", ""))
        if not project:
            return {"error": "LLM_PROJECT_ID not set", "latency_ms": 0}

        location = os.getenv("GCP_REGION", "us-central1")

        # Initialize client
        client = genai.Client(vertexai=True, project=project, location=location)

        # Generate content
        config = types.GenerateContentConfig(
            temperature=0.1,
            max_output_tokens=512,
            top_p=0.8,
            top_k=20,
        )

        start = time.perf_counter()
        resp = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=config
        )
        latency_ms = (time.perf_counter() - start) * 1000

        response_text = resp.text if hasattr(resp, 'text') else None
        if not response_text:
            return {"error": "Empty response", "latency_ms": latency_ms}

        # Extract JSON
        text = response_text.strip()
        start_idx, end_idx = text.find("{"), text.rfind("}")
        if start_idx < 0 or end_idx <= start_idx:
            return {"error": "No JSON in response", "latency_ms": latency_ms, "raw": text[:200]}

        result = json.loads(text[start_idx:end_idx + 1])
        return {
            "result": result,
            "latency_ms": latency_ms,
            "error": None
        }

    except Exception as e:
        return {
            "error": str(e),
            "latency_ms": 0
        }


def compare_models():
    """Compare Llama 3.1 8B vs Gemini 2.5 Flash."""

    # Model configuration
    gemini_model = os.getenv("VERTEX_MODEL", os.getenv("GEMINI_MODEL"))
    llama_model = os.getenv("LLAMA_VERTEX_MODEL", "meta/llama3-8b-instruct-maas")

    if not gemini_model:
        print("ERROR: VERTEX_MODEL or GEMINI_MODEL environment variable must be set")
        print("Example: export VERTEX_MODEL=gemini-2.0-flash-exp")
        return

    print("=" * 80)
    print("LLAMA 3.1 8B vs GEMINI 2.5 FLASH - INTENT PARSING COMPARISON")
    print("=" * 80)
    print(f"\nGemini Model: {gemini_model}")
    print(f"Llama Model:  {llama_model}")
    print(f"\nTest Queries: {len(TEST_QUERIES)}")
    print()

    # Fetch context data once
    print("Fetching device/mixer context...")
    try:
        known_devices = fetch_devices_cached()
        mixer_params = fetch_mixer_params_cached()
    except Exception as e:
        print(f"WARNING: Could not fetch context: {e}")
        print("Using empty context for testing...")
        known_devices = []
        mixer_params = {}

    results = {
        "gemini": {"successes": 0, "errors": 0, "latencies": []},
        "llama": {"successes": 0, "errors": 0, "latencies": []}
    }

    print("\n" + "=" * 80)
    print("TESTING EACH QUERY")
    print("=" * 80 + "\n")

    for query, description in TEST_QUERIES:
        print(f"\n{'='*80}")
        print(f"Query: {query}")
        print(f"Description: {description}")
        print(f"{'='*80}\n")

        # Build prompt once
        prompt = build_daw_prompt(query, mixer_params, known_devices)

        # Test Gemini
        print("Testing Gemini 2.5 Flash...")
        gemini_result = test_model(gemini_model, query, prompt)
        if gemini_result.get("error"):
            print(f"  ✗ ERROR: {gemini_result['error']}")
            results["gemini"]["errors"] += 1
        else:
            print(f"  ✓ SUCCESS - {gemini_result['latency_ms']:.2f}ms")
            intent = gemini_result["result"].get("intent")
            print(f"    Intent: {intent}")
            if intent == "set_parameter":
                targets = gemini_result["result"].get("targets", [])
                if targets:
                    t = targets[0]
                    print(f"    Target: track={t.get('track')}, plugin={t.get('plugin')}, param={t.get('parameter')}")
            results["gemini"]["successes"] += 1
            results["gemini"]["latencies"].append(gemini_result["latency_ms"])

        # Test Llama
        print("\nTesting Llama 3.1 8B...")
        llama_result = test_model(llama_model, query, prompt)
        if llama_result.get("error"):
            print(f"  ✗ ERROR: {llama_result['error']}")
            if "raw" in llama_result:
                print(f"    Raw response: {llama_result['raw']}")
            results["llama"]["errors"] += 1
        else:
            print(f"  ✓ SUCCESS - {llama_result['latency_ms']:.2f}ms")
            intent = llama_result["result"].get("intent")
            print(f"    Intent: {intent}")
            if intent == "set_parameter":
                targets = llama_result["result"].get("targets", [])
                if targets:
                    t = targets[0]
                    print(f"    Target: track={t.get('track')}, plugin={t.get('plugin')}, param={t.get('parameter')}")
            results["llama"]["successes"] += 1
            results["llama"]["latencies"].append(llama_result["latency_ms"])

        # Compare results
        if not gemini_result.get("error") and not llama_result.get("error"):
            g_intent = gemini_result["result"].get("intent")
            l_intent = llama_result["result"].get("intent")
            match = g_intent == l_intent
            print(f"\n  Match: {'✓ YES' if match else '✗ NO'}")
            if not match:
                print(f"    Gemini: {g_intent}")
                print(f"    Llama:  {l_intent}")

    # Final summary
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80 + "\n")

    print(f"{'Metric':<30} {'Gemini 2.5 Flash':>20} {'Llama 3.1 8B':>20}")
    print(f"{'-'*30} {'-'*20} {'-'*20}")

    print(f"{'Total Queries':<30} {len(TEST_QUERIES):>20} {len(TEST_QUERIES):>20}")
    print(f"{'Successes':<30} {results['gemini']['successes']:>20} {results['llama']['successes']:>20}")
    print(f"{'Errors':<30} {results['gemini']['errors']:>20} {results['llama']['errors']:>20}")
    print()

    # Calculate Gemini stats
    if results["gemini"]["latencies"]:
        g_avg = sum(results["gemini"]["latencies"]) / len(results["gemini"]["latencies"])
        g_median = sorted(results["gemini"]["latencies"])[len(results["gemini"]["latencies"]) // 2]
        g_min = min(results["gemini"]["latencies"])
        g_max = max(results["gemini"]["latencies"])
    else:
        g_avg = g_median = g_min = g_max = 0

    # Calculate Llama stats
    if results["llama"]["latencies"]:
        l_avg = sum(results["llama"]["latencies"]) / len(results["llama"]["latencies"])
        l_median = sorted(results["llama"]["latencies"])[len(results["llama"]["latencies"]) // 2]
        l_min = min(results["llama"]["latencies"])
        l_max = max(results["llama"]["latencies"])
    else:
        l_avg = l_median = l_min = l_max = 0

    # Print latency stats
    g_avg_str = f"{g_avg:.2f}" if g_avg > 0 else "N/A"
    l_avg_str = f"{l_avg:.2f}" if l_avg > 0 else "N/A"
    print(f"{'Average Latency (ms)':<30} {g_avg_str:>20} {l_avg_str:>20}")

    if g_avg > 0 and l_avg > 0:
        print(f"{'Median Latency (ms)':<30} {g_median:>20.2f} {l_median:>20.2f}")
        print(f"{'Min Latency (ms)':<30} {g_min:>20.2f} {l_min:>20.2f}")
        print(f"{'Max Latency (ms)':<30} {g_max:>20.2f} {l_max:>20.2f}")
    elif g_avg > 0:
        print(f"{'Median Latency (ms)':<30} {g_median:>20.2f} {'N/A':>20}")
        print(f"{'Min Latency (ms)':<30} {g_min:>20.2f} {'N/A':>20}")
        print(f"{'Max Latency (ms)':<30} {g_max:>20.2f} {'N/A':>20}")

    print()

    # Performance comparison
    if g_avg > 0 and l_avg > 0:
        if l_avg < g_avg:
            speedup = g_avg / l_avg
            improvement = ((g_avg - l_avg) / g_avg) * 100
            print(f"{'='*80}")
            print(f"LLAMA 3.1 8B PERFORMANCE")
            print(f"{'='*80}")
            print(f"Speedup: {speedup:.2f}x faster than Gemini")
            print(f"Latency Reduction: {improvement:.1f}%")
            print(f"Time Saved per Query: {g_avg - l_avg:.2f} ms")
        else:
            slowdown = l_avg / g_avg
            print(f"{'='*80}")
            print(f"LLAMA 3.1 8B PERFORMANCE")
            print(f"{'='*80}")
            print(f"Slowdown: {slowdown:.2f}x slower than Gemini")

    # Recommendation
    print(f"\n{'='*80}")
    print("RECOMMENDATION")
    print(f"{'='*80}")

    g_success_rate = (results["gemini"]["successes"] / len(TEST_QUERIES)) * 100
    l_success_rate = (results["llama"]["successes"] / len(TEST_QUERIES)) * 100

    print(f"\nGemini Success Rate: {g_success_rate:.1f}%")
    print(f"Llama Success Rate:  {l_success_rate:.1f}%")

    if l_success_rate >= 90 and l_avg > 0 and l_avg < g_avg:
        print("\n✓ RECOMMENDATION: Use Llama 3.1 8B for intent parsing")
        print(f"  - High accuracy ({l_success_rate:.1f}%)")
        print(f"  - Faster than Gemini ({speedup:.1f}x speedup)")
        print(f"  - Cost savings")
    elif l_success_rate >= 90:
        print("\n⚠ RECOMMENDATION: Llama accuracy is good but check latency")
        print(f"  - High accuracy ({l_success_rate:.1f}%)")
    else:
        print("\n✗ RECOMMENDATION: Stick with Gemini 2.5 Flash")
        print(f"  - Llama accuracy too low ({l_success_rate:.1f}%)")
        print("  - Gemini more reliable for production")


if __name__ == "__main__":
    import sys

    print("\nTo run this test, you need:")
    print("1. VERTEX_MODEL or GEMINI_MODEL set to your Gemini model")
    print("2. LLM_PROJECT_ID set to your GCP project")
    print("3. Llama 3.1 8B deployed in Vertex AI Model Garden")
    print("4. LLAMA_VERTEX_MODEL set to the Llama endpoint (optional, defaults to meta/llama3-8b-instruct-maas)")
    print()

    # Skip interactive prompt if running non-interactively
    if sys.stdin.isatty():
        input("Press Enter to continue...")
    else:
        print("Running in non-interactive mode...")
        print()

    compare_models()
