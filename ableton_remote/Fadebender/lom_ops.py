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
import json


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
_DEVICE_MAP_CACHE: Optional[Dict[str, Any]] = None  # Lazy-loaded device mapping


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


def _load_device_mapping() -> Dict[str, Any]:
    """Load device mapping from ~/.fadebender/device_map.json (best-effort, cached)."""
    global _DEVICE_MAP_CACHE
    if _DEVICE_MAP_CACHE is not None:
        return _DEVICE_MAP_CACHE
    try:
        config_path = os.path.expanduser("~/.fadebender/device_map.json")
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                _DEVICE_MAP_CACHE = json.load(f) or {}
                return _DEVICE_MAP_CACHE
    except Exception:
        pass
    _DEVICE_MAP_CACHE = {}
    return _DEVICE_MAP_CACHE


def _get_browser_from_live(live) -> Any:
    """Best-effort helper to obtain Live's Application.browser from a Song.

    Tries multiple strategies to maximize compatibility across Live versions.
    """
    app = None
    # 1) song.app if available
    try:
        app = getattr(live, "app", None)
    except Exception:
        app = None
    # 2) Application.view's canonical parent (often Application)
    if app is None and _APP_VIEW_GETTER is not None:
        try:
            view = _APP_VIEW_GETTER()
            if view is not None:
                app = getattr(view, "canonical_parent", None) or getattr(view, "app", None)
        except Exception:
            app = None
    # 3) Live.Application.get_application()
    if app is None:
        try:
            import Live  # type: ignore

            app = Live.Application.get_application()
        except Exception:
            app = None
    if app is None:
        return None
    try:
        return getattr(app, "browser", None)
    except Exception:
        return None


def _navigate_browser_path(browser, path: List[str]):
    """Navigate a Live browser tree using a simple path list.

    path examples: ['audio_effects', 'Reverb'], ['midi_effects', 'Chord'], etc.
    """
    if not path:
        return None
    root = path[0]
    try:
        if root == "audio_effects":
            current = getattr(browser, "audio_effects", None)
        elif root == "midi_effects":
            current = getattr(browser, "midi_effects", None)
        elif root == "plugins":
            current = getattr(browser, "plugins", None)
        elif root == "samples":
            current = getattr(browser, "samples", None)
        else:
            return None
    except Exception:
        return None
    for name in path[1:]:
        try:
            children = list(getattr(current, "iter_children", []) or [])
            current = next((item for item in children if str(getattr(item, "name", "")) == str(name)), None)
        except Exception:
            return None
        if current is None:
            return None
    return current


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
                        val = float(getattr(param, 'value', 0.0))
                        display = None
                        try:
                            display = str(param.str_for_value(val))
                        except:
                            pass
                        _emit({"event": "mixer_changed", "track": track_idx, "field": "volume", "value": val, "display_value": display})
                    except Exception:
                        pass
                return _cb
            _add_param_listener(vol, make_cb())
        if pan is not None:
            def make_cb(param=pan, track_idx=idx):
                def _cb():
                    try:
                        val = float(getattr(param, 'value', 0.0))
                        display = None
                        try:
                            display = str(param.str_for_value(val))
                        except:
                            pass
                        _emit({"event": "mixer_changed", "track": track_idx, "field": "pan", "value": val, "display_value": display})
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
                        val = float(getattr(param, 'value', 0.0))
                        display = None
                        try:
                            display = str(param.str_for_value(val))
                        except:
                            pass
                        _emit({"event": "return_mixer_changed", "return": return_idx, "field": "volume", "value": val, "display_value": display})
                    except Exception:
                        pass
                return _cb
            _add_param_listener(vol, make_cb())
        if pan is not None:
            def make_cb(param=pan, return_idx=idx):
                def _cb():
                    try:
                        val = float(getattr(param, 'value', 0.0))
                        display = None
                        try:
                            display = str(param.str_for_value(val))
                        except:
                            pass
                        _emit({"event": "return_mixer_changed", "return": return_idx, "field": "pan", "value": val, "display_value": display})
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
                    display = None
                    try:
                        display = str(param.str_for_value(val))
                    except:
                        pass
                    _emit({"event": "master_mixer_changed", "field": field, "value": val, "display_value": display})
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


def create_audio_track(live, index: int | None = None) -> Dict[str, Any]:
    """Create an audio track at the given 1-based index (or append if None)."""
    try:
        if live is not None:
            song = live

            def _do_create():
                tracks = getattr(song, "tracks", []) or []
                n = len(tracks)
                if index is None:
                    insert_idx = n
                else:
                    try:
                        idx1 = int(index)
                    except Exception:
                        idx1 = n + 1
                    insert_idx = max(0, min(n, idx1 - 1))
                try:
                    song.create_audio_track(insert_idx)
                    _emit({"event": "track_created", "type": "audio", "index": insert_idx + 1})
                    return {"ok": True, "index": insert_idx + 1}
                except Exception as e:
                    return {"ok": False, "error": str(e)}

            return _run_on_main(_do_create) or {"ok": False}
    except Exception as e:
        return {"ok": False, "error": str(e)}

    # Stub: append audio track
    tracks = _STATE.setdefault("tracks", [])
    next_idx = (tracks[-1]["index"] + 1) if tracks else 1
    tracks.append(
        {
            "index": next_idx,
            "name": f"Track {next_idx}",
            "type": "audio",
            "mixer": {"volume": 0.5, "pan": 0.0},
            "mute": False,
            "solo": False,
            "sends": [0.0, 0.0],
            "devices": [],
        }
    )
    _emit({"event": "track_created", "type": "audio", "index": next_idx})
    return {"ok": True, "index": next_idx}


def create_midi_track(live, index: int | None = None) -> Dict[str, Any]:
    """Create a MIDI track at the given 1-based index (or append if None)."""
    try:
        if live is not None:
            song = live

            def _do_create():
                tracks = getattr(song, "tracks", []) or []
                n = len(tracks)
                if index is None:
                    insert_idx = n
                else:
                    try:
                        idx1 = int(index)
                    except Exception:
                        idx1 = n + 1
                    insert_idx = max(0, min(n, idx1 - 1))
                try:
                    song.create_midi_track(insert_idx)
                    _emit({"event": "track_created", "type": "midi", "index": insert_idx + 1})
                    return {"ok": True, "index": insert_idx + 1}
                except Exception as e:
                    return {"ok": False, "error": str(e)}

            return _run_on_main(_do_create) or {"ok": False}
    except Exception as e:
        return {"ok": False, "error": str(e)}

    # Stub: append midi track
    tracks = _STATE.setdefault("tracks", [])
    next_idx = (tracks[-1]["index"] + 1) if tracks else 1
    tracks.append(
        {
            "index": next_idx,
            "name": f"Track {next_idx}",
            "type": "midi",
            "mixer": {"volume": 0.5, "pan": 0.0},
            "mute": False,
            "solo": False,
            "sends": [0.0, 0.0],
            "devices": [],
        }
    )
    _emit({"event": "track_created", "type": "midi", "index": next_idx})
    return {"ok": True, "index": next_idx}


