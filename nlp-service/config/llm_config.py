"""
LLM configuration utilities for Fadebender.

Provides project and API key configuration with safe defaults derived from
environment variables, adapted for DAW control use case.
"""
import os


def get_llm_project_id() -> str:
    """Return the Google Cloud project ID for Vertex AI usage."""
    return os.getenv("LLM_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("PROJECT_ID") or "fadebender"


def get_llm_api_key() -> str:
    """Return the Google API key for Vertex AI Gemini (if using key-based auth)."""
    # Support multiple env var names
    return (
        os.getenv("GEMINI_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
        or os.getenv("LLM_API_KEY")
        or ""
    )


def get_default_model_name(preference: str | None = None, operation: str = "intent_parsing") -> str:
    """
    Map a human-friendly preference to a concrete model name.

    Priority order:
    1. preference parameter (explicit override)
    2. Environment variables (VERTEX_MODEL, LLM_MODEL, GEMINI_MODEL)
    3. app_config.py models configuration for specific operation
    4. Fallback to gemini-2.5-flash

    Args:
        preference: 'gemini' | 'llama' | explicit model string (highest priority)
        operation: Operation type for model selection (e.g., 'intent_parsing', 'audio_analysis')

    Returns:
        Concrete Vertex model name (e.g., 'gemini-2.5-flash-lite')
    """
    # Explicit preference takes precedence (highest priority)
    if preference:
        pref = preference.lower()
        # Map generic preferences to env vars
        if pref in ("gemini", "gemini-flash", "flash"):
            # Generic "gemini" preference - check env vars
            model = (
                os.getenv("VERTEX_MODEL")
                or os.getenv("LLM_MODEL")
                or os.getenv("GEMINI_MODEL")
            )
            if not model:
                raise ValueError("VERTEX_MODEL, LLM_MODEL, or GEMINI_MODEL environment variable must be set")
            return model
        if pref in ("llama", "llama-8b"):
            # Generic "llama" preference - check env vars
            return os.getenv("LLAMA_MODEL", "meta-llama/Llama-3.1-8B-Instruct")
        # Already a concrete model name (e.g., "gemini-2.5-flash-lite", "meta-llama/...")
        return preference

    # Check app_config for operation-specific model (second priority - respects your config!)
    try:
        from server.config.app_config import get_model_for_operation
        model = get_model_for_operation(operation)
        if model:
            return model
    except Exception:
        pass  # Config not available (e.g., running from nlp-service standalone)

    # Check environment variables (third priority - global override)
    env_model = os.getenv("VERTEX_MODEL") or os.getenv("LLM_MODEL") or os.getenv("GEMINI_MODEL")
    if env_model:
        return env_model

    # Fallback to default (last resort)
    default_pref = os.getenv("LLM_MODEL_PREFERENCE", "gemini-2.5-flash")
    return default_pref


def get_llama_http_config() -> dict:
    """Return OpenAI-compatible HTTP endpoint config for Llama (optional)."""
    return {
        "endpoint": os.getenv("LLAMA_ENDPOINT"),
        "api_key": os.getenv("LLAMA_API_KEY"),
        "model": os.getenv("LLAMA_MODEL", "meta-llama/Llama-3.1-8B-Instruct"),
    }
