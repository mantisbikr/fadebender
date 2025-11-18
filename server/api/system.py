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
