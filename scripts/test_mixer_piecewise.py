#!/usr/bin/env python3
"""
Comprehensive Mixer Piecewise Mapping Test

Tests all mixer operations across tracks, returns, and master:
- Absolute sets (volume, send, pan, cue)
- Relative changes (increase by, decrease by, reduce)
- Pan operations (pan left by, pan right by)

Can run in two modes:
1. DRY RUN (no Live needed): Tests conversion logic only
2. LIVE MODE (requires Live): Full integration test with actual Live communication

Usage:
    python3 test_mixer_piecewise.py              # Run dry-run mode
    python3 test_mixer_piecewise.py --live       # Run with Live (requires Live running)
"""
import sys
import os
import argparse
from typing import Dict, Any, List, Optional, Tuple

# Add server to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'server'))

from services.intents.utils.mixer import (
    get_mixer_param_meta,
    apply_mixer_fit_forward,
    apply_mixer_fit_inverse,
)

# Terminal colors
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    END = '\033[0m'
    BOLD = '\033[1m'

def color(text: str, c: str) -> str:
    return f"{c}{text}{Colors.END}"

class TestStats:
    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.skipped = 0

    def record_pass(self):
        self.total += 1
        self.passed += 1

    def record_fail(self):
        self.total += 1
        self.failed += 1

    def record_skip(self):
        self.total += 1
        self.skipped += 1

def print_header(text: str):
    print(f"\n{color('='*80, Colors.BLUE)}")
    print(color(f"  {text}", Colors.BOLD + Colors.BLUE))
    print(color('='*80, Colors.BLUE))

def print_test_result(name: str, passed: bool, details: str = ""):
    status = color("✓ PASS", Colors.GREEN) if passed else color("✗ FAIL", Colors.RED)
    print(f"{status} | {name}")
    if details:
        print(f"         {details}")

# ==============================================================================
# CONVERSION ACCURACY TESTS (No Live needed)
# ==============================================================================

def test_volume_conversion_accuracy(entity_type: str, param_name: str, stats: TestStats) -> bool:
    """Test volume/cue conversion accuracy using piecewise fit."""
    print(f"\n{color(f'Testing {entity_type}.{param_name} conversions', Colors.CYAN)}")

    pm = get_mixer_param_meta(entity_type, param_name)
    if not pm or not pm.get("fit"):
        print(f"  {color('SKIP', Colors.YELLOW)} - No piecewise fit available for {entity_type}.{param_name}")
        stats.record_skip()
        return False

    # Known test points from Live measurements
    test_cases = [
        (1.0, 6.0),
        (0.925, 3.0),
        (0.850, 0.0),
        (0.775, -3.0),
        (0.700, -6.0),
        (0.625, -9.0),
        (0.550, -12.0),
        (0.0, -70.0),
    ]

    all_pass = True
    print(f"\n  {'Normalized':>12} | {'Expected dB':>12} | {'Converted dB':>12} | {'Error':>8} | {'Status':>6}")
    print(f"  {'-'*70}")

    for norm, expected_db in test_cases:
        converted_db = apply_mixer_fit_forward(pm, norm)
        if converted_db is None:
            print(f"  {norm:>12.3f} | {expected_db:>12.1f} | {'None':>12} | {'N/A':>8} | {color('FAIL', Colors.RED)}")
            all_pass = False
            stats.record_fail()
            continue

        error = abs(converted_db - expected_db)
        status = "PASS" if error < 0.1 else "FAIL"
        status_color = Colors.GREEN if status == "PASS" else Colors.RED

        print(f"  {norm:>12.3f} | {expected_db:>12.1f} | {converted_db:>12.1f} | {error:>8.2f} | {color(status, status_color)}")

        if status == "PASS":
            stats.record_pass()
        else:
            all_pass = False
            stats.record_fail()

    # Test inverse (dB -> normalized)
    print(f"\n  {'dB':>12} | {'Expected Norm':>15} | {'Converted Norm':>15} | {'Error':>8} | {'Status':>6}")
    print(f"  {'-'*70}")

    for expected_norm, db in test_cases:
        converted_norm = apply_mixer_fit_inverse(pm, db)
        if converted_norm is None:
            print(f"  {db:>12.1f} | {expected_norm:>15.3f} | {'None':>15} | {'N/A':>8} | {color('FAIL', Colors.RED)}")
            all_pass = False
            stats.record_fail()
            continue

        error = abs(converted_norm - expected_norm)
        status = "PASS" if error < 0.01 else "FAIL"
        status_color = Colors.GREEN if status == "PASS" else Colors.RED

        print(f"  {db:>12.1f} | {expected_norm:>15.3f} | {converted_norm:>15.3f} | {error:>8.4f} | {color(status, status_color)}")

        if status == "PASS":
            stats.record_pass()
        else:
            all_pass = False
            stats.record_fail()

    return all_pass


