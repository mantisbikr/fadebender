from __future__ import annotations

import asyncio
import uuid
from typing import Any, Dict, List, Set

from server.services.learn_jobs import LEARN_JOBS
from server.services.backcompat import udp_request
from server.services.mapping_utils import make_device_signature, detect_device_type
from server.utils.params import (
    parse_unit_from_display,
    build_groups_from_params,
    group_role_for_device,
)
from server.api.device_mapping import _fit_models as fit_models  # reuse fit helper
from server.core.deps import get_store


async def learn_return_device_start(return_index: int, device_index: int, resolution: int = 41, sleep_ms: int = 20) -> Dict[str, Any]:
    """Kick off an exhaustive learning job and return job_id.

    Mirrors legacy behavior from app.py. Writes progress into LEARN_JOBS.
    """
    job_id = str(uuid.uuid4())
    LEARN_JOBS[job_id] = {
        "state": "queued",
        "progress": 0,
        "total": 1,
        "message": "Starting",
    }

    async def run() -> None:
        try:
            ri = int(return_index)
            di = int(device_index)
            res = max(3, int(resolution))
            delay = max(0, int(sleep_ms)) / 1000.0

            # Fetch device + params
            devs = udp_request({"op": "get_return_devices", "return_index": ri}, timeout=1.0)
            devices = ((devs or {}).get("data") or {}).get("devices") or []
            dname = None
            for d in devices:
                if int(d.get("index", -1)) == di:
                    dname = str(d.get("name", f"Device {di}"))
                    break
            params_resp = udp_request({"op": "get_return_device_params", "return_index": ri, "device_index": di}, timeout=1.2)
            params = ((params_resp or {}).get("data") or {}).get("params") or []
            signature = make_device_signature(dname or f"Device {di}", params)
            total_steps = max(1, len(params) * res)
            LEARN_JOBS[job_id].update({"state": "running", "progress": 0, "total": total_steps, "signature": signature})

            learned_params: List[Dict[str, Any]] = []
            step = 0
            for p in params:
                idx = int(p.get("index", 0))
                name = str(p.get("name", f"Param {idx}"))
                vmin = float(p.get("min", 0.0))
                vmax = float(p.get("max", 1.0))
                v0 = float(p.get("value", 0.0))

                # Coarse check for quantization using 9 points
                import time as _t
                labels: Set[str] = set()
                coarse = 9
                span = vmax - vmin if vmax != vmin else 1.0
                for i in range(coarse):
                    t = i / float(coarse - 1)
                    val = vmin + span * t
                    udp_request({"op": "set_return_device_param", "return_index": ri, "device_index": di, "param_index": idx, "value": float(val)}, timeout=0.6)
                    if delay:
                        _t.sleep(delay)
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
                unit = None
                labels_list: List[str] = []
                control_type = "continuous"
                if is_enum:
                    control_type = "quantized"
                    # Probe ends + mid and build label_map
                    seen = set()
                    for t in [0.0, 0.5, 1.0]:
                        val = vmin + span * t
                        udp_request({"op": "set_return_device_param", "return_index": ri, "device_index": di, "param_index": idx, "value": float(val)}, timeout=0.6)
                        if delay:
                            _t.sleep(delay)
                        rd = udp_request({"op": "get_return_device_params", "return_index": ri, "device_index": di}, timeout=1.0)
                        rparams = ((rd or {}).get("data") or {}).get("params") or []
                        dp = next((rp for rp in rparams if int(rp.get("index", -1)) == idx), None)
                        if dp is None:
                            continue
                        disp = str(dp.get("display_value", ""))
                        if unit is None:
                            unit = parse_unit_from_display(disp)
                        if disp in seen:
                            continue
                        seen.add(disp)
                        samples.append({"value": float(val), "display": disp, "display_num": None})
                        step += 1
                        LEARN_JOBS[job_id].update({"progress": min(step, total_steps), "message": f"{name}: {int(t* (coarse-1))+1}/{coarse}"})
                    label_map = {s["display"]: s["value"] for s in samples}
                    labels_list = list(label_map.keys())
                else:
                    # Continuous anchors only to estimate duration; detailed fit handled in quick path
                    control_type = "continuous"
                    # Probe across grid
                    import time as _t
                    for i in range(res):
                        t = i / float(res - 1)
                        val = vmin + span * t
                        udp_request({"op": "set_return_device_param", "return_index": ri, "device_index": di, "param_index": idx, "value": float(val)}, timeout=0.6)
                        if delay:
                            _t.sleep(delay)
                        rd = udp_request({"op": "get_return_device_params", "return_index": ri, "device_index": di}, timeout=1.0)
                        rparams = ((rd or {}).get("data") or {}).get("params") or []
                        dp = next((rp for rp in rparams if int(rp.get("index", -1)) == idx), None)
                        if dp is None:
                            continue
                        disp = str(dp.get("display_value", ""))
                        if unit is None:
                            unit = parse_unit_from_display(disp)
                        from re import search as _re_search
                        disp_num = None
                        try:
                            m = _re_search(r"-?\d+(?:\.\d+)?", disp)
                            if m:
                                disp_num = float(m.group(0))
                        except Exception:
                            disp_num = None
                        samples.append({"value": float(val), "display": disp, "display_num": disp_num})
                        step += 1
                        LEARN_JOBS[job_id].update({"progress": min(step, total_steps), "message": f"{name}: {i+1}/{res}"})
                    fit = fit_models(samples) or None

                # restore
                udp_request({"op": "set_return_device_param", "return_index": ri, "device_index": di, "param_index": idx, "value": float(v0)}, timeout=0.6)
                # Group/role annotation
                gname, role, _m = group_role_for_device(dname, name)
                learned_params.append({
                    "index": idx,
                    "name": name,
                    "min": vmin,
                    "max": vmax,
                    "samples": samples,
                    "quantized": is_enum,
                    "control_type": control_type,
                    "unit": unit,
                    "labels": labels_list,
                    "label_map": label_map,
                    "fit": fit,
                    "group": gname,
                    "role": role,
                })

            # Save results
            STORE = get_store()
            groups_meta = build_groups_from_params(learned_params, dname)
            device_type = detect_device_type(params, dname)
            local_saved = STORE.save_device_map_local(signature, {"name": dname, "device_type": device_type, "groups": groups_meta}, learned_params)
            saved = STORE.save_device_map(signature, {"name": dname, "device_type": device_type, "groups": groups_meta}, learned_params)
            LEARN_JOBS[job_id].update({"state": "done", "saved": saved, "local_saved": local_saved})
        except Exception as e:
            LEARN_JOBS[job_id].update({"state": "error", "error": str(e)})

    asyncio.create_task(run())
    return {"ok": True, "job_id": job_id}

