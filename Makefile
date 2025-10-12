# Fadebender Makefile
# Quick commands to run services

.PHONY: help venv install-nlp run-nlp run-controller run-bridge run-server run-chat run-server-chat run-all3 stop-nlp stop-server stop-chat stop-all status restart-all udp-stub run-udp-bridge stop-udp returns-status verify-vertex index-knowledge undo redo accept install-remote outline launch-live live-dev dev-returns dev-live migrate-local-maps list-local-maps all clean

help:
	@echo "Fadebender Dev Commands:"
	@echo "  make venv            - create Python venv in nlp-service/"
	@echo "  make install-nlp     - install Python deps into venv"
	@echo "  make run-nlp         - run NLP FastAPI service (on :8000)"
	@echo "  make run-controller  - run Master Controller (Node/TS)"
	@echo "  make run-server      - run Backend Server (on :8722)"
	@echo "  make run-chat        - run Web Chat UI (on :3000)"
	@echo "  make run-server-chat - run Backend Server and Chat together"
	@echo "  make run-all3        - run NLP + Server + Chat (parallel)"
	@echo "  make status          - show port listeners and service health"
	@echo "  make restart-all     - stop-all then run-all3"
	@echo "  make stop-all        - stop NLP/Server/Chat by ports"
	@echo "  make udp-stub        - run local UDP echo on :19845 for testing"
	@echo "  make run-udp-bridge  - run return-aware UDP bridge (Ableton stub)"
	@echo "  make stop-udp        - stop any process bound to ABLETON_UDP_PORT"
	@echo "  make returns-status  - print return tracks/devices/params via server"
	@echo "  make verify-vertex   - validate Vertex creds/model access"
	@echo "  make index-knowledge - list discovered knowledge files/headings"
	@echo "  make export-digest   - export per-signature digest to JSON (OUT=/path SIG=sha1 or RET=0 DEV=0)"
	@echo "  make import-mapping  - import mapping/grouping/params_meta from JSON (FILE=/path)"
	@echo "  make fit-from-presets-apply - fit continuous params from presets and import (SIG=sha1 | RET=0 DEV=0)"
	@echo "  make undo            - undo last mixer change via /op/undo_last"
	@echo "  make redo            - redo last mixer change via /op/redo_last"
	@echo "  make accept          - run acceptance checks against running services"
	@echo "  make install-remote  - install Remote Script into Ableton (macOS)"
	@echo "  make outline         - fetch project outline from server"
	@echo "  make launch-live     - macOS: launch Ableton Live with UDP enabled"
	@echo "  make live-dev        - stop UDP stub, install remote, launch Live"
	@echo "  make run-bridge      - reminder for running Swift bridge in Xcode"
	@echo "  make all             - run NLP + Controller together"
	@echo "  make clean           - remove Python venv and Node modules"

# ---- Python NLP Service ----
venv:
	cd nlp-service && python3 -m venv .venv

install-nlp:
	cd nlp-service && . .venv/bin/activate && pip install -r requirements.txt

run-nlp:
	cd nlp-service && . .venv/bin/activate && uvicorn app:app --reload --port 8000

# ---- Python Backend Server ----
# Default local map directory (can override: make LOCAL_MAP_DIR=/path run-server)
LOCAL_MAP_DIR ?= $(HOME)/.fadebender/param_maps

run-server:
		@echo "FB_LOCAL_MAP_DIR=$(LOCAL_MAP_DIR)"
		@set -a && [ -f .env ] && . ./.env && set +a && FB_LOCAL_MAP_DIR=$(LOCAL_MAP_DIR) . nlp-service/.venv/bin/activate && PYTHONPATH=$$PWD python -m uvicorn server.app:app --reload --host 127.0.0.1 --port $${SERVER_PORT-8722}

run-server-noreload:
		@echo "FB_LOCAL_MAP_DIR=$(LOCAL_MAP_DIR) (no-reload)"
		FB_LOCAL_MAP_DIR=$(LOCAL_MAP_DIR) . nlp-service/.venv/bin/activate && PYTHONPATH=$$PWD python -m uvicorn server.app:app --host 127.0.0.1 --port $${SERVER_PORT-8722}

