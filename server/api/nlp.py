from __future__ import annotations

from typing import Any, Dict

import os
import pathlib
import re
import sys

from fastapi import APIRouter, HTTPException

from server.models.requests import IntentParseBody
from server.services.ableton_client import request_op
from server.services.intent_mapper import map_llm_to_canonical
from server.services.param_normalizer import _levenshtein_distance


router = APIRouter()

# Check if layered parser should be used
USE_LAYERED = os.getenv("USE_LAYERED_PARSER", "").lower() in ("1", "true", "yes")
print(f"[NLP] USE_LAYERED_PARSER env var: {os.getenv('USE_LAYERED_PARSER')}, USE_LAYERED={USE_LAYERED}")

# Module-level cache for parse index (only needed for layered parser)
_PARSE_INDEX = None
_PARSE_INDEX_TIMESTAMP = 0.0
_PARSE_INDEX_TTL = 60.0  # Refresh every 60 seconds to pick up device changes


_VERB_CANONICAL_MAP = {
    # Creation
    "create": "create",
    "add": "create",
    "new": "create",
    # Deletion
    "delete": "delete",
    "remove": "delete",
    # Duplication
    "duplicate": "duplicate",
    "copy": "duplicate",
    # Transport / firing
    "fire": "fire",
    "launch": "fire",
    "stop": "stop",
    # Naming
    "rename": "rename",
    "name": "rename",
    # Track arm
    "arm": "arm",
    "disarm": "disarm",
    "unarm": "disarm",
}


def _normalize_command_verbs(text: str) -> str:
    """Fuzzy-normalize key command verbs before regex parsing.

    This recovers from common one-off typos like 'duplidate' → 'duplicate'
    without touching names, numbers, or parameters. Only verbs in
    _VERB_CANONICAL_MAP are considered, and we require Levenshtein distance 1.
    """
    if not text:
        return text

    # Split but keep whitespace separators so we can rejoin faithfully
    tokens = re.split(r"(\s+)", text)
    for i, tok in enumerate(tokens):
        word = tok.strip()
        if not word or not word.isalpha():
            continue

        lower = word.lower()
        if lower in _VERB_CANONICAL_MAP:
            # Already a known verb/synonym; leave as-is so regexes
            # that distinguish 'copy' vs 'duplicate' still work.
            continue

        best = None
        best_dist = 10
        for cand in _VERB_CANONICAL_MAP.keys():
            # Quick length gate to avoid wild matches
            if abs(len(cand) - len(lower)) > 2:
                continue
            dist = _levenshtein_distance(lower, cand)
            if dist < best_dist:
                best = cand
                best_dist = dist

        # Only accept very close matches:
        #   - distance 1 for any length
        #   - distance 2 allowed for longer words (>= 6 chars)
        if best is not None and (
            best_dist == 1 or (best_dist == 2 and len(lower) >= 6)
        ):
            tokens[i] = best

    return "".join(tokens)


