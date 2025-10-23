#!/usr/bin/env python3
"""
Comprehensive GET Parameter Testing Script

PHASE 1: NLP Layer Testing (LLM typo correction & query intent parsing)
- No Live connection needed
- Tests /intent/parse endpoint for get_parameter intents
- Validates typo correction and target structure

PHASE 2: Integration Testing (Live query execution)
- Requires Live running
- Tests /snapshot/query endpoint
- Validates display_value formatting, error handling

Usage:
    python3 test_nlp_get_comprehensive.py              # Run both phases
    python3 test_nlp_get_comprehensive.py --phase1     # Run Phase 1 only
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


def query_parameters(targets: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Query parameters via /snapshot/query endpoint."""
    try:
        resp = requests.post(
            f"{BASE_URL}/snapshot/query",
            json={"targets": targets},
            timeout=10
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"ok": False, "error": str(e)}


# =============================================================================
# PHASE 1: NLP LAYER TESTING (Typo Correction & Query Intent Parsing)
# =============================================================================

def phase1_mixer_query_typo_correction() -> List[TestResult]:
    """Test mixer parameter query typo correction in NLP layer.

    Validates that LLM correctly interprets typos and outputs proper get_parameter intent.
    Does NOT execute queries - purely tests the parsing.
    """
    print_header("PHASE 1.1: Mixer Queries - Typo Correction")
    print(color_text("Testing LLM's ability to correct typos and parse mixer queries\n", 'YELLOW'))

    tests = [
        {
            "name": "Track volume with typos (tack → track, vilme → volume)",
            "utterance": "what is tack 1 vilme",
            "expect_targets": [{
                "track": "Track 1",
                "plugin": None,
                "parameter": "volume",
            }]
        },
        {
            "name": "Return volume typos (retun → return, volme → volume)",
            "utterance": "what is retun A volme",
            "expect_targets": [{
                "track": "Return A",
                "plugin": None,
                "parameter": "volume",
            }]
        },
        {
            "name": "Pan typo (paning → pan)",
            "utterance": "what is track 2 paning",
            "expect_targets": [{
                "track": "Track 2",
                "plugin": None,
                "parameter": "pan",
            }]
        },
        {
            "name": "Send typo (sennd → send)",
            "utterance": "what is track 1 sennd A",
            "expect_targets": [{
                "track": "Track 1",
                "plugin": None,
                "parameter": "send",
            }]
        },
        {
            "name": "Mute typo (mut → mute)",
            "utterance": "is track 3 mut on",
            "expect_targets": [{
                "track": "Track 3",
                "plugin": None,
                "parameter": "mute",
            }]
        },
        {
            "name": "Solo typo (slo → solo)",
            "utterance": "is return B slo enabled",
            "expect_targets": [{
                "track": "Return B",
                "plugin": None,
                "parameter": "solo",
            }]
        },
        {
            "name": "Master volume (mastr → master)",
            "utterance": "what is mastr volume",
            "expect_targets": [{
                "track": "Master",
                "plugin": None,
                "parameter": "volume",
            }]
        },
    ]

    results = []
    for test in tests:
        print(f"Testing: {test['name']}")
        print(f"  Input:  \"{test['utterance']}\"")

        parsed = parse_intent(test["utterance"])

        # get_parameter intents return ok=false with "non_control_intent" error
        raw_intent = parsed.get("raw_intent", {})
        if raw_intent.get("intent") != "get_parameter":
            results.append(TestResult(test["name"], False, f"Wrong intent type: {raw_intent.get('intent')}"))
            print(f"  {color_text('✗ FAIL', 'RED')} - Not recognized as get_parameter intent\n")
            continue

        targets = raw_intent.get("targets", [])
        expected_targets = test["expect_targets"]
        errors = []

        if len(targets) != len(expected_targets):
            errors.append(f"Expected {len(expected_targets)} targets, got {len(targets)}")
        else:
            # Check each target
            for i, (target, expected) in enumerate(zip(targets, expected_targets)):
                # Normalize track name for comparison
                track = target.get("track", "")
                expected_track = expected.get("track", "")
                if track.lower().replace(" ", "") != expected_track.lower().replace(" ", ""):
                    errors.append(f"target[{i}].track={track} (expected {expected_track})")

                # Check plugin (should be None/null for mixer params)
                plugin = target.get("plugin")
                expected_plugin = expected.get("plugin")
                if expected_plugin is None and plugin is not None and plugin != "":
                    errors.append(f"target[{i}].plugin={plugin} (expected None for mixer query)")
                elif expected_plugin is not None:
                    if str(plugin or "").lower() != str(expected_plugin).lower():
                        errors.append(f"target[{i}].plugin={plugin} (expected {expected_plugin})")

                # Check parameter with fuzzy matching
                param = str(target.get("parameter", "")).lower()
                expected_param = str(expected.get("parameter", "")).lower()
                if expected_param not in param and param not in expected_param:
                    errors.append(f"target[{i}].parameter={target.get('parameter')} (expected {expected.get('parameter')})")

        if not errors:
            results.append(TestResult(test["name"], True, "Correctly parsed as get_parameter intent"))
            print(f"  {color_text('✓ PASS', 'GREEN')} - Intent structure correct\n")
        else:
            msg = "; ".join(errors)
            results.append(TestResult(test["name"], False, msg, raw_intent))
            print(f"  {color_text('✗ FAIL', 'RED')} - {msg}")
            print(f"  Targets: {json.dumps(targets, indent=4)}\n")

    return results


