# Fadebender Installer Guide

This guide describes how to create installers for Fadebender that properly set up configuration files and detect Ableton Live.

## Installation Steps

### 1. Detect Ableton Live Location

Use `server.config.paths.find_live_library()` or scan these paths:

#### macOS
```
/Applications/Ableton Live [VERSION] [EDITION].app/Contents/App-Resources/Core Library/
```

Versions to check: 12, 11, 10
Editions to check: Suite, Standard, Intro

#### Windows
```
C:\ProgramData\Ableton\Live [VERSION] [EDITION]\Resources\Core Library\
```

#### Validation
Check that `<Core Library>/Devices/` exists to confirm valid Live installation.

### 2. Build Device Map

Run the device map builder script:

```bash
python scripts/build_device_map.py --live-library "/path/to/Core Library" --output device_map.json
```

This scans Live's Devices folder and generates a complete mapping.

### 3. Create Config Directory

Create platform-specific config directory:

| Platform | Config Directory |
|----------|------------------|
| macOS | `~/.fadebender/` (legacy) or `~/Library/Application Support/Fadebender/` |
| Windows | `%APPDATA%\Fadebender\` |
| Linux | `~/.config/fadebender/` |

Use `server.config.paths.get_config_dir()` to get the correct path.

### 4. Install Device Map

Copy the generated `device_map.json` to:
- Remote Script: `~/.fadebender/device_map.json` (all platforms - hardcoded in Remote Script)
- Server: Use `server.config.paths.get_device_map_path()` (may be same as above)

**Important**: The Remote Script runs inside Live's Python interpreter and expects the file at `~/.fadebender/device_map.json` specifically. Even on macOS, use this path (not `~/Library/Application Support/`).

### 5. Install Remote Script

Copy `ableton_remote/Fadebender/` to Live's Remote Scripts directory:

| Platform | Remote Scripts Directory |
|----------|--------------------------|
| macOS | `~/Music/Ableton/User Library/Remote Scripts/` |
| Windows | `%USERPROFILE%\Documents\Ableton\User Library\Remote Scripts\` |
| Linux | `~/Music/Ableton/User Library/Remote Scripts/` |

## Configuration Files

### device_map.json Structure

```json
{
  "Reverb": {
    "path": ["audio_effects", "Reverb"],
    "type": "audio_effects",
    "presets": {
      "Cathedral": ["audio_effects", "Reverb", "Hall", "Cathedral.adv"],
      "Chamber": ["audio_effects", "Reverb", "Hall", "Chamber.adv"]
    }
  },
  "Compressor": {
    "path": ["audio_effects", "Compressor"],
    "type": "audio_effects",
    "presets": {
      "Gentle": ["audio_effects", "Compressor", "Gentle.adv"]
    }
  }
}
```

**Path format**:
- First element is device type: `audio_effects`, `midi_effects`, or `instruments`
- Remaining elements are folder/file names in Live's Browser hierarchy
- Preset paths include the full path from device type to preset file

### App Configuration

The server looks for config files in:
- `server.config.paths.get_config_dir()` - config files
- `server.config.paths.get_app_data_dir()` - application data (logs, databases)
- `server.config.paths.get_cache_dir()` - temporary cache files

## Development vs Production

### Development
- Set `FADEBENDER_CONFIG_DIR` environment variable to override config directory
- Allows testing without modifying user's actual config

### Production
- Remove `FADEBENDER_CONFIG_DIR` (or set to empty)
- Use platform-specific standard directories
- Device map builder runs automatically or prompts user for Live location

## Installer Checklist

- [ ] Detect Ableton Live installation(s)
- [ ] Offer version/edition selection if multiple found
- [ ] Build device_map.json from selected Live library
- [ ] Create config directory
- [ ] Copy device_map.json to `~/.fadebender/`
- [ ] Copy Remote Script to Live's Remote Scripts directory
- [ ] (Optional) Add server to system startup
- [ ] (Optional) Create desktop shortcut for WebUI

## Update Strategy

When user upgrades Ableton Live:

1. Detect new Live version
2. Re-run device map builder with new library path
3. Merge with existing device_map.json (preserve user customizations)
4. Prompt user to restart Live to load updated Remote Script

## User Customization

Users can manually edit `~/.fadebender/device_map.json` to:
- Add third-party devices
- Add custom presets
- Change default device paths
- Add aliases for devices

The builder script supports `--output` to avoid overwriting user customizations.
