from __future__ import annotations

from typing import Any, Dict, Optional


def build_capabilities_ref(*, domain: str,
                           track_index: Optional[int] = None,
                           return_index: Optional[int] = None,
                           device_index: Optional[int] = None) -> Dict[str, Any]:
    """Build a lightweight capabilities reference for deferred loading.

    Instead of fetching full capabilities immediately (blocking on Firestore),
    return metadata that allows the client to fetch capabilities on demand.

    Args:
        domain: One of "track", "return", "master", "track_device", "return_device".
        track_index: Track index when domain involves tracks.
        return_index: Return index when domain involves returns.
        device_index: Device index when domain involves devices.

    Returns:
        Dict with available=True and necessary indices for later fetch.
    """
    ref = {"available": True, "domain": domain}

    if track_index is not None:
        ref["track_index"] = int(track_index)
    if return_index is not None:
        ref["return_index"] = int(return_index)
    if device_index is not None:
        ref["device_index"] = int(device_index)

    return ref


def ensure_capabilities(resp: Dict[str, Any], *, domain: str,
                        track_index: Optional[int] = None,
                        return_index: Optional[int] = None,
                        device_index: Optional[int] = None) -> Dict[str, Any]:
    """Attach capabilities to a response if missing so UI can render cards.

    Args:
        resp: Response dict from an execute/read handler.
        domain: One of "track", "return", "master", "return_device".
        track_index: 1-based track index when domain==track.
        return_index: 0-based return index when domain==return or return_device.
        device_index: Device index when domain==return_device.
    """
    if not isinstance(resp, dict):
        return resp
    data = resp.setdefault("data", {}) if isinstance(resp, dict) else {}
    if isinstance(data, dict) and data.get("capabilities"):
        return resp
    try:
        caps = None
        if domain == "track" and track_index is not None:
            from server.api.tracks import get_track_mixer_capabilities  # type: ignore
            # Historical quirk: callers often pass 1-based; tracks.get_* accepts same
            caps = get_track_mixer_capabilities(index=max(0, int(track_index) - 1))
        elif domain == "return" and return_index is not None:
            from server.api.returns import get_return_mixer_capabilities  # type: ignore
            caps = get_return_mixer_capabilities(index=int(return_index))
        elif domain == "master":
            from server.api.master import get_master_mixer_capabilities  # type: ignore
            caps = get_master_mixer_capabilities()
        elif domain == "return_device" and return_index is not None and device_index is not None:
            from server.api.returns import get_return_device_capabilities  # type: ignore
            caps = get_return_device_capabilities(index=int(return_index), device=int(device_index))
        if isinstance(caps, dict) and caps.get("ok"):
            if isinstance(data, dict):
                data["capabilities"] = caps.get("data")
    except Exception:
        pass
    return resp

