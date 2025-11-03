"""Read service for intent reads (mixer and routing parameter reads).

Handles reading current parameter values when UI clicks on capability chips.
Returns current values with display formatting.
"""
from __future__ import annotations

import re
from typing import Any, Dict

from fastapi import HTTPException

from server.models.intents_api import ReadIntent
from server.services.ableton_client import request_op
from server.volume_utils import live_float_to_db_send
from server.services.intents.utils.refs import _letter_to_index
from server.services.mapping_utils import make_device_signature
from server.core.deps import get_store


def read_intent(intent: ReadIntent) -> Dict[str, Any]:
    """Read current parameter values for mixer and routing.

    Used by the UI when clicking on capability chips to open parameter editors.
    Returns current values with display formatting.
    """
    domain = intent.domain
    field = (intent.field or "").strip()

    # Detect "Send A/B/C" pattern and convert to field="send", send_ref="A/B/C"
    send_match = re.match(r'^send\s+([a-z])$', field, re.IGNORECASE)
    if send_match:
        send_ref = send_match.group(1).upper()
        field = "send"
    else:
        send_ref = intent.send_ref
        field = field.lower()

    # Handle send reads
    if field == "send" and send_ref:
        return _read_send(domain, intent, send_ref)

    # Handle device parameter reads
    if domain == "device":
        param_ref = intent.param_ref or field
        return _read_device_param(intent, param_ref)

    # Handle mixer parameter reads (volume, pan, mute, solo, cue)
    if domain in ("track", "return", "master") and field in ("volume", "pan", "mute", "solo", "cue"):
        return _read_mixer_param(domain, intent, field)

    # Unsupported read
    raise HTTPException(400, "unsupported_read_intent")


def _read_send(domain: str, intent: ReadIntent, send_ref: str) -> Dict[str, Any]:
    """Read send parameter value for track or return."""
    send_idx = _letter_to_index(send_ref)

    if domain == "track" and intent.track_index is not None:
        ti = int(intent.track_index)
        resp = request_op("get_track_sends", timeout=1.0, track_index=ti)
        if not resp:
            raise HTTPException(504, "no_reply")
        sends = ((resp.get("data") or resp) if isinstance(resp, dict) else resp).get("sends", [])
        for s in sends:
            if int(s.get("index", -1)) == send_idx:
                value = s.get("value")
                display = s.get("display_value")
                if display is None and value is not None:
                    try:
                        display = f"{live_float_to_db_send(float(value)):.1f}"
                    except Exception:
                        pass
                return {
                    "ok": True,
                    "field": "send",
                    "send_index": send_idx,
                    "display_value": display,
                    "normalized_value": value,
                }
        raise HTTPException(404, f"send_{send_ref}_not_found")

    elif domain == "return" and (intent.return_index is not None or intent.return_ref is not None):
        if intent.return_ref:
            ri = _letter_to_index(intent.return_ref)
        else:
            ri = int(intent.return_index)
        resp = request_op("get_return_sends", timeout=1.0, return_index=ri)
        if not resp:
            raise HTTPException(504, "no_reply")
        sends = ((resp.get("data") or resp) if isinstance(resp, dict) else resp).get("sends", [])
        for s in sends:
            if int(s.get("index", -1)) == send_idx:
                value = s.get("value")
                display = s.get("display_value")
                if display is None and value is not None:
                    try:
                        display = f"{live_float_to_db_send(float(value)):.1f}"
                    except Exception:
                        pass
                return {
                    "ok": True,
                    "field": "send",
                    "send_index": send_idx,
                    "display_value": display,
                    "normalized_value": value,
                }
        raise HTTPException(404, f"send_{send_ref}_not_found")

    raise HTTPException(400, "unsupported_send_read")


