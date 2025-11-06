"""Error handling middleware for consistent error responses."""

from __future__ import annotations

import logging
import traceback
from typing import Callable

from fastapi import HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from server.models.errors import AppError, ErrorResponse

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware that catches exceptions and returns standard error responses.

    Handles:
    - AppError: Custom application errors with standard format
    - HTTPException: FastAPI HTTP exceptions (converted to standard format)
    - Exception: Unexpected errors (converted to 500 internal error)
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            response = await call_next(request)
            return response
        except AppError as exc:
            # Our custom application errors
            logger.warning(
                f"AppError: {exc.code} - {exc.message}",
                extra={"code": exc.code, "detail": exc.detail},
            )
            return JSONResponse(
                status_code=exc.status_code,
                content=exc.to_response().model_dump(),
            )
        except HTTPException as exc:
            # FastAPI HTTPException - convert to standard format
            # Extract code from detail if it's a simple string like "device_not_found"
            detail_str = str(exc.detail) if exc.detail else "http_error"
            code = detail_str if "_" in detail_str else "http_error"

            error_response = ErrorResponse(
                ok=False,
                code=code,
                message=exc.detail or "HTTP error",
                detail={"status_code": exc.status_code},
            )
            logger.warning(
                f"HTTPException: {code}",
                extra={"status_code": exc.status_code, "detail": exc.detail},
            )
            return JSONResponse(
                status_code=exc.status_code,
                content=error_response.model_dump(),
            )
        except Exception as exc:
            # Unexpected errors - log full traceback and return 500
            logger.error(
                f"Unexpected error: {exc}",
                exc_info=True,
                extra={"traceback": traceback.format_exc()},
            )
            error_response = ErrorResponse(
                ok=False,
                code="internal_error",
                message="An unexpected error occurred",
                detail={"error": str(exc)} if logger.isEnabledFor(logging.DEBUG) else None,
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=error_response.model_dump(),
            )
