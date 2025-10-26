from __future__ import annotations
import os
from typing import Any, Dict, Optional
import time
import asyncio
from fastapi.responses import StreamingResponse
import json

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from server.services.ableton_client import request_op
from server.models.ops import MixerOp, SendOp, DeviceParamOp
from server.services.intent_mapper import map_llm_to_canonical
from server.volume_utils import db_to_live_float, live_float_to_db, db_to_live_float_send, live_float_to_db_send
from server.config.app_config import (
    get_app_config,
    get_send_aliases,
    get_ui_settings,
    set_ui_settings,
    set_send_aliases,
    get_debug_settings,
    set_debug_settings,
    reload_config as cfg_reload,
    save_config as cfg_save,
)
from server.config.param_learn_config import (
    get_param_learn_config,
    set_param_learn_config,
    reload_param_learn_config,
    save_param_learn_config,
)
from server.config.param_registry import (
    get_param_registry,
    reload_param_registry,
)
from server.services.mapping_store import MappingStore
from server.services.mapping_utils import detect_device_type, make_device_signature
from server.services.param_analysis import (
    build_groups_from_params,
    classify_control_type,
    fit_models,
    group_role_for_device,
    parse_unit_from_display,
)
from server.services.preset_metadata import generate_preset_metadata_llm
from server.services.chat_service import ChatBody, HelpBody, handle_chat, handle_help
from server.services.history import (
    DEVICE_BYPASS_CACHE,
    LAST_SENT,
    REDO_STACK,
    UNDO_STACK,
    history_state as get_history_state,
    redo_last as history_redo_last,
    undo_last as history_undo_last,
    _key,
    _rate_limited,
)
from server.services.event_listener import (
    schedule_live_index_tasks,
    start_ableton_event_listener,
)
from server.core.deps import set_store_instance, get_live_index
from server.core.events import broker, emit_event, schedule_emit
from server.api.events import router as events_router
from server.api.health import router as health_router
from server.api.transport import router as transport_router
from server.api.config import router as config_router
from server.api.master import router as master_router
from server.api.tracks import router as tracks_router
from server.api.returns import router as returns_router
from server.api.ops import router as ops_router
from server.api.device_mapping import router as device_mapping_router
from server.api.presets import router as presets_router
from server.api.intents import router as intents_router
from server.api.overview import router as overview_router
# from server.api.snapshot import router as snapshot_router  # Merged into overview_router
import math
from server.volume_parser import parse_volume_command
_MASTER_DEDUP: dict[str, tuple[float, float]] = {}

app = FastAPI(title="Fadebender Ableton Server", version="0.1.0")

# Back-compat shim: route legacy udp_request-style calls via request_op
def udp_request(msg: Dict[str, Any], timeout: float = 1.0):
    try:
        op = str((msg or {}).get("op", ""))
        params = dict(msg or {})
        params.pop("op", None)
        return request_op(op, timeout=timeout, **params)
    except Exception:
        return None


def _status_ttl_seconds(default: float = 1.0) -> float:
    try:
        env = os.getenv("FB_STATUS_TTL_SECONDS")
        if env is not None and str(env).strip() != "":
            v = float(env)
            return max(0.0, v)
    except Exception:
        pass
    try:
        cfg = get_app_config()
        v = cfg.get("server", {}).get("status_ttl_seconds", default)
        return max(0.0, float(v))
    except Exception:
        return default

# Load .env at server startup so Vertex/LLM config can come from file
try:  # optional dependency
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass

def _cors_origins() -> list[str]:
    # Read from env: FB_CORS_ORIGINS as comma-separated list; if FB_ALLOW_ALL_CORS=1, allow '*'
    allow_all = str(os.getenv("FB_ALLOW_ALL_CORS", "")).lower() in ("1", "true", "yes", "on")
    if allow_all:
        return ["*"]
    env_val = os.getenv("FB_CORS_ORIGINS")
    if env_val:
        try:
            vals = [v.strip() for v in env_val.split(",") if v.strip()]
            if vals:
                return vals
        except Exception:
            pass
    return [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]


app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# llm/health is now provided by the health router


# --- Simple SSE event broker ---
STORE = MappingStore()
set_store_instance(STORE)
LEARN_JOBS: dict[str, dict] = {}

app.include_router(events_router)
app.include_router(transport_router)
app.include_router(config_router)
app.include_router(master_router)
app.include_router(tracks_router)
app.include_router(returns_router)
app.include_router(device_mapping_router)
app.include_router(presets_router)
app.include_router(ops_router)
app.include_router(intents_router)
app.include_router(overview_router)
# app.include_router(snapshot_router)  # Merged into overview_router


app.include_router(health_router)


# Transport routes moved to server.api.transport


# Master routes moved to server.api.master


"""Config routes moved to server.api.config"""


"""Param registry route moved to server.api.config"""


"""Param learn routes moved to server.api.config"""


class IntentParseBody(BaseModel):
    text: str
    model: Optional[str] = None
    strict: Optional[bool] = None


class VolumeDbBody(BaseModel):
    track_index: int
    db: float


@app.get("/ping")
def ping() -> Dict[str, Any]:
    resp = request_op("ping", timeout=0.5)
    ok = bool(resp and resp.get("ok", True))
    return {"ok": ok, "remote": resp}


@app.get("/status")
def status() -> Dict[str, Any]:
    # short TTL cache to reduce poll churn
    try:
        now = time.time()
        ttl = _status_ttl_seconds(1.0)
        cache = globals().setdefault("_TTL_CACHE", {})  # type: ignore
        ent = cache.get("status") if isinstance(cache, dict) else None
        if ent and isinstance(ent, dict):
            ts = float(ent.get("ts", 0.0))
            if ttl > 0 and (now - ts) < ttl:
                return ent.get("data")
        resp = request_op("get_overview", timeout=1.0)
        if not resp:
            return {"ok": False, "error": "no response"}
        cache["status"] = {"ts": now, "data": resp}
        return resp
    except Exception:
        resp = request_op("get_overview", timeout=1.0)
        if not resp:
            return {"ok": False, "error": "no response"}
        return resp


@app.get("/project/outline")
def project_outline() -> Dict[str, Any]:
    """Return lightweight project outline (tracks, selected track, scenes)."""
    try:
        now = time.time()
        ttl = _status_ttl_seconds(1.0)
        cache = globals().setdefault("_TTL_CACHE", {})  # type: ignore
        ent = cache.get("project_outline") if isinstance(cache, dict) else None
        if ent and isinstance(ent, dict):
            ts = float(ent.get("ts", 0.0))
            if ttl > 0 and (now - ts) < ttl:
                return ent.get("data")
        resp = request_op("get_overview", timeout=1.0)
        if not resp:
            return {"ok": False, "error": "no response"}
        data = resp.get("data") if isinstance(resp, dict) else resp
        out = {"ok": True, "data": data}
        cache["project_outline"] = {"ts": now, "data": out}
        return out
    except Exception:
        resp = request_op("get_overview", timeout=1.0)
        if not resp:
            return {"ok": False, "error": "no response"}
        data = resp.get("data") if isinstance(resp, dict) else resp
        return {"ok": True, "data": data}


# Track status moved to server.api.tracks


# Track sends moved to server.api.tracks


# Track routing moved to server.api.tracks


# Returns listing moved to server.api.returns


