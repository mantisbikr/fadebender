from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional
import os

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from server.core.deps import get_store
from server.services.ableton_client import request_op, data_or_raw
from server.services.mapping_utils import make_device_signature, detect_device_type
from server.services.device_mapping_service import ensure_device_mapping
from server.services.preset_service import save_base_preset
from server.services import device_mapping_io as dmio
import math
import re as _re
from server.services.mapping_utils import detect_device_type
from pydantic import BaseModel


router = APIRouter()

_should_capture = dmio.should_capture


@router.get("/return/device/map")
async def get_return_device_map(index: int, device: int) -> Dict[str, Any]:
    # Fetch device name and params to compute signature
    try:
        dname, live_params, signature, device_type = dmio.resolve_return_device_signature(int(index), int(device))
    except ValueError:
        return {"ok": False, "error": "device_not_found"}
    store = get_store()
    backend = store.backend
    exists = False

    # Ensure base mapping exists immediately (non-blocking safety)
    dmio.ensure_structure_and_capture(signature, device_type, int(index), int(device), dname, live_params)

    # New base mapping existence check
    mapping_exists = False
    try:
        new_map = store.get_device_mapping(signature)
        mapping_exists = bool(new_map)
    except Exception:
        mapping_exists = False

    # Save a minimal preset (values + display) in background (idempotent)
    # capture handled in dmio.ensure_structure_and_capture

    # Legacy learned mapping check (samples)
    try:
        m = store.get_device_map(signature) if store.enabled else store.get_device_map_local(signature)
        learned_params = (m.get("params") or []) if m else []
        if isinstance(learned_params, list):
            for p in learned_params:
                sm = p.get("samples") or []
                if isinstance(sm, list) and len(sm) >= 3:
                    exists = True
                    break
    except Exception:
        exists = False

    # Note: We intentionally do not auto-capture/enrich presets here to keep
    # learning minimal (structure-first). Higher-level enrichment can run later.

    return {
        "ok": True,
        "exists": bool(mapping_exists or exists),
        "mapping_exists": bool(mapping_exists),
        "learned_exists": bool(exists),
        "signature": signature,
        "backend": backend,
        "device_type": device_type,
        "device_name": dname,
    }


@router.get("/return/device/map_summary")
async def get_return_device_map_summary(index: int, device: int) -> Dict[str, Any]:
    try:
        dname, params, signature, _dtype = dmio.resolve_return_device_signature(int(index), int(device))
    except ValueError:
        return {"ok": False, "error": "device_not_found"}
    store = get_store()
    backend = store.backend
    exists = False
    mapping_exists = False
    learned_exists = False

    # Ensure base mapping (structure) exists so UI can turn green quickly
    try:
        ensure_device_mapping(signature, detect_device_type(params, dname), params)
    except Exception:
        pass

    # Prefer legacy learned mapping when present (samples data)
    legacy = dmio.get_legacy_map(signature)

    data = None
    if legacy:
        learned_params = (legacy.get("params") or [])
        plist = []
        for p in learned_params:
            try:
                nm = p.get("name")
                sm = p.get("samples") or []
                fit = p.get("fit")
                if isinstance(sm, list) and len(sm) >= 3:
                    learned_exists = True
                plist.append({
                    "name": nm,
                    "index": p.get("index"),
                    "sample_count": len(sm),
                    "quantized": bool(p.get("quantized", False)),
                    "control_type": p.get("control_type"),
                    "unit": p.get("unit"),
                    "min": p.get("min"),
                    "max": p.get("max"),
                    "fit": bool(fit),
                })
            except Exception:
                continue
        # Also check for base mapping
        try:
            mapping_exists = bool(dmio.get_mapping(signature))
        except Exception:
            mapping_exists = False
        data = {
            "device_name": legacy.get("device_name") or dname,
            "signature": signature,
            "params": plist,
            "groups": legacy.get("groups") or [],
            "exists": bool(learned_exists or mapping_exists),
            "learned_exists": learned_exists,
            "mapping_exists": mapping_exists,
        }
    else:
        # Check new base mapping (params_meta) in Firestore
        try:
            new_map = store.get_device_mapping(signature)
            if new_map:
                mapping_exists = True
                pm = new_map.get("params_meta") or []
                data = {
                    "device_name": dname,
                    "signature": signature,
                    "params": [{
                        "name": p.get("name"),
                        "index": p.get("index"),
                        "min": p.get("min"),
                        "max": p.get("max"),
                        "sample_count": 0,
                    } for p in pm],
                    "exists": True,
                    "mapping_exists": True,
                    "learned_exists": False,
                }
        except Exception:
            mapping_exists = False

    # Save minimal preset (values + display) in background (idempotent)
    dmio.ensure_structure_and_capture(signature, detect_device_type(params, dname), int(index), int(device), dname, params)

    # If neither mapping exists, derive minimal summary from live params
    if data is None:
        data = {
            "device_name": dname,
            "signature": signature,
            "params": [{
                "name": p.get("name"),
                "index": p.get("index"),
                "min": p.get("min"),
                "max": p.get("max"),
                "sample_count": 0,
            } for p in params],
            # Treat as learned for UI purposes (structure known from live)
            "exists": True,
            "mapping_exists": False,
            "learned_exists": False,
        }

    exists = bool((data or {}).get("exists"))
    return {
        "ok": True,
        "backend": backend,
        "signature": signature,
        "exists": exists,
        "data": data,
    }


