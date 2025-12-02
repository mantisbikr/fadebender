from __future__ import annotations

import asyncio
import json
import logging
import os
import pathlib
import re
import sys
import time
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

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
from server.services.chat_models import ChatBody, HelpBody
from server.services.chat_summarizer import generate_summary_from_canonical
from server.services.rag_service import get_rag_service


"""Chat models moved to server.services.chat_models; summarizer moved to chat_summarizer."""

# Feature flag: route /chat through layered parser when enabled.
# This is intentionally separate from USE_LAYERED_PARSER (which controls /intent/parse).
USE_LAYERED_CHAT = os.getenv("USE_LAYERED_CHAT", "").lower() in ("1", "true", "yes")

# Cached parse index for layered parser (avoids repeated initialization)
_PARSE_INDEX: Optional[Dict[str, Any]] = None


def _find_device_index_by_hint(device_hint: str, devices: list[Dict[str, Any]]) -> Optional[int]:
    """Find device index matching a hint using device_map fuzzy matching.

    Args:
        device_hint: Device name hint (e.g., "reverb", "comp", "eq")
        devices: List of device dicts from Live (each with "name" and optionally "class_name" fields)

    Returns:
        Device index (0-based) or None if not found
    """
    if not device_hint or not devices:
        return None

    try:
        from server.services.nlp.layered.parsers.device_action_parser import (
            _get_device_names,
            _fuzzy_match_device,
            _load_device_map
        )

        # Get canonical device names from device_map
        device_names = _get_device_names()

        # Fuzzy match the hint to get canonical name (lowercase)
        canonical_name_lower = _fuzzy_match_device(device_hint, device_names, max_distance=2)

        if not canonical_name_lower:
            # No match in device_map, fall back to direct substring matching
            hint_lower = device_hint.lower()
            for idx, dev in enumerate(devices):
                dev_name = dev.get("name", "").lower()
                dev_class = dev.get("class_name", "").lower()
                if hint_lower in dev_name or dev_name in hint_lower:
                    return idx
                if dev_class and (hint_lower in dev_class or dev_class in hint_lower):
                    return idx
            return None

        # Get the properly-cased device name from device_map
        device_map = _load_device_map()
        canonical_name = None
        for key in device_map.keys():
            if key.lower() == canonical_name_lower:
                canonical_name = key
                break

        if not canonical_name:
            canonical_name = canonical_name_lower

        # Match against actual devices from Live (case-insensitive)
        # Check both "name" (preset name like "Ambience Medium") and "class_name" (device type like "Reverb")
        canonical_lower = canonical_name.lower()
        for idx, dev in enumerate(devices):
            dev_name = dev.get("name", "")
            dev_class = dev.get("class_name", "")

            # Exact match on class_name (preferred)
            if dev_class.lower() == canonical_lower:
                return idx

            # Exact match on name
            if dev_name.lower() == canonical_lower:
                return idx

            # Substring match on class_name
            if dev_class and (canonical_lower in dev_class.lower() or dev_class.lower() in canonical_lower):
                return idx

            # Substring match on name (least preferred)
            if canonical_lower in dev_name.lower() or dev_name.lower() in canonical_lower:
                return idx

        return None

    except Exception:
        # Fallback to simple substring matching on error
        hint_lower = device_hint.lower()
        for idx, dev in enumerate(devices):
            dev_name = dev.get("name", "").lower()
            dev_class = dev.get("class_name", "").lower()
            if hint_lower in dev_name or dev_name in hint_lower:
                return idx
            if dev_class and (hint_lower in dev_class or dev_class in hint_lower):
                return idx
        return None


