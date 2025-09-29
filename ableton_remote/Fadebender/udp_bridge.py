"""
UDP bridge for the Fadebender Remote Script (scaffold).

Safe by default: only starts when FADEBENDER_UDP_ENABLE=1 is present in
Live's environment. Delegates operations to lom_ops where the actual
Live Object Model access belongs.
"""
from __future__ import annotations

import json
import os
import socket
from . import lom_ops
from typing import Callable, Optional, Any


HOST = os.getenv("ABLETON_UDP_HOST", "127.0.0.1")
PORT = int(os.getenv("ABLETON_UDP_PORT", "19845"))

_LIVE_ACCESSOR: Optional[Callable[[], Any]] = None


def set_live_accessor(getter: Callable[[], Any]):  # pragma: no cover
    global _LIVE_ACCESSOR
    _LIVE_ACCESSOR = getter


def start_udp_server():  # pragma: no cover
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((HOST, PORT))
    while True:
        data, addr = sock.recvfrom(64 * 1024)
        try:
            msg = json.loads(data.decode("utf-8"))
        except Exception:
            continue
        op = (msg.get("op") or "").strip()
        try:
            if op == "ping":
                resp = {"ok": True, "op": "ping"}
            elif op == "get_overview":
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                data_out = lom_ops.get_overview(live_ctx)
                resp = {"ok": True, "op": op, "data": data_out}
            elif op == "get_track_status":
                ti = int(msg.get("track_index", 0))
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                data_out = lom_ops.get_track_status(live_ctx, ti)
                resp = {"ok": True, "op": op, "data": data_out}
            elif op == "set_mixer":
                track_index = int(msg.get("track_index", 0))
                field = str(msg.get("field"))
                value = float(msg.get("value", 0.0))
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                ok = lom_ops.set_mixer(live_ctx, track_index, field, value)
                resp = {"ok": bool(ok), "op": op}
            elif op == "set_send":
                track_index = int(msg.get("track_index", 0))
                send_index = int(msg.get("send_index", 0))
                value = float(msg.get("value", 0.0))
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                ok = lom_ops.set_send(live_ctx, track_index, send_index, value)
                resp = {"ok": bool(ok), "op": op}
            elif op == "set_device_param":
                track_index = int(msg.get("track_index", 0))
                device_index = int(msg.get("device_index", 0))
                param_index = int(msg.get("param_index", 0))
                value = float(msg.get("value", 0.0))
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                ok = lom_ops.set_device_param(live_ctx, track_index, device_index, param_index, value)
                resp = {"ok": bool(ok), "op": op}
            elif op == "get_track_sends":
                track_index = int(msg.get("track_index", 0))
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                data_out = lom_ops.get_track_sends(live_ctx, track_index)
                resp = {"ok": True, "op": op, "data": data_out}
            elif op == "set_volume_db":
                track_index = int(msg.get("track_index", 0))
                db = float(msg.get("db", 0.0))
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                result = lom_ops.set_volume_db(live_ctx, track_index, db)
                if isinstance(result, dict):
                    resp = {"ok": bool(result.get("ok", False)), "op": op, **result}
                else:
                    resp = {"ok": bool(result), "op": op}
            elif op == "select_track":
                track_index = int(msg.get("track_index", 0))
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                ok = lom_ops.select_track(live_ctx, track_index)
                resp = {"ok": bool(ok), "op": op}
            else:
                resp = {"ok": False, "error": f"unknown op: {op}", "echo": msg}
        except Exception as e:  # pragma: no cover
            resp = {"ok": False, "error": f"exception: {e}"}

        try:
            sock.sendto(json.dumps(resp).encode("utf-8"), addr)
        except Exception:
            pass
