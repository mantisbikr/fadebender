#!/bin/bash

# Test transport commands
echo "Testing transport commands:"
echo "==========================="
echo

commands=(
  "loop on"
  "loop off"
  "set tempo to 130"
  "set loop start to 24"
  "set loop length to 8"
  "set time signature numerator to 3"
  "set time signature denominator to 4"
  "set playhead to 8"
)

for cmd in "${commands[@]}"; do
  echo "Command: $cmd"
  result=$(curl -s http://127.0.0.1:8722/intent/parse -X POST \
    -H "Content-Type: application/json" \
    -d "{\"text\":\"$cmd\"}")

  ok=$(echo "$result" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('ok','N/A'))")
  intent=$(echo "$result" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('raw_intent',{}).get('intent','N/A'))")

  if [ "$ok" == "True" ]; then
    echo "  ✓ OK: $ok, Intent: $intent"
  else
    echo "  ✗ FAILED: $ok, Intent: $intent"
  fi
  echo
done