def test_send_conversion_accuracy(entity_type: str, stats: TestStats) -> bool:
    """Test send conversion accuracy using round-trip tests."""
    print(f"\n{color(f'Testing {entity_type}.send conversions (round-trip)', Colors.CYAN)}")

    pm = get_mixer_param_meta(entity_type, "send")
    if not pm or not pm.get("fit"):
        print(f"  {color('SKIP', Colors.YELLOW)} - No piecewise fit available for {entity_type}.send")
        stats.record_skip()
        return False

    # Test round-trip conversion at various normalized values
    test_normalized_values = [0.0, 0.1, 0.25, 0.4, 0.5, 0.6, 0.7, 0.8, 0.85]

    all_pass = True
    print(f"\n  {'Input Norm':>12} | {'dB':>12} | {'Round-trip Norm':>16} | {'Error':>8} | {'Status':>6}")
    print(f"  {'-'*70}")

    for original_norm in test_normalized_values:
        # Convert to dB
        db_value = apply_mixer_fit_forward(pm, original_norm)
        if db_value is None:
            print(f"  {original_norm:>12.3f} | {'None':>12} | {'N/A':>16} | {'N/A':>8} | {color('FAIL', Colors.RED)}")
            all_pass = False
            stats.record_fail()
            continue

        # Convert back to normalized
        round_trip_norm = apply_mixer_fit_inverse(pm, db_value)
        if round_trip_norm is None:
            print(f"  {original_norm:>12.3f} | {db_value:>12.1f} | {'None':>16} | {'N/A':>8} | {color('FAIL', Colors.RED)}")
            all_pass = False
            stats.record_fail()
            continue

        error = abs(round_trip_norm - original_norm)
        status = "PASS" if error < 0.001 else "FAIL"
        status_color = Colors.GREEN if status == "PASS" else Colors.RED

        print(f"  {original_norm:>12.3f} | {db_value:>12.1f} | {round_trip_norm:>16.3f} | {error:>8.5f} | {color(status, status_color)}")

        if status == "PASS":
            stats.record_pass()
        else:
            all_pass = False
            stats.record_fail()

    return all_pass


# ==============================================================================
# LIVE INTEGRATION TESTS (Requires Live)
# ==============================================================================

def test_absolute_set_live(entity_type: str, param: str, index: Optional[int], value: float, unit: str, stats: TestStats) -> bool:
    """Test absolute parameter set via Live."""
    from services.ableton_client import request_op, data_or_raw

    # Construct the operation based on entity type
    if entity_type == "track":
        op_name = "set_track_mixer"
        op_params = {"track_index": index, "field": param, "value": value}
    elif entity_type == "return":
        op_name = "set_return_mixer"
        op_params = {"return_index": index, "field": param, "value": value}
    elif entity_type == "master":
        op_name = "set_master_mixer"
        op_params = {"field": param, "value": value}
    else:
        stats.record_fail()
        return False

    try:
        # First convert dB to normalized if needed
        if unit == "dB":
            pm = get_mixer_param_meta(entity_type, param)
            if pm and pm.get("fit"):
                normalized = apply_mixer_fit_inverse(pm, value)
                if normalized is not None:
                    op_params["value"] = normalized

        resp = request_op(op_name, timeout=2.0, **op_params)

        if not resp or not resp.get("ok"):
            print_test_result(f"{entity_type}.{param} = {value} {unit}", False, f"Operation failed: {resp}")
            stats.record_fail()
            return False

        print_test_result(f"{entity_type}.{param} = {value} {unit}", True)
        stats.record_pass()
        return True

    except Exception as e:
        print_test_result(f"{entity_type}.{param} = {value} {unit}", False, f"Error: {e}")
        stats.record_fail()
        return False


