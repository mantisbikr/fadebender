"""Layer 4: Intent Builder & Router

Combines outputs from Layers 1-3 into final raw_intent structure.
Routes based on intent_type and device field.
"""

from __future__ import annotations
from typing import Dict, Optional, Any
import re
from server.services.nlp.action_parser import ActionMatch
from server.services.nlp.track_parser import TrackMatch
from server.services.nlp.device_param_parser import DeviceParamMatch


def build_raw_intent(
    text: str,
    action: Optional[ActionMatch],
    track: Optional[TrackMatch],
    device_param: Optional[DeviceParamMatch]
) -> Optional[Dict[str, Any]]:
    """Build raw_intent from layer outputs.

    Args:
        text: Original input text
        action: ActionMatch from Layer 1
        track: TrackMatch from Layer 2
        device_param: DeviceParamMatch from Layer 3

    Returns:
        raw_intent dict ready for intent_mapper, or None if incomplete/ambiguous
    """
    if not action:
        return None  # No action parsed - can't build intent

    # Calculate overall confidence
    confidence = action.confidence
    if track:
        confidence = min(confidence, track.confidence)
    if device_param:
        confidence = min(confidence, device_param.confidence)

    # Build meta section
    meta = {
        "utterance": text,
        "confidence": confidence,
        "pipeline": "regex",
        "layer_methods": {
            "action": action.method if action else "none",
            "track": track.method if track else "none",
            "device_param": device_param.method if device_param else "none"
        }
    }

    # ROUTE 1: Transport intents (no targets)
    if action.intent_type == "transport":
        return _build_transport_intent(action, meta)

    # ROUTE 1b: Project structure intents (create/delete/duplicate)
    if action.intent_type in ("create_track", "delete_track", "duplicate_track",
                               "create_scene", "delete_scene", "duplicate_scene"):
        return _build_project_structure_intent(action, meta)

    # ROUTE 2: Navigation intents (open/list)
    if action.intent_type in ("open_capabilities", "list_capabilities"):
        return _build_navigation_intent(action, track, device_param, meta)

    # ROUTE 3: SET Parameter intents (mixer or device)
    if action.intent_type == "set_parameter":
        if not track:
            return None  # Need track for parameter intents

        # Sub-route based on device field
        if device_param and device_param.device == "mixer":
            return _build_mixer_intent(action, track, device_param, meta)
        elif device_param and device_param.device:
            return _build_device_intent(action, track, device_param, meta)
        else:
            return None  # Ambiguous - fallback to LLM

    # ROUTE 3b: RELATIVE_CHANGE Parameter intents (same as set_parameter but with relative operation)
    if action.intent_type == "relative_change":
        if not track:
            return None  # Need track for parameter intents

        # Sub-route based on device field
        if device_param and device_param.device == "mixer":
            return _build_mixer_intent(action, track, device_param, meta)
        elif device_param and device_param.device:
            return _build_device_intent(action, track, device_param, meta)
        else:
            return None  # Ambiguous - fallback to LLM

    # ROUTE 4: GET Parameter queries (mixer or device)
    if action.intent_type == "get_parameter":
        if not track:
            return None  # Need track for parameter queries

        # Sub-route based on device field
        if device_param and device_param.device == "mixer":
            return _build_get_mixer_intent(action, track, device_param, meta)
        elif device_param and device_param.device:
            return _build_get_device_intent(action, track, device_param, meta)
        else:
            return None  # Ambiguous - fallback to LLM

    return None  # Unknown intent type


def _build_transport_intent(action: ActionMatch, meta: Dict) -> Dict[str, Any]:
    """Build transport intent (play, stop, loop, tempo, etc.)."""
    # Transport intents have no targets, just action/value
    # Determine action from unit (tempo, loop_start, etc), value (play, stop), or raw_text (loop)
    transport_action = None
    transport_value = None

    if action.unit:
        # Commands with units: "set tempo to 130" → unit="bpm", value=130.0
        transport_action = str(action.unit)
        transport_value = action.value
    elif isinstance(action.value, str):
        # String value commands: "play" → value="play"
        transport_action = str(action.value)
        transport_value = None
    else:
        # Numeric value without unit: "loop off" → value=0.0, unit=None, raw_text="loop off"
        # Extract action from raw_text
        raw = (action.raw_text or "").lower()
        if "loop" in raw:
            transport_action = "loop"
            transport_value = action.value

    return {
        "intent": "transport",
        "operation": {
            "action": transport_action,
            "value": transport_value,
            "unit": action.unit
        },
        "meta": meta
    }


