# Fadebender Refactor Plan (Assessment + Phases)

This plan outlines refactor opportunities across the codebase with low‑risk “quick wins” and a phased path. No behavior changes are intended; focus is modularity, testability, and startup/runtime reliability.

---

## Scope Summary
- Monolith hotspots and mixed concerns:
  - `server/app.py:1` (~1,594 lines) mixes bootstrap, models, legacy shims, and long handlers.
  - Large routers: `server/api/overview.py:1` (937 lines), `server/api/device_mapping.py:1` (883), `server/api/returns.py:1` (648), `server/api/tracks.py:1` (520).
  - Heavy service: `server/services/chat_service.py:1` (very large; duplicates `udp_request`, broad responsibilities).
- Duplications:
  - `udp_request` in `server/app.py:86` and `server/services/chat_service.py:49`.
  - `_MASTER_DEDUP` in `server/app.py:81` and `server/core/events.py:40`.
  - Request models (`VolumeDbBody`/`IntentParseBody`) appear in multiple places (`server/app.py:186`, `server/app.py:192`, `server/api/ops.py:232`).
- Config/CORS/env scattered in `server/app.py:96`, `server/app.py:118` instead of centralized helpers.
- Blocking work in request handlers (e.g., `learn_return_device_quick` in `server/app.py:698`).

---

## Goals
- Thin application entrypoints; domain logic lives in services.
- Single source for shared models, shims, config, and caches.
- Async‑friendly handlers; heavy work offloaded or scheduled.
- Clear module boundaries enable unit tests and future packaging.

---

## Quick Wins (0.5–1 day)
- Remove local duplicates:
  - Use `_MASTER_DEDUP` only from `server/core/events.py` (stop defining in app).
  - Use a single `VolumeDbBody` from `server/api/ops.py` (or a shared models module) instead of redefining in `server/app.py:192`.
  - Drop `IntentParseBody` from `server/app.py:186` if unused; otherwise move to `server/models/requests.py`.
- Wrap startup calls in lifecycle hooks:
  - Move `start_ableton_event_listener` and `schedule_live_index_tasks` from bottom of `server/app.py` into `@app.on_event("startup")` or FastAPI lifespan.
- Centralize `udp_request` shim:
  - Create `server/services/backcompat.py` with `udp_request` and import where needed.

---

## Phase 1: App/Config Structure (1–2 days)
- App bootstrap split:
  - `server/app.py` → keep FastAPI init + `include_router` only.
  - New `server/bootstrap.py` → env load (`dotenv`), CORS config, lifespan startup.
  - New `server/config/helpers.py` → `_status_ttl_seconds`, `_cors_origins`, typed settings accessors.
- Shared models:
  - New `server/models/requests.py` for request DTOs used across routers.
  - Ensure routers import shared DTOs; remove duplicates from files.
- Tests: add smoke tests for app import and basic route mount checks.

---

## Phase 2: Router Decomposition (3–5 days)
- Split large routers by concern:
  - `server/api/overview.py` → `overview_status.py` (transport/mixer snapshot) + `overview_devices.py` (devices/capabilities) + `overview_cache.py` (cached summaries).
  - `server/api/device_mapping.py` → carve out import/export helpers to `server/services/device_mapping_io.py`; keep router thin.
  - `server/api/returns.py` and `server/api/tracks.py` → extract repeated mixer/device helpers to `server/services/mixer_readers.py` and `server/services/device_readers.py`.
- Move shared utilities now imported ad‑hoc (e.g., `ensure_capabilities`) under `server/api/cap_utils.py` or a service module and dedupe call‑sites.
- Tests: unit tests for extracted services (pure functions), keep routers minimal.

---

## Phase 3: Learning/Chat Services (3–5 days)
- Parameter learning:
  - Move `learn_return_device_quick` from `server/app.py:698` into `server/api/learn.py` (router) and `server/services/param_learning_quick.py` (service).
  - Make probing/reads async‑friendly (optionally `run_in_executor`) and configurable delays.
- Chat service modularization:
  - Split `server/services/chat_service.py` into:
    - `chat_models.py` (pydantic request/response)
    - `chat_handlers.py` (route handlers orchestrating services)
    - `chat_summarizer.py` (format/summary generation)
    - `chat_backcompat.py` (shim to canonical intent execution)
  - Remove local `udp_request`; import from `backcompat.py`.

---

## Phase 4: Config + Security Harden (1–2 days)
- CORS and origins:
  - Single parser in `server/config/helpers.py`; allow env var list and dev “allow all”.
- Token gating (optional, LAN):
  - Add short‑lived pairing token middleware; configurable on/off.
- Settings surface:
  - Typed settings object with `.from_env()` used by app and services, reducing scattered `os.getenv` calls.

---

## Phase 5: Performance + Background Work (2–3 days)
- Background tasks:
  - Offload long‑running probes/learning and periodic indexing to a background scheduler (e.g., `asyncio.create_task` + queues) rather than blocking handlers.
- Update cadence manager:
  - Introduce `UpdateManager` to modulate polling (transport always; mixer/devices conditional) and make it per‑connection if feasible.

---

## Coding Conventions
- Routers: thin controllers calling services; no sleeps or heavy logic.
- Services: pure or side‑effect modules with clear inputs/outputs; easy to test.
- Models: shared Pydantic DTOs live under `server/models`.
- Config: helpers under `server/config/helpers.py`; avoid direct `os.getenv` in handlers.

---

## Validation Checklist
- App imports fast; basic routes mounted.
- No duplicate definitions of shared models or shims.
- Large files reduced in size:
  - `server/app.py` < 300 lines
  - Each router file < 400 lines
- Async handlers do not block; long work scheduled/backgrounded.
- Unit tests pass; quick smoke test for startup hooks.

---

## Notes on NLP Service
- Similar structure can be applied incrementally to `nlp-service/`:
  - Centralize env/config in one module; remove repeated `MappingStore()` instantiation across fetchers.
  - Keep `audio_assistant/` modular (already in good shape); consider a small CLI to prebuild manual index for prod.

