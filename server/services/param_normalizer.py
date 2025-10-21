"""
Parameter normalization and fuzzy matching for device parameters.

Handles:
- Parameter aliases (Lo Cut → LowCut, Low Cut → LowCut)
- Typos and fuzzy matching
- Case-insensitive matching
- Canonical parameter name resolution from Firestore
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple
import re


# Global parameter aliases - common variations and typos
PARAM_ALIASES = {
    # Spacing variations
    "lo cut": "LowCut",
    "low cut": "LowCut",
    "lowcut": "LowCut",
    "hi cut": "HighCut",
    "high cut": "HighCut",
    "highcut": "HighCut",
    "dry wet": "Dry/Wet",
    "drywet": "Dry/Wet",
    "dry / wet": "Dry/Wet",

    # Common typos
    "feedbak": "Feedback",
    "feeback": "Feedback",
    "treshold": "Threshold",
    "threshhold": "Threshold",
    "predelay": "Pre-Delay",
    "pre delay": "Pre-Delay",
    "predelay": "Pre-Delay",

    # Shortened forms
    "pre": "Pre-Delay",
    "freq": "Frequency",
    "resonance": "Resonance",
    "res": "Resonance",
    "atk": "Attack",
    "rel": "Release",
    "comp": "Compression",
    "exp": "Expansion",

    # Case variations (will be handled by normalization)
    "decay": "Decay",
    "mode": "Mode",
    "type": "Type",
    "algorithm": "Algorithm",
    "quality": "Quality",
}


def _normalize_text(text: str) -> str:
    """Normalize text for comparison: lowercase, strip, collapse whitespace."""
    return re.sub(r"\s+", " ", text.lower().strip())


def _levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate Levenshtein distance between two strings."""
    if len(s1) < len(s2):
        return _levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            # j+1 instead of j since previous_row and current_row are one character longer than s2
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


class ParameterNormalizer:
    """Normalize and fuzzy match parameter names against canonical parameter lists."""

    def __init__(self, custom_aliases: Optional[Dict[str, str]] = None):
        """
        Initialize parameter normalizer.

        Args:
            custom_aliases: Optional additional aliases to merge with defaults
        """
        self.aliases = PARAM_ALIASES.copy()
        if custom_aliases:
            self.aliases.update(custom_aliases)

    def normalize_param(
        self,
        user_param: str,
        canonical_params: List[str],
        max_distance: int = 2
    ) -> Tuple[Optional[str], float]:
        """
        Normalize user-provided parameter name to canonical form.

        Args:
            user_param: User's parameter name (may have typos, aliases, etc.)
            canonical_params: List of canonical parameter names from device structure
            max_distance: Maximum Levenshtein distance for fuzzy matching

        Returns:
            Tuple of (canonical_param_name, confidence_score)
            Returns (None, 0.0) if no match found
        """
        if not user_param or not canonical_params:
            return None, 0.0

        normalized_input = _normalize_text(user_param)

        # Step 1: Check aliases first
        if normalized_input in self.aliases:
            alias_target = self.aliases[normalized_input]
            # Find exact match in canonical params (case-insensitive)
            for cparam in canonical_params:
                if _normalize_text(cparam) == _normalize_text(alias_target):
                    return cparam, 1.0  # Perfect match via alias

        # Step 2: Exact match (case-insensitive)
        for cparam in canonical_params:
            if _normalize_text(cparam) == normalized_input:
                return cparam, 1.0

        # Step 3: Fuzzy matching with Levenshtein distance
        best_match = None
        best_distance = float('inf')

        for cparam in canonical_params:
            canonical_norm = _normalize_text(cparam)
            distance = _levenshtein_distance(normalized_input, canonical_norm)

            if distance < best_distance:
                best_distance = distance
                best_match = cparam

        # Only return match if within acceptable distance
        if best_match and best_distance <= max_distance:
            # Calculate confidence: 1.0 for exact, decreasing with distance
            confidence = 1.0 - (best_distance / max(len(normalized_input), len(_normalize_text(best_match))))
            return best_match, confidence

        return None, 0.0

    def add_alias(self, alias: str, canonical: str):
        """Add a new parameter alias."""
        self.aliases[_normalize_text(alias)] = canonical

    def get_all_aliases(self) -> Dict[str, str]:
        """Get all registered aliases."""
        return self.aliases.copy()


# Global instance for convenience
_default_normalizer = ParameterNormalizer()


def normalize_parameter(
    user_param: str,
    canonical_params: List[str],
    max_distance: int = 2
) -> Tuple[Optional[str], float]:
    """
    Convenience function using default normalizer.

    Args:
        user_param: User's parameter name
        canonical_params: List of canonical parameter names from device
        max_distance: Maximum edit distance for fuzzy matching

    Returns:
        Tuple of (canonical_param_name, confidence_score)
    """
    return _default_normalizer.normalize_param(user_param, canonical_params, max_distance)
