# Fadebender

**Fadebender** is an NLP-driven conductor for your DAW.
It lets you type or speak natural language commands like:

- “set track one volume to minus six dB”
- “pan track two left 20 percent”
- “increase reverb wet on bus one by 10 percent”
- “how do I sidechain the pad to the kick?”

and have those actions carried out directly inside Logic Pro, Ableton Live, or Cubase.

---

## 🚀 Project Goals

- **MVP v0.1 (Logic-first):**
  Control a single track volume and one plugin parameter in Logic via Controller Assignments + MIDI Bridge.

- **MVP v0.2 (Ableton):**
  Add full state-aware control using Remote Scripts (Python API).

- **MVP v0.3 (Cubase):**
  Support Cubase 12+ MIDI Remote API for two-way parameter mapping.

---

## 🛠 Quickstart

1. Run NLP Service
   ```bash
   cd nlp-service
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   uvicorn app:app --reload
   ```

2. Run Master Controller
   ```bash
   cd ../master-controller
   npm install
   npm run dev
   ```

3. Run Bridge
   - Open `native-bridge-mac/BridgeApp.xcodeproj` in Xcode.
   - Run → creates virtual MIDI port "Fadebender Out".

4. In Logic
   - Open Controller Assignments → Learn → move Track 1 Volume.
   - Send a test CC from `/scripts/send_test_cc.py`.
   - Logic maps Track 1 Volume ↔ CC#20.

5. Test End-to-End
   - POST `"set track one volume to -6 dB"` to NLP → Controller → Bridge → Logic fader moves.

---

## Developer Setup

- Read the scaffold and acceptance criteria in `docs/Fadebender_Codex_Handoff.md`.
- The roadmap is in `docs/roadmap.md` (copied from `Fadebender_MVP.md`).

---

## 📂 Repo Structure

```
fadebender/
  README.md
  /docs/
    roadmap.md
    api.md
    Fadebender_MVP.md
    Fadebender_Codex_Handoff.md
  /nlp-service/            # FastAPI service for parsing utterances
  /master-controller/      # TypeScript orchestrator
  /native-bridge-mac/      # Swift MIDI/WS bridge for macOS
  /clients/                # web-chat + vscode extension
  /configs/                # mapping.json and env
  /scripts/                # helpers + test scripts
```

---

© 2025 Fadebender Project

