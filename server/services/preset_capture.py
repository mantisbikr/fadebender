from __future__ import annotations

import asyncio
import os
import time
from typing import Any, Dict, List

from server.core.deps import get_store
from server.core.events import broker
from server.services.ableton_client import request_op
from server.services.preset_metadata import generate_preset_metadata_llm

_CAPTURE_DEDUPE: Dict[str, float] = {}


def should_capture_signature(sig: str, ttl_sec: float = 60.0) -> bool:
    try:
        now = time.time()
        last = _CAPTURE_DEDUPE.get(sig)
        if last is not None and (now - last) < ttl_sec:
            return False
        _CAPTURE_DEDUPE[sig] = now
        return True
    except Exception:
        return True


async def ensure_device_mapping(device_signature: str, device_type: str, params: List[Dict[str, Any]]) -> None:
    try:
        if not params or len(params) < 5:
            return
        store = get_store()
        mapping = store.get_device_mapping(device_signature)
        if mapping:
            return
        params_meta = []
        for p in params:
            params_meta.append(
                {
                    "index": p.get("index"),
                    "name": p.get("name"),
                    "min": p.get("min", 0.0),
                    "max": p.get("max", 1.0),
                    "control_type": None,
                    "unit": None,
                    "min_display": None,
                    "max_display": None,
                }
            )
        mapping_data = {
            "device_signature": device_signature,
            "device_type": device_type,
            "params_meta": params_meta,
            "param_count": len(params_meta),
            "created_at": int(time.time()),
            "updated_at": int(time.time()),
            "metadata_status": "pending_analysis",
        }
        store.save_device_mapping(device_signature, mapping_data)
    except Exception:
        return


async def auto_capture_preset(
    return_index: int,
    device_index: int,
    device_name: str,
    device_type: str,
    structure_signature: str,
    params: List[Dict[str, Any]],
) -> None:
    try:
        store = get_store()
        preset_id = f"{device_type}_{device_name.lower().replace(' ', '_')}"
        existing = store.get_preset(preset_id)
        if existing:
            values = existing.get("parameter_values") or {}
            try:
                store.save_preset(preset_id, existing, local_only=False)
            except Exception:
                pass
            if isinstance(values, dict) and len(values) >= 5:
                return

        parameter_values: Dict[str, float] = {}
        parameter_display_values: Dict[str, str] = {}
        for p in params:
            name = p.get("name")
            if not name:
                continue
            if p.get("value") is not None:
                try:
                    parameter_values[str(name)] = float(p.get("value"))
                except Exception:
                    pass
            if p.get("display_value") is not None:
                parameter_display_values[str(name)] = str(p.get("display_value"))

        fast_path = str(os.getenv("SKIP_LOCAL_METADATA_GENERATION", "")).lower() in ("1", "true", "yes", "on")
        if fast_path:
            metadata: Dict[str, Any] = {"metadata_status": "pending_enrichment"}
        else:
            metadata = await generate_preset_metadata_llm(
                device_name=device_name,
                device_type=device_type,
                parameter_values=parameter_values,
                store=store,
            )

        preset_data: Dict[str, Any] = {
            "name": device_name,
            "device_name": device_name.split()[0] if " " in device_name else device_name,
            "manufacturer": "Ableton",
            "daw": "Ableton Live",
            "structure_signature": structure_signature,
            "device_signature": structure_signature,
            "category": device_type,
            "preset_type": "stock",
            "parameter_values": parameter_values,
            "parameter_display_values": parameter_display_values,
            "values_status": "ok" if len(parameter_values) >= 5 else "pending",
            "metadata_status": "captured",
            "captured_at": int(time.time()),
            "updated_at": int(time.time()),
            **metadata,
        }

        await ensure_device_mapping(structure_signature, device_type, params)

        saved = store.save_preset(preset_id, preset_data, local_only=False)
        if saved:
            try:
                await broker.publish(
                    {
                        "event": "preset_captured",
                        "return": return_index,
                        "device": device_index,
                        "preset_id": preset_id,
                        "device_type": device_type,
                        "device_name": device_name,
                        "signature": structure_signature,
                    }
                )
            except Exception:
                pass
            try:
                asyncio.create_task(
                    verify_and_retry_preset(
                        preset_id,
                        return_index=return_index,
                        device_index=device_index,
                    )
                )
            except Exception:
                pass
    except Exception:
        return


async def verify_and_retry_preset(
    preset_id: str,
    *,
    return_index: int,
    device_index: int,
    min_params: int = 5,
    max_retries: int = 3,
    attempt: int = 0,
) -> None:
    try:
        store = get_store()
        preset = store.get_preset(preset_id) or {}
        count = len((preset.get("parameter_values") or {}))
        if count >= min_params:
            try:
                await broker.publish(
                    {
                        "event": "preset_verified",
                        "preset_id": preset_id,
                        "values_ok": True,
                        "count": count,
                    }
                )
            except Exception:
                pass
            return

        if attempt >= max_retries:
            try:
                await broker.publish(
                    {
                        "event": "preset_verify_failed",
                        "preset_id": preset_id,
                        "values_ok": False,
                        "count": count,
                    }
                )
            except Exception:
                pass
            return

        backoffs = [1.0, 3.0, 10.0]
        delay = backoffs[min(attempt, len(backoffs) - 1)]
        await asyncio.sleep(delay)

        resp = request_op(
            "get_return_device_params",
            timeout=1.2,
            return_index=int(return_index),
            device_index=int(device_index),
        )
        params = ((resp or {}).get("data") or resp or {}).get("params") or []
        live_vals: Dict[str, float] = {}
        live_disp: Dict[str, str] = {}
        for p in params:
            name = p.get("name")
            if name is None:
                continue
            if p.get("value") is not None:
                try:
                    live_vals[str(name)] = float(p.get("value"))
                except Exception:
                    pass
            if p.get("display_value") is not None:
                live_disp[str(name)] = str(p.get("display_value"))

        if live_vals:
            preset["parameter_values"] = live_vals
            preset["values_status"] = "ok" if len(live_vals) >= min_params else "pending"
            preset["updated_at"] = int(time.time())
            if live_disp:
                preset["parameter_display_values"] = live_disp
            store.save_preset(preset_id, preset, local_only=False)

        try:
            await broker.publish(
                {
                    "event": "preset_retry",
                    "preset_id": preset_id,
                    "attempt": attempt + 1,
                    "count": len(live_vals),
                }
            )
        except Exception:
            pass

        await verify_and_retry_preset(
            preset_id,
            return_index=return_index,
            device_index=device_index,
            min_params=min_params,
            max_retries=max_retries,
            attempt=attempt + 1,
        )
    except Exception:
        return
