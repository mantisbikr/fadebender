# Device Loading Architecture for Fadebender

**Status:** Research Complete - Implementation Pending
**Date:** October 20, 2025
**Priority:** Medium (After current issues resolved)

---

## Overview

This document outlines the architecture for programmatically adding and removing devices to/from Ableton Live tracks using the Live Object Model (LOM) via MIDI Remote Scripts. This approach works on **all Ableton Live editions** (Intro, Standard, Suite) without requiring Max for Live.

## Market Consideration

**Critical:** Requiring Max for Live would limit the market:
- **Intro** (~$99): No Max for Live ✗
- **Standard** (~$449): No Max for Live (requires $99 add-on) ✗
- **Suite** (~$749): Includes Max for Live ✓

**Solution:** Use MIDI Remote Scripts which work on ALL editions.

---

## Device Locations

### Built-in Effects and Presets

**Base Path:**
```
/Applications/Ableton Live 12 Trial.app/Contents/App-Resources/Core Library/Devices/
```

**Structure:**
```
Core Library/Devices/
├── Audio Effects/
│   ├── Reverb/
│   │   ├── Hall/
│   │   │   ├── Cathedral.adv
│   │   │   ├── Church.adv
│   │   │   └── ...
│   │   ├── Room/
│   │   └── Special/
│   ├── Delay/
│   ├── Amp/
│   └── ...
├── MIDI Effects/
└── Instruments/
```

**Key Finding:** Preset files use `.adv` extension (Ableton Device)

---

## Browser API Architecture

### 1. Browser Navigation Structure

The Live API provides browser roots (NOT file paths):

```python
browser.audio_effects   # Built-in Audio Effects
browser.midi_effects    # Built-in MIDI Effects
browser.plugins         # VST/AU plugins
browser.samples         # Samples
browser.places          # User folders, Downloads
browser.packs           # Installed packs
browser.current_project # Current Live project folder
```

### 2. Browser Item Navigation

Items are **BrowserItem objects**, not file path strings:

```python
# Navigate through folders
items = [item for item in parent.iter_children]

# Check properties
if item.is_loadable:
    browser.load_item(item)  # Load the device!

if item.is_folder:
    # Recurse deeper
    sub_items = [sub for sub in item.iter_children]
```

### 3. Key Constraint: NO Direct File Path URIs

**Important:** The browser API does NOT accept file paths like:
```python
# ✗ This doesn't work:
browser.load_item("/Applications/Ableton.../Reverb/Hall/Cathedral.adv")

# ✓ This works:
item = navigate_to(browser, ["audio_effects", "Reverb", "Hall", "Cathedral.adv"])
browser.load_item(item)
```

You must traverse the browser tree to get the BrowserItem object.

---

## Installation & Discovery Strategy

### Automatic Setup - Zero Manual Configuration

**Key Principle:** User downloads installer, runs it, starts Live - everything works automatically.

**Why This Matters:**
- Most users won't know where config files should go
- Manual folder selection creates support burden
- Automatic discovery provides best UX

### Installation Flow

```
User downloads Fadebender.pkg
     ↓
Installer runs:
  ✓ Install remote script to ~/Music/Ableton/User Library/Remote Scripts/Fadebender/
  ✓ Create ~/.fadebender/ directory
  ✓ Copy bundled default_device_map.json (50+ built-in Live devices)
     ↓
User starts Ableton Live
     ↓
Remote script loads automatically
     ↓
Background scan (first launch):
  ✓ Detect user packs (if any)
  ✓ Scan user library devices
  ✓ Append to device_map.json
  ✓ Save updated mapping
     ↓
User opens Fadebender:
  "Ready! 127 devices available"
     ↓
User says: "Add reverb to Return A"
  → Works immediately!
```

**No Manual Steps Required:**
- ✗ No folder selection dialogs
- ✗ No config file editing
- ✗ No "run discovery" button
- ✓ Just install and go!

---

