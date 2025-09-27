#!/usr/bin/env python3
"""
List knowledge files and their top-level headings.
Useful to verify what the app will search.
"""
from __future__ import annotations

import os
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
KNOW_DIR = ROOT / "knowledge"


def headings(md: str) -> list[str]:
    return re.findall(r"^#\s+(.+)$", md, flags=re.M)


def main() -> int:
    include_refs = os.getenv("KNOWLEDGE_INCLUDE_REFERENCES", "").lower() in ("1", "true", "yes", "on")
    print(f"Knowledge root: {KNOW_DIR}")
    print(f"Include references/: {'yes' if include_refs else 'no'}\n")
    count = 0
    for path in sorted(KNOW_DIR.rglob('*.md')):
        if not include_refs and 'references' in path.parts:
            continue
        try:
            text = path.read_text(encoding='utf-8')
        except Exception:
            continue
        title_list = headings(text)
        rel = path.relative_to(KNOW_DIR)
        print(f"- {rel}")
        if title_list:
            for t in title_list[:6]:
                print(f"    # {t}")
        else:
            print("    (no top-level headings)")
        count += 1
    print(f"\nFiles indexed: {count}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