class MappingImportBody(BaseModel):
    signature: str
    device_type: Optional[str] = None
    grouping: Optional[dict] = None
    params_meta: Optional[list] = None
    sources: Optional[dict] = None
    analysis_status: Optional[str] = None


@router.post("/device_mapping/import")
def import_device_mapping(body: MappingImportBody) -> Dict[str, Any]:
    sig = str(body.signature or "").strip()
    if not sig:
        raise HTTPException(400, "signature required")
    store = get_store()
    if not store.enabled:
        return {"ok": False, "error": "firestore_disabled"}
    existing = store.get_device_mapping(sig) or {}
    updated: Dict[str, Any] = dict(existing)
    updated["device_signature"] = sig
    if body.device_type:
        updated["device_type"] = body.device_type
    if body.grouping is not None:
        updated["grouping"] = body.grouping
    if body.params_meta is not None:
        updated["params_meta"] = list(body.params_meta)  # replace
    if body.sources is not None:
        src = dict(updated.get("sources") or {})
        src.update(dict(body.sources))
        updated["sources"] = src
    if body.analysis_status:
        updated["analysis_status"] = body.analysis_status
    try:
        import time as _time
        if "created_at" not in updated:
            updated["created_at"] = int(_time.time())
        updated["updated_at"] = int(_time.time())
    except Exception:
        pass
    ok = store.save_device_mapping(sig, updated)
    return {"ok": bool(ok), "signature": sig}


@router.get("/device_mapping")
def get_device_mapping(signature: Optional[str] = None, index: Optional[int] = None, device: Optional[int] = None) -> Dict[str, Any]:
    sig = (signature or "").strip()
    if not sig:
        if index is None or device is None:
            raise HTTPException(400, "Provide signature or index+device")
        devs = request_op("get_return_devices", timeout=1.0, return_index=int(index))
        devices = ((devs or {}).get("data") or {}).get("devices") or []
        dname = None
        for d in devices:
            if int(d.get("index", -1)) == int(device):
                dname = str(d.get("name", f"Device {device}"))
                break
        if dname is None:
            raise HTTPException(404, "device_not_found")
        params_resp = request_op("get_return_device_params", timeout=1.2, return_index=int(index), device_index=int(device))
        live_params = ((params_resp or {}).get("data") or {}).get("params") or []
        sig = make_device_signature(dname, live_params)
    store = get_store()
    mapping = store.get_device_mapping(sig) if store.enabled else None
    if not mapping:
        return {"ok": True, "signature": sig, "mapping_exists": False}
    params_meta = mapping.get("params_meta") or []
    fitted = [p.get("name") for p in params_meta if isinstance(p, dict) and isinstance(p.get("fit"), dict)]
    missing_cont = [p.get("name") for p in params_meta if isinstance(p, dict) and (p.get("control_type") == "continuous") and (not p.get("fit"))]
    return {"ok": True, "signature": sig, "mapping_exists": True, "mapping": mapping, "summary": {"params_meta_total": len(params_meta), "fitted_count": len(fitted), "fitted_names": fitted, "missing_continuous": missing_cont}}


