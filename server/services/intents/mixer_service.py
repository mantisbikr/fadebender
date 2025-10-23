from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from fastapi import HTTPException

from server.config.app_config import get_feature_flags
from server.services.ableton_client import request_op
from server.core.deps import get_value_registry
from server.models.intents_api import CanonicalIntent
from server.volume_utils import (
    db_to_live_float,
    live_float_to_db,
)
from server.services.intents.utils.mixer import (
    clamp,
    get_mixer_param_meta,
    get_mixer_display_range,
    resolve_mixer_display_value,
)


def set_track_mixer(intent: CanonicalIntent) -> Dict[str, Any]:
    if intent.track_index is None:
        raise HTTPException(400, "track_index_required")
    track_idx = int(intent.track_index)
    if track_idx < 1:
        raise HTTPException(400, "track_index_must_be_at_least_1")

    # Validate track exists (best effort)
    try:
        ov = request_op("get_overview", timeout=1.0) or {}
        tracks = ((ov.get("data") or ov) if isinstance(ov, dict) else ov).get("tracks", [])
        if tracks and track_idx > len(tracks):
            names = ", ".join([str(t.get("name", f"Track {t.get('index')}")) for t in tracks])
            raise HTTPException(404, f"track_out_of_range:{track_idx}; available=1..{len(tracks)}; tracks=[{names}]")
    except HTTPException:
        raise
    except Exception:
        pass

    field = str(intent.field or "")
    v = float(intent.value if intent.value is not None else 0.0)
    display_only_io = bool((get_feature_flags() or {}).get("display_only_io", False))

    # Resolve display inputs
    resolved_from_display = False
    if intent.display and field in ("pan", "volume"):
        resolved = resolve_mixer_display_value(field, intent.display)
        if resolved is not None:
            v = resolved
            resolved_from_display = True

    if field == "volume" and not resolved_from_display:
        if display_only_io and (intent.unit is None) and 0.0 <= v <= 1.0:
            raise HTTPException(400, "normalized_not_allowed_for_volume: provide dB (unit='db') or percent")
        if (intent.unit or "").lower() in ("db", "dB".lower()):
            v = db_to_live_float(v)
        elif (intent.unit or "").lower() in ("percent", "%"):
            v = v / 100.0
        v = clamp(v, 0.0, 1.0) if intent.clamp else v
    elif field == "pan" and not resolved_from_display:
        if display_only_io and (intent.display is None) and -1.0 <= v <= 1.0 and not intent.unit:
            raise HTTPException(400, "normalized_not_allowed_for_pan: provide display like '30L'/'30R'")
        if abs(v) > 1.0:
            display_min, display_max = get_mixer_display_range("pan")
            display_scale = max(abs(display_min), abs(display_max))
            v = clamp(v, display_min, display_max) / display_scale
        else:
            v = clamp(v, -1.0, 1.0) if intent.clamp else v
    elif field in ("mute", "solo"):
        v = 1.0 if v >= 0.5 else 0.0

    if intent.dry_run:
        return {"ok": True, "preview": {"op": "set_mixer", "track_index": track_idx, "field": field, "value": v}}

    resp = request_op("set_mixer", timeout=1.0, track_index=track_idx, field=str(field), value=float(v))
    if not resp:
        raise HTTPException(504, "no_reply")

    # Write-through to ValueRegistry
    try:
        reg = get_value_registry()
        disp = None
        unit = None
        if intent.display and field in ("volume", "pan"):
            disp = intent.display
            unit = intent.unit if field == "volume" else None
        elif field == "volume":
            try:
                disp = f"{live_float_to_db(float(v)):.2f}"
                unit = "dB"
            except Exception:
                pass
        elif field == "pan":
            try:
                display_min, display_max = get_mixer_display_range("pan")
                display_scale = max(abs(display_min), abs(display_max))
                disp = f"{float(v) * display_scale:.2f}"
                unit = None
            except Exception:
                pass
        reg.update_mixer("track", track_idx, field, float(v), disp, unit, source="op")
    except Exception:
        pass

    # Ensure mixer capabilities (track)
    try:
        from server.api.cap_utils import ensure_capabilities  # type: ignore
        resp = ensure_capabilities(resp, domain="track", track_index=track_idx)
    except Exception:
        pass

    return resp


