from __future__ import annotations

import json
import os
import socket
import threading
from typing import Optional

import asyncio

from server.core.events import schedule_emit
from server.core.deps import get_live_index

_EVENT_THREAD: Optional[threading.Thread] = None


def start_ableton_event_listener() -> None:
    global _EVENT_THREAD
    if _EVENT_THREAD and _EVENT_THREAD.is_alive():
        return
    host = os.getenv("ABLETON_UDP_CLIENT_HOST", "127.0.0.1")
    port = int(os.getenv("ABLETON_UDP_CLIENT_PORT", os.getenv("ABLETON_EVENT_PORT", "19846")))
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((host, port))
        print(f"[Ableton] Listening for notifications on {host}:{port}")
    except Exception as e:
        print(f"[Ableton] Failed to bind event listener on {host}:{port} -> {e}")
        return

    def loop():
        while True:
            try:
                data, _ = sock.recvfrom(64 * 1024)
            except Exception:
                continue
            try:
                payload = json.loads(data.decode("utf-8"))
            except Exception:
                continue
            schedule_emit(payload)

    _EVENT_THREAD = threading.Thread(target=loop, name="AbletonEventListener", daemon=True)
    _EVENT_THREAD.start()


def schedule_live_index_tasks() -> None:
    try:
        li = get_live_index()
        asyncio.create_task(li.refresh_all())
        asyncio.create_task(li.loop(interval_sec=60.0))
    except Exception:
        pass
