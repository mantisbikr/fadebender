from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from server.core.events import broker
from server.services.ableton_client import request_op, data_or_raw


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

