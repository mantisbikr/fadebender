"""
UDP bridge for the Fadebender Remote Script (scaffold).

Safe by default: only starts when FADEBENDER_UDP_ENABLE=1 is present in
Live's environment. Delegates operations to lom_ops where the actual
Live Object Model access belongs.
"""
from __future__ import annotations

import json
import os
import socket
from . import lom_ops
from typing import Callable, Optional, Any, Dict


HOST = os.getenv("ABLETON_UDP_HOST", "127.0.0.1")
PORT = int(os.getenv("ABLETON_UDP_PORT", "19845"))
CLIENT_HOST = os.getenv("ABLETON_UDP_CLIENT_HOST", HOST)
CLIENT_PORT = int(os.getenv("ABLETON_UDP_CLIENT_PORT", os.getenv("ABLETON_EVENT_PORT", "19846")))

_LIVE_ACCESSOR: Optional[Callable[[], Any]] = None


def set_live_accessor(getter: Callable[[], Any]):  # pragma: no cover
    global _LIVE_ACCESSOR
    _LIVE_ACCESSOR = getter


def start_udp_server():  # pragma: no cover
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((HOST, PORT))
    event_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def notify(payload: Dict[str, Any]):  # pragma: no cover
        try:
            event_sock.sendto(json.dumps(payload).encode("utf-8"), (CLIENT_HOST, CLIENT_PORT))
        except Exception:
            pass

    lom_ops.set_notifier(notify)
    try:
        if _LIVE_ACCESSOR:
            lom_ops.init_listeners(_LIVE_ACCESSOR())
    except Exception:
        pass
    while True:
        data, addr = sock.recvfrom(64 * 1024)
        try:
            msg = json.loads(data.decode("utf-8"))
        except Exception:
            continue
        op = (msg.get("op") or "").strip()
        try:
            if op == "ping":
                resp = {"ok": True, "op": "ping"}
            elif op == "get_overview":
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                data_out = lom_ops.get_overview(live_ctx)
                resp = {"ok": True, "op": op, "data": data_out}
            elif op == "get_scenes":
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                data_out = lom_ops.get_scenes(live_ctx)
                resp = {"ok": True, "op": op, "data": data_out}
            elif op == "get_track_status":
                ti = int(msg.get("track_index", 0))
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                data_out = lom_ops.get_track_status(live_ctx, ti)
                resp = {"ok": True, "op": op, "data": data_out}
            elif op == "set_mixer":
                track_index = int(msg.get("track_index", 0))
                field = str(msg.get("field"))
                value = float(msg.get("value", 0.0))
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                ok = lom_ops.set_mixer(live_ctx, track_index, field, value)
                resp = {"ok": bool(ok), "op": op}
            elif op == "set_send":
                track_index = int(msg.get("track_index", 0))
                send_index = int(msg.get("send_index", 0))
                value = float(msg.get("value", 0.0))
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                ok = lom_ops.set_send(live_ctx, track_index, send_index, value)
                resp = {"ok": bool(ok), "op": op}
            elif op == "set_device_param":
                track_index = int(msg.get("track_index", 0))
                device_index = int(msg.get("device_index", 0))
                param_index = int(msg.get("param_index", 0))
                value = float(msg.get("value", 0.0))
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                ok = lom_ops.set_device_param(live_ctx, track_index, device_index, param_index, value)
                resp = {"ok": bool(ok), "op": op}
            elif op == "get_track_sends":
                track_index = int(msg.get("track_index", 0))
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                data_out = lom_ops.get_track_sends(live_ctx, track_index)
                resp = {"ok": True, "op": op, "data": data_out}
            elif op == "create_audio_track":
                index = msg.get("index")
                index_int = int(index) if index is not None else None
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                data_out = lom_ops.create_audio_track(live_ctx, index_int)
                resp = {"op": op, **(data_out or {"ok": False})}
            elif op == "create_midi_track":
                index = msg.get("index")
                index_int = int(index) if index is not None else None
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                data_out = lom_ops.create_midi_track(live_ctx, index_int)
                resp = {"op": op, **(data_out or {"ok": False})}
            elif op == "create_return_track":
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                data_out = lom_ops.create_return_track(live_ctx)
                resp = {"op": op, **(data_out or {"ok": False})}
            elif op == "delete_track":
                track_index = int(msg.get("track_index", 0))
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                data_out = lom_ops.delete_track(live_ctx, track_index)
                resp = {"op": op, **(data_out or {"ok": False})}
            elif op == "duplicate_track":
                track_index = int(msg.get("track_index", 0))
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                data_out = lom_ops.duplicate_track(live_ctx, track_index)
                resp = {"op": op, **(data_out or {"ok": False})}
            elif op == "get_track_routing":
                track_index = int(msg.get("track_index", 0))
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                data_out = lom_ops.get_track_routing(live_ctx, track_index)
                resp = {"ok": True, "op": op, "data": data_out}
            elif op == "set_track_routing":
                track_index = int(msg.get("track_index", 0))
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                # Pass through provided keys
                ok = lom_ops.set_track_routing(
                    live_ctx,
                    track_index,
                    monitor_state=msg.get("monitor_state"),
                    audio_from_type=msg.get("audio_from_type"),
                    audio_from_channel=msg.get("audio_from_channel"),
                    audio_to_type=msg.get("audio_to_type"),
                    audio_to_channel=msg.get("audio_to_channel"),
                    midi_from_type=msg.get("midi_from_type"),
                    midi_from_channel=msg.get("midi_from_channel"),
                    midi_to_type=msg.get("midi_to_type"),
                    midi_to_channel=msg.get("midi_to_channel"),
                )
                resp = {"ok": bool(ok), "op": op}
            elif op == "set_track_arm":
                track_index = int(msg.get("track_index", 0))
                arm = bool(msg.get("arm", True))
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                ok = lom_ops.set_track_arm(live_ctx, track_index, arm)
                resp = {"ok": bool(ok), "op": op}
            elif op == "get_return_tracks":
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                data_out = lom_ops.get_return_tracks(live_ctx)
                resp = {"ok": True, "op": op, "data": data_out}
            elif op == "get_return_sends":
                return_index = int(msg.get("return_index", 0))
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                data_out = lom_ops.get_return_sends(live_ctx, return_index)
                resp = {"ok": True, "op": op, "data": data_out}
            elif op == "set_return_send":
                return_index = int(msg.get("return_index", 0))
                send_index = int(msg.get("send_index", 0))
                value = float(msg.get("value", 0.0))
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                ok = lom_ops.set_return_send(live_ctx, return_index, send_index, value)
                resp = {"ok": bool(ok), "op": op}
            elif op == "set_return_mixer":
                return_index = int(msg.get("return_index", 0))
                field = str(msg.get("field"))
                value = float(msg.get("value", 0.0))
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                ok = lom_ops.set_return_mixer(live_ctx, return_index, field, value)
                resp = {"ok": bool(ok), "op": op}
            elif op == "get_return_devices":
                return_index = int(msg.get("return_index", 0))
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                data_out = lom_ops.get_return_devices(live_ctx, return_index)
                resp = {"ok": True, "op": op, "data": data_out}
            elif op == "delete_return_device":
                return_index = int(msg.get("return_index", 0))
                device_index = int(msg.get("device_index", 0))
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                ok = lom_ops.delete_return_device(live_ctx, return_index, device_index)
                resp = {"ok": bool(ok), "op": op}
            elif op == "load_return_device":
                return_index = int(msg.get("return_index", 0))
                device_name = str(msg.get("device_name", "")).strip()
                preset_name = msg.get("preset_name")
                preset = str(preset_name).strip() if isinstance(preset_name, str) and preset_name.strip() else None
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                data_out = lom_ops.load_device_on_return(live_ctx, return_index, device_name, preset)
                resp = {"op": op, **(data_out or {"ok": False})}
            elif op == "reorder_return_device":
                return_index = int(msg.get("return_index", 0))
                old_index = int(msg.get("old_index", 0))
                new_index = int(msg.get("new_index", 0))
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                result = lom_ops.reorder_return_device(live_ctx, return_index, old_index, new_index)
                if isinstance(result, dict):
                    resp = {"op": op, **result}
                else:
                    resp = {"ok": bool(result), "op": op}
            elif op == "get_return_device_params":
                return_index = int(msg.get("return_index", 0))
                device_index = int(msg.get("device_index", 0))
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                data_out = lom_ops.get_return_device_params(live_ctx, return_index, device_index)
                resp = {"ok": True, "op": op, "data": data_out}
            elif op == "set_return_device_param":
                return_index = int(msg.get("return_index", 0))
                device_index = int(msg.get("device_index", 0))
                param_index = int(msg.get("param_index", 0))
                value = float(msg.get("value", 0.0))
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                ok = lom_ops.set_return_device_param(live_ctx, return_index, device_index, param_index, value)
                resp = {"ok": bool(ok), "op": op}
            elif op == "get_track_devices":
                track_index = int(msg.get("track_index", 0))
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                data_out = lom_ops.get_track_devices(live_ctx, track_index)
                resp = {"ok": True, "op": op, "data": data_out}
            elif op == "delete_track_device":
                track_index = int(msg.get("track_index", 0))
                device_index = int(msg.get("device_index", 0))
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                ok = lom_ops.delete_track_device(live_ctx, track_index, device_index)
                resp = {"ok": bool(ok), "op": op}
            elif op == "load_track_device":
                track_index = int(msg.get("track_index", 0))
                device_name = str(msg.get("device_name", "")).strip()
                preset_name = msg.get("preset_name")
                preset = str(preset_name).strip() if isinstance(preset_name, str) and preset_name.strip() else None
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                data_out = lom_ops.load_device_on_track(live_ctx, track_index, device_name, preset)
                resp = {"op": op, **(data_out or {"ok": False})}
            elif op == "reorder_track_device":
                track_index = int(msg.get("track_index", 0))
                old_index = int(msg.get("old_index", 0))
                new_index = int(msg.get("new_index", 0))
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                result = lom_ops.reorder_track_device(live_ctx, track_index, old_index, new_index)
                if isinstance(result, dict):
                    resp = {"op": op, **result}
                else:
                    resp = {"ok": bool(result), "op": op}
            elif op == "get_track_device_params":
                track_index = int(msg.get("track_index", 0))
                device_index = int(msg.get("device_index", 0))
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                data_out = lom_ops.get_track_device_params(live_ctx, track_index, device_index)
                resp = {"ok": True, "op": op, "data": data_out}
            elif op == "set_track_device_param":
                track_index = int(msg.get("track_index", 0))
                device_index = int(msg.get("device_index", 0))
                param_index = int(msg.get("param_index", 0))
                value = float(msg.get("value", 0.0))
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                ok = lom_ops.set_device_param(live_ctx, track_index, device_index, param_index, value)
                resp = {"ok": bool(ok), "op": op}
            elif op == "create_clip":
                track_index = int(msg.get("track_index", 0))
                scene_index = int(msg.get("scene_index", 0))
                length = float(msg.get("length_beats", 1.0))
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                data_out = lom_ops.create_clip(live_ctx, track_index, scene_index, length)
                resp = {"op": op, **(data_out or {"ok": False})}
            elif op == "delete_clip":
                track_index = int(msg.get("track_index", 0))
                scene_index = int(msg.get("scene_index", 0))
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                data_out = lom_ops.delete_clip(live_ctx, track_index, scene_index)
                resp = {"op": op, **(data_out or {"ok": False})}
            elif op == "duplicate_clip":
                track_index = int(msg.get("track_index", 0))
                scene_index = int(msg.get("scene_index", 0))
                target_track_index = msg.get("target_track_index")
                target_scene_index = msg.get("target_scene_index")
                tti = int(target_track_index) if target_track_index is not None else None
                tsi = int(target_scene_index) if target_scene_index is not None else None
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                data_out = lom_ops.duplicate_clip(live_ctx, track_index, scene_index, tti, tsi)
                resp = {"op": op, **(data_out or {"ok": False})}
            elif op == "create_scene":
                index = msg.get("index")
                index_int = int(index) if index is not None else None
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                data_out = lom_ops.create_scene(live_ctx, index_int)
                resp = {"op": op, **(data_out or {"ok": False})}
            elif op == "delete_scene":
                scene_index = int(msg.get("scene_index", 0))
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                data_out = lom_ops.delete_scene(live_ctx, scene_index)
                resp = {"op": op, **(data_out or {"ok": False})}
            elif op == "duplicate_scene":
                scene_index = int(msg.get("scene_index", 0))
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                data_out = lom_ops.duplicate_scene(live_ctx, scene_index)
                resp = {"op": op, **(data_out or {"ok": False})}
            elif op == "fire_clip":
                track_index = int(msg.get("track_index", 0))
                scene_index = int(msg.get("scene_index", 0))
                select = bool(msg.get("select", True))
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                data_out = lom_ops.fire_clip(live_ctx, track_index, scene_index, select)
                resp = {"op": op, **(data_out or {"ok": False})}
            elif op == "stop_clip":
                track_index = int(msg.get("track_index", 0))
                scene_index = int(msg.get("scene_index", 0))
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                data_out = lom_ops.stop_clip(live_ctx, track_index, scene_index)
                resp = {"op": op, **(data_out or {"ok": False})}
            elif op == "get_master_devices":
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                data_out = lom_ops.get_master_devices(live_ctx)
                resp = {"ok": True, "op": op, "data": data_out}
            elif op == "get_master_device_params":
                device_index = int(msg.get("device_index", 0))
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                data_out = lom_ops.get_master_device_params(live_ctx, device_index)
                resp = {"ok": True, "op": op, "data": data_out}
            elif op == "set_master_device_param":
                device_index = int(msg.get("device_index", 0))
                param_index = int(msg.get("param_index", 0))
                value = float(msg.get("value", 0.0))
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                ok = lom_ops.set_master_device_param(live_ctx, device_index, param_index, value)
                resp = {"ok": bool(ok), "op": op}
            elif op == "capture_and_insert_scene":
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                data_out = lom_ops.capture_and_insert_scene(live_ctx)
                resp = {"op": op, **(data_out or {"ok": False})}
            elif op == "fire_scene":
                scene_index = int(msg.get("scene_index", 0))
                select = bool(msg.get("select", True))
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                data_out = lom_ops.fire_scene(live_ctx, scene_index, select)
                resp = {"op": op, **(data_out or {"ok": False})}
            elif op == "stop_scene":
                scene_index = int(msg.get("scene_index", 0))
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                data_out = lom_ops.stop_scene(live_ctx, scene_index)
                resp = {"op": op, **(data_out or {"ok": False})}
            elif op == "get_return_routing":
                return_index = int(msg.get("return_index", 0))
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                data_out = lom_ops.get_return_routing(live_ctx, return_index)
                resp = {"ok": True, "op": op, "data": data_out}
            elif op == "set_return_routing":
                return_index = int(msg.get("return_index", 0))
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                ok = lom_ops.set_return_routing(
                    live_ctx,
                    return_index,
                    audio_to_type=msg.get("audio_to_type"),
                    audio_to_channel=msg.get("audio_to_channel"),
                    sends_mode=msg.get("sends_mode"),
                )
                resp = {"ok": bool(ok), "op": op}
            elif op == "set_volume_db":
                track_index = int(msg.get("track_index", 0))
                db = float(msg.get("db", 0.0))
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                result = lom_ops.set_volume_db(live_ctx, track_index, db)
                if isinstance(result, dict):
                    resp = {"ok": bool(result.get("ok", False)), "op": op, **result}
                else:
                    resp = {"ok": bool(result), "op": op}
            elif op == "select_track":
                track_index = int(msg.get("track_index", 0))
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                ok = lom_ops.select_track(live_ctx, track_index)
                resp = {"ok": bool(ok), "op": op}
            elif op == "get_transport":
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                data_out = lom_ops.get_transport(live_ctx)
                resp = {"ok": True, "op": op, "data": data_out}
            elif op == "get_song_info":
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                data_out = lom_ops.get_song_info(live_ctx)
                resp = {"ok": True, "op": op, "data": data_out}
            elif op == "set_transport":
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                action = str(msg.get("action", ""))
                val = msg.get("value")
                data_out = lom_ops.set_transport(live_ctx, action, val)
                resp = {"ok": bool(data_out.get("ok", True)), "op": op, "data": data_out.get("state", {})}
            elif op == "get_undo_status":
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                data_out = lom_ops.get_undo_status(live_ctx)
                resp = {"ok": True, "op": op, "data": data_out}
            elif op == "song_undo":
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                data_out = lom_ops.song_undo(live_ctx)
                resp = {"op": op, **(data_out or {"ok": False})}
            elif op == "song_redo":
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                data_out = lom_ops.song_redo(live_ctx)
                resp = {"op": op, **(data_out or {"ok": False})}
            elif op == "get_master_status":
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                data_out = lom_ops.get_master_status(live_ctx)
                resp = {"ok": True, "op": op, "data": data_out}
            elif op == "set_master_mixer":
                field = str(msg.get("field"))
                value = float(msg.get("value", 0.0))
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                ok = lom_ops.set_master_mixer(live_ctx, field, value)
                resp = {"ok": bool(ok), "op": op}
            elif op == "set_view":
                mode = str(msg.get("mode", "")).strip()
                data_out = lom_ops.set_view_mode(_LIVE_ACCESSOR() if _LIVE_ACCESSOR else None, mode)
                resp = {"op": op, **(data_out or {"ok": False})}
            elif op == "set_track_name":
                track_index = int(msg.get("track_index", 0))
                name = str(msg.get("name", "")).strip()
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                ok = lom_ops.set_track_name(live_ctx, track_index, name)
                resp = {"ok": bool(ok), "op": op}
            elif op == "set_scene_name":
                scene_index = int(msg.get("scene_index", 0))
                name = str(msg.get("name", "")).strip()
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                ok = lom_ops.set_scene_name(live_ctx, scene_index, name)
                resp = {"ok": bool(ok), "op": op}
            elif op == "set_clip_name":
                track_index = int(msg.get("track_index", 0))
                scene_index = int(msg.get("scene_index", 0))
                name = str(msg.get("name", "")).strip()
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                ok = lom_ops.set_clip_name(live_ctx, track_index, scene_index, name)
                resp = {"ok": bool(ok), "op": op}
            elif op == "set_track_device_name":
                track_index = int(msg.get("track_index", 0))
                device_index = int(msg.get("device_index", 0))
                name = str(msg.get("name", "")).strip()
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                ok = lom_ops.set_track_device_name(live_ctx, track_index, device_index, name)
                resp = {"ok": bool(ok), "op": op}
            elif op == "set_return_device_name":
                return_index = int(msg.get("return_index", 0))
                device_index = int(msg.get("device_index", 0))
                name = str(msg.get("name", "")).strip()
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                ok = lom_ops.set_return_device_name(live_ctx, return_index, device_index, name)
                resp = {"ok": bool(ok), "op": op}
            elif op == "get_full_snapshot":
                skip_param_values = bool(msg.get("skip_param_values", False))
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                data_out = lom_ops.get_full_snapshot(live_ctx, skip_param_values=skip_param_values)
                resp = {"ok": True, "op": op, "data": data_out}
            elif op == "get_cue_points":
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                data_out = lom_ops.get_cue_points(live_ctx)
                resp = {"ok": True, "op": op, "data": data_out}
            elif op == "add_cue_point":
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                time_beats = msg.get("time_beats")
                name = msg.get("name")
                data_out = lom_ops.add_cue_point(live_ctx, time_beats, name)
                resp = {"op": op, **(data_out or {"ok": False})}
            elif op == "set_cue_name":
                cue_index = int(msg.get("cue_index", 0))
                name = str(msg.get("name", "")).strip()
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                data_out = lom_ops.set_cue_name(live_ctx, cue_index, name)
                resp = {"op": op, **(data_out or {"ok": False})}
            elif op == "set_cue_time":
                cue_index = int(msg.get("cue_index", 0))
                time_beats = float(msg.get("time_beats", 0.0))
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                data_out = lom_ops.set_cue_time(live_ctx, cue_index, time_beats)
                resp = {"op": op, **(data_out or {"ok": False})}
            elif op == "delete_cue_point":
                cue_index = int(msg.get("cue_index", 0))
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                data_out = lom_ops.delete_cue_point(live_ctx, cue_index)
                resp = {"op": op, **(data_out or {"ok": False})}
            elif op == "jump_to_cue":
                live_ctx = _LIVE_ACCESSOR() if _LIVE_ACCESSOR else None
                cue_index = msg.get("cue_index")
                name = msg.get("name")
                ci = int(cue_index) if cue_index is not None else None
                data_out = lom_ops.jump_to_cue(live_ctx, ci, name)
                resp = {"op": op, **(data_out or {"ok": False})}
            else:
                resp = {"ok": False, "error": f"unknown op: {op}", "echo": msg}
        except Exception as e:  # pragma: no cover
            resp = {"ok": False, "error": f"exception: {e}"}

        try:
            sock.sendto(json.dumps(resp).encode("utf-8"), addr)
        except Exception:
            pass