def test_relative_change_live(entity_type: str, param: str, index: Optional[int], delta: float, operation: str, stats: TestStats) -> bool:
    """Test relative parameter change (increase/decrease by)."""
    from services.ableton_client import request_op, data_or_raw

    # Get current value first
    if entity_type == "track":
        get_op = "get_track_status"
        get_params = {"track_index": index}
        mixer_key = "mixer"
    elif entity_type == "return":
        get_op = "get_return_status"
        get_params = {"return_index": index}
        mixer_key = "mixer"
    elif entity_type == "master":
        get_op = "get_master_status"
        get_params = {}
        mixer_key = "mixer"
    else:
        stats.record_fail()
        return False

    try:
        # Get current value
        resp = request_op(get_op, timeout=2.0, **get_params)
        if not resp or not resp.get("ok"):
            print_test_result(f"{entity_type}.{param} {operation} {delta} dB", False, "Failed to get current value")
            stats.record_fail()
            return False

        data = data_or_raw(resp)
        current_norm = data.get(mixer_key, {}).get(param)
        if current_norm is None:
            print_test_result(f"{entity_type}.{param} {operation} {delta} dB", False, "No current value")
            stats.record_fail()
            return False

        # Convert current to dB
        pm = get_mixer_param_meta(entity_type, param)
        if not pm or not pm.get("fit"):
            print_test_result(f"{entity_type}.{param} {operation} {delta} dB", False, "No piecewise fit")
            stats.record_fail()
            return False

        current_db = apply_mixer_fit_forward(pm, current_norm)
        if current_db is None:
            print_test_result(f"{entity_type}.{param} {operation} {delta} dB", False, "Failed to convert current")
            stats.record_fail()
            return False

        # Calculate new value
        if operation in ("increase", "increase by"):
            new_db = current_db + delta
        elif operation in ("decrease", "decrease by", "reduce", "reduce by"):
            new_db = current_db - delta
        else:
            stats.record_fail()
            return False

        # Convert back to normalized
        new_norm = apply_mixer_fit_inverse(pm, new_db)
        if new_norm is None:
            print_test_result(f"{entity_type}.{param} {operation} {delta} dB", False, "Failed to convert new value")
            stats.record_fail()
            return False

        # Apply the change
        if entity_type == "track":
            set_op = "set_track_mixer"
            set_params = {"track_index": index, "field": param, "value": new_norm}
        elif entity_type == "return":
            set_op = "set_return_mixer"
            set_params = {"return_index": index, "field": param, "value": new_norm}
        elif entity_type == "master":
            set_op = "set_master_mixer"
            set_params = {"field": param, "value": new_norm}

        resp = request_op(set_op, timeout=2.0, **set_params)
        if not resp or not resp.get("ok"):
            print_test_result(f"{entity_type}.{param} {operation} {delta} dB", False, f"Set failed: {resp}")
            stats.record_fail()
            return False

        print_test_result(f"{entity_type}.{param} {operation} {delta} dB", True,
                         f"({current_db:.1f} dB → {new_db:.1f} dB)")
        stats.record_pass()
        return True

    except Exception as e:
        print_test_result(f"{entity_type}.{param} {operation} {delta} dB", False, f"Error: {e}")
        stats.record_fail()
        return False


