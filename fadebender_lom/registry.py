from __future__ import annotations

import json
import os
from typing import Any, Dict

_REGISTRY: Dict[str, Any] | None = None


def _default_registry() -> Dict[str, Any]:
    return {
        "track": {
            "volume": {"kind": "mapped_db", "min_db": -60, "max_db": 6, "mapping_file": "docs/volume_map.csv", "fallback": "heuristic_around_0db"},
            "pan": {"kind": "linear_bipolar", "min": -1.0, "max": 1.0},
        },
        "sends": {
            "volume": {"kind": "mapped_db", "min_db": -60, "max_db": 6, "offset_db": 6, "mapping_file": "docs/volume_map.csv", "fallback": "heuristic_around_0db"},
        },
    }


def _load_registry() -> Dict[str, Any]:
    global _REGISTRY
    if _REGISTRY is not None:
        return _REGISTRY
    reg = _default_registry()
    # Allow override via environment
    override_path = os.getenv("FB_PARAM_REGISTRY_PATH")
    if not override_path:
        # Fallback to repo configs
        repo_root = os.getenv("FB_REPO_ROOT") or os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
        override_path = os.path.join(repo_root, "configs", "param_registry.json")
    try:
        if override_path and os.path.exists(override_path):
            with open(override_path, "r", encoding="utf-8") as f:
                user = json.load(f)
                for k, v in (user or {}).items():
                    if isinstance(v, dict) and isinstance(reg.get(k), dict):
                        reg[k].update(v)
                    else:
                        reg[k] = v
    except Exception:
        pass
    _REGISTRY = reg
    return reg


def get_param_registry() -> Dict[str, Any]:
    return _load_registry()


def reload_param_registry() -> Dict[str, Any]:
    global _REGISTRY
    _REGISTRY = None
    return _load_registry()

