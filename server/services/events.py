"""Unified event publishing helper.

Wraps SSE broker publishing with a small helper to keep call sites simple
and resilient to exceptions.
"""

from __future__ import annotations

from typing import Any, Dict

from server.core.events import broker
import asyncio


async def _publish_async(event: Dict[str, Any]) -> None:
  try:
    # Add display_value for mixer events that don't have it
    if isinstance(event, dict) and "display_value" not in event:
      evt_name = event.get("event")
      field = event.get("field")
      value = event.get("value")

      if evt_name in ("mixer_changed", "return_mixer_changed", "master_mixer_changed"):
        if field == "volume" and isinstance(value, (int, float)):
          from server.volume_utils import live_float_to_db
          event["display_value"] = round(live_float_to_db(float(value)), 2)
        elif field == "pan" and isinstance(value, (int, float)):
          pan_val = float(value) * 50.0
          event["display_value"] = round(pan_val, 1)
        elif field == "cue" and isinstance(value, (int, float)):
          from server.volume_utils import live_float_to_db
          event["display_value"] = round(live_float_to_db(float(value)), 2)
      elif evt_name == "send_changed" and isinstance(value, (int, float)):
        from server.volume_utils import live_float_to_db_send
        event["display_value"] = round(live_float_to_db_send(float(value)), 1)

    await broker.publish(event)
  except Exception:
    # Best-effort; do not crash callers
    pass


def publish(event: str, **payload: Any) -> None:
  """Fire-and-forget publish to the SSE broker.

  Usage: publish("mixer_changed", track=1, field="volume")
  """
  try:
    asyncio.create_task(_publish_async({"event": event, **payload}))
  except Exception:
    # Not in an event loop or scheduling failed; ignore
    pass

