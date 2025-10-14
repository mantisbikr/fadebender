from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import re as _re

from server.config.param_learn_config import get_param_learn_config  # optional usage guarded


def parse_unit_from_display(disp: str) -> Optional[str]:
    if not disp:
        return None
    s = str(disp).strip()
    if "dB" in s or _re.search(r"\bdB\b", s):
        return "dB"
    if "%" in s:
        return "%"
    if "kHz" in s:
        return "kHz"
    if _re.search(r"\bHz\b", s):
        return "Hz"
    if _re.search(r"\bms\b", s):
        return "ms"
    if _re.search(r"\bs\b", s):
        return "s"
    if "°" in s:
        return "deg"
    return None


def classify_control_type(samples: List[Dict[str, Any]], vmin: float, vmax: float) -> Tuple[str, List[str]]:
    if not samples:
        return ("continuous", [])
    labels = list({str(s.get("display", "")) for s in samples if s.get("display") is not None})
    numeric_like = 0
    for lab in labels:
        if _re.search(r"-?\d+(?:\.\d+)?", lab):
            numeric_like += 1
    if len(labels) <= 2:
        return ("binary", labels)
    if len(labels) > 0 and len(labels) <= 12 and numeric_like < len(labels):
        return ("quantized", labels)
    return ("continuous", [])


def _group_role_for_reverb_param(pname: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    n = (pname or "").strip()
    nlc = n.lower()
    if nlc == "chorus on":
        return ("Chorus", "master", None)
    if nlc in ("chorus rate", "chorus amount"):
        return ("Chorus", "dependent", "Chorus On")
    if nlc == "er spin on":
        return ("Early", "master", None)
    if nlc in ("er spin rate", "er spin amount"):
        return ("Early", "dependent", "ER Spin On")
    if nlc in ("lowshelf on", "low shelf on", "low shelf enabled"):
        return ("Tail", "master", None)
    if nlc.startswith("lowshelf ") or nlc.startswith("low shelf "):
        if nlc not in ("low shelf on", "lowshelf on"):
            return ("Tail", "dependent", "LowShelf On")
    if nlc in ("hishelf on", "high shelf on", "high shelf enabled"):
        return ("Tail", "master", None)
    if nlc.startswith("hishelf ") or nlc.startswith("high shelf "):
        if nlc not in ("hishelf on", "high shelf on"):
            return ("Tail", "dependent", "HiShelf On")
    if nlc == "hifilter on":
        return ("Tail", "master", None)
    if nlc.startswith("hifilter "):
        if nlc != "hifilter on":
            return ("Tail", "dependent", "HiFilter On")
    if nlc == "freeze on":
        return ("Global", "master", None)
    if nlc in ("flat on", "cut on"):
        return ("Global", "dependent", "Freeze On")
    if nlc in ("dry/wet", "dry wet", "reflect level", "diffuse level"):
        return ("Output", None, None)
    if nlc in ("predelay", "decay", "size", "stereo image", "density", "size smoothing", "scale", "diffusion"):
        return ("Global", None, None)
    if nlc.startswith("in ") or nlc.startswith("input "):
        if nlc.endswith(" on"):
            return ("Input", "master", None)
        return ("Input", "dependent", None)
    return (None, None, None)


def group_role_for_device(device_name: Optional[str], param_name: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    dn = (device_name or "").strip().lower()
    pn = (param_name or "").strip()
    try:
        PLC = get_param_learn_config()
        grp = PLC.get("grouping", {}) or {}
        match_key = None
        for key in grp.keys():
            kl = str(key).lower()
            if kl == "default":
                continue
            if kl in dn:
                match_key = key
                break
        if match_key is None:
            match_key = "default"
        rules = grp.get(match_key) or {}
        deps = rules.get("dependents") or {}
        for dep_name, master_name in deps.items():
            if str(dep_name).lower() == pn.lower():
                return (
                    match_key.title() if match_key != "default" else None,
                    "dependent",
                    str(master_name),
                )
        for m in (rules.get("masters") or []):
            alts = [s.strip() for s in str(m).split("|")]
            if any(pn.lower() == a.lower() for a in alts):
                return (
                    match_key.title() if match_key != "default" else None,
                    "master",
                    None,
                )
    except Exception:
        pass
    if "reverb" in dn:
        return _group_role_for_reverb_param(param_name)
    return (None, None, None)


def build_groups_from_params(params: List[Dict[str, Any]], device_name: Optional[str]) -> List[Dict[str, Any]]:
    groups: Dict[str, Dict[str, Any]] = {}
    for p in params:
        name = str(p.get("name", ""))
        gname, role, master_name = group_role_for_device(device_name, name)
        if not gname:
            continue
        if gname not in groups:
            groups[gname] = {"name": gname, "master": None, "dependents": []}
        if role == "master":
            groups[gname]["master"] = {"name": name, "index": int(p.get("index", 0))}
        elif role == "dependent":
            groups[gname]["dependents"].append({"name": name, "index": int(p.get("index", 0)), "master": master_name})
    return list(groups.values())

