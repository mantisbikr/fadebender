# Decisions Log

Each entry: Context, Decision, Consequences, Links (concise).

## 2025-09-14 — NLP Provider
- Context: MVP needs simple AI parsing with local fallback.
- Decision: Use Google Gemini 1.5 Flash when `GOOGLE_API_KEY` is set; otherwise rule-based fallback.
- Consequences: Network optional; consistent API; enable richer /howto responses.
- Links: nlp-service/app.py:23, nlp-service/app.py:43, nlp-service/app.py:60

## 2025-09-14 — Service Architecture
- Context: Clear separation of parsing, orchestration, and DAW I/O.
- Decision: Polyglot architecture: FastAPI NLP (`nlp-service/`), TS controller (`master-controller/`), Swift native bridge (`native-bridge-mac/`).
- Consequences: Strong boundaries; more repos/languages to maintain; easier perf/isolation.
- Links: docs/roadmap.md:73, master-controller/package.json:1, native-bridge-mac/

## 2025-09-14 — Ableton Control Path
- Context: Need a reliable path to move parameters in Ableton Live.
- Decision: Use Ableton Remote Script + UDP bridge for indexed ops; map intents to LOM operations.
- Consequences: Two-way state, safer ops, better readback; more initial scripting.
- Links: docs/roadmap.md:2

## 2025-09-14 — Knowledge Base Strategy
- Context: Ground responses in expert audio practices and DAW specifics.
- Decision: Keep curated knowledge in-repo under `knowledge/` and integrate into system prompt.
- Consequences: Deterministic grounding; easy iteration; size grows with scope.
- Links: knowledge/DAW-ROADMAP.md:1, knowledge/shared/audio-engineering-principles.md:1
