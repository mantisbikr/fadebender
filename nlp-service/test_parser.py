#!/usr/bin/env python3
"""Quick test script for DAW Intent Parser with Vertex AI.

Usage:
    python test_parser.py
    python test_parser.py "increase track 2 volume by 3 dB"
"""
import sys
import json
from intents.parser import DAWIntentParser, fallback_parse

def test_parser():
    """Test the parser with various commands"""

    # Test commands
    test_commands = [
        "increase track 2 volume by 3 dB",
        "pan track 1 left 30%",
        "add reverb to vocals",  # Should ask for clarification
        "what did I just do?",
        "set track 3 volume to -6 dB",
    ]

    # If command provided via CLI, use that instead
    if len(sys.argv) > 1:
        test_commands = [" ".join(sys.argv[1:])]

    print("=" * 60)
    print("Testing DAW Intent Parser with Vertex AI")
    print("=" * 60)
    print()

    # Initialize parser (will auto-detect Vertex AI or fall back)
    print("Initializing parser...")
    parser = DAWIntentParser()
    print()

    # Test each command
    for cmd in test_commands:
        print(f"Command: '{cmd}'")
        print("-" * 60)

        try:
            result = parser.parse(cmd)
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(f"❌ Error: {e}")

        print()

    print("=" * 60)
    print("Test complete!")
    print()

    # Show what would happen with fallback
    if parser.model:
        print("✅ Vertex AI is working!")
        print("   To test fallback parser only, set VERTEX_AVAILABLE=False")
    else:
        print("⚠️  Using fallback parser (Vertex AI not available)")
        print("   Install with: pip install google-cloud-aiplatform")

if __name__ == "__main__":
    test_parser()
