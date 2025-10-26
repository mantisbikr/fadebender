from __future__ import annotations
import os
from typing import Any, Dict, Optional
import time
import asyncio
from fastapi.responses import StreamingResponse
import json
import socket
import threading

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from server.services.ableton_client import request_op
from server.models.ops import MixerOp, SendOp, DeviceParamOp
from server.services.knowledge import search_knowledge
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
from server.cloud.enrich_queue import enqueue_preset_enrich
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


# --- Simple safety state: undo + rate limiting ---
UNDO_STACK: list[Dict[str, Any]] = []
REDO_STACK: list[Dict[str, Any]] = []
# Cache last known non-zero Dry/Wet (or Mix) value per return device for bypass restore
DEVICE_BYPASS_CACHE: dict[tuple[int, int], float] = {}
LAST_SENT: Dict[str, float] = {}
LAST_TS: Dict[str, float] = {}
MIN_INTERVAL_SEC = 0.05  # 50ms per target key

def _key(field: str, track_index: int) -> str:
    return f"mixer:{field}:{track_index}"

def _rate_limited(field: str, track_index: int) -> bool:
    k = _key(field, track_index)
    now = time.time()
    last = LAST_TS.get(k, 0.0)
    if now - last < MIN_INTERVAL_SEC:
        return True
    LAST_TS[k] = now
    return False

# --- Simple SSE event broker ---
STORE = MappingStore()
set_store_instance(STORE)
LEARN_JOBS: dict[str, dict] = {}
BACKFILL_JOBS: dict[str, dict] = {}

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

def _get_prev_mixer_value(track_index: int, field: str) -> Optional[float]:
    """Try to read previous mixer value from Ableton (if bridge supports it)."""
    try:
        resp = request_op("get_track_status", timeout=0.4, track_index=int(track_index))
        if not resp:
            return None
        data = resp.get("data") or resp
        mixer = data.get("mixer") if isinstance(data, dict) else None
        if not mixer:
            return None
        val = mixer.get(field)
        if val is None:
            return None
        return float(val)
    except Exception:
        return None


class ChatBody(BaseModel):
    text: str
    confirm: bool = True
    model: Optional[str] = None  # e.g., 'gemini-2.5-flash' or 'llama'
    strict: Optional[bool] = None


class HelpBody(BaseModel):
    query: str
    context: Optional[Dict[str, Any]] = None


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


# ==================== Preset Metadata Backfill ====================

class BackfillBody(BaseModel):
    device_type: Optional[str] = None
    preset_type: Optional[str] = None  # stock | user
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


@app.post("/presets/backfill_metadata")
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

    # Snapshot list of presets to process
    presets = STORE.list_presets(device_type=device_type, structure_signature=signature, preset_type=preset_type)
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
                        preset = STORE.get_preset(pid) or {}
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
                            store=STORE,
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
                            ok = STORE.save_preset(pid, preset, local_only=False)
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


