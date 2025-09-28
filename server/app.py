from __future__ import annotations
import os
from typing import Any, Dict, Optional
import time

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from server.ableton.client_udp import request as udp_request, send as udp_send
from server.models.ops import MixerOp, SendOp, DeviceParamOp
from server.services.knowledge import search_knowledge
from server.services.intent_mapper import map_llm_to_canonical


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


@app.post("/op/mixer")
def op_mixer(op: MixerOp) -> Dict[str, Any]:
    msg = {"op": "set_mixer", **op.dict()}
    resp = udp_request(msg, timeout=1.0)
    if not resp:
        raise HTTPException(504, "No reply from Ableton Remote Script")
    return resp


@app.post("/op/send")
def op_send(op: SendOp) -> Dict[str, Any]:
    msg = {"op": "set_send", **op.dict()}
    resp = udp_request(msg, timeout=1.0)
    if not resp:
        raise HTTPException(504, "No reply from Ableton Remote Script")
    return resp


@app.post("/op/device/param")
def op_device_param(op: DeviceParamOp) -> Dict[str, Any]:
    msg = {"op": "set_device_param", **op.dict()}
    resp = udp_request(msg, timeout=1.0)
    if not resp:
        raise HTTPException(504, "No reply from Ableton Remote Script")
    return resp


@app.post("/op/volume_db")
def op_volume_db(body: VolumeDbBody) -> Dict[str, Any]:
    msg = {"op": "set_volume_db", "track_index": int(body.track_index), "db": float(body.db)}
    resp = udp_request(msg, timeout=1.0)
    if not resp:
        raise HTTPException(504, "No reply from Ableton Remote Script")
    return resp


@app.post("/op/select_track")
def op_select_track(body: SelectTrackBody) -> Dict[str, Any]:
    msg = {"op": "select_track", "track_index": int(body.track_index)}
    resp = udp_request(msg, timeout=1.0)
    if not resp:
        raise HTTPException(504, "No reply from Ableton Remote Script")
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
    # Pre-parse common direct commands to avoid LLM ambiguity
    import re
    m = re.search(r"\b(mute|unmute|solo|unsolo)\s+track\s+(\d+)\b", text_lc, flags=re.I)
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

    # Volume without 'dB': treat as dB by default
    m = re.search(r"\bset\s+track\s+(\d+)\s+vol(?:ume)?\s+to\s+(-?\d+(?:\.\d+)?)\b", text_lc)
    if m:
        track_index = int(m.group(1))
        target = float(m.group(2))
        target = max(-60.0, min(6.0, target))
        warn = target > 0.0
        msg = {"op": "set_volume_db", "track_index": track_index, "db": target}
        if not body.confirm:
            return {"ok": True, "preview": msg, "summary": f"Set Track {track_index} volume to {target:g} dB" + (" (warning: >0 dB may clip)" if warn else "")}
        resp = udp_request(msg, timeout=1.0)
        summ = f"Set Track {track_index} volume to {target:g} dB"
        if isinstance(resp, dict) and resp.get("achieved_db") is not None:
            summ = f"Set Track {track_index} volume to {float(resp['achieved_db']):.1f} dB"
        if warn:
            summ += " (warning: >0 dB may clip)"
        return {"ok": bool(resp and resp.get("ok", True)), "resp": resp, "summary": summ}

    # Pan Live-style inputs like '25L'/'25R' (floats allowed)
    m = re.search(r"\bset\s+track\s+(\d+)\s+pan\s+to\s+((?:\d{1,2}(?:\.\d+)?)|50(?:\.0+)?)\s*([lLrR])\b", text_lc)
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
        return {"ok": bool(resp and resp.get("ok", True)), "resp": resp, "summary": f"Set Track {track_index} pan to {label}"}

    # Pan absolute numeric -50..50 (floats)
    m = re.search(r"\bset\s+track\s+(\d+)\s+pan\s+to\s+(-?\d+(?:\.\d+)?)\b", text_lc)
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
        # Map dB -60..+6 to 0..1
        val = float(op.get("value", 0))
        # Prefer precise dB setting via dedicated op (bridge performs internal adjustment)
        msg = {"op": "set_volume_db", "track_index": track_index, "db": max(-60.0, min(6.0, val))}
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
