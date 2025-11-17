
# AbletonOSC API – Summary Markdown

_Source: ideoforms/AbletonOSC GitHub README (accessed Nov 16, 2025). This is a structured summary so you can quickly compare Fadebender’s capabilities against the OSC surface area._

AbletonOSC exposes a set of OSC namespaces under `/live/...` that mirror Live’s internal Live Object Model (LOM). Messages are sent **to** AbletonOSC on port `11000`, and replies are sent **from** AbletonOSC on port `11001` to the sender’s IP.

---

## 1. Application API

Basic communication, logging, and status utilities.

### 1.1 Commands

- `/live/test`  
  Ping: shows a confirmation in Live and sends an OSC reply.

- `/live/application/get/version`  
  Returns Live’s version (major + minor).

- `/live/api/reload`  
  Reloads the AbletonOSC Python code (development hot‑reload).

- `/live/api/get/log_level`  
  Query current log level.

- `/live/api/set/log_level <log_level>`  
  Set log level. Valid levels: `debug`, `info`, `warning`, `error`, `critical`.

- `/live/api/show_message <message>`  
  Show a text message in Live’s status bar.

### 1.2 Automatic status messages (push)

These are pushed automatically from AbletonOSC to your OSC client:

- `/live/startup` – sent when AbletonOSC starts.
- `/live/error <error_msg>` – sent when an internal error occurs.

---

## 2. Song API

Represents the top‑level `Song` object. Covers transport, global parameters, scene/track creation, and cue points.

### 2.1 Song actions (methods)

- `/live/song/capture_midi`
- `/live/song/continue_playing`
- `/live/song/create_audio_track <index>`  
  Create audio track at index (`-1` = append to end).
- `/live/song/create_midi_track <index>`  
  Create MIDI track at index (`-1` = append to end).
- `/live/song/create_return_track`
- `/live/song/create_scene <index>`  
  Create scene at index (`-1` = append to end).
- `/live/song/cue_point/jump <cue_point>`  
  Jump to cue by name or numeric index.
- `/live/song/cue_point/add_or_delete`  
  Toggle cue at current playhead (add if none, delete if exists).
- `/live/song/cue_point/set/name <cue_index> <name>`  
  Rename cue.
- `/live/song/delete_scene <scene_index>`
- `/live/song/delete_return_track <track_index>`
- `/live/song/delete_track <track_index>`
- `/live/song/duplicate_scene <scene_index>`
- `/live/song/duplicate_track <track_index>`
- `/live/song/jump_by <beats>`  
  Move song position by given beat offset.
- `/live/song/jump_to_next_cue`
- `/live/song/jump_to_prev_cue`
- `/live/song/redo`
- `/live/song/start_playing`
- `/live/song/stop_playing`
- `/live/song/stop_all_clips`
- `/live/song/tap_tempo`
- `/live/song/trigger_session_record`
- `/live/song/undo`

### 2.2 Song property listeners

- You can listen to any song property via:  
  `/live/song/start_listen/<property>`  
- Replies are sent to:  
  `/live/song/get/<property>`  
  with the property’s current value.

### 2.3 Song property getters (selection)

- `/live/song/get/arrangement_overdub`
- `/live/song/get/back_to_arranger`
- `/live/song/get/can_redo`
- `/live/song/get/can_undo`
- `/live/song/get/clip_trigger_quantization`
- `/live/song/get/current_song_time`
- `/live/song/get/groove_amount`
- `/live/song/get/is_playing`
- `/live/song/get/loop`
- `/live/song/get/loop_length`
- `/live/song/get/loop_start`
- `/live/song/get/metronome`
- `/live/song/get/midi_recording_quantization`
- `/live/song/get/nudge_down`
- `/live/song/get/nudge_up`
- `/live/song/get/punch_in`
- `/live/song/get/punch_out`
- `/live/song/get/record_mode`
- `/live/song/get/root_note`
- `/live/song/get/scale_name`
- `/live/song/get/session_record`
- `/live/song/get/session_record_status`
- `/live/song/get/signature_denominator`
- `/live/song/get/signature_numerator`
- `/live/song/get/song_length`
- `/live/song/get/tempo`

### 2.4 Song property setters

- `/live/song/set/arrangement_overdub <0|1>`
- `/live/song/set/back_to_arranger <0|1>`
- `/live/song/set/clip_trigger_quantization <value>`
- `/live/song/set/current_song_time <beats>`
- `/live/song/set/groove_amount <value>`
- `/live/song/set/loop <0|1>`
- `/live/song/set/loop_length <beats>`
- `/live/song/set/loop_start <beats>`
- `/live/song/set/metronome <0|1>`
- `/live/song/set/midi_recording_quantization <value>`
- `/live/song/set/nudge_down <value>`
- `/live/song/set/nudge_up <value>`
- `/live/song/set/punch_in <0|1>`
- `/live/song/set/punch_out <0|1>`
- `/live/song/set/record_mode <value>`
- `/live/song/set/session_record <0|1>`
- `/live/song/set/signature_denominator <int>`
- `/live/song/set/signature_numerator <int>`
- `/live/song/set/tempo <bpm>`