def _build_project_structure_intent(action: ActionMatch, meta: Dict) -> Dict[str, Any]:
    """Build project structure intent (create/delete/duplicate tracks/scenes)."""
    # Parse value string: "type:midi|index:3|name:Drums" or "default" or just an integer
    value_str = str(action.value) if action.value else "default"

    # Parse the structured value
    value_data = None
    track_type = None  # "midi" or "audio"

    if value_str == "default":
        # No index or name provided - create at end
        value_data = None
    elif "|" in value_str:
        # Structured data: "type:midi|index:3|name:Drums"
        value_data = {}
        for part in value_str.split("|"):
            if ":" in part:
                key, val = part.split(":", 1)
                if key == "index":
                    value_data["index"] = int(val)
                elif key == "name":
                    value_data["name"] = val
                elif key == "type":
                    track_type = val
    else:
        # Simple integer
        try:
            value_data = int(value_str)
        except:
            value_data = None

    # Map intent type to action name, using track_type if specified
    if action.intent_type == "create_track":
        if track_type == "midi":
            action_name = "create_midi_track"
        else:
            action_name = "create_audio_track"
    else:
        action_map = {
            "delete_track": "delete_track",
            "duplicate_track": "duplicate_track",
            "create_scene": "create_scene",
            "delete_scene": "delete_scene",
            "duplicate_scene": "duplicate_scene",
        }
        action_name = action_map.get(action.intent_type, action.intent_type)

    return {
        "intent": "transport",
        "operation": {
            "action": action_name,
            "value": value_data,
            "unit": None
        },
        "meta": meta
    }


def _build_navigation_intent(
    action: ActionMatch,
    track: Optional[TrackMatch],
    device_param: Optional[DeviceParamMatch],
    meta: Dict
) -> Dict[str, Any]:
    """Build navigation intent (open/list tracks, devices, etc.).

    For compatibility with the existing WebUI and legacy regex executor,
    we emit the same target structure as _open_capabilities_from_regex:

        {"type": "mixer", "entity": "track", "track_index": 1}
        {"type": "mixer", "entity": "return", "return_ref": "A"}
        {"type": "mixer", "entity": "master"}
        {"type": "device", "scope": "return", "return_ref": "A", "device_name_hint": "reverb"}
    """
    target: Dict[str, Any] = {}

    # OPEN CAPABILITIES: build structured target for mixer/device scopes
    if action.intent_type == "open_capabilities":
        # Device on return (e.g., "open return A reverb")
        if track and track.domain == "return" and device_param and device_param.device:
            # Return ref letter (A/B/C...) from index if available
            return_ref = None
            if track.index is not None:
                try:
                    return_ref = chr(ord("A") + int(track.index))
                except Exception:
                    return_ref = None
            # Fallback to reference string "Return X"
            if not return_ref and isinstance(track.reference, str) and " " in track.reference:
                try:
                    return_ref = track.reference.split()[1].upper()
                except Exception:
                    return_ref = None

            target = {
                "type": "device",
                "scope": "return",
            }
            if return_ref:
                target["return_ref"] = return_ref
            if device_param.device:
                target["device_name_hint"] = device_param.device
        # Mixer scopes: track / return / master
        elif track:
            if track.domain == "track" and track.index is not None:
                # Track indices are 0-based in TrackMatch; UI expects 1-based
                target = {
                    "type": "mixer",
                    "entity": "track",
                    "track_index": int(track.index) + 1,
                }
            elif track.domain == "return":
                return_ref = None
                if track.index is not None:
                    try:
                        return_ref = chr(ord("A") + int(track.index))
                    except Exception:
                        return_ref = None
                target = {
                    "type": "mixer",
                    "entity": "return",
                }
                if return_ref:
                    target["return_ref"] = return_ref
            elif track.domain == "master":
                target = {
                    "type": "mixer",
                    "entity": "master",
                }
        # Drawer actions (e.g., "open controls") are currently handled by old stack;
        # layered parser does not emit them yet, so we leave this path empty.

    else:
        # LIST CAPABILITIES: keep simple target reference + optional filter
        target_ref = track.reference if track else None

        # For list_capabilities with collection queries, add filter to meta if present
        if track and hasattr(track, "filter") and track.filter:
            meta["filter"] = track.filter

        target = target_ref

    return {
        "intent": action.intent_type,
        "target": target,
        "meta": meta,
    }