@app.post("/presets/backfill_ids")
async def backfill_preset_metadata_by_ids(body: BackfillIdsBody) -> Dict[str, Any]:
    ids = [str(x).strip() for x in (body.preset_ids or []) if str(x).strip()]
    if not ids:
        raise HTTPException(400, "no_preset_ids")
    fields_allow = list(body.fields_allowlist or [])
    dry_run = bool(body.dry_run)
    job_id = f"bf_ids_{int(time.time())}_{len(ids)}"
    BACKFILL_JOBS[job_id] = {"state": "queued", "total": len(ids), "completed": 0, "updated": 0, "skipped": 0, "errors": 0}

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
                    preset = STORE.get_preset(pid) or {}
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
                        store=STORE,
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
                        ok = STORE.save_preset(pid, preset, local_only=False)
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
    # Import llm_daw from nlp-service/ dynamically (folder has a hyphen)
    import sys
    import pathlib
    nlp_dir = pathlib.Path(__file__).resolve().parent.parent / "nlp-service"
    if nlp_dir.exists() and str(nlp_dir) not in sys.path:
        sys.path.insert(0, str(nlp_dir))
    text_lc = body.text.strip()
    # Normalize variants like "-10db" → "-10 dB" to make regex matching robust
    import re
    text_norm = re.sub(r'(-?\d+(?:\.\d+)?)(?:db|dB)\b', r'\1 dB', text_lc, flags=re.I)
    # Pre-parse common direct commands to avoid LLM ambiguity
    m = re.search(r"\b(mute|unmute|solo|unsolo)\s+track\s+(\d+)\b", text_norm, flags=re.I)
    if m:
        action = m.group(1).lower()
        track_index = int(m.group(2))
        field = 'mute' if 'mute' in action else 'solo'
        value = 0 if action in ('unmute', 'unsolo') else 1
        msg = {"op": "set_mixer", "track_index": track_index, "field": field, "value": value}
        if not body.confirm:
            return {"ok": True, "preview": msg, "summary": f"{action.title()} Track {track_index}"}
        resp = udp_request(msg, timeout=1.0)
        return {"ok": bool(resp and resp.get("ok", True)), "resp": resp, "summary": f"{action.title()} Track {track_index}"}

    # Parse volume commands using helper function
    volume_cmd = parse_volume_command(text_norm)
    if volume_cmd:
        track_index = volume_cmd["track_index"]
        target = volume_cmd["db_value"]
        float_value = volume_cmd["live_float"]
        warn = volume_cmd["warning"]


        msg = {"op": "set_mixer", "track_index": track_index, "field": "volume", "value": float_value}
        if not body.confirm:
            return {"ok": True, "preview": msg, "summary": f"Set Track {track_index} volume to {target:g} dB" + (" (warning: >0 dB may clip)" if warn else "")}
        resp = udp_request(msg, timeout=1.0)
        # Publish SSE so UI tooltips/details refresh immediately
        try:
            schedule_emit({"event": "mixer_changed", "track": track_index, "field": "volume"})
        except Exception:
            pass
        # Add capabilities for mixer operations
        try:
            from server.api.cap_utils import ensure_capabilities
            resp = ensure_capabilities(resp, domain="track", track_index=track_index)
        except Exception:
            pass
        summ = f"Set Track {track_index} volume to {target:g} dB"
        if warn:
            summ += " (warning: >0 dB may clip)"
        # Extract capabilities to top level for consistency
        result = {"ok": bool(resp and resp.get("ok", True)), "resp": resp, "summary": summ}
        if isinstance(resp, dict) and "data" in resp and "capabilities" in resp.get("data", {}):
            result["data"] = resp["data"]
        return result

    # --- Send controls ---
    # Absolute: set track N send <idx|name> to X [dB|%]
    m = re.search(r"\bset\s+track\s+(\d+)\s+(?:send\s+)?([\w\s]+?)\s+to\s+(-?\d+(?:\.\d+)?)\s*(db|dB|%|percent|percentage)?\b", text_norm, flags=re.I)
    if m:
        track_index = int(m.group(1))
        send_label = (m.group(2) or '').strip()
        raw_val = float(m.group(3))
        unit = (m.group(4) or '').lower()
        # Resolve send index by label (A/B/0/1 or name)
        si = None
        sl = send_label.lower()
        if sl in ('a','b','c','d'):
            si = ord(sl) - ord('a')
        elif sl.isdigit():
            si = int(sl)
        else:
            try:
                ts = udp_request({"op": "get_track_sends", "track_index": track_index}, timeout=0.8)
                sends = ((ts or {}).get('data') or {}).get('sends') or []
                for s in sends:
                    nm = str(s.get('name','')).strip().lower()
                    if nm and sl in nm:
                        si = int(s.get('index', 0))
                        break
            except Exception:
                pass
        if si is None:
            # Fallback alias mapping from config
            aliases = get_send_aliases()
            if sl in aliases:
                si = int(aliases[sl])
        if si is None:
            raise HTTPException(400, f"unknown_send:{send_label}")
        # Compute target float
        if unit in ('%','percent','percentage'):
            target_float = max(0.0, min(1.0, raw_val / 100.0))
        else:
            target_db = max(-60.0, min(6.0, raw_val))
            target_float = db_to_live_float_send(target_db)
        msg = {"op": "set_send", "track_index": track_index, "send_index": si, "value": round(float(target_float), 6)}
        if not body.confirm:
            return {"ok": True, "preview": msg, "summary": f"Set Track {track_index} send {send_label} to {raw_val:g}{' ' + (unit or 'dB') if unit else ' dB'}"}
        resp = udp_request(msg, timeout=1.0)
        try:
            schedule_emit({"event": "send_changed", "track": track_index, "send_index": si})
        except Exception:
            pass
        return {"ok": bool(resp and resp.get('ok', True)), "resp": resp, "summary": f"Set Track {track_index} send {send_label} to {raw_val:g}{' ' + (unit or 'dB') if unit else ' dB'}"}

    # Relative: increase/decrease send <name> on track N by X [dB|%]
    m = re.search(r"\b(increase|decrease|reduce|lower|raise)\s+(?:send\s+)?([\w\s]+?)\s+(?:on|for)?\s*track\s+(\d+)\s+by\s+(\d+(?:\.\d+)?)\s*(db|dB|%|percent|percentage)?\b", text_norm, flags=re.I)
    if m:
        action = m.group(1).lower()
        send_label = (m.group(2) or '').strip()
        track_index = int(m.group(3))
        amt = float(m.group(4))
        unit = (m.group(5) or '').lower()
        delta_sign = -1.0 if action in ('decrease','reduce','lower') else 1.0
        # Resolve send index
        si = None
        sl = send_label.lower()
        if sl in ('a','b','c','d'):
            si = ord(sl) - ord('a')
        elif sl.isdigit():
            si = int(sl)
        else:
            try:
                ts = udp_request({"op": "get_track_sends", "track_index": track_index}, timeout=0.8)
                sends = ((ts or {}).get('data') or {}).get('sends') or []
                for s in sends:
                    nm = str(s.get('name','')).strip().lower()
                    if nm and sl in nm:
                        si = int(s.get('index', 0))
                        break
            except Exception:
                pass
        if si is None:
            aliases = get_send_aliases()
            if sl in aliases:
                si = int(aliases[sl])
        if si is None:
            raise HTTPException(400, f"unknown_send:{send_label}")
        # Read current
        cur = 0.0
        try:
            ts = udp_request({"op": "get_track_sends", "track_index": track_index}, timeout=0.8)
            sends = ((ts or {}).get('data') or {}).get('sends') or []
            for s in sends:
                if int(s.get('index', -1)) == si:
                    cur = float(s.get('value', 0.0))
                    break
        except Exception:
            pass
        if unit in ('%','percent','percentage'):
            target_float = max(0.0, min(1.0, cur + delta_sign * (amt/100.0)))
        else:
            cur_db = live_float_to_db_send(cur)
            target_db = max(-60.0, min(6.0, cur_db + delta_sign * amt))
            target_float = db_to_live_float_send(target_db)
        msg = {"op": "set_send", "track_index": track_index, "send_index": si, "value": round(float(target_float), 6)}
        if not body.confirm:
            return {"ok": True, "preview": msg, "summary": f"{action.title()} Track {track_index} send {send_label} by {amt:g}{' ' + (unit or 'dB') if unit else ' dB'}"}
        resp = udp_request(msg, timeout=1.0)
        try:
            schedule_emit({"event": "send_changed", "track": track_index, "send_index": si})
        except Exception:
            pass
        return {"ok": bool(resp and resp.get('ok', True)), "resp": resp, "summary": f"{action.title()} Track {track_index} send {send_label} by {amt:g}{' ' + (unit or 'dB') if unit else ' dB'}"}

    # Pan Live-style inputs like '25L'/'25R' (floats allowed)
    m = re.search(r"\bset\s+track\s+(\d+)\s+pan\s+to\s+((?:\d{1,2}(?:\.\d+)?)|50(?:\.0+)?)\s*([lLrR])\b", text_norm)
    if m:
        track_index = int(m.group(1))
        amt = float(m.group(2))
        side = m.group(3).lower()
        pan = (-amt if side == 'l' else amt) / 50.0
        msg = {"op": "set_mixer", "track_index": track_index, "field": "pan", "value": round(pan, 4)}
        label = f"{amt}{'L' if side=='l' else 'R'}"
        if not body.confirm:
            return {"ok": True, "preview": msg, "summary": f"Set Track {track_index} pan to {label}"}
        resp = udp_request(msg, timeout=1.0)
        try:
            schedule_emit({"event": "mixer_changed", "track": track_index, "field": "pan"})
        except Exception:
            pass
        return {"ok": bool(resp and resp.get("ok", True)), "resp": resp, "summary": f"Set Track {track_index} pan to {label}"}

    # Pan absolute numeric -50..50 (floats)
    m = re.search(r"\bset\s+track\s+(\d+)\s+pan\s+to\s+(-?\d+(?:\.\d+)?)\b", text_norm)
    if m:
        track_index = int(m.group(1))
        val = float(m.group(2))
        val = max(-50.0, min(50.0, val))
        pan = val / 50.0
        msg = {"op": "set_mixer", "track_index": track_index, "field": "pan", "value": round(pan, 4)}
        label = f"{int(abs(val))}{'L' if val < 0 else ('R' if val > 0 else '')}"
        if not body.confirm:
            return {"ok": True, "preview": msg, "summary": f"Set Track {track_index} pan to {label}"}
        resp = udp_request(msg, timeout=1.0)
        try:
            schedule_emit({"event": "mixer_changed", "track": track_index, "field": "pan"})
        except Exception:
            pass
        return {"ok": bool(resp and resp.get("ok", True)), "resp": resp, "summary": f"Set Track {track_index} pan to {label}"}

    try:
        from llm_daw import interpret_daw_command  # type: ignore
    except Exception as e:
        raise HTTPException(500, f"NLP module not available: {e}")

    intent = interpret_daw_command(text_lc, model_preference=body.model, strict=body.strict)

    # Transform NLP intent to canonical format (like /intent/parse does)
    from server.services.intent_mapper import map_llm_to_canonical
    canonical, errors = map_llm_to_canonical(intent)

    # If we got a valid canonical intent, execute it directly
    if canonical and body.confirm:
        try:
            from server.api.intents import execute_intent as exec_canonical
            from server.models.intents_api import CanonicalIntent
            # Convert dict to Pydantic model
            canonical_intent = CanonicalIntent(**canonical)
            result = exec_canonical(canonical_intent, debug=False)
            # Return with the raw NLP intent for transparency
            return {
                "ok": result.get("ok", True),
                "intent": intent,
                "canonical": canonical,
                "summary": result.get("summary", "Command executed"),
                **result
            }
        except HTTPException as he:
            # Return error with intent for debugging
            return {
                "ok": False,
                "reason": "http_error",
                "intent": intent,
                "canonical": canonical,
                "summary": f"Error: {he.detail}",
                "error": str(he.detail)
            }
        except Exception as e:
            return {
                "ok": False,
                "reason": "execution_error",
                "intent": intent,
                "canonical": canonical,
                "summary": f"Error: {str(e)}",
                "error": str(e)
            }

    # Handle help-style responses inline by consulting knowledge base
    if intent.get("intent") == "question_response":
        from server.services.knowledge import search_knowledge
        q = intent.get("meta", {}).get("utterance") or body.text
        matches = search_knowledge(q)
        snippets: list[str] = []
        sources: list[Dict[str, str]] = []
        for src, title, body_text in matches:
            sources.append({"source": src, "title": title})
            snippets.append(f"{title}:\n" + body_text)
        answer = "\n\n".join(snippets[:2]) if snippets else "Here are general tips: increase the track volume slightly, apply gentle compression (2–4 dB GR), and cut muddiness around 200–400 Hz."
        suggested = [
            "increase track 1 volume by 3 dB",
            "set track 1 volume to -6 dB",
            "reduce compressor threshold on track 1 by 3 dB",
        ]
        return {"ok": False, "summary": answer, "answer": answer, "suggested_intents": suggested, "sources": sources, "intent": intent}

    # Auto-exec transport intents
    if intent.get("intent") == "transport":
        op = intent.get("operation") or {}
        action = str(op.get("action", ""))
        value = op.get("value")
        msg = {"op": "set_transport", "action": action}
        if value is not None:
            try:
                msg["value"] = float(value)
            except Exception:
                pass
        summary = f"Transport: {action}{(' ' + str(value)) if value is not None else ''}"
        if not body.confirm:
            return {"ok": True, "preview": msg, "intent": intent, "summary": summary}
        resp = udp_request(msg, timeout=1.0)
        try:
            schedule_emit({"event": "transport_changed", "action": action})
        except Exception:
            pass
        return {"ok": bool(resp and resp.get("ok", True)), "resp": resp, "intent": intent, "summary": summary}

    # Very small mapper for MVP: support volume absolute set if provided
    targets = intent.get("targets") or []
    op = intent.get("operation") or {}
    param = None
    if targets:
        param = (targets[0] or {}).get("parameter")
    track_index: Optional[int] = None
    if targets and targets[0].get("track"):
        try:
            label = targets[0]["track"]  # e.g., "Track 2"
            track_index = int(str(label).split()[-1])
        except Exception:
            track_index = None

    if intent.get("intent") == "set_parameter" and param == "volume" and track_index is not None and op.get("type") == "absolute":
        val = float(op.get("value", 0))
        float_value = db_to_live_float(val)
        msg = {"op": "set_mixer", "track_index": track_index, "field": "volume", "value": float_value}
        summary = f"Set Track {track_index} volume to {val:g} dB (target)"
        if not body.confirm:
            return {"ok": True, "preview": msg, "intent": intent, "summary": summary}
        # Rate limit
        if _rate_limited("volume", track_index):
            return {"ok": False, "reason": "rate_limited", "intent": intent, "summary": summary}
        # Prepare undo entry
        k = _key("volume", track_index)
        prev = _get_prev_mixer_value(track_index, "volume")
        if prev is None:
            prev = LAST_SENT.get(k)
        if prev is None:
            # Default previous volume to mid (0.5) when unknown (useful with UDP stub)
            prev = 0.5
        resp = udp_request(msg, timeout=1.0)
        if resp and resp.get("ok", True):
            # We cannot know the exact normalized value here; store None and rely on readback for undo if needed
            UNDO_STACK.append({"key": k, "field": "volume", "track_index": track_index, "prev": prev, "new": None})
            REDO_STACK.clear()
            # Readback to cache LAST_SENT
            try:
                ts = udp_request({"op": "get_track_status", "track_index": track_index}, timeout=0.6)
                data = (ts or {}).get("data") or {}
                nv = data.get("mixer", {}).get("volume")
                if nv is not None:
                    LAST_SENT[k] = float(nv)
                # Prefer display dB from status if present
                vdb = data.get("volume_db")
                if isinstance(vdb, (int, float)):
                    summary = f"Set Track {track_index} volume to {float(vdb):.1f} dB"
            except Exception:
                pass
            # If bridge reported achieved_db, surface it
            achieved = resp.get("achieved_db") if isinstance(resp, dict) else None
            if achieved is not None:
                summary = f"Set Track {track_index} volume to {float(achieved):.1f} dB"
            # Publish SSE for freshness
            try:
                asyncio.create_task(broker.publish({"event": "mixer_changed", "track": track_index, "field": "volume"}))
            except Exception:
                pass
            return {"ok": True, "preview": msg, "resp": resp, "intent": intent, "summary": summary}
        # Fallback to linear mapping if precise op failed
        norm = (max(-60.0, min(6.0, val)) + 60.0) / 66.0
        fallback_msg = {"op": "set_mixer", "track_index": track_index, "field": "volume", "value": round(norm, 4)}
        fb_resp = udp_request(fallback_msg, timeout=1.0)
        ok = bool(fb_resp and fb_resp.get("ok", True))
        if ok:
            UNDO_STACK.append({"key": k, "field": "volume", "track_index": track_index, "prev": prev, "new": fallback_msg["value"]})
            REDO_STACK.clear()
            LAST_SENT[k] = fallback_msg["value"]
        return {"ok": ok, "preview": fallback_msg, "resp": fb_resp, "intent": intent, "summary": summary + (" (fallback)" if ok else "")}

    # New: pan absolute set
    if intent.get("intent") == "set_parameter" and param == "pan" and track_index is not None and op.get("type") == "absolute":
        # Accept % (-100..100) or direct -1..1; map user % to Live's scale where 50L/R == 1.0/-1.0
        raw_val = float(op.get("value", 0))
        unit = str(op.get("unit") or "").strip().lower()
        if unit in ("%", "percent", "percentage"):
            # User expects -50% to show 50L in Live => map percent to [-1..1] with 50 -> 1.0
            pan = max(-50.0, min(50.0, raw_val)) / 50.0
        else:
            # Heuristic: values beyond 1 likely percent
            pan = (raw_val / 50.0) if abs(raw_val) > 1.0 else raw_val
        pan = max(-1.0, min(1.0, pan))
        msg = {"op": "set_mixer", "track_index": track_index, "field": "pan", "value": round(pan, 4)}
        # Live displays 50L/50R at extremes; compute label accordingly
        label = f"{int(abs(pan)*50)}" + ("L" if pan < 0 else ("R" if pan > 0 else ""))
        summary = f"Set Track {track_index} pan to {label}"
        if not body.confirm:
            return {"ok": True, "preview": msg, "intent": intent, "summary": summary}
        if _rate_limited("pan", track_index):
            return {"ok": False, "reason": "rate_limited", "intent": intent, "summary": summary}
        k = _key("pan", track_index)
        prev = _get_prev_mixer_value(track_index, "pan")
        if prev is None:
            prev = LAST_SENT.get(k)
        if prev is None:
            # Default previous pan to center when unknown
            prev = 0.0
        resp = udp_request(msg, timeout=1.0)
        if resp and resp.get("ok", True):
            UNDO_STACK.append({"key": k, "field": "pan", "track_index": track_index, "prev": prev, "new": msg["value"]})
            REDO_STACK.clear()
            LAST_SENT[k] = msg["value"]
        return {"ok": bool(resp and resp.get("ok", True)), "preview": msg, "resp": resp, "intent": intent, "summary": summary}

    # Device parameter control (returns only for now)
    if intent.get("intent") == "set_parameter":
        targets = intent.get("targets") or []
        if targets:
            target = targets[0]

            # LLM generates "track": "Return A" not "return": "A"
            # Handle both formats
            track_ref = target.get("track") or target.get("return")
            device_ref = target.get("plugin") or target.get("device")
            param_name = target.get("parameter")

            # Check if this is a return track (starts with "Return")
            is_return = isinstance(track_ref, str) and track_ref.strip().upper().startswith("RETURN")

            if is_return:
                # Extract return device parameter intent
                op = intent.get("operation") or {}
                value = op.get("value")
                unit = op.get("unit")

                # Parse return index from "Return A" or "A"
                return_index = None
                if isinstance(track_ref, str):
                    letter = track_ref.strip().upper().replace("RETURN", "").strip()
                    if len(letter) == 1 and 'A' <= letter <= 'Z':
                        return_index = ord(letter) - ord('A')

                if return_index is None or param_name is None:
                    # Can't auto-execute without return and param
                    return {
                        "ok": False,
                        "reason": "incomplete_device_intent",
                        "intent": intent,
                        "summary": "I need a return track letter and parameter name to proceed."
                    }

                # Get devices to find device_index
                try:
                    from server.api.intents import execute_intent as exec_canonical
                    from server.api.intents import CanonicalIntent

                    # Build canonical intent for device parameter, carry device hints if available
                    device_name_hint = None
                    device_ordinal_hint = None
                    try:
                        if device_ref:
                            dev_l = str(device_ref).strip().lower()
                            if dev_l not in ("device", "fx", "effect", "plugin"):
                                device_name_hint = str(device_ref)
                        ord_val = target.get("device_ordinal")
                        if ord_val is not None:
                            device_ordinal_hint = int(ord_val)
                    except Exception:
                        pass

                    canonical = CanonicalIntent(
                        domain="device",
                        return_index=return_index,
                        device_index=0,  # default; execute_intent will resolve using hints when present
                        param_ref=param_name,
                        display=str(value) if value is not None and isinstance(value, str) else None,
                        value=(None if isinstance(value, str) else value),
                        unit=unit,
                        device_name_hint=device_name_hint,
                        device_ordinal_hint=device_ordinal_hint,
                        dry_run=not body.confirm
                    )

                    # Execute the intent
                    result = exec_canonical(canonical)

                    if not result.get("ok"):
                        return {
                            "ok": False,
                            "reason": "execution_failed",
                            "intent": intent,
                            "summary": result.get("summary") or "Failed to set parameter",
                            "error": result.get("error")
                        }

                    summary = result.get("summary") or f"Set {param_name}"

                    # Prefer capabilities attached by exec_canonical; fetch only if missing
                    capabilities = None
                    try:
                        if isinstance(result, dict):
                            capabilities = ((result.get("data") or {}) or {}).get("capabilities")
                    except Exception:
                        capabilities = None
                    # Do not fetch fallback capabilities with device=0; rely on execute response

                    return {
                        "ok": True,
                        "summary": summary,
                        "intent": intent,
                        "data": {"capabilities": capabilities} if capabilities else {}
                    }

                except HTTPException as he:
                    return {
                        "ok": False,
                        "reason": "http_error",
                        "intent": intent,
                        "summary": f"Error: {he.detail}",
                        "error": str(he.detail)
                    }
                except Exception as e:
                    print(f"[CHAT] Device parameter execution error: {e}")
                    import traceback
                    traceback.print_exc()
                    return {
                        "ok": False,
                        "reason": "execution_error",
                        "intent": intent,
                        "summary": f"Error executing command: {str(e)}",
                        "error": str(e)
                    }

    # Auto-execute Return mixer (volume/pan/mute/solo) and sends using CanonicalIntent
    try:
        if intent.get("intent") == "set_parameter":
            targets = intent.get("targets") or []
            if targets:
                target = targets[0] or {}
                track_ref = target.get("track") or target.get("return")
                plugin = target.get("plugin")
                param_name = (target.get("parameter") or "").strip().lower()
                if isinstance(track_ref, str) and track_ref.strip().lower().startswith("return ") and not plugin:
                    from server.api.intents import execute_intent as exec_canonical
                    from server.api.intents import CanonicalIntent
                    letter = track_ref.strip().split()[-1].upper()
                    op = intent.get("operation") or {}
                    # Send detection
                    import re as _re
                    m = _re.search(r"\bsend\s*([a-d])\b", param_name)
                    if m:
                        send_ref = m.group(1).upper()
                        canonical = CanonicalIntent(
                            domain="return",
                            return_ref=letter,
                            field="send",
                            send_ref=send_ref,
                            value=op.get("value"),
                            unit=op.get("unit"),
                            dry_run=not body.confirm,
                        )
                    else:
                        canonical = CanonicalIntent(
                            domain="return",
                            return_ref=letter,
                            field=param_name,
                            value=op.get("value"),
                            unit=op.get("unit"),
                            display=str(op.get("value")) if str(op.get("unit") or "").lower() == "display" else None,
                            dry_run=not body.confirm,
                        )
                    result = exec_canonical(canonical)
                    ok = bool(result and result.get("ok", True))
                    summary = result.get("summary") or (f"Set Return {letter} send {send_ref}" if m else f"Set Return {letter} {param_name}")
                    data = result.get("data") if isinstance(result, dict) else {}
                    # Ensure capabilities are present for UI cards
                    try:
                        caps = ((data or {}).get("capabilities") if isinstance(data, dict) else None)
                        if not caps:
                            from server.api.returns import get_return_mixer_capabilities
                            ri = ord(letter) - ord('A')
                            caps_res = get_return_mixer_capabilities(index=ri)
                            if isinstance(caps_res, dict) and caps_res.get("ok"):
                                if isinstance(data, dict):
                                    data.setdefault("capabilities", caps_res.get("data"))
                                else:
                                    data = {"capabilities": caps_res.get("data")}
                    except Exception:
                        pass
                    return {"ok": ok, "intent": intent, "summary": summary, "data": data or {}}
    except Exception:
        pass

    # Auto-execute Track mixer (volume/pan/mute/solo) and sends using CanonicalIntent (ensures UI cards)
    try:
        if intent.get("intent") == "set_parameter":
            targets = intent.get("targets") or []
            if targets:
                target = targets[0] or {}
                track_ref = target.get("track")
                plugin = target.get("plugin")
                param_name = (target.get("parameter") or "").strip().lower()
                if isinstance(track_ref, str) and track_ref.strip().lower().startswith("track ") and not plugin:
                    from server.api.intents import execute_intent as exec_canonical
                    from server.api.intents import CanonicalIntent
                    # Extract track index from "Track N"
                    try:
                        track_idx = int(track_ref.strip().split()[-1])
                    except Exception:
                        track_idx = None
                    if track_idx:
                        import re as _re
                        m = _re.search(r"\bsend\s*([a-d])\b", param_name)
                        if m:
                            send_ref = m.group(1).upper()
                            op = intent.get("operation") or {}
                            canonical = CanonicalIntent(
                                domain="track",
                                track_index=int(track_idx),
                                field="send",
                                send_ref=send_ref,
                                value=op.get("value"),
                                unit=op.get("unit"),
                                dry_run=not body.confirm,
                            )
                            result = exec_canonical(canonical)
                            ok = bool(result and result.get("ok", True))
                            summary = result.get("summary") or f"Set Track {track_idx} send {send_ref}"
                            data = result.get("data") if isinstance(result, dict) else {}
                            # Ensure track capabilities for UI cards
                            try:
                                caps = ((data or {}).get("capabilities") if isinstance(data, dict) else None)
                                if not caps:
                                    from server.api.tracks import get_track_mixer_capabilities
                                    caps_res = get_track_mixer_capabilities(index=max(0, int(track_idx) - 1))
                                    if isinstance(caps_res, dict) and caps_res.get("ok"):
                                        if isinstance(data, dict):
                                            data.setdefault("capabilities", caps_res.get("data"))
                                        else:
                                            data = {"capabilities": caps_res.get("data")}
                            except Exception:
                                pass
                            return {"ok": ok, "intent": intent, "summary": summary, "data": data or {}}
                        elif param_name in ("volume", "pan", "mute", "solo"):
                            op = intent.get("operation") or {}
                            canonical = CanonicalIntent(
                                domain="track",
                                track_index=int(track_idx),
                                field=param_name,
                                value=op.get("value"),
                                unit=op.get("unit"),
                                display=str(op.get("value")) if str(op.get("unit") or "").lower() == "display" else None,
                                dry_run=not body.confirm,
                            )
                            result = exec_canonical(canonical)
                            ok = bool(result and result.get("ok", True))
                            summary = result.get("summary") or f"Set Track {track_idx} {param_name}"
                            data = result.get("data") if isinstance(result, dict) else {}
                            try:
                                caps = ((data or {}).get("capabilities") if isinstance(data, dict) else None)
                                if not caps:
                                    from server.api.tracks import get_track_mixer_capabilities
                                    caps_res = get_track_mixer_capabilities(index=max(0, int(track_idx) - 1))
                                    if isinstance(caps_res, dict) and caps_res.get("ok"):
                                        if isinstance(data, dict):
                                            data.setdefault("capabilities", caps_res.get("data"))
                                        else:
                                            data = {"capabilities": caps_res.get("data")}
                            except Exception:
                                pass
                            return {"ok": ok, "intent": intent, "summary": summary, "data": data or {}}
    except Exception:
        pass

    # Auto-execute Master mixer using CanonicalIntent
    try:
        if intent.get("intent") == "set_parameter":
            targets = intent.get("targets") or []
            if targets:
                target = targets[0] or {}
                track_ref = target.get("track")
                plugin = target.get("plugin")
                param_name = (target.get("parameter") or "").strip().lower()
                if isinstance(track_ref, str) and track_ref.strip().lower() == "master" and not plugin:
                    from server.api.intents import execute_intent as exec_canonical
                    from server.api.intents import CanonicalIntent
                    op = intent.get("operation") or {}
                    canonical = CanonicalIntent(
                        domain="master",
                        field=param_name,
                        value=op.get("value"),
                        unit=op.get("unit"),
                        display=str(op.get("value")) if str(op.get("unit") or "").lower() == "display" else None,
                        dry_run=not body.confirm,
                    )
                    result = exec_canonical(canonical)
                    ok = bool(result and result.get("ok", True))
                    summary = result.get("summary") or f"Set Master {param_name}"
                    data = result.get("data") if isinstance(result, dict) else {}
                    # Ensure master capabilities for UI cards
                    try:
                        caps = ((data or {}).get("capabilities") if isinstance(data, dict) else None)
                        if not caps:
                            from server.api.master import get_master_mixer_capabilities
                            caps_res = get_master_mixer_capabilities()
                            if isinstance(caps_res, dict) and caps_res.get("ok"):
                                if isinstance(data, dict):
                                    data.setdefault("capabilities", caps_res.get("data"))
                                else:
                                    data = {"capabilities": caps_res.get("data")}
                    except Exception:
                        pass
                    return {"ok": ok, "intent": intent, "summary": summary, "data": data or {}}
    except Exception:
        pass

    # Fallback: return intent for UI to decide
    return {
        "ok": False,
        "reason": "unsupported_intent_for_auto_execute",
        "intent": intent,
        "summary": "I can auto-execute only absolute track volume right now."
    }


