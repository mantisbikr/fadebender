from __future__ import annotations

from typing import Any, Dict

from server.services.ableton_client import request_op, data_or_raw


def read_track_devices(index: int) -> Dict[str, Any]:
    resp = request_op("get_track_devices", timeout=1.0, track_index=int(index))
    return data_or_raw(resp) if resp else {}


def read_return_devices(index: int) -> Dict[str, Any]:
    resp = request_op("get_return_devices", timeout=1.0, return_index=int(index))
    return data_or_raw(resp) if resp else {}


def read_track_device_params(index: int, device: int) -> Dict[str, Any]:
    resp = request_op("get_track_device_params", timeout=1.0, track_index=int(index), device_index=int(device))
    return data_or_raw(resp) if resp else {}


def read_return_device_params(index: int, device: int) -> Dict[str, Any]:
    resp = request_op("get_return_device_params", timeout=1.0, return_index=int(index), device_index=int(device))
    return data_or_raw(resp) if resp else {}

