#!/usr/bin/env python3
"""
Comprehensive intent testing suite for Fadebender NLP system.

Run this after any changes to parser, intent mapper, or NLP pipeline
to ensure all intent types work correctly.
"""

import requests
import json
from typing import Dict, Any, List, Tuple

BASE_URL = "http://127.0.0.1:8722"

# Test results tracking
results = {
    "passed": 0,
    "failed": 0,
    "failures": []
}


def test_intent(text: str, expected_action: str = None, expected_ok: bool = True,
                description: str = "") -> bool:
    """Test a single intent and track results"""
    try:
        response = requests.post(
            f"{BASE_URL}/intent/parse",
            json={"text": text},
            headers={"Content-Type": "application/json"},
            timeout=10
        )

        if response.status_code != 200:
            results["failed"] += 1
            results["failures"].append({
                "text": text,
                "description": description,
                "error": f"HTTP {response.status_code}"
            })
            return False

        data = response.json()
        ok = data.get("ok", False)
        action = data.get("raw_intent", {}).get("intent")

        # Check if result matches expectations
        if expected_ok and not ok:
            results["failed"] += 1
            results["failures"].append({
                "text": text,
                "description": description,
                "error": f"Expected ok=True, got ok=False"
            })
            return False

        if expected_action and action != expected_action:
            results["failed"] += 1
            results["failures"].append({
                "text": text,
                "description": description,
                "error": f"Expected action='{expected_action}', got '{action}'"
            })
            return False

        results["passed"] += 1
        return True

    except Exception as e:
        results["failed"] += 1
        results["failures"].append({
            "text": text,
            "description": description,
            "error": str(e)
        })
        return False


def run_test_category(category: str, tests: List[Tuple[str, str, str]]):
    """Run a category of tests"""
    print(f"\n{'='*70}")
    print(f"{category}")
    print(f"{'='*70}")

    for text, expected_action, description in tests:
        result = test_intent(text, expected_action, description=description)
        status = "✓" if result else "✗"
        print(f"{status} {description}")
        if not result:
            print(f"   Command: '{text}'")


def main():
    print("=" * 70)
    print("COMPREHENSIVE INTENT TESTING SUITE")
    print("=" * 70)
    print()

    # Check server health
    try:
        health = requests.get(f"{BASE_URL}/health", timeout=2)
        if health.status_code != 200:
            print("✗ Server not responding. Start server with: npm run server")
            return
        print("✓ Server is running")
    except Exception as e:
        print(f"✗ Cannot connect to server: {e}")
        return

    # ========================================================================
    # 1. MIXER COMMANDS - Track Controls
    # ========================================================================
    run_test_category("1. MIXER - Track Controls", [
        ("set track 1 volume to -10db", "set_parameter", "Set track volume (absolute)"),
        ("increase track 1 volume by 3db", "relative_change", "Increase track volume (relative)"),
        ("decrease track 2 volume by 2db", "relative_change", "Decrease track volume (relative)"),
        ("set track 1 pan to 50% left", "set_parameter", "Set track pan"),
        ("mute track 1", "set_parameter", "Mute track"),
        ("solo track 2", "set_parameter", "Solo track"),
        ("set track 1 send a to -20db", "set_parameter", "Set track send"),
    ])

    # ========================================================================
    # 2. MIXER COMMANDS - Return Controls
    # ========================================================================
    run_test_category("2. MIXER - Return Controls", [
        ("set return a volume to -10db", "set_parameter", "Set return volume"),
        ("increase return a send a by 5db", "relative_change", "Increase return send"),
        ("mute return b", "set_parameter", "Mute return"),
    ])

    # ========================================================================
    # 3. DEVICE PARAMETERS - Absolute Changes
    # ========================================================================
    run_test_category("3. DEVICE PARAMETERS - Absolute", [
        ("set return a reverb decay to 5 seconds", "set_parameter", "Set reverb decay"),
        ("set return a reverb dry/wet to 50%", "set_parameter", "Set reverb dry/wet"),
        ("set return b delay time to 250ms", "set_parameter", "Set delay time"),
    ])

    # ========================================================================
    # 4. DEVICE PARAMETERS - Relative Changes
    # ========================================================================
    run_test_category("4. DEVICE PARAMETERS - Relative", [
        ("increase return a reverb dry/wet by 10%", "relative_change", "Increase reverb dry/wet"),
        ("decrease return a reverb feedback by 5%", "relative_change", "Decrease reverb feedback"),
        ("increase return a reverb decay by 1 second", "relative_change", "Increase reverb decay"),
    ])

    # ========================================================================
    # 5. TRANSPORT COMMANDS
    # ========================================================================
    run_test_category("5. TRANSPORT Commands", [
        ("loop on", "transport", "Loop on"),
        ("loop off", "transport", "Loop off"),
        ("set tempo to 130", "transport", "Set tempo"),
        ("set loop start to 24", "transport", "Set loop start"),
        ("set loop length to 8", "transport", "Set loop length"),
        ("set time signature numerator to 3", "transport", "Set time signature numerator"),
        ("set time signature denominator to 4", "transport", "Set time signature denominator"),
        ("set playhead to 8", "transport", "Set playhead position"),
    ])

    # ========================================================================
    # 6. NAVIGATION COMMANDS
    # ========================================================================
    run_test_category("6. NAVIGATION Commands", [
        ("open track 1", "open_capabilities", "Open track capabilities"),
        ("open return a", "open_capabilities", "Open return capabilities"),
        ("open return a reverb", "open_capabilities", "Open device by name"),
        ("open return b device 0", "open_capabilities", "Open device by index"),
    ])

    # ========================================================================
    # 7. TYPO HANDLING
    # ========================================================================
    run_test_category("7. TYPO HANDLING", [
        ("set track 1 volum to -20", "set_parameter", "Typo: volum → volume"),
        ("set track 1 volumz to -15", "set_parameter", "Typo: volumz → volume"),
        ("set return a reverbb decay to 3", "set_parameter", "Typo: reverbb → reverb"),
        ("incrase track volume by 5db", "relative_change", "Typo: incrase → increase"),
    ])

    # ========================================================================
    # 8. SPECIAL CHARACTERS IN PARAMETERS
    # ========================================================================
    run_test_category("8. SPECIAL CHARACTERS", [
        ("set return a reverb dry wet to 50%", "set_parameter", "Slash omitted: dry wet → Dry/Wet"),
        ("set return a compressor s c eq freq to 1000", "set_parameter", "Slash omitted: s c → S/C"),
    ])

    # ========================================================================
    # SUMMARY
    # ========================================================================
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    print(f"Total:  {results['passed'] + results['failed']}")

    if results['failed'] > 0:
        print()
        print("=" * 70)
        print("FAILURES")
        print("=" * 70)
        for failure in results['failures']:
            print(f"\n✗ {failure['description']}")
            print(f"  Command: '{failure['text']}'")
            print(f"  Error: {failure['error']}")

    print()
    if results['failed'] == 0:
        print("✓ All tests passed!")
    else:
        pass_rate = (results['passed'] / (results['passed'] + results['failed'])) * 100
        print(f"Pass rate: {pass_rate:.1f}%")
    print()


if __name__ == "__main__":
    main()