@app.post("/op/undo_last")
def undo_last() -> Dict[str, Any]:
    """Undo the last successful change (mixer or device param) if previous value is known."""
    while UNDO_STACK:
        entry = UNDO_STACK.pop()
        etype = entry.get("type", "mixer")
        if etype == "mixer":
            prev = entry.get("prev")
            track_index = entry.get("track_index")
            field = entry.get("field")
            if prev is None or track_index is None or field not in ("volume", "pan"):
                continue
            msg = {"op": "set_mixer", "track_index": int(track_index), "field": field, "value": float(prev)}
            resp = udp_request(msg, timeout=1.0)
            if resp and resp.get("ok", True):
                LAST_SENT[_key(field, int(track_index))] = float(prev)
                # push redo entry
                REDO_STACK.append({"type": "mixer", "key": entry.get("key"), "field": field, "track_index": track_index, "prev": msg["value"], "new": entry.get("new")})
                return {"ok": True, "undone": entry, "resp": resp}
            else:
                return {"ok": False, "error": "undo_send_failed", "attempt": entry}
        elif etype == "device_param":
            prev = entry.get("prev")
            ri = entry.get("return_index")
            di = entry.get("device_index")
            pi = entry.get("param_index")
            if prev is None or ri is None or di is None or pi is None:
                continue
            msg = {"op": "set_return_device_param", "return_index": int(ri), "device_index": int(di), "param_index": int(pi), "value": float(prev)}
            resp = udp_request(msg, timeout=1.0)
            if resp and resp.get("ok", True):
                # push redo entry
                REDO_STACK.append({"type": "device_param", "return_index": ri, "device_index": di, "param_index": pi, "prev": entry.get("new"), "new": prev})
                try:
                    schedule_emit({"event": "device_param_restored", "return_index": ri, "device_index": di})
                except Exception:
                    pass
                return {"ok": True, "undone": entry, "resp": resp}
            else:
                return {"ok": False, "error": "undo_send_failed", "attempt": entry}
    return {"ok": False, "error": "nothing_to_undo"}


