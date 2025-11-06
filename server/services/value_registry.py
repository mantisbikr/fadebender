"""ValueRegistry service and façade wrappers.

Defines the ValueRegistry class (in-memory last-known state) and provides
simple wrapper functions to update via the global singleton without
introducing import cycles.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


class ValueRegistry:
  """In-memory registry for last-known mixer/device/transport values.

  This mirrors the previous behavior expected throughout the codebase:
  - update_mixer/update_device_param write-through from ops/services
  - get_mixer/get_devices provide data to snapshot/overview APIs
  - update_transport/get_transport track tempo/metronome state
  """

  def __init__(self) -> None:
    self._mixer: Dict[str, Dict[int, Dict[str, Dict[str, Any]]]] = {
      "track": {},
      "return": {},
      "master": {},
    }
    # devices: domain -> index -> device_index -> param_name -> {normalized, display, unit}
    self._devices: Dict[str, Dict[int, Dict[int, Dict[str, Dict[str, Any]]]]] = {
      "track": {},
      "return": {},
    }
    self._transport: Dict[str, Any] = {}

  # --- Mixer ---
  def update_mixer(
    self,
    entity: str,
    index: int,
    field: str,
    *,
    normalized_value: Optional[float] = None,
    display_value: Optional[str] = None,
    unit: Optional[str] = None,
    source: str = "op",
  ) -> None:
    try:
      entity_map = self._mixer.setdefault(str(entity), {})
      fields = entity_map.setdefault(int(index), {})
      fields[str(field)] = {
        "normalized": normalized_value,
        "display": display_value,
        "unit": unit,
        "source": source,
      }
    except Exception:
      pass

  def get_mixer(self) -> Dict[str, Any]:
    return self._mixer

  # --- Devices ---
  def update_device_param(
    self,
    *,
    domain: str,
    index: int,
    device_index: int,
    param_name: str,
    normalized_value: Optional[float] = None,
    display_value: Optional[str] = None,
    unit: Optional[str] = None,
    source: str = "op",
  ) -> None:
    try:
      dom = self._devices.setdefault(str(domain), {})
      devs = dom.setdefault(int(index), {})
      params = devs.setdefault(int(device_index), {})
      params[str(param_name)] = {
        "normalized": normalized_value,
        "display": display_value,
        "unit": unit,
        "source": source,
      }
    except Exception:
      pass

  def get_devices(self) -> Dict[str, Any]:
    return self._devices

  # --- Transport ---
  def update_transport(self, name: str, value: Any, *, source: str = "op") -> None:
    try:
      self._transport[str(name)] = value
    except Exception:
      pass

  def get_transport(self) -> Dict[str, Any]:
    return dict(self._transport)


# --- Façade wrappers (import inside to avoid cycles) ---
def update_mixer(
  entity: str,
  index: int,
  field: str,
  *,
  normalized_value: Optional[float] = None,
  display_value: Optional[str] = None,
  unit: Optional[str] = None,
  source: str = "op",
) -> None:
  try:
    from server.core.deps import get_value_registry  # local import to avoid cycle
    reg = get_value_registry()
    reg.update_mixer(
      entity=entity,
      index=index,
      field=field,
      normalized_value=normalized_value,
      display_value=display_value,
      unit=unit,
      source=source,
    )
  except Exception:
    pass


def update_device_param(
  domain: str,
  index: int,
  device_index: int,
  param_name: str,
  *,
  normalized_value: Optional[float] = None,
  display_value: Optional[str] = None,
  unit: Optional[str] = None,
  source: str = "op",
) -> None:
  try:
    from server.core.deps import get_value_registry  # local import to avoid cycle
    reg = get_value_registry()
    reg.update_device_param(
      domain=domain,
      index=index,
      device_index=device_index,
      param_name=param_name,
      normalized_value=normalized_value,
      display_value=display_value,
      unit=unit,
      source=source,
    )
  except Exception:
    pass
