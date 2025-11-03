#!/usr/bin/env python3
"""
Store piecewise mappings directly in Firestore (no fitting).

This script:
 1) Loads the measured piecewise mapping from fadebender_lom.volume
 2) Stores it directly in Firestore mixer_mappings as type="piecewise"
 3) Writes to the database configured via FIRESTORE_DATABASE_ID env var
"""
from __future__ import annotations

import sys
from typing import List, Tuple, Dict, Any


def load_piecewise_points(kind: str) -> List[Tuple[float, float]]:
    """Return list of (db, normalized) pairs for 'volume' or 'send'."""
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


def piecewise_to_dict(points: List[Tuple[float, float]]) -> Dict[str, Any]:
    """Convert piecewise points to Firestore-friendly dict."""
    return {
        "type": "piecewise",
        "points": [
            {"db": float(db), "normalized": float(norm)}
            for db, norm in points
        ]
    }


def write_piecewise_to_mapping(entity: str, param_name: str, points: List[Tuple[float, float]]) -> bool:
    """Update mixer_mappings/{entity}_channel.params_meta with piecewise mapping."""
    try:
        from google.cloud import firestore  # type: ignore
        import os
    except Exception as e:
        print("ERROR: google-cloud-firestore not installed or not configured.", file=sys.stderr)
        return False

    # Use same database configuration as MappingStore
    try:
        project_id = os.getenv("FIRESTORE_PROJECT_ID")
        database_id = os.getenv("FIRESTORE_DATABASE_ID", "(default)")

        if project_id and database_id and database_id != "(default)":
            client = firestore.Client(project=project_id, database=database_id)
            print(f"  → Writing to database: {database_id}")
        elif project_id:
            client = firestore.Client(project=project_id)
            print(f"  → Writing to project: {project_id} (default database)")
        else:
            client = firestore.Client()
            print(f"  → Writing to default Firestore")
    except Exception as e:
        print(f"ERROR: cannot connect to Firestore: {e}", file=sys.stderr)
        return False

    doc_id = f"{entity}_channel"
    ref = client.collection("mixer_mappings").document(doc_id)
    snap = ref.get()
    data: Dict[str, Any] = snap.to_dict() if snap.exists else {}
    params_meta = data.get("params_meta") or []

    # Locate param meta
    found = False
    for pm in params_meta:
        if str(pm.get("name", "")).lower() == param_name.lower():
            pm["fit"] = piecewise_to_dict(points)
            pm.setdefault("unit", "dB")
            found = True
            break

    if not found:
        params_meta.append({
            "name": param_name,
            "unit": "dB",
            "fit": piecewise_to_dict(points)
        })

    data["params_meta"] = params_meta

    try:
        ref.set(data, merge=True)
        return True
    except Exception as e:
        print(f"ERROR: failed to write piecewise for {entity}/{param_name}: {e}", file=sys.stderr)
        return False


def main() -> int:
    # Store volume piecewise
    vol_pts = load_piecewise_points("volume")
    print(f"Volume piecewise: {len(vol_pts)} points from {vol_pts[0][0]:.1f} to {vol_pts[-1][0]:.1f} dB")
    ok1 = write_piecewise_to_mapping("track", "volume", vol_pts)

    # Store send piecewise
    snd_pts = load_piecewise_points("send")
    print(f"Send piecewise: {len(snd_pts)} points from {snd_pts[0][0]:.1f} to {snd_pts[-1][0]:.1f} dB")
    ok2 = write_piecewise_to_mapping("track", "send", snd_pts)

    # Mirror to return and master channels
    ok3 = write_piecewise_to_mapping("return", "volume", vol_pts)
    ok4 = write_piecewise_to_mapping("return", "send", snd_pts)
    ok5 = write_piecewise_to_mapping("master", "volume", vol_pts)
    ok6 = write_piecewise_to_mapping("master", "cue", vol_pts)  # cue uses same as volume

    all_ok = ok1 and ok2 and ok3 and ok4 and ok5 and ok6

    print("\nSummary:")
    print(f"  track.volume   updated: {ok1}")
    print(f"  track.send     updated: {ok2}")
    print(f"  return.volume  updated: {ok3}")
    print(f"  return.send    updated: {ok4}")
    print(f"  master.volume  updated: {ok5}")
    print(f"  master.cue     updated: {ok6}")

    return 0 if all_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
