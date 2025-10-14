from __future__ import annotations

from typing import Any, Dict, Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from server.services.ableton_client import request_op
from server.volume_utils import db_to_live_float


router = APIRouter()


Domain = Literal["track", "return", "master", "device", "transport"]


class CanonicalIntent(BaseModel):
    domain: Domain = Field(..., description="Scope: track|return|master|device|transport")
    action: Literal["set"] = "set"

    # Targets (one of):
    track_index: Optional[int] = None
    return_index: Optional[int] = None
    device_index: Optional[int] = None  # device on track or return (depending on which index is present)

    # Field/parameter selection
    field: Optional[str] = None            # mixer field: volume|pan|mute|solo|tempo|send
    send_index: Optional[int] = None       # for sends
    param_index: Optional[int] = None      # device param index (preferred)
    param_ref: Optional[str] = None        # device param lookup by name (contains match)

    # Value + unit (absolute only in v1)
    value: Optional[float] = None
    unit: Optional[str] = None             # db|percent|normalized|ms|hz|on|off

    # Options
    dry_run: bool = False
    clamp: bool = True


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _resolve_param(params: list[dict], param_index: Optional[int], param_ref: Optional[str]) -> dict:
    if isinstance(param_index, int):
        for p in params:
            if int(p.get("index", -1)) == int(param_index):
                return p
        raise HTTPException(404, "param_not_found")
    if param_ref:
        pref = param_ref.strip().lower()
        cand = [p for p in params if pref in str(p.get("name", "")).lower()]
        if len(cand) == 1:
            return cand[0]
        if len(cand) == 0:
            raise HTTPException(404, "param_not_found")
        raise HTTPException(409, "param_ambiguous")
    raise HTTPException(400, "param_selector_required")


def _auto_enable_master_if_needed(params: list[dict], target_param_name: str) -> Optional[dict]:
    """Heuristic: if a related "X On" exists and is off, return that toggle param dict.

    This is a simple name-based approach to help users who set a dependent first.
    More robust, mapping-driven grouping can replace this later.
    """
    name = (target_param_name or "").lower()
    candidates = []
    # Common sections whose dependents often require an On toggle
    keys = [
        ("chorus", "chorus on"),
        ("er spin", "er spin on"),
        ("lowshelf", "low shelf on"),
        ("low shelf", "low shelf on"),
        ("hishelf", "hi shelf on"),
        ("high shelf", "hi shelf on"),
        ("hifilter", "hifilter on"),
        ("hi filter", "hifilter on"),
        ("freeze", "freeze on"),
    ]
    for k, toggle in keys:
        if k in name:
            candidates.append(toggle)
    if not candidates:
        return None
    # find first toggle present and currently off
    for p in params:
        pname = str(p.get("name", "")).lower()
        if any(t in pname for t in candidates):
            try:
                # Off if value ~ 0.0
                val = float(p.get("value", 0.0))
                vmin = float(p.get("min", 0.0)); vmax = float(p.get("max", 1.0))
                is_off = abs(val - vmin) <= 1e-6
                if is_off:
                    return p
            except Exception:
                continue
    return None


