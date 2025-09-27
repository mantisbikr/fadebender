# Multi‑User Architecture and Local DAW Connectivity

Goal
- Allow many users to use Fadebender from the cloud while controlling their own local Ableton Live installs securely.

Key design
- Hybrid model: Cloud services for chat, parsing, and knowledge; a small local connector (agent) on each user’s machine to reach Ableton Live.
- The local connector connects outbound to the cloud (WebSocket/WebRTC), so users don’t need to open ports.

Components
- Cloud
  - Web UI (chat)
  - API Gateway (FastAPI/Node)
  - NLP Service (Vertex/HTTP LLM)
  - Session + Auth (JWT/OAuth)
  - Intent router (per session)
- Local (user machine)
  - Fadebender Agent (native bridge) + Ableton Remote Script
  - Outbound secure tunnel (WSS/WebRTC) to Cloud
  - Executes commands from cloud and returns results/events

Flow
- User logs in on Web UI → gets a session
- Local Agent signs in (device token) → opens an outbound WSS/WebRTC to Cloud
- When the user issues a command in the browser, Cloud routes the validated intent to that user’s active agent
- Agent translates to UDP JSON to the Remote Script (127.0.0.1:19845) and returns results
- Events (selection, parameter changes) stream back to Cloud to keep Chat + Sidebar in sync

Security
- Per‑user auth: tokens bound to user + device
- End‑to‑end TLS for agent ↔ cloud; no inbound ports on user machine
- Rate limiting and allowlist on server + agent; clamping on agent before sending to Live

Packaging for users
- What they install locally:
  1) Ableton Remote Script (Fadebender) — copied into Live’s MIDI Remote Scripts folder
  2) Fadebender Agent app (macOS first) — signs in and runs a secure connection to Cloud
- What runs in Cloud:
  - Web app + APIs + NLP (your infrastructure; can be multi‑tenant)

Development modes
- Local‑only (dev): run everything on localhost with the UDP stub or Live
- Hybrid (staging): web UI from Cloud, agent local, NLP can be Cloud or local HTTP
- Full SaaS (prod): all users use the same cloud endpoints; agents per machine per user

Model providers (Model Garden)
- Switch providers via env at NLP service:
  - Vertex (Gemini/Model Garden): `LLM_PROVIDER=vertex`, `GEMINI_MODEL=...`
  - OpenAI‑compatible HTTP (local Llama): `LLM_PROVIDER=http`, `LLAMA_ENDPOINT/KEY/MODEL`
- UI exposes provider + model selector; server passes through to NLP

Roadmap mapping
- Phase 1–2: Local dev complete; add Remote Script + minimal agent (can reuse native‑bridge‑mac)
- Phase 3–6: Sidebar, history, resolver, background agent/events
- Phase 7: Provider switch (Model Garden)
- Phase 8–9: Observability + docs

FAQ
- Can a user run with only the web app? No — to control their local Live, they need the local agent + Remote Script.
- Can multiple users share one Live? Not supported; each agent controls the local Live it’s attached to.
- Windows support? Yes, with a Windows agent and the same Remote Script layout (path differs).
