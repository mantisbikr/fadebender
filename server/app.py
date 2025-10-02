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

from server.ableton.client_udp import request as udp_request, send as udp_send
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
    reload_config as cfg_reload,
    save_config as cfg_save,
)
from server.config.param_learn_config import (
    get_param_learn_config,
    set_param_learn_config,
    reload_param_learn_config,
    save_param_learn_config,
)
from server.services.mapping_store import MappingStore
import hashlib
import math
from server.volume_parser import parse_volume_command

# --------- Param classification & grouping helpers ---------
import re as _re

def _parse_unit_from_display(disp: str) -> str | None:
    if not disp:
        return None
    s = str(disp).strip()
    # Common units: ms, s, Hz, kHz, %, dB, °
    # Try suffix tokens
    if "dB" in s or _re.search(r"\bdB\b", s):
        return "dB"
    if "%" in s:
        return "%"
    if "kHz" in s:
        return "kHz"
    if _re.search(r"\bHz\b", s):
        return "Hz"
    if _re.search(r"\bms\b", s):
        return "ms"
    if _re.search(r"\bs\b", s):
        return "s"
    if "°" in s:
        return "deg"
    return None

def _classify_control_type(samples: list[dict], vmin: float, vmax: float) -> tuple[str, list[str]]:
    # Return (control_type, labels)
    if not samples:
        # fallback on range heuristic
        return ("continuous", [])
    labels = list({str(s.get("display", "")) for s in samples if s.get("display") is not None})
    # Count numeric-like labels
    numeric_like = 0
    for lab in labels:
        if _re.search(r"-?\d+(?:\.\d+)?", lab):
            numeric_like += 1
    # Binary if <=2 labels and not mostly numeric
    if len(labels) <= 2 and numeric_like < len(labels):
        return ("binary", labels)
    # Quantized if small label set and not numeric
    if len(labels) > 0 and len(labels) <= 12 and numeric_like < len(labels):
        return ("quantized", labels)
    return ("continuous", [])

def _group_role_for_reverb_param(pname: str) -> tuple[str | None, str | None, str | None]:
    """Return (group_name, role, master_name) for Ableton Reverb param name.
    role in {master, dependent, None}. master_name populated for dependents.
    """
    n = (pname or "").strip()
    nlc = n.lower()
    # Chorus
    if nlc == "chorus on":
        return ("Chorus", "master", None)
    if nlc in ("chorus rate", "chorus amount"):
        return ("Chorus", "dependent", "Chorus On")
    # ER Spin (Early)
    if nlc == "er spin on":
        return ("Early", "master", None)
    if nlc in ("er spin rate", "er spin amount"):
        return ("Early", "dependent", "ER Spin On")
    # Shelves / Filters (Tail)
    if nlc in ("lowshelf on", "low shelf on", "low shelf enabled"):
        return ("Tail", "master", None)
    if nlc.startswith("lowshelf ") or nlc.startswith("low shelf "):
        if nlc not in ("low shelf on", "lowshelf on"):
            return ("Tail", "dependent", "LowShelf On")
    if nlc in ("hishelf on", "high shelf on", "high shelf enabled"):
        return ("Tail", "master", None)
    if nlc.startswith("hishelf ") or nlc.startswith("high shelf "):
        if nlc not in ("hishelf on", "high shelf on"):
            return ("Tail", "dependent", "HiShelf On")
    if nlc == "hifilter on":
        return ("Tail", "master", None)
    if nlc.startswith("hifilter "):
        if nlc != "hifilter on":
            return ("Tail", "dependent", "HiFilter On")
    # Freeze (Global). Handle carefully: do NOT auto-enable master implicitly.
    if nlc == "freeze on":
        return ("Global", "master", None)
    if nlc in ("flat on", "cut on"):
        return ("Global", "dependent", "Freeze On")
    # Input / Output / Global catch-alls based on names
    if nlc in ("dry/wet", "dry wet", "reflect level", "diffuse level"):
        return ("Output", None, None)
    if nlc in ("predelay", "decay", "size", "stereo image", "density", "size smoothing", "scale", "diffusion"):
        return ("Global", None, None)
    # Input filters sometimes appear as "In HighCut On/Freq" etc.
    if nlc.startswith("in ") or nlc.startswith("input "):
        if nlc.endswith(" on"):
            return ("Input", "master", None)
        return ("Input", "dependent", None)
    return (None, None, None)

