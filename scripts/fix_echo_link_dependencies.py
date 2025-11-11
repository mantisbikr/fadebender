#!/usr/bin/env python3
"""
Fix Echo Link-dependent parameter behavior.

CRITICAL FINDINGS from manual testing:
1. L 16th is actually "Mid" (7 values): 1/64, 1/32, 1/16, 1/8, 1/4, 1/2, 1
2. R 16th is actually "Size" (16 values): 1, 2, 3, ..., 16
3. Link parameter controls complex behavior:
   - When Link = 1.0 (ON):
     * L Time and R Time both show time in ms
   - When Link = 0.0 (OFF):
     * L Time stays as time in ms
     * R Time becomes "Side" showing integers 1-16 (not time!)
"""
import os
os.environ["FIRESTORE_DATABASE_ID"] = "dev-display-value"
import sys
sys.path.insert(0, '/Users/sunils/ai-projects/fadebender')

from google.cloud import firestore

ECHO_SIG = "9bd78001e088fcbde50e2ead80ef01e393f3d0ba"

def fix_echo_link_dependencies():
    """Fix Echo Link-dependent parameters based on manual testing."""

    client = firestore.Client(database="dev-display-value")
    doc_ref = client.collection("device_mappings").document(ECHO_SIG)
    doc = doc_ref.get()

    if not doc.exists:
        print("❌ Echo device not found")
        return False

    data = doc.to_dict()
    params_meta = data.get("params_meta", [])

    print("=" * 80)
    print("FIXING ECHO LINK-DEPENDENT PARAMETERS")
    print("=" * 80)

    fixes_applied = []

    for param in params_meta:
        name = param.get("name")

        # Fix 1: L 16th is actually "Mid" with 7 beat division values
        if name == "L 16th":
            param["display_name"] = "Mid"  # Actual name in Live
            param["labels"] = ["1/64", "1/32", "1/16", "1/8", "1/4", "1/2", "1"]
            param["min"] = 0.0
            param["max"] = 6.0  # 7 values (0-6)
            param["label_map"] = {str(float(i)): label for i, label in enumerate(param["labels"])}
            fixes_applied.append(f"{name} → 'Mid' (7 beat divisions: 1/64 to 1)")
            print(f"✓ Fixed L 16th → Mid (7 values)")

        # Fix 2: R 16th is actually "Size" with integer values 1-16
        elif name == "R 16th":
            param["display_name"] = "Size"  # Actual name in Live
            param["labels"] = [str(i) for i in range(1, 17)]  # "1", "2", ..., "16"
            param["min"] = 0.0
            param["max"] = 15.0  # 16 values (0-15)
            param["label_map"] = {str(float(i)): str(i+1) for i in range(16)}
            fixes_applied.append(f"{name} → 'Size' (integer values 1-16)")
            print(f"✓ Fixed R 16th → Size (values 1-16)")

    # Update grouping to add Link as a master parameter
    grouping = data.get("grouping", {})

    # Add Link to masters if not already there
    if "Link" not in grouping.get("masters", []):
        grouping.setdefault("masters", []).append("Link")
        fixes_applied.append("Added 'Link' to master parameters")
        print("✓ Added Link as master parameter")

    # Note about R Time/Side dependency
    # When Link = 0: R Time changes from time (ms) to "Side" (1-16)
    # This is a display_name change, not a control_type change
    # The parameter itself remains continuous (0.0-1.0), but UI should show different controls

    # Add note in R Time parameter
    for param in params_meta:
        if param.get("name") == "R Time":
            param["notes"] = "When Link=OFF, this becomes 'Side' (integer 1-16) instead of time"
            fixes_applied.append("Added note to R Time about Link dependency")
            print("✓ Added note to R Time parameter")
            break

    # Update Firestore
    data["params_meta"] = params_meta
    data["grouping"] = grouping
    doc_ref.update({
        "params_meta": params_meta,
        "grouping": grouping
    })

    print("\n" + "=" * 80)
    print("SUMMARY OF FIXES")
    print("=" * 80)
    for fix in fixes_applied:
        print(f"  - {fix}")

    print(f"\n✅ SUCCESS - {len(fixes_applied)} Link-dependency issues fixed!")
    print(f"   Database: dev-display-value")
    print(f"   Signature: {ECHO_SIG}")

    print("\n" + "=" * 80)
    print("REMAINING ISSUES (require UI/frontend changes):")
    print("=" * 80)
    print("  - Toggle switches turn off immediately (ALL devices)")
    print("    → UI regression, needs frontend debugging")
    print("  - L/R Offset range not showing -33% to +33%")
    print("    → May need UI cache refresh or data re-fetch")
    print("  - R Time should dynamically show 'Side' (1-16) when Link=OFF")
    print("    → Requires UI to handle conditional parameter display based on Link state")

    return True

if __name__ == "__main__":
    success = fix_echo_link_dependencies()
    sys.exit(0 if success else 1)
