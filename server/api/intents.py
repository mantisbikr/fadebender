from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from server.models.intents_api import (
    Domain,
    CanonicalIntent,
    ReadIntent,
    QueryTarget,
    QueryIntent,
)


router = APIRouter()


@router.post("/intent/execute")
def execute_intent(intent: CanonicalIntent, debug: bool = False) -> Dict[str, Any]:
    """Dispatch canonical intent to specialized services.

    The API layer keeps minimal logic and delegates execution to
    server.services.intents.* modules to avoid drift and reduce size.
    """
    d = intent.domain
    field = (intent.field or "").strip().lower()

    # Transport domain (direct pass-through)
    if d == "transport":
        from server.services.ableton_client import request_op as _req
        action = getattr(intent, "action", "")
        value = getattr(intent, "value", None)
        # Combined time signature
        if action == "time_sig_both" and isinstance(value, dict):
            num = value.get("num"); den = value.get("den")
            ok_all = True
            if num is not None:
                r1 = _req("set_transport", timeout=1.0, action="time_sig_num", value=float(num))
                ok_all = ok_all and bool(r1 and r1.get("ok", True))
            if den is not None:
                r2 = _req("set_transport", timeout=1.0, action="time_sig_den", value=float(den))
                ok_all = ok_all and bool(r2 and r2.get("ok", True))
            return {"ok": ok_all, "summary": f"Transport: time_signature {num}/{den}"}
        # Combined loop region
        if action == "loop_region" and isinstance(value, dict):
            start = value.get("start"); length = value.get("length")
            ok_all = True
            _ = _req("set_transport", timeout=1.0, action="loop_on", value=1.0)
            if start is not None:
                r1 = _req("set_transport", timeout=1.0, action="loop_start", value=float(start))
                ok_all = ok_all and bool(r1 and r1.get("ok", True))
            if length is not None:
                r2 = _req("set_transport", timeout=1.0, action="loop_length", value=float(length))
                ok_all = ok_all and bool(r2 and r2.get("ok", True))
            return {"ok": ok_all, "summary": f"Transport: loop_region start={start} length={length}"}
        # Simple action
        params: Dict[str, Any] = {"action": str(action)}
        if value is not None:
            try:
                params["value"] = float(value)
            except Exception:
                pass
        r = _req("set_transport", timeout=1.0, **params)
        return {"ok": bool(r and r.get("ok", True)), "summary": f"Transport: {action}{(' ' + str(value)) if value is not None else ''}", "resp": r}

    # Routing
    if d == "track" and field == "routing" and intent.track_index is not None:
        from server.services.intents.routing_service import set_track_routing
        return set_track_routing(intent)
    if d == "return" and field == "routing" and (intent.return_index is not None or intent.return_ref is not None):
        from server.services.intents.routing_service import set_return_routing
        return set_return_routing(intent)

    # Mixer (track/return/master)
    if d == "track" and field in ("volume", "pan", "mute", "solo"):
        from server.services.intents.mixer_service import set_track_mixer
        return set_track_mixer(intent)
    if d == "track" and field == "send":
        from server.services.intents.mixer_service import set_track_send
        return set_track_send(intent)

    if d == "return" and field in ("volume", "pan", "mute", "solo"):
        from server.services.intents.mixer_service import set_return_mixer
        return set_return_mixer(intent)
    if d == "return" and field == "send":
        from server.services.intents.mixer_service import set_return_send
        return set_return_send(intent)

    if d == "master" and field in ("volume", "pan", "cue"):
        from server.services.intents.mixer_service import set_master_mixer
        return set_master_mixer(intent)

    # Device parameters (track/return)
    if d == "device" and (intent.return_index is not None or intent.return_ref is not None) and intent.device_index is not None:
        from server.services.intents.param_service import set_return_device_param
        return set_return_device_param(intent, debug=debug)
    if d == "device" and intent.track_index is not None and intent.device_index is not None:
        from server.services.intents.param_service import set_track_device_param
        return set_track_device_param(intent, debug=debug)

    # If we reach here, the intent is unsupported
    raise HTTPException(400, "unsupported_intent")


@router.post("/intent/read")
def read_intent_endpoint(intent: ReadIntent) -> Dict[str, Any]:
    """Read current parameter values for mixer and routing.

    Used by the UI when clicking on capability chips to open parameter editors.
    Returns current values with display formatting.
    """
    from server.services.intents.read_service import read_intent
    return read_intent(intent)


@router.post("/intent/query")
async def query_intent(intent: QueryIntent) -> Dict[str, Any]:
    """Handle get_parameter intent by calling /snapshot/query endpoint."""
    import httpx

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://localhost:8722/snapshot/query",
                json={"targets": [t.model_dump() for t in intent.targets]},
                timeout=5.0,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(500, f"Failed to query snapshot: {str(e)}")
