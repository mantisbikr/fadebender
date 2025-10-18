Knowledge Retriever (Cloud Run)

Purpose
- Serve knowledge retrieval for chat: product help, audio advice, Ableton manual.
- Ingest Markdown from GCS → chunk → embed (Vertex) → store vectors + metadata (Firestore/GCS).
- Provide `/search` API for the server to fetch grounded snippets with citations.

Endpoints (planned)
- POST `/ingest` — { gcs_prefix, chunk_strategy?, overwrite? }
- POST `/search` — { query, top_k=5, tags? } → { hits: [{id, path, title, section, score, text}], usage }

Storage
- GCS: raw docs and chunk JSONL (`{id,path,title,section,text}`)
- Firestore: `knowledge_chunks/{id}` with metadata and optional vector
- Vertex Matching Engine or BigQuery Vector Search for scale (optional)

Dev notes
- Requires GOOGLE_APPLICATION_CREDENTIALS and Vertex AI access.
- Keep chunks small (512–1024 tokens) and store path/title/section for citations.

