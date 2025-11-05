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

