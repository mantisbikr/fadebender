"""Config helper functions for backward compatibility and convenience.

This module provides helper functions that wrap the new Pydantic Settings
while maintaining backward compatibility with existing code.
"""

from __future__ import annotations

import os
from typing import Optional

from server.config.settings import get_settings, get_cors_origins as _get_cors_origins
from server.config.app_config import get_app_config, get_debug_settings


def status_ttl_seconds(default: float = 1.0) -> float:
    """Get status cache TTL in seconds.

    Checks (in order):
    1. Pydantic Settings (FB_STATUS_TTL_SECONDS env var)
    2. Legacy app_config.json
    3. Default value

    Args:
        default: Default value if not configured

    Returns:
        TTL in seconds (>= 0.0)
    """
    try:
        settings = get_settings()
        return max(0.0, settings.status_ttl_seconds)
    except Exception:
        # Fall back to legacy config
        try:
            cfg = get_app_config()
            v = cfg.get("server", {}).get("status_ttl_seconds", default)
            return max(0.0, float(v))
        except Exception:
            return default


def cors_origins() -> list[str]:
    """Get CORS origins list.

    Returns:
        List of allowed CORS origins, or ["*"] if allow_all is enabled.
    """
    return _get_cors_origins()


def debug_enabled(name: str) -> bool:
    """Check if a debug feature is enabled.

    Checks both environment variables and debug settings in config.

    Args:
        name: Debug feature name (e.g., "sse", "auto_capture")

    Returns:
        True if the debug feature is enabled, False otherwise.
    """
    try:
        if name == "sse":
            env = str(os.getenv("FB_DEBUG_SSE", "")).lower() in ("1", "true", "yes", "on")
            cfg = get_debug_settings().get("sse", False)
            return bool(env or cfg)
        if name == "auto_capture":
            env = str(os.getenv("FB_DEBUG_AUTO_CAPTURE", "")).lower() in ("1", "true", "yes", "on")
            cfg = get_debug_settings().get("auto_capture", False)
            return bool(env or cfg)
    except Exception:
        return False
    return False


# Legacy aliases for backward compatibility
_status_ttl_seconds = status_ttl_seconds
_cors_origins = cors_origins
_debug_enabled = debug_enabled
