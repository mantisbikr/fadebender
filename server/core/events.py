from __future__ import annotations

import asyncio
import os
import json
import time
import asyncio
from typing import Any, Dict, Optional


class EventBroker:
    def __init__(self) -> None:
        self._subs: list[asyncio.Queue] = []
        self._lock = asyncio.Lock()

    async def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        async with self._lock:
            self._subs.append(q)
        return q

    async def publish(self, data: Dict[str, Any]) -> None:
        async with self._lock:
            for q in list(self._subs):
                try:
                    q.put_nowait(data)
                except Exception:
                    pass

    async def unsubscribe(self, q: asyncio.Queue) -> None:
        async with self._lock:
            if q in self._subs:
                self._subs.remove(q)


# Shared broker singleton
broker = EventBroker()


_MASTER_DEDUP: Dict[str, tuple[float, float]] = {}


def _debug_enabled() -> bool:
    try:
        return str(os.getenv("FB_DEBUG_SSE", "")).lower() in ("1", "true", "yes", "on")
    except Exception:
        return False


async def emit_event(payload: Dict[str, Any]) -> None:
    try:
        if isinstance(payload, dict) and payload.get("event") == "master_mixer_changed":
            fld = str(payload.get("field") or "").strip()
            val = payload.get("value")
            if fld and isinstance(val, (int, float)):
                v = float(val)
                last = _MASTER_DEDUP.get(fld)
                if last is not None:
                    last_v, _last_ts = last
                    if abs(v - last_v) <= 1e-7:
                        return
                _MASTER_DEDUP[fld] = (v, time.time())
    except Exception:
        pass

    # Add display_value for mixer events that don't have it (from Live listeners)
    try:
        if isinstance(payload, dict) and "display_value" not in payload:
            event = payload.get("event")
            field = payload.get("field")
            value = payload.get("value")
            print(f"[SSE-CONVERT] Event={event}, field={field}, value={value}, has_display={('display_value' in payload)}")

            if event in ("mixer_changed", "return_mixer_changed", "master_mixer_changed"):
                if field == "volume" and isinstance(value, (int, float)):
                    from server.volume_utils import live_float_to_db
                    display = round(live_float_to_db(float(value)), 2)
                    payload["display_value"] = display
                    print(f"[SSE-CONVERT] Added volume display_value: {display}")
                elif field == "pan" and isinstance(value, (int, float)):
                    pan_val = float(value) * 50.0
                    payload["display_value"] = round(pan_val, 1)
                elif field == "cue" and isinstance(value, (int, float)):
                    from server.volume_utils import live_float_to_db
                    payload["display_value"] = round(live_float_to_db(float(value)), 2)
            elif event == "send_changed" and isinstance(value, (int, float)):
                from server.volume_utils import live_float_to_db_send
                payload["display_value"] = round(live_float_to_db_send(float(value)), 1)
    except Exception:
        pass

    if _debug_enabled():
        try:
            ename = payload.get("event")
            meta = {k: v for k, v in payload.items() if k != "data"}
            print(f"[SSE] Emitting {ename}: {json.dumps(meta)}")
        except Exception:
            print(f"[SSE] Emitting {payload}")
    await broker.publish(payload)


def schedule_emit(payload: Dict[str, Any]) -> None:
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(emit_event(payload))
    except RuntimeError:
        try:
            asyncio.run(emit_event(payload))
        except RuntimeError:
            try:
                asyncio.ensure_future(emit_event(payload))
            except Exception:
                pass
