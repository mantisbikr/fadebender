#!/bin/bash

# Test script for return pan compact format parsing
# Tests the preprocessing normalization (30L → -30, 30R → 30) and the new parse_return_pan_absolute parser

BASE_URL="http://127.0.0.1:8722/intent/parse"

echo "======================================"
echo "Testing Return Pan Compact Format"
echo "======================================"
echo ""

# Test cases
tests=(
    "pan return A to 30L"
    "set return A pan to 30L"
    "pan return A to 25R"
    "set return A pan to 25R"
    "pan return A to 30 left"
    "pan return A to 25 right"
    "pan return A to -20"
    "pan return A to 15"
    "pan return B to 40L"
    "pan return B to 35R"
)

pass_count=0
fail_count=0

for test in "${tests[@]}"; do
    echo "Testing: '$test'"

    result=$(curl -s "$BASE_URL" -X POST -H "Content-Type: application/json" -d "{\"text\":\"$test\"}" | python3 -m json.tool 2>/dev/null)

    # Extract expected return track
    return_track=$(echo "$test" | grep -o "return [A-D]" | tr '[:lower:]' '[:upper:]')
    expected_track=$(echo "$return_track" | sed 's/RETURN /Return /')

    # Check if result contains the correct return track and pan parameter
    if echo "$result" | grep -q "\"track\": \"$expected_track\"" && echo "$result" | grep -q '"parameter": "pan"'; then
        echo "  ✓ PASS - Correctly parsed as $expected_track pan"

        # Extract and show the value
        value=$(echo "$result" | grep -o '"value": [^,}]*' | head -1)
        echo "    $value"
        ((pass_count++))
    else
        echo "  ✗ FAIL - Did not parse as $expected_track pan"
        echo "    Result: $result"
        ((fail_count++))
    fi
    echo ""
done

echo "======================================"
echo "SUMMARY: $pass_count passed, $fail_count failed"
echo "======================================"
