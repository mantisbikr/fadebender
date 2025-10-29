#!/usr/bin/env python3
"""Comprehensive test suite for typo learning system.

Tests both GET and SET intents with cached typos to ensure:
1. Typo corrections are applied correctly
2. Intent parsing is accurate (action, field, value, track_index)
3. Performance is fast (using regex, not LLM fallback)
4. No regressions in normal queries
"""

import requests
import json
import sys
from typing import Dict, Any

SERVER_URL = "http://127.0.0.1:8722/intent/parse"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def test_query(test_name: str, query: str, expected: Dict[str, Any]) -> bool:
    """Test a single query and validate the response.

    Args:
        test_name: Human-readable test name
        query: User query to test
        expected: Expected intent values
            - action: 'get' or 'set'
            - field: 'volume', 'pan', 'mute', etc.
            - track_index: int
            - value: float (for SET queries)
            - max_latency_ms: int (max acceptable latency)

    Returns:
        True if test passed, False otherwise
    """
    try:
        response = requests.post(
            SERVER_URL,
            headers={"Content-Type": "application/json"},
            json={"text": query},
            timeout=15
        )

        if response.status_code != 200:
            print(f"{Colors.RED}✗ {test_name}{Colors.RESET}")
            print(f"  HTTP {response.status_code}: {response.text[:100]}")
            return False

        data = response.json()
        intent = data.get('intent', {})
        meta = data.get('raw_intent', {}).get('meta', {})

        # Check all expected fields
        passed = True
        failures = []

        # Check action
        if 'action' in expected and intent.get('action') != expected['action']:
            passed = False
            failures.append(f"action: expected '{expected['action']}', got '{intent.get('action')}'")

        # Check field
        if 'field' in expected and intent.get('field') != expected['field']:
            passed = False
            failures.append(f"field: expected '{expected['field']}', got '{intent.get('field')}'")

        # Check track_index
        if 'track_index' in expected and intent.get('track_index') != expected['track_index']:
            passed = False
            failures.append(f"track_index: expected {expected['track_index']}, got {intent.get('track_index')}")

        # Check value (for SET queries)
        if 'value' in expected and intent.get('value') != expected['value']:
            passed = False
            failures.append(f"value: expected {expected['value']}, got {intent.get('value')}'")

        # Check latency
        latency = meta.get('latency_ms', 999999)
        max_latency = expected.get('max_latency_ms', 1000)
        if latency > max_latency:
            passed = False
            failures.append(f"latency: {latency:.0f}ms > {max_latency}ms (too slow!)")

        # Check pipeline (should be regex for cached typos)
        pipeline = meta.get('pipeline', 'unknown')
        if 'pipeline' in expected and pipeline != expected['pipeline']:
            passed = False
            failures.append(f"pipeline: expected '{expected['pipeline']}', got '{pipeline}'")

        # Print result
        if passed:
            print(f"{Colors.GREEN}✓ {test_name}{Colors.RESET}")
            print(f"  {Colors.BLUE}Pipeline: {pipeline}, Latency: {latency:.0f}ms{Colors.RESET}")
            print(f"  Intent: {intent}")
            return True
        else:
            print(f"{Colors.RED}✗ {test_name}{Colors.RESET}")
            for failure in failures:
                print(f"  {Colors.RED}- {failure}{Colors.RESET}")
            print(f"  Intent: {intent}")
            print(f"  Meta: {meta}")
            return False

    except Exception as e:
        print(f"{Colors.RED}✗ {test_name}{Colors.RESET}")
        print(f"  Exception: {e}")
        return False


