#!/usr/bin/env python3
"""Check and clean typo cache in Firestore."""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../nlp-service'))

from google.cloud import firestore

def main():
    # Initialize Firestore
    project_id = os.getenv("FIRESTORE_PROJECT_ID")
    database_id = os.getenv("FIRESTORE_DATABASE_ID", "(default)")

    if project_id and database_id != "(default)":
        client = firestore.Client(project=project_id, database=database_id)
    elif project_id:
        client = firestore.Client(project=project_id)
    else:
        client = firestore.Client()

    # Get typo corrections
    doc_ref = client.collection("nlp_config").document("typo_corrections")
    doc = doc_ref.get()

    if not doc.exists:
        print("No typo corrections found in Firestore")
        return

    corrections = doc.to_dict().get("corrections", {})
    print(f"Found {len(corrections)} typo corrections:")
    print()

    # Look for problematic entries
    for typo, correction in sorted(corrections.items()):
        # Highlight entries related to "filter" or "freq"
        if "filter" in typo or "freq" in typo or "filter" in correction or "freq" in correction:
            print(f">>> '{typo}' → '{correction}'")
        else:
            print(f"    '{typo}' → '{correction}'")

    print()
    print("Entries marked with '>>>' contain 'filter' or 'freq'")

if __name__ == "__main__":
    main()