def _build_mixer_intent(
    action: ActionMatch,
    track: TrackMatch,
    device_param: DeviceParamMatch,
    meta: Dict
) -> Dict[str, Any]:
    """Build mixer parameter intent (volume, pan, mute, send, etc.)."""
    # Determine intent type based on operation
    intent_type = "relative_change" if action.operation == "relative" else "set_parameter"

    return {
        "intent": intent_type,
        "targets": [{
            "track": track.reference,
            "plugin": None,  # NULL = mixer parameter
            "parameter": device_param.param
        }],
        "operation": {
            "type": action.operation,
            "value": action.value,
            "unit": action.unit
        },
        "meta": meta
    }


def _build_device_intent(
    action: ActionMatch,
    track: TrackMatch,
    device_param: DeviceParamMatch,
    meta: Dict
) -> Dict[str, Any]:
    """Build device parameter intent (reverb decay, delay feedback, etc.)."""
    # Determine intent type based on operation
    intent_type = "relative_change" if action.operation == "relative" else "set_parameter"

    target = {
        "track": track.reference,
        "plugin": device_param.device,
        "parameter": device_param.param
    }

    # Add device_ordinal if specified
    if device_param.device_ordinal is not None:
        target["device_ordinal"] = device_param.device_ordinal

    return {
        "intent": intent_type,
        "targets": [target],
        "operation": {
            "type": action.operation,
            "value": action.value,
            "unit": action.unit
        },
        "meta": meta
    }


def _build_get_mixer_intent(
    action: ActionMatch,
    track: TrackMatch,
    device_param: DeviceParamMatch,
    meta: Dict
) -> Dict[str, Any]:
    """Build GET mixer parameter intent (volume, pan, mute, send, etc.)."""
    return {
        "intent": "get_parameter",
        "targets": [{
            "track": track.reference,
            "plugin": None,  # NULL = mixer parameter
            "parameter": device_param.param
        }],
        "meta": meta
    }


def _build_get_device_intent(
    action: ActionMatch,
    track: TrackMatch,
    device_param: DeviceParamMatch,
    meta: Dict
) -> Dict[str, Any]:
    """Build GET device parameter intent (reverb decay, delay feedback, etc.)."""
    target = {
        "track": track.reference,
        "plugin": device_param.device,
        "parameter": device_param.param
    }

    # Add device_ordinal if specified
    if device_param.device_ordinal is not None:
        target["device_ordinal"] = device_param.device_ordinal

    return {
        "intent": "get_parameter",
        "targets": [target],
        "meta": meta
    }


def _apply_fuzzy_action_corrections(text: str) -> str:
    """Apply fuzzy matching to action words in text for better pattern matching.

    Replaces fuzzy-matched action words with their canonical forms.
    Example: "lsit audio tracks" → "list audio tracks"

    Args:
        text: Lowercase text to correct

    Returns:
        Text with fuzzy-matched action words replaced
    """
    from server.services.nlp.action_parser import fuzzy_match_action_word
    import re

    words = text.split()
    corrected_words = []

    for word in words:
        # Remove punctuation for matching
        clean_word = re.sub(r'[^\w]', '', word)
        matched = fuzzy_match_action_word(clean_word)
        if matched:
            # Preserve punctuation but replace word
            corrected_word = re.sub(r'[\w]+', matched, word, count=1)
            corrected_words.append(corrected_word)
        else:
            corrected_words.append(word)

    return ' '.join(corrected_words)


def _normalize_track_number_words(text: str) -> str:
    """Normalize simple number words in track references.

    Examples:
        "open track one" → "open track 1"
        "set track two volume" → "set track 2 volume"
        "set track to volume" → "set track 2 volume"  (STT mis-hear)
    """
    num_words = {
        "one": "1",
        "two": "2",
        "three": "3",
        "four": "4",
        "five": "5",
        "six": "6",
        "seven": "7",
        "eight": "8",
        "nine": "9",
        "ten": "10",
    }

    normalized = text
    for word, num in num_words.items():
        # Match "track one", "track   two", etc. as whole words
        pattern = rf"\btrack\s+{word}\b"
        normalized = re.sub(pattern, f"track {num}", normalized)

    # Handle common STT mis-hear: "track to" → "track 2" in mixer contexts
    # Example: "set track to volume to -10 db"
    normalized = re.sub(
        r"\btrack\s+to\b\s+(volume|pan|mute|solo|send\b)",
        r"track 2 \1",
        normalized,
    )
    # Also handle "track too" → "track 2" for the same contexts
    normalized = re.sub(
        r"\btrack\s+too\b\s+(volume|pan|mute|solo|send\b)",
        r"track 2 \1",
        normalized,
    )

    return normalized