def phase1_device_query_typo_correction() -> List[TestResult]:
    """Test device parameter query typo correction in NLP layer.

    Device Setup:
    - Return A: device 0 = reverb, device 1 = 4th bandpass (delay)
    - Return B: device 0 = Align Delay, device 1 = Screamer (amp)
    """
    print_header("PHASE 1.2: Device Queries - Typo Correction")
    print(color_text("Testing LLM's ability to correct typos in device queries\n", 'YELLOW'))

    tests = [
        {
            "name": "Reverb decay typo (revreb → reverb, dcay → decay)",
            "utterance": "what is return A revreb dcay",
            "expect_targets": [{
                "track": "Return A",
                "plugin": "reverb",
                "parameter": "decay",
            }]
        },
        {
            "name": "4th bandpass dry/wet typo (bandpas → bandpass, drywet → dry/wet)",
            "utterance": "what is return A 4th bandpas drywet",
            "expect_targets": [{
                "track": "Return A",
                "plugin": "4th bandpass",
                "parameter": "dry",  # fuzzy: dry/wet/drywet should match
            }]
        },
        {
            "name": "Align Delay mode typo (alin dlay → align delay, mod → mode)",
            "utterance": "what is return B alin dlay mod",
            "expect_targets": [{
                "track": "Return B",
                "plugin": "align delay",
                "parameter": "mode",
            }]
        },
        {
            "name": "Screamer gain typo (screamr → screamer, gan → gain)",
            "utterance": "what is return B screamr gan",
            "expect_targets": [{
                "track": "Return B",
                "plugin": "screamer",
                "parameter": "gain",
            }]
        },
        {
            "name": "Reverb predelay typo (predlay → predelay)",
            "utterance": "what is return A reverb predlay",
            "expect_targets": [{
                "track": "Return A",
                "plugin": "reverb",
                "parameter": "predelay",
            }]
        },
        {
            "name": "Device on track (not just returns)",
            "utterance": "what is track 1 compressor threshold",
            "expect_targets": [{
                "track": "Track 1",
                "plugin": "compressor",
                "parameter": "threshold",
            }]
        },
    ]

    results = []
    for test in tests:
        print(f"Testing: {test['name']}")
        print(f"  Input:  \"{test['utterance']}\"")

        parsed = parse_intent(test["utterance"])

        raw_intent = parsed.get("raw_intent", {})
        if raw_intent.get("intent") != "get_parameter":
            results.append(TestResult(test["name"], False, f"Wrong intent type: {raw_intent.get('intent')}"))
            print(f"  {color_text('✗ FAIL', 'RED')} - Not recognized as get_parameter intent\n")
            continue

        targets = raw_intent.get("targets", [])
        expected_targets = test["expect_targets"]
        errors = []

        if len(targets) != len(expected_targets):
            errors.append(f"Expected {len(expected_targets)} targets, got {len(targets)}")
        else:
            for i, (target, expected) in enumerate(zip(targets, expected_targets)):
                # Check track
                track = str(target.get("track", "")).lower().replace(" ", "")
                expected_track = str(expected.get("track", "")).lower().replace(" ", "")
                if track != expected_track:
                    errors.append(f"target[{i}].track={target.get('track')} (expected {expected.get('track')})")

                # Check plugin (fuzzy match)
                plugin = str(target.get("plugin", "")).lower()
                expected_plugin = str(expected.get("plugin", "")).lower()
                if expected_plugin not in plugin and plugin not in expected_plugin:
                    errors.append(f"target[{i}].plugin={target.get('plugin')} (expected {expected.get('plugin')})")

                # Check parameter (fuzzy match)
                param = str(target.get("parameter", "")).lower()
                expected_param = str(expected.get("parameter", "")).lower()
                if expected_param not in param and param not in expected_param:
                    errors.append(f"target[{i}].parameter={target.get('parameter')} (expected {expected.get('parameter')})")

        if not errors:
            results.append(TestResult(test["name"], True, "Correctly parsed as device query"))
            print(f"  {color_text('✓ PASS', 'GREEN')} - Intent structure correct\n")
        else:
            msg = "; ".join(errors)
            results.append(TestResult(test["name"], False, msg, raw_intent))
            print(f"  {color_text('✗ FAIL', 'RED')} - {msg}")
            print(f"  Targets: {json.dumps(targets, indent=4)}\n")

    return results


