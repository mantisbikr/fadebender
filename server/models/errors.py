"""Standard error response models and exceptions for consistent error handling."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Standard error response format.

    All API errors should follow this structure:
    {
        "ok": false,
        "code": "error_code_snake_case",
        "message": "Human-readable error message",
        "detail": {...}  # Optional additional context
    }
    """

    ok: bool = False
    code: str
    message: str
    detail: Optional[Any] = None


class AppError(Exception):
    """Base application error that will be caught by error middleware.

    Usage:
        raise AppError("not_found", "Device not found", status_code=404, detail={"device_id": 123})
    """

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        detail: Optional[Any] = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.detail = detail
        super().__init__(message)

    def to_response(self) -> ErrorResponse:
        """Convert to standard error response model."""
        return ErrorResponse(
            ok=False,
            code=self.code,
            message=self.message,
            detail=self.detail,
        )


# Common error helpers for convenience
def not_found_error(resource: str, identifier: Any = None) -> AppError:
    """Helper for 404 not found errors."""
    message = f"{resource.replace('_', ' ').title()} not found"
    detail = {"resource": resource}
    if identifier is not None:
        detail["id"] = identifier
    return AppError(
        code=f"{resource}_not_found",
        message=message,
        status_code=404,
        detail=detail,
    )


def validation_error(message: str, detail: Optional[Any] = None) -> AppError:
    """Helper for 400 validation errors."""
    return AppError(
        code="validation_error",
        message=message,
        status_code=400,
        detail=detail,
    )


def internal_error(message: str = "Internal server error", detail: Optional[Any] = None) -> AppError:
    """Helper for 500 internal errors."""
    return AppError(
        code="internal_error",
        message=message,
        status_code=500,
        detail=detail,
    )
