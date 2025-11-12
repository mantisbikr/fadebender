#!/usr/bin/env python3
"""Quick test for Layer 1: Action Parser"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from server.services.nlp.action_parser import parse_action


def test_action_parser():
    """Test action parser with various commands"""

    tests = [
        # Absolute changes
        ("set track 1 volume to -10 dB", "set_parameter", "absolute", -10.0, "dB"),
        ("set return A reverb decay to 5 seconds", "set_parameter", "absolute", 5.0, "s"),
        ("change track 2 pan to 50%", "set_parameter", "absolute", 50.0, "%"),

        # Relative changes
        ("increase track 1 volume by 3 dB", "set_parameter", "relative", 3.0, "dB"),
        ("decrease return A reverb decay by 1 second", "set_parameter", "relative", -1.0, "s"),
        ("raise track 2 send A by 5 dB", "set_parameter", "relative", 5.0, "dB"),

        # Toggle operations
        ("mute track 1", "set_parameter", "absolute", 1.0, None),
        ("solo return A", "set_parameter", "absolute", 1.0, None),
        ("unmute track 2", "set_parameter", "absolute", 0.0, None),

        # Transport
        ("loop on", "transport", None, 1.0, None),
        ("set tempo to 130", "transport", None, 130.0, "bpm"),
        ("play", "transport", None, "play", None),
        ("stop", "transport", None, "stop", None),

        # Navigation
        ("open track 1", "open_capabilities", None, None, None),
        ("list tracks", "list_capabilities", None, None, None),
        ("open return A reverb", "open_capabilities", None, None, None),
    ]

    passed = 0
    failed = 0

    print("=" * 70)
    print("LAYER 1: ACTION PARSER TESTS")
    print("=" * 70)
    print()

    for text, expected_intent, expected_op, expected_val, expected_unit in tests:
        result = parse_action(text.lower())

        if result:
            if (result.intent_type == expected_intent and
                result.operation == expected_op and
                result.value == expected_val and
                result.unit == expected_unit):

                print(f"✓ {text}")
                print(f"  → intent={result.intent_type}, op={result.operation}, val={result.value}, unit={result.unit}")
                passed += 1
            else:
                print(f"✗ {text}")
                print(f"  Expected: intent={expected_intent}, op={expected_op}, val={expected_val}, unit={expected_unit}")
                print(f"  Got:      intent={result.intent_type}, op={result.operation}, val={result.value}, unit={result.unit}")
                failed += 1
        else:
            print(f"✗ {text} - NO MATCH")
            failed += 1

        print()

    print("=" * 70)
    print(f"SUMMARY: {passed} passed, {failed} failed")
    print("=" * 70)

    return failed == 0


if __name__ == "__main__":
    success = test_action_parser()
    sys.exit(0 if success else 1)
