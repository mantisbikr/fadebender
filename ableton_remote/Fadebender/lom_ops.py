"""
LOM helpers scaffold. Implement actual Live Object Model calls here.

For development outside Ableton, these functions operate on a tiny in-memory
stub so that the UDP bridge can respond meaningfully.
"""
from __future__ import annotations

from typing import Dict, Any
import time


_STATE: Dict[str, Any] = {
    "tracks": [
        {"index": 1, "name": "Track 1", "type": "audio", "mixer": {"volume": 0.5, "pan": 0.0}, "mute": False, "solo": False, "sends": [0.0, 0.0]},
        {"index": 2, "name": "Track 2", "type": "audio", "mixer": {"volume": 0.5, "pan": 0.0}, "mute": False, "solo": False, "sends": [0.0, 0.0]},
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
                vol_param = getattr(mix, "volume", None)
                vol = getattr(vol_param, "value", None)
                pan = getattr(getattr(mix, "panning", None), "value", None)
                # Mute via track activator: 1 = active(unmuted), 0 = muted
                activator = getattr(mix, "track_activator", None)
                activator_val = getattr(activator, "value", None)
                mute = None if activator_val is None else (activator_val == 0)
                # Solo may be on Track.solo
                solo_prop = getattr(tr, "solo", None)
                solo = bool(solo_prop) if solo_prop is not None else None
                # Display dB if available
                vdb = _parse_db(getattr(vol_param, 'display_value', None)) if vol_param is not None else None
                if vdb is None and vol is not None:
                    # Fallback to approximate mapping near 0 dB region
                    try:
                        v = float(vol)
                        vdb = (v - 0.85) / 0.025
                        if v <= 0.001:
                            vdb = -60.0
                        vdb = max(-60.0, min(6.0, vdb))
                    except Exception:
                        vdb = None
                return {
                    "index": idx,
                    "name": str(getattr(tr, "name", f"Track {idx}")),
                    "mixer": {"volume": float(vol) if vol is not None else None, "pan": float(pan) if pan is not None else None},
                    "mute": bool(mute) if mute is not None else None,
                    "solo": bool(solo) if solo is not None else None,
                    "volume_db": vdb,
                }
    except Exception:
        pass
    for t in _STATE["tracks"]:
        if t["index"] == int(track_index):
            # Approximate dB for stub using inverse of local taper near 0 dB
            norm = float(t["mixer"]["volume"])
            approx_db = max(-60.0, min(6.0, (norm - 0.85) / 0.025))
            if norm <= 0.001:
                approx_db = -60.0
            return {"index": t["index"], "name": t["name"], "mixer": t["mixer"].copy(), "mute": t.get("mute"), "solo": t.get("solo"), "volume_db": approx_db}
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
                if field == "mute" and hasattr(mix, "track_activator"):
                    # Set activator: 1 = active(unmuted), 0 = muted
                    mix.track_activator.value = 0 if bool(value) else 1
                    return True
                if field == "solo" and hasattr(tr, "solo"):
                    tr.solo = bool(value)
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
            if field == "mute":
                t["mute"] = bool(value)
                return True
            if field == "solo":
                t["solo"] = bool(value)
                return True
            return False
    return False


def set_send(live, track_index: int, send_index: int, value: float) -> bool:  # noqa: ARG001
    try:
        if live is not None:
            idx = int(track_index)
            if 1 <= idx <= len(live.tracks):
                tr = live.tracks[idx - 1]
                mix = getattr(tr, "mixer_device", None)
                sends = getattr(mix, "sends", None)
                if sends is not None and 0 <= int(send_index) < len(sends):
                    sends[int(send_index)].value = max(0.0, min(1.0, float(value)))
                    return True
    except Exception:
        pass
    for t in _STATE["tracks"]:
        if t["index"] == int(track_index):
            arr = t.setdefault("sends", [0.0, 0.0])
            si = int(send_index)
            if 0 <= si < len(arr):
                arr[si] = max(0.0, min(1.0, float(value)))
                return True
    return False

def get_track_sends(live, track_index: int) -> dict:
    """Return a list of sends for a track: [{index, name, value, db?}]"""
    try:
        if live is not None:
            idx = int(track_index)
            if 1 <= idx <= len(live.tracks):
                tr = live.tracks[idx - 1]
                mix = getattr(tr, "mixer_device", None)
                sends = getattr(mix, "sends", []) or []
                out = []
                for i, p in enumerate(sends):
                    try:
                        val = float(getattr(p, 'value', 0.0))
                    except Exception:
                        val = 0.0
                    # name best-effort: use corresponding return track name if available
                    name = f"Send {i}"
                    try:
                        returns = getattr(getattr(tr.canonical_parent, 'return_tracks', []), '__iter__', None)
                        if returns:
                            rts = list(tr.canonical_parent.return_tracks)
                            if 0 <= i < len(rts):
                                name = str(getattr(rts[i], 'name', name))
                    except Exception:
                        pass
                    out.append({"index": i, "name": name, "value": val})
                return {"index": idx, "sends": out}
    except Exception:
        pass
    for t in _STATE["tracks"]:
        if t["index"] == int(track_index):
            arr = t.setdefault("sends", [0.0, 0.0])
            out = []
            labels = ["A", "B", "C", "D"]
            for i, v in enumerate(arr):
                out.append({"index": i, "name": labels[i] if i < len(labels) else f"Send {i}", "value": float(v)})
            return {"index": t["index"], "sends": out}
    return {"error": "track_not_found", "index": track_index}


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


def _parse_db(display_value) -> float | None:
    try:
        s = str(display_value)
        if 'dB' in s:
            s = s.replace('dB', '').strip()
        return float(s)
    except Exception:
        return None


def set_volume_db(live, track_index: int, target_db: float):
    """Set volume by dB target. In Live, use quick binary search on parameter value to match display dB.

    Returns dict { ok: bool, achieved_db: float } when Live is available; True/False in stub mode.
    """
    target_db = max(-60.0, min(6.0, float(target_db)))
    # Stub path
    if live is None:
        # Use correct formula: X ≈ 0.85 - (0.025 × |dB_target|)
        norm = max(0.0, min(1.0, 0.85 - 0.025 * abs(target_db)))
        return set_mixer(None, track_index, 'volume', norm)

    try:
        idx = int(track_index)
        if not (1 <= idx <= len(live.tracks)):
            return {"ok": False}
        tr = live.tracks[idx - 1]
        mix = getattr(tr, 'mixer_device', None)
        vol = getattr(mix, 'volume', None)
        if vol is None:
            return {"ok": False}
        # Start from good initial guess using correct formula: X ≈ 0.85 - (0.025 × |dB_target|)
        guess = max(0.0, min(1.0, 0.85 - 0.025 * abs(target_db)))
        vol.value = guess
        time.sleep(0.01)
        dv = _parse_db(getattr(vol, 'display_value', None))
        if dv is not None and abs(dv - target_db) <= 0.1:
            return {"ok": True, "achieved_db": dv}
        # Binary search on .value to reach target display dB
        lo, hi = (0.0, guess) if (dv is not None and dv > target_db) else (guess, 1.0)
        achieved = dv
        for _ in range(24):
            mid = (lo + hi) / 2.0
            vol.value = mid
            time.sleep(0.01)
            dv = _parse_db(getattr(vol, 'display_value', None))
            # Handle '-inf dB' cases
            if dv is None and isinstance(getattr(vol, 'display_value', None), str) and 'inf' in getattr(vol, 'display_value'):
                dv = -60.0
            if dv is None:
                break
            achieved = dv
            if abs(dv - target_db) <= 0.1:
                break
            if dv < target_db:
                lo = mid
            else:
                hi = mid
        return {"ok": True, "achieved_db": achieved}
    except Exception:
        # Fallback to stub mapping if anything fails using correct formula
        norm = max(0.0, min(1.0, 0.85 - 0.025 * abs(target_db)))
        return set_mixer(None, track_index, 'volume', norm)
