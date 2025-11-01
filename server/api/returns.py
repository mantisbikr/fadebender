from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from server.core.events import broker, schedule_emit
from server.services.ableton_client import request_op, data_or_raw
from server.core.deps import get_store
from server.services.mapping_utils import make_device_signature
import re as _re
from server.core.deps import get_store
from server.services.history import DEVICE_BYPASS_CACHE, UNDO_STACK, REDO_STACK


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
    ri = int(index)
    resp = request_op("get_return_routing", timeout=1.0, return_index=ri)
    if not resp:
        return {"ok": False, "error": "no response"}
    data = data_or_raw(resp)
    # Probe sends capability: if sends list exists and has length>0, declare capable
    try:
        s = request_op("get_return_sends", timeout=1.0, return_index=ri) or {}
        sdata = (s.get("data") or s) if isinstance(s, dict) else {}
        sends = (sdata or {}).get("sends") or []
        data["sends_capable"] = bool(sends)
    except Exception:
        data["sends_capable"] = False
    return {"ok": True, "data": data}


class BypassBody(BaseModel):
    return_index: int
    device_index: int
    on: bool  # True = turn on, False = bypass/off


def _find_device_param(params: list[dict], names: list[str]) -> Optional[dict]:
    for nm in names:
        p = next((x for x in params if str(x.get("name", "")).lower() == nm.lower()), None)
        if p:
            return p
    return None


@router.post("/return/device/bypass")
def bypass_return_device(body: BypassBody) -> Dict[str, Any]:
    ri = int(body.return_index)
    di = int(body.device_index)
    resp = request_op("get_return_device_params", timeout=1.0, return_index=ri, device_index=di)
    params = ((resp or {}).get("data") or resp or {}).get("params") or []
    if not params:
        raise HTTPException(404, "device_params_not_found")

    dev_on = _find_device_param(params, ["Device On"])
    if dev_on is not None:
        idx = int(dev_on.get("index", -1))
        if idx < 0:
            raise HTTPException(500, "invalid_param_index")
        prev = float(dev_on.get("value", 1.0))
        target = 1.0 if body.on else 0.0
        ok = request_op(
            "set_return_device_param",
            timeout=0.8,
            return_index=ri,
            device_index=di,
            param_index=idx,
            value=float(target),
        )
        if ok and ok.get("ok", True):
            UNDO_STACK.append(
                {
                    "type": "device_param",
                    "return_index": ri,
                    "device_index": di,
                    "param_index": idx,
                    "prev": prev,
                    "new": target,
                }
            )
            REDO_STACK.clear()
            try:
                schedule_emit({"event": "device_bypass_changed", "return_index": ri, "device_index": di, "on": body.on})
            except Exception:
                pass
            return {"ok": True, "method": "device_on", "prev": prev, "new": target}
        raise HTTPException(502, "set_param_failed")

    drywet = _find_device_param(params, ["Dry/Wet", "Mix"])
    if drywet is None:
        raise HTTPException(400, "no_bypass_strategy_available")
    idx = int(drywet.get("index", -1))
    if idx < 0:
        raise HTTPException(500, "invalid_param_index")
    prev = float(drywet.get("value", 0.0))
    key = (ri, di)
    if not body.on:
        if prev > 0.0:
            DEVICE_BYPASS_CACHE[key] = prev
        target = 0.0
    else:
        restore = DEVICE_BYPASS_CACHE.get(key, None)
        target = float(restore if restore is not None else max(prev, 0.25))
    ok = request_op(
        "set_return_device_param",
        timeout=0.8,
        return_index=ri,
        device_index=di,
        param_index=idx,
        value=float(target),
    )
    if ok and ok.get("ok", True):
        UNDO_STACK.append(
            {
                "type": "device_param",
                "return_index": ri,
                "device_index": di,
                "param_index": idx,
                "prev": prev,
                "new": target,
            }
        )
        REDO_STACK.clear()
        if body.on and key in DEVICE_BYPASS_CACHE:
            try:
                del DEVICE_BYPASS_CACHE[key]
            except Exception:
                pass
        try:
            schedule_emit({"event": "device_bypass_changed", "return_index": ri, "device_index": di, "on": body.on})
        except Exception:
            pass
        return {"ok": True, "method": "drywet", "prev": prev, "new": target}
    raise HTTPException(502, "set_param_failed")


