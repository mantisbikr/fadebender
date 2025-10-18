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
        },
        "server": {
            "send_aliases": {
                "reverb": 0,
                "verb": 0,
                "hall": 0,
                "room": 0,
                "delay": 1,
                "echo": 1,
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