def _group_role_for_device(device_name: str | None, param_name: str) -> tuple[str | None, str | None, str | None]:
    dn = (device_name or "").strip().lower()
    pn = (param_name or "").strip()
    # Config-driven first
    try:
        PLC = get_param_learn_config()
        grp = PLC.get("grouping", {}) or {}
        match_key = None
        for key in grp.keys():
            kl = str(key).lower()
            if kl == "default":
                continue
            if kl in dn:
                match_key = key
                break
        if match_key is None:
            match_key = "default"
        rules = grp.get(match_key) or {}
        # Check dependents mapping exact/regex via pipes
        deps = rules.get("dependents") or {}
        for dep_name, master_name in deps.items():
            # dep_name may be exact or partial; use case-insensitive contains
            if str(dep_name).lower() == pn.lower():
                return (match_key.title() if match_key != 'default' else None, "dependent", str(master_name))
        # For masters list, allow "A|B|C" alternatives
        for m in (rules.get("masters") or []):
            alts = [s.strip() for s in str(m).split("|")]
            if any(pn.lower() == a.lower() for a in alts):
                return (match_key.title() if match_key != 'default' else None, "master", None)
    except Exception:
        pass
    # Built-in fallbacks
    if "reverb" in dn:
        return _group_role_for_reverb_param(param_name)
    return (None, None, None)

def _build_groups_from_params(params: list[dict], device_name: str | None) -> list[dict]:
    groups: dict[str, dict] = {}
    # Map by name for quick lookup
    by_name = {str(p.get("name", "")): p for p in params}
    for p in params:
        name = str(p.get("name", ""))
        gname, role, master_name = _group_role_for_device(device_name, name)
        if not gname:
            continue
        if gname not in groups:
            groups[gname] = {"name": gname, "master": None, "dependents": []}
        if role == "master":
            groups[gname]["master"] = {"name": name, "index": int(p.get("index", 0))}
        elif role == "dependent":
            groups[gname]["dependents"].append({"name": name, "index": int(p.get("index", 0)), "master": master_name})
    return list(groups.values())


app = FastAPI(title="Fadebender Ableton Server", version="0.1.0")

# Load .env at server startup so Vertex/LLM config can come from file
try:  # optional dependency
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Simple safety state: undo + rate limiting ---
UNDO_STACK: list[Dict[str, Any]] = []
REDO_STACK: list[Dict[str, Any]] = []
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
class EventBroker:
    def __init__(self) -> None:
        self._subs: list[asyncio.Queue] = []
        self._lock = asyncio.Lock()

    async def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        async with self._lock:
            self._subs.append(q)
        return q

    async def publish(self, data: Dict[str, Any]) -> None:
        async with self._lock:
            for q in list(self._subs):
                try:
                    q.put_nowait(data)
                except Exception:
                    pass

    async def unsubscribe(self, q: asyncio.Queue) -> None:
        async with self._lock:
            if q in self._subs:
                self._subs.remove(q)


broker = EventBroker()
STORE = MappingStore()
LEARN_JOBS: dict[str, dict] = {}

@app.get("/events")
async def events():
    q = await broker.subscribe()
    async def event_gen():
        try:
            while True:
                data = await q.get()
                try:
                    payload = json.dumps(data)
                except Exception:
                    payload = json.dumps({"malformed": True, "repr": str(data)})
                yield "data: " + payload + "\n\n"
        except asyncio.CancelledError:
            await broker.unsubscribe(q)
    return StreamingResponse(event_gen(), media_type="text/event-stream")


@app.get("/config")
def app_config() -> Dict[str, Any]:
    """Expose a subset of app config to clients (UI + aliases)."""
    ui = get_ui_settings()
    aliases = get_send_aliases()
    return {"ok": True, "ui": ui, "aliases": {"sends": aliases}}


@app.post("/config/update")
def app_config_update(body: Dict[str, Any]) -> Dict[str, Any]:
    ui_in = (body or {}).get("ui") or {}
    aliases_in = ((body or {}).get("aliases") or {}).get("sends") or {}
    ui = set_ui_settings(ui_in) if ui_in else get_ui_settings()
    aliases = set_send_aliases(aliases_in) if aliases_in else get_send_aliases()
    saved = cfg_save()
    return {"ok": True, "saved": saved, "ui": ui, "aliases": {"sends": aliases}}


