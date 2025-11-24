from __future__ import annotations

from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field


# Shared domain for canonical intents handled by API
Domain = Literal["track", "return", "master", "device", "transport", "song"]


class CanonicalIntent(BaseModel):
    domain: Domain = Field(..., description="Scope: track|return|master|device|transport|song")
    # Allow transport-specific actions to pass through
    action: str = "set"

    # Targets (one of):
    track_index: Optional[int] = None
    return_index: Optional[int] = None      # numeric index (0-based) OR
    return_ref: Optional[str] = None        # letter reference: "A", "B", "C"
    device_index: Optional[int] = None      # device on track or return (depending on which index is present)
    device_name_hint: Optional[str] = None  # optional hint to resolve device_index by name
    device_ordinal_hint: Optional[int] = None  # 1-based ordinal among matches (or among all if no name)

    # Field/parameter selection
    field: Optional[str] = None             # mixer field: volume|pan|mute|solo|cue|tempo|send|routing
    send_index: Optional[int] = None        # numeric index (0-based) OR
    send_ref: Optional[str] = None          # letter reference: "A", "B", "C"
    param_index: Optional[int] = None       # device param index (preferred)
    param_ref: Optional[str] = None         # device param lookup by name (contains match)

    # Value + unit (absolute only in v1)
    # For routing intents, value may be an object with routing keys
    value: Optional[Any] = None
    unit: Optional[str] = None             # db|percent|normalized|ms|hz|on|off
    # For device params: accept display strings (e.g., "245 ms", "5.0 kHz", "High")
    display: Optional[str] = None

    # Song-level fields (for domain="song")
    locator_index: Optional[int] = None        # Locator index (1-based)
    locator_name: Optional[str] = None         # Locator name for jump/lookup
    new_name: Optional[str] = None             # New name for rename operations

    # Options
    dry_run: bool = False
    clamp: bool = True
    # Options for device param dependencies
    auto_enable_master: Optional[bool] = True


class ReadIntent(BaseModel):
    domain: Domain = Field(..., description="Scope: track|return|master|device|transport|song")
    # Targets (one of):
    track_index: Optional[int] = None
    return_index: Optional[int] = None
    return_ref: Optional[str] = None
    device_index: Optional[int] = None

    # Selection
    field: Optional[str] = None            # mixer field for track/return/master
    param_index: Optional[int] = None      # device param index (preferred)
    param_ref: Optional[str] = None        # device param name contains
    # For send reads (track/return)
    send_index: Optional[int] = None
    send_ref: Optional[str] = None


class QueryTarget(BaseModel):
    """Target for get_parameter intent - matches overview.py QueryTarget"""
    track: Optional[str] = None            # "Track 1", "Return A", "Master", or None for transport
    plugin: Optional[str] = None           # Device name or None for mixer params
    parameter: str                         # Parameter name
    device_ordinal: Optional[int] = None   # Optional device ordinal


class QueryIntent(BaseModel):
    """Intent for get_parameter queries"""
    intent: Literal["get_parameter"] = "get_parameter"
    targets: list[QueryTarget]
