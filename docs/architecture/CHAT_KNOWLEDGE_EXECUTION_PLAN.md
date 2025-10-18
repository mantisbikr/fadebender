# Chat + Knowledge + Intents Roadmap (Phased)

Status: Draft plan for phased rollout using GCS knowledge, LLM parsing, and deterministic intents execution.

Goals
- Help: Fadebender product help and how‑to.
- Audio advice: General audio engineering guidance.
- Ableton Live: Manual‑grounded answers with citations.
- Live‑set aware: Advise → recommend intents → preview → execute.

Strategy
- Parsing/reasoning via LLM (with fallback rules).
- Execution via `/intent/execute` (clamped, unit‑aware).
- Readbacks via `/intent/read` (display_value + normalized).
- Retrieval via RAG over GCS (embeddings + metadata), with Firestore for metadata, optional Vertex vector services.

Phases & Checklists

P0 — Foundation (routing switch + safety)
- [ ] UI chat path: `/intent/parse` → `/intent/execute` (feature flag)
- [ ] UI display values via `/intent/read` (vol dB, pan C/30L/30R, sends dB)
- [ ] Keep `/op/*` for sliders/fast controls
- [ ] Rule fallback for simple commands (mute/solo/volume/pan/sends)
- [ ] Logging: parse confidence, fallback rate, exec outcomes

P1 — Product Help (Fadebender UX)
- [ ] Ingestion: docs → GCS (`gs://<bucket>/knowledge/product/…`)
- [ ] Chunker: heading‑based Markdown splitter → JSONL (`{id,path,title,section,text}`)
- [ ] Embed: Vertex Text Embeddings → vectors stored alongside chunks in GCS or Firestore
- [ ] Index: metadata in Firestore (`knowledge_chunks`), vector refs (GCS URIs) or stored vectors
- [ ] Retriever service (Cloud Run): hybrid semantic + keyword scoring, top‑k with citations
- [ ] Server `/help`: call retriever; return `answer + suggested_intents`

P2 — Audio Engineering Advice
- [ ] Ingestion: audio‑fundamentals → GCS (`…/knowledge/audio/…`)
- [ ] Advice prompt: concise guidance + 2–4 actionable intents
- [ ] Confirm‑to‑execute flow for suggested intents via `/intent/execute`

P3 — Ableton Manual Knowledge
- [ ] Ingestion: Ableton manual sections → GCS (`…/knowledge/ableton/*`)
- [ ] Tagging: device names, parameter names, categories in chunk metadata
- [ ] Retriever boost rules for exact device/param matches
- [ ] Answers include citations (file:section)

P4 — Live‑Set Aware Advise → Recommend → Execute
- [ ] Snapshot endpoint: summarize tracks/returns/master + focused devices/params
- [ ] Persist snapshots in Firestore (per user/session/project, TTL)
- [ ] Prompt assembly: include minimal "state card" and mapping metadata (grouping, label_map, fits)
- [ ] LLM proposes 1–3 intents with rationale; UI previews via `/intent/read`; single confirm executes

P5 — Plans & Automation
- [ ] Multi‑step plans (small chains) with dry‑run previews
- [ ] Relative adjectives (slight/moderate/large) → step tables
- [ ] Undo surfaced; strict clamps in executor

GCS/Vertex Architecture
- Storage layout (example):
  - `gs://fadebender-knowledge/product/*.md|.jsonl`
  - `gs://fadebender-knowledge/audio/*.md|.jsonl`
  - `gs://fadebender-knowledge/ableton/*.md|.jsonl`
- Embeddings pipeline (Cloud Run job or Cloud Build):
  1) Read Markdown from GCS → chunk → JSONL
  2) Call Vertex Text Embeddings → vectors
  3) Write `{chunk,vector}` to GCS; write metadata to Firestore (`knowledge_chunks`): `{id, path, title, section, tags, gcs_uri, vector?: [..]}`
- Retrieval options:
  - Start: Pull vectors from Firestore and do in‑process ANN (small corpus)
  - Scale: Vertex Matching Engine or BigQuery Vector Search (store only IDs/metadata in Firestore)
- Serving (Cloud Run): stateless retriever API with hybrid rerank (semantic + keyword + tag boosts)

Device Mapping Priorities
- Current: Reverb mapped fully (best device‑level UX today)
- Recommendation: Proceed with phases P0–P2 in parallel while expanding mapping coverage. Full P4 benefits from more devices, but early phases don’t block on it.
- Next devices (impact‑first order):
  1) Delay (Simple/Hybrid): time, feedback, filter, dry/wet
  2) Compressor/Glue: threshold, ratio, attack/release, makeup
  3) EQ Eight: band gains/freqs/Q, HP/LP modes
  4) Utility: gain, width, mono, phase
- For each: add `params_meta` (units/labels/fits), grouping (masters→dependents), sanity tests.

Immediate TODOs
- [ ] P0 switch (feature flag) + read UX via intents
- [ ] Add `sends_capable` probe in return read/routing (optional UX hint)
- [ ] Stand up GCS → embeddings → Firestore pipeline (product docs first)
- [ ] Define advice prompt templates and suggested intents format

Acceptance Criteria (per phase)
- P0: Chat executes via `/intent/execute`; UI values from `/intent/read`; tests passing
- P1: `/help` returns grounded answers + 2–4 suggested intents with citations
- P2: Audio guidance produces actionable, safe intents; user confirm flow
- P3: Manual‑based answers reference correct devices/params; citations present
- P4: Snapshot used in prompt; system recommends and executes with preview
- P5: Multi‑step plans with dry‑run previews and undo

Operational Notes
- Keep `/op/*` for low‑latency sliders; intents for chat/automation.
- Cost controls: cache top chunks; short LLM timeouts; fall back to rules.
- Privacy: minimal state in prompts; per‑user Firestore scoping; TTL on snapshots.

