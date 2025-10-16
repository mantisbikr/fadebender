from __future__ import annotations

from typing import Any, Dict, Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from server.services.ableton_client import request_op
from server.core.deps import get_store
from server.services.mapping_utils import make_device_signature
import math
import re as _re
from server.volume_utils import db_to_live_float, db_to_live_float_send


router = APIRouter()


Domain = Literal["track", "return", "master", "device", "transport"]


class CanonicalIntent(BaseModel):
    domain: Domain = Field(..., description="Scope: track|return|master|device|transport")
    action: Literal["set"] = "set"

    # Targets (one of):
    track_index: Optional[int] = None
    return_index: Optional[int] = None      # numeric index (0-based) OR
    return_ref: Optional[str] = None        # letter reference: "A", "B", "C" (preferred for user-facing API)
    device_index: Optional[int] = None      # device on track or return (depending on which index is present)

    # Field/parameter selection
    field: Optional[str] = None             # mixer field: volume|pan|mute|solo|cue|tempo|send
    send_index: Optional[int] = None        # numeric index (0-based) OR
    send_ref: Optional[str] = None          # letter reference: "A", "B", "C" (preferred for user-facing API)
    param_index: Optional[int] = None       # device param index (preferred)
    param_ref: Optional[str] = None         # device param lookup by name (contains match)

    # Value + unit (absolute only in v1)
    value: Optional[float] = None
    unit: Optional[str] = None             # db|percent|normalized|ms|hz|on|off
    # For device params: accept display strings (e.g., "245 ms", "5.0 kHz", "High")
    display: Optional[str] = None

    # Options
    dry_run: bool = False
    clamp: bool = True


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _letter_to_index(letter: str) -> int:
    """Convert letter reference to 0-based index.

    Examples:
        "A" or "a" → 0
        "B" or "b" → 1
        "C" or "c" → 2

    Raises HTTPException if invalid.
    """
    letter = letter.strip().upper()
    if len(letter) != 1 or not letter.isalpha():
        raise HTTPException(400, f"invalid_letter_reference:{letter}")
    return ord(letter) - ord('A')


def _resolve_return_index(intent: CanonicalIntent) -> int:
    """Resolve return index from either return_index or return_ref.

    Prefers return_ref if provided, falls back to return_index.
    Returns 0-based index for Live API.
    """
    if intent.return_ref is not None:
        return _letter_to_index(intent.return_ref)
    if intent.return_index is not None:
        idx = int(intent.return_index)
        if idx < 0:
            raise HTTPException(400, "return_index_must_be_at_least_0")
        return idx
    raise HTTPException(400, "return_index_or_return_ref_required")


def _resolve_send_index(intent: CanonicalIntent) -> int:
    """Resolve send index from either send_index or send_ref.

    Prefers send_ref if provided, falls back to send_index.
    Returns 0-based index for Live API.
    """
    if intent.send_ref is not None:
        return _letter_to_index(intent.send_ref)
    if intent.send_index is not None:
        idx = int(intent.send_index)
        if idx < 0:
            raise HTTPException(400, "send_index_must_be_at_least_0")
        return idx
    raise HTTPException(400, "send_index_or_send_ref_required")


def _resolve_param(params: list[dict], param_index: Optional[int], param_ref: Optional[str]) -> dict:
    if isinstance(param_index, int):
        for p in params:
            if int(p.get("index", -1)) == int(param_index):
                return p
        raise HTTPException(404, "param_not_found")
    if param_ref:
        pref = param_ref.strip().lower()
        cand = [p for p in params if pref in str(p.get("name", "")).lower()]
        if len(cand) == 1:
            return cand[0]
        if len(cand) == 0:
            raise HTTPException(404, "param_not_found")
        raise HTTPException(409, "param_ambiguous")
    raise HTTPException(400, "param_selector_required")