def _read_device_param(intent: ReadIntent, param_name: str) -> Dict[str, Any]:
    """Read device parameter value for track or return device."""
    # Return device
    if intent.return_index is not None or intent.return_ref is not None:
        if intent.return_ref:
            ri = _letter_to_index(intent.return_ref)
        else:
            ri = int(intent.return_index)

        if intent.device_index is None:
            raise HTTPException(400, "device_index_required")
        di = int(intent.device_index)

        resp = request_op("get_return_device_params", timeout=1.2, return_index=ri, device_index=di)
        if not resp:
            raise HTTPException(504, "no_reply")

        params = ((resp.get("data") or resp) if isinstance(resp, dict) else resp).get("params", [])
        param_name_lower = param_name.lower()

        # Get device name for signature lookup
        dv = request_op("get_return_devices", timeout=0.8, return_index=ri) or {}
        dlist = ((dv.get("data") or dv) if isinstance(dv, dict) else dv).get("devices") or []
        dname = next((str(d.get("name", "")) for d in dlist if int(d.get("index", -1)) == di), f"Device {di}")

        # Build signature and fetch mapping to get label_map for quantized params
        sig = make_device_signature(dname, params)
        store = get_store()
        mapping = store.get_device_map(sig) if store.enabled else None

        for p in params:
            if str(p.get("name", "")).lower() == param_name_lower:
                display_value = p.get("display_value")
                normalized_value = p.get("value")

                # For quantized params, look up the label from Firestore label_map
                if mapping:
                    mparams = mapping.get("params_meta") or mapping.get("params") or []
                    mparam = next((mp for mp in mparams if str(mp.get("name", "")).lower() == param_name_lower), None)
                    if mparam and mparam.get("label_map"):
                        # Convert normalized value (e.g., 1.0) to label (e.g., "Fade")
                        label_map = mparam.get("label_map")
                        try:
                            normalized_int = round(float(normalized_value))
                            label_key = str(normalized_int)
                            if label_key in label_map:
                                display_value = label_map[label_key]
                        except Exception:
                            pass  # Fall back to original display_value

                return {
                    "ok": True,
                    "field": param_name,
                    "param_index": p.get("index"),
                    "display_value": display_value,
                    "normalized_value": normalized_value,
                }

        raise HTTPException(404, f"parameter_{param_name}_not_found")

    # Track device
    elif intent.track_index is not None:
        ti = int(intent.track_index)

        if intent.device_index is None:
            raise HTTPException(400, "device_index_required")
        di = int(intent.device_index)

        resp = request_op("get_track_device_params", timeout=1.2, track_index=ti, device_index=di)
        if not resp:
            raise HTTPException(504, "no_reply")

        params = ((resp.get("data") or resp) if isinstance(resp, dict) else resp).get("params", [])
        param_name_lower = param_name.lower()

        # Get device name for signature lookup
        dv = request_op("get_track_devices", timeout=0.8, track_index=ti) or {}
        dlist = ((dv.get("data") or dv) if isinstance(dv, dict) else dv).get("devices") or []
        dname = next((str(d.get("name", "")) for d in dlist if int(d.get("index", -1)) == di), f"Device {di}")

        # Build signature and fetch mapping to get label_map for quantized params
        sig = make_device_signature(dname, params)
        store = get_store()
        mapping = store.get_device_map(sig) if store.enabled else None

        for p in params:
            if str(p.get("name", "")).lower() == param_name_lower:
                display_value = p.get("display_value")
                normalized_value = p.get("value")

                # For quantized params, look up the label from Firestore label_map
                if mapping:
                    mparams = mapping.get("params_meta") or mapping.get("params") or []
                    mparam = next((mp for mp in mparams if str(mp.get("name", "")).lower() == param_name_lower), None)
                    if mparam and mparam.get("label_map"):
                        # Convert normalized value (e.g., 1.0) to label (e.g., "Fade")
                        label_map = mparam.get("label_map")
                        try:
                            normalized_int = round(float(normalized_value))
                            label_key = str(normalized_int)
                            if label_key in label_map:
                                display_value = label_map[label_key]
                        except Exception:
                            pass  # Fall back to original display_value

                return {
                    "ok": True,
                    "field": param_name,
                    "param_index": p.get("index"),
                    "display_value": display_value,
                    "normalized_value": normalized_value,
                }

        raise HTTPException(404, f"parameter_{param_name}_not_found")

    raise HTTPException(400, "track_index_or_return_index_required")


