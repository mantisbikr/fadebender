# Execution Plan (Next Phases)

This document tracks the prioritized phases after Step 9.

Phase 1 — Ableton Remote Script MVP
- Implement UDP JSON bridge: ping, get_overview, get_track_status, set_mixer, set_send, set_device_param
- LOM helpers: volume/pan/mute/solo, sends list/values, selected device/param count
- Clamp, throttle on script side
- Acceptance: /ping ok, /status shows project, /op/mixer and readback work

Phase 2 — Server cache + Project outline
- server/ableton/cache.py to maintain tracks/sends/devices
- Endpoints: GET /project/outline, GET /track/:id/status
- Optional: push events from Live → server to update cache

Phase 3 — UI: Sidebar + History
- Left sidebar with tabs: Project, History
- History endpoints: POST /history/log, GET /history/recent; replay with Preview/Execute toggle

Phase 4 — Resolver + Clarification
- Map nouns to names ("vocals" → matching tracks); synonyms, alias memory
- Structured clarification when ambiguous or missing fields; store choices for session

Phase 5 — Background Project Agent
- Agent + Remote Script send selection/value change events (throttled)
- Cache reflects Live within ~200 ms; sidebar updates

Phase 6 — Model Garden switching
- NLP supports provider/model selection (Vertex Gemini, Model Garden Llama, local HTTP/OpenAI compatible)
- UI exposes provider + model dropdown and passes selections to /intent/parse and /chat

Phase 7 — Observability + Safety polish
- Structured logs, rate limit per-field, undo/redo coverage for sends, basic device params

Phase 8 — Docs & QA
- ABLETON_SETUP.md finalized with script install; screenshots/GIFs
- Acceptance script expanded to 10–15 commands

Links
- docs/ABLETON_SETUP.md — install Live Remote Script
- docs/ARCHITECTURE_MULTIUSER.md — cloud + local agent design
- docs/RUNBOOK.md — day‑to‑day dev runbook
- docs/INTENT_SUPPORT.md — canonical intents + examples
