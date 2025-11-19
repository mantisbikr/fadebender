# Fadebender User Guide

## Overview
Fadebender is a natural language interface for controlling Ableton Live. Users type commands in a web-based chat interface. The system displays context-aware visual controls in a capabilities drawer (mixer controls, device parameters) and a sidebar showing tracks and returns.

## Interface Components

### Web Chat Interface
- Chat input: accepts natural language commands
- Auto-correction: automatic typo correction on space/tab
- Clarification prompts: system asks follow-up questions for ambiguous commands
- Message history: displays command results and system responses

### Transport Bar
- Location: top of interface
- Displays: tempo, time signature, playhead position (2 decimal places), loop markers
- Controls: play, stop, record, metronome toggle
- Behavior: keyboard focus returns to chat input after any transport interaction

### Sidebar
- Left panel showing project structure
- Lists: audio tracks, MIDI tracks, return tracks
- Type indicators: AUDIO, MIDI, RETURN badges
- Behavior: clicking sidebar does NOT auto-open capabilities drawer

### Capabilities Drawer
- Right panel with context-aware controls
- Two modes: Mixer view (volume, pan, mute, solo, sends) and Device view (effect/instrument parameters)
- Auto-open: opens when executing commands or asking "get" queries
- Pin behavior: pin to keep open, unpin for auto-close on context switch
- Type badges: displays AUDIO, MIDI, or RETURN for current context

### Undo/Redo
- Location: header buttons
- Scope: mixer adjustments and device parameter changes

## Navigation Commands

### Opening Capabilities Drawer
Syntax variations: "open" or "view" (interchangeable)

**Track mixer controls:**
- `open track 1` or `view track 1`
- `open track 2` or `view track 2`

**Return mixer controls:**
- `open return A` or `view return A`
- `open return B` or `view return B`

**Device controls on returns:**
- `open return A reverb` or `view return A reverb`
- `open return B delay` or `view return B delay`

**Device controls on tracks:**
- `open track 2 delay` or `view track 2 delay`
- `open track 3 compressor` or `view track 3 compressor`

Result: Opens capabilities drawer with relevant mixer or device controls

## Mixer Control Commands

### Volume Control
**Absolute values:**
- `set track 1 volume to -6 dB`
- `set track 2 volume to -12 dB`
- `set return A volume to -3 dB`
- `set master volume to 0 dB`

**Relative adjustments:**
- `increase track 1 volume by 3 dB`
- `decrease track 2 volume by 2 dB`
- `increase return B volume by 1.5 dB`

### Pan Control
**Absolute values:**
- `set track 1 pan to 25R` (25% right)
- `set track 2 pan to 30L` (30% left)
- `set track 3 pan to center`
- `set return A pan to 50R`

**Relative adjustments:**
- `increase track 1 pan by 10`
- `decrease track 2 pan by 15`

### Mute and Solo
**Mute:**
- `mute track 1`
- `mute track 3`
- `unmute track 2`

**Solo:**
- `solo track 1`
- `solo track 4`
- `unsolo track 1`

### Send Control
**Absolute values (percentage):**
- `set track 1 send A to 20%`
- `set track 2 send B to 35%`
- `set track 3 send C to 50%`

**Absolute values (dB):**
- `set track 1 send A to -12 dB`
- `set track 2 send B to -6 dB`

**Relative adjustments:**
- `increase track 1 send A by 5%`
- `decrease track 2 send B by 10%`

## Device Control Commands

### Return Device Parameters
**Setting device parameters:**
- `set return A reverb decay to 2 s`
- `set return B delay feedback to 35%`
- `set return A reverb wet to 15%`
- `set return B delay time to 500 ms`

**Multiple devices of same type (device ordinal):**
- `set return B reverb 2 decay to 1.5 s` (controls 2nd reverb device)
- `set return A delay 2 feedback to 40%` (controls 2nd delay device)

### Track Device Parameters
**Setting device parameters:**
- `set track 1 compressor threshold to -18 dB`
- `set track 2 EQ high gain to 3 dB`
- `set track 3 reverb decay to 1.5 s`

**Relative adjustments:**
- `increase track 1 EQ high gain by 2 dB`
- `decrease track 2 compressor ratio by 1`

## Query Commands (Get Information)

### Parameter Value Queries
Action words: "what is", "show", "show me", "tell", "tell me", "get", "check" (all interchangeable)

**Single parameter queries:**
- `what is track 1 volume?`
- `show me track 1 volume`
- `show track 1 pan`
- `tell me return A pan`
- `tell track 1 volume`
- `get track 2 volume`
- `check track 1 mute`
- `what's the current tempo?`
- `is the metronome on?`

**Device parameter queries:**
- `what is return A reverb decay?`
- `show me track 1 compressor threshold`
- `get return B delay feedback`

Result: Opens capabilities drawer with relevant controls

### State Bundle Queries
Returns complete overview: volume, pan, mute, solo, sends, routing summary

**Syntax:**
- `what is track 1 state`
- `what is track 2 state`
- `what is return A state`
- `what is return B state`
- `what is master state`

### Device Topology Queries
**List devices on track/return:**
- `what are track 1 devices`
- `what are track 2 devices`
- `what are return A devices`
- `what are return B devices`
- `show me track 1 devices`

