#!/usr/bin/env python3
"""
Fix Echo parameter issues found during testing.
Issues:
1. L/R Offset: Should be -33% to +33%
2. Input Gain: Should be -40 to +40 dB
3. L/R Time: Should be 1ms to 2500ms (2.5 sec)
4. L/R 16th: Should be quantized with beat division labels
5. HP/LP Res: Should be 0 to 0.3 (no unit, not percent)
6. Channel Mode: Check labels
"""
import os
os.environ["FIRESTORE_DATABASE_ID"] = "dev-display-value"
import sys
sys.path.insert(0, '/Users/sunils/ai-projects/fadebender')

from google.cloud import firestore

ECHO_SIG = "9bd78001e088fcbde50e2ead80ef01e393f3d0ba"

def fix_echo_parameters():
    """Fix all reported Echo parameter issues."""

    client = firestore.Client(database="dev-display-value")
    doc_ref = client.collection("device_mappings").document(ECHO_SIG)
    doc = doc_ref.get()

    if not doc.exists:
        print("❌ Echo device not found")
        return False

    data = doc.to_dict()
    params_meta = data.get("params_meta", [])

    print("=" * 80)
    print("FIXING ECHO PARAMETER ISSUES")
    print("=" * 80)

    fixes_applied = []

    for param in params_meta:
        name = param.get("name")

        # Issue 1 & 2: Fix L Offset and R Offset ranges
        if name in ["L Offset", "R Offset"]:
            old_min = param.get("min_display")
            old_max = param.get("max_display")
            param["min_display"] = -33.0
            param["max_display"] = 33.0
            fixes_applied.append(f"{name}: {old_min} to {old_max} → -33.0 to 33.0 %")
            print(f"✓ Fixed {name}: range -33% to +33%")

        # Issue 3: Fix Input Gain range
        elif name == "Input Gain":
            old_min = param.get("min_display")
            old_max = param.get("max_display")
            param["min_display"] = -40.0
            param["max_display"] = 40.0
            fixes_applied.append(f"{name}: {old_min} to {old_max} → -40.0 to 40.0 dB")
            print(f"✓ Fixed {name}: range -40 to +40 dB")

        # Issue 4: Fix L Time and R Time max
        elif name in ["L Time", "R Time"]:
            old_max = param.get("max_display")
            param["max_display"] = 2500.0  # 2.5 seconds
            fixes_applied.append(f"{name}: max {old_max} → 2500.0 ms")
            print(f"✓ Fixed {name}: max 2500 ms (2.5 seconds)")

        # Issue 5: Convert L 16th and R 16th to quantized
        elif name in ["L 16th", "R 16th"]:
            old_type = param.get("control_type")
            param["control_type"] = "quantized"
            param["min"] = 0.0
            param["max"] = 15.0  # 16 values (0-15)
            param["labels"] = [
                "1/64", "1/64T", "1/32", "1/32T",
                "1/16", "1/16T", "1/8", "1/8T",
                "1/4", "1/4T", "1/2", "1/2T",
                "1 Bar", "2 Bars", "3 Bars", "4 Bars"
            ]
            param["label_map"] = {str(float(i)): label for i, label in enumerate(param["labels"])}
            # Remove continuous-only fields
            if "fit" in param:
                del param["fit"]
            if "unit" in param:
                del param["unit"]
            if "min_display" in param:
                del param["min_display"]
            if "max_display" in param:
                del param["max_display"]
            fixes_applied.append(f"{name}: {old_type} → quantized (beat divisions)")
            print(f"✓ Fixed {name}: converted to quantized with beat divisions")

        # Issue 6: Fix HP Res and LP Res
        elif name in ["HP Res", "LP Res"]:
            old_unit = param.get("unit")
            old_max = param.get("max_display")
            param["unit"] = ""  # No unit
            param["min_display"] = 0.0
            param["max_display"] = 0.3
            fixes_applied.append(f"{name}: unit '{old_unit}' → '' (no unit), max {old_max} → 0.3")
            print(f"✓ Fixed {name}: removed unit, range 0 to 0.3")

    # Update Firestore
    data["params_meta"] = params_meta
    doc_ref.update({"params_meta": params_meta})

    print("\n" + "=" * 80)
    print("SUMMARY OF FIXES")
    print("=" * 80)
    for fix in fixes_applied:
        print(f"  - {fix}")

    print(f"\n✅ SUCCESS - {len(fixes_applied)} parameter issues fixed!")
    print(f"   Database: dev-display-value")
    print(f"   Signature: {ECHO_SIG}")

    print("\n" + "=" * 80)
    print("KNOWN ISSUES NOT FIXED BY THIS SCRIPT:")
    print("=" * 80)
    print("  - Feedback Inv & Clip Dry: Switches turn off immediately")
    print("    → May be normal behavior or depend on other parameters")
    print("  - Channel Mode: Cannot select Ping Pong (goes to Mid/Side)")
    print("    → Need to investigate label mapping or quantized values")
    print("  - HP Freq: Takes effect only on 2nd try")
    print("    → Likely a timing/UI refresh issue, not a data issue")

    return True

if __name__ == "__main__":
    success = fix_echo_parameters()
    sys.exit(0 if success else 1)
