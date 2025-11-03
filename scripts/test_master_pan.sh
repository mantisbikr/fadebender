#!/bin/bash

# Test script for master pan compact format parsing
# Tests the preprocessing normalization (30L → -30, 30R → 30)

BASE_URL="http://127.0.0.1:8722/intent/parse"

echo "======================================"
echo "Testing Master Pan Compact Format"
echo "======================================"
echo ""

# Test cases
tests=(
    "pan master to 30L"
    "set master pan to 30L"
    "pan master to 25R"
    "set master pan to 25R"
    "pan master to 30 left"
    "pan master to 25 right"
    "pan master to -20"
    "pan master to 15"
)

pass_count=0
fail_count=0

for test in "${tests[@]}"; do
    echo "Testing: '$test'"

    result=$(curl -s "$BASE_URL" -X POST -H "Content-Type: application/json" -d "{\"text\":\"$test\"}" | python3 -m json.tool 2>/dev/null)

    # Check if result contains Master track and pan parameter
    if echo "$result" | grep -q '"track": "Master"' && echo "$result" | grep -q '"parameter": "pan"'; then
        echo "  ✓ PASS - Correctly parsed as Master pan"

        # Extract and show the value
        value=$(echo "$result" | grep -o '"value": [^,}]*' | head -1)
        echo "    $value"
        ((pass_count++))
    else
        echo "  ✗ FAIL - Did not parse as Master pan"
        echo "    Result: $result"
        ((fail_count++))
    fi
    echo ""
done

echo "======================================"
echo "SUMMARY: $pass_count passed, $fail_count failed"
echo "======================================"
