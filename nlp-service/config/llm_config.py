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


def get_default_model_name(preference: str | None = None) -> str:
    """
    Map a human-friendly preference to a concrete model name.

    preference: 'gemini' | 'llama' | explicit model string
    returns: concrete Vertex model name
    """
    if not preference:
        preference = os.getenv("LLM_MODEL_PREFERENCE", "gemini-2.5-flash").lower()
    pref = preference.lower()
    if pref in ("gemini", "gemini-flash", "flash", "gemini-2.5-flash"):
        # Check multiple env var names for model selection
        model = (
            os.getenv("VERTEX_MODEL")
            or os.getenv("LLM_MODEL")
            or os.getenv("GEMINI_MODEL")
        )
        if not model:
            raise ValueError("VERTEX_MODEL, LLM_MODEL, or GEMINI_MODEL environment variable must be set")
        return model
    if pref in ("llama", "llama-8b", "llama-3.1-8b-instruct", "llama-8b-mass"):
        # Name used for non-Vertex llama endpoints; caller can use LLAMA_* env
        return os.getenv("LLAMA_MODEL", "meta-llama/Llama-3.1-8B-Instruct")
    # Already a concrete model name
    return preference


def get_llama_http_config() -> dict:
    """Return OpenAI-compatible HTTP endpoint config for Llama (optional)."""
    return {
        "endpoint": os.getenv("LLAMA_ENDPOINT"),
        "api_key": os.getenv("LLAMA_API_KEY"),
        "model": os.getenv("LLAMA_MODEL", "meta-llama/Llama-3.1-8B-Instruct"),
    }
