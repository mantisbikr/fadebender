"""Regex-based parsing executor."""

from __future__ import annotations

import re
from typing import Dict, Any, List, Set

from parsers import (
    apply_typo_corrections,
    parse_mixer_command,
    parse_device_command,
    parse_transport_command,
)
from execution.response_builder import build_question_response


def _extract_known_terms_fast() -> Set[str]:
    """Extract known terms from config for typo detection.

    Returns set of canonical terms that should NOT be treated as typos.
    Optimized version that caches result.
    """
    # Use the same extraction as typo_learner but cache it
    try:
        from learning.typo_learner import _extract_known_terms
        return _extract_known_terms()
    except Exception:
        # Fallback to common terms
        return {
            'volume', 'pan', 'mute', 'solo', 'send', 'return', 'track',
            'reverb', 'delay', 'eq', 'compressor', 'amp', 'chorus', 'flanger', 'phaser',
            'decay', 'feedback', 'rate', 'depth', 'mix', 'wet', 'dry',
            'frequency', 'gain', 'threshold', 'ratio', 'attack', 'release',
            'set', 'get', 'what', 'is', 'the', 'to', 'at', 'by', 'of', 'on',
        }


def _extract_suspected_typos(query: str) -> List[str]:
    """Extract words from query that are not in known terms (suspected typos).

    Args:
        query: Original user query

    Returns:
        List of words that don't match known terms (potential typos)

    Examples:
        >>> _extract_suspected_typos("set track 2 paning to left")
        ['paning']
        >>> _extract_suspected_typos("set track 1 volme to -20")
        ['volme']
    """
    # Stop words that should never be treated as typos
    stop_words = {
        # Query structure words
        'set', 'make', 'change', 'adjust', 'get', 'what', 'is', 'the',
        'to', 'at', 'by', 'of', 'on', 'in', 'for', 'a', 'an', 'and',
        # Target types
        'track', 'return', 'device', 'plugin',
        # Action words (critical: never treat these as typos!)
        'mute', 'unmute', 'solo', 'unsolo', 'enable', 'disable',
        'bypass', 'unbypass', 'arm', 'unarm',
        # Directional words
        'left', 'right', 'center',
        # Ordinals (though converted to numbers)
        'first', 'second', 'third', 'fourth', 'fifth',
    }

    known_terms = _extract_known_terms_fast()

    # Tokenize query (extract alphabetic words)
    tokens = re.findall(r'\b[a-z]+\b', query.lower())

    # Find words not in known terms or stop words
    suspected = []
    for token in tokens:
        if token not in known_terms and token not in stop_words and len(token) >= 3:
            suspected.append(token)

    return suspected


