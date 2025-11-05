"""Typed settings for environment-based configuration.

This module provides a Pydantic-based settings class for type-safe configuration.
It will gradually replace dictionary-based config access in Phase 1.

Usage:
    from server.config.settings import get_settings

    settings = get_settings()
    port = settings.server_port
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All settings can be overridden via environment variables.
    Prefix: FB_ (FadeBender)

    Example:
        export FB_SERVER_PORT=8722
        export FB_LOG_LEVEL=DEBUG
    """

    # Server settings
    server_host: str = Field(default="127.0.0.1", description="Server host")
    server_port: int = Field(default=8722, description="Server port")

    # CORS settings
    cors_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        description="Comma-separated list of allowed CORS origins"
    )
    allow_all_cors: bool = Field(default=False, description="Allow all CORS origins (*)")

    # Logging
    log_level: str = Field(default="INFO", description="Logging level (DEBUG, INFO, WARNING, ERROR)")

    # Ableton connection
    ableton_host: str = Field(default="127.0.0.1", description="Ableton Live host")
    ableton_port: int = Field(default=9001, description="Ableton Live OSC port")

    # Status/cache TTLs
    status_ttl_seconds: float = Field(default=1.0, description="Status cache TTL in seconds")

    # LLM settings
    llm_model: Optional[str] = Field(default=None, description="LLM model name")
    vertex_project: Optional[str] = Field(default=None, description="GCP Vertex AI project")
    vertex_location: str = Field(default="us-central1", description="GCP Vertex AI location")

    # Debug/development
    debug: bool = Field(default=False, description="Enable debug mode")
    reload: bool = Field(default=False, description="Enable auto-reload in dev mode")

    class Config:
        # Environment variable prefix
        env_prefix = "FB_"
        # Case insensitive env vars
        case_sensitive = False
        # Allow extra fields from environment
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance.

    Settings are loaded once and cached for the lifetime of the process.
    To reload settings, clear the cache: get_settings.cache_clear()
    """
    return Settings()


def get_cors_origins() -> list[str]:
    """Get CORS origins as a list.

    Returns:
        List of allowed origins, or ["*"] if allow_all_cors is True.
    """
    settings = get_settings()
    if settings.allow_all_cors:
        return ["*"]

    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    return origins if origins else ["http://localhost:3000", "http://127.0.0.1:3000"]
