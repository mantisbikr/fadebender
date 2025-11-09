#!/bin/bash
# Test reading Dual Mono parameter

echo "================================================================================"
echo "Testing Dual Mono Read"
echo "================================================================================"
echo

echo "1. Set Dual Mono to Mono (0)"
curl -s -X POST "http://127.0.0.1:8722/op/return/param_by_name" \
  -H "Content-Type: application/json" \
  -d '{"return_ref":"B","device_ref":"1","param_ref":"dual mono","target_display":"mono"}' | python3 -m json.tool
echo

echo "2. Read back Dual Mono value"
curl -s -X POST "http://127.0.0.1:8722/intent/read" \
  -H "Content-Type: application/json" \
  -d '{"domain":"device","return_ref":"B","device_index":1,"param_ref":"dual mono"}' | python3 -m json.tool
echo

echo "3. Set Dual Mono to Dual (1)"
curl -s -X POST "http://127.0.0.1:8722/op/return/param_by_name" \
  -H "Content-Type: application/json" \
  -d '{"return_ref":"B","device_ref":"1","param_ref":"dual mono","target_display":"dual"}' | python3 -m json.tool
echo

echo "4. Read back Dual Mono value again"
curl -s -X POST "http://127.0.0.1:8722/intent/read" \
  -H "Content-Type: application/json" \
  -d '{"domain":"device","return_ref":"B","device_index":1,"param_ref":"dual mono"}' | python3 -m json.tool
echo

echo "================================================================================"
