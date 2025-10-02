from __future__ import annotations

import json
import os
from typing import Any, Dict

_CFG: Dict[str, Any] | None = None
_PATH: str | None = None


def _defaults() -> Dict[str, Any]:
    return {
        "defaults": {
            "sleep_ms_quick": 10,
            "r2_accept_quick": 0.99,
            "r2_excellent": 0.999,
            "max_extra_points_quick": 2,
            "refine_max_nudges": 2,
            "relative_threshold": 0.02,
        },
        "sampling": {
            "continuous": {
                "linear": [0.0, 0.5, 1.0],
                "exp": [0.05, 0.5, 0.95],
                "fallback_extra": [0.25, 0.75],
            },
            "binary": ["min", "max"],
            "quantized": {
                "coarse_points": 7,
                "stop_on_repeat": True,
            },
        },
        "heuristics": {
            "linear_names": ["amount", "level", "mix", "stereo", "scale", "diffusion", "shape", "gain"],
            "exp_names": ["delay", "decay", "freq", "rate", "size"],
            "linear_units": ["%", "db"],
            "exp_units": ["ms", "s", "hz", "khz"],
            "fallback_try_both": True,
        },
        "grouping": {
            "reverb": {
                "masters": [
                    "Chorus On",
                    "ER Spin On",
                    "LowShelf On",
                    "HiFilter On",
                    "HiShelf On|High Shelf On|High Shelf Enabled",
                ],
                "dependents": {
                    "Chorus Rate": "Chorus On",
                    "Chorus Amount": "Chorus On",
                    "ER Spin Rate": "ER Spin On",
                    "ER Spin Amount": "ER Spin On",
                    "LowShelf Freq": "LowShelf On",
                    "LowShelf Gain": "LowShelf On",
                    "HiFilter Freq": "HiFilter On",
                    "HiFilter Type": "HiFilter On",
                    "HiShelf Gain": "HiShelf On",
                },
                "skip_auto_enable": ["Freeze On"],
            },
            "default": {
                "masters": [],
                "dependents": {},
                "skip_auto_enable": ["Freeze On"],
            },
        },
        "refine": {
            "enabled": True,
            "trigger": "idle",
            "idle_ms": 30000,
            "budget_ms": 500,
            "target_r2": 0.999,
            "max_params_per_pass": 4,
        },
    }


def _load_path() -> str:
    global _PATH
    if _PATH:
        return _PATH
    here = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(here, os.pardir, os.pardir))
    _PATH = os.path.join(repo_root, "configs", "param_learn.json")
    return _PATH


def get_param_learn_config() -> Dict[str, Any]:
    global _CFG
    if _CFG is not None:
        return _CFG
    cfg = _defaults()
    path = _load_path()
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                user = json.load(f)
                # shallow merge top-level
                for k, v in user.items():
                    if isinstance(v, dict) and isinstance(cfg.get(k), dict):
                        cfg[k].update(v)
                    else:
                        cfg[k] = v
    except Exception:
        pass
    _CFG = cfg
    return cfg


def set_param_learn_config(new_cfg: Dict[str, Any]) -> Dict[str, Any]:
    cfg = get_param_learn_config()
    if isinstance(new_cfg, dict):
        for k, v in new_cfg.items():
            if isinstance(v, dict) and isinstance(cfg.get(k), dict):
                cfg[k].update(v)
            else:
                cfg[k] = v
    return cfg


def reload_param_learn_config() -> Dict[str, Any]:
    global _CFG
    _CFG = None
    return get_param_learn_config()


def save_param_learn_config() -> bool:
    try:
        cfg = get_param_learn_config()
        path = _load_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
        return True
    except Exception:
        return False

