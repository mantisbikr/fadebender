from __future__ import annotations

import re
from typing import Any, Dict, Optional


def _intent(action: str, value: Optional[float] = None, utterance: Optional[str] = None) -> Dict[str, Any]:
    op: Dict[str, Any] = {"action": action}
    if value is not None:
        op["value"] = float(value)
    intent: Dict[str, Any] = {
        "intent": "transport",
        "targets": [],
        "operation": op,
        "meta": {"parsed_by": "regex_transport"}
    }
    if utterance:
        intent["meta"]["utterance"] = utterance
    return intent


def parse_transport_command(q: str, raw: str, _err: str, _model: Optional[str]) -> Optional[Dict[str, Any]]:
    s = q.lower().strip()

    # Play / Stop
    # Important: avoid matching "start" in phrases like "loop start".
    # Only treat explicit "play" or "start playing/playback" as play.
    if (re.search(r"\bplay\b", s) or re.search(r"\bstart\s+(play|playing|playback)\b", s)) and not re.search(r"\bstop\b", s):
        return _intent("play", utterance=raw)
    if re.search(r"\bstop\b", s):
        return _intent("stop", utterance=raw)

    # Record (toggle)
    if re.search(r"\b(start\s+record(ing)?|record\b)\b", s) and not re.search(r"stop\s+record", s):
        return _intent("record", utterance=raw)
    if re.search(r"\bstop\s+record(ing)?\b", s):
        return _intent("record", utterance=raw)

    # Metronome toggle / on / off
    if re.search(r"\bmetronome\b.*\bon\b", s) or re.search(r"\b(toggle|tap)\s+metronome\b", s):
        return _intent("metronome", utterance=raw)
    if re.search(r"\bmetronome\b.*\boff\b", s):
        return _intent("metronome", utterance=raw)

    # Tempo / BPM
    m = re.search(r"\b(set|change)\s+(tempo|bpm)\s*(to)?\s*(\d+(?:\.\d+)?)\b", s)
    if m:
        bpm = float(m.group(4))
        return _intent("tempo", bpm, raw)
    m = re.search(r"\b(tempo|bpm)\s*(to)?\s*(\d+(?:\.\d+)?)\b", s)
    if m:
        bpm = float(m.group(3))
        return _intent("tempo", bpm, raw)

    # Time signature
    # Full form: "set time signature to 3/8" → combined intent
    m = re.search(r"\bset\s+(time\s*signature|time\s*sig|timesig|meter)\s*(to\s*)?(\d+)\s*/\s*(\d+)\b", s)
    if m:
        num = int(m.group(3)); den = int(m.group(4))
        return {
            "intent": "transport",
            "targets": [],
            "operation": {"action": "time_sig_both", "value": {"num": num, "den": den}},
            "meta": {"parsed_by": "regex_transport", "utterance": raw}
        }
    # Shorthand forms: "time signature 3/8", "time sig 3/8", "meter 3/8"
    m = re.search(r"\b(time\s*signature|time\s*sig|timesig|meter)\s*(to\s*)?(\d+)\s*/\s*(\d+)\b", s)
    if m:
        num = int(m.group(3)); den = int(m.group(4))
        return {
            "intent": "transport",
            "targets": [],
            "operation": {"action": "time_sig_both", "value": {"num": num, "den": den}},
            "meta": {"parsed_by": "regex_transport", "utterance": raw}
        }
    m = re.search(r"\bset\s+(time\s*signature|time\s*sig|timesig|meter)\s+numerator\s*(to\s*)?(\d+)\b", s)
    if m:
        num = int(m.group(3))
        return _intent("time_sig_num", num, raw)
    m = re.search(r"\bset\s+(time\s*signature|time\s*sig|timesig|meter)\s+denominator\s*(to\s*)?(\d+)\b", s)
    if m:
        den = int(m.group(3))
        return _intent("time_sig_den", den, raw)
    # Reverse form: "3/8 time signature"
    m = re.search(r"\b(\d+)\s*/\s*(\d+)\b\s*(time\s*signature|time\s*sig|timesig|meter)\b", s)
    if m:
        num = int(m.group(1)); den = int(m.group(2))
        return {
            "intent": "transport",
            "targets": [],
            "operation": {"action": "time_sig_both", "value": {"num": num, "den": den}},
            "meta": {"parsed_by": "regex_transport", "utterance": raw}
        }

    # Loop controls (place before playhead to avoid accidental matches)
    m = re.search(r"\b(loop)\s*(on|off|toggle)\b", s)
    if m:
        mode = m.group(2).lower()
        if mode == 'toggle':
            return _intent("loop", None, raw)
        val = 1.0 if mode == 'on' else 0.0
        return _intent("loop_on", val, raw)
    if re.search(r"\b(enable\s+loop)\b", s):
        return _intent("loop_on", 1.0, raw)
    if re.search(r"\b(disable\s+loop)\b", s):
        return _intent("loop_on", 0.0, raw)
    m = re.search(r"\b(set|change)\s+loop\s+start\s*(to\s*)?(\d+(?:\.\d+)?)\b", s)
    if m:
        val = float(m.group(3))
        return _intent("loop_start", val, raw)
    m = re.search(r"\b(set|change)\s+loop\s+length\s*(to\s*)?(\d+(?:\.\d+)?)\b", s)
    if m:
        val = float(m.group(3))
        return _intent("loop_length", val, raw)

    # Playhead position and nudge (require explicit keyword to avoid collisions)
    m = re.search(r"\b(set|move|go\s*to|locate)\s*(the\s*)?(playhead|position)\s*(to\s*)?(\d+(?:\.\d+)?)\s*(beats?)?\b", s)
    if m:
        pos = float(m.group(5))
        return _intent("position", pos, raw)
    m = re.search(r"\b(go\s*to|move\s*to|locate)\s*bar\s*(\d+)\b", s)
    if m:
        bar = int(m.group(2)); beats = max(0, (bar - 1) * 4)
        return _intent("position", float(beats), raw)
    m = re.search(r"\b(nudge|move)\s*(forward|back|backward)?\s*(by\s*)?(\d+(?:\.\d+)?)\s*(bars?|beats?)?\b", s)
    if m:
        direction = (m.group(2) or '').lower(); amt = float(m.group(4)); unit = (m.group(5) or 'beats').lower()
        beats = amt * (4.0 if unit.startswith('bar') else 1.0)
        if direction in ('back', 'backward'):
            beats = -beats
        return _intent("nudge", beats, raw)

    return None
