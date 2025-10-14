from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

from server.config.app_config import (
    get_ui_settings,
    get_send_aliases,
    set_ui_settings,
    set_send_aliases,
    get_debug_settings,
    set_debug_settings,
    reload_config as cfg_reload,
    save_config as cfg_save,
)
from server.config.param_learn_config import (
    get_param_learn_config,
    set_param_learn_config,
    reload_param_learn_config,
    save_param_learn_config,
)
from server.config.param_registry import (
    get_param_registry,
    reload_param_registry,
)


router = APIRouter()


@router.get("/config")
def app_config() -> Dict[str, Any]:
    """Expose a subset of app config to clients (UI + aliases)."""
    ui = get_ui_settings()
    aliases = get_send_aliases()
    debug = get_debug_settings()
    return {"ok": True, "ui": ui, "aliases": {"sends": aliases}, "debug": debug}


@router.post("/config/update")
def app_config_update(body: Dict[str, Any]) -> Dict[str, Any]:
    ui_in = (body or {}).get("ui") or {}
    aliases_in = ((body or {}).get("aliases") or {}).get("sends") or {}
    debug_in = (body or {}).get("debug") or {}
    ui = set_ui_settings(ui_in) if ui_in else get_ui_settings()
    aliases = set_send_aliases(aliases_in) if aliases_in else get_send_aliases()
    debug = set_debug_settings(debug_in) if debug_in else get_debug_settings()
    saved = cfg_save()
    return {"ok": True, "saved": saved, "ui": ui, "aliases": {"sends": aliases}, "debug": debug}


@router.post("/config/reload")
def app_config_reload() -> Dict[str, Any]:
    cfg = cfg_reload()
    plc = reload_param_learn_config()
    preg = reload_param_registry()
    return {"ok": True, "config": cfg, "param_learn": plc, "param_registry": preg}


@router.get("/param_registry")
def get_param_registry_endpoint() -> Dict[str, Any]:
    """Expose parameter registry for track/sends mappings to clients."""
    try:
        reg = get_param_registry()
        return {"ok": True, "registry": reg}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.get("/param_learn/config")
def get_param_learn_cfg() -> Dict[str, Any]:
    return {"ok": True, "config": get_param_learn_config()}


@router.post("/param_learn/config")
def set_param_learn_cfg(body: Dict[str, Any]) -> Dict[str, Any]:
    cfg = set_param_learn_config(body or {})
    saved = save_param_learn_config()
    return {"ok": True, "saved": saved, "config": cfg}

