"""
Device Context Parser

Provides device-context-aware parsing using the parse index vocabulary.
Resolves parameter ambiguity by considering which devices are in the current Live set.

Example:
    parser = DeviceContextParser(parse_index)
    result = parser.parse_device_param("set return A reverb decay to 5 seconds")
    # result.device = "Reverb"
    # result.param = "Decay"  (not ambiguous because we know it's a reverb)
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple


# ------------------ Normalization ------------------

CONFUSABLES = {
    "—": "-", "–": "-", """: "\"", """: "\"", "'": "'", "'": "'"
}


def normalize_text(s: str) -> str:
    """Normalize text for parsing: lowercase, normalize unicode, replace confusables."""
    s = s.lower()
    s = unicodedata.normalize("NFKC", s)
    for k, v in CONFUSABLES.items():
        s = s.replace(k, v)
    s = re.sub(r"\s+", " ", s).strip()
    return s


# ------------------ Fuzzy Matching ------------------

def damerau_levenshtein(a: str, b: str) -> int:
    """Calculate Damerau-Levenshtein edit distance between two strings."""
    n, m = len(a), len(b)
    if n == 0:
        return m
    if m == 0:
        return n

    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,        # deletion
                dp[i][j - 1] + 1,        # insertion
                dp[i - 1][j - 1] + cost  # substitution
            )
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                dp[i][j] = min(dp[i][j], dp[i - 2][j - 2] + 1)  # transposition

    return dp[n][m]


def token_ok(query_token: str, candidate: str) -> Tuple[bool, float]:
    """
    Check if query token matches candidate within acceptable edit distance.

    Returns:
        (match_ok, normalized_distance)
    """
    if not query_token or not candidate:
        return (False, 1.0)

    dist = damerau_levenshtein(query_token, candidate)
    L = max(len(candidate), 3)
    norm = dist / L

    # Thresholds by length (stricter for short words)
    if len(candidate) <= 3 and dist > 0:
        return (False, norm)
    if 4 <= len(candidate) <= 6 and dist > 1:
        return (False, norm)
    if 7 <= len(candidate) <= 10 and dist > 2:
        return (False, norm)
    if len(candidate) >= 11 and dist > 3:
        return (False, norm)

    return (True, norm)


def phrase_score(query_phrase: str, candidate_phrase: str) -> float:
    """
    Calculate fuzzy match score between query and candidate phrases.
    Handles space/hyphen variations.

    Returns:
        Score (0.0 = perfect match, higher = worse match)
    """
    # Normalize spaces and hyphens
    qtoks = query_phrase.replace("-", " ").split()
    ctoks = candidate_phrase.replace("-", " ").split()

    if not ctoks:
        return 1.0

    scores = []
    for i, c in enumerate(ctoks):
        q = qtoks[i] if i < len(qtoks) else ""
        ok, sc = token_ok(q, c)

        # Weight rightmost token higher (more discriminative)
        if i == len(ctoks) - 1:
            sc *= 0.67

        scores.append(sc if ok else 1.0)

    return sum(scores) / len(scores)


# ------------------ Regex Builder ------------------

def build_alt(sorted_list: List[str]) -> str:
    """Build regex alternation pattern from list (longest first to avoid prefix issues)."""
    parts = [re.escape(x) for x in sorted(sorted_list, key=len, reverse=True)]
    return r"(?i)(?:^|(?<=\s))(?:" + "|".join(parts) + r")(?:(?=\s)|$)"


# ------------------ Data Classes ------------------

@dataclass
class DeviceParamMatch:
    """Result of device + parameter parsing."""
    device: Optional[str]                 # Canonical device name (e.g., "Reverb")
    device_type: Optional[str]            # Device type (e.g., "reverb")
    device_ordinal: Optional[int]         # Device instance number (e.g., 2 for "reverb 2")
    param: Optional[str]                  # Canonical parameter name (e.g., "Decay")
    confidence: float                     # 0.0-1.0 confidence score
    method: str                           # "exact" | "fuzzy_device" | "fuzzy_param" | "fuzzy_both"


# ------------------ Device Context Parser ------------------

class DeviceContextParser:
    """
    Parser that uses parse index vocabulary for device-context-aware parameter parsing.

    The parser resolves parameter ambiguities by considering:
    1. Which devices are currently in the Live set
    2. Device type context (e.g., "decay" in reverb vs delay)
    3. Device-specific parameter names and aliases
    """

    def __init__(self, parse_index: Dict):
        """
        Initialize parser with parse index vocabulary.

        Args:
            parse_index: Parse index dict from ParseIndexBuilder
        """
        self.index = parse_index
        self.mixer_params = set(parse_index.get("mixer_params", []))

        # Build device vocabulary (names + aliases)
        device_names = []
        for d in parse_index["devices_in_set"]:
            device_names.append(d["name"])
            for a in d.get("aliases", []):
                device_names.append(a)

        self.device_vocab = device_names
        self.DEVICE_RE = re.compile(build_alt(device_names)) if device_names else None

        # Build per-device parameter regexes
        self.PARAM_RE = {}
        for dev, spec in parse_index["params_by_device"].items():
            plist = list(spec.get("params", []))
            for pname, alist in spec.get("aliases", {}).items():
                plist.extend(alist)
            self.PARAM_RE[dev] = re.compile(build_alt(plist)) if plist else None

        # Build global parameter regex (mixer + all device params)
        all_params = set(parse_index.get("mixer_params", []))
        for spec in parse_index["params_by_device"].values():
            all_params.update(spec.get("params", []))
            for al in spec.get("aliases", {}).values():
                all_params.update(al)

        self.ALL_PARAM_RE = re.compile(build_alt(list(all_params))) if all_params else None

        # Build canonical mappings (lowercase → canonical)
        self.device_canonical = {}
        for d in parse_index['devices_in_set']:
            self.device_canonical[d['name'].lower()] = d['name']
            for a in d.get('aliases', []):
                self.device_canonical[a.lower()] = d['name']

        self.param_canonical = {}
        for dev, spec in parse_index['params_by_device'].items():
            for p in spec.get('params', []):
                self.param_canonical[p.lower()] = p
            for canon, als in spec.get('aliases', {}).items():
                self.param_canonical[canon.lower()] = canon
                for a in als:
                    self.param_canonical[a.lower()] = canon

        # Device type lookup
        self.device_types = {}
        for dev, spec in parse_index['params_by_device'].items():
            self.device_types[dev] = spec.get('device_type', 'unknown')

        self.typo_map = parse_index.get("typo_map", {})

    def apply_typo_map(self, text: str) -> str:
        """Apply typo corrections from parse index."""
        tokens = text.split()
        corrected = " ".join(self.typo_map.get(tok, tok) for tok in tokens)
        return corrected

    def fuzzy_best(
        self,
        text: str,
        vocab: List[str],
        want: str = "rightmost",
        limit_region: Optional[Tuple[int, int]] = None
    ) -> Optional[Tuple[str, Tuple[int, int], float]]:
        """
        Find best fuzzy match in text using sliding window.

        Args:
            text: Text to search in
            vocab: List of candidate strings to match
            want: "leftmost" or "rightmost" (tie-breaker for equal scores)
            limit_region: Optional (start, end) character indices to limit search

        Returns:
            (matched_string, (start_idx, end_idx), score) or None if no match
        """
        start, end = (0, len(text)) if not limit_region else limit_region
        snippet = text[start:end]

        best = None
        for cand in vocab:
            words = snippet.split()
            if not words:
                continue

            # Sliding window: try all combinations of 1-5 consecutive words
            for i in range(len(words)):
                for L in range(1, min(5, len(words) - i) + 1):
                    span_words = words[i:i + L]
                    span_text = " ".join(span_words)
                    sc = phrase_score(span_text, cand)

                    # Accept if score is good enough (< 0.34 = ~66% match quality)
                    if sc <= 0.34:
                        # Convert word indices to character indices
                        char_start = sum(len(words[j]) + 1 for j in range(i))
                        char_end = char_start + len(span_text)
                        abs_span = (start + char_start, start + char_end)
                        entry = (cand, abs_span, sc)

                        # Update best match using score + position preference
                        if best is None:
                            best = entry
                        else:
                            # Prefer lower score (better match)
                            if sc < best[2] - 1e-6:
                                best = entry
                            # Tie: use position preference
                            elif abs(sc - best[2]) < 1e-6:
                                if want == "leftmost" and abs_span[0] < best[1][0]:
                                    best = entry
                                elif want == "rightmost" and abs_span[1] > best[1][1]:
                                    best = entry

        return best

    def parse_device_param(self, text: str) -> DeviceParamMatch:
        """
        Parse device and parameter from text using device-context-aware matching.

        Args:
            text: Input text (e.g., "set reverb decay to 5 seconds")

        Returns:
            DeviceParamMatch with parsed device, param, and confidence
        """
        # Normalize and apply typo corrections
        text = normalize_text(text)
        text = self.apply_typo_map(text)

        device = None
        device_span = None
        param = None
        param_span = None
        confidence = 0.0
        method = "none"

        # Try exact device match first
        if self.DEVICE_RE:
            dev_m = self.DEVICE_RE.search(text)
            if dev_m:
                device = self.device_canonical.get(dev_m.group(0).lower(), dev_m.group(0))
                device_span = dev_m.span()
                confidence += 0.5
                method = "exact"

        # Try exact parameter match (search after device if found)
        start_idx = 0 if not device_span else device_span[1]
        if self.ALL_PARAM_RE:
            prm_m = self.ALL_PARAM_RE.search(text[start_idx:])
            if prm_m:
                param = self.param_canonical.get(prm_m.group(0).lower(), prm_m.group(0))
                param_span = (start_idx + prm_m.start(), start_idx + prm_m.end())
                confidence += 0.5
                if method == "exact":
                    method = "exact"
            else:
                # Try fuzzy parameter match
                vocab = set()
                vocab.update(self.index.get("mixer_params", []))
                for spec in self.index["params_by_device"].values():
                    vocab.update(spec.get("params", []))
                    for vs in spec.get("aliases", {}).values():
                        vocab.update(vs)

                best = self.fuzzy_best(text, list(vocab), want="rightmost", limit_region=(start_idx, len(text)))
                if best:
                    param = self.param_canonical.get(best[0].lower(), best[0])
                    param_span = best[1]
                    confidence += 0.35
                    method = "fuzzy_param" if method == "exact" else "fuzzy_param"

        # If no device found, try fuzzy device match
        if not device:
            best_dev = self.fuzzy_best(text, self.device_vocab, want="leftmost")
            if best_dev:
                device = self.device_canonical.get(best_dev[0].lower(), best_dev[0])
                device_span = best_dev[1]
                confidence += 0.35
                method = "fuzzy_both" if "fuzzy" in method else "fuzzy_device"

                # If still no param, try fuzzy param after device
                if not param:
                    start_idx = device_span[1] if device_span else 0
                    vocab = set()
                    for spec in self.index["params_by_device"].values():
                        vocab.update(spec.get("params", []))
                        for vs in spec.get("aliases", {}).values():
                            vocab.update(vs)
                    vocab.update(self.index.get("mixer_params", []))

                    best_prm = self.fuzzy_best(text, list(vocab), want="rightmost", limit_region=(start_idx, len(text)))
                    if best_prm:
                        param = self.param_canonical.get(best_prm[0].lower(), best_prm[0])
                        param_span = best_prm[1]
                        confidence += 0.35
                        method = "fuzzy_both"

        # Extract device ordinal if present (e.g., "reverb 2", "delay #3")
        device_ordinal = None
        if device and device_span:
            post_device = text[device_span[1]:]
            m = re.search(r"(?:#|\s)(\d+)\b", post_device)
            if m:
                try:
                    device_ordinal = int(m.group(1))
                except:
                    pass

        # Get device type
        device_type = self.device_types.get(device, "unknown") if device else None

        # Clamp confidence to [0.0, 1.0]
        confidence = max(0.0, min(1.0, confidence))

        return DeviceParamMatch(
            device=device,
            device_type=device_type,
            device_ordinal=device_ordinal,
            param=param,
            confidence=confidence,
            method=method
        )
