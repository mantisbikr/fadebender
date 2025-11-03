#!/bin/bash

# Comprehensive Pan Tests
# Tests all pan command variations (compact format, word-based, numeric)
# Ensures preprocessing normalization and parsers work correctly

set -e  # Exit on first failure

echo "======================================"
echo "Running All Pan Command Tests"
echo "======================================"
echo ""

total_pass=0
total_fail=0

# Test Master Pan
echo "1/3 Testing Master Pan Commands..."
echo "--------------------------------------"
bash scripts/test_master_pan.sh > /tmp/master_pan_results.txt 2>&1
master_pass=$(grep "SUMMARY:" /tmp/master_pan_results.txt | grep -o "[0-9]* passed" | grep -o "[0-9]*")
master_fail=$(grep "SUMMARY:" /tmp/master_pan_results.txt | grep -o "[0-9]* failed" | grep -o "[0-9]*" | tail -1)
echo "Master Pan: $master_pass passed, $master_fail failed"
total_pass=$((total_pass + master_pass))
total_fail=$((total_fail + master_fail))
echo ""

# Test Return Pan
echo "2/3 Testing Return Pan Commands..."
echo "--------------------------------------"
bash scripts/test_return_pan.sh > /tmp/return_pan_results.txt 2>&1
return_pass=$(grep "SUMMARY:" /tmp/return_pan_results.txt | grep -o "[0-9]* passed" | grep -o "[0-9]*")
return_fail=$(grep "SUMMARY:" /tmp/return_pan_results.txt | grep -o "[0-9]* failed" | grep -o "[0-9]*" | tail -1)
echo "Return Pan: $return_pass passed, $return_fail failed"
total_pass=$((total_pass + return_pass))
total_fail=$((total_fail + return_fail))
echo ""

# Test Track Pan
echo "3/3 Testing Track Pan Commands..."
echo "--------------------------------------"
bash scripts/test_track_pan.sh > /tmp/track_pan_results.txt 2>&1
track_pass=$(grep "SUMMARY:" /tmp/track_pan_results.txt | grep -o "[0-9]* passed" | grep -o "[0-9]*")
track_fail=$(grep "SUMMARY:" /tmp/track_pan_results.txt | grep -o "[0-9]* failed" | grep -o "[0-9]*" | tail -1)
echo "Track Pan: $track_pass passed, $track_fail failed"
total_pass=$((total_pass + track_pass))
total_fail=$((total_fail + track_fail))
echo ""

echo "======================================"
echo "OVERALL SUMMARY"
echo "======================================"
echo "Total: $total_pass passed, $total_fail failed"
echo ""

if [ $total_fail -eq 0 ]; then
    echo "✅ All pan tests passed!"
    exit 0
else
    echo "❌ Some tests failed. Check individual test outputs above."
    exit 1
fi
