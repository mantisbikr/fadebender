Fadebender User Guide

Overview
- Fadebender is a chat-first assistant for controlling your DAW (Ableton Live via Remote Script). You can ask for actions (set parameters) or information (get parameters/topology), and it presents context-aware controls in a capabilities drawer.

Quick Start
- Start services (local dev):
  - `make venv` then `make install-nlp`
  - `make run-all3` (starts NLP :8000, Server :8722, Chat :3000)
- Open the web UI at http://127.0.0.1:3000
- Optional: `make status` to verify health (NLP, Server, Chat)

Chat Basics
- Type natural language commands, press Enter to send
- Autocorrect on space/tab: common typos are fixed client-side (e.g., `trac` → `track`), and merged with server typo corrections from `configs/app_config.json`
- Clarification: when the intent is ambiguous, the UI asks a follow‑up question and shows suggested commands
- Help: conceptual questions route to help; operational questions route to control or query flows

Capabilities Drawer
- Auto‑opens with context when you run a command or ask a supported "get" query
- Device drawer: shows grouped device parameters with inline editors
- Mixer drawer: shows mixer parameters for tracks/returns/master (volume, pan, mute, solo, sends)
- Pin to keep it visible; unpin to auto‑close when switching context
 - Type badge: shows AUDIO / MIDI on track contexts and RETURN on return contexts
 - Sidebar clicks no longer auto‑open the drawer; use list chips (see below) or explicit commands

Opening Controls (Navigation)
- Multiple ways to open the capabilities drawer:
  - `open track 1` / `view track 1` → opens mixer controls for Track 1
  - `open return A` / `view return A` → opens mixer controls for Return A
  - `open return A reverb` / `view return A reverb` → opens device controls for reverb on Return A
  - `open track 2 delay` / `view track 2 delay` → opens device controls for delay on Track 2
- Both "open" and "view" work identically for navigation commands

Core Mixer Commands (examples)
- Absolute:
  - `set track 1 volume to -6 dB`
  - `set track 2 pan to 25R` (compact: 25R = +25, 30L = −30)
  - `mute track 3` / `solo track 1`
  - `set track 1 send A to 20%` or `-12 dB`
- Relative:
  - `increase track 1 volume by 3 dB`
  - `decrease track 2 send B by 5%`

Device Control (returns and tracks)
- Return device parameters:
  - `set return A reverb decay to 2 s`
  - `set return B delay feedback to 35%`
  - `what is return A reverb decay?`
- Device ordinal (when multiple of same type):
  - `set return B reverb 2 decay to 1.5 s`

Get Parameter: Values and Topology
- Value reads (multiple ways to ask):
  - `what is track 1 volume?`
  - `show me track 1 volume` / `show track 1 pan`
  - `tell me return A pan` / `tell track 1 volume`
  - `get track 2 volume` / `check track 1 mute`
  - `what's the current tempo?` / `is the metronome on?`
- State bundles (volume, pan, mute, solo + routing summary):
  - `what is track 1 state`
  - `what is return A state`
  - `what is master state`
- Topology:
  - `what are return A devices` → ordered list of devices on Return A
  - `what are track 1 devices` → ordered list of devices on the track
  - `who sends to return A` / `which tracks send to return A` → tracks with non‑zero sends to A
- `what does track 1 send A affect` → lists devices on the destination return
- Drawer behavior: these queries open the relevant mixer/device drawer when possible

Project Overview Queries (counts and lists)
- Counts:
  - `how many audio tracks`
  - `how many midi tracks`
  - `how many return tracks`
  - `track count`
- Lists (response includes clickable chips to open controls):
  - `list audio tracks`
  - `list midi tracks`
  - `list returns`
  - Click a “Track N (Name)” or “Return A (Name)” chip to open its capabilities drawer

Transport
- Reads:
  - `what is the tempo?`
  - `is the click on?`
