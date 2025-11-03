#!/usr/bin/env python3
"""
Test WebUI validation removal - verify backend handles all validation correctly.
Tests commands that previously relied on WebUI keyword validation.
"""
import sys
import requests
from typing import List, Tuple, Dict, Any

# Server endpoint
BASE_URL = "http://127.0.0.1:8722"


def test_command(text: str, should_succeed: bool = True) -> Tuple[bool, str]:
    """Test a command via /chat endpoint (same as WebUI uses)."""
    try:
        response = requests.post(
            f"{BASE_URL}/chat",
            json={"text": text},
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            ok = data.get("ok", False)
            summary = data.get("summary", "")

            if should_succeed:
                # Command should work
                if ok:
                    return True, f"✓ {summary[:30]}"
                else:
                    error_msg = data.get("error", "Unknown error")
                    return False, f"✗ FAIL: Expected success but got ok=False, error={error_msg}"
            else:
                # Command should fail
                if not ok:
                    return True, f"✓ REJECTED (expected)"
                else:
                    return False, f"✗ FAIL: Expected error but command succeeded"
        else:
            if should_succeed:
                return False, f"✗ FAIL: HTTP {response.status_code}"
            else:
                return True, f"✓ REJECTED (expected): HTTP {response.status_code}"

    except Exception as e:
        return False, f"✗ ERROR: {str(e)[:30]}"


def main():
    print("=" * 80)
    print("Testing WebUI Validation Removal")
    print("=" * 80)
    print("\nVerifying backend properly validates commands now that WebUI")
    print("keyword validation has been removed.\n")

    # Test cases: (command, should_succeed, description)
    test_cases: List[Tuple[str, bool, str]] = [
        # Commands that should work
        ("set track 1 volume to -10", True, "Basic volume command"),
        ("increase track 2 volume by 3 db", True, "Relative volume increase"),
        ("decrease master cue by 2", True, "Master cue decrease"),
        ("reduce master cue by 4", True, "Master cue reduce (now working)"),
        ("set return A volume to -6", True, "Return volume command"),
        ("pan track 1 left by 10%", True, "Pan command"),
        ("set track 1 send A to -20", True, "Send command"),
        ("increase track 3 volume by 20%", True, "Percent increase"),

        # Commands with typos (should be corrected by backend or autocorrect)
        ("set track 1 volum to -15", True, "Typo in 'volume'"),
    ]

    print(f"{'#':<4} {'Result':<8} {'Description':<40} {'Details':<30}")
    print("-" * 80)

    passed = 0
    failed = 0

    for i, (command, should_succeed, description) in enumerate(test_cases, 1):
        success, details = test_command(command, should_succeed)
        result = "PASS" if success else "FAIL"

        if success:
            passed += 1
        else:
            failed += 1

        # Truncate for display
        cmd_display = command if len(command) <= 30 else command[:27] + "..."

        print(f"{i:<4} {result:<8} {description:<40} {details[:30]}")

    print("\n" + "=" * 80)
    print(f"SUMMARY: {passed}/{len(test_cases)} tests passed")
    print("=" * 80)

    if failed > 0:
        print(f"\n❌ {failed} test(s) FAILED - backend validation may need adjustment")
        return 1
    else:
        print("\n✅ All tests PASSED - backend validation working correctly!")
        print("   WebUI keyword validation can be safely removed.")
        return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(130)
