# Fadebender Runbook (Dev)

This runbook covers starting/stopping services, verifying health, using the web UI, and quick test flows.

Prereqs
- Python 3.10+
- Node 18/20 LTS
- Optional: Vertex AI creds (.env) if not using fallback

Start/Stop
- Start all: `make run-all3`
- Stop all: `make stop-all`
- Restart: `make restart-all`
- Status: `make status`
- UDP stub (no Ableton): `make udp-stub` (run in a separate terminal)

Vertex check (optional)
- `make verify-vertex` shows env, model access, and a minimal call result

Web UI
- Open http://localhost:3000
- Header
  - Execute / Preview only toggle controls whether /chat actually sends UDP
  - Undo / Redo buttons (disabled when nothing to undo/redo)
  - Model selector (Gemini or Llama preference)
- Input
  - Control: type commands like “set track 1 volume to -6 dB”
  - Help: type questions like “my vocals sound weak” (shows grounded answer + suggested actions)

What works now
- Canonical intent parsing (POST /intent/parse)
- Auto-exec via /chat
  - Absolute volume (dB) and absolute pan (% or -1..1)
  - Relative volume (preview only for now)
- Undo/Redo (volume/pan only)
  - Undo: `make undo` or header button
  - Redo: `make redo` or header button
- Knowledge-backed help (POST /help)

One-shot curl tests
- NLP health: `curl -s http://127.0.0.1:8000/health | jq`
- Server ping: `curl -s http://127.0.0.1:8722/ping | jq`
- Parse only: `curl -s -X POST http://127.0.0.1:8722/intent/parse -H 'Content-Type: application/json' -d '{"text":"set track 1 volume to -6 dB"}' | jq`
- Preview control: `curl -s -X POST http://127.0.0.1:8722/chat -H 'Content-Type: application/json' -d '{"text":"set track 1 volume to -6 dB","confirm":false}' | jq`
- Help: `curl -s -X POST http://127.0.0.1:8722/help -H 'Content-Type: application/json' -d '{"query":"my vocals sound weak"}' | jq`

Troubleshooting
- ModuleNotFoundError (server): run from repo root and use `python -m uvicorn server.app:app ...` (Makefile does this)
- CORS: server allows localhost:3000 already
- Blank UI: check browser console; ensure Node deps installed (`npm install` in clients/web-chat)
- Undo says nothing to undo: ensure Execute is ON and ping ok:true (run `make udp-stub`), then perform an executed change

See also
- docs/INTENT_SUPPORT.md — canonical intents, examples, and execution notes