- Actions (if enabled in your build): play/stop/record/click toggles via the transport bar
 - UI polish:
   - Playhead and loop fields display up to 2 decimal places
   - Compact widths for tempo, time signature, playhead, loop start/length
- After sending an intent, keyboard focus returns to the chat input automatically

Undo/Redo
- The header provides Undo/Redo for recent mixer/device adjustments

Scenes, Clips, and Views
- List scenes (names):
  - HTTP: GET `/scenes`
- Create / delete / duplicate scenes:
  - HTTP: POST `/scene/create` { "index": N? } (omit index to append at end)
  - HTTP: POST `/scene/delete` { "scene_index": N }
  - HTTP: POST `/scene/duplicate` { "scene_index": N }
 - NLP examples (when `use_intents_for_chat` is enabled):
   - `create scene`
   - `create scene at 3`
   - `delete scene 2`
   - `duplicate scene 1`
- Fire/stop a scene:
  - HTTP: POST `/scene/fire` { "scene_index": N, "select": true }
  - HTTP: POST `/scene/stop` { "scene_index": N }
 - NLP examples (chat or `/intent/parse` when `use_intents_for_chat` is enabled):
   - `fire scene 3`
   - `launch scene 5`
   - `stop scene 2`
- Capture and insert a new scene from currently playing clips:
  - HTTP: POST `/scene/capture_insert` {}
- Create an empty MIDI clip in Session view:
  - HTTP: POST `/clip/create` { "track_index": T, "scene_index": S, "length_beats": 4 }
  - Notes: Only works on MIDI tracks; slot must be empty.
- Fire/stop a single clip in Session view:
  - HTTP: POST `/clip/fire` { "track_index": T, "scene_index": S, "select": true }
  - HTTP: POST `/clip/stop` { "track_index": T, "scene_index": S }
 - Create/delete/duplicate clips (NLP + API):
   - NLP (when `use_intents_for_chat` is enabled):
     - `create clip 4 3` (creates a MIDI clip of default length at Track 4, Scene 3)
     - `create clip 4 3 8` (explicit length in beats)
     - `delete clip 4 3`
     - `duplicate clip 4 3` (duplicates to Track 4, Scene 4 if empty)
     - `duplicate clip 4 3 to 4 5`
   - API:
     - POST `/clip/delete` { "track_index": T, "scene_index": S }
     - POST `/clip/duplicate` { "track_index": T, "scene_index": S, "target_track_index"?: T2, "target_scene_index"?: S2 }
- Switch between Session and Arrangement views:
  - HTTP: POST `/view` { "mode": "session" | "arrangement" }

Naming and Device Order
- Rename items:
  - Track: POST `/track/name` { "track_index": T, "name": "Guitars" }
  - Scene: POST `/scene/name` { "scene_index": S, "name": "Chorus" }
  - Clip: POST `/clip/name` { "track_index": T, "scene_index": S, "name": "Hook" }
 - NLP examples (when `use_intents_for_chat` is enabled):
   - `rename track 3 to Pianos`
   - `rename scene 1 to Intro`
   - `rename clip 4 2 to Beatbox`
- Devices:
  - Track device: POST `/track/device/name` { "track_index": T, "device_index": D, "name": "Glue Comp" }
  - Return device: POST `/return/device/name` { "return_index": R, "device_index": D, "name": "Main Reverb" }
- Track devices:
  - Delete: POST `/track/device/delete` { "track_index": T, "device_index": D }
  - Reorder: POST `/track/device/reorder` { "track_index": T, "old_index": D1, "new_index": D2 }
- Return devices:
  - Delete: POST `/return/device/delete` { "return_index": R, "device_index": D }
  - Reorder: POST `/return/device/reorder` { "return_index": R, "old_index": D1, "new_index": D2 }

Track Arm and Monitoring
- Arm/disarm a track:
  - HTTP: POST `/track/arm` { "track_index": T, "arm": true|false }
  - NLP (when `use_intents_for_chat` is enabled):
    - `arm track 3`
    - `disarm track 3`
