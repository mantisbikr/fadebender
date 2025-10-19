from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Optional


def detect_device_type(params: List[Dict[str, Any]], device_name: Optional[str] = None) -> str:
    name_lc = (device_name or "").strip().lower()
    if name_lc:
        if any(k in name_lc for k in ("delay", "echo")):
            return "delay"
        if any(k in name_lc for k in ("reverb", "hall", "plate", "room")):
            return "reverb"
        if any(k in name_lc for k in ("compressor", "glue")):
            return "compressor"
        if "eq" in name_lc and "eight" in name_lc:
            return "eq8"
        if "auto filter" in name_lc or ("filter" in name_lc and "auto" in name_lc):
            return "autofilter"
        if "saturator" in name_lc:
            return "saturator"
        if "amp" in name_lc:
            return "amp"

    param_set = set(str(p.get("name", "")) for p in params)

    if {"ER Spin On", "Freeze On", "Chorus On", "Diffusion"}.issubset(param_set):
        return "reverb"
    if {"L Time", "R Time", "Ping Pong", "Feedback"}.issubset(param_set):
        return "delay"
    if {"Threshold", "Ratio", "Attack", "Release", "Knee"}.issubset(param_set):
        return "compressor"
    if {"1 Frequency A", "2 Frequency A", "3 Frequency A"}.issubset(param_set):
        return "eq8"
    if {"Filter Type", "Frequency", "Resonance", "LFO Amount"}.issubset(param_set):
        return "autofilter"
    if {"Drive", "Dry/Wet", "Color", "Type"}.issubset(param_set):
        return "saturator"
    if {"Amp Type", "Bass", "Middle", "Treble", "Gain"}.issubset(param_set):
        return "amp"

    if {"Time", "Feedback"}.intersection(param_set) and any("Time" in n for n in param_set):
        return "delay"
    if {"Decay", "Size"}.intersection(param_set):
        return "reverb"
    return "unknown"


def make_device_signature(name: str, params: List[Dict[str, Any]]) -> str:
    param_names = ",".join([str(p.get("name", "")) for p in params])
    base = f"{len(params)}|{param_names}"
    return hashlib.sha1(base.encode("utf-8")).hexdigest()