### 2.5 Scene / track / cue helpers

- `/live/song/get/cue_points`  
  Returns list of cue names and times.
- `/live/song/get/num_scenes`
- `/live/song/get/num_tracks`
- `/live/song/get/track_names [index_min index_max]`  
  Track names, optionally restricted to a range.
- `/live/song/get/track_data <start_idx> <end_idx> <prop...>`  
  Bulk query for track/clip/clip_slot properties (e.g. `track.name`, `clip.name`, `clip.length`).

### 2.6 Beat events

- `/live/song/start_listen/beat`  
  Enable periodic beat messages.
- `/live/song/get/beat`  
  Beat messages arrive here with current beat index.
- `/live/song/stop_listen/beat`

---

## 3. View API

Represents `Application.View`/`Song.View`. Lets you query and set selection in the Live UI.

### 3.1 Getters

- `/live/view/get/selected_scene`
- `/live/view/get/selected_track`
- `/live/view/get/selected_clip`
- `/live/view/get/selected_device`

### 3.2 Setters

- `/live/view/set/selected_scene <scene_index>`
- `/live/view/set/selected_track <track_index>`
- `/live/view/set/selected_clip <track_index> <scene_index>`
- `/live/view/set/selected_device <track_index> <device_index>`

### 3.3 Selection listeners

- `/live/view/start_listen/selected_scene`
- `/live/view/start_listen/selected_track`
- `/live/view/stop_listen/selected_scene`
- `/live/view/stop_listen/selected_track`

---

## 4. Track API

Represents audio, MIDI, return, or master tracks. Controls routing, arm/solo/mute, metering, and access to clips and devices.

### 4.1 Methods

- `/live/track/stop_all_clips <track_id>`

### 4.2 Track property listeners

- Start listener:  
  `/live/track/start_listen/<property> <track_index>`  
- Responses arrive at:  
  `/live/track/get/<property>` with `<track_index>` and value.

### 4.3 Track getters (selection)

- `/live/track/get/arm`
- `/live/track/get/available_input_routing_channels`
- `/live/track/get/available_input_routing_types`
- `/live/track/get/available_output_routing_channels`
- `/live/track/get/available_output_routing_types`
- `/live/track/get/can_be_armed`
- `/live/track/get/color`
- `/live/track/get/color_index`
- `/live/track/get/current_monitoring_state`
- `/live/track/get/fired_slot_index`
- `/live/track/get/fold_state`
- `/live/track/get/has_audio_input`
- `/live/track/get/has_audio_output`
- `/live/track/get/has_midi_input`
- `/live/track/get/has_midi_output`
- `/live/track/get/input_routing_channel`
- `/live/track/get/input_routing_type`
- `/live/track/get/output_routing_channel`
- `/live/track/get/output_routing_type`
- `/live/track/get/output_meter_left`
- `/live/track/get/output_meter_right`
- `/live/track/get/output_meter_level`
- `/live/track/get/is_foldable`
- `/live/track/get/is_grouped`
- `/live/track/get/is_visible`
- `/live/track/get/mute`
- `/live/track/get/name`
- `/live/track/get/panning`
- `/live/track/get/playing_slot_index`
- `/live/track/get/send <track_id> <send_id>`
- `/live/track/get/solo`
- `/live/track/get/volume`

### 4.4 Track setters

- `/live/track/set/arm <track_id> <0|1>`
- `/live/track/set/color <track_id> <color>`
- `/live/track/set/color_index <track_id> <index>`
- `/live/track/set/current_monitoring_state <track_id> <state>`
- `/live/track/set/fold_state <track_id> <0|1>`
- `/live/track/set/input_routing_channel <track_id> <channel>`
- `/live/track/set/input_routing_type <track_id> <type>`
- `/live/track/set/mute <track_id> <0|1>`
- `/live/track/set/name <track_id> <name>`
- `/live/track/set/output_routing_channel <track_id> <channel>`
- `/live/track/set/output_routing_type <track_id> <type>`
- `/live/track/set/panning <track_id> <value>`
- `/live/track/set/send <track_id> <send_id> <value>`
- `/live/track/set/solo <track_id> <0|1>`
- `/live/track/set/volume <track_id> <value>`

### 4.5 Track: multiple clips

