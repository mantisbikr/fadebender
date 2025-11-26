# Fadebender MCP Integration Plan

**Status**: 🧩 **IN PROGRESS** (Cloud Functions + MCP HTTP helpers implemented; MCP tool wiring and tests pending)
**Date**: 2025-11-25

## Overview

Fadebender already has a mature internal API surface:

- `/intent/parse` → NL → canonical `CanonicalIntent`
- `/intent/execute` → Execute canonical intents against Ableton Live
- `/snapshot/query` → Snapshot + Live-backed reads (mixer, transport, topology)
- `/help` → RAG + Gemini 2.5 Flash Lite over `knowledge/*.md`
- Firestore: `device_mappings`, `presets`, preset metadata

We now want to expose these capabilities to external LLM hosts via a **single MCP server** (`fadebender`), so an agent can:

- Ask **general audio engineering questions**
- Explain **Ableton / Fadebender usage**
- Inspect **current Live set state** (snapshot)
- Inspect **device capabilities & presets** via Firestore-backed metadata
- Optionally execute control commands via `parse_intent` → `execute_intent`

All user-facing documentation (audio fundamentals, Ableton concepts, Fadebender usage) will live in **Firebase Studio** and be embedded there. The old `abletonosc_api_summary.md` is implementation-only and is **not** exposed as a resource.

## Design Principles

- **IO-only MCP**: MCP tools expose *data and actions* (snapshot, capabilities, presets, intent execution). The “brain” for orchestration stays in the host LLM.
- **Reuse existing APIs**: MCP calls the same FastAPI endpoints the web UI uses, avoiding divergent behavior.
- **Firestore as the single source of truth** for device and preset metadata (no separate doc copies).
- **No AbletonOSC docs as resources**: AbletonOSC remains an internal implementation detail of the Remote Script.

## MCP Server: `fadebender`

The `fadebender` MCP server exposes four main tool groups:

1. **Intent & Execution**
2. **Help (Studio)**
3. **Snapshot & Topology**
4. **Devices & Presets**
5. **High-Level Advisory**
6. **User Context & Health**

### 1. Intent & Execution Tools

These tools are the bridge between NL commands and canonical execution.

- **`fadebender.parse_intent`**
  - **Input**:  
    `{ "text": string, "model"?: string, "strict"?: boolean }`
  - **Backend**: `POST /intent/parse`
  - **Output** (mirrors `/intent/parse`):  
    `{ "ok": boolean, "intent": any, "raw_intent"?: any, "clarification"?: any }`
  - **Usage**: Convert user NL into canonical intent or richer raw intent for inspection/validation.

- **`fadebender.execute_intent`**
  - **Input**:  
    `{ "intent": CanonicalIntent, "debug"?: boolean }`
  - **Backend**: `POST /intent/execute`
  - **Output**:  
    `{ "ok": boolean, "summary": string, "resp"?: any }`
  - **Usage**: Execute a canonical intent created by `parse_intent` or constructed by the host.

**Typical flow**:  
User text → host LLM → `parse_intent` → (optional: adjust intent) → `execute_intent`.

### 2. Help (Studio) Tools

Docs are embedded via Firebase Studio and exposed through a **single Studio help surface**. MCP only talks to Cloud Functions; the Python `/help` endpoint remains an internal implementation detail.

- **`fadebender.help_studio`**
  - **Input**:  
    `{ "query": string, "userId"?: string }`
  - **Backend**: `POST https://<cloud-functions-host>/help` → Feature-flagged RAG (`help.ts`) → `callPythonHelp` internally when needed.
  - **Output** (mirrors `HelpResponse` from Cloud Functions):  
    ```json
    {
      "response": "markdown answer",
      "model_used": "gemini-1.5-flash",
      "sources": [{ "title": "string", "snippet": "string" }],
      "mode": "rag" | "fallback"
    }
    ```
  - **Usage**:
    - Audio engineering questions: “my vocals sound weak”, “mix is muddy”
    - Ableton / Live questions: “what are sends and returns”
    - Fadebender usage: “how do I control reverb on return A”

In production, `fadebender.help_studio` is the **only** help tool exposed to MCP clients. All multi-user, serverless behavior (Firebase Studio docs, Vertex AI Search, etc.) is handled at the Cloud Functions layer.

