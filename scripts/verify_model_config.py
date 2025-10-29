#!/usr/bin/env python3
"""
Verify model configuration settings.

Shows which models are configured for different operations.
"""
import os
import sys

# Add server and nlp-service to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'server'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'nlp-service'))

from server.config.app_config import get_models_config, get_model_for_operation
from config.llm_config import get_default_model_name

print("=" * 80)
print("MODEL CONFIGURATION VERIFICATION")
print("=" * 80)

print("\n1. app_config.py models configuration:")
print("-" * 80)
models = get_models_config()
for operation, model in models.items():
    print(f"  {operation:<20} -> {model}")

print("\n2. Environment variables:")
print("-" * 80)
env_vars = ["VERTEX_MODEL", "LLM_MODEL", "GEMINI_MODEL", "LLM_MODEL_PREFERENCE"]
for var in env_vars:
    value = os.getenv(var, "(not set)")
    print(f"  {var:<25} = {value}")

print("\n3. Model selection for operations:")
print("-" * 80)
operations = ["intent_parsing", "audio_analysis", "context_analysis", "unknown_operation"]
for op in operations:
    try:
        model = get_default_model_name(None, op)
        print(f"  {op:<20} -> {model}")
    except Exception as e:
        print(f"  {op:<20} -> ERROR: {e}")

print("\n4. Test with explicit preference:")
print("-" * 80)
test_prefs = [None, "gemini-2.5-flash", "gemini-2.5-flash-lite"]
for pref in test_prefs:
    try:
        model = get_default_model_name(pref, "intent_parsing")
        print(f"  preference={str(pref):<25} -> {model}")
    except Exception as e:
        print(f"  preference={str(pref):<25} -> ERROR: {e}")

print("\n" + "=" * 80)
print("CONFIGURATION STATUS")
print("=" * 80)

# Determine effective model for intent parsing
try:
    effective_model = get_default_model_name(None, "intent_parsing")
    print(f"\n✓ Intent parsing will use: {effective_model}")

    if effective_model == "gemini-2.5-flash-lite":
        print("  → This is the faster, lower-cost model (RECOMMENDED)")
    elif effective_model == "gemini-2.5-flash":
        print("  → This is the standard model")
    else:
        print(f"  → Using custom model: {effective_model}")

except Exception as e:
    print(f"\n✗ ERROR: Cannot determine model - {e}")
    print("  → Check that VERTEX_MODEL or LLM_MODEL is set in .env")

print()
