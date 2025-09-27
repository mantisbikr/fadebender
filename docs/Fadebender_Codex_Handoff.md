# Fadebender — Codex Handoff Guide (Scaffold & Bootstrap)

**Context:** You (Codex) have access to `Fadebender_MVP.md`. Read that doc fully and scaffold the repo as specified. This guide is your task list and acceptance criteria.

---

## 1) Repository Scaffold

**Create the folder tree exactly:**
```
fadebender/
  README.md
  /docs/
    roadmap.md
    api.md
  /nlp-service/
    app.py
    requirements.txt
    intents/
      parser.py
      patterns.yml
      tests/
  /master-controller/
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
    tsconfig.json
  /native-bridge-mac/
    BridgeApp.xcodeproj/        # create Xcode project placeholder
    Sources/
      AppDelegate.swift
      WebSocketServer.swift
      MidiOut.swift
    README.md
  /clients/
    /web-chat/
      src/
      package.json
    /vscode-extension/
      src/
      package.json
  /configs/
    mapping.json
    .env.example
  /scripts/
    seed_mapping.py
    send_test_cc.py
```

- Copy the content of **Fadebender_MVP.md** into `docs/roadmap.md` and add a short `README.md` pointing to it.

---

## 2) Minimal Implementations (stubs that run)

### 2.1 NLP Service (FastAPI, Python 3.11)
- `requirements.txt` must include: `fastapi`, `uvicorn`, `pydantic`
- `app.py`:
  - `POST /parse` → parse utterances for track #, parameter {volume|pan}, absolute dB values (e.g., “-6 dB”), and relative (“up 2 dB”).
  - `POST /howto` → return a placeholder string (later backed by LLM).
- `intents/parser.py` → simple regex-based parser with unit tests in `intents/tests/`.
- Include a `run_dev.sh` (optional) that starts uvicorn.

### 2.2 Master Controller (TypeScript, Node 18+)
- `package.json` with scripts:
  - `dev`: `ts-node src/index.ts` (or `tsx src/index.ts`)
  - `test`: `vitest` (or `jest`)
- `src/types.d.ts` → shared interfaces for Intent, Mapping, BridgeMessage.
- `src/mapping.ts` → load `/configs/mapping.json` and expose lookup helpers.
- `src/scaling.ts` → dB↔CC linear mapping + clamping.
- `src/execute.ts` → `executeIntent(intent): BridgeMessage[]`.
- `src/index.ts` → tiny HTTP server with `POST /execute-intent` to call `executeIntent` and post to Bridge WS (`ws://127.0.0.1:17890`).
- Tests for mapping & scaling.

### 2.3 Native Bridge (Swift)
- macOS app that:
  - Opens WebSocket server on `127.0.0.1:17890`.
  - Accepts JSON messages `{ op: "emit_cc", payload: [{ cc, channel, value }] }`.
  - Emits these as MIDI CC on a **virtual destination** named `Fadebender Out`.
- `README.md` with build/run steps in Xcode.

### 2.4 Clients
- **web-chat**: Minimal React page with two tabs: **Control** (sends text to `/parse` then `/execute-intent`) and **Help** (calls `/howto`). No styling needed.
- **vscode-extension**: Placeholder command to open a panel that posts to the same endpoints.

---

## 3) Configs & Scripts

### 3.1 `/configs/mapping.json` (starter)
```json
{
  "version": 1,
  "mappings": [
    {
      "alias": "track1.volume",
      "logic_target": {"track": "Track 1", "parameter": "volume"},
      "midi": {"cc": 20, "channel": 1},
      "scale": {"type": "linear", "in_min": -60, "in_max": 6, "out_min": 0, "out_max": 127},
      "smoothing_ms": 150
    }
  ]
}
```

### 3.2 `/scripts/send_test_cc.py`
- A Python script that opens a UDP/WebSocket to the Bridge and sends a single `emit_cc` for CC#20, ch1, value 96 (for MIDI Learn/testing).

### 3.3 `.env.example`
```
BRIDGE_WS_URL=ws://127.0.0.1:17890
CONTROLLER_PORT=8721
NLP_URL=http://127.0.0.1:8000
```

---

## 4) Quickstart Tasks (must succeed)

1. **Install deps**
   - `cd nlp-service && pip install -r requirements.txt`
   - `cd ../master-controller && npm i`
2. **Run services**
   - `uvicorn app:app --reload` (NLP)
   - `npm run dev` (Controller)
   - Build & run **Bridge** in Xcode (creates `Fadebender Out` MIDI port).
3. **E2E Test**
   - POST to NLP `/parse` with: `"set track one volume to minus six dB"`.
   - Feed intent to Controller `/execute-intent` → confirm fader moves in Ableton.

---

## 5) Acceptance Criteria

- Repo matches the scaffold exactly.
- NLP parses absolute and relative volume; pan is stubbed (TODO).
- Controller returns at least one BridgeMessage for parsed intents.
- Bridge receives JSON and emits MIDI CC to a virtual port named `Fadebender Out`.
- The Ableton fader moves with the Controller path via Remote Script.
- `README.md` documents the above quickstart in 10 steps or fewer.

---

## 6) Stretch (optional if time remains)

- Add **relative volume** (“make track 1 2 dB louder”).
- Add **pan** absolute (“pan left 20%” → CC mapping −100..+100 → 0..127).
- Add rudimentary **undo** in Controller (store last value per alias).

---

## 7) Notes to Keep in Mind

- Keep endpoints localhost only for MVP. Use Ableton Remote Script/UDP for control.
- Keep all network endpoints **localhost only** for MVP.
- Log every action to `/logs/YYYY-MM-DD.log` from Controller for traceability.