> Note: There is **no MCP resource** for `abletonosc_api_summary.md`. That file remains internal to the Remote Script implementation.

### 3. Snapshot & Topology Tools

These tools give the host access to the current Live set so it can ground advice in reality.

- **`fadebender.query_parameters`**
  - **Input** (mirrors `SnapshotQueryRequest`):  
    ```json
    {
      "targets": [{
        "track"?: string,
        "plugin"?: string,
        "parameter": string,
        "device_ordinal"?: number
      }]
    }
    ```
    - `track`: `"Track 1"`, `"Return A"`, `"Master"` or `""` for global queries.
    - `plugin`: device name (e.g. `"reverb"`, `"compressor"`), or `null` for mixer params.
    - `parameter`: `"volume"`, `"pan"`, `"tempo"`, `"tracks_count"`, `"tracks_list"`, `"return_tracks_list"`, etc.
  - **Backend**: `POST /snapshot/query`
  - **Output**: Snapshot values and display strings exactly as returned today.
  - **Usage examples**:
    - “What is track 1 volume?” → `parameter="volume", track="Track 1"`
    - “How many audio tracks?” → `parameter="audio_tracks_count"`
    - “Which tracks send to return A?” → use appropriate topology parameters.

- **`fadebender.snapshot_overview`** (optional, for structure)
  - **Input**: `{ "force_refresh"?: boolean }`
  - **Backend**: `GET /snapshot`
  - **Output**: High-level project structure (tracks, returns, devices, mixer cache).
  - **Usage**: Cheap way to understand the overall set structure without per-device param values.

- **`fadebender.snapshot_full`** (advanced / slower)
  - **Input**: `{ "skip_param_values"?: boolean }`
  - **Backend**: `GET /snapshot/full?skip_param_values={true|false}`
  - **Output**: Single-call full snapshot from Live (`get_full_snapshot`), including devices and (optionally) param values.
  - **Usage**:
    - Only for heavy analysis tools or offline diagnostics.
    - In most cases, prefer `query_parameters` + device capabilities to avoid the cost of full snapshots.

### 4. Devices & Presets Tools

These tools expose Firestore-backed device mappings and presets so the host can understand *what a device can do* and *what a preset means*.

- **`fadebender.get_track_device_capabilities`**
  - **Input**:  
    `{ "track_index": number, "device_index": number }`
  - **Backend**: `GET /track/device/capabilities?index={track_index}&device={device_index}`
  - **Output** (current shape):  
    ```json
    {
      "ok": true,
      "data": {
        "track_index": number,
        "device_index": number,
        "device_name": string,
        "device_type"?: string,
        "groups": [{ "name": string, "params": [{ "index": number, "name": string, "unit"?: string, "labels"?: string[], "role"?: string }] }],
        "ungrouped": [{ "index": number, "name": string, "unit"?: string, "labels"?: string[], "role"?: string }],
        "values": { "Param Name": { "value": number | string, "display_value": string } }
      }
    }
    ```
  - **Usage**:
    - “What knobs does this reverb have?”
    - “Which parameter is decay vs pre-delay vs high cut?”

- **`fadebender.get_return_device_capabilities`**
  - **Input**:  
    `{ "return_index": number, "device_index": number }`
  - **Backend**: `GET /return/device/capabilities?index={return_index}&device={device_index}`
  - **Output**: Same structure as track version.
  - **Usage**: Same as above, but for return devices (e.g., main reverb/delay).

- **`fadebender.get_preset_metadata`**
  - **Input** (one of):  
    - `{ "preset_id": string }`  
    - `{ "device_type": string, "preset_name": string }`
  - **Backend**: New FastAPI route wrapping `mapping_store.get_preset(...)` and related helpers.
  - **Output** (Firestore-backed):  
    ```json
    {
      "ok": boolean,
      "preset": {
        "preset_id": string,
        "name": string,
        "device_name": string,
        "device_type": string,
        "preset_type": "stock" | "user",
        "category"?: string,
        "description"?: any,
        "parameter_values"?: { [name: string]: number },
        "parameter_display_values"?: { [name: string]: string }
      }
    }
    ```
  - **Usage**:
    - “What does the ‘Cathedral’ preset do?”
    - “Recommend darker vocal plate presets for this device.”

> All of this metadata ultimately comes from Firestore (via `device_mappings` and `presets`). Firebase Studio is the UI / authoring environment for these docs; MCP just exposes the structured view.

