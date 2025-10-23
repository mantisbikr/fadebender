from __future__ import annotations

from fastapi import HTTPException


def _letter_to_index(letter: str) -> int:
    """Convert a letter reference (e.g., 'A', 'B') to a 0-based index.

    Examples:
        'A' or 'a' -> 0
        'B' or 'b' -> 1

    Raises HTTPException(400) if the input is not a single alphabetic character.
    """
    if letter is None:
        raise HTTPException(400, "invalid_letter_reference:None")
    s = str(letter).strip().upper()
    if len(s) != 1 or not s.isalpha():
        raise HTTPException(400, f"invalid_letter_reference:{letter}")
    return ord(s) - ord('A')

