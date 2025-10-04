#!/usr/bin/env python3
"""
Re-enrich existing presets by triggering cloud enrichment.

This script:
1. Finds all presets with metadata_version < 2 (not cloud-enriched)
2. Publishes preset_enrich_requested messages to Pub/Sub for each
3. Cloud worker will then re-process with parameter conversion
"""
from __future__ import annotations

import os
import sys
from typing import Optional


def re_enrich_presets(
    project_id: str,
    topic_name: str = "preset-enrich",
    force: bool = False,
    dry_run: bool = False
) -> None:
    """Re-enrich all presets by publishing to Pub/Sub.

    Args:
        project_id: GCP project ID
        topic_name: Pub/Sub topic name
        force: If True, re-enrich even if metadata_version >= 2
        dry_run: If True, only print what would be done
    """
    from google.cloud import firestore, pubsub_v1
    import json

    # Get all presets
    client = firestore.Client(project=project_id)
    all_presets = list(client.collection("presets").stream())

    # Filter presets that need enrichment
    if force:
        presets = all_presets
    else:
        # Filter for metadata_version < 2 (including missing field which defaults to 0)
        presets = [
            doc for doc in all_presets
            if doc.to_dict().get("metadata_version", 0) < 2
        ]

    print(f"Found {len(presets)} presets to re-enrich")
    print()

    if dry_run:
        print("DRY RUN - would enqueue:")
        for doc in presets:
            data = doc.to_dict()
            print(f"  {doc.id}: {data.get('name')} (v{data.get('metadata_version', 0)})")
        return

    # Publish to Pub/Sub
    publisher = pubsub_v1.PublisherClient()
    topic_path = f"projects/{project_id}/topics/{topic_name}"

    success_count = 0
    fail_count = 0

    for doc in presets:
        data = doc.to_dict()
        preset_id = doc.id
        name = data.get("name", "Unknown")
        current_version = data.get("metadata_version", 0)

        try:
            # Publish enrichment request
            payload = json.dumps({
                "event": "preset_enrich_requested",
                "preset_id": preset_id,
                "metadata_version": current_version,
            }).encode("utf-8")

            future = publisher.publish(topic_path, payload)
            future.result(timeout=5.0)

            print(f"✓ Enqueued {preset_id}: {name} (v{current_version})")
            success_count += 1

        except Exception as e:
            print(f"✗ Failed to enqueue {preset_id}: {e}")
            fail_count += 1

    print()
    print(f"Results: {success_count} enqueued, {fail_count} failed")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Re-enrich presets with cloud worker using parameter conversion"
    )
    parser.add_argument(
        "--project",
        default=os.getenv("GOOGLE_CLOUD_PROJECT", "fadebender"),
        help="GCP project ID (default: $GOOGLE_CLOUD_PROJECT or 'fadebender')"
    )
    parser.add_argument(
        "--topic",
        default="preset-enrich",
        help="Pub/Sub topic name (default: preset-enrich)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-enrich all presets, even if already enriched (metadata_version >= 2)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only print what would be done, don't actually enqueue"
    )

    args = parser.parse_args()

    re_enrich_presets(
        project_id=args.project,
        topic_name=args.topic,
        force=args.force,
        dry_run=args.dry_run
    )


if __name__ == "__main__":
    main()