## 5. High-Level Advisory Tools (Cloud Functions)

These tools live in **Cloud Functions** and orchestrate multiple underlying endpoints (snapshot, capabilities, help, presets) to provide higher-level advice. MCP sees a single tool; Cloud Functions hides the complexity.

- **`fadebender.mix_advice`**
  - **Location**: Cloud Function (e.g. `functions/src/mix-advice.ts`).
  - **Input**:  
    ```json
    { "query": "string", "userId"?: "string" }
    ```
    Example: `"my vocals are muddy and drums are too loud"`.
  - **Backend orchestration** (inside the function):
    - Calls Python `/snapshot/query` to get relevant mixer/transport values for vocal, drum, and return tracks.
    - Optionally calls `/track/device/capabilities` or `/return/device/capabilities` when deeper device context is needed.
    - Calls Studio help (`/help`) with a prompt that includes:
      - User question.
      - A compact summary of current set state (levels, sends, key device params).
  - **Output** (structured for MCP):  
    ```json
    {
      "analysis": "short natural-language summary",
      "recommendations": [
        { "description": "what to change and why", "intent_suggestion": "set track 1 send A to -12 dB" }
      ]
    }
    ```
  - **Usage**: One-shot “mix doctor” suggestions grounded in the actual Live set, without the host having to chain multiple tools.

- **`fadebender.preset_recommendations`**
  - **Location**: Cloud Function (e.g. `functions/src/preset-recommendations.ts`).
  - **Input**:  
    ```json
    { "device_type": "reverb" | "compressor" | "...", "goal": "string", "userId"?: "string" }
    ```
    Example: `{ "device_type": "reverb", "goal": "dark vocal plate" }`.
  - **Backend orchestration**:
    - Queries Firestore `presets` for matching `device_type` (via `category` field).
    - Builds a compact list of candidates with `description`, `audio_engineering`, `genre_tags`, and `subcategory`.
    - Uses the existing Python `/help` LLM (via `callPythonHelp`) to rank candidates for the user goal, returning STRICT JSON with top recommendations.
  - **Output**:  
    ```json
    {
      "recommendations": [
        {
          "preset_id": "reverb_dark_vocal_plate",
          "name": "Dark Vocal Plate",
          "why": "shorter decay, strong HPF, reduced brightness",
          "suggested_commands": [
            "load reverb preset dark vocal plate on track 2"
          ]
        }
      ]
    }
    ```
  - **Usage**: “Preset browser” that speaks in musical goals instead of preset names.

- **`fadebender.device_explainer`**
  - **Location**: Cloud Function (e.g. `functions/src/device-explainer.ts`).
  - **Input**:  
    ```json
    { "device_type": "compressor" | "reverb" | "...", "experience_level"?: "beginner" | "advanced" }
    ```
  - **Backend orchestration**:
    - Reads a representative device mapping (via Firestore `device_mappings`).
    - Uses mapping metadata (and later `params_meta.audio_knowledge`) to build an LLM prompt via Python `/help`.
  - **Output**:  
    ```json
    {
      "summary": "short overview of what this device does",
      "controls": [
        { "name": "Threshold", "role": "sets level where compression starts", "tips": "lower for more compression" }
      ]
    }
    ```
  - **Usage**: User-facing explanations of core devices without touching parser or UI.

- **`fadebender.preset_tuning_advice`**
  - **Location**: Cloud Function (e.g. `functions/src/preset-tuning-advice.ts`).
  - **Input**:  
    ```json
    {
      "device_type": "reverb",
      "goal": "make vocal reverb darker and closer",
      "location": { "domain": "return", "return_index": 0, "device_index": 0 }
    }
    ```
  - **Backend orchestration** (planned):
    - Calls Python `/track/device/capabilities` or `/return/device/capabilities` for the specified device instance to get current parameter values and roles.
    - Looks up the associated preset in Firestore and reads its metadata (`audio_engineering`, `natural_language_controls`).
    - Uses an LLM prompt to generate structured tweak suggestions (e.g., lower `Decay Time`, lower `HighCut`).
  - **Output** (target shape):  
    ```json
    {
      "analysis": "short explanation of what to change",
      "tweaks": [
        { "param": "Decay Time", "from": 2.5, "to": 1.6, "unit": "s", "reason": "shorter, more intimate space" }
      ]
    }
    ```
  - **Status**: Endpoint scaffolded; tweak logic to be implemented once capabilities + preset metadata wiring is finalized.

