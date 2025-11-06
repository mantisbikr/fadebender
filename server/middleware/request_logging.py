"""Lightweight request logging middleware.

Logs a single JSON line for key endpoints with route, method, status, latency,
and X-Request-ID (from RequestIDMiddleware).
"""

from __future__ import annotations

import json
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


KEY_PATHS = {
    "/chat",
    "/intent/parse",
    "/snapshot/query",
    "/intent/execute",
    "/op/mixer",
}


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.perf_counter()
        response: Response
        try:
            response = await call_next(request)
            return response
        finally:
            elapsed_ms = round((time.perf_counter() - start) * 1000.0, 2)
            path = request.url.path
            if any(path.startswith(p) for p in KEY_PATHS):
                rid = getattr(getattr(request, "state", object()), "request_id", None)
                rec = {
                    "event": "request",
                    "path": path,
                    "method": request.method,
                    "status": getattr(response, "status_code", None),
                    "duration_ms": elapsed_ms,
                    "request_id": rid,
                }
                try:
                    print(json.dumps(rec, separators=(",", ":")))
                except Exception:
                    pass