Result: Ordered list of all devices on specified track/return

### Routing Queries
**Find send sources:**
- `who sends to return A`
- `which tracks send to return A`
- `who sends to return B`
- `which tracks send to return B`

Result: List of tracks with non-zero sends to specified return

**Trace send destinations:**
- `what does track 1 send A affect`
- `what does track 2 send B affect`

Result: Lists devices on the destination return

### Project Overview Queries

**Count queries:**
- `how many audio tracks`
- `how many midi tracks`
- `how many return tracks`
- `track count`

**List queries:**
- `list audio tracks`
- `list midi tracks`
- `list returns`

Result: Response includes clickable chips/buttons for each track/return that open capabilities drawer when clicked

## Scene Commands

### Scene Creation
- `create scene` (appends at end)
- `create scene at 3` (inserts at position 3)

### Scene Deletion
- `delete scene 2`
- `delete scene 5`

### Scene Duplication
- `duplicate scene 1`
- `duplicate scene 3`

### Scene Firing (Playback)
Action words: "fire" or "launch" (interchangeable)
- `fire scene 1`
- `fire scene 3`
- `launch scene 5`
- `launch scene 2`

### Scene Stopping
- `stop scene 1`
- `stop scene 3`

## Clip Commands

### Clip Creation
Constraint: MIDI tracks only, empty clip slots only
- `create clip 2 4`
- `create clip 2 4 8` (explicit length in beats)

### Clip Firing
- `fire clip 4 2` (track 4, scene 2)
- `fire clip 1 3` (track 1, scene 3)

### Clip Stopping
- `stop clip 4 2` (track 4, scene 2)
- `stop clip 1 3` (track 1, scene 3)

### Clip Deletion
- `delete clip 4 2`
- `delete clip 1 3`

### Clip Duplication
- `duplicate clip 4 2` (copies to next scene on same track if empty)
- `duplicate clip 4 2 to 4 5`
- `duplicate clip 4 2 to 4 5 as Bongos`

## View Switching Commands

### Session vs Arrangement View
- `switch to session view`
- `switch to arrangement view`

## Track Management Commands

### Track Creation
**Audio tracks:**
- `create audio track` (appends at end)
- `create audio track at 3` (inserts at position 3)

**MIDI tracks:**
- `create midi track` (appends at end)
- `create midi track at 4` (inserts at position 4)

### Track Deletion
- `delete track 1`
- `delete track 3`

### Track Duplication
- `duplicate track 1`
- `duplicate track 2`

### Track Arming (Recording)
- `arm track 1` (enable recording)
- `arm track 3`
- `disarm track 1` (disable recording)
- `disarm track 3`

## Naming Commands

### Track Naming
- `rename track 1 to Bass`
- `rename track 2 to Drums`
- `rename track 3 to Pianos`

### Scene Naming
- `rename scene 1 to Intro`
- `rename scene 2 to Verse`
- `rename scene 3 to Chorus`

### Clip Naming
- `rename clip 4 2 to Beatbox` (track 4, scene 2)
- `rename clip 1 1 to Hook` (track 1, scene 1)

### Device Naming
**Track devices:**
- `rename track 1 device 1 to Glue Comp`
- `rename track 2 device 2 to Main EQ`

**Return devices:**
- `rename return A device 1 to Main Reverb`
- `rename return B device 1 to Slapback Delay`

## Troubleshooting Guide

### Parameter Not Found
**Symptom:** Command fails to find specified parameter
**Solution:**
- Check capabilities drawer for available parameters
- Use exact device name as shown in Live
- Query device list: `what are track X devices`

### Send/Device Topology Empty
**Symptom:** Routing queries or device lists return empty
**Solution:**
- Execute any mixer command first to trigger data fetch
- Re-run the query after mixer interaction

### Track Type Badges Missing
**Symptom:** AUDIO/MIDI/RETURN badges not showing
**Solution:**
- Restart Ableton Live
- Toggle Control Surface in Live Preferences to reload script

### Clip/Scene Commands Failing
**Constraints:**
- Clip creation: MIDI tracks only, empty slots only
- Scene/clip operations: Session view only
**Solution:** Verify track type and view mode before operation

### Device Parameter Names
**Note:** Parameter names depend on currently loaded Live set and device mappings. Use exact names from Ableton Live interface.

## Known Limitations
- Device discovery relies on Ableton's current device set
- Some routing fields unavailable depending on track type (MIDI vs audio)
- Percentage-based relative adjustments on certain parameters may not work consistently

## Common Command Patterns

### Mixer Workflows
```
set track 1 send A to -12 dB
increase return B volume by 2 dB
set return A reverb wet to 15%
mute track 3
solo track 1
```

### Query Workflows
```
what are track 2 devices
show me track 2 devices
who sends to return B
check return B senders
what is return A state
tell me return A state
what is track 1 volume
get track 1 volume
```

### Navigation Workflows
```
open track 1
view track 1
open return A reverb
view return A reverb
```

### Scene/Clip Workflows
```
fire scene 3
launch scene 5
stop scene 3
fire clip 4 2
stop clip 4 2
create scene
duplicate scene 1
```

### Track Management Workflows
```
create audio track
create midi track at 3
rename track 2 to Bass
delete track 3
duplicate track 2
arm track 1
list audio tracks
how many midi tracks
```
