from __future__ import annotations

import json
import os
from typing import Any, Dict


_CONFIG: Dict[str, Any] | None = None
_PATH: str | None = None


def _load() -> Dict[str, Any]:
    global _CONFIG
    if _CONFIG is not None:
        return _CONFIG
    # Look for configs/app_config.json at repo root
    here = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(here, os.pardir, os.pardir))
    global _PATH
    path = os.path.join(repo_root, "configs", "app_config.json")
    _PATH = path
    cfg: Dict[str, Any] = {
        "ui": {
            "refresh_ms": 5000,
            "sends_open_refresh_ms": 800,
            "master_refresh_ms": 800,
            "track_refresh_ms": 1200,
            "returns_refresh_ms": 3000,
            "sse_throttle_ms": 150,
            "sidebar_width_px": 360,
            "default_sidebar_tab": "tracks",
        },
        "features": {
            "use_intents_for_chat": True,  # Use /intent/execute for chat commands (default enabled)
            "simple_device_resolver": True,  # Simplified device resolver for device intents (name/type/qualifier)
        },
        "server": {
            "send_aliases": {
                "reverb": 0,
                "verb": 0,
                "hall": 0,
                "room": 0,
                "delay": 1,
                "echo": 1,
            },
            # Canonical device types -> list of name keywords/synonyms to match in resolver
            "device_type_aliases": {
                "reverb": ["reverb", "hall", "room", "plate", "space", "ambience", "ambient"],
                "delay": ["delay", "echo", "slapback", "pingpong", "ping-pong"],
                "compressor": ["compress", "compressor"],
                "eq": ["eq", "equalizer"],
                "amp": ["amp", "screamer", "overdrive", "distortion", "fuzz", "saturator"],
                "chorus": ["chorus"],
                "flanger": ["flanger"],
                "phaser": ["phaser"],
            },
            "device_qualifier_aliases": {
                "reverb": {
                    "ambience": ["ambience", "ambient"],
                    "hall": ["hall"],
                    "room": ["room"],
                    "plate": ["plate"],
                    "spring": ["spring"],
                    "chamber": ["chamber"],
                    "cathedral": ["cathedral"],
                    "big room": ["big room", "large room"],
                    "small room": ["small room", "tiny room"],
                },
                "delay": {
                    "ping pong": ["ping pong", "ping-pong"],
                    "slapback": ["slapback"],
                    "tape": ["tape"],
                    "grain": ["grain", "granular"],
                    "multi": ["multi", "multitap"],
                },
                "amp": {
                    "screamer": ["screamer"],
                    "clean": ["clean"],
                    "crunch": ["crunch"],
                    "lead": ["lead"],
                    "bass": ["bass"],
                }
            },
            # Aliases for parameter names (mixer and device)
            "param_aliases": {
                # Mixer parameter aliases map to canonical names
                "mixer": {
                    "vol": "volume",
                    "level": "volume",
                    "gain": "volume",
                    "loudness": "volume",
                    "pan": "pan",
                    "balance": "pan",
                    "mute": "mute",
                    "unmute": "mute",
                    "solo": "solo",
                    "unsolo": "solo",
                },
                # Device parameter aliases map to canonical param labels
                "device": {
                    "mix": "dry/wet",
                    "wet": "dry/wet",
                    "dry": "dry/wet",
                    "dry wet": "dry/wet",
                    "dry / wet": "dry/wet",
                    "lo cut": "low cut",
                    "locut": "low cut",
                    "lowcut": "low cut",
                    "hi cut": "high cut",
                    "hicut": "high cut",
                    "highcut": "high cut",
                    "lo shelf": "low shelf",
                    "loshelf": "low shelf",
                    "hi shelf": "hi shelf",
                    "hishelf": "hi shelf",
                    "low pass": "low cut",
                    "low-pass": "low cut",
                    "lpf": "low cut",
                    "lp": "low cut",
                    "high pass": "high cut",
                    "high-pass": "high cut",
                    "hpf": "high cut",
                    "hp": "high cut",
                    "bandwidth": "q",
                    "bw": "q",
                    "q factor": "q",
                    "q-factor": "q",
                    "res": "q",
                    "resonance": "q",
                    "speed": "rate",
                    "intensity": "depth",
                    "amt": "amount",
                    "fbk": "feedback",
                    "feed back": "feedback",
                    "feedback amount": "feedback",
                    "width": "stereo image",
                    "stereo width": "stereo image",
                    "image": "stereo image",
                    "decay time": "decay",
                    "pre delay": "predelay",
                    "pre-delay": "predelay",
                }
            },
        },
        "nlp": {
            # Configurable typo corrections for fallback parser
            "typo_corrections": {
                "retrun": "return",
                "retun": "return",
                "revreb": "reverb",
                "reverbb": "reverb",
                "revebr": "reverb",
                "reverv": "reverb",
                "strereo": "stereo",
                "streo": "stereo",
                "stere": "stereo",
                "tack": "track",
                "trck": "track",
                "trac": "track",
                "sennd": "send",
                "snd": "send",
            }
        },
        "debug": {
            "firestore": True,     # Firestore/mapping store debug prints
            "sse": False,            # Log SSE emits (event name + minimal payload)
            "auto_capture": True,   # Log auto-capture preset flow
        },
    }
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                user = json.load(f)
                # Shallow merge
                for k, v in user.items():
                    if isinstance(v, dict) and isinstance(cfg.get(k), dict):
                        cfg[k].update(v)
                    else:
                        cfg[k] = v
    except Exception:
        pass
    _CONFIG = cfg
    return cfg


