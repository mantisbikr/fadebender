from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, List

from fastapi import APIRouter
from pydantic import BaseModel

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
            "transport": reg.get_transport(),  # Last-known transport state (tempo, metronome)
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


# ============================================================================
# PHASE 3: Snapshot Query Endpoint with Device Parameters + Capabilities
# ============================================================================

class QueryTarget(BaseModel):
    """Single parameter to query."""
    track: str | None = None  # "Track 1", "Return A", "Master", or None for transport
    plugin: str | None = None  # Device name (e.g., "reverb", "compressor"), or None for mixer params
    parameter: str  # Parameter name (e.g., "volume", "decay", "threshold"), or "*" for all device params
    device_ordinal: int | None = None  # Optional device ordinal (e.g., "reverb 2" → ordinal=2)


class SnapshotQueryRequest(BaseModel):
    """Request to query multiple parameters."""
    targets: List[QueryTarget]


@router.post("/snapshot/query")
async def query_parameters(request: SnapshotQueryRequest) -> Dict[str, Any]:
    """Query parameter values from snapshot with Live fallback (Phase 2: mixer + transport).

    Returns conversational answer plus structured values.
    Phase 2: Snapshot-first with Live fallback and snapshot update
    Phase 3: Will add device parameters + capabilities
    """
    from server.services.ableton_client import get_transport as svc_get_transport

    reg = get_value_registry()
    results = []

    for target in request.targets:
        track_name = target.track or ""
        param_name = target.parameter

        # Transport params (no track)
        if not track_name and param_name in ("tempo", "metronome"):
            transport = reg.get_transport()
            param_data = transport.get(param_name)
            if param_data:
                results.append({
                    "track": None,
                    "parameter": param_name,
                    "value": param_data.get("value"),
                    "display_value": str(param_data.get("value")),
                    "source": param_data.get("source"),
                })
            else:
                # Fallback to Live
                loop = asyncio.get_event_loop()
                transport_live = await loop.run_in_executor(None, lambda: svc_get_transport(timeout=1.0))
                if transport_live and transport_live.get("ok"):
                    transport_data = transport_live.get("data") or {}
                    value = transport_data.get(param_name)
                    if value is not None:
                        # Update snapshot
                        reg.update_transport(param_name, value, source="live_fallback")
                        results.append({
                            "track": None,
                            "parameter": param_name,
                            "value": value,
                            "display_value": str(value),
                            "source": "live_fallback",
                        })
                    else:
                        results.append({
                            "track": None,
                            "parameter": param_name,
                            "error": "not_available",
                        })
                else:
                    results.append({
                        "track": None,
                        "parameter": param_name,
                        "error": "live_query_failed",
                    })
            continue

        # Parse track/return/master
        domain, index = _parse_track_name(track_name)
        if not domain:
            results.append({
                "track": track_name,
                "parameter": param_name,
                "error": f"Could not parse track: {track_name}",
            })
            continue

        # Device parameters (if plugin specified)
        if target.plugin:
            result = await _query_device_param(domain, index, target.plugin, param_name, track_name, target.device_ordinal)
            results.append(result)
            continue

        # Query mixer parameter from snapshot
        mixer_map = reg.get_mixer()
        entity_data = mixer_map.get(domain, {})

        # Get track/return/master data
        if domain == "master":
            track_data = entity_data.get(0, {})
        else:
            track_data = entity_data.get(index, {})

        param_data = track_data.get(param_name)

        if param_data:
            # Found in snapshot
            display_val = param_data.get("display") or _format_mixer_display(param_name, param_data.get("normalized"))
            results.append({
                "track": track_name,
                "parameter": param_name,
                "value": param_data.get("normalized"),
                "display_value": display_val,
                "source": param_data.get("source"),
            })
        else:
            # Fallback to Live
            result = await _query_live_mixer_param(domain, index, param_name, track_name, reg)
            results.append(result)

    # Format conversational answer
    answer = _format_query_answer(results)

    return {
        "ok": True,
        "answer": answer,
        "values": results,
    }


def _parse_track_name(track_name: str) -> tuple[str | None, int | None]:
    """Parse track name into domain and index.
    
    Examples:
        "Master" → ("master", 0)
        "Track 1" → ("track", 1)
        "Return A" → ("return", 0)
        "A-Reverb" → ("return", 0)
    """
    if not track_name:
        return None, None

    name_lower = track_name.lower().strip()

    # Master
    if name_lower == "master":
        return "master", 0

    # Return track patterns
    if "return" in name_lower or name_lower[0] in "abc":
        # Extract letter: "Return A" → A, "A-Reverb" → A
        import re
        match = re.search(r'\b([A-C])\b', track_name.upper())
        if match:
            letter = match.group(1)
            return "return", ord(letter) - ord('A')

    # Track pattern: "Track 1", "1-808 Core"
    import re
    match = re.search(r'(\d+)', track_name)
    if match:
        track_idx = int(match.group(1))
        return "track", track_idx

    return None, None


