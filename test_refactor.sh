#!/bin/bash
# Comprehensive test script for app.py refactoring
# Tests param_analysis, preset_metadata, and preset_capture services

set -e  # Exit on any error

echo "========================================="
echo "Testing Refactored Services"
echo "========================================="
echo ""

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

function run_test() {
    local test_name="$1"
    local test_cmd="$2"

    TESTS_RUN=$((TESTS_RUN + 1))
    echo -n "Running: $test_name... "

    if eval "$test_cmd" > /dev/null 2>&1; then
        echo -e "${GREEN}PASSED${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}FAILED${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

echo "Phase 1: Module Compilation Tests"
echo "-----------------------------------"

run_test "Compile param_analysis.py" \
    "python3 -m compileall server/services/param_analysis.py"

run_test "Compile preset_metadata.py" \
    "python3 -m compileall server/services/preset_metadata.py"

run_test "Compile preset_capture.py" \
    "python3 -m compileall server/services/preset_capture.py"

run_test "Compile preset_service.py" \
    "python3 -m compileall server/services/preset_service.py"

run_test "Compile presets.py API" \
    "python3 -m compileall server/api/presets.py"

run_test "Compile app.py" \
    "python3 -m compileall server/app.py"

echo ""
echo "Phase 2: Import Tests"
echo "-----------------------------------"

run_test "Import param_analysis module" \
    "python3 -c 'from server.services.param_analysis import parse_unit_from_display, classify_control_type, group_role_for_device, build_groups_from_params, fit_models'"

run_test "Import preset_metadata module" \
    "python3 -c 'from server.services.preset_metadata import generate_preset_metadata_llm, basic_metadata_fallback, preset_metadata_schema'"

run_test "Import preset_capture module" \
    "python3 -c 'from server.services.preset_capture import auto_capture_preset, should_capture_signature, ensure_device_mapping'"

run_test "Import app module" \
    "python3 -c 'from server.app import app'"

echo ""
echo "Phase 3: Unit Tests - param_analysis"
echo "-----------------------------------"

run_test "parse_unit_from_display (dB)" \
    "python3 -c \"from server.services.param_analysis import parse_unit_from_display; assert parse_unit_from_display('-6.0 dB') == 'dB'\""

run_test "parse_unit_from_display (Hz)" \
    "python3 -c \"from server.services.param_analysis import parse_unit_from_display; assert parse_unit_from_display('100 Hz') == 'Hz'\""

run_test "parse_unit_from_display (%)" \
    "python3 -c \"from server.services.param_analysis import parse_unit_from_display; assert parse_unit_from_display('50%') == '%'\""

run_test "classify_control_type (continuous)" \
    "python3 -c \"from server.services.param_analysis import classify_control_type; c, l = classify_control_type([], 0.0, 1.0); assert c == 'continuous'\""

run_test "classify_control_type (binary)" \
    "python3 -c \"from server.services.param_analysis import classify_control_type; c, l = classify_control_type([{'display': '0'}, {'display': '1'}], 0.0, 1.0); assert c == 'binary'\""

run_test "group_role_for_device (master)" \
    "python3 -c \"from server.services.param_analysis import group_role_for_device; g, r, m = group_role_for_device('Reverb', 'Chorus On'); assert r == 'master'\""

run_test "group_role_for_device (dependent)" \
    "python3 -c \"from server.services.param_analysis import group_role_for_device; g, r, m = group_role_for_device('Reverb', 'Chorus Rate'); assert r == 'dependent'\""

run_test "build_groups_from_params" \
    "python3 -c \"from server.services.param_analysis import build_groups_from_params; p = [{'name': 'Chorus On', 'index': 0}, {'name': 'Chorus Rate', 'index': 1}]; g = build_groups_from_params(p, 'Reverb'); assert len(g) >= 1\""

run_test "fit_models (linear)" \
    "python3 -c \"from server.services.param_analysis import fit_models; s = [{'value': 0.0, 'display_num': 0.0}, {'value': 0.5, 'display_num': 50.0}, {'value': 1.0, 'display_num': 100.0}]; f = fit_models(s); assert f['type'] == 'linear'\""

echo ""
echo "Phase 4: Unit Tests - preset_metadata"
echo "-----------------------------------"

run_test "basic_metadata_fallback" \
    "python3 -c \"from server.services.preset_metadata import basic_metadata_fallback; m = basic_metadata_fallback('Test', 'reverb', {}); assert 'description' in m and 'audio_engineering' in m\""

run_test "preset_metadata_schema" \
    "python3 -c \"from server.services.preset_metadata import preset_metadata_schema; s = preset_metadata_schema(); assert s['type'] == 'object' and 'properties' in s\""

run_test "json_lenient_parse (valid)" \
    "python3 -c \"from server.services.preset_metadata import json_lenient_parse; p = json_lenient_parse('{\\\"test\\\": \\\"value\\\"}'); assert p == {'test': 'value'}\""

run_test "json_lenient_parse (trailing comma)" \
    "python3 -c \"from server.services.preset_metadata import json_lenient_parse; p = json_lenient_parse('{\\\"a\\\": 1,}'); assert p == {'a': 1}\""

echo ""
echo "Phase 5: Unit Tests - preset_capture"
echo "-----------------------------------"

run_test "should_capture_signature (first call)" \
    "python3 -c \"from server.services.preset_capture import should_capture_signature; assert should_capture_signature('test_1', 60.0) == True\""

run_test "should_capture_signature (dedupe)" \
    "python3 -c \"from server.services.preset_capture import should_capture_signature; should_capture_signature('test_2', 60.0); assert should_capture_signature('test_2', 60.0) == False\""

echo ""
echo "Phase 6: Integration Test - Server Startup"
echo "-----------------------------------"

# Check if server is already running
if lsof -Pi :8722 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}Server already running on port 8722, skipping startup test${NC}"
else
    echo -n "Testing server startup... "
    timeout 5 python3 -m uvicorn server.app:app --host 127.0.0.1 --port 8723 &
    SERVER_PID=$!
    sleep 2

    if ps -p $SERVER_PID > /dev/null 2>&1; then
        echo -e "${GREEN}PASSED${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        kill $SERVER_PID 2>/dev/null || true
        wait $SERVER_PID 2>/dev/null || true
    else
        echo -e "${RED}FAILED${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    TESTS_RUN=$((TESTS_RUN + 1))
fi

echo ""
echo "Phase 7: Code Quality Checks"
echo "-----------------------------------"

run_test "Check for old preset_enricher imports" \
    "! grep -r 'from server.services.preset_enricher' server --include='*.py' 2>/dev/null | grep -v __pycache__"

run_test "Verify app.py size reduction" \
    "test \$(wc -l < server/app.py) -lt 3500"

run_test "Verify no duplicate function definitions" \
    "! grep -n 'def parse_unit_from_display\\|def classify_control_type' server/app.py"

echo ""
echo "========================================="
echo "Test Summary"
echo "========================================="
echo -e "Total tests run:    ${TESTS_RUN}"
echo -e "Tests passed:       ${GREEN}${TESTS_PASSED}${NC}"
echo -e "Tests failed:       ${RED}${TESTS_FAILED}${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ All tests passed!${NC}"
    echo ""
    echo "The refactoring is complete and all services work correctly."
    echo "You can now commit these changes."
    exit 0
else
    echo ""
    echo -e "${RED}❌ Some tests failed${NC}"
    echo "Please review the failures above before committing."
    exit 1
fi
