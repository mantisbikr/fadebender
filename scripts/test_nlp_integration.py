#!/usr/bin/env python3
"""Automated integration tests for NLP + device resolution."""
import requests
import time
import sys

BASE_URL = "http://127.0.0.1:8722"

test_cases = [
    {
        "name": "Return device by generic name",
        "utterance": "set Return B Align Delay Mode to Distance",
        "expect_ok": True,
        "expect_in_response": "distance"  # Can be in canonical or anywhere
    },
    {
        "name": "Return device by arbitrary name",
        "utterance": "set Return A 4th Bandpass mode to Repitch",
        "expect_ok": True
    },
    {
        "name": "Alias: LoCut → Low Cut",
        "utterance": "set Return A reverb LoCut to 100 Hz",
        "expect_ok": True
    },
    {
        "name": "Alias: HiCut → High Cut",
        "utterance": "set Return A reverb HiCut to 5 kHz",
        "expect_ok": True
    },
    {
        "name": "Alias: BW → Bandwidth/Q",
        "utterance": "set Return A filter BW to 0.7",
        "expect_ok": True
    },
    {
        "name": "Alias: speed → rate",
        "utterance": "set Return A LFO speed to 2 Hz",
        "expect_ok": True
    },
    {
        "name": "Amp Type label (Rock)",
        "utterance": "set Return B Amp Type to Rock",
        "expect_ok": True,
        "expect_in_response": "rock"  # Check for "Rock" in response, not "3"
    },
    {
        "name": "Reverb Density label",
        "utterance": "set Return A Reverb Density to High",
        "expect_ok": True
    },
    {
        "name": "Track mixer volume",
        "utterance": "set track 1 volume to -6 dB",
        "expect_ok": True,
        "expect_in_response": "track"
    },
    {
        "name": "Return mixer volume",
        "utterance": "set Return A volume to -3 dB",
        "expect_ok": True
    },
]

def run_tests():
    passed = 0
    failed = 0
    errors = []

    print("="*70)
    print("NLP INTEGRATION TEST SUITE")
    print("="*70)

    # Health check
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        if resp.status_code != 200:
            print("✗ Server not responding. Please start the server first.")
            return False
        print("✓ Server is running\n")
    except Exception as e:
        print(f"✗ Cannot connect to server: {e}")
        return False

    for i, test in enumerate(test_cases, 1):
        print(f"[{i}/{len(test_cases)}] {test['name']}")
        print(f"    Utterance: \"{test['utterance']}\"")

        try:
            resp = requests.post(
                f"{BASE_URL}/intent/parse",
                json={"text": test["utterance"]},
                timeout=10
            )

            if resp.status_code == 200:
                data = resp.json()
                ok = data.get("ok", False)
                summary = data.get("summary", "")

                # Also check raw_intent and canonical_intent
                raw_intent = data.get("raw_intent", {})
                canonical = data.get("canonical_intent", {})

                if test.get("expect_ok"):
                    if ok:
                        # Check if expected text is in response
                        if test.get("expect_in_response"):
                            full_response = str(data).lower()
                            expected = test["expect_in_response"].lower()

                            if expected in full_response:
                                print(f"    ✓ PASS - Found '{test['expect_in_response']}' in response")
                                passed += 1
                            else:
                                print(f"    ✗ FAIL - Response doesn't contain '{test['expect_in_response']}'")
                                print(f"    Summary: {summary}")
                                print(f"    Raw intent: {raw_intent.get('intent') if raw_intent else 'N/A'}")
                                print(f"    Canonical: {canonical}")
                                failed += 1
                                errors.append(f"{test['name']}: Response content mismatch")
                        else:
                            print(f"    ✓ PASS - {summary[:60] if summary else 'ok=true'}...")
                            passed += 1
                    else:
                        print(f"    ✗ FAIL - Expected ok=true, got ok=false")
                        print(f"    Response: {data}")
                        failed += 1
                        errors.append(f"{test['name']}: ok=false")
                else:
                    # Expecting failure
                    if not ok:
                        print(f"    ✓ PASS - Correctly failed")
                        passed += 1
                    else:
                        print(f"    ✗ FAIL - Expected failure but succeeded")
                        failed += 1
                        errors.append(f"{test['name']}: Unexpected success")
            else:
                print(f"    ✗ FAIL - HTTP {resp.status_code}")
                print(f"    Response: {resp.text[:200]}")
                failed += 1
                errors.append(f"{test['name']}: HTTP {resp.status_code}")

        except Exception as e:
            print(f"    ✗ FAIL - Exception: {e}")
            failed += 1
            errors.append(f"{test['name']}: {str(e)}")

        print()
        time.sleep(0.5)  # Small delay between tests

    print("="*70)
    print("RESULTS")
    print("="*70)
    print(f"Total tests: {len(test_cases)}")
    print(f"✓ Passed: {passed}")
    print(f"✗ Failed: {failed}")

    if failed > 0:
        print(f"\nFailed tests:")
        for error in errors:
            print(f"  - {error}")

    print("="*70)

    return failed == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