@app.post("/op/redo_last")
def redo_last() -> Dict[str, Any]:
    """Re-apply the last undone change (mixer or device param) if available."""
    while REDO_STACK:
        entry = REDO_STACK.pop()
        etype = entry.get("type", "mixer")
        if etype == "mixer":
            new_val = entry.get("new")
            track_index = entry.get("track_index")
            field = entry.get("field")
            if new_val is None or track_index is None or field not in ("volume", "pan"):
                continue
            msg = {"op": "set_mixer", "track_index": int(track_index), "field": field, "value": float(new_val)}
            resp = udp_request(msg, timeout=1.0)
            if resp and resp.get("ok", True):
                LAST_SENT[_key(field, int(track_index))] = float(new_val)
                UNDO_STACK.append({"type": "mixer", "key": entry.get("key"), "field": field, "track_index": track_index, "prev": entry.get("prev"), "new": new_val})
                return {"ok": True, "redone": entry, "resp": resp}
            else:
                return {"ok": False, "error": "redo_send_failed", "attempt": entry}
        elif etype == "device_param":
            new_val = entry.get("new")
            ri = entry.get("return_index")
            di = entry.get("device_index")
            pi = entry.get("param_index")
            if new_val is None or ri is None or di is None or pi is None:
                continue
            msg = {"op": "set_return_device_param", "return_index": int(ri), "device_index": int(di), "param_index": int(pi), "value": float(new_val)}
            resp = udp_request(msg, timeout=1.0)
            if resp and resp.get("ok", True):
                UNDO_STACK.append({"type": "device_param", "return_index": ri, "device_index": di, "param_index": pi, "prev": entry.get("prev"), "new": new_val})
                return {"ok": True, "redone": entry, "resp": resp}
            else:
                return {"ok": False, "error": "redo_send_failed", "attempt": entry}
    return {"ok": False, "error": "nothing_to_redo"}