## Proposed Architecture

### Phase 1: Bundled Defaults + Auto-Discovery

**A. Installer Package Contents:**
```
Fadebender-Installer.pkg/
├── Remote Script/
│   ├── Fadebender/
│   │   ├── __init__.py
│   │   ├── Fadebender.py
│   │   ├── lom_ops.py
│   │   ├── udp_bridge.py
│   │   └── default_device_map.json  ← Pre-built mappings for Live built-ins
│
└── Install Script:
    1. Copy Fadebender/ to ~/Music/Ableton/User Library/Remote Scripts/
    2. Create ~/.fadebender/ directory
    3. Copy default_device_map.json to ~/.fadebender/
```

**B. Default Device Map (Bundled):**

Ships with mappings for **all standard Ableton Live 12 devices**:
- Audio Effects: Reverb, Delay, EQ Eight, Compressor, etc. (50+ devices)
- MIDI Effects: Arpeggiator, Chord, Scale, etc. (15+ devices)
- Instruments: Wavetable, Operator, Sampler, etc. (10+ devices)

This is generated once during Fadebender development and included in installer.

**C. First Launch Auto-Discovery:**

In remote script initialization (`Fadebender.py`):

```python
def __init__(self, c_instance):
    super().__init__(c_instance)
    # ... existing initialization ...

    # Auto-discover on first launch
    self._check_and_discover_devices()

def _check_and_discover_devices(self):
    """
    Automatic device discovery on first launch or when new packs detected.
    Runs in background, doesn't block Live startup.
    """
    config_path = os.path.expanduser('~/.fadebender/device_map.json')

    # First time: Copy bundled defaults
    if not os.path.exists(config_path):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        bundled_default = os.path.join(script_dir, 'default_device_map.json')

        # Create config directory if needed
        os.makedirs(os.path.dirname(config_path), exist_ok=True)

        # Copy bundled mapping
        import shutil
        shutil.copy(bundled_default, config_path)

        self.log_message("Fadebender: Installed default device mappings")

    # Schedule background scan for user packs/custom devices
    # Don't block startup - do this after Live is fully loaded
    self.schedule_message(5, self._discover_user_devices)

def _discover_user_devices(self):
    """
    Scan for user packs and custom devices.
    Appends to existing device_map.json (incremental discovery).
    """
    try:
        browser = self.application().browser

        # Load current mapping
        config_path = os.path.expanduser('~/.fadebender/device_map.json')
        with open(config_path, 'r') as f:
            current_mapping = json.load(f)

        # Scan user packs (if any)
        new_devices = self._scan_user_packs(browser)

        # Merge with existing
        if new_devices:
            current_mapping.update(new_devices)

            # Save updated mapping
            with open(config_path, 'w') as f:
                json.dump(current_mapping, f, indent=2)

            self.log_message(f"Fadebender: Discovered {len(new_devices)} additional devices from packs")

    except Exception as e:
        self.log_message(f"Fadebender: Auto-discovery error (non-fatal): {e}")

def _scan_user_packs(self, browser):
    """Scan installed packs for additional devices"""
    # Implementation: scan browser.packs for user-installed content
    # Returns dict of new device mappings
    pass
```

