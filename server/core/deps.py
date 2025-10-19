from __future__ import annotations

from typing import Optional

from server.services.mapping_store import MappingStore
from server.services.live_index import LiveIndex
from server.services.device_resolver import DeviceResolver
from server.services.value_registry import ValueRegistry


_STORE: Optional[MappingStore] = None
_INDEX: Optional[LiveIndex] = None
_RESOLVER: Optional[DeviceResolver] = None
_REGISTRY: Optional[ValueRegistry] = None


def set_store_instance(store: MappingStore) -> None:
    global _STORE
    _STORE = store


def get_store() -> MappingStore:
    global _STORE
    if _STORE is None:
        _STORE = MappingStore()
    return _STORE


def get_live_index() -> LiveIndex:
    global _INDEX
    if _INDEX is None:
        _INDEX = LiveIndex()
    return _INDEX


def get_device_resolver() -> DeviceResolver:
    global _RESOLVER
    if _RESOLVER is None:
        _RESOLVER = DeviceResolver(get_live_index())
    return _RESOLVER


def get_value_registry() -> ValueRegistry:
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = ValueRegistry()
    return _REGISTRY
