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
            "sse_throttle_ms": 150,
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
    cfg.setdefault("ui", {}).update({k: v for k, v in ui.items() if isinstance(v, (int, float))})
    return get_ui_settings()


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
