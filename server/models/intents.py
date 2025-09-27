from __future__ import annotations

from typing import Literal, Optional, Union
from pydantic import BaseModel, Field, validator


class ByRef(BaseModel):
    by: Literal["index", "name"]
    value: Union[int, str]


class TrackTarget(BaseModel):
    track: ByRef


class SendRef(BaseModel):
    by: Literal["index", "name"]
    value: Union[int, str]


class DeviceRef(BaseModel):
    by: Literal["index", "name"]
    value: Union[int, str]


class ParamRef(BaseModel):
    by: Literal["index", "name"]
    value: Union[int, str]


class ValueSpec(BaseModel):
    type: Literal["absolute", "relative"]
    amount: float
    unit: Optional[str] = None  # e.g., 'dB', '%'


# ---- Intent variants ----


class GetOverviewIntent(BaseModel):
    op: Literal["get_overview"] = "get_overview"


class GetTrackStatusIntent(BaseModel):
    op: Literal["get_track_status"] = "get_track_status"
    target: TrackTarget


class SetMixerIntent(BaseModel):
    op: Literal["set_mixer"] = "set_mixer"
    target: TrackTarget
    field: Literal["volume", "pan", "mute", "solo"]
    value: ValueSpec

    @validator("value")
    def clamp_units(cls, v: ValueSpec, values):
        field = values.get("field")
        # Normalize common units for mixer fields
        if field == "volume" and (v.unit is None or v.unit.lower() in {"db", "dB"}):
            v.unit = "dB"
        if field == "pan" and (v.unit is None or v.unit == "%"):
            v.unit = "%"
        return v


class SetSendIntent(BaseModel):
    op: Literal["set_send"] = "set_send"
    target: TrackTarget
    send: SendRef
    value: ValueSpec


class SetDeviceParamIntent(BaseModel):
    op: Literal["set_device_param"] = "set_device_param"
    target: TrackTarget
    device: DeviceRef
    param: ParamRef
    value: ValueSpec


class SelectIntent(BaseModel):
    op: Literal["select"] = "select"
    target: Union[TrackTarget]


# Union alias for external type hints
CanonicalIntent = Union[
    GetOverviewIntent,
    GetTrackStatusIntent,
    SetMixerIntent,
    SetSendIntent,
    SetDeviceParamIntent,
    SelectIntent,
]

