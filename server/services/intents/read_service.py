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
