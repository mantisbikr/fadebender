"""
Volume conversion utilities for Ableton Live API.

Uses an empirical mapping if available (docs/volume_map.csv), with linear
interpolation between sampled points. Falls back to the heuristic formula:
  X ≈ 0.85 - (0.025 × |dB_target|)
when no mapping file is present.
"""

from __future__ import annotations

import os
import re
from typing import List, Tuple

# Global lookup tables (sorted)
_MAP_DB2F: List[Tuple[float, float]] = []  # (db, float)
_MAP_F2DB: List[Tuple[float, float]] = []  # (float, db)


def _try_load_mapping() -> None:
    """Load docs/volume_map.csv if present, robust to accidental RTF wrappers.

    Expected logical content is lines with two numeric columns: db, float
    """
    global _MAP_DB2F, _MAP_F2DB
    if _MAP_DB2F:
        return
    here = os.path.dirname(os.path.abspath(__file__))
    # repo root is server/.. so docs is sibling to server
    repo_root = os.path.abspath(os.path.join(here, os.pardir))
    candidates = [
        os.path.join(repo_root, "docs", "volume_map.csv"),
        os.path.join(repo_root, "../docs", "volume_map.csv"),
    ]
    path = None
    for p in candidates:
        if os.path.exists(p):
            path = p
            break
    if not path:
        return
    try:
        pairs: List[Tuple[float, float]] = []
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                # Extract first two floating/decimal numbers in the line
                nums = re.findall(r"[-+]?\d+(?:\.\d+)?", line)
                if len(nums) < 2:
                    continue
                try:
                    db = float(nums[0])
                    val = float(nums[1])
                except Exception:
                    continue
                pairs.append((db, val))
        # Deduplicate and sort
        pairs = sorted({(round(db, 6), round(val, 9)) for db, val in pairs})
        # Filter to plausible ranges
        pairs = [(db, val) for db, val in pairs if -80.0 <= db <= 12.0 and 0.0 <= val <= 1.0]
        # Ensure monotonicity by db
        pairs.sort(key=lambda x: x[0])
        if len(pairs) >= 4:
            _MAP_DB2F = pairs
            _MAP_F2DB = sorted([(v, d) for d, v in pairs], key=lambda x: x[0])
    except Exception:
        # silently ignore mapping load issues; fallback will be used
        pass


def _interp_x(y: float, pts: List[Tuple[float, float]]) -> float:
    """Given y and points (x,y) sorted by x, linearly interpolate x.

    Used for inverse lookups (float->dB) when pts is (float, db) or forward
    lookups (db->float) when pts is (db, float) by swapping names.
    """
    if not pts:
        return 0.0
    # Clamp outside range
    if y <= pts[0][0]:
        return pts[0][1]
    if y >= pts[-1][0]:
        return pts[-1][1]
    # Binary search for interval
    lo, hi = 0, len(pts) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if pts[mid][0] < y:
            lo = mid + 1
        else:
            hi = mid - 1
    # Interpolate between hi and lo (neighboring points)
    i1 = max(0, hi)
    i2 = min(len(pts) - 1, lo)
    x1, y1 = pts[i1][0], pts[i1][1]
    x2, y2 = pts[i2][0], pts[i2][1]
    if x2 == x1:
        return y1
    t = (y - x1) / (x2 - x1)
    return y1 + t * (y2 - y1)


def db_to_live_float(db_value: float) -> float:
    """
    Convert dB value to Ableton Live API float value (0.0 to 1.0).

    Formula: X ≈ 0.85 - (0.025 × |dB_target|)

    Args:
        db_value: dB value (typically -60 to +6)

    Returns:
        Float value for Live API (0.0 to 1.0)
    """
    _try_load_mapping()
    # Clamp to typical range
    db_clamped = max(-60.0, min(6.0, float(db_value)))
    if _MAP_DB2F:
        # Interpolate float from db using the table
        # pts is (db, float): reuse _interp_x by flipping axes notionally
        # We want y=db, return mapped float
        # Build helper list as (db, float) already
        # Clamp via interpolation boundary behavior
        y = db_clamped
        pts = [(d, v) for d, v in _MAP_DB2F]
        # _interp_x expects pts sorted by x (here db), returns interpolated value (float)
        f = _interp_x(y, pts)
        return max(0.0, min(1.0, float(f)))
    # Fallback heuristic
    float_value = 0.85 - (0.025 * abs(db_clamped))
    return max(0.0, min(1.0, float_value))


def live_float_to_db(float_value: float) -> float:
    """
    Convert Ableton Live API float value (0.0 to 1.0) to dB.

    Inverse formula: dB ≈ -(0.85 - X) / 0.025

    Args:
        float_value: Live API float value (0.0 to 1.0)

    Returns:
        dB value (typically -60 to +6)
    """
    _try_load_mapping()
    # Clamp float to valid range
    float_clamped = max(0.0, min(1.0, float(float_value)))
    if _MAP_F2DB:
        # Interpolate db from float using the inverse table
        y = float_clamped
        pts = [(v, d) for v, d in _MAP_F2DB]
        d_b = _interp_x(y, pts)
        return max(-60.0, min(6.0, float(d_b)))
    # Handle special case for very low values
    if float_clamped <= 0.001:
        return -60.0
    db_value = -(0.85 - float_clamped) / 0.025
    return max(-60.0, min(6.0, db_value))


# Test the conversion functions
if __name__ == "__main__":
    # Quick smoke test using either mapping or fallback
    for db in [-60, -30, -12, -6, -3, 0, 3, 6]:
        f = db_to_live_float(db)
        back = live_float_to_db(f)
        print(f"{db:6.1f} dB → {f:.6f} → {back:.2f} dB")
