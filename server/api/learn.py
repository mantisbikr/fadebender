from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from server.services.learn_jobs import LEARN_JOBS
from pydantic import BaseModel
from server.services.param_learning_quick import learn_return_device_quick as svc_learn_quick


router = APIRouter()


@router.get("/return/device/learn_status")
def learn_return_device_status(id: str) -> Dict[str, Any]:
    """Return status for a learning job (shared job registry)."""
    job = LEARN_JOBS.get(id)
    if not job:
        return {"ok": False, "error": "unknown_job"}
    return {"ok": True, **job}


class LearnQuickBody(BaseModel):
    return_index: int
    device_index: int


@router.post("/return/device/learn_quick")
def learn_quick(body: LearnQuickBody) -> Dict[str, Any]:
    """Fast learning using minimal anchors + heuristics.

    Matches legacy behavior; gated by FB_DEBUG_LEGACY_LEARN in app layer previously.
    We keep endpoint behavior identical here.
    """
    import os
    if str(os.getenv("FB_DEBUG_LEGACY_LEARN", "")).lower() not in ("1", "true", "yes", "on"):
        raise HTTPException(404, "legacy_disabled")
    try:
        return svc_learn_quick(int(body.return_index), int(body.device_index))
    except ValueError as e:
        if str(e) == "device_not_found":
            raise HTTPException(404, "device_not_found")
        raise
