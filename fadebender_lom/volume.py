"""
Volume conversion utilities for Ableton Live API (shared package).
"""
from __future__ import annotations

from typing import List, Tuple
from google.cloud import firestore

_MAP_DB2F: List[Tuple[float, float]] = []  # (db, float)
_MAP_F2DB: List[Tuple[float, float]] = []  # (float, db)
_SEND_MAP_DB2F: List[Tuple[float, float]] = []  # (db, float) for sends
_SEND_MAP_F2DB: List[Tuple[float, float]] = []  # (float, db) for sends


def _try_load_mapping() -> None:
    """Load volume mappings from Firestore dev-display-value database.

    Loads both 'volume' and 'send' mappings from mixer_mappings collection.
    Fails with clear error if mappings are not found.
    """
    global _MAP_DB2F, _MAP_F2DB, _SEND_MAP_DB2F, _SEND_MAP_F2DB
    if _MAP_DB2F:
        return

    try:
        db = firestore.Client(database='dev-display-value')

        # Load volume mapping (for tracks, returns, master)
        volume_doc = db.collection('mixer_mappings').document('volume').get()
        if not volume_doc.exists:
            raise RuntimeError(
                "Volume mapping not found in Firestore! "
                "Run: python3 scripts/upload_mixer_mappings.py"
            )

        volume_data = volume_doc.to_dict()
        mapping = volume_data.get('mapping', [])

        if len(mapping) < 4:
            raise RuntimeError(
                f"Invalid volume mapping in Firestore: only {len(mapping)} points found, need at least 4"
            )

        _MAP_DB2F = [(point['db'], point['float']) for point in mapping]
        _MAP_F2DB = sorted([(point['float'], point['db']) for point in mapping], key=lambda x: x[0])

        # Load send mapping
        send_doc = db.collection('mixer_mappings').document('send').get()
        if send_doc.exists:
            send_data = send_doc.to_dict()
            send_mapping = send_data.get('mapping', [])
            _SEND_MAP_DB2F = [(point['db'], point['float']) for point in send_mapping]
            _SEND_MAP_F2DB = sorted([(point['float'], point['db']) for point in send_mapping], key=lambda x: x[0])

    except Exception as e:
        raise RuntimeError(
            f"Failed to load mixer mappings from Firestore: {e}\n"
            "Make sure you've run: python3 scripts/upload_mixer_mappings.py"
        ) from e


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
    """Convert dB to Live float value (0.0-1.0) for track/return/master volume.

    Range: -60dB to +6dB
    Uses accurate mapping from Firestore (measured from Ableton Live 12).
    Raises RuntimeError if mapping not loaded.
    """
    _try_load_mapping()
    if not _MAP_DB2F:
        raise RuntimeError("Volume mapping not loaded from Firestore")

    db_clamped = max(-60.0, min(6.0, float(db_value)))
    pts = [(d, v) for d, v in _MAP_DB2F]
    f = _interp_x(db_clamped, pts)
    return max(0.0, min(1.0, float(f)))


def live_float_to_db(float_value: float) -> float:
    """Convert Live float value (0.0-1.0) to dB for track/return/master volume.

    Range: -60dB to +6dB
    Uses accurate mapping from Firestore (measured from Ableton Live 12).
    Raises RuntimeError if mapping not loaded.
    """
    _try_load_mapping()
    if not _MAP_F2DB:
        raise RuntimeError("Volume mapping not loaded from Firestore")

    float_clamped = max(0.0, min(1.0, float(float_value)))
    pts = [(v, d) for v, d in _MAP_F2DB]
    d_b = _interp_x(float_clamped, pts)
    return max(-60.0, min(6.0, float(d_b)))


def db_to_live_float_send(db_value: float) -> float:
    """Convert dB to Live float value for send levels.

    Range: -60dB to 0dB (sends have +6dB offset relative to tracks)
    Uses accurate mapping from Firestore (measured from Ableton Live 12).
    """
    return db_to_live_float(float(db_value) + 6.0)


def live_float_to_db_send(float_value: float) -> float:
    """Convert Live float value to dB for send levels.

    Range: -60dB to 0dB (sends have +6dB offset relative to tracks)
    Uses accurate mapping from Firestore (measured from Ableton Live 12).
    """
    return live_float_to_db(float_value) - 6.0

