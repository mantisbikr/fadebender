"""Feature flags for safe rollout of new features.

Environment variables control feature flags. Set to "1", "true", "yes", or "on" to enable.

Example:
    export FB_FEATURE_NEW_ERROR_HANDLING=1
    export FB_FEATURE_NEW_ROUTING=0

Usage:
    from server.config.feature_flags import is_enabled

    if is_enabled("new_routing"):
        # Use new routing logic
    else:
        # Use legacy routing
"""

from __future__ import annotations

import os
from typing import Dict


# Default flag states (conservative defaults - new features off by default)
_DEFAULT_FLAGS: Dict[str, bool] = {
    # Error handling is already integrated, so it's on by default
    "new_error_handling": True,
    # Disabled: new_routing uses lightweight router with empty devices, breaking NLP
    "new_routing": False,
    "strict_validation": False,
    "rate_limiting": False,
}


def _parse_bool(value: str | None) -> bool | None:
    """Parse string to boolean. Returns None if value is None or empty."""
    if value is None or value.strip() == "":
        return None
    return value.strip().lower() in ("1", "true", "yes", "on")


def is_enabled(flag_name: str, default: bool | None = None) -> bool:
    """Check if a feature flag is enabled.

    Args:
        flag_name: Name of the feature flag (e.g., "new_routing")
        default: Optional override for default value. If None, uses _DEFAULT_FLAGS.

    Returns:
        True if enabled, False otherwise.

    Environment variable format: FB_FEATURE_{FLAG_NAME_UPPER}
    Example: FB_FEATURE_NEW_ROUTING=1
    """
    # Normalize flag name
    normalized = flag_name.lower().replace("-", "_")

    # Check environment variable
    env_key = f"FB_FEATURE_{normalized.upper()}"
    env_value = _parse_bool(os.getenv(env_key))

    if env_value is not None:
        return env_value

    # Use provided default or fall back to _DEFAULT_FLAGS
    if default is not None:
        return default

    return _DEFAULT_FLAGS.get(normalized, False)


def get_all_flags() -> Dict[str, bool]:
    """Get all feature flags and their current states.

    Returns:
        Dictionary mapping flag names to their enabled state.
    """
    flags = {}
    for flag_name in _DEFAULT_FLAGS.keys():
        flags[flag_name] = is_enabled(flag_name)
    return flags


def get_flag_status() -> Dict[str, Dict[str, bool | str]]:
    """Get detailed flag status including source (env vs default).

    Returns:
        Dictionary with flag details including value and source.
    """
    status = {}
    for flag_name in _DEFAULT_FLAGS.keys():
        env_key = f"FB_FEATURE_{flag_name.upper()}"
        env_value = os.getenv(env_key)
        has_env = env_value is not None and env_value.strip() != ""

        status[flag_name] = {
            "enabled": is_enabled(flag_name),
            "source": "environment" if has_env else "default",
            "env_var": env_key,
        }
    return status