def parse_command_layered(text: str, parse_index: Dict) -> Optional[Dict[str, Any]]:
    """Full layered parsing pipeline.

    Coordinates all layers and builds final raw_intent.

    Args:
        text: Input text command
        parse_index: Parse index dict from ParseIndexBuilder

    Returns:
        raw_intent dict ready for intent_mapper, or None if parsing failed
    """
    from server.services.nlp.action_parser import parse_action
    from server.services.nlp.track_parser import parse_track
    from server.services.nlp.device_param_parser import parse_device_param

    # Import typo corrector (from nlp-service)
    import pathlib
    import sys
    nlp_dir = pathlib.Path(__file__).resolve().parent.parent.parent / "nlp-service"
    if nlp_dir.exists() and str(nlp_dir) not in sys.path:
        sys.path.insert(0, str(nlp_dir))


    try:
        from parsers import apply_typo_corrections
        # Apply typo corrections BEFORE parsing (same as old parser)
        text_corrected = apply_typo_corrections(text)
    except Exception:
        # Fallback to uncorrected text if typo corrector unavailable
        text_corrected = text

    # Lowercase for consistency
    text_lower = text_corrected.lower()

    # Normalize simple number words in track references so
    # "open track one" behaves like "open track 1".
    text_lower = _normalize_track_number_words(text_lower)

    # Apply fuzzy action word replacement for better pattern matching
    # This ensures fallback patterns can match typos like "lsit" → "list"
    text_fuzzy_corrected = _apply_fuzzy_action_corrections(text_lower)

    # First: try OPEN navigation patterns that should always map to
    # open_capabilities intents (mixer/device/drawer).
    open_nav = _try_open_navigation_patterns(text_lower, text)
    if open_nav:
        return open_nav

    # First: try special GET/query patterns that should always map to
    # get_parameter intents (project counts/lists, topology queries, etc.).
    # This preserves legacy behavior for queries like:
    #   "list audio tracks" → audio_tracks_list
    special = _try_special_get_patterns(text_fuzzy_corrected, text)
    if special:
        return special

    # Try song-level commands (undo/redo, locators, song info)
    # These are complete commands that don't need multi-layer parsing
    song_intent = _try_song_patterns(text_lower, text)
    if song_intent:
        return song_intent

    # Try device action commands (load, etc.)
    # These are complete commands that specify device operations
    device_action_intent = _try_device_action_patterns(text_lower, text)
    if device_action_intent:
        return device_action_intent

    # Try device browser commands (list devices, etc.)
    # These commands display available devices for user selection
    device_browser_intent = _try_device_browser_patterns(text_lower, text)
    if device_browser_intent:
        return device_browser_intent

    # Layer 1: Parse action/value/unit
    # Pass original text to preserve case in user-provided names
    action = parse_action(text_lower, original_text=text)

    # Layer 2: Parse track/return/master
    track = parse_track(text_lower)

    # Layer 3: Parse device/parameter
    device_param = parse_device_param(text_lower, parse_index)

    # Layer 4: Build intent from layer outputs
    raw_intent = build_raw_intent(text, action, track, device_param)

    # If layered approach succeeded, return it
    if raw_intent:
        return raw_intent

    # No match
    return None


