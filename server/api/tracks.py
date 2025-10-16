from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from server.core.events import broker
from server.services.ableton_client import request_op, data_or_raw
import re as _re


router = APIRouter()


@router.get("/track/status")
def track_status(index: int) -> Dict[str, Any]:
    resp = request_op("get_track_status", timeout=1.0, track_index=int(index))
    if not resp:
        return {"ok": False, "error": "no response"}
    return {"ok": True, "data": data_or_raw(resp)}


@router.get("/track/sends")
def track_sends(index: int) -> Dict[str, Any]:
    resp = request_op("get_track_sends", timeout=1.0, track_index=int(index))
    if not resp:
        return {"ok": False, "error": "no response"}
    return {"ok": True, "data": data_or_raw(resp)}


class TrackRoutingSetBody(BaseModel):
    track_index: int
    monitor_state: Optional[str] = None  # "in" | "auto" | "off"
    audio_from_type: Optional[str] = None
    audio_from_channel: Optional[str] = None
    audio_to_type: Optional[str] = None
    audio_to_channel: Optional[str] = None
    midi_from_type: Optional[str] = None
    midi_from_channel: Optional[str] = None
    midi_to_type: Optional[str] = None
    midi_to_channel: Optional[str] = None


@router.get("/track/routing")
def get_track_routing(index: int) -> Dict[str, Any]:
    resp = request_op("get_track_routing", timeout=1.0, track_index=int(index))
    if not resp:
        return {"ok": False, "error": "no response"}
    return {"ok": True, "data": data_or_raw(resp)}


@router.post("/track/routing")
def set_track_routing(body: TrackRoutingSetBody) -> Dict[str, Any]:
    msg: Dict[str, Any] = {"track_index": int(body.track_index)}
    for k, v in body.dict().items():
        if k == "track_index":
            continue
        if v is not None:
            msg[k] = v
    resp = request_op("set_track_routing", timeout=1.2, **msg)
    if not resp:
        raise HTTPException(504, "no response from remote script")
    try:
        asyncio.create_task(broker.publish({"event": "track_routing_changed", "track_index": int(body.track_index)}))
    except Exception:
        pass
    return resp if isinstance(resp, dict) else {"ok": True, "data": resp}


@router.get("/track/devices")
def get_track_devices(index: int) -> Dict[str, Any]:
    resp = request_op("get_track_devices", timeout=1.0, track_index=int(index))
    if not resp:
        return {"ok": False, "error": "no response"}
    return {"ok": True, "data": data_or_raw(resp)}


@router.get("/track/device/params")
def get_track_device_params(index: int, device: int) -> Dict[str, Any]:
    resp = request_op(
        "get_track_device_params", timeout=1.0, track_index=int(index), device_index=int(device)
    )
    if not resp:
        return {"ok": False, "error": "no response"}
    return {"ok": True, "data": data_or_raw(resp)}


def _parse_num(s: str) -> float | None:
    try:
        m = _re.search(r"-?\d+(?:\.\d+)?", str(s))
        return float(m.group(0)) if m else None
    except Exception:
        return None


@router.get("/track/device/param_lookup")
def track_device_param_lookup(index: int, device: int, param_ref: str) -> Dict[str, Any]:
    """Lookup a track device parameter by name substring and report display + on/off state.

    Returns same shape as /return/device/param_lookup.
    """
    pr = request_op("get_track_device_params", timeout=1.0, track_index=int(index), device_index=int(device))
    if not pr:
        return {"ok": False, "error": "no response"}
    params = ((pr or {}).get("data") or {}).get("params") or []
    pref = str(param_ref or "").strip().lower()
    cands = [p for p in params if pref in str(p.get("name", "")).lower()]
    if not cands:
        return {"ok": False, "match_type": "not_found"}
    if len(cands) > 1:
        return {"ok": False, "match_type": "ambiguous", "candidates": [p.get("name") for p in cands]}
    p = cands[0]
    name = p.get("name")
    val = float(p.get("value", 0.0))
    vmin = float(p.get("min", 0.0)); vmax = float(p.get("max", 1.0))
    disp = p.get("display_value")
    disp_num = _parse_num(disp)
    nlc = str(name or "").lower()
    is_toggle_like = nlc.endswith(" on") or nlc.endswith(" enabled") or nlc.endswith(" enable")
    is_on = None
    try:
        if is_toggle_like:
            is_on = abs(val - vmax) <= 1e-6
    except Exception:
        is_on = None
    return {
        "ok": True,
        "match_type": "unique",
        "param": {
            "name": name,
            "index": p.get("index"),
            "value": val,
            "min": vmin,
            "max": vmax,
            "display_value": disp,
            "display_num": disp_num,
            "is_on": is_on,
        },
    }


class TrackDeviceParamBody(BaseModel):
    track_index: int
    device_index: int
    param_index: int
    value: float


@router.post("/op/track/device/param")
def set_track_device_param(body: TrackDeviceParamBody) -> Dict[str, Any]:
    resp = request_op(
        "set_track_device_param",
        timeout=1.0,
        track_index=int(body.track_index),
        device_index=int(body.device_index),
        param_index=int(body.param_index),
        value=float(body.value),
    )
    if not resp:
        raise HTTPException(504, "No reply from Ableton Remote Script")
    try:
        asyncio.create_task(broker.publish({
            "event": "device_param_changed",
            "scope": "track",
            "track": int(body.track_index),
            "device_index": int(body.device_index),
            "param_index": int(body.param_index),
            "value": float(body.value),
        }))
    except Exception:
        pass
    return resp if isinstance(resp, dict) else {"ok": True}
