# Fadebender vs AbletonOSC - Feature Comparison

**Date**: 2025-11-16

## Overview

This document compares Fadebender's capabilities against AbletonOSC to identify gaps and prioritize features.

---

## ✅ What Fadebender Has That AbletonOSC Doesn't

### 1. Natural Language Interface (Fadebender's Core Advantage)

**AbletonOSC**: Raw OSC commands only (`/live/track/set/volume 0 0.8`)

**Fadebender**:
- Conversational queries: "what is track 1 volume?", "show me return A devices"
- Multiple phrasings: "increase", "raise", "boost" all work
- Typo correction: "incrase" → "increase", "volumz" → "volume"
- Fuzzy matching for action words and parameters
- 4-layer NLP architecture with confidence scoring

### 2. Smart Context-Aware UI

**Fadebender Unique Features**:
- Capabilities drawer with auto-opening based on command context
- Device parameter grouping (instead of flat lists)
- Mixer controls with inline editors
- Type badges (AUDIO/MIDI/RETURN)
- Clickable list chips that open relevant controls
- Pin/unpin drawer behavior
- Autocorrect on client side (space/tab triggers)

### 3. Topology Intelligence

**Fadebender Exclusive Queries**:
- `who sends to return A` - finds tracks with non-zero sends
- `what does track 1 send A affect` - shows devices on destination return
- `what is track 1 state` - comprehensive state bundle (volume, pan, mute, solo, routing)
- Drawer behavior: queries auto-open relevant controls

### 4. Remote Script Extensions (Not in AbletonOSC)

**Fadebender via Remote Script**:
- ✅ Device reordering on tracks/returns
- ✅ Device deletion on tracks/returns
- ✅ Clip/track/scene renaming via HTTP
- ✅ Clip creation (already have)
- ✅ Session/Arrangement view mode switching
- ✅ Scene capture and insert
- ✅ Track type detection (audio vs MIDI in outline)

**AbletonOSC**: Explicitly does NOT provide these (requires separate Remote Script)

### 5. Integrated Architecture

**Fadebender**:
- HTTP + Chat unified system
- Single backend handles both protocols
- Clarification flows when ambiguous
- Project outline with track metadata

---

## ❌ What AbletonOSC Has That Fadebender Lacks

### 🔴 HIGH PRIORITY GAPS (Core Session View Workflow)

#### 1. Clip Fire/Stop ⭐ **CRITICAL**
**AbletonOSC**:
- `/live/clip/fire <track_id> <clip_id>` - Fire/stop clip
- `/live/clip_slot/fire <track_index> <clip_index>` - Fire clip in slot

**Fadebender**: ❌ Not implemented

**Impact**: Can't perform in session view, can't trigger clips
**Minimum to Add**:
```
NLP: "fire track 1 clip 2", "play track 3 scene 1", "stop track 1 clip 4"
HTTP: POST /clip/fire { track_index, scene_index }
HTTP: POST /clip/stop { track_index, scene_index }
Remote Script: clip.fire(), clip.stop()
```

#### 2. Scene Fire (NLP Missing) ⭐ **HIGH**
**AbletonOSC**:
- `/live/scene/fire <scene_id>`
- `/live/scene/fire_as_selected <scene_id>`
- `/live/scene/fire_selected`

**Fadebender**:
- ✅ HTTP endpoint exists: `POST /scene/fire`
- ❌ No NLP support

**Impact**: Have to use HTTP, can't say "fire scene 3"
**Minimum to Add**:
```
NLP: "fire scene 1", "trigger scene 2", "play scene 3"
```

#### 3. Track Arm/Monitoring ⭐ **HIGH**
**AbletonOSC**:
- `/live/track/get/arm <track_id>`
- `/live/track/set/arm <track_id> <0|1>`
- `/live/track/get/current_monitoring_state <track_id>`
- `/live/track/set/current_monitoring_state <track_id> <state>`

**Fadebender**: ❌ Not implemented

