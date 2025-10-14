from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from server.core.events import broker
from server.services.ableton_client import request_op, data_or_raw


router = APIRouter()


@router.get("/master/status")
def get_master_status() -> Dict[str, Any]:
    resp = request_op("get_master_status", timeout=1.0)
    if not resp:
        return {"ok": False, "error": "no response"}
    data = data_or_raw(resp)
    # Assist UI: emit one-shot SSE with current values so Master tab seeds instantly
    try:
        mix = (data or {}).get("mixer") if isinstance(data, dict) else None
        if isinstance(mix, dict):
            for fld in ("volume", "pan", "cue"):
                val = mix.get(fld)
                if isinstance(val, (int, float)):
                    asyncio.create_task(broker.publish({
                        "event": "master_mixer_changed",
                        "field": fld,
                        "value": float(val),
                    }))
    except Exception:
        pass
    return {"ok": True, "data": data}


class MasterMixerBody(BaseModel):
    field: str  # 'volume' | 'pan' | 'cue'
    value: float


@router.post("/op/master/mixer")
def op_master_mixer(body: MasterMixerBody) -> Dict[str, Any]:
    if body.field not in ("volume", "pan", "cue"):
        raise HTTPException(400, "invalid_field")
    resp = request_op(
        "set_master_mixer",
        timeout=1.0,
        field=body.field,
        value=float(body.value),
    )
    if not resp:
        raise HTTPException(504, "No reply from Ableton Remote Script")
    try:
        asyncio.create_task(broker.publish({
            "event": "master_mixer_changed",
            "field": body.field,
            "value": float(body.value),
        }))
    except Exception:
        pass
    return resp


@router.get("/master/devices")
def get_master_devices_endpoint() -> Dict[str, Any]:
    resp = request_op("get_master_devices", timeout=1.0)
    if not resp:
        return {"ok": False, "error": "no response"}
    return {"ok": True, "data": data_or_raw(resp)}


@router.get("/master/device/params")
def get_master_device_params_endpoint(device: int) -> Dict[str, Any]:
    resp = request_op("get_master_device_params", timeout=1.0, device_index=int(device))
    if not resp:
        return {"ok": False, "error": "no response"}
    return {"ok": True, "data": data_or_raw(resp)}


class MasterDeviceParamBody(BaseModel):
    device_index: int
    param_index: int
    value: float


@router.post("/op/master/device/param")
def set_master_device_param(body: MasterDeviceParamBody) -> Dict[str, Any]:
    resp = request_op(
        "set_master_device_param",
        timeout=1.0,
        device_index=int(body.device_index),
        param_index=int(body.param_index),
        value=float(body.value),
    )
    if not resp:
        raise HTTPException(504, "No reply from Ableton Remote Script")
    try:
        asyncio.create_task(broker.publish({
            "event": "master_device_param_changed",
            "device_index": int(body.device_index),
            "param_index": int(body.param_index),
            "value": float(body.value),
        }))
    except Exception:
        pass
    return resp if isinstance(resp, dict) else {"ok": True}

