from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from server.core.events import broker
from server.services.ableton_client import request_op, data_or_raw


router = APIRouter()


@router.get("/returns")
def get_returns() -> Dict[str, Any]:
    resp = request_op("get_return_tracks", timeout=1.0)
    if not resp:
        return {"ok": False, "error": "no response"}
    return {"ok": True, "data": data_or_raw(resp)}


@router.get("/return/sends")
def get_return_sends(index: int) -> Dict[str, Any]:
    try:
        resp = request_op("get_return_sends", timeout=1.0, return_index=int(index))
        if not resp:
            return {"ok": False, "error": "no response"}
        return {"ok": True, "data": data_or_raw(resp)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


class ReturnRoutingSetBody(BaseModel):
    return_index: int
    audio_to_type: Optional[str] = None
    audio_to_channel: Optional[str] = None
    sends_mode: Optional[str] = None  # "pre" | "post" (optional capability)


@router.get("/return/routing")
def get_return_routing(index: int) -> Dict[str, Any]:
    resp = request_op("get_return_routing", timeout=1.0, return_index=int(index))
    if not resp:
        return {"ok": False, "error": "no response"}
    return {"ok": True, "data": data_or_raw(resp)}


@router.post("/return/routing")
def set_return_routing(body: ReturnRoutingSetBody) -> Dict[str, Any]:
    msg: Dict[str, Any] = {"return_index": int(body.return_index)}
    for k, v in body.dict().items():
        if k == "return_index":
            continue
        if v is not None:
            msg[k] = v
    resp = request_op("set_return_routing", timeout=1.2, **msg)
    if not resp:
        raise HTTPException(504, "no response from remote script")
    try:
        asyncio.create_task(broker.publish({"event": "return_routing_changed", "return_index": int(body.return_index)}))
    except Exception:
        pass
    return resp if isinstance(resp, dict) else {"ok": True, "data": resp}


@router.get("/return/devices")
def get_return_devices(index: int) -> Dict[str, Any]:
    resp = request_op("get_return_devices", timeout=1.0, return_index=int(index))
    if not resp:
        return {"ok": False, "error": "no response"}
    return {"ok": True, "data": data_or_raw(resp)}


@router.get("/return/device/params")
def get_return_device_params(index: int, device: int) -> Dict[str, Any]:
    resp = request_op(
        "get_return_device_params", timeout=1.0, return_index=int(index), device_index=int(device)
    )
    if not resp:
        return {"ok": False, "error": "no response"}
    return {"ok": True, "data": data_or_raw(resp)}

