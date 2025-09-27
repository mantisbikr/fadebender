#!/usr/bin/env bash
set -euo pipefail

SERVER_PORT=${SERVER_PORT:-8722}
SERVER_BASE="http://127.0.0.1:${SERVER_PORT}"

pass() { echo "PASS: $1"; }
fail() { echo "FAIL: $1"; exit 1; }

# 1) Ping
PING=$(curl -s "${SERVER_BASE}/ping" || true)
echo "Ping: ${PING}"

# 2) Help question
HELP=$(curl -s -X POST "${SERVER_BASE}/help" -H 'Content-Type: application/json' -d '{"query":"my vocals sound weak"}')
echo "Help: ${HELP}" | jq '.' >/dev/null 2>&1 || true
echo "$HELP" | grep -q '"answer"' && pass "help endpoint returned answer" || fail "help endpoint missing answer"

# 3) Canonical parse
PARSE=$(curl -s -X POST "${SERVER_BASE}/intent/parse" -H 'Content-Type: application/json' -d '{"text":"set track 1 volume to -6 dB"}')
echo "Parse: ${PARSE}" | jq '.' >/dev/null 2>&1 || true
echo "$PARSE" | grep -q '"ok": true' && pass "intent parse ok" || fail "intent parse failed"

# 4) Preview control (no UDP dependency)
CHAT_PREVIEW=$(curl -s -X POST "${SERVER_BASE}/chat" -H 'Content-Type: application/json' -d '{"text":"set track 1 volume to -6 dB","confirm":false}')
echo "Chat preview: ${CHAT_PREVIEW}" | jq '.' >/dev/null 2>&1 || true
echo "$CHAT_PREVIEW" | grep -q '"ok": true' && pass "chat preview ok" || fail "chat preview failed"

echo "\nAll acceptance checks completed."
