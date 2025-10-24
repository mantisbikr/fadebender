from __future__ import annotations

from fastapi import HTTPException
from typing import Optional


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


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


def _resolve_return_index(return_index: Optional[int] = None, return_ref: Optional[str] = None) -> int:
    if return_ref is not None and return_index is None:
        return _letter_to_index(return_ref)
    if return_index is not None:
        idx = int(return_index)
        if idx < 0:
            raise HTTPException(400, "return_index_must_be_at_least_0")
        return idx
    raise HTTPException(400, "return_index_or_return_ref_required")


def _resolve_send_index(send_index: Optional[int] = None, send_ref: Optional[str] = None) -> int:
    if send_ref is not None and send_index is None:
        return _letter_to_index(send_ref)
    if send_index is not None:
        idx = int(send_index)
        if idx < 0:
            raise HTTPException(400, "send_index_must_be_at_least_0")
        return idx
    raise HTTPException(400, "send_index_or_send_ref_required")
