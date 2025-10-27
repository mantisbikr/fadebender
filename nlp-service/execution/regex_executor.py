"""Regex-based parsing executor."""

from __future__ import annotations

from typing import Dict, Any

from parsers import apply_typo_corrections, parse_mixer_command, parse_device_command
from execution.response_builder import build_question_response


def try_regex_parse(
    query: str,
    error_msg: str,
    model_preference: str | None
) -> Dict[str, Any] | None:
    """Try regex-based parsing.

    Args:
        query: User query text
        error_msg: Error message from previous attempts
        model_preference: User's model preference

    Returns:
        Intent dict if matched, None if no match
    """
    # Apply typo corrections and expand ordinal words
    q = apply_typo_corrections(query)

    # Try mixer commands first (most common: volume, pan, solo, mute, sends)
    result = parse_mixer_command(q, query, error_msg, model_preference)
    if result:
        return result

    # Try device commands (reverb, delay, compressor, etc.)
    result = parse_device_command(q, query, error_msg, model_preference)
    if result:
        return result

    # Questions about problems (treat as help-style queries)
    if any(phrase in q for phrase in [
        "too soft", "too quiet", "can't hear", "how to", "what does",
        "weak", "thin", "muddy", "boomy", "harsh", "dull"
    ]):
        return build_question_response(query, error_msg, model_preference)

    # No match
    return None
