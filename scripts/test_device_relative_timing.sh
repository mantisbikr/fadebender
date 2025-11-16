#!/bin/bash
# Quick timing test script to verify device relative changes work
# Tests a single dry/wet parameter on Return A, Device 1 (assumed to be delay)

set -e

BASE_URL="http://127.0.0.1:8722"

echo "================================"
echo "Device Relative Change Timing Test"
echo "================================"
echo ""
echo "Testing Delay Dry/Wet on Return A, Device 1"
echo ""

# Step 1: Set to 50%
echo "1. Setting dry/wet to 0.5 (50%)..."
curl -s "$BASE_URL/intent/execute" -X POST -H "Content-Type: application/json" -d '{
  "domain": "device",
  "action": "set",
  "return_index": 0,
  "device_index": 0,
  "param_ref": "dry/wet",
  "value": 0.5
}' | python3 -m json.tool

echo ""
sleep 0.3

# Step 2: Read back
echo "2. Reading back current value..."
READ_RESULT=$(curl -s "$BASE_URL/intent/read" -X POST -H "Content-Type: application/json" -d '{
  "domain": "device",
  "return_index": 0,
  "device_index": 0,
  "param_ref": "dry/wet"
}')

echo "$READ_RESULT" | python3 -m json.tool

NORMALIZED=$(echo "$READ_RESULT" | python3 -c "import sys, json; print(json.load(sys.stdin).get('normalized_value', 'null'))")
DISPLAY=$(echo "$READ_RESULT" | python3 -c "import sys, json; print(json.load(sys.stdin).get('display_value', 'null'))")

echo ""
echo "  Current: normalized=$NORMALIZED, display=$DISPLAY"
echo ""

# Step 3: Increase by 20%
echo "3. Increasing by 20% using chat API..."
curl -s "$BASE_URL/chat" -X POST -H "Content-Type: application/json" -d '{
  "text": "increase return A device 0 dry wet by 20 percent"
}' | python3 -m json.tool

echo ""
sleep 0.3

# Step 4: Read back
echo "4. Reading back to verify change..."
READ_RESULT2=$(curl -s "$BASE_URL/intent/read" -X POST -H "Content-Type: application/json" -d '{
  "domain": "device",
  "return_index": 0,
  "device_index": 0,
  "param_ref": "dry/wet"
}')

echo "$READ_RESULT2" | python3 -m json.tool

NORMALIZED2=$(echo "$READ_RESULT2" | python3 -c "import sys, json; print(json.load(sys.stdin).get('normalized_value', 'null'))")
DISPLAY2=$(echo "$READ_RESULT2" | python3 -c "import sys, json; print(json.load(sys.stdin).get('display_value', 'null'))")

echo ""
echo "  New: normalized=$NORMALIZED2, display=$DISPLAY2"
echo ""

# Validate
echo "================================"
echo "VALIDATION"
echo "================================"

# Check if normalized value increased by ~0.2 (20% additive in normalized space)
python3 - "$NORMALIZED" "$NORMALIZED2" << 'EOF'
import sys

normalized_before = float(sys.argv[1]) if sys.argv[1] != 'null' else None
normalized_after = float(sys.argv[2]) if sys.argv[2] != 'null' else None

if normalized_before is None or normalized_after is None:
    print("❌ FAIL: Could not read normalized values")
    sys.exit(1)

# Expected increase is 20% additive (0.5 + 0.2 = 0.7)
expected_increase = 0.2
actual_increase = normalized_after - normalized_before
tolerance = 0.05

if abs(actual_increase - expected_increase) <= tolerance:
    print(f"✅ PASS: Value increased correctly by 20%")
    print(f"   Before: {normalized_before:.3f}")
    print(f"   After:  {normalized_after:.3f}")
    print(f"   Increase: {actual_increase:.3f} (expected: {expected_increase})")
    sys.exit(0)
else:
    print(f"❌ FAIL: Value did not increase as expected")
    print(f"   Before: {normalized_before:.3f}")
    print(f"   After:  {normalized_after:.3f}")
    print(f"   Increase: {actual_increase:.3f} (expected: {expected_increase})")
    sys.exit(1)
EOF

echo ""
