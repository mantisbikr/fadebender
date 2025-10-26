from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from server.core.deps import get_store
from server.core.events import broker
from server.services.ableton_client import request_op, data_or_raw
from server.services.mapping_utils import make_device_signature, detect_device_type
from server.services.preset_metadata import generate_preset_metadata_llm
from server.cloud.enrich_queue import enqueue_preset_enrich


router = APIRouter()

# Global state for async backfill job tracking
BACKFILL_JOBS: dict[str, dict] = {}


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
    metadata = await generate_preset_metadata_llm(device_name=device_name, device_type=device_type, parameter_values=parameter_values, store=store)
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


class BackfillBody(BaseModel):
    device_type: Optional[str] = None
    preset_type: Optional[str] = None
    structure_signature: Optional[str] = None
    dry_run: Optional[bool] = False
    limit: Optional[int] = None
    fields_allowlist: Optional[list[str]] = None
    concurrency: Optional[int] = 3

class BackfillIdsBody(BaseModel):
    preset_ids: list[str]
    fields_allowlist: Optional[list[str]] = None
    dry_run: Optional[bool] = False


def _needs_metadata(p: dict) -> bool:
    if not isinstance(p, dict):
        return True
    # If any key is missing/empty, needs backfill
    for k in ("description", "audio_engineering", "natural_language_controls"):
        if k not in p or not p.get(k):
            return True
    # Quality threshold: require sufficiently rich content
    try:
        why = str(((p.get("description") or {}).get("why")) or "")
        ucs = ((p.get("audio_engineering") or {}).get("use_cases")) or []
        if len(why) < 200 or not isinstance(ucs, list) or len(ucs) < 4:
            return True
    except Exception:
        return True
    return False


@router.post("/presets/backfill_metadata")
async def backfill_preset_metadata(body: BackfillBody) -> Dict[str, Any]:
    """Batch-enrich preset metadata in the background and stream SSE progress.

    Filters: device_type, preset_type, structure_signature. Use `dry_run` to preview.
    Concurrency is capped to avoid overwhelming the LLM API.
    """
    device_type = (body.device_type or "").strip() or None
    preset_type = (body.preset_type or "").strip() or None
    signature = (body.structure_signature or "").strip() or None
    dry_run = bool(body.dry_run)
    limit = int(body.limit) if body.limit else None
    fields_allow = list(body.fields_allowlist or [])
    concurrency = max(1, int(body.concurrency or 3))

    store = get_store()
    # Snapshot list of presets to process
    presets = store.list_presets(device_type=device_type, structure_signature=signature, preset_type=preset_type)
    if limit is not None:
        presets = presets[:limit]

    job_id = f"bf_{int(time.time())}_{len(presets)}"
    BACKFILL_JOBS[job_id] = {"state": "queued", "total": len(presets), "completed": 0, "updated": 0, "skipped": 0, "errors": 0}

    async def run():
        BACKFILL_JOBS[job_id].update({"state": "running"})
        try:
            sem = asyncio.Semaphore(concurrency)
            updated = 0
            skipped = 0
            errors = 0
            completed = 0

            async def process(item: dict):
                nonlocal updated, skipped, errors, completed
                pid = item.get("id")
                if not pid:
                    skipped += 1; completed += 1
                    await broker.publish({"event": "preset_backfill_item", "preset_id": None, "status": "skipped", "reason": "no_id"})
                    return
                async with sem:
                    try:
                        preset = store.get_preset(pid) or {}
                        if not _needs_metadata(preset):
                            skipped += 1; completed += 1
                            await broker.publish({"event": "preset_backfill_item", "preset_id": pid, "status": "skipped"})
                            return
                        if dry_run:
                            completed += 1
                            await broker.publish({"event": "preset_backfill_item", "preset_id": pid, "status": "dry_run"})
                            return

                        dname = preset.get("name") or preset.get("device_name") or pid
                        dtype = preset.get("category") or preset.get("device_type") or (device_type or "unknown")
                        pvals = dict(preset.get("parameter_values") or {})

                        metadata = await generate_preset_metadata_llm(
                            device_name=dname,
                            device_type=dtype,
                            parameter_values=pvals,
                            store=store,
                        )
                        allowed = {"description", "audio_engineering", "natural_language_controls", "warnings", "genre_tags", "subcategory"}
                        if fields_allow:
                            allowed = allowed.intersection(set(fields_allow))
                        updates: Dict[str, Any] = {}
                        if isinstance(metadata, dict):
                            for k in allowed:
                                if k in metadata:
                                    updates[k] = metadata[k]
                        # Merge + save
                        if updates:
                            preset.update(updates)
                            preset.setdefault("updated_at", int(time.time()))
                            preset.setdefault("metadata_status", "ok")
                            ok = store.save_preset(pid, preset, local_only=False)
                            status = "updated" if ok else "error"
                            if ok:
                                updated += 1
                            else:
                                errors += 1
                        else:
                            status = "no_changes"
                            skipped += 1
                        completed += 1
                        await broker.publish({"event": "preset_backfill_item", "preset_id": pid, "status": status, "updated_fields": list(updates.keys())})
                        # Enqueue cloud enrichment for richer RAG if configured
                        try:
                            enqueue_preset_enrich(pid, metadata_version=1)
                        except Exception:
                            pass
                    except Exception as e:
                        errors += 1; completed += 1
                        await broker.publish({"event": "preset_backfill_item", "preset_id": item.get("id"), "status": "error", "error": str(e)})
                    finally:
                        BACKFILL_JOBS[job_id].update({"completed": completed, "updated": updated, "skipped": skipped, "errors": errors})
                        await broker.publish({"event": "preset_backfill_progress", "job_id": job_id, "completed": completed, "total": len(presets), "updated": updated, "skipped": skipped, "errors": errors})

            await broker.publish({"event": "preset_backfill_start", "job_id": job_id, "total": len(presets)})
            # Launch with bounded concurrency
            tasks = [process(p) for p in presets]
            await asyncio.gather(*tasks)
            BACKFILL_JOBS[job_id].update({"state": "done"})
            await broker.publish({"event": "preset_backfill_done", "job_id": job_id, "summary": BACKFILL_JOBS[job_id]})
        except Exception as e:
            BACKFILL_JOBS[job_id].update({"state": "error", "error": str(e)})
            try:
                await broker.publish({"event": "preset_backfill_done", "job_id": job_id, "summary": BACKFILL_JOBS[job_id]})
            except Exception:
                pass

    asyncio.create_task(run())
    return {"ok": True, "job_id": job_id, "queued": BACKFILL_JOBS[job_id]["total"], "dry_run": dry_run}


