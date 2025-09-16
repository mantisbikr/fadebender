# Fadebender

**Fadebender** is an intelligent NLP-driven conductor for your DAW that provides expert-level audio engineering advice through natural conversation.

It lets you type commands like:
- "I want spaciousness to my vocals" → ChromaVerb Synth Hall preset recommendations
- "add punch to my drums" → Multipressor settings with professional compression ratios
- "set track one volume to minus six dB" → Direct parameter control
- "go back to how track 2 sounded 5 minutes ago" → Complete version control

**Current Status (Sept 14, 2024)**: Core architecture and professional knowledge base complete. Expert AI system functional with Logic Pro workflows. Intent execution pipeline needs debugging.

Fadebender transforms natural language into professional mixing workflows, making advanced audio engineering techniques accessible through conversation.

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

