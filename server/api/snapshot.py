from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter

from server.core.deps import get_live_index, get_value_registry


router = APIRouter()


@router.get("/snapshot")
def get_snapshot() -> Dict[str, Any]:
    li = get_live_index()
    reg = get_value_registry()
    # Minimal structure: just expose cached devices and mixer registry
    out: Dict[str, Any] = {
        "devices": {
            "tracks": li._tracks,  # safe enough for debugging; consider proper API transform later
            "returns": li._returns,
        },
        "mixer": reg.get_mixer(),
    }
    return {"ok": True, "data": out}


@router.get("/snapshot/devices")
def get_snapshot_devices(domain: str, index: int) -> Dict[str, Any]:
    li = get_live_index()
    if domain == "return":
        devs = li.get_return_devices_cached(int(index))
    elif domain == "track":
        devs = li.get_track_devices_cached(int(index))
    else:
        devs = []
    return {"ok": True, "data": {"domain": domain, "index": int(index), "devices": devs}}

