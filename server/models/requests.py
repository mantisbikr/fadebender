"""Shared request DTO models used across routers.

This module contains Pydantic models for API request bodies that are
used by multiple routers or endpoints.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class IntentParseBody(BaseModel):
    """Request body for intent parsing endpoint.

    Used by: /intent/parse
    """

    text: str
    model: Optional[str] = None
    strict: Optional[bool] = None
    context: Optional[dict] = None


class VolumeDbBody(BaseModel):
    """Request body for volume operations in decibels.

    Used by: /op/volume_db and other volume endpoints
    """

    track_index: int
    db: float


class SelectTrackBody(BaseModel):
    """Request body for track selection.

    Used by: track selection endpoints
    """

    track_index: int