def try_regex_parse(
    query: str,
    error_msg: str,
    model_preference: str | None
) -> tuple[Dict[str, Any] | None, List[str]]:
    """Try regex-based parsing.

    Args:
        query: User query text
        error_msg: Error message from previous attempts
        model_preference: User's model preference

    Returns:
        Tuple of (Intent dict if matched or None, list of suspected typo words)
        - If parsing succeeds: (intent_dict, [])
        - If parsing fails: (None, ['suspected', 'typo', 'words'])
    """
    # Apply typo corrections and expand ordinal words
    q = apply_typo_corrections(query)

    # Try mixer commands first (most common: volume, pan, solo, mute, sends)
    result = parse_mixer_command(q, query, error_msg, model_preference)
    if result:
        return result, []

    # Try transport commands (play/stop/record/metronome/tempo/position/nudge/time signature/loop)
    result = parse_transport_command(q, query, error_msg, model_preference)
    if result:
        return result, []

    # Try device commands (reverb, delay, compressor, etc.)
    result = parse_device_command(q, query, error_msg, model_preference)
    if result:
        return result, []

    # Special: Topology questions about sends/connectivity
    try:
        import re as _re
        # Pattern A: "what does/is track 1 send A affect/connect..."
        m1 = _re.search(r"what\s+(?:does|is)\s+track\s+(\d+)\s+send\s+([a-c])\s+(?:affect|connect\w*|go\s+to|route|target|do)\b", q)
        # Pattern B: "what is the effect on track 1 send A"
        m2 = _re.search(r"what\s+is\s+the\s+effect\s+on\s+track\s+(\d+)\s+send\s+([a-c])\b", q)
        m = m1 or m2
        if m:
            ti = int(m.group(1))
            letter = m.group(2).upper()
            intent = {
                "intent": "get_parameter",
                "targets": [
                    {"track": f"Track {ti}", "plugin": None, "parameter": f"send {letter} effects"}
                ],
                "meta": {"parsed_by": "regex_topology"}
            }
            return intent, []
    except Exception:
        pass

    # Open capabilities (drawer) requests
    try:
        oc = _open_capabilities_from_regex(q)
        if oc:
            return oc, []
    except Exception:
        pass

    # Pattern: device list queries
    try:
        import re as _re
        # "what are return A devices" | "what are track 1 devices" | "device list"
        m_ret = _re.search(r"what\s+are\s+return\s+([a-c])\s+devices\b", q)
        m_trk = _re.search(r"what\s+are\s+track\s+(\d+)\s+devices\b", q)
        if m_ret:
            letter = m_ret.group(1).upper()
            intent = {
                "intent": "get_parameter",
                "targets": [{"track": f"Return {letter}", "plugin": None, "parameter": "devices"}],
                "meta": {"parsed_by": "regex_devices"}
            }
            return intent, []
        if m_trk:
            ti = int(m_trk.group(1))
            intent = {
                "intent": "get_parameter",
                "targets": [{"track": f"Track {ti}", "plugin": None, "parameter": "devices"}],
                "meta": {"parsed_by": "regex_devices"}
            }
            return intent, []
    except Exception:
        pass

    # Pattern: sources for return
    try:
        import re as _re
        m = _re.search(r"(who|which\s+tracks)\s+sends?\s+to\s+return\s+([a-c])\b", q)
        if m:
            letter = m.group(2).upper()
            intent = {
                "intent": "get_parameter",
                "targets": [{"track": f"Return {letter}", "plugin": None, "parameter": "sources"}],
                "meta": {"parsed_by": "regex_sources"}
            }
            return intent, []
    except Exception:
        pass

    # Pattern: mixer state bundle
    try:
        import re as _re
        # "what is track 1 state" | "what is return A state" | "what is master state"
        m_trk = _re.search(r"what\s+is\s+track\s+(\d+)\s+state\b", q)
        m_ret = _re.search(r"what\s+is\s+return\s+([a-c])\s+state\b", q)
        m_mas = _re.search(r"what\s+is\s+master\s+state\b", q)
        if m_trk:
            ti = int(m_trk.group(1))
            intent = {
                "intent": "get_parameter",
                "targets": [{"track": f"Track {ti}", "plugin": None, "parameter": "state"}],
                "meta": {"parsed_by": "regex_state"}
            }
            return intent, []
        if m_ret:
            letter = m_ret.group(1).upper()
            intent = {
                "intent": "get_parameter",
                "targets": [{"track": f"Return {letter}", "plugin": None, "parameter": "state"}],
                "meta": {"parsed_by": "regex_state"}
            }
            return intent, []
        if m_mas:
            intent = {
                "intent": "get_parameter",
                "targets": [{"track": "Master", "plugin": None, "parameter": "state"}],
                "meta": {"parsed_by": "regex_state"}
            }
            return intent, []
    except Exception:
        pass

    # Pattern: returns summary (track sends)
    try:
        import re as _re
        m = _re.search(r"what\s+is\s+track\s+(\d+)\s+returns\b", q)
        if m:
            ti = int(m.group(1))
            return {
                "intent": "get_parameter",
                "targets": [{"track": f"Track {ti}", "plugin": None, "parameter": "returns"}],
                "meta": {"parsed_by": "regex_returns"}
            }, []
    except Exception:
        pass

    # Questions about problems (treat as help-style queries)
    if any(phrase in q for phrase in [
        "too soft", "too quiet", "can't hear", "how to", "what does",
        "weak", "thin", "muddy", "boomy", "harsh", "dull"
    ]):
        return build_question_response(query, error_msg, model_preference), []

    # No match - extract suspected typos for learning
    suspected_typos = _extract_suspected_typos(query)
    return None, suspected_typos