**Impact**: Can't arm tracks for recording, can't control monitoring
**Minimum to Add**:
```
NLP: "arm track 1", "disarm track 2"
NLP: "set track 1 monitoring to auto", "set track 2 monitoring to in/off"
HTTP: POST /track/arm { track_index, armed: true/false }
HTTP: POST /track/monitoring { track_index, mode: "auto"|"in"|"off" }
Remote Script: track.arm, track.current_monitoring_state
```

#### 4. Clip Playing Status ⭐ **MEDIUM-HIGH**
**AbletonOSC**:
- `/live/clip/get/is_playing <track_id> <clip_id>`
- `/live/clip/get/is_recording <track_id> <clip_id>`
- `/live/track/get/playing_slot_index <track_id>` - Which clip is playing on this track
- `/live/track/get/fired_slot_index <track_id>` - Which clip is about to play

**Fadebender**: ❌ Not implemented

**Impact**: Can't see which clips are playing, no visual feedback in UI
**Minimum to Add**:
```
NLP: "is track 1 clip 2 playing?", "what clip is playing on track 3?"
HTTP: GET /track/playing_clip?track_index=1
HTTP: GET /clip/status?track_index=1&scene_index=2
Remote Script: clip.is_playing, clip.is_recording, track.playing_slot_index
Visual: Clip status indicators in capabilities drawer
```

#### 5. Undo/Redo (Song-Level) ⭐ **MEDIUM**
**AbletonOSC**:
- `/live/song/undo`
- `/live/song/redo`
- `/live/song/get/can_undo`
- `/live/song/get/can_redo`

