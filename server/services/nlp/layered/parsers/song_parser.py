"""Parse song-level commands (undo/redo, info, locators)."""

import re
from typing import Optional, Dict, Any


def parse_song_undo(text: str) -> Optional[Dict[str, Any]]:
    """Parse undo command.

    Examples:
        "undo"
        "undo last change"
    """
    pattern = r"^undo(?:\s+last)?(?:\s+change)?$"
    if re.match(pattern, text, re.IGNORECASE):
        return {
            "domain": "song",
            "action": "undo"
        }
    return None


def parse_song_redo(text: str) -> Optional[Dict[str, Any]]:
    """Parse redo command.

    Examples:
        "redo"
        "redo that"
    """
    pattern = r"^redo(?:\s+that)?$"
    if re.match(pattern, text, re.IGNORECASE):
        return {
            "domain": "song",
            "action": "redo"
        }
    return None


def parse_song_info(text: str) -> Optional[Dict[str, Any]]:
    """Parse song info queries.

    Examples:
        "what's the song name"
        "show song info"
        "what's the tempo"
    """
    patterns = [
        r"^(?:what'?s|show|get)\s+(?:the\s+)?song\s+(?:name|info)$",
        r"^what'?s\s+(?:the\s+)?(?:tempo|song\s+name|time\s+signature)$"
    ]
    for pattern in patterns:
        if re.match(pattern, text, re.IGNORECASE):
            return {
                "domain": "song",
                "action": "get_info"
            }
    return None


def parse_jump_locator(text: str) -> Optional[Dict[str, Any]]:
    """Parse jump to locator command.

    Examples:
        "jump to locator 2"
        "go to intro"
        "jump to verse"
    """
    # By index
    m = re.match(r"^(?:jump\s+to|go\s+to)\s+locator\s+(\d+)$", text, re.IGNORECASE)
    if m:
        return {
            "domain": "song",
            "action": "jump_locator",
            "locator_index": int(m.group(1))
        }

    # By name (greedy - capture everything after jump/go)
    m = re.match(r"^(?:jump\s+to|go\s+to)\s+(.+)$", text, re.IGNORECASE)
    if m:
        return {
            "domain": "song",
            "action": "jump_locator",
            "locator_name": m.group(1).strip()
        }

    return None


def parse_rename_locator(text: str) -> Optional[Dict[str, Any]]:
    """Parse rename locator command.

    Examples:
        "rename locator 1 to intro"
        "call locator 2 verse"
    """
    m = re.match(r"^(?:rename|call)\s+locator\s+(\d+)\s+(?:to\s+)?(.+)$", text, re.IGNORECASE)
    if m:
        return {
            "domain": "song",
            "action": "rename_locator",
            "locator_index": int(m.group(1)),
            "new_name": m.group(2).strip()
        }
    return None


def parse_list_locators(text: str) -> Optional[Dict[str, Any]]:
    """Parse list locators command.

    Examples:
        "list locators"
        "show locators"
    """
    if re.match(r"^(?:list|show)\s+locators?$", text, re.IGNORECASE):
        return {
            "domain": "song",
            "action": "list_locators"
        }
    return None


def parse_song(text: str) -> Optional[Dict[str, Any]]:
    """Try all song-level parsers in order.

    Returns parsed intent or None.
    """
    parsers = [
        parse_song_undo,
        parse_song_redo,
        parse_song_info,
        parse_jump_locator,
        parse_rename_locator,
        parse_list_locators
    ]

    for parser in parsers:
        result = parser(text)
        if result:
            return result

    return None