def _get_parse_index() -> Dict[str, Any]:
    """Get or build the parse index for layered parser.

    Builds index from Live set if available, otherwise returns minimal index.
    Cached at module level with 60s TTL to pick up device changes.
    """
    global _PARSE_INDEX, _PARSE_INDEX_TIMESTAMP

    import time

    # Check if cache is still valid (non-empty AND not expired)
    cache_age = time.time() - _PARSE_INDEX_TIMESTAMP
    if _PARSE_INDEX is not None and cache_age < _PARSE_INDEX_TTL:
        return _PARSE_INDEX

    try:
        from server.services.parse_index.parse_index_builder import ParseIndexBuilder

        # Try to build index from Live snapshot devices (tracks + returns + master).
        try:
            # Use fast snapshot/full endpoint (structure only, no param values needed)
            # This is 6-7x faster than old snapshot endpoint (1.0s vs 6.8s)
            import requests

            snap_resp = requests.get("http://127.0.0.1:8722/snapshot/full?skip_param_values=true", timeout=3.0)
            live_devices = []
            if snap_resp.ok:
                snapshot = snap_resp.json()
                data = snapshot.get("data", {})

                # Extract devices from tracks
                for track in data.get("tracks", []):
                    for dev in track.get("devices", []):
                        live_devices.append(
                            {
                                "name": dev.get("name"),
                                "device_type": str(dev.get("device_type", "unknown")).lower(),
                                "ordinals": 1,
                            }
                        )

                # Extract devices from returns
                for ret in data.get("returns", []):
                    for dev in ret.get("devices", []):
                        live_devices.append(
                            {
                                "name": dev.get("name"),
                                "device_type": str(dev.get("device_type", "unknown")).lower(),
                                "ordinals": 1,
                            }
                        )

                # Extract devices from master
                for dev in data.get("master", {}).get("devices", []):
                    live_devices.append(
                        {
                            "name": dev.get("name"),
                            "device_type": str(dev.get("device_type", "unknown")).lower(),
                            "ordinals": 1,
                        }
                    )

            builder = ParseIndexBuilder()
            _PARSE_INDEX = builder.build_from_live_set(live_devices)
            _PARSE_INDEX_TIMESTAMP = time.time()
            print(f"[LAYERED] Built parse index with {len(_PARSE_INDEX.get('devices_in_set', []))} devices from fast snapshot")
        except Exception as e:
            print(f"[LAYERED] Failed to build parse index from snapshot: {e}, using minimal index")
            _PARSE_INDEX = {
                "version": "pi-minimal",
                "devices_in_set": [],
                "params_by_device": {},
                "device_type_index": {},
                "param_to_device_types": {},
                "mixer_params": ["volume", "pan", "mute", "solo", "send a", "send b", "send c", "send d"],
                "typo_map": {},
            }
            _PARSE_INDEX_TIMESTAMP = time.time()
    except Exception as e:
        print(f"[LAYERED] Failed to initialize parse index: {e}")
        _PARSE_INDEX = {
            "version": "pi-minimal",
            "devices_in_set": [],
            "params_by_device": {},
            "device_type_index": {},
            "param_to_device_types": {},
            "mixer_params": ["volume", "pan", "mute", "solo", "send a", "send b", "send c", "send d"],
            "typo_map": {},
        }
        _PARSE_INDEX_TIMESTAMP = time.time()

    return _PARSE_INDEX