# Return sends moved to server.api.returns


# ==================== Return Routing & Sends Mode ====================

class ReturnRoutingSetBody(BaseModel):
    return_index: int
    audio_to_type: Optional[str] = None
    audio_to_channel: Optional[str] = None
    sends_mode: Optional[str] = None  # "pre" | "post" (optional capability)


# Return routing GET moved to server.api.returns


# Return routing POST moved to server.api.returns


# Return devices moved to server.api.returns


# ---------------- Track devices (Phase A - minimal) ----------------

# Track devices moved to server.api.tracks


# Track device params moved to server.api.tracks


# Track device param set moved to server.api.tracks


# ---------------- Master devices (Phase A - minimal) ----------------

"""Master devices moved to server.api.master"""


"""Master device params moved to server.api.master"""


"""Master device param set moved to server.api.master"""


"""Return device params moved to server.api.returns"""


"""Return device map endpoints moved to server.api.device_mapping (removed)."""


"""Map delete and return op bodies moved to server.api.* (removed duplicates)."""


# ---------------- Device Mapping Import (LLM + Numeric Fits) ----------------

class MappingImportBody(BaseModel):
    signature: str
    device_type: Optional[str] = None
    grouping: Optional[dict] = None
    params_meta: Optional[list] = None
    sources: Optional[dict] = None
    analysis_status: Optional[str] = None  # e.g., "partial_fits" | "analyzed"


# moved: /device_mapping/import handled by server.api.device_mapping
def import_device_mapping(body: MappingImportBody) -> Dict[str, Any]:
    # Keep a thin shim to avoid breaking any imports; delegate to router impl
    from server.api.device_mapping import import_device_mapping as _imp
    return _imp(body)


# moved: /device_mapping handled by server.api.device_mapping
def get_device_mapping(signature: Optional[str] = None, index: Optional[int] = None, device: Optional[int] = None) -> Dict[str, Any]:
    from server.api.device_mapping import get_device_mapping as _get
    return _get(signature=signature, index=index, device=device)


# moved: /device_mapping/validate handled by server.api.device_mapping
def validate_device_mapping(signature: Optional[str] = None, index: Optional[int] = None, device: Optional[int] = None) -> Dict[str, Any]:
    from server.api.device_mapping import validate_device_mapping as _val
    return _val(signature=signature, index=index, device=device)


class SanityProbeBody(BaseModel):
    return_index: int
    device_index: int
    param_ref: str  # name substring or index string
    target_display: str
    restore: Optional[bool] = True


"""/device_mapping/sanity_probe moved to server.api.device_mapping"""


# moved: /device_mapping/fits handled by server.api.device_mapping
"""/device_mapping/fits moved to server.api.device_mapping"""


"""/device_mapping/enumerate_labels moved to server.api.device_mapping"""


class ReturnMixerBody(BaseModel):
    return_index: int
    field: str  # 'volume' | 'pan' | 'mute' | 'solo'
    value: float


"""/op/return/mixer moved to server.api.ops"""
def op_return_mixer(body: ReturnMixerBody) -> Dict[str, Any]:
    ...


class LearnDeviceBody(BaseModel):
    return_index: int
    device_index: int
    resolution: int = 21
    sleep_ms: int = 25


@app.post("/return/device/learn")
def learn_return_device(body: LearnDeviceBody) -> Dict[str, Any]:
    if str(os.getenv("FB_DEBUG_LEGACY_LEARN", "")).lower() not in ("1", "true", "yes", "on"):
        raise HTTPException(404, "legacy_disabled")
    """Sweep device params to build value->display mapping and store in Firestore.

    For each parameter, samples 'resolution' points between min..max, reading display_value.
    Restores the original value after sampling.
    """
    import time

    ri = int(body.return_index)
    di = int(body.device_index)
    res = max(3, int(body.resolution))
    delay = max(0, int(body.sleep_ms)) / 1000.0

    # Fetch device name and params
    devs = udp_request({"op": "get_return_devices", "return_index": ri}, timeout=1.0)
    devices = ((devs or {}).get("data") or {}).get("devices") or []
    dname = None
    for d in devices:
        if int(d.get("index", -1)) == di:
            dname = str(d.get("name", f"Device {di}"))
            break
    if dname is None:
        raise HTTPException(404, "device_not_found")

    params_resp = udp_request({"op": "get_return_device_params", "return_index": ri, "device_index": di}, timeout=1.2)
    params = ((params_resp or {}).get("data") or {}).get("params") or []
    if not params:
        return {"ok": False, "reason": "no_params"}

    signature = make_device_signature(dname, params)

    learned_params: list[dict] = []

    for p in params:
        idx = int(p.get("index", 0))
        name = str(p.get("name", f"Param {idx}"))
        vmin = float(p.get("min", 0.0))
        vmax = float(p.get("max", 1.0))
        v0 = float(p.get("value", 0.0))
        samples: list[dict] = []
        unit: str | None = None

        # Guard: avoid zero-length spans
        span = vmax - vmin if vmax != vmin else 1.0
        for i in range(res):
            t = i / float(res - 1)
            val = vmin + span * t
            # set param
            udp_request({
                "op": "set_return_device_param",
                "return_index": ri,
                "device_index": di,
                "param_index": idx,
                "value": float(val)
            }, timeout=0.6)
            if delay:
                time.sleep(delay)
            # readback
            rd = udp_request({"op": "get_return_device_params", "return_index": ri, "device_index": di}, timeout=1.0)
            rparams = ((rd or {}).get("data") or {}).get("params") or []
            dp = next((rp for rp in rparams if int(rp.get("index", -1)) == idx), None)
            if dp is None:
                continue
            disp = str(dp.get("display_value", ""))
            disp_num = None
            # Try parse numeric from display if present
            try:
                import re
                m = re.search(r"-?\d+(?:\.\d+)?", disp)
                if m:
                    disp_num = float(m.group(0))
                if unit is None:
                    # crude unit detection
                    unit = parse_unit_from_display(disp)
            except Exception:
                disp_num = None
            samples.append({"value": float(val), "display": disp, "display_num": disp_num})

        # restore
        udp_request({
            "op": "set_return_device_param",
            "return_index": ri,
            "device_index": di,
            "param_index": idx,
            "value": float(v0)
        }, timeout=0.6)

        # Classify control type and labels if any
        ctype, labels = classify_control_type(samples, vmin, vmax)
        gname, role, _m = group_role_for_device(dname, name)
        fit = fit_models(samples) if ctype == "continuous" else None
        label_map = None
        if ctype in ("binary", "quantized"):
            label_map = {}
            for s in samples:
                lab = str(s.get("display", ""))
                if lab not in label_map:
                    label_map[lab] = float(s.get("value", vmin))
        learned_params.append({
            "index": idx,
            "name": name,
            "min": vmin,
            "max": vmax,
            "samples": samples,
            "control_type": ctype,
            "unit": unit,
            "labels": labels,
            "label_map": label_map,
            "fit": fit,
            "group": gname,
            "role": role,
        })

    # Save to mapping store (Firestore)
    groups_meta = build_groups_from_params(learned_params, dname)
    device_type = detect_device_type(params, dname)
    saved = STORE.save_device_map(signature, {"name": dname, "device_type": device_type, "groups": groups_meta}, learned_params)
    return {"ok": True, "signature": signature, "saved": saved, "backend": STORE.backend, "param_count": len(learned_params)}


