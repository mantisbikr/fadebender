from __future__ import annotations

_ALIASES = {
    "drywet": "Dry/Wet",
    "dry/wet": "Dry/Wet",
    "wet": "Dry/Wet",
    "mix": "Dry/Wet",
    "predelay": "Pre-Delay",
    "pre-delay": "Pre-Delay",
    "decay": "Decay Time",
    "decay time": "Decay Time",
    "size": "Size",
    "stereo": "Stereo Width",
    "stereo width": "Stereo Width",
    "diffusion": "Diffusion",
    "frequency": "Frequency",
    "high cut": "High Cut",
    "low cut": "Low Cut",
}


def canonical_name(name: str) -> str:
    k = (name or "").strip().lower()
    return _ALIASES.get(k, name)

