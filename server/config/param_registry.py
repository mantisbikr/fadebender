from __future__ import annotations

from typing import Any, Dict

# Delegate to shared package implementation to avoid duplication
from fadebender_lom.registry import get_param_registry as _get, reload_param_registry as _reload


def get_param_registry() -> Dict[str, Any]:
    return _get()


def reload_param_registry() -> Dict[str, Any]:
    return _reload()
