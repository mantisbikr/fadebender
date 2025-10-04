from __future__ import annotations

from typing import Any, Dict, Optional

def enqueue_preset_enrich(preset_id: str, metadata_version: int = 1) -> bool:
    """Publish a preset enrichment request to Pub/Sub if configured.

    Expects env vars:
      - PUBSUB_TOPIC: full topic path or short name
      - VERTEX_PROJECT/GOOGLE_CLOUD_PROJECT: used when building topic path from short name

    Returns True if enqueued, False otherwise (no-op when not configured).
    """
    import os
    topic = os.getenv("PUBSUB_TOPIC")
    if not topic:
        print("[PUBSUB] ⊘ Pub/Sub not configured (PUBSUB_TOPIC missing)")
        return False
    try:
        from google.cloud import pubsub_v1  # type: ignore
        project = os.getenv("VERTEX_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT")
        if topic and not topic.startswith("projects/"):
            if not project:
                print("[PUBSUB] ✗ Missing project for short topic name; set VERTEX_PROJECT or GOOGLE_CLOUD_PROJECT")
                return False
            topic_path = f"projects/{project}/topics/{topic}"
        else:
            topic_path = topic
        publisher = pubsub_v1.PublisherClient()
        import json
        payload = json.dumps({
            "event": "preset_enrich_requested",
            "preset_id": preset_id,
            "metadata_version": int(metadata_version),
        }).encode("utf-8")
        future = publisher.publish(topic_path, payload)
        future.result(timeout=5.0)
        print(f"[PUBSUB] ✓ Enqueued preset_enrich_requested for {preset_id} to {topic_path}")
        return True
    except Exception as e:
        print(f"[PUBSUB] ✗ Failed to enqueue for {preset_id}: {e}")
        return False
