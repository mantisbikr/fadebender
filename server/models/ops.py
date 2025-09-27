from typing import Optional, Literal
from pydantic import BaseModel, Field, validator


class MixerOp(BaseModel):
    track_index: int = Field(ge=1)
    field: Literal["volume", "pan", "mute", "solo"]
    value: float

    @validator("value")
    def clamp_value(cls, v, values):
        field = values.get("field")
        if field == "pan":
            return max(-1.0, min(1.0, float(v)))
        if field in ("volume",):
            return max(0.0, min(1.0, float(v)))
        return float(v)


class SendOp(BaseModel):
    track_index: int = Field(ge=1)
    send_index: int = Field(ge=0)
    value: float

    @validator("value")
    def clamp_send(cls, v):
        return max(0.0, min(1.0, float(v)))


class DeviceParamOp(BaseModel):
    track_index: int = Field(ge=1)
    device_index: int = Field(ge=0)
    param_index: int = Field(ge=0)
    value: float
