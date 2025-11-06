from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter
from server.services.chat_service import ChatBody, HelpBody, handle_chat, handle_help


router = APIRouter()


@router.post("/chat")
def chat(body: ChatBody) -> Dict[str, Any]:
    return handle_chat(body)


@router.post("/help")
def help_endpoint(body: HelpBody) -> Dict[str, Any]:
    return handle_help(body)