@app.get("/op/history_state")
def history_state() -> Dict[str, Any]:
    return {
        "ok": True,
        "undo_available": bool(UNDO_STACK),
        "redo_available": bool(REDO_STACK),
        "undo_depth": len(UNDO_STACK),
        "redo_depth": len(REDO_STACK),
    }


# ==================== Return Device Control Helpers ====================

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


@app.post("/return/device/bypass")
def bypass_return_device(body: BypassBody) -> Dict[str, Any]:
    """Bypass or enable a return device.

    Strategy:
    - Prefer the binary parameter "Device On" (1=on, 0=off)
    - Fallback: set "Dry/Wet" to 0 when turning off; restore previous value when turning on if known
    """
    ri = int(body.return_index)
    di = int(body.device_index)
    # Read current params
    resp = udp_request({"op": "get_return_device_params", "return_index": ri, "device_index": di}, timeout=1.0)
    params = ((resp or {}).get("data") or {}).get("params") or []
    if not params:
        raise HTTPException(404, "device_params_not_found")

    # Try Device On first
    dev_on = _find_device_param(params, ["Device On"])  # Ableton stock devices commonly expose this
    if dev_on is not None:
        idx = int(dev_on.get("index", -1))
        if idx < 0:
            raise HTTPException(500, "invalid_param_index")
        prev = float(dev_on.get("value", 1.0))
        target = 1.0 if body.on else 0.0
        ok = udp_request({
            "op": "set_return_device_param",
            "return_index": ri,
            "device_index": di,
            "param_index": idx,
            "value": float(target),
        }, timeout=0.8)
        if ok and ok.get("ok", True):
            # Push undo entry for device param
            UNDO_STACK.append({
                "type": "device_param",
                "return_index": ri,
                "device_index": di,
                "param_index": idx,
                "prev": prev,
                "new": target,
            })
            REDO_STACK.clear()
            try:
                schedule_emit({"event": "device_bypass_changed", "return_index": ri, "device_index": di, "on": body.on})
            except Exception:
                pass
            return {"ok": True, "method": "device_on", "prev": prev, "new": target}
        raise HTTPException(502, "set_param_failed")

    # Fallback: use Dry/Wet as proxy for bypass when turning off
    drywet = _find_device_param(params, ["Dry/Wet", "Mix"])  # try common names
    if drywet is None:
        raise HTTPException(400, "no_bypass_strategy_available")
    idx = int(drywet.get("index", -1))
    if idx < 0:
        raise HTTPException(500, "invalid_param_index")
    prev = float(drywet.get("value", 0.0))
    key = (ri, di)
    # When turning off, remember the last non-zero Dry/Wet to restore later
    if not body.on:
        if prev > 0.0:
            DEVICE_BYPASS_CACHE[key] = prev
        target = 0.0
    else:
        # Restore cached non-zero value if available; otherwise a sensible default
        restore = DEVICE_BYPASS_CACHE.get(key, None)
        target = float(restore if restore is not None else max(prev, 0.25))
    ok = udp_request({
        "op": "set_return_device_param",
        "return_index": ri,
        "device_index": di,
        "param_index": idx,
        "value": float(target),
    }, timeout=0.8)
    if ok and ok.get("ok", True):
        UNDO_STACK.append({
            "type": "device_param",
            "return_index": ri,
            "device_index": di,
            "param_index": idx,
            "prev": prev,
            "new": target,
        })
        REDO_STACK.clear()
        # If we restored a value, clear cache to avoid stale
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


