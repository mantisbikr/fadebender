import os
import pathlib
import re
from typing import List, Tuple

ROOT = pathlib.Path(__file__).resolve().parents[2]
KNOW_DIR = ROOT / "knowledge"


def _read(path: pathlib.Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def _sections(md: str) -> List[Tuple[str, str]]:
    # Split by headings and keep (title, body)
    out: List[Tuple[str, str]] = []
    parts = re.split(r"^#+\s+", md, flags=re.M)
    if not parts:
        return out
    # parts like [prefix, title1, body1, title2, body2, ...]
    it = iter(parts[1:])
    for title, body in zip(it, it):
        out.append((title.strip(), body.strip()))
    return out


def search_knowledge(query: str, limit: int = 3) -> List[Tuple[str, str, str]]:
    """Return list of (source, title, body) best matches from all knowledge/*.md files."""
    q = query.lower()
    keywords = set(re.findall(r"[a-zA-Z0-9_]+", q))
    scored: List[Tuple[float, str, str, str]] = []

    include_refs = os.getenv("KNOWLEDGE_INCLUDE_REFERENCES", "").lower() in ("1", "true", "yes", "on")
    # Collect all .md files under knowledge/, optionally excluding knowledge/references
    for path in KNOW_DIR.rglob('*.md'):
        # Skip references (unless explicitly enabled), hidden files, and hidden directories
        if (not include_refs and any(part == 'references' for part in path.parts)) or any(part.startswith('.') for part in path.parts):  # type: ignore[attr-defined]
            continue
        rel = str(path.relative_to(KNOW_DIR))
        text = _read(path)
        if not text:
            continue
        for title, body in _sections(text):
            hay = (title + "\n" + body).lower()
            # simple keyword overlap score
            score = sum(1 for k in keywords if k in hay)
            # boost if exact phrase occurs
            if q in hay:
                score += 5
            if score > 0:
                scored.append((score, rel, title, body))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [(src, title, body) for _, src, title, body in scored[:limit]]
