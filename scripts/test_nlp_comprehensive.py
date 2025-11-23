#!/usr/bin/env python3
"""
Comprehensive NLP + Intent Testing Script

PHASE 1: NLP Layer Testing (LLM typo correction & intent parsing)
- No Live connection needed
- Tests /intent/parse endpoint
- Validates typo correction and intent structure

PHASE 2: Integration Testing (Live execution)
- Requires Live running
- Tests /chat endpoint
- Validates execution, capabilities sync, error handling

Usage:
    python3 test_nlp_comprehensive.py              # Run both phases
    python3 test_nlp_comprehensive.py --phase1     # Run Phase 1 only
"""
import requests
import json
import sys
import argparse
from typing import Dict, Any, List, Optional
from datetime import datetime

BASE_URL = "http://127.0.0.1:8722"
COLORS = {
    'GREEN': '\033[92m',
    'RED': '\033[91m',
    'YELLOW': '\033[93m',
    'BLUE': '\033[94m',
    'CYAN': '\033[96m',
    'END': '\033[0m'
}

class TestResult:
    def __init__(self, name: str, passed: bool, message: str = "", details: Any = None):
        self.name = name
        self.passed = passed
        self.message = message
        self.details = details


def color_text(text: str, color: str) -> str:
    return f"{COLORS.get(color, '')}{text}{COLORS['END']}"


def print_header(text: str):
    print(f"\n{color_text('='*80, 'BLUE')}")
    print(color_text(f"  {text}", 'BLUE'))
    print(color_text('='*80, 'BLUE') + "\n")


def print_phase_header(phase: int, title: str, description: str):
    print(f"\n{color_text('█'*80, 'CYAN')}")
    print(color_text(f"  PHASE {phase}: {title}", 'CYAN'))
    print(color_text(f"  {description}", 'CYAN'))
    print(color_text('█'*80, 'CYAN') + "\n")


def parse_intent(utterance: str) -> Dict[str, Any]:
    """Parse intent via /intent/parse endpoint (NLP layer only)."""
    try:
        resp = requests.post(
            f"{BASE_URL}/intent/parse",
            json={"text": utterance},
            timeout=10
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"ok": False, "error": str(e)}


def execute_chat(utterance: str) -> Dict[str, Any]:
    """Execute command via /chat endpoint (full integration)."""
    try:
        resp = requests.post(
            f"{BASE_URL}/chat",
            json={"text": utterance, "confirm": True},
            timeout=15
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"ok": False, "error": str(e)}


# =============================================================================
# PHASE 1: NLP LAYER TESTING (Typo Correction & Intent Parsing)
# =============================================================================

def phase1_mixer_typo_correction() -> List[TestResult]:
    """Test mixer parameter typo correction in NLP layer.

    Validates that LLM correctly interprets typos and outputs proper intent structure.
    Does NOT execute in Live - purely tests the parsing.
    """
    print_header("PHASE 1.1: Mixer Operations - Typo Correction")
    print(color_text("Testing LLM's ability to correct typos and parse mixer commands\n", 'YELLOW'))

    tests = [
        {
            "name": "Track volume with typos (tack → track, vilme → volume)",
            "utterance": "set tack 1 vilme to -20",
            "expect_intent": {
                "domain": "track",
                "track_index": 1,
                "field": "volume",
                "device_name_hint": None,  # Should be null for mixer ops
                "value": -20,
            }
        },
        {
            "name": "Return volume typos (retun → return, volme → volume)",
            "utterance": "set retun A volme to -6 dB",
            "expect_intent": {
                "domain": "return",
                "return_ref": "A",
                "field": "volume",
                "device_name_hint": None,
                "value": -6,
                "unit": "dB",
            }
        },
        {
            "name": "Pan typo (paning → pan)",
            "utterance": "set track 2 paning to 25% left",
            "expect_intent": {
                "domain": "track",
                "track_index": 2,
                "field": "pan",
                "device_name_hint": None,
                "value": -25,  # 25% left = -25
            }
        },
        {
            "name": "Send typo (sennd → send)",
            "utterance": "set track 1 sennd A to -12 dB",
            "expect_intent": {
                "domain": "track",
                "track_index": 1,
                "field": "send",
                "device_name_hint": None,
                "value": -12,
                "unit": "dB",
            }
        },
    ]

    results = []
    for test in tests:
        print(f"Testing: {test['name']}")
        print(f"  Input:  \"{test['utterance']}\"")

        parsed = parse_intent(test["utterance"])

        if not parsed.get("ok"):
            results.append(TestResult(test["name"], False, f"Parse failed: {parsed.get('error')}"))
            print(f"  {color_text('✗ FAIL', 'RED')} - Parse failed: {parsed.get('error')}\n")
            continue

        intent = parsed.get("intent", {})
        expected = test["expect_intent"]
        errors = []

        # Check each expected field
        for key, expected_val in expected.items():
            actual_val = intent.get(key)

            # Special handling for fields that might use fuzzy matching
            if key == "field":
                actual_field = str(actual_val or "").lower()
                expected_field = str(expected_val or "").lower()
                if expected_field not in actual_field and actual_field not in expected_field:
                    errors.append(f"{key}={actual_val} (expected {expected_val})")
            elif key == "device_name_hint" and expected_val is None:
                # For mixer ops, device_name_hint should be None or not present
                if actual_val is not None and actual_val != "":
                    errors.append(f"{key}={actual_val} (expected None/absent for mixer op)")
            elif actual_val != expected_val:
                # Allow some flexibility for numeric values
                if isinstance(expected_val, (int, float)) and isinstance(actual_val, (int, float)):
                    if abs(actual_val - expected_val) > 0.01:
                        errors.append(f"{key}={actual_val} (expected {expected_val})")
                else:
                    errors.append(f"{key}={actual_val} (expected {expected_val})")

        if not errors:
            results.append(TestResult(test["name"], True, "Correctly parsed as mixer operation"))
            print(f"  {color_text('✓ PASS', 'GREEN')} - Intent structure correct\n")
        else:
            msg = "; ".join(errors)
            results.append(TestResult(test["name"], False, msg, intent))
            print(f"  {color_text('✗ FAIL', 'RED')} - {msg}")
            print(f"  Intent: {json.dumps(intent, indent=4)}\n")

    return results


