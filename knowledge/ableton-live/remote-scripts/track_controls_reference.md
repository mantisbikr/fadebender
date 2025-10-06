---
title: "Ableton Live Track Controls via Remote Script (LOM Reference)"
version: "1.0"
category: "Ableton Live Remote Scripts"
description: "Comprehensive mapping of all controllable track-level parameters and functions in Ableton Live via the Python Remote Script API (Live Object Model), annotated with recommended Fadebender control surfaces (UI, LLM, or Both)."
last_updated: "2025-10-05"
tags: ["ableton", "remote-script", "fadebender", "lom", "track-control", "ui-llm-mapping"]
---

# 🎚️ Ableton Live Track Controls via Remote Script

This document details all **track-level parameters, routing options, and functions** accessible via the **Live Object Model (LOM)** — the foundation of custom Python Remote Scripts in Ableton Live.  

It specifies:  
- The **object path** used in the LOM hierarchy  
- Whether it can be **read/written**  
- Fadebender’s recommended **control surface** ownership — whether it should be managed through **UI**, **LLM chat**, or **Both**

---

## ⚙️ Track Control Reference Table

| **Parameter / Function** | **Object Path** | **Description** | **LOM Access** | **Recommended Control Surface** |
|---|---|---|---|---|
| **Track Name** | `Track.name` | Rename the track. | ✅ RW | **LLM** — “rename track 2 to vocals” |
| **Track Color** | `Track.color` | Set the color of the track header. | ✅ RW | **UI** (color picker) |
| **Track Type** | `Track.has_audio_input`, `Track.has_midi_input` | Indicates whether the track handles audio or MIDI. | ✅ Read | UI |
| **Mute / Unmute** | `Track.mute` | Toggle mute state. | ✅ RW | **Both** |
| **Solo / Unsolo** | `Track.solo` | Solo the track. | ✅ RW | **Both** |
| **Arm for Recording** | `Track.arm` | Arm/disarm track for recording. | ✅ RW | **Both** |
| **Track Volume** | `Track.mixer_device.volume` | Controls the output level. | ✅ RW | **Both** |
| **Track Pan** | `Track.mixer_device.panning` | Left-right balance. | ✅ RW | **Both** |
| **Send Levels (A/B/C)** | `Track.mixer_device.sends[]` | Send amount per return track. | ✅ RW | **Both** |
| **Crossfader Assign** | `Track.mixer_device.crossfade_assign` | Assign track to crossfader A/B/X. | ✅ RW | **UI** |
| **Monitor State** | `Track.current_monitoring_state` | Set to “In”, “Auto”, or “Off”. | ✅ RW | **UI** |
| **Freeze / Unfreeze** | `Track.freeze_track()`, `Track.unfreeze_track()` | Freeze track audio. | ✅ Execute | **LLM** (confirmation recommended) |
| **Delete Track** | `LiveSet.delete_track(track)` | Remove track. | ✅ Execute | **LLM (with confirmation)** |
| **Fold State** | `Track.fold_state` | Collapse or expand track (esp. MIDI). | ✅ RW | **UI** |
| **Group / Ungroup** | `Track.group_track`, `Track.is_grouped` | Manage group assignments. | ✅ RW | **UI** |
| **Input Routing (Audio From)** | `Track.input_routing_type`, `Track.input_routing_channel` | Select audio input device and channel. | ✅ RW | **UI** |
| **Output Routing (Audio To)** | `Track.output_routing_type`, `Track.output_routing_channel` | Choose audio output or bus. | ✅ RW | **UI** |
| **MIDI Routing (From/To)** | `Track.input_routing_type`, `Track.output_routing_type` | Set MIDI device routing. | ✅ RW | **UI** |
| **Automation Arm** | `Track.automation_arm` | Enable or disable automation writing. | ✅ RW | **Both** |
| **Device Chain Access** | `Track.devices[]` | Access device list. | ✅ RW | **Both** |
| **Device Parameter Control** | `DeviceParameter.value` | Adjust any parameter value. | ✅ RW | **Both** |
| **Device Bypass / On-Off** | `Device.parameters[0]` | Toggle device enabled/disabled. | ✅ RW | **Both** |
| **Load Device Preset** | `Track.drop_device(file_path)` | Load device or rack from file. | ✅ Execute | **LLM** |
| **Clip Slot List** | `Track.clip_slots[]` | All clip slots on the track. | ✅ RW | **Both** |
| **Launch Clip** | `ClipSlot.fire()` | Launch a clip. | ✅ Execute | **Both** |
| **Stop Clip** | `ClipSlot.stop()` | Stop clip playback. | ✅ Execute | **Both** |
| **Create Empty Clip** | `ClipSlot.create_clip(length)` | Create a new clip of specified length. | ✅ Execute | **LLM** |
| **Duplicate Clip** | `ClipSlot.duplicate_clip_to(target)` | Duplicate an existing clip. | ✅ Execute | **LLM** |
| **Clip Rename** | `Clip.name` | Rename clip. | ✅ RW | **LLM** |
| **Clip Length** | `Clip.loop_end - loop_start` | Set total loop length. | ✅ RW | **Both** |
| **Clip Looping** | `Clip.looping` | Toggle looping on/off. | ✅ RW | **Both** |
| **Clip Start Position** | `Clip.start_marker` | Adjust where playback begins. | ✅ RW | **Both** |
| **Clip Warp Toggle** | `Clip.warping` | Enable/disable warping. | ✅ RW | **UI** |
| **Clip Quantization** | `Clip.quantization` | Set quantize mode. | ✅ RW | **UI** |
| **Scene Launch / Stop** | `Scene.fire()`, `Scene.stop_all_clips()` | Launch or stop a scene. | ✅ Execute | **Both** |
| **Scene Rename** | `Scene.name` | Rename scene. | ✅ RW | **LLM** |
| **Scene Tempo / Time Sig Override** | `Scene.tempo`, `Scene.time_signature` | Local tempo/time signature overrides. | ✅ RW | **UI + LLM** |
| **Automation Envelope Access** | `ClipEnvelope` | Read/write envelope data. | ✅ RW | **UI + LLM** |
| **Track Playing Slot Index** | `Track.playing_slot_index` | Indicates current playing clip index. | ✅ Read | **UI** |
| **Track Output Meter** | *(not officially exposed)* | Peak/RMS metering (requires C-API). | ❌ | **UI (future)** |