- `/live/track/get/clips/name <track_id>`
- `/live/track/get/clips/length <track_id>`
- `/live/track/get/clips/color <track_id>`
- `/live/track/get/arrangement_clips/name <track_id>`
- `/live/track/get/arrangement_clips/length <track_id>`
- `/live/track/get/arrangement_clips/start_time <track_id>`

### 4.6 Track: devices overview

- `/live/track/get/num_devices <track_id>`
- `/live/track/get/devices/name <track_id>`
- `/live/track/get/devices/type <track_id>`  
  Device type values: 1 = audio effect, 2 = instrument, 4 = MIDI effect.
- `/live/track/get/devices/class_name <track_id>`  
  e.g. `Reverb`, `Operator`, `AuPluginDevice`, `PluginDevice`, `InstrumentGroupDevice`, etc.

---

## 5. Clip Slot API

Represents a single clip slot (container for a clip).

### 5.1 Methods & properties

- `/live/clip_slot/fire <track_index> <clip_index>`  
  Trigger/stop clip in this slot.
- `/live/clip_slot/create_clip <track_index> <clip_index> <length>`  
  Create a new clip of given length (beats).
- `/live/clip_slot/delete_clip <track_index> <clip_index>`
- `/live/clip_slot/get/has_clip <track_index> <clip_index>`
- `/live/clip_slot/get/has_stop_button <track_index> <clip_index>`
- `/live/clip_slot/set/has_stop_button <track_index> <clip_index> <0|1>`
- `/live/clip_slot/duplicate_clip_to <track_index> <clip_index> <target_track_index> <target_clip_index>`

---

## 6. Clip API

Represents audio or MIDI clips: playback, notes, loop markers, pitch, and color.

### 6.1 Methods

- `/live/clip/fire <track_id> <clip_id>`
- `/live/clip/stop <track_id> <clip_id>`
- `/live/clip/duplicate_loop <track_id> <clip_id>`

### 6.2 Notes

- `/live/clip/get/notes <track_id> <clip_id> [start_pitch pitch_span start_time time_span]`  
  Query MIDI notes in the clip (optional time/pitch range).
- `/live/clip/add/notes <track_id> <clip_id> <pitch> <start_time> <duration> <velocity> <mute> ...`
- `/live/clip/remove/notes [start_pitch pitch_span start_time time_span]`  
  Remove notes in a given region (or all if no range).

### 6.3 Clip properties

- `/live/clip/get/color`
- `/live/clip/set/color`
- `/live/clip/get/name`
- `/live/clip/set/name`
- `/live/clip/get/gain`
- `/live/clip/set/gain`
- `/live/clip/get/length`
- `/live/clip/get/pitch_coarse`
- `/live/clip/set/pitch_coarse`
- `/live/clip/get/pitch_fine`
- `/live/clip/set/pitch_fine`
- `/live/clip/get/file_path`
- `/live/clip/get/is_audio_clip`
- `/live/clip/get/is_midi_clip`
- `/live/clip/get/is_playing`
- `/live/clip/get/is_recording`
- `/live/clip/get/playing_position`
- `/live/clip/start_listen/playing_position`
- `/live/clip/stop_listen/playing_position`
- `/live/clip/get/loop_start`
- `/live/clip/set/loop_start`
- `/live/clip/get/loop_end`
- `/live/clip/set/loop_end`
- `/live/clip/get/warping`
- `/live/clip/set/warping`
- `/live/clip/get/start_marker`
- `/live/clip/set/start_marker`
- `/live/clip/get/end_marker`
- `/live/clip/set/end_marker`

---

## 7. Scene API

Trigger scenes and control scene‑level metadata (name, color, tempo, time signature).

### 7.1 Methods

- `/live/scene/fire <scene_id>`
- `/live/scene/fire_as_selected <scene_id>`  
  Fire and advance selection.
- `/live/scene/fire_selected`  
  Fire currently selected scene and advance selection.

### 7.2 Scene property listeners

- Start listening: `/live/scene/start_listen/<property> <scene_index>`  
- Replies: `/live/scene/get/<property>` with `<scene_index>` and value.

### 7.3 Scene getters

- `/live/scene/get/color`
- `/live/scene/get/color_index`
- `/live/scene/get/is_empty`
- `/live/scene/get/is_triggered`
- `/live/scene/get/name`
- `/live/scene/get/tempo`
- `/live/scene/get/tempo_enabled`
- `/live/scene/get/time_signature_numerator`
- `/live/scene/get/time_signature_denominator`
- `/live/scene/get/time_signature_enabled`

### 7.4 Scene setters

