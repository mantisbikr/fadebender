"""
LOM helpers scaffold. Implement actual Live Object Model calls here.

For development outside Ableton, these functions operate on a tiny in-memory
stub so that the UDP bridge can respond meaningfully.
"""
from __future__ import annotations

from typing import Dict, Any, Callable, List, Tuple, Optional
import os
import time
import threading


_STATE: Dict[str, Any] = {
    "tracks": [
        {"index": 1, "name": "Track 1", "type": "audio", "mixer": {"volume": 0.5, "pan": 0.0}, "mute": False, "solo": False, "sends": [0.0, 0.0],
         "devices": [
             {"index": 0, "name": "Utility"},
             {"index": 1, "name": "EQ Eight"},
         ],
         "routing": {"monitor_state": "auto", "audio_from": {"type": "Ext. In", "channel": "1"}, "audio_to": {"type": "Master", "channel": "1/2"}}},
        {"index": 2, "name": "Track 2", "type": "audio", "mixer": {"volume": 0.5, "pan": 0.0}, "mute": False, "solo": False, "sends": [0.0, 0.0],
         "devices": [
             {"index": 0, "name": "Compressor"}
         ]},
    ],
    "selected_track": 1,
    "scenes": 1,
    "scene_names": {1: "Scene 1"},
    # Session clip names by (track, scene)
    "clips": {},
    "returns": [
        {
            "index": 0,
            "name": "A Reverb",
            "routing": {"audio_to": {"type": "Master", "channel": "1/2"}, "sends_mode": "post"},
            "devices": [
                {
                    "index": 0,
                    "name": "Reverb",
                    "params": [
                        {"index": 0, "name": "Wet", "value": 0.25, "min": 0.0, "max": 1.0},
                        {"index": 1, "name": "Decay", "value": 0.5, "min": 0.0, "max": 1.0},
                    ],
                }
            ],
        },
        {
            "index": 1,
            "name": "B Delay",
            "routing": {"audio_to": {"type": "Master", "channel": "1/2"}, "sends_mode": "post"},
            "devices": [
                {
                    "index": 0,
                    "name": "Delay",
                    "params": [
                        {"index": 0, "name": "Wet", "value": 0.2, "min": 0.0, "max": 1.0},
                        {"index": 1, "name": "Feedback", "value": 0.35, "min": 0.0, "max": 1.0},
                    ],
                }
            ],
        }
    ],
    "transport": {"is_playing": False, "is_recording": False, "metronome": False, "tempo": 120.0},
}

_NOTIFIER: Optional[Callable[[Dict[str, Any]], None]] = None
_SCHEDULER: Optional[Callable[..., None]] = None  # ControlSurface.schedule_message
_LISTENERS: List[Tuple[Any, Callable[[], None]]] = []
_LAST_MASTER_VALUES: Dict[str, float] = {}  # Cache to prevent duplicate master events
_LAST_TRANSPORT_VALUES: Dict[str, Any] = {}  # Cache to prevent duplicate transport events
_APP_VIEW_GETTER: Optional[Callable[[], Any]] = None  # Application.view accessor


def set_notifier(fn: Callable[[Dict[str, Any]], None]) -> None:
    global _NOTIFIER
    _NOTIFIER = fn


def set_scheduler(scheduler: Callable[..., None]) -> None:
    """Inject ControlSurface.schedule_message to run LOM writes on Live's main thread."""
    global _SCHEDULER
    _SCHEDULER = scheduler


def set_app_view_getter(getter: Callable[[], Any]) -> None:
    """Inject Application.view getter (for view switching)."""
    global _APP_VIEW_GETTER
    _APP_VIEW_GETTER = getter


def _run_on_main(fn: Callable[[], Any]) -> Any:
    """Run a function on Live's main thread via schedule_message, waiting up to 1s.

    If no scheduler is available, execute immediately.
    """
    if _SCHEDULER is None:
        return fn()
    done = threading.Event()
    out: Dict[str, Any] = {}

    def _wrapped(_ignored=None):  # schedule_message passes arg
        try:
            out["value"] = fn()
        except Exception as e:
            out["error"] = e
        finally:
            try:
                done.set()
            except Exception:
                pass

    try:
        _SCHEDULER(0, _wrapped, None)
        done.wait(1.0)
    except Exception:
        return fn()
    return out.get("value")


def _emit(payload: Dict[str, Any]) -> None:
    notify = _NOTIFIER
    if notify is None:
        return
    try:
        notify(payload)
    except Exception:
        pass


def clear_listeners() -> None:
    global _LISTENERS
    for param, cb in _LISTENERS:
        try:
            if hasattr(param, 'remove_value_listener'):
                param.remove_value_listener(cb)
        except Exception:
            pass
    _LISTENERS = []


def _add_param_listener(param, cb):
    try:
        if not hasattr(param, 'add_value_listener'):
            return
        if hasattr(param, 'value_has_listener') and param.value_has_listener(cb):
            return
        param.add_value_listener(cb)
        _LISTENERS.append((param, cb))
    except Exception:
        pass


def init_listeners(live) -> None:
    clear_listeners()
    if live is None:
        return
    try:
        scope_raw = (os.getenv("FADEBENDER_LISTENERS") or "master").lower()
        scopes = {s.strip() for s in scope_raw.split(",") if s.strip()}
        all_on = ("all" in scopes or "*" in scopes)
        if all_on or "tracks" in scopes or "track" in scopes:
            _attach_track_listeners(live)
        if all_on or "returns" in scopes or "return" in scopes:
            _attach_return_listeners(live)
        if all_on or "master" in scopes:
            _attach_master_listeners(live)
        if all_on or "transport" in scopes:
            _attach_transport_listeners(live)
    except Exception:
        pass


def _attach_track_listeners(live) -> None:
    tracks = getattr(live, 'tracks', []) or []
    for idx, tr in enumerate(tracks, start=1):
        mix = getattr(tr, 'mixer_device', None)
        if mix is None:
            continue
        vol = getattr(mix, 'volume', None)
        pan = getattr(mix, 'panning', None)
        if vol is not None:
            def make_cb(param=vol, track_idx=idx):
                def _cb():
                    try:
                        _emit({"event": "mixer_changed", "track": track_idx, "field": "volume", "value": float(getattr(param, 'value', 0.0))})
                    except Exception:
                        pass
                return _cb
            _add_param_listener(vol, make_cb())
        if pan is not None:
            def make_cb(param=pan, track_idx=idx):
                def _cb():
                    try:
                        _emit({"event": "mixer_changed", "track": track_idx, "field": "pan", "value": float(getattr(param, 'value', 0.0))})
                    except Exception:
                        pass
                return _cb
            _add_param_listener(pan, make_cb())


def _attach_return_listeners(live) -> None:
    returns = getattr(live, 'return_tracks', []) or []
    for idx, rt in enumerate(returns):
        mix = getattr(rt, 'mixer_device', None)
        if mix is None:
            continue
        vol = getattr(mix, 'volume', None)
        pan = getattr(mix, 'panning', None)
        if vol is not None:
            def make_cb(param=vol, return_idx=idx):
                def _cb():
                    try:
                        _emit({"event": "return_mixer_changed", "return": return_idx, "field": "volume", "value": float(getattr(param, 'value', 0.0))})
                    except Exception:
                        pass
                return _cb
            _add_param_listener(vol, make_cb())
        if pan is not None:
            def make_cb(param=pan, return_idx=idx):
                def _cb():
                    try:
                        _emit({"event": "return_mixer_changed", "return": return_idx, "field": "pan", "value": float(getattr(param, 'value', 0.0))})
                    except Exception:
                        pass
                return _cb
            _add_param_listener(pan, make_cb())


def _attach_master_listeners(live) -> None:
    global _LAST_MASTER_VALUES
    master = getattr(live, 'master_track', None)
    if master is None:
        return
    mix = getattr(master, 'mixer_device', None)
    if mix is None:
        return
    volume = getattr(mix, 'volume', None)
    pan = getattr(mix, 'panning', None)
    cue = getattr(mix, 'cue_volume', None)

    def add(field, param):
        if param is None:
            return
        def _cb():
            try:
                val = float(getattr(param, 'value', 0.0))
                # Only emit if value actually changed (threshold: 0.0001)
                last = _LAST_MASTER_VALUES.get(field)
                if last is None or abs(val - last) > 0.0001:
                    _LAST_MASTER_VALUES[field] = val
                    _emit({"event": "master_mixer_changed", "field": field, "value": val})
            except Exception:
                pass
        _add_param_listener(param, _cb)

    add('volume', volume)
    add('pan', pan)
    add('cue', cue)


