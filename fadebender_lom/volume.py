"""
Volume conversion utilities for Ableton Live API (shared package).
"""
from __future__ import annotations

import os
import re
from typing import List, Tuple

_MAP_DB2F: List[Tuple[float, float]] = []  # (db, float)
_MAP_F2DB: List[Tuple[float, float]] = []  # (float, db)


def _try_load_mapping() -> None:
    """Load docs/volume_map.csv if present, robust to accidental RTF wrappers.

    Expected logical content is lines with two numeric columns: db, float
    """
    global _MAP_DB2F, _MAP_F2DB
    if _MAP_DB2F:
        return
    repo_root = os.getenv("FB_REPO_ROOT") or os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
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
                nums = re.findall(r"[-+]?\d+(?:\.\d+)?", line)
                if len(nums) < 2:
                    continue
                try:
                    db = float(nums[0]); val = float(nums[1])
                except Exception:
                    continue
                pairs.append((db, val))
        pairs = sorted({(round(db, 6), round(val, 9)) for db, val in pairs})
        pairs = [(db, val) for db, val in pairs if -80.0 <= db <= 12.0 and 0.0 <= val <= 1.0]
        pairs.sort(key=lambda x: x[0])
        if len(pairs) >= 4:
            _MAP_DB2F = pairs
            _MAP_F2DB = sorted([(v, d) for d, v in pairs], key=lambda x: x[0])
    except Exception:
        pass


def _interp_x(y: float, pts: List[Tuple[float, float]]) -> float:
    if not pts:
        return 0.0
    if y <= pts[0][0]:
        return pts[0][1]
    if y >= pts[-1][0]:
        return pts[-1][1]
    lo, hi = 0, len(pts) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if pts[mid][0] < y:
            lo = mid + 1
        else:
            hi = mid - 1
    i1 = max(0, hi)
    i2 = min(len(pts) - 1, lo)
    x1, y1 = pts[i1][0], pts[i1][1]
    x2, y2 = pts[i2][0], pts[i2][1]
    if x2 == x1:
        return y1
    t = (y - x1) / (x2 - x1)
    return y1 + t * (y2 - y1)


def db_to_live_float(db_value: float) -> float:
    _try_load_mapping()
    db_clamped = max(-60.0, min(6.0, float(db_value)))
    if _MAP_DB2F:
        y = db_clamped
        pts = [(d, v) for d, v in _MAP_DB2F]
        f = _interp_x(y, pts)
        return max(0.0, min(1.0, float(f)))
    float_value = 0.85 - (0.025 * abs(db_clamped))
    return max(0.0, min(1.0, float_value))


def live_float_to_db(float_value: float) -> float:
    _try_load_mapping()
    float_clamped = max(0.0, min(1.0, float(float_value)))
    if _MAP_F2DB:
        y = float_clamped
        pts = [(v, d) for v, d in _MAP_F2DB]
        d_b = _interp_x(y, pts)
        return max(-60.0, min(6.0, float(d_b)))
    if float_clamped <= 0.001:
        return -60.0
    db_value = -(0.85 - float_clamped) / 0.025
    return max(-60.0, min(6.0, db_value))


def db_to_live_float_send(db_value: float) -> float:
    return db_to_live_float(float(db_value) + 6.0)


def live_float_to_db_send(float_value: float) -> float:
    return live_float_to_db(float_value) - 6.0