def _read_mixer_param(domain: str, intent: ReadIntent, field: str) -> Dict[str, Any]:
    """Read mixer parameter value (volume, pan, mute, solo) for track/return/master."""
    from server.volume_utils import live_float_to_db

    # Track mixer
    if domain == "track":
        if intent.track_index is None:
            raise HTTPException(400, "track_index_required")
        ti = int(intent.track_index)

        resp = request_op("get_track_status", timeout=1.0, track_index=ti)
        if not resp:
            raise HTTPException(504, "no_reply")

        data = ((resp.get("data") or resp) if isinstance(resp, dict) else resp)

        # mute/solo are at data level, not in mixer dict
        if field in ("mute", "solo"):
            if field not in data:
                raise HTTPException(404, f"{field}_not_found")
            value = data.get(field)
        else:
            # volume/pan are in mixer dict
            mixer = data.get("mixer", {})
            if field not in mixer:
                raise HTTPException(404, f"{field}_not_found_in_mixer")
            value = mixer.get(field)

        # Format display value
        display = None
        if field == "volume":
            try:
                display = f"{live_float_to_db(float(value)):.2f}"
            except Exception:
                pass
        elif field == "pan":
            try:
                # Pan: [-1, 1] → [-50, 50] with L/R/C
                pan_val = float(value) * 50.0
                if abs(pan_val) < 0.1:
                    display = "C"
                else:
                    display = f"{abs(pan_val):.0f}{'R' if pan_val > 0 else 'L'}"
            except Exception:
                pass
        elif field in ("mute", "solo"):
            display = "On" if bool(value) else "Off"

        return {
            "ok": True,
            "field": field,
            "display_value": display,
            "normalized_value": value,
            "value": value
        }

    # Return mixer
    elif domain == "return":
        if intent.return_ref:
            ri = _letter_to_index(intent.return_ref)
        elif intent.return_index is not None:
            ri = int(intent.return_index)
        else:
            raise HTTPException(400, "return_index_or_return_ref_required")

        # Get all returns and find the one we want
        resp = request_op("get_return_tracks", timeout=1.0)
        if not resp:
            raise HTTPException(504, "no_reply")

        returns = ((resp.get("data") or resp) if isinstance(resp, dict) else resp).get("returns", [])
        ret = next((r for r in returns if int(r.get("index", -1)) == ri), None)
        if not ret:
            raise HTTPException(404, "return_not_found")

        # For returns, all fields (including mute/solo) are in mixer dict
        mixer = ret.get("mixer", {})
        if field not in mixer:
            raise HTTPException(404, f"{field}_not_found_in_mixer")
        value = mixer.get(field)

        # Format display value
        display = None
        if field == "volume":
            try:
                display = f"{live_float_to_db(float(value)):.2f}"
            except Exception:
                pass
        elif field == "pan":
            try:
                pan_val = float(value) * 50.0
                if abs(pan_val) < 0.1:
                    display = "C"
                else:
                    display = f"{abs(pan_val):.0f}{'R' if pan_val > 0 else 'L'}"
            except Exception:
                pass
        elif field in ("mute", "solo"):
            display = "On" if bool(value) else "Off"

        return {
            "ok": True,
            "field": field,
            "display_value": display,
            "normalized_value": value,
            "value": value
        }

    # Master mixer
    elif domain == "master":
        resp = request_op("get_master_status", timeout=1.0)
        if not resp:
            raise HTTPException(504, "no_reply")

        mixer = ((resp.get("data") or resp) if isinstance(resp, dict) else resp).get("mixer", {})

        # Check if field exists in mixer (use 'in' to allow 0/False values)
        if field not in mixer:
            raise HTTPException(404, f"{field}_not_found_in_mixer")

        value = mixer.get(field)

        # Format display value
        display = None
        if field in ("volume", "cue"):
            try:
                display = f"{live_float_to_db(float(value)):.2f}"
            except Exception:
                pass
        elif field == "pan":
            try:
                pan_val = float(value) * 50.0
                if abs(pan_val) < 0.1:
                    display = "C"
                else:
                    display = f"{abs(pan_val):.0f}{'R' if pan_val > 0 else 'L'}"
            except Exception:
                pass

        return {
            "ok": True,
            "field": field,
            "display_value": display,
            "normalized_value": value,
            "value": value
        }

    raise HTTPException(400, "unsupported_mixer_domain")