def _try_open_navigation_patterns(text_lower: str, original_text: str) -> Optional[Dict[str, Any]]:
    """Recognize 'open …' drawer/mixer/device requests and build open_capabilities.

    Mirrors logic from nlp-service/execution/regex_executor._open_capabilities_from_regex
    for compatibility with existing UI behavior.
    """
    import re as _re

    qs = text_lower.strip()
    if not (qs.startswith("open ") or qs.startswith("close ") or qs.startswith("pin ") or qs.startswith("unpin ")):
        return None

    # Sends group (preselect) – must be checked before generic track mixer
    m = _re.search(r"^\s*open\s+track\s+(\d+)\s+send\s+([a-l])(?:\s+controls)?\s*$", qs)
    if m:
        ti = int(m.group(1)); letter = m.group(2).upper()
        return {
            "intent": "open_capabilities",
            "target": {"type": "mixer", "entity": "track", "track_index": ti, "group_hint": "Sends", "send_ref": letter},
            "meta": {"utterance": original_text, "parsed_by": "regex_open"}
        }

    # Device on return by index
    m = _re.search(r"^\s*open\s+return\s+([a-l])\s+device\s+(\d+)(?:\s+([a-z0-9][a-z0-9 /%\.-]+))?\s*$", qs)
    if m:
        letter = m.group(1).upper(); di = int(m.group(2)); ph = (m.group(3) or "").strip() or None
        payload: Dict[str, Any] = {"type": "device", "scope": "return", "return_ref": letter, "device_index": di}
        if ph:
            payload["param_hint"] = ph
        return {"intent": "open_capabilities", "target": payload, "meta": {"utterance": original_text, "parsed_by": "regex_open"}}

    # Device on return by name (+ optional ordinal)
    m = _re.search(r"^\s*open\s+return\s+([a-l])\s+([a-z0-9 ][a-z0-9 \-]+?)(?:\s+(\d+))?(?:\s+([a-z0-9][a-z0-9 /%\.-]+))?\s*$", qs)
    if m:
        letter = m.group(1).upper()
        name = m.group(2).strip()
        ords = m.group(3)
        ph = (m.group(4) or "").strip() or None
        payload: Dict[str, Any] = {"type": "device", "scope": "return", "return_ref": letter, "device_name_hint": name}
        if ords:
            try:
                payload["device_ordinal_hint"] = int(ords)
            except Exception:
                pass
        if ph:
            payload["param_hint"] = ph
        return {"intent": "open_capabilities", "target": payload, "meta": {"utterance": original_text, "parsed_by": "regex_open"}}

    # Generic mixer scopes (track/return/master) checked after device/sends
    m = _re.search(r"^\s*open\s+track\s+(\d+)(?:\s+(?:controls|mixer))?\s*$", qs)
    if m:
        ti = int(m.group(1))
        return {
            "intent": "open_capabilities",
            "target": {"type": "mixer", "entity": "track", "track_index": ti},
            "meta": {"utterance": original_text, "parsed_by": "regex_open"}
        }
    m = _re.search(r"^\s*open\s+return\s+([a-l])(?:\s+(?:controls|mixer))?\s*$", qs)
    if m:
        letter = m.group(1).upper()
        return {
            "intent": "open_capabilities",
            "target": {"type": "mixer", "entity": "return", "return_ref": letter},
            "meta": {"utterance": original_text, "parsed_by": "regex_open"}
        }
    m = _re.search(r"^\s*open\s+master(?:\s+(?:controls|mixer))?\s*$", qs)
    if m:
        return {
            "intent": "open_capabilities",
            "target": {"type": "mixer", "entity": "master"},
            "meta": {"utterance": original_text, "parsed_by": "regex_open"}
        }

    # Drawer actions
    m = _re.search(r"^\s*open\s+controls\s*$", qs)
    if m:
        return {
            "intent": "open_capabilities",
            "target": {"type": "drawer", "action": "open"},
            "meta": {"utterance": original_text, "parsed_by": "regex_open"}
        }
    m = _re.search(r"^\s*close\s+controls\s*$", qs)
    if m:
        return {
            "intent": "open_capabilities",
            "target": {"type": "drawer", "action": "close"},
            "meta": {"utterance": original_text, "parsed_by": "regex_open"}
        }
    m = _re.search(r"^\s*pin\s+controls\s*$", qs)
    if m:
        return {
            "intent": "open_capabilities",
            "target": {"type": "drawer", "action": "pin"},
            "meta": {"utterance": original_text, "parsed_by": "regex_open"}
        }
    m = _re.search(r"^\s*unpin\s+controls\s*$", qs)
    if m:
        return {
            "intent": "open_capabilities",
            "target": {"type": "drawer", "action": "unpin"},
            "meta": {"utterance": original_text, "parsed_by": "regex_open"}
        }

    return None


