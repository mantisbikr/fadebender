# Fadebender Refactor Plan (Assessment + Phases)

This plan outlines refactor opportunities across the codebase with low‑risk “quick wins” and a phased path. No behavior changes are intended; focus is modularity, testability, and startup/runtime reliability.

---

## Progress Update (current status)

What’s completed
- App bootstrap hardening
  - FastAPI init + CORS + error middleware installed; request ID middleware in place.
  - Standard error DTO responses across routers.
- Feature flags and defaults
  - FB_FEATURE_NEW_ROUTING validated and now default ON (no env needed). Use env to disable if necessary.
- Router decomposition (initial)
  - Extracted routers: `server/api/chat.py`, `server/api/nlp.py`, `server/api/system.py`,
    `server/api/overview_status.py`, `server/api/overview_devices.py`, `server/api/learn.py`.
  - Overview split: `/snapshot` is now in `overview_status`; `/snapshot/query` delegated for parity.
- Services extraction
  - Readers: `mixer_readers.py`, `device_readers.py`.
  - Chat split: `chat_models.py`, `chat_summarizer.py`, `chat_handlers.py`.
  - Device mapping I/O: `device_mapping_io.py`.
  - Learning: `param_learning_quick.py`, `param_learning_start.py`, `learn_jobs.py`.
- Value/Unit enrichment
  - `/intent/read` returns `unit`, `min_display`, `max_display` for mixer volume/pan/sends and device params when metadata is available.
- Cleanup in `server/app.py`
  - Removed legacy `op_*` stubs moved to `server/api/ops`.
  - Large inlined learn handler left intentionally for testing (gated by `FB_DEBUG_LEGACY_LEARN`).

What’s pending (pause here until device learning is tested)
- Remove the inlined `/return/device/learn_start` legacy block in `server/app.py` once learning endpoints are verified; rely on `server/api/learn.py`.
- Move remaining preset refresh handler and return-device helper utilities out of `server/app.py` into appropriate service/router modules.
- Add fallback enrichment for device param reads when mapping meta is missing (unit/min/max may be null today).
- Confirm logging middleware outputs single-line JSON including `request_id` and `duration_ms`.

Validation snapshot
- Pan tests: all green via `scripts/run_all_pan_tests.sh`.
- NLP tests (Phase 1): all green for `test_nlp_comprehensive.py --phase1` and `test_nlp_get_comprehensive.py --phase1`.
- WebUI validation: 8/9 passing with a known relative-volume increase failure; verified OK via WebChat UI.

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
- ValueRegistry boundary (low risk):
  - Add `server/services/value_registry.py` façade with `update_mixer(...)`, `update_device_param(...)`, and event emission hooks.
  - All write‑throughs import this façade instead of reaching into registry directly.
- Event broker helper (low risk):
  - Add `server/services/events.py` with `publish(event_name, **payload)` that wraps SSE publishing and handles exceptions/debouncing in one place.

---

## Phase 0a: Incremental Low‑Risk Wins (This Week)
Focus on tiny, reversible changes that reduce risk and enable later phases.

- Health/readiness endpoints
  - Add `/health` (process up) and `/ready` (Remote Script reachable, store ready)
  - Use in dev + CI smoke checks
- Standard error DTO + middleware
  - Error shape: `{ ok: false, code: string, message: string, detail?: any }`
  - Map common errors (e.g., `track_out_of_range`, `unsupported_intent`) to codes
- Config unification (typed settings)
  - Single `Settings.from_env()` used in app + services (ports, origins, timeouts)
- OpenAPI snapshot + diff check in CI
  - Prevent accidental breaking changes before versioning
- Feature flags
  - Tiny env‑based flags per refactor area (e.g., `USE_NEW_ROUTING=false`)
- Token‑bucket rate limiting (dev default off)
  - Simple per‑route limiter for `/op/mixer` and `/op/send`

Acceptance (Phase 0a)
- `/health` and `/ready` return 200; `/ready` fails when Remote Script is down
- Errors return standard DTO in JSON across routers
- `settings.py` consumed by at least app.py and one service
- OpenAPI diff job runs and reports clean
- Env flags toggle behavior in one small area (smoke‑verified)