def _attach_transport_listeners(live) -> None:
    """Attach transport listeners with change detection to prevent SSE storms."""
    global _LAST_TRANSPORT_VALUES
    if live is None:
        return

    # Listen to is_playing
    def make_playing_cb():
        def _cb():
            try:
                val = bool(getattr(live, 'is_playing', False))
                last = _LAST_TRANSPORT_VALUES.get('is_playing')
                if last is None or val != last:
                    _LAST_TRANSPORT_VALUES['is_playing'] = val
                    _emit({"event": "transport_changed", "field": "is_playing", "value": val})
            except Exception:
                pass
        return _cb

    # Listen to metronome
    def make_metronome_cb():
        def _cb():
            try:
                val = bool(getattr(live, 'metronome', False))
                last = _LAST_TRANSPORT_VALUES.get('metronome')
                if last is None or val != last:
                    _LAST_TRANSPORT_VALUES['metronome'] = val
                    _emit({"event": "transport_changed", "field": "metronome", "value": val})
            except Exception:
                pass
        return _cb

    # Listen to tempo (with threshold for floating point)
    def make_tempo_cb():
        def _cb():
            try:
                val = float(getattr(live, 'tempo', 120.0))
                last = _LAST_TRANSPORT_VALUES.get('tempo')
                if last is None or abs(val - last) > 0.01:  # 0.01 BPM threshold
                    _LAST_TRANSPORT_VALUES['tempo'] = val
                    _emit({"event": "transport_changed", "field": "tempo", "value": val})
            except Exception:
                pass
        return _cb

    # Attach listeners if they exist
    try:
        if hasattr(live, 'is_playing_has_listener') and hasattr(live, 'add_is_playing_listener'):
            if not live.is_playing_has_listener(make_playing_cb()):
                live.add_is_playing_listener(make_playing_cb())
                # Note: We don't add to _LISTENERS because transport listeners have different API
    except Exception:
        pass

    try:
        if hasattr(live, 'metronome_has_listener') and hasattr(live, 'add_metronome_listener'):
            if not live.metronome_has_listener(make_metronome_cb()):
                live.add_metronome_listener(make_metronome_cb())
    except Exception:
        pass

    try:
        if hasattr(live, 'tempo_has_listener') and hasattr(live, 'add_tempo_listener'):
            if not live.tempo_has_listener(make_tempo_cb()):
                live.add_tempo_listener(make_tempo_cb())
    except Exception:
        pass


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
            # Robust type detection across Live versions
            ttype = "track"
            try:
                has_midi = bool(getattr(tr, "has_midi_input", False))
            except Exception:
                has_midi = False
            try:
                has_audio = bool(getattr(tr, "has_audio_input", False))
            except Exception:
                has_audio = True  # default to audio when unknown

            if has_midi and not has_audio:
                ttype = "midi"
            elif has_audio and not has_midi:
                ttype = "audio"
            else:
                # Fallback: inspect class name hints if properties are inconclusive
                try:
                    cls_name = getattr(tr, "__class__", type(tr)).__name__.lower()
                except Exception:
                    cls_name = ""
                if "midi" in cls_name:
                    ttype = "midi"
                elif "audio" in cls_name:
                    ttype = "audio"
                else:
                    ttype = "audio"  # default bias to audio

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


def get_scenes(live) -> Dict[str, Any]:
    """List scenes with names.

    Returns: { scenes: [ { index: 1-based, name: str } ] }
    """
    try:
        if live is not None:
            scenes = getattr(live, 'scenes', []) or []
            out = []
            for i, sc in enumerate(scenes, start=1):
                try:
                    nm = str(getattr(sc, 'name', f'Scene {i}'))
                except Exception:
                    nm = f"Scene {i}"
                out.append({"index": i, "name": nm})
            return {"scenes": out}
    except Exception:
        pass
    # Stub
    total = int(_STATE.get("scenes", 0) or 0)
    names = _STATE.get("scene_names", {}) or {}
    out = []
    for i in range(1, total + 1):
        out.append({"index": i, "name": str(names.get(i, f"Scene {i}"))})
    return {"scenes": out}


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
                    val = max(0.0, min(1.0, float(value)))
                    mix.volume.value = val
                    _emit({"event": "mixer_changed", "track": idx, "field": "volume", "value": float(val)})
                    return True
                if field == "pan" and hasattr(mix, "panning"):
                    val = max(-1.0, min(1.0, float(value)))
                    mix.panning.value = val
                    _emit({"event": "mixer_changed", "track": idx, "field": "pan", "value": float(val)})
                    return True
                if field == "mute" and hasattr(mix, "track_activator"):
                    # Set activator: 1 = active(unmuted), 0 = muted
                    mix.track_activator.value = 0 if bool(value) else 1
                    _emit({"event": "mixer_changed", "track": idx, "field": "mute", "value": bool(value)})
                    return True
                if field == "solo" and hasattr(tr, "solo"):
                    tr.solo = bool(value)
                    _emit({"event": "mixer_changed", "track": idx, "field": "solo", "value": bool(value)})
                    return True
                return False
    except Exception:
        pass
    for t in _STATE["tracks"]:
        if t["index"] == int(track_index):
            if field == "volume":
                val = max(0.0, min(1.0, float(value)))
                t["mixer"]["volume"] = val
                _emit({"event": "mixer_changed", "track": int(track_index), "field": "volume", "value": float(val)})
                return True
            if field == "pan":
                val = max(-1.0, min(1.0, float(value)))
                t["mixer"]["pan"] = val
                _emit({"event": "mixer_changed", "track": int(track_index), "field": "pan", "value": float(val)})
                return True
            if field == "mute":
                t["mute"] = bool(value)
                _emit({"event": "mixer_changed", "track": int(track_index), "field": "mute", "value": bool(value)})
                return True
            if field == "solo":
                t["solo"] = bool(value)
                _emit({"event": "mixer_changed", "track": int(track_index), "field": "solo", "value": bool(value)})
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


def get_return_tracks(live) -> dict:
    """List return tracks with basic mixer state for UI feedback.

    Returns shape: { returns: [ { index, name, mixer: { volume, pan, mute, solo } } ] }
    """
    try:
        if live is not None:
            returns = getattr(live, "return_tracks", []) or []
            out = []
            for idx, tr in enumerate(returns):
                mix = getattr(tr, "mixer_device", None)
                vol = getattr(getattr(mix, "volume", None), "value", None)
                pan = getattr(getattr(mix, "panning", None), "value", None)
                mute = getattr(tr, "mute", None)
                solo = getattr(tr, "solo", None)
                out.append({
                    "index": idx,
                    "name": str(getattr(tr, "name", f"Return {idx}")),
                    "mixer": {
                        "volume": float(vol) if vol is not None else None,
                        "pan": float(pan) if pan is not None else None,
                        "mute": bool(mute) if mute is not None else False,
                        "solo": bool(solo) if solo is not None else False,
                    },
                })
            return {"returns": out}
    except Exception:
        pass
    # Stub
    out = []
    for r in _STATE.get("returns", []):
        mx = r.get("mixer") or {}
        out.append({
            "index": r["index"],
            "name": r["name"],
            "mixer": {
                "volume": float(mx.get("volume", 0.5)),
                "pan": float(mx.get("pan", 0.0)),
                "mute": bool(r.get("mute", False)),
                "solo": bool(r.get("solo", False)),
            },
        })
    return {"returns": out}


def get_return_sends(live, return_index: int) -> dict:
    """Return sends for a return track: [{index, name, value}] where available.

    Availability depends on Live preference allowing return→return sends.
    """
    try:
        if live is not None:
            ri = int(return_index)
            returns = getattr(live, "return_tracks", []) or []
            if 0 <= ri < len(returns):
                rt = returns[ri]
                mix = getattr(rt, "mixer_device", None)
                sends = getattr(mix, "sends", []) or []
                out = []
                # Infer names from the project return tracks list
                names = []
                try:
                    names = [str(getattr(x, "name", f"Return {i}")) for i, x in enumerate(returns)]
                except Exception:
                    names = []
                for i, p in enumerate(sends):
                    try:
                        val = float(getattr(p, 'value', 0.0))
                    except Exception:
                        val = 0.0
                    name = names[i] if i < len(names) else f"Send {i}"
                    out.append({"index": i, "name": name, "value": val})
                return {"index": ri, "sends": out}
    except Exception:
        pass
    # Stub fallback
    for r in _STATE.get("returns", []):
        if r["index"] == int(return_index):
            arr = r.setdefault("sends", [0.0, 0.0])
            labels = ["A", "B", "C", "D"]
            out = [{"index": i, "name": labels[i] if i < len(labels) else f"Send {i}", "value": float(v)} for i, v in enumerate(arr)]
            return {"index": r["index"], "sends": out}
    return {"error": "return_not_found", "index": return_index}


