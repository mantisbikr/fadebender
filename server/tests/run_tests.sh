#!/bin/bash
#
# Test runner for Intents API
#

set -e

cd "$(dirname "$0")/.."

echo "========================================"
echo "Running Intents API Test Suite"
echo "========================================"

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest not found. Installing..."
    pip install pytest pytest-cov httpx
fi

# Run tests with coverage
echo ""
echo "Running tests..."
pytest tests/test_intents.py -v --tb=short --cov=server.api.intents --cov-report=term-missing

echo ""
echo "========================================"
echo "Test Summary"
echo "========================================"
pytest tests/test_intents.py -v --tb=line -q

echo ""
echo "✅ All tests complete!"
