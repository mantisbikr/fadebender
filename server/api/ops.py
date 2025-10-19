from __future__ import annotations

import asyncio
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from server.core.events import broker
from server.services.ableton_client import request_op
from server.models.ops import MixerOp, SendOp, DeviceParamOp
from server.volume_utils import db_to_live_float
from server.core.deps import get_store
from server.services.mapping_utils import make_device_signature
import math
import re as _re


router = APIRouter()


class ReturnDeviceParamBody(BaseModel):
    return_index: int
    device_index: int
    param_index: int
    value: float


@router.post("/op/return/device/param")
def op_return_device_param(op: ReturnDeviceParamBody) -> Dict[str, Any]:
    resp = request_op(
        "set_return_device_param",
        timeout=1.0,
        return_index=int(op.return_index),
        device_index=int(op.device_index),
        param_index=int(op.param_index),
        value=float(op.value),
    )
    if not resp:
        raise HTTPException(504, "No reply from Ableton Remote Script")
    try:
        asyncio.create_task(broker.publish({
            "event": "return_device_param_changed",
            "return": int(op.return_index),
            "device": int(op.device_index),
            "param": int(op.param_index),
        }))
    except Exception:
        pass
    return resp


class ReturnSendBody(BaseModel):
    return_index: int
    send_index: int
    value: float


@router.post("/op/return/send")
def op_return_send(body: ReturnSendBody) -> Dict[str, Any]:
    resp = request_op(
        "set_return_send",
        timeout=1.0,
        return_index=int(body.return_index),
        send_index=int(body.send_index),
        value=float(body.value),
    )
    if not resp:
        raise HTTPException(504, "No reply from Ableton Remote Script")
    try:
        asyncio.create_task(broker.publish({
            "event": "return_send_changed",
            "return": int(body.return_index),
            "send_index": int(body.send_index),
        }))
    except Exception:
        pass
    return resp


class ReturnMixerBody(BaseModel):
    return_index: int
    field: str  # 'volume' | 'pan' | 'mute' | 'solo'
    value: float


@router.post("/op/return/mixer")
def op_return_mixer(body: ReturnMixerBody) -> Dict[str, Any]:
    if body.field not in ("volume", "pan", "mute", "solo"):
        raise HTTPException(400, "invalid_field")
    resp = request_op(
        "set_return_mixer",
        timeout=1.0,
        return_index=int(body.return_index),
        field=str(body.field),
        value=float(body.value),
    )
    if not resp:
        raise HTTPException(504, "No reply from Ableton Remote Script")
    try:
        asyncio.create_task(broker.publish({
            "event": "return_mixer_changed",
            "return": int(body.return_index),
            "field": body.field,
        }))
    except Exception:
        pass
    return resp


@router.post("/op/mixer")
def op_mixer(op: MixerOp) -> Dict[str, Any]:
    resp = request_op("set_mixer", timeout=1.0, **op.dict())
    if not resp:
        raise HTTPException(504, "No reply from Ableton Remote Script")
    try:
        asyncio.create_task(broker.publish({
            "event": "mixer_changed",
            "track": op.track_index,
            "field": op.field,
        }))
    except Exception:
        pass
    return resp


@router.post("/op/send")
def op_send(op: SendOp) -> Dict[str, Any]:
    resp = request_op("set_send", timeout=1.0, **op.dict())
    if not resp:
        raise HTTPException(504, "No reply from Ableton Remote Script")
    try:
        asyncio.create_task(broker.publish({
            "event": "send_changed",
            "track": op.track_index,
            "send_index": op.send_index,
        }))
    except Exception:
        pass
    return resp


@router.post("/op/device/param")
def op_device_param(op: DeviceParamOp) -> Dict[str, Any]:
    resp = request_op("set_device_param", timeout=1.0, **op.dict())
    if not resp:
        raise HTTPException(504, "No reply from Ableton Remote Script")
    try:
        asyncio.create_task(broker.publish({
            "event": "device_param_changed",
            "track": op.track_index,
            "device": op.device_index,
            "param": op.param_index,
        }))
    except Exception:
        pass
    return resp


class VolumeDbBody(BaseModel):
    track_index: int
    db: float


@router.post("/op/volume_db")
def op_volume_db(body: VolumeDbBody) -> Dict[str, Any]:
    float_value = db_to_live_float(body.db)
    resp = request_op(
        "set_mixer",
        timeout=1.0,
        track_index=int(body.track_index),
        field="volume",
        value=float_value,
    )
    if not resp:
        raise HTTPException(504, "No reply from Ableton Remote Script")
    try:
        asyncio.create_task(broker.publish({
            "event": "mixer_changed",
            "track": int(body.track_index),
            "field": "volume",
        }))
    except Exception:
        pass
    return resp


