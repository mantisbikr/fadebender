#!/bin/bash
# Build an unsigned .pkg installer for Fadebender
# Requires: pkgbuild, zip
set -euo pipefail

IDENT=com.fadebender.agent
BUILD_DIR=build
PAYLOAD=installer/payload
RESOURCES=$PAYLOAD/resources
SCRIPTS=installer/scripts

ROOT_DIR=$(git rev-parse --show-toplevel 2>/dev/null || pwd)

rm -rf "$BUILD_DIR" "$PAYLOAD"
mkdir -p "$BUILD_DIR" "$RESOURCES" "$SCRIPTS"

# 1) Package the Ableton Remote Script into payload/resources/remote_script.zip
RS_SRC="$ROOT_DIR/ableton_remote/Fadebender"
if [[ ! -d "$RS_SRC" ]]; then
  echo "Remote Script not found at $RS_SRC" >&2
  exit 1
fi
(cd "$RS_SRC/.." && zip -r "$ROOT_DIR/$RESOURCES/remote_script.zip" "Fadebender" >/dev/null)

# 2) Provide a run_server.sh template with a placeholder for REPO_DIR
cat > "$RESOURCES/run_server.sh" <<'SH'
#!/bin/bash
exec >> /tmp/fadebender.log 2>> /tmp/fadebender-error.log
export ENV=production
REPO_DIR="%REPO_DIR%"
cd "$REPO_DIR"
# if [ -f .venv/bin/activate ]; then source .venv/bin/activate; fi
/usr/bin/python3 -m uvicorn server.app:app --host 127.0.0.1 --port 8722 --workers 1
SH
chmod +x "$RESOURCES/run_server.sh"

# 3) Ensure postinstall script is executable
chmod +x "$SCRIPTS/postinstall"

# 4) Build pkg with payload targeting /usr/local/share/fadebender
pkgbuild \
  --root "$PAYLOAD" \
  --identifier "$IDENT" \
  --scripts "$SCRIPTS" \
  --install-location /usr/local/share/fadebender \
  "$BUILD_DIR/fadebender.pkg"

echo "Built: $BUILD_DIR/fadebender.pkg"

