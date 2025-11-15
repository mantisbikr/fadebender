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

    # ROUTE 3: Parameter intents (mixer or device)
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

    # Lowercase for consistency
    text_lower = text.lower()

    # Layer 1: Parse action/value/unit
    action = parse_action(text_lower)

    # Layer 2: Parse track/return/master
    track = parse_track(text_lower)

    # Layer 3: Parse device/parameter
    device_param = parse_device_param(text_lower, parse_index)

    # Layer 4: Build intent from layer outputs
    raw_intent = build_raw_intent(text, action, track, device_param)

    return raw_intent