## Implementation Checklist

1. **MCP server scaffolding**
   - [x] Create `mcp/fadebender_mcp_server.ts` (Node/TypeScript) with HTTP helpers for Cloud Functions and server endpoints.
   - [ ] Wire MCP SDK tool registration to use these helpers and expose tools to hosts.
   - [ ] Finalize configuration to point at:
     - Local Fadebender server (`http://127.0.0.1:8722`) for control/snapshot/capabilities/presets.
     - Cloud Functions base URL for Studio help and advisory tools (`https://<cloud-functions-host>`).

2. **Tool wiring (HTTP-based)**
   - [ ] Implement `parse_intent` → `/intent/parse` (MCP tool + helper).
   - [ ] Implement `execute_intent` → `/intent/execute` (MCP tool + helper).
   - [x] Implement `help_studio` → Cloud Functions `/help` (HTTP helper in `mcp/fadebender_mcp_server.ts`).
   - [ ] Implement `query_parameters` → `/snapshot/query` (MCP tool).
   - [ ] Implement `snapshot_overview` → `/snapshot` (MCP tool).
   - [ ] Implement `snapshot_full` → `/snapshot/full` (MCP tool, used sparingly).
   - [ ] Implement `get_track_device_capabilities` → `/track/device/capabilities` (MCP tool).
   - [ ] Implement `get_return_device_capabilities` → `/return/device/capabilities` (MCP tool).
   - [ ] Implement `get_preset_metadata` → new presets API endpoint (MCP + Python route).
   - [x] Implement `mix_advice` → Cloud Function (`functions/src/mix-advice.ts`, snapshot-aware).
   - [x] Implement `preset_recommendations` → Cloud Function (`functions/src/preset-recommendations.ts`, metadata-aware ranking).
   - [x] Implement `device_explainer` → Cloud Function (`functions/src/device-explainer.ts`, basic summary).
   - [x] Implement `preset_tuning_advice` → Cloud Function (`functions/src/preset-tuning-advice.ts`, uses capabilities + preset metadata + LLM).
   - [x] Implement `get_user_profile` / `update_user_profile` → Cloud Functions (`functions/src/user-profile.ts`).
   - [x] Implement `health` → Cloud Function (`functions/src/health.ts`).

3. **New minimal API endpoints**
   - [ ] `GET /presets/metadata` (or similar) → wraps `mapping_store.get_preset(...)` if a dedicated metadata endpoint is desired.
   - [ ] `POST /knowledge/search` → wraps `search_knowledge` if raw snippet access is needed by MCP tools.

4. **Testing**
   - [ ] Add small MCP integration tests that:
     - Call `parse_intent` → `execute_intent` for basic mixer commands.
     - Call `query_parameters` and verify values match `/snapshot/query` directly.
     - Call `get_return_device_capabilities` and `get_preset_metadata` for a known device/preset.
     - Call `help_studio` and verify `response`, `mode`, and `sources` fields exist.
     - Call advisory tools (`mix_advice`, `preset_recommendations`, `device_explainer`, `preset_tuning_advice`) and validate structure and basic behavior.
     - Call `get_user_profile` / `update_user_profile` and ensure preferences persist in Firestore.
     - Call `health` and check that MCP reacts appropriately to different modes.

## Current Implementation Status

- **Cloud Functions (implemented)**
  - `help` → RAG-powered Studio help with fallback.
  - `mixAdvice` → Uses Python `/help` plus a lightweight `/snapshot` summary for Live-set-aware mix advice.
  - `presetRecommendations` → Reads Firestore `presets`, uses LLM (via Python `/help`) to rank presets for a given `device_type` + goal.
  - `deviceExplainer` → Fetches one `device_mappings` doc and asks LLM for a textual device overview (controls still text-only).
  - `presetTuningAdvice` → Fetches `/track|/return/device/capabilities` and optional `presets/{preset_id}` metadata, then asks LLM for structured tuning tweaks.
  - `getUserProfile` / `updateUserProfile` → Firestore-backed user profile storage.
  - `health` → Checks Python `/snapshot` and returns `{ server_ok, snapshot_ok, live_connected, mode }`.