def create_return_track(live) -> Dict[str, Any]:
    """Create a new return track (appended at the end)."""
    try:
        if live is not None:
            song = live

            def _do_create():
                try:
                    before = len(getattr(song, "return_tracks", []) or [])
                    song.create_return_track()
                    after = len(getattr(song, "return_tracks", []) or [])
                    idx = after - 1 if after > 0 else before
                    _emit({"event": "return_created", "index": idx})
                    return {"ok": True, "index": idx}
                except Exception as e:
                    return {"ok": False, "error": str(e)}

            return _run_on_main(_do_create) or {"ok": False}
    except Exception as e:
        return {"ok": False, "error": str(e)}

    # Stub: append return track
    returns = _STATE.setdefault("returns", [])
    next_idx = (returns[-1]["index"] + 1) if returns else 0
    returns.append(
        {
            "index": next_idx,
            "name": f"{chr(ord('A') + next_idx)} Return",
            "routing": {"audio_to": {"type": "Master", "channel": "1/2"}, "sends_mode": "post"},
            "devices": [],
        }
    )
    _emit({"event": "return_created", "index": next_idx})
    return {"ok": True, "index": next_idx}


def delete_track(live, track_index: int) -> Dict[str, Any]:
    """Delete a track by 1-based index (excluding master/return tracks)."""
    try:
        ti = int(track_index)
        if live is not None:
            song = live

            def _do_delete():
                tracks = getattr(song, "tracks", []) or []
                if not (1 <= ti <= len(tracks)):
                    return {"ok": False, "error": "track_out_of_range"}
                try:
                    song.delete_track(ti - 1)
                    _emit({"event": "track_deleted", "index": ti})
                    return {"ok": True}
                except Exception as e:
                    return {"ok": False, "error": str(e)}

            return _run_on_main(_do_delete) or {"ok": False}
    except Exception as e:
        return {"ok": False, "error": str(e)}

    # Stub
    tracks = _STATE.setdefault("tracks", [])
    try:
        ti = int(track_index)
        idx = next((i for i, t in enumerate(tracks) if t["index"] == ti), None)
        if idx is None:
            return {"ok": False, "error": "track_not_found"}
        tracks.pop(idx)
        # Reindex
        for i, t in enumerate(tracks, start=1):
            t["index"] = i
        _emit({"event": "track_deleted", "index": ti})
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def duplicate_track(live, track_index: int) -> Dict[str, Any]:
    """Duplicate a track by 1-based index."""
    try:
        ti = int(track_index)
        if live is not None:
            song = live

            def _do_dup():
                tracks = getattr(song, "tracks", []) or []
                if not (1 <= ti <= len(tracks)):
                    return {"ok": False, "error": "track_out_of_range"}
                try:
                    song.duplicate_track(ti - 1)
                    _emit({"event": "track_duplicated", "index": ti})
                    return {"ok": True}
                except Exception as e:
                    return {"ok": False, "error": str(e)}

            return _run_on_main(_do_dup) or {"ok": False}
    except Exception as e:
        return {"ok": False, "error": str(e)}

    # Stub: shallow duplicate of track dict
    tracks = _STATE.setdefault("tracks", [])
    try:
        ti = int(track_index)
        src = next((t for t in tracks if t["index"] == ti), None)
        if src is None:
            return {"ok": False, "error": "track_not_found"}
        import copy

        dup = copy.deepcopy(src)
        next_idx = (tracks[-1]["index"] + 1) if tracks else ti + 1
        dup["index"] = next_idx
        dup["name"] = f"{src.get('name','Track')} Copy"
        tracks.append(dup)
        _emit({"event": "track_duplicated", "index": ti, "new_index": next_idx})
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def create_scene(live, index: int | None = None) -> Dict[str, Any]:
    """Create a blank scene at the given 1-based index (or append if None)."""
    try:
        if live is not None:
            song = live

            def _do_create():
                scenes = getattr(song, "scenes", []) or []
                n = len(scenes)
                if index is None:
                    insert_idx = n
                else:
                    try:
                        idx1 = int(index)
                    except Exception:
                        idx1 = n + 1
                    insert_idx = max(0, min(n, idx1 - 1))
                try:
                    song.create_scene(insert_idx)
                    _emit({"event": "scene_created", "index": insert_idx + 1})
                    return {"ok": True, "index": insert_idx + 1}
                except Exception as e:
                    return {"ok": False, "error": str(e)}

            return _run_on_main(_do_create) or {"ok": False}
    except Exception as e:
        return {"ok": False, "error": str(e)}

    # Stub
    _STATE["scenes"] = int(_STATE.get("scenes", 0) or 0) + 1
    idx = _STATE["scenes"]
    _STATE.setdefault("scene_names", {})[idx] = f"Scene {idx}"
    _emit({"event": "scene_created", "index": idx})
    return {"ok": True, "index": idx}


def delete_scene(live, scene_index: int) -> Dict[str, Any]:
    """Delete a scene by 1-based index."""
    try:
        si = int(scene_index)
        if live is not None:
            song = live

            def _do_delete():
                scenes = getattr(song, "scenes", []) or []
                if not (1 <= si <= len(scenes)):
                    return {"ok": False, "error": "scene_out_of_range"}
                try:
                    song.delete_scene(si - 1)
                    _emit({"event": "scene_deleted", "index": si})
                    return {"ok": True}
                except Exception as e:
                    return {"ok": False, "error": str(e)}

            return _run_on_main(_do_delete) or {"ok": False}
    except Exception as e:
        return {"ok": False, "error": str(e)}

    # Stub
    try:
        si = int(scene_index)
        total = int(_STATE.get("scenes", 0) or 0)
        if not (1 <= si <= total):
            return {"ok": False, "error": "scene_out_of_range"}
        names = _STATE.setdefault("scene_names", {})
        # Shift down names above deleted index
        for i in range(si, total):
            names[i] = names.get(i + 1, f"Scene {i}")
        names.pop(total, None)
        _STATE["scenes"] = total - 1
        _emit({"event": "scene_deleted", "index": si})
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def duplicate_scene(live, scene_index: int) -> Dict[str, Any]:
    """Duplicate a scene by 1-based index."""
    try:
        si = int(scene_index)
        if live is not None:
            song = live

            def _do_dup():
                scenes = getattr(song, "scenes", []) or []
                if not (1 <= si <= len(scenes)):
                    return {"ok": False, "error": "scene_out_of_range"}
                try:
                    # Some Live versions provide duplicate_scene(scene), others duplicate_scene(index)
                    sc = scenes[si - 1]
                    dup_ok = False
                    try:
                        song.duplicate_scene(sc)
                        dup_ok = True
                    except Exception:
                        try:
                            song.duplicate_scene(si - 1)
                            dup_ok = True
                        except Exception:
                            dup_ok = False
                    if dup_ok:
                        _emit({"event": "scene_duplicated", "index": si})
                        return {"ok": True}
                    return {"ok": False, "error": "duplicate_failed"}
                except Exception as e:
                    return {"ok": False, "error": str(e)}

            return _run_on_main(_do_dup) or {"ok": False}
    except Exception as e:
        return {"ok": False, "error": str(e)}

    # Stub
    try:
        si = int(scene_index)
        total = int(_STATE.get("scenes", 0) or 0)
        if not (1 <= si <= total):
            return {"ok": False, "error": "scene_out_of_range"}
        names = _STATE.setdefault("scene_names", {})
        # Insert duplicate name after si
        dup_name = names.get(si, f"Scene {si}") + " Copy"
        for i in range(total, si, -1):
            names[i + 1] = names.get(i, f"Scene {i}")
        names[si + 1] = dup_name
        _STATE["scenes"] = total + 1
        _emit({"event": "scene_duplicated", "index": si})
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}


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