def set_return_send(live, return_index: int, send_index: int, value: float) -> bool:
    try:
        if live is not None:
            ri = int(return_index)
            si = int(send_index)
            returns = getattr(live, "return_tracks", []) or []
            if 0 <= ri < len(returns):
                rt = returns[ri]
                sends = getattr(getattr(rt, "mixer_device", None), "sends", []) or []
                if 0 <= si < len(sends):
                    sends[si].value = max(0.0, min(1.0, float(value)))
                    return True
    except Exception:
        pass
    # Stub
    for r in _STATE.get("returns", []):
        if r["index"] == int(return_index):
            arr = r.setdefault("sends", [0.0, 0.0])
            si = int(send_index)
            if 0 <= si < len(arr):
                arr[si] = max(0.0, min(1.0, float(value)))
                return True
    return False


# ---------- Track Devices ----------
def _device_kind(dev) -> str:
    try:
        cls = str(getattr(dev, '__class__', type(dev)).__name__).lower()
        name = str(getattr(dev, 'name', '')).lower()
        disp = str(getattr(dev, 'class_display_name', '') or '').lower()
        # Heuristics
        if 'audioeffect' in cls or 'audio effect' in disp:
            return 'audio_effect'
        if 'midieffect' in cls or ('midi' in cls and 'effect' in cls) or 'midi effect' in disp:
            return 'midi_effect'
        if 'instrument' in cls or 'drum' in cls or 'simpler' in cls or 'sampler' in cls or 'instrument' in disp or 'drum' in disp:
            return 'instrument'
        if 'plugindevice' in cls or 'plugin' in cls or 'plug-in' in disp:
            # Unknown if instrument or effect; classify as plugin
            return 'plugin'
        # Racks / GroupDevices
        if 'audioeffectgroupdevice' in cls or 'audiorack' in cls or 'effectrack' in cls or 'audio effect rack' in disp:
            return 'audio_effect'
        if 'midieffectgroupdevice' in cls or 'midirack' in cls or 'midi effect rack' in disp:
            return 'midi_effect'
        if 'drumgroupdevice' in cls or 'drumrack' in cls or 'instrumentgroupdevice' in cls or 'instrumentrack' in cls or 'instrument rack' in disp or 'drum rack' in disp:
            return 'instrument'
        # Fallback by name hints
        if 'instrument' in name:
            return 'instrument'
        if 'effect' in name:
            return 'audio_effect'
    except Exception:
        pass
    return 'unknown'


def get_track_devices(live, track_index: int) -> Dict[str, Any]:
    idx_int = int(track_index)
    if live is None:
        return {"index": idx_int, "devices": []}
    try:
        tr = live.tracks[idx_int - 1] if 1 <= idx_int <= len(live.tracks) else None
        if tr is None:
            return {"index": idx_int, "devices": []}
        devs = getattr(tr, 'devices', []) or []
        out = []
        # Determine track type and instrument boundary (best-effort)
        try:
            tr_cls = str(getattr(tr, '__class__', type(tr)).__name__).lower()
            is_midi = bool(getattr(tr, 'has_midi_input', False) or 'midi' in tr_cls)
        except Exception:
            is_midi = False
        prelim_kinds = []
        instrument_idx = None
        for di, d in enumerate(devs):
            try:
                k = _device_kind(d)
                prelim_kinds.append(k)
                disp = str(getattr(d, 'class_display_name', '') or '').lower()
                if instrument_idx is None and (k == 'instrument' or 'instrument' in disp or 'drum' in disp):
                    instrument_idx = di
            except Exception:
                prelim_kinds.append('unknown')
        for di, d in enumerate(devs):
            try:
                name = str(getattr(d, 'name', f'Device {di}'))
                k = prelim_kinds[di]
                if k == 'unknown':
                    if not is_midi:
                        k = 'audio_effect'
                    else:
                        if instrument_idx is not None and di > instrument_idx:
                            k = 'audio_effect'
                        else:
                            k = 'instrument'
                is_on = False
                try:
                    is_on = bool(getattr(d, 'is_enabled', getattr(d, 'is_active', True)))
                except Exception:
                    is_on = True
                out.append({"index": di, "name": name, "isOn": is_on, "kind": k})
            except Exception:
                continue
        return {"index": idx_int, "devices": out}
    except Exception:
        return {"index": idx_int, "devices": []}


def get_track_device_params(live, track_index: int, device_index: int) -> Dict[str, Any]:
    try:
        if live is not None:
            idx = int(track_index)
            di = int(device_index)
            tr = live.tracks[idx - 1] if 1 <= idx <= len(live.tracks) else None
            if tr is None:
                raise RuntimeError("track_not_found")
            devs = getattr(tr, 'devices', []) or []
            d = devs[di] if 0 <= di < len(devs) else None
            if d is None:
                raise RuntimeError("device_not_found")
            params = getattr(d, 'parameters', []) or []
            out = []
            for pi, p in enumerate(params):
                try:
                    out.append({
                        "index": pi,
                        "name": str(getattr(p, 'name', f'Param {pi}')),
                        "value": float(getattr(p, 'value', 0.0)),
                        "min": float(getattr(p, 'min', 0.0)) if hasattr(p, 'min') else 0.0,
                        "max": float(getattr(p, 'max', 1.0)) if hasattr(p, 'max') else 1.0,
                    })
                except Exception:
                    continue
            return {"index": int(idx), "device_index": int(di), "params": out}
    except Exception:
        pass
    return {"index": int(track_index), "device_index": int(device_index), "params": []}


# ---------- Master Devices ----------
def get_master_devices(live) -> Dict[str, Any]:
    try:
        if live is not None:
            mt = getattr(live, 'master_track', None)
            if mt is None:
                raise RuntimeError("no_master")
            devs = getattr(mt, 'devices', []) or []
            out = []
            for di, d in enumerate(devs):
                name = str(getattr(d, 'name', f'Device {di}'))
                kind = _device_kind(d)
                is_on = bool(getattr(d, 'is_enabled', getattr(d, 'is_active', True)))
                out.append({"index": di, "name": name, "isOn": is_on, "kind": kind})
            return {"devices": out}
    except Exception:
        pass
    return {"devices": []}


def get_master_device_params(live, device_index: int) -> Dict[str, Any]:
    try:
        if live is not None:
            mt = getattr(live, 'master_track', None)
            if mt is None:
                raise RuntimeError("no_master")
            di = int(device_index)
            devs = getattr(mt, 'devices', []) or []
            d = devs[di] if 0 <= di < len(devs) else None
            if d is None:
                raise RuntimeError("device_not_found")
            params = getattr(d, 'parameters', []) or []
            out = []
            for pi, p in enumerate(params):
                try:
                    out.append({
                        "index": pi,
                        "name": str(getattr(p, 'name', f'Param {pi}')),
                        "value": float(getattr(p, 'value', 0.0)),
                        "min": float(getattr(p, 'min', 0.0)) if hasattr(p, 'min') else 0.0,
                        "max": float(getattr(p, 'max', 1.0)) if hasattr(p, 'max') else 1.0,
                    })
                except Exception:
                    continue
            return {"device_index": int(di), "params": out}
    except Exception:
        pass
    return {"device_index": int(device_index), "params": []}


def set_master_device_param(live, device_index: int, param_index: int, value: float) -> bool:
    try:
        if live is not None:
            mt = getattr(live, 'master_track', None)
            if mt is None:
                return False
            di = int(device_index)
            pi = int(param_index)
            devs = getattr(mt, 'devices', []) or []
            d = devs[di] if 0 <= di < len(devs) else None
            if d is None:
                return False
            params = getattr(d, 'parameters', []) or []
            p = params[pi] if 0 <= pi < len(params) else None
            if p is None:
                return False
            v = float(value)
            setattr(p, 'value', v)
            _emit({"event": "master_device_param_changed", "device_index": di, "param_index": pi, "value": v})
            return True
    except Exception:
        pass
    return False


def get_return_devices(live, return_index: int) -> dict:
    try:
        if live is not None:
            ri = int(return_index)
            returns = getattr(live, "return_tracks", []) or []
            if 0 <= ri < len(returns):
                devs = getattr(returns[ri], "devices", []) or []
                out = []
                for di, dv in enumerate(devs):
                    out.append({"index": di, "name": str(getattr(dv, "name", f"Device {di}"))})
                return {"index": ri, "devices": out}
    except Exception:
        pass
    for r in _STATE.get("returns", []):
        if r["index"] == int(return_index):
            out = []
            for d in r.get("devices", []):
                out.append({"index": d["index"], "name": d["name"]})
            return {"index": r["index"], "devices": out}
    return {"error": "return_not_found", "index": return_index}