@router.post("/intent/execute")
def execute_intent(intent: CanonicalIntent) -> Dict[str, Any]:
    d = intent.domain
    field = intent.field or ""
    # Track mixer
    if d == "track" and field in ("volume", "pan", "mute", "solo"):
        if intent.track_index is None:
            raise HTTPException(400, "track_index_required")
        # Value handling
        v = float(intent.value if intent.value is not None else 0.0)
        if field == "volume":
            if (intent.unit or "").lower() in ("db", "dB".lower()):
                v = db_to_live_float(v)
            elif (intent.unit or "").lower() in ("percent", "%"):
                v = v / 100.0
            v = _clamp(v, 0.0, 1.0) if intent.clamp else v
        elif field == "pan":
            # Accept -1..+1 (normalized pan). If percent provided, map -100..+100 -> -1..+1
            if (intent.unit or "").lower() in ("percent", "%"):
                v = _clamp(v, -100.0, 100.0) / 100.0
            else:
                v = _clamp(v, -1.0, 1.0) if intent.clamp else v
        elif field in ("mute", "solo"):
            # Treat >0.5 as on
            v = 1.0 if v >= 0.5 else 0.0
        if intent.dry_run:
            return {"ok": True, "preview": {"op": "set_mixer", "track_index": intent.track_index, "field": field, "value": v}}
        resp = request_op("set_mixer", timeout=1.0, track_index=int(intent.track_index), field=str(field), value=float(v))
        if not resp:
            raise HTTPException(504, "no_reply")
        return resp

    # Track sends
    if d == "track" and field == "send":
        if intent.track_index is None or intent.send_index is None:
            raise HTTPException(400, "track_index_and_send_index_required")
        v = float(intent.value if intent.value is not None else 0.0)
        if (intent.unit or "").lower() in ("percent", "%"):
            v = v / 100.0
        v = _clamp(v, 0.0, 1.0) if intent.clamp else v
        if intent.dry_run:
            return {"ok": True, "preview": {"op": "set_send", "track_index": intent.track_index, "send_index": intent.send_index, "value": v}}
        resp = request_op("set_send", timeout=1.0, track_index=int(intent.track_index), send_index=int(intent.send_index), value=float(v))
        if not resp:
            raise HTTPException(504, "no_reply")
        return resp

    # Return mixer
    if d == "return" and field in ("volume", "pan", "mute", "solo"):
        if intent.return_index is None:
            raise HTTPException(400, "return_index_required")
        v = float(intent.value if intent.value is not None else 0.0)
        if field == "volume":
            if (intent.unit or "").lower() in ("percent", "%"):
                v = v / 100.0
            v = _clamp(v, 0.0, 1.0) if intent.clamp else v
        elif field == "pan":
            if (intent.unit or "").lower() in ("percent", "%"):
                v = _clamp(v, -100.0, 100.0) / 100.0
            else:
                v = _clamp(v, -1.0, 1.0) if intent.clamp else v
        elif field in ("mute", "solo"):
            v = 1.0 if v >= 0.5 else 0.0
        if intent.dry_run:
            return {"ok": True, "preview": {"op": "set_return_mixer", "return_index": intent.return_index, "field": field, "value": v}}
        resp = request_op("set_return_mixer", timeout=1.0, return_index=int(intent.return_index), field=str(field), value=float(v))
        if not resp:
            raise HTTPException(504, "no_reply")
        return resp

    # Return sends
    if d == "return" and field == "send":
        if intent.return_index is None or intent.send_index is None:
            raise HTTPException(400, "return_index_and_send_index_required")
        v = float(intent.value if intent.value is not None else 0.0)
        if (intent.unit or "").lower() in ("percent", "%"):
            v = v / 100.0
        v = _clamp(v, 0.0, 1.0) if intent.clamp else v
        if intent.dry_run:
            return {"ok": True, "preview": {"op": "set_return_send", "return_index": intent.return_index, "send_index": intent.send_index, "value": v}}
        resp = request_op("set_return_send", timeout=1.0, return_index=int(intent.return_index), send_index=int(intent.send_index), value=float(v))
        if not resp:
            raise HTTPException(504, "no_reply")
        return resp

    # Master mixer (subset)
    if d == "master" and field in ("volume", "pan"):
        v = float(intent.value if intent.value is not None else 0.0)
        if field == "volume" and (intent.unit or "").lower() in ("db", "dB".lower()):
            v = db_to_live_float(v)
        elif (intent.unit or "").lower() in ("percent", "%"):
            v = v / 100.0 if field == "volume" else _clamp(v, -100.0, 100.0) / 100.0
        if field == "volume":
            v = _clamp(v, 0.0, 1.0) if intent.clamp else v
        else:
            v = _clamp(v, -1.0, 1.0) if intent.clamp else v
        if intent.dry_run:
            return {"ok": True, "preview": {"op": "set_master_mixer", "field": field, "value": v}}
        resp = request_op("set_master_mixer", timeout=1.0, field=str(field), value=float(v))
        if not resp:
            raise HTTPException(504, "no_reply")
        return resp

    # Device parameter (return device)
    if d == "device" and intent.return_index is not None and intent.device_index is not None:
        ri = int(intent.return_index); di = int(intent.device_index)
        # Read params to get min/max, resolve selection
        pr = request_op("get_return_device_params", timeout=1.2, return_index=ri, device_index=di)
        params = ((pr or {}).get("data") or {}).get("params") or []
        if not params:
            raise HTTPException(404, "params_not_found")
        sel = _resolve_param(params, intent.param_index, intent.param_ref)
        vmin = float(sel.get("min", 0.0)); vmax = float(sel.get("max", 1.0))
        x = float(intent.value if intent.value is not None else vmin)
        # Basic unit handling for device: percent means within [vmin,vmax]
        if (intent.unit or "").lower() in ("percent", "%"):
            x = vmin + (vmax - vmin) * _clamp(x, 0.0, 100.0) / 100.0
        # Optional dependency enable
        master_toggle = _auto_enable_master_if_needed(params, str(sel.get("name", "")))
        preview: Dict[str, Any] = {"op": "set_return_device_param", "return_index": ri, "device_index": di, "param_index": int(sel.get("index", 0)), "value": float(_clamp(x, vmin, vmax) if intent.clamp else x)}
        if master_toggle is not None:
            preview["pre"] = {
                "op": "set_return_device_param",
                "return_index": ri,
                "device_index": di,
                "param_index": int(master_toggle.get("index", 0)),
                "value": float(master_toggle.get("max", 1.0)),
                "note": "auto_enable_master"
            }
        if intent.dry_run:
            return {"ok": True, "preview": preview}
        # Apply pre toggle if any
        if preview.get("pre"):
            pre = preview["pre"]
            request_op("set_return_device_param", timeout=1.0, **{k: pre[k] for k in ("return_index","device_index","param_index","value")})
        resp = request_op("set_return_device_param", timeout=1.0, return_index=ri, device_index=di, param_index=int(sel.get("index", 0)), value=float(preview["value"]))
        if not resp:
            raise HTTPException(504, "no_reply")
        return resp

    # Device parameter (track device)
    if d == "device" and intent.track_index is not None and intent.device_index is not None:
        ti = int(intent.track_index); di = int(intent.device_index)
        pr = request_op("get_track_device_params", timeout=1.2, track_index=ti, device_index=di)
        params = ((pr or {}).get("data") or {}).get("params") or []
        if not params:
            raise HTTPException(404, "params_not_found")
        sel = _resolve_param(params, intent.param_index, intent.param_ref)
        vmin = float(sel.get("min", 0.0)); vmax = float(sel.get("max", 1.0))
        x = float(intent.value if intent.value is not None else vmin)
        if (intent.unit or "").lower() in ("percent", "%"):
            x = vmin + (vmax - vmin) * _clamp(x, 0.0, 100.0) / 100.0
        preview = {"op": "set_device_param", "track_index": ti, "device_index": di, "param_index": int(sel.get("index", 0)), "value": float(_clamp(x, vmin, vmax) if intent.clamp else x)}
        if intent.dry_run:
            return {"ok": True, "preview": preview}
        resp = request_op("set_device_param", timeout=1.0, track_index=ti, device_index=di, param_index=int(sel.get("index", 0)), value=float(preview["value"]))
        if not resp:
            raise HTTPException(504, "no_reply")
        return resp

    raise HTTPException(400, "unsupported_intent")

