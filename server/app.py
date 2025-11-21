from __future__ import annotations
import os
from typing import Any, Dict, Optional
import time
import asyncio
from fastapi.responses import StreamingResponse
import json

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from server.middleware.error_handler import ErrorHandlerMiddleware
from server.middleware.request_id import RequestIDMiddleware

from server.services.ableton_client import request_op
from server.services.backcompat import udp_request
from server.config.helpers import status_ttl_seconds, cors_origins, debug_enabled
from server.models.requests import IntentParseBody, VolumeDbBody, SelectTrackBody
from server.models.ops import MixerOp, SendOp, DeviceParamOp
from server.services.intent_mapper import map_llm_to_canonical
from server.volume_utils import db_to_live_float, live_float_to_db, db_to_live_float_send, live_float_to_db_send
from server.config.app_config import (
    get_app_config,
    get_send_aliases,
    get_ui_settings,
    set_ui_settings,
    set_send_aliases,
    get_debug_settings,
    set_debug_settings,
    reload_config as cfg_reload,
    save_config as cfg_save,
)
from server.config.param_learn_config import (
    get_param_learn_config,
    set_param_learn_config,
    reload_param_learn_config,
    save_param_learn_config,
)
from server.config.param_registry import (
    get_param_registry,
    reload_param_registry,
)
from server.services.mapping_store import MappingStore
from server.services.mapping_utils import detect_device_type, make_device_signature
from server.services.param_analysis import (
    build_groups_from_params,
    classify_control_type,
    fit_models,
    group_role_for_device,
    parse_unit_from_display,
)
from server.services.preset_metadata import generate_preset_metadata_llm
# Chat routes are provided by server.api.chat router
from server.services.history import (
    DEVICE_BYPASS_CACHE,
    LAST_SENT,
    REDO_STACK,
    UNDO_STACK,
    history_state as get_history_state,
    redo_last as history_redo_last,
    undo_last as history_undo_last,
    _key,
    _rate_limited,
)
from server.services.event_listener import (
    schedule_live_index_tasks,
    start_ableton_event_listener,
)
from server.core.deps import set_store_instance, get_live_index
from server.core.events import broker, emit_event, schedule_emit
from server.api.events import router as events_router
from server.api.health import router as health_router
from server.api.transport import router as transport_router
from server.api.config import router as config_router
from server.api.master import router as master_router
from server.api.tracks import router as tracks_router
from server.api.returns import router as returns_router
from server.api.ops import router as ops_router
from server.api.device_mapping import router as device_mapping_router
from server.api.presets import router as presets_router
from server.api.intents import router as intents_router
from server.api.nlp import router as nlp_router
from server.api.overview import router as overview_router
from server.api.overview_status import router as overview_status_router
from server.api.overview_devices import router as overview_devices_router
from server.api.chat import router as chat_router
from server.api.system import router as system_router
from server.api.learn import router as learn_router
# from server.api.snapshot import router as snapshot_router  # Merged into overview_router
import math
from server.volume_parser import parse_volume_command
_MASTER_DEDUP: dict[str, tuple[float, float]] = {}

app = FastAPI(title="Fadebender Ableton Server", version="0.1.0")

# Load .env at server startup so Vertex/LLM config can come from file
try:  # optional dependency
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass


app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Attach request IDs for better tracing/logging
app.add_middleware(RequestIDMiddleware)

# Error handling middleware for consistent error responses
app.add_middleware(ErrorHandlerMiddleware)


# llm/health is now provided by the health router


# --- Simple SSE event broker ---
STORE = MappingStore()
set_store_instance(STORE)
from server.services.learn_jobs import LEARN_JOBS

app.include_router(events_router)
app.include_router(transport_router)
app.include_router(config_router)
app.include_router(master_router)
app.include_router(tracks_router)
app.include_router(returns_router)
app.include_router(device_mapping_router)
app.include_router(presets_router)
app.include_router(ops_router)
app.include_router(intents_router)
app.include_router(nlp_router)

# FORCE legacy router (full enrichment) - new_routing flag is broken
print("[APP STARTUP] FORCING LEGACY ROUTING (overview_router - full enrichment)")
app.include_router(overview_router)