def get_return_device_params(live, return_index: int, device_index: int) -> dict:
    try:
        if live is not None:
            ri = int(return_index)
            di = int(device_index)
            returns = getattr(live, "return_tracks", []) or []
            if 0 <= ri < len(returns):
                devs = getattr(returns[ri], "devices", []) or []
                if 0 <= di < len(devs):
                    device = devs[di]
                    params = getattr(device, "parameters", []) or []
                    out = []
                    for pi, p in enumerate(params):
                        try:
                            out.append({
                                "index": pi,
                                "name": str(getattr(p, "name", f"Param {pi}")),
                                "value": float(getattr(p, "value", 0.0)),
                                "min": float(getattr(p, "min", 0.0)) if hasattr(p, 'min') else 0.0,
                                "max": float(getattr(p, "max", 1.0)) if hasattr(p, 'max') else 1.0,
                                "display_value": str(getattr(p, "display_value", "")),
                            })
                        except Exception:
                            pass
                    return {"return_index": ri, "device_index": di, "params": out}
    except Exception:
        pass
    for r in _STATE.get("returns", []):
        if r["index"] == int(return_index):
            for d in r.get("devices", []):
                if d["index"] == int(device_index):
                    out = []
                    for p in d.get("params", []):
                        out.append({
                            "index": p["index"],
                            "name": p["name"],
                            "value": float(p["value"]),
                            "min": float(p.get("min", 0.0)),
                            "max": float(p.get("max", 1.0)),
                            "display_value": None,
                        })
                    return {"return_index": r["index"], "device_index": d["index"], "params": out}
    return {"error": "device_not_found", "return_index": return_index, "device_index": device_index}


def set_return_device_param(live, return_index: int, device_index: int, param_index: int, value: float) -> bool:
    try:
        if live is not None:
            ri = int(return_index)
            di = int(device_index)
            pi = int(param_index)
            returns = getattr(live, "return_tracks", []) or []
            if 0 <= ri < len(returns):
                devs = getattr(returns[ri], "devices", []) or []
                if 0 <= di < len(devs):
                    params = getattr(devs[di], "parameters", []) or []
                    if 0 <= pi < len(params):
                        params[pi].value = float(value)
                        return True
    except Exception:
        pass
    for r in _STATE.get("returns", []):
        if r["index"] == int(return_index):
            for d in r.get("devices", []):
                if d["index"] == int(device_index):
                    for p in d.get("params", []):
                        if p["index"] == int(param_index):
                            p["value"] = max(p.get("min", 0.0), min(p.get("max", 1.0), float(value)))
                            return True
    return False


def set_return_mixer(live, return_index: int, field: str, value: float) -> bool:
    """Set return track mixer fields: volume [0..1], pan [-1..1], mute/solo (bool)."""
    try:
        if live is not None:
            ri = int(return_index)
            if 0 <= ri < len(getattr(live, "return_tracks", [])):
                tr = live.return_tracks[ri]
                mix = getattr(tr, "mixer_device", None)
                if field == "volume" and hasattr(mix, "volume"):
                    val = max(0.0, min(1.0, float(value)))
                    mix.volume.value = val
                    _emit({"event": "return_mixer_changed", "return": ri, "field": "volume", "value": float(val)})
                    return True
                if field == "pan" and hasattr(mix, "panning"):
                    val = max(-1.0, min(1.0, float(value)))
                    mix.panning.value = val
                    _emit({"event": "return_mixer_changed", "return": ri, "field": "pan", "value": float(val)})
                    return True
                if field == "mute":
                    # Return tracks typically use Track.mute directly
                    if hasattr(tr, "mute"):
                        setattr(tr, "mute", bool(value))
                        _emit({"event": "return_mixer_changed", "return": ri, "field": "mute", "value": bool(value)})
                        return True
                if field == "solo":
                    if hasattr(tr, "solo"):
                        setattr(tr, "solo", bool(value))
                        _emit({"event": "return_mixer_changed", "return": ri, "field": "solo", "value": bool(value)})
                        return True
                return False
    except Exception:
        pass
    # Stub fallback
    for r in _STATE.get("returns", []):
        if r["index"] == int(return_index):
            if field == "volume":
                val = max(0.0, min(1.0, float(value)))
                r.setdefault("mixer", {}).update({"volume": val})
                _emit({"event": "return_mixer_changed", "return": int(return_index), "field": "volume", "value": float(val)})
                return True
            if field == "pan":
                val = max(-1.0, min(1.0, float(value)))
                r.setdefault("mixer", {}).update({"pan": val})
                _emit({"event": "return_mixer_changed", "return": int(return_index), "field": "pan", "value": float(val)})
                return True
            if field in ("mute", "solo"):
                r[field] = bool(value)
                _emit({"event": "return_mixer_changed", "return": int(return_index), "field": field, "value": bool(value)})
                return True
            return False
    return False


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


# ---------------- Transport ----------------
def get_transport(live) -> Dict[str, Any]:
    try:
        if live is not None:
            song = live
            return {
                "is_playing": bool(getattr(song, "is_playing", False)),
                # Prefer session_record (Session view) then record_mode (Arrangement)
                "is_recording": bool(getattr(song, "session_record", False) or getattr(song, "record_mode", False)),
                "metronome": bool(getattr(song, "metronome", False)),
                "tempo": float(getattr(song, "tempo", 120.0)),
                # Additional transport context
                "time_signature_numerator": int(getattr(song, "signature_numerator", 4)),
                "time_signature_denominator": int(getattr(song, "signature_denominator", 4)),
                # Ableton Live exposes current_song_time as a float (beats). We surface it directly.
                "current_song_time": float(getattr(song, "current_song_time", 0.0)),
                # Loop state
                "loop_on": bool(getattr(song, "loop", False)),
                "loop_start": float(getattr(song, "loop_start", 0.0)),
                "loop_length": float(getattr(song, "loop_length", 0.0)),
            }
    except Exception:
        pass
    return dict(_STATE.get("transport", {}))


