from __future__ import annotations

import math
import re
from typing import Dict, List, Optional, Tuple

from server.config.param_learn_config import get_param_learn_config


def parse_unit_from_display(disp: str) -> Optional[str]:
    if not disp:
        return None
    text = str(disp).strip()
    if "dB" in text or re.search(r"\bdB\b", text):
        return "dB"
    if "%" in text:
        return "%"
    if "kHz" in text:
        return "kHz"
    if re.search(r"\bHz\b", text):
        return "Hz"
    if re.search(r"\bms\b", text):
        return "ms"
    if re.search(r"\bs\b", text):
        return "s"
    if "°" in text:
        return "deg"
    return None


def classify_control_type(samples: List[Dict], vmin: float, vmax: float) -> Tuple[str, List[str]]:
    if not samples:
        return ("continuous", [])
    labels = list({str(s.get("display", "")) for s in samples if s.get("display") is not None})
    numeric_like = sum(1 for lab in labels if re.search(r"-?\d+(?:\.\d+)?", lab))
    if len(labels) <= 2:
        return ("binary", labels)
    if 0 < len(labels) <= 12 and numeric_like < len(labels):
        return ("quantized", labels)
    return ("continuous", [])


def _group_role_for_reverb_param(param_name: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    name = (param_name or "").strip()
    lowered = name.lower()
    if lowered == "chorus on":
        return ("Chorus", "master", None)
    if lowered in ("chorus rate", "chorus amount"):
        return ("Chorus", "dependent", "Chorus On")
    if lowered == "er spin on":
        return ("Early", "master", None)
    if lowered in ("er spin rate", "er spin amount"):
        return ("Early", "dependent", "ER Spin On")
    if lowered in ("lowshelf on", "low shelf on", "low shelf enabled"):
        return ("Tail", "master", None)
    if lowered.startswith("lowshelf ") or lowered.startswith("low shelf "):
        if lowered not in ("low shelf on", "lowshelf on"):
            return ("Tail", "dependent", "LowShelf On")
    if lowered in ("hishelf on", "high shelf on", "high shelf enabled"):
        return ("Tail", "master", None)
    if lowered.startswith("hishelf ") or lowered.startswith("high shelf "):
        if lowered not in ("hishelf on", "high shelf on"):
            return ("Tail", "dependent", "HiShelf On")
    if lowered == "hifilter on":
        return ("Tail", "master", None)
    if lowered.startswith("hifilter "):
        if lowered != "hifilter on":
            return ("Tail", "dependent", "HiFilter On")
    if lowered == "freeze on":
        return ("Global", "master", None)
    if lowered in ("flat on", "cut on"):
        return ("Global", "dependent", "Freeze On")
    if lowered in ("dry/wet", "dry wet", "reflect level", "diffuse level"):
        return ("Output", None, None)
    if lowered in ("predelay", "decay", "size", "stereo image", "density", "size smoothing", "scale", "diffusion"):
        return ("Global", None, None)
    if lowered.startswith("in ") or lowered.startswith("input "):
        if lowered.endswith(" on"):
            return ("Input", "master", None)
        return ("Input", "dependent", None)
    return (None, None, None)


def group_role_for_device(device_name: Optional[str], param_name: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    device_lower = (device_name or "").strip().lower()
    pname = (param_name or "").strip()
    try:
        plc = get_param_learn_config()
        grouping = plc.get("grouping", {}) or {}
        match_key = None
        for key in grouping.keys():
            lowered = str(key).lower()
            if lowered == "default":
                continue
            if lowered in device_lower:
                match_key = key
                break
        if match_key is None:
            match_key = "default"
        rules = grouping.get(match_key) or {}
        dependents = rules.get("dependents") or {}
        for dep_name, master_name in dependents.items():
            if str(dep_name).lower() == pname.lower():
                group_name = match_key.title() if match_key != "default" else None
                return (group_name, "dependent", str(master_name))
        for master in (rules.get("masters") or []):
            alternatives = [s.strip() for s in str(master).split("|")]
            if any(pname.lower() == alt.lower() for alt in alternatives):
                group_name = match_key.title() if match_key != "default" else None
                return (group_name, "master", None)
    except Exception:
        pass
    if "reverb" in device_lower:
        return _group_role_for_reverb_param(param_name)
    return (None, None, None)


def build_groups_from_params(params: List[Dict], device_name: Optional[str]) -> List[Dict]:
    groups: Dict[str, Dict] = {}
    for param in params:
        name = str(param.get("name", ""))
        group_name, role, master_name = group_role_for_device(device_name, name)
        if not group_name:
            continue
        groups.setdefault(group_name, {"name": group_name, "master": None, "dependents": []})
        if role == "master":
            groups[group_name]["master"] = {"name": name, "index": int(param.get("index", 0))}
        elif role == "dependent":
            groups[group_name]["dependents"].append(
                {"name": name, "index": int(param.get("index", 0)), "master": master_name}
            )
    return list(groups.values())


def fit_models(samples: List[Dict]) -> Optional[Dict]:
    points = [
        (float(s["value"]), float(s["display_num"]))
        for s in samples
        if s.get("display_num") is not None and math.isfinite(float(s.get("value", 0.0))) and math.isfinite(float(s["display_num"]))
    ]
    if len(points) < 3:
        return None
    points.sort(key=lambda p: p[0])
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]

    def linear_fit(x_vals, y_vals):
        n = len(x_vals)
        sx = sum(x_vals)
        sy = sum(y_vals)
        sxx = sum(v * v for v in x_vals)
        sxy = sum(a * b for a, b in zip(x_vals, y_vals))
        denominator = n * sxx - sx * sx
        if denominator == 0:
            return None
        slope = (n * sxy - sx * sy) / denominator
        intercept = (sy - slope * sx) / n
        predictions = [slope * v + intercept for v in x_vals]
        ss_res = sum((yv - pv) ** 2 for yv, pv in zip(y_vals, predictions))
        mean_y = sy / n
        ss_tot = sum((yv - mean_y) ** 2 for yv in y_vals) or 1.0
        r_squared = 1.0 - ss_res / ss_tot
        return {"type": "linear", "a": slope, "b": intercept, "r2": r_squared}

    def log_fit(x_vals, y_vals):
        try:
            transformed = [math.log(max(1e-9, v)) for v in x_vals]
        except ValueError:
            return None
        fit = linear_fit(transformed, y_vals)
        if not fit:
            return None
        return {**fit, "type": "log", "x_transform": "ln(x)"}

    def exp_fit(x_vals, y_vals):
        if any(val <= 0 for val in y_vals):
            return None
        transformed = [math.log(val) for val in y_vals]
        fit = linear_fit(x_vals, transformed)
        if not fit:
            return None
        a = fit["a"]
        b = fit["b"]
        r2 = fit["r2"]
        return {"type": "exp", "a": a, "b": b, "r2": r2}

    candidates = []
    linear = linear_fit(xs, ys)
    if linear:
        candidates.append(linear)
    log_candidate = log_fit(xs, ys)
    if log_candidate:
        candidates.append(log_candidate)
    exp_candidate = exp_fit(xs, ys)
    if exp_candidate:
        candidates.append(exp_candidate)
    best = max(candidates, key=lambda d: d["r2"]) if candidates else None
    if best and best.get("r2", 0.0) >= 0.9:
        return best
    return {
        "type": "piecewise",
        "r2": best.get("r2") if best else 0.0,
        "points": [{"x": x, "y": y} for x, y in points],
    }