# Disabled: new_routing uses empty devices, breaks NLP
# from server.config.feature_flags import is_enabled
# if is_enabled("new_routing"):
#     print("[APP STARTUP] Using NEW_ROUTING (overview_status_router - empty devices)")
#     app.include_router(overview_status_router)
#     app.include_router(overview_devices_router)
# else:
#     print("[APP STARTUP] Using LEGACY ROUTING (overview_router - full enrichment)")
#     app.include_router(overview_router)
# app.include_router(snapshot_router)  # Merged into overview_router


app.include_router(health_router)
app.include_router(chat_router)
app.include_router(system_router)
app.include_router(learn_router)


# Transport routes moved to server.api.transport


# Master routes moved to server.api.master


"""Config routes moved to server.api.config"""


"""Param registry route moved to server.api.config"""


"""Param learn routes moved to server.api.config"""




# Track status moved to server.api.tracks


# Track sends moved to server.api.tracks


# Track routing moved to server.api.tracks


# Returns listing moved to server.api.returns


# Return sends moved to server.api.returns


"""Return routing & sends moved to server.api.returns"""


# Return devices moved to server.api.returns


# ---------------- Track devices (Phase A - minimal) ----------------

# Track devices moved to server.api.tracks


# Track device params moved to server.api.tracks


# Track device param set moved to server.api.tracks


# ---------------- Master devices (Phase A - minimal) ----------------

"""Master devices moved to server.api.master"""


"""Master device params moved to server.api.master"""


"""Master device param set moved to server.api.master"""


"""Return device params moved to server.api.returns"""


"""Return device map endpoints moved to server.api.device_mapping (removed)."""


"""Map delete and return op bodies moved to server.api.* (removed duplicates)."""


"""Device mapping import/get/validate moved to server.api.device_mapping"""


"""/device_mapping/sanity_probe moved to server.api.device_mapping"""


# moved: /device_mapping/fits handled by server.api.device_mapping
"""/device_mapping/fits moved to server.api.device_mapping"""


"""/device_mapping/enumerate_labels moved to server.api.device_mapping"""


"""/op/return/mixer moved to server.api.ops"""


"""Legacy /return/device/learn moved to server.api.learn"""


"""/return/device/learn_start moved to server.api.learn (legacy handler removed)"""


"""/return/device/learn_quick moved to server.api.learn"""


"""/mappings/push_local moved to server.api.device_mapping"""


"""/mappings/migrate_schema moved to server.api.device_mapping"""


"""Signature helper moved to server.api.device_mapping"""


"""/mappings/fit moved to server.api.device_mapping"""


"""Preset endpoints moved to server.api.presets (removed legacy stubs)."""


"""Preset refresh moved to server.api.presets"""


"""Param-by-name helpers moved to server.api.ops"""