def _try_special_get_patterns(text_lower: str, original_text: str) -> Optional[Dict[str, Any]]:
    """Try special GET query patterns that don't fit the layered parser structure.

    These are complex queries that need complete pattern matching:
    - Topology queries (send routing)
    - Device lists
    - Source queries (who sends to)
    - State bundles
    - Project counts/lists
    - Device by ordinal
    - Returns summaries
    """
    import re

    # 1. TOPOLOGY: Send effects routing
    # "what does track 1 send A affect" | "what is track 1 send A connected to"
    m1 = re.search(r"what\s+(?:does|is)\s+track\s+(\d+)\s+send\s+([a-l])\s+(?:affect|connect\w*|go\s+to|route|target|do)\b", text_lower)
    m2 = re.search(r"what\s+is\s+the\s+effect\s+on\s+track\s+(\d+)\s+send\s+([a-l])\b", text_lower)
    m = m1 or m2
    if m:
        track_num = int(m.group(1))
        send_letter = m.group(2).upper()
        return {
            "intent": "get_parameter",
            "targets": [{
                "track": f"Track {track_num}",
                "plugin": None,
                "parameter": f"send {send_letter} effects"
            }],
            "meta": {
                "utterance": original_text,
                "confidence": 0.95,
                "pipeline": "regex",
                "layer_methods": {"pattern": "topology"}
            }
        }

    # 2. DEVICE LISTS: Get all devices on track/return
    # "what are return A devices" | "what are track 1 devices"
    m_ret = re.search(r"what\s+are\s+return\s+([a-l])\s+devices\b", text_lower)
    m_trk = re.search(r"what\s+are\s+track\s+(\d+)\s+devices\b", text_lower)
    if m_ret:
        return_letter = m_ret.group(1).upper()
        return {
            "intent": "get_parameter",
            "targets": [{
                "track": f"Return {return_letter}",
                "plugin": None,
                "parameter": "devices"
            }],
            "meta": {
                "utterance": original_text,
                "confidence": 0.95,
                "pipeline": "regex",
                "layer_methods": {"pattern": "device_list"}
            }
        }
    if m_trk:
        track_num = int(m_trk.group(1))
        return {
            "intent": "get_parameter",
            "targets": [{
                "track": f"Track {track_num}",
                "plugin": None,
                "parameter": "devices"
            }],
            "meta": {
                "utterance": original_text,
                "confidence": 0.95,
                "pipeline": "regex",
                "layer_methods": {"pattern": "device_list"}
            }
        }

    # 3. SOURCE QUERIES: Who sends to return
    # "who sends to return A" | "which tracks send to return B"
    m = re.search(r"(who|which\s+tracks)\s+sends?\s+to\s+return\s+([a-l])\b", text_lower)
    if m:
        return_letter = m.group(2).upper()
        return {
            "intent": "get_parameter",
            "targets": [{
                "track": f"Return {return_letter}",
                "plugin": None,
                "parameter": "sources"
            }],
            "meta": {
                "utterance": original_text,
                "confidence": 0.95,
                "pipeline": "regex",
                "layer_methods": {"pattern": "sources"}
            }
        }

    # 4. STATE BUNDLES: Full mixer state for track/return/master
    # "what is track 1 state" | "what is return A state" | "what is master state"
    m_trk = re.search(r"what\s+is\s+track\s+(\d+)\s+state\b", text_lower)
    m_ret = re.search(r"what\s+is\s+return\s+([a-l])\s+state\b", text_lower)
    m_mas = re.search(r"what\s+is\s+master\s+state\b", text_lower)
    if m_trk:
        track_num = int(m_trk.group(1))
        return {
            "intent": "get_parameter",
            "targets": [{
                "track": f"Track {track_num}",
                "plugin": None,
                "parameter": "state"
            }],
            "meta": {
                "utterance": original_text,
                "confidence": 0.95,
                "pipeline": "regex",
                "layer_methods": {"pattern": "state"}
            }
        }
    if m_ret:
        return_letter = m_ret.group(1).upper()
        return {
            "intent": "get_parameter",
            "targets": [{
                "track": f"Return {return_letter}",
                "plugin": None,
                "parameter": "state"
            }],
            "meta": {
                "utterance": original_text,
                "confidence": 0.95,
                "pipeline": "regex",
                "layer_methods": {"pattern": "state"}
            }
        }
    if m_mas:
        return {
            "intent": "get_parameter",
            "targets": [{
                "track": "Master",
                "plugin": None,
                "parameter": "state"
            }],
            "meta": {
                "utterance": original_text,
                "confidence": 0.95,
                "pipeline": "regex",
                "layer_methods": {"pattern": "state"}
            }
        }

    # 5. PROJECT COUNTS: How many tracks/returns
    if re.search(r"\bhow\s+many\s+audio\s+tracks\b|\baudio\s+tracks?\s+count\b|\bnumber\s+of\s+audio\s+tracks\b", text_lower):
        return {
            "intent": "get_parameter",
            "targets": [{"track": None, "plugin": None, "parameter": "audio_tracks_count"}],
            "meta": {
                "utterance": original_text,
                "confidence": 0.95,
                "pipeline": "regex",
                "layer_methods": {"pattern": "project_counts"}
            }
        }
    if re.search(r"\bhow\s+many\s+midi\s+tracks\b|\bmidi\s+tracks?\s+count\b|\bnumber\s+of\s+midi\s+tracks\b", text_lower):
        return {
            "intent": "get_parameter",
            "targets": [{"track": None, "plugin": None, "parameter": "midi_tracks_count"}],
            "meta": {
                "utterance": original_text,
                "confidence": 0.95,
                "pipeline": "regex",
                "layer_methods": {"pattern": "project_counts"}
            }
        }
    if re.search(r"\bhow\s+many\s+return\s+tracks\b|\breturns?\s+count\b|\bnumber\s+of\s+returns?\b", text_lower):
        return {
            "intent": "get_parameter",
            "targets": [{"track": None, "plugin": None, "parameter": "return_tracks_count"}],
            "meta": {
                "utterance": original_text,
                "confidence": 0.95,
                "pipeline": "regex",
                "layer_methods": {"pattern": "project_counts"}
            }
        }
    if re.search(r"\bhow\s+many\s+tracks\b|\bnumber\s+of\s+tracks\b|\btrack\s+count\b", text_lower):
        return {
            "intent": "get_parameter",
            "targets": [{"track": None, "plugin": None, "parameter": "tracks_count"}],
            "meta": {
                "utterance": original_text,
                "confidence": 0.95,
                "pipeline": "regex",
                "layer_methods": {"pattern": "project_counts"}
            }
        }

    # 6. PROJECT LISTS: List all tracks/returns
    if re.search(r"\blist\s+(the\s+)?tracks\b|\blist\s+all\s+tracks\b|\btracks\s+list\b", text_lower):
        return {
            "intent": "get_parameter",
            "targets": [{"track": None, "plugin": None, "parameter": "tracks_list"}],
            "meta": {
                "utterance": original_text,
                "confidence": 0.95,
                "pipeline": "regex",
                "layer_methods": {"pattern": "project_lists"}
            }
        }
    if re.search(r"\blist\s+(the\s+)?audio\s+tracks\b|\baudio\s+tracks\s+list\b", text_lower):
        return {
            "intent": "get_parameter",
            "targets": [{"track": None, "plugin": None, "parameter": "audio_tracks_list"}],
            "meta": {
                "utterance": original_text,
                "confidence": 0.95,
                "pipeline": "regex",
                "layer_methods": {"pattern": "project_lists"}
            }
        }
    if re.search(r"\blist\s+(the\s+)?midi\s+tracks\b|\bmidi\s+tracks\s+list\b", text_lower):
        return {
            "intent": "get_parameter",
            "targets": [{"track": None, "plugin": None, "parameter": "midi_tracks_list"}],
            "meta": {
                "utterance": original_text,
                "confidence": 0.95,
                "pipeline": "regex",
                "layer_methods": {"pattern": "project_lists"}
            }
        }
    if re.search(r"\blist\s+(the\s+)?returns?\b|\blist\s+all\s+returns?\b|\blist\s+return\s+tracks\b|\blist\s+all\s+return\s+tracks\b|\breturns?\s+list\b", text_lower):
        return {
            "intent": "get_parameter",
            "targets": [{"track": None, "plugin": None, "parameter": "return_tracks_list"}],
            "meta": {
                "utterance": original_text,
                "confidence": 0.95,
                "pipeline": "regex",
                "layer_methods": {"pattern": "project_lists"}
            }
        }

    # 7. DEVICE BY ORDINAL: Query device parameter by position
    # "what is return A device 1 feedback" | "what is track 2 device 3 decay"
    m_ret = re.search(r"what\s+is\s+return\s+([a-l])\s+device\s+(\d+)\s+([a-z0-9][a-z0-9 /%\.-]+)\??$", text_lower)
    m_trk = re.search(r"what\s+is\s+track\s+(\d+)\s+device\s+(\d+)\s+([a-z0-9][a-z0-9 /%\.-]+)\??$", text_lower)
    if m_ret:
        return_letter = m_ret.group(1).upper()
        device_index = int(m_ret.group(2))
        param_name = m_ret.group(3).strip()
        return {
            "intent": "get_parameter",
            "targets": [{
                "track": f"Return {return_letter}",
                "plugin": "device",
                "parameter": param_name,
                "device_ordinal": device_index
            }],
            "meta": {
                "utterance": original_text,
                "confidence": 0.95,
                "pipeline": "regex",
                "layer_methods": {"pattern": "device_ordinal"}
            }
        }
    if m_trk:
        track_num = int(m_trk.group(1))
        device_index = int(m_trk.group(2))
        param_name = m_trk.group(3).strip()
        return {
            "intent": "get_parameter",
            "targets": [{
                "track": f"Track {track_num}",
                "plugin": "device",
                "parameter": param_name,
                "device_ordinal": device_index
            }],
            "meta": {
                "utterance": original_text,
                "confidence": 0.95,
                "pipeline": "regex",
                "layer_methods": {"pattern": "device_ordinal"}
            }
        }

    # 8. RETURNS SUMMARY: All return sends for a track
    # "what is track 1 returns" | "what are track 2 returns"
    m = re.search(r"what\s+(?:is|are)\s+track\s+(\d+)\s+returns\b", text_lower)
    if m:
        track_num = int(m.group(1))
        return {
            "intent": "get_parameter",
            "targets": [{
                "track": f"Track {track_num}",
                "plugin": None,
                "parameter": "returns"
            }],
            "meta": {
                "utterance": original_text,
                "confidence": 0.95,
                "pipeline": "regex",
                "layer_methods": {"pattern": "returns_summary"}
            }
        }

    # No special pattern matched
    return None


