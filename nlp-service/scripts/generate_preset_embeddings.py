#!/usr/bin/env python3
"""
Generate embeddings for all presets and store in Firestore
One-time setup for Tier 2 semantic search
"""

import os
import sys
import logging
from google.cloud import firestore
import vertexai
from vertexai.language_models import TextEmbeddingModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_preset_description(preset_id: str, data: dict) -> str:
    """
    Generate a rich text description for embedding
    Combines preset name, category, device type, and parameter values
    """
    # Extract device and preset name
    parts = preset_id.split('_', 1)
    device = parts[0] if len(parts) > 0 else 'unknown'
    preset_name = parts[1].replace('_', ' ') if len(parts) > 1 else preset_id

    # Get category
    category = data.get('category', 'General')

    # Build description
    description_parts = [
        f"{preset_name} preset for {device}",
        f"Category: {category}",
    ]

    # Add key parameter info if available
    params = data.get('parameter_display_values', {})
    if params:
        # Select most descriptive parameters
        key_params = []
        for param_name, value in list(params.items())[:5]:  # Top 5 params
            key_params.append(f"{param_name}: {value}")
        if key_params:
            description_parts.append("Parameters: " + ", ".join(key_params))

    return ". ".join(description_parts)


def generate_embeddings_batch(texts: list, model: TextEmbeddingModel) -> list:
    """Generate embeddings for a batch of texts"""
    try:
        embeddings = model.get_embeddings(texts)
        return [emb.values for emb in embeddings]
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        return None


def main():
    # Initialize Firestore
    project_id = os.getenv('FIRESTORE_PROJECT_ID', 'fadebender')
    database_id = os.getenv('FIRESTORE_DATABASE_ID', 'dev-display-value')

    logger.info(f"Connecting to Firestore: {project_id}/{database_id}")
    db = firestore.Client(project=project_id, database=database_id)

    # Initialize Vertex AI
    vertexai.init(project=project_id)
    embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-004")

    # Get all presets
    logger.info("Fetching all presets...")
    presets_ref = db.collection('presets').stream()

    presets_to_process = []
    for preset in presets_ref:
        doc_id = preset.id
        data = preset.to_dict()

        # Skip if already has embedding
        if 'embedding' in data and data['embedding']:
            logger.info(f"Skipping {doc_id} (already has embedding)")
            continue

        presets_to_process.append({
            'id': doc_id,
            'ref': db.collection('presets').document(doc_id),
            'data': data,
            'description': generate_preset_description(doc_id, data)
        })

    if not presets_to_process:
        logger.info("All presets already have embeddings!")
        return

    logger.info(f"Generating embeddings for {len(presets_to_process)} presets...")

    # Process in batches of 5 (Vertex AI limit)
    batch_size = 5
    total_processed = 0

    for i in range(0, len(presets_to_process), batch_size):
        batch = presets_to_process[i:i + batch_size]
        descriptions = [p['description'] for p in batch]

        logger.info(f"Processing batch {i//batch_size + 1} ({len(batch)} presets)")

        # Generate embeddings
        embeddings = generate_embeddings_batch(descriptions, embedding_model)

        if not embeddings:
            logger.error(f"Failed to generate embeddings for batch {i//batch_size + 1}")
            continue

        # Store in Firestore
        for preset, embedding in zip(batch, embeddings):
            try:
                preset['ref'].update({
                    'embedding': embedding,
                    'embedding_description': preset['description']
                })
                logger.info(f"✓ Stored embedding for {preset['id']}")
                total_processed += 1
            except Exception as e:
                logger.error(f"✗ Error updating {preset['id']}: {e}")

    logger.info(f"\n{'='*60}")
    logger.info(f"COMPLETE: Generated embeddings for {total_processed}/{len(presets_to_process)} presets")
    logger.info(f"{'='*60}")


if __name__ == "__main__":
    main()
