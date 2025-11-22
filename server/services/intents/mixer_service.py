from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from fastapi import HTTPException

from server.config.app_config import get_feature_flags
from server.services.ableton_client import request_op
from server.core.deps import get_value_registry
from server.models.intents_api import CanonicalIntent
from server.services.intents.utils.mixer import (
    clamp,
    get_mixer_param_meta,
    get_mixer_display_range,
    resolve_mixer_display_value,
    normalize_unit,
    apply_mixer_fit_inverse,
    apply_mixer_fit_forward,
)
from server.services.intents.utils.refs import _resolve_send_index, _resolve_return_index


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
            raise HTTPException(400, "normalized_not_allowed_for_volume: provide display value or percent")
        unit_l = (intent.unit or "").lower()
        if unit_l in ("percent", "%"):
            v = v / 100.0
        else:
            # Use piecewise fit to convert dB -> normalized
            pm = get_mixer_param_meta("track", "volume")
            if pm and pm.get("fit"):
                inv = apply_mixer_fit_inverse(pm, float(v))
                if inv is not None:
                    v = float(inv)
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
            # Use piecewise fit for display
            pm = get_mixer_param_meta("track", "volume")
            if pm and pm.get("fit"):
                dval = apply_mixer_fit_forward(pm, float(v))
                if dval is not None:
                    disp = f"{float(dval):.2f}"
                    unit = "dB"
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

    # Add a concise summary for chat/UI
    try:
        disp_txt = None
        if field == "volume":
            # Use piecewise fit for summary
            pm = get_mixer_param_meta("track", "volume")
            if pm and pm.get("fit"):
                dval = apply_mixer_fit_forward(pm, float(v))
                if dval is not None:
                    disp_txt = f"{float(dval):.1f} dB"
        elif field == "pan":
            try:
                display_min, display_max = get_mixer_display_range("pan")
                display_scale = max(abs(display_min), abs(display_max))
                pan_val = float(v) * display_scale
                # Round to avoid scientific notation for values very close to zero
                if abs(pan_val) < 0.5:
                    disp_txt = "C"
                else:
                    disp_txt = f"{abs(pan_val):.0f}{'R' if pan_val > 0 else 'L'}"
            except Exception:
                pass
        elif field in ("mute", "solo"):
            disp_txt = "On" if float(v) >= 0.5 else "Off"
        if isinstance(resp, dict):
            if disp_txt:
                resp["summary"] = f"Set Track {track_idx} {field} to {disp_txt}"
            else:
                resp["summary"] = f"Set Track {track_idx} {field}"
    except Exception:
        pass

    # Capabilities ref now added centrally in chat_service.py
    return resp


def set_return_mixer(intent: CanonicalIntent) -> Dict[str, Any]:
    return_idx: Optional[int]
    if intent.return_ref is not None and intent.return_index is None:
        return_idx = _resolve_return_index(None, intent.return_ref)
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
        unit_l = (intent.unit or "").lower()
        if unit_l in ("percent", "%"):
            v = v / 100.0
        else:
            # Use piecewise fit to convert dB -> normalized
            pm = get_mixer_param_meta("return", "volume")
            if pm and pm.get("fit"):
                inv = apply_mixer_fit_inverse(pm, float(v))
                if inv is not None:
                    v = float(inv)
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
            pm = get_mixer_param_meta("return", "volume")
            if pm and pm.get("fit"):
                dval = apply_mixer_fit_forward(pm, float(v))
                if dval is not None:
                    disp = f"{float(dval):.2f}"
                    unit = "dB"
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
            pm = get_mixer_param_meta("return", "volume")
            if pm and pm.get("fit"):
                dval = apply_mixer_fit_forward(pm, float(v))
                if dval is not None:
                    disp_txt = f"{float(dval):.1f} dB"
        elif field == "pan":
            try:
                display_min, display_max = get_mixer_display_range("pan")
                display_scale = max(abs(display_min), abs(display_max))
                pan_val = float(v) * display_scale
                # Round to avoid scientific notation for values very close to zero
                if abs(pan_val) < 0.5:
                    disp_txt = "C"
                else:
                    disp_txt = f"{abs(pan_val):.0f}{'R' if pan_val > 0 else 'L'}"
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
    # Capabilities ref now added centrally in chat_service.py
    return resp