---

## Phase 1: App/Config Structure (1–2 days)
- App bootstrap split:
  - `server/app.py` → keep FastAPI init + `include_router` only.
  - New `server/bootstrap.py` → env load (`dotenv`), CORS config, lifespan startup.
  - New `server/config/helpers.py` → `_status_ttl_seconds`, `_cors_origins`, typed settings accessors.
- Shared models:
  - New `server/models/requests.py` for request DTOs used across routers.
  - Ensure routers import shared DTOs; remove duplicates from files.
- ValueRegistry façade + DI:
  - Introduce `ValueRegistryService` (façade) and inject via FastAPI `Depends()` where needed.
  - Replace direct `get_value_registry()` calls in routers/services with the façade.
- Event publishing standardization:
  - Replace scattered `broker.publish` calls with `Events.publish(...)` helper; add basic debouncing/backoff for bursty updates.
- Error/logging middleware:
  - Add centralized exception handler mapping to standard error DTO; enable structured JSON logs (request_id, route, latency, status).
- Tests: add smoke tests for app import and basic route mount checks.

---

## Phase 2: Router Decomposition (3–5 days)
- Split large routers by concern:
  - `server/api/overview.py` → `overview_status.py` (transport/mixer snapshot) + `overview_devices.py` (devices/capabilities) + `overview_cache.py` (cached summaries).
  - `server/api/device_mapping.py` → carve out import/export helpers to `server/services/device_mapping_io.py`; keep router thin.
  - `server/api/returns.py` and `server/api/tracks.py` → extract repeated mixer/device helpers to `server/services/mixer_readers.py` and `server/services/device_readers.py`.
- Move shared utilities now imported ad‑hoc (e.g., `ensure_capabilities`) under `server/api/cap_utils.py` or a service module and dedupe call‑sites.
- Snapshot/cache invalidation policy:
  - Document and implement when snapshot is authoritative vs. on‑demand reads.
  - Add explicit cache TTLs; call invalidation hooks from mixer/device write paths.
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
- Rate limiting + backpressure:
  - Wrap learning and chat endpoints with light rate limits and background queue submission where appropriate.

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
- Observability baseline:
  - Add minimal metrics (p50/p95 latency, 4xx/5xx) per router and export via `/metrics` (optional). Establish dashboards later.

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

---

## Plan Assessment & Recommended Enhancements

**Overall Score: 8/10** - Excellent foundation with strong architectural thinking and practical scoping.

### Strengths

**1. Excellent Phasing & Scoping**
- Clear progression from Quick Wins → Complex phases
- Realistic time estimates
- Specific line number references and file sizes
- Low-risk approach ("no behavior changes intended")

**2. Addresses Real Pain Points**
- 1,594-line `app.py` monolith
- Multiple `udp_request` duplications
- Blocking work in handlers
- Scattered config/CORS logic

**3. Good Architectural Principles**
- Thin controllers, fat services
- Single source of truth for models
- Async-friendly design
- Clear module boundaries

**4. Measurable Success Criteria**
- `app.py` < 300 lines
- Routers < 400 lines
- Concrete validation checklist

---

### Critical Gaps & Improvements

**1. Testing Strategy (CRITICAL)**

Add to each phase:
- **Regression test suite BEFORE refactoring starts**
- Integration tests to verify no behavior changes
- How to run existing tests during refactor
- Consider snapshot testing for API responses
- Document which tests must pass before proceeding to next phase

Recommendation: Add comprehensive testing requirements to Phase 0 (see below).

**2. Error Handling & Logging Standardization**

Missing from plan:
- Centralized error handling middleware
- Standardized logging format across modules (structured logging)
- Error response DTOs with consistent shape
- Exception hierarchy for domain errors

Recommendation: Add to Phase 1 or create new "Phase 0.5" before router decomposition.

**3. Data Access Layer**

Plan mentions model duplication but not:
- Firestore access patterns (are they duplicated too?)
- Repository pattern for data access
- Caching strategy for Firestore reads
- Connection pooling and retry logic

Recommendation: Add to Phase 1 or Phase 2.

**3a. ValueRegistry Boundary (NEW)**