- **MCP Helper Layer (implemented, not yet wired to SDK)**
  - `mcp/fadebender_mcp_server.ts` provides HTTP helpers and TypeScript types for:
    - `help_studio` → Cloud Functions `/help`
    - `mix_advice` → `/mixAdvice`
    - `preset_recommendations` → `/presetRecommendations`
    - `device_explainer` → `/deviceExplainer`
    - `preset_tuning_advice` → `/presetTuningAdvice`
    - `get_user_profile` / `update_user_profile` → `/getUserProfile`, `/updateUserProfile`
    - `health` → `/health`
  - These helpers are ready to be plugged into an MCP SDK `Server.tool(...)` registration.

- **Server Endpoints (already existing / reused)**
  - `/snapshot`, `/snapshot/full`, `/snapshot/query`
  - `/track/device/capabilities`, `/return/device/capabilities`
  - `/presets`, `/presets/{preset_id}`, `/presets/refresh_metadata`
  - `/help` (Python) for local knowledge + LLM, used internally by Cloud Functions.

- **Remaining Work to be Fully Functional**
  - Wire MCP tools using an MCP SDK (Node/TypeScript) so external hosts can call:
    - `fadebender.help_studio`, `fadebender.mix_advice`, `fadebender.preset_recommendations`,
      `fadebender.device_explainer`, `fadebender.preset_tuning_advice`,
      `fadebender.get_user_profile`, `fadebender.update_user_profile`, `fadebender.health`,
      plus control/snapshot tools (`parse_intent`, `execute_intent`, `query_parameters`, etc.).
  - Add small, focused prompt tuning/tests to:
    - Tighten JSON-only behavior for `preset_recommendations` and `preset_tuning_advice` (LLM responses).
    - Evolve `device_explainer` to return structured `controls` (mapping `natural_language_controls` into the `controls` array).
  - Implement remaining Python endpoints:
    - `/presets/metadata` (or equivalent) if a separate metadata-only endpoint is needed for MCP.
    - `/knowledge/search` if raw knowledge snippets are needed by future tools.
  - Update and reindex Firebase Studio datasets:
    - Ensure `knowledge/fadebender/user-guide.md` and related docs are up to date with the latest command set and workflows.
    - Regenerate `device-catalog.md` and `preset-catalog.md` as device/preset metadata evolves, then reindex in Firebase Studio.

All of these advisory tools can be implemented entirely in Cloud Functions by calling existing Python HTTP endpoints and Firestore; MCP just wraps them as tools.

## 6. User Context & Health Tools

### User Profile & Preferences

- **`fadebender.get_user_profile` / `fadebender.update_user_profile`**
  - **Location**: Cloud Functions (e.g. `functions/src/user-profile.ts`).
  - **Purpose**: Store per-user preferences in Firestore without changing the main server:
    - Preferred units (`"db"`, `"percent"`).
    - Typical vocal/bass track indices.
    - Preferred genres, loudness targets, “safe max” changes (e.g. never boost more than 6 dB).
  - **Usage**: Called by MCP host before `mix_advice` / `preset_recommendations` to tailor suggestions.

### Health & Mode

- **`fadebender.health`**
  - **Location**: Cloud Function (e.g. `functions/src/health.ts`).
  - **Backend orchestration**:
    - Pings Python `/health` (if available).
    - Optionally calls key endpoints like `/snapshot` or `/snapshot/query` with a small test.
    - Returns a compact status:
      ```json
      {
        "server_ok": true,
        "snapshot_ok": true,
        "live_connected": true,
        "mode": "full" | "explain_only"
      }
      ```
  - **Usage**: MCP host checks this before trying to execute commands; if `mode="explain_only"`, it sticks to help/explanations and avoids control tools.

### Cost / Quality Mode

- Many Cloud Function tools (`help_studio`, `mix_advice`, `preset_recommendations`) can accept an optional:
  - `"mode": "cheap" | "rich"` flag.
  - `"max_tokens"` / `"max_context_chars"` hints.
  - These can map to:
    - Smaller vs larger models.
    - Whether to hit Vertex Search or use cached/stored context only.

## Example Flows

### A. Current Live Set–Based Advice

User: “My vocals are muddy and washed out.”

1. Host calls `fadebender.query_parameters` to inspect:
   - Vocal track volume / EQ / sends
   - Return A/B device types and key params (decay, HPF, HF damping)
