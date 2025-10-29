"""Persistence module for saving learned typo corrections to config.

This module provides safe, async-friendly mechanisms to persist learned
typo corrections to the app_config.json file.
"""

from __future__ import annotations

import os
import sys
from typing import Dict


def persist_typos(corrections: Dict[str, str]) -> bool:
    """Persist typo corrections to Firestore.

    This function:
    1. Saves corrections to Firestore (instant availability)
    2. Updates in-memory cache immediately
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
        # Primary: Save to Firestore with instant cache update
        from learning.typo_cache_store import save_typo_corrections

        success = save_typo_corrections(corrections)

        if success:
            print(f"[TYPO PERSISTENCE] Saved {len(corrections)} correction(s) to Firestore")
        else:
            print(f"[TYPO PERSISTENCE] Failed to save corrections to Firestore")

        return success

    except Exception as e:
        print(f"[TYPO PERSISTENCE] Error persisting typos: {e}")

        # Fallback: Try saving to local config file
        try:
            from server.config.app_config import add_typo_corrections, save_config
            add_typo_corrections(corrections)
            fallback_success = save_config()

            if fallback_success:
                print(f"[TYPO PERSISTENCE] Fallback: Saved to local config file")

            return fallback_success
        except Exception as fallback_error:
            print(f"[TYPO PERSISTENCE] Fallback also failed: {fallback_error}")
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