@app.post("/return/device/save_as_user_preset")
def save_as_user_preset(body: SaveUserPresetBody) -> Dict[str, Any]:
    """Capture current device state and save as a user preset in Firestore."""
    ri = int(body.return_index)
    di = int(body.device_index)
    # Read device info and params
    devs = udp_request({"op": "get_return_devices", "return_index": ri}, timeout=1.0)
    if not devs or "devices" not in devs:
        raise HTTPException(404, "return_not_found")
    devices = devs.get("devices", [])
    if di >= len(devices):
        raise HTTPException(404, "device_index_out_of_range")
    device = devices[di]
    device_name = device.get("name", "Unknown")

    params_resp = udp_request({"op": "get_return_device_params", "return_index": ri, "device_index": di}, timeout=1.0)
    if not params_resp or "params" not in params_resp:
        raise HTTPException(500, "device_params_fetch_failed")
    params = params_resp.get("params", [])

    # Build param values and signature
    parameter_values: Dict[str, float] = {}
    for p in params:
        nm = p.get("name"); val = p.get("value")
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

    ok = STORE.save_preset(preset_id, preset_data, local_only=False)
    try:
        schedule_emit({"event": "preset_saved", "preset_id": preset_id, "name": body.preset_name})
    except Exception:
        pass
    return {"ok": bool(ok), "preset_id": preset_id, "device_type": device_type, "signature": signature}


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("SERVER_HOST", "127.0.0.1")
    port = int(os.getenv("SERVER_PORT", "8722"))
    uvicorn.run("server.app:app", host=host, port=port, reload=True)