# ---------------- Song-level helpers (undo, info, cues) ----------------

def get_undo_status(live) -> Dict[str, Any]:
    """Return whether Live reports that undo/redo are currently possible."""
    try:
        if live is not None:
            song = live
            can_undo = bool(getattr(song, "can_undo", False))
            can_redo = bool(getattr(song, "can_redo", False))
            return {"can_undo": can_undo, "can_redo": can_redo}
    except Exception:
        pass
    # Stub: no real undo stack, just report False
    return {"can_undo": False, "can_redo": False}


def song_undo(live) -> Dict[str, Any]:
    """Trigger Live's global undo (project-wide history)."""
    try:
        if live is not None and hasattr(live, "undo"):
            def _do_undo():
                try:
                    live.undo()
                    return {"ok": True}
                except Exception as e:
                    return {"ok": False, "error": str(e)}
            res = _run_on_main(_do_undo)
            return res or {"ok": False}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    # Stub: nothing to undo
    return {"ok": False, "error": "undo_not_available"}


def song_redo(live) -> Dict[str, Any]:
    """Trigger Live's global redo (project-wide history)."""
    try:
        if live is not None and hasattr(live, "redo"):
            def _do_redo():
                try:
                    live.redo()
                    return {"ok": True}
                except Exception as e:
                    return {"ok": False, "error": str(e)}
            res = _run_on_main(_do_redo)
            return res or {"ok": False}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    # Stub: nothing to redo
    return {"ok": False, "error": "redo_not_available"}


def get_song_info(live) -> Dict[str, Any]:
    """Return basic Live Set metadata (name, tempo, time signature, song length)."""
    if live is not None:
        try:
            song = live
            name = ""
            try:
                raw_name = getattr(song, "name", "")  # Live Set name (no .als)
                if raw_name is not None:
                    name = str(raw_name)
            except Exception:
                name = ""
            try:
                tempo = float(getattr(song, "tempo", 120.0))
            except Exception:
                tempo = 120.0
            try:
                num = int(getattr(song, "signature_numerator", 4))
            except Exception:
                num = 4
            try:
                den = int(getattr(song, "signature_denominator", 4))
            except Exception:
                den = 4
            try:
                song_length = float(getattr(song, "song_length", 0.0))
            except Exception:
                song_length = 0.0
            return {
                "name": name,
                "tempo": tempo,
                "time_signature_numerator": num,
                "time_signature_denominator": den,
                "song_length": song_length,
            }
        except Exception:
            pass
    # Stub: derive from in-memory transport + a generic name
    tr = dict(_STATE.get("transport", {}))
    return {
        "name": "Untitled Set",
        "tempo": float(tr.get("tempo", 120.0)),
        "time_signature_numerator": int(tr.get("time_signature_numerator", 4)),
        "time_signature_denominator": int(tr.get("time_signature_denominator", 4)),
        "song_length": float(tr.get("song_length", 0.0)),
    }


def get_cue_points(live) -> Dict[str, Any]:
    """Return arrangement cue points (locators) as a simple list."""
    try:
        if live is not None:
            song = live
            cues = list(getattr(song, "cue_points", []) or [])
            out = []
            for idx, cp in enumerate(cues, start=1):
                try:
                    t = float(getattr(cp, "time", 0.0))
                except Exception:
                    t = 0.0
                try:
                    name = str(getattr(cp, "name", f"Cue {idx}"))
                except Exception:
                    name = f"Cue {idx}"
                out.append({"index": idx, "time": t, "name": name})
            return {"cue_points": out}
    except Exception:
        pass
    # Stub: use in-memory list
    cps = _STATE.setdefault("cue_points", [])
    return {"cue_points": list(cps)}


def add_cue_point(live, time_beats: float | None = None, name: str | None = None) -> Dict[str, Any]:
    """Add a cue point at the given time (or current song time if None)."""
    try:
        if live is not None:
            song = live

            def _do_add():
                # Snapshot existing cue objects so we can detect the new one
                before = list(getattr(song, "cue_points", []) or [])
                try:
                    t = float(time_beats) if time_beats is not None else float(getattr(song, "current_song_time", 0.0))
                except Exception:
                    t = 0.0
                created = None
                # Prefer explicit create API when available
                try:
                    if hasattr(song, "create_cue_point"):
                        created = song.create_cue_point(t)
                    elif hasattr(song, "add_or_delete_cue"):
                        # Fallback: move playhead then toggle cue at that point
                        try:
                            setattr(song, "current_song_time", t)
                        except Exception:
                            pass
                        song.add_or_delete_cue()
                except Exception:
                    created = None

                cues = list(getattr(song, "cue_points", []) or [])
                # Try to infer which cue is new
                new_cue = None
                try:
                    if created is not None and created in cues and created not in before:
                        new_cue = created
                    else:
                        before_set = set(before)
                        candidates = [cp for cp in cues if cp not in before_set]
                        if len(candidates) == 1:
                            new_cue = candidates[0]
                        elif candidates:
                            # Pick the one whose time is closest to requested t
                            def _time(cp):
                                try:
                                    return float(getattr(cp, "time", 0.0))
                                except Exception:
                                    return 0.0
                            new_cue = min(candidates, key=lambda cp: abs(_time(cp) - float(t)))
                except Exception:
                    new_cue = None

                # Fallback: if we still didn't identify a unique cue, just use the last one
                if new_cue is None and cues:
                    new_cue = cues[-1]

                # Apply name if requested
                if name and new_cue is not None:
                    try:
                        setattr(new_cue, "name", str(name))
                    except Exception:
                        pass

                # Compute index and actual time from the final cue list
                idx = 0
                actual_time = t
                cue_name = name
                try:
                    # Sort cues by time to derive a stable 1-based index
                    def _time(cp):
                        try:
                            return float(getattr(cp, "time", 0.0))
                        except Exception:
                            return 0.0

                    cues_sorted = sorted(cues, key=_time)
                    if new_cue is not None and new_cue in cues_sorted:
                        idx = cues_sorted.index(new_cue) + 1
                        actual_time = _time(new_cue)
                        try:
                            cue_name = str(getattr(new_cue, "name", cue_name or f"Cue {idx}"))
                        except Exception:
                            cue_name = cue_name or f"Cue {idx}"
                    else:
                        # Fallback: use last cue
                        last = cues_sorted[-1]
                        idx = len(cues_sorted)
                        actual_time = _time(last)
                        try:
                            cue_name = str(getattr(last, "name", cue_name or f"Cue {idx}"))
                        except Exception:
                            cue_name = cue_name or f"Cue {idx}"
                except Exception:
                    idx = len(cues) or 1
                    actual_time = t
                    if not cue_name:
                        cue_name = f"Cue {idx}"

                return {"ok": True, "index": idx, "time": float(actual_time), "name": cue_name}

            res = _run_on_main(_do_add)
            return res or {"ok": False}
    except Exception as e:
        return {"ok": False, "error": str(e)}

    # Stub: append to in-memory list
    cps = _STATE.setdefault("cue_points", [])
    idx = len(cps) + 1
    try:
        t = float(time_beats) if time_beats is not None else float(_STATE.get("transport", {}).get("current_song_time", 0.0))
    except Exception:
        t = 0.0
    cue_name = name or f"Cue {idx}"
    cp = {"index": idx, "time": float(t), "name": cue_name}
    cps.append(cp)
    return {"ok": True, "index": idx, "time": float(t), "name": cue_name}


