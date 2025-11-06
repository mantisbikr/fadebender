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

