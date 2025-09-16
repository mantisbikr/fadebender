# Open Questions

Track unresolved questions; mark resolved with links to decisions/commits.

## Unresolved
- Why do effect intents return 400 in controller? Confirm parameter mapping + MIDI emit path (`master-controller/src/`).
- Ableton adapter: Remote Script vs Max for Live bridge? Define control/event protocol (`docs/roadmap.md:7`).
- Versioning storage: SQLite vs file-based snapshots for undo/redo (`knowledge/VERSIONING-ARCHITECTURE.md`).

## Resolved
- NLP provider choice: Use Gemini 1.5 Flash when available; fallback otherwise → DECISION (DECISIONS.md, nlp-service/app.py:23).
- Logic control path via MIDI CC mapping → DECISION (configs/mapping.json, docs/roadmap.md:6).

