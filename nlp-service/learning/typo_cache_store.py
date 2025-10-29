"""Firestore-backed typo corrections cache with TTL.

Provides fast in-memory reads with automatic refresh from Firestore.
Ensures learned typos are immediately available across server instances.
"""

from __future__ import annotations

import os
import time
from typing import Dict

# Global cache
_TYPO_CACHE: Dict[str, str] | None = None
_CACHE_TIMESTAMP: float = 0
_FIRESTORE_CLIENT = None
_FIRESTORE_ENABLED = False

# Configuration
TTL_SECONDS = 30  # Refresh from Firestore every 30 seconds


def _init_firestore():
    """Initialize Firestore client (lazy initialization)."""
    global _FIRESTORE_CLIENT, _FIRESTORE_ENABLED

    if _FIRESTORE_CLIENT is not None:
        return  # Already initialized

    try:
        from google.cloud import firestore

        project_id = os.getenv("FIRESTORE_PROJECT_ID")
        database_id = os.getenv("FIRESTORE_DATABASE_ID", "(default)")

        # Initialize client with database parameter
        if project_id and database_id and database_id != "(default)":
            _FIRESTORE_CLIENT = firestore.Client(project=project_id, database=database_id)
        elif project_id:
            _FIRESTORE_CLIENT = firestore.Client(project=project_id)
        else:
            _FIRESTORE_CLIENT = firestore.Client()

        _FIRESTORE_ENABLED = True
        print("[TYPO CACHE] Firestore initialized successfully")
    except Exception as e:
        print(f"[TYPO CACHE] Firestore initialization failed: {e}")
        _FIRESTORE_CLIENT = None
        _FIRESTORE_ENABLED = False


def _load_from_firestore() -> Dict[str, str]:
    """Load all typo corrections from Firestore.

    Returns:
        Dictionary mapping typo -> correction
    """
    _init_firestore()

    if not _FIRESTORE_ENABLED or not _FIRESTORE_CLIENT:
        return {}

    try:
        doc_ref = _FIRESTORE_CLIENT.collection("nlp_config").document("typo_corrections")
        doc = doc_ref.get()

        if doc.exists:
            data = doc.to_dict()
            corrections = data.get("corrections", {})
            print(f"[TYPO CACHE] Loaded {len(corrections)} corrections from Firestore")
            return corrections
        else:
            print("[TYPO CACHE] No typo corrections document found in Firestore")
            return {}
    except Exception as e:
        print(f"[TYPO CACHE] Error loading from Firestore: {e}")
        return {}


def get_typo_corrections() -> Dict[str, str]:
    """Get typo corrections with TTL-based caching.

    Returns cached corrections if still fresh (< 30s old),
    otherwise refreshes from Firestore.

    Returns:
        Dictionary mapping typo -> correction (e.g., {"paning": "pan"})
    """
    global _TYPO_CACHE, _CACHE_TIMESTAMP

    now = time.time()

    # Initialize timestamp if this is the first call
    if _CACHE_TIMESTAMP == 0:
        _CACHE_TIMESTAMP = now
        cache_age = TTL_SECONDS + 1  # Force initial load
    else:
        cache_age = now - _CACHE_TIMESTAMP

    # Refresh if cache is stale or empty
    if _TYPO_CACHE is None or cache_age > TTL_SECONDS:
        _TYPO_CACHE = _load_from_firestore()
        _CACHE_TIMESTAMP = now

        if _TYPO_CACHE:
            print(f"[TYPO CACHE] Refreshed cache (age: {cache_age:.1f}s, {len(_TYPO_CACHE)} corrections)")

    return _TYPO_CACHE or {}


def save_typo_corrections(corrections: Dict[str, str]) -> bool:
    """Save typo corrections to Firestore.

    Merges new corrections with existing ones and updates cache immediately.

    Args:
        corrections: Dictionary mapping typo -> correction

    Returns:
        True if saved successfully, False otherwise
    """
    global _TYPO_CACHE, _CACHE_TIMESTAMP

    _init_firestore()

    if not _FIRESTORE_ENABLED or not _FIRESTORE_CLIENT:
        print("[TYPO CACHE] Firestore not enabled, cannot save")
        return False

    if not corrections:
        return True  # Nothing to save

    try:
        doc_ref = _FIRESTORE_CLIENT.collection("nlp_config").document("typo_corrections")

        # Get existing corrections
        doc = doc_ref.get()
        if doc.exists:
            existing = doc.to_dict().get("corrections", {})
        else:
            existing = {}

        # Merge new corrections
        merged = {**existing, **corrections}

        # Save to Firestore
        doc_ref.set({"corrections": merged}, merge=True)

        # Update cache immediately
        _TYPO_CACHE = merged
        _CACHE_TIMESTAMP = time.time()

        print(f"[TYPO CACHE] Saved {len(corrections)} correction(s) to Firestore")
        return True

    except Exception as e:
        print(f"[TYPO CACHE] Error saving to Firestore: {e}")
        return False


def force_refresh() -> Dict[str, str]:
    """Force refresh cache from Firestore (useful for testing).

    Returns:
        Updated typo corrections dictionary
    """
    global _TYPO_CACHE, _CACHE_TIMESTAMP

    _TYPO_CACHE = _load_from_firestore()
    _CACHE_TIMESTAMP = time.time()

    return _TYPO_CACHE or {}