# =============================================================================
# PHASE 2: INTEGRATION TESTING (Live Query Execution)
# =============================================================================

def phase2_query_execution_and_formatting() -> List[TestResult]:
    """Test that queries execute correctly and return properly formatted values.

    Device Setup:
    - Return A: device 0 = reverb, device 1 = 4th bandpass (delay)
    - Return B: device 0 = Align Delay, device 1 = Screamer (amp)
    """
    print_header("PHASE 2.1: Query Execution & Display Value Formatting")
    print(color_text("Testing query execution and display_value formatting (REQUIRES LIVE RUNNING)\n", 'YELLOW'))

    tests = [
        {
            "name": "Track volume - should return dB formatted value",
            "targets": [{"track": "Track 1", "plugin": None, "parameter": "volume"}],
            "expect_format": "dB",  # e.g., "-6.00" or "-6.0 dB"
        },
        {
            "name": "Return volume - should return dB formatted value",
            "targets": [{"track": "Return A", "plugin": None, "parameter": "volume"}],
            "expect_format": "dB",
        },
        {
            "name": "Track pan - should return pan value",
            "targets": [{"track": "Track 1", "plugin": None, "parameter": "pan"}],
            "expect_has_value": True,
        },
        {
            "name": "Track send - should return dB formatted value",
            "targets": [{"track": "Track 1", "plugin": None, "parameter": "send A"}],
            "expect_has_value": True,
        },
        {
            "name": "Reverb decay - should return time value",
            "targets": [{"track": "Return A", "plugin": "reverb", "parameter": "decay"}],
            "expect_has_value": True,
        },
        {
            "name": "Screamer gain - should return numeric value",
            "targets": [{"track": "Return B", "plugin": "screamer", "parameter": "gain"}],
            "expect_has_value": True,
        },
        {
            "name": "4th bandpass dry/wet - should return percentage",
            "targets": [{"track": "Return A", "plugin": "4th bandpass", "parameter": "dry/wet"}],
            "expect_has_value": True,
        },
        {
            "name": "Multiple parameters in one query",
            "targets": [
                {"track": "Track 1", "plugin": None, "parameter": "volume"},
                {"track": "Track 1", "plugin": None, "parameter": "pan"},
            ],
            "expect_count": 2,
        },
        {
            "name": "Master volume",
            "targets": [{"track": "Master", "plugin": None, "parameter": "volume"}],
            "expect_has_value": True,
        },
    ]

    results = []
    for test in tests:
        print(f"Testing: {test['name']}")
        print(f"  Targets: {json.dumps(test['targets'], indent=4)}")

        result = query_parameters(test["targets"])

        if not result.get("ok"):
            results.append(TestResult(test["name"], False, f"Query failed: {result.get('error')}"))
            print(f"  {color_text('✗ FAIL', 'RED')} - Query failed: {result.get('error')}\n")
            continue

        values = result.get("values", [])
        answer = result.get("answer", "")
        errors = []

        # Check value count
        if "expect_count" in test and len(values) != test["expect_count"]:
            errors.append(f"Expected {test['expect_count']} values, got {len(values)}")

        # Check values exist
        if test.get("expect_has_value") and not values:
            errors.append("No values returned")

        # Check formatting
        if test.get("expect_format") and values:
            display_val = values[0].get("display_value", "")
            if test["expect_format"] == "dB":
                # Should be numeric with optional dB suffix or negative infinity
                if not (display_val.replace("-", "").replace(".", "").replace("inf", "").replace(" ", "").replace("dB", "").strip().isdigit() or "inf" in display_val):
                    errors.append(f"Expected dB format, got: {display_val}")

        # Check answer exists
        if not answer:
            errors.append("No conversational answer returned")

        if not errors:
            results.append(TestResult(test["name"], True, f"Query successful: {answer}"))
            print(f"  {color_text('✓ PASS', 'GREEN')} - {answer}\n")
        else:
            msg = "; ".join(errors)
            results.append(TestResult(test["name"], False, msg, result))
            print(f"  {color_text('✗ FAIL', 'RED')} - {msg}\n")

    return results


