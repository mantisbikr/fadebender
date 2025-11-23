from __future__ import annotations

import time
from typing import Any, Dict

from fastapi import APIRouter

from server.services.ableton_client import request_op
from server.config.helpers import status_ttl_seconds


router = APIRouter()


@router.get("/ping")
def ping() -> Dict[str, Any]:
    resp = request_op("ping", timeout=0.5)
    ok = bool(resp and resp.get("ok", True))
    return {"ok": ok, "remote": resp}


@router.get("/status")
def status() -> Dict[str, Any]:
    # short TTL cache to reduce poll churn
    try:
        now = time.time()
        ttl = status_ttl_seconds(1.0)
        cache = globals().setdefault("_TTL_CACHE", {})  # type: ignore
        ent = cache.get("status") if isinstance(cache, dict) else None
        if ent and isinstance(ent, dict):
            ts = float(ent.get("ts", 0.0))
            if ttl > 0 and (now - ts) < ttl:
                return ent.get("data")
        resp = request_op("get_overview", timeout=1.0)
        if not resp:
            return {"ok": False, "error": "no response"}
        cache["status"] = {"ts": now, "data": resp}
        return resp
    except Exception:
        resp = request_op("get_overview", timeout=1.0)
        if not resp:
            return {"ok": False, "error": "no response"}
        return resp


@router.get("/project/outline")
def project_outline() -> Dict[str, Any]:
    """Return lightweight project outline (tracks, selected track, scenes)."""
    try:
        now = time.time()
        ttl = status_ttl_seconds(1.0)
        cache = globals().setdefault("_TTL_CACHE", {})  # type: ignore
        ent = cache.get("project_outline") if isinstance(cache, dict) else None
        if ent and isinstance(ent, dict):
            ts = float(ent.get("ts", 0.0))
            if ttl > 0 and (now - ts) < ttl:
                return ent.get("data")
        resp = request_op("get_overview", timeout=1.0)
        if not resp:
            return {"ok": False, "error": "no response"}
        data = resp.get("data") if isinstance(resp, dict) else resp
        out = {"ok": True, "data": data}
        cache["project_outline"] = {"ts": now, "data": out}
        return out
    except Exception:
        resp = request_op("get_overview", timeout=1.0)
        if not resp:
            return {"ok": False, "error": "no response"}
        data = resp.get("data") if isinstance(resp, dict) else resp
        return {"ok": True, "data": data}


@router.get("/scenes")
def list_scenes() -> Dict[str, Any]:
    resp = request_op("get_scenes", timeout=1.0)
    if not resp:
        return {"ok": False, "error": "no response"}
    data = resp.get("data") if isinstance(resp, dict) else resp
    return {"ok": True, "data": data}


from pydantic import BaseModel


class CaptureInsertSceneBody(BaseModel):
    pass


@router.post("/scene/capture_insert")
def capture_insert_scene(_: CaptureInsertSceneBody) -> Dict[str, Any]:
    resp = request_op("capture_and_insert_scene", timeout=2.0)
    if not resp:
        return {"ok": False, "error": "no response"}
    data = resp.get("data") if isinstance(resp, dict) else resp
    return {"ok": True, "data": data}


class CreateSceneBody(BaseModel):
    index: int | None = None  # 1-based insert position; omit to append


@router.post("/scene/create")
def create_scene(body: CreateSceneBody) -> Dict[str, Any]:
    msg: Dict[str, Any] = {}
    if body.index is not None:
        msg["index"] = int(body.index)
    resp = request_op("create_scene", timeout=1.5, **msg)
    if not resp:
        return {"ok": False, "error": "no response"}
    data = resp.get("data") if isinstance(resp, dict) else resp
    return {"ok": True, "data": data}


class SetViewBody(BaseModel):
    mode: str  # 'session' | 'arrangement'


@router.post("/view")
def set_view(body: SetViewBody) -> Dict[str, Any]:
    resp = request_op("set_view", timeout=1.0, mode=str(body.mode))
    if not resp:
        return {"ok": False, "error": "no response"}
    data = resp.get("data") if isinstance(resp, dict) else resp
    return {"ok": True, "data": data}


class FireSceneBody(BaseModel):
    scene_index: int
    select: bool = True


@router.post("/scene/fire")
def fire_scene(body: FireSceneBody) -> Dict[str, Any]:
    resp = request_op("fire_scene", timeout=1.0, scene_index=int(body.scene_index), select=bool(body.select))
    if not resp:
        return {"ok": False, "error": "no response"}
    data = resp.get("data") if isinstance(resp, dict) else resp
    return {"ok": True, "data": data}


class StopSceneBody(BaseModel):
    scene_index: int


@router.post("/scene/stop")
def stop_scene(body: StopSceneBody) -> Dict[str, Any]:
    resp = request_op("stop_scene", timeout=1.0, scene_index=int(body.scene_index))
    if not resp:
        return {"ok": False, "error": "no response"}
    data = resp.get("data") if isinstance(resp, dict) else resp
    return {"ok": True, "data": data}


class DeleteSceneBody(BaseModel):
    scene_index: int


@router.post("/scene/delete")
def delete_scene(body: DeleteSceneBody) -> Dict[str, Any]:
    resp = request_op("delete_scene", timeout=1.5, scene_index=int(body.scene_index))
    if not resp:
        return {"ok": False, "error": "no response"}
    data = resp.get("data") if isinstance(resp, dict) else resp
    return {"ok": True, "data": data}


