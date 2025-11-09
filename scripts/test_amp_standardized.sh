#!/bin/bash
# Test standardized Amp device mapping

echo "================================================================================"
echo "Testing Standardized Amp Device"
echo "================================================================================"
echo

echo "1. Test Bass (continuous, 0-10)"
curl -s -X POST http://127.0.0.1:8722/op/return/param_by_name \
  -H "Content-Type: application/json" \
  -d '{"return_ref":"0","device_ref":"amp","param_ref":"bass","target_display":"5"}' | python3 -m json.tool
echo

echo "2. Test Gain (continuous, 0-10)"
curl -s -X POST http://127.0.0.1:8722/op/return/param_by_name \
  -H "Content-Type: application/json" \
  -d '{"return_ref":"0","device_ref":"amp","param_ref":"gain","target_display":"8"}' | python3 -m json.tool
echo

echo "3. Test Device On (binary)"
curl -s -X POST http://127.0.0.1:8722/op/return/param_by_name \
  -H "Content-Type: application/json" \
  -d '{"return_ref":"0","device_ref":"amp","param_ref":"device on","target_display":"on"}' | python3 -m json.tool
echo

echo "4. Test Amp Type (quantized)"
curl -s -X POST http://127.0.0.1:8722/op/return/param_by_name \
  -H "Content-Type: application/json" \
  -d '{"return_ref":"0","device_ref":"amp","param_ref":"amp type","target_display":"rock"}' | python3 -m json.tool
echo

echo "5. Test Dry/Wet (continuous, 0-100%)"
curl -s -X POST http://127.0.0.1:8722/op/return/param_by_name \
  -H "Content-Type: application/json" \
  -d '{"return_ref":"0","device_ref":"amp","param_ref":"dry wet","target_display":"75"}' | python3 -m json.tool
echo

echo "================================================================================"
echo "All Amp tests complete"
echo "================================================================================"