def phase1_device_typo_correction() -> List[TestResult]:
    """Test device parameter typo correction in NLP layer.

    Device Setup:
    - Return A: device 0 = reverb, device 1 = 4th bandpass (delay)
    - Return B: device 0 = Align Delay, device 1 = Screamer (amp)
    """
    print_header("PHASE 1.2: Device Operations - Typo Correction")
    print(color_text("Testing LLM's ability to correct typos in device commands\n", 'YELLOW'))

    tests = [
        {
            "name": "Reverb decay typo (revreb → reverb, dcay → decay)",
            "utterance": "set return A revreb dcay to 2 s",
            "expect_intent": {
                "domain": "device",
                "return_ref": "A",
                "device_name_hint": "reverb",
                "param_ref": "decay",
                "value": 2,
                "unit": "s",
            }
        },
        {
            "name": "4th bandpass dry/wet typo (bandpas → bandpass, drywet → dry/wet)",
            "utterance": "set return A 4th bandpas drywet to 75%",
            "expect_intent": {
                "domain": "device",
                "return_ref": "A",
                "device_name_hint": "4th bandpass",
                "param_ref": "dry",  # fuzzy: dry/wet/drywet should match
            }
        },
        {
            "name": "Align Delay mode typo (alin dlay → align delay, mod → mode)",
            "utterance": "set return B alin dlay mod to distance",
            "expect_intent": {
                "domain": "device",
                "return_ref": "B",
                "device_name_hint": "align delay",
                "param_ref": "mode",
                "display": "distance",
            }
        },
        {
            "name": "Screamer gain typo (screamr → screamer, gan → gain)",
            "utterance": "set return B screamr gan to 7.5",
            "expect_intent": {
                "domain": "device",
                "return_ref": "B",
                "device_name_hint": "screamer",
                "param_ref": "gain",
                "value": 7.5,
            }
        },
    ]

    results = []
    for test in tests:
        print(f"Testing: {test['name']}")
        print(f"  Input:  \"{test['utterance']}\"")

        parsed = parse_intent(test["utterance"])

        if not parsed.get("ok"):
            results.append(TestResult(test["name"], False, f"Parse failed: {parsed.get('error')}"))
            print(f"  {color_text('✗ FAIL', 'RED')} - Parse failed\n")
            continue

        intent = parsed.get("intent", {})
        expected = test["expect_intent"]
        errors = []

        for key, expected_val in expected.items():
            actual_val = intent.get(key)

            # Fuzzy matching for device/param names
            if key in ["device_name_hint", "param_ref"]:
                actual_str = str(actual_val or "").lower()
                expected_str = str(expected_val or "").lower()
                if expected_str not in actual_str and actual_str not in expected_str:
                    errors.append(f"{key}={actual_val} (expected {expected_val})")
            elif actual_val != expected_val:
                if isinstance(expected_val, (int, float)) and isinstance(actual_val, (int, float)):
                    if abs(actual_val - expected_val) > 0.01:
                        errors.append(f"{key}={actual_val} (expected {expected_val})")
                else:
                    errors.append(f"{key}={actual_val} (expected {expected_val})")

        if not errors:
            results.append(TestResult(test["name"], True, "Correctly parsed as device operation"))
            print(f"  {color_text('✓ PASS', 'GREEN')} - Intent structure correct\n")
        else:
            msg = "; ".join(errors)
            results.append(TestResult(test["name"], False, msg, intent))
            print(f"  {color_text('✗ FAIL', 'RED')} - {msg}")
            print(f"  Intent: {json.dumps(intent, indent=4)}\n")

    return results