def set_transport(live, action: str, value: Any | None = None) -> Dict[str, Any]:
    ok = False
    try:
        if live is not None:
            song = live
            a = str(action or "").lower()
            if a == "play":
                try:
                    if hasattr(song, "start_playing"):
                        song.start_playing()
                        ok = True
                except Exception:
                    ok = False
            elif a == "stop":
                try:
                    if hasattr(song, "stop_playing"):
                        song.stop_playing()
                        ok = True
                except Exception:
                    ok = False
            elif a == "record":
                try:
                    # Prefer session_record toggle (common in Session view)
                    if hasattr(song, "session_record"):
                        song.session_record = not bool(getattr(song, "session_record", False))
                        ok = True
                    elif hasattr(song, "record_mode"):
                        song.record_mode = not bool(getattr(song, "record_mode", False))
                        ok = True
                except Exception:
                    ok = False
            elif a == "metronome":
                try:
                    song.metronome = not bool(getattr(song, "metronome", False))
                    ok = True
                except Exception:
                    ok = False
            elif a == "tempo" and value is not None:
                try:
                    song.tempo = float(value)
                    ok = True
                except Exception:
                    ok = False
            elif a in ("loop", "loop_on"):
                # Toggle or set loop state
                def _do_set_loop():
                    cur = bool(getattr(song, 'loop', False))
                    if value is None:
                        setattr(song, 'loop', not cur)
                    else:
                        setattr(song, 'loop', bool(float(value) > 0.5))
                try:
                    _run_on_main(_do_set_loop)
                    ok = True
                except Exception:
                    ok = False
            elif a == "loop_start" and value is not None:
                def _do_set_ls():
                    # Ensure loop is enabled before adjusting region
                    try:
                        setattr(song, 'loop', True)
                    except Exception:
                        pass
                    lv = float(value)
                    if lv < 0.0:
                        lv = 0.0
                    setattr(song, 'loop_start', lv)
                try:
                    _run_on_main(_do_set_ls)
                    ok = True
                except Exception:
                    ok = False
            elif a == "loop_length" and value is not None:
                def _do_set_ll():
                    # Ensure loop is enabled before adjusting region
                    try:
                        setattr(song, 'loop', True)
                    except Exception:
                        pass
                    lv = max(0.0, float(value))
                    setattr(song, 'loop_length', float(lv))
                try:
                    _run_on_main(_do_set_ll)
                    ok = True
                except Exception:
                    ok = False
            elif a in ("time_sig_num", "time_signature_numerator") and value is not None:
                # Change time signature numerator on Live's main thread
                def _do_set_num():
                    nv = int(float(value))
                    nv = 1 if nv < 1 else (32 if nv > 32 else nv)
                    if hasattr(song, "signature_numerator"):
                        song.signature_numerator = nv
                try:
                    _run_on_main(_do_set_num)
                    ok = True
                except Exception:
                    ok = False
            elif a in ("time_sig_den", "time_signature_denominator") and value is not None:
                # Change time signature denominator on Live's main thread
                def _do_set_den():
                    dv = int(float(value))
                    allowed = [1, 2, 4, 8, 16, 32]
                    if dv not in allowed:
                        dv = min(allowed, key=lambda x: abs(x - dv))
                    if hasattr(song, "signature_denominator"):
                        song.signature_denominator = dv
                try:
                    _run_on_main(_do_set_den)
                    ok = True
                except Exception:
                    ok = False
            elif a in ("position", "locate") and value is not None:
                # Set absolute playhead position (in beats) via current_song_time
                try:
                    song.current_song_time = float(value)
                    ok = True
                except Exception:
                    ok = False
            elif a == "nudge" and value is not None:
                # Relative move of playhead (in beats); positive or negative
                try:
                    cur = float(getattr(song, "current_song_time", 0.0))
                    song.current_song_time = float(cur + float(value))
                    ok = True
                except Exception:
                    ok = False
            elif a == "loop_region" and isinstance(value, dict):
                def _do_set_region():
                    try:
                        setattr(song, 'loop', True)
                    except Exception:
                        pass
                    start = float(value.get('start', getattr(song, 'loop_start', 0.0)))
                    length = float(value.get('length', getattr(song, 'loop_length', 4.0)))
                    if start < 0.0:
                        start = 0.0
                    if length < 0.0:
                        length = 0.0
                    setattr(song, 'loop_start', start)
                    setattr(song, 'loop_length', length)
                try:
                    _run_on_main(_do_set_region)
                    ok = True
                except Exception:
                    ok = False
            state = get_transport(live)
            return {"ok": ok, "state": state}
    except Exception:
        ok = False
    # Stub fallback
    a = str(action or "").lower()
    tr = _STATE.setdefault(
        "transport",
        {
            "is_playing": False,
            "is_recording": False,
            "metronome": False,
            "tempo": 120.0,
            "time_signature_numerator": 4,
            "time_signature_denominator": 4,
            "current_song_time": 0.0,
            "loop_on": False,
            "loop_start": 0.0,
            "loop_length": 8.0,
        },
    )
    if a == "play":
        tr["is_playing"] = True
        ok = True
    elif a == "stop":
        tr["is_playing"] = False
        ok = True
    elif a == "record":
        tr["is_recording"] = not bool(tr.get("is_recording", False))
        ok = True
    elif a == "metronome":
        tr["metronome"] = not bool(tr.get("metronome", False))
        ok = True
    elif a == "tempo" and value is not None:
        try:
            tr["tempo"] = float(value)
            ok = True
        except Exception:
            ok = False
    elif a in ("loop", "loop_on"):
        try:
            if value is None:
                tr["loop_on"] = not bool(tr.get("loop_on", False))
            else:
                tr["loop_on"] = bool(float(value) > 0.5)
            ok = True
        except Exception:
            ok = False
    elif a == "loop_start" and value is not None:
        try:
            tr["loop_start"] = float(value)
            ok = True
        except Exception:
            ok = False
    elif a == "loop_length" and value is not None:
        try:
            tr["loop_length"] = max(0.0, float(value))
            ok = True
        except Exception:
            ok = False
    elif a in ("time_sig_num", "time_signature_numerator") and value is not None:
        try:
            nv = int(float(value)); nv = 1 if nv < 1 else (32 if nv > 32 else nv)
            tr["time_signature_numerator"] = nv
            ok = True
        except Exception:
            ok = False
    elif a in ("time_sig_den", "time_signature_denominator") and value is not None:
        try:
            dv = int(float(value))
            allowed = [1, 2, 4, 8, 16, 32]
            if dv not in allowed:
                dv = min(allowed, key=lambda x: abs(x - dv))
            tr["time_signature_denominator"] = dv
            ok = True
        except Exception:
            ok = False
    elif a in ("position", "locate") and value is not None:
        try:
            tr["current_song_time"] = float(value)
            ok = True
        except Exception:
            ok = False
    elif a == "nudge" and value is not None:
        try:
            tr["current_song_time"] = float(tr.get("current_song_time", 0.0)) + float(value)
            ok = True
        except Exception:
            ok = False
    elif a == "loop_region" and isinstance(value, dict):
        try:
            tr["loop_on"] = True
            if "start" in value:
                tr["loop_start"] = float(value.get("start", tr.get("loop_start", 0.0)))
            if "length" in value:
                tr["loop_length"] = max(0.0, float(value.get("length", tr.get("loop_length", 4.0))))
            ok = True
        except Exception:
            ok = False
    return {"ok": ok, "state": dict(tr)}


# ---------------- Master ----------------

def get_master_status(live) -> Dict[str, Any]:
    try:
        if live is not None:
            mt = getattr(live, "master_track", None)
            if mt is None:
                raise RuntimeError("no_master")
            mix = getattr(mt, "mixer_device", None)
            vol = getattr(getattr(mix, "volume", None), "value", None)
            pan = getattr(getattr(mix, "panning", None), "value", None)
            cue = getattr(getattr(mix, "cue_volume", None), "value", None)
            return {
                "mixer": {
                    "volume": float(vol) if vol is not None else None,
                    "pan": float(pan) if pan is not None else 0.0,
                    "cue": float(cue) if cue is not None else 0.0,
                },
            }
    except Exception:
        pass
    # stub: reuse first track if present (master tracks don't have mute/solo)
    mt = _STATE["tracks"][0] if _STATE.get("tracks") else {"mixer": {"volume": 0.8, "pan": 0.0, "cue": 0.0}}
    return {"mixer": {"volume": float(mt.get("mixer", {}).get("volume", 0.8)), "pan": float(mt.get("mixer", {}).get("pan", 0.0)), "cue": float(mt.get("mixer", {}).get("cue", 0.0))}}


def set_master_mixer(live, field: str, value: float) -> bool:
    try:
        if live is not None:
            mt = getattr(live, "master_track", None)
            if mt is None:
                return False
            mix = getattr(mt, "mixer_device", None)
            if field == "volume" and hasattr(mix, "volume"):
                val = max(0.0, min(1.0, float(value)))
                mix.volume.value = val
                _emit({"event": "master_mixer_changed", "field": "volume", "value": float(val)})
                return True
            if field == "pan" and hasattr(mix, "panning"):
                val = max(-1.0, min(1.0, float(value)))
                mix.panning.value = val
                _emit({"event": "master_mixer_changed", "field": "pan", "value": float(val)})
                return True
            if field == "cue" and hasattr(mix, "cue_volume"):
                val = max(0.0, min(1.0, float(value)))
                mix.cue_volume.value = val
                _emit({"event": "master_mixer_changed", "field": "cue", "value": float(val)})
                return True
            return False
    except Exception:
        pass
    # stub: update in-memory
    mt = _STATE.setdefault("master", {"mixer": {"volume": 0.8, "pan": 0.0}, "mute": False, "solo": False})
    if field == "volume":
        val = max(0.0, min(1.0, float(value)))
        mt.setdefault("mixer", {}).update({"volume": val})
        _emit({"event": "master_mixer_changed", "field": "volume", "value": float(val)})
        return True
    if field == "pan":
        val = max(-1.0, min(1.0, float(value)))
        mt.setdefault("mixer", {}).update({"pan": val})
        _emit({"event": "master_mixer_changed", "field": "pan", "value": float(val)})
        return True
    if field == "cue":
        val = max(0.0, min(1.0, float(value)))
        mt.setdefault("mixer", {}).update({"cue": val})
        _emit({"event": "master_mixer_changed", "field": "cue", "value": float(val)})
        return True
    return False


# ---------------- Routing & Monitoring ----------------

def _routing_options_stub(track_type: str = "audio") -> Dict[str, Any]:
    opts: Dict[str, Any] = {
        "audio_from_types": ["Ext. In"],
        "audio_from_channels": ["1", "2"],
        "audio_to_types": ["Master", "Sends Only", "Ext. Out"],
        "audio_to_channels": ["1/2", "3/4"],
    }
    if track_type == "midi":
        opts.update({
            "midi_from_types": ["All Ins", "Fadebender In"],
            "midi_from_channels": ["All Channels", "1", "10"],
            "midi_to_types": ["No Output", "Fadebender Out"],
            "midi_to_channels": ["All Channels", "1", "10"],
        })
    return opts