---

## 🔁 Return Track Controls

Return tracks are accessed via `LiveSet.return_tracks[]` and expose a similar `Track` interface with mixer and devices, but no clips.

| **Parameter / Function** | **Object Path** | **Description** | **LOM Access** | **Recommended Control Surface** |
|---|---|---|---|---|
| Return Name | `ReturnTrack.name` | Rename return (A/B/C…). | ✅ RW | LLM |
| Return Color | `ReturnTrack.color` | Color of return header. | ✅ RW | UI |
| Volume | `ReturnTrack.mixer_device.volume` | Return output level. | ✅ RW | Both |
| Pan | `ReturnTrack.mixer_device.panning` | Return L/R balance. | ✅ RW | Both |
| Mute / Solo | `ReturnTrack.mute/solo` | Mute or solo the return bus. | ✅ RW | Both |
| Devices List | `ReturnTrack.devices[]` | Enumerate devices on return. | ✅ RW | Both |
| Device On/Off | `Device.parameters[0]` | Toggle device enabled. | ✅ RW | Both |
| Device Parameter | `DeviceParameter.value` | Adjust parameter value. | ✅ RW | Both |
| Insert Device/Preset | `ReturnTrack.drop_device(path)` | Add device/rack to return. | ✅ Exec | LLM (with confirm) |
| Return→Return Sends (optional) | `ReturnTrack.mixer_device.sends[]` | Only if enabled in Live prefs. | 🟡 | UI |

Notes:
- Return tracks do not have clip slots. Scene/clip commands do not apply.
- Return→return sends depend on Live preferences/version; treat as optional and behind a feature flag.

---

## 🎚️ Master Track Controls

The master bus is accessed via `LiveSet.master_track`. Common mixer parameters are available; avoid destructive actions.

| **Parameter / Function** | **Object Path** | **Description** | **LOM Access** | **Recommended Control Surface** |
|---|---|---|---|---|
| Master Volume | `MasterTrack.mixer_device.volume` | Main output level. | ✅ RW | Both |
| Crossfader | `MasterTrack.mixer_device.crossfader` | A↔B blend. | ✅ RW | UI + LLM |
| Cue Volume (if exposed) | `MasterTrack.mixer_device.cue_volume` | Cue bus level. | 🟡 RW | UI |
| Devices List | `MasterTrack.devices[]` | Enumerate master devices. | ✅ RW | UI |
| Device On/Off | `Device.parameters[0]` | Toggle device enabled. | ✅ RW | UI |
| Device Parameter | `DeviceParameter.value` | Adjust parameter value. | ✅ RW | UI |

Notes:
- Not all Live versions expose `cue_volume` in the same way; handle gracefully if missing.
- No clips on master; clip/scene ops do not apply directly.

---

## 🎛️ Control Surface Ownership Summary

| **Category** | **UI Only** | **LLM Only** | **Both (Bidirectional)** |
|---|---|---|---|
| **Routing & Monitoring** | Input/Output routing, Monitor, Crossfader | — | — |
| **Track Metadata** | Color, Type, Group hierarchy | Rename | — |
| **Mixing (Tracks/Returns/Master)** | — | — | Volume, Pan, Mute, Solo, Sends (tracks), Crossfader |
| **Clips & Scenes (Tracks only)** | Warp, Quantize | Create, Duplicate, Rename | Launch, Stop, Loop, Length |
| **Devices & Presets** | Macro mapping | Load/Insert preset to track/return/master | On/Off, Parameter control |
| **Automation** | Graph view & editing | “Add fade out”, “automate filter” | Read/write envelopes |
| **Transport** | Loop brace visuals | “Set tempo 120”, “start recording” | Play, Stop, Record, Tempo |
| **Browser / Library** | — | “Add reverb preset to track 2” | — |
| **Monitoring** | Meters | “Is track clipping?” (query) | — |

---

## 💡 Implementation Guidelines

- **UI Controls** should manage precise parameters: faders, dials, meters, routing selectors, and color pickers.  
- **LLM Chat Controls** handle contextual or intent-driven actions (“add reverb”, “make the snare wider”, “loop this clip for 8 bars”).  
- **Both** categories should use *bidirectional synchronization* so UI updates reflect LLM changes in real time.  

Every controllable value in `Track.mixer_device`, `DeviceParameter`, and `Clip` supports **value listeners**, enabling the Remote Script to send state updates back to the Fadebender UI or chat layer.

---

## 🧠 Integration Tip

> For best results, design each Track in Fadebender as a **data node** with a reactive schema:  
> ```json
> {
>   "id": "track_2",
>   "name": "Vocals",
>   "type": "audio",
>   "volume": 0.85,
>   "pan": -0.1,
>   "sends": { "A": 0.25, "B": 0.60 },
>   "devices": [ "Compressor", "EQ Eight", "Reverb" ],
>   "clip_slots": 10,
>   "armed": true,
>   "solo": false,
>   "mute": false
> }
> ```
>  
> The LLM or UI can then read/write to this unified structure through the Remote Script bridge.

---

*Maintained by: Fadebender Core Team*  
*Last Updated: 2025-10-05*
