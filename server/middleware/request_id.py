"""Middleware to attach a request ID to every request/response.

Adds `X-Request-ID` header if not provided by the client and exposes the
value on `request.state.request_id` for logging.
"""

from __future__ import annotations

import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class RequestIDMiddleware(BaseHTTPMiddleware):
  async def dispatch(self, request: Request, call_next: Callable) -> Response:
    req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = req_id
    response = await call_next(request)
    response.headers.setdefault("X-Request-ID", req_id)
    return response