def get_track_routing(live, track_index: int) -> Dict[str, Any]:
    try:
        if live is not None:
            idx = int(track_index)
            tr = live.tracks[idx - 1] if 1 <= idx <= len(live.tracks) else None
            if tr is None:
                raise RuntimeError("track_not_found")
            # Monitor state mapping
            mon_val = getattr(tr, "current_monitoring_state", None)
            mon_state = None
            try:
                mv = int(mon_val)
                mon_state = {0: "off", 1: "auto", 2: "in"}.get(mv)
            except Exception:
                mon_state = None
            # Routing current values (best-effort)
            af_type = getattr(tr, "input_routing_type", None)
            af_chan = getattr(tr, "input_routing_channel", None)
            ao_type = getattr(tr, "output_routing_type", None)
            ao_chan = getattr(tr, "output_routing_channel", None)
            def _name(x):
                if x is None:
                    return None
                return str(getattr(x, "display_name", None) or getattr(x, "to_string", lambda: None)() or str(x))
            data = {
                "monitor_state": mon_state,
                "audio_from": {"type": _name(af_type), "channel": _name(af_chan)},
                "audio_to": {"type": _name(ao_type), "channel": _name(ao_chan)},
            }
            # MIDI only for MIDI tracks
            try:
                if getattr(tr, "has_midi_input", False) or tr.__class__.__name__.lower().startswith("midi"):
                    mf_type = getattr(tr, "midi_input_routing_type", None) or getattr(tr, "input_routing_type", None)
                    mf_chan = getattr(tr, "midi_input_routing_channel", None) or getattr(tr, "input_routing_channel", None)
                    mt_type = getattr(tr, "midi_output_routing_type", None) or getattr(tr, "output_routing_type", None)
                    mt_chan = getattr(tr, "midi_output_routing_channel", None) or getattr(tr, "output_routing_channel", None)
                    data.update({
                        "midi_from": {"type": _name(mf_type), "channel": _name(mf_chan)},
                        "midi_to": {"type": _name(mt_type), "channel": _name(mt_chan)},
                    })
            except Exception:
                pass
            # Options
            def _list_names(objs):
                out = []
                for o in (objs or []):
                    try:
                        out.append(str(getattr(o, "display_name", None) or getattr(o, "to_string", lambda: None)() or str(o)))
                    except Exception:
                        continue
                return out
            opts = {
                "audio_from_types": _list_names(getattr(tr, "available_input_routing_types", [])),
                "audio_from_channels": _list_names(getattr(tr, "available_input_routing_channels", [])),
                "audio_to_types": _list_names(getattr(tr, "available_output_routing_types", [])),
                "audio_to_channels": _list_names(getattr(tr, "available_output_routing_channels", [])),
            }
            # MIDI opts best-effort
            try:
                if "midi_from" in data:
                    opts.update({
                        "midi_from_types": _list_names(getattr(tr, "available_input_routing_types", [])),
                        "midi_from_channels": _list_names(getattr(tr, "available_input_routing_channels", [])),
                        "midi_to_types": _list_names(getattr(tr, "available_output_routing_types", [])),
                        "midi_to_channels": _list_names(getattr(tr, "available_output_routing_channels", [])),
                    })
            except Exception:
                pass
            data["options"] = opts
            return data
    except Exception:
        pass
    # Stub fallback
    for t in _STATE["tracks"]:
        if t["index"] == int(track_index):
            r = t.get("routing") or {"monitor_state": "auto", "audio_from": {"type": "Ext. In", "channel": "1"}, "audio_to": {"type": "Master", "channel": "1/2"}}
            data = {**r}
            data["options"] = _routing_options_stub(t.get("type", "audio"))
            return data
    return {"error": "track_not_found"}


def set_track_routing(live, track_index: int, **kwargs) -> bool:
    # kwargs: monitor_state, audio_from_type, audio_from_channel, audio_to_type, audio_to_channel,
    #         midi_from_type, midi_from_channel, midi_to_type, midi_to_channel
    try:
        if live is not None:
            idx = int(track_index)
            tr = live.tracks[idx - 1] if 1 <= idx <= len(live.tracks) else None
            if tr is None:
                return False
            # Monitor
            mon = kwargs.get("monitor_state")
            if mon is not None and hasattr(tr, "current_monitoring_state"):
                m = str(mon).lower()
                val = {"off": 0, "auto": 1, "in": 2}.get(m)
                if val is not None:
                    try:
                        tr.current_monitoring_state = int(val)
                    except Exception:
                        pass
            # Helper to set routing by matching display_name
            def _assign(name_list, attr_name, chosen):
                if chosen is None:
                    return
                try:
                    avail = getattr(tr, name_list, [])
                    for o in avail:
                        nm = str(getattr(o, "display_name", None) or getattr(o, "to_string", lambda: None)() or str(o))
                        if nm == str(chosen):
                            setattr(tr, attr_name, o)
                            return
                except Exception:
                    return
            _assign("available_input_routing_types", "input_routing_type", kwargs.get("audio_from_type"))
            _assign("available_input_routing_channels", "input_routing_channel", kwargs.get("audio_from_channel"))
            _assign("available_output_routing_types", "output_routing_type", kwargs.get("audio_to_type"))
            _assign("available_output_routing_channels", "output_routing_channel", kwargs.get("audio_to_channel"))
            # MIDI (best-effort using same available lists)
            _assign("available_input_routing_types", "midi_input_routing_type", kwargs.get("midi_from_type"))
            _assign("available_input_routing_channels", "midi_input_routing_channel", kwargs.get("midi_from_channel"))
            _assign("available_output_routing_types", "midi_output_routing_type", kwargs.get("midi_to_type"))
            _assign("available_output_routing_channels", "midi_output_routing_channel", kwargs.get("midi_to_channel"))
            return True
    except Exception:
        pass
    # Stub state update
    for t in _STATE["tracks"]:
        if t["index"] == int(track_index):
            r = t.setdefault("routing", {"monitor_state": "auto", "audio_from": {"type": "Ext. In", "channel": "1"}, "audio_to": {"type": "Master", "channel": "1/2"}})
            if kwargs.get("monitor_state"):
                r["monitor_state"] = str(kwargs["monitor_state"]).lower()
            if kwargs.get("audio_from_type"):
                r.setdefault("audio_from", {}).update({"type": kwargs.get("audio_from_type")})
            if kwargs.get("audio_from_channel"):
                r.setdefault("audio_from", {}).update({"channel": kwargs.get("audio_from_channel")})
            if kwargs.get("audio_to_type"):
                r.setdefault("audio_to", {}).update({"type": kwargs.get("audio_to_type")})
            if kwargs.get("audio_to_channel"):
                r.setdefault("audio_to", {}).update({"channel": kwargs.get("audio_to_channel")})
            # MIDI ignored in stub unless present
            return True
    return False


def get_return_routing(live, return_index: int) -> Dict[str, Any]:
    try:
        if live is not None:
            ri = int(return_index)
            returns = getattr(live, "return_tracks", []) or []
            if 0 <= ri < len(returns):
                rt = returns[ri]
                ao_type = getattr(rt, "output_routing_type", None)
                ao_chan = getattr(rt, "output_routing_channel", None)
                def _name(x):
                    if x is None:
                        return None
                    return str(getattr(x, "display_name", None) or getattr(x, "to_string", lambda: None)() or str(x))
                data = {
                    "audio_to": {"type": _name(ao_type), "channel": _name(ao_chan)}
                }
                # Sends mode (pre/post) if exposed
                try:
                    sends_pre = getattr(rt, "sends_are_pre", None)
                    if sends_pre is not None:
                        data["sends_mode"] = "pre" if bool(sends_pre) else "post"
                except Exception:
                    pass
                # Options lists
                def _list_names(objs):
                    out = []
                    for o in (objs or []):
                        try:
                            out.append(str(getattr(o, "display_name", None) or getattr(o, "to_string", lambda: None)() or str(o)))
                        except Exception:
                            continue
                    return out
                data["options"] = {
                    "audio_to_types": _list_names(getattr(rt, "available_output_routing_types", [])),
                    "audio_to_channels": _list_names(getattr(rt, "available_output_routing_channels", [])),
                    "sends_modes": ["pre", "post"],
                }
                return data
    except Exception:
        pass
    # Stub
    for r in _STATE.get("returns", []):
        if r["index"] == int(return_index):
            data = {"audio_to": r.get("routing", {}).get("audio_to", {"type": "Master", "channel": "1/2"}), "sends_mode": r.get("routing", {}).get("sends_mode", "post")}
            data["options"] = {"audio_to_types": ["Master", "Ext. Out"], "audio_to_channels": ["1/2", "3/4"], "sends_modes": ["pre", "post"]}
            return data
    return {"error": "return_not_found"}