@router.get("/device_mapping/validate")
def validate_device_mapping(signature: Optional[str] = None, index: Optional[int] = None, device: Optional[int] = None) -> Dict[str, Any]:
    sig = (signature or "").strip()
    live_params: list[dict] = []
    if not sig:
        if index is None or device is None:
            raise HTTPException(400, "Provide signature or index+device")
        devs = request_op("get_return_devices", timeout=1.0, return_index=int(index))
        devices = ((devs or {}).get("data") or {}).get("devices") or []
        dname = None
        for d in devices:
            if int(d.get("index", -1)) == int(device):
                dname = str(d.get("name", f"Device {device}"))
                break
        if dname is None:
            raise HTTPException(404, "device_not_found")
        params_resp = request_op("get_return_device_params", timeout=1.2, return_index=int(index), device_index=int(device))
        live_params = ((params_resp or {}).get("data") or {}).get("params") or []
        sig = make_device_signature(dname, live_params)
    else:
        if index is not None and device is not None:
            params_resp = request_op("get_return_device_params", timeout=1.2, return_index=int(index), device_index=int(device))
            live_params = ((params_resp or {}).get("data") or {}).get("params") or []
    live_names = set(str(p.get("name", "")).strip() for p in (live_params or []))
    store = get_store()
    mapping = store.get_device_mapping(sig) if store.enabled else None
    if not mapping:
        return {"ok": True, "signature": sig, "mapping_exists": False, "live_names": sorted(list(live_names))}
    declared = set()
    try:
        for m in (mapping.get("grouping", {}) or {}).get("masters", []) or []:
            declared.add(str(m))
        for d, m in ((mapping.get("grouping", {}) or {}).get("dependents", {}) or {}).items():
            declared.add(str(d))
        for pm in mapping.get("params_meta", []) or []:
            declared.add(str(pm.get("name", "")))
    except Exception:
        pass
    missing_in_live = sorted([n for n in declared if n and n not in live_names])
    unused_in_mapping = sorted([n for n in live_names if n and n not in declared])
    return {"ok": True, "signature": sig, "mapping_exists": True, "missing_in_live": missing_in_live, "unused_in_mapping": unused_in_mapping, "counts": {"declared": len(declared), "live": len(live_names)}}