@app.post("/help")
def help_endpoint(body: HelpBody) -> Dict[str, Any]:
    """Return grounded help snippets from local knowledge notes.

    Response shape:
    { ok, answer, sources: [{source, title}] }
    """
    matches = search_knowledge(body.query)
    # Compose a short answer from top matches if any
    snippets: list[str] = []
    sources: list[Dict[str, str]] = []
    for src, title, body_text in matches:
        sources.append({"source": src, "title": title})
        snippets.append(f"{title}:\n" + body_text)

    # Heuristic suggestions based on common phrases
    q = (body.query or "").lower()
    suggested: list[str] = []
    if any(k in q for k in ["vocal", "vocals", "singer", "voice", "weak", "soft", "quiet"]):
        suggested.extend([
            "increase track 1 volume by 3 dB",
            "set track 1 volume to -6 dB",
            "reduce compressor threshold on track 1 by 3 dB",
        ])
    if any(k in q for k in ["bass", "muddy", "low end", "boom"]):
        suggested.extend([
            "cut 200 Hz on track 2 by 3 dB",
            "enable high-pass filter on track 2 at 80 Hz",
        ])
    if any(k in q for k in ["reverb", "space", "spacious", "hall", "room"]):
        suggested.extend([
            "increase send A on track 1 by 10%",
            "set reverb wet on track 1 to 20%",
        ])

    # Sends and routing guidance
    if any(k in q for k in ["send", "sends", "routing", "route"]):
        suggested.extend([
            "set track 1 send A to -12 dB",
            "set return A send B to 25%",
            "set track 2 send B to 15%",
        ])
        # If no snippets matched, produce a concise, grounded answer about sends
        if not snippets:
            answer = (
                "Sends control how much signal is sent to return tracks (A/B/…).\n"
                "- Track sends: use intents like ‘set track 1 send A to -12 dB’ or ‘25%’.\n"
                "- Return→Return sends: available only if enabled in Live Preferences; then use ‘set Return A send B to 20%’.\n"
                "- Read sends: /return/sends?index=0 or /track/sends?index=1; formatted readbacks via /intent/read.\n"
                "- Pre/Post: see Return routing via /return/routing (field ‘sends_mode’)."
            )
            return {"ok": True, "answer": answer, "sources": sources, "suggested_intents": suggested}

    # Live-set aware helpers
    ctx = body.context or {}
    try:
        # Normalize indices from context if present
        ri = ctx.get("return_index")
        if ri is None and isinstance(ctx.get("return_ref"), str):
            ri = max(0, ord(str(ctx.get("return_ref")).strip().upper()[0]) - ord('A'))
        di = ctx.get("device_index")
        # Device parameter listing
        if any(k in q for k in ["what parameters", "what params", "what can i control", "list parameters", "list params"]):
            if ri is not None and di is not None:
                pr = request_op("get_return_device_params", timeout=1.0, return_index=int(ri), device_index=int(di)) or {}
                params = ((pr.get("data") or pr) if isinstance(pr, dict) else pr).get("params", [])
                devs = request_op("get_return_devices", timeout=0.8, return_index=int(ri)) or {}
                devs_list = ((devs.get("data") or devs) if isinstance(devs, dict) else devs).get("devices", [])
                dname = next((str(d.get("name","")) for d in devs_list if int(d.get("index",-1)) == int(di)), f"Device {di}")
                ans = f"Parameters on Return {chr(ord('A')+int(ri))} • {dname}:\n"
                names = [str(p.get("name","")) for p in params]
                ans += ", ".join(names[:40])
                return {"ok": True, "answer": ans, "suggested_intents": suggested}
        # Preset listing for current device
        if any(k in q for k in ["what presets", "list presets", "presets available"]):
            if ri is not None and di is not None:
                # Build signature for filtering if possible
                pr = request_op("get_return_device_params", timeout=1.0, return_index=int(ri), device_index=int(di)) or {}
                params = ((pr.get("data") or pr) if isinstance(pr, dict) else pr).get("params", [])
                devs = request_op("get_return_devices", timeout=0.8, return_index=int(ri)) or {}
                devs_list = ((devs.get("data") or devs) if isinstance(devs, dict) else devs).get("devices", [])
                dname = next((str(d.get("name","")) for d in devs_list if int(d.get("index",-1)) == int(di)), f"Device {di}")
                sig = make_device_signature(dname, params)
                store = get_store()
                device_type = ""
                mapping = store.get_device_mapping(sig) if store.enabled else None
                if mapping:
                    device_type = str((mapping.get("device_type") or "")).lower()
                presets = store.list_presets(device_type=device_type or None, structure_signature=sig) if store.enabled else []
                if presets:
                    ids = [p.get("id") for p in presets[:15]]
                    ans = f"Presets for {dname}:\n" + ", ".join([str(x) for x in ids])
                else:
                    ans = f"No presets found for {dname}."
                return {"ok": True, "answer": ans, "suggested_intents": suggested}
        # What does param/group do?
        m = re.search(r"what\s+does\s+(.+?)\s+do\??", q)
        if m and (ri is not None and di is not None):
            query_name = m.group(1).strip().lower()
            pr = request_op("get_return_device_params", timeout=1.0, return_index=int(ri), device_index=int(di)) or {}
            params = ((pr.get("data") or pr) if isinstance(pr, dict) else pr).get("params", [])
            devs = request_op("get_return_devices", timeout=0.8, return_index=int(ri)) or {}
            devs_list = ((devs.get("data") or devs) if isinstance(devs, dict) else devs).get("devices", [])
            dname = next((str(d.get("name","")) for d in devs_list if int(d.get("index",-1)) == int(di)), f"Device {di}")
            sig = make_device_signature(dname, params)
            store = get_store()
            mapping = store.get_device_mapping(sig) if store.enabled else None
            if mapping:
                pm = mapping.get("params") or []
                # Firestore schema stores list of param docs under 'params'
                # Fallback: use live params if mapping missing
                meta_list = pm if pm else []
                # Try to resolve by exact or contains
                cand = []
                for p in meta_list:
                    nm = str(p.get("name",""))
                    if query_name == nm.lower() or query_name in nm.lower():
                        cand.append(p)
                if cand:
                    p0 = cand[0]
                    desc = []
                    unit = p0.get("unit")
                    qz = p0.get("quantized")
                    labels = p0.get("labels") or (list((p0.get("label_map") or {}).keys()) if p0.get("label_map") else None)
                    rng = (p0.get("min"), p0.get("max")) if (p0.get("min") is not None and p0.get("max") is not None) else None
                    if unit: desc.append(f"unit: {unit}")
                    if rng: desc.append(f"range: {rng[0]}–{rng[1]}")
                    if qz: desc.append("quantized")
                    if labels: desc.append(f"labels: {', '.join([str(x) for x in labels][:12])}")
                    answer = f"{p0.get('name')} — " + "; ".join(desc) if desc else f"{p0.get('name')} — no extra metadata available"
                    return {"ok": True, "answer": answer, "suggested_intents": suggested}
    except Exception:
        pass

    answer = None
    if snippets:
        answer = "\n\n".join(snippets[:2])
    else:
        answer = "I couldn't find specific notes, but try adjusting volume, EQ muddiness around 200–400 Hz, or adding gentle compression."

    return {"ok": True, "answer": answer, "sources": sources, "suggested_intents": suggested}


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


