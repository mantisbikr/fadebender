from __future__ import annotations

from typing import Any, Dict

from fastapi import HTTPException

from server.config.app_config import get_app_config
from server.services.ableton_client import request_op
from server.models.intents_api import CanonicalIntent


def set_track_routing(intent: CanonicalIntent) -> Dict[str, Any]:
    if intent.track_index is None:
        raise HTTPException(400, "track_index_required")
    ti = int(intent.track_index)

    # Allowed keys for routing payload
    allowed = {
        "monitor_state": None,
        "audio_from_type": None,
        "audio_from_channel": None,
        "audio_to_type": None,
        "audio_to_channel": None,
        "midi_from_type": None,
        "midi_from_channel": None,
        "midi_to_type": None,
        "midi_to_channel": None,
    }

    payload: Dict[str, Any] = {}
    if isinstance(intent.value, dict):
        for k in allowed.keys():
            v = intent.value.get(k)
            if v is not None:
                payload[k] = v

    # Validate against available options
    cur = request_op("get_track_routing", timeout=1.0, track_index=ti) or {}
    data_cur = (cur.get("data") or cur) if isinstance(cur, dict) else {}
    opts = (data_cur or {}).get("options") or {}
    cfg = get_app_config()
    aliases = (cfg.get("routing_aliases") or {}).get("track", {})

    def _normalize_choice(val, option_key):
        if val is None:
            return None
        arr = opts.get(option_key) or []
        lower_map = {str(x).strip().lower(): str(x) for x in arr}
        v_in = str(val).strip()
        v_l = v_in.lower()
        if v_l in lower_map:
            return lower_map[v_l]
        # Alias map: aliases[option_key] is a dict of alias->canonical
        try:
            ali = ((aliases.get(option_key)) or {})
            target = ali.get(v_l)
            if target:
                t_l = str(target).strip().lower()
                if t_l in lower_map:
                    return lower_map[t_l]
        except Exception:
            pass
        return None

    # Normalize and validate each provided routing key
    if "audio_to_type" in payload:
        norm = _normalize_choice(payload.get("audio_to_type"), "audio_to_types")
        if norm is None:
            return {"ok": False, "error": "invalid_audio_to_type", "requested": payload.get("audio_to_type"), "allowed": opts.get("audio_to_types")}
        payload["audio_to_type"] = norm
    if "audio_to_channel" in payload:
        norm = _normalize_choice(payload.get("audio_to_channel"), "audio_to_channels")
        if norm is None:
            return {"ok": False, "error": "invalid_audio_to_channel", "requested": payload.get("audio_to_channel"), "allowed": opts.get("audio_to_channels")}
        payload["audio_to_channel"] = norm
    if "audio_from_type" in payload:
        norm = _normalize_choice(payload.get("audio_from_type"), "audio_from_types")
        if norm is None:
            return {"ok": False, "error": "invalid_audio_from_type", "requested": payload.get("audio_from_type"), "allowed": opts.get("audio_from_types")}
        payload["audio_from_type"] = norm
    if "audio_from_channel" in payload:
        norm = _normalize_choice(payload.get("audio_from_channel"), "audio_from_channels")
        if norm is None:
            return {"ok": False, "error": "invalid_audio_from_channel", "requested": payload.get("audio_from_channel"), "allowed": opts.get("audio_from_channels")}
        payload["audio_from_channel"] = norm
    if "midi_from_type" in payload:
        norm = _normalize_choice(payload.get("midi_from_type"), "midi_from_types")
        if norm is None:
            return {"ok": False, "error": "invalid_midi_from_type", "requested": payload.get("midi_from_type"), "allowed": opts.get("midi_from_types")}
        payload["midi_from_type"] = norm
    if "midi_from_channel" in payload:
        norm = _normalize_choice(payload.get("midi_from_channel"), "midi_from_channels")
        if norm is None:
            return {"ok": False, "error": "invalid_midi_from_channel", "requested": payload.get("midi_from_channel"), "allowed": opts.get("midi_from_channels")}
        payload["midi_from_channel"] = norm
    if "midi_to_type" in payload:
        norm = _normalize_choice(payload.get("midi_to_type"), "midi_to_types")
        if norm is None:
            return {"ok": False, "error": "invalid_midi_to_type", "requested": payload.get("midi_to_type"), "allowed": opts.get("midi_to_types")}
        payload["midi_to_type"] = norm
    if "midi_to_channel" in payload:
        norm = _normalize_choice(payload.get("midi_to_channel"), "midi_to_channels")
        if norm is None:
            return {"ok": False, "error": "invalid_midi_to_channel", "requested": payload.get("midi_to_channel"), "allowed": opts.get("midi_to_channels")}
        payload["midi_to_channel"] = norm

    if intent.dry_run:
        return {"ok": True, "preview": {"current": (cur.get("data") or cur), "apply": {"track_index": ti, **payload}}}

    resp = request_op("set_track_routing", timeout=1.2, track_index=ti, **payload)
    if not resp:
        raise HTTPException(504, "no_reply")
    return resp


def set_return_routing(intent: CanonicalIntent) -> Dict[str, Any]:
    if intent.return_index is None:
        raise HTTPException(400, "return_index_required")
    ri = int(intent.return_index)

    allowed = {"audio_to_type": None, "audio_to_channel": None, "sends_mode": None}
    payload: Dict[str, Any] = {}
    if isinstance(intent.value, dict):
        for k in allowed.keys():
            v = intent.value.get(k)
            if v is not None:
                payload[k] = v

    # Validate choices against options
    cur = request_op("get_return_routing", timeout=1.0, return_index=ri) or {}
    data_cur = (cur.get("data") or cur) if isinstance(cur, dict) else {}
    opts = (data_cur or {}).get("options") or {}
    cfg = get_app_config()
    aliases = (cfg.get("routing_aliases") or {}).get("return", {})

    def _normalize_choice(val, option_key):
        if val is None:
            return None
        arr = opts.get(option_key) or []
        lower_map = {str(x).strip().lower(): str(x) for x in arr}
        v_in = str(val).strip(); v_l = v_in.lower()
        if v_l in lower_map:
            return lower_map[v_l]
        try:
            ali = ((aliases.get(option_key)) or {})
            target = ali.get(v_l)
            if target:
                t_l = str(target).strip().lower()
                if t_l in lower_map:
                    return lower_map[t_l]
        except Exception:
            pass
        return None

    if "audio_to_type" in payload:
        norm = _normalize_choice(payload.get("audio_to_type"), "audio_to_types")
        if norm is None:
            return {"ok": False, "error": "invalid_audio_to_type", "requested": payload.get("audio_to_type"), "allowed": opts.get("audio_to_types")}
        payload["audio_to_type"] = norm
    if "audio_to_channel" in payload:
        norm = _normalize_choice(payload.get("audio_to_channel"), "audio_to_channels")
        if norm is None:
            return {"ok": False, "error": "invalid_audio_to_channel", "requested": payload.get("audio_to_channel"), "allowed": opts.get("audio_to_channels")}
        payload["audio_to_channel"] = norm

    if intent.dry_run:
        return {"ok": True, "preview": {"current": (cur.get("data") or cur), "apply": {"return_index": ri, **payload}}}

    resp = request_op("set_return_routing", timeout=1.2, return_index=ri, **payload)
    if not resp:
        raise HTTPException(504, "no_reply")
    return resp

