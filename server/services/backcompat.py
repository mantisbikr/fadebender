"""Backward compatibility shims for legacy code.

This module provides compatibility functions for code that hasn't been
migrated to use the new request_op interface directly.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from server.services.ableton_client import request_op


def udp_request(msg: Dict[str, Any], timeout: float = 1.0) -> Optional[Any]:
    """Legacy UDP-style request shim.

    This is a backward compatibility function that wraps request_op for
    code that still uses the old udp_request interface.

    Args:
        msg: Message dict with 'op' key and additional params
        timeout: Request timeout in seconds

    Returns:
        Result from request_op, or None on error

    Example:
        >>> result = udp_request({"op": "get_transport"}, timeout=1.0)
    """
    try:
        op = str((msg or {}).get("op", ""))
        params = dict(msg or {})
        params.pop("op", None)
        return request_op(op, timeout=timeout, **params)
    except Exception:
        return None
