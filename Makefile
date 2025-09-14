# Fadebender Makefile
# Quick commands to run services

.PHONY: help venv install-nlp run-nlp run-controller run-bridge all clean

help:
	@echo "Fadebender Dev Commands:"
	@echo "  make venv            - create Python venv in nlp-service/"
	@echo "  make install-nlp     - install Python deps into venv"
	@echo "  make run-nlp         - run NLP FastAPI service (on :8000)"
	@echo "  make run-controller  - run Master Controller (Node/TS)"
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
