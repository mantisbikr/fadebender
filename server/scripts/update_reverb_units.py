#!/usr/bin/env python3
"""
Update Reverb device parameter units in dev-display-value database.

Based on actual Ableton Live Reverb parameter display units:
- Predelay: ms (milliseconds)
- Decay Time: ms to s (depends on value)
- Dry/Wet: %
- Chorus Amount: (no unit)
- Chorus Rate: Hz
- Stereo Image: degrees
- In Filter Freq: Hz or kHz
- Room Size: (no unit)
- Reflect Level: dB
- Diffuse Level: dB
- Diffusion: %
- Scale: %
- HiFilter Freq: Hz or kHz
- LowShelf Freq: Hz or kHz
- ER Shape: (no unit)
- HiShelf Gain: dB
- LowShelf Gain: dB
"""

from google.cloud import firestore

# Connect to dev-display-value database
client = firestore.Client(database="dev-display-value")

# Reverb signature
REVERB_SIG = "64ccfc236b79371d0b45e913f81bf0f3a55c6db9"

# Parameter name to unit mapping
PARAM_UNITS = {
    "Predelay": "ms",
    "Decay Time": "ms",  # Can also be s for larger values
    "Dry/Wet": "%",
    "Chorus Amount": "",  # No unit
    "Chorus Rate": "Hz",
    "Stereo Image": "degrees",
    "In Filter Freq": "Hz",  # Can also be kHz
    "Room Size": "",  # No unit
    "Reflect Level": "dB",
    "Diffuse Level": "dB",
    "Diffusion": "%",
    "Scale": "%",
    "HiFilter Freq": "Hz",  # Can also be kHz
    "LowShelf Freq": "Hz",  # Can also be kHz
    "ER Shape": "",  # No unit
    "HiShelf Gain": "dB",
    "LowShelf Gain": "dB",
}

print("=" * 70)
print("UPDATE REVERB PARAMETER UNITS")
print("=" * 70)
print()

# Get Reverb device mapping
doc_ref = client.collection("device_mappings").document(REVERB_SIG)
doc = doc_ref.get()

if not doc.exists:
    print(f"✗ Reverb mapping not found (signature: {REVERB_SIG})")
    exit(1)

data = doc.to_dict()
device_name = data.get("device_name", "unknown")
print(f"Found device: {device_name}")
print(f"Signature: {REVERB_SIG}")
print()

# Update params_meta with units
params_meta = data.get("params_meta", [])
if not params_meta:
    print("✗ No params_meta found")
    exit(1)

updated_count = 0
for pm in params_meta:
    param_name = pm.get("name", "")

    # Skip binary/quantized parameters (toggles)
    control_type = pm.get("control_type", "")
    if control_type in ("binary", "quantized"):
        continue

    # Update unit if we have a mapping for it
    if param_name in PARAM_UNITS:
        old_unit = pm.get("unit", "")
        new_unit = PARAM_UNITS[param_name]

        if old_unit != new_unit:
            pm["unit"] = new_unit
            updated_count += 1
            print(f"✓ {param_name:30} unit: '{old_unit}' → '{new_unit}'")

print()
print(f"Updated {updated_count} parameter units")
print()

# Write back to Firestore
if updated_count > 0:
    doc_ref.set(data)
    print("✓ Saved updates to dev-display-value database")
else:
    print("No changes needed")

print()
print("=" * 70)