def set_return_routing(live, return_index: int, **kwargs) -> bool:
    # kwargs: audio_to_type, audio_to_channel, sends_mode
    try:
        if live is not None:
            ri = int(return_index)
            returns = getattr(live, "return_tracks", []) or []
            if 0 <= ri < len(returns):
                rt = returns[ri]
                def _assign(obj, list_attr, target_attr, chosen):
                    if chosen is None:
                        return
                    try:
                        avail = getattr(obj, list_attr, [])
                        for o in avail:
                            nm = str(getattr(o, "display_name", None) or getattr(o, "to_string", lambda: None)() or str(o))
                            if nm == str(chosen):
                                setattr(obj, target_attr, o)
                                return
                    except Exception:
                        return
                _assign(rt, "available_output_routing_types", "output_routing_type", kwargs.get("audio_to_type"))
                _assign(rt, "available_output_routing_channels", "output_routing_channel", kwargs.get("audio_to_channel"))
                sm = kwargs.get("sends_mode")
                if sm is not None and hasattr(rt, "sends_are_pre"):
                    try:
                        rt.sends_are_pre = (str(sm).lower() == "pre")
                    except Exception:
                        pass
                return True
    except Exception:
        pass
    # Stub
    for r in _STATE.get("returns", []):
        if r["index"] == int(return_index):
            rr = r.setdefault("routing", {"audio_to": {"type": "Master", "channel": "1/2"}, "sends_mode": "post"})
            if kwargs.get("audio_to_type"):
                rr.setdefault("audio_to", {}).update({"type": kwargs.get("audio_to_type")})
            if kwargs.get("audio_to_channel"):
                rr.setdefault("audio_to", {}).update({"channel": kwargs.get("audio_to_channel")})
            if kwargs.get("sends_mode"):
                rr["sends_mode"] = str(kwargs.get("sends_mode")).lower()
            return True
    return False

# ---------------- Renaming & Device Order Ops ----------------

def set_track_name(live, track_index: int, name: str) -> bool:
    """Rename a track by index (1-based)."""
    try:
        idx = int(track_index)
        if live is not None and 1 <= idx <= len(getattr(live, 'tracks', [])):
            song = live
            try:
                if hasattr(song, 'begin_undo_step'):
                    song.begin_undo_step()
                tr = song.tracks[idx - 1]
                tr.name = str(name)
                _emit({"event": "track_renamed", "track": idx, "name": str(name)})
                return True
            finally:
                try:
                    if hasattr(song, 'end_undo_step'):
                        song.end_undo_step()
                except Exception:
                    pass
    except Exception:
        pass
    # Stub fallback
    for t in _STATE.get("tracks", []):
        if t["index"] == int(track_index):
            t["name"] = str(name)
            _emit({"event": "track_renamed", "track": int(track_index), "name": str(name)})
            return True
    return False


def set_scene_name(live, scene_index: int, name: str) -> bool:
    """Rename a scene by index (1-based)."""
    try:
        si = int(scene_index)
        if live is not None:
            scenes = getattr(live, 'scenes', []) or []
            if 1 <= si <= len(scenes):
                song = live
                try:
                    if hasattr(song, 'begin_undo_step'):
                        song.begin_undo_step()
                    sc = scenes[si - 1]
                    sc.name = str(name)
                    _emit({"event": "scene_renamed", "scene": si, "name": str(name)})
                    return True
                finally:
                    try:
                        if hasattr(song, 'end_undo_step'):
                            song.end_undo_step()
                    except Exception:
                        pass
    except Exception:
        pass
    # Stub
    _STATE.setdefault("scene_names", {})[int(scene_index)] = str(name)
    _emit({"event": "scene_renamed", "scene": int(scene_index), "name": str(name)})
    return True


def set_clip_name(live, track_index: int, scene_index: int, name: str) -> bool:
    """Rename a Session clip at [track, scene] (1-based indices).

    If the slot has no clip, returns False.
    """
    try:
        ti = int(track_index)
        si = int(scene_index)
        if live is not None:
            tracks = getattr(live, 'tracks', []) or []
            if 1 <= ti <= len(tracks):
                tr = tracks[ti - 1]
                slots = getattr(tr, 'clip_slots', []) or []
                if 1 <= si <= len(slots):
                    slot = slots[si - 1]
                    clip = getattr(slot, 'clip', None)
                    if clip is None:
                        return False
                    song = live
                    try:
                        if hasattr(song, 'begin_undo_step'):
                            song.begin_undo_step()
                        clip.name = str(name)
                        _emit({"event": "clip_renamed", "track": ti, "scene": si, "name": str(name)})
                        return True
                    finally:
                        try:
                            if hasattr(song, 'end_undo_step'):
                                song.end_undo_step()
                        except Exception:
                            pass
    except Exception:
        pass
    # Stub
    key = (int(track_index), int(scene_index))
    _STATE.setdefault("clips", {})[key] = str(name)
    _emit({"event": "clip_renamed", "track": int(track_index), "scene": int(scene_index), "name": str(name)})
    return True


def delete_track_device(live, track_index: int, device_index: int) -> bool:
    """Remove a device from a track by index (0-based device index)."""
    try:
        ti = int(track_index)
        di = int(device_index)
        if live is not None:
            tracks = getattr(live, 'tracks', []) or []
            if 1 <= ti <= len(tracks):
                tr = tracks[ti - 1]
                if hasattr(tr, 'delete_device'):
                    song = live
                    try:
                        if hasattr(song, 'begin_undo_step'):
                            song.begin_undo_step()
                        tr.delete_device(di)
                        _emit({"event": "track_device_deleted", "track": ti, "device_index": di})
                        return True
                    finally:
                        try:
                            if hasattr(song, 'end_undo_step'):
                                song.end_undo_step()
                        except Exception:
                            pass
    except Exception:
        pass
    # Stub
    for t in _STATE.get("tracks", []):
        if t["index"] == int(track_index):
            devs = t.setdefault("devices", [])
            if 0 <= int(device_index) < len(devs):
                devs.pop(int(device_index))
                for i, d in enumerate(devs):
                    d["index"] = i
                _emit({"event": "track_device_deleted", "track": int(track_index), "device_index": int(device_index)})
                return True
            return False
    return False


def reorder_track_device(live, track_index: int, old_index: int, new_index: int) -> bool:
    """Reorder a device within a track from old_index to new_index (0-based).

    Tries multiple API spellings for compatibility across Live versions.
    """
    try:
        ti = int(track_index)
        oi = int(old_index)
        ni = int(new_index)
        if live is not None:
            tracks = getattr(live, 'tracks', []) or []
            if 1 <= ti <= len(tracks):
                tr = tracks[ti - 1]
                song = live
                try:
                    if hasattr(song, 'begin_undo_step'):
                        song.begin_undo_step()
                    ok = False
                    try:
                        if hasattr(tr, 'reorder_device'):
                            try:
                                tr.reorder_device(oi, ni)
                                ok = True
                            except Exception:
                                devs = list(getattr(tr, 'devices', []) or [])
                                if 0 <= oi < len(devs):
                                    tr.reorder_device(devs[oi], ni)
                                    ok = True
                    except Exception:
                        ok = False
                    if not ok and hasattr(tr, 'reorder_devices'):
                        try:
                            tr.reorder_devices(oi, ni)
                            ok = True
                        except Exception:
                            pass
                    if ok:
                        _emit({"event": "track_device_reordered", "track": ti, "from": oi, "to": ni})
                        return True
                finally:
                    try:
                        if hasattr(song, 'end_undo_step'):
                            song.end_undo_step()
                    except Exception:
                        pass
    except Exception:
        pass
    # Stub
    for t in _STATE.get("tracks", []):
        if t["index"] == int(track_index):
            devs = t.setdefault("devices", [])
            if not (0 <= int(old_index) < len(devs) and 0 <= int(new_index) <= len(devs)):
                return False
            item = devs.pop(int(old_index))
            devs.insert(int(new_index), item)
            for i, d in enumerate(devs):
                d["index"] = i
            _emit({"event": "track_device_reordered", "track": int(track_index), "from": int(old_index), "to": int(new_index)})
            return True
    return False


