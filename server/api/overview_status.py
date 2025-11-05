from __future__ import annotations

import time
from typing import Any, Dict, List

from fastapi import APIRouter

from server.services.ableton_client import request_op, data_or_raw
from server.core.deps import get_live_index, get_value_registry
from server.config.app_config import get_snapshot_config


router = APIRouter()


@router.get("/snapshot")
async def get_snapshot(force_refresh: bool = False) -> Dict[str, Any]:
    """Stable wrapper around the existing snapshot logic (status/mixer/transport).

    Mirrors server/api/overview.py:get_snapshot output for compatibility.
    Device enrichment remains in the devices router.
    """
    # Overview (names)
    ov = request_op("get_overview", timeout=1.0) or {}
    ov_data = data_or_raw(ov) or {}
    tracks: List[Dict[str, Any]] = list(ov_data.get("tracks") or [])

    # Returns
    r = request_op("get_return_tracks", timeout=1.0) or {}
    r_data = data_or_raw(r) or {}
    returns = list(r_data.get("returns") or [])

    out_tracks: List[Dict[str, Any]] = []
    for track in tracks:
        track_idx = int(track.get("index", 0))
        out_tracks.append({
            "index": track_idx,
            "name": str(track.get("name", f"Track {track_idx + 1}")),
            "type": track.get("type", "audio"),
            "devices": [],  # keep structure; devices are provided by devices router
        })

    out_returns: List[Dict[str, Any]] = []
    for ret in returns:
        ret_idx = int(ret.get("index", 0))
        out_returns.append({
            "index": ret_idx,
            "name": str(ret.get("name", f"Return {ret_idx}")),
            "devices": [],
        })

    # LiveIndex + ValueRegistry
    li = get_live_index()
    reg = get_value_registry()
    mixer_map = reg.get_mixer() or {}

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

    # Device values TTL (snapshots keep same semantics)
    now = time.time()
    config = get_snapshot_config()
    ttl = config["device_ttl_seconds"]

    return {
        "ok": True,
        "tracks": out_tracks,
        "track_count": len(out_tracks),
        "returns": out_returns,
        "return_count": len(out_returns),
        "sends_per_track": len(out_returns),
        "master": {"name": "Master", "devices": []},
        "data": {
            "devices": {
                "tracks": li._tracks,
                "returns": li._returns,
            },
            "device_values": reg.get_devices(),
            "mixer": mixer_arr,
            "mixer_map": mixer_map,
            "transport": reg.get_transport(),
        },
        "cache_info": {
            "device_cache_age_seconds": 0.0,  # devices enrichment handled elsewhere
            "device_ttl_seconds": ttl,
            "enriched_devices_cache_age_seconds": 0.0,
        }
    }


# Delegate /snapshot/query to legacy implementation to maintain parity
try:
    # Reuse existing models/logic to avoid drift
    from server.api.overview import SnapshotQueryRequest as _SnapshotQueryRequest
    from server.api.overview import query_parameters as _legacy_query_parameters

    @router.post("/snapshot/query")
    async def query_parameters(request: _SnapshotQueryRequest) -> Dict[str, Any]:
        return await _legacy_query_parameters(request)
except Exception:
    # If legacy import fails, expose a 501 stub to make failure explicit
    @router.post("/snapshot/query")
    async def query_parameters_stub(_: Dict[str, Any]) -> Dict[str, Any]:
        return {"ok": False, "error": "not_implemented"}
