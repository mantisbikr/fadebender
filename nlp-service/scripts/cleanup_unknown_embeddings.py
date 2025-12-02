#!/usr/bin/env python3
"""
Remove embeddings for unknown/unlearned devices
Keep only: reverb, delay, compressor, amp
"""

import os
import logging
from google.cloud import firestore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Learned devices only
LEARNED_DEVICES = ['reverb', 'delay', 'compressor', 'amp']


def main():
    # Initialize Firestore
    project_id = os.getenv('FIRESTORE_PROJECT_ID', 'fadebender')
    database_id = os.getenv('FIRESTORE_DATABASE_ID', 'dev-display-value')

    logger.info(f"Connecting to Firestore: {project_id}/{database_id}")
    db = firestore.Client(project=project_id, database=database_id)

    # Get all presets
    logger.info("Fetching all presets...")
    presets_ref = db.collection('presets').stream()

    removed_count = 0
    kept_count = 0

    for preset in presets_ref:
        doc_id = preset.id
        data = preset.to_dict()

        # Check if preset has embedding
        if 'embedding' not in data or not data['embedding']:
            continue

        # Extract device type
        device = doc_id.split('_')[0] if '_' in doc_id else 'unknown'

        # Remove embedding if not a learned device
        if device not in LEARNED_DEVICES:
            try:
                db.collection('presets').document(doc_id).update({
                    'embedding': firestore.DELETE_FIELD,
                    'embedding_description': firestore.DELETE_FIELD
                })
                logger.info(f"✗ Removed embedding from {doc_id} (device: {device})")
                removed_count += 1
            except Exception as e:
                logger.error(f"Error removing embedding from {doc_id}: {e}")
        else:
            logger.info(f"✓ Kept embedding for {doc_id} (device: {device})")
            kept_count += 1

    logger.info(f"\n{'='*60}")
    logger.info(f"COMPLETE:")
    logger.info(f"  Kept: {kept_count} embeddings (learned devices)")
    logger.info(f"  Removed: {removed_count} embeddings (unknown devices)")
    logger.info(f"{'='*60}")


if __name__ == "__main__":
    main()