class LearnStartBody(BaseModel):
    return_index: int
    device_index: int
    resolution: int = 41
    sleep_ms: int = 20
    mode: Optional[str] = "quick"  # quick | exhaustive


@app.post("/return/device/learn_start")
async def learn_return_device_start(body: LearnStartBody) -> Dict[str, Any]:
    if str(os.getenv("FB_DEBUG_LEGACY_LEARN", "")).lower() not in ("1", "true", "yes", "on"):
        raise HTTPException(404, "legacy_disabled")
    import asyncio
    import uuid

    job_id = str(uuid.uuid4())
    LEARN_JOBS[job_id] = {
        "state": "queued",
        "progress": 0,
        "total": 1,
        "message": "Starting",
    }

    async def run():
        try:
            ri = int(body.return_index)
            di = int(body.device_index)
            res = max(3, int(body.resolution))
            delay = max(0, int(body.sleep_ms)) / 1000.0

            # Fetch device + params
            devs = udp_request({"op": "get_return_devices", "return_index": ri}, timeout=1.0)
            devices = ((devs or {}).get("data") or {}).get("devices") or []
            dname = None
            for d in devices:
                if int(d.get("index", -1)) == di:
                    dname = str(d.get("name", f"Device {di}"))
                    break
            params_resp = udp_request({"op": "get_return_device_params", "return_index": ri, "device_index": di}, timeout=1.2)
            params = ((params_resp or {}).get("data") or {}).get("params") or []
            signature = make_device_signature(dname or f"Device {di}", params)
            total_steps = max(1, len(params) * res)
            LEARN_JOBS[job_id].update({"state": "running", "progress": 0, "total": total_steps, "signature": signature})

            learned_params: list[dict] = []
            step = 0
            for p in params:
                idx = int(p.get("index", 0))
                name = str(p.get("name", f"Param {idx}"))
                vmin = float(p.get("min", 0.0))
                vmax = float(p.get("max", 1.0))
                v0 = float(p.get("value", 0.0))

                # Coarse check for quantization using 9 points
                import time as _t
                labels = set()
                coarse = 9
                span = vmax - vmin if vmax != vmin else 1.0
                for i in range(coarse):
                    t = i / float(coarse - 1)
                    val = vmin + span * t
                    udp_request({"op": "set_return_device_param", "return_index": ri, "device_index": di, "param_index": idx, "value": float(val)}, timeout=0.6)
                    if delay: _t.sleep(delay)
                    rd = udp_request({"op": "get_return_device_params", "return_index": ri, "device_index": di}, timeout=1.0)
                    rparams = ((rd or {}).get("data") or {}).get("params") or []
                    dp = next((rp for rp in rparams if int(rp.get("index", -1)) == idx), None)
                    if dp is not None:
                        labels.add(str(dp.get("display_value", "")))

                # If few unique labels and not numeric -> treat as enum/binary
                from re import search as _re_search
                numeric_count = 0
                for lab in labels:
                    if _re_search(r"-?\d+(?:\.\d+)?", lab):
                        numeric_count += 1
                is_enum = (len(labels) <= 6 and numeric_count < len(labels)) or (len(labels) <= 2)

                samples: list[dict] = []
                unit: str | None = None
                control_type = "continuous"
                labels_list: list[str] = []
                label_map: dict[str, float] | None = None
                fit: dict | None = None

                if is_enum:
                    # Sweep fine until labels stop changing
                    seen = set()
                    # Ensure attempt at both ends for binary/switches
                    for val in [vmin, vmax]:
                        udp_request({"op": "set_return_device_param", "return_index": ri, "device_index": di, "param_index": idx, "value": float(val)}, timeout=0.6)
                        if delay: _t.sleep(delay)
                        rd = udp_request({"op": "get_return_device_params", "return_index": ri, "device_index": di}, timeout=1.0)
                        rparams = ((rd or {}).get("data") or {}).get("params") or []
                        dp = next((rp for rp in rparams if int(rp.get("index", -1)) == idx), None)
                        if dp is None: continue
                        disp = str(dp.get("display_value", ""))
                        if disp in seen: continue
                        seen.add(disp)
                        samples.append({"value": float(val), "display": disp, "display_num": None})
                        step += 1
                        LEARN_JOBS[job_id].update({"progress": min(step, total_steps), "message": f"{name}: {len(samples)} labels"})
                    for i in range(res):
                        t = i / float(res - 1)
                        val = vmin + span * t
                        udp_request({"op": "set_return_device_param", "return_index": ri, "device_index": di, "param_index": idx, "value": float(val)}, timeout=0.6)
                        if delay: _t.sleep(delay)
                        rd = udp_request({"op": "get_return_device_params", "return_index": ri, "device_index": di}, timeout=1.0)
                        rparams = ((rd or {}).get("data") or {}).get("params") or []
                        dp = next((rp for rp in rparams if int(rp.get("index", -1)) == idx), None)
                        if dp is None: continue
                        disp = str(dp.get("display_value", ""))
                        if disp in seen: continue
                        seen.add(disp)
                        samples.append({"value": float(val), "display": disp, "display_num": None})
                        step += 1
                        LEARN_JOBS[job_id].update({"progress": min(step, total_steps), "message": f"{name}: {len(samples)} labels"})
                    labels_list = [str(s.get("display", "")) for s in samples]
                    control_type = "binary" if len(labels_list) <= 2 else "quantized"
                    # Build label->value map using first-seen sample for each label
                    label_map = {}
                    for s in samples:
                        lab = str(s.get("display", ""))
                        if lab not in label_map:
                            label_map[lab] = float(s.get("value", vmin))
                else:
                    # Continuous: numeric parse & store
                    for i in range(res):
                        t = i / float(res - 1)
                        val = vmin + span * t
                        udp_request({"op": "set_return_device_param", "return_index": ri, "device_index": di, "param_index": idx, "value": float(val)}, timeout=0.6)
                        if delay: _t.sleep(delay)
                        rd = udp_request({"op": "get_return_device_params", "return_index": ri, "device_index": di}, timeout=1.0)
                        rparams = ((rd or {}).get("data") or {}).get("params") or []
                        dp = next((rp for rp in rparams if int(rp.get("index", -1)) == idx), None)
                        if dp is None: continue
                        disp = str(dp.get("display_value", ""))
                        if unit is None:
                            unit = parse_unit_from_display(disp)
                        disp_num = None
                        try:
                            m = _re_search(r"-?\d+(?:\.\d+)?", disp)
                            if m: disp_num = float(m.group(0))
                        except Exception:
                            disp_num = None
                        samples.append({"value": float(val), "display": disp, "display_num": disp_num})
                        step += 1
                        LEARN_JOBS[job_id].update({"progress": min(step, total_steps), "message": f"{name}: {i+1}/{res}"})
                    control_type = "continuous"
                    fit = fit_models(samples) or None

                # restore
                udp_request({"op": "set_return_device_param", "return_index": ri, "device_index": di, "param_index": idx, "value": float(v0)}, timeout=0.6)
                # Group/role annotation
                gname, role, _m = group_role_for_device(dname, name)
                learned_params.append({
                    "index": idx,
                    "name": name,
                    "min": vmin,
                    "max": vmax,
                    "samples": samples,
                    "quantized": is_enum,
                    "control_type": control_type,
                    "unit": unit,
                    "labels": labels_list,
                    "label_map": label_map,
                    "fit": fit,
                    "group": gname,
                    "role": role,
                })

            # Build groups metadata from learned params
            groups_meta = build_groups_from_params(learned_params, dname)
            device_type = detect_device_type(params, dname)
            # Always save locally to avoid losing long scans
            local_saved = STORE.save_device_map_local(signature, {"name": dname, "device_type": device_type, "groups": groups_meta}, learned_params)
            saved = STORE.save_device_map(signature, {"name": dname, "device_type": device_type, "groups": groups_meta}, learned_params)
            LEARN_JOBS[job_id].update({"state": "done", "saved": saved, "local_saved": local_saved})
        except Exception as e:
            LEARN_JOBS[job_id].update({"state": "error", "error": str(e)})

    asyncio.create_task(run())
    return {"ok": True, "job_id": job_id}