def _auto_enable_master_if_needed(params: list[dict], target_param_name: str) -> Optional[dict]:
    """Heuristic: if a related "X On" exists and is off, return that toggle param dict.

    This is a simple name-based approach to help users who set a dependent first.
    More robust, mapping-driven grouping can replace this later.
    """
    name = (target_param_name or "").lower()
    candidates = []
    # Common sections whose dependents often require an On toggle
    keys = [
        ("chorus", "chorus on"),
        ("er spin", "er spin on"),
        ("lowshelf", "low shelf on"),
        ("low shelf", "low shelf on"),
        ("hishelf", "hi shelf on"),
        ("high shelf", "hi shelf on"),
        ("hifilter", "hifilter on"),
        ("hi filter", "hifilter on"),
        ("freeze", "freeze on"),
    ]
    for k, toggle in keys:
        if k in name:
            candidates.append(toggle)
    if not candidates:
        return None
    # find first toggle present and currently off
    for p in params:
        pname = str(p.get("name", "")).lower()
        if any(t in pname for t in candidates):
            try:
                # Off if value ~ 0.0
                val = float(p.get("value", 0.0))
                vmin = float(p.get("min", 0.0)); vmax = float(p.get("max", 1.0))
                is_off = abs(val - vmin) <= 1e-6
                if is_off:
                    return p
            except Exception:
                continue
    return None


def _parse_target_display(s: str) -> Optional[float]:
    try:
        m = _re.search(r"-?\d+(?:\.\d+)?", str(s))
        if not m:
            return None
        return float(m.group(0))
    except Exception:
        return None


def _invert_fit_to_value(fit: dict, target_y: float, vmin: float, vmax: float) -> float:
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


def _convert_unit_value(value: float, src: Optional[str], dest: Optional[str]) -> float:
    """Convert a numeric display value between basic units when needed.

    Supported conversions: ms<->s, Hz<->kHz, pass-through for percent.
    Unknown pairs return the original value.
    """
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


def _get_mixer_display_range(field: str):
    """Get display range (min, max) for a mixer field from Firestore mapping.

    Args:
        field: Mixer field name ("pan", "volume", etc.)

    Returns:
        Tuple of (display_min, display_max), or default fallback values
    """
    try:
        store = get_store()
        if not store.enabled:
            return (-50.0, 50.0) if field == "pan" else (0.0, 1.0)

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
    """Resolve mixer parameter display value to normalized value using Firestore mappings.

    Args:
        field: Mixer field name ("pan", "volume", etc.)
        display: Display value string (e.g., "25L", "center", "unity")

    Returns:
        Normalized value or None if not found
    """
    try:
        store = get_store()
        if not store.enabled:
            return None

        mapping = store.get_mixer_param_mapping(field)
        if not mapping:
            return None

        presets = mapping.get("display_value_presets", {})
        if not isinstance(presets, dict):
            return None

        # Normalize the display string for lookup
        display_normalized = display.strip().lower()

        # Direct lookup
        if display_normalized in presets:
            return float(presets[display_normalized])

        # Try numeric parsing for display range values
        # For pan: use the display_range from mapping
        if field == "pan":
            num = _parse_target_display(display)
            if num is not None:
                # Get display range from Firestore mapping
                display_min, display_max = _get_mixer_display_range("pan")
                display_scale = max(abs(display_min), abs(display_max))
                # Convert display value to normalized (-1.0 to 1.0)
                return _clamp(float(num) / display_scale, -1.0, 1.0)

        return None
    except Exception:
        return None


