from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from server.services.learn_jobs import LEARN_JOBS


router = APIRouter()


@router.get("/return/device/learn_status")
def learn_return_device_status(id: str) -> Dict[str, Any]:
    """Return status for a learning job (shared job registry)."""
    job = LEARN_JOBS.get(id)
    if not job:
        return {"ok": False, "error": "unknown_job"}
    return {"ok": True, **job}