class LearnQuickBody(BaseModel):
    return_index: int
    device_index: int


@app.post("/return/device/learn_quick")
def learn_return_device_quick(body: LearnQuickBody) -> Dict[str, Any]:
    if str(os.getenv("FB_DEBUG_LEGACY_LEARN", "")).lower() not in ("1", "true", "yes", "on"):
        raise HTTPException(404, "legacy_disabled")
    """Fast learning using minimal anchors + heuristics. Saves locally + Firestore.
    Intended to complete in seconds for stock devices.
    """
    import time as _t
    PLC = get_param_learn_config()
    delay = max(0, int(PLC.get("defaults", {}).get("sleep_ms_quick", 10))) / 1000.0
    r2_accept = float(PLC.get("defaults", {}).get("r2_accept_quick", 0.99))
    max_extra = int(PLC.get("defaults", {}).get("max_extra_points_quick", 2))

    ri = int(body.return_index)
    di = int(body.device_index)
    # Fetch device + params
    devs = udp_request({"op": "get_return_devices", "return_index": ri}, timeout=1.0)
    devices = ((devs or {}).get("data") or {}).get("devices") or []
    dname = None
    for d in devices:
        if int(d.get("index", -1)) == di:
            dname = str(d.get("name", f"Device {di}"))
            break
    if dname is None:
        raise HTTPException(404, "device_not_found")
    params_resp = udp_request({"op": "get_return_device_params", "return_index": ri, "device_index": di}, timeout=1.2)
    params = ((params_resp or {}).get("data") or {}).get("params") or []
    signature = make_device_signature(dname or f"Device {di}", params)

    H = PLC.get("heuristics", {})
    lin_units = [str(u).lower() for u in (H.get("linear_units") or [])]
    exp_units = [str(u).lower() for u in (H.get("exp_units") or [])]
    linear_names = [str(n).lower() for n in (H.get("linear_names") or [])]
    exp_names = [str(n).lower() for n in (H.get("exp_names") or [])]
    SampC = (PLC.get("sampling", {}).get("continuous") or {})
    anchors_linear = SampC.get("linear") or [0.0, 0.5, 1.0]
    anchors_exp = SampC.get("exp") or [0.05, 0.5, 0.95]
    extra_anchors = SampC.get("fallback_extra") or [0.25, 0.75]

    learned_params: list[dict] = []
    for p in params:
        idx = int(p.get("index", 0)); name = str(p.get("name", f"Param {idx}"))
        vmin = float(p.get("min", 0.0)); vmax = float(p.get("max", 1.0))
        v0 = float(p.get("value", 0.0))
        span = vmax - vmin if vmax != vmin else 1.0
        unit_guess = parse_unit_from_display(str(p.get("display_value", "")))

        # Quick enum detection
        labels = set()
        for t in [0.0, 0.5, 1.0]:
            val = vmin + span * t
            udp_request({"op": "set_return_device_param", "return_index": ri, "device_index": di, "param_index": idx, "value": float(val)}, timeout=0.6)
            if delay: _t.sleep(delay)
            rd = udp_request({"op": "get_return_device_params", "return_index": ri, "device_index": di}, timeout=1.0)
            rparams = ((rd or {}).get("data") or {}).get("params") or []
            dp = next((rp for rp in rparams if int(rp.get("index", -1)) == idx), None)
            if dp is not None:
                labels.add(str(dp.get("display_value", "")))

        from re import search as _re_search
        numeric_count = sum(1 for lab in labels if _re_search(r"-?\d+(?:\.\d+)?", lab))
        is_enum = (len(labels) <= 6 and numeric_count < len(labels)) or (len(labels) <= 2)

        samples: list[dict] = []
        label_map: dict[str, float] | None = None
        fit = None
        unit = unit_guess
        if is_enum:
            # Ends + a mid probe
            seen = set()
            for t in [0.0, 0.5, 1.0]:
                val = vmin + span * t
                udp_request({"op": "set_return_device_param", "return_index": ri, "device_index": di, "param_index": idx, "value": float(val)}, timeout=0.6)
                if delay: _t.sleep(delay)
                rd = udp_request({"op": "get_return_device_params", "return_index": ri, "device_index": di}, timeout=1.0)
                rparams = ((rd or {}).get("data") or {}).get("params") or []
                dp = next((rp for rp in rparams if int(rp.get("index", -1)) == idx), None)
                if dp is None: continue
                disp = str(dp.get("display_value", ""))
                if disp in seen: continue
                seen.add(disp)
                samples.append({"value": float(val), "display": disp, "display_num": None})
            label_map = {}
            for s in samples:
                lab = str(s.get("display", ""))
                if lab not in label_map:
                    label_map[lab] = float(s.get("value", vmin))
        else:
            # Continuous quick anchors by heuristic
            nm = name.lower(); ustr = (unit_guess or "").lower()
            anchors = anchors_exp if (ustr in exp_units or any(k in nm for k in exp_names)) else anchors_linear
            def probe(tfrac: float):
                val = vmin + span * max(0.0, min(1.0, tfrac))
                udp_request({"op": "set_return_device_param", "return_index": ri, "device_index": di, "param_index": idx, "value": float(val)}, timeout=0.6)
                if delay: _t.sleep(delay)
                rd = udp_request({"op": "get_return_device_params", "return_index": ri, "device_index": di}, timeout=1.0)
                rparams = ((rd or {}).get("data") or {}).get("params") or []
                dp = next((rp for rp in rparams if int(rp.get("index", -1)) == idx), None)
                if dp is None: return
                disp = str(dp.get("display_value", ""))
                dnum = None
                try:
                    m = _re_search(r"-?\d+(?:\.\d+)?", disp)
                    if m: dnum = float(m.group(0))
                except Exception:
                    dnum = None
                samples.append({"value": float(val), "display": disp, "display_num": dnum})
            for t in anchors:
                probe(float(t))
            fit = fit_models(samples)
            if not fit or float(fit.get("r2", 0.0)) < r2_accept:
                for t in extra_anchors[:max_extra]:
                    probe(float(t))
                fit = fit_models(samples)

        # restore
        udp_request({"op": "set_return_device_param", "return_index": ri, "device_index": di, "param_index": idx, "value": float(v0)}, timeout=0.6)

        ctype, labels_list = classify_control_type(samples, vmin, vmax)
        gname, role, _m = group_role_for_device(dname, name)
        learned_params.append({
            "index": idx,
            "name": name,
            "min": vmin,
            "max": vmax,
            "samples": samples,
            "control_type": ctype,
            "unit": unit,
            "labels": labels_list,
            "label_map": label_map,
            "fit": fit if ctype == "continuous" else None,
            "group": gname,
            "role": role,
        })

    groups_meta = build_groups_from_params(learned_params, dname)
    device_type = detect_device_type(params, dname)
    local_ok = STORE.save_device_map_local(signature, {"name": dname, "device_type": device_type, "groups": groups_meta}, learned_params)
    fs_ok = STORE.save_device_map(signature, {"name": dname, "device_type": device_type, "groups": groups_meta}, learned_params)
    return {"ok": True, "signature": signature, "local_saved": local_ok, "saved": fs_ok, "param_count": len(learned_params)}


