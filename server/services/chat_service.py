from __future__ import annotations

import asyncio
import json
import pathlib
import re
import sys
from typing import Any, Dict, Optional

from fastapi import HTTPException
from pydantic import BaseModel

from server.config.app_config import get_send_aliases
from server.core.deps import get_store
from server.core.events import broker, schedule_emit
from server.services.ableton_client import request_op
from server.services.history import (
    DEVICE_BYPASS_CACHE,
    LAST_SENT,
    REDO_STACK,
    UNDO_STACK,
    _key,
    _rate_limited,
)
from server.services.intent_mapper import map_llm_to_canonical
from server.services.knowledge import search_knowledge
from server.services.mapping_utils import detect_device_type, make_device_signature
from server.volume_parser import parse_volume_command
from server.volume_utils import (
    db_to_live_float,
    db_to_live_float_send,
    live_float_to_db,
    live_float_to_db_send,
)


class ChatBody(BaseModel):
    text: str
    confirm: bool = True
    model: Optional[str] = None
    strict: Optional[bool] = None


class HelpBody(BaseModel):
    query: str
    context: Optional[Dict[str, Any]] = None


def udp_request(msg: Dict[str, Any], timeout: float = 1.0):
    try:
        op = str((msg or {}).get("op", ""))
        params = dict(msg or {})
        params.pop("op", None)
        return request_op(op, timeout=timeout, **params)
    except Exception:
        return None


def _get_prev_mixer_value(track_index: int, field: str) -> Optional[float]:
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


def generate_summary_from_canonical(canonical: Dict[str, Any]) -> str:
    """
    Generate a human-readable summary from a canonical intent.

    Examples:
        - Set Track 1 volume to -10 dB
        - Set Track 2 send A to -6 dB
        - Mute Track 3
        - Set Master cue to -20 dB
    """
    if not canonical:
        return "Command executed"

    domain = canonical.get("domain", "")
    action = canonical.get("action", "set")
    field = canonical.get("field", "")
    value = canonical.get("value")
    unit = canonical.get("unit", "")

    # Build entity reference (Track 1, Return A, Master, Device)
    entity = ""
    if domain == "track":
        track_idx = canonical.get("track_index", 1)
        entity = f"Track {track_idx}"
    elif domain == "return":
        return_idx = canonical.get("return_index")
        return_ref = canonical.get("return_ref")
        if return_ref:
            entity = f"Return {return_ref.upper()}"
        elif return_idx is not None:
            letter = chr(ord('A') + return_idx)
            entity = f"Return {letter}"
        else:
            entity = "Return"
    elif domain == "master":
        entity = "Master"
    elif domain == "device":
        # Build device reference with return context
        device_name = canonical.get("device_name_hint", "")
        return_ref = canonical.get("return_ref")
        return_idx = canonical.get("return_index")
        device_idx = canonical.get("device_index")

        parts = []
        if return_ref:
            parts.append(f"Return {return_ref.upper()}")
        elif return_idx is not None:
            letter = chr(ord('A') + return_idx)
            parts.append(f"Return {letter}")

        if device_name:
            parts.append(device_name.capitalize())
        elif device_idx is not None:
            parts.append(f"Device {device_idx + 1}")
        else:
            parts.append("Device")

        entity = " ".join(parts) if parts else "Device"
    elif domain == "transport":
        entity = "Transport"
    else:
        entity = domain.capitalize()

    # Build field description
    # Device parameters use param_ref instead of field
    if domain == "device":
        param_ref = canonical.get("param_ref", "")
        field_desc = param_ref if param_ref else "parameter"
    else:
        field_desc = field
        if field == "send":
            send_ref = canonical.get("send_ref", "")
            field_desc = f"send {send_ref.upper()}" if send_ref else "send"

    # Build value description
    value_desc = ""
    if value is not None:
        # Format the value to avoid scientific notation for small floats
        if isinstance(value, (int, float)):
            # Round to 2 decimal places for display, or show as integer if whole number
            if abs(value) < 0.01:
                # Values very close to zero - show as 0
                formatted_value = "0"
            elif abs(value - round(value)) < 0.01:
                # Essentially a whole number
                formatted_value = str(int(round(value)))
            else:
                # Show with up to 2 decimal places
                formatted_value = f"{value:.2f}".rstrip('0').rstrip('.')
        else:
            formatted_value = str(value)

        if unit:
            value_desc = f"to {formatted_value} {unit}"
        else:
            value_desc = f"to {formatted_value}"

    # Build action description
    action_verb = action.capitalize()
    if action == "set":
        action_verb = "Set"
    elif action == "increase":
        action_verb = "Increased"
    elif action == "decrease":
        action_verb = "Decreased"

    # Assemble summary
    if value_desc:
        return f"{action_verb} {entity} {field_desc} {value_desc}"
    else:
        return f"{action_verb} {entity} {field_desc}"