def test_pan_operation_live(entity_type: str, index: Optional[int], direction: str, amount: float, stats: TestStats) -> bool:
    """Test pan left/right operations."""
    from services.ableton_client import request_op, data_or_raw

    # Get current pan value
    if entity_type == "track":
        get_op = "get_track_status"
        get_params = {"track_index": index}
    elif entity_type == "return":
        get_op = "get_return_status"
        get_params = {"return_index": index}
    elif entity_type == "master":
        get_op = "get_master_status"
        get_params = {}
    else:
        stats.record_fail()
        return False

    try:
        resp = request_op(get_op, timeout=2.0, **get_params)
        if not resp or not resp.get("ok"):
            print_test_result(f"{entity_type} pan {direction} {amount}", False, "Failed to get current pan")
            stats.record_fail()
            return False

        data = data_or_raw(resp)
        current_pan = data.get("mixer", {}).get("pan", 0.0)

        # Calculate new pan (-1.0 to 1.0 range, where -1 is full left, 1 is full right)
        if direction == "left":
            new_pan = max(-1.0, current_pan - (amount / 50.0))  # Assuming 50 is max display range
        elif direction == "right":
            new_pan = min(1.0, current_pan + (amount / 50.0))
        else:
            stats.record_fail()
            return False

        # Set new pan
        if entity_type == "track":
            set_op = "set_track_mixer"
            set_params = {"track_index": index, "field": "pan", "value": new_pan}
        elif entity_type == "return":
            set_op = "set_return_mixer"
            set_params = {"return_index": index, "field": "pan", "value": new_pan}
        elif entity_type == "master":
            set_op = "set_master_mixer"
            set_params = {"field": "pan", "value": new_pan}

        resp = request_op(set_op, timeout=2.0, **set_params)
        if not resp or not resp.get("ok"):
            print_test_result(f"{entity_type} pan {direction} {amount}", False, f"Set failed: {resp}")
            stats.record_fail()
            return False

        print_test_result(f"{entity_type} pan {direction} {amount}", True,
                         f"({current_pan:.2f} → {new_pan:.2f})")
        stats.record_pass()
        return True

    except Exception as e:
        print_test_result(f"{entity_type} pan {direction} {amount}", False, f"Error: {e}")
        stats.record_fail()
        return False


# ==============================================================================
# TEST SUITES
# ==============================================================================

def run_conversion_tests(stats: TestStats):
    """Run all conversion accuracy tests (no Live needed)."""
    print_header("CONVERSION ACCURACY TESTS (No Live Required)")

    # Test track volume
    test_volume_conversion_accuracy("track", "volume", stats)

    # Test return volume
    test_volume_conversion_accuracy("return", "volume", stats)

    # Test master volume
    test_volume_conversion_accuracy("master", "volume", stats)

    # Test master cue (uses same mapping as volume)
    test_volume_conversion_accuracy("master", "cue", stats)

    # Test track sends
    test_send_conversion_accuracy("track", stats)

    # Test return sends
    test_send_conversion_accuracy("return", stats)


