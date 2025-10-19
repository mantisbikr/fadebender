from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from server.services.live_index import LiveIndex, _norm_name


def _resolve_by_name(devs: List[Dict[str, Any]], name_hint: str) -> List[int]:
    if not name_hint:
        return []
    nh = str(name_hint).strip()
    nhl = nh.lower()
    nhn = _norm_name(nh)
    exact = [int(d["index"]) for d in devs if str(d.get("name", "")).strip().lower() == nhl]
    if exact:
        return exact
    # normalized exact
    ne = [int(d["index"]) for d in devs if str(d.get("nname", "")) == nhn]
    if ne:
        return ne
    # contains
    cont = [int(d["index"]) for d in devs if (nhl in str(d.get("name", "")).lower()) or (nhn in str(d.get("nname", "")))]
    return cont


class DeviceResolver:
    def __init__(self, index: LiveIndex) -> None:
        self.index = index

    def resolve_return(self, *, return_index: int, device_name_hint: Optional[str], device_ordinal_hint: Optional[int]) -> Tuple[int, str, Dict[str, Any]]:
        devs = self.index.get_return_devices_cached(return_index)
        notes: Dict[str, Any] = {"source": "index"}
        if device_name_hint:
            matches = _resolve_by_name(devs, device_name_hint)
            if matches:
                # If ordinal present and valid within matches, honor it; else take first match
                if isinstance(device_ordinal_hint, int) and device_ordinal_hint >= 1 and device_ordinal_hint <= len(matches):
                    di = matches[device_ordinal_hint - 1]
                else:
                    di = matches[0]
                name = next((str(d["name"]) for d in devs if int(d["index"]) == di), str(device_name_hint))
                return di, name, notes
        # Generic ordinal among all devices
        if isinstance(device_ordinal_hint, int) and device_ordinal_hint >= 1 and device_ordinal_hint <= len(devs):
            di = int(devs[device_ordinal_hint - 1]["index"])
            name = str(devs[device_ordinal_hint - 1]["name"])
            return di, name, notes
        # Default to first device when available
        if devs:
            return int(devs[0]["index"]), str(devs[0]["name"]), notes
        # Fallback
        return 0, "Device 0", notes

    def resolve_track(self, *, track_index: int, device_name_hint: Optional[str], device_ordinal_hint: Optional[int]) -> Tuple[int, str, Dict[str, Any]]:
        devs = self.index.get_track_devices_cached(track_index)
        notes: Dict[str, Any] = {"source": "index"}
        if device_name_hint:
            matches = _resolve_by_name(devs, device_name_hint)
            if matches:
                if isinstance(device_ordinal_hint, int) and device_ordinal_hint >= 1 and device_ordinal_hint <= len(matches):
                    di = matches[device_ordinal_hint - 1]
                else:
                    di = matches[0]
                name = next((str(d["name"]) for d in devs if int(d["index"]) == di), str(device_name_hint))
                return di, name, notes
        if isinstance(device_ordinal_hint, int) and device_ordinal_hint >= 1 and device_ordinal_hint <= len(devs):
            di = int(devs[device_ordinal_hint - 1]["index"])
            name = str(devs[device_ordinal_hint - 1]["name"])
            return di, name, notes
        if devs:
            return int(devs[0]["index"]), str(devs[0]["name"]), notes
        return 0, "Device 0", notes

