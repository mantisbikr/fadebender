"""Layer 4: Intent Builder & Router

Combines outputs from Layers 1-3 into final raw_intent structure.
Routes based on intent_type and device field.
"""

from __future__ import annotations
from typing import Dict, Optional, Any
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
    return {
        "intent": "transport",
        "operation": {
            "action": str(action.value) if isinstance(action.value, str) else None,
            "value": action.value if not isinstance(action.value, str) else None,
            "unit": action.unit
        },
        "meta": meta
    }


def _build_navigation_intent(
    action: ActionMatch,
    track: Optional[TrackMatch],
    device_param: Optional[DeviceParamMatch],
    meta: Dict
) -> Dict[str, Any]:
    """Build navigation intent (open/list tracks, devices, etc.)."""
    # Build target reference
    target_ref = track.reference if track else None

    # If device specified, append to reference
    if device_param and device_param.device:
        target_ref = f"{target_ref} {device_param.device}" if target_ref else device_param.device

    return {
        "intent": action.intent_type,
        "target": target_ref,
        "meta": meta
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

    # Apply fuzzy action word replacement for better pattern matching
    # This ensures fallback patterns can match typos like "lsit" → "list"
    text_fuzzy_corrected = _apply_fuzzy_action_corrections(text_lower)

    # Layer 1: Parse action/value/unit
    action = parse_action(text_lower)

    # Layer 2: Parse track/return/master
    track = parse_track(text_lower)

    # Layer 3: Parse device/parameter
    device_param = parse_device_param(text_lower, parse_index)

    # Layer 4: Build intent from layer outputs
    raw_intent = build_raw_intent(text, action, track, device_param)

    # If layered approach succeeded, return it
    if raw_intent:
        return raw_intent

    # FALLBACK: Special GET patterns that don't fit the layered structure
    # These mirror the old regex_executor.py patterns (lines 118-281)
    # Use fuzzy-corrected text for better pattern matching (e.g., "lsit" → "list")
    return _try_special_get_patterns(text_fuzzy_corrected, text)


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
    m1 = re.search(r"what\s+(?:does|is)\s+track\s+(\d+)\s+send\s+([a-c])\s+(?:affect|connect\w*|go\s+to|route|target|do)\b", text_lower)
    m2 = re.search(r"what\s+is\s+the\s+effect\s+on\s+track\s+(\d+)\s+send\s+([a-c])\b", text_lower)
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
    m_ret = re.search(r"what\s+are\s+return\s+([a-c])\s+devices\b", text_lower)
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
    m = re.search(r"(who|which\s+tracks)\s+sends?\s+to\s+return\s+([a-c])\b", text_lower)
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
    m_ret = re.search(r"what\s+is\s+return\s+([a-c])\s+state\b", text_lower)
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
    if re.search(r"\blist\s+(the\s+)?returns?\b|\blist\s+return\s+tracks\b|\breturns?\s+list\b", text_lower):
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
    m_ret = re.search(r"what\s+is\s+return\s+([a-c])\s+device\s+(\d+)\s+([a-z0-9][a-z0-9 /%\.-]+)\??$", text_lower)
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