def _get_parse_index() -> Dict[str, Any]:
    """Get or build parse index for layered parser.

    Uses minimal index when device mappings are unavailable so that
    mixer/track/open/list commands still work.
    """
    global _PARSE_INDEX
    if _PARSE_INDEX is not None:
        return _PARSE_INDEX

    try:
        from server.services.parse_index.parse_index_builder import ParseIndexBuilder

        try:
            # For now build from empty Live set; device-aware parsing
            # still falls back to LLM if needed.
            live_devices: list[Dict[str, Any]] = []
            builder = ParseIndexBuilder()
            _PARSE_INDEX = builder.build_from_live_set(live_devices)
        except Exception:
            _PARSE_INDEX = {
                "version": "pi-minimal",
                "devices_in_set": [],
                "params_by_device": {},
                "device_type_index": {},
                "param_to_device_types": {},
                "mixer_params": [
                    "volume",
                    "pan",
                    "mute",
                    "solo",
                    *[f"send {chr(ord('a') + i)}" for i in range(12)],
                ],
                "typo_map": {},
            }
    except Exception:
        _PARSE_INDEX = {
            "version": "pi-minimal",
            "devices_in_set": [],
            "params_by_device": {},
            "device_type_index": {},
            "param_to_device_types": {},
            "mixer_params": [
                "volume",
                "pan",
                "mute",
                "solo",
                *[f"send {chr(ord('a') + i)}" for i in range(12)],
            ],
            "typo_map": {},
        }

    return _PARSE_INDEX


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

    Automatically routes help/question queries to handle_help for better quality.
    """
    # Generate unique request ID for tracking (used for capabilities history)
    request_id = str(int(time.time() * 1000))  # millisecond timestamp

    # Import llm_daw from nlp-service/ dynamically (folder has a hyphen)
    nlp_dir = pathlib.Path(__file__).resolve().parent.parent.parent / "nlp-service"
    if nlp_dir.exists() and str(nlp_dir) not in sys.path:
        sys.path.insert(0, str(nlp_dir))

    text_lc = body.text.strip()

    # AUTO-ROUTE HELP QUERIES: Detect help/question queries and route to handle_help
    # This ensures web UI gets proper help responses without needing to call /help endpoint
    from server.services.help_router import get_help_router, QueryType
    help_router = get_help_router()
    query_type, _ = help_router.classify_query(text_lc)

    # If it's a help query (not a command), route to help system
    help_query_types = {
        QueryType.FACTUAL_COUNT,
        QueryType.FACTUAL_LIST,
        QueryType.FACTUAL_PARAMS,
        QueryType.PARAMETER_SEARCH,
        QueryType.SEMANTIC,
        QueryType.COMPARISON,
        QueryType.WORKFLOW
    }

    if query_type in help_query_types:
        logger.info(f"[Chat→Help] Auto-routing help query (type={query_type.value}): {text_lc[:50]}...")
        # Convert ChatBody to HelpBody and delegate to help handler
        help_body = HelpBody(
            query=body.text,
            context={'userId': body.model} if body.model else None
        )
        return handle_help(help_body)

    intent: Dict[str, Any] = {}

    # Step 1: Parse command.
    # If layered chat mode is enabled, try the layered parser first and fall back
    # to llm_daw for anything it cannot handle (questions, complex queries, etc.).
    if USE_LAYERED_CHAT:
        try:
            from server.services.nlp.intent_builder import parse_command_layered

            parse_index = _get_parse_index()
            layered_intent = parse_command_layered(text_lc, parse_index)
            if layered_intent:
                intent = layered_intent
            else:
                # Fallback to llm_daw if layered parser produced no intent
                from llm_daw import interpret_daw_command  # type: ignore

                intent = interpret_daw_command(
                    text_lc, model_preference=body.model, strict=body.strict
                )
        except Exception:
            # On any error, fall back to llm_daw path
            try:
                from llm_daw import interpret_daw_command  # type: ignore
            except Exception as e:
                raise HTTPException(500, f"NLP module not available: {e}")
            intent = interpret_daw_command(
                text_lc, model_preference=body.model, strict=body.strict
            )
    else:
        # Original behavior: llm_daw-only path
        try:
            from llm_daw import interpret_daw_command  # type: ignore
        except Exception as e:
            raise HTTPException(500, f"NLP module not available: {e}")
        intent = interpret_daw_command(
            text_lc, model_preference=body.model, strict=body.strict
        )

    # Handle non-control intents that should not go through canonical mapper
    # GET queries: delegate to snapshot/query (same behavior as /intent/query)
    if intent.get("intent") == "get_parameter":
        raw_targets = intent.get("targets") or []
        # Normalize mixer parameter names to lowercase (device params keep casing)
        targets = []
        for t in raw_targets:
            try:
                plugin = t.get("plugin")
                param_raw = t.get("parameter") or ""
                param = str(param_raw).lower() if not plugin else param_raw
                nt = dict(t)
                nt["parameter"] = param
                targets.append(nt)
            except Exception:
                targets.append(t)
        try:
            import httpx

            resp = httpx.post(
                "http://localhost:8722/snapshot/query",
                json={"targets": targets},
                timeout=5.0,
            )
            resp.raise_for_status()
            data = resp.json()
            return {
                "ok": bool(data.get("ok", True)),
                "intent": intent,
                **data,
            }
        except Exception as e:
            return {
                "ok": False,
                "intent": intent,
                "reason": "query_error",
                "summary": f"Query error: {e}",
                "error": str(e),
            }

    # Navigation intents: auto-open capabilities drawer
    if intent.get("intent") == "open_capabilities":
        target = intent.get("target", {})
        capabilities_ref = None
        summary = "Open controls"

        try:
            from server.api.cap_utils import build_capabilities_ref

            # Parse target structure and build capabilities_ref
            target_type = target.get("type")

            if target_type == "mixer":
                entity = target.get("entity")
                if entity == "track":
                    track_index = target.get("track_index", 0)  # 1-based from intent
                    capabilities_ref = build_capabilities_ref(domain="track", track_index=track_index)
                    summary = f"Opening Track {track_index} controls"
                elif entity == "return":
                    return_ref = target.get("return_ref", "A")
                    return_index = ord(return_ref.upper()) - ord('A') if return_ref else 0
                    capabilities_ref = build_capabilities_ref(domain="return", return_index=return_index)
                    summary = f"Opening Return {return_ref} controls"
                elif entity == "master":
                    capabilities_ref = build_capabilities_ref(domain="master")
                    summary = "Opening Master controls"

            elif target_type == "device":
                scope = target.get("scope")
                if scope == "return":
                    return_ref = target.get("return_ref", "A")
                    return_index = ord(return_ref.upper()) - ord('A') if return_ref else 0
                    device_name_hint = target.get("device_name_hint", "")
                    device_index = target.get("device_index")

                    # If device_index not provided but device_name_hint is, find the device
                    if device_index is None and device_name_hint:
                        from server.services.device_readers import read_return_devices
                        devices_data = read_return_devices(return_index)
                        devices = devices_data.get("devices", [])
                        device_index = _find_device_index_by_hint(device_name_hint, devices)

                    # Default to 0 if still not found
                    if device_index is None:
                        device_index = 0

                    capabilities_ref = build_capabilities_ref(
                        domain="return_device",
                        return_index=return_index,
                        device_index=device_index
                    )
                    summary = f"Opening Return {return_ref} {device_name_hint} controls"
                elif scope == "track":
                    track_index = target.get("track_index", 1)
                    device_name_hint = target.get("device_name_hint", "")
                    device_index = target.get("device_index")

                    # If device_index not provided but device_name_hint is, find the device
                    if device_index is None and device_name_hint:
                        from server.services.device_readers import read_track_devices
                        devices_data = read_track_devices(track_index)
                        devices = devices_data.get("devices", [])
                        device_index = _find_device_index_by_hint(device_name_hint, devices)

                    # Default to 0 if still not found
                    if device_index is None:
                        device_index = 0

                    capabilities_ref = build_capabilities_ref(
                        domain="track_device",
                        track_index=track_index,
                        device_index=device_index
                    )
                    summary = f"Opening Track {track_index} Device {device_index} {device_name_hint} controls".strip()

        except Exception:
            pass

        # Check config to determine if navigation commands should auto-open
        auto_open_enabled = False
        try:
            from server.config.app_config import get_app_config
            cfg = get_app_config()
            auto_open_enabled = cfg.get("features", {}).get("auto_open_capabilities_on_navigation", True)
        except Exception:
            auto_open_enabled = True  # Default to True if config unavailable

        return {
            "ok": True,
            "request_id": request_id,
            "intent": intent,
            "capabilities_ref": capabilities_ref,
            "auto_open": auto_open_enabled,  # Configurable via app_config.json
            "summary": summary
        }

    # List capabilities: still UI-only, no auto-open
    if intent.get("intent") == "list_capabilities":
        return {"ok": True, "request_id": request_id, "intent": intent, "summary": "navigation_intent"}

    # Step 2: Transform to canonical format for control intents
    from server.services.intent_mapper import map_llm_to_canonical
    canonical, errors = map_llm_to_canonical(intent)

    # Step 3: Execute canonical intent
    # Special-case: transport domain is handled directly (not via CanonicalIntent)
    if canonical and canonical.get("domain") == "transport" and body.confirm:
        action = str(canonical.get("action", ""))
        value = canonical.get("value")
        # Combined time signature (num/den)
        if action == "time_sig_both":
            num = None; den = None
            if isinstance(value, dict):
                num = value.get("num"); den = value.get("den")
            elif isinstance(value, str) and "/" in value:
                try:
                    parts = value.split("/"); num = float(parts[0]); den = float(parts[1])
                except Exception:
                    pass
            ok_all = True
            if num is not None:
                r1 = udp_request({"op": "set_transport", "action": "time_sig_num", "value": float(num)}, timeout=1.0)
                ok_all = ok_all and bool(r1 and r1.get("ok", True))
            if den is not None:
                r2 = udp_request({"op": "set_transport", "action": "time_sig_den", "value": float(den)}, timeout=1.0)
                ok_all = ok_all and bool(r2 and r2.get("ok", True))
            try:
                schedule_emit({"event": "transport_changed", "action": "time_signature"})
            except Exception:
                pass
            return {"ok": ok_all, "intent": intent, "canonical": canonical, "summary": f"Transport: time_signature {num}/{den}"}

        # Combined loop region (enable loop then set start/length)
        if action == "loop_region" and isinstance(value, dict):
            start = value.get("start"); length = value.get("length")
            ok_all = True
            _ = udp_request({"op": "set_transport", "action": "loop_on", "value": 1.0}, timeout=1.0)
            if start is not None:
                r1 = udp_request({"op": "set_transport", "action": "loop_start", "value": float(start)}, timeout=1.0)
                ok_all = ok_all and bool(r1 and r1.get("ok", True))
            if length is not None:
                r2 = udp_request({"op": "set_transport", "action": "loop_length", "value": float(length)}, timeout=1.0)
                ok_all = ok_all and bool(r2 and r2.get("ok", True))
            try:
                schedule_emit({"event": "transport_changed", "action": "loop_region"})
            except Exception:
                pass
            return {"ok": ok_all, "intent": intent, "canonical": canonical, "summary": f"Transport: loop_region start={start} length={length}"}

        # Project structure commands should be routed to execute_intent
        PROJECT_STRUCTURE_ACTIONS = {
            "create_audio_track", "create_midi_track", "delete_track", "duplicate_track",
            "create_scene", "delete_scene", "duplicate_scene",
            "rename_track", "rename_scene", "rename_clip",
            "scene_fire", "scene_stop"
        }
        if action in PROJECT_STRUCTURE_ACTIONS:
            # Route to execute_intent which has dedicated handlers
            from server.api.intents import execute_intent as exec_canonical
            from server.models.intents_api import CanonicalIntent
            canonical_intent = CanonicalIntent(
                domain="transport",
                action=action,
                value=value
            )
            result = exec_canonical(canonical_intent)
            result["intent"] = intent
            result["canonical"] = canonical
            return result

        # Simple transport action passthrough
        msg = {"op": "set_transport", "action": action}
        if value is not None:
            try:
                msg["value"] = float(value)
            except Exception:
                pass
        resp = udp_request(msg, timeout=1.0)
        try:
            schedule_emit({"event": "transport_changed", "action": action})
        except Exception:
            pass
        return {"ok": bool(resp and resp.get("ok", True)), "intent": intent, "canonical": canonical, "summary": f"Transport: {action}{(' ' + str(value)) if value is not None else ''}", "resp": resp}

    if canonical and body.confirm:
        try:
            from server.api.intents import execute_intent as exec_canonical
            from server.models.intents_api import CanonicalIntent
            canonical_intent = CanonicalIntent(**canonical)
            result = exec_canonical(canonical_intent, debug=False)

            # Centralized: Add capabilities_ref based on canonical intent
            from server.api.cap_utils import add_capabilities_ref
            result = add_capabilities_ref(result, canonical)

            # Build response preserving all fields from result (especially capabilities_ref)
            response = {
                "ok": result.get("ok", True),
                "request_id": request_id,
                "intent": intent,
                "canonical": canonical,
            }

            # Use summary from result if present, otherwise generate from canonical
            if "summary" in result:
                response["summary"] = result["summary"]
            else:
                response["summary"] = generate_summary_from_canonical(canonical)

            # Explicitly preserve data field (deprecated - for backward compat)
            if "data" in result:
                response["data"] = result["data"]

            # Add any other fields from result (including capabilities_ref)
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

    # Transport controls (when confirm=false, for preview)
    if intent.get("intent") == "transport":
        op = intent.get("operation") or {}
        action = str(op.get("action", ""))
        value = op.get("value")

        # Combined time signature change: set numerator then denominator
        if action == "time_sig_both":
            num = None; den = None
            if isinstance(value, dict):
                num = value.get("num"); den = value.get("den")
            elif isinstance(value, str) and "/" in value:
                try:
                    parts = value.split("/"); num = float(parts[0]); den = float(parts[1])
                except Exception:
                    pass
            summary = f"Transport: time_signature {num}/{den}"
            if not body.confirm:
                return {"ok": True, "preview": [{"op": "set_transport", "action": "time_sig_num", "value": num}, {"op": "set_transport", "action": "time_sig_den", "value": den}], "intent": intent, "summary": summary}
            ok_all = True
            if num is not None:
                r1 = udp_request({"op": "set_transport", "action": "time_sig_num", "value": float(num)}, timeout=1.0)
                ok_all = ok_all and bool(r1 and r1.get("ok", True))
            if den is not None:
                r2 = udp_request({"op": "set_transport", "action": "time_sig_den", "value": float(den)}, timeout=1.0)
                ok_all = ok_all and bool(r2 and r2.get("ok", True))
            try:
                schedule_emit({"event": "transport_changed", "action": "time_signature"})
            except Exception:
                pass
            return {"ok": ok_all, "intent": intent, "summary": summary}

        # Combined loop region: enable loop, set start and length
        if action == "loop_region" and isinstance(value, dict):
            start = value.get("start"); length = value.get("length")
            summary = f"Transport: loop_region start={start} length={length}"
            if not body.confirm:
                preview = []
                preview.append({"op": "set_transport", "action": "loop_on", "value": 1.0})
                if start is not None:
                    preview.append({"op": "set_transport", "action": "loop_start", "value": float(start)})
                if length is not None:
                    preview.append({"op": "set_transport", "action": "loop_length", "value": float(length)})
                return {"ok": True, "preview": preview, "intent": intent, "summary": summary}
            ok_all = True
            _ = udp_request({"op": "set_transport", "action": "loop_on", "value": 1.0}, timeout=1.0)
            if start is not None:
                r1 = udp_request({"op": "set_transport", "action": "loop_start", "value": float(start)}, timeout=1.0)
                ok_all = ok_all and bool(r1 and r1.get("ok", True))
            if length is not None:
                r2 = udp_request({"op": "set_transport", "action": "loop_length", "value": float(length)}, timeout=1.0)
                ok_all = ok_all and bool(r2 and r2.get("ok", True))
            try:
                schedule_emit({"event": "transport_changed", "action": "loop_region"})
            except Exception:
                pass
            return {"ok": ok_all, "intent": intent, "summary": summary}

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
            schedule_emit({"event": "mixer_changed", "track": track_index, "field": "volume", "value": float_value})
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
            schedule_emit({"event": "send_changed", "track": track_index, "send_index": si, "value": target_float})
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
            schedule_emit({"event": "send_changed", "track": track_index, "send_index": si, "value": target_float})
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
            schedule_emit({"event": "mixer_changed", "track": track_index, "field": "pan", "value": pan})
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
            schedule_emit({"event": "mixer_changed", "track": track_index, "field": "pan", "value": pan})
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
                asyncio.create_task(broker.publish({"event": "mixer_changed", "track": track_index, "field": "volume", "value": nv if nv is not None else LAST_SENT.get(k)}))
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



def handle_help_local(body: HelpBody) -> Dict[str, Any]:
    """Fallback: Return grounded help snippets from local knowledge notes.

    Uses Gemini 2.5 Flash Lite to generate concise, formatted responses.

    Response shape:
    { ok, answer, sources: [{source, title}] }
    """
    from server.services.help_generator import generate_help_response

    matches = search_knowledge(body.query)
    sources: list[Dict[str, str]] = []
    for src, title, _ in matches:
        sources.append({"source": src, "title": title})

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
        if not matches:
            answer = (
                "**Sends in Fadebender**\n\n"
                "Sends control how much signal is sent to return tracks (A/B/…).\n\n"
                "- **Track sends**: `set track 1 send A to -12 dB` or `25%`\n"
                "- **Return→Return sends**: Available only if enabled in Live Preferences; use `set Return A send B to 20%`\n"
                "- **Read sends**: `/return/sends?index=0` or `/track/sends?index=1`\n"
                "- **Pre/Post**: See Return routing via `/return/routing` (field 'sends_mode')"
            )
            return {"ok": True, "answer": answer, "sources": sources, "suggested_intents": suggested}

    # Generate LLM-powered response from knowledge snippets
    answer = generate_help_response(body.query, matches, suggested)

    return {"ok": True, "answer": answer, "sources": sources, "suggested_intents": suggested}


# Session storage for conversational RAG
_help_sessions: Dict[str, str] = {}  # user_id -> session_id


def handle_help(body: HelpBody) -> Dict[str, Any]:
    """Handle help requests with smart routing.

    Architecture:
    1. Smart routing classifies query type
    2. Factual queries → Firestore (instant: <100ms)
    3. Semantic queries → Vector search (fast: ~1.5s) [future]
    4. Complex queries → Full RAG (configurable via RAG_MODE)

    RAG modes (for complex queries):
    - assistants: OpenAI Assistants API (GPT-4o, 20s, $20-40/mo) - best quality
    - hybrid: OpenAI embeddings + Gemini (8s, $2-5/mo) - good quality
    - vertex: Vertex AI Search (when quota available) - high quality

    Features:
    - Smart routing saves 70-80% on costs
    - Firestore queries 200x faster than RAG
    - Fully conversational with context awareness
    - Performance timing for benchmarking
    """
    import time
    from server.services.help_router import get_help_router, QueryType
    from server.services.firestore_help_service import get_firestore_help_service

    rag_mode = os.getenv('RAG_MODE', 'hybrid').lower()
    user_id = getattr(body, 'userId', None) or (body.context or {}).get('userId', 'default')

    logger.info(f"[Help] Query: {body.query[:50]}...")
    start_time = time.time()

    # Step 1: Classify query
    router = get_help_router()
    query_type, metadata = router.classify_query(body.query)
    logger.info(f"[Help] Classified as {query_type.value}, metadata={metadata}")

    # Step 2: Route to appropriate backend
    if router.should_use_firestore(query_type):
        # Fast path: Firestore direct query
        firestore_service = get_firestore_help_service()

        try:
            if query_type == QueryType.FACTUAL_COUNT:
                device = metadata.get('device')
                count = firestore_service.get_preset_count(device)

                if count is not None:
                    answer = f"There are {count} {device} presets available in Ableton Live."
                    total_time = time.time() - start_time
                    logger.info(f"[Help] Firestore factual_count completed in {total_time:.3f}s")

                    return {
                        "ok": True,
                        "answer": answer,
                        "sources": [],
                        "suggested_intents": [],
                        "format": 'default',
                        "mode": "firestore-count",
                        "timing": {"total": round(total_time, 3)},
                        "query_type": query_type.value
                    }

            elif query_type == QueryType.FACTUAL_LIST:
                device = metadata.get('device')
                include_ids = metadata.get('include_ids', False)
                presets = firestore_service.list_all_presets(device, include_ids)

                if presets:
                    # Format preset list
                    if include_ids:
                        preset_lines = [f"{i+1}. {p['name']} (ID: {p['id']})" for i, p in enumerate(presets)]
                    else:
                        preset_lines = [f"{i+1}. {p['name']}" for i, p in enumerate(presets)]

                    answer = f"Here are all {len(presets)} {device} presets:\n\n" + "\n".join(preset_lines)
                    total_time = time.time() - start_time
                    logger.info(f"[Help] Firestore factual_list completed in {total_time:.3f}s")

                    return {
                        "ok": True,
                        "answer": answer,
                        "sources": [],
                        "suggested_intents": [],
                        "format": 'default',
                        "mode": "firestore-list",
                        "timing": {"total": round(total_time, 3)},
                        "query_type": query_type.value
                    }

            elif query_type == QueryType.FACTUAL_PARAMS:
                device = metadata.get('device')
                params = firestore_service.get_device_parameters(device)

                if params:
                    param_list = ', '.join(params)
                    answer = f"The {device} has these controllable parameters: {param_list}"
                    total_time = time.time() - start_time
                    logger.info(f"[Help] Firestore factual_params completed in {total_time:.3f}s")

                    return {
                        "ok": True,
                        "answer": answer,
                        "sources": [],
                        "suggested_intents": [],
                        "format": 'default',
                        "mode": "firestore-params",
                        "timing": {"total": round(total_time, 3)},
                        "query_type": query_type.value
                    }

            elif query_type == QueryType.PARAMETER_SEARCH:
                device = metadata.get('device')
                param_name = metadata.get('param_name')
                operator = metadata.get('operator')
                value = metadata.get('value')

                matching = firestore_service.search_presets_by_parameter(
                    device, param_name, operator, value
                )

                if matching:
                    preset_lines = [f"{i+1}. {p['name']} ({param_name}: {p[f'{param_name}_value']})"
                                    for i, p in enumerate(matching)]
                    answer = f"Found {len(matching)} {device} presets with {param_name} {operator.replace('_', ' ')} {value}:\n\n" + "\n".join(preset_lines)
                    total_time = time.time() - start_time
                    logger.info(f"[Help] Firestore parameter_search completed in {total_time:.3f}s")

                    return {
                        "ok": True,
                        "answer": answer,
                        "sources": [],
                        "suggested_intents": [],
                        "format": 'default',
                        "mode": "firestore-search",
                        "timing": {"total": round(total_time, 3)},
                        "query_type": query_type.value
                    }

        except Exception as e:
            logger.warning(f"[Help] Firestore query failed: {e}, falling back to RAG")
            # Fall through to RAG

    # Step 2: Try semantic search for recommendation queries (Tier 2)
    if router.should_use_vector_search(query_type):
        from server.services.semantic_search_service import get_semantic_search_service
        semantic_service = get_semantic_search_service()

        try:
            # Extract device name if present
            device_name = metadata.get('device') if metadata else None

            result_data = semantic_service.search_similar_presets(
                query=body.query,
                device_name=device_name,
                top_k=5
            )

            if result_data:
                answer = result_data.get('response', '')
                presets = result_data.get('similar_presets', [])
                total_time = time.time() - start_time
                logger.info(f"[Help] Semantic search completed in {total_time:.3f}s")

                return {
                    "ok": True,
                    "answer": answer,
                    "sources": [],
                    "suggested_intents": [],
                    "format": 'default',
                    "mode": "semantic-search",
                    "timing": {"total": round(total_time, 3)},
                    "query_type": query_type.value,
                    "similar_presets": presets[:3]  # Top 3
                }
        except Exception as e:
            logger.warning(f"[Help] Semantic search failed: {e}, falling back to RAG")
            # Fall through to RAG

    # Step 3: Fall back to full RAG for complex queries or if earlier tiers failed (Tier 3)
    result = None
    fallback_used = False

    try:
        if rag_mode == 'assistants':
            # OpenAI Assistants API (GPT-4o)
            from server.services.assistant_rag_service import get_assistant_rag
            assistant_rag = get_assistant_rag()
            result = assistant_rag.query(user_id=user_id, question=body.query)

        elif rag_mode == 'hybrid':
            # Hybrid: OpenAI embeddings + Gemini generation
            from server.services.hybrid_rag_service import get_hybrid_rag
            hybrid_rag = get_hybrid_rag()
            result = hybrid_rag.query(user_id=user_id, question=body.query)

        elif rag_mode == 'vertex':
            # Vertex AI with Gemini (hybrid embeddings + Gemini generation)
            from server.services.hybrid_rag_service import get_hybrid_rag
            hybrid_rag = get_hybrid_rag()
            result = hybrid_rag.query(user_id=user_id, question=body.query)
            fallback_used = False  # This IS the intended Vertex AI mode

        else:
            logger.warning(f"Unknown RAG_MODE: {rag_mode}, falling back to hybrid")
            from server.services.hybrid_rag_service import get_hybrid_rag
            hybrid_rag = get_hybrid_rag()
            result = hybrid_rag.query(user_id=user_id, question=body.query)
            fallback_used = True

        # If query failed, fall back to local help
        if not result or not result.get('ok'):
            logger.warning(f"{rag_mode} RAG failed: {result.get('error') if result else 'None'}, falling back to local help")
            return handle_help_local(body)

        total_time = time.time() - start_time
        logger.info(f"[RAG] {rag_mode} completed in {total_time:.2f}s")

        # Extract result data
        answer = result.get('answer', '')
        sources = result.get('sources', [])
        mode = result.get('mode', rag_mode)
        timing = result.get('timing', {'total': round(total_time, 2)})

        # Build suggested intents based on query (keep existing heuristics)
        q = (body.query or "").lower()
        suggested: list[str] = []
        if any(k in q for k in ["vocal", "vocals", "singer", "voice", "weak", "soft", "quiet"]):
            suggested.extend([
                "increase track 1 volume by 3 dB",
                "set track 1 volume to -6 dB",
                "load compressor preset gentle on track 1",
            ])
        if any(k in q for k in ["reverb", "space", "spacious", "hall", "room", "preset"]):
            suggested.extend([
                "load reverb preset plate medium on return A",
                "set track 1 send A to -12 dB",
            ])

        response = {
            "ok": True,
            "answer": answer,
            "sources": sources,
            "suggested_intents": suggested,
            "format": 'default',
            "mode": mode,
            "timing": timing,
            "rag_mode": rag_mode
        }

        # Add thread_id for assistants mode (conversation continuity)
        if 'thread_id' in result:
            response['thread_id'] = result['thread_id']

        # Add model complexity for hybrid mode (smart routing)
        if 'model_complexity' in result:
            response['model_complexity'] = result['model_complexity']

        return response

    except Exception as e:
        logger.error(f"RAG query failed: {e}", exc_info=True)
        logger.info("Falling back to local help")
        return handle_help_local(body)
