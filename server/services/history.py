from __future__ import annotations

import time
from typing import Any, Callable, Dict, List, Optional, Tuple

# Simple shared state for mixer/device history and throttling
MIN_INTERVAL_SEC = 0.05  # 50ms per target key
UNDO_STACK: List[Dict[str, Any]] = []
REDO_STACK: List[Dict[str, Any]] = []
DEVICE_BYPASS_CACHE: Dict[Tuple[int, int], float] = {}
LAST_SENT: Dict[str, float] = {}
LAST_TS: Dict[str, float] = {}


def _key(field: str, track_index: int) -> str:
    return f"mixer:{field}:{track_index}"


def _rate_limited(field: str, track_index: int) -> bool:
    k = _key(field, track_index)
    now = time.time()
    last = LAST_TS.get(k, 0.0)
    if now - last < MIN_INTERVAL_SEC:
        return True
    LAST_TS[k] = now
    return False


def undo_last(
    udp_request_fn: Callable[..., Any],
    *,
    schedule_emit_fn: Optional[Callable[[Dict[str, Any]], Any]] = None,
) -> Dict[str, Any]:
    """Undo the last successful change (mixer or device param) if previous value is known."""
    while UNDO_STACK:
        entry = UNDO_STACK.pop()
        etype = entry.get("type", "mixer")
        if etype == "mixer":
            prev = entry.get("prev")
            track_index = entry.get("track_index")
            field = entry.get("field")
            if prev is None or track_index is None or field not in ("volume", "pan"):
                continue
            msg = {
                "op": "set_mixer",
                "track_index": int(track_index),
                "field": field,
                "value": float(prev),
            }
            resp = udp_request_fn(msg, timeout=1.0)
            if resp and resp.get("ok", True):
                LAST_SENT[_key(field, int(track_index))] = float(prev)
                REDO_STACK.append(
                    {
                        "type": "mixer",
                        "key": entry.get("key"),
                        "field": field,
                        "track_index": track_index,
                        "prev": msg["value"],
                        "new": entry.get("new"),
                    }
                )
                return {"ok": True, "undone": entry, "resp": resp}
            return {"ok": False, "error": "undo_send_failed", "attempt": entry}
        if etype == "device_param":
            prev = entry.get("prev")
            ri = entry.get("return_index")
            di = entry.get("device_index")
            pi = entry.get("param_index")
            if prev is None or ri is None or di is None or pi is None:
                continue
            msg = {
                "op": "set_return_device_param",
                "return_index": int(ri),
                "device_index": int(di),
                "param_index": int(pi),
                "value": float(prev),
            }
            resp = udp_request_fn(msg, timeout=1.0)
            if resp and resp.get("ok", True):
                REDO_STACK.append(
                    {
                        "type": "device_param",
                        "return_index": ri,
                        "device_index": di,
                        "param_index": pi,
                        "prev": entry.get("new"),
                        "new": prev,
                    }
                )
                if schedule_emit_fn is not None:
                    try:
                        schedule_emit_fn(
                            {
                                "event": "device_param_restored",
                                "return_index": ri,
                                "device_index": di,
                            }
                        )
                    except Exception:
                        pass
                return {"ok": True, "undone": entry, "resp": resp}
            return {"ok": False, "error": "undo_send_failed", "attempt": entry}
    return {"ok": False, "error": "nothing_to_undo"}


def redo_last(
    udp_request_fn: Callable[..., Any],
) -> Dict[str, Any]:
    """Re-apply the last undone change (mixer or device param) if available."""
    while REDO_STACK:
        entry = REDO_STACK.pop()
        etype = entry.get("type", "mixer")
        if etype == "mixer":
            new_val = entry.get("new")
            track_index = entry.get("track_index")
            field = entry.get("field")
            if new_val is None or track_index is None or field not in ("volume", "pan"):
                continue
            msg = {
                "op": "set_mixer",
                "track_index": int(track_index),
                "field": field,
                "value": float(new_val),
            }
            resp = udp_request_fn(msg, timeout=1.0)
            if resp and resp.get("ok", True):
                LAST_SENT[_key(field, int(track_index))] = float(new_val)
                UNDO_STACK.append(
                    {
                        "type": "mixer",
                        "key": entry.get("key"),
                        "field": field,
                        "track_index": track_index,
                        "prev": entry.get("prev"),
                        "new": new_val,
                    }
                )
                return {"ok": True, "redone": entry, "resp": resp}
            return {"ok": False, "error": "redo_send_failed", "attempt": entry}
        if etype == "device_param":
            new_val = entry.get("new")
            ri = entry.get("return_index")
            di = entry.get("device_index")
            pi = entry.get("param_index")
            if new_val is None or ri is None or di is None or pi is None:
                continue
            msg = {
                "op": "set_return_device_param",
                "return_index": int(ri),
                "device_index": int(di),
                "param_index": int(pi),
                "value": float(new_val),
            }
            resp = udp_request_fn(msg, timeout=1.0)
            if resp and resp.get("ok", True):
                UNDO_STACK.append(
                    {
                        "type": "device_param",
                        "return_index": ri,
                        "device_index": di,
                        "param_index": pi,
                        "prev": entry.get("prev"),
                        "new": new_val,
                    }
                )
                return {"ok": True, "redone": entry, "resp": resp}
            return {"ok": False, "error": "redo_send_failed", "attempt": entry}
    return {"ok": False, "error": "nothing_to_redo"}


def history_state() -> Dict[str, Any]:
    return {
        "ok": True,
        "undo_available": bool(UNDO_STACK),
        "redo_available": bool(REDO_STACK),
        "undo_depth": len(UNDO_STACK),
        "redo_depth": len(REDO_STACK),
    }