@router.get("/device_mapping/validate_grouping")
def validate_grouping(signature: Optional[str] = None, index: Optional[int] = None, device: Optional[int] = None) -> Dict[str, Any]:
    sig = (signature or "").strip()
    live_params: list[dict] = []
    device_name: str = ""
    if not sig:
        if index is None or device is None:
            raise HTTPException(400, "Provide signature or index+device")
        devs = request_op("get_return_devices", timeout=1.0, return_index=int(index))
        devices = ((devs or {}).get("data") or {}).get("devices") or []
        dname = None
        for d in devices:
            if int(d.get("index", -1)) == int(device):
                dname = str(d.get("name", f"Device {device}"))
                break
        if dname is None:
            raise HTTPException(404, "device_not_found")
        params_resp = request_op("get_return_device_params", timeout=1.2, return_index=int(index), device_index=int(device))
        live_params = ((params_resp or {}).get("data") or {}).get("params") or []
        device_name = dname
        sig = make_device_signature(dname, live_params)
    else:
        if index is not None and device is not None:
            params_resp = request_op("get_return_device_params", timeout=1.2, return_index=int(index), device_index=int(device))
            live_params = ((params_resp or {}).get("data") or {}).get("params") or []
    store = get_store()
    mapping = store.get_device_mapping(sig) if store.enabled else None
    if not mapping:
        return {"ok": True, "signature": sig, "mapping_exists": False, "reason": "no_mapping"}
    grp = mapping.get("grouping") or {}
    deps = grp.get("dependents") or {}
    live_names = set(str(p.get("name", "")).strip().lower() for p in (live_params or []))
    results = []
    unresolved = {"missing_dependent": [], "missing_master": []}
    for dep, master in deps.items():
        dep_lc = str(dep).strip().lower()
        mas_lc = str(master).strip().lower()
        dep_ok = dep_lc in live_names
        mas_ok = mas_lc in live_names
        if not dep_ok:
            unresolved["missing_dependent"].append(dep)
        if not mas_ok:
            unresolved["missing_master"].append(master)
        results.append({
            "dependent_name": dep,
            "master_name": master,
            "dependent_live_exists": bool(dep_ok),
            "master_live_exists": bool(mas_ok),
        })
    return {"ok": True, "signature": sig, "device_name": device_name or mapping.get("device_name"), "grouping_count": len(deps), "results": results, "unresolved": unresolved}


# --- Helpers for name/index resolution and numeric parsing ---

def _resolve_param_index(ri: int, di: int, ref: str) -> int:
    resp = request_op("get_return_device_params", timeout=1.0, return_index=int(ri), device_index=int(di))
    params = ((resp or {}).get("data") or {}).get("params") or []
    r = str(ref).strip().lower()
    if r.isdigit():
        return int(r)
    for p in params:
        nm = str(p.get("name", "")).lower()
        if r in nm:
            return int(p.get("index", 0))
    raise HTTPException(404, f"param_not_found:{ref}")


def _compute_signature_for(index: int, device: int) -> str:
    devs = request_op("get_return_devices", timeout=1.0, return_index=int(index))
    devices = ((devs or {}).get("data") or {}).get("devices") or []
    dname = None
    for d in devices:
        if int(d.get("index", -1)) == int(device):
            dname = str(d.get("name", f"Device {device}"))
            break
    params_resp = request_op("get_return_device_params", timeout=1.2, return_index=int(index), device_index=int(device))
    params = ((params_resp or {}).get("data") or {}).get("params") or []
    return make_device_signature(dname or f"Device {device}", params)


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