class DuplicateSceneBody(BaseModel):
    scene_index: int


@router.post("/scene/duplicate")
def duplicate_scene(body: DuplicateSceneBody) -> Dict[str, Any]:
    resp = request_op("duplicate_scene", timeout=1.5, scene_index=int(body.scene_index))
    if not resp:
        return {"ok": False, "error": "no response"}
    data = resp.get("data") if isinstance(resp, dict) else resp
    return {"ok": True, "data": data}


# ---------------- Song-level helpers: undo/redo, info, cues ----------------


@router.get("/song/info")
def get_song_info() -> Dict[str, Any]:
    """Return basic Live Set metadata (name, tempo, time signature)."""
    resp = request_op("get_song_info", timeout=1.0)
    if not resp:
        return {"ok": False, "error": "no response"}
    data = resp.get("data") if isinstance(resp, dict) else resp
    return {"ok": True, "data": data}


@router.get("/song/undo_status")
def get_song_undo_status() -> Dict[str, Any]:
    """Return whether Live reports that undo/redo are currently possible."""
    resp = request_op("get_undo_status", timeout=0.8)
    if not resp:
        return {"ok": False, "error": "no response"}
    data = resp.get("data") if isinstance(resp, dict) and "data" in resp else resp
    return {"ok": True, "data": data}


class SongUndoBody(BaseModel):
    pass


@router.post("/song/undo")
def song_undo(_: SongUndoBody) -> Dict[str, Any]:
    """Trigger Live's global undo (project history)."""
    resp = request_op("song_undo", timeout=1.5)
    if not resp:
        return {"ok": False, "error": "no response"}
    data = resp.get("data") if isinstance(resp, dict) and "data" in resp else resp
    return {"ok": True, "data": data}


class SongRedoBody(BaseModel):
    pass


@router.post("/song/redo")
def song_redo(_: SongRedoBody) -> Dict[str, Any]:
    """Trigger Live's global redo (project history)."""
    resp = request_op("song_redo", timeout=1.5)
    if not resp:
        return {"ok": False, "error": "no response"}
    data = resp.get("data") if isinstance(resp, dict) and "data" in resp else resp
    return {"ok": True, "data": data}


@router.get("/song/cues")
def get_song_cues() -> Dict[str, Any]:
    """List arrangement cue points (locators)."""
    resp = request_op("get_cue_points", timeout=1.0)
    if not resp:
        return {"ok": False, "error": "no response"}
    data = resp.get("data") if isinstance(resp, dict) else resp
    return {"ok": True, "data": data}


class AddCueBody(BaseModel):
    time_beats: float | None = None  # omit to use current song time
    name: str | None = None


@router.post("/song/cue/add")
def add_song_cue(body: AddCueBody) -> Dict[str, Any]:
    """Not implemented: Live's Python API cannot reliably create multiple cue points.

    Fadebender should use its own virtual cue system plus /song/cue/jump instead.
    """
    return {"ok": False, "error": "live_cue_add_not_supported"}


class RenameCueBody(BaseModel):
    cue_index: int
    name: str


@router.post("/song/cue/rename")
def rename_song_cue(body: RenameCueBody) -> Dict[str, Any]:
    """Rename a cue by index (1-based)."""
    resp = request_op("set_cue_name", timeout=1.0, cue_index=int(body.cue_index), name=str(body.name))
    if not resp:
        return {"ok": False, "error": "no response"}
    data = resp.get("data") if isinstance(resp, dict) and "data" in resp else resp
    return {"ok": True, "data": data}


class DeleteCueBody(BaseModel):
    cue_index: int


@router.post("/song/cue/delete")
def delete_song_cue(body: DeleteCueBody) -> Dict[str, Any]:
    """Not implemented: Live's Python API cannot delete cue points from Remote Scripts."""
    return {"ok": False, "error": "live_cue_delete_not_supported"}


class JumpCueBody(BaseModel):
    cue_index: int | None = None
    name: str | None = None


@router.post("/song/cue/jump")
def jump_to_song_cue(body: JumpCueBody) -> Dict[str, Any]:
    """Jump the song position to a cue by index or name."""
    msg: Dict[str, Any] = {}
    if body.cue_index is not None:
        msg["cue_index"] = int(body.cue_index)
    if body.name is not None:
        msg["name"] = str(body.name)
    resp = request_op("jump_to_cue", timeout=1.5, **msg)
    if not resp:
        return {"ok": False, "error": "no response"}
    data = resp.get("data") if isinstance(resp, dict) and "data" in resp else resp
    return {"ok": True, "data": data}


class MoveCueBody(BaseModel):
    cue_index: int
    time_beats: float


@router.post("/song/cue/move")
def move_song_cue(body: MoveCueBody) -> Dict[str, Any]:
    """Move an existing cue to a new time (in beats) by index."""
    resp = request_op("set_cue_time", timeout=1.5, cue_index=int(body.cue_index), time_beats=float(body.time_beats))
    if not resp:
        return {"ok": False, "error": "no response"}
    data = resp.get("data") if isinstance(resp, dict) and "data" in resp else resp
    return {"ok": True, "data": data}
