from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from server.core.events import broker
from server.services.ableton_client import request_op, data_or_raw
from server.services.mixer_readers import read_track_status, read_track_sends
from server.services.device_readers import read_track_devices, read_track_device_params
from server.core.deps import get_store
from server.services.mapping_utils import make_device_signature
import re as _re


router = APIRouter()


@router.get("/track/status")
def track_status(index: int) -> Dict[str, Any]:
    data = read_track_status(int(index))
    if not data:
        return {"ok": False, "error": "no response"}
    return {"ok": True, "data": data}


@router.get("/track/sends")
def track_sends(index: int) -> Dict[str, Any]:
    data = read_track_sends(int(index))
    if not data:
        return {"ok": False, "error": "no response"}
    return {"ok": True, "data": data}


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
    data = read_track_devices(int(index))
    if not data:
        return {"ok": False, "error": "no response"}

    # Enrich devices with device_type from Firestore
    devices = data.get("devices", [])
    store = get_store()
    if store and store.enabled:
        for device in devices:
            device_name = device.get("name")
            if device_name:
                try:
                    device_type = store.get_device_type_by_name(device_name)
                    if device_type:
                        device["device_type"] = device_type
                except Exception:
                    pass

    return {"ok": True, "data": data}


@router.get("/track/device/params")
def get_track_device_params(index: int, device: int) -> Dict[str, Any]:
    data = read_track_device_params(int(index), int(device))
    if not data:
        return {"ok": False, "error": "no response"}
    return {"ok": True, "data": data}


@router.get("/track/device/capabilities")
def get_track_device_capabilities(index: int, device: int) -> Dict[str, Any]:
    """Return parameter capabilities for a track device: groups + params + current values.

    Response shape:
    { ok, data: {
        track_index, device_index, device_name, device_type?,
        groups: [{ name, params: [{ index, name, unit?, labels?, role? }] }],
        ungrouped: [{ index, name, unit?, labels?, role? }],
        values: { name -> { value, display_value } }
    } }
    """
    ti = int(index); di = int(device)
    # Read current params
    pr = request_op("get_track_device_params", timeout=1.0, track_index=ti, device_index=di)
    if not pr:
        raise HTTPException(504, "no response")
    pdata = data_or_raw(pr) or {}
    params = list((pdata.get("params") or []))
    # Resolve device name
    dv = request_op("get_track_devices", timeout=0.8, track_index=ti) or {}
    dlist = (data_or_raw(dv) or {}).get("devices") or []
    dname = next((str(d.get("name", "")) for d in dlist if int(d.get("index", -1)) == di), f"Device {di}")
    # Build signature and fetch mapping
    sig = make_device_signature(dname, params)
    store = get_store()
    mapping = store.get_device_map(sig) if store.enabled else None

    # Assemble values map, preferring ValueRegistry over fresh Live query
    from server.core.deps import get_value_registry
    reg = get_value_registry()
    devices_map = reg.get_devices() if reg else {}
    cached_device_values = devices_map.get("track", {}).get(ti, {}).get(di, {})

    values = {}
    for p in params:
        pname = str(p.get("name", ""))
        # Prefer cached value from ValueRegistry (most recent from operations)
        if pname in cached_device_values:
            cached = cached_device_values[pname]
            values[pname] = {
                "value": cached.get("normalized"),
                "display_value": cached.get("display")
            }
        else:
            # Fall back to fresh Live query value
            try:
                values[pname] = {"value": float(p.get("value", 0.0)), "display_value": p.get("display_value")}
            except Exception:
                values[pname] = {"value": p.get("value"), "display_value": p.get("display_value")}
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
            label_map_raw = mp.get("label_map") or {}
            # Normalize labels and label_map for UI
            labels_ui = mp.get("labels")
            label_map_ui = None
            try:
                if isinstance(label_map_raw, dict) and label_map_raw:
                    def _is_num_key(k: object) -> bool:
                        try:
                            float(str(k))
                            return True
                        except Exception:
                            return False
                    if any(_is_num_key(k) for k in label_map_raw.keys()):
                        # number -> label mapping; use values for labels
                        labels_ui = labels_ui or [str(v) for v in label_map_raw.values()]
                        # preserve as string keys for client lookup
                        label_map_ui = {str(k): str(v) for k, v in label_map_raw.items()}
                    else:
                        # label -> value mapping; invert to number -> label for UI
                        inv: Dict[str, str] = {}
                        for lab, val in label_map_raw.items():
                            try:
                                inv[str(int(round(float(val))))] = str(lab)
                            except Exception:
                                # fallback: use raw string
                                try:
                                    inv[str(val)] = str(lab)
                                except Exception:
                                    pass
                        if inv:
                            label_map_ui = inv
                            labels_ui = labels_ui or [str(v) for v in inv.values()]
            except Exception:
                pass
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
                "labels": labels_ui,
                "label_map": label_map_ui,
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
        "track_index": ti,
        "device_index": di,
        "device_name": dname,
        "structure_signature": sig,
        "groups": groups,
        "ungrouped": ungrouped,
        "values": values,
    }}