Create a façade service for ValueRegistry updates/reads with a stable interface and event hooks. Replace direct calls across services/routers to reduce coupling and ease testing.

**3b. Eventing Consistency (NEW)**

Provide a single `Events.publish(name, **payload)` helper that wraps SSE broker usage, guards exceptions, and offers basic debouncing for bursty updates (e.g., sliders).

**4. Phase Order Consideration**

Phase 4 (Security) should potentially come earlier:
- CORS/token gating issues could block development/testing
- Security should be established before large-scale refactoring

Recommendation: Move CORS/security basics to Phase 1.5, leave token gating in Phase 4.

**5. Rollback Strategy**

Add:
- Feature flags for gradual rollout (per phase or module)
- Branch strategy (trunk-based vs feature branches per phase)
- Rollback plan if phase fails in production
- Canary deployment strategy

**6. Dependency Injection Pattern**

With many new services, clarify:
- Service instantiation pattern
- Dependency injection framework (FastAPI's `Depends()` pattern)
- Service lifecycle management (singleton vs per-request)
- Mock strategies for testing

Example pattern to document:
```python
# server/dependencies.py
def get_mixer_reader() -> MixerReader:
    return MixerReader()

# In router
@router.get("/track/{track_id}/mixer")
async def get_track_mixer(
    track_id: int,
    mixer_reader: MixerReader = Depends(get_mixer_reader)
):
    return await mixer_reader.get_track_mixer(track_id)
```

**7. Phase 2 Timeline May Be Optimistic**

Splitting 4 large routers (937, 883, 648, 520 lines) in 3-5 days:
- Hidden interdependencies often emerge during extraction
- Testing each split thoroughly takes time

Recommendation: Adjust to 5-7 days or split into Phase 2a/2b.

**8. NLP Service Section Needs Detail**

Expand with:
- Specific phases for nlp-service refactor (similar granularity to server/)
- MappingStore() duplication fix details
- audio_assistant module boundaries and interfaces
- CLI prebuild strategy and deployment integration

**9. API Versioning Strategy**

Router splits = good time to add:
- `/v1/` prefix structure
- Deprecation path for old endpoints
- Version negotiation strategy
- Migration guide for clients

**10. Observability & Monitoring**

Add to Phase 5 or establish baseline in Phase 0:
- Metrics/monitoring for new services (latency, error rates)
- Performance baseline BEFORE refactor
- Performance targets POST-refactor
- Health check endpoints for each major service
- Distributed tracing support (OpenTelemetry?)

---

### Recommended Additions

#### Phase 0: Pre-Refactor Preparation (1-2 days)

**Purpose:** Establish safety nets and baseline metrics before making changes.

Tasks:
- **Regression Test Baseline:**
  - Document all existing tests and their pass/fail status
  - Add missing integration tests for critical paths (mixer operations, device control, chat commands)
  - Create API contract tests (request/response shape verification)
  - Set up automated test running on each commit

- **Performance Baseline:**
  - Measure and document current response times for key endpoints
  - Measure startup time
  - Document memory usage patterns
  - Set acceptable degradation thresholds (e.g., no more than 10% slower)

- **API Contract Documentation:**
  - Document all endpoint contracts (request/response schemas)
  - Create OpenAPI/Swagger docs if not present
  - Identify any undocumented endpoints

- **Feature Flag Infrastructure:**
  - Add simple feature flag system for toggling new vs old implementations
  - Example: `USE_NEW_MIXER_SERVICE` flag
  - Allows gradual rollout and easy rollback
- **API Error DTO + Middleware:**
  - Define `{ ok: false, code, message, detail? }` and install global handler
- **Health/Readiness:**
  - Add `/health` and `/ready` endpoints and wire into CI smoke tests

- **Branch Strategy:**
  - Decide: feature branches per phase vs trunk-based with flags
  - Set up CI/CD pipeline to run tests on each phase branch

**Success Criteria:**
- All tests pass and are documented
- Performance baselines recorded
- Feature flag system functional
- Rollback procedure tested
- `/health` and `/ready` implemented; error DTO enforced

---

#### Enhanced Validation Checklist

**Per-Phase Validation:**
- All existing tests pass ✓
- No API contract changes (or documented/versioned) ✓
- Response times within 10% of baseline ✓
- Error rates unchanged or improved ✓
- Memory usage stable or reduced ✓
- Logging captures all request/response cycles ✓
- Code coverage maintained or improved ✓
- No new linter warnings ✓
- Documentation updated for changed modules ✓

**End-to-End Validation:**
- Full integration test suite passes
- Manual smoke testing of critical workflows
- Load testing shows acceptable performance
- Security scan passes (no new vulnerabilities)
- Deployment to staging environment successful

---

#### Risk Mitigation Strategy

**Development Practices:**
- Run each phase on feature branch first
- Pair programming for critical refactors (`chat_service`, `app.py`, large routers)
- Daily standups during active refactoring phases
- Code review required for every phase completion

**Deployment Strategy:**
- Deploy each phase to staging environment first
- Canary deployment (10% → 50% → 100% traffic)
- Monitor error rates and performance metrics during rollout
- Keep previous version running for quick rollback

**Rollback Triggers:**
- Error rate increases by >20%
- Response time increases by >25%
- Any critical functionality broken
- Ableton Live communication failures

**Communication:**
- Notify team before starting each phase
- Daily status updates during active work
- Immediate notification of any issues
- Post-mortem after each phase completion

---

### Expanded NLP Service Refactoring

Apply similar phased approach to `nlp-service/`:

**NLP Quick Wins (0.5 day):**
- Centralize `MappingStore()` instantiation (single source)
- Extract config loading to `nlp-service/config/settings.py`
- Standardize error responses across fetchers

**NLP Phase 1: Service Boundaries (1-2 days):**
- Split intent parsing concerns:
  - `nlp-service/parsers/mixer_parser.py`
  - `nlp-service/parsers/device_parser.py`
  - `nlp-service/parsers/transport_parser.py`
- Shared models in `nlp-service/models/`
- Service interfaces for each parser

**NLP Phase 2: Audio Assistant Optimization (1-2 days):**
- Clarify `audio_assistant/` module boundaries
- Create CLI tool for prebuild manual index:
  ```bash
  python -m nlp_service.audio_assistant.build_index --output data/index.pkl
  ```
- Document deployment process for prebuilt indexes
- Add index validation and health checks

**NLP Phase 3: Firestore Access Layer (1 day):**
- Repository pattern for Firestore access
- Caching layer for frequently-accessed mappings
- Connection pooling and retry logic
- Mock Firestore client for testing

---

### Updated Timeline Estimate

| Phase | Original | Adjusted | Notes |
|-------|----------|----------|-------|
| Phase 0 (NEW) | - | 1-2 days | Critical for safety |
| Phase 0a (NEW) | - | 1 day | Low‑risk enablers |
| Quick Wins | 0.5-1 day | 1 day | Include testing |
| Phase 1 | 1-2 days | 2-3 days | Add error handling |
| Phase 2 | 3-5 days | 5-7 days | Complex router splits |
| Phase 3 | 3-5 days | 4-6 days | Chat service is critical |
| Phase 4 | 1-2 days | 2-3 days | Security needs thorough testing |
| Phase 5 | 2-3 days | 3-4 days | Performance tuning takes time |
| **Total** | **11-18 days** | **18-26 days** | More realistic with testing |

---

### Execution Recommendations

**Start with Phase 0:**
Invest in testing infrastructure upfront - it pays dividends throughout the refactor.

**One Phase at a Time:**
Resist temptation to jump ahead. Complete validation before moving to next phase.

**Maintain Working Software:**
Every commit should leave the codebase in runnable state (even if behind feature flag).

**Document as You Go:**
Update architecture docs after each phase with new structure.

**Celebrate Milestones:**
Each phase completion is a win - acknowledge progress.

---

### Conclusion

This refactoring plan is **solid and well-conceived**. The main enhancements needed are:
1. **Testing infrastructure** (Phase 0)
2. **Error handling standardization** (add to Phase 1)
3. **More realistic timelines** (account for testing and unforeseen issues)
4. **Rollback and risk mitigation strategies**

With these additions, this plan provides a comprehensive, low-risk path to dramatically improving the codebase structure while maintaining stability and functionality.
