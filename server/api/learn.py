from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from server.services.learn_jobs import LEARN_JOBS
from pydantic import BaseModel
from server.services.param_learning_quick import learn_return_device_quick as svc_learn_quick
from server.services.param_learning_start import learn_return_device_start as svc_learn_start


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
    """Fast learning using minimal anchors + heuristics (always enabled)."""
    try:
        return svc_learn_quick(int(body.return_index), int(body.device_index))
    except ValueError as e:
        if str(e) == "device_not_found":
            raise HTTPException(404, "device_not_found")
        raise


class LearnStartBody(BaseModel):
    return_index: int
    device_index: int
    resolution: int = 41
    sleep_ms: int = 20


@router.post("/return/device/learn_start")
async def learn_start(body: LearnStartBody) -> Dict[str, Any]:
    return await svc_learn_start(int(body.return_index), int(body.device_index), int(body.resolution), int(body.sleep_ms))