"""/op/return/param_by_name moved to server.api.ops"""
"""
    # Fetch current params and signature
    p_resp = udp_request({"op": "get_return_device_params", "return_index": ri, "device_index": di}, timeout=1.2)
    p_list = ((p_resp or {}).get("data") or {}).get("params") or []
    cur = next((p for p in p_list if int(p.get("index", -1)) == pi), None)
    if not cur:
        raise HTTPException(404, "param_state_not_found")
    vmin = float(cur.get("min", 0.0)); vmax = float(cur.get("max", 1.0))

    # Build signature and fetch learned map (Firestore then local)
    signature = _compute_signature_for(ri, di)
    mapping = STORE.get_device_map(signature) if STORE.enabled else None
    if not mapping:
        mapping = STORE.get_device_map_local(signature)
    # Fetch new device mapping (fits/labels) when available
    new_map = None
    try:
        new_map = STORE.get_device_mapping(signature) if STORE.enabled else None
    except Exception:
        new_map = None
    # Try exact param match by name (with alias normalization)
    param_name = str(cur.get("name", ""))
    learned = None
    canonical = None
    try:
        from shared.aliases import canonical_name  # type: ignore
        canonical = canonical_name(param_name)
    except Exception:
        canonical = param_name
    if mapping and isinstance(mapping.get("params"), list):
        for mp in mapping["params"]:
            mpn = str(mp.get("name", ""))
            if mpn.lower() == param_name.lower() or mpn.lower() == str(canonical or "").lower():
                learned = mp
                break

    # Determine target
    target_y = None
    label = None
    if body.target_display:
        y = _parse_target_display(body.target_display)
        if y is not None:
            target_y = y
        else:
            label = body.target_display.strip()
    elif body.target_value is not None:
        target_y = float(body.target_value)

    # Relative mode: interpret numeric as delta in display units
    if (body.mode or "absolute").lower() == "relative":
        try:
            cur_disp = str(cur.get("display_value", ""))
            cur_num = _parse_target_display(cur_disp)
            if cur_num is not None and target_y is not None:
                target_y = cur_num + float(target_y)
        except Exception:
            pass

# param_by_name logic removed (moved to server.api.ops)

        # NEW PATH: Use new_map.grouping if available
        if new_map and isinstance(new_map.get("grouping"), dict):
            grp = new_map.get("grouping") or {}
            skip_list = [str(x).lower() for x in (grp.get("skip_auto_enable") or [])]

            # Check if this param is a dependent
            deps_map = grp.get("dependents") or {}
            for dep_name, master_ref in deps_map.items():
                if str(dep_name).lower() == param_name.lower():
                    # Parse master_ref which can be "MasterName" or dict with name/active_when
                    if isinstance(master_ref, dict):
                        master_name = str(master_ref.get("name", ""))
                        desired_val = master_ref.get("active_when")
                    else:
                        master_name = str(master_ref)

                    # Check if this master should skip auto-enable
                    if master_name and any(master_name.lower() == s or s in master_name.lower() for s in skip_list):
                        skip_auto = True
                    break

        # LEGACY PATH: Use old learned mapping if new_map didn't provide grouping
        elif learned:
            role = (learned.get("role") or "").lower()
            gname = (learned.get("group") or "").lower()
            if role == "dependent" and gname not in ("global", "output"):
                # Load grouping rules for this device to determine the correct master
                dname = (mapping.get("device_name") or "").lower()
                PLC = get_param_learn_config()
                grp = PLC.get("grouping", {}) or {}
                match_key = None
                for key in grp.keys():
                    kl = str(key).lower()
                    if kl == "default":
                        continue
                    if kl in dname:
                        match_key = key
                        break
                rules = grp.get(match_key or "default") or {}
                # Respect per-device skip list (e.g., Freeze On)
                skip_list = [str(x).lower() for x in (rules.get("skip_auto_enable") or [])]
                if any(s in param_name.lower() for s in skip_list) or ("freeze" in param_name.lower()):
                    skip_auto = True

                if not skip_auto:
                    # First preference: config dependents mapping (exact or case-insensitive)
                    deps_map = rules.get("dependents") or {}
                    for dn, mn in deps_map.items():
                        if str(dn).lower() == param_name.lower():
                            master_name = str(mn)
                            break
                    # If master name uses alternatives (A|B|C), choose the first available in current params
                    if master_name and "|" in master_name:
                        alts = [s.strip() for s in master_name.split("|") if s.strip()]
                        chosen = None
                        for alt in alts:
                            if any(str(pp.get("name","" )).lower() == alt.lower() for pp in p_list):
                                chosen = alt
                                break
                        master_name = chosen or alts[0]

                    # Fallback: infer from stored groups metadata
                    if not master_name:
                        groups = (mapping.get("groups") or []) if mapping else []
                        for g in groups:
                            deps = [str(d.get("name","")) for d in (g.get("dependents") or [])]
                            if any(param_name.lower() == dn.lower() for dn in deps):
                                mref = g.get("master") or {}
                                master_name = str(mref.get("name")) if mref else None
                                break
                    # Last resort: construct "<Base> On" switch
                    if not master_name and " " in param_name:
                        master_name = param_name.rsplit(" ", 1)[0] + " On"

                    # Use per-dependent desired master value when provided
                    dm = rules.get("dependent_master_values") or {}
                    for k, v in dm.items():
                        if str(k).lower() == param_name.lower():
                            try:
                                desired_val = float(v)
                            except Exception:
                                desired_val = None
                            break

        # Actually enable the master if we found one
        if master_name and not skip_auto:
            for p in p_list:
                if str(p.get("name","")) .lower()== master_name.lower():
                    master_idx = int(p.get("index", 0))
                    mmin = float(p.get("min", 0.0)); mmax = float(p.get("max", 1.0))
                    # Binary toggles usually 0..1; prefer explicit desired_val else max/1.0
                    mval = desired_val if desired_val is not None else (mmax if mmax >= 1.0 else 1.0)
                    udp_request({"op": "set_return_device_param", "return_index": ri, "device_index": di, "param_index": master_idx, "value": float(mval)}, timeout=0.8)
                    break
    except Exception:
        pass

    # Compute candidate value in [vmin..vmax]
    x = vmin
    # Helper for binary/toggle mapping
    def _is_binary(ln: Optional[dict]) -> bool:
        if not ln:
            return False
        if str(ln.get("control_type","")) == "binary":
            return True
        # If learned shows two or fewer label samples, treat as binary
        labs = list({str(s.get("display","")) for s in (ln.get("samples") or []) if s.get("display") is not None})
        return len(labs) <= 2

    # Prefer new mapping for label/fit inversion when available
    pm_entry = None
    try:
        if new_map and isinstance(new_map.get("params_meta"), list):
            for pme in new_map["params_meta"]:
                if str(pme.get("name", "")).lower() == param_name.lower():
                    pm_entry = pme
                    break
    except Exception:
        pm_entry = None

    # For quantized params with numeric string labels (e.g., "0.0", "1.0"),
    # treat numeric target_y as a label lookup instead of a fit inversion
    if target_y is not None and not label and pm_entry:
        if str(pm_entry.get("control_type", "")).lower() == "quantized":
            lm = pm_entry.get("label_map") or {}
            # Check if this label_map has numeric string keys
            numeric_key_found = False
            for k in lm.keys():
                try:
                    float(str(k))
                    numeric_key_found = True
                    break
                except:
                    pass
            # If so, treat target_y as a label string
            if numeric_key_found:
                label = str(target_y) if target_y == int(target_y) else f"{target_y:.1f}"
                target_y = None

    # Handle explicit label via new mapping label_map
    handled_label = False
    if label and pm_entry:
        lm = pm_entry.get("label_map") or {}
        # label_map format: {"0": "Clean", "1": "Boost", ...} (number → label)
        for k, v in lm.items():
            try:
                if str(v).strip().lower() == label.lower():
                    x = max(vmin, min(vmax, float(k)))
                    handled_label = True
                    break
            except Exception:
                continue
        if not handled_label and str(pm_entry.get("control_type", "")).lower() == "binary":
            l = label.strip().lower()
            on_words = {"on","enable","enabled","true","1","yes"}
            off_words = {"off","disable","disabled","false","0","no"}
            if l in on_words:
                x = vmax if vmax >= 1.0 else 1.0
                handled_label = True
            elif l in off_words:
                x = vmin if vmin <= 0.0 else 0.0
                handled_label = True

    # Fallback: explicit label using legacy learned mapping samples
    if label and learned and not handled_label:
        # Try exact label match from samples
        found = False
        for s in learned.get("samples", []) or []:
            if str(s.get("display", "")).strip().lower() == label.lower():
                x = float(s.get("value", vmin))
                found = True
                break
        if not found and _is_binary(learned):
            l = label.strip().lower()
            on_words = {"on","enable","enabled","true","1","yes"}
            off_words = {"off","disable","disabled","false","0","no"}
            if l in on_words:
                x = vmax
            elif l in off_words:
                x = vmin
            else:
                # If label_map is present, try keys like "1.0"/"0.0"
                lm = learned.get("label_map") or {}
                for k, v in lm.items():
                    if str(k).strip().lower() == l:
                        x = float(v)
                        found = True
                        break
    elif target_y is not None and pm_entry and isinstance(pm_entry.get("fit"), dict):
        # Numeric target via new mapping fit inversion
        try:
            x = _invert_fit_to_value(pm_entry.get("fit") or {}, float(target_y), vmin, vmax)
        except Exception:
            pass
    elif target_y is not None and learned:
        # Use shared conversion for display->normalized when mapping is available
        try:
            from shared.param_convert import to_normalized  # type: ignore
            x = float(to_normalized(target_y, learned))
        except Exception:
            fit = learned.get("fit")
            if fit:
                x = _invert_fit_to_value(fit, target_y, vmin, vmax)
            else:
                # fallback: nearest sample
                best = None; bestd = 1e9
                for s in learned.get("samples", []) or []:
                    dy = s.get("display_num")
                    if dy is None: continue
                    d = abs(float(dy) - target_y)
                    if d < bestd:
                        bestd = d; best = s
                if best:
                    x = float(best.get("value", vmin))
        # If this is effectively binary, snap to edges based on threshold
        if _is_binary(learned):
            x = vmax if float(target_y) >= 0.5 else vmin

    # Send set + refine steps (up to 2)
    udp_request({"op": "set_return_device_param", "return_index": ri, "device_index": di, "param_index": pi, "value": float(x)}, timeout=1.0)
    # Readback
    rb = udp_request({"op": "get_return_device_params", "return_index": ri, "device_index": di}, timeout=1.0)
    rps = ((rb or {}).get("data") or {}).get("params") or []
    newp = next((p for p in rps if int(p.get("index", -1)) == pi), None)
    applied_disp = newp.get("display_value") if newp else None
    # Up to two corrective nudges if continuous and numeric target provided
    try:
        if learned and learned.get("control_type") == "continuous" and target_y is not None and newp is not None:
            fit = learned.get("fit")
            if fit:
                for _ in range(2):
                    actual_num = _parse_target_display(str(applied_disp))
                    if actual_num is None:
                        break
                    err = target_y - actual_num
                    # 2% relative threshold (or 1 unit when near zero)
                    thresh = 0.02 * (abs(target_y) if target_y != 0 else 1.0)
                    if abs(err) <= thresh:
                        break
                    x2 = _invert_fit_to_value(fit, target_y, vmin, vmax)
                    if abs(x2 - x) <= 1e-6:
                        # fallback: nearest sample by display_num
                        best = None; bestd = 1e9
                        for s in learned.get("samples", []) or []:
                            dy = s.get("display_num")
                            if dy is None: continue
                            d = abs(float(dy) - target_y)
                            if d < bestd:
                                bestd = d; best = s
                        if best:
                            x2 = float(best.get("value", vmin))
                        else:
                            # last resort: proportional nudge in x space
                            direction = -1.0 if err < 0 else 1.0  # if actual > target, decrease x
                            step = 0.1 * (vmax - vmin)
                            x2 = max(vmin, min(vmax, x + direction * step))
                    udp_request({"op": "set_return_device_param", "return_index": ri, "device_index": di, "param_index": pi, "value": float(x2)}, timeout=1.0)
                    x = x2
                    rb2 = udp_request({"op": "get_return_device_params", "return_index": ri, "device_index": di}, timeout=1.0)
                    rps2 = ((rb2 or {}).get("data") or {}).get("params") or []
                    newp = next((p for p in rps2 if int(p.get("index", -1)) == pi), None)
                    applied_disp = newp.get("display_value") if newp else applied_disp
            # If still not within threshold, attempt a brief monotonic bisection on x
            actual_num2 = _parse_target_display(str(applied_disp))
            if actual_num2 is not None:
                err2 = target_y - actual_num2
                thresh2 = 0.02 * (abs(target_y) if target_y != 0 else 1.0)
                if abs(err2) > thresh2:
                    lo = vmin; hi = vmax; curx = x
                    # Initialize bounds by nudging one side based on error direction
                    if err2 < 0:  # actual > target -> decrease x
                        hi = curx
                    else:
                        lo = curx
                    for _ in range(8):
                        mid = (lo + hi) / 2.0
                        udp_request({"op": "set_return_device_param", "return_index": ri, "device_index": di, "param_index": pi, "value": float(mid)}, timeout=1.0)
                        rb3 = udp_request({"op": "get_return_device_params", "return_index": ri, "device_index": di}, timeout=1.0)
                        rps3 = ((rb3 or {}).get("data") or {}).get("params") or []
                        newp3 = next((p for p in rps3 if int(p.get("index", -1)) == pi), None)
                        applied_disp = newp3.get("display_value") if newp3 else applied_disp
                        act = _parse_target_display(str(applied_disp))
                        if act is None:
                            break
                        if abs(act - target_y) <= thresh2:
                            x = mid
                            break
                        if act > target_y:
                            hi = mid
                        else:
                            lo = mid
                        x = mid
    except Exception:
        pass
# param_by_name return removed (moved to server.api.ops)


"""
"""/return/device/learn_status moved to server.api.learn"""


"""ops moved to server.api.ops (legacy stubs removed)"""






@app.on_event("startup")
async def _ableton_startup_listener() -> None:
    start_ableton_event_listener()
    schedule_live_index_tasks()