def set_track_send(intent: CanonicalIntent) -> Dict[str, Any]:
    if intent.track_index is None:
        raise HTTPException(400, "track_index_required")
    if intent.send_index is None and intent.send_ref is None:
        raise HTTPException(400, "send_index_or_send_ref_required")
    track_idx = int(intent.track_index)
    send_idx = _resolve_send_index(intent.send_index, intent.send_ref)
    if track_idx < 1:
        raise HTTPException(400, "track_index_must_be_at_least_1")

    v = float(intent.value if intent.value is not None else 0.0)
    pm = get_mixer_param_meta("track", "send")  # Get once for both conversion and display
    unit_norm = normalize_unit(intent.unit)
    if unit_norm in ("percent", "%"):
        v = v / 100.0
    else:
        # Use piecewise fit to convert dB -> normalized
        if pm and pm.get("fit"):
            inv = apply_mixer_fit_inverse(pm, float(v))
            if inv is not None:
                v = float(inv)

    v = clamp(v, 0.0, 1.0) if intent.clamp else v

    if intent.dry_run:
        return {"ok": True, "preview": {"op": "set_send", "track_index": track_idx, "send_index": send_idx, "value": v}}

    resp = request_op("set_send", timeout=1.0, track_index=track_idx, send_index=send_idx, value=float(v))
    if not resp:
        raise HTTPException(504, "no_reply")

    # Write-through to ValueRegistry
    try:
        reg = get_value_registry()
        disp = None
        unit = None
        if intent.display:
            disp = intent.display
            unit = intent.unit
        else:
            # Use piecewise fit for display
            if pm and pm.get("fit"):
                dval = apply_mixer_fit_forward(pm, float(v))
                if dval is not None:
                    disp = f"{float(dval):.2f}"
                    unit = "dB"
        reg.update_mixer("track", track_idx, f"send_{send_idx}", float(v), disp, unit, source="op")
    except Exception:
        pass

    # Capabilities ref now added centrally in chat_service.py

    # Emit SSE event for real-time UI updates
    try:
        import asyncio
        from server.core.deps import get_broker
        broker = get_broker()
        asyncio.create_task(broker.publish({
            "event": "send_changed",
            "track": track_idx,
            "send_index": send_idx,
        }))
    except Exception:
        pass

    return resp


def set_return_send(intent: CanonicalIntent) -> Dict[str, Any]:
    return_idx = _resolve_return_index(intent.return_index, intent.return_ref)

    # Validate bounds (best effort)
    try:
        rs = request_op("get_return_tracks", timeout=1.0) or {}
        rets = ((rs.get("data") or rs) if isinstance(rs, dict) else rs).get("returns", [])
        if rets and (return_idx < 0 or return_idx >= len(rets)):
            letters = [chr(ord('A') + int(r.get("index", 0))) for r in rets]
            raise HTTPException(404, f"return_out_of_range:{return_idx}; returns={letters}")
    except HTTPException:
        raise
    except Exception:
        pass

    send_idx = _resolve_send_index(intent.send_index, intent.send_ref)
    v = float(intent.value if intent.value is not None else 0.0)
    pm = get_mixer_param_meta("return", "send")  # Get once for both conversion and display
    unit_norm = normalize_unit(intent.unit)
    if unit_norm in ("percent", "%"):
        v = v / 100.0
    else:
        # Use piecewise fit to convert dB -> normalized
        if pm and pm.get("fit"):
            inv = apply_mixer_fit_inverse(pm, float(v))
            if inv is not None:
                v = float(inv)

    v = clamp(v, 0.0, 1.0) if intent.clamp else v

    if intent.dry_run:
        return {"ok": True, "preview": {"op": "set_return_send", "return_index": return_idx, "send_index": send_idx, "value": v}}

    resp = request_op("set_return_send", timeout=1.0, return_index=return_idx, send_index=send_idx, value=float(v))
    if not resp:
        raise HTTPException(504, "no_reply")

    try:
        reg = get_value_registry()
        disp = None
        unit = None
        # Prefer forward fit for display if available
        try:
            from server.services.intents.utils.mixer import apply_mixer_fit_forward
            if pm and isinstance(pm.get("fit"), dict):
                dval = apply_mixer_fit_forward(pm, float(v))
                if dval is not None:
                    disp = f"{float(dval):.2f}"
                    unit = "dB"
        except Exception:
            pass
        reg.update_mixer("return", return_idx, f"send_{send_idx}", float(v), disp, unit, source="op")
    except Exception:
        pass

    # Add summary for chat/UI
    try:
        letter = chr(ord('A') + int(return_idx))
        disp_txt = None
        try:
            # Use piecewise fit for summary
            if pm and pm.get("fit"):
                dval = apply_mixer_fit_forward(pm, float(v))
                if dval is not None:
                    disp_txt = f"{float(dval):.1f} dB"
        except Exception:
            pass
        if isinstance(resp, dict):
            if disp_txt:
                resp["summary"] = f"Set Return {letter} send {chr(ord('A') + int(send_idx))} to {disp_txt}"
            else:
                resp["summary"] = f"Set Return {letter} send {chr(ord('A') + int(send_idx))}"
    except Exception:
        pass

    # Capabilities ref now added centrally in chat_service.py

    # Emit SSE event for real-time UI updates
    try:
        import asyncio
        from server.core.deps import get_broker
        broker = get_broker()
        asyncio.create_task(broker.publish({
            "event": "return_send_changed",
            "return": return_idx,
            "send_index": send_idx,
        }))
    except Exception:
        pass

    return resp