@app.post("/config/reload")
def app_config_reload() -> Dict[str, Any]:
    cfg = cfg_reload()
    plc = reload_param_learn_config()
    return {"ok": True, "config": cfg, "param_learn": plc}


@app.get("/param_learn/config")
def get_param_learn_cfg() -> Dict[str, Any]:
    return {"ok": True, "config": get_param_learn_config()}


@app.post("/param_learn/config")
def set_param_learn_cfg(body: Dict[str, Any]) -> Dict[str, Any]:
    cfg = set_param_learn_config(body or {})
    saved = save_param_learn_config()
    return {"ok": True, "saved": saved, "config": cfg}

def _get_prev_mixer_value(track_index: int, field: str) -> Optional[float]:
    """Try to read previous mixer value from Ableton (if bridge supports it)."""
    try:
        resp = udp_request({"op": "get_track_status", "track_index": int(track_index)}, timeout=0.4)
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


class IntentParseBody(BaseModel):
    text: str
    model: Optional[str] = None
    strict: Optional[bool] = None


class VolumeDbBody(BaseModel):
    track_index: int
    db: float


@app.get("/ping")
def ping() -> Dict[str, Any]:
    resp = udp_request({"op": "ping"}, timeout=0.5)
    ok = bool(resp and resp.get("ok", True))
    return {"ok": ok, "remote": resp}


@app.get("/status")
def status() -> Dict[str, Any]:
    resp = udp_request({"op": "get_overview"}, timeout=1.0)
    if not resp:
        return {"ok": False, "error": "no response"}
    return resp


@app.get("/project/outline")
def project_outline() -> Dict[str, Any]:
    """Return lightweight project outline (tracks, selected track, scenes)."""
    resp = udp_request({"op": "get_overview"}, timeout=1.0)
    if not resp:
        return {"ok": False, "error": "no response"}
    # Normalize to { ok, data }
    data = resp.get("data") if isinstance(resp, dict) else None
    if data is None:
        data = resp
    return {"ok": True, "data": data}


@app.get("/track/status")
def track_status(index: int) -> Dict[str, Any]:
    """Return per-track status (mixer values) for quick diagnostics."""
    resp = udp_request({"op": "get_track_status", "track_index": int(index)}, timeout=1.0)
    if not resp:
        return {"ok": False, "error": "no response"}
    data = resp.get("data") if isinstance(resp, dict) else None
    if data is None:
        data = resp
    return {"ok": True, "data": data}


@app.get("/track/sends")
def track_sends(index: int) -> Dict[str, Any]:
    """Return sends for a track as { index, sends: [{index, name, value}] }"""
    resp = udp_request({"op": "get_track_sends", "track_index": int(index)}, timeout=1.0)
    if not resp:
        return {"ok": False, "error": "no response"}
    data = resp.get("data") if isinstance(resp, dict) else None
    if data is None:
        data = resp
    return {"ok": True, "data": data}


@app.get("/returns")
def get_returns() -> Dict[str, Any]:
    resp = udp_request({"op": "get_return_tracks"}, timeout=1.0)
    if not resp:
        return {"ok": False, "error": "no response"}
    data = resp.get("data") if isinstance(resp, dict) else None
    if data is None:
        data = resp
    return {"ok": True, "data": data}


@app.get("/return/devices")
def get_return_devices(index: int) -> Dict[str, Any]:
    resp = udp_request({"op": "get_return_devices", "return_index": int(index)}, timeout=1.0)
    if not resp:
        return {"ok": False, "error": "no response"}
    data = resp.get("data") if isinstance(resp, dict) else None
    if data is None:
        data = resp
    return {"ok": True, "data": data}


@app.get("/return/device/params")
def get_return_device_params(index: int, device: int) -> Dict[str, Any]:
    resp = udp_request({"op": "get_return_device_params", "return_index": int(index), "device_index": int(device)}, timeout=1.0)
    if not resp:
        return {"ok": False, "error": "no response"}
    data = resp.get("data") if isinstance(resp, dict) else None
    if data is None:
        data = resp
    return {"ok": True, "data": data}


