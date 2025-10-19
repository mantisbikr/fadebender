from __future__ import annotations

import time
from typing import Any, Dict, Optional


class ValueRegistry:
    """Lightweight, in-memory registry of last-known mixer and device param values.

    - Mixer values stored per entity (track/return/master)
    - Device params stored per domain (track/return) → index → device_index → param_name
    - Stores both normalized values and display strings when known, plus unit and source
    """

    def __init__(self) -> None:
        self._mixer: Dict[str, Dict[int, Dict[str, Any]]] = {"track": {}, "return": {}, "master": {}}
        self._device: Dict[str, Dict[int, Dict[int, Dict[str, Dict[str, Any]]]]] = {"track": {}, "return": {}}

    # ---------- Mixer ----------
    def update_mixer(self, entity: str, index: int, field: str, normalized_value: Optional[float], display_value: Optional[str], unit: Optional[str], source: str = "op") -> None:
        entity = entity.lower()
        if entity not in ("track", "return", "master"):
            return
        idx = int(index)
        ent = self._mixer.setdefault(entity, {})
        row = ent.setdefault(idx, {})
        row[str(field)] = {
            "normalized": normalized_value,
            "display": display_value,
            "unit": unit,
            "ts": time.time(),
            "source": source,
        }

    # ---------- Device params ----------
    def update_device_param(self, domain: str, index: int, device_index: int, param_name: str, normalized_value: Optional[float], display_value: Optional[str], unit: Optional[str], source: str = "op") -> None:
        d = domain.lower()
        if d not in ("track", "return"):
            return
        idx = int(index)
        di = int(device_index)
        dom = self._device.setdefault(d, {})
        ent = dom.setdefault(idx, {})
        dev = ent.setdefault(di, {})
        dev[str(param_name)] = {
            "normalized": normalized_value,
            "display": display_value,
            "unit": unit,
            "ts": time.time(),
            "source": source,
        }

    # ---------- Snapshots ----------
    def get_mixer(self) -> Dict[str, Any]:
        return self._mixer

    def get_devices(self) -> Dict[str, Any]:
        return self._device