def run_live_tests(stats: TestStats):
    """Run all Live integration tests (requires Live)."""
    print_header("LIVE INTEGRATION TESTS (Requires Ableton Live)")

    print(f"\n{color('Testing TRACK operations', Colors.CYAN)}")

    # Track volume absolute sets
    test_absolute_set_live("track", "volume", 1, -6.0, "dB", stats)
    test_absolute_set_live("track", "volume", 1, 0.0, "dB", stats)
    test_absolute_set_live("track", "volume", 1, -12.0, "dB", stats)

    # Track volume relative changes
    test_relative_change_live("track", "volume", 1, 3.0, "increase by", stats)
    test_relative_change_live("track", "volume", 1, 6.0, "decrease by", stats)

    # Track pan operations
    test_pan_operation_live("track", 1, "left", 10.0, stats)
    test_pan_operation_live("track", 1, "right", 20.0, stats)

    # Track send operations
    test_absolute_set_live("track", "send_0", 1, -12.0, "dB", stats)
    test_relative_change_live("track", "send_0", 1, 3.0, "increase by", stats)

    print(f"\n{color('Testing RETURN operations', Colors.CYAN)}")

    # Return volume absolute sets
    test_absolute_set_live("return", "volume", 0, -6.0, "dB", stats)
    test_absolute_set_live("return", "volume", 0, 0.0, "dB", stats)

    # Return volume relative changes
    test_relative_change_live("return", "volume", 0, 3.0, "increase by", stats)
    test_relative_change_live("return", "volume", 0, 3.0, "reduce by", stats)

    # Return pan operations
    test_pan_operation_live("return", 0, "left", 15.0, stats)
    test_pan_operation_live("return", 0, "right", 15.0, stats)

    # Return send operations
    test_absolute_set_live("return", "send_0", 0, -12.0, "dB", stats)

    print(f"\n{color('Testing MASTER operations', Colors.CYAN)}")

    # Master volume absolute sets
    test_absolute_set_live("master", "volume", None, -6.0, "dB", stats)
    test_absolute_set_live("master", "volume", None, 0.0, "dB", stats)

    # Master volume relative changes
    test_relative_change_live("master", "volume", None, 3.0, "increase by", stats)
    test_relative_change_live("master", "volume", None, 3.0, "decrease by", stats)

    # Master cue operations
    test_absolute_set_live("master", "cue", None, -6.0, "dB", stats)
    test_relative_change_live("master", "cue", None, 3.0, "increase by", stats)

    # Master pan operations
    test_pan_operation_live("master", None, "left", 10.0, stats)
    test_pan_operation_live("master", None, "right", 10.0, stats)


def print_summary(stats: TestStats):
    """Print test summary."""
    print_header("TEST SUMMARY")

    total = stats.total
    passed = stats.passed
    failed = stats.failed
    skipped = stats.skipped

    pass_rate = (passed / total * 100) if total > 0 else 0

    print(f"\n  Total tests:    {total}")
    print(f"  {color('✓ Passed:', Colors.GREEN)}      {passed} ({pass_rate:.1f}%)")
    if failed > 0:
        print(f"  {color('✗ Failed:', Colors.RED)}      {failed}")
    if skipped > 0:
        print(f"  {color('⊘ Skipped:', Colors.YELLOW)}     {skipped}")

    print()

    if failed == 0 and passed > 0:
        print(f"  {color('🎉 ALL TESTS PASSED!', Colors.GREEN + Colors.BOLD)}")
    elif failed > 0:
        print(f"  {color('❌ SOME TESTS FAILED', Colors.RED + Colors.BOLD)}")

    print()


def main():
    parser = argparse.ArgumentParser(description='Test mixer piecewise mappings')
    parser.add_argument('--live', action='store_true', help='Run Live integration tests (requires Live)')
    parser.add_argument('--conversions-only', action='store_true', help='Run only conversion tests')
    args = parser.parse_args()

    stats = TestStats()

    print(color("""
╔═══════════════════════════════════════════════════════════════════════════╗
║                  MIXER PIECEWISE MAPPING TEST SUITE                       ║
║                                                                           ║
║  Tests all mixer conversions and operations with piecewise mappings      ║
╚═══════════════════════════════════════════════════════════════════════════╝
    """, Colors.BOLD + Colors.BLUE))

    # Always run conversion tests
    run_conversion_tests(stats)

    # Run Live tests if requested
    if args.live and not args.conversions_only:
        print()
        try:
            run_live_tests(stats)
        except ImportError as e:
            print(f"\n{color('ERROR:', Colors.RED)} Cannot import Live client modules: {e}")
            print(f"{color('HINT:', Colors.YELLOW)} Make sure the server is running")
    elif not args.conversions_only:
        print(f"\n{color('INFO:', Colors.YELLOW)} Skipping Live integration tests (use --live to enable)")

    # Print summary
    print_summary(stats)

    # Exit with appropriate code
    return 0 if stats.failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
