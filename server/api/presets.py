from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from server.core.deps import get_store
from server.services.ableton_client import request_op, data_or_raw
from server.services.mapping_utils import make_device_signature, detect_device_type
from server.services.preset_enricher import generate_preset_metadata_llm


router = APIRouter()


class CapturePresetBody(BaseModel):
    return_index: int
    device_index: int
    preset_name: str
    category: str = "stock"  # stock | user
    description: Optional[str] = None


@router.post("/return/device/capture_preset")
def capture_preset(body: CapturePresetBody) -> Dict[str, Any]:
    store = get_store()
    ret_idx = int(body.return_index)
    dev_idx = int(body.device_index)
    devs = request_op("get_return_devices", timeout=1.0, return_index=ret_idx)
    data = (devs or {}).get("data") or devs or {}
    devices = data.get("devices", [])
    if dev_idx >= len(devices):
        raise HTTPException(status_code=404, detail=f"Device index {dev_idx} out of range")
    device = devices[dev_idx]
    device_name = device.get("name", "Unknown")
    params_resp = request_op("get_return_device_params", timeout=1.0, return_index=ret_idx, device_index=dev_idx)
    pdata = (params_resp or {}).get("data") or params_resp or {}
    params = pdata.get("params", [])
    signature = make_device_signature(device_name, params)
    # Ensure structure exists (local or remote)
    mapping = store.get_device_map_local(signature) or (store.get_device_map(signature) if store.enabled else None)
    if not mapping:
        raise HTTPException(status_code=400, detail=f"Device structure not learned. Please learn device first (signature: {signature})")
    parameter_values = {}
    parameter_display_values = {}
    for p in params:
        nm = p.get("name"); val = p.get("value"); disp = p.get("display_value")
        if nm and val is not None:
            parameter_values[nm] = float(val)
        if nm and disp is not None:
            parameter_display_values[nm] = str(disp)
    device_type = detect_device_type(params, body.preset_name)
    preset_id = f"{device_type}_{body.preset_name.lower().replace(' ', '_')}"
    preset_data = {
        "name": body.preset_name,
        "device_name": device_name,
        "manufacturer": "Ableton",
        "daw": "Ableton Live",
        "structure_signature": signature,
        "category": device_type,
        "preset_type": body.category,
        "parameter_values": parameter_values,
        "parameter_display_values": parameter_display_values,
    }
    if body.description:
        preset_data["description"] = {"what": body.description}
    saved = store.save_preset(preset_id, preset_data, local_only=(body.category == "user"))
    return {"ok": saved, "preset_id": preset_id, "device_name": device_name, "device_type": device_type, "signature": signature, "param_count": len(parameter_values)}


class ApplyPresetBody(BaseModel):
    return_index: int
    device_index: int
    preset_id: str


@router.post("/return/device/apply_preset")
def apply_preset(body: ApplyPresetBody) -> Dict[str, Any]:
    store = get_store()
    ret_idx = int(body.return_index)
    dev_idx = int(body.device_index)
    preset_id = str(body.preset_id)
    preset = store.get_preset(preset_id)
    if not preset:
        raise HTTPException(status_code=404, detail=f"Preset not found: {preset_id}")
    devs = request_op("get_return_devices", timeout=1.0, return_index=ret_idx)
    data = (devs or {}).get("data") or devs or {}
    devices = data.get("devices", [])
    if dev_idx >= len(devices):
        raise HTTPException(status_code=404, detail=f"Device index {dev_idx} out of range")
    device = devices[dev_idx]
    device_name = device.get("name", "Unknown")
    params_resp = request_op("get_return_device_params", timeout=1.0, return_index=ret_idx, device_index=dev_idx)
    pdata = (params_resp or {}).get("data") or params_resp or {}
    params = pdata.get("params", [])
    current_signature = make_device_signature(device_name, params)
    preset_signature = preset.get("structure_signature")
    if current_signature != preset_signature:
        raise HTTPException(status_code=400, detail=f"Device structure mismatch. Current: {current_signature}, Preset: {preset_signature}")
    parameter_values = preset.get("parameter_values", {})
    applied = 0
    errors = []
    import time
    for param_name, target_value in parameter_values.items():
        try:
            param = next((p for p in params if p.get("name") == param_name), None)
            if not param:
                errors.append(f"Parameter not found: {param_name}")
                continue
            param_index = param.get("index")
            result = request_op(
                "set_return_device_param",
                timeout=0.5,
                return_index=ret_idx,
                device_index=dev_idx,
                param_index=param_index,
                value=float(target_value),
            )
            if result and result.get("ok"):
                applied += 1
            else:
                errors.append(f"Failed to set {param_name}")
            time.sleep(0.005)
        except Exception as e:
            errors.append(f"Error setting {param_name}: {str(e)}")
    return {"ok": applied > 0, "preset_name": preset.get("name"), "device_name": device_name, "applied": applied, "total": len(parameter_values), "errors": errors or None}


