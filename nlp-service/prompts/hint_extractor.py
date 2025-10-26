from __future__ import annotations

from typing import Any, Dict

import re


def extract_llm_hints(query: str) -> Dict[str, Any]:
    """Extract lightweight hints from the user utterance to guide the LLM.

    Returns a dict that may include:
      - track_hint: "Return A" | "Track N" | "Master"
      - device_name_hint: device name (known generic or arbitrary name before param keywords)
      - device_ordinal_hint: 1-based ordinal (from "reverb 2" or "device 2" or word ordinals)
    """
    import re
    h: Dict[str, Any] = {}
    q = query or ""
    ql = q.lower()

    # Track/Return/Master
    m_ret = re.search(r"\breturn\s+([a-d])\b", ql)
    if m_ret:
        h["track_hint"] = f"Return {m_ret.group(1).upper()}"
    else:
        m_trk = re.search(r"\btrack\s+(\d+)\b", ql)
        if m_trk:
            h["track_hint"] = f"Track {int(m_trk.group(1))}"
        elif re.search(r"\bmaster\b", ql):
            h["track_hint"] = "Master"

    # Known generic device names
    generic = ["align delay", "reverb", "delay", "compressor", "eq", "equalizer"]
    found = None
    for name in generic:
        pat = name.replace(" ", r"\s+")
        if re.search(rf"\b{pat}\b", ql):
            found = name
            break
    if found:
        if found == "equalizer":
            found = "eq"
        h["device_name_hint"] = found

    # Arbitrary device names before known param keywords (e.g., "4th bandpass" before "mode")
    if "device_name_hint" not in h:
        m_arbitrary = re.search(r"\breturn\s+[a-d]\b\s+(?:the\s+)?(.+?)\s+(mode|quality|type|algorithm|alg|distunit|units?)\b", ql)
        if m_arbitrary:
            dn = m_arbitrary.group(1).strip()
            if dn:
                h["device_name_hint"] = dn

    # Ordinals (numeric and word)
    ord_map = {"first":1,"second":2,"third":3,"fourth":4,"fifth":5,"sixth":6,"seventh":7,"eighth":8,"ninth":9,"tenth":10}
    ord_val = None
    # Generic: device N
    m_devn = re.search(r"\bdevice\s+(\d+)\b", ql)
    if m_devn:
        ord_val = int(m_devn.group(1))
    # Named: <device> N
    if ord_val is None and ("device_name_hint" in h):
        pat = str(h["device_name_hint"]).replace(" ", r"\s+")
        m_named = re.search(rf"\b{pat}\s+(\d+)\b", ql)
        if m_named:
            ord_val = int(m_named.group(1))
    # Word ordinals
    if ord_val is None:
        m_word = re.search(r"\b(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth)\s+(?:device|" + (str(h.get("device_name_hint",""))).replace(" ", r"\s+") + r")\b", ql)
        if m_word:
            ord_val = ord_map.get(m_word.group(1).lower())
    if isinstance(ord_val, int) and ord_val > 0:
        h["device_ordinal_hint"] = ord_val

    return h


