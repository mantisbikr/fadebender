#!/usr/bin/env python3
"""
Test relative intent handling (increase/decrease commands)
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8722"

def test_intent(text, expected_action=None):
    """Test a single intent"""
    response = requests.post(
        f"{BASE_URL}/intent/parse",
        json={"text": text},
        headers={"Content-Type": "application/json"}
    )

    if response.status_code != 200:
        return False, f"HTTP {response.status_code}", None

    data = response.json()
    action = data.get("action")

    if expected_action and action != expected_action:
        return False, f"Expected '{expected_action}', got '{action}'", data

    return True, action, data

def main():
    print("=" * 70)
    print("RELATIVE INTENT TESTING")
    print("=" * 70)
    print()

    # Test categories
    tests = [
        # MIXER RELATIVE CHANGES
        ("MIXER - Track Volume", [
            ("increase track 1 volume by 3db", "increase_track_param"),
            ("decrease track 2 volume by 2db", "decrease_track_param"),
            ("increase track volume by 5%", "increase_track_param"),
            ("decrease track volume by 10 percent", "decrease_track_param"),
        ]),

        # MIXER - Pan
        ("MIXER - Track Pan", [
            ("increase track 1 pan by 10%", "increase_track_param"),
            ("decrease track pan by 15 percent", "decrease_track_param"),
        ]),

        # MIXER - Send
        ("MIXER - Send", [
            ("increase track 1 send a by 5db", "increase_track_param"),
            ("decrease track send b by 10%", "decrease_track_param"),
            ("increase return a send a by 20%", "increase_return_param"),
        ]),

        # DEVICE RELATIVE CHANGES
        ("DEVICE - Always Additive Parameters", [
            # These should be in percent_always_additive config
            ("increase reverb dry/wet by 10%", "increase_device_param"),
            ("decrease reverb feedback by 5%", "decrease_device_param"),
            ("increase delay dry/wet by 15 percent", "increase_device_param"),
        ]),

        ("DEVICE - Other Parameters", [
            ("increase reverb decay by 1 second", "increase_device_param"),
            ("decrease delay time by 50ms", "decrease_device_param"),
            ("increase compressor threshold by 3db", "increase_device_param"),
        ]),

        # EDGE CASES
        ("EDGE CASES", [
            ("increase track 1 volume", "increase_track_param"),  # No amount specified
            ("decrease reverb dry wet", "decrease_device_param"),  # No amount specified
        ]),
    ]

    total_pass = 0
    total_fail = 0

    for category, category_tests in tests:
        print(f"\n{'='*70}")
        print(f"{category}")
        print(f"{'='*70}")

        for text, expected_action in category_tests:
            success, action, data = test_intent(text, expected_action)

            if success:
                print(f"✓ PASS: {text}")
                print(f"  Action: {action}")

                # Show relevant fields
                if "target" in data:
                    print(f"  Target: {data['target']}")
                if "parameter" in data:
                    print(f"  Parameter: {data['parameter']}")
                if "amount" in data:
                    print(f"  Amount: {data['amount']}")
                if "unit" in data:
                    print(f"  Unit: {data['unit']}")

                total_pass += 1
            else:
                print(f"✗ FAIL: {text}")
                print(f"  {action}")
                if data:
                    print(f"  Got action: {data.get('action')}")
                    print(f"  Full response: {json.dumps(data, indent=2)}")
                total_fail += 1
            print()

    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total Pass: {total_pass}")
    print(f"Total Fail: {total_fail}")
    print(f"Pass Rate: {total_pass / (total_pass + total_fail) * 100:.1f}%")
    print()

if __name__ == "__main__":
    main()
