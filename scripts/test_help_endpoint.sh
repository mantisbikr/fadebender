#!/bin/bash
# Test script for the improved help endpoint

echo "Testing improved help endpoint with various queries..."
echo ""

BASE_URL="http://127.0.0.1:8722"

echo "1. Testing reverb question:"
curl -s "$BASE_URL/help" \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"query":"how do I use reverb on vocals?"}' | python3 -m json.tool
echo ""
echo "---"
echo ""

echo "2. Testing sends question:"
curl -s "$BASE_URL/help" \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"query":"what are sends?"}' | python3 -m json.tool
echo ""
echo "---"
echo ""

echo "3. Testing Fadebender usage question:"
curl -s "$BASE_URL/help" \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"query":"how do I control track volume?"}' | python3 -m json.tool
echo ""

echo "Done!"