def _try_song_patterns(text_lower: str, original_text: str) -> Optional[Dict[str, Any]]:
    """Try song-level command patterns (undo/redo, locators, song info).

    These commands operate at the song/project level rather than on specific
    tracks/devices, so they bypass the multi-layer parser.

    Examples:
        "undo" → song undo
        "list locators" → list arrangement cue points
        "jump to intro" → jump to locator by name
    """
    from server.services.nlp.layered.parsers.song_parser import parse_song

    result = parse_song(original_text)
    if not result:
        return None

    # Convert to raw_intent format expected by intent_mapper
    domain = result.get("domain")
    action = result.get("action")

    return {
        "intent": "song_command",
        "domain": domain,
        "action": action,
        "locator_index": result.get("locator_index"),
        "locator_name": result.get("locator_name"),
        "new_name": result.get("new_name"),
        "meta": {
            "utterance": original_text,
            "confidence": 0.98,
            "pipeline": "regex_song",
            "parsed_by": "song_parser"
        }
    }


def _try_device_action_patterns(text_lower: str, original_text: str) -> Optional[Dict[str, Any]]:
    """Try device action command patterns (load device, etc.).

    These commands operate on devices (loading, removing, etc.) and bypass
    the multi-layer parser for direct execution.

    Examples:
        "load reverb on track 2" → load device on track
        "add compressor to return A" → load device on return
        "load analog preset lush pad on track 3" → load device with preset
    """
    from server.services.nlp.layered.parsers.device_action_parser import parse_device_action

    result = parse_device_action(original_text)
    if not result:
        return None

    # Convert to raw_intent format expected by intent_mapper
    domain = result.get("domain")
    action = result.get("action")

    return {
        "intent": "device_action",
        "domain": domain,
        "action": action,
        "device_name": result.get("device_name"),
        "preset_name": result.get("preset_name"),
        "device_index": result.get("device_index"),
        "device_ordinal": result.get("device_ordinal"),
        "target_domain": result.get("target_domain"),
        "track_index": result.get("track_index"),
        "return_index": result.get("return_index"),
        "return_ref": result.get("return_ref"),
        "meta": {
            "utterance": original_text,
            "confidence": 0.98,
            "pipeline": "regex_device_action",
            "parsed_by": "device_action_parser"
        }
    }


def _try_device_browser_patterns(text_lower: str, original_text: str) -> Optional[Dict[str, Any]]:
    """Try device browser command patterns (list devices, etc.).

    These commands display available devices and presets for user selection.

    Examples:
        "list devices" → show all device categories
        "show audio effects" → show audio effects devices
        "list instruments" → show instrument devices
    """
    from server.services.nlp.layered.parsers.device_browser_parser import parse_device_browser

    result = parse_device_browser(original_text)
    if not result:
        return None

    return {
        "intent": "device_browser",
        "domain": result.get("domain"),
        "action": result.get("action"),
        "category": result.get("category"),
        "meta": {
            "utterance": original_text,
            "confidence": 0.98,
            "pipeline": "regex_device_browser",
            "parsed_by": "device_browser_parser"
        }
    }
