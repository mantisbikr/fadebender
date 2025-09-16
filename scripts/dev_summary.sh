#!/usr/bin/env bash
set -euo pipefail

echo "=== Fadebender Dev Summary ==="

echo "-- Repo --"
BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
echo "branch: ${BRANCH}"
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || true)
echo "last_tag: ${LAST_TAG:-<none>}"
echo "recent commits:"
git --no-pager log -n 10 --pretty=format:'%h %ad %s (%an)' --date=short || true

echo
echo "-- Services --"
if command -v python3 >/dev/null 2>&1; then python3 -V; else python -V 2>/dev/null || true; fi
command -v node >/dev/null 2>&1 && node -v || echo "node: not installed"
command -v npm >/dev/null 2>&1 && npm -v || echo "npm: not installed"

echo
echo "-- Key Paths --"
for p in nlp-service master-controller native-bridge-mac clients configs knowledge; do
  if [ -d "$p" ]; then echo "dir: $p"; fi
done

echo
echo "-- NLP Service --"
if [ -f nlp-service/app.py ]; then
  rg -n "^app = FastAPI|@app.post|@app.get" -S nlp-service/app.py || sed -n '1,40p' nlp-service/app.py
else
  echo "missing: nlp-service/app.py"
fi

echo
echo "-- Known Issues (from PROJECT-STATUS.md) --"
rg -n "KNOWN ISSUES|Priority Fixes|Intent Execution" -n PROJECT-STATUS.md || true

echo
echo "-- Mapping Aliases --"
jq -r '.mappings[]?.alias' configs/mapping.json 2>/dev/null || rg -n '"alias"' configs/mapping.json || true

echo
echo "=== End Summary ==="

