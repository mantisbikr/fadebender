from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from server.core.events import broker
from server.services.ableton_client import request_op, data_or_raw
import re as _re


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


def _parse_num(s: str) -> float | None:
    try:
        m = _re.search(r"-?\d+(?:\.\d+)?", str(s))
        return float(m.group(0)) if m else None
    except Exception:
        return None


@router.get("/return/device/param_lookup")
def return_device_param_lookup(index: int, device: int, param_ref: str) -> Dict[str, Any]:
    """Lookup a return device parameter by name substring and report display + on/off state.

    Returns:
      - unique match: { ok, match_type: 'unique', param: { name,index,value,min,max,display_value,is_on,display_num } }
      - ambiguous: { ok, match_type: 'ambiguous', candidates: [names...] }
      - not found: { ok:false, match_type:'not_found' }
    """
    pr = request_op("get_return_device_params", timeout=1.0, return_index=int(index), device_index=int(device))
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
    # Simple on/off heuristic for toggles
    nlc = str(name or "").lower()
    is_toggle_like = nlc.endswith(" on") or nlc.endswith(" enabled") or nlc.endswith(" enable")
    is_on = None
    try:
        if is_toggle_like:
            # consider near min as off, near max as on
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