def set_return_mixer(intent: CanonicalIntent) -> Dict[str, Any]:
    from server.services.intents.utils.refs import _letter_to_index as _ltx

    return_idx: Optional[int]
    if intent.return_ref is not None and intent.return_index is None:
        return_idx = _ltx(intent.return_ref)
    else:
        return_idx = int(intent.return_index) if intent.return_index is not None else None

    if return_idx is None:
        raise HTTPException(400, "return_index_or_return_ref_required")

    try:
        rs = request_op("get_return_tracks", timeout=1.0) or {}
        rets = ((rs.get("data") or rs) if isinstance(rs, dict) else rs).get("returns", [])
        if rets and (return_idx < 0 or return_idx >= len(rets)):
            letters = [chr(ord('A') + int(r.get("index", 0))) for r in rets]
            names = ", ".join([f"{letters[i]}:{str(rets[i].get('name',''))}" for i in range(len(rets))])
            raise HTTPException(404, f"return_out_of_range:{return_idx}; available=0..{len(rets)-1} (A..{letters[-1] if letters else 'A'}); returns=[{names}]")
    except HTTPException:
        raise
    except Exception:
        pass

    field = str(intent.field or "")
    v = float(intent.value if intent.value is not None else 0.0)
    display_only_io = bool((get_feature_flags() or {}).get("display_only_io", False))

    # Display resolution
    resolved_from_display = False
    if intent.display and field in ("pan", "volume"):
        resolved = resolve_mixer_display_value(field, intent.display)
        if resolved is not None:
            v = resolved
            resolved_from_display = True

    if field == "volume" and not resolved_from_display:
        if display_only_io and (intent.unit is None) and 0.0 <= v <= 1.0:
            raise HTTPException(400, "normalized_not_allowed_for_volume: provide dB (unit='db') or percent")
        if (intent.unit or "").lower() in ("db", "dB".lower()):
            v = db_to_live_float(v)
        elif (intent.unit or "").lower() in ("percent", "%"):
            v = v / 100.0
        v = clamp(v, 0.0, 1.0) if intent.clamp else v
    elif field == "pan" and not resolved_from_display:
        if display_only_io and (intent.display is None) and -1.0 <= v <= 1.0 and not intent.unit:
            raise HTTPException(400, "normalized_not_allowed_for_pan: provide display like '30L'/'30R'")
        if abs(v) > 1.0:
            display_min, display_max = get_mixer_display_range("pan")
            display_scale = max(abs(display_min), abs(display_max))
            v = clamp(v, display_min, display_max) / display_scale
        else:
            v = clamp(v, -1.0, 1.0) if intent.clamp else v
    elif field in ("mute", "solo"):
        v = 1.0 if v >= 0.5 else 0.0

    if intent.dry_run:
        return {"ok": True, "preview": {"op": "set_return_mixer", "return_index": return_idx, "field": field, "value": v}}

    resp = request_op("set_return_mixer", timeout=1.0, return_index=return_idx, field=str(field), value=float(v))
    if not resp:
        raise HTTPException(504, "no_reply")

    try:
        reg = get_value_registry()
        disp = None
        unit = None
        if intent.display and field in ("volume", "pan"):
            disp = intent.display
            unit = intent.unit if field == "volume" else None
        elif field == "volume":
            try:
                disp = f"{live_float_to_db(float(v)):.2f}"
                unit = "dB"
            except Exception:
                pass
        elif field == "pan":
            try:
                display_min, display_max = get_mixer_display_range("pan")
                display_scale = max(abs(display_min), abs(display_max))
                disp = f"{float(v) * display_scale:.2f}"
                unit = None
            except Exception:
                pass
        reg.update_mixer("return", return_idx, field, float(v), disp, unit, source="op")
    except Exception:
        pass
    # Add a concise summary for chat/UI
    try:
        letter = chr(ord('A') + int(return_idx))
        disp_txt = None
        if field == "volume":
            try:
                disp_txt = f"{live_float_to_db(float(v)):.1f} dB"
            except Exception:
                pass
        elif field == "pan":
            try:
                display_min, display_max = get_mixer_display_range("pan")
                display_scale = max(abs(display_min), abs(display_max))
                disp_txt = f"{float(v) * display_scale:.0f}{'R' if float(v) > 0 else ('L' if float(v) < 0 else 'C')}"
            except Exception:
                pass
        elif field in ("mute", "solo"):
            disp_txt = "On" if float(v) >= 0.5 else "Off"
        if isinstance(resp, dict):
            if disp_txt:
                resp["summary"] = f"Set Return {letter} {field} to {disp_txt}"
            else:
                resp["summary"] = f"Set Return {letter} {field}"
    except Exception:
        pass
    # Ensure return mixer capabilities
    try:
        from server.api.cap_utils import ensure_capabilities  # type: ignore
        resp = ensure_capabilities(resp, domain="return", return_index=return_idx)
    except Exception:
        pass

    return resp
