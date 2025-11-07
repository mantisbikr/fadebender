from __future__ import annotations

"""
Lightweight local RAG for /help without Gemini File Search.

Builds a simple in-process index from:
  - data/sources/audio_engineering_knowledge_base_v1.md
  - data/sources/ableton-live-12-md.zip (markdown bundle)
Falls back gracefully if sources are missing.

Search: keyword overlap + exact phrase boost.
Answer: optionally summarized by LLM (Vertex) when available; otherwise
returns concatenated top snippets.
"""

import os
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import re

_INDEX_BUILT = False
_DOCS: List[Tuple[str, str, str]] = []  # (source, title, body)


def _sections(md: str) -> List[Tuple[str, str]]:
    out: List[Tuple[str, str]] = []
    parts = re.split(r"^#+\s+", md, flags=re.M)
    if not parts:
        return out
    it = iter(parts[1:])
    for title, body in zip(it, it):
        out.append((title.strip(), body.strip()))
    return out


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def _ingest_sources() -> None:
    global _DOCS
    root = Path(__file__).resolve().parents[2]
    # Audio KB (single file)
    kb = Path(os.getenv("AUDIO_ENG_KB_MD", root / "data" / "sources" / "audio_engineering_knowledge_base_v1.md"))
    if kb.exists():
        txt = _read_text(kb)
        for title, body in _sections(txt):
            _DOCS.append(("audio_kb", title, body))

    # Ableton manual zip (markdown bundle)
    zp = Path(os.getenv("ABLETON_MANUAL_ZIP", root / "data" / "sources" / "ableton-live-12-md.zip"))
    if zp.exists():
        try:
            with zipfile.ZipFile(zp, 'r') as zf:
                for n in zf.namelist():
                    if not n.lower().endswith('.md'):
                        continue
                    try:
                        with zf.open(n) as fh:
                            content = fh.read().decode('utf-8', errors='ignore')
                            for title, body in _sections(content):
                                _DOCS.append((f"manual:{n}", title, body))
                    except Exception:
                        continue
        except Exception:
            pass


def _ensure_index() -> None:
    global _INDEX_BUILT
    if _INDEX_BUILT:
        return
    _ingest_sources()
    _INDEX_BUILT = True


def _device_hints(q: str) -> List[str]:
    ql = (q or "").lower()
    hints = []
    for w in [
        "reverb", "delay", "compressor", "eq", "equalizer", "chorus", "flanger",
        "phaser", "saturator", "tension", "operator", "analog", "wavetable",
    ]:
        if w in ql:
            hints.append(w)
    # special phrase
    if "early reflections" in ql or " er " in f" {ql} ":
        hints.append("early reflections")
    return hints


def search_local(query: str, limit: int = 3) -> List[Tuple[str, str, str]]:
    """Return top (source, title, body) matches by simple keyword scoring."""
    _ensure_index()
    if not _DOCS:
        return []
    q = (query or "").lower()
    # Lightweight query expansion for common abbreviations
    expansions: List[str] = []
    if "er shape" in q:
        expansions += ["early reflections shape", "early reflection shape"]
    if re.search(r"\ber\b", q):
        expansions += [q.replace(" er ", " early reflections ")]
    # tokens: words >= 3 chars, plus keep quoted phrases as-is
    keywords = set(re.findall(r"[a-z0-9_]{3,}", q))
    phrase_boost = [p.lower() for p in re.findall(r"([A-Za-z][A-Za-z\s]{1,40}[A-Za-z])", query or "") if len(p.split()) >= 2]
    phrase_boost += expansions
    device_terms = _device_hints(q)
    scored: List[Tuple[float, str, str, str]] = []
    for src, title, body in _DOCS:
        hay = (title + "\n" + body).lower()
        score = 0.0
        score += sum(1 for k in keywords if k in hay)
        for ph in phrase_boost:
            if ph in hay:
                score += 4.0
        # Device/path/title boosts
        src_lc = (src or "").lower()
        title_lc = (title or "").lower()
        for t in device_terms:
            if t in src_lc:
                score += 3.0
            if t in title_lc:
                score += 2.0
        # Prefer audio effects over instruments for effect queries
        if any(t in ("reverb", "delay", "compressor", "eq", "chorus", "flanger", "phaser") for t in device_terms):
            if "instrument" in title_lc or "/instruments/" in src_lc:
                score -= 3.0
        if score > 0:
            # prefer shorter sections slightly
            score += max(0.0, 2.0 - min(len(body), 2000) / 2000.0)
            scored.append((score, src, title, body))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [(src, title, body) for _, src, title, body in scored[:limit]]


def _trim_lines(text: str, max_lines: int = 6, max_len: int = 120) -> str:
    lines = [ln.strip() for ln in (text or '').splitlines() if ln.strip()]
    out = []
    for ln in lines[:max_lines]:
        if len(ln) > max_len:
            ln = ln[: max_len - 1].rstrip() + '…'
        out.append(ln)
    return "\n".join(out)


def _llm_summarize(question: str, snippets: List[Tuple[str, str, str]]) -> Optional[str]:
    """Ask LLM (Vertex) to answer using provided snippets. Returns None on error."""
    try:
        from google import genai  # type: ignore
        from google.genai import types  # type: ignore
    except Exception:
        return None

    # Model selection: prefer context_analysis; falls back to default
    model = os.getenv("VERTEX_MODEL") or os.getenv("LLM_MODEL") or os.getenv("GEMINI_MODEL") or "gemini-2.5-flash"
    # If user prefers Lite, let them set env GEMINI_MODEL/LLM_MODEL to a lite variant

    project = os.getenv("LLM_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("PROJECT_ID") or "fadebender"
    location = os.getenv("GCP_REGION", os.getenv("VERTEX_LOCATION", "us-central1"))

    try:
        client = genai.Client(vertexai=True, project=project, location=location)
        kb_text = []
        for src, title, body in snippets:
            kb_text.append(f"Source: {src}\nTitle: {title}\n---\n{body}\n")
        context = "\n\n".join(kb_text[:3])
        sys_prompt = (
            "You are an audio engineering assistant for Ableton Live."
            " Answer ONLY using the provided context."
            " Format as 3–5 terse bullets, max ~80 chars each."
            " Cover: what it does, how to set it, typical ranges."
            " No preamble, no outro, no fluff."
        )
        cfg = types.GenerateContentConfig(temperature=0.1, max_output_tokens=220)
        contents = [
            types.Content(role="user", parts=[f"{sys_prompt}\n\nContext:\n{context}\n\nQuestion: {question}\nAnswer:"])
        ]
        resp = client.models.generate_content(model=model, contents=contents, config=cfg)
        text = getattr(resp, "text", None)
        if not text:
            return None
        return _trim_lines(text.strip(), max_lines=6, max_len=120)
    except Exception:
        return None


def answer_local_rag(query: str) -> Optional[Dict[str, Any]]:
    """Return {ok, answer, sources} using local RAG, or None if no match."""
    matches = search_local(query, limit=3)
    if not matches:
        return None
    # Try LLM summarize; fallback to concatenated snippets
    ans = _llm_summarize(query, matches)
    if not ans:
        ans = "\n\n".join([f"{t}:\n{b}" for _, t, b in matches[:2]])
    sources = [{"source": s, "title": t} for s, t, _ in matches]
    return {"ok": True, "answer": ans, "sources": sources}


__all__ = ["search_local", "answer_local_rag"]