def set_cue_name(live, cue_index: int, name: str) -> Dict[str, Any]:
    """Rename a cue point by 1-based index."""
    try:
        ci = int(cue_index)
        if live is not None:
            song = live

            def _do_rename():
                cues = list(getattr(song, "cue_points", []) or [])
                if not (1 <= ci <= len(cues)):
                    return {"ok": False, "error": "cue_out_of_range"}
                cp = cues[ci - 1]
                try:
                    setattr(cp, "name", str(name))
                except Exception:
                    return {"ok": False, "error": "rename_failed"}
                return {"ok": True, "index": ci, "name": str(name)}

            res = _run_on_main(_do_rename)
            return res or {"ok": False}
    except Exception as e:
        return {"ok": False, "error": str(e)}

    # Stub
    cps = _STATE.setdefault("cue_points", [])
    if 1 <= int(cue_index) <= len(cps):
        cps[int(cue_index) - 1]["name"] = str(name)
        return {"ok": True, "index": int(cue_index), "name": str(name)}
    return {"ok": False, "error": "cue_out_of_range"}


def set_cue_time(live, cue_index: int, time_beats: float) -> Dict[str, Any]:
    """Move a cue point to a new time (in beats) by 1-based index.

    Note: On the target Live build, CuePoint.time is read-only and cannot be
    written from a Remote Script. We expose this helper only for stub/dev mode.
    """
    # Live does not support moving cues from Remote Scripts in this environment.
    if live is not None:
        return {"ok": False, "error": "live_cue_move_not_supported"}

    # Stub (dev mode only)
    cps = _STATE.setdefault("cue_points", [])
    ci = int(cue_index)
    if not (1 <= ci <= len(cps)):
        return {"ok": False, "error": "cue_out_of_range"}
    cps[ci - 1]["time"] = float(time_beats)
    return {"ok": True, "index": ci, "time": float(time_beats)}


def delete_cue_point(live, cue_index: int) -> Dict[str, Any]:
    """Delete a cue point by 1-based index."""
    try:
        ci = int(cue_index)
        if live is not None:
            song = live

            def _do_delete():
                cues = list(getattr(song, "cue_points", []) or [])
                if not (1 <= ci <= len(cues)):
                    return {"ok": False, "error": "cue_out_of_range"}
                cp = cues[ci - 1]
                try:
                    if hasattr(song, "delete_cue_point"):
                        song.delete_cue_point(cp)
                    elif hasattr(cp, "delete"):
                        cp.delete()
                    else:
                        return {"ok": False, "error": "delete_not_supported"}
                    return {"ok": True, "index": ci}
                except Exception as e:
                    return {"ok": False, "error": str(e)}

            res = _run_on_main(_do_delete)
            return res or {"ok": False}
    except Exception as e:
        return {"ok": False, "error": str(e)}

    # Stub
    cps = _STATE.setdefault("cue_points", [])
    ci = int(cue_index)
    if not (1 <= ci <= len(cps)):
        return {"ok": False, "error": "cue_out_of_range"}
    cps.pop(ci - 1)
    for i, cp in enumerate(cps, start=1):
        cp["index"] = i
    return {"ok": True, "index": ci}


def jump_to_cue(live, cue_index: int | None = None, name: str | None = None) -> Dict[str, Any]:
    """Move the song position to a cue point by index or name."""
    try:
        if live is not None:
            song = live

            def _do_jump():
                cues = list(getattr(song, "cue_points", []) or [])
                target = None
                if cue_index is not None:
                    try:
                        ci = int(cue_index)
                        if 1 <= ci <= len(cues):
                            target = cues[ci - 1]
                    except Exception:
                        target = None
                elif name:
                    target_name = str(name).strip().lower()
                    for cp in cues:
                        try:
                            if str(getattr(cp, "name", "")).strip().lower() == target_name:
                                target = cp
                                break
                        except Exception:
                            continue
                if target is None:
                    return {"ok": False, "error": "cue_not_found"}
                try:
                    t = float(getattr(target, "time", 0.0))
                except Exception:
                    t = 0.0
                try:
                    setattr(song, "current_song_time", t)
                except Exception:
                    return {"ok": False, "error": "jump_failed"}
                return {"ok": True, "time": float(t)}

            res = _run_on_main(_do_jump)
            return res or {"ok": False}
    except Exception as e:
        return {"ok": False, "error": str(e)}

    # Stub
    cps = _STATE.setdefault("cue_points", [])
    target = None
    if cue_index is not None:
        try:
            ci = int(cue_index)
            if 1 <= ci <= len(cps):
                target = cps[ci - 1]
        except Exception:
            target = None
    elif name:
        n = str(name).strip().lower()
        for cp in cps:
            if str(cp.get("name", "")).strip().lower() == n:
                target = cp
                break
    if target is None:
        return {"ok": False, "error": "cue_not_found"}
    t = float(target.get("time", 0.0))
    _STATE.setdefault("transport", {})["current_song_time"] = t
    return {"ok": True, "time": float(t)}


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


def set_track_arm(live, track_index: int, arm: bool) -> bool:
    """Arm or disarm a track by index (1-based)."""
    try:
        ti = int(track_index)
        if live is not None:
            tracks = getattr(live, "tracks", []) or []
            if not (1 <= ti <= len(tracks)):
                return False
            tr = tracks[ti - 1]

            def _do_set_arm():
                try:
                    if hasattr(tr, "can_be_armed") and not getattr(tr, "can_be_armed", True):
                        return False
                    setattr(tr, "arm", bool(arm))
                    _emit({"event": "track_armed", "track": ti, "armed": bool(arm)})
                    return True
                except Exception:
                    return False

            ok = _run_on_main(_do_set_arm)
            if bool(ok):
                return True
    except Exception:
        pass
    # Stub
    for t in _STATE.get("tracks", []):
        if t["index"] == int(track_index):
            t["armed"] = bool(arm)
            _emit({"event": "track_armed", "track": int(track_index), "armed": bool(arm)})
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

            def _do_set_name():
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

            ok = _run_on_main(_do_set_name)
            if bool(ok):
                return True
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

                def _do_set_scene_name():
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

                ok = _run_on_main(_do_set_scene_name)
                if bool(ok):
                    return True
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

                    def _do_set_clip_name():
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

                    ok = _run_on_main(_do_set_clip_name)
                    if bool(ok):
                        return True
    except Exception:
        pass
    # Stub
    key = (int(track_index), int(scene_index))
    _STATE.setdefault("clips", {})[key] = str(name)
    _emit({"event": "clip_renamed", "track": int(track_index), "scene": int(scene_index), "name": str(name)})
    return True


