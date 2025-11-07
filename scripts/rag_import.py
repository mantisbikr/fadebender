#!/usr/bin/env python3
"""
Import Fadebender help sources into a Gemini File Search store.

Requirements:
  - Auth: gcloud ADC (application-default login) or Vertex SA with permissions
  - Package: google-genai (installed in nlp-service/.venv via requirements.txt)

Usage:
  python3 scripts/rag_import.py \
    [--store-name fileSearchStores/my-store] \
    [--manual-zip data/sources/ableton-live-12-md.zip] \
    [--audio-kb data/sources/audio_engineering_knowledge_base_v1.md]

If --store-name is omitted, a new store is created. The resulting store name
is printed and can be placed in GEMINI_FILE_SEARCH_STORE.
"""
from __future__ import annotations

import argparse
import os
import sys
import tempfile
import zipfile
import time
from pathlib import Path


def _project_id() -> str:
    return os.getenv("LLM_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("PROJECT_ID") or "fadebender"


def _region() -> str:
    return os.getenv("GCP_REGION", os.getenv("VERTEX_LOCATION", "us-central1"))


def _client():
    try:
        from google import genai  # type: ignore
        return genai.Client(vertexai=True, project=_project_id(), location=_region())
    except Exception as e:
        print(f"ERROR: google-genai not available or auth not configured: {e}", file=sys.stderr)
        sys.exit(2)


def _wait_operation(client, op):
    # Poll simple LRO until done
    for _ in range(120):  # up to ~10 minutes (5s * 120)
        if getattr(op, "done", False):
            return True
        time.sleep(5)
        op = client.operations.get(name=getattr(op, "name", ""))
    return False


def ensure_store(client, name: str | None, display_name: str = "fadebender-help"):
    # Validate client has File Search APIs
    if not hasattr(client, "file_search_stores"):
        print("ERROR: google-genai version does not support File Search stores.\n"
              "Please upgrade: pip install -U google-genai", file=sys.stderr)
        sys.exit(3)
    if name:
        return name
    store = client.file_search_stores.create(config={'display_name': display_name})
    return store.name


def import_file(client, store_name: str, path: Path, metadata: dict):
    f = client.files.upload(file=str(path), display_name=path.name)
    op = client.file_search_stores.import_file(
        file_search_store_name=store_name,
        file_name=f.name,
        custom_metadata=[{"key": k, "string_value": str(v)} for k, v in metadata.items()],
    )
    _wait_operation(client, op)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--store-name", default=os.getenv("GEMINI_FILE_SEARCH_STORE"))
    ap.add_argument("--manual-zip", default=os.getenv("ABLETON_MANUAL_ZIP", "data/sources/ableton-live-12-md.zip"))
    ap.add_argument("--audio-kb", default=os.getenv("AUDIO_ENG_KB_MD", "data/sources/audio_engineering_knowledge_base_v1.md"))
    ap.add_argument("--max-files", type=int, default=500, help="Max manual files to import (safety limit)")
    args = ap.parse_args()

    client = _client()
    store_name = ensure_store(client, args.store_name)
    print(f"STORE: {store_name}")

    # Import audio engineering KB (single file)
    kb_path = Path(args.audio_kb)
    if kb_path.exists():
        print(f"Importing audio KB: {kb_path}")
        import_file(client, store_name, kb_path, {"source": "audio_kb"})
    else:
        print(f"WARN: audio KB not found at {kb_path}")

    # Import Ableton manual (zip of markdown)
    zip_path = Path(args.manual_zip)
    if zip_path.exists():
        print(f"Importing Ableton manual from zip: {zip_path}")
        with tempfile.TemporaryDirectory() as td:
            with zipfile.ZipFile(zip_path, 'r') as z:
                z.extractall(td)
            root = Path(td)
            count = 0
            for p in root.rglob('*.md'):
                import_file(client, store_name, p, {"source": "ableton_manual"})
                count += 1
                if count >= args.max_files:
                    print(f"Reached max-files limit ({args.max_files}); stopping manual import.")
                    break
            print(f"Imported {count} manual files")
    else:
        print(f"WARN: manual zip not found at {zip_path}")

    print("DONE. Set GEMINI_FILE_SEARCH_STORE to:")
    print(store_name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