@app.post("/mappings/push_local")
def push_local_mappings(signature: Optional[str] = None) -> Dict[str, Any]:
    if signature:
        ok = STORE.push_local_to_firestore(signature)
        return {"ok": ok, "signature": signature, "backend": STORE.backend}
    count = STORE.push_all_local()
    return {"ok": True, "pushed": count, "backend": STORE.backend}


@app.post("/mappings/migrate_schema")
def migrate_mapping_schema(index: Optional[int] = None, device: Optional[int] = None, signature: Optional[str] = None) -> Dict[str, Any]:
    """Backfill control_type/unit/labels/groups on an existing map and save locally; also push to Firestore if available.

    Provide either (index, device) to compute signature from Live, or a signature directly.
    """
    if not signature:
        if index is None or device is None:
            raise HTTPException(400, "index_device_or_signature_required")
        signature = _compute_signature_for(int(index), int(device))
    data = STORE.get_device_map_local(signature)
    if not data and STORE.enabled:
        data = STORE.get_device_map(signature)
    if not data:
        return {"ok": False, "error": "map_not_found", "signature": signature}
    params = data.get("params") or []
    updated_params: list[dict] = []
    for p in params:
        name = str(p.get("name", ""))
        vmin = float(p.get("min", 0.0))
        vmax = float(p.get("max", 1.0))
        samples = p.get("samples") or []
        unit = p.get("unit") or (parse_unit_from_display(str(samples[0].get("display", ""))) if samples else None)
        ctype, labels = classify_control_type(samples, vmin, vmax)
        gname, role, _m = group_role_for_device(data.get("device_name"), name)
        label_map = p.get("label_map")
        if ctype in ("binary", "quantized") and not label_map:
            label_map = {}
            for s in samples:
                lab = str(s.get("display", ""))
                if lab not in label_map:
                    label_map[lab] = float(s.get("value", vmin))
        fit = p.get("fit") or (fit_models(samples) if ctype == "continuous" else None)
        p.update({
            "control_type": ctype,
            "unit": unit,
            "labels": labels,
            "label_map": label_map,
            "fit": fit,
            "group": gname,
            "role": role,
        })
        updated_params.append(p)
    groups_meta = build_groups_from_params(updated_params, data.get("device_name"))
    device_type = detect_device_type(updated_params, data.get("device_name"))
    ok_local = STORE.save_device_map_local(signature, {"name": data.get("device_name"), "device_type": device_type, "groups": groups_meta}, updated_params)
    ok_fs = STORE.save_device_map(signature, {"name": data.get("device_name"), "device_type": device_type, "groups": groups_meta}, updated_params)
    return {"ok": True, "signature": signature, "local_saved": ok_local, "firestore_saved": ok_fs, "updated_params": len(updated_params)}


def _compute_signature_for(index: int, device: int) -> str:
    devs = udp_request({"op": "get_return_devices", "return_index": int(index)}, timeout=1.0)
    devices = ((devs or {}).get("data") or {}).get("devices") or []
    dname = None
    for d in devices:
        if int(d.get("index", -1)) == int(device):
            dname = str(d.get("name", f"Device {device}"))
            break
    params_resp = udp_request({"op": "get_return_device_params", "return_index": int(index), "device_index": int(device)}, timeout=1.2)
    params = ((params_resp or {}).get("data") or {}).get("params") or []
    return make_device_signature(dname or f"Device {device}", params)


"""/mappings/fit moved to server.api.device_mapping"""


"""Preset endpoints moved to server.api.presets (removed legacy stubs)."""


class RefreshPresetBody(BaseModel):
    preset_id: str
    update_values_from_live: Optional[bool] = False
    return_index: Optional[int] = None
    device_index: Optional[int] = None
    fields_allowlist: Optional[list[str]] = None


# moved: /presets/refresh_metadata handled by server.api.presets
async def refresh_preset_metadata(body: RefreshPresetBody) -> Dict[str, Any]:
    """Regenerate preset metadata via LLM and optionally refresh values from live device.

    - Resolves preset by `preset_id` (e.g., reverb_arena_tail)
    - If `update_values_from_live` and indices provided, reads current param values
    - Calls LLM to generate metadata; merges selected fields
    - Saves back to storage and emits `preset_updated` SSE event
    """
    preset_id = body.preset_id.strip()
    preset = STORE.get_preset(preset_id)
    if not preset:
        raise HTTPException(status_code=404, detail=f"Preset not found: {preset_id}")

    device_type = preset.get("category") or preset.get("device_type") or "unknown"
    device_name = preset.get("name") or preset.get("device_name") or preset_id
    parameter_values = dict(preset.get("parameter_values") or {})

    # Optionally refresh parameter values (and display values) from live device
    if body.update_values_from_live and body.return_index is not None and body.device_index is not None:
        try:
            rd = udp_request({
                "op": "get_return_device_params",
                "return_index": int(body.return_index),
                "device_index": int(body.device_index),
            }, timeout=1.2)
            rparams = ((rd or {}).get("data") or {}).get("params") or []
            live_vals = {}
            live_disp = {}
            for p in rparams:
                nm = p.get("name")
                val = p.get("value")
                disp = p.get("display_value")
                if nm is not None and val is not None:
                    live_vals[str(nm)] = float(val)
                if nm is not None and disp is not None:
                    live_disp[str(nm)] = str(disp)
            if live_vals:
                parameter_values = live_vals
            if live_disp:
                # attach display values alongside normalized values
                preset["parameter_display_values"] = live_disp
        except Exception:
            # keep existing values if live read fails
            pass

    # Generate new metadata (with fallback handled inside the function)
    metadata = await generate_preset_metadata_llm(
        device_name=device_name,
        device_type=device_type,
        parameter_values=parameter_values,
        store=STORE,
    )

    # Allowed metadata keys to merge
    allowed_keys = {
        "description",
        "audio_engineering",
        "natural_language_controls",
        "warnings",
        "genre_tags",
        "subcategory",
    }
    if body.fields_allowlist:
        allowed_keys = allowed_keys.intersection({k for k in body.fields_allowlist})

    updates: Dict[str, Any] = {}
    if isinstance(metadata, dict):
        for k in allowed_keys:
            if k in metadata:
                updates[k] = metadata[k]

    # Apply updates to preset
    preset.update(updates)
    preset["parameter_values"] = parameter_values

    saved = STORE.save_preset(preset_id, preset, local_only=False)
    try:
        await broker.publish({
            "event": "preset_updated",
            "preset_id": preset_id,
            "device_type": device_type,
            "device_name": device_name,
            "updated_fields": list(updates.keys()),
        })
    except Exception:
        pass

    return {"ok": bool(saved), "preset_id": preset_id, "updated_fields": list(updates.keys()), "values_refreshed": bool(parameter_values)}


