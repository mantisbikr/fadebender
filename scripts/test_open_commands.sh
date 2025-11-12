#!/bin/bash

# Test 'open' commands
echo "Testing 'open' commands:"
echo "========================"
echo

for cmd in "open track 1" "open return A" "open return A reverb" "open return B device 0"; do
  echo "Command: $cmd"
  result=$(curl -s http://127.0.0.1:8722/intent/parse -X POST \
    -H "Content-Type: application/json" \
    -d "{\"text\":\"$cmd\"}")

  intent=$(echo "$result" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('raw_intent',{}).get('intent','N/A'))")
  target=$(echo "$result" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('raw_intent',{}).get('target','N/A'))")

  echo "  Intent: $intent"
  echo "  Target: $target"
  echo
done
