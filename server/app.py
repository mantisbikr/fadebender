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
from server.cloud.enrich_queue import enqueue_preset_enrich
import hashlib
import math
from server.volume_parser import parse_volume_command
_MASTER_DEDUP: dict[str, tuple[float, float]] = {}

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
    # Binary if there are two or fewer distinct labels (even if numeric-like)
    # This captures toggles that display "0.0"/"1.0" and were misclassified as continuous.
    if len(labels) <= 2:
        return ("binary", labels)
    # Quantized if small label set and not mostly numeric
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

# Initialize Vertex AI (if env configured)
try:
    import vertexai  # type: ignore
    _VERTEX_INITED = False
    def _vertex_init_once() -> None:
        global _VERTEX_INITED
        if _VERTEX_INITED:
            return
        project = os.getenv("VERTEX_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT")
        location = os.getenv("VERTEX_LOCATION") or "us-central1"
        if project:
            try:
                vertexai.init(project=project, location=location)
                _VERTEX_INITED = True
            except Exception:
                # Defer errors to first model call
                _VERTEX_INITED = False
except Exception:
    def _vertex_init_once() -> None:
        return


def _json_lenient_parse(text: str) -> Optional[Dict[str, Any]]:
    """Try to parse JSON with light repairs for common LLM artifacts.

    Repairs:
    - Strip markdown code fences
    - Normalize smart quotes to ASCII
    - Remove trailing commas before } or ]
    - Try largest-brace substring
    - As last resort, convert single quotes to double quotes (heuristic)
    """
    import re as _r
    t = str(text or "")
    if not t:
        return None
    # Strip code fences
    if t.strip().startswith("```"):
        parts = t.split("```")
        if len(parts) >= 3:
            t = parts[1] if parts[0].strip() == "" else parts[1]
    # Normalize quotes
    t = t.replace("“", '"').replace("”", '"').replace("‟", '"').replace("’", "'").replace("‘", "'")
    # Remove trailing commas
    t = _r.sub(r",\s*(\}|\])", r"\1", t)
    # Try direct parse
    try:
        import json as _json
        return _json.loads(t)
    except Exception:
        pass
    # Try largest brace substring
    i, j = t.find("{"), t.rfind("}")
    if i >= 0 and j > i:
        s = t[i:j+1]
        s = _r.sub(r",\s*(\}|\])", r"\1", s)
        try:
            import json as _json
            return _json.loads(s)
        except Exception:
            pass
    # Heuristic: convert single quotes to double quotes (may over-correct)
    t2 = t
    if t2.count('"') < 2 and t2.count("'") >= 4:
        t2 = t2.replace("'", '"')
        t2 = _r.sub(r",\s*(\}|\])", r"\1", t2)
        try:
            import json as _json
            return _json.loads(t2)
        except Exception:
            return None
    return None


def _preset_metadata_schema() -> Dict[str, Any]:
    """JSON schema for LLM response to enforce strict JSON output."""
    return {
        "type": "object",
        "properties": {
            "description": {
                "type": "object",
                "properties": {
                    "what": {"type": "string"},
                    "when": {"type": "array", "items": {"type": "string"}},
                    "why": {"type": "string"},
                },
                "required": ["what"],
                "additionalProperties": True,
            },
            "audio_engineering": {"type": "object"},
            "natural_language_controls": {"type": "object"},
            "warnings": {"type": "object"},
            "genre_tags": {"type": "array", "items": {"type": "string"}},
            "subcategory": {"type": "string"},
        },
        "additionalProperties": True,
    }


