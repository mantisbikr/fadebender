# Preset Enrichment Plan

Status: Draft
Scope: Define mapping-driven enrichment vs. LLM summarization, output schema, and triggers.

## Goals
- Keep runtime simple: structure-first + minimal preset capture (no enrichment by default).
- Use device mappings (grouping + param meta) to filter stale/inactive parameters.
- Apply LLM where it adds semantics: descriptions, use-cases, tags, warnings.

## Inputs
- Device mapping (`device_mappings`):
  - `device_signature`, `device_type`, `grouping` (masters/dependents), `params_meta` (control_type, unit, label_map, optional fit)
- Captured preset (`presets`):
  - `parameter_values` (normalized for writing), `parameter_display_values` (authoritative for reading)

## Output Schema (Enriched Fields)
- `summary.description`:
  - `what` (string)
  - `when` (string[])
  - `why` (string)
- `audio_engineering`:
  - `space_type` / `mode` (device-type dependent)
  - `use_cases`: [{ source, context, send_level, notes }]
  - `character`: concise timbre/behavior descriptors
- `natural_language_controls`: key phrases mapped to param intents
- `warnings`: context-specific pitfalls
- `genre_tags`: string[]

Note: Raw `parameter_values` and `parameter_display_values` remain as-is for traceability.

## Process
1. Filter Params (mapping-driven)
   - Resolve active masters and modes using `grouping` rules.
   - Drop inactive dependents from enrichment payload.
2. Build Canonical Payload
   - Use `parameter_display_values` only; they reflect Ableton UI.
   - Include minimal device context: `device_name`, `device_type`, active groups/modes.
3. LLM Summarization (optional/triggered)
   - Prompt LLM to produce `summary`, `audio_engineering`, `natural_language_controls`, `warnings`, `genre_tags` constrained to JSON schema.
   - Validate JSON (lenient parse + schema check). Fallback to deterministic heuristics when invalid.
4. Persist
   - Save enriched fields into preset document under `enrichment`.
   - Record `enrichment_status` and timestamps.

## Triggers
- On-demand API (admin): enqueue enrichment for a signature or category.
- Background batch: when `device_mappings.params_meta` or `grouping` updated.
- Post-capture debounce: if mapping already exists and enrichment enabled.

## Safety & Idempotency
- Enrichment is additive: never overwrites captured values.
- Jobs deduped by `device_signature` + `preset_id` with short TTL.
- Retry with backoff on transient failures; persist partials with status.

## Open Questions
- Confidence thresholds for numeric fits: when to fall back to JIT probes.
- Cross-device semantics normalization (e.g., “Warmth”, “Width”).
- Multi-device chain enrichment.