@router.post("/device_mapping/sanity_probe")
def sanity_probe(body: Dict[str, Any]) -> Dict[str, Any]:
    ri = int(body.get("return_index"))
    di = int(body.get("device_index"))
    param_ref = str(body.get("param_ref"))
    target_display = str(body.get("target_display"))
    restore = bool(body.get("restore", True))
    # Resolve param index
    pi = _resolve_param_index(ri, di, param_ref)
    pr = request_op("get_return_device_params", timeout=1.2, return_index=ri, device_index=di)
    params = ((pr or {}).get("data") or {}).get("params") or []
    cur = next((p for p in params if int(p.get("index", -1)) == pi), None)
    if not cur:
        raise HTTPException(404, "param_not_found")
    vmin = float(cur.get("min", 0.0))
    vmax = float(cur.get("max", 1.0))
    prev_x = float(cur.get("value", vmin))
    pname = str(cur.get("name", ""))
    # Compute signature and mapping
    sig = _compute_signature_for(ri, di)
    store = get_store()
    mapping = store.get_device_mapping(sig) if store.enabled else None
    ty = _parse_target_display(target_display)
    applied_disp = ""
    applied_num = None
    if ty is None and mapping:
        pm = next(
            (
                pme
                for pme in (mapping.get("params_meta") or [])
                if str(pme.get("name", "")).lower() == pname.lower()
            ),
            None,
        )
        if pm and isinstance(pm.get("label_map"), dict):
            lm = pm.get("label_map") or {}
            # label_map format: {"0": "Clean", "1": "Boost", ...} (number → label)
            for k, v in lm.items():
                if str(v).strip().lower() == target_display.strip().lower():
                    x = max(vmin, min(vmax, float(k)))
                    request_op(
                        "set_return_device_param",
                        timeout=1.0,
                        return_index=ri,
                        device_index=di,
                        param_index=pi,
                        value=float(x),
                    )
                    break
        # readback
        rb = request_op("get_return_device_params", timeout=1.0, return_index=ri, device_index=di)
        rps = ((rb or {}).get("data") or {}).get("params") or []
        newp = next((p for p in rps if int(p.get("index", -1)) == pi), None)
        applied_disp = str((newp or {}).get("display_value", ""))
        applied_num = _parse_target_display(applied_disp)
    if ty is not None:
        x = prev_x
        pm = (
            next(
                (
                    pme
                    for pme in (mapping.get("params_meta") or [])
                    if str(pme.get("name", "")).lower() == pname.lower()
                ),
                None,
            )
            if mapping
            else None
        )
        if pm and isinstance(pm.get("fit"), dict):
            x = _invert_fit_to_value(pm.get("fit") or {}, float(ty), vmin, vmax)
        request_op(
            "set_return_device_param",
            timeout=1.0,
            return_index=ri,
            device_index=di,
            param_index=pi,
            value=float(x),
        )
        rb = request_op("get_return_device_params", timeout=1.0, return_index=ri, device_index=di)
        rps = ((rb or {}).get("data") or {}).get("params") or []
        newp = next((p for p in rps if int(p.get("index", -1)) == pi), None)
        applied_disp = str((newp or {}).get("display_value", ""))
        applied_num = _parse_target_display(applied_disp)
        if applied_num is not None:
            td = float(ty)
            err0 = td - float(applied_num)
            thresh = 0.02 * (abs(td) if td != 0 else 1.0)
            if abs(err0) > thresh:
                lo = vmin
                hi = vmax
                curx = x
                if err0 < 0:
                    hi = curx
                else:
                    lo = curx
                for _ in range(6):
                    mid = (lo + hi) / 2.0
                    request_op(
                        "set_return_device_param",
                        timeout=1.0,
                        return_index=ri,
                        device_index=di,
                        param_index=pi,
                        value=float(mid),
                    )
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
    err = None
    td_final = _parse_target_display(target_display)
    if td_final is not None and applied_num is not None:
        err = float(td_final) - float(applied_num)
    if bool(restore):
        request_op(
            "set_return_device_param",
            timeout=1.0,
            return_index=ri,
            device_index=di,
            param_index=pi,
            value=float(prev_x),
        )
    return {"ok": True, "signature": sig, "param": pname, "applied_display": applied_disp, "error": err}