class SaveUserPresetBody(BaseModel):
    return_index: int
    device_index: int
    preset_name: str
    user_id: Optional[str] = None


@router.post("/return/device/save_as_user_preset")
def save_as_user_preset(body: SaveUserPresetBody) -> Dict[str, Any]:
    ri = int(body.return_index)
    di = int(body.device_index)
    devs = request_op("get_return_devices", timeout=1.0, return_index=ri) or {}
    devices = ((devs.get("data") or devs) if isinstance(devs, dict) else devs).get("devices", [])
    if di >= len(devices):
        raise HTTPException(404, "device_index_out_of_range")
    device = devices[di]
    device_name = device.get("name", "Unknown")

    params_resp = request_op("get_return_device_params", timeout=1.0, return_index=ri, device_index=di) or {}
    params = ((params_resp.get("data") or params_resp) if isinstance(params_resp, dict) else params_resp).get("params", [])
    if not params:
        raise HTTPException(500, "device_params_fetch_failed")

    parameter_values: Dict[str, float] = {}
    for p in params:
        nm = p.get("name")
        val = p.get("value")
        if nm is not None and val is not None:
            parameter_values[str(nm)] = float(val)

    signature = make_device_signature(device_name, params)
    device_type = detect_device_type(params, device_name)

    preset_id = f"{device_type}_user_{body.preset_name.lower().replace(' ', '_')}"
    preset_data = {
        "name": body.preset_name,
        "device_name": device_name,
        "manufacturer": "Ableton",
        "daw": "Ableton Live",
        "structure_signature": signature,
        "category": device_type,
        "preset_type": "user",
        "user_id": body.user_id,
        "parameter_values": parameter_values,
    }

    store = get_store()
    ok = store.save_preset(preset_id, preset_data, local_only=False)
    try:
        schedule_emit({"event": "preset_saved", "preset_id": preset_id, "name": body.preset_name})
    except Exception:
        pass
    return {"ok": bool(ok), "preset_id": preset_id, "device_type": device_type, "signature": signature}


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


