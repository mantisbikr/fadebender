#!/usr/bin/env python3
"""
Test Gemini 2.5 Flash-Lite vs Gemini 2.5 Flash for intent parsing.

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
    """Compare Gemini 2.5 Flash-Lite vs Gemini 2.5 Flash."""

    # Model configuration
    gemini_flash_model = os.getenv("VERTEX_MODEL", os.getenv("GEMINI_MODEL"))
    gemini_lite_model = os.getenv("GEMINI_LITE_MODEL", "gemini-2.5-flash-lite")

    if not gemini_flash_model:
        print("ERROR: VERTEX_MODEL or GEMINI_MODEL environment variable must be set")
        print("Example: export VERTEX_MODEL=gemini-2.5-flash")
        return

    print("=" * 80)
    print("GEMINI 2.5 FLASH-LITE vs GEMINI 2.5 FLASH - INTENT PARSING COMPARISON")
    print("=" * 80)
    print(f"\nGemini Flash Model: {gemini_flash_model}")
    print(f"Gemini Lite Model:  {gemini_lite_model}")
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
        "flash": {"successes": 0, "errors": 0, "latencies": []},
        "lite": {"successes": 0, "errors": 0, "latencies": []}
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

        # Test Gemini Flash
        print("Testing Gemini 2.5 Flash...")
        flash_result = test_model(gemini_flash_model, query, prompt)
        if flash_result.get("error"):
            print(f"  ✗ ERROR: {flash_result['error']}")
            results["flash"]["errors"] += 1
        else:
            print(f"  ✓ SUCCESS - {flash_result['latency_ms']:.2f}ms")
            intent = flash_result["result"].get("intent")
            print(f"    Intent: {intent}")
            if intent == "set_parameter":
                targets = flash_result["result"].get("targets", [])
                if targets:
                    t = targets[0]
                    print(f"    Target: track={t.get('track')}, plugin={t.get('plugin')}, param={t.get('parameter')}")
            results["flash"]["successes"] += 1
            results["flash"]["latencies"].append(flash_result["latency_ms"])

        # Test Gemini Flash-Lite
        print("\nTesting Gemini 2.5 Flash-Lite...")
        lite_result = test_model(gemini_lite_model, query, prompt)
        if lite_result.get("error"):
            print(f"  ✗ ERROR: {lite_result['error']}")
            if "raw" in lite_result:
                print(f"    Raw response: {lite_result['raw']}")
            results["lite"]["errors"] += 1
        else:
            print(f"  ✓ SUCCESS - {lite_result['latency_ms']:.2f}ms")
            intent = lite_result["result"].get("intent")
            print(f"    Intent: {intent}")
            if intent == "set_parameter":
                targets = lite_result["result"].get("targets", [])
                if targets:
                    t = targets[0]
                    print(f"    Target: track={t.get('track')}, plugin={t.get('plugin')}, param={t.get('parameter')}")
            results["lite"]["successes"] += 1
            results["lite"]["latencies"].append(lite_result["latency_ms"])

        # Compare results
        if not flash_result.get("error") and not lite_result.get("error"):
            f_intent = flash_result["result"].get("intent")
            l_intent = lite_result["result"].get("intent")
            match = f_intent == l_intent
            print(f"\n  Match: {'✓ YES' if match else '✗ NO'}")
            if not match:
                print(f"    Flash:      {f_intent}")
                print(f"    Flash-Lite: {l_intent}")

    # Final summary
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80 + "\n")

    print(f"{'Metric':<30} {'Flash':>20} {'Flash-Lite':>20}")
    print(f"{'-'*30} {'-'*20} {'-'*20}")

    print(f"{'Total Queries':<30} {len(TEST_QUERIES):>20} {len(TEST_QUERIES):>20}")
    print(f"{'Successes':<30} {results['flash']['successes']:>20} {results['lite']['successes']:>20}")
    print(f"{'Errors':<30} {results['flash']['errors']:>20} {results['lite']['errors']:>20}")
    print()

    # Calculate Flash stats
    if results["flash"]["latencies"]:
        f_avg = sum(results["flash"]["latencies"]) / len(results["flash"]["latencies"])
        f_median = sorted(results["flash"]["latencies"])[len(results["flash"]["latencies"]) // 2]
        f_min = min(results["flash"]["latencies"])
        f_max = max(results["flash"]["latencies"])
    else:
        f_avg = f_median = f_min = f_max = 0

    # Calculate Flash-Lite stats
    if results["lite"]["latencies"]:
        l_avg = sum(results["lite"]["latencies"]) / len(results["lite"]["latencies"])
        l_median = sorted(results["lite"]["latencies"])[len(results["lite"]["latencies"]) // 2]
        l_min = min(results["lite"]["latencies"])
        l_max = max(results["lite"]["latencies"])
    else:
        l_avg = l_median = l_min = l_max = 0

    # Print latency stats
    f_avg_str = f"{f_avg:.2f}" if f_avg > 0 else "N/A"
    l_avg_str = f"{l_avg:.2f}" if l_avg > 0 else "N/A"
    print(f"{'Average Latency (ms)':<30} {f_avg_str:>20} {l_avg_str:>20}")

    if f_avg > 0 and l_avg > 0:
        print(f"{'Median Latency (ms)':<30} {f_median:>20.2f} {l_median:>20.2f}")
        print(f"{'Min Latency (ms)':<30} {f_min:>20.2f} {l_min:>20.2f}")
        print(f"{'Max Latency (ms)':<30} {f_max:>20.2f} {l_max:>20.2f}")
    elif f_avg > 0:
        print(f"{'Median Latency (ms)':<30} {f_median:>20.2f} {'N/A':>20}")
        print(f"{'Min Latency (ms)':<30} {f_min:>20.2f} {'N/A':>20}")
        print(f"{'Max Latency (ms)':<30} {f_max:>20.2f} {'N/A':>20}")

    print()

    # Performance comparison
    if f_avg > 0 and l_avg > 0:
        if l_avg < f_avg:
            speedup = f_avg / l_avg
            improvement = ((f_avg - l_avg) / f_avg) * 100
            print(f"{'='*80}")
            print(f"GEMINI 2.5 FLASH-LITE PERFORMANCE")
            print(f"{'='*80}")
            print(f"Speedup: {speedup:.2f}x faster than Flash")
            print(f"Latency Reduction: {improvement:.1f}%")
            print(f"Time Saved per Query: {f_avg - l_avg:.2f} ms")
        else:
            slowdown = l_avg / f_avg
            print(f"{'='*80}")
            print(f"GEMINI 2.5 FLASH-LITE PERFORMANCE")
            print(f"{'='*80}")
            print(f"Slowdown: {slowdown:.2f}x slower than Flash")

    # Recommendation
    print(f"\n{'='*80}")
    print("RECOMMENDATION")
    print(f"{'='*80}")

    f_success_rate = (results["flash"]["successes"] / len(TEST_QUERIES)) * 100
    l_success_rate = (results["lite"]["successes"] / len(TEST_QUERIES)) * 100

    print(f"\nGemini Flash Success Rate:      {f_success_rate:.1f}%")
    print(f"Gemini Flash-Lite Success Rate: {l_success_rate:.1f}%")

    if l_success_rate >= 90 and l_avg > 0 and l_avg < f_avg:
        print("\n✓ RECOMMENDATION: Use Gemini 2.5 Flash-Lite for intent parsing")
        print(f"  - High accuracy ({l_success_rate:.1f}%)")
        print(f"  - Faster than Flash ({speedup:.1f}x speedup)")
        print(f"  - Lower cost per query")
    elif l_success_rate >= 90:
        print("\n⚠ RECOMMENDATION: Flash-Lite accuracy is good but check latency")
        print(f"  - High accuracy ({l_success_rate:.1f}%)")
    else:
        print("\n✗ RECOMMENDATION: Stick with Gemini 2.5 Flash")
        print(f"  - Flash-Lite accuracy too low ({l_success_rate:.1f}%)")
        print("  - Flash more reliable for production")


if __name__ == "__main__":
    import sys

    print("\nTo run this test, you need:")
    print("1. VERTEX_MODEL or GEMINI_MODEL set to your Gemini Flash model (e.g., gemini-2.5-flash)")
    print("2. LLM_PROJECT_ID set to your GCP project")
    print("3. GEMINI_LITE_MODEL set to Flash-Lite model (optional, defaults to gemini-2.5-flash-lite)")
    print()

    # Skip interactive prompt if running non-interactively
    if sys.stdin.isatty():
        input("Press Enter to continue...")
    else:
        print("Running in non-interactive mode...")
        print()

    compare_models()
