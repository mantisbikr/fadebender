from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from server.core.events import broker
from server.services.ableton_client import request_op, data_or_raw
from server.core.deps import get_store


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


@router.get("/master/mixer/capabilities")
def get_master_mixer_capabilities() -> Dict[str, Any]:
    ms = request_op("get_master_status", timeout=1.0)
    if not ms:
        return {"ok": False, "error": "no response"}
    data = data_or_raw(ms) or {}
    mixer = data.get("mixer") or {}

    store = get_store()
    mapping = store.get_mixer_channel_mapping("master") if store.enabled else None
    if not mapping:
        return {"ok": False, "error": "no_mixer_mapping"}

    params_meta = mapping.get("params_meta") or []
    sections = mapping.get("sections") or {}

    section_params = {name: (sec.get("parameters") or []) for name, sec in sections.items()}
    param_to_section = {}
    for sname, plist in section_params.items():
        for pname in plist:
            param_to_section[pname] = sname

    groups = []
    by_group = {}
    values: Dict[str, Any] = {}

    def _display_for(name: str, raw):
        try:
            if name in ("volume", "cue"):
                from server.volume_utils import live_float_to_db
                return float(f"{live_float_to_db(float(raw)):.2f}")
            if name == "pan":
                return float(f"{(float(raw) * 50.0):.2f}")
            return raw
        except Exception:
            return raw

    raw_map = {
        "volume": mixer.get("volume"),
        "pan": mixer.get("pan"),
        "cue": mixer.get("cue"),
    }

    for mp in params_meta:
        pname = mp.get("name")
        item = {
            "index": int(mp.get("index", 0)),
            "name": pname,
            "unit": mp.get("unit"),
            "labels": mp.get("labels"),
            "label_map": mp.get("label_map"),
            "min_display": mp.get("min_display"),
            "max_display": mp.get("max_display"),
            "min": mp.get("min"),
            "max": mp.get("max"),
            "control_type": mp.get("control_type"),
            "role": mp.get("role"),
            "tooltip": (mp.get("audio_knowledge") or {}).get("audio_function"),
        }
        gname = param_to_section.get(pname) or str(mp.get("group") or "").strip() or None
        if gname:
            by_group.setdefault(gname, []).append(item)
        else:
            by_group.setdefault("Other", []).append(item)
        rv = raw_map.get(pname)
        values[pname] = {"value": rv, "display_value": _display_for(pname, rv)}

    for gname, plist in by_group.items():
        sec_meta = sections.get(gname, {})
        groups.append({
            "name": gname,
            "params": plist,
            "description": sec_meta.get("description"),
            "sonic_focus": sec_meta.get("sonic_focus"),
        })

    return {"ok": True, "data": {
        "entity_type": "master",
        "device_name": "Master Mixer",
        "groups": groups,
        "ungrouped": [],
        "values": values,
    }}


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