@router.get("/return/mixer/capabilities")
def get_return_mixer_capabilities(index: int) -> Dict[str, Any]:
    ri = int(index)
    rs = request_op("get_return_tracks", timeout=1.0)
    if not rs:
        return {"ok": False, "error": "no response"}
    data = data_or_raw(rs) or {}
    rets = data.get("returns") or []
    ret = next((r for r in rets if int(r.get("index", -1)) == ri), None)
    mixer = (ret or {}).get("mixer") or {}

    store = get_store()
    mapping = store.get_mixer_channel_mapping("return") if store.enabled else None
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
    values = {}

    def _display_for(name: str, raw):
        try:
            if name == "volume":
                from server.volume_utils import live_float_to_db
                return float(f"{live_float_to_db(float(raw)):.2f}")
            if name == "pan":
                return float(f"{(float(raw) * 50.0):.2f}")
            if name in ("mute", "solo"):
                return "On" if bool(raw) else "Off"
            return raw
        except Exception:
            return raw

    raw_map = {
        "volume": mixer.get("volume"),
        "pan": mixer.get("pan"),
        "mute": mixer.get("mute"),
        "solo": mixer.get("solo"),
    }

    for mp in params_meta:
        pname = mp.get("name")
        control_type = mp.get("control_type")

        # Skip template parameters that aren't user-controllable
        if pname == "send":  # Template for Send A/B/C conversions, not directly controllable
            continue

        # Special case: expand "sends" into individual Send A/B/C parameters
        if control_type == "send_array" and pname == "sends":
            # Fetch actual send values
            try:
                from server.volume_utils import live_float_to_db_send
                sends_resp = request_op("get_return_sends", timeout=2.0, return_index=ri)
                sends_data = (sends_resp or {}).get("data") or sends_resp or {}
                sends = sends_data.get("sends") or []

                # If no sends available, skip expansion and fall through to regular parameter
                if not sends:
                    raise Exception("no_sends_available")

                # Use same group resolution as regular parameters
                gname = param_to_section.get(pname) or str(mp.get("group") or "").strip() or "Other"

                # Create individual Send A/B/C parameters
                for send in sends:
                    send_idx = int(send.get("index", 0))
                    send_letter = chr(ord('A') + send_idx)
                    send_name = f"Send {send_letter}"
                    send_value = send.get("value")
                    send_display = send.get("display_value")

                    if send_display is None and send_value is not None:
                        try:
                            send_display = f"{live_float_to_db_send(float(send_value)):.1f}"
                        except Exception:
                            send_display = None

                    send_item = {
                        "index": send_idx,
                        "name": send_name,
                        "unit": mp.get("unit"),  # Use unit from mapping (dB)
                        "labels": None,
                        "label_map": None,
                        "min_display": mp.get("min_display"),  # Use from mapping
                        "max_display": mp.get("max_display"),  # Use from mapping
                        "min": mp.get("min"),
                        "max": mp.get("max"),
                        "control_type": "continuous",  # Individual sends are continuous
                        "role": None,
                        "tooltip": f"Send level to {send_letter}",
                        "send_index": send_idx,
                        "send_letter": send_letter,
                    }
                    by_group.setdefault(gname, []).append(send_item)
                    values[send_name] = {"value": send_value, "display_value": send_display}

                # Successfully expanded sends, skip adding the "sends" array parameter itself
                continue
            except Exception:
                # Fallback: keep single "sends" parameter if send expansion fails
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
                    "control_type": control_type,
                    "role": mp.get("role"),
                    "tooltip": (mp.get("audio_knowledge") or {}).get("audio_function"),
                }
                gname = param_to_section.get(pname) or str(mp.get("group") or "").strip() or None
                if gname:
                    by_group.setdefault(gname, []).append(item)
                else:
                    by_group.setdefault("Other", []).append(item)
                values[pname] = {"value": None, "display_value": None}
        else:
            # Regular parameter
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
                "control_type": control_type,
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
        "entity_type": "return",
        "return_index": ri,
        "device_name": f"Return {chr(ord('A')+ri)} Mixer",
        "groups": groups,
        "ungrouped": [],
        "values": values,
    }}


@router.get("/return/device/params")
def get_return_device_params(index: int, device: int) -> Dict[str, Any]:
    resp = request_op(
        "get_return_device_params", timeout=1.0, return_index=int(index), device_index=int(device)
    )
    if not resp:
        return {"ok": False, "error": "no response"}
    return {"ok": True, "data": data_or_raw(resp)}


