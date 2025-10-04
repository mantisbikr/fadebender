Debug Controls (Server)

You can toggle verbose debug logging without code edits. Debug flags live in configs/app_config.json under the debug section and can also be overridden with environment variables.

Available flags
- firestore
  - Purpose: Show Firestore mapping store reads (device_mappings and params).
  - Config key: debug.firestore (true|false)
  - Env override: FB_DEBUG_FIRESTORE=1

- sse
  - Purpose: Log each SSE emit (event name + minimal payload) from the server.
  - Config key: debug.sse (true|false)
  - Env override: FB_DEBUG_SSE=1

- auto_capture
  - Purpose: Verbose logs for auto‑capture preset flow.
  - Config key: debug.auto_capture (true|false)
  - Env override: FB_DEBUG_AUTO_CAPTURE=1

How to view/update
- Read current config:
  - GET /config

- Update flags (example enables firestore + sse):
  - POST /config/update
    Body:
    {
      "debug": { "firestore": true, "sse": true }
    }

- Reload from disk (configs/app_config.json):
  - POST /config/reload

Edit config file directly
- File: configs/app_config.json
- Example:
  {
    "debug": {
      "firestore": false,
      "sse": true,
      "auto_capture": false
    }
  }

Environment variable overrides (highest priority)
- FB_DEBUG_FIRESTORE=1
- FB_DEBUG_SSE=1
- FB_DEBUG_AUTO_CAPTURE=1

Notes
- Flags can be toggled at runtime via /config/update; no server restart required.
- Env variables apply at process start and override the config file.