def set_master_mixer(intent: CanonicalIntent) -> Dict[str, Any]:
    field = str(intent.field or "")
    v = float(intent.value if intent.value is not None else 0.0)

    # Display resolution
    resolved_from_display = False
    if intent.display and field in ("pan", "volume", "cue"):
        resolved = resolve_mixer_display_value(field, intent.display)
        if resolved is not None:
            v = resolved
            resolved_from_display = True

    if field == "volume" and not resolved_from_display:
        unit_l = (intent.unit or "").lower()
        if unit_l in ("percent", "%"):
            v = v / 100.0
        else:
            # Use piecewise fit to convert dB -> normalized (default to dB semantics)
            pm = get_mixer_param_meta("master", "volume")
            if pm and pm.get("fit"):
                inv = apply_mixer_fit_inverse(pm, float(v))
                if inv is not None:
                    v = float(inv)
        v = clamp(v, 0.0, 1.0) if intent.clamp else v
    elif field == "cue" and not resolved_from_display:
        unit_norm = normalize_unit(intent.unit)
        if unit_norm in ("percent", "%"):
            v = v / 100.0
        else:
            # Use piecewise fit to convert dB -> normalized (cue uses same mapping as volume)
            pm = get_mixer_param_meta("master", "cue")
            if pm and pm.get("fit"):
                inv = apply_mixer_fit_inverse(pm, float(v))
                if inv is not None:
                    v = float(inv)
        v = clamp(v, 0.0, 1.0) if intent.clamp else v
    elif field == "pan":
        if abs(v) > 1.0:
            display_min, display_max = get_mixer_display_range("pan")
            display_scale = max(abs(display_min), abs(display_max))
            v = clamp(v, display_min, display_max) / display_scale
        else:
            v = clamp(v, -1.0, 1.0) if intent.clamp else v

    if intent.dry_run:
        return {"ok": True, "preview": {"op": "set_master_mixer", "field": field, "value": v}}

    resp = request_op("set_master_mixer", timeout=1.0, field=str(field), value=float(v))
    if not resp:
        raise HTTPException(504, "no_reply")

    try:
        reg = get_value_registry()
        disp = None
        unit = None
        if intent.display and field in ("volume", "pan", "cue"):
            disp = intent.display
            unit = intent.unit if field in ("volume", "cue") else None
        elif field == "volume":
            try:
                # Use piecewise fit for display
                pm = get_mixer_param_meta("master", "volume")
                if pm and pm.get("fit"):
                    dval = apply_mixer_fit_forward(pm, float(v))
                    if dval is not None:
                        disp = f"{float(dval):.1f} dB"
                        unit = "db"
            except Exception:
                pass
        elif field == "cue":
            try:
                # Use piecewise fit for display (cue uses same mapping as volume)
                pm = get_mixer_param_meta("master", "cue")
                if pm and pm.get("fit"):
                    dval = apply_mixer_fit_forward(pm, float(v))
                    if dval is not None:
                        disp = f"{float(dval):.1f} dB"
                        unit = "db"
            except Exception:
                pass
        reg.update_mixer("master", 0, field, float(v), disp, unit, source="op")
    except Exception:
        pass

    # Capabilities ref now added centrally in chat_service.py
    return resp
