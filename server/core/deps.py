from __future__ import annotations

from typing import Optional

from server.services.mapping_store import MappingStore


_STORE: Optional[MappingStore] = None


def set_store_instance(store: MappingStore) -> None:
    global _STORE
    _STORE = store


def get_store() -> MappingStore:
    global _STORE
    if _STORE is None:
        _STORE = MappingStore()
    return _STORE