@app.get("/return/device/map")
def get_return_device_map(index: int, device: int) -> Dict[str, Any]:
    """Return whether a learned mapping exists for this return device (by signature)."""
    # Fetch device name and params to compute signature
    devs = udp_request({"op": "get_return_devices", "return_index": int(index)}, timeout=1.0)
    devices = ((devs or {}).get("data") or {}).get("devices") or []
    dname = None
    for d in devices:
        if int(d.get("index", -1)) == int(device):
            dname = str(d.get("name", f"Device {device}"))
            break
    if dname is None:
        return {"ok": False, "error": "device_not_found"}
    params_resp = udp_request({"op": "get_return_device_params", "return_index": int(index), "device_index": int(device)}, timeout=1.2)
    params = ((params_resp or {}).get("data") or {}).get("params") or []
    signature = _make_device_signature(dname, params)
    backend = STORE.backend
    exists = False
    try:
        m = STORE.get_device_map(signature) if STORE.enabled else None
        if m and isinstance(m.get("params"), list):
            # Consider learned only if at least one param has >= 3 samples
            for p in m["params"]:
                sm = p.get("samples") or []
                if isinstance(sm, list) and len(sm) >= 3:
                    exists = True
                    break
    except Exception:
        exists = False
    return {"ok": True, "exists": exists, "signature": signature, "backend": backend}


@app.get("/return/device/map_summary")
def get_return_device_map_summary(index: int, device: int) -> Dict[str, Any]:
    """Return a summary of a learned mapping: param names and sample counts."""
    devs = udp_request({"op": "get_return_devices", "return_index": int(index)}, timeout=1.0)
    devices = ((devs or {}).get("data") or {}).get("devices") or []
    dname = None
    for d in devices:
        if int(d.get("index", -1)) == int(device):
            dname = str(d.get("name", f"Device {device}"))
            break
    if dname is None:
        return {"ok": False, "error": "device_not_found"}
    params_resp = udp_request({"op": "get_return_device_params", "return_index": int(index), "device_index": int(device)}, timeout=1.2)
    params = ((params_resp or {}).get("data") or {}).get("params") or []
    signature = _make_device_signature(dname, params)
    backend = STORE.backend
    data = None
    try:
        m = STORE.get_device_map(signature) if STORE.enabled else None
        if m:
            plist = []
            for p in m.get("params", []) or []:
                plist.append({
                    "name": p.get("name"),
                    "index": p.get("index"),
                    "sample_count": len(p.get("samples") or []),
                    "quantized": bool(p.get("quantized", False)),
                    "control_type": p.get("control_type"),
                    "unit": p.get("unit"),
                    "group": p.get("group"),
                    "role": p.get("role"),
                    "labels": p.get("labels") or [],
                    "label_map": p.get("label_map"),
                    "min": p.get("min"),
                    "max": p.get("max"),
                })
            data = {
                "device_name": m.get("device_name") or dname,
                "signature": signature,
                "groups": m.get("groups") or [],
                "params": plist,
            }
    except Exception as e:
        return {"ok": False, "error": str(e), "backend": backend}
    return {"ok": True, "backend": backend, "signature": signature, "data": data}


class MapDeleteBody(BaseModel):
    return_index: int
    device_index: int


@app.post("/return/device/map_delete")
def delete_return_device_map(body: MapDeleteBody) -> Dict[str, Any]:
    # Compute signature
    devs = udp_request({"op": "get_return_devices", "return_index": int(body.return_index)}, timeout=1.0)
    devices = ((devs or {}).get("data") or {}).get("devices") or []
    dname = None
    for d in devices:
        if int(d.get("index", -1)) == int(body.device_index):
            dname = str(d.get("name", f"Device {body.device_index}"))
            break
    if dname is None:
        raise HTTPException(404, "device_not_found")
    params_resp = udp_request({"op": "get_return_device_params", "return_index": int(body.return_index), "device_index": int(body.device_index)}, timeout=1.2)
    params = ((params_resp or {}).get("data") or {}).get("params") or []
    signature = _make_device_signature(dname, params)
    ok = STORE.delete_device_map(signature) if STORE.enabled else False
    return {"ok": ok, "signature": signature, "backend": STORE.backend}


class ReturnDeviceParamBody(BaseModel):
    return_index: int
    device_index: int
    param_index: int
    value: float


