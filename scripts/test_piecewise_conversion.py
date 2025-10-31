#!/usr/bin/env python3
"""Test piecewise conversion accuracy."""
import sys
import os

# Add server to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'server'))

from services.intents.utils.mixer import get_mixer_param_meta, apply_mixer_fit_forward, apply_mixer_fit_inverse

def test_volume():
    """Test volume conversions match user's Live measurements."""
    print("="*80)
    print("Testing VOLUME piecewise conversion")
    print("="*80)

    param_meta = get_mixer_param_meta("track", "volume")
    if not param_meta:
        print("ERROR: Could not get volume param_meta")
        return False

    # User's measurements from Live
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

    print(f"\n{'Normalized':>12} | {'Expected dB':>12} | {'Converted dB':>12} | {'Error':>10} | {'Status':>6}")
    print("-" * 80)

    all_pass = True
    for norm, expected_db in test_cases:
        converted_db = apply_mixer_fit_forward(param_meta, norm)
        if converted_db is None:
            print(f"{norm:>12.3f} | {expected_db:>12.1f} | {'None':>12} | {'N/A':>10} | FAIL")
            all_pass = False
            continue

        error = abs(converted_db - expected_db)
        status = "PASS" if error < 0.1 else "FAIL"
        if status == "FAIL":
            all_pass = False

        print(f"{norm:>12.3f} | {expected_db:>12.1f} | {converted_db:>12.1f} | {error:>10.2f} | {status:>6}")

    print("\n" + "="*80)
    print("Testing INVERSE (dB -> normalized)")
    print("="*80)
    print(f"\n{'dB':>12} | {'Expected Norm':>15} | {'Converted Norm':>15} | {'Error':>10} | {'Status':>6}")
    print("-" * 80)

    for expected_norm, db in test_cases:
        converted_norm = apply_mixer_fit_inverse(param_meta, db)
        if converted_norm is None:
            print(f"{db:>12.1f} | {expected_norm:>15.3f} | {'None':>15} | {'N/A':>10} | FAIL")
            all_pass = False
            continue

        error = abs(converted_norm - expected_norm)
        status = "PASS" if error < 0.01 else "FAIL"
        if status == "FAIL":
            all_pass = False

        print(f"{db:>12.1f} | {expected_norm:>15.3f} | {converted_norm:>15.3f} | {error:>10.4f} | {status:>6}")

    return all_pass


def main():
    vol_ok = test_volume()

    print("\n" + "="*80)
    print("OVERALL RESULT")
    print("="*80)
    if vol_ok:
        print("✅ All tests PASSED - piecewise conversion is accurate!")
        return 0
    else:
        print("❌ Some tests FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