class ReturnParamByNameBody(BaseModel):
    return_ref: str  # e.g., "A", "0", or name substring
    device_ref: str  # device name substring
    param_ref: str   # parameter name substring (as shown by Live)
    target_display: Optional[str] = None  # e.g., "25 ms", "20%", "High"
    target_value: Optional[float] = None  # optional numeric y for continuous
    mode: Optional[str] = "absolute"


def _resolve_return_index(ref: str) -> int:
    # Try A/B/C → 0/1/2
    r = ref.strip().lower()
    if len(r) == 1 and r in "abcd":
        return ord(r) - ord('a')
    if r.isdigit():
        return int(r)
    # Fallback: scan names
    resp = udp_request({"op": "get_return_tracks"}, timeout=1.0)
    returns = ((resp or {}).get("data") or {}).get("returns") or []
    for rt in returns:
        nm = str(rt.get("name", "")).lower()
        if r in nm:
            return int(rt.get("index", 0))
    raise HTTPException(404, f"return_not_found:{ref}")


def _resolve_device_index(ri: int, ref: str) -> int:
    resp = udp_request({"op": "get_return_devices", "return_index": ri}, timeout=1.0)
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
    resp = udp_request({"op": "get_return_device_params", "return_index": ri, "device_index": di}, timeout=1.0)
    params = ((resp or {}).get("data") or {}).get("params") or []
    r = ref.strip().lower()
    if r.isdigit():
        return int(r)
    for p in params:
        nm = str(p.get("name", "")).lower()
        if r in nm:
            return int(p.get("index", 0))
    raise HTTPException(404, f"param_not_found:{ref}")


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
        # y = a*ln(x)+b -> x = exp((y-b)/a)
        x = math.exp((target_y - b)/a) if a != 0 else vmin
    elif ftype == "exp":
        # y = a * exp(b*x) -> x = ln(y/a) / b
        a = float(coeffs.get("a", 1.0))
        b = float(coeffs.get("b", 1.0))
        if target_y <= 0:
            x = vmin
        else:
            x = math.log(target_y / a) / b if (a != 0 and b != 0) else vmin
    else:
        # piecewise
        pts = fit.get("points") or []
        pts = sorted([(float(p.get("y")), float(p.get("x"))) for p in pts if p.get("x") is not None and p.get("y") is not None])
        if not pts:
            return vmin
        # find neighbors
        lo = None; hi = None
        for y, x in pts:
            if y <= target_y:
                lo = (y, x)
            if y >= target_y and hi is None:
                hi = (y, x)
        if lo and hi and hi[0] != lo[0]:
            # interpolate
            y1, x1 = lo; y2, x2 = hi
            tfrac = (target_y - y1) / (y2 - y1)
            x = x1 + tfrac * (x2 - x1)
        else:
            # clamp to nearest
            x = lo[1] if lo else hi[1]
    return max(vmin, min(vmax, float(x)))


def _parse_target_display(s: str) -> Optional[float]:
    try:
        import re
        m = re.search(r"-?\d+(?:\.\d+)?", str(s))
        if not m: return None
        return float(m.group(0))
    except Exception:
        return None


