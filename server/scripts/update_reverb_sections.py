#!/usr/bin/env python3
"""
Update Reverb device sections based on user feedback:
1. Rename "Input Processing" -> "Input Filter", add In LowCut On, In HighCut On
2. Early Reflections - keep as is
3. Diffusion Network - add HiFilter On, HiShelf Gain
4. Chorus - keep as is
5. Output - keep as is
6. Rename "Global Settings" -> "Global", add Size Smoothing
7. Create new "Device" section with Device On
"""

from google.cloud import firestore

# Connect to dev-display-value database
client = firestore.Client(database="dev-display-value")

# Reverb signature
REVERB_SIG = "64ccfc236b79371d0b45e913f81bf0f3a55c6db9"

print("=" * 70)
print("UPDATE REVERB SECTIONS")
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

# Get current sections
sections = data.get("sections", {})
print(f"Current sections ({len(sections)}):")
for section_name in sections.keys():
    params = sections[section_name].get("parameters", [])
    print(f"  {section_name:30} - {len(params)} parameters")
print()

# Create new sections dictionary
new_sections = {}

# 1. Device section (new)
new_sections["Device"] = {
    "technical_name": "Device",
    "description": "Device on/off control",
    "sonic_focus": "Enable or disable the entire effect",
    "parameters": ["Device On"],
    "technical_notes": []
}

# 2. Input Filter (renamed from Input Processing)
old_input = sections.get("Input Processing", {})
new_sections["Input Filter"] = {
    "technical_name": old_input.get("technical_name", "Input Filter"),
    "description": old_input.get("description", "The input signal passes first through low and high cut filters."),
    "sonic_focus": old_input.get("sonic_focus", "Pre-filtering to shape what enters the reverb"),
    "parameters": old_input.get("parameters", []) + ["In LowCut On", "In HighCut On"],
    "technical_notes": old_input.get("technical_notes", [])
}

# 3. Early Reflections (unchanged)
if "Early Reflections" in sections:
    new_sections["Early Reflections"] = sections["Early Reflections"]

# 4. Diffusion Network (add HiFilter On, HiShelf Gain)
old_diffusion = sections.get("Diffusion Network", {})
diffusion_params = old_diffusion.get("parameters", [])
if "HiFilter On" not in diffusion_params:
    diffusion_params.append("HiFilter On")
if "HiShelf Gain" not in diffusion_params:
    diffusion_params.append("HiShelf Gain")
# Also add LowShelf On if not present
if "LowShelf On" not in diffusion_params:
    diffusion_params.append("LowShelf On")

new_sections["Diffusion Network"] = {
    "technical_name": old_diffusion.get("technical_name", "Diffusion Network"),
    "description": old_diffusion.get("description", "The Diffusion Network creates the reverberant tail."),
    "sonic_focus": old_diffusion.get("sonic_focus", "Reverb tail texture and frequency response"),
    "parameters": diffusion_params,
    "technical_notes": old_diffusion.get("technical_notes", [])
}

# 5. Chorus (unchanged)
if "Chorus" in sections:
    new_sections["Chorus"] = sections["Chorus"]

# 6. Output (unchanged)
if "Output" in sections:
    new_sections["Output"] = sections["Output"]

# 7. Global (renamed from Global Settings, add Size Smoothing)
old_global = sections.get("Global Settings", {})
global_params = old_global.get("parameters", [])
if "Size Smoothing" not in global_params:
    global_params.append("Size Smoothing")
# Remove Device On if it's there
if "Device On" in global_params:
    global_params.remove("Device On")

new_sections["Global"] = {
    "technical_name": old_global.get("technical_name", "Global Settings"),
    "description": old_global.get("description", "Controls that affect the overall reverb character."),
    "sonic_focus": old_global.get("sonic_focus", "Overall space character and special effects"),
    "parameters": global_params,
    "technical_notes": old_global.get("technical_notes", [])
}

# Show changes
print("=" * 70)
print("NEW SECTIONS")
print("=" * 70)
print()
for section_name, section_data in new_sections.items():
    params = section_data.get("parameters", [])
    print(f"{section_name:30} - {len(params)} parameters")
    for p in params:
        print(f"  • {p}")
    print()

# Auto-apply (backup already created)
print("=" * 70)
print("Applying changes...")

# Update the document
data["sections"] = new_sections
doc_ref.set(data)

print()
print("✓ Saved updates to dev-display-value database")
print()
print("=" * 70)
print("DONE - Restart your server to see the changes")
print("=" * 70)
