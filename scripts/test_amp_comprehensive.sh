#!/bin/bash
# Comprehensive Amp parameter test after standardization fixes

echo "================================================================================"
echo "Comprehensive Amp Parameter Test"
echo "================================================================================"
echo

# Test 1: Binary parameter with custom labels (Dual Mono)
echo "TEST 1: Dual Mono (binary with custom labels)"
echo "----------------------------------------------"
echo "1. Set Dual Mono to Mono (0)"
curl -s -X POST "http://127.0.0.1:8722/intent/execute" \
  -H "Content-Type: application/json" \
  -d '{"domain":"device","action":"set","return_index":1,"device_index":1,"param_ref":"dual mono","value":0}' | python3 -m json.tool
echo

echo "2. Read back Dual Mono value (should show 'Mono')"
curl -s -X POST "http://127.0.0.1:8722/intent/read" \
  -H "Content-Type: application/json" \
  -d '{"domain":"device","return_index":1,"device_index":1,"param_ref":"dual mono"}' | python3 -m json.tool
echo

echo "3. Set Dual Mono to Dual (1)"
curl -s -X POST "http://127.0.0.1:8722/intent/execute" \
  -H "Content-Type: application/json" \
  -d '{"domain":"device","action":"set","return_index":1,"device_index":1,"param_ref":"dual mono","value":1}' | python3 -m json.tool
echo

echo "4. Read back Dual Mono value (should show 'Dual')"
curl -s -X POST "http://127.0.0.1:8722/intent/read" \
  -H "Content-Type: application/json" \
  -d '{"domain":"device","return_index":1,"device_index":1,"param_ref":"dual mono"}' | python3 -m json.tool
echo

# Test 2: Quantized parameter (Amp Type)
echo "TEST 2: Amp Type (quantized with 7 options)"
echo "---------------------------------------------"
echo "1. Set Amp Type to Clean (0)"
curl -s -X POST "http://127.0.0.1:8722/intent/execute" \
  -H "Content-Type: application/json" \
  -d '{"domain":"device","action":"set","return_index":1,"device_index":1,"param_ref":"amp type","value":0}' | python3 -m json.tool
echo

echo "2. Read back Amp Type (should show 'Clean')"
curl -s -X POST "http://127.0.0.1:8722/intent/read" \
  -H "Content-Type: application/json" \
  -d '{"domain":"device","return_index":1,"device_index":1,"param_ref":"amp type"}' | python3 -m json.tool
echo

echo "3. Set Amp Type to Boost (3)"
curl -s -X POST "http://127.0.0.1:8722/intent/execute" \
  -H "Content-Type: application/json" \
  -d '{"domain":"device","action":"set","return_index":1,"device_index":1,"param_ref":"amp type","value":3}' | python3 -m json.tool
echo

echo "4. Read back Amp Type (should show 'Boost')"
curl -s -X POST "http://127.0.0.1:8722/intent/read" \
  -H "Content-Type: application/json" \
  -d '{"domain":"device","return_index":1,"device_index":1,"param_ref":"amp type"}' | python3 -m json.tool
echo

# Test 3: Continuous parameters (Bass, Gain, Volume)
echo "TEST 3: Continuous Parameters (Bass, Gain, Volume)"
echo "---------------------------------------------------"
echo "1. Set Bass to 5.0 dB"
curl -s -X POST "http://127.0.0.1:8722/intent/execute" \
  -H "Content-Type: application/json" \
  -d '{"domain":"device","action":"set","return_index":1,"device_index":1,"param_ref":"bass","value":0.625}' | python3 -m json.tool
echo

echo "2. Read back Bass (should show ~5.0 dB)"
curl -s -X POST "http://127.0.0.1:8722/intent/read" \
  -H "Content-Type: application/json" \
  -d '{"domain":"device","return_index":1,"device_index":1,"param_ref":"bass"}' | python3 -m json.tool
echo

echo "3. Set Gain to 5.0"
curl -s -X POST "http://127.0.0.1:8722/intent/execute" \
  -H "Content-Type: application/json" \
  -d '{"domain":"device","action":"set","return_index":1,"device_index":1,"param_ref":"gain","value":0.5}' | python3 -m json.tool
echo

echo "4. Read back Gain (should show ~5.0)"
curl -s -X POST "http://127.0.0.1:8722/intent/read" \
  -H "Content-Type: application/json" \
  -d '{"domain":"device","return_index":1,"device_index":1,"param_ref":"gain"}' | python3 -m json.tool
echo

# Test 4: Device volume routing (should change device param, not mixer)
echo "TEST 4: Device Volume Routing (should change device param, not mixer)"
echo "----------------------------------------------------------------------"
echo "1. Parse 'set return B screamer volume to 6' (should route to device domain)"
curl -s -X POST "http://127.0.0.1:8722/intent/parse" \
  -H "Content-Type: application/json" \
  -d '{"text":"set return B screamer volume to 6"}' | python3 -m json.tool
echo

echo "2. Execute and verify it changes device Volume, not mixer"
curl -s -X POST "http://127.0.0.1:8722/intent/execute" \
  -H "Content-Type: application/json" \
  -d '{"domain":"device","action":"set","return_index":1,"device_index":1,"param_ref":"volume","value":0.6}' | python3 -m json.tool
echo

echo "3. Read back device Volume parameter"
curl -s -X POST "http://127.0.0.1:8722/intent/read" \
  -H "Content-Type: application/json" \
  -d '{"domain":"device","return_index":1,"device_index":1,"param_ref":"volume"}' | python3 -m json.tool
echo

echo "================================================================================"
echo "Test Complete!"
echo "================================================================================"