"""Emit helpers moved to server.core.events (emit_event, schedule_emit)"""


_EVENT_THREAD: Optional[threading.Thread] = None


def start_ableton_event_listener() -> None:
    global _EVENT_THREAD
    if _EVENT_THREAD and _EVENT_THREAD.is_alive():
        return
    host = os.getenv("ABLETON_UDP_CLIENT_HOST", "127.0.0.1")
    port = int(os.getenv("ABLETON_UDP_CLIENT_PORT", os.getenv("ABLETON_EVENT_PORT", "19846")))
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((host, port))
        print(f"[Ableton] Listening for notifications on {host}:{port}")
    except Exception as e:
        print(f"[Ableton] Failed to bind event listener on {host}:{port} -> {e}")
        return

    def loop():
        while True:
            try:
                data, _ = sock.recvfrom(64 * 1024)
            except Exception:
                continue
            try:
                payload = json.loads(data.decode("utf-8"))
            except Exception:
                continue
            schedule_emit(payload)

    _EVENT_THREAD = threading.Thread(target=loop, name="AbletonEventListener", daemon=True)
    _EVENT_THREAD.start()


@app.on_event("startup")
async def _ableton_startup_listener() -> None:
    start_ableton_event_listener()
    # Start LiveIndex background refresher
    try:
        import asyncio as _asyncio
        li = get_live_index()
        _asyncio.create_task(li.refresh_all())
        _asyncio.create_task(li.loop(interval_sec=60.0))
    except Exception:
        pass