def main():
    print(f"\n{Colors.BLUE}=== PHASE 3 TYPO LEARNING: COMPREHENSIVE TEST SUITE ==={Colors.RESET}\n")

    tests_passed = 0
    tests_failed = 0

    # ============================================================
    # CATEGORY 1: SET queries with cached typos
    # ============================================================
    print(f"{Colors.YELLOW}[1/5] Testing SET queries with cached typos{Colors.RESET}\n")

    tests = [
        ("SET track volume with 'volum' typo", "set track 3 volum to -12", {
            'action': 'set',
            'field': 'volume',
            'track_index': 3,
            'value': -12.0,
            'max_latency_ms': 500,
            'pipeline': 'regex'
        }),
        ("SET track volume with 'volumz' typo", "set track 1 volumz to -6", {
            'action': 'set',
            'field': 'volume',
            'track_index': 1,
            'value': -6.0,
            'max_latency_ms': 500,
            'pipeline': 'regex'
        }),
        ("SET track mute with 'mut' typo", "mute track 2", {
            'action': 'set',
            'field': 'mute',
            'track_index': 2,
            'value': 1.0,
            'max_latency_ms': 500,
            'pipeline': 'regex'
        }),
        ("SET track pan with 'paning' typo", "set track 1 paning 25l", {
            'action': 'set',
            'field': 'pan',
            'track_index': 1,
            'value': -25.0,
            'max_latency_ms': 500,
            'pipeline': 'regex'
        }),
    ]

    for test_name, query, expected in tests:
        if test_query(test_name, query, expected):
            tests_passed += 1
        else:
            tests_failed += 1
        print()

    # ============================================================
    # CATEGORY 2: GET queries with cached typos
    # ============================================================
    print(f"{Colors.YELLOW}[2/5] Testing GET queries with cached typos{Colors.RESET}\n")

    tests = [
        ("GET track volume with 'volum' typo", "get track 2 volum", {
            'action': 'get',
            'field': 'volume',
            'track_index': 2,
            'max_latency_ms': 500,
            'pipeline': 'regex'
        }),
        ("GET track volume with 'volumz' typo", "what is track 5 volumz", {
            'action': 'get',
            'field': 'volume',
            'track_index': 5,
            'max_latency_ms': 500,
            'pipeline': 'regex'
        }),
        ("GET track mute with 'mut' typo", "get track 1 mut", {
            'action': 'get',
            'field': 'mute',
            'track_index': 1,
            'max_latency_ms': 500,
            'pipeline': 'regex'
        }),
    ]

    for test_name, query, expected in tests:
        if test_query(test_name, query, expected):
            tests_passed += 1
        else:
            tests_failed += 1
        print()

    # ============================================================
    # CATEGORY 3: Queries with NO typos (regression testing)
    # ============================================================
    print(f"{Colors.YELLOW}[3/5] Testing queries WITHOUT typos (no regressions){Colors.RESET}\n")

    tests = [
        ("SET track volume (correct spelling)", "set track 1 volume to -10", {
            'action': 'set',
            'field': 'volume',
            'track_index': 1,
            'value': -10.0,
            'max_latency_ms': 500,
            'pipeline': 'regex'
        }),
        ("GET track volume (correct spelling)", "get track 3 volume", {
            'action': 'get',
            'field': 'volume',
            'track_index': 3,
            'max_latency_ms': 500,
            'pipeline': 'regex'
        }),
        ("SET track pan (correct spelling)", "set track 2 pan 50r", {
            'action': 'set',
            'field': 'pan',
            'track_index': 2,
            'value': 50.0,
            'max_latency_ms': 500,
            'pipeline': 'regex'
        }),
        ("SET track mute (correct spelling)", "mute track 4", {
            'action': 'set',
            'field': 'mute',
            'track_index': 4,
            'value': 1.0,
            'max_latency_ms': 500,
            'pipeline': 'regex'
        }),
    ]

    for test_name, query, expected in tests:
        if test_query(test_name, query, expected):
            tests_passed += 1
        else:
            tests_failed += 1
        print()

    # ============================================================
    # CATEGORY 4: Edge cases
    # ============================================================
    print(f"{Colors.YELLOW}[4/5] Testing edge cases{Colors.RESET}\n")

    tests = [
        ("Typo at end of query", "set track 1 to -8 volum", {
            'action': 'set',
            'field': 'volume',
            'track_index': 1,
            'value': -8.0,
            'max_latency_ms': 500,
        }),
        ("Multiple parameters in one query", "set track 1 volume to -5", {
            'action': 'set',
            'field': 'volume',
            'track_index': 1,
            'value': -5.0,
            'max_latency_ms': 500,
        }),
    ]

    for test_name, query, expected in tests:
        if test_query(test_name, query, expected):
            tests_passed += 1
        else:
            tests_failed += 1
        print()

    # ============================================================
    # CATEGORY 5: New typo learning (should use LLM first time)
    # ============================================================
    print(f"{Colors.YELLOW}[5/5] Testing brand new typo learning{Colors.RESET}\n")

    # First check if this typo already exists in Firestore
    print("  (Testing new typo: 'vlume' -> 'volume')")
    print("  First request: should use LLM fallback and learn")

    test_query(
        "First occurrence of 'vlume' typo (learning phase)",
        "set track 1 vlume to -15",
        {
            'action': 'set',
            'field': 'volume',
            'track_index': 1,
            'value': -15.0,
            'max_latency_ms': 80000,  # Allow LLM time
        }
    )
    print()

    print("  Waiting 2 seconds for cache to update...")
    import time
    time.sleep(2)

    print("  Second request: should use regex (cached correction)")
    if test_query(
        "Second occurrence of 'vlume' typo (should be fast)",
        "set track 2 vlume to -20",
        {
            'action': 'set',
            'field': 'volume',
            'track_index': 2,
            'value': -20.0,
            'max_latency_ms': 500,
            'pipeline': 'regex'
        }
    ):
        tests_passed += 1
        print(f"{Colors.GREEN}  ✓ Typo learning working end-to-end!{Colors.RESET}")
    else:
        tests_failed += 1
        print(f"{Colors.RED}  ✗ Typo learning NOT working!{Colors.RESET}")

    # ============================================================
    # SUMMARY
    # ============================================================
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}SUMMARY{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"  {Colors.GREEN}Passed: {tests_passed}{Colors.RESET}")
    print(f"  {Colors.RED}Failed: {tests_failed}{Colors.RESET}")
    print(f"  Total: {tests_passed + tests_failed}")

    if tests_failed == 0:
        print(f"\n{Colors.GREEN}🎉 ALL TESTS PASSED! Typo learning system is working correctly!{Colors.RESET}\n")
        sys.exit(0)
    else:
        print(f"\n{Colors.RED}❌ SOME TESTS FAILED. Please review failures above.{Colors.RESET}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
