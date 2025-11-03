#!/bin/bash

# Test script for track pan compact format parsing

BASE_URL="http://127.0.0.1:8722/intent/parse"

echo "======================================"
echo "Testing Track Pan Compact Format"
echo "======================================"
echo ""

# Test cases
tests=(
    "pan track 1 to 30L"
    "set track 1 pan to 30L"
    "pan track 2 to 25R"
    "set track 2 pan to 25R"
    "pan track 1 to 30 left"
    "pan track 2 to 25 right"
    "pan track 1 to -20"
    "pan track 2 to 15"
)

pass_count=0
fail_count=0

for test in "${tests[@]}"; do
    echo "Testing: '$test'"

    result=$(curl -s "$BASE_URL" -X POST -H "Content-Type: application/json" -d "{\"text\":\"$test\"}" | python3 -m json.tool 2>/dev/null)

    # Extract expected track number
    track_num=$(echo "$test" | grep -o "track [0-9]" | grep -o "[0-9]")
    expected_track="Track $track_num"

    # Check if result contains the correct track and pan parameter
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
