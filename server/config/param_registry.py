from __future__ import annotations

import json
import os
from typing import Any, Dict

_REGISTRY: Dict[str, Any] | None = None
_PATH: str | None = None


def _load_registry() -> Dict[str, Any]:
    global _REGISTRY, _PATH
    if _REGISTRY is not None:
        return _REGISTRY
    here = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(here, os.pardir, os.pardir))
    path = os.path.join(repo_root, "configs", "param_registry.json")
    _PATH = path
    # Default registry if file is missing
    reg: Dict[str, Any] = {
        "track": {
            "volume": {"kind": "mapped_db", "min_db": -60, "max_db": 6, "mapping_file": "docs/volume_map.csv", "fallback": "heuristic_around_0db"},
            "pan": {"kind": "linear_bipolar", "min": -1.0, "max": 1.0},
        },
        "sends": {
            "volume": {"kind": "mapped_db", "min_db": -60, "max_db": 6, "offset_db": 6, "mapping_file": "docs/volume_map.csv", "fallback": "heuristic_around_0db"},
        },
    }
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                user = json.load(f)
                # shallow merge top level groups
                for k, v in (user or {}).items():
                    if isinstance(v, dict) and isinstance(reg.get(k), dict):
                        reg[k].update(v)
                    else:
                        reg[k] = v
    except Exception:
        # keep defaults on failure
        pass
    _REGISTRY = reg
    return reg


def get_param_registry() -> Dict[str, Any]:
    return _load_registry()


def reload_param_registry() -> Dict[str, Any]:
    global _REGISTRY
    _REGISTRY = None
    return _load_registry()