def _open_capabilities_from_regex(q: str):
    """Recognize "open …" drawer requests and return an open_capabilities intent.

    Returns intent dict or None.
    """
    import re as _re
    qs = q.strip().lower()
    if not qs.startswith("open "):
        return None

    # PRIORITY: specific patterns before generic mixer opens
    # Sends group (preselect) – must be checked before generic track mixer
    m = _re.search(r"^\s*open\s+track\s+(\d+)\s+send\s+([a-c])(?:\s+controls)?\s*$", qs)
    if m:
        ti = int(m.group(1)); letter = m.group(2).upper()
        return {
            "intent": "open_capabilities",
            "target": {"type": "mixer", "entity": "track", "track_index": ti, "group_hint": "Sends", "send_ref": letter},
            "meta": {"parsed_by": "regex_open"}
        }

    # Device on return by index
    m = _re.search(r"^\s*open\s+return\s+([a-c])\s+device\s+(\d+)(?:\s+([a-z0-9][a-z0-9 /%\.-]+))?\s*$", qs)
    if m:
        letter = m.group(1).upper(); di = int(m.group(2)); ph = (m.group(3) or '').strip() or None
        return {
            "intent": "open_capabilities",
            "target": {"type": "device", "scope": "return", "return_ref": letter, "device_index": di, **({"param_hint": ph} if ph else {})},
            "meta": {"parsed_by": "regex_open"}
        }

    # Device on return by name (+ optional ordinal)
    m = _re.search(r"^\s*open\s+return\s+([a-c])\s+([a-z0-9 ][a-z0-9 \-]+?)(?:\s+(\d+))?(?:\s+([a-z0-9][a-z0-9 /%\.-]+))?\s*$", qs)
    if m:
        letter = m.group(1).upper(); name = m.group(2).strip(); ords = m.group(3); ph = (m.group(4) or '').strip() or None
        payload = {"type": "device", "scope": "return", "return_ref": letter, "device_name_hint": name}
        if ords:
            try: payload["device_ordinal_hint"] = int(ords)
            except Exception: pass
        if ph:
            payload["param_hint"] = ph
        return {"intent": "open_capabilities", "target": payload, "meta": {"parsed_by": "regex_open"}}

    # Generic mixer scopes (checked after device/sends patterns to avoid premature matches)
    m = _re.search(r"^\s*open\s+track\s+(\d+)(?:\s+(?:controls|mixer))?\s*$", qs)
    if m:
        ti = int(m.group(1))
        return {
            "intent": "open_capabilities",
            "target": {"type": "mixer", "entity": "track", "track_index": ti},
            "meta": {"parsed_by": "regex_open"}
        }
    m = _re.search(r"^\s*open\s+return\s+([a-c])(?:\s+(?:controls|mixer))?\s*$", qs)
    if m:
        letter = m.group(1).upper()
        return {
            "intent": "open_capabilities",
            "target": {"type": "mixer", "entity": "return", "return_ref": letter},
            "meta": {"parsed_by": "regex_open"}
        }
    m = _re.search(r"^\s*open\s+master(?:\s+(?:controls|mixer))?\s*$", qs)
    if m:
        return {"intent": "open_capabilities", "target": {"type": "mixer", "entity": "master"}, "meta": {"parsed_by": "regex_open"}}

    # Drawer actions
    m = _re.search(r"^\s*open\s+controls\s*$", qs)
    if m:
        return {"intent": "open_capabilities", "target": {"type": "drawer", "action": "open"}, "meta": {"parsed_by": "regex_open"}}
    m = _re.search(r"^\s*close\s+controls\s*$", qs)
    if m:
        return {"intent": "open_capabilities", "target": {"type": "drawer", "action": "close"}, "meta": {"parsed_by": "regex_open"}}
    m = _re.search(r"^\s*pin\s+controls\s*$", qs)
    if m:
        return {"intent": "open_capabilities", "target": {"type": "drawer", "action": "pin"}, "meta": {"parsed_by": "regex_open"}}
    m = _re.search(r"^\s*unpin\s+controls\s*$", qs)
    if m:
        return {"intent": "open_capabilities", "target": {"type": "drawer", "action": "unpin"}, "meta": {"parsed_by": "regex_open"}}

    return None
