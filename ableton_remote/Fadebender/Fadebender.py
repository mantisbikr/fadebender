"""
Minimal Fadebender Remote Script for Ableton Live.

This is a scaffold. It creates a no-op ControlSurface and is ready to
add a UDP bridge and LOM operations. It should load safely in Live.
"""
from __future__ import annotations

import threading
import os


try:  # Ableton Live environment
    from _Framework.ControlSurface import ControlSurface  # type: ignore
except Exception:  # Fallback for dev/linters
    class ControlSurface:  # type: ignore
        def __init__(self, *a, **k):
            pass

        def log_message(self, *a, **k):
            print(*a)


class Fadebender(ControlSurface):
    def __init__(self, c_instance):  # noqa: N803 (Live API uses this name)
        super(Fadebender, self).__init__(c_instance)
        try:
            self.log_message("[Fadebender] Remote Script loaded")
        except Exception:
            pass

        # Optional: start UDP bridge if explicitly enabled by env
        if os.environ.get("FADEBENDER_UDP_ENABLE") in ("1", "true", "True"):
            try:
                from .udp_bridge import start_udp_server, set_live_accessor  # type: ignore

                set_live_accessor(lambda: self.song())
                t = threading.Thread(target=start_udp_server, name="FadebenderUDP", daemon=True)
                t.start()
                self.log_message("[Fadebender] UDP bridge started")
            except Exception as e:  # pragma: no cover
                self.log_message(f"[Fadebender] UDP not started: {e}")


def create_instance(c_instance):  # noqa: N802 (Live API name)
    return Fadebender(c_instance)
