from __future__ import annotations

from typing import Any, Dict, Optional

from server.ableton.client_udp import request as udp_request, send as udp_send  # noqa: F401


def request_op(op: str, timeout: float = 1.0, **params: Any) -> Optional[Dict[str, Any]]:
    """Thin wrapper around udp_request with consistent shape.

    Returns the raw response (dict) from the remote script or None on failure.
    """
    msg: Dict[str, Any] = {"op": op}
    if params:
        msg.update(params)
    return udp_request(msg, timeout=timeout)


def ok(resp: Optional[Dict[str, Any]]) -> bool:
    return bool(resp and (resp.get("ok", True)))


def data_or_raw(resp: Optional[Dict[str, Any]]) -> Any:
    if not resp:
        return None
    data = resp.get("data") if isinstance(resp, dict) else None
    return data if data is not None else resp


# Convenience domain helpers used by routers

def get_transport(timeout: float = 1.0) -> Dict[str, Any]:
    resp = request_op("get_transport", timeout=timeout)
    if not resp:
        return {"ok": False, "error": "no response"}
    data = data_or_raw(resp)
    return {"ok": True, "data": data}


def set_transport(action: str, value: Optional[float] = None, timeout: float = 1.0) -> Dict[str, Any]:
    msg: Dict[str, Any] = {"action": str(action)}
    if value is not None:
        msg["value"] = float(value)
    resp = request_op("set_transport", timeout=timeout, **msg)
    if not resp:
        return {"ok": False, "error": "no response"}
    return resp if isinstance(resp, dict) else {"ok": True, "data": resp}

