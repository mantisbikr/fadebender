from __future__ import annotations

from typing import Any, Dict, List

from server.core.deps import get_store
from server.services.mapping_utils import make_device_signature, detect_device_type
from server.services.preset_enricher import generate_preset_metadata_llm


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
        # Build values map
        values: Dict[str, float] = {}
        for p in params:
            try:
                values[str(p.get("name", ""))] = float(p.get("value", 0.0))
            except Exception:
                continue

        preset_id = f"{device_type}_{device_name.lower().replace(' ', '_')}"
        existing = store.get_preset(preset_id)
        if existing and isinstance(existing.get("values"), dict) and len(existing.get("values") or {}) >= 3:
            return
        metadata = await generate_preset_metadata_llm(device_name, device_type, values)
        preset_data = {
            "id": preset_id,
            "device_signature": structure_signature,
            "device_type": device_type,
            "device_name": device_name,
            "values": values,
            "metadata": metadata,
        }
        store.save_preset(preset_id, preset_data, local_only=False)
    except Exception:
        return


async def save_base_preset(
    return_index: int,
    device_index: int,
    device_name: str,
    device_type: str,
    structure_signature: str,
    params: list[Dict[str, Any]],
) -> None:
    """Save a minimal preset (values + display) without LLM metadata.

    Idempotent: if a preset with parameter_values exists with >= 3 entries,
    it will not overwrite unless fields are missing.
    """
    try:
        store = get_store()
        # Build values and display maps
        values: Dict[str, float] = {}
        displays: Dict[str, str] = {}
        for p in params:
            nm = p.get("name")
            if nm is None:
                continue
            if p.get("value") is not None:
                try:
                    values[str(nm)] = float(p.get("value"))
                except Exception:
                    pass
            if p.get("display_value") is not None:
                try:
                    displays[str(nm)] = str(p.get("display_value"))
                except Exception:
                    pass
        preset_id = f"{device_type}_{device_name.lower().replace(' ', '_')}"
        existing = store.get_preset(preset_id) or {}
        existing_values = dict(existing.get("parameter_values") or {})
        if existing_values and len(existing_values) >= 3:
            # Ensure display map is present
            if displays and not existing.get("parameter_display_values"):
                existing["parameter_display_values"] = displays
                store.save_preset(preset_id, existing, local_only=False)
            return
        preset_data = {
            "id": preset_id,
            "structure_signature": structure_signature,
            "category": device_type,
            "device_name": device_name,
            "parameter_values": values,
            "parameter_display_values": displays,
        }
        store.save_preset(preset_id, preset_data, local_only=False)
    except Exception:
        return
