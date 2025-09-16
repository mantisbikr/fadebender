# Fadebender – Roadmap (Concise)

## Next
- Fix 400 errors in intent execution in `master-controller/src/index.ts`; verify MIDI CC output reaches DAW.
- Validate end-to-end flow NLP → Controller → Logic with simple volume intents.
- Add structured error logging and diagnostics in controller service.
- Prepare Ableton adapter scaffolding and interface contracts (see `docs/roadmap.md:7`).

## Later
- Multi-DAW expansion (Ableton, Cubase) per `knowledge/DAW-ROADMAP.md`.
- Versioning system (undo/redo, snapshots) per `knowledge/VERSIONING-ARCHITECTURE.md`.
- Learning system and preference modeling (post v0.1 stability).

## Notes
- Full plan lives in `docs/roadmap.md` (MVP scope, architecture, milestones).
- Current known issues and sprint goals summarized in `PROJECT-STATUS.md`.