def set_track_device_name(live, track_index: int, device_index: int, name: str) -> bool:
    """Rename a device on a track by [track, device] indices (1-based track, 0-based device)."""
    try:
        ti = int(track_index)
        di = int(device_index)
        if live is not None:
            tracks = getattr(live, "tracks", []) or []
            if 1 <= ti <= len(tracks):
                song = live
                tr = tracks[ti - 1]

                def _do_set_track_device_name():
                    try:
                        if hasattr(song, "begin_undo_step"):
                            song.begin_undo_step()
                        devs = getattr(tr, "devices", []) or []
                        if not (0 <= di < len(devs)):
                            return False
                        dv = devs[di]
                        dv.name = str(name)
                        _emit(
                            {
                                "event": "track_device_renamed",
                                "track": ti,
                                "device_index": di,
                                "name": str(name),
                            }
                        )
                        return True
                    finally:
                        try:
                            if hasattr(song, "end_undo_step"):
                                song.end_undo_step()
                        except Exception:
                            pass

                ok = _run_on_main(_do_set_track_device_name)
                if bool(ok):
                    return True
    except Exception:
        pass
    # Stub: update in-memory state
    for t in _STATE.get("tracks", []):
        if t["index"] == int(track_index):
            devs = t.setdefault("devices", [])
            if 0 <= int(device_index) < len(devs):
                devs[int(device_index)]["name"] = str(name)
                _emit(
                    {
                        "event": "track_device_renamed",
                        "track": int(track_index),
                        "device_index": int(device_index),
                        "name": str(name),
                    }
                )
                return True
            break
    return False


def set_return_device_name(live, return_index: int, device_index: int, name: str) -> bool:
    """Rename a device on a return track by [return, device] indices (0-based return, 0-based device)."""
    try:
        ri = int(return_index)
        di = int(device_index)
        if live is not None:
            returns = getattr(live, "return_tracks", []) or []
            if 0 <= ri < len(returns):
                song = live
                rt = returns[ri]

                def _do_set_return_device_name():
                    try:
                        if hasattr(song, "begin_undo_step"):
                            song.begin_undo_step()
                        devs = getattr(rt, "devices", []) or []
                        if not (0 <= di < len(devs)):
                            return False
                        dv = devs[di]
                        dv.name = str(name)
                        _emit(
                            {
                                "event": "return_device_renamed",
                                "return": ri,
                                "device_index": di,
                                "name": str(name),
                            }
                        )
                        return True
                    finally:
                        try:
                            if hasattr(song, "end_undo_step"):
                                song.end_undo_step()
                        except Exception:
                            pass

                ok = _run_on_main(_do_set_return_device_name)
                if bool(ok):
                    return True
    except Exception:
        pass
    # Stub: update in-memory state
    for r in _STATE.get("returns", []):
        if r["index"] == int(return_index):
            devs = r.setdefault("devices", [])
            if 0 <= int(device_index) < len(devs):
                devs[int(device_index)]["name"] = str(name)
                _emit(
                    {
                        "event": "return_device_renamed",
                        "return": int(return_index),
                        "device_index": int(device_index),
                        "name": str(name),
                    }
                )
                return True
            break
    return False


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
                    def _do_delete_device():
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

                    ok = _run_on_main(_do_delete_device)
                    if bool(ok):
                        return True
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


