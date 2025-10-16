#!/usr/bin/env python3
"""
Interactive Live Testing for Intents API

Runs tests one-by-one against actual Ableton Live, pausing for user verification.
"""

import requests
import sys
from typing import Dict, Any, Optional

# Server configuration
SERVER_URL = "http://127.0.0.1:8722"
INTENT_ENDPOINT = f"{SERVER_URL}/intent/execute"


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Print a bold header."""
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{text}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*70}{Colors.ENDC}")


def print_test(number: int, total: int, description: str):
    """Print test number and description."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}[Test {number}/{total}] {description}{Colors.ENDC}")


def print_intent(intent: Dict[str, Any]):
    """Print the intent being sent."""
    print(f"\n{Colors.BLUE}Intent:{Colors.ENDC}")
    for key, value in intent.items():
        if value is not None:
            print(f"  {key}: {value}")


def print_success(message: str):
    """Print success message."""
    print(f"{Colors.GREEN}✓ {message}{Colors.ENDC}")


def print_error(message: str):
    """Print error message."""
    print(f"{Colors.RED}✗ {message}{Colors.ENDC}")


def print_info(message: str):
    """Print info message."""
    print(f"{Colors.YELLOW}ℹ {message}{Colors.ENDC}")


def execute_intent(intent: Dict[str, Any], dry_run: bool = False) -> Optional[Dict[str, Any]]:
    """Execute an intent and return the response."""
    try:
        intent_copy = intent.copy()
        intent_copy["dry_run"] = dry_run

        response = requests.post(INTENT_ENDPOINT, json=intent_copy, timeout=5.0)

        if response.status_code == 200:
            return response.json()
        else:
            print_error(f"HTTP {response.status_code}: {response.text}")
            return None
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to server. Is it running on port 8722?")
        return None
    except Exception as e:
        print_error(f"Error: {e}")
        return None


def wait_for_user(prompt: str = "Press Enter to continue, 's' to skip, 'q' to quit") -> str:
    """Wait for user input."""
    print(f"\n{Colors.YELLOW}{prompt}: {Colors.ENDC}", end='')
    response = input().strip().lower()
    return response


def run_test(test_num: int, total: int, description: str, intent: Dict[str, Any],
             expected: str, verify_instructions: str) -> bool:
    """Run a single test with user verification."""

    print_test(test_num, total, description)
    print_intent(intent)
    print(f"\n{Colors.CYAN}Expected:{Colors.ENDC} {expected}")
    print(f"{Colors.CYAN}Verify:{Colors.ENDC} {verify_instructions}")

    # Execute the intent
    result = execute_intent(intent)

    if result:
        if result.get("ok"):
            print_success("Intent executed successfully")
            if "preview" in result:
                print_info(f"Preview: {result['preview']}")
        else:
            print_error(f"Execution failed: {result}")
            return False
    else:
        return False

    # Wait for user verification
    response = wait_for_user("Did it work correctly? (y/n/s/q)")

    if response == 'q':
        print_info("Test session aborted by user")
        sys.exit(0)
    elif response == 's':
        print_info("Test skipped")
        return None
    elif response == 'y':
        print_success("Test PASSED - verified by user")
        return True
    else:
        print_error("Test FAILED - user reported it didn't work")
        return False


