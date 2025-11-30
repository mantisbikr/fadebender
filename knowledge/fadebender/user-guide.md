Fadebender User Guide

What is Fadebender?
Fadebender is your AI-powered mixing and production assistant for Ableton Live. It combines three powerful capabilities:

1. **DAW Control**: Control Ableton Live using natural language commands - "set track 1 volume to -6 dB", "load reverb on return A", "open track 2 compressor"

2. **Audio Engineering Guidance**: Get expert advice on mixing and production - "my vocals sound weak", "how to make my kick punch through", "my mix sounds muddy"

3. **Context-Aware Help**: Fadebender understands your current Live set and provides specific advice tailored to your project - "how can I improve my mix", "what's the best way to use my return tracks", "help me balance my drums"

It learns from professional audio engineering knowledge, the complete Ableton Live manual, and understands your project's routing and signal flow to give you relevant, actionable guidance.

Getting Started
When you first open Fadebender:

1. **Look around the interface:**
   - **Sidebar (left)**: Shows your tracks, returns, and master
   - **Chat input (bottom)**: Where you type commands and questions
   - **Transport bar (top)**: Play, record, tempo, and loop controls
   - **Capabilities drawer (right)**: Opens automatically when you run commands

2. **Try your first interactions:**
   - **Control commands**: Type `set track 1 volume to -6 dB` - Changes the volume and shows mixer controls
   - **Navigation**: Type `open track 1` - The capabilities drawer opens with track 1's mixer controls
   - **Query information**: Type `what is track 1 volume` - Shows the current volume value
   - **Audio advice**: Type `my vocals sound weak` - Get expert mixing advice
   - **Ableton questions**: Type `what are sends and returns` - Learn from the Ableton manual
   - **Context-aware help**: Type `how can I improve my mix` - Get advice specific to your Live set

3. **Explore the capabilities drawer:**
   - After running a command, scroll through the drawer to see all available controls
   - Click the pin icon to keep it open while you work
   - Use sliders, toggles, and dropdowns to adjust parameters visually

4. **Ask questions:**
   - "what are track 2 devices" - See what's on a track
   - "who sends to return A" - Understand your routing
   - "list audio tracks" - Get an overview of your project

Command Capabilities Summary
This section provides a quick overview of all available commands to help you understand what Fadebender can do.

**Command Categories (60+ command patterns):**
- Mixer Control (12): volume, pan, mute, solo, sends (absolute + relative)
- Device Control (8): device parameters on tracks/returns, device ordinals
- Device Management (4): load devices, delete devices, with preset support
- Navigation (4): open/view mixer or device controls
- Transport (11): tempo, loop, time signature, playhead queries
- Song Operations (9): undo/redo, song info, locators, song length
- Track Management (7): create, delete, duplicate, arm/disarm, rename
- Scene Operations (5): create, delete, duplicate, fire, stop
- Clip Operations (5): create, delete, duplicate, fire, stop
- Query Commands (15+): parameter values, state bundles, topology, routing, project overview
- Naming (4): rename tracks, scenes, clips, devices
- View Switching (2): session/arrangement

**Supported Targets:**
- Tracks: audio tracks, MIDI tracks (by index: 1, 2, 3...)
- Returns: A, B, C, D... (by letter or index: 0, 1, 2...)
- Master: master track
- Devices: by name, index, or ordinal (first/second/1st/2nd)
- Scenes: by index (1, 2, 3...)
- Clips: by track + scene index (track 4, scene 2)
- Locators: by index or name

**Action Types:**
- SET: absolute values (set track 1 volume to -6 dB)
- RELATIVE: increase/decrease (increase track 1 volume by 3 dB)
- TOGGLE: mute, solo, loop
- CREATE: tracks, scenes, clips
- DELETE: tracks, scenes, clips, devices
- LOAD: devices with optional presets
- DUPLICATE: tracks, scenes, clips
- RENAME: tracks, scenes, clips, devices
- QUERY: what is, show, tell, get, check (parameter values)
- TOPOLOGY: list devices, who sends to, what affects

**Parameter Types & Units:**
- Volume: dB (-inf to +6 dB), percent (0-100%), normalized (0.0-1.0)
- Pan: L/R notation (25L, 30R), percent, normalized, center
- Sends: dB, percent, normalized
- Device parameters: seconds (s), milliseconds (ms), hertz (Hz), kilohertz (kHz), dB, percent, normalized, display labels (High, Low, On, Off)
- Tempo: BPM (40-999)
- Time signature: numerator (1-99), denominator (1, 2, 4, 8, 16)
- Loop: start/length in beats

