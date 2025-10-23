from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, List

from fastapi import APIRouter

from server.services.ableton_client import request_op, data_or_raw
from server.core.deps import get_live_index, get_value_registry
from server.config.app_config import get_snapshot_config


router = APIRouter()

# Module-level cache for device values with TTL tracking
_device_cache_timestamp: float = 0.0


async def _refresh_device_values_chunked(tracks: List[Dict[str, Any]], returns: List[Dict[str, Any]]) -> None:
    """Refresh device parameter values with chunked parallel queries.

    Args:
        tracks: List of track metadata dicts
        returns: List of return metadata dicts with device names
    """
    from server.core.deps import get_value_registry

    reg = get_value_registry()
    config = get_snapshot_config()
    chunk_size = config["device_chunk_size"]
    delay_ms = config["device_chunk_delay_ms"]

    # Build list of all devices to query
    devices_to_query: List[Dict[str, Any]] = []

    # Track devices
    for track in tracks:
        track_idx = int(track.get("index", 0))
        try:
            track_devs_resp = request_op("get_track_devices", timeout=0.8, track_index=track_idx) or {}
            track_devs_data = data_or_raw(track_devs_resp) or {}
            for dev in (track_devs_data.get("devices") or []):
                devices_to_query.append({
                    "domain": "track",
                    "index": track_idx,
                    "device_index": int(dev.get("index", 0)),
                })
        except Exception:
            continue

    # Return devices
    for ret in returns:
        ret_idx = int(ret.get("index", 0))
        try:
            ret_devs_resp = request_op("get_return_devices", timeout=0.8, return_index=ret_idx) or {}
            ret_devs_data = data_or_raw(ret_devs_resp) or {}
            for dev in (ret_devs_data.get("devices") or []):
                devices_to_query.append({
                    "domain": "return",
                    "index": ret_idx,
                    "device_index": int(dev.get("index", 0)),
                })
        except Exception:
            continue

    if not devices_to_query:
        return

    # Process in chunks
    for i in range(0, len(devices_to_query), chunk_size):
        chunk = devices_to_query[i:i+chunk_size]

        # Query chunk in parallel using gather
        tasks = []
        for d in chunk:
            if d["domain"] == "track":
                task = asyncio.create_task(_query_track_device_params(d["index"], d["device_index"]))
            else:
                task = asyncio.create_task(_query_return_device_params(d["index"], d["device_index"]))
            tasks.append((d, task))

        # Wait for chunk to complete
        results = await asyncio.gather(*[t for _, t in tasks], return_exceptions=True)

        # Update registry with results
        for (d, _), result in zip(tasks, results):
            if isinstance(result, dict) and result.get("ok"):
                params = (data_or_raw(result) or {}).get("params") or []
                for param in params:
                    try:
                        reg.update_device_param(
                            domain=d["domain"],
                            index=d["index"],
                            device_index=d["device_index"],
                            param_name=str(param.get("name", "")),
                            normalized_value=param.get("value"),
                            display_value=param.get("display_value"),
                            unit=param.get("unit"),
                            source="snapshot_refresh"
                        )
                    except Exception:
                        continue

        # Brief pause before next chunk (unless last chunk)
        if i + chunk_size < len(devices_to_query):
            await asyncio.sleep(delay_ms / 1000.0)


async def _query_track_device_params(track_index: int, device_index: int) -> Dict[str, Any]:
    """Async wrapper for track device param query."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        lambda: request_op("get_track_device_params",
                          track_index=track_index,
                          device_index=device_index,
                          timeout=1.0) or {}
    )


async def _query_return_device_params(return_index: int, device_index: int) -> Dict[str, Any]:
    """Async wrapper for return device param query."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        lambda: request_op("get_return_device_params",
                          return_index=return_index,
                          device_index=device_index,
                          timeout=1.0) or {}
    )


@router.get("/snapshot")
async def snapshot(force_refresh: bool = False) -> Dict[str, Any]:
    """Return a comprehensive snapshot of the current Live set.

    Includes:
    - Overview: tracks, returns (with device names)
    - Devices: LiveIndex cached device structures (tracks, returns)
    - Mixer: ValueRegistry mixer parameter values (volume, pan, sends, etc.)
    """
    # Get overview data (track/return names and types)
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

    # Get LiveIndex and ValueRegistry data
    li = get_live_index()
    reg = get_value_registry()
    mixer_map = reg.get_mixer() or {}

    # Transform mixer_map (string-keyed dicts) into array-of-objects for easy clients
    def _map_to_array(m: Dict[str, Dict[int, Dict[str, Any]]], key: str) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        try:
            tbl = m.get(key) or {}
            for k, fields in tbl.items():
                try:
                    idx = int(k)
                except Exception:
                    idx = k
                out.append({"index": idx, "fields": fields})
        except Exception:
            pass
        # Sort by index if numeric
        try:
            out.sort(key=lambda x: int(x.get("index", 0)))
        except Exception:
            pass
        return out

    mixer_arr = {
        "track": _map_to_array(mixer_map, "track"),
        "return": _map_to_array(mixer_map, "return"),
        "master": (mixer_map.get("master") or {}),
    }

    # Device values: Lazy refresh with TTL
    global _device_cache_timestamp
    now = time.time()
    config = get_snapshot_config()
    ttl = config["device_ttl_seconds"]

    if force_refresh or (now - _device_cache_timestamp) > ttl:
        # Refresh device values from Live
        await _refresh_device_values_chunked(tracks, out_returns)
        _device_cache_timestamp = now

    return {
        "ok": True,
        "tracks": tracks,
        "track_count": len(tracks),
        "returns": out_returns,
        "return_count": len(out_returns),
        "sends_per_track": len(out_returns),
        "data": {
            "devices": {
                "tracks": li._tracks,
                "returns": li._returns,
            },
            # Last-known device parameter values written via ValueRegistry
            "device_values": reg.get_devices(),
            "mixer": mixer_arr,
            "mixer_map": mixer_map,  # for backward-compat tests that use string keys
        },
        "cache_info": {
            "device_cache_age_seconds": round(now - _device_cache_timestamp, 2),
            "device_ttl_seconds": ttl,
        }
    }


@router.get("/snapshot/devices")
def get_snapshot_devices(domain: str, index: int) -> Dict[str, Any]:
    """Get cached device list for a specific track or return from LiveIndex.

    Args:
        domain: "track" or "return"
        index: Track index (1-based for tracks) or return index (0-based)

    Returns:
        List of devices with their cached structure from LiveIndex
    """
    li = get_live_index()
    if domain == "return":
        devs = li.get_return_devices_cached(int(index))
    elif domain == "track":
        devs = li.get_track_devices_cached(int(index))
    else:
        devs = []
    return {"ok": True, "data": {"domain": domain, "index": int(index), "devices": devs}}