2. Host optionally calls `get_return_device_capabilities` for the reverb to know which params map to “brightness”, “tails”, etc.
3. Host calls `fadebender.help_studio` with:
   - User question
   - Optionally, a short summary of the current settings from step 1/2 embedded into the query (e.g. “my vocals are muddy; vocal send A is at -2 dB into a bright plate with 5s decay, no HPF”).
4. Host responds with:
   - A concise explanation (“too much low end into a bright, long reverb”)
   - 2–3 suggested commands (e.g. `set return A reverb decay to 1.8 s`, `cut 250 Hz on track 2 by 3 dB`).
5. User (or agent) feeds those commands to `parse_intent` → `execute_intent` via MCP.

### B. Device & Preset Exploration

User: “What does the ‘Lush Plate’ preset on my main vocal reverb do?”

1. Host calls `fadebender.get_return_device_capabilities` to confirm the device type and param names.
2. Host calls `fadebender.get_preset_metadata` with either:
   - `preset_id`, or
   - `(device_type, preset_name)` pair.
3. Host uses description + parameter values to explain:
   - What the preset emphasizes/attenuates.
   - How to tweak it for this session (e.g., shorten decay, increase HPF).
4. Host suggests concrete commands for adjustments.

### C. Usage / “How do I phrase this?” Questions

User: “How do I load a reverb preset on track 2?”

1. Host calls `fadebender.help_studio` with the question.
2. Cloud Function `/help` uses Vertex AI Search over Firebase Studio docs + internal Python help, then Gemini to generate:
   - A short explanation (what the feature does).
   - Example commands in Fadebender syntax:
     - `load reverb preset cathedral on track 2`
     - `load reverb on track 2`
3. Host surfaces answer + examples; user can then trigger them via `parse_intent` → `execute_intent`.

## Implementation Checklist

1. **MCP server scaffolding**
   - [ ] Create `mcp/fadebender_mcp_server.ts` (Node/TypeScript).
   - [ ] Wire configuration to point at:
     - Local Fadebender server (`http://127.0.0.1:8722`) for control/snapshot/capabilities/presets.
     - Cloud Functions base URL for Studio help (`https://<cloud-functions-host>`).

2. **Tool wiring (HTTP-based)**
   - [ ] Implement `parse_intent` → `/intent/parse`
   - [ ] Implement `execute_intent` → `/intent/execute`
   - [ ] Implement `help_studio` → Cloud Functions `/help`
   - [ ] Implement `query_parameters` → `/snapshot/query`
   - [ ] Implement `snapshot_overview` → `/snapshot`
   - [ ] Implement `snapshot_full` → `/snapshot/full`
   - [ ] Implement `get_track_device_capabilities` → `/track/device/capabilities`
   - [ ] Implement `get_return_device_capabilities` → `/return/device/capabilities`
   - [ ] Implement `get_preset_metadata` → new presets API endpoint
   - [ ] Implement `mix_advice` → Cloud Function
   - [ ] Implement `preset_recommendations` → Cloud Function
   - [ ] Implement `device_explainer` → Cloud Function
   - [ ] Implement `get_user_profile` / `update_user_profile` → Cloud Function
   - [ ] Implement `health` → Cloud Function

3. **New minimal API endpoints**
   - [ ] `GET /presets/metadata` (or similar) → wraps `mapping_store.get_preset(...)`.

4. **Testing**
   - [ ] Add small MCP integration tests that:
     - Call `parse_intent` → `execute_intent` for basic mixer commands.
     - Call `query_parameters` and verify values match `/snapshot/query` directly.
     - Call `get_return_device_capabilities` and `get_preset_metadata` for a known device/preset.
     - Call `help_studio` and verify `response`, `mode`, and `sources` fields exist.
      - Call advisory tools (`mix_advice`, `preset_recommendations`, `device_explainer`) and validate structure.
      - Call `get_user_profile` / `update_user_profile` and ensure preferences persist in Firestore.
      - Call `health` and check that MCP reacts appropriately to different modes.

5. **Docs**
   - [ ] Link this roadmap from `phase1-rag-setup-complete.md` / `vertex-ai-search-setup-complete.md` as the MCP integration layer.
   - [ ] Ensure Firebase Studio docs and Firestore metadata align on naming for devices/presets used in examples.