@router.get("/device_mapping/fits")
def get_device_mapping_fits(signature: Optional[str] = None, index: Optional[int] = None, device: Optional[int] = None) -> Dict[str, Any]:
    if str(os.getenv("FB_DEBUG_LEGACY_LEARN", "")).lower() not in ("1", "true", "yes", "on"):
        raise HTTPException(404, "legacy_disabled")
    sig = (signature or "").strip()
    if not sig:
        if index is None or device is None:
            raise HTTPException(400, "Provide signature or index+device")
        devs = request_op("get_return_devices", timeout=1.0, return_index=int(index))
        devices = ((devs or {}).get("data") or {}).get("devices") or []
        dname = None
        for d in devices:
            if int(d.get("index", -1)) == int(device):
                dname = str(d.get("name", f"Device {device}"))
                break
        if dname is None:
            raise HTTPException(404, "device_not_found")
        params_resp = request_op("get_return_device_params", timeout=1.2, return_index=int(index), device_index=int(device))
        live_params = ((params_resp or {}).get("data") or {}).get("params") or []
        sig = make_device_signature(dname, live_params)
    store = get_store()
    mapping = store.get_device_mapping(sig) if store.enabled else None
    if not mapping:
        return {"ok": True, "signature": sig, "mapping_exists": False, "fits": []}
    fits = []
    for pm in (mapping.get("params_meta") or []):
        try:
            fit = pm.get("fit")
            if isinstance(fit, dict):
                fits.append(
                    {
                        "name": pm.get("name"),
                        "type": fit.get("type"),
                        "coeffs": fit.get("coeffs"),
                        "r2": fit.get("r2"),
                        "confidence": pm.get("confidence"),
                    }
                )
        except Exception:
            continue
    fits = sorted(fits, key=lambda x: str(x.get("name", "")))
    return {"ok": True, "signature": sig, "count": len(fits), "fits": fits}


@router.get("/device_mapping/enumerate_labels")
def enumerate_param_labels(index: int, device: int, param_ref: str) -> Dict[str, Any]:
    ri = int(index)
    di = int(device)
    try:
        pi = _resolve_param_index(ri, di, param_ref)
    except Exception:
        raise HTTPException(404, "param_not_found")
    pr = request_op("get_return_device_params", timeout=1.2, return_index=ri, device_index=di)
    params = ((pr or {}).get("data") or {}).get("params") or []
    cur = next((p for p in params if int(p.get("index", -1)) == pi), None)
    if not cur:
        raise HTTPException(404, "param_not_found")
    vmin = float(cur.get("min", 0.0))
    vmax = float(cur.get("max", 1.0))
    prev = float(cur.get("value", vmin))
    name = str(cur.get("name", ""))
    labels = []
    try:
        import time as _t

        lo = int(vmin)
        hi = int(vmax)
        for step in range(lo, hi + 1):
            request_op(
                "set_return_device_param",
                timeout=1.0,
                return_index=ri,
                device_index=di,
                param_index=pi,
                value=float(step),
            )
            _t.sleep(0.15)
            rb = request_op("get_return_device_params", timeout=1.0, return_index=ri, device_index=di)
            rps = ((rb or {}).get("data") or {}).get("params") or []
            p2 = next((p for p in rps if int(p.get("index", -1)) == pi), None)
            disp = str((p2 or {}).get("display_value", ""))
            labels.append({"step": step, "display": disp})
    finally:
        try:
            request_op(
                "set_return_device_param",
                timeout=1.0,
                return_index=ri,
                device_index=di,
                param_index=pi,
                value=float(prev),
            )
        except Exception:
            pass
    label_map = {}
    for item in labels:
        d = item.get("display")
        if d and d not in label_map:
            label_map[d] = float(item.get("step", 0))
    return {"ok": True, "param": name, "index": pi, "range": [int(vmin), int(vmax)], "samples": labels, "label_map_suggested": label_map}


