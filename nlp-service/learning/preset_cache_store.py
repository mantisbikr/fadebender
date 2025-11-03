"""Firestore-backed preset cache for dynamic device/category recognition.

Loads all presets from Firestore and auto-generates aliases for NLP parsing.
Skips 'unknown_*' presets which need manual learning.

Cache Structure:
- categories: Set of device types (e.g., {'reverb', 'delay', 'eq'})
- device_aliases: Dict mapping aliases to canonical device names
  Example: {'valhalla': 'Valhalla VintageVerb', 'vintage verb': 'Valhalla VintageVerb'}
"""

from __future__ import annotations

import os
import time
import re
from typing import Dict, Set, Tuple

# Global cache
_CATEGORY_CACHE: Set[str] | None = None
_DEVICE_ALIAS_CACHE: Dict[str, str] | None = None
_CACHE_TIMESTAMP: float = 0
_FIRESTORE_CLIENT = None
_FIRESTORE_ENABLED = False

# Just-in-time device lookup cache (alias -> device info)
_JIT_DEVICE_CACHE: Dict[str, Dict[str, str] | None] = {}

# Configuration
TTL_SECONDS = 60  # Refresh from Firestore every 60 seconds

# Only load devices with these structure signatures (fully learned devices)
LEARNED_STRUCTURE_SIGNATURES = {
    '9bfcc8b6e739d9675c03f6fe0664cfada9ef7df1',  # Delay
    '64ccfc236b79371d0b45e913f81bf0f3a55c6db9',  # Reverb
    'd554752f4be9eee62197c37b45b1c22237842c37',  # Amp
}


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
        if database_id and database_id != "(default)":
            _FIRESTORE_CLIENT = firestore.Client(database=database_id)
            print(f"[PRESET CACHE] Firestore initialized (database: {database_id})")
        elif project_id:
            _FIRESTORE_CLIENT = firestore.Client(project=project_id)
            print(f"[PRESET CACHE] Firestore initialized (project: {project_id})")
        else:
            _FIRESTORE_CLIENT = firestore.Client()
            print("[PRESET CACHE] Firestore initialized (default)")

        _FIRESTORE_ENABLED = True
    except Exception as e:
        print(f"[PRESET CACHE] Firestore initialization failed: {e}")
        _FIRESTORE_CLIENT = None
        _FIRESTORE_ENABLED = False


def _generate_device_aliases(device_name: str) -> list[str]:
    """Auto-generate aliases for a device name.

    Args:
        device_name: Full device name (e.g., "FabFilter Pro-Q 3", "Valhalla VintageVerb")

    Returns:
        List of aliases (lowercase) including:
        - Full name: "fabfilter pro-q 3"
        - Without version: "fabfilter pro-q"
        - Short forms: "pro-q 3", "pro-q"
        - Abbreviated: "proq"
        - Brand only: "fabfilter"

    Examples:
        >>> _generate_device_aliases("FabFilter Pro-Q 3")
        ['fabfilter pro-q 3', 'fabfilter pro-q', 'pro-q 3', 'pro-q', 'proq', 'fabfilter']

        >>> _generate_device_aliases("Valhalla VintageVerb")
        ['valhalla vintageverb', 'vintageverb', 'vintage verb', 'valhalla']
    """
    name = device_name.lower()
    aliases = [name]  # Always include full name

    # Tokenize on spaces, hyphens, underscores
    tokens = re.split(r'[\s\-_]+', name)

    # Remove version numbers from tokens
    tokens_no_version = [t for t in tokens if not re.match(r'^\d+(\.\d+)?$', t)]

    # Full name without version
    if len(tokens_no_version) < len(tokens):
        aliases.append(' '.join(tokens_no_version))

    # Brand + product (skip first word if it's a brand)
    # E.g., "FabFilter Pro-Q" → ["Pro-Q", "FabFilter"]
    if len(tokens) > 1:
        # Product name (everything after first token)
        product = ' '.join(tokens[1:])
        if product:
            aliases.append(product)

        # Product without version
        product_no_version = ' '.join(tokens_no_version[1:])
        if product_no_version and product_no_version != product:
            aliases.append(product_no_version)

        # Abbreviated (remove spaces/hyphens): "Pro-Q" → "proq"
        abbreviated = ''.join(tokens_no_version[1:])
        if abbreviated and len(abbreviated) >= 3:
            aliases.append(abbreviated)

        # Brand only (first token)
        brand = tokens[0]
        if len(brand) >= 3:  # Skip very short brands
            aliases.append(brand)

    # Handle camelCase splitting (e.g., "VintageVerb" → "vintage verb")
    if not ' ' in name and not '-' in name:
        # Split on uppercase letters
        camel_split = re.sub(r'([A-Z])', r' \1', device_name).strip().lower()
        if camel_split != name and len(camel_split.split()) > 1:
            aliases.append(camel_split)

    # Remove duplicates and empty strings, preserve order
    seen = set()
    result = []
    for alias in aliases:
        alias = alias.strip()
        if alias and alias not in seen and len(alias) >= 2:
            seen.add(alias)
            result.append(alias)

    return result


