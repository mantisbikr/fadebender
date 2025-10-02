# Fadebender — First Codex Prompt

**You are setting up a new repo named `fadebender`. Follow these instructions exactly.**

---

## 1) Create repo + docs

- Create a new folder `fadebender/`.
- Inside `fadebender/docs/`, add these two files **using the contents I provide**:
  - `Fadebender_MVP.md` (the roadmap/architecture)
  - `Fadebender_Codex_Handoff.md` (the scaffold guide)
- Create a root `README.md` from the provided README content.

---

## 2) Scaffold the repository exactly as specified

- Read `docs/Fadebender_Codex_Handoff.md` fully.
- Create the folder tree and files exactly as shown under **Repository Scaffold**.
- Fill in **minimal, runnable stubs**:
  - **nlp-service/** (FastAPI): `app.py` with `POST /parse` and `POST /howto` stub endpoints; `requirements.txt` with `fastapi`, `uvicorn`, `pydantic`.
  - **master-controller/** (TypeScript): `src/` with `types.d.ts`, `mapping.ts`, `scaling.ts`, `execute.ts`, `index.ts`; `package.json` with `dev` script; `tsconfig.json`.
  - **native-bridge-mac/** (Swift): Xcode project placeholder; `Sources/` with `AppDelegate.swift`, `WebSocketServer.swift`, `MidiOut.swift` as **stubs** that compile (no complex logic yet). The virtual MIDI port **must** be named **“Fadebender Out”** in code comments/placeholders.
  - **clients/web-chat/**: minimal React app with a textarea and two buttons (“Control” → call `/parse`, then `/execute-intent`; “Help” → call `/howto`).
  - **clients/vscode-extension/**: minimal extension skeleton that opens a webview panel (stub).

---

## 3) Configs & scripts

- Create `/configs/mapping.json` with the single starter mapping for `Track 1 Volume` (as shown in the handoff doc).
- Create `/scripts/send_test_cc.py` as a stub that will later send a test `emit_cc` to the Bridge (put TODOs).

---

## 4) Wire basic flows

- In **master-controller**, implement:
  - Load `configs/mapping.json`.
  - `scaling.ts`: linear dB ↔ CC mapping function with clamping.
  - `execute.ts`: take a parsed intent and return a Bridge message `{ op: "emit_cc", payload: [...] }`.
  - `index.ts`: tiny HTTP server exposing `POST /execute-intent` that forwards the Bridge message to `ws://127.0.0.1:17890` (don’t implement WS yet—just leave a TODO and echo the message in logs).
- In **nlp-service**, implement a **rule-based** parser for:
  - Absolute volume (e.g., “set track 1 volume to -6 dB”).
  - Relative volume (e.g., “make track 1 2 dB louder”) — add a TODO if not implemented yet.
  - Return the **Intent JSON** exactly as in the doc.

---

## 5) Acceptance criteria

- `npm run dev` runs the controller without errors.
- `uvicorn app:app --reload` runs the NLP service without errors.
- Project structure **matches** the scaffold in the handoff doc.
- `configs/mapping.json` exists and loads in the controller.
- The controller can **echo** a Bridge JSON message for a parsed NLP intent (WS send can be a TODO).

---

## 6) Documentation updates

- Copy the content from `docs/Fadebender_MVP.md` into `docs/roadmap.md`.
- Keep `docs/Fadebender_Codex_Handoff.md` as-is and link to it from the root `README.md` under a “Developer Setup” section.

---

## 7) Important naming rules

- Use the exact names **“Fadebender”** (product) and **“Fadebender Out”** (virtual MIDI port) everywhere.
- Do not invent additional files or rename anything.

---

## 8) Final output requirements

When finished, list:  
- The full tree of created files  
- The commands to run each service  
- Any TODOs left in code  

---