def get_app_config() -> Dict[str, Any]:
    return _load()


def get_send_aliases() -> Dict[str, int]:
    cfg = _load()
    return dict(cfg.get("server", {}).get("send_aliases", {}))


def get_device_type_aliases() -> Dict[str, Any]:
    cfg = _load()
    return dict(cfg.get("server", {}).get("device_type_aliases", {}))


def get_device_qualifier_aliases() -> Dict[str, Any]:
    cfg = _load()
    return dict(cfg.get("server", {}).get("device_qualifier_aliases", {}))


def get_mixer_param_aliases() -> Dict[str, str]:
    cfg = _load()
    return dict(cfg.get("server", {}).get("param_aliases", {}).get("mixer", {}))


def get_device_param_aliases() -> Dict[str, str]:
    cfg = _load()
    return dict(cfg.get("server", {}).get("param_aliases", {}).get("device", {}))


def get_typo_corrections() -> Dict[str, str]:
    cfg = _load()
    return dict(cfg.get("nlp", {}).get("typo_corrections", {}))


def get_ui_settings() -> Dict[str, Any]:
    return dict(_load().get("ui", {}))


def set_ui_settings(ui: Dict[str, Any]) -> Dict[str, Any]:
    cfg = _load()
    if not isinstance(ui, dict):
        return get_ui_settings()
    cur = cfg.setdefault("ui", {})
    for k, v in ui.items():
        if k in ("refresh_ms", "sends_open_refresh_ms", "master_refresh_ms", "track_refresh_ms", "returns_refresh_ms", "sse_throttle_ms", "sidebar_width_px"):
            try:
                cur[k] = int(v)
            except Exception:
                continue
        elif k in ("default_sidebar_tab",):
            try:
                cur[k] = str(v)
            except Exception:
                continue
    return get_ui_settings()


def get_debug_settings() -> Dict[str, Any]:
    return dict(_load().get("debug", {}))


def get_feature_flags() -> Dict[str, Any]:
    return dict(_load().get("features", {}))


def set_debug_settings(debug: Dict[str, Any]) -> Dict[str, Any]:
    cfg = _load()
    if not isinstance(debug, dict):
        return get_debug_settings()
    cur = cfg.setdefault("debug", {})
    for k, v in debug.items():
        cur[str(k).lower()] = bool(v)
    return get_debug_settings()


def set_feature_flags(features: Dict[str, Any]) -> Dict[str, Any]:
    cfg = _load()
    if not isinstance(features, dict):
        return get_feature_flags()
    cur = cfg.setdefault("features", {})
    for k, v in features.items():
        cur[str(k)] = bool(v) if isinstance(v, (bool, int)) else v
    return get_feature_flags()


def set_send_aliases(aliases: Dict[str, int]) -> Dict[str, int]:
    cfg = _load()
    if not isinstance(aliases, dict):
        return get_send_aliases()
    srv = cfg.setdefault("server", {})
    cur = srv.setdefault("send_aliases", {})
    for k, v in aliases.items():
        try:
            cur[str(k).lower()] = int(v)
        except Exception:
            continue
    return get_send_aliases()


def reload_config() -> Dict[str, Any]:
    global _CONFIG
    _CONFIG = None
    return _load()


def save_config() -> bool:
    try:
        cfg = _load()
        path = _PATH
        if not path:
            return False
        # Write pretty JSON
        with open(path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, sort_keys=True)
        return True
    except Exception:
        return False


def get_snapshot_config() -> Dict[str, Any]:
    """Get snapshot refresh configuration with env var overrides."""
    return {
        "device_ttl_seconds": int(os.getenv("DEVICE_SNAPSHOT_TTL_SECONDS", "30")),
        "device_chunk_size": int(os.getenv("DEVICE_REFRESH_CHUNK_SIZE", "3")),
        "device_chunk_delay_ms": int(os.getenv("DEVICE_REFRESH_CHUNK_DELAY_MS", "40")),
    }
