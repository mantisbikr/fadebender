from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from server.models.intents_api import (
    Domain,
    CanonicalIntent,
    ReadIntent,
    QueryTarget,
    QueryIntent,
)


router = APIRouter()


@router.post("/intent/execute")
def execute_intent(intent: CanonicalIntent, debug: bool = False) -> Dict[str, Any]:
    """Dispatch canonical intent to specialized services.

    The API layer keeps minimal logic and delegates execution to
    server.services.intents.* modules to avoid drift and reduce size.
    """
    import time
    from server.api.cap_utils import add_capabilities_ref

    # Generate unique request ID
    request_id = str(int(time.time() * 1000))

    d = intent.domain
    field = (intent.field or "").strip().lower()

    # Transport domain (direct pass-through)
    if d == "transport":
        from server.services.ableton_client import request_op as _req
        action = getattr(intent, "action", "")
        value = getattr(intent, "value", None)
        # Scene fire/stop mapped to dedicated ops
        if action == "scene_fire":
            try:
                scene_index = int(value)
            except Exception:
                raise HTTPException(400, "invalid_scene_index")
            r = _req("fire_scene", timeout=1.0, scene_index=scene_index, select=True)
            return {
                "ok": bool(r and r.get("ok", True)),
                "summary": f"Scene {scene_index} fired",
                "resp": r,
            }
        if action == "scene_stop":
            try:
                scene_index = int(value)
            except Exception:
                raise HTTPException(400, "invalid_scene_index")
            r = _req("stop_scene", timeout=1.0, scene_index=scene_index)
            return {
                "ok": bool(r and r.get("ok", True)),
                "summary": f"Scene {scene_index} stopped",
                "resp": r,
            }
        # Naming: track / scene / clip (mapped to existing UDP ops)
        if action == "rename_track":
            if not isinstance(value, dict):
                raise HTTPException(400, "invalid_rename_track_payload")
            try:
                ti = int(value.get("track_index"))
                name = str(value.get("name") or "").strip()
            except Exception:
                raise HTTPException(400, "invalid_rename_track_payload")
            if not name:
                raise HTTPException(400, "empty_track_name")
            r = _req("set_track_name", timeout=1.0, track_index=ti, name=name)
            return {
                "ok": bool(r and r.get("ok", True)),
                "summary": f"Renamed Track {ti} to \"{name}\"",
                "resp": r,
            }
        if action == "rename_scene":
            if not isinstance(value, dict):
                raise HTTPException(400, "invalid_rename_scene_payload")
            try:
                si = int(value.get("scene_index"))
                name = str(value.get("name") or "").strip()
            except Exception:
                raise HTTPException(400, "invalid_rename_scene_payload")
            if not name:
                raise HTTPException(400, "empty_scene_name")
            r = _req("set_scene_name", timeout=1.0, scene_index=si, name=name)
            return {
                "ok": bool(r and r.get("ok", True)),
                "summary": f"Renamed Scene {si} to \"{name}\"",
                "resp": r,
            }
        if action == "rename_clip":
            if not isinstance(value, dict):
                raise HTTPException(400, "invalid_rename_clip_payload")
            try:
                ti = int(value.get("track_index"))
                si = int(value.get("scene_index"))
                name = str(value.get("name") or "").strip()
            except Exception:
                raise HTTPException(400, "invalid_rename_clip_payload")
            if not name:
                raise HTTPException(400, "empty_clip_name")
            r = _req(
                "set_clip_name",
                timeout=1.0,
                track_index=ti,
                scene_index=si,
                name=name,
            )
            return {
                "ok": bool(r and r.get("ok", True)),
                "summary": f"Renamed Clip [{ti},{si}] to \"{name}\"",
                "resp": r,
            }
        # Project structure: tracks/scenes create/delete/duplicate
        if action == "create_audio_track":
            idx = None
            name = None
            if isinstance(value, dict):
                idx = value.get("index")
                name = (value.get("name") or "").strip() or None
            elif value is not None:
                try:
                    idx = int(value)
                except Exception:
                    idx = None
            params: Dict[str, Any] = {}
            if idx is not None:
                params["index"] = int(idx)
            r = _req("create_audio_track", timeout=1.5, **params)
            new_index = None
            try:
                new_index = r.get("index")
            except Exception:
                new_index = idx
            # Optional naming step
            if name and new_index:
                try:
                    _ = _req("set_track_name", timeout=1.0, track_index=int(new_index), name=name)
                except Exception:
                    pass
            return {
                "ok": bool(r and r.get("ok", True)),
                "summary": (
                    f"Created audio track {new_index} \"{name}\""
                    if new_index and name
                    else f"Created audio track at index {idx}" if idx is not None else "Created audio track at end"
                ),
                "resp": r,
            }
        if action == "create_midi_track":
            idx = None
            name = None
            if isinstance(value, dict):
                idx = value.get("index")
                name = (value.get("name") or "").strip() or None
            elif value is not None:
                try:
                    idx = int(value)
                except Exception:
                    idx = None
            params: Dict[str, Any] = {}
            if idx is not None:
                params["index"] = int(idx)
            r = _req("create_midi_track", timeout=1.5, **params)
            new_index = None
            try:
                new_index = r.get("index")
            except Exception:
                new_index = idx
            if name and new_index:
                try:
                    _ = _req("set_track_name", timeout=1.0, track_index=int(new_index), name=name)
                except Exception:
                    pass
            return {
                "ok": bool(r and r.get("ok", True)),
                "summary": (
                    f"Created MIDI track {new_index} \"{name}\""
                    if new_index and name
                    else f"Created MIDI track at index {idx}" if idx is not None else "Created MIDI track at end"
                ),
                "resp": r,
            }
        if action == "delete_track":
            ti = None
            if isinstance(value, dict):
                ti = value.get("index")
            else:
                try:
                    ti = int(value)
                except Exception:
                    ti = None
            if ti is None:
                raise HTTPException(400, "invalid_track_index")
            r = _req("delete_track", timeout=1.5, track_index=int(ti))
            return {
                "ok": bool(r and r.get("ok", True)),
                "summary": f"Deleted track {ti}",
                "resp": r,
            }
        if action == "duplicate_track":
            ti = None
            name = None
            if isinstance(value, dict):
                ti = value.get("index")
                name = (value.get("name") or "").strip() or None
            else:
                try:
                    ti = int(value)
                except Exception:
                    ti = None
            if ti is None:
                raise HTTPException(400, "invalid_track_index")
            r = _req("duplicate_track", timeout=1.5, track_index=int(ti))
            # In Live, duplicate_track inserts the new track directly after the source.
            # Use ti+1 as the new index for optional renaming.
            new_index = int(ti) + 1
            if name:
                try:
                    rename_result = _req("set_track_name", timeout=1.0, track_index=new_index, name=name)
                except Exception as e:
                    pass
            return {
                "ok": bool(r and r.get("ok", True)),
                "summary": (
                    f"Duplicated track {ti} as {new_index} \"{name}\""
                    if name
                    else f"Duplicated track {ti} as {new_index}"
                ),
                "resp": r,
            }
        if action == "create_scene":
            idx = None
            name = None
            if isinstance(value, dict):
                idx = value.get("scene_index")
                name = (value.get("name") or "").strip() or None
            elif value is not None:
                try:
                    idx = int(value)
                except Exception:
                    idx = None
            params: Dict[str, Any] = {}
            if idx is not None:
                params["index"] = int(idx)
            r = _req("create_scene", timeout=1.5, **params)
            new_index = None
            try:
                new_index = r.get("index")
            except Exception:
                new_index = idx
            if name and new_index:
                try:
                    _ = _req("set_scene_name", timeout=1.0, scene_index=int(new_index), name=name)
                except Exception:
                    pass
            return {
                "ok": bool(r and r.get("ok", True)),
                "summary": (
                    f"Created scene {new_index} \"{name}\""
                    if new_index and name
                    else f"Created scene at index {idx}" if idx is not None else "Created scene at end"
                ),
                "resp": r,
            }
        if action == "delete_scene":
            si = None
            if isinstance(value, dict):
                si = value.get("scene_index")
            else:
                try:
                    si = int(value)
                except Exception:
                    si = None
            if si is None:
                raise HTTPException(400, "invalid_scene_index")
            r = _req("delete_scene", timeout=1.5, scene_index=int(si))
            return {
                "ok": bool(r and r.get("ok", True)),
                "summary": f"Deleted scene {si}",
                "resp": r,
            }
        if action == "duplicate_scene":
            si = None
            name = None
            if isinstance(value, dict):
                si = value.get("scene_index")
                name = (value.get("name") or "").strip() or None
            else:
                try:
                    si = int(value)
                except Exception:
                    si = None
            if si is None:
                raise HTTPException(400, "invalid_scene_index")
            r = _req("duplicate_scene", timeout=1.5, scene_index=int(si))
            # In Live, duplicate_scene inserts the new scene directly after the source.
            # Use si+1 as the new index for optional renaming.
            new_index = int(si) + 1
            if name:
                try:
                    _ = _req("set_scene_name", timeout=1.0, scene_index=new_index, name=name)
                except Exception:
                    pass
            return {
                "ok": bool(r and r.get("ok", True)),
                "summary": (
                    f"Duplicated scene {si} as {new_index} \"{name}\""
                    if name
                    else f"Duplicated scene {si}"
                ),
                "resp": r,
            }
        # Clip fire/stop (Session clips)
        if action == "clip_fire":
            ti = None
            si = None
            if isinstance(value, dict):
                ti = value.get("track_index")
                si = value.get("scene_index")
            elif isinstance(value, (list, tuple)) and len(value) >= 2:
                ti, si = value[0], value[1]
            try:
                track_index = int(ti)
                scene_index = int(si)
            except Exception:
                raise HTTPException(400, "invalid_clip_coordinates")
            r = _req(
                "fire_clip",
                timeout=1.0,
                track_index=track_index,
                scene_index=scene_index,
                select=True,
            )
            return {
                "ok": bool(r and r.get("ok", True)),
                "summary": f"Clip [{track_index},{scene_index}] fired",
                "resp": r,
            }
        if action == "clip_stop":
            ti = None
            si = None
            if isinstance(value, dict):
                ti = value.get("track_index")
                si = value.get("scene_index")
            elif isinstance(value, (list, tuple)) and len(value) >= 2:
                ti, si = value[0], value[1]
            try:
                track_index = int(ti)
                scene_index = int(si)
            except Exception:
                raise HTTPException(400, "invalid_clip_coordinates")
            r = _req(
                "stop_clip",
                timeout=1.0,
                track_index=track_index,
                scene_index=scene_index,
            )
            return {
                "ok": bool(r and r.get("ok", True)),
                "summary": f"Clip [{track_index},{scene_index}] stopped",
                "resp": r,
            }
        if action == "clip_create":
            ti = None
            si = None
            length = 4.0
            if isinstance(value, dict):
                ti = value.get("track_index")
                si = value.get("scene_index")
                if value.get("length_beats") is not None:
                    try:
                        length = float(value.get("length_beats"))
                    except Exception:
                        length = 4.0
            try:
                track_index = int(ti)
                scene_index = int(si)
            except Exception:
                raise HTTPException(400, "invalid_clip_coordinates")
            r = _req(
                "create_clip",
                timeout=1.5,
                track_index=track_index,
                scene_index=scene_index,
                length_beats=length,
            )
            return {
                "ok": bool(r and r.get("ok", True)),
                "summary": f"Created clip on Track {track_index}, Scene {scene_index}",
                "resp": r,
            }
        if action == "clip_delete":
            ti = None
            si = None
            if isinstance(value, dict):
                ti = value.get("track_index")
                si = value.get("scene_index")
            try:
                track_index = int(ti)
                scene_index = int(si)
            except Exception:
                raise HTTPException(400, "invalid_clip_coordinates")
            r = _req(
                "delete_clip",
                timeout=1.5,
                track_index=track_index,
                scene_index=scene_index,
            )
            return {
                "ok": bool(r and r.get("ok", True)),
                "summary": f"Deleted clip on Track {track_index}, Scene {scene_index}",
                "resp": r,
            }
        if action == "clip_duplicate":
            ti = None
            si = None
            tti = None
            tsi = None
            name = None
            if isinstance(value, dict):
                ti = value.get("track_index")
                si = value.get("scene_index")
                tti = value.get("target_track_index")
                tsi = value.get("target_scene_index")
                name = (value.get("name") or "").strip() or None
            try:
                track_index = int(ti)
                scene_index = int(si)
                target_track_index = int(tti) if tti is not None else track_index
                target_scene_index = int(tsi) if tsi is not None else (scene_index + 1)
            except Exception:
                raise HTTPException(400, "invalid_clip_coordinates")
            r = _req(
                "duplicate_clip",
                timeout=1.5,
                track_index=track_index,
                scene_index=scene_index,
                target_track_index=target_track_index,
                target_scene_index=target_scene_index,
            )
            # Optional rename of duplicated clip when a name is provided
            if name and (r and r.get("ok", True)):
                try:
                    _ = _req(
                        "set_clip_name",
                        timeout=1.0,
                        track_index=target_track_index,
                        scene_index=target_scene_index,
                        name=name,
                    )
                except Exception:
                    # Best-effort only; don't fail duplication on rename issues
                    pass
            return {
                "ok": bool(r and r.get("ok", True)),
                "summary": (
                    f"Duplicated clip [{track_index},{scene_index}] \u2192 [{target_track_index},{target_scene_index}] \"{name}\""
                    if name
                    else f"Duplicated clip [{track_index},{scene_index}] \u2192 [{target_track_index},{target_scene_index}]"
                ),
                "resp": r,
            }
        # Combined time signature
        if action == "time_sig_both" and isinstance(value, dict):
            num = value.get("num"); den = value.get("den")
            ok_all = True
            if num is not None:
                r1 = _req("set_transport", timeout=1.0, action="time_sig_num", value=float(num))
                ok_all = ok_all and bool(r1 and r1.get("ok", True))
            if den is not None:
                r2 = _req("set_transport", timeout=1.0, action="time_sig_den", value=float(den))
                ok_all = ok_all and bool(r2 and r2.get("ok", True))
            return {"ok": ok_all, "summary": f"Transport: time_signature {num}/{den}"}
        # Combined loop region
        if action == "loop_region" and isinstance(value, dict):
            start = value.get("start"); length = value.get("length")
            ok_all = True
            _ = _req("set_transport", timeout=1.0, action="loop_on", value=1.0)
            if start is not None:
                r1 = _req("set_transport", timeout=1.0, action="loop_start", value=float(start))
                ok_all = ok_all and bool(r1 and r1.get("ok", True))
            if length is not None:
                r2 = _req("set_transport", timeout=1.0, action="loop_length", value=float(length))
                ok_all = ok_all and bool(r2 and r2.get("ok", True))
            return {"ok": ok_all, "summary": f"Transport: loop_region start={start} length={length}"}
        # Simple action
        params: Dict[str, Any] = {"action": str(action)}
        if value is not None:
            try:
                params["value"] = float(value)
            except Exception:
                pass
        r = _req("set_transport", timeout=1.0, **params)
        return {"ok": bool(r and r.get("ok", True)), "summary": f"Transport: {action}{(' ' + str(value)) if value is not None else ''}", "resp": r}

    # Track arm (separate from mixer field operations)
    if d == "track" and getattr(intent, "action", "") == "arm" and intent.track_index is not None:
        from server.services.ableton_client import request_op as _req
        try:
            arm_val = bool(intent.value) if intent.value is not None else True
            ti = int(intent.track_index)
        except Exception:
            raise HTTPException(400, "invalid_track_arm_payload")
        r = _req("set_track_arm", timeout=1.0, track_index=ti, arm=arm_val)
        return {
            "ok": bool(r and r.get("ok", True)),
            "summary": f"Track {ti} {'armed' if arm_val else 'disarmed'}",
            "resp": r,
        }

    # Routing
    if d == "track" and field == "routing" and intent.track_index is not None:
        from server.services.intents.routing_service import set_track_routing
        return set_track_routing(intent)
    if d == "return" and field == "routing" and (intent.return_index is not None or intent.return_ref is not None):
        from server.services.intents.routing_service import set_return_routing
        return set_return_routing(intent)

    # Mixer (track/return/master)
    if d == "track" and field in ("volume", "pan", "mute", "solo"):
        from server.services.intents.mixer_service import set_track_mixer
        result = set_track_mixer(intent)
        result["request_id"] = request_id
        return add_capabilities_ref(result, intent.model_dump())
    if d == "track" and field == "send":
        from server.services.intents.mixer_service import set_track_send
        result = set_track_send(intent)
        result["request_id"] = request_id
        return add_capabilities_ref(result, intent.model_dump())

    if d == "return" and field in ("volume", "pan", "mute", "solo"):
        from server.services.intents.mixer_service import set_return_mixer
        result = set_return_mixer(intent)
        result["request_id"] = request_id
        return add_capabilities_ref(result, intent.model_dump())
    if d == "return" and field == "send":
        from server.services.intents.mixer_service import set_return_send
        result = set_return_send(intent)
        result["request_id"] = request_id
        return add_capabilities_ref(result, intent.model_dump())

    if d == "master" and field in ("volume", "pan", "cue"):
        from server.services.intents.mixer_service import set_master_mixer
        result = set_master_mixer(intent)
        result["request_id"] = request_id
        return add_capabilities_ref(result, intent.model_dump())

    # Device parameters (track/return)
    if d == "device" and (intent.return_index is not None or intent.return_ref is not None) and intent.device_index is not None:
        from server.services.intents.param_service import set_return_device_param
        result = set_return_device_param(intent, debug=debug)
        result["request_id"] = request_id
        return add_capabilities_ref(result, intent.model_dump())
    if d == "device" and intent.track_index is not None and intent.device_index is not None:
        from server.services.intents.param_service import set_track_device_param
        result = set_track_device_param(intent, debug=debug)
        result["request_id"] = request_id
        return add_capabilities_ref(result, intent.model_dump())

    # Song-level operations (undo/redo, info, locators)
    if d == "song":
        from server.services.ableton_client import request_op as _req
        action = getattr(intent, "action", "")

        # Undo
        if action == "undo":
            r = _req("song_undo", timeout=1.5)
            return {
                "ok": bool(r and r.get("ok", True)),
                "summary": "Undo last change",
                "resp": r,
            }

        # Redo
        if action == "redo":
            r = _req("song_redo", timeout=1.5)
            return {
                "ok": bool(r and r.get("ok", True)),
                "summary": "Redo last change",
                "resp": r,
            }

        # Song info
        if action == "get_info":
            r = _req("get_song_info", timeout=1.0)
            if not r:
                return {"ok": False, "error": "no response"}
            data = r.get("data") if isinstance(r, dict) else r
            song_name = data.get("name", "Unknown") if isinstance(data, dict) else "Unknown"
            tempo = data.get("tempo") if isinstance(data, dict) else None
            time_sig_num = data.get("time_signature_numerator") if isinstance(data, dict) else None
            time_sig_den = data.get("time_signature_denominator") if isinstance(data, dict) else None

            # Build comprehensive summary
            parts = [f"Song: {song_name}"]
            if tempo is not None:
                parts.append(f"Tempo: {tempo} BPM")
            if time_sig_num is not None and time_sig_den is not None:
                parts.append(f"Time signature: {time_sig_num}/{time_sig_den}")

            return {
                "ok": True,
                "summary": " | ".join(parts),
                "data": data,
                "resp": r,
            }

        # List locators
        if action == "list_locators":
            r = _req("get_cue_points", timeout=1.0)
            if not r:
                return {"ok": False, "error": "no response"}
            data = r.get("data") if isinstance(r, dict) else r
            cues = data.get("cue_points", []) if isinstance(data, dict) else []
            count = len(cues)

            # Build formatted list
            if count == 0:
                summary = "No locators found"
            else:
                header = f"Found {count} locator{'s' if count != 1 else ''}:"
                locator_lines = []
                for cue in cues:
                    idx = cue.get("index", "?")
                    name = cue.get("name", "Untitled")
                    time = cue.get("time", 0)
                    locator_lines.append(f"  {idx}. {name} @ {time} beats")
                summary = header + "\n" + "\n".join(locator_lines)

            return {
                "ok": True,
                "summary": summary,
                "data": data,
                "resp": r,
            }

        # Jump to locator
        if action == "jump_locator":
            params: Dict[str, Any] = {}
            if intent.locator_index is not None:
                params["cue_index"] = int(intent.locator_index)
            if intent.locator_name is not None:
                params["name"] = str(intent.locator_name)

            if not params:
                raise HTTPException(400, "missing_locator_target")

            r = _req("jump_to_cue", timeout=1.5, **params)
            target = f"locator {intent.locator_index}" if intent.locator_index else f'"{intent.locator_name}"'
            return {
                "ok": bool(r and r.get("ok", True)),
                "summary": f"Jumped to {target}",
                "resp": r,
            }

        # Rename locator
        if action == "rename_locator":
            if intent.locator_index is None or not intent.new_name:
                raise HTTPException(400, "missing_rename_params")

            r = _req(
                "set_cue_name",
                timeout=1.0,
                cue_index=int(intent.locator_index),
                name=str(intent.new_name)
            )
            return {
                "ok": bool(r and r.get("ok", True)),
                "summary": f'Renamed locator {intent.locator_index} to "{intent.new_name}"',
                "resp": r,
            }

        # Unknown song action
        raise HTTPException(400, f"unsupported_song_action: {action}")

    # If we reach here, the intent is unsupported
    raise HTTPException(400, "unsupported_intent")


@router.post("/intent/read")
def read_intent_endpoint(intent: ReadIntent) -> Dict[str, Any]:
    """Read current parameter values for mixer and routing.

    Used by the UI when clicking on capability chips to open parameter editors.
    Returns current values with display formatting.
    """
    from server.services.intents.read_service import read_intent
    return read_intent(intent)


@router.post("/intent/query")
async def query_intent(intent: QueryIntent) -> Dict[str, Any]:
    """Handle get_parameter intent by calling /snapshot/query endpoint."""
    import httpx

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://localhost:8722/snapshot/query",
                json={"targets": [t.model_dump() for t in intent.targets]},
                timeout=5.0,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(500, f"Failed to query snapshot: {str(e)}")