class SelectTrackBody(BaseModel):
    track_index: int


@router.post("/op/select_track")
def op_select_track(body: SelectTrackBody) -> Dict[str, Any]:
    resp = request_op("select_track", timeout=1.0, track_index=int(body.track_index))
    if not resp:
        raise HTTPException(504, "No reply from Ableton Remote Script")
    try:
        asyncio.create_task(broker.publish({
            "event": "selection_changed",
            "track": int(body.track_index),
        }))
    except Exception:
        pass
    return resp


# ---- Helpers for name-based param control on return devices ----

def _resolve_return_index(ref: str) -> int:
    r = ref.strip().lower()
    if len(r) == 1 and r in "abcdefghijklmnopqrstuvwxyz":
        return ord(r) - ord("a")
    if r.isdigit():
        return int(r)
    resp = request_op("get_return_tracks", timeout=1.0)
    returns = ((resp or {}).get("data") or {}).get("returns") or []
    for rt in returns:
        nm = str(rt.get("name", "")).lower()
        if r in nm:
            return int(rt.get("index", 0))
    raise HTTPException(404, f"return_not_found:{ref}")


def _resolve_device_index(ri: int, ref: str) -> int:
    resp = request_op("get_return_devices", timeout=1.0, return_index=int(ri))
    devices = ((resp or {}).get("data") or {}).get("devices") or []
    r = ref.strip().lower()
    if r.isdigit():
        return int(r)
    for d in devices:
        nm = str(d.get("name", "")).lower()
        if r in nm:
            return int(d.get("index", 0))
    raise HTTPException(404, f"device_not_found:{ref}")


def _resolve_param_index(ri: int, di: int, ref: str) -> int:
    resp = request_op("get_return_device_params", timeout=1.0, return_index=int(ri), device_index=int(di))
    params = ((resp or {}).get("data") or {}).get("params") or []
    r = ref.strip().lower()
    if r.isdigit():
        return int(r)
    for p in params:
        nm = str(p.get("name", "")).lower()
        if r in nm:
            return int(p.get("index", 0))
    raise HTTPException(404, f"param_not_found:{ref}")


def _parse_target_display(s: str) -> Optional[float]:
    try:
        m = _re.search(r"-?\d+(?:\.\d+)?", str(s))
        if not m:
            return None
        return float(m.group(0))
    except Exception:
        return None


def _invert_fit_to_value(fit: dict, target_y: float, vmin: float, vmax: float) -> float:
    t = (lambda a, b, y: (y - b) / a)
    ftype = fit.get("type")
    coeffs = fit.get("coeffs", {})
    if ftype == "linear":
        a = float(coeffs.get("a", 1.0))
        b = float(coeffs.get("b", 0.0))
        x = t(a, b, target_y)
    elif ftype == "log":
        a = float(coeffs.get("a", 1.0))
        b = float(coeffs.get("b", 0.0))
        x = math.exp((target_y - b) / a) if a != 0 else vmin
    elif ftype == "exp":
        a = float(coeffs.get("a", 1.0))
        b = float(coeffs.get("b", 1.0))
        if target_y <= 0:
            x = vmin
        else:
            x = math.log(target_y / a) / b if (a != 0 and b != 0) else vmin
    else:
        pts = fit.get("points") or []
        pts = sorted(
            [
                (float(p.get("y")), float(p.get("x")))
                for p in pts
                if p.get("x") is not None and p.get("y") is not None
            ]
        )
        if not pts:
            return vmin
        lo = None
        hi = None
        for y, x in pts:
            if y <= target_y:
                lo = (y, x)
            if y >= target_y and hi is None:
                hi = (y, x)
        if lo and hi and hi[0] != lo[0]:
            y1, x1 = lo
            y2, x2 = hi
            tfrac = (target_y - y1) / (y2 - y1)
            x = x1 + tfrac * (x2 - x1)
        else:
            x = lo[1] if lo else hi[1]
    return max(vmin, min(vmax, float(x)))


class ReturnParamByNameBody(BaseModel):
    return_ref: str
    device_ref: str
    param_ref: str
    target_display: Optional[str] = None
    target_value: Optional[float] = None
    mode: Optional[str] = "absolute"


