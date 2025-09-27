# Canonical Intent Support and UI Coverage

This document tracks what the canonical intent layer supports, how the UI surfaces it, and example prompts to test.

Updated: Step 5 milestone

- Server endpoint: `POST /intent/parse`
- Purpose: Parse NL text to a canonical, validated JSON intent (no execution)
- UI: Shows an Intent card for every command before/alongside execution

Supported canonical intents

- set_mixer
  - Fields: `field` = `volume` | `pan`
  - Target: `target.track.by` = `index` or `name`
  - Value: `{ type: 'absolute'|'relative', amount: number, unit?: 'dB'|'%' }`
  - Notes: `volume` defaults to `dB`, `pan` defaults to `%`
- get_overview
- get_track_status

UI behavior

- On submit, the client calls `/intent/parse` and renders a teal Intent card with:
  - Human summary: e.g., `volume • Track 2 • relative +3 dB`
  - “View Intent JSON” accordion with canonical JSON and raw LLM intent
- Then the client calls `/chat` to preview/execute (auto‑exec currently: absolute volume only).
- Help questions use `/help` and render a grounded answer with suggested intents (if provided).

What executes today

- Auto‑exec (server `/chat`):
  - Absolute track volume only (e.g., `set track 1 volume to -6 dB`)
  - Requires UDP stub/bridge for `ok:true` (use `make udp-stub` to simulate)
- Preview only:
  - Relative volume (e.g., `increase track 2 volume by 3 dB`)
  - Pan (mapped to canonical, not yet auto‑executed)

Examples to test

- Canonical + auto‑exec
  - Prompt: `set track 1 volume to -6 dB`
  - Expect:
    - Intent card: `volume • Track 1 • absolute -6 dB`
    - Chat summary: `Set Track 1 volume to -6 dB`
    - ok:true if UDP stub/bridge is running

- Canonical + preview
  - Prompt: `increase track 2 volume by 3 dB`
  - Expect:
    - Intent card: `volume • Track 2 • relative +3 dB`
    - Chat summary: “I can auto‑execute only absolute track volume right now.”

- Pan mapping (canonical only for now)
  - Prompt: `pan track 3 left by 20%`
  - Expect:
    - Intent card: `pan • Track 3 • relative -20 %` (left is negative)
    - Chat summary: unsupported for auto‑exec (until Step 6)

How to view canonical intents via curl

- Absolute: `curl -s -X POST http://127.0.0.1:8722/intent/parse -H 'Content-Type: application/json' -d '{"text":"set track 1 volume to -6 dB"}' | jq`
- Relative: `curl -s -X POST http://127.0.0.1:8722/intent/parse -H 'Content-Type: application/json' -d '{"text":"increase track 2 volume by 3 dB"}' | jq`

Next planned (Step 6)

- UI confirm/preview toggle
- Auto‑exec: pan absolute, relative volume with UDP readback, basic sends
- Safety: clamping, `/op/undo_last`, rate limiting

