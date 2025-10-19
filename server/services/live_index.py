from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, List, Optional

from server.services.ableton_client import request_op


def _norm_name(s: str) -> str:
    import re as _re
    s0 = (s or "").strip().lower()
    s0 = _re.sub(r"\blo\b", "low", s0)
    s0 = _re.sub(r"\bhi\b", "high", s0)
    s0 = _re.sub(r"[^a-z0-9]", "", s0)
    return s0


class LiveIndex:
    """Lightweight index of tracks/returns/master devices + last refresh times.

    In-memory only; refreshed on a timer and opportunistically by API flows.
    """

    def __init__(self) -> None:
        self._tracks: Dict[int, Dict[str, Any]] = {}
        self._returns: Dict[int, Dict[str, Any]] = {}
        self._last_full_refresh: float = 0.0
        self._lock = asyncio.Lock()

    # --------- Query helpers ---------
    def get_return_devices_cached(self, ri: int) -> List[Dict[str, Any]]:
        return list((self._returns.get(int(ri)) or {}).get("devices") or [])

    def get_track_devices_cached(self, ti: int) -> List[Dict[str, Any]]:
        return list((self._tracks.get(int(ti)) or {}).get("devices") or [])

    # --------- Refresh helpers ---------
    async def refresh_return(self, ri: int) -> None:
        try:
            resp = request_op("get_return_devices", timeout=1.0, return_index=int(ri)) or {}
            devs = ((resp.get("data") or resp) if isinstance(resp, dict) else resp).get("devices", [])
            items = []
            for d in devs:
                name = str(d.get("name", ""))
                items.append({
                    "index": int(d.get("index", 0)),
                    "name": name,
                    "nname": _norm_name(name),
                })
            self._returns[int(ri)] = {"devices": items, "ts": time.time()}
        except Exception:
            pass

    async def refresh_track(self, ti: int) -> None:
        try:
            resp = request_op("get_track_devices", timeout=1.0, track_index=int(ti)) or {}
            devs = ((resp.get("data") or resp) if isinstance(resp, dict) else resp).get("devices", [])
            items = []
            for d in devs:
                name = str(d.get("name", ""))
                items.append({
                    "index": int(d.get("index", 0)),
                    "name": name,
                    "nname": _norm_name(name),
                })
            self._tracks[int(ti)] = {"devices": items, "ts": time.time()}
        except Exception:
            pass

    async def refresh_all(self) -> None:
        async with self._lock:
            try:
                ov = request_op("get_overview", timeout=1.0) or {}
                data = (ov.get("data") or ov) if isinstance(ov, dict) else ov
                tracks = data.get("tracks") or []
                for t in tracks:
                    await self.refresh_track(int(t.get("index", 0)))
            except Exception:
                pass
            try:
                rs = request_op("get_return_tracks", timeout=1.0) or {}
                rdata = (rs.get("data") or rs) if isinstance(rs, dict) else rs
                returns = rdata.get("returns") or []
                for r in returns:
                    await self.refresh_return(int(r.get("index", 0)))
            except Exception:
                pass
            self._last_full_refresh = time.time()

    # --------- Background loop ---------
    async def loop(self, interval_sec: float = 60.0) -> None:
        while True:
            try:
                await self.refresh_all()
            except Exception:
                pass
            await asyncio.sleep(interval_sec)