# =============================================================================
# PHASE 2: INTEGRATION TESTING (Live Execution)
# =============================================================================

def phase2_execution_and_capabilities() -> List[TestResult]:
    """Test that correctly parsed intents execute in Live and return correct capabilities_ref.

    NOTE: Tests now validate capabilities_ref (lightweight reference) instead of full capabilities.
    Full capabilities are fetched on-demand by the UI using the reference.

    Device Setup:
    - Return A: device 0 = reverb, device 1 = 4th bandpass (delay)
    - Return B: device 0 = Align Delay, device 1 = Screamer (amp)
    """
    print_header("PHASE 2.1: Execution & Capabilities Reference Validation")
    print(color_text("Testing execution in Live and capabilities_ref validation (REQUIRES LIVE RUNNING)\n", 'YELLOW'))

    tests = [
        {
            "name": "4th bandpass (device) - capabilities should match device_index=1",
            "utterance": "set return A 4th bandpass dry wet to 75%",
            "expect_caps": {
                "type": "device",
                "device_name": "4th bandpass",
                "device_index": 1,
                "return_index": 0,
            }
        },
        {
            "name": "Reverb (device) - capabilities should match device_index=0",
            "utterance": "set return A reverb decay to 2 s",
            "expect_caps": {
                "type": "device",
                "device_name": "reverb",
                "device_index": 0,
                "return_index": 0,
            }
        },
        {
            "name": "Screamer (device) - capabilities should match device_index=1",
            "utterance": "set return B screamer gain to 7.5",
            "expect_caps": {
                "type": "device",
                "device_name": "screamer",
                "device_index": 1,
                "return_index": 1,
            }
        },
        {
            "name": "Track volume (mixer) - capabilities should be mixer type",
            "utterance": "set track 1 volume to -6 dB",
            "expect_caps": {
                "type": "mixer",
                "entity_type": "track",
            }
        },
        {
            "name": "Return volume (mixer) - capabilities should be mixer type",
            "utterance": "set return A volume to -3 dB",
            "expect_caps": {
                "type": "mixer",
                "entity_type": "return",
            }
        },
    ]

    results = []
    for test in tests:
        print(f"Testing: {test['name']}")
        print(f"  Command: \"{test['utterance']}\"")

        result = execute_chat(test["utterance"])

        if not result.get("ok"):
            results.append(TestResult(test["name"], False, f"Execution failed: {result.get('error') or result.get('summary')}"))
            print(f"  {color_text('✗ FAIL', 'RED')} - Execution failed: {result.get('summary', result.get('error'))}\n")
            continue

        # NEW FORMAT: Check for capabilities_ref instead of data.capabilities
        caps_ref = result.get("capabilities_ref")
        if not caps_ref:
            results.append(TestResult(test["name"], False, "No capabilities_ref returned"))
            print(f"  {color_text('✗ FAIL', 'RED')} - No capabilities_ref in response\n")
            continue

        expected = test["expect_caps"]
        errors = []

        # Validate capabilities_ref fields (lightweight reference, not full data)
        if expected["type"] == "device":
            # Device capabilities should have domain="return_device" or "track_device"
            domain = caps_ref.get("domain", "")
            if domain not in ("return_device", "track_device"):
                errors.append(f"domain={domain} (expected return_device or track_device)")

            # Validate device_index
            if caps_ref.get("device_index") != expected.get("device_index"):
                errors.append(f"device_index={caps_ref.get('device_index')} (expected {expected.get('device_index')})")

            # Validate return_index if specified
            if "return_index" in expected:
                if caps_ref.get("return_index") != expected.get("return_index"):
                    errors.append(f"return_index={caps_ref.get('return_index')} (expected {expected.get('return_index')})")

            # Note: device_name is NOT in capabilities_ref (it's in full capabilities fetched later)
            # We're just validating the reference structure here

        elif expected["type"] == "mixer":
            # Mixer capabilities should have domain="track" or "return" or "master"
            domain = caps_ref.get("domain", "")
            expected_entity = expected.get("entity_type")

            if expected_entity == "track" and domain != "track":
                errors.append(f"domain={domain} (expected track)")
            elif expected_entity == "return" and domain != "return":
                errors.append(f"domain={domain} (expected return)")
            elif expected_entity == "master" and domain != "master":
                errors.append(f"domain={domain} (expected master)")

        if not errors:
            results.append(TestResult(test["name"], True, "Executed successfully, capabilities_ref is correct"))
            print(f"  {color_text('✓ PASS', 'GREEN')} - Execution OK, capabilities_ref validated\n")
        else:
            msg = "; ".join(errors)
            results.append(TestResult(test["name"], False, msg, caps_ref))
            print(f"  {color_text('✗ FAIL', 'RED')} - {msg}\n")

    return results


