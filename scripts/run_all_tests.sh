#!/bin/bash
# Master test runner for baseline and validation

set -e

echo "=== Running All Tests ==="
echo ""

echo "1. Pan Commands..."
bash scripts/run_all_pan_tests.sh

echo ""
echo "2. NLP Comprehensive..."
python3 scripts/test_nlp_comprehensive.py

echo ""
echo "3. Get Operations..."
python3 scripts/test_nlp_get_comprehensive.py

echo ""
echo "4. Web UI Validation..."
python3 scripts/test_webui_validation.py

echo ""
echo "=== All Tests Complete ==="