@router.post("/op/return/param_by_name")
def set_return_param_by_name(body: ReturnParamByNameBody) -> Dict[str, Any]:
    ri = _resolve_return_index(body.return_ref)
    di = _resolve_device_index(ri, body.device_ref)
    pi = _resolve_param_index(ri, di, body.param_ref)
    # Fetch current param and signature
    p_resp = request_op("get_return_device_params", timeout=1.2, return_index=ri, device_index=di)
    p_list = ((p_resp or {}).get("data") or {}).get("params") or []
    cur = next((p for p in p_list if int(p.get("index", -1)) == pi), None)
    if not cur:
        raise HTTPException(404, "param_state_not_found")
    vmin = float(cur.get("min", 0.0)); vmax = float(cur.get("max", 1.0))
    device_name = str(cur.get("device_name", "")) if cur else ""
    # Build signature from device name + params list
    devs = request_op("get_return_devices", timeout=1.0, return_index=ri)
    devices = ((devs or {}).get("data") or {}).get("devices") or []
    dname = device_name or next((str(d.get("name", "")) for d in devices if int(d.get("index", -1)) == di), f"Device {di}")
    sig = make_device_signature(dname, p_list)
    store = get_store()
    mapping = None
    try:
        mapping = store.get_device_mapping(sig) if store.enabled else None
    except Exception:
        mapping = None
    # Determine target
    x = float(cur.get("value", vmin))
    target_display = body.target_display
    target_value = body.target_value
    applied_disp = None
    applied_num = None
    if target_value is not None:
        x = max(vmin, min(vmax, float(target_value)))
        resp = request_op("set_return_device_param", timeout=1.0, return_index=ri, device_index=di, param_index=pi, value=float(x))
        if not resp:
            raise HTTPException(504, "No reply from Ableton Remote Script")
        rb = request_op("get_return_device_params", timeout=1.0, return_index=ri, device_index=di)
        rps = ((rb or {}).get("data") or {}).get("params") or []
        newp = next((p for p in rps if int(p.get("index", -1)) == pi), None)
        applied_disp = str((newp or {}).get("display_value", ""))
        applied_num = _parse_target_display(applied_disp)
    elif target_display is not None:
        pm = None
        if mapping:
            pm = next((pme for pme in (mapping.get("params_meta") or []) if str(pme.get("name", "")).lower() == str(cur.get("name", "")).lower()), None)
        # Label map path
        ty = _parse_target_display(target_display)
        if pm and isinstance(pm.get("label_map"), dict) and ty is None:
            lm = pm.get("label_map") or {}
            # label_map format: {"0": "Clean", "1": "Boost", ...} (number → label)
            for k, v in lm.items():
                if str(v).strip().lower() == target_display.strip().lower():
                    x = max(vmin, min(vmax, float(k)))
                    request_op("set_return_device_param", timeout=1.0, return_index=ri, device_index=di, param_index=pi, value=float(x))
                    break
        else:
            # Numeric path with optional fit
            if pm and isinstance(pm.get("fit"), dict) and ty is not None:
                x = _invert_fit_to_value(pm.get("fit") or {}, float(ty), vmin, vmax)
            request_op("set_return_device_param", timeout=1.0, return_index=ri, device_index=di, param_index=pi, value=float(x))
        rb = request_op("get_return_device_params", timeout=1.0, return_index=ri, device_index=di)
        rps = ((rb or {}).get("data") or {}).get("params") or []
        newp = next((p for p in rps if int(p.get("index", -1)) == pi), None)
        applied_disp = str((newp or {}).get("display_value", ""))
        applied_num = _parse_target_display(applied_disp)
        # refine if numeric target provided and off by threshold
        if ty is not None and applied_num is not None:
            td = float(ty)
            err0 = td - float(applied_num)
            thresh = 0.02 * (abs(td) if td != 0 else 1.0)
            if abs(err0) > thresh:
                lo = vmin; hi = vmax; curx = x
                if err0 < 0:
                    hi = curx
                else:
                    lo = curx
                for _ in range(6):
                    mid = (lo + hi) / 2.0
                    request_op("set_return_device_param", timeout=1.0, return_index=ri, device_index=di, param_index=pi, value=float(mid))
                    rb2 = request_op("get_return_device_params", timeout=1.0, return_index=ri, device_index=di)
                    rps2 = ((rb2 or {}).get("data") or {}).get("params") or []
                    newp2 = next((p for p in rps2 if int(p.get("index", -1)) == pi), None)
                    applied_disp = str((newp2 or {}).get("display_value", ""))
                    applied_num = _parse_target_display(applied_disp)
                    if applied_num is None:
                        break
                    if abs(float(applied_num) - td) <= thresh:
                        x = mid
                        break
                    if float(applied_num) > td:
                        hi = mid
                    else:
                        lo = mid
                    x = mid
    else:
        raise HTTPException(400, "target_required")
    return {"ok": True, "signature": sig, "param": cur.get("name"), "applied_display": applied_disp}