def _load_from_firestore() -> Tuple[Set[str], Dict[str, str]]:
    """Load all presets from Firestore and extract categories + device aliases.

    Returns:
        Tuple of (categories, device_aliases)
        - categories: Set of device types (e.g., {'reverb', 'delay'})
        - device_aliases: Dict mapping alias → canonical device name
    """
    _init_firestore()

    if not _FIRESTORE_ENABLED or not _FIRESTORE_CLIENT:
        return set(), {}

    try:
        # Load all presets
        presets_ref = _FIRESTORE_CLIENT.collection("presets")
        presets = list(presets_ref.stream())

        categories = set()
        device_aliases = {}

        for preset in presets:
            preset_id = preset.id
            data = preset.to_dict()

            # Skip unknown_* presets (need manual learning)
            if preset_id.startswith('unknown_'):
                continue

            device_name = data.get('device_name')
            if device_name and device_name.lower().startswith('unknown'):
                continue

            # Only load devices with learned structure signatures
            structure_sig = data.get('structure_signature')
            if structure_sig not in LEARNED_STRUCTURE_SIGNATURES:
                continue

            # Extract category (device type)
            category = data.get('category')
            if category:
                categories.add(category.lower())

            # Generate device aliases
            if device_name:
                canonical = device_name  # Keep original casing for canonical
                aliases = _generate_device_aliases(device_name)

                for alias in aliases:
                    # Only add if not already mapped (first occurrence wins)
                    if alias not in device_aliases:
                        device_aliases[alias] = canonical

        print(f"[PRESET CACHE] Loaded {len(presets)} presets: {len(categories)} categories, {len(device_aliases)} device aliases")
        return categories, device_aliases

    except Exception as e:
        print(f"[PRESET CACHE] Error loading from Firestore: {e}")
        return set(), {}


def get_device_categories() -> Set[str]:
    """Get all device categories (types) with TTL-based caching.

    Returns:
        Set of device types (e.g., {'reverb', 'delay', 'eq', 'compressor'})
    """
    global _CATEGORY_CACHE, _DEVICE_ALIAS_CACHE, _CACHE_TIMESTAMP

    now = time.time()

    # Initialize timestamp if this is the first call
    if _CACHE_TIMESTAMP == 0:
        _CACHE_TIMESTAMP = now
        cache_age = TTL_SECONDS + 1  # Force initial load
    else:
        cache_age = now - _CACHE_TIMESTAMP

    # Refresh if cache is stale or empty
    if _CATEGORY_CACHE is None or cache_age > TTL_SECONDS:
        _CATEGORY_CACHE, _DEVICE_ALIAS_CACHE = _load_from_firestore()
        _CACHE_TIMESTAMP = now

        if _CATEGORY_CACHE:
            print(f"[PRESET CACHE] Refreshed cache (age: {cache_age:.1f}s)")

    return _CATEGORY_CACHE or set()


