# Fadebender — Multi-DAW NLP Conductor (MVP Plan)

> **Project name:** **Fadebender**  
> **Alt options:** MixPilot, Condukt, BusDriver, FaderPilot, OrchestrAID

**Goal:** Build a minimal, demo-ready system where a user types natural language (or speaks) and DAW parameters change accordingly. Focus on **Ableton Live** first, then consider **Cubase**.

---

## 0) High-level Scope

- **MVP v0.1 (Ableton)**  
  - Use Remote Scripts API to read/write track/device states.  
  - Confirm changes and mirror state.

- **MVP v0.3 (Cubase)**  
  - Use MIDI Remote API (Cubase 12+). Two-way mapping possible.

---

## 1) Repo & Folder Setup

```
fadebender/
  README.md
  /docs/
    roadmap.md
    api.md
  /nlp-service/                # Python FastAPI (rules now, LLM later)
    app.py
    requirements.txt
    intents/
      parser.py
      patterns.yml
      tests/
  /master-controller/          # TypeScript core
    src/
      index.ts
      mapping.ts
      scaling.ts
      execute.ts
      types.d.ts
      adapters/
        ableton.ts
        ableton.ts
        cubase.ts
    test/
    package.json
  /native-bridge-mac/          # Swift bridge for CoreMIDI
    BridgeApp.xcodeproj/
    Sources/
      AppDelegate.swift
      WebSocketServer.swift
      MidiOut.swift
    README.md
  /clients/
    /web-chat/                 # Minimal React UI
    /vscode-extension/         # Optional VS Code panel
  /configs/
    mapping.json               # one-track mapping for v0.1
  /scripts/
    seed_mapping.py
    send_test_cc.py
```

---

## 2) Architecture (MVP)

```mermaid
flowchart LR
    UI["Web Chat / VS Code Panel"]
    NLP["NLP Service (FastAPI)"]
    CTRL["Master Controller (TypeScript)"]
    BR["Native Bridge (Swift, CoreMIDI)"]
    
    LIVE["Ableton Live (Remote Scripts)"]
    CUBASE["Cubase (MIDI Remote API)"]
    MAPS["Mapping Registry (mapping.json)"]

    UI --> NLP --> CTRL
    CTRL <---> MAPS
    CTRL -->|WS JSON| BR
    
    CTRL --> LIVE
    CTRL --> CUBASE
```

---

## 3) Data Contracts

**Intent (NLP → Controller)**

```json
{
  "intent": "set_parameter",
  "targets": [{"track": "Track 1", "plugin": null, "parameter": "volume"}],
  "operation": {"type": "absolute", "value": -6, "unit": "dB"},
  "meta": {"utterance": "set track one volume to minus six dB"}
}
```

**Bridge Message (Controller → Bridge)**

```json
{
  "op": "emit_cc",
  "payload": [{"cc": 20, "channel": 1, "value": 96, "target": "Track 1 Volume"}]
}
```

---

## 4) Mapping Registry (v0.1)

```json
{
  "version": 1,
  "mappings": [
    {
      "alias": "track1.volume",
      "target": {"track": "Track 1", "parameter": "volume"},
      "midi": {"cc": 20, "channel": 1},
      "scale": {"type": "linear", "in_min": -60, "in_max": 6, "out_min": 0, "out_max": 127}
    }
  ]
}
```

---

## 5) Component Specs

### NLP Service (FastAPI)
- `POST /parse` → intent JSON  
- `POST /howto` → DAW help answers  
- Start with regex + rules, LLM later.

### Master Controller (TS)
- Loads mapping.json  
- `executeIntent()` → resolve targets, scale values, send to Bridge  
- Maintains shadow state

### Native Bridge (Swift)
- Creates CoreMIDI virtual port `Fadebender Out`  
- WebSocket server at `localhost:17890`  
- Accepts JSON → emits CCs

---

## 6) Ableton Live Setup (v0.1)

1. Install the Fadebender Remote Script in your Ableton User Library.  
2. Ensure the UDP bridge is running and reachable.  
3. Verify Track 1 volume can be set via the server.

---

## 7) Ableton Adapter (v0.2)

- Create Remote Script in `User Library/Remote Scripts/Fadebender/`.  
- Expose TCP/WS channel.  
- Implement `set`, `get`, and `event` for parameters.  
- Example:

```json
// Controller → Ableton Script
{ "op": "set", "track": 1, "device": "Reverb", "param": "Dry/Wet", "value": 0.25 }

// Ableton Script → Controller
{ "op": "event", "track": 1, "param": "Volume", "value": -6.0 }
```

---

## 8) Cubase Adapter (v0.3)

- Use Cubase 12+ MIDI Remote API (JS/TS).  
- Create a virtual surface and map track/device params.  
- Enable feedback to Controller.

---

## 9) Dev Quickstart

```bash
# Clone repo
git clone <repo> fadebender && cd fadebender

# NLP
cd nlp-service
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload &

# Controller
cd ../master-controller
npm i && npm run dev &

# Bridge (Swift)
open native-bridge-mac/BridgeApp.xcodeproj
# Run from Xcode
```

---

## 10) Milestones

- **M1 (Day 1–3):** Bridge up, can move volume via Ableton Remote Script.  
- **M2 (Day 4–6):** NLP → Controller → Ableton (absolute volume).  
- **M3 (Day 7–10):** Add relative ops, pan, reverb wet.  
- **M4 (Day 11–14):** Ableton adapter (track vol/pan, device wet).  
- **M5 (Day 15–18):** Ableton feedback + scenes/macros groundwork.

---

## 11) Example Utterances

- “set track one volume to minus six dB”  
- “make track one two dB louder”  
- “pan track one left 20%”  
- “increase reverb wet by 10%”  
- “how do I sidechain the pad to the kick in Ableton?”

---
