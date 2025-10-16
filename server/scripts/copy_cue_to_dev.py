#!/usr/bin/env python3
"""
Copy cue mapping from default database to dev-display-value database.
"""

from google.cloud import firestore

# Connect to default database
default_client = firestore.Client()

# Connect to dev-display-value database
dev_client = firestore.Client(database="dev-display-value")

# Read cue mapping from default
default_doc = default_client.collection("mixer_mappings").document("cue").get()
if not default_doc.exists:
    print("✗ Cue mapping not found in default database")
    exit(1)

cue_data = default_doc.to_dict()
print(f"✓ Found cue mapping in default database")
print(f"  Presets: {len(cue_data.get('display_value_presets', {}))}")

# Write to dev-display-value
dev_doc = dev_client.collection("mixer_mappings").document("cue")
dev_doc.set(cue_data)

print(f"✓ Copied cue mapping to dev-display-value database")
