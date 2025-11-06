from __future__ import annotations

from typing import Any, Dict, List, Tuple

import time as _t

from server.config.param_learn_config import get_param_learn_config
from server.core.deps import get_store
from server.services.backcompat import udp_request
from server.services.mapping_utils import make_device_signature, detect_device_type
from server.utils.params import (
    parse_unit_from_display,
    classify_control_type,
    build_groups_from_params,
    group_role_for_device,
)
from server.api.device_mapping import _fit_models as fit_models  # reuse existing helper


def learn_return_device_quick(return_index: int, device_index: int) -> Dict[str, Any]:
    """Fast learning using minimal anchors + heuristics. Saves locally + Firestore.

    Mirrors legacy behavior from app handler; returns { ok, signature, local_saved, saved, param_count }.
    """
    PLC = get_param_learn_config()
    delay = max(0, int(PLC.get("defaults", {}).get("sleep_ms_quick", 10))) / 1000.0
    r2_accept = float(PLC.get("defaults", {}).get("r2_accept_quick", 0.99))
    max_extra = int(PLC.get("defaults", {}).get("max_extra_points_quick", 2))

    ri = int(return_index)
    di = int(device_index)

    # Fetch device + params
    devs = udp_request({"op": "get_return_devices", "return_index": ri}, timeout=1.0)
    devices = ((devs or {}).get("data") or {}).get("devices") or []
    dname = None
    for d in devices:
        if int(d.get("index", -1)) == di:
            dname = str(d.get("name", f"Device {di}"))
            break
    if dname is None:
        raise ValueError("device_not_found")

    params_resp = udp_request({"op": "get_return_device_params", "return_index": ri, "device_index": di}, timeout=1.2)
    params = ((params_resp or {}).get("data") or {}).get("params") or []
    signature = make_device_signature(dname or f"Device {di}", params)

    H = PLC.get("heuristics", {})
    lin_units = [str(u).lower() for u in (H.get("linear_units") or [])]
    exp_units = [str(u).lower() for u in (H.get("exp_units") or [])]
    linear_names = [str(n).lower() for n in (H.get("linear_names") or [])]
    exp_names = [str(n).lower() for n in (H.get("exp_names") or [])]
    SampC = (PLC.get("sampling", {}).get("continuous") or {})
    anchors_linear = SampC.get("linear") or [0.0, 0.5, 1.0]
    anchors_exp = SampC.get("exp") or [0.05, 0.5, 0.95]
    extra_anchors = SampC.get("fallback_extra") or [0.25, 0.75]

    learned_params: List[Dict[str, Any]] = []
    for p in params:
        idx = int(p.get("index", 0)); name = str(p.get("name", f"Param {idx}"))
        vmin = float(p.get("min", 0.0)); vmax = float(p.get("max", 1.0))
        v0 = float(p.get("value", 0.0))
        span = vmax - vmin if vmax != vmin else 1.0
        unit_guess = parse_unit_from_display(str(p.get("display_value", "")))

        # Quick enum detection
        labels = set()
        for t in [0.0, 0.5, 1.0]:
            val = vmin + span * t
            udp_request({"op": "set_return_device_param", "return_index": ri, "device_index": di, "param_index": idx, "value": float(val)}, timeout=0.6)
            if delay: _t.sleep(delay)
            rd = udp_request({"op": "get_return_device_params", "return_index": ri, "device_index": di}, timeout=1.0)
            rparams = ((rd or {}).get("data") or {}).get("params") or []
            dp = next((rp for rp in rparams if int(rp.get("index", -1)) == idx), None)
            if dp is not None:
                labels.add(str(dp.get("display_value", "")))

        from re import search as _re_search
        numeric_count = sum(1 for lab in labels if _re_search(r"-?\d+(?:\.\d+)?", lab))
        is_enum = (len(labels) <= 6 and numeric_count < len(labels)) or (len(labels) <= 2)

        samples: List[Dict[str, Any]] = []
        label_map: Dict[str, float] | None = None
        fit = None
        unit = unit_guess
        if is_enum:
            # Ends + a mid probe
            seen = set()
            for t in [0.0, 0.5, 1.0]:
                val = vmin + span * t
                udp_request({"op": "set_return_device_param", "return_index": ri, "device_index": di, "param_index": idx, "value": float(val)}, timeout=0.6)
                if delay: _t.sleep(delay)
                rd = udp_request({"op": "get_return_device_params", "return_index": ri, "device_index": di}, timeout=1.0)
                rparams = ((rd or {}).get("data") or {}).get("params") or []
                dp = next((rp for rp in rparams if int(rp.get("index", -1)) == idx), None)
                if dp is None: continue
                disp = str(dp.get("display_value", ""))
                if disp in seen: continue
                seen.add(disp)
                samples.append({"value": float(val), "display": disp, "display_num": None})
            label_map = {}
            for s in samples:
                lab = str(s.get("display", ""))
                if lab not in label_map:
                    label_map[lab] = float(s.get("value", vmin))
        else:
            # Continuous quick anchors by heuristic
            nm = name.lower(); ustr = (unit_guess or "").lower()
            anchors = anchors_exp if (ustr in exp_units or any(k in nm for k in exp_names)) else anchors_linear

            def probe(tfrac: float):
                val = vmin + span * max(0.0, min(1.0, tfrac))
                udp_request({"op": "set_return_device_param", "return_index": ri, "device_index": di, "param_index": idx, "value": float(val)}, timeout=0.6)
                if delay: _t.sleep(delay)
                rd = udp_request({"op": "get_return_device_params", "return_index": ri, "device_index": di}, timeout=1.0)
                rparams = ((rd or {}).get("data") or {}).get("params") or []
                dp = next((rp for rp in rparams if int(rp.get("index", -1)) == idx), None)
                if dp is None: return
                disp = str(dp.get("display_value", ""))
                dnum = None
                try:
                    import re as _re
                    m = _re.search(r"-?\d+(?:\.\d+)?", disp)
                    if m: dnum = float(m.group(0))
                except Exception:
                    dnum = None
                samples.append({"value": float(val), "display": disp, "display_num": dnum})

            for t in anchors:
                probe(float(t))
            fit = fit_models(samples)
            if not fit or float(fit.get("r2", 0.0)) < r2_accept:
                for t in extra_anchors[:max_extra]:
                    probe(float(t))
                fit = fit_models(samples)

        # restore
        udp_request({"op": "set_return_device_param", "return_index": ri, "device_index": di, "param_index": idx, "value": float(v0)}, timeout=0.6)

        ctype, labels_list = classify_control_type(samples, vmin, vmax)
        gname, role, _m = group_role_for_device(dname, name)
        learned_params.append({
            "index": idx,
            "name": name,
            "min": vmin,
            "max": vmax,
            "samples": samples,
            "control_type": ctype,
            "unit": unit,
            "labels": labels_list,
            "label_map": label_map,
            "fit": fit if ctype == "continuous" else None,
            "group": gname,
            "role": role,
        })

    groups_meta = build_groups_from_params(learned_params, dname)
    device_type = detect_device_type(params, dname)
    STORE = get_store()
    local_ok = STORE.save_device_map_local(signature, {"name": dname, "device_type": device_type, "groups": groups_meta}, learned_params)
    fs_ok = STORE.save_device_map(signature, {"name": dname, "device_type": device_type, "groups": groups_meta}, learned_params)
    return {"ok": True, "signature": signature, "local_saved": local_ok, "saved": fs_ok, "param_count": len(learned_params)}

