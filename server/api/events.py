from __future__ import annotations

import json
from typing import Any, Dict

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from server.core.events import broker
from server.services.ableton_client import request_op


router = APIRouter()


@router.get("/events")
async def events():
    q = await broker.subscribe()

    async def event_gen():
        # Bootstrap: emit current master mixer values so clients seed immediately
        try:
            resp = request_op("get_master_status", timeout=0.6)
            data = (resp.get("data") if isinstance(resp, dict) else resp) if resp else None
            mix = (data or {}).get("mixer") if isinstance(data, dict) else None
            if isinstance(mix, dict):
                for fld in ("volume", "pan", "cue"):
                    val = mix.get(fld)
                    if isinstance(val, (int, float)):
                        payload = json.dumps({"event": "master_mixer_changed", "field": fld, "value": float(val)})
                        yield "data: " + payload + "\n\n"
        except Exception:
            pass
        try:
            while True:
                data = await q.get()
                try:
                    payload = json.dumps(data)
                except Exception:
                    payload = json.dumps({"malformed": True, "repr": str(data)})
                yield "data: " + payload + "\n\n"
        except Exception:
            # Ensure unsubscribe on cancellation or any generator exit
            try:
                await broker.unsubscribe(q)
            except Exception:
                pass

    return StreamingResponse(event_gen(), media_type="text/event-stream")