# ---- Web Chat UI ----
run-chat:
	cd clients/web-chat && npm install && npm run dev

# ---- Convenience: run all 3 (NLP, Server, Chat) ----
run-all3:
		@echo "Starting NLP (:8000), Server (:8722), and Chat (:3000) in parallel..."
		@$(MAKE) -j3 run-nlp run-server run-chat

run-server-chat:
		@echo "Starting Server (:8722) and Chat (:3000) in parallel..."
		@$(MAKE) -j2 run-server run-chat

# ---- Stop helpers (macOS) ----
stop-nlp:
	-@lsof -ti :8000 | xargs kill -15 2>/dev/null || true; sleep 0.3; \
	 lsof -ti :8000 | xargs kill -9 2>/dev/null || true

stop-server:
	-@lsof -ti :$${SERVER_PORT-8722} | xargs kill -15 2>/dev/null || true; sleep 0.3; \
	 lsof -ti :$${SERVER_PORT-8722} | xargs kill -9 2>/dev/null || true

stop-chat:
	-@lsof -ti :3000 | xargs kill -15 2>/dev/null || true; sleep 0.3; \
	 lsof -ti :3000 | xargs kill -9 2>/dev/null || true

stop-all: stop-nlp stop-server stop-chat

# ---- Status / Health ----
status:
	@echo "== Ports listening (3000,8000,8721,8722) =="
	@lsof -nP -iTCP -sTCP:LISTEN | egrep ':(3000|8000|8721|8722)\b' || true
	@echo "\n== NLP health (:8000) =="
	@curl -sS http://127.0.0.1:8000/health || echo "NLP not responding"
	@echo "\n== Server ping (:8722) =="
	@curl -sS http://127.0.0.1:8722/ping || echo "Server not responding"
	@echo "\n== Server status (:8722) =="
	@curl -sS http://127.0.0.1:8722/status || echo "Server not responding"
	@echo "\n== Chat (:3000) HTTP status =="
	@curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:3000 || echo "0"

# ---- Restart convenience ----
restart-all: stop-all
	@sleep 0.5
	@$(MAKE) run-all3

# ---- UDP echo stub (for testing without Ableton) ----
udp-stub:
	@echo "Starting UDP echo stub on $${ABLETON_UDP_HOST-127.0.0.1}:$${ABLETON_UDP_PORT-19845} (Ctrl+C to stop)"
	@python3 scripts/udp_stub.py

# ---- Return-aware UDP bridge (uses ableton_remote/Fadebender/udp_bridge.py) ----
UDP_HOST ?= 127.0.0.1
UDP_PORT ?= 19845

run-udp-bridge:
		@echo "Starting return-aware UDP bridge on $(UDP_HOST):$(UDP_PORT) (Ctrl+C to stop)"
		@ABLETON_UDP_HOST=$(UDP_HOST) ABLETON_UDP_PORT=$(UDP_PORT) python3 - <<'PY'
	from ableton_remote.Fadebender.udp_bridge import start_udp_server
	start_udp_server()
	PY

stop-udp:
	-@lsof -ti :$${ABLETON_UDP_PORT-$(UDP_PORT)} | xargs kill -15 2>/dev/null || true; sleep 0.3; \
	 lsof -ti :$${ABLETON_UDP_PORT-$(UDP_PORT)} | xargs kill -9 2>/dev/null || true

returns-status:
	@echo "== Return tracks =="
	@curl -sS http://127.0.0.1:$${SERVER_PORT-8722}/returns | jq .
	@echo "\n== Return 0 devices =="
	@curl -sS "http://127.0.0.1:$${SERVER_PORT-8722}/return/devices?index=0" | jq .
	@echo "\n== Return 0, Device 0 params =="
	@curl -sS "http://127.0.0.1:$${SERVER_PORT-8722}/return/device/params?index=0&device=0" | jq .

# ---- Vertex verification ----
verify-vertex:
	cd nlp-service && . .venv/bin/activate && cd .. && python3 scripts/verify_vertex.py

# ---- Knowledge index ----
index-knowledge:
	@python3 scripts/index_knowledge.py