**Special Features:**
- Device ordinals: control multiple devices of same type ("reverb 2", "second compressor")
- Multi-word devices: "auto filter", "eq eight", "beat repeat"
- Case-insensitive: commands, device names, parameter names work in any case
- Typo correction: automatically fixes common typos as you type
- Preset loading: explicit ("preset cathedral") or implicit ("gentle")
- State bundles: get all mixer settings + routing in one query
- Topology queries: understand signal flow and routing
- Clarification prompts: system asks follow-up questions for ambiguous commands
- Context-aware UI: capabilities drawer opens with relevant controls

**Command Verb Variations:**
- Navigation: "open", "view" (interchangeable)
- Query: "what is", "show", "show me", "tell", "tell me", "get", "check" (interchangeable)
- Scene playback: "fire", "launch" (interchangeable)
- Device loading: "load", "add", "put", "insert" (interchangeable)
- Device deletion: "delete", "remove" (interchangeable)
- Tempo: "set tempo", "set bpm", "change tempo" (interchangeable)

**Help System:**
Fadebender provides three types of help:

1. **Audio Engineering Advice**: Get expert guidance on mixing, production, and sound design
   - "my vocals sound weak" - Advice on EQ, compression, presence
   - "my mix sounds muddy" - Tips on frequency management and clarity
   - "how to make my kick punch through" - Techniques for drum presence
   - "what's the best reverb settings for vocals" - Parameter recommendations

2. **Ableton Live Knowledge**: Learn from the complete Ableton manual
   - "what are sends and returns" - Routing concepts explained
   - "how does sidechaining work in Ableton" - Feature tutorials
   - "explain the compressor parameters" - Device documentation
   - "what's the difference between audio and MIDI tracks" - DAW fundamentals

3. **Context-Aware Project Help**: Get advice specific to your current Live set
   - "how can I improve my mix" - Analysis based on your tracks and routing
   - "what's the best way to organize my returns" - Recommendations for your project
   - "help me balance my drums" - Advice considering your drum tracks
   - "which tracks should I sidechain" - Suggestions based on your signal flow

All responses include relevant command suggestions to implement the advice immediately.

Chat Basics
- Type natural language commands, press Enter to send
- Autocorrect: common typos are fixed automatically as you type (e.g., `trac` → `track`)
- Clarification: when the intent is ambiguous, the UI asks a follow‑up question and shows suggested commands
- Help: ask conceptual questions ("my vocals sound weak") or operational questions ("what is track 1 volume")

Understanding the Interface