**Fadebender**:
- ✅ Has UI-level undo/redo for adjustments
- ❌ No song-level undo/redo (Live's history)

**Impact**: Can't undo clip creation, track deletion, etc. - only parameter changes
**Minimum to Add**:
```
NLP: "undo", "redo", "can I undo?"
HTTP: POST /song/undo
HTTP: POST /song/redo
HTTP: GET /song/can_undo
Remote Script: song.undo(), song.redo()
```

---

### 🟡 MEDIUM PRIORITY GAPS (Enhanced Control)

#### 6. Track Colors
**AbletonOSC**:
- `/live/track/get/color <track_id>`
- `/live/track/set/color <track_id> <color>`
- `/live/track/get/color_index <track_id>`

**Fadebender**: ❌ Not implemented

**Minimum to Add**:
```
NLP: "set track 1 color to red", "what is track 2 color?"
HTTP: POST /track/color { track_index, color }
Visual: Color indicators in capabilities drawer
```

#### 7. Track Metering (Real-time levels)
**AbletonOSC**:
- `/live/track/get/output_meter_left <track_id>`
- `/live/track/get/output_meter_right <track_id>`
- `/live/track/get/output_meter_level <track_id>`

**Fadebender**: ❌ Not implemented

**Impact**: No visual level meters
**Minimum to Add**:
```
HTTP: GET /track/meters (with live updates)
Visual: Level meters in capabilities drawer
Requires: Listener/polling mechanism
```

#### 8. Cue Points
**AbletonOSC**:
- `/live/song/cue_point/jump <cue_point>`
- `/live/song/cue_point/add_or_delete`
- `/live/song/cue_point/set/name <cue_index> <name>`
- `/live/song/get/cue_points`

**Fadebender**: ❌ Not implemented

**Minimum to Add**:
```
NLP: "jump to cue intro", "add cue here", "list cues"
HTTP: POST /song/cue/jump { name_or_index }
HTTP: GET /song/cues
```

#### 9. Track Routing Info
**AbletonOSC**:
- `/live/track/get/input_routing_type <track_id>`
- `/live/track/get/input_routing_channel <track_id>`
- `/live/track/get/output_routing_type <track_id>`
- `/live/track/get/output_routing_channel <track_id>`
- Plus: available routing options

**Fadebender**: ❌ Not implemented

**Minimum to Add**:
```
NLP: "what is track 1 input routing?", "what is track 2 output routing?"
HTTP: GET /track/routing?track_index=1
Visual: Routing info in state bundle
```

#### 10. Clip Duplicate/Delete
**AbletonOSC**:
- `/live/clip_slot/delete_clip <track_index> <clip_index>`
- `/live/clip_slot/duplicate_clip_to <track_index> <clip_index> <target_track> <target_clip>`

**Fadebender**: ❌ Not implemented (have create, but not delete/duplicate)

**Minimum to Add**:
```
NLP: "delete track 1 clip 2", "duplicate track 1 clip 3 to track 2 clip 1"
HTTP: POST /clip/delete { track_index, scene_index }
HTTP: POST /clip/duplicate { source_track, source_scene, target_track, target_scene }
```

---

### 🟢 LOW PRIORITY GAPS (Advanced Features)

#### 11. Clip Loop Markers & Warping
**AbletonOSC**:
- `/live/clip/get/loop_start`, `/live/clip/set/loop_start`
- `/live/clip/get/loop_end`, `/live/clip/set/loop_end`
- `/live/clip/get/warping`, `/live/clip/set/warping`
- `/live/clip/get/start_marker`, `/live/clip/set/start_marker`
- `/live/clip/get/end_marker`, `/live/clip/set/end_marker`
- `/live/clip/get/pitch_coarse`, `/live/clip/set/pitch_coarse`
- `/live/clip/get/pitch_fine`, `/live/clip/set/pitch_fine`
- `/live/clip/get/gain`, `/live/clip/set/gain`

**Fadebender**: ❌ Not implemented

#### 12. MIDI Note Manipulation
**AbletonOSC**:
- `/live/clip/get/notes <track_id> <clip_id> [range]`
- `/live/clip/add/notes <track_id> <clip_id> <pitch> <start_time> <duration> <velocity> ...`
- `/live/clip/remove/notes [range]`

**Fadebender**: ❌ Not implemented

**Impact**: Complex, likely out of scope for chat-first interface

#### 13. Device Parameter Listeners (Push Updates)
**AbletonOSC**:
- `/live/device/start_listen/parameter/value <track_index> <device_index> <parameter_index>`
- Automatic push notifications when parameter changes

**Fadebender**:
- ✅ Can GET parameters on demand
- ❌ No live listeners/push updates

**Impact**: UI doesn't update when parameters change in Live

#### 14. Beat Synchronization
**AbletonOSC**:
- `/live/song/start_listen/beat`
- `/live/song/get/beat` - Pushed on every beat

**Fadebender**: ❌ Not implemented

**Impact**: Can't sync UI animations to beat

#### 15. Selection Control
**AbletonOSC**:
- `/live/view/get/selected_track`
- `/live/view/set/selected_track <track_index>`
- `/live/view/get/selected_scene`
- `/live/view/set/selected_scene <scene_index>`
- `/live/view/get/selected_clip`
- `/live/view/set/selected_clip <track_index> <scene_index>`
- `/live/view/get/selected_device`
- `/live/view/set/selected_device <track_index> <device_index>`

**Fadebender**: ❌ Not explicitly implemented (may have indirect control via "open track 1")

#### 16. Session Recording & Arrangement
**AbletonOSC**:
- `/live/song/set/session_record <0|1>`
- `/live/song/get/session_record_status`
- `/live/song/set/arrangement_overdub <0|1>`
- `/live/song/set/back_to_arranger <0|1>`
- `/live/song/set/punch_in <0|1>`, `/live/song/set/punch_out <0|1>`
- `/live/song/set/record_mode <value>`

**Fadebender**: ❌ Not implemented

#### 17. Additional Song Properties
**AbletonOSC**:
- Groove amount
- Clip trigger quantization
- MIDI recording quantization
- Nudge up/down
- Root note / scale settings
- Signature numerator/denominator

**Fadebender**: ❌ Not implemented

#### 18. Arrangement Clips
**AbletonOSC**:
- `/live/track/get/arrangement_clips/name <track_id>`
- `/live/track/get/arrangement_clips/length <track_id>`
- `/live/track/get/arrangement_clips/start_time <track_id>`

**Fadebender**: ❌ Not implemented (session view focused)

#### 19. MIDI CC Mapping
**AbletonOSC**:
- `/live/midimap/map_cc <track_id> <device_id> <param_id> <channel> <cc>`

**Fadebender**: ❌ Not implemented

---

## 📊 Feature Gap Summary

### Fadebender Strengths vs AbletonOSC:
✅ Natural language interface (huge UX advantage)
✅ Smart UI with context-aware capabilities
✅ Topology queries (send analysis, state bundles)
✅ Remote Script features (device reorder/delete, renaming)
✅ Integrated HTTP + Chat
✅ Typo correction & fuzzy matching

### AbletonOSC Strengths vs Fadebender:
✅ Complete clip fire/stop control
✅ Track arm/monitoring
✅ Clip playing status
✅ Song-level undo/redo
✅ Track colors & metering
✅ Cue points
✅ Track routing info
✅ Clip loop markers & warping
✅ MIDI note manipulation
✅ Parameter listeners (push updates)
✅ Beat sync
✅ Selection control

---

## ⭐ Minimum Features to Add for Competitive Parity

To match core session view workflow, prioritize these **5 features**:

### 1. Clip Fire/Stop ⭐⭐⭐ (CRITICAL)
**Why**: Fundamental for session view performance
**Implementation**:
- NLP: "fire track 1 clip 2", "stop track 1 clip 3"
- HTTP: POST /clip/fire, POST /clip/stop
- Remote Script: clip.fire(), clip.stop()

### 2. Scene Fire (NLP Support) ⭐⭐⭐ (HIGH)
**Why**: HTTP exists, just need NLP for chat interface
**Implementation**:
- NLP: "fire scene 1", "trigger scene 2"
- Reuse existing HTTP endpoint

### 3. Track Arm/Monitoring ⭐⭐⭐ (HIGH)
**Why**: Essential for recording workflow
**Implementation**:
- NLP: "arm track 1", "set track 2 monitoring to auto"
- HTTP: POST /track/arm, POST /track/monitoring
- Remote Script: track.arm, track.current_monitoring_state

### 4. Clip Playing Status ⭐⭐ (MEDIUM-HIGH)
**Why**: Visual feedback for what's playing
**Implementation**:
- NLP: "is track 1 clip 2 playing?"
- HTTP: GET /clip/status
- Visual: Indicators in UI
- Remote Script: clip.is_playing, track.playing_slot_index

### 5. Song-Level Undo/Redo ⭐⭐ (MEDIUM)
**Why**: Undo clip/track operations, not just parameters
**Implementation**:
- NLP: "undo", "redo"
- HTTP: POST /song/undo, POST /song/redo
- Remote Script: song.undo(), song.redo()

---

## 🎯 Recommended Implementation Priority

**Phase 1 (Session View Essentials):**
1. Clip fire/stop
2. Scene fire NLP
3. Clip playing status

**Phase 2 (Recording Workflow):**
4. Track arm/monitoring
5. Song undo/redo

**Phase 3 (Enhanced Control):**
6. Track colors
7. Clip delete/duplicate
8. Cue points

**Phase 4 (Advanced):**
9. Track metering (live updates)
10. Parameter listeners
11. Clip loop markers

**Out of Scope (For Now):**
- MIDI note manipulation (complex, may not fit chat interface)
- Beat sync (nice but not critical)
- Arrangement clips (if session view focused)
- MIDI CC mapping (advanced use case)

---

## Conclusion

**Fadebender's NLP + Smart UI is a huge competitive advantage over AbletonOSC's raw OSC commands.**

The main gaps are in **session view clip control** (fire/stop) and **recording workflow** (arm/monitoring). Adding the 5 minimum features above would give Fadebender competitive parity for core workflows while maintaining its superior UX.

After that, focus on where Fadebender can differentiate further:
- Smarter topology queries
- Workflow automation (chains of commands)
- Context-aware suggestions
- Better visualization of project state
