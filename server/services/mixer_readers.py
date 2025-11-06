from __future__ import annotations

from typing import Any, Dict

from server.services.ableton_client import request_op, data_or_raw


def read_track_status(index: int) -> Dict[str, Any]:
    resp = request_op("get_track_status", timeout=1.0, track_index=int(index))
    return data_or_raw(resp) if resp else {}


def read_track_sends(index: int) -> Dict[str, Any]:
    resp = request_op("get_track_sends", timeout=1.0, track_index=int(index))
    return data_or_raw(resp) if resp else {}


def read_return_sends(index: int) -> Dict[str, Any]:
    resp = request_op("get_return_sends", timeout=1.0, return_index=int(index))
    return data_or_raw(resp) if resp else {}


def read_return_routing(index: int) -> Dict[str, Any]:
    resp = request_op("get_return_routing", timeout=1.0, return_index=int(index))
    return data_or_raw(resp) if resp else {}

