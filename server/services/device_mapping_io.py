from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, List, Tuple

from server.core.deps import get_store
from server.services.ableton_client import request_op, data_or_raw
from server.services.mapping_utils import make_device_signature, detect_device_type
from server.services.device_mapping_service import ensure_device_mapping
from server.services.preset_service import save_base_preset


_CAPTURE_DEDUPE: Dict[str, float] = {}


def should_capture(signature: str, ttl_sec: float = 60.0) -> bool:
    now = time.time()
    last = _CAPTURE_DEDUPE.get(signature)
    if last is not None and (now - last) < ttl_sec:
        return False
    _CAPTURE_DEDUPE[signature] = now
    return True


def resolve_return_device_signature(return_index: int, device_index: int) -> Tuple[str, List[Dict[str, Any]], str, str]:
    """Resolve device name/params and compute signature and device_type.

    Returns (device_name, live_params, signature, device_type)
    Raises HTTP-friendly exceptions at router layer if needed.
    """
    devs = request_op("get_return_devices", timeout=1.0, return_index=int(return_index)) or {}
    devices = (data_or_raw(devs) or {}).get("devices") or []
    dname = None
    for d in devices:
        if int(d.get("index", -1)) == int(device_index):
            dname = str(d.get("name", f"Device {device_index}"))
            break
    if dname is None:
        raise ValueError("device_not_found")
    params_resp = request_op("get_return_device_params", timeout=1.2, return_index=int(return_index), device_index=int(device_index)) or {}
    live_params = (data_or_raw(params_resp) or {}).get("params") or []
    signature = make_device_signature(dname, live_params)
    device_type = detect_device_type(live_params, dname)
    return dname, live_params, signature, device_type


def ensure_structure_and_capture(signature: str, device_type: str, return_index: int, device_index: int, device_name: str, live_params: List[Dict[str, Any]]) -> None:
    """Ensure base mapping exists and schedule capture of base preset (idempotent)."""
    try:
        ensure_device_mapping(signature, device_type, live_params)
    except Exception:
        pass
    try:
        if should_capture(signature):
            asyncio.create_task(
                save_base_preset(
                    return_index,
                    device_index,
                    device_name,
                    device_type,
                    signature,
                    live_params,
                )
            )
    except Exception:
        pass


def get_backend() -> str:
    store = get_store()
    return store.backend


def get_mapping(signature: str) -> Dict[str, Any] | None:
    store = get_store()
    return store.get_device_mapping(signature) if store.enabled else None


def get_legacy_map(signature: str) -> Dict[str, Any] | None:
    store = get_store()
    try:
        return store.get_device_map(signature) if store.enabled else store.get_device_map_local(signature)
    except Exception:
        return None

