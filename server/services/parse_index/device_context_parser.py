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


def generate_phrase_space_variations(text: str) -> List[str]:
    """Generate space-normalized variations of a SHORT phrase (1-5 words).

    This is used during fuzzy matching to handle space typos at the token level.
    For example, when matching "mixgel" against "Mix Gel" or "8 dot ball" against "8DotBall".

    Strategy:
    - Original text
    - Remove spaces (join all words)
    - Add spaces before digits and capital letters

    Examples:
        "mixgel" → ["mixgel", "mix gel"]
        "mix gel" → ["mix gel", "mixgel"]
        "8dotball" → ["8dotball", "8 dot ball"]
        "8 dot ball" → ["8 dot ball", "8dotball"]
        "roomsize" → ["roomsize", "room size"]

    Args:
        text: A short phrase (typically from sliding window during fuzzy matching)

    Returns:
        List of space-normalized variations
    """
    variations = [text]

    # Variation 1: Remove all spaces (if present)
    if " " in text:
        no_space = text.replace(" ", "")
        if no_space not in variations:
            variations.append(no_space)

    # Variation 2: Add spaces before digits and capital letters
    # "8dotball" → "8 dot ball", "mixgel" → "mix gel", "roomsize" → "room size"
    spaced = re.sub(r'(\d)([a-z])', r'\1 \2', text)  # digit followed by letter
    spaced = re.sub(r'([a-z])([A-Z])', r'\1 \2', spaced)  # lowercase followed by uppercase

    # Also try adding space before uppercase letters in the middle
    # "MixGel" → "Mix Gel"
    if spaced != text and spaced not in variations:
        variations.append(spaced)

    return variations


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

    Relaxed thresholds to handle common typos (missing/transposed/wrong characters).

    Returns:
        (match_ok, normalized_distance)
    """
    if not query_token or not candidate:
        return (False, 1.0)

    dist = damerau_levenshtein(query_token, candidate)
    L = max(len(candidate), 3)
    norm = dist / L

    # Relaxed thresholds to handle common typos
    # Allow 1 edit for short words (was 0 for len <= 3)
    if len(candidate) <= 4 and dist > 1:
        return (False, norm)
    if 5 <= len(candidate) <= 7 and dist > 2:
        return (False, norm)
    if 8 <= len(candidate) <= 10 and dist > 3:
        return (False, norm)
    if len(candidate) >= 11 and dist > 4:
        return (False, norm)

    return (True, norm)


def phrase_score(query_phrase: str, candidate_phrase: str) -> float:
    """
    Calculate fuzzy match score between query and candidate phrases.
    Handles space/hyphen variations and space-normalized matching.

    Returns:
        Score (0.0 = perfect match, higher = worse match)
    """
    # Normalize spaces and hyphens
    qtoks = query_phrase.replace("-", " ").split()
    ctoks = candidate_phrase.replace("-", " ").split()

    if not ctoks:
        return 1.0

    # Special case: if token counts mismatch, try space-normalized comparison
    # e.g., query="mixgel" (1 token) vs candidate="mix gel" (2 tokens)
    if len(qtoks) != len(ctoks):
        # Try comparing with spaces removed
        q_nospace = query_phrase.replace(" ", "").replace("-", "")
        c_nospace = candidate_phrase.replace(" ", "").replace("-", "")
        ok, sc = token_ok(q_nospace, c_nospace)
        if ok:
            return sc

    # Token-by-token comparison (original logic)
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

        # Build device type vocabulary (for excluding from parameter matches)
        device_types_list = list(set(
            spec.get('device_type', '')
            for spec in parse_index['params_by_device'].values()
        ))
        device_types_list = [dt for dt in device_types_list if dt and dt != 'unknown']

        # Combine device names and types into exclusion set (lowercase for matching)
        self.device_words = set(d.lower() for d in device_names + device_types_list)

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

    def get_canonical_param(self, param_text: str, device_name: Optional[str] = None) -> str:
        """Get canonical parameter name, optionally scoped to a specific device.

        This handles the case where multiple devices have different canonical forms
        for the same normalized parameter (e.g., "Dry/Wet" vs "Dry Wet").

        Args:
            param_text: The parameter text to canonicalize (e.g., "dry wet")
            device_name: Optional device name to scope the lookup

        Returns:
            Canonical parameter name for the device, or the input if not found
        """
        param_lower = param_text.lower()

        # If device is specified, look up canonical form within that device's parameters
        if device_name and device_name in self.index["params_by_device"]:
            device_spec = self.index["params_by_device"][device_name]

            # Check direct parameters
            for param in device_spec.get("params", []):
                if param.lower() == param_lower:
                    return param

            # Check aliases
            for canonical, aliases in device_spec.get("aliases", {}).items():
                if canonical.lower() == param_lower:
                    return canonical
                for alias in aliases:
                    if alias.lower() == param_lower:
                        return canonical

        # Fall back to global param_canonical
        return self.param_canonical.get(param_lower, param_text)

    def fuzzy_best(
        self,
        text: str,
        vocab: List[str],
        want: str = "rightmost",
        limit_region: Optional[Tuple[int, int]] = None,
        exclude_device_words: bool = False
    ) -> Optional[Tuple[str, Tuple[int, int], float]]:
        """
        Find best fuzzy match in text using sliding window with space normalization.

        Args:
            text: Text to search in
            vocab: List of candidate strings to match
            want: "leftmost" or "rightmost" (tie-breaker for equal scores)
            limit_region: Optional (start, end) character indices to limit search
            exclude_device_words: If True, skip spans that contain device/type words

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

                    # Smart device word filtering: extract non-device words from span
                    if exclude_device_words and hasattr(self, 'device_words'):
                        # Filter out device words, keep the rest
                        non_device_words = [w for w in span_words if w.lower() not in self.device_words]

                        if not non_device_words:
                            # All words are device words, skip entire span
                            continue

                        if len(non_device_words) < len(span_words):
                            # Some device words filtered out, use remaining words
                            span_text = " ".join(non_device_words)

                    # Try space-normalized variations of the span
                    # This handles typos like "mixgel" vs "mix gel" or "8 dot ball" vs "8dotball"
                    span_variations = generate_phrase_space_variations(span_text)

                    # Try matching each variation
                    best_variation_score = None
                    for span_var in span_variations:
                        sc = phrase_score(span_var, cand)
                        if best_variation_score is None or sc < best_variation_score:
                            best_variation_score = sc

                    # Use the best score from all variations
                    sc = best_variation_score

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

    def _parse_device_param_internal(self, text: str) -> DeviceParamMatch:
        """
        Internal method: Parse device and parameter using dynamic device-type resolution.

        Algorithm:
        1. Parse parameter name (exact/fuzzy, excluding spans with device words)
        2. Look up which device types have this parameter (from Firestore)
        3. Find device type/name word in text (e.g., "delay", "4th bandpass", "reverb")
        4. Resolve device type to actual device name from snapshot
        5. Handle ordinals and ambiguity

        The parameter-first approach is intentional: often the parameter is easier to
        identify than the device. Fuzzy matching excludes spans containing device/type
        words to prevent "reverb decay" from matching as a single parameter.

        Args:
            text: Input text (already normalized, e.g., "set reverb decay to 5")

        Returns:
            DeviceParamMatch with parsed device, param, and confidence
        """

        device = None
        device_type = None
        device_ordinal = None
        param = None
        confidence = 0.0
        method = "none"

        # Step 1: Try exact parameter match
        if self.ALL_PARAM_RE:
            prm_m = self.ALL_PARAM_RE.search(text)
            if prm_m:
                param = self.param_canonical.get(prm_m.group(0).lower(), prm_m.group(0))
                param_span = prm_m.span()
                confidence += 0.5
                method = "exact"
            else:
                # Try fuzzy parameter match - exclude spans containing device/type words
                # This prevents "reverb decay" from matching as single parameter
                vocab = set()
                vocab.update(self.index.get("mixer_params", []))
                for spec in self.index["params_by_device"].values():
                    vocab.update(spec.get("params", []))
                    for vs in spec.get("aliases", {}).values():
                        vocab.update(vs)

                best = self.fuzzy_best(text, list(vocab), want="rightmost", exclude_device_words=True)
                if best:
                    param = self.param_canonical.get(best[0].lower(), best[0])
                    param_span = best[1]
                    confidence += 0.35
                    method = "fuzzy_param"
        else:
            return DeviceParamMatch(None, None, None, None, 0.0, "no_params")

        # If no parameter found, return early
        if not param:
            return DeviceParamMatch(None, None, None, None, 0.0, "no_param_match")

        # Step 2: Look up which device types have this parameter
        param_to_types = self.index.get("param_to_device_types", {})
        candidate_types = param_to_types.get(param, [])

        if not candidate_types:
            # Parameter not found in any device - return with low confidence
            return DeviceParamMatch(None, None, None, param, confidence * 0.5, method + "_no_device_types")

        # Step 4: Try exact device name match first
        if self.DEVICE_RE:
            dev_m = self.DEVICE_RE.search(text)
            if dev_m:
                device = self.device_canonical.get(dev_m.group(0).lower(), dev_m.group(0))
                device_span = dev_m.span()
                device_type = self.device_types.get(device, "unknown")

                # Extract ordinal if present
                post_device = text[device_span[1]:]
                m = re.search(r"(?:#|\s)(\d+)\b", post_device)
                if m:
                    try:
                        device_ordinal = int(m.group(1))
                    except:
                        pass

                # Device name found - verify param belongs to this device
                device_spec = self.index["params_by_device"].get(device, {})
                device_param_list = device_spec.get("params", [])

                if param in device_param_list:
                    # Parameter belongs to this device - perfect match
                    confidence += 0.5
                    method = "exact" if method == "exact" else "exact_device"
                    return DeviceParamMatch(device, device_type, device_ordinal, param, confidence, method)
                else:
                    # Parameter doesn't belong to this device - search device's params for match
                    # Try exact match in device's params first
                    if self.PARAM_RE.get(device):
                        param_re = self.PARAM_RE[device]
                        start_idx = device_span[1]
                        prm_m = param_re.search(text[start_idx:])
                        if prm_m:
                            # Use device-scoped canonical lookup
                            param = self.get_canonical_param(prm_m.group(0), device)
                            confidence = 1.0  # Reset confidence for exact match
                            method = "exact"
                            return DeviceParamMatch(device, device_type, device_ordinal, param, confidence, method)

                    # Try fuzzy match in device's params
                    device_param_vocab = list(device_param_list)
                    for pname, alist in device_spec.get("aliases", {}).items():
                        device_param_vocab.extend(alist)

                    if device_param_vocab:
                        start_idx = device_span[1]
                        best_prm = self.fuzzy_best(text, device_param_vocab, want="rightmost", limit_region=(start_idx, len(text)))
                        if best_prm:
                            # Use device-scoped canonical lookup
                            param = self.get_canonical_param(best_prm[0], device)
                            confidence += 0.35
                            method = "exact_device_fuzzy_param"
                            return DeviceParamMatch(device, device_type, device_ordinal, param, confidence, method)

                    # Device found but no matching param - return what we have
                    confidence += 0.3
                    method = "device_only"
                    return DeviceParamMatch(device, device_type, device_ordinal, param, confidence * 0.6, method)

        # Step 5: Try device type resolution (e.g., "delay" → "4th Bandpass")
        # Build regex for device types that have this parameter
        type_names = candidate_types
        type_pattern = build_alt(type_names) if type_names else None

        if type_pattern:
            type_re = re.compile(type_pattern)
            type_m = type_re.search(text)

            if type_m:
                # Found device type in text
                matched_type = type_m.group(0).lower()
                device_type_index = self.index.get("device_type_index", {})

                # Find devices in snapshot with this type
                devices_with_type = device_type_index.get(matched_type, [])

                if devices_with_type:
                    # Extract ordinal if present (e.g., "delay 2")
                    post_type = text[type_m.end():]
                    m = re.search(r"(?:#|\s)(\d+)\b", post_type)
                    if m:
                        try:
                            device_ordinal = int(m.group(1))
                        except:
                            pass

                    if len(devices_with_type) == 1:
                        # Unambiguous - only one device of this type
                        device = devices_with_type[0]
                        device_type = matched_type
                        confidence += 0.4
                        method = "type_resolution" if method == "exact" else "fuzzy_type_resolution"
                    elif device_ordinal:
                        # Multiple devices, but ordinal specified
                        if 1 <= device_ordinal <= len(devices_with_type):
                            device = devices_with_type[device_ordinal - 1]
                            device_type = matched_type
                            confidence += 0.4
                            method = "type_resolution_ordinal"
                        else:
                            # Invalid ordinal
                            device = None
                            confidence *= 0.5
                            method = "invalid_ordinal"
                    else:
                        # Ambiguous - multiple devices, no ordinal
                        # Return first device but mark as ambiguous
                        device = devices_with_type[0]
                        device_type = matched_type
                        confidence *= 0.6  # Lower confidence for ambiguity
                        method = "type_resolution_ambiguous"

                    return DeviceParamMatch(device, device_type, device_ordinal, param, confidence, method)

        # Step 5.5: Try fuzzy device type matching as fallback (if exact type match failed)
        # This handles typos in device types like "dela" → "delay"
        if type_names and param:
            device_type_index = self.index.get("device_type_index", {})

            # Try fuzzy matching against all device types that have this parameter
            best_type = self.fuzzy_best(text, type_names, want="leftmost")

            if best_type:
                matched_type = best_type[0].lower()
                devices_with_type = device_type_index.get(matched_type, [])

                if devices_with_type:
                    # Extract ordinal if present
                    type_span = best_type[1]
                    post_type = text[type_span[1]:]
                    m = re.search(r"(?:#|\s)(\d+)\b", post_type)
                    if m:
                        try:
                            device_ordinal = int(m.group(1))
                        except:
                            pass

                    if len(devices_with_type) == 1:
                        # Unambiguous - only one device of this type
                        device = devices_with_type[0]
                        device_type = matched_type
                        confidence += 0.35  # Slightly lower than exact type match
                        method = "fuzzy_type_resolution"
                    elif device_ordinal:
                        # Multiple devices, but ordinal specified
                        if 1 <= device_ordinal <= len(devices_with_type):
                            device = devices_with_type[device_ordinal - 1]
                            device_type = matched_type
                            confidence += 0.35
                            method = "fuzzy_type_resolution_ordinal"
                        else:
                            # Invalid ordinal
                            device = None
                            confidence *= 0.5
                            method = "invalid_ordinal"
                    else:
                        # Ambiguous - multiple devices, no ordinal
                        device = devices_with_type[0]
                        device_type = matched_type
                        confidence *= 0.55  # Lower confidence for ambiguity + fuzzy match
                        method = "fuzzy_type_resolution_ambiguous"

                    return DeviceParamMatch(device, device_type, device_ordinal, param, confidence, method)

        # Step 6: Try fuzzy device name match as fallback
        best_dev = self.fuzzy_best(text, self.device_vocab, want="leftmost")
        if best_dev:
            device = self.device_canonical.get(best_dev[0].lower(), best_dev[0])
            device_type = self.device_types.get(device, "unknown")
            confidence += 0.3
            method = "fuzzy_device_fallback"

            # Extract ordinal
            device_span = best_dev[1]
            post_device = text[device_span[1]:]
            m = re.search(r"(?:#|\s)(\d+)\b", post_device)
            if m:
                try:
                    device_ordinal = int(m.group(1))
                except:
                    pass

            # Device-scoped fuzzy parameter matching
            # Now that we've identified the device, try to match parameter within device's params
            device_spec = self.index["params_by_device"].get(device)
            if device_spec:
                device_param_list = device_spec.get("params", [])

                # Build vocabulary with device's params and aliases
                device_param_vocab = list(device_param_list)
                for pname, alist in device_spec.get("aliases", {}).items():
                    device_param_vocab.extend(alist)

                if device_param_vocab:
                    # Try fuzzy match in device's params (search after device name)
                    start_idx = device_span[1]
                    best_prm = self.fuzzy_best(text, device_param_vocab, want="rightmost", limit_region=(start_idx, len(text)))
                    if best_prm:
                        # Use device-scoped canonical lookup
                        param = self.get_canonical_param(best_prm[0], device)
                        confidence += 0.35
                        method = "fuzzy_device_fuzzy_param"
                        return DeviceParamMatch(device, device_type, device_ordinal, param, confidence, method)

            # No fuzzy param match - use device-scoped canonical lookup to handle collisions (e.g., "Dry/Wet" vs "Dry Wet")
            param = self.get_canonical_param(param, device)

            return DeviceParamMatch(device, device_type, device_ordinal, param, confidence, method)

        # Step 7: No device match - check if it's a mixer parameter
        if param.lower() in [p.lower() for p in self.mixer_params]:
            return DeviceParamMatch(
                device="mixer",
                device_type="mixer",
                device_ordinal=None,
                param=param,
                confidence=confidence,
                method=method
            )

        # Step 8: No device match and not a mixer param - return param only
        return DeviceParamMatch(None, None, None, param, confidence * 0.5, method + "_no_device")

    def parse_device_param(self, text: str) -> DeviceParamMatch:
        """
        Parse device and parameter with typo correction.

        Space normalization is now handled at the token level during fuzzy matching,
        so we no longer need sentence-level fallback variations.

        Strategy:
        1. Normalize text and apply typo map
        2. Parse using fuzzy matching (which includes space normalization at token level)

        Args:
            text: Input text (e.g., "set mixgel feedback to 50%")

        Returns:
            DeviceParamMatch with parsed device, param, and confidence
        """
        # Step 1: Normalize and apply typo corrections
        normalized_text = normalize_text(text)
        normalized_text = self.apply_typo_map(normalized_text)

        # Step 2: Parse using internal method
        # Space normalization happens automatically during fuzzy matching
        result = self._parse_device_param_internal(normalized_text)

        return result