def _basic_metadata_fallback(device_name: str, device_type: str, parameter_values: Dict[str, float]) -> Dict[str, Any]:
    """Heuristic fallback metadata when LLM JSON is unavailable."""
    desc = {
        "what": f"{device_name} preset for {device_type}",
        "when": ["general purpose", "subtle ambience"],
        "why": "Automatically generated fallback without LLM."
    }
    # Try to pull a short rationale from local KB to extend the 'why' section
    def _kb_excerpt(dtype: str) -> str:
        try:
            import pathlib
            base = pathlib.Path(os.getcwd()) / "knowledge" / "audio-fundamentals"
            fname = None
            if dtype.lower() == "reverb":
                fname = base / "deep_audio_engineering_reverb.md"
            elif dtype.lower() == "delay":
                fname = base / "deep_audio_engineering_delay.md"
            if fname and fname.exists():
                txt = fname.read_text(encoding="utf-8", errors="ignore")
                return txt.strip().replace("\n", " ")[:600]
        except Exception:
            pass
        return "This preset leverages time-domain processing and frequency-domain shaping to achieve the desired psychoacoustic perception in a mix."

    ae: Dict[str, Any] = {}
    if device_type == "reverb":
        decay = None
        # Try common names
        for k in ("Decay", "Decay Time", "DecayTime"):
            if k in parameter_values:
                decay = float(parameter_values[k]); break
        predelay = None
        for k in ("Predelay", "PreDelay", "Pre-Delay"):
            if k in parameter_values:
                predelay = float(parameter_values[k]); break
        ae = {
            "space_type": "hall" if (decay or 0) >= 3.5 else "room",
            "decay_time": f"~{decay:.2f}s" if decay is not None else None,
            "predelay": f"~{predelay:.0f} ms" if predelay is not None else None,
            "frequency_character": "neutral",
            "stereo_width": "wide",
            "diffusion": "smooth",
            "use_cases": [
                {"source": "vocal", "context": "ballad", "send_level": "15-25%", "notes": "Fallback guidance"}
            ],
        }
    # Build at least 4 generic use cases when LLM metadata is unavailable
    default_use_cases = [
        {"source": "lead vocal", "context": "ballad", "send_level": "15-25%", "send_level_rationale": "maintain intelligibility while adding space", "eq_prep": "HPF 100 Hz, gentle de-ess", "eq_rationale": "reduce mud and sibilance feeding the reverb", "notes": "consider a pre-delay of 20-40 ms to preserve consonants"},
        {"source": "electric guitar", "context": "solo", "send_level": "10-20%", "send_level_rationale": "share space without washing transients", "eq_prep": "HPF 120 Hz, tilt -1 dB @ 4 kHz", "eq_rationale": "avoid low-end buildup and harshness", "notes": "wider stereo helpful for size, beware mono collapse"},
        {"source": "synth pad", "context": "ambient", "send_level": "25-40%", "send_level_rationale": "embrace tail for texture", "eq_prep": "HPF 80 Hz", "eq_rationale": "protect low-end clarity", "notes": "increase diffusion for smoother tail"},
        {"source": "drums", "context": "room enhancement", "send_level": "5-12%", "send_level_rationale": "enhance room sense without blurring hits", "eq_prep": "HPF 150 Hz, notch 500 Hz", "eq_rationale": "control boxiness", "notes": "short decay <1.2s for punch"},
    ]

    return {
        "description": desc,
        "audio_engineering": {
            **ae,
            "use_cases": default_use_cases if device_type == "reverb" else default_use_cases[:4],
        },
        "natural_language_controls": {},
        "warnings": {},
        "genre_tags": [],
        "subcategory": ae.get("space_type") if isinstance(ae, dict) else "unknown",
        # Expand 'why' with KB excerpt to meet minimum richness
        "description": {
            **desc,
            "why": (desc.get("why") or "") + " " + _kb_excerpt(device_type)
        }
    }

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/llm/health")
def llm_health() -> Dict[str, Any]:
    """Quick LLM health: show resolved model/project/location and a JSON echo test.

    Does not consume many tokens; intended for debugging env issues.
    """
    import traceback
    model_name = os.getenv("LLM_MODEL") or os.getenv("VERTEX_MODEL") or "gemini-2.5-flash"
    project = os.getenv("VERTEX_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("VERTEX_LOCATION") or "us-central1"
    ok = False
    error = None
    tried = None
    try:
        _vertex_init_once()
        from vertexai.generative_models import GenerativeModel  # type: ignore
        m = GenerativeModel(model_name)
        prompt = "Return a JSON object: {\"ok\": true, \"note\": \"healthcheck\"}"
        r = m.generate_content(prompt, generation_config={"response_mime_type": "application/json", "max_output_tokens": 64, "temperature": 0.0})
        txt = getattr(r, "text", "")
        tried = bool(txt)
        if txt:
            import json as _json
            data = _json.loads(txt)
            if isinstance(data, dict) and data.get("ok") is True:
                ok = True
        if not ok:
            error = "unexpected_response"
    except Exception as e:
        error = f"{e}\n{traceback.format_exc()}"
    return {"ok": ok, "model": model_name, "project": project, "location": location, "tried_text": tried, "error": error}


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
BACKFILL_JOBS: dict[str, dict] = {}

# --- Auto-capture dedupe for UI polling ---
_CAPTURE_DEDUPE: dict[str, float] = {}

def _should_capture_signature(sig: str, ttl_sec: float = 60.0) -> bool:
    """Return True if we should trigger capture for this signature now.

    Prevents repeated auto-capture on frequent UI polls for the same device
    signature. TTL defaults to 60s; capture itself is idempotent and will
    skip when sufficient values already exist.
    """
    try:
        now = time.time()
        last = _CAPTURE_DEDUPE.get(sig)
        if last is not None and (now - last) < ttl_sec:
            return False
        _CAPTURE_DEDUPE[sig] = now
        return True
    except Exception:
        return True

@app.get("/events")
async def events():
    q = await broker.subscribe()
    async def event_gen():
        # Bootstrap: emit current master mixer values so clients seed immediately
        try:
            resp = udp_request({"op": "get_master_status"}, timeout=0.6)
            data = (resp.get("data") if isinstance(resp, dict) else resp) if resp else None
            mix = (data or {}).get("mixer") if isinstance(data, dict) else None
            if isinstance(mix, dict):
                for fld in ("volume", "pan", "cue"):
                    val = mix.get(fld)
                    if isinstance(val, (int, float)):
                        payload = json.dumps({"event": "master_mixer_changed", "field": fld, "value": float(val)})
                        yield "data: " + payload + "\n\n"
        except Exception:
            pass
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


@app.get("/health")
def server_health() -> Dict[str, Any]:
    """Simple controller health endpoint for UI status."""
    return {"status": "healthy", "service": "controller"}


# ==================== Transport ====================

@app.get("/transport")
def get_transport_state() -> Dict[str, Any]:
    resp = udp_request({"op": "get_transport"}, timeout=1.0)
    if not resp:
        return {"ok": False, "error": "no response"}
    data = resp.get("data") if isinstance(resp, dict) else None
    if data is None:
        data = resp
    return {"ok": True, "data": data}


class TransportBody(BaseModel):
    action: str  # play|stop|record|metronome|tempo
    value: Optional[float] = None  # used for tempo


@app.post("/transport")
def set_transport(body: TransportBody) -> Dict[str, Any]:
    msg: Dict[str, Any] = {"op": "set_transport", "action": str(body.action)}
    if body.value is not None:
        msg["value"] = float(body.value)
    resp = udp_request(msg, timeout=1.0)
    if not resp:
        raise HTTPException(504, "no response from remote script")
    # broadcast minimal event
    try:
        schedule_emit({"event": "transport_changed", "action": str(body.action)})
    except Exception:
        pass
    return resp if isinstance(resp, dict) else {"ok": True, "data": resp}


# ==================== Master ====================

@app.get("/master/status")
def get_master_status() -> Dict[str, Any]:
    resp = udp_request({"op": "get_master_status"}, timeout=1.0)
    if not resp:
        return {"ok": False, "error": "no response"}
    data = resp.get("data") if isinstance(resp, dict) else None
    if data is None:
        data = resp
    # Assist UI: emit one-shot SSE with current values so Master tab seeds instantly
    try:
        mix = (data or {}).get("mixer") if isinstance(data, dict) else None
        if isinstance(mix, dict):
            for fld in ("volume", "pan", "cue"):
                val = mix.get(fld)
                if isinstance(val, (int, float)):
                    schedule_emit({"event": "master_mixer_changed", "field": fld, "value": float(val)})
    except Exception:
        pass
    return {"ok": True, "data": data}


class MasterMixerBody(BaseModel):
    field: str  # 'volume' | 'pan' | 'cue'
    value: float


@app.post("/op/master/mixer")
def op_master_mixer(body: MasterMixerBody) -> Dict[str, Any]:
    if body.field not in ("volume", "pan", "cue"):
        raise HTTPException(400, "invalid_field")
    msg = {"op": "set_master_mixer", "field": body.field, "value": float(body.value)}
    resp = udp_request(msg, timeout=1.0)
    if not resp:
        raise HTTPException(504, "No reply from Ableton Remote Script")
    try:
        schedule_emit({"event": "master_mixer_changed", "field": body.field, "value": float(body.value)})
    except Exception:
        pass
    return resp


@app.get("/config")
def app_config() -> Dict[str, Any]:
    """Expose a subset of app config to clients (UI + aliases)."""
    ui = get_ui_settings()
    aliases = get_send_aliases()
    debug = get_debug_settings()
    return {"ok": True, "ui": ui, "aliases": {"sends": aliases}, "debug": debug}


@app.post("/config/update")
def app_config_update(body: Dict[str, Any]) -> Dict[str, Any]:
    ui_in = (body or {}).get("ui") or {}
    aliases_in = ((body or {}).get("aliases") or {}).get("sends") or {}
    debug_in = (body or {}).get("debug") or {}
    ui = set_ui_settings(ui_in) if ui_in else get_ui_settings()
    aliases = set_send_aliases(aliases_in) if aliases_in else get_send_aliases()
    debug = set_debug_settings(debug_in) if debug_in else get_debug_settings()
    saved = cfg_save()
    return {"ok": True, "saved": saved, "ui": ui, "aliases": {"sends": aliases}, "debug": debug}


@app.post("/config/reload")
def app_config_reload() -> Dict[str, Any]:
    cfg = cfg_reload()
    plc = reload_param_learn_config()
    preg = reload_param_registry()
    return {"ok": True, "config": cfg, "param_learn": plc, "param_registry": preg}


@app.get("/param_registry")
def get_param_registry_endpoint() -> Dict[str, Any]:
    """Expose parameter registry for track/sends mappings to clients."""
    try:
        reg = get_param_registry()
        return {"ok": True, "registry": reg}
    except Exception as e:
        return {"ok": False, "error": str(e)}


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


# ==================== Track Routing & Monitor ====================

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


@app.get("/track/routing")
def get_track_routing(index: int) -> Dict[str, Any]:
    """Get current routing + available options for a track (for LLM disambiguation)."""
    resp = udp_request({"op": "get_track_routing", "track_index": int(index)}, timeout=1.0)
    if not resp:
        return {"ok": False, "error": "no response"}
    data = resp.get("data") if isinstance(resp, dict) else None
    if data is None:
        data = resp
    return {"ok": True, "data": data}


@app.post("/track/routing")
def set_track_routing(body: TrackRoutingSetBody) -> Dict[str, Any]:
    """Set routing and/or monitor state for a track. Any field can be omitted to leave unchanged.

    Delegates to Remote Script op "set_track_routing" with provided keys only.
    """
    msg: Dict[str, Any] = {"op": "set_track_routing", "track_index": int(body.track_index)}
    for k, v in body.dict().items():
        if k == "track_index":
            continue
        if v is not None:
            msg[k] = v
    resp = udp_request(msg, timeout=1.2)
    if not resp:
        raise HTTPException(504, "no response from remote script")
    try:
        schedule_emit({"event": "track_routing_changed", "track_index": int(body.track_index)})
    except Exception:
        pass
    return resp if isinstance(resp, dict) else {"ok": True, "data": resp}


@app.get("/returns")
def get_returns() -> Dict[str, Any]:
    resp = udp_request({"op": "get_return_tracks"}, timeout=1.0)
    if not resp:
        return {"ok": False, "error": "no response"}
    data = resp.get("data") if isinstance(resp, dict) else None
    if data is None:
        data = resp
    return {"ok": True, "data": data}


@app.get("/return/sends")
def get_return_sends(index: int) -> Dict[str, Any]:
    """Read sends for a return track (if supported by bridge)."""
    try:
        resp = udp_request({"op": "get_return_sends", "return_index": int(index)}, timeout=1.0)
        if not resp:
            return {"ok": False, "error": "no response"}
        data = resp.get("data") if isinstance(resp, dict) else None
        if data is None:
            data = resp
        return {"ok": True, "data": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ==================== Return Routing & Sends Mode ====================

class ReturnRoutingSetBody(BaseModel):
    return_index: int
    audio_to_type: Optional[str] = None
    audio_to_channel: Optional[str] = None
    sends_mode: Optional[str] = None  # "pre" | "post" (optional capability)


@app.get("/return/routing")
def get_return_routing(index: int) -> Dict[str, Any]:
    """Get return track routing (Audio To) and available options if provided by RS."""
    resp = udp_request({"op": "get_return_routing", "return_index": int(index)}, timeout=1.0)
    if not resp:
        return {"ok": False, "error": "no response"}
    data = resp.get("data") if isinstance(resp, dict) else None
    if data is None:
        data = resp
    return {"ok": True, "data": data}


@app.post("/return/routing")
def set_return_routing(body: ReturnRoutingSetBody) -> Dict[str, Any]:
    """Set return Audio To destination and/or sends mode if supported."""
    msg: Dict[str, Any] = {"op": "set_return_routing", "return_index": int(body.return_index)}
    for k, v in body.dict().items():
        if k == "return_index":
            continue
        if v is not None:
            msg[k] = v
    resp = udp_request(msg, timeout=1.2)
    if not resp:
        raise HTTPException(504, "no response from remote script")
    try:
        schedule_emit({"event": "return_routing_changed", "return_index": int(body.return_index)})
    except Exception:
        pass
    return resp if isinstance(resp, dict) else {"ok": True, "data": resp}


@app.get("/return/devices")
def get_return_devices(index: int) -> Dict[str, Any]:
    resp = udp_request({"op": "get_return_devices", "return_index": int(index)}, timeout=1.0)
    if not resp:
        return {"ok": False, "error": "no response"}
    data = resp.get("data") if isinstance(resp, dict) else None
    if data is None:
        data = resp
    return {"ok": True, "data": data}


# ---------------- Track devices (Phase A - minimal) ----------------

@app.get("/track/devices")
def get_track_devices(index: int) -> Dict[str, Any]:
    resp = udp_request({"op": "get_track_devices", "track_index": int(index)}, timeout=1.0)
    if not resp:
        return {"ok": False, "error": "no response"}
    data = resp.get("data") if isinstance(resp, dict) else resp
    return {"ok": True, "data": data}


@app.get("/track/device/params")
def get_track_device_params(index: int, device: int) -> Dict[str, Any]:
    resp = udp_request({"op": "get_track_device_params", "track_index": int(index), "device_index": int(device)}, timeout=1.0)
    if not resp:
        return {"ok": False, "error": "no response"}
    data = resp.get("data") if isinstance(resp, dict) else resp
    return {"ok": True, "data": data}


class TrackDeviceParamBody(BaseModel):
    track_index: int
    device_index: int
    param_index: int
    value: float


@app.post("/op/track/device/param")
def set_track_device_param(body: TrackDeviceParamBody) -> Dict[str, Any]:
    msg = {"op": "set_track_device_param", "track_index": int(body.track_index), "device_index": int(body.device_index), "param_index": int(body.param_index), "value": float(body.value)}
    resp = udp_request(msg, timeout=1.0)
    if not resp:
        raise HTTPException(504, "No reply from Ableton Remote Script")
    # optional SSE
    try:
        schedule_emit({"event": "device_param_changed", "scope": "track", "track": int(body.track_index), "device_index": int(body.device_index), "param_index": int(body.param_index), "value": float(body.value)})
    except Exception:
        pass
    return resp if isinstance(resp, dict) else {"ok": True}


# ---------------- Master devices (Phase A - minimal) ----------------

@app.get("/master/devices")
def get_master_devices_endpoint() -> Dict[str, Any]:
    resp = udp_request({"op": "get_master_devices"}, timeout=1.0)
    if not resp:
        return {"ok": False, "error": "no response"}
    data = resp.get("data") if isinstance(resp, dict) else resp
    return {"ok": True, "data": data}


@app.get("/master/device/params")
def get_master_device_params_endpoint(device: int) -> Dict[str, Any]:
    resp = udp_request({"op": "get_master_device_params", "device_index": int(device)}, timeout=1.0)
    if not resp:
        return {"ok": False, "error": "no response"}
    data = resp.get("data") if isinstance(resp, dict) else resp
    return {"ok": True, "data": data}


class MasterDeviceParamBody(BaseModel):
    device_index: int
    param_index: int
    value: float


@app.post("/op/master/device/param")
def set_master_device_param(body: MasterDeviceParamBody) -> Dict[str, Any]:
    msg = {"op": "set_master_device_param", "device_index": int(body.device_index), "param_index": int(body.param_index), "value": float(body.value)}
    resp = udp_request(msg, timeout=1.0)
    if not resp:
        raise HTTPException(504, "No reply from Ableton Remote Script")
    try:
        schedule_emit({"event": "master_device_param_changed", "device_index": int(body.device_index), "param_index": int(body.param_index), "value": float(body.value)})
    except Exception:
        pass
    return resp if isinstance(resp, dict) else {"ok": True}


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
async def get_return_device_map(index: int, device: int) -> Dict[str, Any]:
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
    live_params = ((params_resp or {}).get("data") or {}).get("params") or []
    signature = _make_device_signature(dname, live_params)
    backend = STORE.backend
    exists = False
    device_type = _detect_device_type(live_params, dname)

    # Ensure base mapping exists immediately (synchronous) for responsive UI
    try:
        await _ensure_device_mapping(signature, device_type, live_params)
    except Exception:
        pass

    # New base mapping (param_structure) existence check
    mapping_exists = False
    try:
        new_map = STORE.get_device_mapping(signature)
        mapping_exists = bool(new_map)
    except Exception:
        mapping_exists = False

    try:
        # Check legacy learned mapping (with samples) for backwards compatibility
        if STORE.enabled:
            m = STORE.get_device_map(signature)
        else:
            m = STORE.get_device_map_local(signature)

        print(f"[DEBUG] get_device_map returned: {type(m)}, is_none: {m is None}")
        learned_params = (m.get("params") or []) if m else []
        if isinstance(learned_params, list):
            # Consider learned only if at least one param has >= 3 samples
            for p in learned_params:
                sm = p.get("samples") or []
                if isinstance(sm, list) and len(sm) >= 3:
                    exists = True
                    print(f"[DEBUG] Found learned param: {p.get('name')} with {len(sm)} samples")
                    break
        print(f"[DEBUG] Final exists (learned): {exists}")
    except Exception as e:
        print(f"[DEBUG] Exception: {e}")
        exists = False

    # Auto-capture preset + ensure device mapping in background (non-blocking)
    # Always trigger when we have device_type and name; capture flow is idempotent
    # and will skip if a preset with sufficient values already exists.
    if device_type and dname and _should_capture_signature(signature):
        try:
            asyncio.create_task(_auto_capture_preset(index, device, dname, device_type, signature, live_params))
        except Exception:
            pass

    # Top-level existence should reflect either new base mapping OR learned mapping
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


@app.get("/return/device/map_summary")
async def get_return_device_map_summary(index: int, device: int) -> Dict[str, Any]:
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
    # Also detect device type from live params so we can optionally
    # trigger auto-capture when a learned mapping exists.
    device_type = _detect_device_type(params, dname)
    data = None
    # Ensure base mapping exists immediately so first UI poll goes green
    try:
        await _ensure_device_mapping(signature, device_type, params)
    except Exception:
        pass

    try:
        # Prefer legacy learned mapping summary when available
        if STORE.enabled:
            m = STORE.get_device_map(signature)
        else:
            m = STORE.get_device_map_local(signature)
        if m:
            plist = []
            learned_exists = False
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
                try:
                    if not learned_exists and len(p.get("samples") or []) >= 3:
                        learned_exists = True
                except Exception:
                    pass
            # Also consider base mapping presence when learned samples are empty
            mapping_exists_flag = False
            try:
                nm = STORE.get_device_mapping(signature)
                mapping_exists_flag = bool(nm)
            except Exception:
                mapping_exists_flag = False
            data = {
                "device_name": m.get("device_name") or dname,
                "signature": signature,
                "groups": m.get("groups") or [],
                "params": plist,
                "exists": bool(learned_exists or mapping_exists_flag),
                "learned_exists": learned_exists,
                "mapping_exists": mapping_exists_flag,
            }
        else:
            # Fall back to new base mapping existence; provide minimal summary
            new_map = STORE.get_device_mapping(signature)
            if new_map:
                ps = new_map.get("param_structure") or []
                data = {
                    "device_name": dname,
                    "signature": signature,
                    "params": [{
                        "name": p.get("name"),
                        "index": p.get("index"),
                        "min": p.get("min"),
                        "max": p.get("max"),
                        "sample_count": 0,
                    } for p in ps],
                    "exists": True,
                    "mapping_exists": True,
                    "learned_exists": False,
                }
    except Exception as e:
        return {"ok": False, "error": str(e), "backend": backend}
    # If neither learned nor base mapping is persisted, derive a minimal summary from live params
    if data is None and params:
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
            "exists": True,              # Treat as mapped for UI purposes
            "mapping_exists": False,
            "learned_exists": False,
        }
    # Unconditionally trigger background preset auto-capture + mapping ensure (deduped).
    if device_type and dname and _should_capture_signature(signature):
        try:
            asyncio.create_task(_auto_capture_preset(index, device, dname, device_type, signature, params))
        except Exception:
            pass
    # Top-level exists mirrors data.exists for convenience
    top_exists = bool((data or {}).get("exists")) if data else False
    return {"ok": True, "backend": backend, "signature": signature, "exists": top_exists, "data": data}


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
        schedule_emit({"event": "return_device_param_changed", "return": op.return_index, "device": op.device_index, "param": op.param_index})
    except Exception:
        pass
    return resp


class ReturnSendBody(BaseModel):
    return_index: int
    send_index: int
    value: float


@app.post("/op/return/send")
def op_return_send(body: ReturnSendBody) -> Dict[str, Any]:
    """Set a return track's send value (if supported by bridge)."""
    msg = {
        "op": "set_return_send",
        "return_index": int(body.return_index),
        "send_index": int(body.send_index),
        "value": float(body.value),
    }
    resp = udp_request(msg, timeout=1.0)
    if not resp:
        raise HTTPException(504, "No reply from Ableton Remote Script")
    try:
        schedule_emit({"event": "return_send_changed", "return": int(body.return_index), "send_index": int(body.send_index)})
    except Exception:
        pass
    return resp


# ---------------- Device Mapping Import (LLM + Numeric Fits) ----------------

class MappingImportBody(BaseModel):
    signature: str
    device_type: Optional[str] = None
    grouping: Optional[dict] = None
    params_meta: Optional[list] = None
    sources: Optional[dict] = None
    analysis_status: Optional[str] = None  # e.g., "partial_fits" | "analyzed"


@app.post("/device_mapping/import")
def import_device_mapping(body: MappingImportBody) -> Dict[str, Any]:
    """Merge provided mapping analysis data into device_mappings for a signature.

    - Creates mapping doc if missing via save_device_mapping()
    - Merges top-level fields: device_type, grouping, params_meta, sources, analysis_status
    - For params_meta, replaces the entire list (simple & safe)
    Requires Firestore to be enabled in MappingStore.
    """
    sig = body.signature.strip()
    if not sig:
        raise HTTPException(400, "signature required")

    if not STORE.enabled:
        return {"ok": False, "error": "firestore_disabled"}

    existing = STORE.get_device_mapping(sig) or {}
    updated: Dict[str, Any] = dict(existing)
    updated["device_signature"] = sig
    if body.device_type:
        updated["device_type"] = body.device_type
    if body.grouping is not None:
        updated["grouping"] = body.grouping
    if body.params_meta is not None:
        updated["params_meta"] = list(body.params_meta)
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

    ok = STORE.save_device_mapping(sig, updated)
    return {"ok": bool(ok), "signature": sig, "updated_fields": [k for k in ("device_type","grouping","params_meta","sources","analysis_status") if k in updated]}


@app.get("/device_mapping")
def get_device_mapping(signature: Optional[str] = None, index: Optional[int] = None, device: Optional[int] = None) -> Dict[str, Any]:
    """Fetch device mapping (grouping + params_meta) for a signature.

    You can provide either:
    - signature: SHA1 of structure
    - or index (return_index) and device (device_index) to derive signature from live
    """
    sig = (signature or "").strip()
    if not sig:
        # derive from live indices
        if index is None or device is None:
            raise HTTPException(400, "Provide signature or index+device")
        devs = udp_request({"op": "get_return_devices", "return_index": int(index)}, timeout=1.0)
        devices = ((devs or {}).get("data") or {}).get("devices") or []
        dname = None
        for d in devices:
            if int(d.get("index", -1)) == int(device):
                dname = str(d.get("name", f"Device {device}"))
                break
        if dname is None:
            raise HTTPException(404, "device_not_found")
        params_resp = udp_request({"op": "get_return_device_params", "return_index": int(index), "device_index": int(device)}, timeout=1.2)
        live_params = ((params_resp or {}).get("data") or {}).get("params") or []
        sig = _make_device_signature(dname, live_params)

    mapping = STORE.get_device_mapping(sig) if STORE.enabled else None
    if not mapping:
        # Return 200 with mapping_exists=False to aid UI/CLI
        return {"ok": True, "signature": sig, "mapping_exists": False}

    params_meta = mapping.get("params_meta") or []
    fitted = [p.get("name") for p in params_meta if isinstance(p, dict) and isinstance(p.get("fit"), dict)]
    missing_cont = [p.get("name") for p in params_meta if isinstance(p, dict) and (p.get("control_type") == "continuous") and (not p.get("fit"))]

    return {
        "ok": True,
        "signature": sig,
        "mapping_exists": True,
        "mapping": mapping,
        "summary": {
            "params_meta_total": len(params_meta),
            "fitted_count": len(fitted),
            "fitted_names": fitted,
            "missing_continuous": missing_cont,
        },
    }


@app.get("/device_mapping/validate")
def validate_device_mapping(signature: Optional[str] = None, index: Optional[int] = None, device: Optional[int] = None) -> Dict[str, Any]:
    """Compare mapping names (masters, dependents, params_meta) with live param names.

    Returns missing_in_live (declared in mapping but not seen live) and
    unused_in_mapping (present live but not declared in mapping).
    """
    # Resolve signature and fetch live param names
    sig = (signature or "").strip()
    if not sig:
        if index is None or device is None:
            raise HTTPException(400, "Provide signature or index+device")
        devs = udp_request({"op": "get_return_devices", "return_index": int(index)}, timeout=1.0)
        devices = ((devs or {}).get("data") or {}).get("devices") or []
        dname = None
        for d in devices:
            if int(d.get("index", -1)) == int(device):
                dname = str(d.get("name", f"Device {device}"))
                break
        if dname is None:
            raise HTTPException(404, "device_not_found")
        params_resp = udp_request({"op": "get_return_device_params", "return_index": int(index), "device_index": int(device)}, timeout=1.2)
        live_params = ((params_resp or {}).get("data") or {}).get("params") or []
        sig = _make_device_signature(dname, live_params)
    else:
        # If signature provided, still fetch live names from either cached indices (if given) or skip
        if index is not None and device is not None:
            params_resp = udp_request({"op": "get_return_device_params", "return_index": int(index), "device_index": int(device)}, timeout=1.2)
            live_params = ((params_resp or {}).get("data") or {}).get("params") or []
        else:
            live_params = []

    live_names = set(str(p.get("name", "")).strip() for p in (live_params or []))
    mapping = STORE.get_device_mapping(sig) if STORE.enabled else None
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

    return {
        "ok": True,
        "signature": sig,
        "mapping_exists": True,
        "missing_in_live": missing_in_live,
        "unused_in_mapping": unused_in_mapping,
        "counts": {"declared": len(declared), "live": len(live_names)},
    }


class SanityProbeBody(BaseModel):
    return_index: int
    device_index: int
    param_ref: str  # name substring or index string
    target_display: str
    restore: Optional[bool] = True


@app.post("/device_mapping/sanity_probe")
def sanity_probe(body: SanityProbeBody) -> Dict[str, Any]:
    """Set a param by display target using mapping, read back, and optionally restore previous value."""
    ri = int(body.return_index); di = int(body.device_index)
    # Resolve param index
    pi = _resolve_param_index(ri, di, body.param_ref)
    pr = udp_request({"op": "get_return_device_params", "return_index": ri, "device_index": di}, timeout=1.2)
    params = ((pr or {}).get("data") or {}).get("params") or []
    cur = next((p for p in params if int(p.get("index", -1)) == pi), None)
    if not cur:
        raise HTTPException(404, "param_not_found")
    vmin = float(cur.get("min", 0.0)); vmax = float(cur.get("max", 1.0))
    prev_x = float(cur.get("value", vmin))
    pname = str(cur.get("name", ""))
    # Compute signature and mapping
    sig = _compute_signature_for(ri, di)
    mapping = STORE.get_device_mapping(sig) if STORE.enabled else None
    # Target parse
    ty = _parse_target_display(body.target_display)
    if ty is None and mapping:
        # label path
        pm = next((pme for pme in (mapping.get("params_meta") or []) if str(pme.get("name", "")).lower() == pname.lower()), None)
        if pm and isinstance(pm.get("label_map"), dict):
            lm = pm.get("label_map") or {}
            for k, v in lm.items():
                if str(k).strip().lower() == body.target_display.strip().lower():
                    ty = None; prev_x = prev_x; x = max(vmin, min(vmax, float(v)))
                    udp_request({"op": "set_return_device_param", "return_index": ri, "device_index": di, "param_index": pi, "value": float(x)}, timeout=1.0)
                    break
    # Numeric path (with quick refinement)
    if ty is not None:
        x = prev_x
        pm = next((pme for pme in (mapping.get("params_meta") or []) if str(pme.get("name", "")).lower() == pname.lower()), None) if mapping else None
        if pm and isinstance(pm.get("fit"), dict):
            x = _invert_fit_to_value(pm.get("fit") or {}, float(ty), vmin, vmax)
        # initial set
        udp_request({"op": "set_return_device_param", "return_index": ri, "device_index": di, "param_index": pi, "value": float(x)}, timeout=1.0)
        # readback
        rb = udp_request({"op": "get_return_device_params", "return_index": ri, "device_index": di}, timeout=1.0)
        rps = ((rb or {}).get("data") or {}).get("params") or []
        newp = next((p for p in rps if int(p.get("index", -1)) == pi), None)
        applied_disp = str((newp or {}).get("display_value", ""))
        applied_num = _parse_target_display(applied_disp)
        # refine with small bisection if off
        if applied_num is not None:
            td = float(ty)
            err0 = td - float(applied_num)
            thresh = 0.02 * (abs(td) if td != 0 else 1.0)
            if abs(err0) > thresh:
                lo = vmin; hi = vmax; curx = x
                if err0 < 0:  # actual > target -> decrease x
                    hi = curx
                else:
                    lo = curx
                for _ in range(6):
                    mid = (lo + hi) / 2.0
                    udp_request({"op": "set_return_device_param", "return_index": ri, "device_index": di, "param_index": pi, "value": float(mid)}, timeout=1.0)
                    rb2 = udp_request({"op": "get_return_device_params", "return_index": ri, "device_index": di}, timeout=1.0)
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
    else:
        # label path already handled above; readback current
        rb = udp_request({"op": "get_return_device_params", "return_index": ri, "device_index": di}, timeout=1.0)
        rps = ((rb or {}).get("data") or {}).get("params") or []
        newp = next((p for p in rps if int(p.get("index", -1)) == pi), None)
        applied_disp = str((newp or {}).get("display_value", ""))
        applied_num = _parse_target_display(applied_disp)
    # Error report
    err = None
    td_final = _parse_target_display(body.target_display)
    if td_final is not None and applied_num is not None:
        err = float(td_final) - float(applied_num)
    # Restore if requested
    if bool(body.restore):
        udp_request({"op": "set_return_device_param", "return_index": ri, "device_index": di, "param_index": pi, "value": float(prev_x)}, timeout=1.0)
    return {"ok": True, "signature": sig, "param": pname, "applied_display": applied_disp, "error": err}


@app.get("/device_mapping/fits")
def get_device_mapping_fits(signature: Optional[str] = None, index: Optional[int] = None, device: Optional[int] = None) -> Dict[str, Any]:
    """List fitted continuous parameters (name, fit type, coeffs, r2, confidence)."""
    sig = (signature or "").strip()
    if not sig:
        if index is None or device is None:
            raise HTTPException(400, "Provide signature or index+device")
        # derive from live
        devs = udp_request({"op": "get_return_devices", "return_index": int(index)}, timeout=1.0)
        devices = ((devs or {}).get("data") or {}).get("devices") or []
        dname = None
        for d in devices:
            if int(d.get("index", -1)) == int(device):
                dname = str(d.get("name", f"Device {device}"))
                break
        if dname is None:
            raise HTTPException(404, "device_not_found")
        params_resp = udp_request({"op": "get_return_device_params", "return_index": int(index), "device_index": int(device)}, timeout=1.2)
        live_params = ((params_resp or {}).get("data") or {}).get("params") or []
        sig = _make_device_signature(dname, live_params)

    mapping = STORE.get_device_mapping(sig) if STORE.enabled else None
    if not mapping:
        return {"ok": True, "signature": sig, "mapping_exists": False, "fits": []}
    fits = []
    for pm in (mapping.get("params_meta") or []):
        try:
            fit = pm.get("fit")
            if isinstance(fit, dict):
                fits.append({
                    "name": pm.get("name"),
                    "type": fit.get("type"),
                    "coeffs": fit.get("coeffs"),
                    "r2": fit.get("r2"),
                    "confidence": pm.get("confidence"),
                })
        except Exception:
            continue
    # Sort by name for stable display
    fits = sorted(fits, key=lambda x: str(x.get("name", "")))
    return {"ok": True, "signature": sig, "count": len(fits), "fits": fits}


@app.get("/device_mapping/enumerate_labels")
def enumerate_param_labels(index: int, device: int, param_ref: str) -> Dict[str, Any]:
    """Enumerate discrete labels for a quantized parameter by sweeping integer steps.

    Restores the original value after sweep. Useful for building label_map.
    """
    ri = int(index); di = int(device)
    # Resolve param index by substring or exact index string
    try:
        pi = _resolve_param_index(ri, di, param_ref)
    except Exception:
        raise HTTPException(404, "param_not_found")
    # Read current params and capture bounds
    pr = udp_request({"op": "get_return_device_params", "return_index": ri, "device_index": di}, timeout=1.2)
    params = ((pr or {}).get("data") or {}).get("params") or []
    cur = next((p for p in params if int(p.get("index", -1)) == pi), None)
    if not cur:
        raise HTTPException(404, "param_not_found")
    vmin = float(cur.get("min", 0.0)); vmax = float(cur.get("max", 1.0))
    prev = float(cur.get("value", vmin))
    name = str(cur.get("name", ""))
    # Sweep integer steps
    labels = []
    try:
        import time as _t
        lo = int(vmin); hi = int(vmax)
        for step in range(lo, hi + 1):
            udp_request({"op": "set_return_device_param", "return_index": ri, "device_index": di, "param_index": pi, "value": float(step)}, timeout=1.0)
            _t.sleep(0.15)
            rb = udp_request({"op": "get_return_device_params", "return_index": ri, "device_index": di}, timeout=1.0)
            rps = ((rb or {}).get("data") or {}).get("params") or []
            p2 = next((p for p in rps if int(p.get("index", -1)) == pi), None)
            disp = str((p2 or {}).get("display_value", ""))
            labels.append({"step": step, "display": disp})
    finally:
        try:
            udp_request({"op": "set_return_device_param", "return_index": ri, "device_index": di, "param_index": pi, "value": float(prev)}, timeout=1.0)
        except Exception:
            pass
    # Build a basic label_map suggestion (unique display -> first step)
    label_map = {}
    for item in labels:
        d = item.get("display")
        if d and d not in label_map:
            label_map[d] = float(item.get("step", 0))
    return {"ok": True, "param": name, "index": pi, "range": [int(vmin), int(vmax)], "samples": labels, "label_map_suggested": label_map}


class ReturnMixerBody(BaseModel):
    return_index: int
    field: str  # 'volume' | 'pan' | 'mute' | 'solo'
    value: float


@app.post("/op/return/mixer")
def op_return_mixer(body: ReturnMixerBody) -> Dict[str, Any]:
    if body.field not in ("volume", "pan", "mute", "solo"):
        raise HTTPException(400, "invalid_field")
    msg = {
        "op": "set_return_mixer",
        "return_index": int(body.return_index),
        "field": body.field,
        "value": float(body.value),
    }
    resp = udp_request(msg, timeout=1.0)
    if not resp:
        raise HTTPException(504, "No reply from Ableton Remote Script")
    try:
        schedule_emit({"event": "return_mixer_changed", "return": int(body.return_index), "field": body.field})
    except Exception:
        pass
    return resp


class LearnDeviceBody(BaseModel):
    return_index: int
    device_index: int
    resolution: int = 21
    sleep_ms: int = 25


def _detect_device_type(params: list[dict], device_name: str | None = None) -> str:
    """Detect device type from parameter fingerprints.

    Uses characteristic parameter names to identify device types.
    Enables storing structures by type (reverb, delay, etc.) rather than
    by device name.

    Args:
        params: List of parameter dictionaries with 'name' field

    Returns:
        Device type string (reverb, delay, compressor, eq, etc.) or "unknown"
    """
    name_lc = (device_name or "").strip().lower()
    if name_lc:
        if any(k in name_lc for k in ("delay", "echo")):
            return "delay"
        if any(k in name_lc for k in ("reverb", "hall", "plate", "room")):
            return "reverb"
        if any(k in name_lc for k in ("compressor", "glue")):
            return "compressor"
        if "eq" in name_lc and "eight" in name_lc:
            return "eq8"
        if "auto filter" in name_lc or ("filter" in name_lc and "auto" in name_lc):
            return "autofilter"
        if "saturator" in name_lc:
            return "saturator"

    param_set = set(p.get("name", "") for p in params)

    # Ableton Reverb signature parameters
    if {"ER Spin On", "Freeze On", "Chorus On", "Diffusion"}.issubset(param_set):
        return "reverb"

    # Ableton Delay signature parameters
    if {"L Time", "R Time", "Ping Pong", "Feedback"}.issubset(param_set):
        return "delay"

    # Ableton Compressor signature parameters
    if {"Threshold", "Ratio", "Attack", "Release", "Knee"}.issubset(param_set):
        return "compressor"

    # Ableton EQ Eight signature parameters
    if {"1 Frequency A", "2 Frequency A", "3 Frequency A"}.issubset(param_set):
        return "eq8"

    # Ableton Auto Filter
    if {"Filter Type", "Frequency", "Resonance", "LFO Amount"}.issubset(param_set):
        return "autofilter"

    # Ableton Saturator
    if {"Drive", "Dry/Wet", "Color", "Type"}.issubset(param_set):
        return "saturator"

    # Fallback: infer from common parameter name hints
    if {"Time", "Feedback"}.intersection(param_set) and any("Time" in n for n in param_set):
        return "delay"
    if {"Decay", "Size"}.intersection(param_set):
        return "reverb"
    return "unknown"


def _make_device_signature(name: str, params: list[dict]) -> str:
    """Generate structure-based signature (excludes device name).

    All Ableton Reverb presets (Arena Tail, Vocal Hall, etc.) share the same
    parameter structure, so they get the same signature. This enables:
    - Learning structure once, reusing for all presets
    - Fast preset loading (just apply parameter values)
    - Separating structure from preset variations

    Args:
        name: Device name (NOT USED in signature, kept for compatibility)
        params: List of parameter dictionaries with 'name' field

    Returns:
        SHA1 hash of param_count|param_names (no device name)
    """
    param_names = ",".join([str(p.get("name", "")) for p in params])
    base = f"{len(params)}|{param_names}"  # REMOVED device name
    return hashlib.sha1(base.encode("utf-8")).hexdigest()


async def _generate_preset_metadata_llm(
    device_name: str,
    device_type: str,
    parameter_values: Dict[str, float],
) -> Dict[str, Any]:
    """Generate preset metadata using LLM analysis.

    Uses Vertex AI LLM to analyze parameter values and generate:
    - Description (what, when, why)
    - Audio engineering explanation
    - Natural language controls
    - Use cases and rationale

    Args:
        device_name: Preset name (e.g., "Arena Tail", "Vocal Hall")
        device_type: Device category (reverb, delay, etc.)
        parameter_values: Dict of param_name -> value

    Returns:
        Dict with description, audio_engineering, natural_language_controls, etc.
    """
    import sys
    import pathlib

    # Import LLM utilities from nlp-service
    nlp_dir = pathlib.Path(__file__).resolve().parent.parent / "nlp-service"
    if nlp_dir.exists() and str(nlp_dir) not in sys.path:
        sys.path.insert(0, str(nlp_dir))

    try:
        import vertexai
        from vertexai.generative_models import GenerativeModel
        from config.llm_config import get_llm_project_id, get_default_model_name

        project = get_llm_project_id()
        location = os.getenv("GCP_REGION", "us-central1")
        model_name = get_default_model_name()  # Use configured model from .env

        vertexai.init(project=project, location=location)

        # Build context-aware prompt
        prompt = f"""You are an expert audio engineer analyzing a {device_type} preset.

Preset Name: {device_name}
Device Type: {device_type}

Parameter Values:
{json.dumps(parameter_values, indent=2)}

Audio Engineering Context:
- Analyze the parameter values to understand the preset's character
- Consider psychoacoustic principles and typical use cases
- Reference standard audio engineering practices

Generate a comprehensive metadata JSON with this structure:

{{
  "description": {{
    "what": "Concise technical description of the preset's sonic character (1-2 sentences)",
    "when": ["Use case 1", "Use case 2", "Use case 3", "Use case 4"],
    "why": "Deep audio engineering explanation covering: decay characteristics, frequency response, stereo imaging, psychoacoustic perception (3-4 sentences)"
  }},
  "audio_engineering": {{
    "space_type": "Type of space being simulated (e.g., hall, room, plate)",
    "size": "Size descriptor with numeric reference if applicable",
    "decay_time": "RT60-style decay description",
    "predelay": "Predelay amount and spatial reasoning",
    "frequency_character": "Frequency response description (bright/dark/neutral + EQ)",
    "stereo_width": "Stereo width description with angle if applicable",
    "diffusion": "Diffusion character (smooth/grainy/dense)",
    "use_cases": [
      {{
        "source": "Audio source type",
        "context": "Musical context",
        "send_level": "Recommended send level (e.g., 15-25%)",
        "send_level_rationale": "Why this send level",
        "eq_prep": "Pre-send EQ recommendations",
        "eq_rationale": "Why this EQ treatment",
        "notes": "Additional mixing tips"
      }}
    ]
  }},
  "natural_language_controls": {{
    "tighter": {{
      "params": {{"param_name": relative_change_value}},
      "explanation": "What happens and why"
    }},
    "looser": {{"params": {{}}, "explanation": "..."}},
    "warmer": {{"params": {{}}, "explanation": "..."}},
    "brighter": {{"params": {{}}, "explanation": "..."}},
    "closer": {{"params": {{}}, "explanation": "..."}},
    "further": {{"params": {{}}, "explanation": "..."}},
    "wider": {{"params": {{}}, "explanation": "..."}},
    "narrower": {{"params": {{}}, "explanation": "..."}}
  }},
  "subcategory": "Specific category (e.g., hall, room, plate for reverb)",
  "warnings": {{
    "mono_compatibility": "Mono playback considerations if stereo width is wide",
    "cpu_usage": "CPU usage notes if complex settings",
    "mix_context": "Mixing context warnings",
    "frequency_buildup": "Frequency accumulation warnings",
    "low_end_accumulation": "Low-end buildup warnings"
  }},
  "genre_tags": ["genre1", "genre2", "genre3"]
}}

Return ONLY valid JSON. Be specific and technical. Use actual parameter values to inform your analysis.
"""

        # Ensure Vertex is initialized
        _vertex_init_once()
        # Use env/config model with JSON-only response for robust parsing
        # Resolve model name with sensible defaults
        model_name = os.getenv("LLM_MODEL") or os.getenv("VERTEX_MODEL") or "gemini-2.5-flash"
        # Encourage strict JSON via system instruction
        # Load local KB context to enrich outputs
        def _load_kb_for(dtype: str) -> str:
            try:
                import pathlib
                base = pathlib.Path(os.getcwd()) / "knowledge" / "audio-fundamentals"
                fname = None
                if dtype.lower() == "reverb":
                    fname = base / "deep_audio_engineering_reverb.md"
                elif dtype.lower() == "delay":
                    fname = base / "deep_audio_engineering_delay.md"
                if fname and fname.exists():
                    text = fname.read_text(encoding="utf-8", errors="ignore")
                    # Trim to a sane size to keep prompt within context window
                    return text[:20000]
            except Exception:
                pass
            return ""

        kb = _load_kb_for(device_type)

        model = GenerativeModel(
            model_name,
            system_instruction=(
                "You are an expert audio engineer. Respond with STRICT JSON only."
            ),
        )
        try:
            # First attempt: JSON-only MIME type
            # Build enriched prompt with KB context and stricter content requirements
            # Allow Firestore prompt template override per device_type
            params_json = json.dumps(parameter_values or {}, indent=2, ensure_ascii=False)
            custom_tpl = None
            try:
                custom_tpl = STORE.get_prompt_template(device_type)
            except Exception:
                custom_tpl = None
            if custom_tpl and isinstance(custom_tpl, str) and custom_tpl.strip():
                enriched_prompt = (custom_tpl
                    .replace("{{device_type}}", str(device_type))
                    .replace("{{device_name}}", str(device_name))
                    .replace("{{parameter_values}}", params_json)
                    .replace("{{kb_context}}", kb or ""))
            else:
                enriched_prompt = f"""
You are generating authoritative audio engineering metadata for a {device_type} preset.

KB Context (verbatim excerpts from internal knowledge):
---
{kb}
---

Preset Name: {device_name}
Parameter Values:
{params_json}

Requirements:
- Output STRICT JSON only (no prose).
- Provide a deeply technical description and rationale grounded in the KB Context and parameter values.
- audio_engineering.use_cases MUST include at least 4 detailed entries with send_level, eq_prep, and rationale fields.
- natural_language_controls MUST include all listed controls with parameter suggestions and explanations grounded in psychoacoustics.
- Prefer precise numeric guidance when possible.

JSON schema/layout to follow:
{{
  "description": {{
    "what": "1–2 sentence sonic character",
    "when": ["Use case 1", "Use case 2", "Use case 3", "Use case 4"],
    "why": "3–6 sentence technical explanation grounded in KB"
  }},
  "audio_engineering": {{
    "space_type": "hall|room|plate|chamber|spring|convolution",
    "size": "qualitative + numeric if known",
    "decay_time": "RT60-like description",
    "predelay": "ms with spatial reasoning",
    "frequency_character": "bright|dark|neutral with EQ hints",
    "stereo_width": "narrow|moderate|wide with angle if applicable",
    "diffusion": "smooth|grainy|dense",
    "use_cases": [
      {{
        "source": "e.g., vocal, guitar, synth",
        "context": "mix context",
        "send_level": "recommended % range",
        "send_level_rationale": "why this send",
        "eq_prep": "pre-send EQ moves",
        "eq_rationale": "why those EQ moves",
        "notes": "extra tips"
      }}
    ]
  }},
  "natural_language_controls": {{
    "tighter": {{"params": {{}} , "explanation": "..."}},
    "looser": {{"params": {{}} , "explanation": "..."}},
    "warmer": {{"params": {{}} , "explanation": "..."}},
    "brighter": {{"params": {{}} , "explanation": "..."}},
    "closer": {{"params": {{}} , "explanation": "..."}},
    "further": {{"params": {{}} , "explanation": "..."}},
    "wider": {{"params": {{}} , "explanation": "..."}},
    "narrower": {{"params": {{}} , "explanation": "..."}}
  }},
  "subcategory": "specific reverb subtype",
  "warnings": {{
    "mono_compatibility": "...",
    "cpu_usage": "...",
    "mix_context": "...",
    "frequency_buildup": "...",
    "low_end_accumulation": "..."
  }},
  "genre_tags": ["genre1", "genre2", "genre3"]
}}

Return ONLY valid JSON.
"""

            resp = model.generate_content(
                enriched_prompt,
                generation_config={
                    "temperature": 0.0,
                    "max_output_tokens": 4096,
                    "top_p": 0.9,
                    "response_mime_type": "application/json",
                },
            )
        except Exception:
            # Fallback: no special JSON constraint (some SDKs don't support response_mime_type)
            resp = model.generate_content(
                enriched_prompt,
                generation_config={
                    "temperature": 0.0,
                    "max_output_tokens": 4096,
                    "top_p": 0.9,
                },
            )

        # Quality helpers
        def _quality_ok(d: Dict[str, Any]) -> bool:
            try:
                why = str(((d or {}).get("description") or {}).get("why") or "")
                ucs = ((d or {}).get("audio_engineering") or {}).get("use_cases") or []
                return (len(why) >= 200) and (isinstance(ucs, list) and len(ucs) >= 4)
            except Exception:
                return False

        def _try_enrich(meta_in: Dict[str, Any]) -> Dict[str, Any]:
            try:
                enrich_prompt = f"""
You are enriching existing preset metadata using the KB Context.
KB Context:
---
{kb}
---
Original Metadata JSON:
{json.dumps(meta_in, indent=2)}

Improve it to meet these minimums:
- description.why >= 200 characters with deeper technical reasoning
- audio_engineering.use_cases must contain at least 4 detailed entries (with send_level, eq_prep, and clear rationale)
Return STRICT JSON only with the same keys expanded.
"""
                resp2 = model.generate_content(
                    enrich_prompt,
                    generation_config={
                        "temperature": 0.2,
                        "max_output_tokens": 4096,
                        "top_p": 0.9,
                        "response_mime_type": "application/json",
                    },
                )
                txt2 = getattr(resp2, "text", None)
                if txt2:
                    meta2 = json.loads(txt2)
                    if _quality_ok(meta2):
                        return meta2
                    # merge if partial improvement
                    try:
                        m = dict(meta_in)
                        m.update(meta2)
                        return m
                    except Exception:
                        return meta_in
            except Exception:
                return meta_in
            return meta_in

        # Prefer direct JSON text when available (JSON mode)
        response_text = getattr(resp, "text", None)
        if response_text:
            try:
                meta = _json_lenient_parse(response_text) or json.loads(response_text)
                if not _quality_ok(meta):
                    meta = _try_enrich(meta)
                return meta
            except Exception:
                pass

        # Vertex SDK variants: try candidates/parts
        try:
            cands = getattr(resp, "candidates", []) or []
            for c in cands:
                content = getattr(c, "content", None)
                parts = getattr(content, "parts", []) if content else []
                for p in parts:
                    t = getattr(p, "text", None)
                    if t:
                        try:
                            meta = _json_lenient_parse(t) or json.loads(t)
                            if not _quality_ok(meta):
                                meta = _try_enrich(meta)
                            return meta
                        except Exception:
                            # Try brace extraction from part text
                            s = str(t)
                            i, j = s.find("{"), s.rfind("}")
                            if i >= 0 and j > i:
                                meta = _json_lenient_parse(s[i:j+1]) or json.loads(s[i:j+1])
                                if not _quality_ok(meta):
                                    meta = _try_enrich(meta)
                                return meta
        except Exception:
            pass

        # to_dict traversal (SDK variant)
        try:
            td = getattr(resp, "to_dict", None)
            if callable(td):
                d = td()
                # Search recursively for JSON-like string
                def _find_json_like(obj):
                    if isinstance(obj, str) and obj.strip().startswith("{") and obj.strip().endswith("}"):
                        try:
                            return json.loads(obj)
                        except Exception:
                            # try brace extraction
                            s = obj; i, j = s.find("{"), s.rfind("}")
                            if i >= 0 and j > i:
                                return json.loads(s[i:j+1])
                    if isinstance(obj, dict):
                        for v in obj.values():
                            r = _find_json_like(v)
                            if r is not None:
                                return r
                    if isinstance(obj, list):
                        for it in obj:
                            r = _find_json_like(it)
                            if r is not None:
                                return r
                    return None
                found = _find_json_like(d)
                if found is not None:
                    meta = found
                    if not _quality_ok(meta):
                        meta = _try_enrich(meta)
                    return meta
        except Exception:
            pass

        # Fallback extractor for raw text
        raw = str(response_text or "").strip()
        i, j = raw.find("{"), raw.rfind("}")
        if i >= 0 and j > i:
            try:
                meta = _json_lenient_parse(raw[i:j + 1]) or json.loads(raw[i:j + 1])
                if not _quality_ok(meta):
                    meta = _try_enrich(meta)
                return meta
            except Exception:
                pass

        # Sectional generation fallback: generate smaller JSON chunks and merge
        try:
            def _gen_section(title: str, tpl: str) -> Dict[str, Any] | None:
                p = f"""
You are generating STRICT JSON for the '{title}' section only. No prose, no markdown.
KB Context (may help):
---
{kb}
---
Preset: {device_name} ({device_type})
Parameter Values:
{json.dumps(parameter_values, indent=2)}

Expected JSON skeleton to fill (return exactly this object with content populated):
{tpl}
"""
                r = model.generate_content(p, generation_config={
                    "temperature": 0.0,
                    "max_output_tokens": 2048,
                    "top_p": 0.9,
                    "response_mime_type": "application/json",
                })
                txt = getattr(r, "text", None)
                if not txt:
                    return None
                return _json_lenient_parse(txt) or json.loads(txt)

            desc = _gen_section(
                "description",
                json.dumps({
                    "description": {
                        "what": "",
                        "when": ["", "", "", ""],
                        "why": ""
                    }
                }, indent=2),
            ) or {}

            eng = _gen_section(
                "audio_engineering",
                json.dumps({
                    "audio_engineering": {
                        "space_type": "",
                        "size": "",
                        "decay_time": "",
                        "predelay": "",
                        "frequency_character": "",
                        "stereo_width": "",
                        "diffusion": "",
                        "use_cases": [
                            {"source": "", "context": "", "send_level": "", "send_level_rationale": "", "eq_prep": "", "eq_rationale": "", "notes": ""}
                        ]
                    }
                }, indent=2),
            ) or {}

            nlc = _gen_section(
                "natural_language_controls",
                json.dumps({
                    "natural_language_controls": {
                        "tighter": {"params": {}, "explanation": ""},
                        "looser": {"params": {}, "explanation": ""},
                        "warmer": {"params": {}, "explanation": ""},
                        "brighter": {"params": {}, "explanation": ""},
                        "closer": {"params": {}, "explanation": ""},
                        "further": {"params": {}, "explanation": ""},
                        "wider": {"params": {}, "explanation": ""},
                        "narrower": {"params": {}, "explanation": ""}
                    }
                }, indent=2),
            ) or {}

            merged: Dict[str, Any] = {}
            for part in (desc, eng, nlc):
                try:
                    for k, v in (part or {}).items():
                        merged[k] = v
                except Exception:
                    continue
            if merged:
                # Ensure minimum quality via enrichment if needed
                if not _quality_ok(merged):
                    merged = _try_enrich(merged)
                return merged
        except Exception:
            pass

        # If we still could not parse, return structured fallback
        return _basic_metadata_fallback(device_name, device_type, parameter_values)

    except Exception as e:
        print(f"[LLM] Failed to generate metadata: {e}")
        # Return minimal fallback metadata
        return {
            "description": {"what": f"{device_name} preset for {device_type}"},
            "subcategory": "unknown",
            "genre_tags": [],
        }


async def _ensure_device_mapping(
    device_signature: str,
    device_type: str,
    params: list[dict],
) -> None:
    """Create or update device mapping in Firestore.

    Creates a device_mappings document with parameter structure on first preset capture.

    Args:
        device_signature: SHA1 hash of parameter structure
        device_type: Device type (reverb, delay, etc.)
        params: List of parameter dicts with index, name, min, max
    """
    try:
        # Skip if params list is empty or too small (device in transition)
        if not params or len(params) < 5:
            print(f"[DEVICE-MAPPING] Skipping - insufficient params ({len(params or [])} params, need at least 5)")
            return

        # Check if device mapping already exists
        mapping = STORE.get_device_mapping(device_signature)
        if mapping:
            print(f"[DEVICE-MAPPING] Device mapping already exists for {device_signature}")
            return

        print(f"[DEVICE-MAPPING] Creating new device mapping for {device_signature}")

        # Build parameter structure from params
        param_structure = []
        for p in params:
            param_info = {
                "index": p.get("index"),
                "name": p.get("name"),
                "min": p.get("min", 0.0),
                "max": p.get("max", 1.0),
            }
            param_structure.append(param_info)

        # Create device mapping document
        import time as _time
        mapping_data = {
            "device_signature": device_signature,
            "device_type": device_type,
            "param_structure": param_structure,
            "param_count": len(param_structure),
            "created_at": int(_time.time()),
            "updated_at": int(_time.time()),
            "metadata_status": "pending_analysis",  # Waiting for LLM analysis
        }

        # Save to Firestore
        saved = STORE.save_device_mapping(device_signature, mapping_data)
        if saved:
            print(f"[DEVICE-MAPPING] ✓ Created device mapping with {len(param_structure)} parameters")
        else:
            print(f"[DEVICE-MAPPING] ✗ Failed to create device mapping")

    except Exception as e:
        print(f"[DEVICE-MAPPING] Error ensuring device mapping: {e}")
        import traceback
        traceback.print_exc()


async def _auto_capture_preset(
    return_index: int,
    device_index: int,
    device_name: str,
    device_type: str,
    structure_signature: str,
    params: list[dict],
) -> None:
    """Auto-capture preset in background when device with learned structure is loaded.

    Workflow:
    1. Generate preset_id from device_type + device_name
    2. Check if preset already exists in Firestore (skip if exists)
    3. Extract parameter values from provided params
    4. Call LLM to generate comprehensive metadata
    5. Save to Firestore presets collection

    Args:
        return_index: Return track index
        device_index: Device index on return track
        device_name: Full device name (e.g., "Reverb Ambience Medium")
        device_type: Detected device type (reverb, delay, etc.)
        structure_signature: Structure-based signature
        params: List of parameter dicts with 'name' and 'value'
    """
    try:
        # Generate preset_id from device name
        # Format: devicetype_presetname (e.g., reverb_ambience_medium)
        preset_id = f"{device_type}_{device_name.lower().replace(' ', '_')}"

        # Check if preset already exists; if it exists but has empty/partial values, refresh it
        existing = STORE.get_preset(preset_id)
        if existing:
            pv = existing.get("parameter_values") or {}
            status = str(existing.get("metadata_status") or "").lower()
            version = int(existing.get("metadata_version") or 0)
            # If this exists only locally, ensure it is present in Firestore
            try:
                saved_remote = STORE.save_preset(preset_id, existing, local_only=False)
                if saved_remote:
                    print(f"[AUTO-CAPTURE] Ensured preset {preset_id} saved to Firestore")
            except Exception:
                pass
            # If values are sufficient, do not re-capture
            if isinstance(pv, dict) and len(pv) >= 5:
                # NOTE: Old Cloud Run enrichment disabled - using ChatGPT batch enrichment
                print(f"[AUTO-CAPTURE] Preset {preset_id} already exists, skipping")
                return
            else:
                print(f"[AUTO-CAPTURE] Preset {preset_id} exists but has {len(pv) if isinstance(pv, dict) else 0} values; refreshing")

        print(f"[AUTO-CAPTURE] Capturing new preset: {preset_id}")

        # DEBUG: Check what params structure we're receiving
        if params and len(params) > 0:
            sample_param = params[0]
            print(f"[AUTO-CAPTURE] DEBUG - First param keys: {list(sample_param.keys())}")
            print(f"[AUTO-CAPTURE] DEBUG - Has 'value'? {'value' in sample_param}")
            print(f"[AUTO-CAPTURE] DEBUG - Sample param: {sample_param}")

        # Extract parameter values AND display values from provided params
        parameter_values = {}
        parameter_display_values = {}
        for p in params:
            param_name = p.get("name")
            param_value = p.get("value")
            param_display = p.get("display_value")

            if param_name and param_value is not None:
                parameter_values[param_name] = float(param_value)

                # Store display value if available
                if param_display is not None:
                    parameter_display_values[param_name] = str(param_display)

                # Debug: Show Sync/Time related params WITH display_value
                if any(x in param_name for x in ['Sync', 'Time', '16th']):
                    print(f"[AUTO-CAPTURE] DEBUG - {param_name}: value={param_value}, display_value='{param_display}'")

        print(f"[AUTO-CAPTURE] Extracted {len(parameter_values)} parameter values")
        print(f"[AUTO-CAPTURE] Extracted {len(parameter_display_values)} parameter display values")

        # Generate metadata (fast-path optional)
        metadata = {}
        fast_path = str(os.getenv("SKIP_LOCAL_METADATA_GENERATION", "")).lower() in ("1","true","yes","on")
        if fast_path:
            print("[AUTO-CAPTURE] Fast-path: skipping local metadata; marking pending_enrichment")
            metadata = {"metadata_status": "pending_enrichment"}
        else:
            print(f"[AUTO-CAPTURE] Generating metadata via LLM...")
            metadata = await _generate_preset_metadata_llm(
                device_name=device_name,
                device_type=device_type,
                parameter_values=parameter_values,
            )

        # Create preset data
        import time as _time
        preset_data = {
            "name": device_name,
            "device_name": device_name.split()[0] if ' ' in device_name else device_name,
            "manufacturer": "Ableton",
            "daw": "Ableton Live",
            "structure_signature": structure_signature,
            "device_signature": structure_signature,  # Alias for clarity
            "category": device_type,
            "preset_type": "stock",
            "parameter_values": parameter_values,
            "parameter_display_values": parameter_display_values,  # NEW: Display values
            "values_status": "ok" if len(parameter_values) >= 5 else "pending",
            "metadata_status": "captured",  # NEW: Track enrichment status
            "captured_at": int(_time.time()),
            "updated_at": int(_time.time()),
            **metadata  # LLM-generated or pending_enrichment flag
        }

        # Create/update device mapping (first time only per device signature)
        await _ensure_device_mapping(structure_signature, device_type, params)

        # Save to Firestore (and local cache)
        saved = STORE.save_preset(preset_id, preset_data, local_only=False)

        if saved:
            print(f"[AUTO-CAPTURE] ✓ Saved preset {preset_id} to Firestore")
            try:
                # Notify UI via SSE so it can refresh preset listings/state
                await broker.publish({
                    "event": "preset_captured",
                    "return": return_index,
                    "device": device_index,
                    "preset_id": preset_id,
                    "device_type": device_type,
                    "device_name": device_name,
                    "signature": structure_signature,
                })
            except Exception:
                pass
            # NOTE: Old Cloud Run enrichment disabled - using ChatGPT batch enrichment instead
            # Enrichment will be done manually after all presets are captured:
            # 1. Export presets with export_for_enrichment.py
            # 2. Feed to ChatGPT with enrichment prompt
            # 3. Apply results with apply_enrichments.py
            # try:
            #     enqueued = enqueue_preset_enrich(preset_id, metadata_version=1)
            #     if enqueued:
            #         print(f"[PUBSUB] ✓ Enqueued preset_enrich_requested for {preset_id}")
            #     else:
            #         print(f"[PUBSUB] ⊘ Pub/Sub not configured (set PUBSUB_TOPIC in .env)")
            # except Exception as e:
            #     print(f"[PUBSUB] ✗ Failed to enqueue: {e}")
            # Post-save verification and optional retry for empty values
            try:
                asyncio.create_task(_verify_and_retry_preset(preset_id, return_index, device_index))
            except Exception:
                pass
        else:
            print(f"[AUTO-CAPTURE] ✗ Failed to save preset {preset_id}")

    except Exception as e:
        print(f"[AUTO-CAPTURE] Error capturing preset: {e}")
        import traceback
        traceback.print_exc()


async def _verify_and_retry_preset(
    preset_id: str,
    return_index: int,
    device_index: int,
    *,
    min_params: int = 5,
    max_retries: int = 3,
    attempt: int = 0,
) -> None:
    """Verify preset parameter_values persisted; if not, retry capture with backoff.

    Uses live device indices to re-read values. Emits SSE events for progress.
    """
    try:
        import asyncio as _asyncio
        import time as _time
        preset = STORE.get_preset(preset_id)
        count = len((preset or {}).get("parameter_values") or {})
        if count >= min_params:
            # success
            try:
                await broker.publish({
                    "event": "preset_verified",
                    "preset_id": preset_id,
                    "values_ok": True,
                    "count": count,
                })
            except Exception:
                pass
            return

        if attempt >= max_retries:
            # give up
            try:
                await broker.publish({
                    "event": "preset_verify_failed",
                    "preset_id": preset_id,
                    "values_ok": False,
                    "count": count,
                })
            except Exception:
                pass
            return

        # backoff: 1s, 3s, 10s
        backoffs = [1.0, 3.0, 10.0]
        delay = backoffs[min(attempt, len(backoffs)-1)]
        await _asyncio.sleep(delay)

        # Re-read live params and update preset values
        rd = udp_request({
            "op": "get_return_device_params",
            "return_index": int(return_index),
            "device_index": int(device_index),
        }, timeout=1.2)
        rparams = ((rd or {}).get("data") or {}).get("params") or []
        live_vals: Dict[str, float] = {}
        live_disp: Dict[str, str] = {}
        for p in rparams:
            nm = p.get("name")
            val = p.get("value")
            disp = p.get("display_value")
            if nm is not None and val is not None:
                live_vals[str(nm)] = float(val)
            if nm is not None and disp is not None:
                live_disp[str(nm)] = str(disp)

        if live_vals:
            # merge into preset doc
            preset = preset or {}
            preset["parameter_values"] = live_vals
            preset["values_status"] = "ok" if len(live_vals) >= min_params else "pending"
            preset["updated_at"] = int(_time.time())
            if live_disp:
                preset["parameter_display_values"] = live_disp
            STORE.save_preset(preset_id, preset, local_only=False)

        try:
            await broker.publish({
                "event": "preset_retry",
                "preset_id": preset_id,
                "attempt": attempt + 1,
                "count": len(live_vals),
            })
        except Exception:
            pass

        # Recurse for next verify
        await _verify_and_retry_preset(
            preset_id,
            return_index,
            device_index,
            min_params=min_params,
            max_retries=max_retries,
            attempt=attempt + 1,
        )
    except Exception:
        pass


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
    device_type = _detect_device_type(params, dname)
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
            device_type = _detect_device_type(params, dname)
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
    device_type = _detect_device_type(params, dname)
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
    device_type = _detect_device_type(updated_params, data.get("device_name"))
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
    device_type = _detect_device_type(params, device_name)
    ok = STORE.save_device_map_local(signature, {"name": data.get("device_name"), "device_type": device_type}, params)
    return {"ok": ok, "signature": signature, "updated": updated}


# ==================== Preset Endpoints ====================

class CapturePresetBody(BaseModel):
    return_index: int
    device_index: int
    preset_name: str
    category: str = "stock"  # stock | user
    description: Optional[str] = None


@app.post("/return/device/capture_preset")
def capture_preset(body: CapturePresetBody) -> Dict[str, Any]:
    """Capture current device parameter values as a preset.

    Does NOT learn the device structure - only captures parameter values.
    Device must already be learned (structure signature must exist).
    """
    ret_idx = body.return_index
    dev_idx = body.device_index

    # Get device info
    devs = udp_request({"op": "get_return_devices", "return_index": ret_idx}, timeout=1.0)
    if not devs or "devices" not in devs:
        raise HTTPException(status_code=404, detail="Return track not found")

    devices = devs.get("devices", [])
    if dev_idx >= len(devices):
        raise HTTPException(status_code=404, detail=f"Device index {dev_idx} out of range")

    device = devices[dev_idx]
    device_name = device.get("name", "Unknown")

    # Get parameters
    params_resp = udp_request({"op": "get_return_device_params", "return_index": ret_idx, "device_index": dev_idx}, timeout=1.0)
    if not params_resp or "params" not in params_resp:
        raise HTTPException(status_code=500, detail="Failed to get device parameters")

    params = params_resp.get("params", [])

    # Compute signature
    signature = _make_device_signature(device_name, params)

    # Check if structure is learned
    mapping = STORE.get_device_map_local(signature)
    if not mapping and STORE.enabled:
        mapping = STORE.get_device_map(signature)

    if not mapping:
        raise HTTPException(
            status_code=400,
            detail=f"Device structure not learned. Please learn device first (signature: {signature})"
        )

    # Extract current parameter values and display strings
    parameter_values = {}
    parameter_display_values = {}
    for p in params:
        param_name = p.get("name")
        param_value = p.get("value")
        param_display = p.get("display_value")
        if param_name and param_value is not None:
            parameter_values[param_name] = float(param_value)
            if param_display is not None:
                parameter_display_values[param_name] = str(param_display)

    # Detect device type
    device_type = _detect_device_type(params, body.preset_name)

    # Create preset data (minimal version - can be enhanced with metadata later)
    preset_id = f"{device_type}_{body.preset_name.lower().replace(' ', '_')}"
    preset_data = {
        "name": body.preset_name,
        "device_name": device_name,
        "manufacturer": "Ableton",  # Can be enhanced to detect
        "daw": "Ableton Live",
        "structure_signature": signature,
        "category": device_type,
        "preset_type": body.category,
        "parameter_values": parameter_values,
        "parameter_display_values": parameter_display_values,
    }

    if body.description:
        preset_data["description"] = {"what": body.description}

    # Save preset (Firestore + local)
    print(f"[CAPTURE] Saving preset {preset_id}, category={body.category}, local_only={body.category == 'user'}")
    saved = STORE.save_preset(preset_id, preset_data, local_only=(body.category == "user"))
    print(f"[CAPTURE] Preset save result: {saved}")

    return {
        "ok": saved,
        "preset_id": preset_id,
        "device_name": device_name,
        "device_type": device_type,
        "signature": signature,
        "param_count": len(parameter_values),
    }


class ApplyPresetBody(BaseModel):
    return_index: int
    device_index: int
    preset_id: str


@app.post("/return/device/apply_preset")
def apply_preset(body: ApplyPresetBody) -> Dict[str, Any]:
    """Apply preset parameter values to a device.

    Device must have matching structure signature (same parameter layout).
    """
    ret_idx = body.return_index
    dev_idx = body.device_index
    preset_id = body.preset_id

    # Get preset data
    preset = STORE.get_preset(preset_id)
    if not preset:
        raise HTTPException(status_code=404, detail=f"Preset not found: {preset_id}")

    # Get current device info
    devs = udp_request({"op": "get_return_devices", "return_index": ret_idx}, timeout=1.0)
    if not devs or "devices" not in devs:
        raise HTTPException(status_code=404, detail="Return track not found")

    devices = devs.get("devices", [])
    if dev_idx >= len(devices):
        raise HTTPException(status_code=404, detail=f"Device index {dev_idx} out of range")

    device = devices[dev_idx]
    device_name = device.get("name", "Unknown")

    # Get current parameters
    params_resp = udp_request({"op": "get_return_device_params", "return_index": ret_idx, "device_index": dev_idx}, timeout=1.0)
    if not params_resp or "params" not in params_resp:
        raise HTTPException(status_code=500, detail="Failed to get device parameters")

    params = params_resp.get("params", [])
    current_signature = _make_device_signature(device_name, params)
    preset_signature = preset.get("structure_signature")

    # Verify signature match
    if current_signature != preset_signature:
        raise HTTPException(
            status_code=400,
            detail=f"Device structure mismatch. Current: {current_signature}, Preset: {preset_signature}"
        )

    # Apply parameter values
    parameter_values = preset.get("parameter_values", {})
    applied = 0
    errors = []

    for param_name, target_value in parameter_values.items():
        try:
            # Find parameter by name
            param = next((p for p in params if p.get("name") == param_name), None)
            if not param:
                errors.append(f"Parameter not found: {param_name}")
                continue

            param_index = param.get("index")

            # Set parameter
            result = udp_request({
                "op": "set_return_device_param",
                "return_index": ret_idx,
                "device_index": dev_idx,
                "param_index": param_index,
                "value": float(target_value),
            }, timeout=0.5)

            if result and result.get("ok"):
                applied += 1
            else:
                errors.append(f"Failed to set {param_name}")

        except Exception as e:
            errors.append(f"Error setting {param_name}: {str(e)}")

    return {
        "ok": applied > 0,
        "preset_name": preset.get("name"),
        "device_name": device_name,
        "applied": applied,
        "total": len(parameter_values),
        "errors": errors if errors else None,
    }


@app.get("/presets")
def list_presets(
    device_type: Optional[str] = None,
    structure_signature: Optional[str] = None,
    preset_type: Optional[str] = None,
) -> Dict[str, Any]:
    """List available presets with optional filtering."""
    presets = STORE.list_presets(device_type, structure_signature, preset_type)
    return {
        "presets": presets,
        "count": len(presets),
    }


@app.get("/presets/{preset_id}")
def get_preset_detail(preset_id: str) -> Dict[str, Any]:
    """Get full preset details including metadata and parameter values."""
    preset = STORE.get_preset(preset_id)
    if not preset:
        raise HTTPException(status_code=404, detail=f"Preset not found: {preset_id}")
    return preset


@app.delete("/presets/{preset_id}")
def delete_preset_endpoint(preset_id: str) -> Dict[str, Any]:
    """Delete a preset (user presets only)."""
    preset = STORE.get_preset(preset_id)
    if preset and preset.get("preset_type") == "stock":
        raise HTTPException(status_code=403, detail="Cannot delete stock presets")

    deleted = STORE.delete_preset(preset_id)
    return {"ok": deleted, "preset_id": preset_id}


# ==================== End Preset Endpoints ====================


class RefreshPresetBody(BaseModel):
    preset_id: str
    update_values_from_live: Optional[bool] = False
    return_index: Optional[int] = None
    device_index: Optional[int] = None
    fields_allowlist: Optional[list[str]] = None


@app.post("/presets/refresh_metadata")
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
    metadata = await _generate_preset_metadata_llm(
        device_name=device_name,
        device_type=device_type,
        parameter_values=parameter_values,
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

                        metadata = await _generate_preset_metadata_llm(
                            device_name=dname,
                            device_type=dtype,
                            parameter_values=pvals,
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
                    meta = await _generate_preset_metadata_llm(device_name=dname, device_type=dtype, parameter_values=pvals)
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
        for k, v in lm.items():
            try:
                if str(k).strip().lower() == label.lower():
                    x = max(vmin, min(vmax, float(v)))
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
        schedule_emit({"event": "mixer_changed", "track": op.track_index, "field": op.field})
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
        schedule_emit({"event": "send_changed", "track": op.track_index, "send_index": op.send_index})
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
        schedule_emit({"event": "device_param_changed", "track": op.track_index, "device": op.device_index, "param": op.param_index})
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
        schedule_emit({"event": "mixer_changed", "track": int(body.track_index), "field": "volume"})
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
        schedule_emit({"event": "selection_changed", "track": int(body.track_index)})
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
            schedule_emit({"event": "mixer_changed", "track": track_index, "field": "volume"})
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

    signature = _make_device_signature(device_name, params)
    device_type = _detect_device_type(params, device_name)

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


async def emit_event(payload: Dict[str, Any]) -> None:
    # Drop duplicate master events (identical value) to prevent storms
    try:
        if isinstance(payload, dict) and payload.get("event") == "master_mixer_changed":
            fld = str(payload.get("field") or "").strip()
            val = payload.get("value")
            if fld and isinstance(val, (int, float)):
                v = float(val)
                last = _MASTER_DEDUP.get(fld)
                if last is not None:
                    last_v, _last_ts = last
                    # Exact or near-exact repeats are dropped
                    if abs(v - last_v) <= 1e-7:
                        return
                _MASTER_DEDUP[fld] = (v, time.time())
    except Exception:
        # Never block emit on dedup errors
        pass
    if _debug_enabled("sse"):
        try:
            ename = payload.get("event")
            meta = {k: v for k, v in payload.items() if k != "data"}
            print(f"[SSE] Emitting {ename}: {json.dumps(meta)}")
        except Exception:
            print(f"[SSE] Emitting {payload}")
    await broker.publish(payload)


def schedule_emit(payload: Dict[str, Any]) -> None:
    """Schedule an SSE emit safely from sync or async contexts without leaking coroutines."""
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(emit_event(payload))
    except RuntimeError:
        # No running loop in this thread; run emit_event synchronously
        try:
            asyncio.run(emit_event(payload))
        except RuntimeError:
            # Already inside a running loop but couldn't get it; last resort: fire and forget via ensure_future
            try:
                asyncio.ensure_future(emit_event(payload))
            except Exception:
                pass


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