def handle_chat(body: ChatBody) -> Dict[str, Any]:
    """
    Handle chat commands through unified NLP → Intent → Execution path.

    This is the single source of truth for all command processing.
    Both WebUI and command-line tests use this same path.
    """
    # Import llm_daw from nlp-service/ dynamically (folder has a hyphen)
    import sys
    import pathlib
    nlp_dir = pathlib.Path(__file__).resolve().parent.parent.parent / "nlp-service"
    if nlp_dir.exists() and str(nlp_dir) not in sys.path:
        sys.path.insert(0, str(nlp_dir))

    text_lc = body.text.strip()

    # Step 1: Parse command with NLP service (handles typos, natural language)
    try:
        from llm_daw import interpret_daw_command  # type: ignore
    except Exception as e:
        raise HTTPException(500, f"NLP module not available: {e}")

    intent = interpret_daw_command(text_lc, model_preference=body.model, strict=body.strict)

    # Step 2: Transform to canonical format
    from server.services.intent_mapper import map_llm_to_canonical
    canonical, errors = map_llm_to_canonical(intent)

    # Step 3: Execute canonical intent
    if canonical and body.confirm:
        try:
            from server.api.intents import execute_intent as exec_canonical
            from server.models.intents_api import CanonicalIntent
            canonical_intent = CanonicalIntent(**canonical)
            result = exec_canonical(canonical_intent, debug=False)

            # Build response preserving all fields from result (especially 'data' with capabilities)
            response = {
                "ok": result.get("ok", True),
                "intent": intent,
                "canonical": canonical,
            }

            # Use summary from result if present, otherwise generate from canonical
            if "summary" in result:
                response["summary"] = result["summary"]
            else:
                response["summary"] = generate_summary_from_canonical(canonical)

            # Explicitly preserve data field with capabilities if present
            if "data" in result:
                response["data"] = result["data"]

            # Add any other fields from result
            for key, value in result.items():
                if key not in response:
                    response[key] = value

            return response
        except HTTPException as he:
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

    # Preview mode (confirm=False)
    if not body.confirm:
        return {
            "ok": True,
            "preview": canonical,
            "intent": intent,
            "summary": f"Preview: {intent.get('intent', 'unknown')}"
        }

    # Handle special intent types that don't use canonical execution

    # Question/help responses
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

    # Transport controls
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

    # Fallback: Intent recognized but not executable
    return {
        "ok": False,
        "intent": intent,
        "summary": f"Intent '{intent.get('intent')}' recognized but not executed",
        "reason": "intent_not_executable"
    }


def handle_chat_legacy(body: ChatBody) -> Dict[str, Any]:
    """
    DEPRECATED: Legacy regex-based chat handler.
    Kept for reference only. Do not use.
    Use handle_chat() instead for unified NLP path.
    """
    text_lc = body.text.strip()
    import re
    text_norm = re.sub(r'(-?\d+(?:\.\d+)?)(?:db|dB)\b', r'\1 dB', text_lc, flags=re.I)

    # Pre-parse common direct commands
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
    # IMPORTANT: "send" keyword is now REQUIRED to avoid false matches with typos like "volme"
    m = re.search(r"\bset\s+track\s+(\d+)\s+send\s+([\w\s]+?)\s+to\s+(-?\d+(?:\.\d+)?)\s*(db|dB|%|percent|percentage)?\b", text_norm, flags=re.I)
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
    # IMPORTANT: "send" keyword is now REQUIRED to avoid false matches
    m = re.search(r"\b(increase|decrease|reduce|lower|raise)\s+send\s+([\w\s]+?)\s+(?:on|for)?\s*track\s+(\d+)\s+by\s+(\d+(?:\.\d+)?)\s*(db|dB|%|percent|percentage)?\b", text_norm, flags=re.I)
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

    # Legacy path fallback: If no regex matched, try NLP
    try:
        from llm_daw import interpret_daw_command  # type: ignore
    except Exception as e:
        raise HTTPException(500, f"NLP module not available: {e}")

    intent = interpret_daw_command(text_lc, model_preference=body.model, strict=body.strict)

    # Transform NLP intent to canonical format
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
                "summary": result.get("summary", generate_summary_from_canonical(canonical)),
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



def handle_help(body: HelpBody) -> Dict[str, Any]:
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