"""/op/return/param_by_name moved to server.api.ops"""
def set_return_param_by_name(body: ReturnParamByNameBody) -> Dict[str, Any]:
    # Resolve indices
    ri = _resolve_return_index(body.return_ref)
    di = _resolve_device_index(ri, body.device_ref)
    pi = _resolve_param_index(ri, di, body.param_ref)

    # Fetch current params and signature
    p_resp = udp_request({"op": "get_return_device_params", "return_index": ri, "device_index": di}, timeout=1.2)
    p_list = ((p_resp or {}).get("data") or {}).get("params") or []
    cur = next((p for p in p_list if int(p.get("index", -1)) == pi), None)
    if not cur:
        raise HTTPException(404, "param_state_not_found")
    vmin = float(cur.get("min", 0.0)); vmax = float(cur.get("max", 1.0))

    # Build signature and fetch learned map (Firestore then local)
    signature = _compute_signature_for(ri, di)
    mapping = STORE.get_device_map(signature) if STORE.enabled else None
    if not mapping:
        mapping = STORE.get_device_map_local(signature)
    # Fetch new device mapping (fits/labels) when available
    new_map = None
    try:
        new_map = STORE.get_device_mapping(signature) if STORE.enabled else None
    except Exception:
        new_map = None
    # Try exact param match by name (with alias normalization)
    param_name = str(cur.get("name", ""))
    learned = None
    canonical = None
    try:
        from shared.aliases import canonical_name  # type: ignore
        canonical = canonical_name(param_name)
    except Exception:
        canonical = param_name
    if mapping and isinstance(mapping.get("params"), list):
        for mp in mapping["params"]:
            mpn = str(mp.get("name", ""))
            if mpn.lower() == param_name.lower() or mpn.lower() == str(canonical or "").lower():
                learned = mp
                break

    # Determine target
    target_y = None
    label = None
    if body.target_display:
        y = _parse_target_display(body.target_display)
        if y is not None:
            target_y = y
        else:
            label = body.target_display.strip()
    elif body.target_value is not None:
        target_y = float(body.target_value)

    # Relative mode: interpret numeric as delta in display units
    if (body.mode or "absolute").lower() == "relative":
        try:
            cur_disp = str(cur.get("display_value", ""))
            cur_num = _parse_target_display(cur_disp)
            if cur_num is not None and target_y is not None:
                target_y = cur_num + float(target_y)
        except Exception:
            pass

    # Auto-enable group masters for dependents (except configured skips)
    # Prefer new_map.grouping when available, fallback to legacy learned mapping
    try:
        master_name: str | None = None
        skip_auto = False
        desired_val = None

        # NEW PATH: Use new_map.grouping if available
        if new_map and isinstance(new_map.get("grouping"), dict):
            grp = new_map.get("grouping") or {}
            skip_list = [str(x).lower() for x in (grp.get("skip_auto_enable") or [])]

            # Check if this param is a dependent
            deps_map = grp.get("dependents") or {}
            for dep_name, master_ref in deps_map.items():
                if str(dep_name).lower() == param_name.lower():
                    # Parse master_ref which can be "MasterName" or dict with name/active_when
                    if isinstance(master_ref, dict):
                        master_name = str(master_ref.get("name", ""))
                        desired_val = master_ref.get("active_when")
                    else:
                        master_name = str(master_ref)

                    # Check if this master should skip auto-enable
                    if master_name and any(master_name.lower() == s or s in master_name.lower() for s in skip_list):
                        skip_auto = True
                    break

        # LEGACY PATH: Use old learned mapping if new_map didn't provide grouping
        elif learned:
            role = (learned.get("role") or "").lower()
            gname = (learned.get("group") or "").lower()
            if role == "dependent" and gname not in ("global", "output"):
                # Load grouping rules for this device to determine the correct master
                dname = (mapping.get("device_name") or "").lower()
                PLC = get_param_learn_config()
                grp = PLC.get("grouping", {}) or {}
                match_key = None
                for key in grp.keys():
                    kl = str(key).lower()
                    if kl == "default":
                        continue
                    if kl in dname:
                        match_key = key
                        break
                rules = grp.get(match_key or "default") or {}
                # Respect per-device skip list (e.g., Freeze On)
                skip_list = [str(x).lower() for x in (rules.get("skip_auto_enable") or [])]
                if any(s in param_name.lower() for s in skip_list) or ("freeze" in param_name.lower()):
                    skip_auto = True

                if not skip_auto:
                    # First preference: config dependents mapping (exact or case-insensitive)
                    deps_map = rules.get("dependents") or {}
                    for dn, mn in deps_map.items():
                        if str(dn).lower() == param_name.lower():
                            master_name = str(mn)
                            break
                    # If master name uses alternatives (A|B|C), choose the first available in current params
                    if master_name and "|" in master_name:
                        alts = [s.strip() for s in master_name.split("|") if s.strip()]
                        chosen = None
                        for alt in alts:
                            if any(str(pp.get("name","" )).lower() == alt.lower() for pp in p_list):
                                chosen = alt
                                break
                        master_name = chosen or alts[0]

                    # Fallback: infer from stored groups metadata
                    if not master_name:
                        groups = (mapping.get("groups") or []) if mapping else []
                        for g in groups:
                            deps = [str(d.get("name","")) for d in (g.get("dependents") or [])]
                            if any(param_name.lower() == dn.lower() for dn in deps):
                                mref = g.get("master") or {}
                                master_name = str(mref.get("name")) if mref else None
                                break
                    # Last resort: construct "<Base> On" switch
                    if not master_name and " " in param_name:
                        master_name = param_name.rsplit(" ", 1)[0] + " On"

                    # Use per-dependent desired master value when provided
                    dm = rules.get("dependent_master_values") or {}
                    for k, v in dm.items():
                        if str(k).lower() == param_name.lower():
                            try:
                                desired_val = float(v)
                            except Exception:
                                desired_val = None
                            break

        # Actually enable the master if we found one
        if master_name and not skip_auto:
            for p in p_list:
                if str(p.get("name","")) .lower()== master_name.lower():
                    master_idx = int(p.get("index", 0))
                    mmin = float(p.get("min", 0.0)); mmax = float(p.get("max", 1.0))
                    # Binary toggles usually 0..1; prefer explicit desired_val else max/1.0
                    mval = desired_val if desired_val is not None else (mmax if mmax >= 1.0 else 1.0)
                    udp_request({"op": "set_return_device_param", "return_index": ri, "device_index": di, "param_index": master_idx, "value": float(mval)}, timeout=0.8)
                    break
    except Exception:
        pass

    # Compute candidate value in [vmin..vmax]
    x = vmin
    # Helper for binary/toggle mapping
    def _is_binary(ln: Optional[dict]) -> bool:
        if not ln:
            return False
        if str(ln.get("control_type","")) == "binary":
            return True
        # If learned shows two or fewer label samples, treat as binary
        labs = list({str(s.get("display","")) for s in (ln.get("samples") or []) if s.get("display") is not None})
        return len(labs) <= 2

    # Prefer new mapping for label/fit inversion when available
    pm_entry = None
    try:
        if new_map and isinstance(new_map.get("params_meta"), list):
            for pme in new_map["params_meta"]:
                if str(pme.get("name", "")).lower() == param_name.lower():
                    pm_entry = pme
                    break
    except Exception:
        pm_entry = None

    # For quantized params with numeric string labels (e.g., "0.0", "1.0"),
    # treat numeric target_y as a label lookup instead of a fit inversion
    if target_y is not None and not label and pm_entry:
        if str(pm_entry.get("control_type", "")).lower() == "quantized":
            lm = pm_entry.get("label_map") or {}
            # Check if this label_map has numeric string keys
            numeric_key_found = False
            for k in lm.keys():
                try:
                    float(str(k))
                    numeric_key_found = True
                    break
                except:
                    pass
            # If so, treat target_y as a label string
            if numeric_key_found:
                label = str(target_y) if target_y == int(target_y) else f"{target_y:.1f}"
                target_y = None

    # Handle explicit label via new mapping label_map
    handled_label = False
    if label and pm_entry:
        lm = pm_entry.get("label_map") or {}
        # label_map format: {"0": "Clean", "1": "Boost", ...} (number → label)
        for k, v in lm.items():
            try:
                if str(v).strip().lower() == label.lower():
                    x = max(vmin, min(vmax, float(k)))
                    handled_label = True
                    break
            except Exception:
                continue
        if not handled_label and str(pm_entry.get("control_type", "")).lower() == "binary":
            l = label.strip().lower()
            on_words = {"on","enable","enabled","true","1","yes"}
            off_words = {"off","disable","disabled","false","0","no"}
            if l in on_words:
                x = vmax if vmax >= 1.0 else 1.0
                handled_label = True
            elif l in off_words:
                x = vmin if vmin <= 0.0 else 0.0
                handled_label = True

    # Fallback: explicit label using legacy learned mapping samples
    if label and learned and not handled_label:
        # Try exact label match from samples
        found = False
        for s in learned.get("samples", []) or []:
            if str(s.get("display", "")).strip().lower() == label.lower():
                x = float(s.get("value", vmin))
                found = True
                break
        if not found and _is_binary(learned):
            l = label.strip().lower()
            on_words = {"on","enable","enabled","true","1","yes"}
            off_words = {"off","disable","disabled","false","0","no"}
            if l in on_words:
                x = vmax
            elif l in off_words:
                x = vmin
            else:
                # If label_map is present, try keys like "1.0"/"0.0"
                lm = learned.get("label_map") or {}
                for k, v in lm.items():
                    if str(k).strip().lower() == l:
                        x = float(v)
                        found = True
                        break
    elif target_y is not None and pm_entry and isinstance(pm_entry.get("fit"), dict):
        # Numeric target via new mapping fit inversion
        try:
            x = _invert_fit_to_value(pm_entry.get("fit") or {}, float(target_y), vmin, vmax)
        except Exception:
            pass
    elif target_y is not None and learned:
        # Use shared conversion for display->normalized when mapping is available
        try:
            from shared.param_convert import to_normalized  # type: ignore
            x = float(to_normalized(target_y, learned))
        except Exception:
            fit = learned.get("fit")
            if fit:
                x = _invert_fit_to_value(fit, target_y, vmin, vmax)
            else:
                # fallback: nearest sample
                best = None; bestd = 1e9
                for s in learned.get("samples", []) or []:
                    dy = s.get("display_num")
                    if dy is None: continue
                    d = abs(float(dy) - target_y)
                    if d < bestd:
                        bestd = d; best = s
                if best:
                    x = float(best.get("value", vmin))
        # If this is effectively binary, snap to edges based on threshold
        if _is_binary(learned):
            x = vmax if float(target_y) >= 0.5 else vmin

    # Send set + refine steps (up to 2)
    udp_request({"op": "set_return_device_param", "return_index": ri, "device_index": di, "param_index": pi, "value": float(x)}, timeout=1.0)
    # Readback
    rb = udp_request({"op": "get_return_device_params", "return_index": ri, "device_index": di}, timeout=1.0)
    rps = ((rb or {}).get("data") or {}).get("params") or []
    newp = next((p for p in rps if int(p.get("index", -1)) == pi), None)
    applied_disp = newp.get("display_value") if newp else None
    # Up to two corrective nudges if continuous and numeric target provided
    try:
        if learned and learned.get("control_type") == "continuous" and target_y is not None and newp is not None:
            fit = learned.get("fit")
            if fit:
                for _ in range(2):
                    actual_num = _parse_target_display(str(applied_disp))
                    if actual_num is None:
                        break
                    err = target_y - actual_num
                    # 2% relative threshold (or 1 unit when near zero)
                    thresh = 0.02 * (abs(target_y) if target_y != 0 else 1.0)
                    if abs(err) <= thresh:
                        break
                    x2 = _invert_fit_to_value(fit, target_y, vmin, vmax)
                    if abs(x2 - x) <= 1e-6:
                        # fallback: nearest sample by display_num
                        best = None; bestd = 1e9
                        for s in learned.get("samples", []) or []:
                            dy = s.get("display_num")
                            if dy is None: continue
                            d = abs(float(dy) - target_y)
                            if d < bestd:
                                bestd = d; best = s
                        if best:
                            x2 = float(best.get("value", vmin))
                        else:
                            # last resort: proportional nudge in x space
                            direction = -1.0 if err < 0 else 1.0  # if actual > target, decrease x
                            step = 0.1 * (vmax - vmin)
                            x2 = max(vmin, min(vmax, x + direction * step))
                    udp_request({"op": "set_return_device_param", "return_index": ri, "device_index": di, "param_index": pi, "value": float(x2)}, timeout=1.0)
                    x = x2
                    rb2 = udp_request({"op": "get_return_device_params", "return_index": ri, "device_index": di}, timeout=1.0)
                    rps2 = ((rb2 or {}).get("data") or {}).get("params") or []
                    newp = next((p for p in rps2 if int(p.get("index", -1)) == pi), None)
                    applied_disp = newp.get("display_value") if newp else applied_disp
            # If still not within threshold, attempt a brief monotonic bisection on x
            actual_num2 = _parse_target_display(str(applied_disp))
            if actual_num2 is not None:
                err2 = target_y - actual_num2
                thresh2 = 0.02 * (abs(target_y) if target_y != 0 else 1.0)
                if abs(err2) > thresh2:
                    lo = vmin; hi = vmax; curx = x
                    # Initialize bounds by nudging one side based on error direction
                    if err2 < 0:  # actual > target -> decrease x
                        hi = curx
                    else:
                        lo = curx
                    for _ in range(8):
                        mid = (lo + hi) / 2.0
                        udp_request({"op": "set_return_device_param", "return_index": ri, "device_index": di, "param_index": pi, "value": float(mid)}, timeout=1.0)
                        rb3 = udp_request({"op": "get_return_device_params", "return_index": ri, "device_index": di}, timeout=1.0)
                        rps3 = ((rb3 or {}).get("data") or {}).get("params") or []
                        newp3 = next((p for p in rps3 if int(p.get("index", -1)) == pi), None)
                        applied_disp = newp3.get("display_value") if newp3 else applied_disp
                        act = _parse_target_display(str(applied_disp))
                        if act is None:
                            break
                        if abs(act - target_y) <= thresh2:
                            x = mid
                            break
                        if act > target_y:
                            hi = mid
                        else:
                            lo = mid
                        x = mid
    except Exception:
        pass
    return {"ok": True, "signature": signature, "applied": {"value": x, "display": applied_disp}}