**Sidebar (Left Side):**
- Shows your project structure: tracks, returns, and master
- Each track shows: number, name, and type (AUDIO/MIDI)
- Return tracks labeled by letter (A, B, C...)
- Click track names to view details (doesn't auto-open drawer - use `open` commands instead)
- Scroll to see all tracks in large projects

**Chat Input (Bottom Center):**
- Type your commands and questions here
- Press Enter to send
- Previous messages show above with timestamps
- AI responses appear with suggested follow-up actions
- "Clear Chat" button removes conversation history

**Transport Bar (Top):**
- Play/Stop/Record buttons
- Metronome toggle
- Tempo display and controls (BPM)
- Time signature controls
- Playhead position
- Loop controls (start/length)
- Undo/Redo buttons
- Settings and view mode toggles

**Capabilities Drawer (Right Side):**
- Opens automatically when you run commands
- Shows context-relevant controls (mixer or device parameters)
- Stays updated in real-time with Live
- Pin/unpin and close buttons in top-right corner
- Scroll to see all available parameters

Capabilities Drawer
The capabilities drawer is Fadebender's context-aware control panel that automatically displays relevant controls when you interact with your project.

**When It Opens:**
- Auto-opens when you run any command (set, increase, decrease, mute, solo, etc.)
- Auto-opens when you ask "get" queries (what is, show, tell me, check)
- Auto-opens when you use navigation commands (open, view)
- Auto-opens when you click list chips from query responses (list audio tracks, list returns)
- Does NOT open when clicking sidebar items (use explicit "open" commands instead)

**Drawer Types:**
1. **Device Drawer** - Shows when controlling device parameters:
   - Displays all parameters for the selected device (reverb, delay, compressor, etc.)
   - Parameters grouped by section (General, Early Reflections, Diffusion, etc.)
   - Each parameter shows: name, current value, range, unit
   - Inline controls: sliders for continuous values, toggles for on/off, dropdowns for discrete choices

2. **Mixer Drawer** - Shows when controlling mixer parameters:
   - Displays volume, pan, mute, solo controls
   - Shows all send levels (Send A, Send B, etc.)
   - Type badge indicates: AUDIO / MIDI (for tracks) or RETURN (for return tracks)
   - Includes cue volume for master

**How to Navigate:**
- Scroll within the drawer to see all parameters
- Parameters are organized by section with clear headings
- Pin icon (top right): Click to keep drawer open when switching context
- Close icon (top right): Click to close drawer
- Pinned drawers stay open until you close them manually
- Unpinned drawers auto-close when you switch to a different track/return/device

**Using Controls:**
- **Sliders**: Drag to adjust, or click the value to type a number
- **Toggles**: Click to switch on/off (Device On, Mute, Solo, etc.)
- **Dropdowns**: Click to see and select from available options
- All changes are sent to Ableton Live in real-time
- Current values update automatically when changed in Live or via commands

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

Device Loading
- **Audio Effects** - Load audio processing devices:
  - `load reverb on track 2`
  - `add compressor to track 1`
  - `put limiter on return A`
  - `insert delay on track 3`
  - `load auto filter on track 5`
  - `add eq eight to track 1`
  - `load beat repeat on track 2`
- **MIDI Effects** - Load MIDI processing devices:
  - `load arpeggiator on track 3`
  - `add chord to track 2`
  - `load note echo on track 4`
  - `add scale on track 1`
- **Instruments** - Load synthesizers and samplers:
  - `load analog on track 5`
  - `add wavetable to track 3`
  - `load impulse on track 2`
  - `add sampler to track 4`
  - `load drum rack on track 1`
- **With Presets** - Load device with specific preset:
  - `load reverb preset cathedral on track 2`
  - `load analog preset lush pad on track 3`
  - `add delay 4th bandpass on return C` (implicit preset)
  - `add compressor gentle on return B` (implicit preset)
- Multi-word devices work automatically (auto filter, eq eight, beat repeat, drum rack)
- Case-insensitive: `load reverb` / `load REVERB` / `load Reverb`
- Supported verbs: load, add, put, insert
- Supported targets: track N, return A-L (letter or number), master
- Requires device_map.json to be configured (auto-generated during installation)

Device Deletion
- Delete devices from tracks or returns:
  - `delete reverb from track 2` (deletes first match)
  - `remove compressor from track 1`
  - `delete delay from return A`
- Delete by device index:
  - `delete device 0 from track 2`
  - `remove device 1 from return A`
- Delete by ordinal (when multiple devices with same name):
  - `delete first reverb from track 2`
  - `remove second compressor from track 1`
  - `delete 2nd eq eight from track 3`
- With optional "the" keyword:
  - `remove the reverb from return B`
  - `delete the limiter from track 1`
- Case-insensitive device matching
- Supported verbs: delete, remove
- Note: Uses exact device index after resolution, so safe even with multiple devices

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

Transport Commands
- Set tempo:
  - `set tempo to 130`
  - `set bpm to 120`
  - `change tempo to 140`
- Loop control:
  - `loop on` / `loop off`
  - `loop toggle`
  - `set loop start to 4`
  - `set loop length to 8`
- Time signature:
  - `set time signature numerator to 4`
  - `set time signature denominator to 4`
  - `set time sig numerator to 3`
- Query commands:
  - `what is the tempo?`
  - `is the click on?`
  - `what's the current tempo?`
- UI controls (if enabled in your build):
  - Play/stop/record/click toggles via the transport bar
  - Playhead and loop fields display up to 2 decimal places
  - Compact widths for tempo, time signature, playhead, loop start/length
- After sending an intent, keyboard focus returns to the chat input automatically

Song-Level Operations

Undo/Redo (Project-Level)
- NLP commands:
  - `undo` / `undo last change` → undoes last project change in Live
  - `redo` / `redo that` → redoes last undone change
- UI: Header icons provide quick undo/redo access
- Note: This is Live's project-level undo (all operations), not Fadebender command history

Song Information
- Query song metadata:
  - `what's the song name` / `show song info` → displays name, tempo, time signature
  - `what is the song length` / `how long is the song` → returns song length in beats
  - `what is the tempo` → shows current tempo
  - `where is the playhead` / `where am I` → shows current playhead position in beats

Locators (Arrangement Cue Points)
- List all locators:
  - `list locators` / `show locators` → displays all locators with positions
- Jump to locator:
  - `jump to locator 2` → jumps to locator by index
  - `jump to intro` / `go to verse` → jumps to locator by name
- Rename locator:
  - `rename locator 1 to intro`
  - `call locator 2 verse`
- Note: Creating/deleting locators not supported due to Live API limitations

Scenes, Clips, and Views
- Create / delete / duplicate scenes:
   - `create scene`
   - `create scene at 3`
   - `delete scene 2`
   - `duplicate scene 1`
- Fire/stop a scene:
   - `fire scene 3`
   - `launch scene 5`
   - `stop scene 2`
- Create/delete/duplicate clips:
   - `create clip 4 3` (creates a MIDI clip of default length at Track 4, Scene 3)
   - `create clip 4 3 8` (explicit length in beats)
   - `delete clip 4 3`
   - `duplicate clip 4 3` (duplicates to the next scene on the same track)
   - `duplicate clip 4 3 to 4 5` (duplicates to a specific position)
   - `duplicate clip 3,1` (comma notation also supported)
   - `duplicate clip 3,1 to 3,3` (comma notation with target)
   - **Note**: Clip creation only works on MIDI tracks with empty slots
   - **Note**: Duplicate clip requires both track and scene coordinates (e.g., `3,1` or `3 1`)
- Fire/stop a single clip:
   - `fire clip 4 2`
   - `stop clip 4 2`

Naming
- Rename items using natural language:
   - `rename track 3 to Pianos`
   - `rename scene 1 to Intro`
   - `rename clip 4 2 to Beatbox`

Track Arm
- Arm/disarm a track for recording:
    - `arm track 3`
    - `disarm track 3`

Track Creation and Management
- Create tracks:
    - `create audio track`
    - `create audio track at 3`
    - `create midi track`
    - `create midi track at 4`
- Delete / duplicate tracks:
    - `delete track 3`
    - `duplicate track 2`

Common Workflows

**Setting up a reverb send:**
1. Type `load reverb on return A` - Adds reverb to return track A
2. Type `open return A reverb` - Opens the reverb controls
3. Adjust reverb parameters in the drawer (decay, wet/dry, etc.)
4. Type `set track 1 send A to -12 dB` - Send track 1 to the reverb
5. Repeat step 4 for other tracks that need reverb

**Controlling multiple devices of the same type:**
1. If you have two reverbs on return A
2. Type `set return A reverb 1 decay to 2s` - Controls the first reverb
3. Type `set return A reverb 2 decay to 4s` - Controls the second reverb
4. Or use ordinals: `set return A second reverb decay to 4s`

**Exploring your project structure:**
1. Type `list audio tracks` - See all audio tracks with clickable chips
2. Click any track chip to open its mixer controls
3. Type `what are track 2 devices` - See all devices on track 2
4. Type `who sends to return A` - Find which tracks are using return A
5. Type `what is return A state` - Get complete mixer settings for return A

**Loading a device with a preset:**
1. Type `load reverb preset cathedral on track 2` - Loads reverb with cathedral preset
2. Type `open track 2 reverb` - View the reverb settings
3. Adjust parameters as needed using the drawer controls

**Working with the capabilities drawer:**
1. Type `open track 1` - Opens mixer controls
2. Click the pin icon to keep it open
3. Type `open track 2` - Drawer switches to track 2 but stays open (because pinned)
4. Type `set track 2 volume to -3 dB` - Adjust while viewing controls
5. Click the close icon when done

**Quick mixing adjustments:**
1. Type `increase track 1 volume by 3 dB` - Relative adjustment
2. Type `decrease track 2 send B by 5%` - Another relative change
3. Type `mute track 3` - Toggle mute
4. Type `solo track 1` - Solo a track
5. Type `set track 1 pan to 25R` - Pan right

Troubleshooting
- **Parameter not found**: UI shows suggestions and (for devices) a parameter list in the drawer
- **Send/device topology shows empty**: Re-ask the query after performing any mixer action
- **Clip creation not working**: Clip creation only works on MIDI tracks with empty slots
- **Audio/MIDI type badge missing**: Restart Ableton Live or toggle the Control Surface in Live's Preferences

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
