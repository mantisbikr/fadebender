from __future__ import annotations

import math
import re as _re
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException

from server.core.deps import get_store, get_device_resolver, get_value_registry
from server.services.ableton_client import request_op
from server.services.mapping_utils import make_device_signature
from server.models.intents_api import CanonicalIntent
from server.config.app_config import get_device_param_aliases
from server.volume_utils import db_to_live_float
from server.services.intents.utils.mixer import (
    parse_target_display,
    normalize_unit,
)


def alias_param_name_if_needed(name: Optional[str]) -> Optional[str]:
    if not name:
        return name
    n = str(name).strip().lower()
    try:
        cfg = get_device_param_aliases() or {}
    except Exception:
        cfg = {}
    # Built-in defaults; cfg overrides extend
    defaults = {
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
    if n in cfg:
        return str(cfg.get(n) or name)
    if n in defaults:
        return defaults[n]
    return name


def normalize_param_with_firestore(
    param_ref: Optional[str],
    device_name: Optional[str] = None,
    device_signature: Optional[str] = None,
) -> Optional[str]:
    if not param_ref or (not device_name and not device_signature):
        return param_ref
    try:
        from server.services.param_normalizer import normalize_parameter
        store = get_store()
        if not store or not store.enabled:
            return param_ref
        canonical_params = store.get_device_param_names(
            device_signature=device_signature,
            device_name=device_name,
        )
        if not canonical_params:
            return param_ref
        normalized, confidence = normalize_parameter(param_ref, canonical_params, max_distance=2)
        if normalized and confidence > 0.6:
            return normalized
        return param_ref
    except Exception:
        return param_ref


def resolve_param(params: List[dict], param_index: Optional[int], param_ref: Optional[str]) -> dict:
    if isinstance(param_index, int):
        for p in params:
            if int(p.get("index", -1)) == int(param_index):
                return p
        raise HTTPException(404, "param_not_found")
    if param_ref:
        import re as _re2

        def _norm_key(s: str) -> str:
            s0 = (s or "").lower()
            s0 = _re2.sub(r"\blo\b", "low", s0)
            s0 = _re2.sub(r"\bhi\b", "high", s0)
            s0 = _re2.sub(r"[^a-z0-9]", "", s0)
            s0 = s0.replace("locut", "lowcut").replace("hicut", "highcut")
            s0 = s0.replace("lowpass", "lowcut").replace("highpass", "highcut")
            s0 = s0.replace("drywet", "drywet")
            return s0

        pref_raw = str(param_ref or "").strip()
        pref = pref_raw.lower()
        pref_norm = _norm_key(pref_raw)
        names = [str(p.get("name", "")) for p in params]
        cand = [p for p in params if pref in str(p.get("name", "")).lower()]
        if len(cand) == 0 and pref_norm:
            pairs = [(p, _norm_key(str(p.get("name", "")))) for p in params]
            exact = [p for (p, nk) in pairs if nk == pref_norm]
            if exact:
                cand = exact
            else:
                cand = [p for (p, nk) in pairs if pref_norm in nk]
        if len(cand) == 1:
            return cand[0]
        if len(cand) == 0:
            starts = [n for n in names if n.lower().startswith(pref) or _norm_key(n).startswith(pref_norm)]
            contains = [n for n in names if (pref in n.lower()) or (pref_norm and pref_norm in _norm_key(n))]
            sugg = starts or contains or names[:8]
            sugg_text = ", ".join(sugg[:5])
            raise HTTPException(404, f"Parameter '{param_ref}' not found. Did you mean: {sugg_text}?")
        raise HTTPException(409, f"param_ambiguous:{param_ref}; candidates={[p.get('name') for p in cand]}")
    raise HTTPException(400, "param_selector_required")


def auto_enable_master_if_needed(params: List[dict], target_param_name: str) -> Optional[dict]:
    name = (target_param_name or "").lower()
    candidates = []
    keys = [
        ("chorus", "chorus on"),
        ("er spin", "er spin on"),
        ("lowshelf", "low shelf on"),
        ("low shelf", "low shelf on"),
        ("hishelf", "hi shelf on"),
        ("hi shelf", "hi shelf on"),
        ("reverb", "reverb on"),
        ("filter", "filter on"),
        ("low cut", "low cut on"),
        ("high cut", "high cut on"),
        ("eq", "eq on"),
        ("compressor", "compressor on"),
        ("gate", "gate on"),
    ]
    for k, toggle in keys:
        if k in name:
            candidates.append(toggle)
    for c in candidates:
        for p in params:
            if str(p.get("name", "")).strip().lower() == c:
                return p
    return None


def master_from_mapping(mapping: Optional[dict], params: List[dict], target_param_name: str) -> Optional[dict]:
    try:
        if not mapping:
            return None
        pmeta = mapping.get("params_meta") or []
        grp = next((g for g in pmeta if str(g.get("name", "")).strip().lower() == str(target_param_name or "").strip().lower()), None)
        if not grp:
            return None
        deps = grp.get("dependencies") or {}
        dep_key = deps.get("master_switch_name") or deps.get("master_on_name")
        if dep_key is None:
            return None
        master_name = str(deps.get(dep_key) or "").strip().lower()
        for p in params:
            if str(p.get("name", "")).strip().lower() == master_name:
                return p
    except Exception:
        return None
    return None


def check_requires_for_effect(mapping: Optional[dict], params: List[dict], target_param_name: str) -> List[dict]:
    prereqs: List[dict] = []
    try:
        if not mapping:
            return prereqs
        pmeta = mapping.get("params_meta") or []
        grp = next((g for g in pmeta if str(g.get("name", "")).strip().lower() == str(target_param_name or "").strip().lower()), None)
        if not grp:
            return prereqs
        requires = grp.get("requires_for_effect") or {}
        # Example: {"dry/wet": ">= 0.05"}
        for k, v in requires.items():
            try:
                key = str(k)
                cond = str(v).strip()
                pv = None
                if ">=" in cond:
                    th = float(cond.split(">=")[1].strip())
                    pv = (">=", th)
                elif ">" in cond:
                    th = float(cond.split(">")[1].strip())
                    pv = (">", th)
                elif "==" in cond:
                    th = float(cond.split("==")[1].strip())
                    pv = ("==", th)
                elif "on" == cond.lower():
                    pv = ("on", 1.0)
                if pv is None:
                    continue
                # find param
                for p in params:
                    if str(p.get("name", "")).strip().lower() == key.strip().lower():
                        vmin = float(p.get("min", 0.0)); vmax = float(p.get("max", 1.0))
                        _, th = pv
                        target_value = vmax if pv[0] in ("on", ">", ">=") and th >= vmax else max(vmin, th)
                        prereqs.append({
                            "param_dict": p,
                            "target_value": float(target_value),
                            "note": f"requires_for_effect:{target_param_name}",
                        })
                        break
            except Exception:
                continue
    except Exception:
        return []
    return prereqs


def invert_fit_to_value(fit: dict, target_y: float, vmin: float, vmax: float) -> float:
    t = (lambda a, b, y: (y - b) / a)
    ftype = fit.get("type")
    coeffs = fit.get("coeffs", {})
    if ftype == "linear":
        a = float(coeffs.get("a", 1.0)); b = float(coeffs.get("b", 0.0))
        x = t(a, b, target_y)
    elif ftype == "log":
        a = float(coeffs.get("a", 1.0)); b = float(coeffs.get("b", 0.0))
        x = math.exp((target_y - b) / a) if a != 0 else vmin
    elif ftype == "exp":
        a = float(coeffs.get("a", 1.0)); b = float(coeffs.get("b", 1.0))
        if target_y <= 0:
            x = vmin
        else:
            x = math.log(target_y / a) / b if (a != 0 and b != 0) else vmin
    else:
        pts = fit.get("points") or []
        pts = sorted([
            (float(p.get("y")), float(p.get("x")))
            for p in pts
            if p.get("x") is not None and p.get("y") is not None
        ])
        if not pts:
            return vmin
        lo = None; hi = None
        for y, x in pts:
            if y <= target_y:
                lo = (y, x)
            if y >= target_y and hi is None:
                hi = (y, x)
        if lo and hi and hi[0] != lo[0]:
            y1, x1 = lo; y2, x2 = hi
            tfrac = (target_y - y1) / (y2 - y1)
            x = x1 + tfrac * (x2 - x1)
        else:
            x = lo[1] if lo else hi[1]
    return max(vmin, min(vmax, float(x)))


def generate_device_param_summary(
    param_name: str,
    param_meta: Optional[dict],
    old_value: float,
    new_value: float,
    new_display: str,
    device_name: str,
    return_ref: Optional[str] = None,
    track_index: Optional[int] = None,
    old_display: Optional[str] = None,
) -> str:
    if return_ref:
        location = f"Return {return_ref} {device_name}"
    elif track_index is not None:
        location = f"Track {track_index} {device_name}"
    else:
        location = device_name
    increased = new_value > old_value
    try:
        od = parse_target_display(str(old_display)) if old_display is not None else None
        nd = parse_target_display(str(new_display)) if new_display is not None else None
        if od is not None and nd is not None:
            increased = float(nd) > float(od)
    except Exception:
        pass
    direction_word = "increased" if increased else ("decreased" if new_value < old_value else "set")
    try:
        s = str(new_display)
        m = _re.search(r"-?\d+(?:\.\d+)?", s)
        if m:
            num = float(m.group(0))
            rounded = round(num, 2)
            num_str = (f"{rounded:.2f}").rstrip('0').rstrip('.')
            new_display = s[:m.start()] + num_str + s[m.end():]
    except Exception:
        pass
    summary = f"Set {param_name} on {location} to {new_display}."
    if param_meta:
        audio_knowledge = param_meta.get("audio_knowledge", {})
        sonic_effect = audio_knowledge.get("sonic_effect", {})
        if sonic_effect:
            effect_text = None
            if increased and sonic_effect.get("increasing"):
                effect_text = sonic_effect.get("increasing")
            elif not increased and sonic_effect.get("decreasing"):
                effect_text = sonic_effect.get("decreasing")
            if effect_text:
                first_word = effect_text.split()[0].lower() if effect_text else ""
                common_verbs = {"create", "creates", "add", "adds", "reduce", "reduces", "increase", "increases", "decrease", "decreases", "make", "makes"}
                if first_word in common_verbs:
                    summary += f" {effect_text}"
                else:
                    summary += f" This {effect_text}."
    return summary


def set_return_device_param(intent: CanonicalIntent, debug: bool = False) -> Dict[str, Any]:
    if intent.return_index is None and intent.return_ref is None:
        raise HTTPException(400, "return_index_or_return_ref_required")
    if intent.device_index is None:
        raise HTTPException(400, "device_index_required")
    ri = int(intent.return_index) if intent.return_index is not None else (ord(str(intent.return_ref).strip().upper()) - ord('A'))
    di = int(intent.device_index)

    # Optional simple name/ordinal resolution
    if intent.device_name_hint or intent.device_ordinal_hint:
        try:
            devs_list = request_op("get_return_devices", timeout=1.0, return_index=ri) or {}
            devs = ((devs_list.get("data") or devs_list) if isinstance(devs_list, dict) else devs_list).get("devices", [])
            matches: List[int] = []
            if intent.device_name_hint:
                hint = str(intent.device_name_hint).strip().lower()
                hint_nos = hint.replace(" ", "")
                for d in devs:
                    nm = str(d.get("name", ""))
                    nml = nm.strip().lower()
                    if nml == hint or nml.replace(" ", "") == hint_nos or (hint in nml) or (hint_nos in nml.replace(" ", "")):
                        matches.append(int(d.get("index", 0)))
            else:
                matches = [int(d.get("index", 0)) for d in devs]
            matches = sorted(set(matches))
            ord_hint = int(intent.device_ordinal_hint) if intent.device_ordinal_hint else None
            if matches:
                if ord_hint:
                    if 1 <= ord_hint <= len(matches):
                        di = matches[ord_hint - 1]
                    else:
                        try:
                            hint_raw = str(intent.device_name_hint or "").strip().lower()
                            exact = next((int(d.get('index', 0)) for d in devs if str(d.get('name','')).strip().lower() == hint_raw), None)
                        except Exception:
                            exact = None
                        if exact is not None:
                            di = exact
                        else:
                            choices = ", ".join([f"{int(d.get('index',0))}:{str(d.get('name',''))}" for d in devs])
                            raise HTTPException(404, f"device_ordinal_out_of_range:{ord_hint}; matches={len(matches)}; devices=[{choices}]")
                else:
                    di = matches[0]
            # NOTE: If no matches, don't raise error here - let DeviceResolver handle it below
        except HTTPException:
            raise
        except Exception:
            pass

    # Validate range and optionally resolve via resolver
    try:
        devs_list = request_op("get_return_devices", timeout=1.0, return_index=ri) or {}
        devs = ((devs_list.get("data") or devs_list) if isinstance(devs_list, dict) else devs_list).get("devices", [])
        if devs and (di < 0 or di >= len(devs)):
            names = ", ".join([f"{int(d.get('index',0))}:{str(d.get('name',''))}" for d in devs])
            raise HTTPException(404, f"device_out_of_range:{di}; devices=[{names}] on Return {chr(ord('A')+ri)}")
    except HTTPException:
        raise
    except Exception:
        pass
    try:
        if intent.device_name_hint or intent.device_ordinal_hint:
            resolver = get_device_resolver()
            di_res, _dname, _notes = resolver.resolve_return(
                return_index=ri,
                device_name_hint=intent.device_name_hint,
                device_ordinal_hint=intent.device_ordinal_hint,
            )
            di = int(di_res)
    except Exception:
        pass

    pr = request_op("get_return_device_params", timeout=1.2, return_index=ri, device_index=di)
    params = ((pr or {}).get("data") or {}).get("params") or []
    if not params:
        raise HTTPException(404, "params_not_found")

    pref = alias_param_name_if_needed(intent.param_ref)
    # Firestore normalization
    try:
        device_name = None
        try:
            devs_list = request_op("get_return_devices", timeout=1.0, return_index=ri) or {}
            devs = ((devs_list.get("data") or devs_list) if isinstance(devs_list, dict) else devs_list).get("devices", [])
            for d in devs:
                if int(d.get("index", -1)) == di:
                    device_name = str(d.get("name", ""))
                    break
        except Exception:
            pass
        if device_name:
            pref = normalize_param_with_firestore(pref, device_name=device_name)
    except Exception:
        pass

    try:
        sel = resolve_param(params, intent.param_index, pref)
    except HTTPException as he:
        msg = str(he.detail) if hasattr(he, "detail") else str(he)
        if isinstance(he.status_code, int) and he.status_code in (404, 409) and ("param_not_found" in msg):
            try:
                devs_list = request_op("get_return_devices", timeout=1.0, return_index=ri) or {}
                devs = ((devs_list.get("data") or devs_list) if isinstance(devs_list, dict) else devs_list).get("devices", [])
                matches = []
                for d in devs:
                    dj = int(d.get("index", 0))
                    prj = request_op("get_return_device_params", timeout=1.0, return_index=ri, device_index=dj)
                    pjs = ((prj or {}).get("data") or {}).get("params") or []
                    try:
                        sj = resolve_param(pjs, intent.param_index, pref)
                        matches.append((dj, pjs, sj, str(d.get("name", f"Device {dj}"))))
                    except HTTPException:
                        continue
                if len(matches) == 1:
                    di, params, sel, _nm = matches[0]
                elif len(matches) > 1:
                    names = ", ".join([f"{m[0]}:{m[3]}" for m in matches])
                    raise HTTPException(409, f"param_ambiguous_across_devices:{pref}; devices=[{names}]")
                else:
                    raise he
            except HTTPException:
                raise
            except Exception:
                raise he
        else:
            raise

    vmin = float(sel.get("min", 0.0)); vmax = float(sel.get("max", 1.0))
    x = float(intent.value if intent.value is not None else vmin)
    used_display = False
    unit_lc = normalize_unit(intent.unit)
    target_display = intent.display if intent.display is not None else (str(intent.value) if unit_lc == "display" and intent.value is not None else None)

    mapping = None
    pm = None
    try:
        store = get_store()
        devs = request_op("get_return_devices", timeout=1.0, return_index=ri)
        devices = ((devs or {}).get("data") or {}).get("devices") or []
        dname = next((str(d.get("name", "")) for d in devices if int(d.get("index", -1)) == di), f"Device {di}")
        sig = make_device_signature(dname, params)
        mapping = store.get_device_mapping(sig) if store.enabled else None
        if mapping:
            pm = next((pme for pme in (mapping.get("params_meta") or []) if str(pme.get("name", "")).lower() == str(sel.get("name", "")).lower()), None)
    except Exception:
        mapping = None
        pm = None

    if target_display is None and unit_lc in ("ms", "s", "hz", "khz", "db", "%", "percent", "degrees", "on", "off") and intent.value is not None:
        target_display = str(intent.value)
    if target_display is None and intent.value is not None:
        try:
            val = float(intent.value)
            if pm and isinstance(pm.get("unit"), str):
                pm_unit = (pm.get("unit") or "").strip().lower()
                if pm_unit in ("ms", "s", "hz", "khz", "db", "%", "degrees"):
                    target_display = str(val)
                    used_display = True
            if target_display is None and pm is not None and pm.get("min_display") is not None and pm.get("max_display") is not None:
                md = float(pm.get("min_display")); Mx = float(pm.get("max_display"))
                if md <= val <= Mx:
                    target_display = str(val)
                    used_display = True
                elif md >= 0.0 and Mx <= 1.0 and 0.0 <= val <= 100.0:
                    unit_lc = "%"
        except Exception:
            pass

    if target_display is not None:
        used_display = True
        ty = parse_target_display(target_display)
        if pm and isinstance(pm.get("label_map"), dict):
            lm = pm.get("label_map") or {}
            lnorm = target_display.strip().lower()
            matched = False
            for k, v in lm.items():
                if str(v).strip().lower() == lnorm:
                    x = float(k)
                    matched = True
                    break
            if not matched:
                if lnorm in {"on", "enable", "enabled", "true", "1", "yes"}:
                    x = vmax; matched = True
                elif lnorm in {"off", "disable", "disabled", "false", "0", "no"}:
                    x = vmin; matched = True
            if matched:
                ty = None
        if ty is None and not (pm.get("label_map") if pm else None):
            lnorm = str(target_display).strip().lower()
            if lnorm in {"on", "enable", "enabled", "true", "1", "yes"}:
                x = vmax
            elif lnorm in {"off", "disable", "disabled", "false", "0", "no"}:
                x = vmin
        elif ty is not None:
            if pm and isinstance(pm.get("fit"), dict):
                pm_unit = (pm.get("unit") or "").strip().lower()
                input_unit = unit_lc or detect_display_unit(target_display) or pm_unit
                ty_aligned = convert_unit_value(float(ty), input_unit, pm_unit)
                x = invert_fit_to_value(pm.get("fit") or {}, float(ty_aligned), vmin, vmax)
            else:
                if intent.dry_run:
                    pv = {"note": "approx_preview_no_fit", "target_display": target_display, "value_range": [vmin, vmax]}
                    return {"ok": True, "preview": pv}
                try:
                    request_op("set_return_device_param", timeout=1.0, return_index=ri, device_index=di, param_index=int(sel.get("index", 0)), value=float(vmin))
                    rb0 = request_op("get_return_device_params", timeout=1.0, return_index=ri, device_index=di)
                    p0s = ((rb0 or {}).get("data") or {}).get("params") or []
                    p0 = next((p for p in p0s if int(p.get("index", -1)) == int(sel.get("index", 0))), None)
                    d0 = parse_target_display(str((p0 or {}).get("display_value", "")))
                    request_op("set_return_device_param", timeout=1.0, return_index=ri, device_index=di, param_index=int(sel.get("index", 0)), value=float(vmax))
                    rb1 = request_op("get_return_device_params", timeout=1.0, return_index=ri, device_index=di)
                    p1s = ((rb1 or {}).get("data") or {}).get("params") or []
                    p1 = next((p for p in p1s if int(p.get("index", -1)) == int(sel.get("index", 0))), None)
                    d1 = parse_target_display(str((p1 or {}).get("display_value", "")))
                    target = float(ty)
                    try:
                        rb_unit = detect_display_unit(str((p1 or {}).get("display_value", ""))) or detect_display_unit(str((p0 or {}).get("display_value", "")))
                        if rb_unit:
                            unit_lc_td = normalize_unit(intent.unit)
                            target = convert_unit_value(float(target), unit_lc_td or rb_unit, rb_unit)
                    except Exception:
                        pass
                    if d0 is not None and d1 is not None and target is not None:
                        lo = vmin; hi = vmax; inc = d1 > d0
                        for _ in range(8):
                            mid = (lo + hi) / 2.0
                            request_op("set_return_device_param", timeout=1.0, return_index=ri, device_index=di, param_index=int(sel.get("index", 0)), value=float(mid))
                            rbm = request_op("get_return_device_params", timeout=1.0, return_index=ri, device_index=di)
                            pms = ((rbm or {}).get("data") or {}).get("params") or []
                            pmid = next((p for p in pms if int(p.get("index", -1)) == int(sel.get("index", 0))), None)
                            dmid = parse_target_display(str((pmid or {}).get("display_value", "")))
                            if dmid is None:
                                break
                            err = abs(dmid - float(target))
                            thresh = 0.02 * (abs(target) if target != 0 else 1.0)
                            if err <= thresh:
                                x = mid
                                break
                            if (dmid < float(target) and inc) or (dmid > float(target) and not inc):
                                lo = mid
                            else:
                                hi = mid
                        else:
                            x = (lo + hi) / 2.0
                except Exception:
                    pass

    if not used_display and (normalize_unit(intent.unit) or "") in ("percent", "%"):
        x = vmin + (vmax - vmin) * max(0.0, min(100.0, x)) / 100.0

    prereq_changes: List[dict] = []
    try:
        store = get_store(); mapping = mapping or (store.get_device_mapping(make_device_signature(dname, params)) if (store and store.enabled) else None)  # type: ignore
    except Exception:
        mapping = None  # type: ignore
    if mapping and intent.auto_enable_master:
        master_toggle = master_from_mapping(mapping, params, str(sel.get("name", "")))
        if master_toggle and float(master_toggle.get("value", 0.0)) < 0.5:
            prereq_changes.append({
                "param_dict": master_toggle,
                "target_value": float(master_toggle.get("max", 1.0)),
                "note": "auto_enable_master",
            })
        for pc in check_requires_for_effect(mapping, params, str(sel.get("name", ""))):
            if not any(int(p.get("index", -1)) == int(pc["param_dict"].get("index", -1)) for p in prereq_changes):
                prereq_changes.append(pc)

    preview: Dict[str, Any] = {"op": "set_return_device_param", "return_index": ri, "device_index": di, "param_index": int(sel.get("index", 0)), "value": float(max(vmin, min(vmax, x)) if intent.clamp else x)}
    if prereq_changes:
        preview["prereqs"] = [
            {
                "op": "set_return_device_param",
                "return_index": ri,
                "device_index": di,
                "param_index": int(pc["param_dict"].get("index", 0)),
                "param_name": pc["param_dict"].get("name"),
                "value": float(pc["target_value"]),
                "note": pc["note"],
            }
            for pc in prereq_changes
        ]
    if intent.dry_run:
        return {"ok": True, "preview": preview}

    for prereq in prereq_changes:
        pd = prereq["param_dict"]
        request_op("set_return_device_param", timeout=1.0, return_index=ri, device_index=di, param_index=int(pd.get("index", 0)), value=float(prereq["target_value"]))

    old_val = float(sel.get("value", 0.0))
    resp = request_op("set_return_device_param", timeout=1.0, return_index=ri, device_index=di, param_index=int(sel.get("index", 0)), value=float(preview["value"]))
    if not resp:
        raise HTTPException(504, "no_reply")

    try:
        readback = request_op("get_return_device_params", timeout=1.0, return_index=ri, device_index=di)
        rb_params = ((readback or {}).get("data") or {}).get("params") or []
        updated_param = next((p for p in rb_params if int(p.get("index", -1)) == int(sel.get("index", 0))), None)
        if updated_param:
            new_display = updated_param.get("display_value") or str(preview["value"])
            new_val = float(updated_param.get("value", preview["value"]))
            devs = request_op("get_return_devices", timeout=0.8, return_index=ri)
            devices = ((devs or {}).get("data") or {}).get("devices") or []
            dname = next((str(d.get("name", "")) for d in devices if int(d.get("index", -1)) == di), f"Device {di}")
            return_letter = chr(ord('A') + ri)
            summary = generate_device_param_summary(
                param_name=str(sel.get("name", "")),
                param_meta=pm,
                old_value=old_val,
                new_value=new_val,
                new_display=new_display,
                device_name=dname,
                return_ref=return_letter,
                old_display=str(sel.get("display_value")) if sel.get("display_value") is not None else None,
            )
            if isinstance(resp, dict):
                resp["summary"] = summary
            try:
                reg = get_value_registry()
                unit_out = None
                try:
                    if pm and isinstance(pm.get("unit"), str):
                        unit_out = str(pm.get("unit")).lower()
                except Exception:
                    pass
                reg.update_device_param("return", ri, di, str(sel.get("name", "")), new_val, new_display, unit_out, source="op")
            except Exception:
                pass
    except Exception:
        pass

    if not intent.dry_run:
        try:
            from server.api.cap_utils import ensure_capabilities  # type: ignore
            resp = ensure_capabilities(resp, domain="return_device", return_index=ri, device_index=di)
        except Exception:
            pass

    return resp


def detect_display_unit(disp: str) -> Optional[str]:
    s = (disp or "").lower()
    if " khz" in s or "khz" in s:
        return "khz"
    if " hz" in s or s.endswith("hz"):
        return "hz"
    if " ms" in s or s.endswith("ms"):
        return "ms"
    if s.endswith(" s") or s.endswith(" sec") or s.endswith(" second") or s.endswith(" seconds") or s.endswith("s"):
        return "s"
    if "db" in s:
        return "db"
    if "degree" in s or "degrees" in s or "°" in s:
        return "degrees"
    if "%" in s:
        return "%"
    return None


def convert_unit_value(value: float, src: Optional[str], dest: Optional[str]) -> float:
    s = (src or "").strip().lower()
    d = (dest or "").strip().lower()
    if not s or not d or s == d:
        return float(value)
    v = float(value)
    if s == "ms" and d == "s":
        return v / 1000.0
    if s == "s" and d == "ms":
        return v * 1000.0
    if s == "khz" and d == "hz":
        return v * 1000.0
    if s == "hz" and d == "khz":
        return v / 1000.0
    if s in ("percent", "%") and d in ("percent", "%"):
        return v
    return v


def set_track_device_param(intent: CanonicalIntent, debug: bool = False) -> Dict[str, Any]:
    if intent.track_index is None or intent.device_index is None:
        raise HTTPException(400, "track_index_and_device_index_required")
    ti = int(intent.track_index)
    di = int(intent.device_index)

    # Optional resolver when hints are present
    try:
        if intent.device_name_hint or intent.device_ordinal_hint:
            resolver = get_device_resolver()
            di_res, _dname, _notes = resolver.resolve_track(
                track_index=ti,
                device_name_hint=intent.device_name_hint,
                device_ordinal_hint=intent.device_ordinal_hint,
            )
            di = int(di_res)
    except Exception:
        pass

    pr = request_op("get_track_device_params", timeout=1.2, track_index=ti, device_index=di)
    params = ((pr or {}).get("data") or {}).get("params") or []
    if not params:
        raise HTTPException(404, "params_not_found")

    pref = alias_param_name_if_needed(intent.param_ref)
    try:
        sel = resolve_param(params, intent.param_index, pref)
    except HTTPException as he:
        msg = str(he.detail) if hasattr(he, "detail") else str(he)
        if isinstance(he.status_code, int) and he.status_code in (404, 409) and ("param_not_found" in msg):
            try:
                devs_list = request_op("get_track_devices", timeout=1.0, track_index=ti) or {}
                devs = ((devs_list.get("data") or devs_list) if isinstance(devs_list, dict) else devs_list).get("devices", [])
                matches = []
                for d in devs:
                    dj = int(d.get("index", 0))
                    prj = request_op("get_track_device_params", timeout=1.0, track_index=ti, device_index=dj)
                    pjs = ((prj or {}).get("data") or {}).get("params") or []
                    try:
                        sj = resolve_param(pjs, intent.param_index, pref)
                        matches.append((dj, pjs, sj, str(d.get("name", f"Device {dj}"))))
                    except HTTPException:
                        continue
                if len(matches) == 1:
                    di, params, sel, _nm = matches[0]
                elif len(matches) > 1:
                    names = ", ".join([f"{m[0]}:{m[3]}" for m in matches])
                    raise HTTPException(409, f"param_ambiguous_across_devices:{pref}; devices=[{names}]")
                else:
                    raise he
            except HTTPException:
                raise
            except Exception:
                raise he
        else:
            raise

    vmin = float(sel.get("min", 0.0)); vmax = float(sel.get("max", 1.0))
    x = float(intent.value if intent.value is not None else vmin)
    used_display = False
    unit_lc = normalize_unit(intent.unit)
    target_display = intent.display if intent.display is not None else (str(intent.value) if unit_lc == "display" and intent.value is not None else None)

    mapping = None
    pm = None
    try:
        store = get_store()
        devs = request_op("get_track_devices", timeout=1.0, track_index=ti)
        devices = ((devs or {}).get("data") or {}).get("devices") or []
        dname = next((str(d.get("name", "")) for d in devices if int(d.get("index", -1)) == di), f"Device {di}")
        sig = make_device_signature(dname, params)
        mapping = store.get_device_mapping(sig) if store.enabled else None
        if mapping:
            pm = next((pme for pme in (mapping.get("params_meta") or []) if str(pme.get("name", "")).lower() == str(sel.get("name", "")).lower()), None)
    except Exception:
        mapping = None
        pm = None

    if target_display is None and unit_lc in ("ms", "s", "hz", "khz", "db", "%", "percent", "degrees", "on", "off") and intent.value is not None:
        target_display = str(intent.value)
    if target_display is None and intent.value is not None:
        try:
            val = float(intent.value)
            if pm and isinstance(pm.get("unit"), str):
                pm_unit = (pm.get("unit") or "").strip().lower()
                if pm_unit in ("ms", "s", "hz", "khz", "db", "%", "degrees"):
                    target_display = str(val)
                    used_display = True
            if target_display is None and pm is not None and pm.get("min_display") is not None and pm.get("max_display") is not None:
                md = float(pm.get("min_display")); Mx = float(pm.get("max_display"))
                if md <= val <= Mx:
                    target_display = str(val)
                    used_display = True
                elif md >= 0.0 and Mx <= 1.0 and 0.0 <= val <= 100.0:
                    unit_lc = "%"
        except Exception:
            pass

    if target_display is not None:
        used_display = True
        ty = parse_target_display(target_display)
        if pm and isinstance(pm.get("label_map"), dict):
            lm = pm.get("label_map") or {}
            lnorm = target_display.strip().lower()
            matched = False
            for k, v in lm.items():
                if str(v).strip().lower() == lnorm:
                    x = float(k)
                    matched = True
                    break
            if not matched:
                if lnorm in {"on", "enable", "enabled", "true", "1", "yes"}:
                    x = vmax; matched = True
                elif lnorm in {"off", "disable", "disabled", "false", "0", "no"}:
                    x = vmin; matched = True
            if matched:
                ty = None
        if ty is None and not (pm.get("label_map") if pm else None):
            lnorm = str(target_display).strip().lower()
            if lnorm in {"on", "enable", "enabled", "true", "1", "yes"}:
                x = vmax
            elif lnorm in {"off", "disable", "disabled", "false", "0", "no"}:
                x = vmin
        elif ty is not None:
            if pm and isinstance(pm.get("fit"), dict):
                pm_unit = (pm.get("unit") or "").strip().lower()
                input_unit = unit_lc or detect_display_unit(target_display) or pm_unit
                ty_aligned = convert_unit_value(float(ty), input_unit, pm_unit)
                x = invert_fit_to_value(pm.get("fit") or {}, float(ty_aligned), vmin, vmax)
            else:
                if intent.dry_run:
                    pv = {"note": "approx_preview_no_fit", "target_display": target_display, "value_range": [vmin, vmax]}
                    return {"ok": True, "preview": pv}
                try:
                    request_op("set_device_param", timeout=1.0, track_index=ti, device_index=di, param_index=int(sel.get("index", 0)), value=float(vmin))
                    rb0 = request_op("get_track_device_params", timeout=1.0, track_index=ti, device_index=di)
                    p0s = ((rb0 or {}).get("data") or {}).get("params") or []
                    p0 = next((p for p in p0s if int(p.get("index", -1)) == int(sel.get("index", 0))), None)
                    d0 = parse_target_display(str((p0 or {}).get("display_value", "")))
                    request_op("set_device_param", timeout=1.0, track_index=ti, device_index=di, param_index=int(sel.get("index", 0)), value=float(vmax))
                    rb1 = request_op("get_track_device_params", timeout=1.0, track_index=ti, device_index=di)
                    p1s = ((rb1 or {}).get("data") or {}).get("params") or []
                    p1 = next((p for p in p1s if int(p.get("index", -1)) == int(sel.get("index", 0))), None)
                    d1 = parse_target_display(str((p1 or {}).get("display_value", "")))
                    ty2 = parse_target_display(target_display)
                    target = float(ty2) if ty2 is not None else None
                    try:
                        if target is not None:
                            rb_unit = detect_display_unit(str((p1 or {}).get("display_value", ""))) or detect_display_unit(str((p0 or {}).get("display_value", "")))
                            if rb_unit:
                                unit_lc_td = normalize_unit(intent.unit)
                                target = convert_unit_value(float(target), unit_lc_td or rb_unit, rb_unit)
                    except Exception:
                        pass
                    if d0 is not None and d1 is not None and target is not None:
                        lo = vmin; hi = vmax; inc = d1 > d0
                        for _ in range(8):
                            mid = (lo + hi) / 2.0
                            request_op("set_device_param", timeout=1.0, track_index=ti, device_index=di, param_index=int(sel.get("index", 0)), value=float(mid))
                            rbm = request_op("get_track_device_params", timeout=1.0, track_index=ti, device_index=di)
                            pms = ((rbm or {}).get("data") or {}).get("params") or []
                            pmid = next((p for p in pms if int(p.get("index", -1)) == int(sel.get("index", 0))), None)
                            dmid = parse_target_display(str((pmid or {}).get("display_value", "")))
                            if dmid is None:
                                break
                            err = abs(dmid - float(target))
                            thresh = 0.02 * (abs(target) if target != 0 else 1.0)
                            if err <= thresh:
                                x = mid
                                break
                            if (dmid < float(target) and inc) or (dmid > float(target) and not inc):
                                lo = mid
                            else:
                                hi = mid
                        else:
                            x = (lo + hi) / 2.0
                except Exception:
                    pass

    if not used_display and (normalize_unit(intent.unit) or "") in ("percent", "%"):
        x = vmin + (vmax - vmin) * max(0.0, min(100.0, x)) / 100.0

    preview = {"op": "set_device_param", "track_index": ti, "device_index": di, "param_index": int(sel.get("index", 0)), "value": float(max(vmin, min(vmax, x)) if intent.clamp else x)}
    if intent.dry_run:
        return {"ok": True, "preview": preview}
    resp = request_op("set_device_param", timeout=1.0, track_index=ti, device_index=di, param_index=int(sel.get("index", 0)), value=float(preview["value"]))
    if not resp:
        raise HTTPException(504, "no_reply")

    try:
        rb = request_op("get_track_device_params", timeout=1.0, track_index=ti, device_index=di)
        params_rb = ((rb or {}).get("data") or {}).get("params") or []
        up = next((p for p in params_rb if int(p.get("index", -1)) == int(sel.get("index", 0))), None)
        if up:
            new_display = up.get("display_value") or str(preview["value"])  # fallback
            new_val = float(up.get("value", preview["value"]))
            try:
                reg = get_value_registry()
                reg.update_device_param("track", ti, di, str(sel.get("name", "")), new_val, new_display, None, source="op")
            except Exception:
                pass
    except Exception:
        pass
    return resp

