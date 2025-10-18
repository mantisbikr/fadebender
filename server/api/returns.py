from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from server.core.events import broker
from server.services.ableton_client import request_op, data_or_raw
from server.core.deps import get_store
from server.services.mapping_utils import make_device_signature
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
    print(f"DEBUG capabilities: pr type={type(pr)}, pdata type={type(pdata)}, params count={len(params)}")
    # Resolve device name
    dv = request_op("get_return_devices", timeout=0.8, return_index=ri) or {}
    dlist = (data_or_raw(dv) or {}).get("devices") or []
    dname = next((str(d.get("name", "")) for d in dlist if int(d.get("index", -1)) == di), f"Device {di}")
    # Build signature and fetch mapping
    sig = make_device_signature(dname, params)
    store = get_store()
    mapping = store.get_device_map(sig) if store.enabled else None
    print(f"DEBUG: Device signature={sig}, store.enabled={store.enabled}, mapping exists={mapping is not None}")
    if mapping:
        print(f"DEBUG: Mapping keys: {list(mapping.keys())}")
        print(f"DEBUG: Mapping content: {mapping}")
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
        print(f"DEBUG: Using Firestore mapping, mapping has {len(mparams)} params_meta, {len(sections)} sections")

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
        print(f"DEBUG: Firestore resulted in {len(groups)} groups, {len(ungrouped)} ungrouped")
    else:
        # Fallback: use live param list
        print(f"DEBUG: No Firestore mapping, using fallback with {len(params)} params")
        for p in params:
            ungrouped.append({"index": int(p.get("index", 0)), "name": p.get("name")})
        print(f"DEBUG: Fallback resulted in {len(ungrouped)} ungrouped params")
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
