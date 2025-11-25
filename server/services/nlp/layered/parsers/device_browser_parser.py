"""Parse device browser commands (list/show devices)."""

import re
from typing import Optional, Dict, Any


def parse_device_browser(text: str) -> Optional[Dict[str, Any]]:
    """Parse device browser commands.

    Examples:
        "list devices"
        "show devices"
        "list audio effects"
        "list audio effects devices"
        "show midi effects"
        "list instruments"
        "show all devices"

    Returns:
        Intent dict with domain="device_browser", action="list", category="all"|"audio_effects"|"midi_effects"|"instruments"
    """
    # Normalize text
    text_lower = text.lower().strip()

    # Pattern: (list|show) [all] (audio effects|midi effects|instruments) [devices]
    # Or: (list|show) [all] devices

    # Try specific category patterns first
    patterns = [
        (r"^(?:list|show)\s+(?:all\s+)?audio\s+effects?(?:\s+devices?)?$", "audio_effects"),
        (r"^(?:list|show)\s+(?:all\s+)?midi\s+effects?(?:\s+devices?)?$", "midi_effects"),
        (r"^(?:list|show)\s+(?:all\s+)?instruments?(?:\s+devices?)?$", "instruments"),
        (r"^(?:list|show)\s+(?:all\s+)?devices?$", "all"),
    ]

    for pattern, category in patterns:
        if re.match(pattern, text_lower):
            return {
                "domain": "device_browser",
                "action": "list",
                "category": category,
            }

    return None