# Test suite
TESTS = [
    # ============================================================================
    # TRACK VOLUME TESTS (dB)
    # ============================================================================
    {
        "description": "Track 1 volume to -6dB",
        "intent": {
            "domain": "track",
            "action": "set",
            "track_index": 1,
            "field": "volume",
            "value": -6.0,
            "unit": "dB"
        },
        "expected": "Track 1 (first track) volume fader at -6dB",
        "verify": "Check Track 1 volume fader shows -6.0 dB in Live"
    },
    {
        "description": "Track 2 volume to 0dB",
        "intent": {
            "domain": "track",
            "action": "set",
            "track_index": 2,
            "field": "volume",
            "value": 0.0,
            "unit": "dB"
        },
        "expected": "Track 2 (second track) volume fader at 0dB (unity gain)",
        "verify": "Check Track 2 volume fader shows 0.0 dB in Live"
    },
    {
        "description": "Track 1 volume to +3dB (test positive dB)",
        "intent": {
            "domain": "track",
            "action": "set",
            "track_index": 1,
            "field": "volume",
            "value": 3.0,
            "unit": "dB"
        },
        "expected": "Track 1 volume fader at +3dB (above unity)",
        "verify": "Check Track 1 volume fader shows +3.0 dB in Live (NOT -3 dB!)"
    },

    # ============================================================================
    # TRACK VOLUME TESTS (Normalized)
    # ============================================================================
    {
        "description": "Track 1 volume to 0.85 (normalized, unity gain)",
        "intent": {
            "domain": "track",
            "action": "set",
            "track_index": 1,
            "field": "volume",
            "value": 0.85
        },
        "expected": "Track 1 volume at 0dB (0.85 normalized = 0dB)",
        "verify": "Check Track 1 volume fader shows ~0.0 dB in Live"
    },
    {
        "description": "Track 1 volume to 0.0 (normalized, -inf dB)",
        "intent": {
            "domain": "track",
            "action": "set",
            "track_index": 1,
            "field": "volume",
            "value": 0.0
        },
        "expected": "Track 1 volume at minimum (-inf dB)",
        "verify": "Check Track 1 volume fader at bottom"
    },
    {
        "description": "Track 1 volume to 1.0 (normalized, +6dB)",
        "intent": {
            "domain": "track",
            "action": "set",
            "track_index": 1,
            "field": "volume",
            "value": 1.0
        },
        "expected": "Track 1 volume at maximum (+6dB)",
        "verify": "Check Track 1 volume fader at top showing +6.0 dB"
    },

    # ============================================================================
    # TRACK PAN TESTS
    # ============================================================================
    {
        "description": "Track 1 pan to -0.5 (50% left)",
        "intent": {
            "domain": "track",
            "action": "set",
            "track_index": 1,
            "field": "pan",
            "value": -0.5
        },
        "expected": "Track 1 panned 50% left",
        "verify": "Check Track 1 pan knob shows 50L in Live"
    },
    {
        "description": "Track 1 pan to 0.5 (50% right)",
        "intent": {
            "domain": "track",
            "action": "set",
            "track_index": 1,
            "field": "pan",
            "value": 0.5
        },
        "expected": "Track 1 panned 50% right",
        "verify": "Check Track 1 pan knob shows 50R in Live"
    },
    {
        "description": "Track 1 pan to 0.0 (center)",
        "intent": {
            "domain": "track",
            "action": "set",
            "track_index": 1,
            "field": "pan",
            "value": 0.0
        },
        "expected": "Track 1 panned center",
        "verify": "Check Track 1 pan knob shows center (C) in Live"
    },

    # ============================================================================
    # TRACK MUTE/SOLO TESTS
    # ============================================================================
    {
        "description": "Mute Track 1",
        "intent": {
            "domain": "track",
            "action": "set",
            "track_index": 1,
            "field": "mute",
            "value": 1.0
        },
        "expected": "Track 1 muted (mute button lit)",
        "verify": "Check Track 1 mute button is orange/lit in Live"
    },
    {
        "description": "Unmute Track 1",
        "intent": {
            "domain": "track",
            "action": "set",
            "track_index": 1,
            "field": "mute",
            "value": 0.0
        },
        "expected": "Track 1 unmuted",
        "verify": "Check Track 1 mute button is off/gray in Live"
    },
    {
        "description": "Solo Track 2",
        "intent": {
            "domain": "track",
            "action": "set",
            "track_index": 2,
            "field": "solo",
            "value": 1.0
        },
        "expected": "Track 2 soloed (solo button lit)",
        "verify": "Check Track 2 solo button is blue/lit in Live"
    },
    {
        "description": "Unsolo Track 2",
        "intent": {
            "domain": "track",
            "action": "set",
            "track_index": 2,
            "field": "solo",
            "value": 0.0
        },
        "expected": "Track 2 unsoloed",
        "verify": "Check Track 2 solo button is off/gray in Live"
    },

    # ============================================================================
    # TRACK SEND TESTS (NEW - with dB support!)
    # ============================================================================
    {
        "description": "Track 1 Send A to -12dB",
        "intent": {
            "domain": "track",
            "action": "set",
            "track_index": 1,
            "field": "send",
            "send_index": 1,
            "value": -12.0,
            "unit": "dB"
        },
        "expected": "Track 1 Send A at -12dB",
        "verify": "Check Track 1 Send A knob shows -12.0 dB in Live"
    },
    {
        "description": "Track 1 Send A to 0dB (max for sends)",
        "intent": {
            "domain": "track",
            "action": "set",
            "track_index": 1,
            "field": "send",
            "send_index": 1,
            "value": 0.0,
            "unit": "dB"
        },
        "expected": "Track 1 Send A at 0dB (maximum)",
        "verify": "Check Track 1 Send A knob shows 0.0 dB in Live"
    },
    {
        "description": "Track 2 Send B to -20dB",
        "intent": {
            "domain": "track",
            "action": "set",
            "track_index": 2,
            "field": "send",
            "send_index": 2,
            "value": -20.0,
            "unit": "dB"
        },
        "expected": "Track 2 Send B at -20dB",
        "verify": "Check Track 2 Send B knob shows -20.0 dB in Live"
    },
    {
        "description": "Track 1 Send A to 0.5 (normalized)",
        "intent": {
            "domain": "track",
            "action": "set",
            "track_index": 1,
            "field": "send",
            "send_index": 1,
            "value": 0.5
        },
        "expected": "Track 1 Send A at ~50% (normalized)",
        "verify": "Check Track 1 Send A knob is roughly in the middle"
    },

    # ============================================================================
    # RETURN TRACK TESTS (NEW - with dB support!)
    # ============================================================================
    {
        "description": "Return A (Return 1) volume to -3dB",
        "intent": {
            "domain": "return",
            "action": "set",
            "return_index": 1,
            "field": "volume",
            "value": -3.0,
            "unit": "dB"
        },
        "expected": "Return A volume fader at -3dB",
        "verify": "Check Return A (first return track) volume shows -3.0 dB in Live"
    },
    {
        "description": "Return A volume to 0dB",
        "intent": {
            "domain": "return",
            "action": "set",
            "return_index": 1,
            "field": "volume",
            "value": 0.0,
            "unit": "dB"
        },
        "expected": "Return A volume fader at 0dB (unity)",
        "verify": "Check Return A volume shows 0.0 dB in Live"
    },
    {
        "description": "Return A pan to -1.0 (full left)",
        "intent": {
            "domain": "return",
            "action": "set",
            "return_index": 1,
            "field": "pan",
            "value": -1.0
        },
        "expected": "Return A panned full left",
        "verify": "Check Return A pan knob shows 100L in Live"
    },
    {
        "description": "Return B mute",
        "intent": {
            "domain": "return",
            "action": "set",
            "return_index": 2,
            "field": "mute",
            "value": 1.0
        },
        "expected": "Return B muted",
        "verify": "Check Return B (second return) mute button is lit in Live"
    },
    {
        "description": "Return B send to Return C at -10dB",
        "intent": {
            "domain": "return",
            "action": "set",
            "return_index": 2,
            "field": "send",
            "send_index": 3,
            "value": -10.0,
            "unit": "dB"
        },
        "expected": "Return B send to Return C at -10dB",
        "verify": "Check Return B's Send C knob shows -10.0 dB in Live"
    },

    # ============================================================================
    # MASTER TRACK TESTS
    # ============================================================================
    {
        "description": "Master volume to -6dB",
        "intent": {
            "domain": "master",
            "action": "set",
            "field": "volume",
            "value": -6.0,
            "unit": "dB"
        },
        "expected": "Master volume fader at -6dB",
        "verify": "Check Master track volume shows -6.0 dB in Live"
    },
    {
        "description": "Master volume to 0dB",
        "intent": {
            "domain": "master",
            "action": "set",
            "field": "volume",
            "value": 0.0,
            "unit": "dB"
        },
        "expected": "Master volume fader at 0dB (unity)",
        "verify": "Check Master track volume shows 0.0 dB in Live"
    },
    {
        "description": "Master pan to 0.3 (30% right)",
        "intent": {
            "domain": "master",
            "action": "set",
            "field": "pan",
            "value": 0.3
        },
        "expected": "Master panned 30% right",
        "verify": "Check Master pan knob shows ~30R in Live"
    },

    # ============================================================================
    # DEVICE PARAMETER TESTS (if you have a Reverb on Return A)
    # ============================================================================
    {
        "description": "Return A Device 1 parameter by fuzzy name (decay)",
        "intent": {
            "domain": "device",
            "action": "set",
            "return_index": 1,
            "device_index": 1,
            "param_ref": "decay",
            "value": 0.75
        },
        "expected": "Return A first device decay parameter at 75%",
        "verify": "Check Return A first device's decay parameter is at ~75%"
    },
    {
        "description": "Return A Device 1 parameter by index",
        "intent": {
            "domain": "device",
            "action": "set",
            "return_index": 1,
            "device_index": 1,
            "param_index": 0,
            "value": 0.3
        },
        "expected": "Return A first device parameter 0 at 30%",
        "verify": "Check Return A first device's first parameter is at ~30%"
    },

    # ============================================================================
    # EDGE CASES & VALIDATION
    # ============================================================================
    {
        "description": "Test clamping: Track 1 volume to -100dB (should clamp to -60dB)",
        "intent": {
            "domain": "track",
            "action": "set",
            "track_index": 1,
            "field": "volume",
            "value": -100.0,
            "unit": "dB"
        },
        "expected": "Track 1 volume clamped to minimum (-60dB)",
        "verify": "Check Track 1 volume shows minimum value (not -100)"
    },
    {
        "description": "Test clamping: Track 1 volume to +20dB (should clamp to +6dB)",
        "intent": {
            "domain": "track",
            "action": "set",
            "track_index": 1,
            "field": "volume",
            "value": 20.0,
            "unit": "dB"
        },
        "expected": "Track 1 volume clamped to maximum (+6dB)",
        "verify": "Check Track 1 volume shows +6.0 dB (maximum, not +20)"
    },
    {
        "description": "Test 1-based indexing: Track 3 volume to -10dB",
        "intent": {
            "domain": "track",
            "action": "set",
            "track_index": 3,
            "field": "volume",
            "value": -10.0,
            "unit": "dB"
        },
        "expected": "Track 3 (THIRD track, not second) volume at -10dB",
        "verify": "Check THIRD track (not second) volume shows -10.0 dB"
    },
]


