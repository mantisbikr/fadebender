#!/bin/bash
# Test typo learning with timing comparison

echo "========================================"
echo "🔬 TYPO LEARNING PERFORMANCE TEST"
echo "========================================"
echo ""
echo "Testing: 'pain' → 'pan' (new typo)"
echo ""

# Test 1: First request (learning)
echo "----------------------------------------"
echo "TEST 1: FIRST REQUEST (Learning Phase)"
echo "----------------------------------------"
echo "Query: 'set track 2 pain to 25% left'"
echo "Expected: LLM fallback (~5-6 seconds)"
echo ""

echo "Sending request..."
START1=$(date +%s%N)
RESPONSE1=$(curl -s http://127.0.0.1:8722/intent/parse \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"text":"set track 2 pain to 25% left"}')
END1=$(date +%s%N)
ELAPSED1=$(( (END1 - START1) / 1000000 ))

echo "$RESPONSE1" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    meta = d['raw_intent']['meta']
    print(f'✓ Pipeline: {meta[\"pipeline\"]}')
    print(f'✓ Server latency: {meta[\"latency_ms\"]:.2f}ms')
    print(f'✓ Total time: ${ELAPSED1}ms')
    print(f'✓ Model: {meta.get(\"model_used\", \"N/A\")}')
    learned = meta.get('learned_typos', {})
    if learned:
        print(f'✓ Learned typos: {learned}')
        print('')
        print('🎓 Typo learned and saved to Firestore!')
except Exception as e:
    print(f'Error: {e}')
    print(sys.stdin.read())
"

echo ""
echo "Waiting 2 seconds for cache to update..."
sleep 2

# Test 2: Second request (fast path)
echo ""
echo "----------------------------------------"
echo "TEST 2: SECOND REQUEST (Fast Path)"
echo "----------------------------------------"
echo "Query: 'set track 2 pain to 25% left' (same)"
echo "Expected: Regex pipeline (~1-10ms)"
echo ""

echo "Sending request..."
START2=$(date +%s%N)
RESPONSE2=$(curl -s http://127.0.0.1:8722/intent/parse \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"text":"set track 2 pain to 25% left"}')
END2=$(date +%s%N)
ELAPSED2=$(( (END2 - START2) / 1000000 ))

echo "$RESPONSE2" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    meta = d['raw_intent']['meta']
    print(f'✓ Pipeline: {meta[\"pipeline\"]}')
    print(f'✓ Server latency: {meta[\"latency_ms\"]:.2f}ms')
    print(f'✓ Total time: ${ELAPSED2}ms')
    learned = meta.get('learned_typos', {})
    if learned:
        print(f'⚠️  Still learning? {learned}')
except Exception as e:
    print(f'Error: {e}')
    print(sys.stdin.read())
"

# Summary
echo ""
echo "========================================"
echo "📊 PERFORMANCE SUMMARY"
echo "========================================"
python3 -c "
elapsed1 = ${ELAPSED1}
elapsed2 = ${ELAPSED2}
speedup = elapsed1 / elapsed2 if elapsed2 > 0 else 0
print(f'First request:  {elapsed1}ms (LLM learning)')
print(f'Second request: {elapsed2}ms (Regex fast path)')
print(f'')
print(f'🚀 Speedup: {speedup:.1f}x faster!')
print(f'💾 Improvement: {elapsed1 - elapsed2}ms saved')
"
echo ""