**Purpose:**
- Ships with complete mappings for built-in devices
- Auto-discovers user packs on first launch
- Runs in background (doesn't block Live startup)
- Incremental updates when new packs installed
- User never touches config files

**Discovery Code:**
```python
def discover_all_devices(browser):
    """
    Scan browser and build device mapping.
    Returns dict of device_name -> path info
    """
    devices = {}

    # Scan Audio Effects
    for category in browser.audio_effects.iter_children:
        if category.is_folder:
            devices[category.name] = {
                'type': 'audio_effect',
                'category': category.name,
                'path': ['audio_effects', category.name],
                'presets': scan_presets(category)
            }

    # Scan MIDI Effects
    for category in browser.midi_effects.iter_children:
        if category.is_folder:
            devices[category.name] = {
                'type': 'midi_effect',
                'category': category.name,
                'path': ['midi_effects', category.name],
                'presets': scan_presets(category)
            }

    return devices

def scan_presets(device_folder, path=None, max_depth=5):
    """
    Recursively scan presets within a device folder.
    Returns dict of preset_name -> path
    """
    if path is None:
        path = []

    if len(path) >= max_depth:
        return {}

    presets = {}

    for item in device_folder.iter_children:
        item_path = path + [item.name]

        if item.is_folder:
            # Recurse into subfolder
            presets.update(scan_presets(item, item_path, max_depth))
        elif item.is_loadable:
            # Store preset path (without .adv extension for cleaner names)
            preset_name = item.name.replace('.adv', '').replace('.adg', '')
            presets[preset_name] = item_path

    return presets
```

**Output Format (device_map.json):**
```json
{
  "Reverb": {
    "type": "audio_effect",
    "category": "Reverb",
    "path": ["audio_effects", "Reverb"],
    "presets": {
      "Cathedral": ["audio_effects", "Reverb", "Hall", "Cathedral.adv"],
      "Church": ["audio_effects", "Reverb", "Hall", "Church.adv"],
      "Dark Hall": ["audio_effects", "Reverb", "Hall", "Dark Hall.adv"],
      "Studio": ["audio_effects", "Reverb", "Room", "Studio.adv"]
    }
  },
  "Delay": {
    "type": "audio_effect",
    "category": "Delay",
    "path": ["audio_effects", "Delay"],
    "presets": {
      "1/4": ["audio_effects", "Delay", "Dotted", "1-4.adv"],
      "Ping Pong": ["audio_effects", "Delay", "Stereo", "Ping Pong.adv"]
    }
  },
  "Amp": {
    "type": "audio_effect",
    "category": "Amp",
    "path": ["audio_effects", "Amp"],
    "presets": {
      "Bass Roundup": ["audio_effects", "Amp", "Bass Amp", "Bass Roundup.adv"],
      "Clean": ["audio_effects", "Amp", "Guitar Amp", "Clean.adv"]
    }
  }
}
```

### Phase 2: Runtime Device Loading

In the Fadebender remote script (`lom_ops.py`):

```python
import json
import os

def load_device_mapping():
    """Load the device mapping from user config"""
    config_path = os.path.expanduser('~/.fadebender/device_map.json')
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return json.load(f)
    return {}

def navigate_browser_path(browser, path):
    """
    Navigate to a browser item using a path list.

    Args:
        browser: Live.Application.Browser object
        path: List of folder/item names, e.g., ['audio_effects', 'Reverb', 'Hall', 'Cathedral.adv']

    Returns:
        BrowserItem or None if not found
    """
    # Start at the appropriate root
    if path[0] == 'audio_effects':
        current = browser.audio_effects
    elif path[0] == 'midi_effects':
        current = browser.midi_effects
    elif path[0] == 'plugins':
        current = browser.plugins
    elif path[0] == 'samples':
        current = browser.samples
    else:
        return None

    # Navigate through the rest of the path
    for step in path[1:]:
        items = [item for item in current.iter_children]
        current = next((item for item in items if item.name == step), None)
        if current is None:
            return None

    return current

def load_device_on_return(live, return_index, device_name, preset_name=None):
    """
    Load a device onto a return track.

    Args:
        live: Live application object
        return_index: Return track index (0-based)
        device_name: Name of device (e.g., "Reverb", "Delay")
        preset_name: Optional preset name (e.g., "Cathedral", "Ping Pong")

    Returns:
        Dict with success status and loaded device info
    """
    try:
        browser = live.application.browser
        mapping = load_device_mapping()

        if device_name not in mapping:
            return {"ok": False, "error": f"Device '{device_name}' not found in mapping"}

        device_info = mapping[device_name]

        # Determine path to load
        if preset_name and preset_name in device_info.get('presets', {}):
            # Load specific preset
            path = device_info['presets'][preset_name]
        else:
            # Load default device (first preset or device itself)
            path = device_info['path']

        # Navigate to the item
        item = navigate_browser_path(browser, path)
        if not item:
            return {"ok": False, "error": f"Could not navigate to path: {path}"}

        if not item.is_loadable:
            return {"ok": False, "error": f"Item is not loadable: {item.name}"}

        # Load the device
        browser.load_item(item)

        # Get the newly loaded device
        returns = getattr(live, "return_tracks", [])
        if 0 <= return_index < len(returns):
            devices = getattr(returns[return_index], "devices", [])
            if devices:
                loaded_device = devices[-1]  # Last device is the newly loaded one
                return {
                    "ok": True,
                    "device_name": str(getattr(loaded_device, "name", "")),
                    "device_index": len(devices) - 1
                }

        return {"ok": True, "message": "Device loaded but could not verify"}

    except Exception as e:
        return {"ok": False, "error": str(e)}

def delete_device_from_return(live, return_index, device_index):
    """
    Remove a device from a return track.

    Args:
        live: Live application object
        return_index: Return track index (0-based)
        device_index: Device index to remove (0-based)

    Returns:
        Dict with success status
    """
    try:
        returns = getattr(live, "return_tracks", [])
        if 0 <= return_index < len(returns):
            track = returns[return_index]
            track.delete_device(device_index)
            return {"ok": True, "message": f"Deleted device {device_index} from return {return_index}"}
        else:
            return {"ok": False, "error": f"Return index {return_index} out of range"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# Similar functions for tracks:

def load_device_on_track(live, track_index, device_name, preset_name=None):
    """Load device on regular track (implementation similar to return version)"""
    # TODO: Implement
    pass

def delete_device_from_track(live, track_index, device_index):
    """Remove device from regular track"""
    try:
        tracks = getattr(live, "tracks", [])
        if 0 <= track_index < len(tracks):
            track = tracks[track_index]
            track.delete_device(device_index)
            return {"ok": True, "message": f"Deleted device {device_index} from track {track_index}"}
        else:
            return {"ok": False, "error": f"Track index {track_index} out of range"}
    except Exception as e:
        return {"ok": False, "error": str(e)}
```

### Phase 3: Server API Integration

Add new endpoints to the Fadebender server:

**In `server/api/devices.py` (new file):**
```python
from fastapi import APIRouter, HTTPException
from server.services.ableton_client import request_op

router = APIRouter()

@router.post("/device/load")
def load_device(
    domain: str,  # "track" or "return"
    index: int,
    device_name: str,
    preset_name: str = None
):
    """Load a device onto a track or return"""
    if domain == "return":
        op = "load_device_on_return"
    elif domain == "track":
        op = "load_device_on_track"
    else:
        raise HTTPException(400, "domain must be 'track' or 'return'")

    result = request_op(
        op,
        return_index=index if domain == "return" else None,
        track_index=index if domain == "track" else None,
        device_name=device_name,
        preset_name=preset_name,
        timeout=5.0
    )

    return result or {"ok": False, "error": "no_response"}

@router.delete("/device")
def delete_device(
    domain: str,
    index: int,
    device_index: int
):
    """Remove a device from a track or return"""
    if domain == "return":
        op = "delete_device_from_return"
    elif domain == "track":
        op = "delete_device_from_track"
    else:
        raise HTTPException(400, "domain must be 'track' or 'return'")

    result = request_op(
        op,
        return_index=index if domain == "return" else None,
        track_index=index if domain == "track" else None,
        device_index=device_index,
        timeout=2.0
    )

    return result or {"ok": False, "error": "no_response"}

@router.get("/device/list")
def list_devices():
    """List all available devices from mapping file (optional endpoint)"""
    # This is optional - could be useful for UI autocomplete
    # Reads from ~/.fadebender/device_map.json and returns available devices
    result = request_op("list_available_devices", timeout=2.0)
    return result or {"ok": False, "error": "no_response"}
```

**Note:** Manual discovery endpoint is NOT needed - discovery happens automatically on first launch!

---

## Example Usage

### 1. Initial Setup (Automatic)

**User Experience:**
1. Download Fadebender installer
2. Run installer (one click)
3. Start Ableton Live
4. Fadebender is ready automatically!

**Behind the scenes:**
- Installer copies remote script and default device mappings
- Remote script loads when Live starts
- Background scan discovers user packs (5 seconds after startup)
- User sees: "Fadebender ready! 127 devices available"

**No manual discovery needed!**

### 2. Add a Device

```bash
# Via API
curl -X POST http://localhost:8722/device/load \
  -H "Content-Type: application/json" \
  -d '{"domain":"return","index":0,"device_name":"Reverb","preset_name":"Cathedral"}'

# Via NLP
"Add Cathedral reverb to Return A"
"Load Ping Pong delay on track 3"
```

### 3. Remove a Device

```bash
# Via API
curl -X DELETE http://localhost:8722/device \
  -H "Content-Type: application/json" \
  -d '{"domain":"return","index":0,"device_index":1}'

# Via NLP
"Remove the second device from Return A"
"Delete the delay from track 2"
```

---

## Implementation Checklist

### Pre-Installation (Development Phase)
- [ ] Generate `default_device_map.json` for all Live 12 built-in devices
  - [ ] Run discovery on clean Live 12 Suite installation
  - [ ] Export complete mapping (Audio Effects, MIDI Effects, Instruments)
  - [ ] Save as `default_device_map.json` in remote script folder
- [ ] Create macOS installer package (`.pkg`)
  - [ ] Install remote script to `~/Music/Ableton/User Library/Remote Scripts/Fadebender/`
  - [ ] Create `~/.fadebender/` directory
  - [ ] Copy `default_device_map.json` to user config

### Remote Script (`ableton_remote/Fadebender/Fadebender.py`)
- [ ] Add `_check_and_discover_devices()` to `__init__`
- [ ] Add `_discover_user_devices()` for background scanning
- [ ] Add `_scan_user_packs()` helper

### Remote Script (`ableton_remote/Fadebender/lom_ops.py`)
- [ ] Add `discover_all_devices()` function (for dev-time default generation)
- [ ] Add `scan_presets()` helper
- [ ] Add `navigate_browser_path()` function
- [ ] Add `load_device_mapping()` function
- [ ] Add `load_device_on_return()` function
- [ ] Add `load_device_on_track()` function
- [ ] Add `delete_device_from_return()` function
- [ ] Add `delete_device_from_track()` function
- [ ] Register new operations in UDP bridge

### Server API
- [ ] Create `server/api/devices.py`
- [ ] Add `/device/load` endpoint
- [ ] Add `/device` DELETE endpoint
- [ ] Add `/device/list` endpoint (optional - list available devices)
- [ ] Register router in `server/app.py`

### NLP Integration
- [ ] Add device loading intents to parser
- [ ] Handle "add [device] to [track/return]"
- [ ] Handle "remove [device] from [track/return]"
- [ ] Handle "load [preset] on [track/return]"

### Testing
- [ ] Test device discovery on different Live versions
- [ ] Test loading built-in devices
- [ ] Test loading user devices/packs
- [ ] Test preset loading
- [ ] Test device removal
- [ ] Test error handling (device not found, invalid index, etc.)

---

## Technical References

### Research Sources
- **Carmine Remote Script**: https://github.com/MartinBspheroid/Carmine
  - Shows `.adv` file loading from project browser
- **Push Legacy Scripts**: https://github.com/cylab/_PushLegacy
  - `BrowserComponent.py` shows `TagBrowserQuery` and navigation
- **Live API Docs**: https://nsuspray.github.io/Live_API_Doc/
  - Browser class documentation
  - BrowserItem properties

### Key API Classes
- `Live.Application.Browser` - Main browser interface
- `Live.Browser.BrowserItem` - Individual items in browser
- `Live.Track.Track.delete_device(index)` - Remove device
- `Live.Browser.Browser.load_item(item)` - Load device/preset

---

## Installer Package Creation

### macOS Installer (.pkg)

**Tools:**
- `pkgbuild` - macOS command-line tool for creating packages
- Optional: Packages app (GUI for .pkg creation)

**Structure:**
```bash
# Create package structure
fadebender-installer/
├── payload/                                    # Files to install
│   └── Music/Ableton/User Library/Remote Scripts/Fadebender/
│       ├── __init__.py
│       ├── Fadebender.py
│       ├── lom_ops.py
│       ├── udp_bridge.py
│       └── default_device_map.json           # Pre-built mappings
│
├── scripts/                                   # Install scripts
│   └── postinstall                           # Runs after file copy
│
└── build.sh                                  # Build script
```

**Post-Install Script (`scripts/postinstall`):**
```bash
#!/bin/bash
# Create config directory
mkdir -p "$HOME/.fadebender"

# Copy default device mapping to user config
SCRIPT_DIR="$HOME/Music/Ableton/User Library/Remote Scripts/Fadebender"
if [ -f "$SCRIPT_DIR/default_device_map.json" ]; then
    cp "$SCRIPT_DIR/default_device_map.json" "$HOME/.fadebender/device_map.json"
fi

echo "Fadebender installed successfully"
echo "Please restart Ableton Live for changes to take effect"
exit 0
```

**Build Script (`build.sh`):**
```bash
#!/bin/bash
# Build Fadebender installer package

VERSION="1.0.0"
IDENTIFIER="com.fadebender.remote-script"

# Build the package
pkgbuild \
    --root ./payload \
    --scripts ./scripts \
    --identifier "$IDENTIFIER" \
    --version "$VERSION" \
    --install-location "/" \
    "Fadebender-${VERSION}.pkg"

echo "Package created: Fadebender-${VERSION}.pkg"
```

**To Create Installer:**
```bash
cd installer/
./build.sh
# Output: Fadebender-1.0.0.pkg
```

### Windows Installer (.msi or .exe)

**Tools:**
- Inno Setup (free, popular for Python apps)
- WiX Toolset (MSI creation)

**Install Locations (Windows):**
```
%USERPROFILE%\Documents\Ableton\User Library\Remote Scripts\Fadebender\
%USERPROFILE%\.fadebender\device_map.json
```

---

## Benefits of This Approach

1. **Universal Compatibility**: Works on Intro, Standard, and Suite (no Max for Live needed)
2. **User Consent**: Discovery is explicit, user-triggered action
3. **Fast Runtime**: Pre-mapped paths mean quick device loading
4. **Flexible**: Supports built-in devices, user devices, and packs
5. **Extensible**: Easy to add support for samples, instruments, etc.
6. **AI-Friendly**: Can recommend and auto-load appropriate devices
7. **Production Ready**: "Add reverb to Return A" becomes a one-liner

---

## Future Enhancements

### Smart Recommendations
```python
# AI suggests and auto-loads appropriate device
"I need more warmth on the vocals"
→ Analyzes track
→ Suggests "Amp: Tube Warmth"
→ User confirms
→ Auto-loads device
```

### Preset Management
```python
# Save current device state as preset
"Save this reverb as 'My Cathedral'"
→ Exports current settings
→ Adds to device_map.json
```

### Chain Management
```python
# Load multiple devices in sequence
"Add my vocal chain to track 1"
→ Loads: EQ Eight → Compressor → Reverb
```

---

## Notes

- This architecture was researched on October 20, 2025
- Implementation is pending resolution of current system issues
- Priority: Medium (important feature but not blocking current work)
- Estimated implementation time: 2-3 days for full feature
- No additional user costs (works on all Live editions)
