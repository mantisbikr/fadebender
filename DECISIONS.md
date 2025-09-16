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

## 2025-09-14 — Logic Control Path
- Context: Need quick path to move parameters in Logic Pro.
- Decision: Use CoreMIDI virtual port + Controller Assignments with CC mappings from `configs/mapping.json`.
- Consequences: Simple, write-focused control; limited readback; reliable for MVP demos.
- Links: docs/roadmap.md:2, configs/mapping.json:1

## 2025-09-14 — Knowledge Base Strategy
- Context: Ground responses in expert audio practices and DAW specifics.
- Decision: Keep curated knowledge in-repo under `knowledge/` and integrate into system prompt.
- Consequences: Deterministic grounding; easy iteration; size grows with scope.
- Links: knowledge/DAW-ROADMAP.md:1, knowledge/shared/audio-engineering-principles.md:1

