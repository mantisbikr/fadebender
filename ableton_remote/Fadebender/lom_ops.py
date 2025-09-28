"""
LOM helpers scaffold. Implement actual Live Object Model calls here.

For development outside Ableton, these functions operate on a tiny in-memory
stub so that the UDP bridge can respond meaningfully.
"""
from __future__ import annotations

from typing import Dict, Any


_STATE: Dict[str, Any] = {
    "tracks": [
        {"index": 1, "name": "Track 1", "type": "audio", "mixer": {"volume": 0.5, "pan": 0.0}, "mute": False, "solo": False},
        {"index": 2, "name": "Track 2", "type": "audio", "mixer": {"volume": 0.5, "pan": 0.0}, "mute": False, "solo": False},
    ],
    "selected_track": 1,
    "scenes": 1,
}


def get_overview(live) -> dict:
    """Return minimal project outline.

    If `live` is a Live song (inside Ableton), read real data. Otherwise, use stub state.
    """
    if live is None:
        return {
            "tracks": [{"index": t["index"], "name": t["name"], "type": t["type"]} for t in _STATE["tracks"]],
            "selected_track": _STATE["selected_track"],
            "scenes": _STATE["scenes"],
        }

    # Try to read tracks from Live; avoid bailing on minor attribute errors
    tracks = []
    try:
        for idx, tr in enumerate(getattr(live, "tracks", []), start=1):
            cls_name = getattr(tr, "__class__", type(tr)).__name__.lower()
            if "return" in cls_name:
                ttype = "return"
            elif "midi" in cls_name:
                ttype = "midi"
            elif "audio" in cls_name:
                ttype = "audio"
            else:
                ttype = "track"
            tname = str(getattr(tr, "name", f"Track {idx}"))
            tracks.append({"index": idx, "name": tname, "type": ttype})
    except Exception:
        # If we cannot enumerate, fallback to stub tracks
        tracks = [{"index": t["index"], "name": t["name"], "type": t["type"]} for t in _STATE["tracks"]]

    # Selected track index (best-effort)
    sel_idx = 0
    try:
        sel = getattr(getattr(live, "view", None), "selected_track", None)
        if sel is not None and tracks:
            for idx, tr in enumerate(getattr(live, "tracks", []), start=1):
                if tr is sel:  # identity comparison is usually valid in Live API
                    sel_idx = idx
                    break
    except Exception:
        sel_idx = 0

    # Scene count (best-effort)
    try:
        scenes = len(getattr(live, "scenes", []))
    except Exception:
        scenes = _STATE["scenes"]

    return {"tracks": tracks, "selected_track": sel_idx, "scenes": scenes}


def get_track_status(live, track_index: int) -> dict:
    try:
        if live is not None:
            idx = int(track_index)
            if 1 <= idx <= len(live.tracks):
                tr = live.tracks[idx - 1]
                mix = getattr(tr, "mixer_device", None)
                vol = getattr(getattr(mix, "volume", None), "value", None)
                pan = getattr(getattr(mix, "panning", None), "value", None)
                mute = getattr(tr, "mute", None)
                solo = getattr(tr, "solo", None)
                return {
                    "index": idx,
                    "name": str(getattr(tr, "name", f"Track {idx}")),
                    "mixer": {"volume": float(vol) if vol is not None else None, "pan": float(pan) if pan is not None else None},
                    "mute": bool(mute) if mute is not None else None,
                    "solo": bool(solo) if solo is not None else None,
                }
    except Exception:
        pass
    for t in _STATE["tracks"]:
        if t["index"] == int(track_index):
            return {"index": t["index"], "name": t["name"], "mixer": t["mixer"].copy(), "mute": t.get("mute"), "solo": t.get("solo")}
    return {"error": "track_not_found", "index": track_index}


def set_mixer(live, track_index: int, field: str, value: float) -> bool:
    try:
        if live is not None:
            idx = int(track_index)
            if 1 <= idx <= len(live.tracks):
                tr = live.tracks[idx - 1]
                mix = getattr(tr, "mixer_device", None)
                if field == "volume" and hasattr(mix, "volume"):
                    mix.volume.value = max(0.0, min(1.0, float(value)))
                    return True
                if field == "pan" and hasattr(mix, "panning"):
                    mix.panning.value = max(-1.0, min(1.0, float(value)))
                    return True
                return False
    except Exception:
        pass
    for t in _STATE["tracks"]:
        if t["index"] == int(track_index):
            if field == "volume":
                t["mixer"]["volume"] = max(0.0, min(1.0, float(value)))
                return True
            if field == "pan":
                t["mixer"]["pan"] = max(-1.0, min(1.0, float(value)))
                return True
            return False
    return False


def set_send(live, track_index: int, send_index: int, value: float) -> bool:  # noqa: ARG001
    # Sends not modeled in stub; accept and return true for now
    return True


def set_device_param(live, track_index: int, device_index: int, param_index: int, value: float) -> bool:  # noqa: ARG001
    # Device params not modeled in stub; accept and return true for now
    return True


def select_track(live, track_index: int) -> bool:
    try:
        if live is not None:
            idx = int(track_index)
            if 1 <= idx <= len(live.tracks):
                live.view.selected_track = live.tracks[idx - 1]
                return True
        # Stub selection
        _STATE["selected_track"] = int(track_index)
        return True
    except Exception:
        return False
