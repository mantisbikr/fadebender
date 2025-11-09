#!/bin/bash
# Test standardized Amp device mapping with Screamer on Return B Device 1

echo "================================================================================"
echo "Testing Standardized Amp - Screamer (Return B, Device 1)"
echo "================================================================================"
echo

echo "1. Test Bass (continuous, 0-10) - setting to 5"
curl -s -X POST "http://127.0.0.1:8722/op/return/param_by_name" \
  -H "Content-Type: application/json" \
  -d '{"return_ref":"B","device_ref":"1","param_ref":"bass","target_display":"5"}' | python3 -m json.tool
echo

echo "2. Test Gain (continuous, 0-10) - setting to 7"
curl -s -X POST "http://127.0.0.1:8722/op/return/param_by_name" \
  -H "Content-Type: application/json" \
  -d '{"return_ref":"B","device_ref":"1","param_ref":"gain","target_display":"7"}' | python3 -m json.tool
echo

echo "3. Test Dry/Wet (continuous, 0-100%) - setting to 80%"
curl -s -X POST "http://127.0.0.1:8722/op/return/param_by_name" \
  -H "Content-Type: application/json" \
  -d '{"return_ref":"B","device_ref":"1","param_ref":"dry wet","target_display":"80"}' | python3 -m json.tool
echo

echo "4. Test Amp Type (quantized) - setting to Rock"
curl -s -X POST "http://127.0.0.1:8722/op/return/param_by_name" \
  -H "Content-Type: application/json" \
  -d '{"return_ref":"B","device_ref":"1","param_ref":"amp type","target_display":"rock"}' | python3 -m json.tool
echo

echo "5. Test Middle (continuous, 0-10) - setting to 6"
curl -s -X POST "http://127.0.0.1:8722/op/return/param_by_name" \
  -H "Content-Type: application/json" \
  -d '{"return_ref":"B","device_ref":"1","param_ref":"middle","target_display":"6"}' | python3 -m json.tool
echo

echo "================================================================================"
echo "SUCCESS: All Amp standardization tests completed!"
echo "================================================================================"