@router.post("/presets/backfill_ids")
async def backfill_preset_metadata_by_ids(body: BackfillIdsBody) -> Dict[str, Any]:
    ids = [str(x).strip() for x in (body.preset_ids or []) if str(x).strip()]
    if not ids:
        raise HTTPException(400, "no_preset_ids")
    fields_allow = list(body.fields_allowlist or [])
    dry_run = bool(body.dry_run)
    job_id = f"bf_ids_{int(time.time())}_{len(ids)}"
    BACKFILL_JOBS[job_id] = {"state": "queued", "total": len(ids), "completed": 0, "updated": 0, "skipped": 0, "errors": 0}

    store = get_store()

    async def run():
        BACKFILL_JOBS[job_id].update({"state": "running"})
        try:
            updated = 0
            skipped = 0
            errors = 0
            completed = 0

            async def process(pid: str):
                nonlocal updated, skipped, errors, completed
                try:
                    preset = store.get_preset(pid) or {}
                    if not preset:
                        skipped += 1; completed += 1
                        await broker.publish({"event": "preset_backfill_item", "preset_id": pid, "status": "skipped", "reason": "not_found"})
                        return
                    dname = preset.get("name") or preset.get("device_name") or pid
                    dtype = preset.get("category") or preset.get("device_type") or "unknown"
                    pvals = dict(preset.get("parameter_values") or {})
                    if dry_run:
                        completed += 1
                        await broker.publish({"event": "preset_backfill_item", "preset_id": pid, "status": "dry_run"})
                        return
                    meta = await generate_preset_metadata_llm(
                        device_name=dname,
                        device_type=dtype,
                        parameter_values=pvals,
                        store=store,
                    )
                    allowed = {"description", "audio_engineering", "natural_language_controls", "warnings", "genre_tags", "subcategory"}
                    if fields_allow:
                        allowed = allowed.intersection(set(fields_allow))
                    updates: Dict[str, Any] = {}
                    if isinstance(meta, dict):
                        for k in allowed:
                            if k in meta:
                                updates[k] = meta[k]
                    if updates:
                        preset.update(updates)
                        preset.setdefault("updated_at", int(time.time()))
                        preset.setdefault("metadata_status", "ok")
                        ok = store.save_preset(pid, preset, local_only=False)
                        status = "updated" if ok else "error"
                        if ok:
                            updated += 1
                        else:
                            errors += 1
                    else:
                        status = "no_changes"; skipped += 1
                    completed += 1
                    await broker.publish({"event": "preset_backfill_item", "preset_id": pid, "status": status, "updated_fields": list(updates.keys())})
                except Exception as e:
                    errors += 1; completed += 1
                    await broker.publish({"event": "preset_backfill_item", "preset_id": pid, "status": "error", "error": str(e)})
                finally:
                    BACKFILL_JOBS[job_id].update({"completed": completed, "updated": updated, "skipped": skipped, "errors": errors})
                    await broker.publish({"event": "preset_backfill_progress", "job_id": job_id, "completed": completed, "total": len(ids), "updated": updated, "skipped": skipped, "errors": errors})

            await broker.publish({"event": "preset_backfill_start", "job_id": job_id, "total": len(ids)})
            for pid in ids:
                await process(pid)
            BACKFILL_JOBS[job_id].update({"state": "done"})
            await broker.publish({"event": "preset_backfill_done", "job_id": job_id, "summary": BACKFILL_JOBS[job_id]})
        except Exception as e:
            BACKFILL_JOBS[job_id].update({"state": "error", "error": str(e)})
            try:
                await broker.publish({"event": "preset_backfill_done", "job_id": job_id, "summary": BACKFILL_JOBS[job_id]})
            except Exception:
                pass

    asyncio.create_task(run())
    return {"ok": True, "job_id": job_id, "queued": BACKFILL_JOBS[job_id]["total"], "dry_run": dry_run}
