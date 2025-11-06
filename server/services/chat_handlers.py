from __future__ import annotations

"""Chat handlers facade.

Currently re-exports handle_chat and handle_help from chat_service. This
provides a stable import path for routers while allowing internal refactors
of chat_service without touching API layers.
"""

from server.services.chat_service import handle_chat, handle_help

__all__ = ["handle_chat", "handle_help"]