# ---- Undo last ----
undo:
	@curl -sS -X POST http://127.0.0.1:$${SERVER_PORT-8722}/op/undo_last | jq .

redo:
	@curl -sS -X POST http://127.0.0.1:$${SERVER_PORT-8722}/op/redo_last | jq .

accept:
	@bash scripts/acceptance.sh

install-remote:
	@python3 scripts/install_remote_script.py

outline:
	@curl -sS --max-time 3 http://127.0.0.1:$${SERVER_PORT-8722}/project/outline | jq .

launch-live:
	@set -a && [ -f .env ] && . ./.env && set +a && python3 scripts/launch_live_mac.py

live-dev: stop-udp install-remote launch-live

# ---- One-shot dev flows ----
dev-returns:
	@echo "Starting Server + Chat + Return-aware UDP bridge (Ctrl+C in this window to stop)"
	@$(MAKE) -j3 run-server run-chat run-udp-bridge

dev-live:
	@echo "Starting Server + Chat and launching Live (ensure 'make install-remote' ran once)"
	@$(MAKE) -j3 run-server run-chat launch-live

# ---- Migrate local learned maps out of the repo to avoid dev reloads ----
migrate-local-maps:
	@echo "Moving any configs/param_maps/*.json to $(LOCAL_MAP_DIR) ..."
	@mkdir -p $(LOCAL_MAP_DIR)
	@if ls configs/param_maps/*.json >/dev/null 2>&1; then \
	  for f in configs/param_maps/*.json; do \
	    base=$$(basename $$f); \
	    echo " -> $$base"; \
	    mv -f "$$f" "$(LOCAL_MAP_DIR)/$$base"; \
	  done; \
	else \
	  echo "No local maps found under configs/param_maps"; \
	fi
	@echo "Done. Server will read FB_LOCAL_MAP_DIR=$(LOCAL_MAP_DIR)"

list-local-maps:
	@echo "Listing local maps in $(LOCAL_MAP_DIR)" && ls -la $(LOCAL_MAP_DIR) 2>/dev/null || echo "(none)"

# ---- Export per-signature digest for LLM analysis ----
export-digest:
	@if [ -z "$(OUT)" ]; then echo "Usage: make export-digest OUT=/tmp/digest.json SIG=<sha1>|RET=<i> DEV=<j>"; exit 2; fi;
	@if [ -n "$(SIG)" ]; then \
		python3 scripts/export_signature_digest.py --signature $(SIG) --out $(OUT); \
	else \
		if [ -z "$(RET)" ] || [ -z "$(DEV)" ]; then echo "Provide SIG or RET and DEV"; exit 3; fi; \
		python3 scripts/export_signature_digest.py --return $(RET) --device $(DEV) --out $(OUT); \
	fi

import-mapping:
	@if [ -z "$(FILE)" ]; then echo "Usage: make import-mapping FILE=/path/analysis.json"; exit 2; fi;
	python3 scripts/import_mapping_analysis.py --file $(FILE)

fit-from-presets-apply:
	@if [ -n "$(SIG)" ]; then \
		python3 scripts/fit_params_from_presets.py --signature $(SIG) --import; \
	else \
		if [ -z "$(RET)" ] || [ -z "$(DEV)" ]; then echo "Provide SIG or RET and DEV"; exit 3; fi; \
		python3 scripts/fit_params_from_presets.py --return $(RET) --device $(DEV) --import; \
	fi

# ---- Master Controller ----
run-controller:
	cd master-controller && npm install && npm run dev

# ---- Swift Bridge ----
run-bridge:
	@echo "Open native-bridge-mac/BridgeApp.xcodeproj in Xcode and hit Run."
	@echo "This will create the CoreMIDI port 'Fadebender Out'."

# ---- Combined ----
all:
	@echo "Starting NLP service and Controller (Bridge must be run separately in Xcode)"
	@$(MAKE) -j2 run-nlp run-controller

# ---- Cleanup ----
clean:
	rm -rf nlp-service/.venv
	rm -rf master-controller/node_modules
	rm -rf master-controller/dist