def create_clip(live, track_index: int, scene_index: int, length_beats: float) -> Dict[str, Any]:
    """Create an empty MIDI clip in the given clip slot (Session view).

    Returns { ok: bool, error?: str }
    """
    try:
        ti = int(track_index)
        si = int(scene_index)
        length = max(0.25, float(length_beats))
        if live is not None:
            tracks = getattr(live, 'tracks', []) or []
            if not (1 <= ti <= len(tracks)):
                return {"ok": False, "error": "track_out_of_range"}
            tr = tracks[ti - 1]
            # Only MIDI tracks support create_clip
            try:
                is_midi = bool(getattr(tr, 'has_midi_input', False)) and not bool(getattr(tr, 'has_audio_input', False))
            except Exception:
                is_midi = False
            if not is_midi:
                return {"ok": False, "error": "track_not_midi"}
            slots = getattr(tr, 'clip_slots', []) or []
            if not (1 <= si <= len(slots)):
                return {"ok": False, "error": "scene_out_of_range"}
            slot = slots[si - 1]
            if getattr(slot, 'has_clip', False):
                return {"ok": False, "error": "slot_already_has_clip"}
            song = live
            try:
                if hasattr(song, 'begin_undo_step'):
                    song.begin_undo_step()
                slot.create_clip(length)
                _emit({"event": "clip_created", "track": ti, "scene": si, "length": float(length)})
                return {"ok": True}
            finally:
                try:
                    if hasattr(song, 'end_undo_step'):
                        song.end_undo_step()
                except Exception:
                    pass
    except Exception as e:
        return {"ok": False, "error": str(e)}
    # Stub
    key = (int(track_index), int(scene_index))
    _STATE.setdefault("clips", {})[key] = _STATE.get("clips", {}).get(key) or f"Clip {track_index}:{scene_index}"
    _emit({"event": "clip_created", "track": int(track_index), "scene": int(scene_index), "length": float(length_beats)})
    return {"ok": True}


def capture_and_insert_scene(live) -> Dict[str, Any]:
    """Capture current playing clips into a new scene and insert it below selection.

    Wraps `Song.capture_and_insert_scene()` when available.
    """
    try:
        if live is not None and hasattr(live, 'capture_and_insert_scene'):
            song = live
            try:
                if hasattr(song, 'begin_undo_step'):
                    song.begin_undo_step()
                live.capture_and_insert_scene()
                # Best effort: determine new count
                try:
                    count = len(getattr(live, 'scenes', []) or [])
                except Exception:
                    count = None
                _emit({"event": "scene_captured", "scenes": count})
                return {"ok": True, "scenes": count}
            finally:
                try:
                    if hasattr(song, 'end_undo_step'):
                        song.end_undo_step()
                except Exception:
                    pass
    except Exception as e:
        return {"ok": False, "error": str(e)}
    # Stub: increment scenes
    _STATE["scenes"] = int(_STATE.get("scenes", 0) or 0) + 1
    idx = _STATE["scenes"]
    _STATE.setdefault("scene_names", {})[idx] = f"Scene {idx}"
    _emit({"event": "scene_captured", "scenes": _STATE["scenes"]})
    return {"ok": True, "scenes": _STATE["scenes"]}


def set_view_mode(live, mode: str) -> Dict[str, Any]:
    """Switch between Session and Arrangement views when possible.

    mode: 'session' | 'arrangement'
    """
    m = (mode or '').strip().lower()
    target = 'Session' if m.startswith('sess') else 'Arranger'
    try:
        if _APP_VIEW_GETTER is not None:
            view = _APP_VIEW_GETTER()
            if view is not None and hasattr(view, 'show_view'):
                # Optional: avoid redundant calls
                try:
                    is_vis = None
                    if hasattr(view, 'is_view_visible'):
                        is_vis = bool(view.is_view_visible(target))
                    if not is_vis:
                        view.show_view(target)
                except Exception:
                    view.show_view(target)
                _emit({"event": "view_changed", "mode": target})
                return {"ok": True, "mode": target}
        return {"ok": False, "error": "app_view_unavailable"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def fire_scene(live, scene_index: int, select: bool = True) -> Dict[str, Any]:
    """Launch a scene by index (1-based). Optionally select it first."""
    try:
        si = int(scene_index)
        if live is not None:
            scenes = getattr(live, 'scenes', []) or []
            if not (1 <= si <= len(scenes)):
                return {"ok": False, "error": "scene_out_of_range"}
            sc = scenes[si - 1]
            try:
                if select and hasattr(getattr(live, 'view', None), 'selected_scene'):
                    live.view.selected_scene = sc
            except Exception:
                pass
            sc.fire()
            _emit({"event": "scene_fired", "scene": si})
            return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    # Stub
    _emit({"event": "scene_fired", "scene": int(scene_index)})
    return {"ok": True}


def stop_scene(live, scene_index: int) -> Dict[str, Any]:
    """Stop all clips in a scene by stopping each track's clip slot at that scene index."""
    try:
        si = int(scene_index)
        if live is not None:
            tracks = getattr(live, 'tracks', []) or []
            if not tracks:
                return {"ok": True}
            for tr in tracks:
                slots = getattr(tr, 'clip_slots', []) or []
                if 1 <= si <= len(slots):
                    try:
                        slots[si - 1].stop()
                    except Exception:
                        pass
            _emit({"event": "scene_stopped", "scene": si})
            return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    # Stub
    _emit({"event": "scene_stopped", "scene": int(scene_index)})
    return {"ok": True}


def delete_return_device(live, return_index: int, device_index: int) -> bool:
    """Remove a device from a return track by index (0-based device index)."""
    try:
        ri = int(return_index)
        di = int(device_index)
        if live is not None:
            returns = getattr(live, 'return_tracks', []) or []
            if 0 <= ri < len(returns):
                rt = returns[ri]
                if hasattr(rt, 'delete_device'):
                    song = live
                    try:
                        if hasattr(song, 'begin_undo_step'):
                            song.begin_undo_step()
                        rt.delete_device(di)
                        _emit({"event": "return_device_deleted", "return": ri, "device_index": di})
                        return True
                    finally:
                        try:
                            if hasattr(song, 'end_undo_step'):
                                song.end_undo_step()
                        except Exception:
                            pass
    except Exception:
        pass
    # Stub
    for r in _STATE.get("returns", []):
        if r["index"] == int(return_index):
            devs = r.setdefault("devices", [])
            if 0 <= int(device_index) < len(devs):
                devs.pop(int(device_index))
                for i, d in enumerate(devs):
                    d["index"] = i
                _emit({"event": "return_device_deleted", "return": int(return_index), "device_index": int(device_index)})
                return True
            return False
    return False


def reorder_return_device(live, return_index: int, old_index: int, new_index: int) -> bool:
    """Reorder a device within a return track from old_index to new_index (0-based)."""
    try:
        ri = int(return_index)
        oi = int(old_index)
        ni = int(new_index)
        if live is not None:
            returns = getattr(live, 'return_tracks', []) or []
            if 0 <= ri < len(returns):
                rt = returns[ri]
                song = live
                try:
                    if hasattr(song, 'begin_undo_step'):
                        song.begin_undo_step()
                    ok = False
                    try:
                        if hasattr(rt, 'reorder_device'):
                            try:
                                rt.reorder_device(oi, ni)
                                ok = True
                            except Exception:
                                devs = list(getattr(rt, 'devices', []) or [])
                                if 0 <= oi < len(devs):
                                    rt.reorder_device(devs[oi], ni)
                                    ok = True
                    except Exception:
                        ok = False
                    if not ok and hasattr(rt, 'reorder_devices'):
                        try:
                            rt.reorder_devices(oi, ni)
                            ok = True
                        except Exception:
                            pass
                    if ok:
                        _emit({"event": "return_device_reordered", "return": ri, "from": oi, "to": ni})
                        return True
                finally:
                    try:
                        if hasattr(song, 'end_undo_step'):
                            song.end_undo_step()
                    except Exception:
                        pass
    except Exception:
        pass
    # Stub
    for r in _STATE.get("returns", []):
        if r["index"] == int(return_index):
            devs = r.setdefault("devices", [])
            if not (0 <= int(old_index) < len(devs) and 0 <= int(new_index) <= len(devs)):
                return False
            item = devs.pop(int(old_index))
            devs.insert(int(new_index), item)
            for i, d in enumerate(devs):
                d["index"] = i
            _emit({"event": "return_device_reordered", "return": int(return_index), "from": int(old_index), "to": int(new_index)})
            return True
    return False