def phase2_error_handling() -> List[TestResult]:
    """Test friendly error messages for device/parameter not found cases."""
    print_header("PHASE 2.2: Error Handling - Friendly Messages")
    print(color_text("Testing user-friendly error messages (REQUIRES LIVE RUNNING)\n", 'YELLOW'))

    tests = [
        {
            "name": "Device not found (reverb on Return B) - should suggest alternatives",
            "utterance": "set return B reverb decay to 2s",
            "expect_friendly": True,
        },
        {
            "name": "Parameter not found - should show friendly error",
            "utterance": "set return A reverb nonexistent to 100",
            "expect_friendly": True,
        },
        {
            "name": "Delay type hint (ambiguous) - should resolve or clarify",
            "utterance": "set return A delay dry wet to 75%",
            "allow_success": True,  # Might resolve to 4th bandpass
        },
    ]

    results = []
    for test in tests:
        print(f"Testing: {test['name']}")
        print(f"  Command: \"{test['utterance']}\"")

        result = execute_chat(test["utterance"])

        if result.get("ok"):
            if test.get("allow_success"):
                results.append(TestResult(test["name"], True, "Resolved and executed successfully"))
                print(f"  {color_text('✓ PASS', 'GREEN')} - Resolved correctly\n")
            else:
                results.append(TestResult(test["name"], True, "Executed (device exists)"))
                print(f"  {color_text('✓ PASS', 'GREEN')} - Device exists\n")
        else:
            # Check for friendly error (not raw error codes)
            summary = result.get("summary", "")
            reason = result.get("reason", "")
            error_text = summary or reason

            # Unfriendly patterns that should NOT appear in user-facing errors
            unfriendly_patterns = ["_not_found", "_ambiguous", "_out_of_range", "HTTPException"]
            is_friendly = not any(pattern in error_text for pattern in unfriendly_patterns)

            if is_friendly:
                results.append(TestResult(test["name"], True, f"Friendly error: {error_text}"))
                print(f"  {color_text('✓ PASS', 'GREEN')} - Friendly error message\n")
            else:
                results.append(TestResult(test["name"], False, f"Unfriendly error: {error_text}"))
                print(f"  {color_text('✗ FAIL', 'RED')} - Raw error code exposed to user\n")

    return results


