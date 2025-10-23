from __future__ import annotations

import math
import re as _re
from typing import Any, Dict, Optional, Tuple

from server.core.deps import get_store


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _parse_target_display(s: str) -> Optional[float]:
    try:
        m = _re.search(r"-?\d+(?:\.\d+)?", str(s))
        if not m:
            return None
        return float(m.group(0))
    except Exception:
        return None


def _normalize_unit(u: Optional[str]) -> Optional[str]:
    if not u:
        return None
    s = str(u).strip().lower()
    if s in ("n/a", "na", "none", "unitless", "no unit", "-", ""):
        return None
    if s in ("sec", "second", "seconds"):
        return "s"
    if s in ("millisecond", "milliseconds"):
        return "ms"
    if s in ("kilohertz", "kiloherz", "khz"):
        return "khz"
    if s in ("hertz", "herz", "hz"):
        return "hz"
    if s in ("percent", "percentage"):
        return "%"
    if s in ("db", "decibel", "decibels"):
        return "db"
    if s in ("degree", "degrees", "deg", "°"):
        return "degrees"
    return s


def _get_mixer_param_meta(entity_type: str, param_name: str) -> Optional[Dict[str, Any]]:
    """Get parameter metadata from consolidated mixer channel mapping."""
    try:
        store = get_store()
        if not store.enabled:
            return None
        channel = store.get_mixer_channel_mapping(entity_type)
        if not channel:
            return None
        params_meta = channel.get("params_meta", [])
        return next((p for p in params_meta if p.get("name") == param_name), None)
    except Exception:
        return None


def _apply_mixer_fit_inverse(param_meta: Dict[str, Any], display_value: float) -> Optional[float]:
    fit = param_meta.get("fit", {})
    fit_type = fit.get("type")
    coeffs = fit.get("coeffs", {})
    if fit_type == "power":
        min_db = coeffs.get("min_db")
        max_db = coeffs.get("max_db")
        gamma = coeffs.get("gamma")
        range_db = coeffs.get("range_db", max_db - min_db if (max_db and min_db) else None)
        if min_db is None or range_db is None or gamma is None:
            return None
        normalized = ((display_value - min_db) / range_db) ** gamma
        return max(0.0, min(1.0, normalized))
    elif fit_type == "linear":
        scale = coeffs.get("scale", 50.0)
        normalized = display_value / scale
        return max(-1.0, min(1.0, normalized))
    return None


def _get_mixer_display_range(field: str) -> Tuple[float, float]:
    try:
        store = get_store()
        if not store.enabled:
            return (-50.0, 50.0) if field == "pan" else (0.0, 1.0)
        for entity_type in ["track", "return", "master"]:
            pm = _get_mixer_param_meta(entity_type, field)
            if pm:
                dmin = pm.get("min_display")
                dmax = pm.get("max_display")
                if dmin is not None and dmax is not None:
                    return (float(dmin), float(dmax))
        mapping = store.get_mixer_param_mapping(field)
        if not mapping:
            return (-50.0, 50.0) if field == "pan" else (0.0, 1.0)
        display_range = mapping.get("display_range", {})
        dmin = float(display_range.get("min", -50.0 if field == "pan" else 0.0))
        dmax = float(display_range.get("max", 50.0 if field == "pan" else 1.0))
        return (dmin, dmax)
    except Exception:
        return (-50.0, 50.0) if field == "pan" else (0.0, 1.0)


def _resolve_mixer_display_value(field: str, display: str) -> Optional[float]:
    try:
        store = get_store()
        if not store.enabled:
            return None
        for entity_type in ["track", "return", "master"]:
            pm = _get_mixer_param_meta(entity_type, field)
            if pm:
                num = _parse_target_display(display)
                if num is not None and pm.get("fit"):
                    result = _apply_mixer_fit_inverse(pm, num)
                    if result is not None:
                        return result
        mapping = store.get_mixer_param_mapping(field)
        if not mapping:
            return None
        presets = mapping.get("display_value_presets", {})
        if not isinstance(presets, dict):
            return None
        display_normalized = display.strip().lower()
        if display_normalized in presets:
            return float(presets[display_normalized])
        if field == "pan":
            num = _parse_target_display(display)
            if num is not None:
                display_min, display_max = _get_mixer_display_range("pan")
                display_scale = max(abs(display_min), abs(display_max))
                return _clamp(float(num) / display_scale, -1.0, 1.0)
        return None
    except Exception:
        return None


# Public aliases (without underscore) for service imports
parse_target_display = _parse_target_display
normalize_unit = _normalize_unit
get_mixer_param_meta = _get_mixer_param_meta
apply_mixer_fit_inverse = _apply_mixer_fit_inverse
get_mixer_display_range = _get_mixer_display_range
resolve_mixer_display_value = _resolve_mixer_display_value
clamp = _clamp

