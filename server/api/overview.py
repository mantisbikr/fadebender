from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter

from server.services.ableton_client import request_op, data_or_raw


router = APIRouter()


@router.get("/snapshot")
def snapshot() -> Dict[str, Any]:
    """Return a concise summary of the current Live set.

    - tracks: [{index,name,type}], count
    - returns: [{index,name,devices:[name...] }], count
    - sends_per_track: equals return count (best-effort)
    """
    ov = request_op("get_overview", timeout=1.0) or {}
    ov_data = data_or_raw(ov) or {}
    tracks: List[Dict[str, Any]] = list(ov_data.get("tracks") or [])

    # Returns + devices
    r = request_op("get_return_tracks", timeout=1.0) or {}
    r_data = data_or_raw(r) or {}
    returns = list(r_data.get("returns") or [])
    out_returns: List[Dict[str, Any]] = []
    for rt in returns:
        idx = int(rt.get("index", 0))
        devs = request_op("get_return_devices", timeout=0.8, return_index=idx) or {}
        devs_data = data_or_raw(devs) or {}
        names = [str(d.get("name", f"Device {int(d.get('index',0))}")) for d in (devs_data.get("devices") or [])]
        out_returns.append({
            "index": idx,
            "name": str(rt.get("name", f"Return {idx}")),
            "devices": names,
        })

    return {
        "ok": True,
        "tracks": tracks,
        "track_count": len(tracks),
        "returns": out_returns,
        "return_count": len(out_returns),
        "sends_per_track": len(out_returns),
    }