def _fit_models(samples: list[dict]) -> dict | None:
    pts = [
        (float(s["value"]), float(s["display_num"]))
        for s in samples
        if s.get("display_num") is not None
    ]
    pts = [(x, y) for x, y in pts if math.isfinite(x) and math.isfinite(y)]
    if len(pts) < 3:
        return None
    pts.sort(key=lambda t: t[0])
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]

    def lin_fit(u, v):
        n = len(u)
        sx = sum(u)
        sy = sum(v)
        sxx = sum(a * a for a in u)
        sxy = sum(a * b for a, b in zip(u, v))
        den = n * sxx - sx * sx
        if den == 0:
            return None
        a = (n * sxy - sx * sy) / den
        b = (sy - a * sx) / n
        yhat = [a * t + b for t in u]
        ss_res = sum((vi - hi) ** 2 for vi, hi in zip(v, yhat))
        ymean = sy / n
        ss_tot = sum((vi - ymean) ** 2 for vi in v) or 1.0
        r2 = 1.0 - ss_res / ss_tot
        return {"type": "linear", "a": a, "b": b, "r2": r2}

    def log_fit(u, v):
        u2 = [math.log(max(1e-9, t)) for t in u]
        base = lin_fit(u2, v)
        return base and {**base, "type": "log", "x_transform": "ln(x)"}

    def exp_fit(u, v):
        if any(val <= 0 for val in v):
            return None
        v2 = [math.log(val) for val in v]
        fit = lin_fit(u, v2)
        if not fit:
            return None
        a = fit["a"]
        b = fit["b"]
        r2 = fit["r2"]
        return {"type": "exp", "a": a, "b": b, "r2": r2}

    cands = []
    f1 = lin_fit(xs, ys)
    if f1:
        cands.append(f1)
    f2 = log_fit(xs, ys)
    if f2:
        cands.append(f2)
    f3 = exp_fit(xs, ys)
    if f3:
        cands.append(f3)
    best = max(cands, key=lambda d: d["r2"]) if cands else None
    if best and best["r2"] >= 0.9:
        return best
    return {
        "type": "piecewise",
        "r2": best["r2"] if best else 0.0,
        "points": [{"x": x, "y": y} for x, y in pts],
    }


@router.post("/mappings/fit")
def fit_mapping(index: Optional[int] = None, device: Optional[int] = None, signature: Optional[str] = None) -> Dict[str, Any]:
    if str(os.getenv("FB_DEBUG_LEGACY_LEARN", "")).lower() not in ("1", "true", "yes", "on"):
        raise HTTPException(404, "legacy_disabled")
    store = get_store()
    sig = (signature or "").strip()
    if not sig:
        if index is None or device is None:
            raise HTTPException(400, "index_device_or_signature_required")
        sig = _compute_signature_for(int(index), int(device))
    data = store.get_device_map_local(sig)
    if not data:
        return {"ok": False, "error": "no_local_map", "signature": sig}
    params = data.get("params") or []
    updated = 0
    for p in params:
        samples = p.get("samples") or []
        fit = _fit_models(samples)
        if fit:
            p["fit"] = fit
            updated += 1
    device_type = detect_device_type(params, data.get("device_name"))
    ok = store.save_device_map_local(sig, {"name": data.get("device_name"), "device_type": device_type}, params)
    return {"ok": ok, "signature": sig, "updated": updated}


class MapDeleteBody(BaseModel):
    return_index: int
    device_index: int


@router.post("/return/device/map_delete")
def delete_return_device_map(body: MapDeleteBody) -> Dict[str, Any]:
    store = get_store()
    devs = request_op("get_return_devices", timeout=1.0, return_index=int(body.return_index))
    devices = ((devs or {}).get("data") or {}).get("devices") or []
    dname = None
    for d in devices:
        if int(d.get("index", -1)) == int(body.device_index):
            dname = str(d.get("name", f"Device {body.device_index}"))
            break
    if dname is None:
        raise HTTPException(404, "device_not_found")
    params_resp = request_op("get_return_device_params", timeout=1.2, return_index=int(body.return_index), device_index=int(body.device_index))
    params = ((params_resp or {}).get("data") or {}).get("params") or []
    signature = make_device_signature(dname, params)
    ok = store.delete_device_map(signature) if store.enabled else False
    return {"ok": ok, "signature": signature, "backend": store.backend}


# --- Legacy learning endpoints (gated) ---

class LearnDeviceBody(BaseModel):
    return_index: int
    device_index: int
    resolution: int = 21
    sleep_ms: int = 25


class LearnQuickBody(BaseModel):
    return_index: int
    device_index: int


"""Legacy learning endpoints are defined in app (to avoid duplicate routes)."""


"""See app for legacy learn_start (gated)."""


"""See app for legacy learn_quick (gated)."""


"""See app for legacy learn_status (gated)."""
