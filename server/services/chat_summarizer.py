from __future__ import annotations

from typing import Any, Dict


def generate_summary_from_canonical(canonical: Dict[str, Any]) -> str:
    """Generate a human-readable summary from a canonical intent.

    Examples:
        - Set Track 1 volume to -10 dB
        - Set Track 2 send A to -6 dB
        - Mute Track 3
        - Set Master cue to -20 dB
    """
    if not canonical:
        return "Command executed"

    domain = canonical.get("domain", "")
    action = canonical.get("action", "set")
    field = canonical.get("field", "")
    value = canonical.get("value")
    unit = canonical.get("unit", "")

    # Build entity reference (Track 1, Return A, Master, Device)
    entity = ""
    if domain == "track":
        track_idx = canonical.get("track_index", 1)
        entity = f"Track {track_idx}"
    elif domain == "return":
        return_idx = canonical.get("return_index")
        return_ref = canonical.get("return_ref")
        if return_ref:
            entity = f"Return {return_ref.upper()}"
        elif return_idx is not None:
            letter = chr(ord('A') + return_idx)
            entity = f"Return {letter}"
        else:
            entity = "Return"
    elif domain == "master":
        entity = "Master"
    elif domain == "device":
        device_name = canonical.get("device_name_hint", "")
        return_ref = canonical.get("return_ref")
        return_idx = canonical.get("return_index")
        device_idx = canonical.get("device_index")

        parts = []
        if return_ref:
            parts.append(f"Return {return_ref.upper()}")
        elif return_idx is not None:
            letter = chr(ord('A') + return_idx)
            parts.append(f"Return {letter}")

        if device_name:
            parts.append(device_name.capitalize())
        elif device_idx is not None:
            parts.append(f"Device {device_idx + 1}")
        else:
            parts.append("Device")

        entity = " ".join(parts) if parts else "Device"
    elif domain == "transport":
        entity = "Transport"
    else:
        entity = domain.capitalize()

    # Build field description (device uses param_ref)
    if domain == "device":
        param_ref = canonical.get("param_ref", "")
        field_desc = param_ref if param_ref else "parameter"
    else:
        field_desc = field
        if field == "send":
            send_ref = canonical.get("send_ref", "")
            field_desc = f"send {send_ref.upper()}" if send_ref else "send"

    # Build value description
    value_desc = ""
    if value is not None:
        if isinstance(value, (int, float)):
            if abs(value) < 0.01:
                formatted_value = "0"
            elif abs(value - round(value)) < 0.01:
                formatted_value = str(int(round(value)))
            else:
                formatted_value = f"{value:.2f}".rstrip('0').rstrip('.')
        else:
            formatted_value = str(value)
        value_desc = f"to {formatted_value} {unit}".strip()

    # Action verb
    action_verb = {
        "set": "Set",
        "increase": "Increased",
        "decrease": "Decreased",
    }.get(action, action.capitalize())

    return f"{action_verb} {entity} {field_desc} {value_desc}".strip()

