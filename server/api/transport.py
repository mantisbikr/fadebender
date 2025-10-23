from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from server.core.events import broker
from server.services.ableton_client import get_transport as svc_get_transport, set_transport as svc_set_transport
from server.core.deps import get_value_registry


router = APIRouter()


@router.get("/transport")
def get_transport_state() -> Dict[str, Any]:
    return svc_get_transport(timeout=1.0)


class TransportBody(BaseModel):
    action: str  # play|stop|record|metronome|tempo
    value: Optional[float] = None  # used for tempo


@router.post("/transport")
def set_transport(body: TransportBody) -> Dict[str, Any]:
    resp = svc_set_transport(body.action, body.value, timeout=1.0)
    if not resp or not resp.get("ok", True):
        raise HTTPException(504, "no response from remote script")

    # Update ValueRegistry for snapshot (only for tempo and metronome)
    try:
        reg = get_value_registry()
        if body.action == "tempo" and body.value is not None:
            reg.update_transport("tempo", body.value, source="web_ui")
        elif body.action == "metronome":
            # metronome is a toggle, get state from response
            data = resp.get("data", {})
            if isinstance(data, dict) and "metronome" in data:
                reg.update_transport("metronome", data.get("metronome"), source="web_ui")
    except Exception:
        pass

    # broadcast minimal event (avoid importing app to prevent cycles)
    try:
        asyncio.create_task(broker.publish({"event": "transport_changed", "action": str(body.action)}))
    except Exception:
        pass
    return resp

