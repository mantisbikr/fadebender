#!/bin/bash
# Master test runner for FadeBender
# Runs all functional and performance tests

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
SKIPPED_TESTS=0

# Function to run a test and track results
run_test() {
    local test_name="$1"
    local test_cmd="$2"
    local optional="${3:-false}"

    echo ""
    echo -e "${BLUE}================================================================================${NC}"
    echo -e "${BLUE}Running: $test_name${NC}"
    echo -e "${BLUE}================================================================================${NC}"

    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    if eval "$test_cmd"; then
        echo -e "${GREEN}✓ PASSED: $test_name${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        if [ "$optional" = "true" ]; then
            echo -e "${YELLOW}⊘ SKIPPED: $test_name (optional test failed)${NC}"
            SKIPPED_TESTS=$((SKIPPED_TESTS + 1))
            return 0
        else
            echo -e "${RED}✗ FAILED: $test_name${NC}"
            FAILED_TESTS=$((FAILED_TESTS + 1))
            return 1
        fi
    fi
}

# Print header
echo ""
echo -e "${BLUE}================================================================================${NC}"
echo -e "${BLUE}                    FadeBender Master Test Suite${NC}"
echo -e "${BLUE}================================================================================${NC}"
echo ""
echo "Running comprehensive test validation..."
echo "This will take approximately 2-3 minutes."
echo ""

# 1. Pan Command Tests
run_test "Pan Commands (Master/Return/Track)" \
    "bash scripts/run_all_pan_tests.sh"

# 2. NLP Comprehensive Tests
run_test "NLP Comprehensive (Mixer/Device Operations)" \
    "python3 scripts/test_nlp_comprehensive.py --yes"

# 3. Device Relative Parser Tests (NEW)
run_test "Device Relative Parsers (Regex Validation)" \
    "python3 scripts/test_device_relative_parsers.py"

# 4. Get Operations Tests
run_test "Get Operations (Query Commands)" \
    "python3 scripts/test_nlp_get_comprehensive.py --yes"

# 5. Web UI Validation
run_test "Web UI Validation (HTTP API)" \
    "python3 scripts/test_webui_validation.py"

# 6. Performance Tests (Optional - may fail if server not running)
echo ""
echo -e "${YELLOW}================================================================================${NC}"
echo -e "${YELLOW}Performance Tests (Optional)${NC}"
echo -e "${YELLOW}================================================================================${NC}"

run_test "Performance: Absolute vs Relative Comparison" \
    "python3 scripts/profile_relative_comparison.py" \
    "true"

run_test "Performance: Device Relative Timing" \
    "bash scripts/test_device_relative_timing.sh" \
    "true"

# Print summary
echo ""
echo -e "${BLUE}================================================================================${NC}"
echo -e "${BLUE}                            TEST SUMMARY${NC}"
echo -e "${BLUE}================================================================================${NC}"
echo ""
echo -e "Total Tests:   $TOTAL_TESTS"
echo -e "${GREEN}Passed:        $PASSED_TESTS${NC}"
if [ $FAILED_TESTS -gt 0 ]; then
    echo -e "${RED}Failed:        $FAILED_TESTS${NC}"
else
    echo -e "Failed:        $FAILED_TESTS"
fi
if [ $SKIPPED_TESTS -gt 0 ]; then
    echo -e "${YELLOW}Skipped:       $SKIPPED_TESTS${NC}"
fi
echo ""

# Exit code
if [ $FAILED_TESTS -gt 0 ]; then
    echo -e "${RED}⚠️  Some tests failed. Please review the output above.${NC}"
    exit 1
else
    echo -e "${GREEN}✓ All critical tests passed!${NC}"
    if [ $SKIPPED_TESTS -gt 0 ]; then
        echo -e "${YELLOW}  (Some optional performance tests were skipped)${NC}"
    fi
    exit 0
fi