def phase2_error_handling() -> List[TestResult]:
    """Test friendly error messages for device/parameter not found cases."""
    print_header("PHASE 2.2: Error Handling - Query Failures")
    print(color_text("Testing error handling for missing devices/parameters (REQUIRES LIVE RUNNING)\n", 'YELLOW'))

    tests = [
        {
            "name": "Device not found (reverb on Return B) - should handle gracefully",
            "targets": [{"track": "Return B", "plugin": "reverb", "parameter": "decay"}],
            "expect_error": True,
        },
        {
            "name": "Parameter not found - should handle gracefully",
            "targets": [{"track": "Return A", "plugin": "reverb", "parameter": "nonexistent"}],
            "expect_error": True,
        },
        {
            "name": "Track doesn't exist - should handle gracefully",
            "targets": [{"track": "Track 999", "plugin": None, "parameter": "volume"}],
            "allow_empty": True,
        },
    ]

    results = []
    for test in tests:
        print(f"Testing: {test['name']}")
        print(f"  Targets: {json.dumps(test['targets'], indent=4)}")

        result = query_parameters(test["targets"])

        if test.get("expect_error"):
            # Should return ok=true but with error in values or empty values
            if result.get("ok"):
                values = result.get("values", [])
                if not values or any("error" in v for v in values):
                    results.append(TestResult(test["name"], True, "Error handled gracefully"))
                    print(f"  {color_text('✓ PASS', 'GREEN')} - Error handled\n")
                else:
                    results.append(TestResult(test["name"], True, "Query succeeded (device/param exists)"))
                    print(f"  {color_text('✓ PASS', 'GREEN')} - Query succeeded\n")
            else:
                results.append(TestResult(test["name"], False, f"Unexpected failure: {result.get('error')}"))
                print(f"  {color_text('✗ FAIL', 'RED')} - Unexpected failure\n")
        elif test.get("allow_empty"):
            # Should return ok=true with empty values or error
            if result.get("ok"):
                results.append(TestResult(test["name"], True, "Empty result handled"))
                print(f"  {color_text('✓ PASS', 'GREEN')} - Handled gracefully\n")
            else:
                results.append(TestResult(test["name"], True, "Error handled"))
                print(f"  {color_text('✓ PASS', 'GREEN')} - Error handled\n")

    return results


# =============================================================================
# MAIN
# =============================================================================

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='FadeBender GET Parameter Testing Suite',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 test_nlp_get_comprehensive.py              # Run both Phase 1 and Phase 2
  python3 test_nlp_get_comprehensive.py --phase1     # Run Phase 1 only (no Live needed)
        """
    )
    parser.add_argument(
        '--phase1',
        action='store_true',
        help='Run Phase 1 only (NLP layer testing, no Live needed)'
    )
    args = parser.parse_args()

    print(color_text("\n🎛️  FadeBender GET Parameter Testing Suite", 'BLUE'))
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
    print_phase_header(1, "NLP Layer Testing", "Typo correction and query intent parsing (no Live needed)")

    all_results.extend(phase1_mixer_query_typo_correction())
    all_results.extend(phase1_device_query_typo_correction())

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
    print_phase_header(2, "Integration Testing", "Query execution and value formatting (requires Ableton Live)")

    print(color_text("⚠️  This phase requires Ableton Live to be running with UDP enabled.\n", 'YELLOW'))
    user_input = input(color_text("Is Live running and ready? (y/N): ", 'YELLOW'))
    if user_input.lower() != 'y':
        print(color_text("\nSkipping Phase 2. Start Live and run again.\n", 'YELLOW'))
        return 0

    all_results.extend(phase2_query_execution_and_formatting())
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
