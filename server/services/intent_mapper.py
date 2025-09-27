from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from server.models.intents import (
    ByRef,
    TrackTarget,
    ValueSpec,
    SetMixerIntent,
    CanonicalIntent,
)


def _parse_track_ref(raw: Any) -> Optional[ByRef]:
    if raw is None:
        return None
    # Accept formats: "Track N", N (int), "N"
    try:
        if isinstance(raw, int):
            return ByRef(by="index", value=int(raw))
        s = str(raw).strip()
        if s.lower().startswith("track "):
            n = int(s.split()[1])
            return ByRef(by="index", value=n)
        if s.isdigit():
            return ByRef(by="index", value=int(s))
        # Otherwise treat as name
        return ByRef(by="name", value=s)
    except Exception:
        return None


def map_llm_to_canonical(llm_intent: Dict[str, Any]) -> Tuple[Optional[CanonicalIntent], List[str]]:
    """Map the current LLM intent JSON into a canonical intent.

    Returns (canonical_intent | None, errors[])
    """
    errors: List[str] = []

    kind = (llm_intent or {}).get("intent")
    targets = (llm_intent or {}).get("targets") or []
    op = (llm_intent or {}).get("operation") or {}

    # Only map control intents here; questions/clarifications bubble up to caller
    if kind not in ("set_parameter", "relative_change"):
        errors.append(f"non_control_intent:{kind}")
        return None, errors

    target = targets[0] if targets else {}
    track_ref = _parse_track_ref(target.get("track"))
    if not track_ref:
        errors.append("missing_or_invalid_track")
        return None, errors

    parameter = (target.get("parameter") or "").lower()
    op_type = (op.get("type") or "").lower()
    value = op.get("value")
    unit = op.get("unit")

    # Simple support: map volume/pan to set_mixer
    if parameter in ("volume", "pan"):
        if op_type not in ("absolute", "relative"):
            errors.append("invalid_op_type")
            return None, errors
        try:
            amount = float(value)
        except Exception:
            errors.append("invalid_value_amount")
            return None, errors

        mix = SetMixerIntent(
            target=TrackTarget(track=track_ref),
            field=parameter,  # type: ignore[arg-type]
            value=ValueSpec(type=op_type, amount=amount, unit=unit),
        )
        return mix, []

    # TODO: map plugin params to set_device_param in future steps
    errors.append(f"unsupported_parameter:{parameter}")
    return None, errors