@app.post("/op/return/device/param")
def op_return_device_param(op: ReturnDeviceParamBody) -> Dict[str, Any]:
    msg = {"op": "set_return_device_param", **op.dict()}
    resp = udp_request(msg, timeout=1.0)
    if not resp:
        raise HTTPException(504, "No reply from Ableton Remote Script")
    try:
        asyncio.create_task(broker.publish({"event": "return_device_param_changed", "return": op.return_index, "device": op.device_index, "param": op.param_index}))
    except Exception:
        pass
    return resp


class LearnDeviceBody(BaseModel):
    return_index: int
    device_index: int
    resolution: int = 21
    sleep_ms: int = 25


def _make_device_signature(name: str, params: list[dict]) -> str:
    param_names = ",".join([str(p.get("name", "")) for p in params])
    base = f"{name}|{len(params)}|{param_names}"
    return hashlib.sha1(base.encode("utf-8")).hexdigest()


@app.post("/return/device/learn")
def learn_return_device(body: LearnDeviceBody) -> Dict[str, Any]:
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

    signature = _make_device_signature(dname, params)

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
                    unit = _parse_unit_from_display(disp)
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
        ctype, labels = _classify_control_type(samples, vmin, vmax)
        gname, role, _m = _group_role_for_device(dname, name)
        fit = _fit_models(samples) if ctype == "continuous" else None
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
    groups_meta = _build_groups_from_params(learned_params, dname)
    saved = STORE.save_device_map(signature, {"name": dname, "groups": groups_meta}, learned_params)
    return {"ok": True, "signature": signature, "saved": saved, "backend": STORE.backend, "param_count": len(learned_params)}


class LearnStartBody(BaseModel):
    return_index: int
    device_index: int
    resolution: int = 41
    sleep_ms: int = 20
    mode: Optional[str] = "quick"  # quick | exhaustive


@app.post("/return/device/learn_start")
async def learn_return_device_start(body: LearnStartBody) -> Dict[str, Any]:
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
            signature = _make_device_signature(dname or f"Device {di}", params)
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
                            unit = _parse_unit_from_display(disp)
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
                    fit = _fit_models(samples) or None

                # restore
                udp_request({"op": "set_return_device_param", "return_index": ri, "device_index": di, "param_index": idx, "value": float(v0)}, timeout=0.6)
                # Group/role annotation
                gname, role, _m = _group_role_for_device(dname, name)
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
            groups_meta = _build_groups_from_params(learned_params, dname)
            # Always save locally to avoid losing long scans
            local_saved = STORE.save_device_map_local(signature, {"name": dname, "groups": groups_meta}, learned_params)
            saved = STORE.save_device_map(signature, {"name": dname, "groups": groups_meta}, learned_params)
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
    signature = _make_device_signature(dname or f"Device {di}", params)

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
        unit_guess = _parse_unit_from_display(str(p.get("display_value", "")))

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
            fit = _fit_models(samples)
            if not fit or float(fit.get("r2", 0.0)) < r2_accept:
                for t in extra_anchors[:max_extra]:
                    probe(float(t))
                fit = _fit_models(samples)

        # restore
        udp_request({"op": "set_return_device_param", "return_index": ri, "device_index": di, "param_index": idx, "value": float(v0)}, timeout=0.6)

        ctype, labels_list = _classify_control_type(samples, vmin, vmax)
        gname, role, _m = _group_role_for_device(dname, name)
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

    groups_meta = _build_groups_from_params(learned_params, dname)
    local_ok = STORE.save_device_map_local(signature, {"name": dname, "groups": groups_meta}, learned_params)
    fs_ok = STORE.save_device_map(signature, {"name": dname, "groups": groups_meta}, learned_params)
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
        unit = p.get("unit") or ( _parse_unit_from_display(str(samples[0].get("display", ""))) if samples else None )
        ctype, labels = _classify_control_type(samples, vmin, vmax)
        gname, role, _m = _group_role_for_device(data.get("device_name"), name)
        label_map = p.get("label_map")
        if ctype in ("binary", "quantized") and not label_map:
            label_map = {}
            for s in samples:
                lab = str(s.get("display", ""))
                if lab not in label_map:
                    label_map[lab] = float(s.get("value", vmin))
        fit = p.get("fit") or (_fit_models(samples) if ctype == "continuous" else None)
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
    groups_meta = _build_groups_from_params(updated_params, data.get("device_name"))
    ok_local = STORE.save_device_map_local(signature, {"name": data.get("device_name"), "groups": groups_meta}, updated_params)
    ok_fs = STORE.save_device_map(signature, {"name": data.get("device_name"), "groups": groups_meta}, updated_params)
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
    return _make_device_signature(dname or f"Device {device}", params)


