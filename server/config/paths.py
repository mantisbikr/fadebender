"""
Fadebender path configuration.

Provides platform-agnostic paths for config, data, and cache directories.
Designed to work in development and production environments.
"""

import os
import platform
from pathlib import Path
from typing import Optional


def get_platform() -> str:
    """Get normalized platform name."""
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    elif system == "windows":
        return "windows"
    else:
        return "linux"


def get_app_data_dir() -> Path:
    """
    Get platform-specific application data directory.

    Returns:
        macOS: ~/Library/Application Support/Fadebender
        Windows: %APPDATA%\Fadebender
        Linux: ~/.local/share/fadebender
    """
    plat = get_platform()

    if plat == "macos":
        base = Path.home() / "Library" / "Application Support" / "Fadebender"
    elif plat == "windows":
        appdata = os.getenv("APPDATA")
        if appdata:
            base = Path(appdata) / "Fadebender"
        else:
            base = Path.home() / "AppData" / "Roaming" / "Fadebender"
    else:  # linux
        xdg_data = os.getenv("XDG_DATA_HOME")
        if xdg_data:
            base = Path(xdg_data) / "fadebender"
        else:
            base = Path.home() / ".local" / "share" / "fadebender"

    base.mkdir(parents=True, exist_ok=True)
    return base


def get_config_dir() -> Path:
    """
    Get platform-specific configuration directory.

    Returns:
        macOS: ~/.fadebender (for backward compat) or ~/Library/Application Support/Fadebender
        Windows: %APPDATA%\Fadebender
        Linux: ~/.config/fadebender
    """
    plat = get_platform()

    if plat == "macos":
        # Check for legacy ~/.fadebender first
        legacy = Path.home() / ".fadebender"
        if legacy.exists():
            return legacy
        # Use app data dir for new installs
        return get_app_data_dir()
    elif plat == "windows":
        return get_app_data_dir()
    else:  # linux
        xdg_config = os.getenv("XDG_CONFIG_HOME")
        if xdg_config:
            base = Path(xdg_config) / "fadebender"
        else:
            base = Path.home() / ".config" / "fadebender"
        base.mkdir(parents=True, exist_ok=True)
        return base


def get_cache_dir() -> Path:
    """
    Get platform-specific cache directory.

    Returns:
        macOS: ~/Library/Caches/Fadebender
        Windows: %LOCALAPPDATA%\Fadebender\Cache
        Linux: ~/.cache/fadebender
    """
    plat = get_platform()

    if plat == "macos":
        base = Path.home() / "Library" / "Caches" / "Fadebender"
    elif plat == "windows":
        localappdata = os.getenv("LOCALAPPDATA")
        if localappdata:
            base = Path(localappdata) / "Fadebender" / "Cache"
        else:
            base = Path.home() / "AppData" / "Local" / "Fadebender" / "Cache"
    else:  # linux
        xdg_cache = os.getenv("XDG_CACHE_HOME")
        if xdg_cache:
            base = Path(xdg_cache) / "fadebender"
        else:
            base = Path.home() / ".cache" / "fadebender"

    base.mkdir(parents=True, exist_ok=True)
    return base


def get_device_map_path() -> Path:
    """
    Get path to device_map.json.

    Returns path to device_map.json in config directory.
    Creates parent directories if needed.
    """
    config_dir = get_config_dir()
    return config_dir / "device_map.json"


def get_live_library_paths() -> list[Path]:
    """
    Get potential Ableton Live library paths for this platform.

    Returns list of paths to check, in priority order.
    Installer should scan these and find the first valid one.
    """
    plat = get_platform()
    paths = []

    if plat == "macos":
        # Common macOS locations
        apps = Path("/Applications")
        for version in ["12", "11", "10"]:
            for edition in ["Suite", "Standard", "Intro"]:
                p = apps / f"Ableton Live {version} {edition}.app" / "Contents" / "App-Resources" / "Core Library"
                paths.append(p)

    elif plat == "windows":
        # Common Windows locations
        programdata = Path(os.getenv("PROGRAMDATA", "C:\\ProgramData"))
        for version in ["12", "11", "10"]:
            for edition in ["Suite", "Standard", "Intro"]:
                p = programdata / "Ableton" / f"Live {version} {edition}" / "Resources" / "Core Library"
                paths.append(p)

    # User libraries (both platforms)
    user_home = Path.home()
    if plat == "macos":
        user_lib = user_home / "Music" / "Ableton" / "User Library"
    else:
        user_lib = user_home / "Documents" / "Ableton" / "User Library"
    paths.append(user_lib)

    return paths


def find_live_library() -> Optional[Path]:
    """
    Find first valid Ableton Live library on this system.

    Returns:
        Path to Core Library if found, None otherwise.
    """
    for path in get_live_library_paths():
        if path.exists() and path.is_dir():
            # Check for Devices subfolder as validation
            devices = path / "Devices"
            if devices.exists():
                return path
    return None


# Development override - check for FADEBENDER_CONFIG_DIR env var
_override = os.getenv("FADEBENDER_CONFIG_DIR")
if _override:
    _OVERRIDE_CONFIG_DIR = Path(_override)

    def get_config_dir() -> Path:  # type: ignore
        _OVERRIDE_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        return _OVERRIDE_CONFIG_DIR
