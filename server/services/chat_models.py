from __future__ import annotations

from typing import Any, Optional, Dict

from pydantic import BaseModel


class ChatBody(BaseModel):
    text: str
    confirm: bool = True
    model: Optional[str] = None
    strict: Optional[bool] = None


class HelpBody(BaseModel):
    query: str
    context: Optional[Dict[str, Any]] = None

