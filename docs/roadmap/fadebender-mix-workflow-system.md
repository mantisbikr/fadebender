# Fadebender Mix Workflow System
**Project Planning, Task Tracking, Change Logging, Device Snapshots, Navigation, Roles, and Bidirectional Sync**

This document defines the internal architecture for Fadebender’s workflow layer:
- DAW-aware tasks + priorities
- Real-time parameter change logging
- Device preset snapshotting + reversible deletion/restore
- Two-way locator & marker navigation system
- Focus Mode with loop length and dimming
- Track Roles / Semantic Layer (multi-role tagging)
- Full bidirectional sync between Fadebender and Ableton Live

All features are implemented **single-user-first**, but the schema is **multi-user ready**.

---

## 1. DATA MODEL (FIRESTORE)

### Collections
```
/workspaces/{workspaceId}
/projects/{projectId}
/liveSets/{liveSetId}
/tracks/{trackId}
/devices/{deviceId}
/markers/{markerId}
/snapshots/{snapshotId}
/tasks/{taskId}
/changeLog/paramEvents/{eventId}
/changeLog/paramEditGroups/{groupId}
/changeLog/transactions/{txnId}
/deviceCapsules/{capsuleId}
/deviceTombstones/{tombstoneId}
```

### Common Fields
```json
{
  "workspaceId": "default",
  "projectId": "p1",
  "ownerId": "local-owner",
  "createdBy": "local-owner",
  "updatedBy": "local-owner",
  "createdAt": 1731070000000,
  "updatedAt": 1731070000000,
  "visibility": "private"
}
```

---

## 2. TASK SYSTEM

Tasks represent **mix decisions** tied to musical context.

### Task Document
```json
{
  "title": "Tame sibilance on Lead Vox",
  "status": "todo",
  "priority": "high",
  "refs": [
    {"type": "track", "id": "track-vox"},
    {"type": "device", "id": "dev-deesser"},
    {"type": "marker", "id": "chorus1"}
  ],
  "labels": ["vocals","harshness"]
}
```

### UI
- Task panel in Track / Return / Device view
- Global task overview drawer
- NLP-driven “Add / Show / Complete task”

---

## 3. PARAMETER CHANGE LOGGING

### Param Event (atomic)
```json
{
  "txnId": "txn_ABC",
  "source": "fb-ui | nlp | automation | live-ui",
  "scope": {"trackId": "track-vox","deviceId": "dev-deesser","paramId": "amount"},
  "value": {"from": {"norm":0.32}, "to": {"norm":0.41}}
}
```

### Edit Group
Groups UI drag changes into single logical movement.

### Transaction
Represents a semantic intent (e.g., “reduce vocal harshness”).

### Revert
- Revert group
- Revert entire transaction

---

## 4. DEVICE SNAPSHOTS (CAPSULES) & RESTORE

### Capsule (preset loaded)
```json
{
  "capsuleId": "cap_9f",
  "trackId": "t1",
  "slotIndex": 2,
  "preset": {"name":"Large Hall","hash":"sha256:..."},
  "params": [...]
}
```

### Delta (tweaks)
```json
{
  "capsuleId": "cap_9f",
  "diff": [{"paramId":"decay","from":"5.2s","to":"4.1s"}]
}
```

### Tombstone (device removed)
```json
{
  "tombstoneId": "ts_...",
  "capsuleId": "cap_9f",
  "restorable": true
}
```

### Restore Options
- As Loaded
- As Tweaked
- Full Chain (for racks)

---

## 5. LIVE SYNC & ECHO SUPPRESSION

- Fadebender sends commands with `txnId`
- Live adapter echoes back param/device events
- Fadebender ignores events with recently-sent `txnId`

### Reconciliation Loop
- Periodically compare Live state vs database
- Resolve differences using **last writer wins** except **recent Live change → user override**

---

## 6. MARKERS, LOCATORS & NAVIGATION

Fadebender mirrors Ableton Locators and adds its own Markers.

### Marker Document
```json
{
  "markerId": "marker_fb_sibilance_check",
  "source": "fadebender | live",
  "name": "Chorus 1",
  "timecode": "57.3.0",
  "barsFromHere": 8,
  "private": false,
  "links": {"taskId": null, "snapshotId": null}
}
```

### Two-Way Sync (You Selected **A**)
- If `source:"fadebender"` and `private:false` → create/update Live Locator
- Live locator edits sync back into Fadebender

---

## 7. FOCUS MODE (LOOP + DIM + SOLO)

When focusing on a task, track group, or marker:
- Loop ±X bars around playhead (`barsFromHere` default = 4)
- Dim all **non‑scope** tracks (e.g., −6 dB)
- Optionally solo scope tracks

### Focus Profile
```json
{
  "loop": {"bars": 8},
  "mix": {"dimOthersDb": 6, "soloReferenced": false},
  "scope": {"trackIds": ["t1","t2"]}
}
```

---

## 8. AUDIT POINTS (NO AUDIO INGEST REQUIRED)

Fadebender does **not** listen to audio.  
Instead, we use a **Probe Rack** with metering devices whose **GR parameters are readable**.

### Probe Rack (Invisible, Bypassed)
- Limiter → Gain Reduction
- Compressor → Gain Reduction
- Multiband Dynamics → Per‑band GR

### Example Triggers
| Condition | Auto-Marker |
|---|---|
| Limiter GR > 3 dB for ≥ 300ms | “Limiter working hard here” |
| Vocal Comp GR > 6 dB sustained | “Over‑compression risk” |
| Silence (GR ≈ max) ≥ 2s | “Potential dead zone” |
| Hi‑band GR high vs mid/low | “Potential harshness hotspot” |

Auto-markers are written into Fadebender, and if `private:false`, also into Live.

---

## 9. CAPABILITY CARD BACK/FORWARD HISTORY

Each view push stored in:
```ts
type ViewRef = {type:'track'|'device'|'task'|'navigator', id?:string}
```

Buttons: **← Back** and **→ Forward**  
Keyboard: `⌘[` / `⌘]`

---

## 10. TRACK ROLES / SEMANTIC LAYER (MULTI‑ROLE TAGGING)

Tracks can have **multiple roles**, allowing Fadebender to understand mix structure.

```json
{
  "roles": ["lead-vocal","airy","emotional-focus"],
  "notes": "Main vocal body; watch sibilance."
}
```

### Role Groups
- Vocals, Guitars, Drums, Keys/Synths, Bass, FX, Buses
- Creative descriptors allowed

### NLP Examples
- “Label Track 3 as **Lead Vocal + Airy**”
- “Show only **drums**”
- “Focus on **vocals and bass** for 8 bars, dim others 9 dB”

---

## 11. ROLE PICKER UI (CONFIGURABLE)

Users may switch:
- **Grouped View** (structured by family)
- **Flat View** (single tag cloud)

Persisted per-project:
```json
{
  "ui": {"rolePicker": {"view": "grouped | flat"}}
}
```

---

## 12. IMPLEMENTATION ROADMAP

1) Task System & UI  
2) Device Capsules + Restore  
3) Locator Sync + Marker Navigation  
4) Focus Mode w/ Loop + Dim  
5) Probe Rack + Audit Points  
6) Track Roles + Role Picker Modes  
7) Mix Progress Heatmap (future)

---

# End of Document