def _format_mixer_display(param_name: str, normalized_value: float | None) -> str:
    """Format normalized mixer value to display string."""
    if normalized_value is None:
        return "N/A"

    # Volume/Cue/Sends: dB
    if param_name in ("volume", "cue") or param_name.startswith("send"):
        if normalized_value <= 0.0:
            return "-inf dB"
        try:
            from server.volume_utils import live_float_to_db
            db_val = live_float_to_db(normalized_value)
            return f"{db_val:.1f} dB"
        except Exception:
            return f"{normalized_value:.2f}"

    # Pan: -50 to +50
    if param_name == "pan":
        pan_val = normalized_value * 50.0
        return f"{pan_val:+.1f}"

    # Mute/Solo: On/Off
    if param_name in ("mute", "solo"):
        return "On" if normalized_value > 0.5 else "Off"

    # Default
    return f"{normalized_value:.2f}"


def _format_query_answer(results: List[Dict[str, Any]]) -> str:
    """Format query results into conversational answer."""
    if not results:
        return "No parameters queried."

    # Filter out errors
    valid_results = [r for r in results if "error" not in r]
    
    if not valid_results:
        # All errors
        if len(results) == 1:
            return results[0].get("error", "Parameter not available")
        return "Parameters not available in snapshot. Try adjusting them via the UI first."

    # Single result
    if len(valid_results) == 1:
        r = valid_results[0]
        track = r.get("track") or "Transport"
        param = r.get("parameter", "")
        display = r.get("display_value", "N/A")
        return f"{track} {param} is {display}"

    # Multiple results - group by track
    track_name = valid_results[0].get("track", "")
    parts = []
    for r in valid_results:
        param = r.get("parameter", "")
        display = r.get("display_value", "N/A")
        parts.append(f"{param}: {display}")

    return f"{track_name} - " + ", ".join(parts)


async def _query_live_mixer_param(domain: str, index: int, param_name: str, track_name: str, reg: Any) -> Dict[str, Any]:
    """Query mixer parameter from Live and update snapshot."""
    import re
    loop = asyncio.get_event_loop()

    try:
        # Handle sends separately
        if param_name.startswith("send"):
            # Extract send index from "send A" → 0, "send B" → 1, etc.
            match = re.search(r'send\s+([A-Z])', param_name, re.IGNORECASE)
            if match and domain == "track":
                send_letter = match.group(1).upper()
                send_index = ord(send_letter) - ord('A')

                resp = await loop.run_in_executor(
                    None,
                    lambda: request_op("get_track_sends", timeout=1.0, track_index=index)
                )

                if resp and resp.get("ok"):
                    sends_data = data_or_raw(resp) or {}
                    sends = sends_data.get("sends") or []
                    send = next((s for s in sends if int(s.get("index", -1)) == send_index), None)
                    if send:
                        value = send.get("value")
                        if value is not None:
                            # Update snapshot
                            reg.update_mixer(
                                entity="track",
                                index=index,
                                field=param_name,
                                normalized_value=value,
                                display_value=None,
                                unit=None,
                                source="live_fallback"
                            )
                            display_val = _format_mixer_display(param_name, value)
                            return {
                                "track": track_name,
                                "parameter": param_name,
                                "value": value,
                                "display_value": display_val,
                                "source": "live_fallback",
                            }

            return {
                "track": track_name,
                "parameter": param_name,
                "error": "send_not_found",
            }

        # Query based on domain
        if domain == "track":
            resp = await loop.run_in_executor(
                None,
                lambda: request_op("get_track_status", timeout=1.0, track_index=index)
            )
        elif domain == "return":
            resp = await loop.run_in_executor(
                None,
                lambda: request_op("get_return_tracks", timeout=1.0)
            )
        elif domain == "master":
            resp = await loop.run_in_executor(
                None,
                lambda: request_op("get_master_status", timeout=1.0)
            )
        else:
            return {
                "track": track_name,
                "parameter": param_name,
                "error": f"unknown_domain:{domain}",
            }

        if not resp or not resp.get("ok"):
            return {
                "track": track_name,
                "parameter": param_name,
                "error": "live_query_failed",
            }

        resp_data = data_or_raw(resp) or {}

        # Extract value based on domain
        if domain == "return":
            returns = resp_data.get("returns") or []
            ret = next((r for r in returns if int(r.get("index", -1)) == index), None)
            if not ret:
                return {
                    "track": track_name,
                    "parameter": param_name,
                    "error": "return_not_found",
                }
            resp_data = ret

        # Get parameter value
        if param_name in ("mute", "solo"):
            value = resp_data.get(param_name)
        else:
            mixer = resp_data.get("mixer") or {}
            value = mixer.get(param_name)

        if value is None:
            return {
                "track": track_name,
                "parameter": param_name,
                "error": "parameter_not_available",
            }

        # Update snapshot
        reg.update_mixer(
            entity=domain,
            index=index,
            field=param_name,
            normalized_value=value,
            display_value=None,
            unit=None,
            source="live_fallback"
        )

        display_val = _format_mixer_display(param_name, value)
        return {
            "track": track_name,
            "parameter": param_name,
            "value": value,
            "display_value": display_val,
            "source": "live_fallback",
        }

    except Exception as e:
        return {
            "track": track_name,
            "parameter": param_name,
            "error": f"exception:{str(e)}",
        }