def _fit_models(samples: list[dict]) -> dict | None:
    # Use numeric samples only
    pts = [(float(s["value"]), float(s["display_num"])) for s in samples if s.get("display_num") is not None]
    pts = [(x, y) for x, y in pts if math.isfinite(x) and math.isfinite(y)]
    if len(pts) < 3:
        return None
    pts.sort(key=lambda t: t[0])
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    def lin_fit(u, v):
        n = len(u)
        sx = sum(u); sy = sum(v)
        sxx = sum(a*a for a in u); sxy = sum(a*b for a,b in zip(u,v))
        den = n*sxx - sx*sx
        if den == 0: return None
        a = (n*sxy - sx*sy) / den  # slope
        b = (sy - a*sx)/n
        # R^2
        yhat = [a*t + b for t in u]
        ss_res = sum((vi - hi)**2 for vi, hi in zip(v, yhat))
        ymean = sy/n
        ss_tot = sum((vi - ymean)**2 for vi in v) or 1.0
        r2 = 1.0 - ss_res/ss_tot
        return {"type": "linear", "a": a, "b": b, "r2": r2}
    def log_fit(u, v):
        u2 = [math.log(max(1e-9, t)) for t in u]
        return lin_fit(u2, v) and {**lin_fit(u2, v), "type": "log", "x_transform": "ln(x)"}
    def exp_fit(u, v):
        # Fit ln(y) = a*x + b -> y = exp(b)*exp(a*x)
        if any(val <= 0 for val in v):
            return None
        v2 = [math.log(val) for val in v]
        fit = lin_fit(u, v2)
        if not fit: return None
        a = fit["a"]; b = fit["b"]; r2 = fit["r2"]
        return {"type": "exp", "a": a, "b": b, "r2": r2}
    cands = []
    f1 = lin_fit(xs, ys)
    if f1: cands.append(f1)
    f2 = log_fit(xs, ys)
    if f2: cands.append(f2)
    f3 = exp_fit(xs, ys)
    if f3: cands.append(f3)
    best = max(cands, key=lambda d: d["r2"]) if cands else None
    if best and best["r2"] >= 0.9:
        return best
    # Fallback: piecewise linear segments (store sorted sample pairs)
    return {"type": "piecewise", "r2": best["r2"] if best else 0.0, "points": [{"x": x, "y": y} for x,y in pts]}


@app.post("/mappings/fit")
def fit_mapping(index: Optional[int] = None, device: Optional[int] = None, signature: Optional[str] = None) -> Dict[str, Any]:
    """Fit models for a learned local mapping and update the local file.

    Provide either (index, device) to compute signature from Live, or a signature directly.
    """
    if not signature:
        if index is None or device is None:
            raise HTTPException(400, "index_device_or_signature_required")
        signature = _compute_signature_for(int(index), int(device))
    data = STORE.get_device_map_local(signature)
    if not data:
        return {"ok": False, "error": "no_local_map", "signature": signature}
    params = data.get("params") or []
    updated = 0
    for p in params:
        samples = p.get("samples") or []
        fit = _fit_models(samples)
        if fit:
            p["fit"] = fit
            updated += 1
    ok = STORE.save_device_map_local(signature, {"name": data.get("device_name")}, params)
    return {"ok": ok, "signature": signature, "updated": updated}


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
    if ftype == "linear":
        a = float(fit.get("a", 1.0)); b = float(fit.get("b", 0.0))
        x = t(a, b, target_y)
    elif ftype == "log":
        a = float(fit.get("a", 1.0)); b = float(fit.get("b", 0.0))
        # y = a*ln(x)+b -> x = exp((y-b)/a)
        x = math.exp((target_y - b)/a) if a != 0 else vmin
    elif ftype == "exp":
        # ln(y) = a*x + b -> x = (ln(y)-b)/a
        a = float(fit.get("a", 1.0)); b = float(fit.get("b", 0.0))
        if target_y <= 0:
            x = vmin
        else:
            x = (math.log(target_y) - b)/a if a != 0 else vmin
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