- `/live/scene/set/name <scene_id> <name>`
- `/live/scene/set/color <scene_id> <color>`
- `/live/scene/set/color_index <scene_id> <index>`
- `/live/scene/set/tempo <scene_id> <tempo>`
- `/live/scene/set/tempo_enabled <scene_id> <0|1>`
- `/live/scene/set/time_signature_numerator <scene_id> <num>`
- `/live/scene/set/time_signature_denominator <scene_id> <den>`
- `/live/scene/set/time_signature_enabled <scene_id> <0|1>`

---

## 8. Device API

Represents an instrument or effect device on a track/return/master. Lets you inspect and control device parameters.

### 8.1 Parameter listeners

- `/live/device/start_listen/parameter/value <track_index> <device_index> <parameter_index>`  
  Subscribe to updates for a single parameter. Replies are delivered to the corresponding `/live/device/get/...` address.

### 8.2 Device info getters

- `/live/device/get/name <track_id> <device_id>`  
  Human‑readable device name (the one shown in Live’s UI).
- `/live/device/get/class_name <track_id> <device_id>`  
  Underlying class (e.g. `Reverb`, `Operator`, `PluginDevice`, `InstrumentGroupDevice`).
- `/live/device/get/type <track_id> <device_id>`  
  Numeric type:  
  - `1` – audio effect  
  - `2` – instrument  
  - `4` – MIDI effect

### 8.3 Parameter lists

- `/live/device/get/num_parameters <track_id> <device_id>`
- `/live/device/get/parameters/name <track_id> <device_id>`  
  Returns list of parameter names.
- `/live/device/get/parameters/value <track_id> <device_id>`  
  Returns list of parameter values.
- `/live/device/get/parameters/min <track_id> <device_id>`  
  Per‑parameter minimums.
- `/live/device/get/parameters/max <track_id> <device_id>`  
  Per‑parameter maximums.
- `/live/device/get/parameters/is_quantized <track_id> <device_id>`  
  Per‑parameter “stepped vs continuous” flags.

### 8.4 Single parameter access

- `/live/device/get/parameter/value <track_id> <device_id> <parameter_id>`
- `/live/device/get/parameter/value_string <track_id> <device_id> <parameter_id>`  
  Returns a human‑friendly formatted value (e.g. `2500 Hz`).
- `/live/device/set/parameters/value <track_id> <device_id> <v1> <v2> ...>`  
  Batch set multiple parameter values in order.
- `/live/device/set/parameter/value <track_id> <device_id> <parameter_id> <value>`

> **Important for Fadebender:** There are _no_ OSC methods here for:
> - adding/removing devices,  
> - reordering devices in the chain, or  
> - loading devices from the library.  
> Those require Remote Script or M4L, not AbletonOSC directly.

---

## 9. MidiMap API

Create MIDI CC mappings to parameters through OSC.

### 9.1 Methods

- `/live/midimap/map_cc <track_id> <device_id> <param_id> <channel> <cc>`  
  Create a mapping so that CC `<cc>` on MIDI channel `<channel>` controls the specified parameter.  
  Note: channel indexing follows the internal API: channel 1 = index `0`.

---

## 10. Utilities

AbletonOSC ships with a console helper:

- `run-console.py`  
  A CLI tool to send OSC commands (e.g. `/live/song/set/tempo 123.0`) and print responses, useful for manual testing and exploration.

---

## 11. Quick Capability Checklist for Fadebender

**AbletonOSC gives you, via OSC:**

- Full song transport & global options (tempo, loop, metronome, cue points).
- Creating and deleting: audio/MIDI/return tracks and scenes.
- Reading/writing most `Song`, `Track`, `Clip`, `Scene` properties.
- Creating/deleting/duplicating clips in session view.
- Reading/creating/removing MIDI notes inside clips.
- Querying arrangement clips (names, length, start times).
- Reading all devices on a track (name, class, type, count).
- Full parameter surface for any device (including min/max, quantization flags).
- View selection control for scene/track/clip/device.
- Track routing, mute/solo/arm, metering, sends, colors.
- MIDI CC mapping via the MidiMap API.

**AbletonOSC does *not* provide OSC commands for:**

- Reordering devices in a chain.  
- Adding or removing devices from the library.  
- Duplicating or moving devices between tracks.  
- Deep file/browse operations (loading samples or presets by filename).  

Those must be implemented via Live’s Python Remote Script (or Max for Live) and, if you want to trigger them from your web UI, exposed via your own OSC or HTTP layer.

---

This markdown file is meant as a practical reference so you can mark off which parts Fadebender already uses (e.g. Song/Track/Device/Clip APIs) and where you might need **Remote Script‑only** extensions (device insertion/reorder, library browsing, automation‑helper workflows, etc.).