@router.get("/return/device/capabilities")
def get_return_device_capabilities(index: int, device: int) -> Dict[str, Any]:
    """Return parameter capabilities for a return device: groups + params + current values.

    Response shape:
    { ok, data: {
        return_index, device_index, device_name, device_type?,
        groups: [{ name, params: [{ index, name, unit?, labels?, role? }] }],
        ungrouped: [{ index, name, unit?, labels?, role? }],
        values: { name -> { value, display_value } }
    } }
    """
    ri = int(index); di = int(device)
    # Read current params
    pr = request_op("get_return_device_params", timeout=1.0, return_index=ri, device_index=di)
    if not pr:
        raise HTTPException(504, "no response")
    pdata = data_or_raw(pr) or {}
    params = list((pdata.get("params") or []))
    # Resolve device name
    dv = request_op("get_return_devices", timeout=0.8, return_index=ri) or {}
    dlist = (data_or_raw(dv) or {}).get("devices") or []
    dname = next((str(d.get("name", "")) for d in dlist if int(d.get("index", -1)) == di), f"Device {di}")
    # Build signature and fetch mapping
    sig = make_device_signature(dname, params)
    store = get_store()
    mapping = store.get_device_map(sig) if store.enabled else None

    # Assemble values map for convenience
    values = {}
    for p in params:
        try:
            values[str(p.get("name", ""))] = {"value": float(p.get("value", 0.0)), "display_value": p.get("display_value")}
        except Exception:
            values[str(p.get("name", ""))] = {"value": p.get("value"), "display_value": p.get("display_value")}
    # Build groups and ungrouped based on mapping params meta
    groups = []
    ungrouped = []
    # Helper: live param lookup by index for min/max (normalized)
    live_by_index = {int(p.get("index", 0)): p for p in params}
    if mapping:
        # Prefer Firestore params docs (stored in 'params_meta', not 'params')
        mparams = mapping.get("params_meta") or mapping.get("params") or []
        sections = mapping.get("sections") or {}
        grouping = (mapping.get("grouping") or {})
        dependents = (grouping.get("dependents") or {})

        # Build section->params mapping if sections exist
        section_params = {}
        if sections:
            for section_name, section_data in sections.items():
                param_names = section_data.get("parameters", [])
                section_params[section_name] = param_names

        # Build group buckets with metadata
        by_group = {}
        param_to_section = {}
        # Build reverse lookup: param name -> section name
        for section_name, param_list in section_params.items():
            for pname in param_list:
                param_to_section[pname] = section_name

        # Build param name -> metadata lookup
        param_meta_map = {mp.get("name"): mp for mp in mparams}

        for mp in mparams:
            pname = mp.get("name")
            # Check if param belongs to a section
            g = param_to_section.get(pname) or str(mp.get("group") or "").strip() or None

            # Extract audio knowledge for tooltip
            audio_knowledge = mp.get("audio_knowledge", {})
            sonic_effect = audio_knowledge.get("sonic_effect", {})
            tooltip = None
            if sonic_effect:
                increasing = sonic_effect.get("increasing", "")
                decreasing = sonic_effect.get("decreasing", "")
                audio_function = audio_knowledge.get("audio_function", "")
                if increasing and decreasing:
                    tooltip = f"{audio_function}\n↑ {increasing}\n↓ {decreasing}"
                elif audio_function:
                    tooltip = audio_function

            idx = int(mp.get("index", 0))
            lp = live_by_index.get(idx, {})
            label_map = mp.get("label_map") or {}
            # Do not infer control_type for devices; require Firestore to provide it
            control_type = mp.get("control_type")
            # dependency (master) info
            master_name = None
            try:
                for dep_k, dep_master in (dependents.items() if isinstance(dependents, dict) else []):
                    if str(dep_k).strip().lower() == str(pname or '').strip().lower():
                        master_name = str(dep_master)
                        break
            except Exception:
                master_name = None

            item = {
                "index": idx,
                "name": pname,
                "unit": mp.get("unit"),
                "labels": mp.get("labels") or (list(label_map.keys()) if isinstance(label_map, dict) else None),
                "label_map": label_map if isinstance(label_map, dict) else None,
                "role": mp.get("role"),
                "tooltip": tooltip,
                "min_display": mp.get("min_display"),
                "max_display": mp.get("max_display"),
                "min": lp.get("min"),
                "max": lp.get("max"),
                "control_type": control_type,
                "has_master": bool(master_name),
                "master_name": master_name,
            }
            if g:
                by_group.setdefault(g, []).append(item)
            else:
                ungrouped.append(item)

        # Convert to list with section metadata
        for gname, plist in by_group.items():
            section_meta = sections.get(gname, {})
            groups.append({
                "name": gname,
                "params": plist,
                "description": section_meta.get("description"),
                "sonic_focus": section_meta.get("sonic_focus"),
            })
    else:
        # Fallback: use live param list
        for p in params:
            ungrouped.append({"index": int(p.get("index", 0)), "name": p.get("name")})
    return {"ok": True, "data": {
        "return_index": ri,
        "device_index": di,
        "device_name": dname,
        "structure_signature": sig,
        "groups": groups,
        "ungrouped": ungrouped,
        "values": values,
    }}


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
