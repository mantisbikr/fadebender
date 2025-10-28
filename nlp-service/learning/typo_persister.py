"""Persistence module for saving learned typo corrections to config.

This module provides safe, async-friendly mechanisms to persist learned
typo corrections to the app_config.json file.
"""

from __future__ import annotations

import os
import sys
from typing import Dict


def persist_typos(corrections: Dict[str, str]) -> bool:
    """Persist typo corrections to app_config.json.

    This function:
    1. Adds corrections to in-memory config
    2. Saves config to disk
    3. Returns success/failure status

    Args:
        corrections: Dictionary mapping typo -> correction

    Returns:
        True if saved successfully, False otherwise
    """
    # Disable persistence if explicitly configured
    if os.getenv("DISABLE_TYPO_PERSISTENCE", "").lower() in ("1", "true", "yes"):
        return False

    if not corrections:
        return True  # Nothing to save

    try:
        # Import the SAME module instance that's already loaded in the server
        # This is critical - using importlib.util would create a separate instance
        # with its own _CONFIG variable, causing cache issues
        from server.config.app_config import add_typo_corrections, save_config

        # Add corrections to config (updates in-memory _CONFIG)
        add_typo_corrections(corrections)

        # Save to disk
        success = save_config()

        if success:
            print(f"[TYPO PERSISTENCE] Saved {len(corrections)} correction(s) to config")
        else:
            print(f"[TYPO PERSISTENCE] Failed to save corrections to config")

        return success

    except Exception as e:
        print(f"[TYPO PERSISTENCE] Error persisting typos: {e}")
        return False


def can_persist() -> bool:
    """Check if typo persistence is enabled and available.

    Returns:
        True if persistence is enabled and functional
    """
    # Check if disabled
    if os.getenv("DISABLE_TYPO_PERSISTENCE", "").lower() in ("1", "true", "yes"):
        return False

    try:
        # Try to import from the server's app_config module
        from server.config import app_config

        # Check if required functions exist
        return hasattr(app_config, 'add_typo_corrections') and hasattr(app_config, 'save_config')
    except Exception:
        return False
