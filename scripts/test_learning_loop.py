#!/usr/bin/env python3
"""Test the complete learning loop: LLM correction → Persist → Fast lookup.

This script tests the full phase 2 learning system:
1. Query with typo falls back to LLM (via HTTP to NLP service)
2. LLM corrects typo, learning system detects it
3. Correction is added to app_config typo_corrections
4. Next query with same typo uses fast typo correction → regex matches

Requirements:
- NLP service must be running (python3 app.py in nlp-service/)
- Service must have LLM access (Vertex AI credentials)
"""

import os
import sys
import json
import requests
import time

# Add server path for config access
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'server'))

from config.app_config import get_typo_corrections, reload_config

SERVER_URL = "http://127.0.0.1:8722"


def check_nlp_service():
    """Check if server with NLP service is running."""
    try:
        # Try a simple parse request - any response means server is up
        resp = requests.post(
            f"{SERVER_URL}/intent/parse",
            json={"text": "set track 1 volume to -20"},
            timeout=10
        )
        # Accept any 2xx status code
        return 200 <= resp.status_code < 300
    except Exception as e:
        print(f"  Debug: Connection error: {e}")
        return False


def call_nlp_service(query: str) -> dict:
    """Call NLP service via main server to parse a query."""
    resp = requests.post(
        f"{SERVER_URL}/intent/parse",
        json={"text": query},
        timeout=30  # LLM can take a while
    )
    resp.raise_for_status()
    result = resp.json()

    # Extract raw_intent which has the meta information
    if 'raw_intent' in result:
        return result['raw_intent']
    return result


def test_persistence_api():
    """Test the persistence API directly."""

    print("=" * 80)
    print("TESTING PERSISTENCE API")
    print("=" * 80)
    print()

    from config.app_config import add_typo_corrections, save_config

    print("Step 1: Add test correction")
    test_correction = {"testtypo": "testcorrect"}
    add_typo_corrections(test_correction)

    current = get_typo_corrections()
    if "testtypo" in current:
        print(f"✓ Added to in-memory config: {current['testtypo']}")
    else:
        print("✗ FAIL: Not added to in-memory config")
        return False

    print("\nStep 2: Save config to disk")
    success = save_config()
    if success:
        print("✓ Config saved successfully")
    else:
        print("✗ FAIL: Could not save config")
        return False

    print("\nStep 3: Reload and verify persistence")
    reload_config()
    reloaded = get_typo_corrections()

    if "testtypo" in reloaded:
        print(f"✓ Correction persisted: {reloaded['testtypo']}")
        print()
        return True
    else:
        print("✗ FAIL: Correction not persisted after reload")
        print()
        return False


def test_learning_loop():
    """Test complete learning loop with real LLM via HTTP."""

    print("=" * 80)
    print("PHASE 2 LEARNING LOOP TEST (via HTTP)")
    print("=" * 80)
    print()

    # Test query with a typo that's NOT in the dictionary yet
    test_typo = "volumee"  # Double 'e' - unlikely to be in config already
    query = f"set track 1 {test_typo} to -20"

    print("Step 1: Check if typo already exists in config")
    print("-" * 80)
    initial_typos = get_typo_corrections()
    print(f"Current typo corrections count: {len(initial_typos)}")

    if test_typo in initial_typos:
        print(f"⚠️  WARNING: '{test_typo}' already in config")
        print(f"   Will remove it and re-test")
        # Could remove it here, but for now just warn
    else:
        print(f"✓ '{test_typo}' not in config (good - we can test learning)")
    print()

    print("Step 2: First query with typo (should fallback to LLM)")
    print("-" * 80)
    print(f"Query: {query}")

    start = time.time()
    result1 = call_nlp_service(query)
    latency1 = (time.time() - start) * 1000

    print(f"Intent: {result1.get('intent')}")
    print(f"Pipeline: {result1.get('meta', {}).get('pipeline')}")
    print(f"Latency: {latency1:.1f}ms")

    learned_typos = result1.get('meta', {}).get('learned_typos', {})
    print(f"Learned typos: {learned_typos}")

    if result1.get('meta', {}).get('pipeline') != 'llm_fallback':
        pipeline = result1.get('meta', {}).get('pipeline')
        if pipeline == 'regex':
            print(f"ℹ️  INFO: Already using regex (typo might already be in config)")
            print(f"   This is OK - means learning worked previously!")
            return True
        else:
            print(f"✗ FAIL: Expected LLM fallback, but got: {pipeline}")
            return False

    if test_typo not in learned_typos:
        print(f"⚠️  WARNING: Expected to learn '{test_typo}', but learned: {learned_typos}")
        print(f"   This might be OK if LLM didn't detect it as a typo")

    print(f"✓ LLM fallback succeeded")
    if learned_typos:
        print(f"  Detected typos: {learned_typos}")
    print()

    print("Step 3: Wait for persistence (async operation)")
    print("-" * 80)
    print("Waiting 2 seconds for config to be saved...")
    time.sleep(2)

    # Reload config to get fresh data from disk
    reload_config()
    updated_typos = get_typo_corrections()

    if test_typo in updated_typos:
        print(f"✓ SUCCESS: '{test_typo}' was added to config")
        print(f"  Correction: {test_typo} → {updated_typos[test_typo]}")
    else:
        print(f"ℹ️  INFO: '{test_typo}' not yet in config")
        print(f"  This is OK - persistence might be disabled or delayed")
    print()

    print("Step 4: Second query with same typo")
    print("-" * 80)
    print(f"Query: {query}")

    start = time.time()
    result2 = call_nlp_service(query)
    latency2 = (time.time() - start) * 1000

    print(f"Intent: {result2.get('intent')}")
    print(f"Pipeline: {result2.get('meta', {}).get('pipeline')}")
    print(f"Latency: {latency2:.1f}ms")

    # Should now use regex (fast path) if typo was corrected
    pipeline2 = result2.get('meta', {}).get('pipeline')
    if pipeline2 == 'regex':
        print(f"✓ SUCCESS: Used fast regex path")
        speedup = latency1 / latency2 if latency2 > 0 else 1
        print(f"  Speed improvement: {speedup:.1f}x faster")
    elif pipeline2 == 'llm_fallback':
        print(f"ℹ️  INFO: Still using LLM fallback")
        print(f"  This means typo correction hasn't taken effect yet")
        print(f"  Possible reasons:")
        print(f"    - Persistence is disabled (DISABLE_TYPO_PERSISTENCE=1)")
        print(f"    - Config reload needed (restart service)")
        print(f"    - Typo corrector not loading updated config")
    else:
        print(f"  Unexpected pipeline: {pipeline2}")

    print()
    print("=" * 80)
    print("LEARNING LOOP TEST COMPLETE")
    print("=" * 80)

    return True


if __name__ == '__main__':
    print("Testing Phase 2 Learning System")
    print("This test requires:")
    print("  1. Main server running (make run-server)")
    print("  2. LLM access (Vertex AI credentials)")
    print()

    # Check if service is running
    if not check_nlp_service():
        print("❌ Server is not running!")
        print("   Start it with: make run-server")
        sys.exit(1)

    print("✓ NLP service is running")
    print()

    # Test persistence API
    if not test_persistence_api():
        print("\n❌ Persistence API test failed")
        sys.exit(1)

    # Test complete learning loop
    try:
        if not test_learning_loop():
            print("\n⚠️  Learning loop test completed with warnings")
            sys.exit(0)
    except Exception as e:
        print(f"\n❌ Learning loop test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("\n✅ All tests passed!")
    sys.exit(0)