def get_device_aliases() -> Dict[str, str]:
    """Get device name aliases with TTL-based caching.

    Returns:
        Dictionary mapping alias → canonical device name
        Example: {'proq': 'FabFilter Pro-Q 3', 'valhalla': 'Valhalla VintageVerb'}
    """
    global _CATEGORY_CACHE, _DEVICE_ALIAS_CACHE, _CACHE_TIMESTAMP

    now = time.time()

    # Initialize timestamp if this is the first call
    if _CACHE_TIMESTAMP == 0:
        _CACHE_TIMESTAMP = now
        cache_age = TTL_SECONDS + 1  # Force initial load
    else:
        cache_age = now - _CACHE_TIMESTAMP

    # Refresh if cache is stale or empty
    if _DEVICE_ALIAS_CACHE is None or cache_age > TTL_SECONDS:
        _CATEGORY_CACHE, _DEVICE_ALIAS_CACHE = _load_from_firestore()
        _CACHE_TIMESTAMP = now

    return _DEVICE_ALIAS_CACHE or {}


def force_refresh() -> Tuple[Set[str], Dict[str, str]]:
    """Force refresh cache from Firestore (useful for testing).

    Returns:
        Tuple of (categories, device_aliases)
    """
    global _CATEGORY_CACHE, _DEVICE_ALIAS_CACHE, _CACHE_TIMESTAMP

    _CATEGORY_CACHE, _DEVICE_ALIAS_CACHE = _load_from_firestore()
    _CACHE_TIMESTAMP = time.time()

    return _CATEGORY_CACHE or set(), _DEVICE_ALIAS_CACHE or {}


def lookup_device_by_name(device_name: str) -> Dict[str, str] | None:
    """Just-in-time lookup of device by name from Firestore.

    Queries Firestore for a device matching the given name (case-insensitive).
    Results are cached in memory to avoid repeated queries.

    Args:
        device_name: Device name or alias to lookup (e.g., "valhalla", "pro-q")

    Returns:
        Device info dict with keys: 'canonical_name', 'category', 'structure_signature'
        Returns None if device not found or not a learned device.

    Example:
        >>> lookup_device_by_name("valhalla")
        {'canonical_name': 'Valhalla VintageVerb', 'category': 'reverb', 'structure_signature': '...'}
    """
    global _JIT_DEVICE_CACHE

    # Normalize search key (lowercase, strip whitespace)
    search_key = device_name.lower().strip()

    # Check cache first
    if search_key in _JIT_DEVICE_CACHE:
        return _JIT_DEVICE_CACHE[search_key]

    # Initialize Firestore if needed
    _init_firestore()

    if not _FIRESTORE_ENABLED or not _FIRESTORE_CLIENT:
        _JIT_DEVICE_CACHE[search_key] = None
        return None

    try:
        # Query Firestore for presets matching device name (case-insensitive)
        presets_ref = _FIRESTORE_CLIENT.collection("presets")

        # We need to query all presets and filter in Python (Firestore doesn't support case-insensitive)
        # To optimize, we could use .where('device_name', '>=', ...) range queries
        # But for now, let's query all learned devices only

        query = presets_ref.where('structure_signature', 'in', list(LEARNED_STRUCTURE_SIGNATURES))
        results = list(query.stream())

        # Search for matching device name or alias
        for preset in results:
            data = preset.to_dict()
            preset_id = preset.id

            # Skip unknown presets
            if preset_id.startswith('unknown_'):
                continue

            device_name_canonical = data.get('device_name')
            if not device_name_canonical or device_name_canonical.lower().startswith('unknown'):
                continue

            # Generate aliases and check for match
            aliases = _generate_device_aliases(device_name_canonical)

            if search_key in [a.lower() for a in aliases] or search_key == device_name_canonical.lower():
                # Found a match!
                result = {
                    'canonical_name': device_name_canonical,
                    'category': data.get('category', '').lower(),
                    'structure_signature': data.get('structure_signature', '')
                }
                _JIT_DEVICE_CACHE[search_key] = result
                print(f"[PRESET CACHE JIT] Found device: {search_key} -> {device_name_canonical} ({result['category']})")
                return result

        # Not found - cache the negative result
        _JIT_DEVICE_CACHE[search_key] = None
        print(f"[PRESET CACHE JIT] Device not found: {search_key}")
        return None

    except Exception as e:
        print(f"[PRESET CACHE JIT] Error looking up device '{device_name}': {e}")
        _JIT_DEVICE_CACHE[search_key] = None
        return None
