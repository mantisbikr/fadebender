#!/usr/bin/env python3
"""
Verify fitted mixer coefficients against the piecewise mapping.

This script:
 1) Loads the measured piecewise mapping (ground truth)
 2) Loads the fitted power-law model
 3) Tests both forward and inverse conversions
 4) Reports maximum error and accuracy metrics

Usage:
  python3 scripts/verify_mixer_fits.py
"""
from __future__ import annotations

import math
import sys
from typing import List, Tuple, Optional

# --- Load piecewise mapping (ground truth) ---
def load_piecewise_points(kind: str) -> List[Tuple[float, float]]:
    """Return list of (db, float) pairs for 'volume' or 'send'."""
    try:
        from fadebender_lom import volume as vol
    except Exception as e:
        print("ERROR: failed to import fadebender_lom.volume.", file=sys.stderr)
        raise

    # Trigger load
    try:
        getattr(vol, "_try_load_mapping")()
    except Exception as e:
        print(f"ERROR: failed to load piecewise mapping: {e}", file=sys.stderr)
        raise

    pts: List[Tuple[float, float]] = []
    if kind == "volume":
        arr = getattr(vol, "_MAP_DB2F", [])
        if arr:
            pts = [(float(d), float(f)) for d, f in arr]
        else:
            # Synthesize by sampling
            for d in range(-60, 7):
                try:
                    f = float(vol.db_to_live_float(float(d)))
                    pts.append((float(d), f))
                except Exception:
                    continue
    elif kind == "send":
        arr = getattr(vol, "_SEND_MAP_DB2F", [])
        if arr:
            pts = [(float(d), float(f)) for d, f in arr]
        else:
            # Synthesize from send converter
            for d in range(-60, 1):
                try:
                    f = float(vol.db_to_live_float_send(float(d)))
                    pts.append((float(d), f))
                except Exception:
                    continue
    else:
        raise ValueError("kind must be 'volume' or 'send'")

    if not pts:
        raise RuntimeError(f"No piecewise points available for {kind}")
    return pts


# --- Power-law fit model ---
def power_law_inverse(db: float, min_db: float, max_db: float, gamma: float) -> float:
    """Convert dB -> normalized using power-law fit."""
    range_db = max_db - min_db
    ratio = (db - min_db) / range_db
    # Clamp ratio first to avoid complex numbers from negative bases
    ratio = max(0.0, min(1.0, ratio))
    normalized = ratio ** gamma
    return max(0.0, min(1.0, normalized))


def power_law_forward(normalized: float, min_db: float, max_db: float, gamma: float) -> float:
    """Convert normalized -> dB using power-law fit."""
    range_db = max_db - min_db
    n_clamped = max(0.0, min(1.0, normalized))
    inv_gamma = 1.0 / gamma
    db = min_db + range_db * (n_clamped ** inv_gamma)
    return db


def verify_fit(kind: str, min_db: float, max_db: float, gamma: float) -> bool:
    """Verify fit accuracy against piecewise mapping."""
    print(f"\n{'='*80}")
    print(f"Verifying {kind.upper()} fit (gamma={gamma:.6f})")
    print(f"{'='*80}\n")

    # Load ground truth
    piecewise = load_piecewise_points(kind)

    # Test inverse conversion (dB -> normalized)
    print("Testing INVERSE conversion (dB -> normalized):")
    print(f"{'dB':>8} | {'Piecewise':>12} | {'Fit':>12} | {'Error':>12} | {'Error %':>10}")
    print("-" * 80)

    max_inverse_error = 0.0
    max_inverse_error_pct = 0.0

    for db, expected_norm in piecewise:
        fitted_norm = power_law_inverse(db, min_db, max_db, gamma)
        error = abs(fitted_norm - expected_norm)
        error_pct = (error / max(abs(expected_norm), 1e-9)) * 100.0

        max_inverse_error = max(max_inverse_error, error)
        max_inverse_error_pct = max(max_inverse_error_pct, error_pct)

        # Print sample points
        if db in [-60, -50, -40, -30, -20, -10, -6, -3, 0, 3, 6] or (kind == "volume" and db == 6):
            print(f"{db:>8.1f} | {expected_norm:>12.6f} | {fitted_norm:>12.6f} | {error:>12.6f} | {error_pct:>9.2f}%")

    print(f"\nMax inverse error: {max_inverse_error:.6f} ({max_inverse_error_pct:.2f}%)")

    # Test forward conversion (normalized -> dB)
    print("\n" + "="*80)
    print("Testing FORWARD conversion (normalized -> dB):")
    print(f"{'Normalized':>12} | {'Expected dB':>12} | {'Fit dB':>12} | {'Error':>12}")
    print("-" * 80)

    max_forward_error = 0.0

    for db, norm in piecewise:
        fitted_db = power_law_forward(norm, min_db, max_db, gamma)
        error = abs(fitted_db - db)
        max_forward_error = max(max_forward_error, error)

        # Print sample points
        if db in [-60, -50, -40, -30, -20, -10, -6, -3, 0, 3, 6] or (kind == "volume" and db == 6):
            print(f"{norm:>12.6f} | {db:>12.1f} | {fitted_db:>12.1f} | {error:>12.2f}")

    print(f"\nMax forward error: {max_forward_error:.2f} dB")

    # Acceptance criteria
    inverse_ok = max_inverse_error < 0.01  # Less than 1% normalized error
    forward_ok = max_forward_error < 1.0   # Less than 1 dB error

    print("\n" + "="*80)
    if inverse_ok and forward_ok:
        print(f"✅ {kind.upper()} fit PASSED verification")
        print(f"   Inverse error: {max_inverse_error:.6f} (< 0.01 threshold)")
        print(f"   Forward error: {max_forward_error:.2f} dB (< 1.0 dB threshold)")
        return True
    else:
        print(f"❌ {kind.upper()} fit FAILED verification")
        if not inverse_ok:
            print(f"   Inverse error: {max_inverse_error:.6f} (>= 0.01 threshold)")
        if not forward_ok:
            print(f"   Forward error: {max_forward_error:.2f} dB (>= 1.0 dB threshold)")
        return False


def main() -> int:
    """Main verification routine."""
    # Fitted coefficients from recalibration script (with corrected ranges)
    volume_gamma = 1.776817
    volume_min_db = -70.0
    volume_max_db = 6.0

    send_gamma = 1.881984
    send_min_db = -76.0
    send_max_db = -6.0

    # Verify volume fit
    vol_ok = verify_fit("volume", min_db=volume_min_db, max_db=volume_max_db, gamma=volume_gamma)

    # Verify send fit
    send_ok = verify_fit("send", min_db=send_min_db, max_db=send_max_db, gamma=send_gamma)

    # Summary
    print("\n" + "="*80)
    print("OVERALL SUMMARY")
    print("="*80)
    print(f"Volume fit: {'✅ PASSED' if vol_ok else '❌ FAILED'}")
    print(f"Send fit:   {'✅ PASSED' if send_ok else '❌ FAILED'}")

    if vol_ok and send_ok:
        print("\n✅ All fits verified successfully!")
        print("   Safe to write to dev-display-value database.")
        return 0
    else:
        print("\n❌ Some fits failed verification.")
        print("   Do NOT write to dev-display-value database.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