def load_device_on_return(live, return_index: int, device_name: str, preset_name: Optional[str] = None) -> Dict[str, Any]:
    """Load a device (optionally preset) onto a return track.

    Uses a simple device mapping at ~/.fadebender/device_map.json and Live's browser API.
    This is best-effort and may not be supported on all Live versions.
    """
    try:
        ri = int(return_index)
        if live is not None:
            browser = _get_browser_from_live(live)
            if browser is None:
                return {"ok": False, "error": "browser_not_available"}
            mapping = _load_device_mapping()
            info = mapping.get(str(device_name)) or mapping.get(device_name)
            if not info:
                return {"ok": False, "error": f"device_not_found:{device_name}"}

            # Choose path: preset-specific if available, else default path
            path = None
            if preset_name:
                presets = info.get("presets") or {}
                path = presets.get(preset_name)
            if path is None:
                path = info.get("path")
            if not isinstance(path, list) or not path:
                return {"ok": False, "error": "invalid_device_path"}

            item = _navigate_browser_path(browser, path)
            if item is None:
                return {"ok": False, "error": "browser_item_not_found"}
            try:
                if not bool(getattr(item, "is_loadable", True)):
                    return {"ok": False, "error": "item_not_loadable"}
            except Exception:
                pass

            returns = list(getattr(live, "return_tracks", []) or [])
            if not (0 <= ri < len(returns)):
                return {"ok": False, "error": "return_index_out_of_range"}
            rt = returns[ri]
            song = live

            def _do_load():
                try:
                    if hasattr(song, "begin_undo_step"):
                        song.begin_undo_step()
                    # Prefer explicit target, fall back to default load_item signature
                    try:
                        browser.load_item(item, rt)
                    except TypeError:
                        browser.load_item(item)
                    # Inspect devices after load
                    devs = list(getattr(rt, "devices", []) or [])
                    if devs:
                        dv = devs[-1]
                        return {
                            "ok": True,
                            "return_index": ri,
                            "device_index": len(devs) - 1,
                            "device_name": str(getattr(dv, "name", device_name)),
                        }
                    return {"ok": True, "return_index": ri, "device_index": None}
                except Exception as e:
                    return {"ok": False, "error": str(e)}
                finally:
                    try:
                        if hasattr(song, "end_undo_step"):
                            song.end_undo_step()
                    except Exception:
                        pass

            res = _run_on_main(_do_load)
            return res or {"ok": False, "error": "load_failed"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

    # Stub: append a fake device to return track in _STATE
    returns = _STATE.setdefault("returns", [])
    for r in returns:
        if r.get("index") == int(return_index):
            devs = r.setdefault("devices", [])
            new_index = len(devs)
            devs.append({"index": new_index, "name": str(device_name)})
            _emit({"event": "return_device_loaded", "return": int(return_index), "device_index": new_index, "name": str(device_name)})
            return {"ok": True, "return_index": int(return_index), "device_index": new_index, "device_name": str(device_name)}
    return {"ok": False, "error": "return_not_found_stub"}


def load_device_on_track(live, track_index: int, device_name: str, preset_name: Optional[str] = None) -> Dict[str, Any]:
    """Load a device (optionally preset) onto a regular track."""
    try:
        ti = int(track_index)
        if live is not None:
            browser = _get_browser_from_live(live)
            if browser is None:
                return {"ok": False, "error": "browser_not_available"}
            mapping = _load_device_mapping()
            info = mapping.get(str(device_name)) or mapping.get(device_name)
            if not info:
                return {"ok": False, "error": f"device_not_found:{device_name}"}

            path = None
            if preset_name:
                presets = info.get("presets") or {}
                path = presets.get(preset_name)
            if path is None:
                path = info.get("path")
            if not isinstance(path, list) or not path:
                return {"ok": False, "error": "invalid_device_path"}

            item = _navigate_browser_path(browser, path)
            if item is None:
                return {"ok": False, "error": "browser_item_not_found"}
            try:
                if not bool(getattr(item, "is_loadable", True)):
                    return {"ok": False, "error": "item_not_loadable"}
            except Exception:
                pass

            tracks = list(getattr(live, "tracks", []) or [])
            if not (1 <= ti <= len(tracks)):
                return {"ok": False, "error": "track_index_out_of_range"}
            tr = tracks[ti - 1]
            song = live

            def _do_load():
                try:
                    if hasattr(song, "begin_undo_step"):
                        song.begin_undo_step()
                    try:
                        browser.load_item(item, tr)
                    except TypeError:
                        browser.load_item(item)
                    devs = list(getattr(tr, "devices", []) or [])
                    if devs:
                        dv = devs[-1]
                        return {
                            "ok": True,
                            "track_index": ti,
                            "device_index": len(devs) - 1,
                            "device_name": str(getattr(dv, "name", device_name)),
                        }
                    return {"ok": True, "track_index": ti, "device_index": None}
                except Exception as e:
                    return {"ok": False, "error": str(e)}
                finally:
                    try:
                        if hasattr(song, "end_undo_step"):
                            song.end_undo_step()
                    except Exception:
                        pass

            res = _run_on_main(_do_load)
            return res or {"ok": False, "error": "load_failed"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

    # Stub: append a fake device to track in _STATE
    tracks = _STATE.setdefault("tracks", [])
    for t in tracks:
        if t.get("index") == int(track_index):
            devs = t.setdefault("devices", [])
            new_index = len(devs)
            devs.append({"index": new_index, "name": str(device_name)})
            _emit({"event": "track_device_loaded", "track": int(track_index), "device_index": new_index, "name": str(device_name)})
            return {"ok": True, "track_index": int(track_index), "device_index": new_index, "device_name": str(device_name)}
    return {"ok": False, "error": "track_not_found_stub"}


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

                def _do_reorder_device():
                    ok_inner = False
                    errors = []
                    try:
                        if hasattr(song, 'begin_undo_step'):
                            song.begin_undo_step()

                        devs = list(getattr(tr, 'devices', []) or [])
                        if not (0 <= oi < len(devs)):
                            return False
                        # Clamp target index into valid range
                        target_idx = ni
                        if target_idx < 0:
                            target_idx = 0
                        if target_idx >= len(devs):
                            target_idx = len(devs) - 1
                        dev = devs[oi]

                        owners = [tr]
                        try:
                            dv_obj = getattr(tr, 'devices', None)
                            if dv_obj is not None and dv_obj is not tr:
                                owners.append(dv_obj)
                        except Exception as e:
                            errors.append(f"devices_owner_probe_failed:{type(e).__name__}")

                        for owner in owners:
                            # Preferred: reorder_device(device, index)
                            try:
                                if hasattr(owner, 'reorder_device'):
                                    owner.reorder_device(dev, target_idx)
                                    ok_inner = True
                                    break
                            except Exception as e:
                                errors.append(f"reorder_device_failed:{type(e).__name__}")
                            # Some Live builds may expose reorder_devices
                            try:
                                if hasattr(owner, 'reorder_devices'):
                                    owner.reorder_devices(dev, target_idx)
                                    ok_inner = True
                                    break
                            except Exception as e:
                                errors.append(f"reorder_devices_failed:{type(e).__name__}")
                            # Fallback: move_device-style API
                            try:
                                if hasattr(owner, 'move_device'):
                                    owner.move_device(dev, target_idx)
                                    ok_inner = True
                                    break
                            except Exception as e:
                                errors.append(f"move_device_failed:{type(e).__name__}")

                        if ok_inner:
                            _emit({"event": "track_device_reordered", "track": ti, "from": oi, "to": target_idx})
                            return {"ok": True, "from": oi, "to": target_idx}
                        return {"ok": False, "error": ";".join(errors) or "reorder_failed", "from": oi, "to": target_idx}
                    finally:
                        try:
                            if hasattr(song, 'end_undo_step'):
                                song.end_undo_step()
                        except Exception:
                            pass

                res = _run_on_main(_do_reorder_device)
                if isinstance(res, dict):
                    return res
                if bool(res):
                    return {"ok": True, "from": oi, "to": ni}
                return {"ok": False, "error": "reorder_failed_no_detail", "from": oi, "to": ni}
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

            def _do_create_clip():
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

            return _run_on_main(_do_create_clip) or {"ok": False}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    # Stub
    key = (int(track_index), int(scene_index))
    _STATE.setdefault("clips", {})[key] = _STATE.get("clips", {}).get(key) or f"Clip {track_index}:{scene_index}"
    _emit({"event": "clip_created", "track": int(track_index), "scene": int(scene_index), "length": float(length_beats)})
    return {"ok": True}


def delete_clip(live, track_index: int, scene_index: int) -> Dict[str, Any]:
    """Delete a clip in the given clip slot (Session view)."""
    try:
        ti = int(track_index)
        si = int(scene_index)
        if live is not None:
            tracks = getattr(live, "tracks", []) or []
            if not (1 <= ti <= len(tracks)):
                return {"ok": False, "error": "track_out_of_range"}
            tr = tracks[ti - 1]
            slots = getattr(tr, "clip_slots", []) or []
            if not (1 <= si <= len(slots)):
                return {"ok": False, "error": "scene_out_of_range"}
            slot = slots[si - 1]
            if not getattr(slot, "has_clip", False):
                return {"ok": False, "error": "slot_empty"}
            song = live

            def _do_delete_clip():
                try:
                    if hasattr(song, "begin_undo_step"):
                        song.begin_undo_step()
                    if hasattr(slot, "delete_clip"):
                        slot.delete_clip()
                    else:
                        # Fallback: stop and clear clip if possible
                        try:
                            slot.stop()
                        except Exception:
                            pass
                    _emit({"event": "clip_deleted", "track": ti, "scene": si})
                    return {"ok": True}
                finally:
                    try:
                        if hasattr(song, "end_undo_step"):
                            song.end_undo_step()
                    except Exception:
                        pass

            return _run_on_main(_do_delete_clip) or {"ok": False}
    except Exception as e:
        return {"ok": False, "error": str(e)}

    # Stub
    key = (int(track_index), int(scene_index))
    try:
        if key in _STATE.get("clips", {}):
            try:
                del _STATE.setdefault("clips", {})[key]
            except Exception:
                pass
        _emit({"event": "clip_deleted", "track": int(track_index), "scene": int(scene_index)})
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def duplicate_clip(
    live,
    track_index: int,
    scene_index: int,
    target_track_index: int | None = None,
    target_scene_index: int | None = None,
) -> Dict[str, Any]:
    """Duplicate a clip from [track, scene] to [target_track, target_scene].

    Defaults to same track and next scene (scene_index + 1) when targets are omitted.
    """
    try:
        ti = int(track_index)
        si = int(scene_index)
        tti = int(target_track_index) if target_track_index is not None else ti
        tsi = int(target_scene_index) if target_scene_index is not None else (si + 1)
        if live is not None:
            tracks = getattr(live, "tracks", []) or []
            if not (1 <= ti <= len(tracks) and 1 <= tti <= len(tracks)):
                return {"ok": False, "error": "track_out_of_range"}
            src_tr = tracks[ti - 1]
            dst_tr = tracks[tti - 1]
            src_slots = getattr(src_tr, "clip_slots", []) or []
            dst_slots = getattr(dst_tr, "clip_slots", []) or []
            if not (1 <= si <= len(src_slots) and 1 <= tsi <= len(dst_slots)):
                return {"ok": False, "error": "scene_out_of_range"}
            src_slot = src_slots[si - 1]
            dst_slot = dst_slots[tsi - 1]
            if not getattr(src_slot, "has_clip", False):
                return {"ok": False, "error": "source_slot_empty"}
            if getattr(dst_slot, "has_clip", False):
                return {"ok": False, "error": "target_slot_not_empty"}
            song = live

            def _do_duplicate_clip():
                try:
                    if hasattr(song, "begin_undo_step"):
                        song.begin_undo_step()
                    if hasattr(src_slot, "duplicate_clip_to"):
                        src_slot.duplicate_clip_to(dst_slot)
                    else:
                        # Fallback: use copy/paste semantics if ever needed (not implemented)
                        pass
                    _emit(
                        {
                            "event": "clip_duplicated",
                            "track": ti,
                            "scene": si,
                            "target_track": tti,
                            "target_scene": tsi,
                        }
                    )
                    return {"ok": True}
                finally:
                    try:
                        if hasattr(song, "end_undo_step"):
                            song.end_undo_step()
                    except Exception:
                        pass

            return _run_on_main(_do_duplicate_clip) or {"ok": False}
    except Exception as e:
        return {"ok": False, "error": str(e)}

    # Stub
    key_src = (int(track_index), int(scene_index))
    key_dst = (int(target_track_index or track_index), int(target_scene_index or (int(scene_index) + 1)))
    clips = _STATE.setdefault("clips", {})
    try:
        if key_src not in clips:
            return {"ok": False, "error": "source_slot_empty"}
        if key_dst in clips:
            return {"ok": False, "error": "target_slot_not_empty"}
        clips[key_dst] = clips[key_src]
        _emit(
            {
                "event": "clip_duplicated",
                "track": int(track_index),
                "scene": int(scene_index),
                "target_track": key_dst[0],
                "target_scene": key_dst[1],
            }
        )
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}


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


def fire_clip(live, track_index: int, scene_index: int, select: bool = True) -> Dict[str, Any]:
    """Launch a clip in a given clip slot [track, scene] (1-based track, 1-based scene).

    Optionally select the slot first.
    """
    try:
        ti = int(track_index)
        si = int(scene_index)
        if live is not None:
            tracks = getattr(live, "tracks", []) or []
            if not (1 <= ti <= len(tracks)):
                return {"ok": False, "error": "track_out_of_range"}
            tr = tracks[ti - 1]
            slots = getattr(tr, "clip_slots", []) or []
            if not (1 <= si <= len(slots)):
                return {"ok": False, "error": "scene_out_of_range"}
            slot = slots[si - 1]
            try:
                if select and hasattr(getattr(live, "view", None), "selected_scene"):
                    # Best-effort: select scene and track so UI follows
                    try:
                        live.view.selected_scene = getattr(live, "scenes", [None])[si - 1]
                    except Exception:
                        pass
                    try:
                        live.view.selected_track = tr
                    except Exception:
                        pass
            except Exception:
                pass
            try:
                slot.fire()
            except Exception as e:
                return {"ok": False, "error": str(e)}
            _emit({"event": "clip_fired", "track": ti, "scene": si})
            return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    # Stub: mark clip as "playing" in state
    key = (int(track_index), int(scene_index))
    _STATE.setdefault("clips", {})[key] = _STATE.get("clips", {}).get(key) or f"Clip {track_index}:{scene_index}"
    _emit({"event": "clip_fired", "track": int(track_index), "scene": int(scene_index)})
    return {"ok": True}


def stop_clip(live, track_index: int, scene_index: int) -> Dict[str, Any]:
    """Stop a single clip by stopping its clip slot at [track, scene]."""
    try:
        ti = int(track_index)
        si = int(scene_index)
        if live is not None:
            tracks = getattr(live, "tracks", []) or []
            if not (1 <= ti <= len(tracks)):
                return {"ok": False, "error": "track_out_of_range"}
            tr = tracks[ti - 1]
            slots = getattr(tr, "clip_slots", []) or []
            if not (1 <= si <= len(slots)):
                return {"ok": False, "error": "scene_out_of_range"}
            try:
                slots[si - 1].stop()
            except Exception:
                pass
            _emit({"event": "clip_stopped", "track": ti, "scene": si})
            return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    # Stub
    _emit({"event": "clip_stopped", "track": int(track_index), "scene": int(scene_index)})
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
                    def _do_delete_return_device():
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

                    ok = _run_on_main(_do_delete_return_device)
                    if bool(ok):
                        return True
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

                def _do_reorder_return_device():
                    ok_inner = False
                    errors = []
                    try:
                        if hasattr(song, 'begin_undo_step'):
                            song.begin_undo_step()

                        devs = list(getattr(rt, 'devices', []) or [])
                        if not (0 <= oi < len(devs)):
                            return {"ok": False, "error": f"old_index_out_of_range:{oi}", "device_count": len(devs)}
                        target_idx = ni
                        if target_idx < 0:
                            target_idx = 0
                        if target_idx >= len(devs):
                            target_idx = len(devs) - 1
                        dev = devs[oi]

                        owners = [rt]
                        try:
                            dv_obj = getattr(rt, 'devices', None)
                            if dv_obj is not None and dv_obj is not rt:
                                owners.append(dv_obj)
                        except Exception as e:
                            errors.append(f"devices_owner_probe_failed:{type(e).__name__}")

                        for owner in owners:
                            try:
                                if hasattr(owner, 'reorder_device'):
                                    owner.reorder_device(dev, target_idx)
                                    ok_inner = True
                                    break
                            except Exception as e:
                                errors.append(f"reorder_device_failed:{type(e).__name__}")
                            try:
                                if hasattr(owner, 'reorder_devices'):
                                    owner.reorder_devices(dev, target_idx)
                                    ok_inner = True
                                    break
                            except Exception as e:
                                errors.append(f"reorder_devices_failed:{type(e).__name__}")
                            try:
                                if hasattr(owner, 'move_device'):
                                    owner.move_device(dev, target_idx)
                                    ok_inner = True
                                    break
                            except Exception as e:
                                errors.append(f"move_device_failed:{type(e).__name__}")

                        if ok_inner:
                            _emit({"event": "return_device_reordered", "return": ri, "from": oi, "to": target_idx})
                            return {"ok": True, "from": oi, "to": target_idx}
                        return {"ok": False, "error": ";".join(errors) or "reorder_failed", "from": oi, "to": target_idx}
                    finally:
                        try:
                            if hasattr(song, 'end_undo_step'):
                                song.end_undo_step()
                        except Exception:
                            pass

                res = _run_on_main(_do_reorder_return_device)
                if isinstance(res, dict):
                    return res
                if bool(res):
                    return {"ok": True, "from": oi, "to": ni}
                return {"ok": False, "error": "reorder_failed_no_detail", "from": oi, "to": ni}
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


def get_full_snapshot(live, skip_param_values: bool = False) -> dict:
    """Get complete Live set snapshot in a single call.

    Returns all tracks, returns, master with devices and optionally parameters.
    This is WAY faster than making dozens of separate UDP calls.

    Args:
        live: Live song object
        skip_param_values: If True, skip parameter values (structure only, faster)

    Returns:
        {
            "tracks": [{index, name, type, mixer: {volume, pan, mute, solo}, devices: [...]}],
            "returns": [{index, name, mixer: {volume, pan, mute, solo}, devices: [...]}],
            "master": {mixer: {volume, pan}, devices: [...]},
            "transport": {tempo, metronome, is_playing, is_recording}
        }
    """
    result = {
        "tracks": [],
        "returns": [],
        "master": {},
        "transport": {}
    }

    try:
        if live is None:
            # Stub mode
            result["tracks"] = _STATE.get("tracks", [])
            result["returns"] = _STATE.get("returns", [])
            result["transport"] = _STATE.get("transport", {})
            return result

        # Transport
        try:
            result["transport"] = {
                "tempo": float(getattr(live, "tempo", 120.0)),
                "metronome": bool(getattr(live, "metronome", False)),
                "is_playing": bool(getattr(live, "is_playing", False)),
                "is_recording": bool(getattr(live, "is_recording", False)),
            }
        except Exception:
            result["transport"] = {}

        # Tracks
        try:
            for idx, tr in enumerate(getattr(live, "tracks", []), start=1):
                track_data = {"index": idx, "name": str(getattr(tr, "name", f"Track {idx}"))}

                # Type detection
                try:
                    has_midi = bool(getattr(tr, "has_midi_input", False))
                    has_audio = bool(getattr(tr, "has_audio_input", False))
                    track_data["type"] = "midi" if has_midi and not has_audio else "audio"
                except Exception:
                    track_data["type"] = "audio"

                # Mixer
                try:
                    mixer_device = getattr(tr, "mixer_device", None)
                    if mixer_device:
                        track_data["mixer"] = {
                            "volume": float(getattr(getattr(mixer_device, "volume", None), "value", 0.85)),
                            "pan": float(getattr(getattr(mixer_device, "panning", None), "value", 0.0)),
                        }
                        track_data["mute"] = bool(getattr(tr, "mute", False))
                        track_data["solo"] = bool(getattr(tr, "solo", False))

                        # Sends
                        sends = getattr(mixer_device, "sends", []) or []
                        track_data["sends"] = []
                        for si, s in enumerate(sends):
                            try:
                                track_data["sends"].append({
                                    "index": si,
                                    "value": float(getattr(s, "value", 0.0))
                                })
                            except Exception:
                                pass
                except Exception:
                    track_data["mixer"] = {}

                # Devices
                devices = []
                for di, dv in enumerate(getattr(tr, "devices", []) or []):
                    dev_data = {
                        "index": di,
                        "name": str(getattr(dv, "name", f"Device {di}"))
                    }

                    # Parameters (optional)
                    if not skip_param_values:
                        params = []
                        for pi, p in enumerate(getattr(dv, "parameters", []) or []):
                            try:
                                params.append({
                                    "index": pi,
                                    "name": str(getattr(p, "name", f"Param {pi}")),
                                    "value": float(getattr(p, "value", 0.0)),
                                    "display_value": str(getattr(p, "display_value", "")),
                                })
                            except Exception:
                                pass
                        dev_data["params"] = params

                    devices.append(dev_data)

                track_data["devices"] = devices
                result["tracks"].append(track_data)
        except Exception:
            pass

        # Returns
        try:
            for ri, ret in enumerate(getattr(live, "return_tracks", []) or []):
                return_data = {
                    "index": ri,
                    "name": str(getattr(ret, "name", f"Return {chr(ord('A') + ri)}"))
                }

                # Mixer
                try:
                    mixer_device = getattr(ret, "mixer_device", None)
                    if mixer_device:
                        return_data["mixer"] = {
                            "volume": float(getattr(getattr(mixer_device, "volume", None), "value", 0.85)),
                            "pan": float(getattr(getattr(mixer_device, "panning", None), "value", 0.0)),
                        }
                        return_data["mute"] = bool(getattr(ret, "mute", False))
                        return_data["solo"] = bool(getattr(ret, "solo", False))
                except Exception:
                    return_data["mixer"] = {}

                # Devices
                devices = []
                for di, dv in enumerate(getattr(ret, "devices", []) or []):
                    dev_data = {
                        "index": di,
                        "name": str(getattr(dv, "name", f"Device {di}"))
                    }

                    # Parameters (optional)
                    if not skip_param_values:
                        params = []
                        for pi, p in enumerate(getattr(dv, "parameters", []) or []):
                            try:
                                params.append({
                                    "index": pi,
                                    "name": str(getattr(p, "name", f"Param {pi}")),
                                    "value": float(getattr(p, "value", 0.0)),
                                    "display_value": str(getattr(p, "display_value", "")),
                                })
                            except Exception:
                                pass
                        dev_data["params"] = params

                    devices.append(dev_data)

                return_data["devices"] = devices
                result["returns"].append(return_data)
        except Exception:
            pass

        # Master
        try:
            master = getattr(live, "master_track", None)
            if master:
                master_data = {}

                # Mixer
                try:
                    mixer_device = getattr(master, "mixer_device", None)
                    if mixer_device:
                        master_data["mixer"] = {
                            "volume": float(getattr(getattr(mixer_device, "volume", None), "value", 0.85)),
                            "pan": float(getattr(getattr(mixer_device, "panning", None), "value", 0.0)),
                        }
                except Exception:
                    master_data["mixer"] = {}

                # Devices
                devices = []
                for di, dv in enumerate(getattr(master, "devices", []) or []):
                    dev_data = {
                        "index": di,
                        "name": str(getattr(dv, "name", f"Device {di}"))
                    }

                    # Parameters (optional)
                    if not skip_param_values:
                        params = []
                        for pi, p in enumerate(getattr(dv, "parameters", []) or []):
                            try:
                                params.append({
                                    "index": pi,
                                    "name": str(getattr(p, "name", f"Param {pi}")),
                                    "value": float(getattr(p, "value", 0.0)),
                                    "display_value": str(getattr(p, "display_value", "")),
                                })
                            except Exception:
                                pass
                        dev_data["params"] = params

                    devices.append(dev_data)

                master_data["devices"] = devices
                result["master"] = master_data
        except Exception:
            pass

    except Exception:
        pass

    return result