@app.post("/op/return/param_by_name")
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
    # Try exact param match by name
    param_name = str(cur.get("name", ""))
    learned = None
    if mapping and isinstance(mapping.get("params"), list):
        for mp in mapping["params"]:
            if str(mp.get("name", "")).lower() == param_name.lower():
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

    # Auto-enable group masters for dependents (except Freeze)
    try:
        if learned:
            role = (learned.get("role") or "").lower()
            gname = (learned.get("group") or "").lower()
            if role == "dependent" and gname not in ("global", "output") and "freeze" not in gname:
                # Resolve master name from stored groups
                groups = (mapping.get("groups") or []) if mapping else []
                master_name = None
                for g in groups:
                    deps = [str(d.get("name","")) for d in (g.get("dependents") or [])]
                    if any(param_name.lower() == dn.lower() for dn in deps):
                        mref = g.get("master") or {}
                        master_name = str(mref.get("name")) if mref else None
                        break
                if not master_name and " " in param_name:
                    master_name = param_name.rsplit(" ", 1)[0] + " On"
                # Config override: allow dependent-specific master target value
                desired_val = None
                try:
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
                    dm = rules.get("dependent_master_values") or {}
                    if param_name in dm:
                        desired_val = float(dm[param_name])
                except Exception:
                    desired_val = None
                if master_name:
                    for p in p_list:
                        if str(p.get("name","")) .lower()== master_name.lower():
                            master_idx = int(p.get("index", 0))
                            mmin = float(p.get("min", 0.0)); mmax = float(p.get("max", 1.0))
                            mval = desired_val if desired_val is not None else (mmax if mmax >= 1.0 else 1.0)
                            udp_request({"op": "set_return_device_param", "return_index": ri, "device_index": di, "param_index": master_idx, "value": float(mval)}, timeout=0.8)
                            break
    except Exception:
        pass

    # Compute candidate value in [vmin..vmax]
    x = vmin
    if label and learned:
        # find sample matching label (case-insensitive)
        for s in learned.get("samples", []) or []:
            if str(s.get("display", "")).strip().lower() == label.lower():
                x = float(s.get("value", vmin))
                break
    elif target_y is not None and learned:
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
    job = LEARN_JOBS.get(id)
    if not job:
        return {"ok": False, "error": "unknown_job"}
    return {"ok": True, **job}


@app.post("/op/mixer")
def op_mixer(op: MixerOp) -> Dict[str, Any]:
    msg = {"op": "set_mixer", **op.dict()}
    resp = udp_request(msg, timeout=1.0)
    if not resp:
        raise HTTPException(504, "No reply from Ableton Remote Script")
    # publish SSE event (fire and forget)
    try:
        asyncio.create_task(broker.publish({"event": "mixer_changed", "track": op.track_index, "field": op.field}))
    except Exception:
        pass
    return resp


@app.post("/op/send")
def op_send(op: SendOp) -> Dict[str, Any]:
    msg = {"op": "set_send", **op.dict()}
    resp = udp_request(msg, timeout=1.0)
    if not resp:
        raise HTTPException(504, "No reply from Ableton Remote Script")
    try:
        asyncio.create_task(broker.publish({"event": "send_changed", "track": op.track_index, "send_index": op.send_index}))
    except Exception:
        pass
    return resp


@app.post("/op/device/param")
def op_device_param(op: DeviceParamOp) -> Dict[str, Any]:
    msg = {"op": "set_device_param", **op.dict()}
    resp = udp_request(msg, timeout=1.0)
    if not resp:
        raise HTTPException(504, "No reply from Ableton Remote Script")
    try:
        asyncio.create_task(broker.publish({"event": "device_param_changed", "track": op.track_index, "device": op.device_index, "param": op.param_index}))
    except Exception:
        pass
    return resp


@app.post("/op/volume_db")
def op_volume_db(body: VolumeDbBody) -> Dict[str, Any]:
    float_value = db_to_live_float(body.db)
    msg = {"op": "set_mixer", "track_index": int(body.track_index), "field": "volume", "value": float_value}
    resp = udp_request(msg, timeout=1.0)
    if not resp:
        raise HTTPException(504, "No reply from Ableton Remote Script")
    try:
        asyncio.create_task(broker.publish({"event": "mixer_changed", "track": int(body.track_index), "field": "volume"}))
    except Exception:
        pass
    return resp


