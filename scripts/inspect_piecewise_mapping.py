#!/usr/bin/env python3
"""Inspect the actual piecewise mapping data."""

import sys
from typing import List, Tuple

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
    elif kind == "send":
        arr = getattr(vol, "_SEND_MAP_DB2F", [])
        if arr:
            pts = [(float(d), float(f)) for d, f in arr]
    else:
        raise ValueError("kind must be 'volume' or 'send'")

    if not pts:
        raise RuntimeError(f"No piecewise points available for {kind}")
    return pts


def main():
    print("="*80)
    print("VOLUME MAPPING")
    print("="*80)
    vol_pts = load_piecewise_points("volume")
    print(f"Total points: {len(vol_pts)}")
    print(f"\nFirst 10 points:")
    for db, norm in vol_pts[:10]:
        print(f"  {db:>7.2f} dB → {norm:.6f}")
    print(f"\nLast 10 points:")
    for db, norm in vol_pts[-10:]:
        print(f"  {db:>7.2f} dB → {norm:.6f}")

    min_db = min(db for db, _ in vol_pts)
    max_db = max(db for db, _ in vol_pts)
    min_norm = min(norm for _, norm in vol_pts)
    max_norm = max(norm for _, norm in vol_pts)

    print(f"\nRange:")
    print(f"  dB:   {min_db:.2f} to {max_db:.2f}")
    print(f"  Norm: {min_norm:.6f} to {max_norm:.6f}")

    print("\n" + "="*80)
    print("SEND MAPPING")
    print("="*80)
    send_pts = load_piecewise_points("send")
    print(f"Total points: {len(send_pts)}")
    print(f"\nFirst 10 points:")
    for db, norm in send_pts[:10]:
        print(f"  {db:>7.2f} dB → {norm:.6f}")
    print(f"\nLast 10 points:")
    for db, norm in send_pts[-10:]:
        print(f"  {db:>7.2f} dB → {norm:.6f}")

    min_db = min(db for db, _ in send_pts)
    max_db = max(db for db, _ in send_pts)
    min_norm = min(norm for _, norm in send_pts)
    max_norm = max(norm for _, norm in send_pts)

    print(f"\nRange:")
    print(f"  dB:   {min_db:.2f} to {max_db:.2f}")
    print(f"  Norm: {min_norm:.6f} to {max_norm:.6f}")


if __name__ == "__main__":
    main()