async def _query_device_param(domain: str, index: int, plugin_name: str, param_name: str, track_name: str, device_ordinal: int | None) -> Dict[str, Any]:
    """Query device parameter using existing endpoints and return value + capabilities."""
    loop = asyncio.get_event_loop()

    try:
        # Step 1: Resolve plugin name to device_index
        if domain == "track":
            devs_resp = await loop.run_in_executor(
                None,
                lambda: request_op("get_track_devices", timeout=1.0, track_index=index)
            )
        elif domain == "return":
            devs_resp = await loop.run_in_executor(
                None,
                lambda: request_op("get_return_devices", timeout=1.0, return_index=index)
            )
        elif domain == "master":
            devs_resp = await loop.run_in_executor(
                None,
                lambda: request_op("get_master_devices", timeout=1.0)
            )
        else:
            return {
                "track": track_name,
                "plugin": plugin_name,
                "parameter": param_name,
                "error": f"unsupported_domain:{domain}",
            }

        if not devs_resp or not devs_resp.get("ok"):
            return {
                "track": track_name,
                "plugin": plugin_name,
                "parameter": param_name,
                "error": "failed_to_get_devices",
            }

        devices_data = data_or_raw(devs_resp) or {}
        devices = devices_data.get("devices") or []

        # Find matching device(s) by name (fuzzy match)
        matches = []
        for dev in devices:
            dev_name = str(dev.get("name", "")).lower()
            plugin_lower = plugin_name.lower()
            if plugin_lower in dev_name or dev_name in plugin_lower:
                matches.append(int(dev.get("index", -1)))

        if not matches:
            return {
                "track": track_name,
                "plugin": plugin_name,
                "parameter": param_name,
                "error": "device_not_found",
            }

        # Use ordinal if specified (1-based), otherwise first match
        if device_ordinal is not None and device_ordinal > 0 and device_ordinal <= len(matches):
            device_index = matches[device_ordinal - 1]
        else:
            device_index = matches[0]

        # Step 2: Query parameter value using param_lookup endpoint
        if domain == "track":
            param_resp = await loop.run_in_executor(
                None,
                lambda: request_op("get_track_device_params", timeout=1.0, track_index=index, device_index=device_index)
            )
        elif domain == "return":
            param_resp = await loop.run_in_executor(
                None,
                lambda: request_op("get_return_device_params", timeout=1.0, return_index=index, device_index=device_index)
            )
        elif domain == "master":
            param_resp = await loop.run_in_executor(
                None,
                lambda: request_op("get_master_device_params", timeout=1.0, device_index=device_index)
            )
        else:
            return {
                "track": track_name,
                "plugin": plugin_name,
                "parameter": param_name,
                "error": "unsupported_domain_for_params",
            }

        if not param_resp or not param_resp.get("ok"):
            return {
                "track": track_name,
                "plugin": plugin_name,
                "parameter": param_name,
                "error": "failed_to_get_params",
            }

        params_data = data_or_raw(param_resp) or {}
        params = params_data.get("params") or []

        # Find matching parameter (fuzzy match)
        param_lower = param_name.lower()
        param_matches = [p for p in params if param_lower in str(p.get("name", "")).lower()]

        if not param_matches:
            return {
                "track": track_name,
                "plugin": plugin_name,
                "parameter": param_name,
                "error": "parameter_not_found",
            }

        if len(param_matches) > 1:
            return {
                "track": track_name,
                "plugin": plugin_name,
                "parameter": param_name,
                "error": "ambiguous_parameter",
                "candidates": [p.get("name") for p in param_matches],
            }

        param = param_matches[0]
        param_value = param.get("value")
        param_display = param.get("display_value") or str(param_value)
        param_index = param.get("index")
        param_actual_name = param.get("name")

        # Step 3: Get capabilities (optional, for UI rendering)
        capabilities = None
        try:
            if domain == "return":
                caps_resp = await loop.run_in_executor(
                    None,
                    lambda: request_op("get_return_device_capabilities", timeout=1.0, return_index=index, device_index=device_index)
                )
                if caps_resp and caps_resp.get("ok"):
                    capabilities = data_or_raw(caps_resp)
        except Exception:
            pass  # Capabilities are optional

        result = {
            "track": track_name,
            "plugin": plugin_name,
            "parameter": param_actual_name,
            "value": param_value,
            "display_value": param_display,
            "source": "live",
            "device_index": device_index,
            "param_index": param_index,
        }

        if capabilities:
            result["capabilities"] = capabilities

        return result

    except Exception as e:
        return {
            "track": track_name,
            "plugin": plugin_name,
            "parameter": param_name,
            "error": f"exception:{str(e)}",
        }
