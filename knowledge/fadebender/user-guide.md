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
- Auto‑opens with context when you run a command or ask a supported “get” query
- Device drawer: shows grouped device parameters with inline editors
- Mixer drawer: shows mixer parameters for tracks/returns/master (volume, pan, mute, solo, sends)
- Pin to keep it visible; unpin to auto‑close when switching context

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
- Value reads:
  - `what is track 1 volume?`
  - `what is return A pan?`
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

Transport
- Reads:
  - `what is the tempo?`
  - `is the click on?`
- Actions (if enabled in your build): play/stop/record/click toggles via the transport bar

Undo/Redo
- The header provides Undo/Redo for recent mixer/device adjustments

Troubleshooting
- Param not found / ambiguous: UI shows suggestions and (for devices) a parameter list in the drawer
- Send/device topology shows empty:
  - The system fetches information on‑demand; re‑ask the query after performing any mixer action if needed
- Autocorrect didn’t trigger:
  - Add typos to `configs/app_config.json -> nlp.typo_corrections`; the client merges these at load

Configuration Tips
- `configs/app_config.json`:
  - `features`: enable sticky capabilities card (`sticky_capabilities_card: true`), intents for chat (`use_intents_for_chat: true`)
  - `nlp.mode`: `regex_first` (fast patterns with LLM fallback)
  - `nlp.typo_corrections`: single source of truth for typo map shared with the client

Known Limitations
- Device discovery and parameter names depend on Ableton’s current set and mappings
- Some routing fields may be unavailable depending on track type (MIDI vs audio)

Appendix: Handy Examples
- `set track 1 send A to -12 dB`
- `increase return B volume by 2 dB`
- `set return A reverb wet to 15%`
- `what are track 2 devices`
- `who sends to return B`
- `what is return A state`

Change Log (high‑level)
- 2025‑11: Added topology queries (devices, sources, send‑to effects) and state bundles; improved drawer behavior and typo handling

