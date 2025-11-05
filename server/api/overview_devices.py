from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, List

from fastapi import APIRouter

from server.services.ableton_client import request_op, data_or_raw
from server.core.deps import get_store


router = APIRouter()

_enriched_devices_cache: Dict[str, Any] = {"tracks": {}, "returns": {}, "master": [], "timestamp": 0.0}
_lock = asyncio.Lock()


def _enrich_device_with_type(device_name: str) -> Dict[str, Any]:
    try:
        store = get_store()
        if store and store.enabled:
            device_type = store.get_device_type_by_name(device_name)
            if device_type:
                return {"device_type": device_type}
    except Exception:
        pass
    return {}


async def _refresh_enriched(tracks: List[Dict[str, Any]], returns: List[Dict[str, Any]]) -> None:
    global _enriched_devices_cache
    async with _lock:
        new_cache: Dict[str, Any] = {"tracks": {}, "returns": {}, "master": [], "timestamp": time.time()}
        # Tracks
        for track in tracks:
            ti = int(track.get("index", 0))
            try:
                resp = request_op("get_track_devices", timeout=0.8, track_index=ti) or {}
                data = data_or_raw(resp) or {}
                enriched = []
                for d in (data.get("devices") or []):
                    obj = {"index": int(d.get("index", 0)), "name": str(d.get("name", f"Device {int(d.get('index',0))}"))}
                    obj.update(_enrich_device_with_type(obj["name"]))
                    enriched.append(obj)
                new_cache["tracks"][ti] = enriched
            except Exception:
                new_cache["tracks"][ti] = []
        # Returns
        for ret in returns:
            ri = int(ret.get("index", 0))
            try:
                resp = request_op("get_return_devices", timeout=0.8, return_index=ri) or {}
                data = data_or_raw(resp) or {}
                enriched = []
                for d in (data.get("devices") or []):
                    obj = {"index": int(d.get("index", 0)), "name": str(d.get("name", f"Device {int(d.get('index',0))}"))}
                    obj.update(_enrich_device_with_type(obj["name"]))
                    enriched.append(obj)
                new_cache["returns"][ri] = enriched
            except Exception:
                new_cache["returns"][ri] = []
        # Master
        try:
            resp = request_op("get_master_devices", timeout=0.8) or {}
            data = data_or_raw(resp) or {}
            enriched = []
            for d in (data.get("devices") or []):
                obj = {"index": int(d.get("index", 0)), "name": str(d.get("name", f"Device {int(d.get('index',0))}"))}
                obj.update(_enrich_device_with_type(obj["name"]))
                enriched.append(obj)
            new_cache["master"] = enriched
        except Exception:
            new_cache["master"] = []
        _enriched_devices_cache = new_cache


@router.get("/devices/enriched")
async def get_enriched_devices() -> Dict[str, Any]:
    # Overview metadata
    ov = request_op("get_overview", timeout=1.0) or {}
    tracks: List[Dict[str, Any]] = list((data_or_raw(ov) or {}).get("tracks") or [])
    r = request_op("get_return_tracks", timeout=1.0) or {}
    returns: List[Dict[str, Any]] = list((data_or_raw(r) or {}).get("returns") or [])

    age = time.time() - _enriched_devices_cache.get("timestamp", 0)
    if age > 3600 or not _enriched_devices_cache.get("tracks"):
        await _refresh_enriched(tracks, returns)

    return {"ok": True, "tracks": _enriched_devices_cache.get("tracks", {}), "returns": _enriched_devices_cache.get("returns", {}), "master": _enriched_devices_cache.get("master", []), "age_seconds": round(age, 2)}