def main():
    """Main test runner."""
    print_header("INTENTS API LIVE TESTING - Interactive Mode")
    print(f"\n{Colors.CYAN}This will test the Intents API against actual Ableton Live.{Colors.ENDC}")
    print(f"{Colors.CYAN}Each test will execute and wait for your verification.{Colors.ENDC}")

    # Pre-flight check
    print_info("\nPre-flight check...")
    try:
        response = requests.get(f"{SERVER_URL}/health", timeout=2.0)
        if response.status_code == 200:
            print_success("Server is reachable")
        else:
            print_error(f"Server returned status {response.status_code}")
            sys.exit(1)
    except Exception as e:
        print_error(f"Cannot connect to server: {e}")
        print_info("Make sure the server is running: cd server && make dev-returns")
        sys.exit(1)

    print_info("Make sure Ableton Live is running and has:")
    print("  • At least 3 tracks")
    print("  • At least 2 return tracks (Return A, Return B)")
    print("  • Optionally: A Reverb device on Return A for device tests")

    response = wait_for_user("\nReady to start testing?")
    if response == 'q':
        print_info("Aborted")
        sys.exit(0)

    # Run tests
    total_tests = len(TESTS)
    passed = 0
    failed = 0
    skipped = 0

    for i, test in enumerate(TESTS, 1):
        result = run_test(
            test_num=i,
            total=total_tests,
            description=test["description"],
            intent=test["intent"],
            expected=test["expected"],
            verify_instructions=test["verify"]
        )

        if result is True:
            passed += 1
        elif result is False:
            failed += 1
        else:
            skipped += 1

    # Summary
    print_header("TEST SUMMARY")
    print(f"\n{Colors.GREEN}Passed: {passed}{Colors.ENDC}")
    print(f"{Colors.RED}Failed: {failed}{Colors.ENDC}")
    print(f"{Colors.YELLOW}Skipped: {skipped}{Colors.ENDC}")
    print(f"{Colors.BOLD}Total: {total_tests}{Colors.ENDC}")

    if failed == 0 and passed > 0:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 All tests passed!{Colors.ENDC}")
    elif failed > 0:
        print(f"\n{Colors.RED}{Colors.BOLD}⚠️  Some tests failed. Review the output above.{Colors.ENDC}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Test session interrupted by user{Colors.ENDC}")
        sys.exit(0)