@app.get("/return/device/learn_status")
def learn_return_device_status(id: str) -> Dict[str, Any]:
    if str(os.getenv("FB_DEBUG_LEGACY_LEARN", "")).lower() not in ("1", "true", "yes", "on"):
        raise HTTPException(404, "legacy_disabled")
    job = LEARN_JOBS.get(id)
    if not job:
        return {"ok": False, "error": "unknown_job"}
    return {"ok": True, **job}


"""/op/mixer moved to server.api.ops"""
def op_mixer(op: MixerOp) -> Dict[str, Any]:
    ...


"""/op/send moved to server.api.ops"""
def op_send(op: SendOp) -> Dict[str, Any]:
    ...


"""/op/device/param moved to server.api.ops"""
def op_device_param(op: DeviceParamOp) -> Dict[str, Any]:
    ...


"""/op/volume_db moved to server.api.ops"""
def op_volume_db(body: VolumeDbBody) -> Dict[str, Any]:
    ...


"""/op/select_track moved to server.api.ops"""
def op_select_track(body: SelectTrackBody) -> Dict[str, Any]:
    ...


@app.post("/chat")
def chat(body: ChatBody) -> Dict[str, Any]:
    return handle_chat(body)


@app.post("/help")
def help_endpoint(body: HelpBody) -> Dict[str, Any]:
    return handle_help(body)


@app.post("/intent/parse")
def intent_parse(body: IntentParseBody) -> Dict[str, Any]:
    """Parse NL text to canonical intent JSON (no execution)."""
    import sys
    import pathlib
    nlp_dir = pathlib.Path(__file__).resolve().parent.parent / "nlp-service"
    if nlp_dir.exists() and str(nlp_dir) not in sys.path:
        sys.path.insert(0, str(nlp_dir))
    try:
        from llm_daw import interpret_daw_command  # type: ignore
    except Exception as e:
        raise HTTPException(500, f"NLP module not available: {e}")

    raw_intent = interpret_daw_command(body.text, model_preference=body.model, strict=body.strict)

    canonical, errors = map_llm_to_canonical(raw_intent)
    if canonical is None:
        # Attempt to provide clarifying choices from snapshot
        try:
            ov = request_op("get_overview", timeout=1.0) or {}
            data = (ov.get("data") or ov) if isinstance(ov, dict) else ov
            tracks = data.get("tracks") or []
            rs = request_op("get_return_tracks", timeout=1.0) or {}
            rdata = (rs.get("data") or rs) if isinstance(rs, dict) else rs
            rets = rdata.get("returns") or []
            question = "Which track or return do you mean?"
            choices = {
                "tracks": [{"index": int(t.get("index",0)), "name": t.get("name") } for t in tracks],
                "returns": [{"index": int(r.get("index",0)), "name": r.get("name"), "letter": chr(ord('A')+int(r.get("index",0))) } for r in rets],
            }
            clar = {"intent": "clarification_needed", "question": question, "choices": choices, "context": body.context}
            return {"ok": False, "errors": errors, "raw_intent": clar}
        except Exception:
            return {"ok": False, "errors": errors, "raw_intent": raw_intent}

    return {"ok": True, "intent": canonical, "raw_intent": raw_intent}
class SelectTrackBody(BaseModel):
    track_index: int
def _debug_enabled(name: str) -> bool:
    try:
        if name == "sse":
            env = str(os.getenv("FB_DEBUG_SSE", "")).lower() in ("1","true","yes","on")
            cfg = get_debug_settings().get("sse", False)
            return bool(env or cfg)
        if name == "auto_capture":
            env = str(os.getenv("FB_DEBUG_AUTO_CAPTURE", "")).lower() in ("1","true","yes","on")
            cfg = get_debug_settings().get("auto_capture", False)
            return bool(env or cfg)
    except Exception:
        return False
    return False



@app.on_event("startup")
async def _ableton_startup_listener() -> None:
    start_ableton_event_listener()
    schedule_live_index_tasks()