# =============================================================================
# MAIN
# =============================================================================

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='FadeBender NLP Testing Suite',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 test_nlp_comprehensive.py              # Run both Phase 1 and Phase 2
  python3 test_nlp_comprehensive.py --phase1     # Run Phase 1 only (no Live needed)
        """
    )
    parser.add_argument(
        '--phase1',
        action='store_true',
        help='Run Phase 1 only (NLP layer testing, no Live needed)'
    )
    parser.add_argument(
        '--yes', '-y',
        action='store_true',
        help='Auto-confirm Live is running (for automated testing)'
    )
    args = parser.parse_args()

    print(color_text("\n🎛️  FadeBender Comprehensive NLP Testing Suite", 'BLUE'))
    print(color_text(f"    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 'BLUE'))
    print(color_text(f"    Target: {BASE_URL}", 'BLUE'))
    if args.phase1:
        print(color_text(f"    Mode: Phase 1 Only (NLP Layer)\n", 'YELLOW'))
    else:
        print(color_text(f"    Mode: Full Test Suite (Phase 1 + Phase 2)\n", 'BLUE'))

    # Check server health
    try:
        health = requests.get(f"{BASE_URL}/health", timeout=5)
        if health.status_code != 200:
            print(color_text("❌ Server health check failed!", 'RED'))
            return 1
        print(color_text("✓ Server is running\n", 'GREEN'))
    except Exception as e:
        print(color_text(f"❌ Cannot connect to server: {e}", 'RED'))
        return 1

    all_results = []

    # =========================================================================
    # PHASE 1: NLP LAYER TESTING (No Live needed)
    # =========================================================================
    print_phase_header(1, "NLP Layer Testing", "Typo correction and intent parsing (no Live needed)")

    all_results.extend(phase1_mixer_typo_correction())
    all_results.extend(phase1_device_typo_correction())

    phase1_results = all_results.copy()
    phase1_passed = sum(1 for r in phase1_results if r.passed)
    phase1_failed = sum(1 for r in phase1_results if not r.passed)

    print(color_text(f"\n{'─'*80}", 'CYAN'))
    print(color_text(f"PHASE 1 SUMMARY: {phase1_passed}/{len(phase1_results)} passed", 'CYAN'))
    print(color_text(f"{'─'*80}\n", 'CYAN'))

    # If --phase1 flag is set, stop here
    if args.phase1:
        print(color_text("✓ Phase 1 complete. Run without --phase1 flag to test Phase 2.\n", 'GREEN'))
        passed = phase1_passed
        failed = phase1_failed
        total = len(phase1_results)
        pass_rate = (passed / total * 100) if total > 0 else 0

        print_header("PHASE 1 FINAL SUMMARY")
        print(f"Total Tests: {total}")
        print(f"{color_text(f'Passed: {passed}', 'GREEN')}")
        print(f"{color_text(f'Failed: {failed}', 'RED')}")
        print(f"Pass Rate: {pass_rate:.1f}%\n")

        if failed > 0:
            print(color_text("Failed Tests:", 'RED'))
            for r in all_results:
                if not r.passed:
                    print(f"  ✗ {r.name}")
                    print(f"    {r.message}")
                    if r.details:
                        print(f"    Details: {json.dumps(r.details, indent=6)}")

        return 0 if failed == 0 else 1

    if phase1_failed > 0:
        print(color_text("⚠️  Phase 1 has failures. Fix NLP layer before proceeding to Phase 2.\n", 'YELLOW'))
        user_input = input(color_text("Continue to Phase 2 anyway? (y/N): ", 'YELLOW'))
        if user_input.lower() != 'y':
            print(color_text("\nStopping. Fix Phase 1 issues first.\n", 'RED'))
            return 1

    # =========================================================================
    # PHASE 2: INTEGRATION TESTING (Requires Live)
    # =========================================================================
    print_phase_header(2, "Integration Testing", "Live execution and capabilities validation (requires Ableton Live)")

    print(color_text("⚠️  This phase requires Ableton Live to be running with UDP enabled.\n", 'YELLOW'))

    if args.yes:
        print(color_text("Auto-confirming Live is running (--yes flag)\n", 'YELLOW'))
    else:
        user_input = input(color_text("Is Live running and ready? (y/N): ", 'YELLOW'))
        if user_input.lower() != 'y':
            print(color_text("\nSkipping Phase 2. Start Live and run again.\n", 'YELLOW'))
            return 0

    all_results.extend(phase2_execution_and_capabilities())
    all_results.extend(phase2_error_handling())

    # =========================================================================
    # FINAL SUMMARY
    # =========================================================================
    print_header("FINAL TEST SUMMARY")

    passed = sum(1 for r in all_results if r.passed)
    failed = sum(1 for r in all_results if not r.passed)
    total = len(all_results)
    pass_rate = (passed / total * 100) if total > 0 else 0

    print(f"Total Tests: {total}")
    print(f"{color_text(f'Passed: {passed}', 'GREEN')}")
    print(f"{color_text(f'Failed: {failed}', 'RED')}")
    print(f"Pass Rate: {pass_rate:.1f}%\n")

    if failed > 0:
        print(color_text("\nFailed Tests:", 'RED'))
        for r in all_results:
            if not r.passed:
                print(f"  ✗ {r.name}")
                print(f"    {r.message}")
                if r.details:
                    print(f"    Details: {json.dumps(r.details, indent=6)}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
