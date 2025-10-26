from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, TypedDict


IntentType = Literal[
    "set_parameter",
    "relative_change",
    "get_parameter",
    "question_response",
    "clarification_needed",
]


class Target(TypedDict, total=False):
    track: Optional[str]
    plugin: Optional[str]
    parameter: str
    device_ordinal: Optional[int]


class Operation(TypedDict, total=False):
    type: Literal["absolute", "relative"]
    value: float | str
    unit: Optional[str]


class Intent(TypedDict, total=False):
    intent: IntentType
    targets: List[Target]
    operation: Operation
    meta: Dict[str, Any]
    answer: str
    suggested_intents: List[str]
    question: str
    context: Dict[str, Any]
