from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException

from server.services.ableton_client import request_op


router = APIRouter()


@router.post("/device/load")
def load_device(
    domain: str,
    index: int,
    device_name: str,
    preset_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Load a device (optionally preset) onto a track or return.

    domain: "track" or "return"
    index:  track index (1-based) for domain="track", or return index (0-based) for domain="return"
    """
    d = (domain or "").strip().lower()
    if d == "return":
        op = "load_return_device"
        params = {"return_index": int(index)}
    elif d == "track":
        op = "load_track_device"
        params = {"track_index": int(index)}
    else:
        raise HTTPException(400, "domain must be 'track' or 'return'")

    params["device_name"] = str(device_name)
    if preset_name is not None:
        params["preset_name"] = str(preset_name)

    resp = request_op(op, timeout=5.0, **params)
    if not resp:
        return {"ok": False, "error": "no_response"}
    return resp if isinstance(resp, dict) else {"ok": True, "data": resp}

