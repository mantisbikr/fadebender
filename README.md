# Fadebender

**Fadebender** is an intelligent NLP-driven conductor for your DAW that provides expert-level audio engineering advice through natural conversation.

It lets you type commands like:
- "I want spaciousness to my vocals" → ChromaVerb Synth Hall preset recommendations
- "add punch to my drums" → Multipressor settings with professional compression ratios
- "set track one volume to minus six dB" → Direct parameter control
- "go back to how track 2 sounded 5 minutes ago" → Complete version control

**Current Status (Sept 14, 2024)**: Core architecture and professional knowledge base complete. Intent execution pipeline needs debugging.

Fadebender transforms natural language into professional mixing workflows, making advanced audio engineering techniques accessible through conversation.

---

## 🚀 Project Goals

- **MVP v0.1 (Ableton-only):**
  Add state-aware control using Ableton Remote Scripts (Python API) and a UDP bridge. Control a single track volume and one device parameter end-to-end.

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

4. In Ableton
   - Load the Remote Script and ensure the UDP bridge is running.
   - Confirm you can ping the script from the server and move Track 1 volume via API.

## 📘 User Onboarding

- For non‑technical users and future cloud releases, see `docs/USER_ONBOARDING.md`.
- To install the Ableton Remote Script manually during development, see `docs/ABLETON_SETUP.md`.

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