- Set monitoring/routing:
  - HTTP: POST `/track/routing` { "track_index": T, "monitor_state": "in" | "auto" | "off", ... }

Track Creation and Management
- Create tracks:
  - HTTP: POST `/track/create_audio` { "index": N? } (omit index to append)
  - HTTP: POST `/track/create_midi` { "index": N? } (omit index to append)
  - NLP (when `use_intents_for_chat` is enabled):
    - `create audio track`
    - `create audio track at 3`
    - `create midi track`
    - `create midi track at 4`
- Delete / duplicate tracks:
  - HTTP: POST `/track/delete` { "track_index": T }
  - HTTP: POST `/track/duplicate` { "track_index": T }
  - NLP:
    - `delete track 3`
    - `duplicate track 2`

Troubleshooting
- Param not found / ambiguous: UI shows suggestions and (for devices) a parameter list in the drawer
- Send/device topology shows empty:
  - The system fetches information on‑demand; re‑ask the query after performing any mixer action if needed
- Autocorrect didn’t trigger:
  - Add typos to `configs/app_config.json -> nlp.typo_corrections`; the client merges these at load
- Audio/MIDI type not showing in outline or badges:
   - Track type comes from the Ableton Remote outline. After updating the Remote, restart Live or toggle the Control Surface in Live’s Preferences to reload the script.
   - Verify with: `curl -s http://127.0.0.1:8722/project/outline | jq '.data.tracks'`
   - Expect each track: `{ index, name, type: "audio"|"midi" }`
 - Scene/view actions not working:
   - Ensure the Remote Script UDP bridge is enabled in Live: set `FADEBENDER_UDP_ENABLE=1` before launching Live.
   - Clip creation works only on MIDI tracks and empty slots.

Configuration Tips
- `configs/app_config.json`:
  - `features`: enable sticky capabilities card (`sticky_capabilities_card: true`), intents for chat (`use_intents_for_chat: true`)
  - `nlp.mode`: `regex_first` (fast patterns with LLM fallback)
  - `nlp.typo_corrections`: single source of truth for typo map shared with the client

Known Limitations
- Device discovery and parameter names depend on Ableton’s current set and mappings
- Some routing fields may be unavailable depending on track type (MIDI vs audio)
 - Additive percentage adjustments are not yet working (e.g., relative +% on some parameters) and need follow‑up

Appendix: Handy Examples
- SET commands:
  - `set track 1 send A to -12 dB`
  - `increase return B volume by 2 dB`
  - `set return A reverb wet to 15%`
- GET queries (multiple phrasings):
  - `what are track 2 devices` / `show me track 2 devices`
  - `who sends to return B` / `check return B senders`
  - `what is return A state` / `tell me return A state`
  - `what is track 1 volume` / `get track 1 volume`
- NAVIGATION:
  - `open track 1` / `view track 1`
  - `open return A reverb` / `view return A reverb`

- SCENES & CLIPS:
  - `fire scene 3`
  - `stop scene 3`
  - `fire clip 4 2` / `stop clip 4 2`
  - (API) POST `/clip/fire` { "track_index": 4, "scene_index": 2, "select": true }
  - (API) POST `/clip/stop` { "track_index": 4, "scene_index": 2 }

Change Log (high‑level)
- 2025‑11:
  - Transport/UI: 2‑decimal playhead/loop, compact fields, auto‑refocus chat input
  - Capabilities: type badges (AUDIO/MIDI/RETURN); Sidebar no longer auto‑opens drawer
  - NLP/Queries: "how many/list audio/midi/returns" with clickable chips to open controls
  - NLP/Action Words: Enhanced vocabulary with fuzzy matching
    - GET queries: added "show", "tell", "get", "check" (in addition to "what is", "how many", "list")
    - NAVIGATION: added "view" (in addition to "open")
    - All action words support typo correction via fuzzy matching
    - Fixed relative_change intent type for "increase"/"decrease" commands
  - Outline: more robust track type detection in the Ableton Remote (may require Live restart)