@router.post("/intent/parse")
def intent_parse(body: IntentParseBody) -> Dict[str, Any]:
    """Parse NL text to canonical intent JSON (no execution).

    Preserves raw_intent for non-control intents (e.g., get_parameter) so
    NLP tests can validate structure even when ok=false. Adds optional
    'clarification' alongside raw_intent when disambiguation is possible.
    """

    # Lightweight pre-normalization for compact pan syntax.
    text = str(body.text or "")
    # Preserve original text (with casing) when provided via context for operations
    # that care about name formatting (e.g., rename track/scene/clip).
    context = body.context or {}
    original_text = str(context.get("original_text") or body.text or "")

    # Normalize clip coordinates so \"clip 4,2\" and \"clip 4 2\" behave the same.
    # This makes client-side punctuation differences harmless.
    try:
        text = re.sub(
            r"\bclip\s+(\d+)\s*,\s*(\d+)\b",
            r"clip \1 \2",
            text,
            flags=re.IGNORECASE,
        )
    except Exception:
        # If anything goes wrong, fall back to original text
        text = str(body.text or "")

    # Fuzzy-normalize key verbs before regex parsing so that
    # common typos like "duplidate" still hit fast paths.
    text = _normalize_command_verbs(text)

    # Pattern 1: "pan track N to VALUE L/R" → "set track N pan to +/-VALUE"
    m = re.search(r"\bpan\s+track\s+(\d+)\s+to\s+(-?\d+)\s*([LR])\b", text, flags=re.IGNORECASE)
    if m:
        idx = m.group(1)
        amt = m.group(2)
        side = m.group(3).upper()
        # Encode direction as sign: left = negative, right = positive
        signed_amt = f"-{amt}" if side == "L" else amt
        text = re.sub(
            r"\bpan\s+track\s+\d+\s+to\s+-?\d+\s*[LR]\b",
            f"set track {idx} pan to {signed_amt}",
            text,
            flags=re.IGNORECASE,
        )
    else:
        # Pattern 2: "pan track N to VALUE" (without L/R) → "set track N pan to VALUE"
        m2 = re.search(r"\bpan\s+track\s+(\d+)\s+to\s+(-?\d+)\b", text, flags=re.IGNORECASE)
        if m2:
            idx = m2.group(1)
            amt = m2.group(2)
            text = re.sub(
                r"\bpan\s+track\s+\d+\s+to\s+-?\d+\b",
                f"set track {idx} pan to {amt}",
                text,
                flags=re.IGNORECASE,
            )

    # Pattern 3: "pan master to VALUE [L/R]" → "set master pan to +/-VALUE"
    m3 = re.search(r"\bpan\s+master\s+to\s+(-?\d+)\s*([LR])?\b", text, flags=re.IGNORECASE)
    if m3:
        amt = m3.group(1)
        side = m3.group(2)
        if side:
            side = side.upper()
            signed_amt = f"-{amt}" if side == "L" else amt
            text = re.sub(
                r"\bpan\s+master\s+to\s+-?\d+\s*[LR]\b",
                f"set master pan to {signed_amt}",
                text,
                flags=re.IGNORECASE,
            )
        else:
            text = re.sub(
                r"\bpan\s+master\s+to\s+-?\d+\b",
                f"set master pan to {amt}",
                text,
                flags=re.IGNORECASE,
            )

    # Pattern 4: "pan return X to VALUE [L/R]" → "set return X pan to +/-VALUE"
    m4 = re.search(r"\bpan\s+return\s+([A-L])\s+to\s+(-?\d+)\s*([LR])?\b", text, flags=re.IGNORECASE)
    if m4:
        ret = m4.group(1).upper()
        amt = m4.group(2)
        side = m4.group(3)
        if side:
            side = side.upper()
            signed_amt = f"-{amt}" if side == "L" else amt
            text = re.sub(
                r"\bpan\s+return\s+[A-C]\s+to\s+-?\d+\s*[LR]\b",
                f"set return {ret} pan to {signed_amt}",
                text,
                flags=re.IGNORECASE,
            )
        else:
            text = re.sub(
                r"\bpan\s+return\s+[A-C]\s+to\s+-?\d+\b",
                f"set return {ret} pan to {amt}",
                text,
                flags=re.IGNORECASE,
            )

    raw_intent: Dict[str, Any] | None = None

    # Fast path: scene fire/stop commands (no need for full NLP or canonical mapper)
    scene_fire_match = re.search(r"\b(fire|launch)\s+scene\s+(\d+)\b", text, flags=re.IGNORECASE)
    scene_stop_match = re.search(r"\bstop\s+scene\s+(\d+)\b", text, flags=re.IGNORECASE)
    if scene_fire_match:
        scene_idx = int(scene_fire_match.group(2))
        raw_intent = {
            "intent": "transport",
            "operation": {
                "action": "scene_fire",
                "value": scene_idx,
            },
            "meta": {
                "utterance": text,
                "pipeline": "regex_scene",
            },
        }
        canonical = {"domain": "transport", "action": "scene_fire", "value": scene_idx}
        return {"ok": True, "intent": canonical, "raw_intent": raw_intent}
    elif scene_stop_match:
        # stop scene pattern has a single capturing group for the index
        scene_idx = int(scene_stop_match.group(1))
        raw_intent = {
            "intent": "transport",
            "operation": {
                "action": "scene_stop",
                "value": scene_idx,
            },
            "meta": {
                "utterance": text,
                "pipeline": "regex_scene",
            },
        }
        canonical = {"domain": "transport", "action": "scene_stop", "value": scene_idx}
        return {"ok": True, "intent": canonical, "raw_intent": raw_intent}

    # Fast path: clip fire/stop commands (Session view)
    clip_fire_match = re.search(
        r"\b(fire|launch)\s+clip\s+(\d+)[,\s]+(\d+)\b", text, flags=re.IGNORECASE
    )
    clip_stop_match = re.search(
        r"\bstop\s+clip\s+(\d+)[,\s]+(\d+)\b", text, flags=re.IGNORECASE
    )
    if clip_fire_match:
        ti = int(clip_fire_match.group(2))
        si = int(clip_fire_match.group(3))
        value = {"track_index": ti, "scene_index": si}
        raw_intent = {
            "intent": "transport",
            "operation": {
                "action": "clip_fire",
                "value": value,
            },
            "meta": {
                "utterance": text,
                "pipeline": "regex_clip",
            },
        }
        canonical = {"domain": "transport", "action": "clip_fire", "value": value}
        return {"ok": True, "intent": canonical, "raw_intent": raw_intent}
    if clip_stop_match:
        ti = int(clip_stop_match.group(1))
        si = int(clip_stop_match.group(2))
        value = {"track_index": ti, "scene_index": si}
        raw_intent = {
            "intent": "transport",
            "operation": {
                "action": "clip_stop",
                "value": value,
            },
            "meta": {
                "utterance": text,
                "pipeline": "regex_clip",
            },
        }
        canonical = {"domain": "transport", "action": "clip_stop", "value": value}
        return {"ok": True, "intent": canonical, "raw_intent": raw_intent}

    # Fast path: clip create/delete/duplicate (Session view)
    # Create clip: "create clip 4 3 [len]" or "create clip on track 4 scene 3 [len]"
    m_create_clip = re.search(
        r"\bcreate\s+clip\s+(\d+)\s*(?:,|\s)\s*(\d+)(?:\s+(\d+(?:\.\d+)?))?\b",
        text,
        flags=re.IGNORECASE,
    )
    if not m_create_clip:
        m_create_clip = re.search(
            r"\bcreate\s+clip\s+on\s+track\s+(\d+)\s+(?:scene\s+)?(\d+)(?:\s+(\d+(?:\.\d+)?))?\b",
            text,
            flags=re.IGNORECASE,
        )
    if m_create_clip:
        ti = int(m_create_clip.group(1))
        si = int(m_create_clip.group(2))
        length = float(m_create_clip.group(3)) if m_create_clip.group(3) else 4.0
        value = {"track_index": ti, "scene_index": si, "length_beats": length}
        raw_intent = {
            "intent": "transport",
            "operation": {"action": "clip_create", "value": value},
            "meta": {"utterance": original_text, "pipeline": "regex_clip_create"},
        }
        canonical = {"domain": "transport", "action": "clip_create", "value": value}
        return {"ok": True, "intent": canonical, "raw_intent": raw_intent}

    # Delete clip: "delete clip 4 3" / "remove clip 4,3"
    m_delete_clip = re.search(
        r"\b(delete|remove)\s+clip\s+(\d+)\s*(?:,|\s)\s*(\d+)\b",
        text,
        flags=re.IGNORECASE,
    )
    if m_delete_clip:
        ti = int(m_delete_clip.group(2))
        si = int(m_delete_clip.group(3))
        value = {"track_index": ti, "scene_index": si}
        raw_intent = {
            "intent": "transport",
            "operation": {"action": "clip_delete", "value": value},
            "meta": {"utterance": original_text, "pipeline": "regex_clip_delete"},
        }
        canonical = {"domain": "transport", "action": "clip_delete", "value": value}
        return {"ok": True, "intent": canonical, "raw_intent": raw_intent}

    # Duplicate clip:
    #   "duplicate clip 4 3" (implied target: 4,4)
    #   "duplicate clip 4,3 to 4,5"
    #   "duplicate clip 4 3 to 4 5 as Bongos"
    m_dup_clip = re.search(
        r"\b(duplicate|copy)\s+clip\s+(\d+)\s*(?:,|\s)\s*(\d+)"
        r"(?:\s+to\s+(\d+)\s*(?:,|\s)\s*(\d+))?\b",
        text,
        flags=re.IGNORECASE,
    )
    if m_dup_clip:
        ti = int(m_dup_clip.group(2))
        si = int(m_dup_clip.group(3))
        if m_dup_clip.group(4) and m_dup_clip.group(5):
            tti = int(m_dup_clip.group(4))
            tsi = int(m_dup_clip.group(5))
        else:
            tti = ti
            tsi = si + 1

        # Optional new name (preserve casing via original_text):
        #   "duplicate clip 4 2 to 4 5 as Bongos"
        #   "duplicate clip 4 2 to 4 5 Bongos"
        m_orig = re.search(
            r"\b(duplicate|copy)\s+clip\s+\d+\s*(?:,|\s)\s*\d+"
            r"(?:\s+to\s+\d+\s*(?:,|\s)\s*\d+)?"
            r"(?:\s+(?:as|to)\s+(.+)|\s+(.+))?$",
            original_text,
            flags=re.IGNORECASE,
        )
        raw_name = None
        if m_orig:
            # Prefer explicit 'as/to' name if present, else trailing words
            raw_name = m_orig.group(2) or m_orig.group(3)
        name = (raw_name or "").strip().strip('"').strip("'") or None

        value = {
            "track_index": ti,
            "scene_index": si,
            "target_track_index": tti,
            "target_scene_index": tsi,
        }
        if name:
            value["name"] = name
        raw_intent = {
            "intent": "transport",
            "operation": {"action": "clip_duplicate", "value": value},
            "meta": {"utterance": original_text, "pipeline": "regex_clip_duplicate"},
        }
        canonical = {"domain": "transport", "action": "clip_duplicate", "value": value}
        return {"ok": True, "intent": canonical, "raw_intent": raw_intent}

    # Fast path: naming commands (track / scene / clip)
    # Examples:
    #   rename track 3 to Guitars
    #   name scene 2 \"Chorus\"
    #   rename clip 4 2 to Hook
    m_rename_track = re.search(
        r"\b(rename|name)\s+track\s+(\d+)\s+(?:to\s+)?(.+)$", text, flags=re.IGNORECASE
    )
    if m_rename_track:
        ti = int(m_rename_track.group(2))
        # Re-extract name portion from original_text to preserve casing
        m_orig = re.search(
            r"\b(rename|name)\s+track\s+(\d+)\s+(?:to\s+)?(.+)$",
            original_text,
            flags=re.IGNORECASE,
        )
        raw_name = m_orig.group(3) if m_orig else m_rename_track.group(3)
        name = (raw_name or "").strip().strip('"').strip("'")
        value = {"track_index": ti, "name": name}
        raw_intent = {
            "intent": "transport",
            "operation": {
                "action": "rename_track",
                "value": value,
            },
            "meta": {
                "utterance": text,
                "pipeline": "regex_rename",
            },
        }
        canonical = {"domain": "transport", "action": "rename_track", "value": value}
        return {"ok": True, "intent": canonical, "raw_intent": raw_intent}

    m_rename_scene = re.search(
        r"\b(rename|name)\s+scene\s+(\d+)\s+(?:to\s+)?(.+)$", text, flags=re.IGNORECASE
    )
    if m_rename_scene:
        si = int(m_rename_scene.group(2))
        m_orig = re.search(
            r"\b(rename|name)\s+scene\s+(\d+)\s+(?:to\s+)?(.+)$",
            original_text,
            flags=re.IGNORECASE,
        )
        raw_name = m_orig.group(3) if m_orig else m_rename_scene.group(3)
        name = (raw_name or "").strip().strip('"').strip("'")
        value = {"scene_index": si, "name": name}
        raw_intent = {
            "intent": "transport",
            "operation": {
                "action": "rename_scene",
                "value": value,
            },
            "meta": {
                "utterance": text,
                "pipeline": "regex_rename",
            },
        }
        canonical = {"domain": "transport", "action": "rename_scene", "value": value}
        return {"ok": True, "intent": canonical, "raw_intent": raw_intent}

    # Clip rename supports both \"clip 4 1\" and \"clip 4,1\" forms
    m_rename_clip = re.search(
        r"\b(rename|name)\s+clip\s+(\d+)\s*(?:,|\s)\s*(\d+)\s+(?:to\s+)?(.+)$",
        text,
        flags=re.IGNORECASE,
    )
    if m_rename_clip:
        ti = int(m_rename_clip.group(2))
        si = int(m_rename_clip.group(3))
        m_orig = re.search(
            r"\b(rename|name)\s+clip\s+(\d+)\s*(?:,|\s)\s*(\d+)\s+(?:to\s+)?(.+)$",
            original_text,
            flags=re.IGNORECASE,
        )
        raw_name = m_orig.group(4) if m_orig else m_rename_clip.group(4)
        name = (raw_name or "").strip().strip('"').strip("'")
        value = {"track_index": ti, "scene_index": si, "name": name}
        raw_intent = {
            "intent": "transport",
            "operation": {
                "action": "rename_clip",
                "value": value,
            },
            "meta": {
                "utterance": text,
                "pipeline": "regex_rename",
            },
        }
        canonical = {"domain": "transport", "action": "rename_clip", "value": value}
        return {"ok": True, "intent": canonical, "raw_intent": raw_intent}

    # Fast path: track arm/disarm
    # Examples:
    #   arm track 3
    #   disarm track 3
    m_arm = re.search(r"\b(arm|disarm|unarm)\s+track\s+(\d+)\b", text, flags=re.IGNORECASE)
    if m_arm:
        verb = (m_arm.group(1) or "").lower()
        ti = int(m_arm.group(2))
        arm = verb == "arm"
        value = {"track_index": ti, "arm": arm}
        raw_intent = {
            "intent": "track_arm",
            "operation": {
                "action": "arm" if arm else "disarm",
                "value": arm,
            },
            "meta": {
                "utterance": original_text,
                "pipeline": "regex_arm",
            },
        }
        canonical = {
            "domain": "track",
            "action": "arm",
            "track_index": ti,
            "value": arm,
        }
        return {"ok": True, "intent": canonical, "raw_intent": raw_intent}

    # Fast path: track/scene create/delete/duplicate (project structure)
    # Track creation (optionally with name)
    m_create_audio = re.search(
        r"\b(create|add|new)\s+audio\s+track(?:\s+(?:at\s+)?(\d+))?(?:\s+(?:as\s+)?(.+))?$",
        text,
        flags=re.IGNORECASE,
    )
    if m_create_audio:
        idx = m_create_audio.group(2)
        index_val = int(idx) if idx else None
        # Re-extract from original_text to preserve casing for names
        m_orig = re.search(
            r"\b(create|add|new)\s+audio\s+track(?:\s+(?:at\s+)?(\d+))?(?:\s+(?:as\s+)?(.+))?$",
            original_text,
            flags=re.IGNORECASE,
        )
        raw_name = (m_orig.group(3) if m_orig else m_create_audio.group(3)) if m_create_audio.lastindex and m_create_audio.lastindex >= 3 else None
        name = (raw_name or "").strip().strip('"').strip("'") or None
        value = {"type": "audio", "index": index_val}
        if name:
            value["name"] = name
        raw_intent = {
            "intent": "project",
            "operation": {"action": "create_audio_track", "value": value},
            "meta": {"utterance": original_text, "pipeline": "regex_project"},
        }
        canonical = {"domain": "transport", "action": "create_audio_track", "value": value}
        return {"ok": True, "intent": canonical, "raw_intent": raw_intent}

    m_create_midi = re.search(
        r"\b(create|add|new)\s+midi\s+track(?:\s+(?:at\s+)?(\d+))?(?:\s+(?:as\s+)?(.+))?$",
        text,
        flags=re.IGNORECASE,
    )
    if m_create_midi:
        idx = m_create_midi.group(2)
        index_val = int(idx) if idx else None
        m_orig = re.search(
            r"\b(create|add|new)\s+midi\s+track(?:\s+(?:at\s+)?(\d+))?(?:\s+(?:as\s+)?(.+))?$",
            original_text,
            flags=re.IGNORECASE,
        )
        raw_name = (m_orig.group(3) if m_orig else m_create_midi.group(3)) if m_create_midi.lastindex and m_create_midi.lastindex >= 3 else None
        name = (raw_name or "").strip().strip('"').strip("'") or None
        value = {"type": "midi", "index": index_val}
        if name:
            value["name"] = name
        raw_intent = {
            "intent": "project",
            "operation": {"action": "create_midi_track", "value": value},
            "meta": {"utterance": original_text, "pipeline": "regex_project"},
        }
        canonical = {"domain": "transport", "action": "create_midi_track", "value": value}
        return {"ok": True, "intent": canonical, "raw_intent": raw_intent}

    # Track delete / duplicate
    m_delete_track = re.search(
        r"\b(delete|remove)\s+track\s+(\d+)\b", text, flags=re.IGNORECASE
    )
    if m_delete_track:
        ti = int(m_delete_track.group(2))
        raw_intent = {
            "intent": "project",
            "operation": {"action": "delete_track", "value": ti},
            "meta": {"utterance": original_text, "pipeline": "regex_project"},
        }
        canonical = {"domain": "transport", "action": "delete_track", "value": ti}
        return {"ok": True, "intent": canonical, "raw_intent": raw_intent}

    m_dup_track = re.search(
        r"\b(duplicate|copy)\s+track\s+(\d+)(?:\s+(?:as\s+)?(.+))?$", text, flags=re.IGNORECASE
    )
    if m_dup_track:
        ti = int(m_dup_track.group(2))
        # Extract name from original_text to preserve casing
        m_orig = re.search(
            r"\b(duplicate|copy)\s+track\s+(\d+)(?:\s+(?:as\s+)?(.+))?$",
            original_text,
            flags=re.IGNORECASE,
        )
        raw_name = (m_orig.group(3) if m_orig else m_dup_track.group(3)) if m_dup_track.lastindex and m_dup_track.lastindex >= 3 else None
        name = (raw_name or "").strip().strip('"').strip("'") or None
        value = {"index": ti}
        if name:
            value["name"] = name
        raw_intent = {
            "intent": "project",
            "operation": {"action": "duplicate_track", "value": value},
            "meta": {"utterance": original_text, "pipeline": "regex_project"},
        }
        canonical = {"domain": "transport", "action": "duplicate_track", "value": value}
        return {"ok": True, "intent": canonical, "raw_intent": raw_intent}

    # Scene creation (blank or named)
    m_create_scene = re.search(
        r"\b(create|add|new)\s+(?:empty\s+)?scene(?:\s+(?:at\s+)?(\d+))?(?:\s+(?:as\s+)?(.+))?$",
        text,
        flags=re.IGNORECASE,
    )
    if m_create_scene:
        idx = m_create_scene.group(2)
        index_val = int(idx) if idx else None
        m_orig = re.search(
            r"\b(create|add|new)\s+(?:empty\s+)?scene(?:\s+(?:at\s+)?(\d+))?(?:\s+(?:as\s+)?(.+))?$",
            original_text,
            flags=re.IGNORECASE,
        )
        raw_name = (m_orig.group(3) if m_orig else m_create_scene.group(3)) if m_create_scene.lastindex and m_create_scene.lastindex >= 3 else None
        name = (raw_name or "").strip().strip('"').strip("'") or None
        value = {"scene_index": index_val} if index_val is not None else {}
        if name:
            value["name"] = name
        raw_intent = {
            "intent": "project",
            "operation": {"action": "create_scene", "value": value},
            "meta": {"utterance": original_text, "pipeline": "regex_project"},
        }
        canonical = {"domain": "transport", "action": "create_scene", "value": value}
        return {"ok": True, "intent": canonical, "raw_intent": raw_intent}

    # Scene delete / duplicate
    m_delete_scene = re.search(
        r"\b(delete|remove)\s+scene\s+(\d+)\b", text, flags=re.IGNORECASE
    )
    if m_delete_scene:
        si = int(m_delete_scene.group(2))
        value = {"scene_index": si}
        raw_intent = {
            "intent": "project",
            "operation": {"action": "delete_scene", "value": value},
            "meta": {"utterance": original_text, "pipeline": "regex_project"},
        }
        canonical = {"domain": "transport", "action": "delete_scene", "value": value}
        return {"ok": True, "intent": canonical, "raw_intent": raw_intent}

    # Scene duplicate (optionally with new name: "duplicate scene 3 as Outro 3"
    # or "duplicate scene 3 Outro 3")
    m_dup_scene = re.search(
        r"\b(duplicate|copy)\s+scene\s+(\d+)"
        r"(?:\s+(?:as|to)\s+(.+)|\s+(.+))?\b",
        text,
        flags=re.IGNORECASE,
    )
    if m_dup_scene:
        si = int(m_dup_scene.group(2))
        m_orig = re.search(
            r"\b(duplicate|copy)\s+scene\s+(\d+)"
            r"(?:\s+(?:as|to)\s+(.+)|\s+(.+))?\b",
            original_text,
            flags=re.IGNORECASE,
        )
        raw_name = None
        if m_orig:
            # Prefer explicit 'as/to' name if present, else trailing words
            raw_name = m_orig.group(3) or m_orig.group(4)
        else:
            raw_name = m_dup_scene.group(3) or m_dup_scene.group(4) if m_dup_scene.lastindex and m_dup_scene.lastindex >= 3 else None
        name = (raw_name or "").strip().strip('"').strip("'") or None
        value: Dict[str, Any] = {"scene_index": si}
        if name:
            value["name"] = name
        raw_intent = {
            "intent": "project",
            "operation": {"action": "duplicate_scene", "value": value},
            "meta": {"utterance": original_text, "pipeline": "regex_project"},
        }
        canonical = {"domain": "transport", "action": "duplicate_scene", "value": value}
        return {"ok": True, "intent": canonical, "raw_intent": raw_intent}

    # Try layered parser first when enabled (if no regex fast-path intent)
    if raw_intent is None and USE_LAYERED:
        try:
            from server.services.nlp.intent_builder import parse_command_layered

            parse_index = _get_parse_index()
            # Use original_text to preserve case in user-provided names
            # Layered parser handles its own typo correction and lowercasing internally
            layered_intent = parse_command_layered(original_text, parse_index)
            if layered_intent:
                raw_intent = layered_intent
                try:
                    intent_name = str(raw_intent.get("intent"))
                except Exception:
                    intent_name = "unknown"
                print(f"[LAYERED] Parsed intent via layered pipeline: {intent_name}")
            else:
                print("[LAYERED] No intent parsed by layered pipeline, falling back to llm_daw")
        except Exception as e:
            print(f"[LAYERED] Error in layered parser: {e}; falling back to llm_daw")

    # Fallback (or default) path: use old llm_daw parser
    if raw_intent is None:
        # Import llm_daw dynamically from nlp-service (hyphen in folder name)
        nlp_dir = pathlib.Path(__file__).resolve().parent.parent.parent / "nlp-service"
        if nlp_dir.exists() and str(nlp_dir) not in sys.path:
            sys.path.insert(0, str(nlp_dir))
        try:
            from llm_daw import interpret_daw_command  # type: ignore
        except Exception as e:
            raise HTTPException(500, f"NLP module not available: {e}")

        raw_intent = interpret_daw_command(text, model_preference=body.model, strict=body.strict)

    # Post-process: Fix intent type for relative operations
    # Both regex and LLM parsers may return "set_parameter" for relative ops
    # But the correct intent should be "relative_change" when operation.type is "relative"
    if (
        raw_intent
        and raw_intent.get("intent") == "set_parameter"
        and raw_intent.get("operation", {}).get("type") == "relative"
    ):
        raw_intent["intent"] = "relative_change"

    # Post-process: Pan absolute commands with explicit left/right.
    # Normalize "25% left/right" into signed values (-25 / +25) for mixer pan.
    try:
        if raw_intent and raw_intent.get("intent") == "set_parameter":
            op = raw_intent.get("operation") or {}
            targets = raw_intent.get("targets") or []
            if (
                op.get("type") == "absolute"
                and isinstance(op.get("value"), (int, float))
                and any(
                    (t.get("plugin") is None and str(t.get("parameter", "")).lower() == "pan")
                    for t in targets
                )
            ):
                tl = text.lower()
                val = float(op.get("value") or 0.0)
                if "left" in tl and val > 0:
                    op["value"] = -val
                    op["unit"] = None  # treat as display percent
                elif "right" in tl and val < 0:
                    op["value"] = -val
                    op["unit"] = None
                raw_intent["operation"] = op
    except Exception:
        pass

    # Normalize parameter names in raw_intent for consistency (lowercase)
    # This ensures tests and UI get consistent parameter names regardless of parser.
    # Do this BEFORE calling intent_mapper so it gets normalized input.
    # Applies to mixer params for set/relative/get; device params keep original casing.
    if raw_intent and raw_intent.get("intent") in (
        "set_parameter",
        "relative_change",
        "get_parameter",
    ):
        targets = raw_intent.get("targets", [])
        normalized_targets = []
        for target in targets:
            param_raw = target.get("parameter") or ""
            plugin = target.get("plugin")
            # Normalize parameter name (lowercase for mixer params, preserve for device params)
            normalized_param = str(param_raw).lower() if not plugin else param_raw
            normalized_target = {**target, "parameter": normalized_param}
            normalized_targets.append(normalized_target)
        raw_intent["targets"] = normalized_targets

    canonical, errors = map_llm_to_canonical(raw_intent)

    # For GET queries, intent_mapper returns normalized_intent in canonical (not None)
    # Use the normalized version for raw_intent to ensure parameter names are lowercase
    if canonical and any(str(e).startswith("non_control_intent:get_parameter") for e in (errors or [])):
        return {"ok": False, "errors": errors, "raw_intent": canonical}

    if canonical is None:
        # Navigation intents (open_capabilities, list_capabilities) are valid UI intents
        # They don't go to the remote script, but should return ok=True for the UI to handle
        if raw_intent and raw_intent.get("intent") in ("open_capabilities", "list_capabilities"):
            return {"ok": True, "intent": raw_intent, "raw_intent": raw_intent}

        # Help/question intents should route to /help endpoint with ok=True
        if raw_intent and raw_intent.get("intent") == "question_response":
            return {"ok": True, "intent": raw_intent, "raw_intent": raw_intent}

        # Preserve original LLM output for non-control intents
        if any(str(e).startswith("non_control_intent") for e in (errors or [])):
            return {"ok": False, "errors": errors, "raw_intent": raw_intent}

        # Attempt to provide clarifying choices, keep raw_intent intact
        try:
            ov = request_op("get_overview", timeout=1.0) or {}
            data = (ov.get("data") or ov) if isinstance(ov, dict) else ov
            tracks = data.get("tracks") or []
            rs = request_op("get_return_tracks", timeout=1.0) or {}
            rdata = (rs.get("data") or rs) if isinstance(rs, dict) else rs
            rets = rdata.get("returns") or []
            question = "Which track or return do you mean?"
            choices = {
                "tracks": [{"index": int(t.get("index", 0)), "name": t.get("name")} for t in tracks],
                "returns": [
                    {
                        "index": int(r.get("index", 0)),
                        "name": r.get("name"),
                        "letter": chr(ord("A") + int(r.get("index", 0))),
                    }
                    for r in rets
                ],
            }
            clar = {"intent": "clarification_needed", "question": question, "choices": choices, "context": body.context}
            return {"ok": False, "errors": errors, "raw_intent": raw_intent, "clarification": clar}
        except Exception:
            return {"ok": False, "errors": errors, "raw_intent": raw_intent}

    return {"ok": True, "intent": canonical, "raw_intent": raw_intent}