@app.post("/op/select_track")
def op_select_track(body: SelectTrackBody) -> Dict[str, Any]:
    msg = {"op": "select_track", "track_index": int(body.track_index)}
    resp = udp_request(msg, timeout=1.0)
    if not resp:
        raise HTTPException(504, "No reply from Ableton Remote Script")
    try:
        asyncio.create_task(broker.publish({"event": "selection_changed", "track": int(body.track_index)}))
    except Exception:
        pass
    return resp


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

        print(f"DEBUG: Parsed volume command - track={track_index}, target={target}, raw='{volume_cmd['raw_value']}'")
        print(f"DEBUG: Converted {target} dB to Live float {float_value}")

        msg = {"op": "set_mixer", "track_index": track_index, "field": "volume", "value": float_value}
        if not body.confirm:
            return {"ok": True, "preview": msg, "summary": f"Set Track {track_index} volume to {target:g} dB" + (" (warning: >0 dB may clip)" if warn else "")}
        resp = udp_request(msg, timeout=1.0)
        # Publish SSE so UI tooltips/details refresh immediately
        try:
            asyncio.create_task(broker.publish({"event": "mixer_changed", "track": track_index, "field": "volume"}))
        except Exception:
            pass
        summ = f"Set Track {track_index} volume to {target:g} dB"
        if warn:
            summ += " (warning: >0 dB may clip)"
        return {"ok": bool(resp and resp.get("ok", True)), "resp": resp, "summary": summ}

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
            asyncio.create_task(broker.publish({"event": "send_changed", "track": track_index, "send_index": si}))
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
            asyncio.create_task(broker.publish({"event": "send_changed", "track": track_index, "send_index": si}))
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
            asyncio.create_task(broker.publish({"event": "mixer_changed", "track": track_index, "field": "pan"}))
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
            asyncio.create_task(broker.publish({"event": "mixer_changed", "track": track_index, "field": "pan"}))
        except Exception:
            pass
        return {"ok": bool(resp and resp.get("ok", True)), "resp": resp, "summary": f"Set Track {track_index} pan to {label}"}

    try:
        from llm_daw import interpret_daw_command  # type: ignore
    except Exception as e:
        raise HTTPException(500, f"NLP module not available: {e}")

    intent = interpret_daw_command(text_lc, model_preference=body.model, strict=body.strict)

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

    # Fallback: return intent for UI to decide
    return {
        "ok": False,
        "reason": "unsupported_intent_for_auto_execute",
        "intent": intent,
        "summary": "I can auto-execute only absolute track volume right now."
    }


@app.post("/op/undo_last")
def undo_last() -> Dict[str, Any]:
    """Undo the last successful mixer change (volume/pan) if previous value is known."""
    while UNDO_STACK:
        entry = UNDO_STACK.pop()
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
            REDO_STACK.append({"key": entry.get("key"), "field": field, "track_index": track_index, "prev": msg["value"], "new": entry.get("new")})
            return {"ok": True, "undone": entry, "resp": resp}
        else:
            return {"ok": False, "error": "undo_send_failed", "attempt": entry}
    return {"ok": False, "error": "nothing_to_undo"}


@app.post("/op/redo_last")
def redo_last() -> Dict[str, Any]:
    """Re-apply the last undone mixer change if available."""
    while REDO_STACK:
        entry = REDO_STACK.pop()
        new_val = entry.get("new")
        track_index = entry.get("track_index")
        field = entry.get("field")
        if new_val is None or track_index is None or field not in ("volume", "pan"):
            continue
        msg = {"op": "set_mixer", "track_index": int(track_index), "field": field, "value": float(new_val)}
        resp = udp_request(msg, timeout=1.0)
        if resp and resp.get("ok", True):
            LAST_SENT[_key(field, int(track_index))] = float(new_val)
            # Add corresponding undo entry so we can undo the redo
            UNDO_STACK.append({"key": entry.get("key"), "field": field, "track_index": track_index, "prev": entry.get("prev"), "new": new_val})
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
        return {"ok": False, "errors": errors, "raw_intent": raw_intent}

    return {"ok": True, "intent": canonical.dict(), "raw_intent": raw_intent}
class SelectTrackBody(BaseModel):
    track_index: int