@router.get("/presets")
def list_presets(device_type: Optional[str] = None, structure_signature: Optional[str] = None, preset_type: Optional[str] = None) -> Dict[str, Any]:
    store = get_store()
    presets = store.list_presets(device_type, structure_signature, preset_type)
    return {"presets": presets, "count": len(presets)}


@router.get("/presets/{preset_id}")
def get_preset_detail(preset_id: str) -> Dict[str, Any]:
    store = get_store()
    preset = store.get_preset(preset_id)
    if not preset:
        raise HTTPException(status_code=404, detail=f"Preset not found: {preset_id}")
    return preset


@router.delete("/presets/{preset_id}")
def delete_preset_endpoint(preset_id: str) -> Dict[str, Any]:
    store = get_store()
    preset = store.get_preset(preset_id)
    if preset and preset.get("preset_type") == "stock":
        raise HTTPException(status_code=403, detail="Cannot delete stock presets")
    deleted = store.delete_preset(preset_id)
    return {"ok": deleted, "preset_id": preset_id}


class RefreshPresetBody(BaseModel):
    preset_id: str
    update_values_from_live: Optional[bool] = False
    return_index: Optional[int] = None
    device_index: Optional[int] = None
    fields_allowlist: Optional[list[str]] = None


@router.post("/presets/refresh_metadata")
async def refresh_preset_metadata(body: RefreshPresetBody) -> Dict[str, Any]:
    store = get_store()
    preset_id = body.preset_id.strip()
    preset = store.get_preset(preset_id)
    if not preset:
        raise HTTPException(status_code=404, detail=f"Preset not found: {preset_id}")
    device_type = preset.get("category") or preset.get("device_type") or "unknown"
    device_name = preset.get("name") or preset.get("device_name") or preset_id
    parameter_values = dict(preset.get("parameter_values") or {})
    if body.update_values_from_live and body.return_index is not None and body.device_index is not None:
        try:
            rd = request_op("get_return_device_params", timeout=1.2, return_index=int(body.return_index), device_index=int(body.device_index))
            rparams = ((rd or {}).get("data") or {}).get("params") or []
            live_vals = {}
            live_disp = {}
            for p in rparams:
                nm = p.get("name"); val = p.get("value"); disp = p.get("display_value")
                if nm is not None and val is not None:
                    live_vals[str(nm)] = float(val)
                if nm is not None and disp is not None:
                    live_disp[str(nm)] = str(disp)
            if live_vals:
                parameter_values = live_vals
            if live_disp:
                preset["parameter_display_values"] = live_disp
        except Exception:
            pass
    metadata = await generate_preset_metadata_llm(device_name=device_name, device_type=device_type, parameter_values=parameter_values)
    allowed_keys = {"description", "audio_engineering", "natural_language_controls", "warnings", "genre_tags", "subcategory"}
    if body.fields_allowlist:
        allowed_keys = allowed_keys.intersection({k for k in body.fields_allowlist})
    updates: Dict[str, Any] = {}
    if isinstance(metadata, dict):
        for k in allowed_keys:
            if k in metadata:
                updates[k] = metadata[k]
    preset.update(updates)
    preset["parameter_values"] = parameter_values
    saved = store.save_preset(preset_id, preset, local_only=False)
    return {"ok": bool(saved), "preset_id": preset_id, "updated_fields": list(updates.keys()), "values_refreshed": bool(parameter_values)}