@router.post("/intent/execute")
def execute_intent(intent: CanonicalIntent) -> Dict[str, Any]:
    d = intent.domain
    field = intent.field or ""
    # Track mixer
    if d == "track" and field in ("volume", "pan", "mute", "solo"):
        if intent.track_index is None:
            raise HTTPException(400, "track_index_required")
        track_idx = int(intent.track_index)
        # Tracks are 1-based in Live API (Track 1 = index 1)
        if track_idx < 1:
            raise HTTPException(400, "track_index_must_be_at_least_1")
        # Value handling
        v = float(intent.value if intent.value is not None else 0.0)

        # Check for display value (string presets like "center", "25L", "unity")
        if intent.display and field in ("pan", "volume"):
            resolved = _resolve_mixer_display_value(field, intent.display)
            if resolved is not None:
                v = resolved
            # If display resolves to None, fall through to normal value handling

        if field == "volume":
            if (intent.unit or "").lower() in ("db", "dB".lower()):
                v = db_to_live_float(v)
            elif (intent.unit or "").lower() in ("percent", "%"):
                v = v / 100.0
            v = _clamp(v, 0.0, 1.0) if intent.clamp else v
        elif field == "pan":
            # Pan: If value is outside [-1, 1], treat as display value and convert
            # Get display range from Firestore mapping (e.g., -50 to 50)
            if abs(v) > 1.0:
                # Display value: convert using mapping range
                display_min, display_max = _get_mixer_display_range("pan")
                display_scale = max(abs(display_min), abs(display_max))
                v = _clamp(v, display_min, display_max) / display_scale
            else:
                # Already normalized -1.0 to 1.0
                v = _clamp(v, -1.0, 1.0) if intent.clamp else v
        elif field in ("mute", "solo"):
            # Treat >0.5 as on
            v = 1.0 if v >= 0.5 else 0.0
        if intent.dry_run:
            return {"ok": True, "preview": {"op": "set_mixer", "track_index": track_idx, "field": field, "value": v}}
        resp = request_op("set_mixer", timeout=1.0, track_index=track_idx, field=str(field), value=float(v))
        if not resp:
            raise HTTPException(504, "no_reply")
        return resp

    # Track sends
    if d == "track" and field == "send":
        if intent.track_index is None:
            raise HTTPException(400, "track_index_required")
        if intent.send_index is None and intent.send_ref is None:
            raise HTTPException(400, "send_index_or_send_ref_required")
        track_idx = int(intent.track_index)
        send_idx = _resolve_send_index(intent)
        # Tracks are 1-based, but sends are 0-based in Live API
        if track_idx < 1:
            raise HTTPException(400, "track_index_must_be_at_least_1")
        v = float(intent.value if intent.value is not None else 0.0)
        # Add dB support for sends (range: -60dB to 0dB)
        if (intent.unit or "").lower() in ("db", "dB".lower()):
            v = db_to_live_float_send(v)
        elif (intent.unit or "").lower() in ("percent", "%"):
            v = v / 100.0
        v = _clamp(v, 0.0, 1.0) if intent.clamp else v
        if intent.dry_run:
            return {"ok": True, "preview": {"op": "set_send", "track_index": track_idx, "send_index": send_idx, "value": v}}
        resp = request_op("set_send", timeout=1.0, track_index=track_idx, send_index=send_idx, value=float(v))
        if not resp:
            raise HTTPException(504, "no_reply")
        return resp

    # Return mixer
    if d == "return" and field in ("volume", "pan", "mute", "solo"):
        return_idx = _resolve_return_index(intent)
        v = float(intent.value if intent.value is not None else 0.0)

        # Check for display value (string presets like "center", "25L", "unity")
        if intent.display and field in ("pan", "volume"):
            resolved = _resolve_mixer_display_value(field, intent.display)
            if resolved is not None:
                v = resolved

        if field == "volume":
            # Add dB support for return volume (range: -60dB to +6dB)
            if (intent.unit or "").lower() in ("db", "dB".lower()):
                v = db_to_live_float(v)
            elif (intent.unit or "").lower() in ("percent", "%"):
                v = v / 100.0
            v = _clamp(v, 0.0, 1.0) if intent.clamp else v
        elif field == "pan":
            # Pan: If value is outside [-1, 1], treat as display value and convert
            # Get display range from Firestore mapping (e.g., -50 to 50)
            if abs(v) > 1.0:
                # Display value: convert using mapping range
                display_min, display_max = _get_mixer_display_range("pan")
                display_scale = max(abs(display_min), abs(display_max))
                v = _clamp(v, display_min, display_max) / display_scale
            else:
                # Already normalized -1.0 to 1.0
                v = _clamp(v, -1.0, 1.0) if intent.clamp else v
        elif field in ("mute", "solo"):
            v = 1.0 if v >= 0.5 else 0.0
        if intent.dry_run:
            return {"ok": True, "preview": {"op": "set_return_mixer", "return_index": return_idx, "field": field, "value": v}}
        resp = request_op("set_return_mixer", timeout=1.0, return_index=return_idx, field=str(field), value=float(v))
        if not resp:
            raise HTTPException(504, "no_reply")
        return resp

    # Return sends
    if d == "return" and field == "send":
        return_idx = _resolve_return_index(intent)
        send_idx = _resolve_send_index(intent)
        v = float(intent.value if intent.value is not None else 0.0)
        # Add dB support for return sends (range: -60dB to 0dB)
        if (intent.unit or "").lower() in ("db", "dB".lower()):
            v = db_to_live_float_send(v)
        elif (intent.unit or "").lower() in ("percent", "%"):
            v = v / 100.0
        v = _clamp(v, 0.0, 1.0) if intent.clamp else v
        if intent.dry_run:
            return {"ok": True, "preview": {"op": "set_return_send", "return_index": return_idx, "send_index": send_idx, "value": v}}
        resp = request_op("set_return_send", timeout=1.0, return_index=return_idx, send_index=send_idx, value=float(v))
        if not resp:
            raise HTTPException(504, "no_reply")
        return resp

    # Master mixer (subset)
    if d == "master" and field in ("volume", "pan", "cue"):
        v = float(intent.value if intent.value is not None else 0.0)

        # Check for display value (string presets like "center", "25L", "unity")
        if intent.display and field in ("pan", "volume", "cue"):
            resolved = _resolve_mixer_display_value(field, intent.display)
            if resolved is not None:
                v = resolved

        if field == "volume":
            if (intent.unit or "").lower() in ("db", "dB".lower()):
                v = db_to_live_float(v)
            elif (intent.unit or "").lower() in ("percent", "%"):
                v = v / 100.0
            v = _clamp(v, 0.0, 1.0) if intent.clamp else v
        elif field == "cue":
            # Cue volume: only supports dB (no percent)
            if (intent.unit or "").lower() in ("db", "dB".lower()):
                v = db_to_live_float(v)
            # No else - if no unit specified, treat as error (user must specify dB)
            elif not intent.display:
                raise HTTPException(400, "cue_requires_db_unit_or_display_value")
            v = _clamp(v, 0.0, 1.0) if intent.clamp else v
        elif field == "pan":
            # Pan: If value is outside [-1, 1], treat as display value and convert
            # Get display range from Firestore mapping (e.g., -50 to 50)
            if abs(v) > 1.0:
                # Display value: convert using mapping range
                display_min, display_max = _get_mixer_display_range("pan")
                display_scale = max(abs(display_min), abs(display_max))
                v = _clamp(v, display_min, display_max) / display_scale
            else:
                # Already normalized -1.0 to 1.0
                v = _clamp(v, -1.0, 1.0) if intent.clamp else v
        if intent.dry_run:
            return {"ok": True, "preview": {"op": "set_master_mixer", "field": field, "value": v}}
        resp = request_op("set_master_mixer", timeout=1.0, field=str(field), value=float(v))
        if not resp:
            raise HTTPException(504, "no_reply")
        return resp

    # Device parameter (return device)
    if d == "device" and (intent.return_index is not None or intent.return_ref is not None) and intent.device_index is not None:
        ri = _resolve_return_index(intent)
        di = int(intent.device_index)
        # Read params to get min/max, resolve selection
        pr = request_op("get_return_device_params", timeout=1.2, return_index=ri, device_index=di)
        params = ((pr or {}).get("data") or {}).get("params") or []
        if not params:
            raise HTTPException(404, "params_not_found")
        sel = _resolve_param(params, intent.param_index, intent.param_ref)
        vmin = float(sel.get("min", 0.0)); vmax = float(sel.get("max", 1.0))
        x = float(intent.value if intent.value is not None else vmin)
        # If display provided, try mapping via params_meta fit/labels; fallback to refine if not dry_run
        used_display = False
        unit_lc = (intent.unit or "").lower().strip()
        target_display = intent.display if intent.display is not None else (str(intent.value) if unit_lc == "display" and intent.value is not None else None)
        # Treat common display units as display-mode if value provided
        if target_display is None and unit_lc in ("ms", "s", "hz", "khz", "db", "%", "percent", "on", "off") and intent.value is not None:
            target_display = str(intent.value)
        if target_display is not None:
            used_display = True
            # Compute signature and fetch mapping
            store = get_store()
            devs = request_op("get_return_devices", timeout=1.0, return_index=ri)
            devices = ((devs or {}).get("data") or {}).get("devices") or []
            dname = next((str(d.get("name", "")) for d in devices if int(d.get("index", -1)) == di), f"Device {di}")
            sig = make_device_signature(dname, params)
            mapping = None
            try:
                mapping = store.get_device_mapping(sig) if store.enabled else None
            except Exception:
                mapping = None
            pm = None
            if mapping:
                pm = next((pme for pme in (mapping.get("params_meta") or []) if str(pme.get("name", "")).lower() == str(sel.get("name", "")).lower()), None)
            ty = _parse_target_display(target_display)
            # Label resolution (non-numeric)
            if pm and isinstance(pm.get("label_map"), dict) and ty is None:
                lm = pm.get("label_map") or {}
                lnorm = target_display.strip().lower()
                if lnorm in {"on", "enable", "enabled", "true", "1", "yes"}:
                    x = vmax
                elif lnorm in {"off", "disable", "disabled", "false", "0", "no"}:
                    x = vmin
                else:
                    for k, v in lm.items():
                        if str(k).strip().lower() == lnorm:
                            x = float(v)
                            break
            # Numeric display
            elif ty is not None:
                if pm and isinstance(pm.get("fit"), dict):
                    # Align input numeric with params_meta unit if provided
                    pm_unit = (pm.get("unit") or "").strip().lower()
                    ty_aligned = _convert_unit_value(float(ty), unit_lc or pm_unit, pm_unit)
                    x = _invert_fit_to_value(pm.get("fit") or {}, float(ty_aligned), vmin, vmax)
                else:
                    # No fit; if dry_run, preview only
                    if intent.dry_run:
                        pv = {
                            "note": "approx_preview_no_fit",
                            "target_display": target_display,
                            "value_range": [vmin, vmax],
                        }
                        return {"ok": True, "preview": pv}
                    # Try a bounded bisection using live readbacks
                    # Probe ends for direction
                    try:
                        # Set to min
                        request_op("set_return_device_param", timeout=1.0, return_index=ri, device_index=di, param_index=int(sel.get("index", 0)), value=float(vmin))
                        rb0 = request_op("get_return_device_params", timeout=1.0, return_index=ri, device_index=di)
                        p0s = ((rb0 or {}).get("data") or {}).get("params") or []
                        p0 = next((p for p in p0s if int(p.get("index", -1)) == int(sel.get("index", 0))), None)
                        d0 = _parse_target_display(str((p0 or {}).get("display_value", "")))
                        # Set to max
                        request_op("set_return_device_param", timeout=1.0, return_index=ri, device_index=di, param_index=int(sel.get("index", 0)), value=float(vmax))
                        rb1 = request_op("get_return_device_params", timeout=1.0, return_index=ri, device_index=di)
                        p1s = ((rb1 or {}).get("data") or {}).get("params") or []
                        p1 = next((p for p in p1s if int(p.get("index", -1)) == int(sel.get("index", 0))), None)
                        d1 = _parse_target_display(str((p1 or {}).get("display_value", "")))
                        if d0 is not None and d1 is not None:
                            lo = vmin; hi = vmax; target = float(ty)
                            # Ensure bounds order based on monotonicity
                            inc = d1 > d0
                            for _ in range(8):
                                mid = (lo + hi) / 2.0
                                request_op("set_return_device_param", timeout=1.0, return_index=ri, device_index=di, param_index=int(sel.get("index", 0)), value=float(mid))
                                rbm = request_op("get_return_device_params", timeout=1.0, return_index=ri, device_index=di)
                                pms = ((rbm or {}).get("data") or {}).get("params") or []
                                pmid = next((p for p in pms if int(p.get("index", -1)) == int(sel.get("index", 0))), None)
                                dmid = _parse_target_display(str((pmid or {}).get("display_value", "")))
                                if dmid is None:
                                    break
                                err = abs(dmid - target)
                                thresh = 0.02 * (abs(target) if target != 0 else 1.0)
                                if err <= thresh:
                                    x = mid
                                    break
                                if (dmid < target and inc) or (dmid > target and not inc):
                                    lo = mid
                                else:
                                    hi = mid
                            else:
                                x = (lo + hi) / 2.0
                    except Exception:
                        pass
        # Basic unit handling for device when numeric value passed: if mapping exists and unit is display-like, use fit; else percent scales within [vmin,vmax]
        if not used_display and unit_lc in ("percent", "%", "ms", "s", "hz", "khz"):
            if pm and isinstance(pm.get("fit"), dict) and unit_lc not in ("percent", "%"):
                pm_unit = (pm.get("unit") or "").strip().lower()
                ty2 = _convert_unit_value(float(x), unit_lc, pm_unit)
                x = _invert_fit_to_value(pm.get("fit") or {}, float(ty2), vmin, vmax)
            elif unit_lc in ("percent", "%"):
                x = vmin + (vmax - vmin) * _clamp(x, 0.0, 100.0) / 100.0
        # Optional dependency enable
        master_toggle = _auto_enable_master_if_needed(params, str(sel.get("name", "")))
        preview: Dict[str, Any] = {"op": "set_return_device_param", "return_index": ri, "device_index": di, "param_index": int(sel.get("index", 0)), "value": float(_clamp(x, vmin, vmax) if intent.clamp else x)}
        if master_toggle is not None:
            preview["pre"] = {
                "op": "set_return_device_param",
                "return_index": ri,
                "device_index": di,
                "param_index": int(master_toggle.get("index", 0)),
                "value": float(master_toggle.get("max", 1.0)),
                "note": "auto_enable_master"
            }
        if intent.dry_run:
            return {"ok": True, "preview": preview}
        # Apply pre toggle if any
        if preview.get("pre"):
            pre = preview["pre"]
            request_op("set_return_device_param", timeout=1.0, **{k: pre[k] for k in ("return_index","device_index","param_index","value")})
        resp = request_op("set_return_device_param", timeout=1.0, return_index=ri, device_index=di, param_index=int(sel.get("index", 0)), value=float(preview["value"]))
        if not resp:
            raise HTTPException(504, "no_reply")
        return resp

    # Device parameter (track device)
    if d == "device" and intent.track_index is not None and intent.device_index is not None:
        ti = int(intent.track_index)
        di = int(intent.device_index)
        pr = request_op("get_track_device_params", timeout=1.2, track_index=ti, device_index=di)
        params = ((pr or {}).get("data") or {}).get("params") or []
        if not params:
            raise HTTPException(404, "params_not_found")
        sel = _resolve_param(params, intent.param_index, intent.param_ref)
        vmin = float(sel.get("min", 0.0)); vmax = float(sel.get("max", 1.0))
        x = float(intent.value if intent.value is not None else vmin)
        used_display = False
        target_display = intent.display if intent.display is not None else (str(intent.value) if (intent.unit or "").lower() == "display" and intent.value is not None else None)
        if target_display is not None:
            used_display = True
            # Mapping for track devices is not yet persisted; attempt readback refine only
            if intent.dry_run:
                return {"ok": True, "preview": {"note": "approx_preview_no_fit", "target_display": target_display, "value_range": [vmin, vmax]}}
            try:
                # Probe ends
                request_op("set_device_param", timeout=1.0, track_index=ti, device_index=di, param_index=int(sel.get("index", 0)), value=float(vmin))
                rb0 = request_op("get_track_device_params", timeout=1.0, track_index=ti, device_index=di)
                p0s = ((rb0 or {}).get("data") or {}).get("params") or []
                p0 = next((p for p in p0s if int(p.get("index", -1)) == int(sel.get("index", 0))), None)
                d0 = _parse_target_display(str((p0 or {}).get("display_value", "")))
                request_op("set_device_param", timeout=1.0, track_index=ti, device_index=di, param_index=int(sel.get("index", 0)), value=float(vmax))
                rb1 = request_op("get_track_device_params", timeout=1.0, track_index=ti, device_index=di)
                p1s = ((rb1 or {}).get("data") or {}).get("params") or []
                p1 = next((p for p in p1s if int(p.get("index", -1)) == int(sel.get("index", 0))), None)
                d1 = _parse_target_display(str((p1 or {}).get("display_value", "")))
                ty = _parse_target_display(target_display)
                if d0 is not None and d1 is not None and ty is not None:
                    lo = vmin; hi = vmax; target = float(ty); inc = d1 > d0
                    for _ in range(8):
                        mid = (lo + hi) / 2.0
                        request_op("set_device_param", timeout=1.0, track_index=ti, device_index=di, param_index=int(sel.get("index", 0)), value=float(mid))
                        rbm = request_op("get_track_device_params", timeout=1.0, track_index=ti, device_index=di)
                        pms = ((rbm or {}).get("data") or {}).get("params") or []
                        pmid = next((p for p in pms if int(p.get("index", -1)) == int(sel.get("index", 0))), None)
                        dmid = _parse_target_display(str((pmid or {}).get("display_value", "")))
                        if dmid is None:
                            break
                        err = abs(dmid - target)
                        thresh = 0.02 * (abs(target) if target != 0 else 1.0)
                        if err <= thresh:
                            x = mid
                            break
                        if (dmid < target and inc) or (dmid > target and not inc):
                            lo = mid
                        else:
                            hi = mid
                    else:
                        x = (lo + hi) / 2.0
            except Exception:
                pass
        if not used_display and (intent.unit or "").lower() in ("percent", "%"):
            x = vmin + (vmax - vmin) * _clamp(x, 0.0, 100.0) / 100.0
        # Optional dependency enable (heuristic) for track devices
        master_toggle = _auto_enable_master_if_needed(params, str(sel.get("name", "")))
        preview = {"op": "set_device_param", "track_index": ti, "device_index": di, "param_index": int(sel.get("index", 0)), "value": float(_clamp(x, vmin, vmax) if intent.clamp else x)}
        if master_toggle is not None:
            preview["pre"] = {
                "op": "set_device_param",
                "track_index": ti,
                "device_index": di,
                "param_index": int(master_toggle.get("index", 0)),
                "value": float(master_toggle.get("max", 1.0)),
                "note": "auto_enable_master"
            }
        if intent.dry_run:
            return {"ok": True, "preview": preview}
        if preview.get("pre"):
            pre = preview["pre"]
            request_op("set_device_param", timeout=1.0, **{k: pre[k] for k in ("track_index","device_index","param_index","value")})
        resp = request_op("set_device_param", timeout=1.0, track_index=ti, device_index=di, param_index=int(sel.get("index", 0)), value=float(preview["value"]))
        if not resp:
            raise HTTPException(504, "no_reply")
        return resp

    raise HTTPException(400, "unsupported_intent")