@router.get("/track/mixer/capabilities")
def get_track_mixer_capabilities(index: int) -> Dict[str, Any]:
    ti = int(index)
    # Current status for values
    # Remote script expects 1-based track indexing
    st = request_op("get_track_status", timeout=1.0, track_index=ti+1)
    if not st:
        return {"ok": False, "error": "no response"}
    sdata = data_or_raw(st) or {}
    mixer = sdata.get("mixer") or {}

    store = get_store()
    mapping = store.get_mixer_channel_mapping("track") if store.enabled else None
    if not mapping:
        return {"ok": False, "error": "no_mixer_mapping"}

    params_meta = mapping.get("params_meta") or []
    sections = mapping.get("sections") or {}

    # Build section name -> param names
    section_params = {name: (sec.get("parameters") or []) for name, sec in sections.items()}
    # Reverse lookup param -> section
    param_to_section = {}
    for sname, plist in section_params.items():
        for pname in plist:
            param_to_section[pname] = sname

    # Build groups and values
    groups = []
    by_group = {}
    values = {}

    def _display_for(name: str, raw):
        try:
            if name == "volume":
                from server.volume_utils import live_float_to_db
                return float(f"{live_float_to_db(float(raw)):.2f}")
            if name == "cue":
                from server.volume_utils import live_float_to_db
                return float(f"{live_float_to_db(float(raw)):.2f}")
            if name == "pan":
                # [-1,1] -> [-50,50]
                return float(f"{(float(raw) * 50.0):.2f}")
            if name in ("mute", "solo"):
                return "On" if bool(raw) else "Off"
            return raw
        except Exception:
            return raw

    # Current values map (normalized raw comes from status)
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
                # Remote script expects 1-based track indexing
                track_index_1based = ti + 1
                sends_resp = request_op("get_track_sends", timeout=2.0, track_index=track_index_1based)
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

            # Attach current value + display
            rv = raw_map.get(pname)
            values[pname] = {"value": rv, "display_value": _display_for(pname, rv)}

    # Build groups list with descriptions
    for gname, plist in by_group.items():
        sec_meta = sections.get(gname, {})
        groups.append({
            "name": gname,
            "params": plist,
            "description": sec_meta.get("description"),
            "sonic_focus": sec_meta.get("sonic_focus"),
        })

    # Resolve human track name from overview for nicer titles
    try:
        ov = request_op("get_overview", timeout=0.8) or {}
        tracks = (data_or_raw(ov) or {}).get("tracks") or []
        tname = next((str(t.get("name", f"Track {ti+1}")) for t in tracks if int(t.get("index", -1)) == ti+1), f"Track {ti+1}")
    except Exception:
        tname = f"Track {ti+1}"

    return {"ok": True, "data": {
        "entity_type": "track",
        "track_index": ti,
        "device_name": f"{tname} Mixer",
        "groups": groups,
        "ungrouped": [],
        "values": values,
    }}


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
