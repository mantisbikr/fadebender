from __future__ import annotations

from typing import Optional, TypedDict, Union


class PatternMatch(TypedDict, total=False):
    track_num: Optional[int]
    return_ref: Optional[str]
    device_name: Optional[str]
    device_ordinal: Optional[int]
    parameter: Optional[str]
    value: Union[float, str, None]
    unit: Optional[str]
