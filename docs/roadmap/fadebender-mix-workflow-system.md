# Fadebender Mix Workflow System
**Project Planning, Task Tracking, Change Logging, Device Snapshots, and Bidirectional Sync**

This document defines the internal architecture for Fadebender’s workflow layer:
- DAW-aware tasks + priorities
- Real-time parameter change logging
- Device preset snapshotting + reversible deletion/restore
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

### Common Fields (included in all docs)
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

This ensures **no schema refactor** when multi-user support is added later.

---

## 2. TASK SYSTEM (PROJECT PLANNING)

### Purpose
Enable users to **prioritize and track decisions** directly tied to:
- Tracks
- Returns
- Master
- Devices
- Timeline positions (markers)

### Task Document
```json
{
  "title": "Tame sibilance on Lead Vox",
  "status": "todo",
  "priority": "high",
  "refs": [
    {"type":"track","id":"track-vox"},
    {"type":"device","id":"dev-deesser"},
    {"type":"marker","id":"chorus1","timecode":"57.3.0"}
  ],
  "labels": ["vocals","harshness"]
}
```

### UI Features
- **Task Panel** on each Track/Return/Master/Device view.
- **Global Task Drawer** with filters (status, priority, context).
- **Focus Mode**: if user chooses a task, surface **only** controls related to its refs.

### NLP Examples
| User Query | Action |
|---|---|
| “What are my high priority items?” | Filter: `priority=high`, `status in todo/doing` |
| “Add a task: fix the reverb tail on Return B.” | Create task, infer `return-b` reference |
| “Mark shorten predelay task as done.” | Update nearest matched task |

---

## 3. PARAMETER CHANGE LOGGING

Capture changes whether they happen in **Fadebender** or **Ableton Live UI**.

### Param Event (atomic)
```json
{
  "txnId": "txn_ABC",
  "source": "fb-ui | nlp | automation | live-ui",
  "scope": {
    "trackId": "track-vox",
    "deviceId": "dev-deesser",
    "paramId": "amount"
  },
  "value": {
    "from": {"norm":0.32,"display":"-3.1 dB"},
    "to": {"norm":0.41,"display":"-1.7 dB"}
  }
}
```

### Edit Group (drag smoothing)
Group multiple fast param changes:
```json
{
  "groupId": "grp_123",
  "from": "12 ms",
  "to": "25 ms",
  "eventCount": 9
}
```

### Transactions
```json
{
  "txnId": "txn_ABC",
  "trigger": "reduce vocal harshness",
  "source": "nlp"
}
```

### Revert
- **Revert group** = restore param to `from`
- **Revert txn** = revert all included groups in order

---

## 4. DEVICE SNAPSHOTS (CAPSULES) & DELETION RESTORE

### When a preset is loaded:
```json
{
  "capsuleId": "cap_9f",
  "trackId": "t1",
  "slotIndex": 2,
  "device": {"kind":"Reverb","version":"12.0.15"},
  "preset": {"name":"Large Hall","hash":"sha256:..."},
  "params": [...full param dump...],
  "chainPath": []
}
```

### When tweaked:
```json
{
  "capsuleDeltaId": "cd_...",
  "capsuleId": "cap_9f",
  "diff": [{"paramId":"decay","from":"5.2s","to":"4.1s"}]
}
```

### When deleted:
```json
{
  "tombstoneId": "ts_...",
  "capsuleId": "cap_9f",
  "trackId": "t1",
  "slotIndex": 2,
  "restorable": true
}
```

### Restore options:
- Restore **as originally loaded**
- Restore **with tweaks applied**
- Restore **entire chain** (if rack)

---

## 5. BIDIRECTIONAL SYNC WITH ABLETON LIVE

### Live Adapter emits:
```
deviceAdded
deviceRemoved
deviceMoved
paramChanged
presetLoaded
```

### Fadebender sends:
```
setParam(liveDeviceId, liveParamId, norm, txnId)
insertDevice(...)
removeDevice(liveDeviceId)
moveDevice(...)
```

### Echo Suppression
Ignore incoming events that match recent `txnId` (2s TTL).

### Reconciliation Loop (every 1–2s)
1. Pull Live inventory
2. Compare with local mirror
3. Detect adds/removes/moves/param changes
4. Log or update model

### Conflict Rule
**Last writer wins**, unless change occurs within 750ms guard window → treat as **live-ui override**.

---

## 6. UI SUMMARY

| Location | Display | Actions |
|---|---|---|
| Track / Return / Device panel | Tasks + changes + presets | Add Task, Jump to Context, Focus Mode |
| Task Drawer | All tasks, filters, NLP actions | Mark Done, Show Context |
| Change Log View | Param change groups & transactions | Revert group/txn |
| Deleted Devices Drawer | Tombstones | Restore As Loaded / As Tweaked |

---

## 7. IMPLEMENTATION ORDER

1) Task storage + UI panels  
2) NLP → Task CRUD & filtering  
3) Parameter event + grouping  
4) Device capsules + tombstones  
5) Live adapter + echo suppression  
6) Focus Mode + Daily Summary

---

## RESULT

Fadebender becomes the **workflow brain** of the mix:
- Remembers *why* changes were made
- Helps users *finish* mixes
- Enables undo/restore safety
- Supports natural language-driven workflow
